import time

import pytest

from huisclos.detection.person_heuristics import (
    CivilityPersonRecognizer,
    FirstNameUpperSurnameRecognizer,
    UpperSurnameFirstNameRecognizer,
    build_person_recognizers,
)


def found(text: str) -> list[tuple[str, str, float]]:
    """Liste (reconnaisseur, texte trouvé, score) pour tous les reconnaisseurs."""
    rows = []
    for recognizer in build_person_recognizers():
        for result in recognizer.analyze(text, ["PERSON"]):
            rows.append((type(recognizer).__name__, text[result.start : result.end], result.score))
    return rows


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Monsieur Jean Dupont a signé.", "Jean Dupont"),
        ("Mme Martin est présente.", "Martin"),
        ("M. DURAND quitte la salle.", "DURAND"),
        ("Mlle O'Brien", "O'Brien"),
        ("Me Lefèvre plaide.", "Lefèvre"),
        ("Maître Dubois", "Dubois"),
        ("Docteur Marie Petit", "Marie Petit"),
        ("Madame Marie-Claire Le Gall", "Marie-Claire Le Gall"),
        ("Maître de Montmorency", "de Montmorency"),
    ],
)
def test_civility_excluded_from_span(text: str, expected: str) -> None:
    assert found(text) == [("CivilityPersonRecognizer", expected, 0.80)]


@pytest.mark.parametrize(
    "text",
    [
        "Monsieur le Président",
        "Monsieur Le Président du tribunal",
        "Madame la Juge",
        "Maître de stage",
        "Selon URSSAF",
        "Le CDI",
        "Chapitre IV",
        "Lyon CEDEX",
        "Dossier RG",
        "TRIBUNAL Judiciaire",
    ],
)
def test_common_phrases_give_nothing(text: str) -> None:
    assert found(text) == []


@pytest.mark.parametrize("text", ["Jean DUPONT", "Marie-Claire LE GALL", "Pour Jean DUPONT"])
def test_first_name_then_upper_surname(text: str) -> None:
    rows = found(text)
    assert [row[0] for row in rows] == ["FirstNameUpperSurnameRecognizer"]
    assert rows[0][1] == text.removeprefix("Pour ")
    assert rows[0][2] == 0.70


@pytest.mark.parametrize("text", ["DUPONT Jean", "DE LA FONTAINE Jean-Pierre"])
def test_upper_surname_then_first_name(text: str) -> None:
    assert found(text) == [("UpperSurnameFirstNameRecognizer", text, 0.70)]


def test_acronym_from_exclusion_list_is_not_a_surname() -> None:
    assert found("Paul SARL") == []
    assert FirstNameUpperSurnameRecognizer(frozenset()).analyze("Paul SARL", ["PERSON"])


def test_results_carry_source_language_and_type() -> None:
    for recognizer in build_person_recognizers():
        assert recognizer.supported_language == "fr"
        assert recognizer.supported_entities == ["PERSON"]
    result = CivilityPersonRecognizer().analyze("Madame Martin", ["PERSON"])[0]
    assert result.entity_type == "PERSON"
    assert result.recognition_metadata["huisclos_source"] == "heuristic"


def test_not_asked_for_person_returns_nothing() -> None:
    assert UpperSurnameFirstNameRecognizer().analyze("DUPONT Jean", ["EMAIL"]) == []


def test_name_does_not_cross_a_line_break() -> None:
    assert found("Madame Martin\nLe tribunal") == [("CivilityPersonRecognizer", "Martin", 0.80)]


@pytest.mark.parametrize("separator", ["\u00a0", "\u202f"])
@pytest.mark.parametrize(
    ("original", "expected"),
    [("Mme Jean DUPONT", "Jean DUPONT"), ("DUPONT Jean", "DUPONT Jean")],
)
def test_nonbreaking_spaces_preserve_name_spans(
    separator: str, original: str, expected: str
) -> None:
    """Conserve les espaces du texte source entre civilité, prénom et nom."""
    text = original.replace(" ", separator)
    rows = found(text)
    assert rows
    assert {row[1] for row in rows} == {expected.replace(" ", separator)}


@pytest.mark.parametrize(
    "text",
    ["A" * 5000, "Dupont " * 715, "DUPONT " * 7143],
    ids=["sans-espace", "initiales-majuscules", "capitales"],
)
def test_long_lines_do_not_trigger_excessive_backtracking(text: str) -> None:
    """Refuse les suites sans prénom en temps borné, même sur 50 000 caractères."""
    started = time.perf_counter()
    assert found(text) == []
    assert time.perf_counter() - started < 1.0


def test_uppercase_run_before_valid_name_is_not_lost() -> None:
    """Une suite sans prénom ne doit pas cacher le nom valide qui la suit."""
    text = "DUPONT DURAND. MARTIN Jean"
    assert found(text) == [("UpperSurnameFirstNameRecognizer", "MARTIN Jean", 0.70)]
