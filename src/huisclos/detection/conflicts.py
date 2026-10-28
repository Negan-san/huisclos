"""Arbitrage des chevauchements entre détections de types différents (règle 5b).

Entrées : le texte, un groupe de détections déjà unies par type (règle 5a) et l'ensemble
des détections admissibles, c'est-à-dire capables d'atteindre le seuil. Sortie : des
détections sans chevauchement dans le groupe. Place dans le pipeline : appelé par
detection.merge, entre l'union par type et la jonction des voisins (règle 6).
"""

from collections.abc import Collection, Iterable
from dataclasses import replace

from huisclos.models import Detection, EntityType, Source

# Du plus prioritaire au moins prioritaire. Les identifiants à clé de contrôle passent avant
# les noms : un e-mail repéré dans un span NER reste un e-mail. Un ajout manuel passe avant
# tout, quel que soit son type.
TYPE_PRIORITY: tuple[EntityType, ...] = tuple(
    EntityType[name]
    for name in (
        "IBAN NIR CUSTOM SIRET SIREN EMAIL PHONE CASE_NUMBER BIRTH_DATE "
        "ADDRESS ORGANIZATION PERSON LOCATION"
    ).split()
)

# Ponctuation retirée en bordure d'un span (guillemets, parenthèses, tirets, points).
BORDER_PUNCTUATION = frozenset(
    ".,;:!?()[]{}<>\"'/\\-*_|\u00ab\u00bb\u2018\u2019\u201c\u201d\u2013\u2014"
)


def priority(detection: Detection) -> tuple[int, int]:
    """Rang de priorité d'une détection : plus il est petit, plus elle l'emporte.

    Exemple : un ajout manuel vaut (0, rang du type), une détection automatique (1, rang).
    """
    manual = 0 if detection.source == Source.MANUAL else 1
    return manual, TYPE_PRIORITY.index(detection.entity_type)


def sort_key(detection: Detection) -> tuple[int, int, str, str, float]:
    """Clé de tri totale, qui rend le résultat indépendant de l'ordre d'arrivée."""
    return (
        detection.start,
        detection.end,
        detection.entity_type.value,
        detection.source.value,
        -detection.score,
    )


def with_span(
    text: str, detection: Detection, start: int, end: int, **changes: object
) -> Detection:
    """Copie la détection sur [start, end) avec le texte exact correspondant."""
    return replace(detection, start=start, end=end, text=text[start:end], **changes)


def strip_borders(
    text: str, start: int, end: int, *, preserve_parentheses: bool = False
) -> tuple[int, int]:
    """Retire les bordures de [start, end) et retourne ses nouvelles positions.

    preserve_parentheses garde les paires internes d'un téléphone : sa parenthèse
    d'indicatif fait partie de la valeur. Les parenthèses sans partenaire sont retirées.
    """
    paired: set[int] = set()
    openings: list[int] = []
    if preserve_parentheses:
        for index in range(start, end):
            if text[index] == "(":
                openings.append(index)
            elif text[index] == ")" and openings:
                paired.update((openings.pop(), index))
    while (
        start < end
        and start not in paired
        and (text[start].isspace() or text[start] in BORDER_PUNCTUATION)
    ):
        start += 1
    while (
        end > start
        and end - 1 not in paired
        and (text[end - 1].isspace() or text[end - 1] in BORDER_PUNCTUATION)
    ):
        end -= 1
    return start, end


def free_parts(
    text: str, detection: Detection, blockers: Iterable[tuple[int, int]]
) -> list[Detection]:
    """Parties de la détection non couvertes par les passages blockers, dans l'ordre.

    Chaque partie doit compter au moins 2 lettres ou chiffres : le reste d'un IBAN rogné par
    un ajout manuel est encore sensible, alors qu'une initiale isolée ne l'est plus. Toutes
    les parties sont gardées : "Paul Martin" et "Marie Durand" autour d'un e-mail sont deux
    noms distincts, et en perdre un laisserait une personne en clair (priorité au rappel).
    """
    parts: list[tuple[int, int]] = []
    cursor = detection.start
    for blocker_start, blocker_end in sorted(blockers):
        if blocker_start > cursor:
            parts.append((cursor, min(blocker_start, detection.end)))
        cursor = max(cursor, blocker_end)
    if cursor < detection.end:
        parts.append((cursor, min(detection.end, len(text))))
    trimmed = [
        strip_borders(
            text, start, end, preserve_parentheses=detection.entity_type == EntityType.PHONE
        )
        for start, end in parts
    ]
    return [
        with_span(text, detection, start, end)
        for start, end in trimmed
        if sum(c.isalnum() for c in text[start:end]) >= 2
    ]


def resolve_conflicts(
    text: str, group: list[Detection], admissible: Collection[Detection]
) -> list[Detection]:
    """Règle 5b : arbitre les chevauchements entre types différents.

    Les détections admissibles sont examinées d'abord, de la plus forte à la plus faible
    (priorité, puis score, puis longueur), puis les autres dans le même ordre. Une détection
    contenue dans une plus forte disparaît ; une détection qui en contient une plus forte,
    ou la chevauche en partie, est réduite à ses parties libres (priorité au rappel).
    Un candidat que le seuil écartera ne retire donc jamais un caractère à un candidat
    admissible : "Paul" en société à 0,10 ne rogne plus "Paul Martin" en personne à 0,85.
    """
    ordered = sorted(
        group,
        key=lambda d: (d not in admissible, priority(d), -d.score, -d.length, sort_key(d)),
    )
    accepted: list[Detection] = []
    for detection in ordered:
        blockers = [a for a in accepted if a.start < detection.end and detection.start < a.end]
        if not blockers:
            accepted.append(detection)
        elif not any(a.start <= detection.start and detection.end <= a.end for a in blockers):
            accepted.extend(free_parts(text, detection, [(a.start, a.end) for a in blockers]))
    return accepted
