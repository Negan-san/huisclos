"""Vérifie les références de procédure et les citations publiées.

Entrées : références fictives, avec ou sans libellé de procédure.
Sorties : assertions sur les spans et le score CASE_NUMBER.
Ces tests limitent le repérage aux références d'affaires sensibles.
"""

import pytest

from huisclos.detection.patterns import CaseNumberRecognizer


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("numéro de parquet : ", "26827000491"),
        ("Parquet n° ", "2026/837291"),
        ("numéro de pourvoi ", "26-93.827"),
        ("pourvoi n° ", "26-93.827"),
        ("Portalis n° ", "DQXN-X-C8M-WVTS"),
    ],
)
def test_procedure_labels_stay_outside_the_span(label: str, value: str) -> None:
    """Garde la seule référence au score 0,90, avec des valeurs inventées."""
    text = label + value + "."
    results = CaseNumberRecognizer().analyze(text, ["CASE_NUMBER"])
    assert [(text[r.start : r.end], r.score) for r in results] == [(value, 0.9)]


@pytest.mark.parametrize(
    "text",
    [
        "26-93.827",
        "26827000491 sans libellé",
        "Cass. soc., 7 octobre 2026, pourvoi n° 26-93.827, publié au Bulletin.",
        "pourvoi 26-93.8279",
        "parquet 268270004910000",
    ],
)
def test_unlabeled_invalid_and_published_references_are_ignored(text: str) -> None:
    """Ne traite ni les nombres ordinaires ni les références publiées comme des affaires privées."""
    assert CaseNumberRecognizer().analyze(text, ["CASE_NUMBER"]) == []


def test_explicitly_unpublished_case_remains_sensitive() -> None:
    """Le nom de la juridiction ne suffit pas à rendre publique une affaire inédite."""
    text = "Cour de cassation : pourvoi n° 26-93.827, affaire non publiée."
    results = CaseNumberRecognizer().analyze(text, ["CASE_NUMBER"])
    assert [text[r.start : r.end] for r in results] == ["26-93.827"]
