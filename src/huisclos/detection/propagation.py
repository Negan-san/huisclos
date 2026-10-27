"""Propagation : retrouve les autres mentions d'une personne ou d'une société déjà repérée.

Entrées : le texte, les détections fusionnées, la configuration et les passages exclus.
Sorties : les mêmes détections, complétées des occurrences trouvées (source "propagation").
Place dans le pipeline : après detection.merge, avant la revue humaine. Si "Jean DUPONT"
est repéré une fois, "M. Dupont" et "DUPONT" plus loin doivent l'être aussi.
"""

import re
from collections.abc import Sequence

from huisclos.config import DetectionConfig
from huisclos.detection.exclusions import is_excluded
from huisclos.models import Detection, EntityType, Source
from huisclos.text_utils import (
    LEGAL_FORMS,
    fold,
    fold_same_length,
    is_capitalized_form,
    letter_count,
)

# Un nom de famille isolé de moins de 3 lettres ("Li", "Ba") masquerait trop de mots courts.
MIN_SURNAME_LETTERS = 3
_PROPAGATED_TYPES = frozenset({EntityType.PERSON, EntityType.ORGANIZATION})


def _is_upper_word(word: str) -> bool:
    """Vrai pour un mot écrit en majuscules d'au moins deux lettres ("DUPONT", "LE")."""
    return letter_count(word) >= 2 and word.upper() == word


def person_variants(name: str) -> set[str]:
    """Formes sous lesquelles une personne peut réapparaître dans le texte.

    Paramètre : name, le texte de la détection ("Jean DUPONT").
    Valeur retournée : la forme exacte, le nom de famille seul s'il compte au moins
    3 lettres, et prénom et nom dans les deux ordres.
    Exemple : person_variants("Jean DUPONT") == {"Jean DUPONT", "DUPONT", "DUPONT Jean"}.
    Le nom de famille est formé des mots en majuscules s'il y en a, sinon du dernier mot.
    """
    words = name.split()
    variants = {" ".join(words)}
    if len(words) < 2:
        return variants
    upper = [_is_upper_word(word) for word in words]
    if any(upper) and not all(upper):
        surname = [w for w, is_upper in zip(words, upper, strict=True) if is_upper]
        given = [w for w, is_upper in zip(words, upper, strict=True) if not is_upper]
    else:
        surname, given = words[-1:], words[:-1]
    if letter_count("".join(surname)) >= MIN_SURNAME_LETTERS:
        variants.add(" ".join(surname))
    variants.add(" ".join(given + surname))
    variants.add(" ".join(surname + given))
    return variants


def organization_variants(name: str) -> set[str]:
    """Formes d'une société : exacte, et sans sa forme juridique ("Garnier Logistique")."""
    words = name.split()
    variants = {" ".join(words)}
    core = list(words)
    while core and core[0] in LEGAL_FORMS:
        core.pop(0)
    while core and core[-1] in LEGAL_FORMS:
        core.pop()
    if core and letter_count("".join(core)) >= MIN_SURNAME_LETTERS:
        variants.add(" ".join(core))
    return variants


def _collect_variants(detections: Sequence[Detection]) -> dict[str, tuple[str, Detection]]:
    """Associe chaque forme repliée à une forme écrite et à l'entité d'origine.

    Si deux entités partagent une forme (le nom de famille d'homonymes), l'entité de plus
    haut score, puis la première dans le texte, est retenue : type et score n'en dépendent
    presque pas, et le regroupement des jetons tranchera à la revue.
    """
    variants: dict[str, tuple[str, Detection]] = {}
    origins = [d for d in detections if d.entity_type in _PROPAGATED_TYPES]
    for origin in sorted(origins, key=lambda d: (-d.score, d.start, d.end)):
        if origin.entity_type == EntityType.PERSON:
            forms = person_variants(origin.text)
        else:
            forms = organization_variants(origin.text)
        for form in sorted(forms):
            if letter_count(form) >= 2:
                variants.setdefault(fold(form), (form, origin))
    return variants


def _pattern(form: str) -> re.Pattern[str]:
    """Motif de recherche d'une forme dans le texte replié, avec bornes de mots."""
    words = [re.escape(word) for word in fold(form).split(" ")]
    return re.compile(r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)")


def matches_case(occurrence: str, form: str) -> bool:
    """Dit si une occurrence respecte les majuscules de la forme cherchée.

    Chaque mot à initiale majuscule dans la forme doit l'être dans l'occurrence, et le
    premier mot de l'occurrence aussi : "petit" ne correspond jamais au nom "Petit".
    """
    found, expected = occurrence.split(), form.split()
    if len(found) != len(expected) or not is_capitalized_form(found[0]):
        return False
    return all(
        is_capitalized_form(word) or not is_capitalized_form(model)
        for word, model in zip(found, expected, strict=True)
    )


def propagate(
    text: str,
    detections: Sequence[Detection],
    config: DetectionConfig,
    exclusion_spans: Sequence[tuple[int, int]] = (),
) -> list[Detection]:
    """Ajoute les autres occurrences des personnes et sociétés retenues.

    Paramètres : text, le texte analysé ; detections, la sortie de merge ; config, pour
    savoir si les exclusions s'appliquent ; exclusion_spans, les passages exclus.
    Valeur retournée : detections et les occurrences ajoutées, triées et sans chevauchement.
    Une occurrence prend le type et le score de son entité d'origine ; elle est ignorée si
    elle chevauche une détection existante ou se trouve dans un passage exclu.
    """
    folded = fold_same_length(text)
    occupied = [(d.start, d.end) for d in detections]
    added: list[Detection] = []
    # Les formes longues d'abord : "Jean DUPONT" doit être pris en entier avant "DUPONT".
    variants = sorted(_collect_variants(detections).items(), key=lambda i: (-len(i[0]), i[0]))
    for _key, (form, origin) in variants:
        for match in _pattern(form).finditer(folded):
            start, end = match.span()
            if not matches_case(text[start:end], form):
                continue
            if any(start < o_end and o_start < end for o_start, o_end in occupied):
                continue
            candidate = Detection(
                start, end, origin.entity_type, origin.score, Source.PROPAGATION, text[start:end]
            )
            if config.use_exclusions and is_excluded(candidate, exclusion_spans):
                continue
            added.append(candidate)
            occupied.append((start, end))
    return sorted([*detections, *added], key=lambda d: (d.start, d.end))
