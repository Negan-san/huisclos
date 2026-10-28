"""Mesure la protection effective : caractères sensibles réellement masqués, par document.

Entrées : longueur du texte, annotations de référence, passages masqués par toutes les
substitutions effectives (quel que soit le type prédit) et, à part, alertes du contrôle final.
Sorties : comptes additifs de couverture complète, d'exposition, de surmasquage et d'alertes.
Place dans le pipeline : calcul pur après la détection ou la pseudonymisation ; les métriques
historiques de metrics.py restent inchangées et n'y gagnent aucun appariement.
"""

from collections.abc import Iterable, Sequence
from dataclasses import astuple, dataclass, fields
from typing import Any

from huisclos.evaluation.corpus import CorpusDocument, GoldEntity
from huisclos.evaluation.metrics import EVALUATED_TYPES
from huisclos.models import Detection

Span = tuple[int, int]
# Le périmètre de comparaison avec les gates reste celui des onze types historiques, quel que
# soit le profil mesuré. CUSTOM et LOCATION sont comptés à part, jamais dans ce dénominateur.
SCOPES: dict[str, frozenset[str]] = {
    "evaluated": frozenset(EVALUATED_TYPES),
    "custom_location": frozenset({"CUSTOM", "LOCATION"}),
}
NOT_APPLICABLE = "not applicable"


def merge_spans(spans: Iterable[Span]) -> list[Span]:
    """Réunit des passages en intervalles triés et disjoints ; deux passages contigus fusionnent.

    Exemple : merge_spans([(4, 9), (0, 5), (9, 12)]) == [(0, 12)].
    """
    merged: list[list[int]] = []
    for start, end in sorted(spans):
        if start < 0 or end <= start:
            raise ValueError("Un passage masqué doit être non vide et de début positif.")
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def visible_parts(start: int, end: int, masked: Sequence[Span]) -> list[Span]:
    """Renvoie les morceaux de [start, end) restés en clair ; masked vient de merge_spans.

    Exemple : visible_parts(0, 10, [(0, 4)]) == [(4, 10)].
    """
    parts: list[Span] = []
    cursor = start
    for mask_start, mask_end in masked:
        if mask_start >= end:
            break
        if mask_end <= cursor:
            continue
        if mask_start > cursor:
            parts.append((cursor, mask_start))
        cursor = max(cursor, mask_end)
    if cursor < end:
        parts.append((cursor, end))
    return parts


def ratio(numerator: int, denominator: int) -> float | None:
    """Divise, ou renvoie None sans dénominateur : la mesure n'est alors pas applicable.

    None ne garantit jamais une fuite nulle ; il signale seulement l'absence de base de calcul.
    """
    return numerator / denominator if denominator else None


@dataclass
class CoverageCounts:
    """Comptes additifs d'un ou plusieurs documents ; les ratios se recalculent sur la somme."""

    documents: int = 0
    documents_with_references: int = 0
    documents_with_any_exposure: int = 0
    reference_entities: int = 0
    entities_fully_covered: int = 0
    entities_partially_exposed: int = 0
    entities_fully_exposed: int = 0
    reference_characters: int = 0
    leaked_characters: int = 0
    non_sensitive_characters: int = 0
    non_sensitive_characters_masked: int = 0

    def scores(self) -> dict[str, int | float | None]:
        """Renvoie les comptes, les expositions réunies et les trois ratios publiés."""
        return {
            **{item.name: getattr(self, item.name) for item in fields(self)},
            "entities_with_any_exposure": self.entities_partially_exposed
            + self.entities_fully_exposed,
            "full_coverage_rate": ratio(self.entities_fully_covered, self.reference_entities),
            "leaked_character_rate": ratio(self.leaked_characters, self.reference_characters),
            "non_sensitive_masked_rate": ratio(
                self.non_sensitive_characters_masked, self.non_sensitive_characters
            ),
        }


@dataclass
class AlertCounts:
    """Comptes additifs des alertes du contrôle final ; une alerte ne masque aucun caractère."""

    documents: int = 0
    documents_with_alerts: int = 0
    alerts: int = 0
    alerts_on_visible_references: int = 0
    alerts_elsewhere: int = 0
    exposed_entities: int = 0
    exposed_entities_alerted: int = 0

    def scores(self) -> dict[str, int | float | None]:
        """Renvoie les comptes et la part des entités exposées qu'une alerte signale."""
        return {
            **{item.name: getattr(self, item.name) for item in fields(self)},
            "exposed_entities_alerted_rate": ratio(
                self.exposed_entities_alerted, self.exposed_entities
            ),
        }


def sum_counts[Counted: (CoverageCounts, AlertCounts)](
    items: Iterable[Counted], empty: Counted
) -> Counted:
    """Additionne champ par champ des cumuls de même nature ; empty donne la nature et le départ.

    Exemple : sum_counts([CoverageCounts(documents=1)] * 2, CoverageCounts()).documents == 2.
    """
    totals = list(astuple(empty))
    for item in items:
        totals = [total + value for total, value in zip(totals, astuple(item), strict=True)]
    return type(empty)(*totals)


def touches(span: Span, others: Sequence[Span]) -> bool:
    """Dit si span partage au moins un caractère avec l'un des passages de others."""
    return any(span[0] < other[1] and other[0] < span[1] for other in others)


def _check_bounds(
    text_length: int, references: Sequence[GoldEntity], masked: Sequence[Span]
) -> None:
    """Refuse une annotation ou un passage masqué qui dépasse la fin du texte."""
    if any(reference.end > text_length for reference in references):
        raise ValueError("Une annotation sort du texte.")
    if masked and masked[-1][1] > text_length:
        raise ValueError("Un passage masqué sort du texte.")


def document_coverage(
    text_length: int,
    references: Sequence[GoldEntity],
    masked: Iterable[Span],
    scope: frozenset[str] = SCOPES["evaluated"],
) -> CoverageCounts:
    """Mesure un document : références du périmètre et caractères non sensibles masqués.

    Paramètres : text_length, longueur du texte ; references, toutes ses annotations ;
    masked, les passages réellement remplacés, de tout type prédit ; scope, les types comptés.
    Un seul caractère sensible visible empêche la couverture intégrale. Les caractères non
    sensibles sont ceux hors de toute annotation, quel que soit son type.
    Exemple : "Léa Morvan" annotée et seul "Léa" masqué : une entité partiellement exposée,
    sept caractères visibles (l'espace et le nom).
    """
    merged = merge_spans(masked)
    _check_bounds(text_length, references, merged)
    counts = CoverageCounts(documents=1)
    for reference in references:
        if reference.type.value not in scope:
            continue
        length = reference.end - reference.start
        visible = sum(
            end - start for start, end in visible_parts(reference.start, reference.end, merged)
        )
        counts.reference_entities += 1
        counts.reference_characters += length
        counts.leaked_characters += visible
        counts.entities_fully_covered += int(visible == 0)
        counts.entities_partially_exposed += int(0 < visible < length)
        counts.entities_fully_exposed += int(visible == length)
    counts.documents_with_references = int(counts.reference_entities > 0)
    counts.documents_with_any_exposure = int(counts.leaked_characters > 0)
    sensitive = merge_spans((reference.start, reference.end) for reference in references)
    for start, end in visible_parts(0, text_length, sensitive):
        unmasked = sum(right - left for left, right in visible_parts(start, end, merged))
        counts.non_sensitive_characters += end - start
        counts.non_sensitive_characters_masked += end - start - unmasked
    return counts


def document_alerts(
    references: Sequence[GoldEntity],
    masked: Iterable[Span],
    alerts: Sequence[Span],
    scope: frozenset[str] = SCOPES["evaluated"],
) -> AlertCounts:
    """Relie les alertes, placées dans le texte d'origine, aux caractères sensibles visibles.

    Une entité exposée est signalée si une alerte touche l'un de ses caractères visibles.
    Les alertes ne sont jamais ajoutées aux passages masqués : la fuite reste inchangée.
    """
    merged = merge_spans(masked)
    exposed = [
        parts
        for reference in references
        if reference.type.value in scope
        and (parts := visible_parts(reference.start, reference.end, merged))
    ]
    visible = [part for parts in exposed for part in parts]
    on_visible = sum(touches(alert, visible) for alert in alerts)
    return AlertCounts(
        documents=1,
        documents_with_alerts=int(bool(alerts)),
        alerts=len(alerts),
        alerts_on_visible_references=on_visible,
        alerts_elsewhere=len(alerts) - on_visible,
        exposed_entities=len(exposed),
        exposed_entities_alerted=sum(
            any(touches(part, alerts) for part in parts) for parts in exposed
        ),
    )


def detection_spans(predictions: Sequence[Detection]) -> list[Span]:
    """Renvoie les passages proposés par la détection, tous types confondus, réunis."""
    return merge_spans((prediction.start, prediction.end) for prediction in predictions)


def substituted_spans(occurrences: Sequence[Sequence[int]]) -> list[Span]:
    """Place dans le texte d'origine chaque remplacement (début, fin produits, longueur d'origine).

    Hors jetons, le texte produit recopie l'original : la position d'origine d'un jeton est
    sa position moins l'écart de longueur cumulé des jetons précédents.
    Exemple : [(0, 12, 10)], "[PERSONNE_1]" à la place de "Léa Morvan", donne [(0, 10)].
    """
    spans: list[Span] = []
    shift = 0
    for start, end, original_length in sorted(tuple(item) for item in occurrences):
        if end <= start or original_length < 1:
            raise ValueError("Un remplacement doit avoir un jeton et un texte d'origine non vides.")
        spans.append((start + shift, start + shift + original_length))
        shift += original_length - (end - start)
    return spans


def original_position(occurrences: Sequence[Sequence[int]], start: int, end: int) -> Span:
    """Place dans le texte d'origine un passage du texte produit situé hors jetons.

    Même règle que final_check.source_span : on retire l'écart de longueur de chaque jeton
    qui précède le passage.
    """
    shift = sum(
        original_length - (token_end - token_start)
        for token_start, token_end, original_length in occurrences
        if token_end <= start
    )
    return start + shift, end + shift


def exposure_rows(
    document: CorpusDocument, masked: Iterable[Span], alerts: Sequence[Span] | None
) -> list[dict[str, Any]]:
    """Décrit, pour un document dev seulement, chaque entité évaluée restée visible.

    Les lignes contiennent l'identifiant, le type, la nature de l'exposition, le texte annoté
    et les morceaux visibles ; alerted vaut None quand le contrôle final est indisponible.
    """
    merged = merge_spans(masked)
    rows = []
    for reference in document.entities:
        parts = visible_parts(reference.start, reference.end, merged)
        if reference.type.value not in SCOPES["evaluated"] or not parts:
            continue
        full = parts == [(reference.start, reference.end)]
        rows.append(
            {
                "document_id": document.id,
                "type": reference.type.value,
                "exposure": "full" if full else "partial",
                "reference_text": reference.text,
                "visible_text": " | ".join(document.text[start:end] for start, end in parts),
                "alerted": None if alerts is None else any(touches(part, alerts) for part in parts),
            }
        )
    return rows
