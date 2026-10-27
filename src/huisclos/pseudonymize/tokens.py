"""Attribution des jetons et substitution dans le texte.

Entrées : le texte, ses détections validées et la forme des jetons (TokenStyle).
Sorties : un PseudonymizationResult (texte à jetons, groupes, occurrences, table).
Place dans le pipeline : après pseudonymize.grouping ; le texte produit part au LLM, la
table reste sur le poste pour pseudonymize.reidentify.
"""

import re
from collections.abc import Callable, Sequence
from dataclasses import replace
from functools import cache

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

from huisclos.models import (
    LETTER_INDEXED,
    TOKEN_LABELS,
    Detection,
    EntityGroup,
    EntityType,
    Occurrence,
    PseudonymizationResult,
    TokenStyle,
)
from huisclos.pseudonymize.grouping import group_mentions
from huisclos.pseudonymize.mapping import Mapping

DEFAULT_STYLE = TokenStyle()


def letter_index(number: int) -> str:
    """Numérotation par lettres, comme les colonnes d'un tableur.

    Paramètre : number, rang à partir de 1.
    Valeur retournée : A pour 1, Z pour 26, AA pour 27, AB pour 28.
    """
    if number < 1:
        raise ValueError(f"le rang doit être au moins 1, reçu {number}")
    letters = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def make_token(entity_type: EntityType, number: int, style: TokenStyle = DEFAULT_STYLE) -> str:
    """Écrit un jeton.

    Paramètres : entity_type, le type ; number, son rang dans ce type (à partir de 1) ;
    style, la langue du libellé et les crochets.
    Valeur retournée : le jeton.
    Exemple : make_token(EntityType.ORGANIZATION, 27) == "[SOCIETE_AA]".
    """
    label = TOKEN_LABELS[entity_type][0 if style.language == "fr" else 1]
    index = letter_index(number) if entity_type in LETTER_INDEXED else str(number)
    return f"{style.open_bracket}{label}_{index}{style.close_bracket}"


def assign_tokens(groups: Sequence[EntityGroup], style: TokenStyle) -> list[EntityGroup]:
    """Donne un jeton à chaque groupe, numéroté par type dans l'ordre de première apparition.

    Paramètres : groups, triés par première apparition ; style, la forme des jetons.
    Valeur retournée : les mêmes groupes, champ token rempli.
    """
    counters: dict[EntityType, int] = {}
    numbered = []
    for group in sorted(groups, key=lambda g: g.mention_spans[0][0]):
        counters[group.entity_type] = counters.get(group.entity_type, 0) + 1
        token = make_token(group.entity_type, counters[group.entity_type], style)
        numbered.append(replace(group, token=token))
    return numbered


def _sorted_detections(text: str, detections: Sequence[Detection]) -> list[Detection]:
    """Trie les détections et refuse un chevauchement ou un texte qui ne correspond pas."""
    ordered = sorted(detections, key=lambda d: (d.start, d.end))
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if current.start < previous.end:
            raise ValueError(f"détections qui se chevauchent : {previous!r} et {current!r}")
    for detection in ordered:
        if detection.end > len(text) or text[detection.start : detection.end] != detection.text:
            raise ValueError(f"détection incohérente avec le texte : {detection!r}")
    return ordered


def _token_tables(text: str, groups: Sequence[EntityGroup]) -> dict[str, dict[str, str]]:
    """Table (type, texte exact de la mention) vers jeton, pour l'opérateur de presidio.

    L'opérateur ne reçoit que le texte de la mention ; la table suffit car deux mentions
    de même type et de même texte ont la même clé, donc le même groupe.
    """
    tables: dict[str, dict[str, str]] = {}
    for group in groups:
        table = tables.setdefault(group.entity_type.value, {})
        for start, end in group.mention_spans:
            mention = text[start:end]
            if table.setdefault(mention, group.token) != group.token:
                raise RuntimeError(f"mention rattachée à deux groupes : {mention!r}")
    return tables


def _lookup(table: dict[str, str]) -> Callable[[str], str]:
    """Fonction confiée à l'opérateur custom de presidio : texte de la mention vers jeton."""
    return table.__getitem__


@cache
def _engine() -> AnonymizerEngine:
    """Moteur presidio, créé une seule fois (il ne fait aucun appel réseau)."""
    return AnonymizerEngine()


def _substitute(
    text: str, detections: Sequence[Detection], groups: Sequence[EntityGroup]
) -> tuple[str, tuple[Occurrence, ...]]:
    """Remplace chaque mention par son jeton avec presidio et relève les occurrences.

    presidio rend, pour chaque remplacement, le jeton et sa position dans le texte
    produit, mais pas le texte d'origine : les éléments triés sont appariés aux
    détections triées, puis contrôlés (D-S21-1).
    """
    tables = _token_tables(text, groups)
    result = _engine().anonymize(
        text=text,
        analyzer_results=[
            RecognizerResult(d.entity_type.value, d.start, d.end, d.score) for d in detections
        ],
        operators={
            name: OperatorConfig("custom", {"lambda": _lookup(table)})
            for name, table in tables.items()
        },
        # Sans cette option, presidio réunit deux mentions voisines de même type séparées
        # par une espace, ce qui fausserait le nombre d'occurrences.
        merge_entities_with_spaces=False,
    )
    items = sorted(result.items, key=lambda item: item.start)
    if len(items) != len(detections):
        raise RuntimeError("presidio n'a pas remplacé exactement une fois chaque détection")
    occurrences = []
    for item, detection in zip(items, detections, strict=True):
        expected = tables[detection.entity_type.value][detection.text]
        if item.text != expected or result.text[item.start : item.end] != expected:
            raise RuntimeError(f"jeton inattendu pour la mention {detection.text!r}")
        occurrences.append(Occurrence(expected, detection.text, item.start, item.end))
    return result.text, tuple(occurrences)


def token_like_warnings(text: str, style: TokenStyle = DEFAULT_STYLE) -> tuple[str, ...]:
    """Signale les chaînes du texte d'entrée qui ont déjà la forme d'un jeton.

    Une telle chaîne pourrait être prise pour un vrai jeton à la restauration.
    Valeur retournée : un message par texte concerné, ou un tuple vide.
    """
    pattern = (
        re.escape(style.open_bracket)
        + r"[A-Z][A-Z_]*_(?:\d+|[A-Z]+)"
        + re.escape(style.close_bracket)
    )
    found = list(dict.fromkeys(re.findall(pattern, text)))
    if not found:
        return ()
    return (
        f"The input text already contains {len(found)} token-like string(s), such as "
        f"{found[0]}. Check the restored text: they may be confused with real tokens.",
    )


def pseudonymize(
    text: str,
    detections: Sequence[Detection],
    style: TokenStyle = DEFAULT_STYLE,
    *,
    created_at: str | None = None,
) -> PseudonymizationResult:
    """Remplace chaque détection par le jeton de son groupe.

    Paramètres : text, le texte d'origine ; detections, les détections validées, sans
    chevauchement ; style, la forme des jetons ; created_at, horodatage imposé de la table.
    Valeur retournée : le résultat ; mêmes entrées et même created_at, même sortie.
    Exemple : pseudonymize("Jean DUPONT et M. Dupont", ...).text vaut
    "[PERSONNE_1] et M. [PERSONNE_1]".
    """
    ordered = _sorted_detections(text, detections)
    groups = tuple(assign_tokens(group_mentions(text, ordered), style))
    output, occurrences = _substitute(text, ordered, groups)
    return PseudonymizationResult(
        text=output,
        groups=groups,
        occurrences=occurrences,
        mapping=Mapping.build(groups, occurrences, output, style, created_at),
        warnings=token_like_warnings(text, style),
    )
