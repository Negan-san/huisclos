"""Contenu sortant : composition unique du message destiné au LLM et contrôle de chaque segment.

Entrées : le résultat de la pseudonymisation, la consigne libre, une détection réglée sous le
seuil, le texte d'origine s'il est disponible et les positions rejetées en revue.
Sorties : OutboundMessage, la chaîne exacte à envoyer, et ses alertes, placées dans leur
segment et dans le contenu complet ; un statut qui n'est jamais un succès par défaut.
Place dans le pipeline : après pseudonymize.tokens, avant tout envoi ou export présenté comme
prêt pour un LLM (D-AF-A3-3 à D-AF-A3-5).
"""

import hashlib
import re
from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from enum import StrEnum

from huisclos.models import TOKEN_LABELS, Detection, EntityType, PseudonymizationResult, Source
from huisclos.pseudonymize.final_check import (
    EXCERPT_CHARS,
    final_check,
    mapping_residuals,
    occurrence_spans,
    output_span,
    outside_tokens,
)

Span = tuple[int, int]
DetectText = Callable[[str], Sequence[Detection]]

# Version du vérificateur, comprise dans les empreintes : un changement de règle périme les
# contrôles et les autorisations déjà donnés.
CHECK_VERSION = "outbound-1"
# Séparateur explicite entre le texte et la consigne ; il fait partie de la chaîne vérifiée.
SEPARATOR = "\n\n---\n\n"
DOCUMENT = "document"
INSTRUCTION = "instruction"

_LABEL_SEPARATOR = r"(?:\\?_|[ \u00a0-])"
_LABELS = "|".join(
    re.escape(label).replace("_", _LABEL_SEPARATOR)
    for label in sorted({label for pair in TOKEN_LABELS.values() for label in pair}, key=len)[::-1]
)
# Forme d'un jeton, même altérée : "[PERSONNE_7]", "PERSON_2", "[Societe B]". Sans crochet,
# le tiret bas est exigé, pour ne pas lire "in case 2" comme un jeton.
_TOKEN_LIKE = re.compile(
    r"(?P<open>[\[({<\u00ab][ \u00a0]*)?(?<![^\W_])(?i:"
    + _LABELS
    + r")(?P<sep>\\?_|[ \u00a0-])(?:\d+|[A-Za-z]{1,3})(?![^\W_])"
    r"(?P<close>[ \u00a0]*[\])}>\u00bb])?"
)


class CheckStatus(StrEnum):
    """État du contrôle : seuls CLEAR et REVIEWED autorisent un envoi présenté comme vérifié."""

    NOT_RUN = "not_run"
    RUNNING = "running"
    UNAVAILABLE = "unavailable"
    ALERTS = "alerts"
    CLEAR = "clear"
    REVIEWED = "reviewed"


SENDABLE = frozenset({CheckStatus.CLEAR, CheckStatus.REVIEWED})


@dataclass(frozen=True)
class OutboundMessage:
    """Chaîne exacte destinée au LLM : texte pseudonymisé, séparateur, puis consigne.

    instruction_start est la position de la consigne dans content, ou None sans consigne.
    """

    document: str
    instruction: str
    content: str
    instruction_start: int | None

    def offset(self, segment: str) -> int:
        """Position du début d'un segment ("document" ou "instruction") dans content."""
        if segment == DOCUMENT:
            return 0
        if self.instruction_start is None:
            raise ValueError("ce message n'a pas de consigne")
        return self.instruction_start


@dataclass(frozen=True)
class Alert:
    """Valeur peut-être identifiante restée en clair dans le contenu sortant.

    start et end sont pris dans le segment, content_start et content_end dans le contenu
    complet ; origin vaut table, detection, context ou unknown_token ; key identifie la
    mention dans son contexte, pour une décision explicite de l'humain.
    """

    segment: str
    start: int
    end: int
    content_start: int
    content_end: int
    text: str
    entity_type: EntityType | None
    origin: str
    key: str

    @property
    def can_acknowledge(self) -> bool:
        """Un jeton inconnu ne se garde pas : il se corrige, car il n'a pas été revu."""
        return self.origin != "unknown_token"


def compose(document: str, instruction: str) -> OutboundMessage:
    """Compose une seule fois le contenu à envoyer.

    Paramètres : document, le texte pseudonymisé ; instruction, la consigne libre.
    Valeur retournée : le message ; une consigne vide ou faite de blancs n'est pas ajoutée.
    Exemple : compose("[PERSONNE_1] écrit.", "Résume.").content
    == "[PERSONNE_1] écrit.\\n\\n---\\n\\nRésume.".
    """
    if not instruction.strip():
        return OutboundMessage(document, "", document, None)
    start = len(document) + len(SEPARATOR)
    return OutboundMessage(document, instruction, document + SEPARATOR + instruction, start)


def known_token_spans(text: str, tokens: Collection[str]) -> list[Span]:
    """Positions des jetons connus écrits exactement, le plus long d'abord, sans chevauchement."""
    spans: list[Span] = []
    for token in sorted(tokens, key=len, reverse=True):
        for match in re.finditer(re.escape(token), text):
            if not any(match.start() < end and start < match.end() for start, end in spans):
                spans.append(match.span())
    return sorted(spans)


def token_like_spans(text: str) -> list[Span]:
    """Positions des chaînes qui ressemblent à un jeton (crochet ou tiret bas exigé)."""
    spans = []
    for match in _TOKEN_LIKE.finditer(text):
        if match["open"] or match["close"] or "_" in match["sep"]:
            start, end = match.span()
            while text[start].isspace():
                start += 1
            spans.append((start, end))
    return spans


def blank(text: str, spans: Sequence[Span]) -> str:
    """Remplace chaque passage par des espaces de même longueur, positions conservées."""
    chars = list(text)
    for start, end in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def alert_key(segment: str, text: str, start: int, end: int) -> str:
    """Identité d'une mention dans son contexte : segment, valeur et 40 caractères autour."""
    left = text[max(0, start - EXCERPT_CHARS) : start]
    right = text[end : end + EXCERPT_CHARS]
    raw = f"{segment}\0{left}\0{text[start:end]}\0{right}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _alerts(
    message: OutboundMessage, segment: str, found: Sequence[tuple[Detection, str]]
) -> list[Alert]:
    """Convertit des restes d'un segment en alertes, les plus longs d'abord, sans chevauchement."""
    text = message.document if segment == DOCUMENT else message.instruction
    offset = message.offset(segment)
    kept: list[tuple[Detection, str]] = []
    for item in sorted(found, key=lambda pair: (-pair[0].length, -pair[0].score, pair[0].start)):
        if not any(d.start < item[0].end and item[0].start < d.end for d, _ in kept):
            kept.append(item)
    return [
        Alert(
            segment,
            d.start,
            d.end,
            d.start + offset,
            d.end + offset,
            text[d.start : d.end],
            None if origin == "unknown_token" else d.entity_type,
            origin,
            alert_key(segment, text, d.start, d.end),
        )
        for d, origin in sorted(kept, key=lambda pair: (pair[0].start, pair[0].end))
    ]


def _trimmed(text: str, start: int, end: int) -> Span | None:
    """Passage sans blancs aux bords, ou None s'il ne contient ni lettre ni chiffre."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end) if any(char.isalnum() for char in text[start:end]) else None


def _subtract(span: Span, removed: Sequence[Span]) -> list[Span]:
    """Parties d'un passage hors des passages retirés."""
    pieces, cursor = [], span[0]
    for start, end in sorted(removed):
        if start < span[1] and cursor < end:
            if cursor < start:
                pieces.append((cursor, start))
            cursor = max(cursor, end)
    if cursor < span[1]:
        pieces.append((cursor, span[1]))
    return pieces


def context_residuals(
    result: PseudonymizationResult,
    source: str,
    detect_text: DetectText,
    rejected_spans: Sequence[Span] = (),
) -> list[Detection]:
    """Restes trouvés en lisant le texte d'origine, avec tout son contexte.

    Une détection du texte d'origine dont une partie n'a pas été remplacée signale une borne
    incomplète ("Jean-Pierre" laissé devant "[PERSONNE_1]"). Les zones réellement remplacées
    et les mentions rejetées sont soustraites ; chaque reste est projeté dans le texte
    pseudonymisé par les longueurs des remplacements, jamais par une recherche de chaîne.
    Lève ValueError si un reste projeté diffère du texte d'origine.
    """
    replaced = [pair[0] for pair in occurrence_spans(result)]
    found = []
    for detection in detect_text(source):
        span = (detection.start, detection.end)
        for start, end in _subtract(span, [*replaced, *rejected_spans]):
            trimmed = _trimmed(source, start, end)
            if trimmed is None:
                continue
            out_start, out_end = output_span(result, *trimmed)
            if result.text[out_start:out_end] != source[trimmed[0] : trimmed[1]]:
                raise ValueError("texte d'origine et texte pseudonymisé incohérents")
            found.append(
                Detection(
                    out_start,
                    out_end,
                    detection.entity_type,
                    detection.score,
                    detection.source,
                    result.text[out_start:out_end],
                )
            )
    return found


def document_alerts(
    message: OutboundMessage,
    result: PseudonymizationResult,
    detect_text: DetectText | None,
    source: str | None = None,
    rejected_spans: Sequence[Span] = (),
) -> list[Alert]:
    """Alertes du texte pseudonymisé : table, nouvelle détection et contexte d'origine.

    Paramètres : message, le contenu composé ; result, la pseudonymisation dont il vient ;
    detect_text, la détection du contrôle, ou None ; source, le texte d'origine s'il est
    disponible ; rejected_spans, les mentions rejetées en revue, en positions d'origine.
    """
    if message.document != result.text:
        raise ValueError("le message ne reprend pas le texte pseudonymisé contrôlé")
    found = [
        (d, "table" if d.source is Source.CASE_TABLE else "detection")
        for d in final_check(result, detect_text, rejected_spans)
    ]
    if source is not None and detect_text is not None:
        tokens = sorted(pair[1] for pair in occurrence_spans(result))
        for detection in context_residuals(result, source, detect_text, rejected_spans):
            found += [
                (piece, "context") for piece in outside_tokens(detection, tokens, result.text)
            ]
    return _alerts(message, DOCUMENT, found)


def instruction_alerts(
    message: OutboundMessage, result: PseudonymizationResult, detect_text: DetectText | None
) -> list[Alert]:
    """Alertes de la consigne libre, à ses propres positions.

    Les jetons connus écrits exactement sont neutralisés ; une forme de jeton absente de la
    table est signalée, sans neutralisation. Le reste est cherché comme le texte : valeurs
    de la table et nouvelle détection. Aucun rejet de la revue ne s'applique à la consigne.
    """
    text = message.instruction
    if not text:
        return []
    known = known_token_spans(text, {entry.token for entry in result.mapping.entities})
    neutral = blank(text, known)
    unknown = token_like_spans(neutral)
    neutral = blank(neutral, unknown)
    found = [
        (Detection(s, e, EntityType.CUSTOM, 1.0, Source.MANUAL, text[s:e]), "unknown_token")
        for s, e in unknown
    ]
    candidates = [(d, "table") for d in mapping_residuals(result.mapping, neutral, text)]
    if detect_text is not None:
        candidates += [(d, "detection") for d in detect_text(neutral)]
    covered = sorted([*known, *unknown])
    for detection, origin in candidates:
        found += [(piece, origin) for piece in outside_tokens(detection, covered, text)]
    return _alerts(message, INSTRUCTION, found)


def check_status(alerts: Sequence[Alert], acknowledged: Collection[str]) -> CheckStatus:
    """Statut d'un contrôle terminé : sans alerte, alertes toutes examinées, ou à traiter.

    Paramètres : alerts, les alertes du contrôle ; acknowledged, les clés des mentions que
    l'humain a explicitement décidé de garder en clair. Un jeton inconnu reste à traiter.
    """
    if not alerts:
        return CheckStatus.CLEAR
    if all(alert.can_acknowledge and alert.key in acknowledged for alert in alerts):
        return CheckStatus.REVIEWED
    return CheckStatus.ALERTS


def send_fingerprint(
    message: OutboundMessage, parameters: str, acknowledged: Collection[str]
) -> str:
    """Empreinte de ce qu'autorise une confirmation : contenu exact, paramètres et décisions.

    Paramètres : message, le contenu composé ; parameters, l'empreinte des réglages du
    contrôle (détection, table, décisions, politique) ; acknowledged, les mentions gardées.
    """
    raw = f"{CHECK_VERSION}\0{message.content}\0{parameters}\0{sorted(acknowledged)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def may_send(authorized: str | None, current: str, status: CheckStatus) -> bool:
    """Dit si l'envoi est permis : statut vérifié et confirmation donnée pour ce contenu exact."""
    return status in SENDABLE and authorized is not None and authorized == current
