"""Contrôle final du texte pseudonymisé, juste avant son envoi au LLM.

Entrées : le résultat de la pseudonymisation, une fonction de détection réglée sous le seuil
courant, et les positions des mentions que l'humain a rejetées à l'étape Review.
Sorties : les restes, des Detection placées dans le texte pseudonymisé ; une liste vide
dit seulement qu'aucun identifiant résiduel n'a été trouvé, jamais que le texte est anonyme.
Place dans le pipeline : après pseudonymize.tokens, avant l'envoi (principe 3, D-S24-3).
"""

from collections.abc import Callable, Sequence
from dataclasses import replace

from huisclos.detection.exclusions import load_exclusions
from huisclos.detection.propagation import organization_variants, person_variants
from huisclos.models import Detection, EntityType, PseudonymizationResult, Source
from huisclos.pseudonymize.case_memory import KNOWN_SCORE, entry_forms, find_value
from huisclos.pseudonymize.mapping import Mapping
from huisclos.text_utils import letter_count

Span = tuple[int, int]

# Un nom de famille de moins de 3 lettres ("Li") ferait signaler trop de mots courts ; même
# limite que la propagation.
MIN_PART_LETTERS = 3
# La nouvelle détection descend de 0,20 sous le seuil courant : une valeur jugée trop
# incertaine pour la revue doit quand même être montrée avant l'envoi.
THRESHOLD_MARGIN = 0.20
EXCERPT_CHARS = 40


def check_threshold(threshold: float) -> float:
    """Seuil de la nouvelle détection : 0,20 sous le seuil courant, jamais négatif.

    Exemple : check_threshold(0.30) == 0.1.
    """
    return max(0.0, round(threshold - THRESHOLD_MARGIN, 2))


def token_spans(result: PseudonymizationResult) -> list[Span]:
    """Positions des jetons dans le texte pseudonymisé, triées."""
    return sorted((o.start, o.end) for o in result.occurrences)


def neutralize_tokens(result: PseudonymizationResult) -> str:
    """Texte pseudonymisé dont chaque jeton devient une suite d'espaces de même longueur.

    Un jeton ne doit ni passer pour un nom à la nouvelle détection, ni être pris pour un
    reste ; la longueur conservée garde les positions du texte pseudonymisé.
    """
    pieces, cursor = [], 0
    for start, end in token_spans(result):
        pieces.extend((result.text[cursor:start], " " * (end - start)))
        cursor = end
    pieces.append(result.text[cursor:])
    return "".join(pieces)


def _is_excluded_word(part: str) -> bool:
    """Dit si une partie de nom est entièrement couverte par data/exclusions_fr.txt."""
    return any(start == 0 and end >= len(part) for start, end in load_exclusions().spans(part))


def significant_parts(entity_type: EntityType, value: str) -> set[str]:
    """Écritures à chercher pour une valeur de la table : elle-même et ses parties sensibles.

    Paramètres : entity_type, le type de la valeur ; value, son écriture.
    Valeur retournée : value, plus, pour une personne, le nom de famille seul et l'ordre
    inverse ; pour une société, le nom sans forme juridique. Une partie de moins de 3 lettres
    ou formée d'un mot de data/exclusions_fr.txt ("Conseil") n'est pas retenue.
    Exemple : significant_parts(EntityType.PERSON, "Pierre VERNOLAC") contient "VERNOLAC".
    """
    if entity_type is EntityType.PERSON:
        parts = person_variants(value)
    elif entity_type is EntityType.ORGANIZATION:
        parts = organization_variants(value)
    else:
        parts = set()
    kept = {
        part
        for part in parts
        if letter_count(part) >= MIN_PART_LETTERS and not _is_excluded_word(part)
    }
    return kept | {value}


def table_residuals(result: PseudonymizationResult, neutral: str) -> list[Detection]:
    """Écritures de la table, ou leurs parties sensibles, restées en clair dans le texte.

    Paramètres : result, la pseudonymisation ; neutral, son texte aux jetons neutralisés.
    La recherche tolère la casse, les accents et les blancs, en mots entiers.
    """
    return mapping_residuals(result.mapping, neutral, result.text)


def mapping_residuals(mapping: Mapping, neutral: str, text: str) -> list[Detection]:
    """Écritures d'une table, ou leurs parties sensibles, trouvées dans un texte neutralisé.

    Paramètres : mapping, la table ; neutral, le texte dont les jetons connus sont des
    blancs ; text, le même texte avant neutralisation, de même longueur, d'où vient le
    texte de chaque Detection. Sert au texte pseudonymisé comme à la consigne libre.
    """
    found = []
    for entry in mapping.entities:
        parts: set[str] = set()
        for form in entry_forms(entry, mapping):
            parts |= significant_parts(entry.entity_type, form)
        for part in parts:
            for start, end in find_value(neutral, part):
                found.append(
                    Detection(
                        start,
                        end,
                        entry.entity_type,
                        KNOWN_SCORE,
                        Source.CASE_TABLE,
                        text[start:end],
                    )
                )
    return found


def outside_tokens(detection: Detection, tokens: Sequence[Span], text: str) -> list[Detection]:
    """Parties d'un reste hors des jetons, sans blancs aux bords ni partie vide.

    Un reste qui enjambe un jeton ("Pierre [PERSONNE_1] VERNOLAC") devient deux restes,
    dont chacun existe tel quel dans le texte d'origine.
    """
    pieces, cursor = [], detection.start
    for start, end in tokens:
        if start < detection.end and detection.start < end:
            pieces.append((cursor, max(cursor, start)))
            cursor = max(cursor, end)
    pieces.append((cursor, detection.end))
    kept = []
    for start, end in pieces:
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if any(char.isalnum() for char in text[start:end]):
            kept.append(replace(detection, start=start, end=end, text=text[start:end]))
    return kept


def source_span(result: PseudonymizationResult, start: int, end: int) -> Span:
    """Position dans le texte d'origine d'un passage du texte pseudonymisé situé hors jetons.

    Hors jetons, le texte est recopié tel quel : il suffit de retirer l'écart de longueur
    entre chaque jeton qui précède et le texte qu'il remplace.
    """
    shift = sum(len(o.original) - (o.end - o.start) for o in result.occurrences if o.end <= start)
    return start + shift, end + shift


def occurrence_spans(result: PseudonymizationResult) -> list[tuple[Span, Span]]:
    """Couples (passage du texte d'origine, jeton du texte pseudonymisé) de chaque remplacement.

    La position d'origine se déduit sans recherche : hors jetons, le texte est recopié tel
    quel, donc chaque jeton décale la suite de l'écart entre sa longueur et celle du texte
    qu'il remplace.
    """
    pairs, shift = [], 0
    for occurrence in sorted(result.occurrences, key=lambda o: o.start):
        start = occurrence.start + shift
        pairs.append(
            ((start, start + len(occurrence.original)), (occurrence.start, occurrence.end))
        )
        shift += len(occurrence.original) - (occurrence.end - occurrence.start)
    return pairs


def output_span(result: PseudonymizationResult, start: int, end: int) -> Span:
    """Position dans le texte pseudonymisé d'un passage du texte d'origine laissé en clair.

    Inverse de source_span. Lève ValueError si le passage touche un texte remplacé : il
    n'a alors pas de place exacte dans le texte pseudonymisé.
    """
    shift = 0
    for (source_start, source_end), (token_start, token_end) in occurrence_spans(result):
        if source_start < end and start < source_end:
            raise ValueError("le passage touche un texte remplacé par un jeton")
        if source_end <= start:
            shift += (source_end - source_start) - (token_end - token_start)
    return start - shift, end - shift


def without_overlaps(found: Sequence[Detection]) -> list[Detection]:
    """Garde les restes les plus longs, puis ceux de la table, sans chevauchement."""
    kept: list[Detection] = []
    for detection in sorted(found, key=lambda d: (-d.length, -d.score, d.start)):
        if not any(d.start < detection.end and detection.start < d.end for d in kept):
            kept.append(detection)
    return sorted(kept, key=lambda d: (d.start, d.end))


def final_check(
    result: PseudonymizationResult,
    detect_text: Callable[[str], Sequence[Detection]] | None = None,
    rejected_spans: Sequence[Span] = (),
) -> list[Detection]:
    """Cherche les identifiants restés en clair dans le texte à envoyer.

    Paramètres : result, la pseudonymisation ; detect_text, une détection réglée sous le
    seuil courant (check_threshold), appliquée au texte aux jetons neutralisés, ou None ;
    rejected_spans, les positions (texte d'origine) des mentions que l'humain a rejetées
    en revue : seules ces mentions ne déclenchent aucune alerte. Un rejet ne vaut pas pour
    la même écriture ailleurs, où le contexte peut identifier quelqu'un (D-AF-A3-4).
    Valeur retournée : les restes, placés dans result.text, triés et sans chevauchement.
    Exemple : un "Vernolac" oublié après "Pierre VERNOLAC" masqué est signalé.
    """
    neutral = neutralize_tokens(result)
    found = table_residuals(result, neutral)
    if detect_text is not None:
        found.extend(detect_text(neutral))
    tokens = token_spans(result)
    pieces = [piece for d in found for piece in outside_tokens(d, tokens, result.text)]
    kept = [
        piece
        for piece in pieces
        if not inside(source_span(result, piece.start, piece.end), rejected_spans)
    ]
    return without_overlaps(kept)


def inside(span: Span, spans: Sequence[Span]) -> bool:
    """Dit si span est compris dans l'un des passages de spans."""
    return any(start <= span[0] and span[1] <= end for start, end in spans)


def excerpt(text: str, residual: Detection, width: int = EXCERPT_CHARS) -> tuple[str, Detection]:
    """Extrait du texte autour d'un reste, coupé à un blanc, et le reste replacé dedans.

    Paramètres : text, le texte pseudonymisé ; residual, un reste de final_check ; width,
    le nombre de caractères de contexte de chaque côté.
    Valeur retournée : l'extrait et le reste aux positions de l'extrait.
    """
    start = max(0, residual.start - width)
    end = min(len(text), residual.end + width)
    if start > 0:
        blank = text.find(" ", start, residual.start)
        start = blank + 1 if blank != -1 else start
    if end < len(text):
        blank = text.rfind(" ", residual.end, end)
        end = blank if blank != -1 else end
    moved = replace(residual, start=residual.start - start, end=residual.end - start)
    return text[start:end], moved
