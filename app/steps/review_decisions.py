"""Décisions de l'écran Review : masquer ou non chaque mention, ajouts manuels.

Entrées : detections, manual_entities et group_decisions dans l'état de session.
Sorties : current_detections() (les détections de travail), is_masked() et add_manual(),
que l'étape Review appelle pour afficher et modifier les décisions.
Place dans le pipeline : entre la détection et pseudonymize.tokens ; ces règles décident de
ce qui sera remplacé par un jeton.
"""

import re
from dataclasses import dataclass, replace

import streamlit as st

from app.state import KEY_DETECTIONS, KEY_GROUP_DECISIONS, KEY_MANUAL_ENTITIES
from huisclos.models import Detection, EntityType, Source
from huisclos.text_utils import fold, fold_same_length

Span = tuple[int, int]


@dataclass(frozen=True)
class Decision:
    """Choix de l'humain pour une mention : la masquer ou non, et un type imposé éventuel."""

    masked: bool = True
    entity_type: EntityType | None = None


def decisions() -> dict[Span, Decision]:
    """Renvoie le dictionnaire des décisions de la session, clé = position (début, fin).

    Les décisions portent sur les positions, pas sur les groupes : un groupe est recalculé
    à chaque ajout ou changement de type, une position reste la même.
    """
    return st.session_state[KEY_GROUP_DECISIONS]


def overlaps(first: Detection, second: Detection) -> bool:
    """Dit si deux détections se recouvrent, ne serait-ce que d'un caractère."""
    return first.start < second.end and second.start < first.end


def current_detections() -> list[Detection]:
    """Construit les détections de travail : détection automatique, ajouts et types imposés.

    Un ajout manuel remplace les détections automatiques qu'il recouvre : la pseudonymisation
    refuse les chevauchements, et le choix explicite de l'humain l'emporte.
    """
    manual = st.session_state[KEY_MANUAL_ENTITIES]
    kept = [d for d in st.session_state[KEY_DETECTIONS] if not any(overlaps(d, m) for m in manual)]
    result = []
    for detection in sorted([*kept, *manual], key=lambda d: (d.start, d.end)):
        forced = decisions().get((detection.start, detection.end), Decision()).entity_type
        result.append(replace(detection, entity_type=forced) if forced else detection)
    return result


def is_masked(detection: Detection) -> bool:
    """Dit si la mention sera remplacée par un jeton (vrai tant que l'humain ne l'a pas rejetée)."""
    return decisions().get((detection.start, detection.end), Decision()).masked


def find_occurrences(text: str, value: str) -> list[Span]:
    """Trouve toutes les occurrences d'une valeur, sans casse, sans accents, mots entiers.

    Paramètres : text, le texte d'origine ; value, la valeur saisie par l'humain.
    Valeur retournée : les positions (début, fin) dans le texte d'origine. Le repli des
    accents garde la longueur du texte, donc les positions trouvées sont valides ; les
    blancs de la valeur correspondent à n'importe quel blanc du texte, retour à la ligne
    compris. Exemple : find_occurrences("Le CLIENT a écrit", "client") donne [(3, 9)].
    """
    folded = fold(value)
    if not folded:
        return []
    body = r"\s+".join(re.escape(word) for word in folded.split(" "))
    before = r"(?<!\w)" if re.match(r"\w", folded[0]) else ""
    after = r"(?!\w)" if re.match(r"\w", folded[-1]) else ""
    pattern = re.compile(f"{before}{body}{after}")
    return [match.span() for match in pattern.finditer(fold_same_length(text))]


def add_manual(text: str, value: str, entity_type: EntityType) -> tuple[int, int]:
    """Ajoute chaque occurrence de la valeur comme détection manuelle de score 1,0.

    Une occurrence déjà comprise dans une valeur masquée est laissée de côté : elle est
    protégée, et la remplacer ferait perdre une partie de la valeur plus longue (le nom
    "DUPONT" dans "Jean DUPONT" ne doit pas libérer "Jean"). Une occurrence qui recouvre
    une valeur rejetée ou une détection partielle la remplace, et les décisions de ces
    positions sont effacées. Renvoie (occurrences ajoutées, occurrences déjà couvertes).
    """
    spans = find_occurrences(text, value)
    protected = [(d.start, d.end) for d in current_detections() if is_masked(d)]
    fresh = [s for s in spans if not any(a <= s[0] and s[1] <= b for a, b in protected)]
    added = [Detection(s, e, entity_type, 1.0, Source.MANUAL, text[s:e]) for s, e in fresh]
    kept = [
        m for m in st.session_state[KEY_MANUAL_ENTITIES] if not any(overlaps(m, a) for a in added)
    ]
    st.session_state[KEY_MANUAL_ENTITIES] = [*kept, *added]
    for span in [s for s in decisions() if any(s[0] < a.end and a.start < s[1] for a in added)]:
        del decisions()[span]
    return len(added), len(spans) - len(added)
