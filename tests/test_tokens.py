"""Tests de l'attribution des jetons et de la substitution (pseudonymize.tokens)."""

import pytest

from huisclos.models import Detection, EntityType, Source, TokenStyle
from huisclos.pseudonymize.mapping import sha256_of
from huisclos.pseudonymize.tokens import letter_index, make_token, pseudonymize

P = EntityType.PERSON
ORG = EntityType.ORGANIZATION
FIXED_TIME = "2026-10-27T12:00:00+00:00"


def mentions(text: str, *items: tuple[str, EntityType]) -> list[Detection]:
    """Construit une détection par fragment, cherché à la suite du précédent."""
    detections, cursor = [], 0
    for fragment, entity_type in items:
        start = text.index(fragment, cursor)
        cursor = start + len(fragment)
        detections.append(Detection(start, cursor, entity_type, 0.9, Source.MANUAL, fragment))
    return detections


CASE_TEXT = (
    "Entre Atelier Verlaine SAS et M. Jean DUPONT, joignable au 01 23 45 67 89 "
    "ou à jean.dupont@example.com. M. Dupont, né le 12 mars 1985, a écrit à la société "
    "Atelier Verlaine depuis le +33 1 23 45 67 89. Marie DUPONT témoigne."
)
CASE_DETECTIONS = mentions(
    CASE_TEXT,
    ("Atelier Verlaine SAS", ORG),
    ("Jean DUPONT", P),
    ("01 23 45 67 89", EntityType.PHONE),
    ("jean.dupont@example.com", EntityType.EMAIL),
    ("Dupont", P),
    ("12 mars 1985", EntityType.BIRTH_DATE),
    ("Atelier Verlaine", ORG),
    ("+33 1 23 45 67 89", EntityType.PHONE),
    ("Marie DUPONT", P),
)


def test_case_text_tokens() -> None:
    result = pseudonymize(CASE_TEXT, CASE_DETECTIONS, created_at=FIXED_TIME)
    assert result.text == (
        "Entre [SOCIETE_A] et M. [PERSONNE_1], joignable au [TELEPHONE_1] "
        "ou à [EMAIL_1]. M. [PERSONNE_2], né le [DATE_NAISSANCE_1], a écrit à la société "
        "[SOCIETE_A] depuis le [TELEPHONE_1]. [PERSONNE_3] témoigne."
    )
    ambiguous = next(g for g in result.groups if g.canonical == "Dupont")
    assert ambiguous.token == "[PERSONNE_2]"
    assert len(ambiguous.ambiguous_with) == 2
    assert result.warnings == ()


def test_no_detected_value_remains_and_occurrences_are_exact() -> None:
    result = pseudonymize(CASE_TEXT, CASE_DETECTIONS, created_at=FIXED_TIME)
    for value in ("Verlaine", "DUPONT", "Dupont", "45 67", "example.com", "1985"):
        assert value not in result.text
    assert [o.original for o in result.occurrences] == [d.text for d in CASE_DETECTIONS]
    starts = [o.start for o in result.occurrences]
    assert starts == sorted(starts)
    for occurrence in result.occurrences:
        assert result.text[occurrence.start : occurrence.end] == occurrence.token


def test_all_dupont_forms_get_one_token() -> None:
    text = "Jean DUPONT, M. Dupont, DUPONT, Dupont, DUPONT Jean, J. Dupont."
    forms = ["Jean DUPONT", "Dupont", "DUPONT", "Dupont", "DUPONT Jean", "J. Dupont"]
    result = pseudonymize(text, mentions(text, *((f, P) for f in forms)))
    assert result.text == (
        "[PERSONNE_1], M. [PERSONNE_1], [PERSONNE_1], [PERSONNE_1], [PERSONNE_1], [PERSONNE_1]."
    )


def test_numbering_follows_first_appearance_per_type() -> None:
    text = "Marie MARTIN, Atelier Verlaine, Paul DURAND, Marie MARTIN."
    result = pseudonymize(
        text,
        mentions(
            text,
            ("Marie MARTIN", P),
            ("Atelier Verlaine", ORG),
            ("Paul DURAND", P),
            ("Marie MARTIN", P),
        ),
    )
    assert result.text == "[PERSONNE_1], [SOCIETE_A], [PERSONNE_2], [PERSONNE_1]."


def test_twenty_seventh_company_gets_double_letters() -> None:
    names = [f"Societe{chr(ord('a') + i // 26)}{chr(ord('a') + i % 26)} SAS" for i in range(27)]
    text = ", ".join(names)
    result = pseudonymize(text, mentions(text, *((n, ORG) for n in names)))
    tokens = [g.token for g in result.groups]
    assert tokens[0] == "[SOCIETE_A]"
    assert tokens[25] == "[SOCIETE_Z]"
    assert tokens[26] == "[SOCIETE_AA]"


@pytest.mark.parametrize(
    ("number", "letters"),
    [
        (1, "A"),
        (26, "Z"),
        (27, "AA"),
        (28, "AB"),
        (52, "AZ"),
        (53, "BA"),
        (702, "ZZ"),
        (703, "AAA"),
    ],
)
def test_letter_index(number: int, letters: str) -> None:
    assert letter_index(number) == letters


def test_letter_index_refuses_zero() -> None:
    with pytest.raises(ValueError):
        letter_index(0)


def test_english_style() -> None:
    text = "Jean DUPONT et Atelier Verlaine SARL."
    detections = mentions(text, ("Jean DUPONT", P), ("Atelier Verlaine SARL", ORG))
    result = pseudonymize(text, detections, TokenStyle(language="en"))
    assert result.text == "[PERSON_1] et [COMPANY_A]."
    assert make_token(EntityType.CASE_NUMBER, 2, TokenStyle(language="en")) == "[CASE_2]"


def test_custom_brackets() -> None:
    style = TokenStyle(open_bracket="<<", close_bracket=">>")
    assert make_token(EntityType.BIRTH_DATE, 1, style) == "<<DATE_NAISSANCE_1>>"


def test_unknown_language_is_refused() -> None:
    with pytest.raises(ValueError, match="language"):
        TokenStyle(language="de")


def test_adjacent_mentions_of_same_type_stay_separate() -> None:
    text = "Signé : Jean DUPONT Paul MARTIN"
    result = pseudonymize(text, mentions(text, ("Jean DUPONT", P), ("Paul MARTIN", P)))
    assert result.text == "Signé : [PERSONNE_1] [PERSONNE_2]"
    assert len(result.occurrences) == 2


def test_determinism() -> None:
    first = pseudonymize(CASE_TEXT, CASE_DETECTIONS, created_at=FIXED_TIME)
    second = pseudonymize(CASE_TEXT, list(reversed(CASE_DETECTIONS)), created_at=FIXED_TIME)
    assert first == second
    assert first.mapping.to_json().encode("utf-8") == second.mapping.to_json().encode("utf-8")


def test_warning_when_input_already_contains_a_token() -> None:
    text = "Voir [PERSONNE_1] et Jean DUPONT."
    result = pseudonymize(text, mentions(text, ("Jean DUPONT", P)))
    assert len(result.warnings) == 1
    assert "[PERSONNE_1]" in result.warnings[0]


def test_no_detection_leaves_text_unchanged() -> None:
    result = pseudonymize("Rien à masquer.", [])
    assert result.text == "Rien à masquer."
    assert result.groups == ()
    assert result.occurrences == ()


def test_overlapping_detections_are_refused() -> None:
    text = "Jean DUPONT"
    detections = [
        Detection(0, 11, P, 1.0, Source.MANUAL, "Jean DUPONT"),
        Detection(5, 11, P, 1.0, Source.MANUAL, "DUPONT"),
    ]
    with pytest.raises(ValueError, match="chevauchent"):
        pseudonymize(text, detections)


def test_mapping_hash_matches_output() -> None:
    result = pseudonymize(CASE_TEXT, CASE_DETECTIONS, created_at=FIXED_TIME)
    assert result.mapping.pseudonymized_sha256 == sha256_of(result.text)
    assert [e.token for e in result.mapping.entities] == [g.token for g in result.groups]
