"""Vérifie les règles des documents anglais : dates, références, contacts et pipeline complet.

Entrées : phrases et fixtures anglaises fictives (tests/fixtures/post_g7/en_*.md).
Sorties : assertions sur les spans, les scores et les négatifs courants.
Les tests du pipeline complet exigent en_core_web_sm ; les autres n'utilisent aucun modèle.
"""

from pathlib import Path

import pytest
import spacy.util

from huisclos.config import DetectionConfig
from huisclos.detection.english_patterns import (
    EnglishBirthDateRecognizer,
    EnglishCaseNumberRecognizer,
    EnglishLabeledIdentifierRecognizer,
    EnglishLocalPhoneRecognizer,
    InternationalPhoneRecognizer,
)
from huisclos.detection.organization_bounds import adjust_organizations
from huisclos.detection.pipeline import detect
from huisclos.models import EntityType
from scripts.build_corpus import parse_source

FIXTURES = Path(__file__).parent / "fixtures" / "post_g7"
ENGLISH = DetectionConfig(threshold=0.30, document_language="en")
needs_english = pytest.mark.skipif(
    not spacy.util.is_package("en_core_web_sm"), reason="en_core_web_sm absent"
)


def _found(recognizer: object, text: str) -> list[tuple[str, float]]:
    """Valeurs et scores trouvés par un reconnaisseur local dans text."""
    entity = recognizer.supported_entities[0]  # type: ignore[attr-defined]
    results = recognizer.analyze(text, [entity])  # type: ignore[attr-defined]
    return [(text[r.start : r.end], r.score) for r in results]


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("Ms Calloway (date of birth: 14 March 1979) applies.", "14 March 1979"),
        ("She was born on 3 April 1985 in Leeds.", "3 April 1985"),
        ("born in Leeds, West Yorkshire, on March 14th, 1979", "March 14th, 1979"),
        ("DOB: 03/04/1985", "03/04/1985"),
        ("D.O.B. 1979-03-14", "1979-03-14"),
        ("Date of birth\n: 14th of March 1979", "14th of March 1979"),
    ],
)
def test_birth_dates_with_english_context(text: str, value: str) -> None:
    """Un contexte de naissance anglais, même éloigné de quelques mots, suffit (0,90)."""
    assert _found(EnglishBirthDateRecognizer("en"), text) == [(value, 0.90)]


@pytest.mark.parametrize(
    "text",
    [
        "The hearing took place on 12 June 2026.",
        "Born in 1980, she attended the hearing on 12 June 2026.",
        "She was born in Leeds. The contract was signed on 3 April 2026.",
        "DOB: 31/02/1990",
        "Date of birth: 13/13/1990",
    ],
)
def test_event_dates_and_impossible_dates_stay_visible(text: str) -> None:
    """Une date d'événement ou impossible n'est pas une date de naissance."""
    assert _found(EnglishBirthDateRecognizer("en"), text) == []


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("Re: Claim No. KB-2026-001234", "KB-2026-001234"),
        ("Case No. 1:23-cv-04567 remains pending.", "1:23-cv-04567"),
        ("Our ref: HCL/2026/0457", "HCL/2026/0457"),
        ("Your ref QS-88213", "QS-88213"),
        ("Ref: ABC/12", "ABC/12"),
        ("File number\n2026-0077", "2026-0077"),
    ],
)
def test_private_references_are_case_numbers(text: str, value: str) -> None:
    """Une référence privée annoncée par son libellé est un numéro de dossier (0,90)."""
    assert _found(EnglishCaseNumberRecognizer("en"), text) == [(value, 0.90)]


@pytest.mark.parametrize(
    "text",
    [
        "See Case C-131/12 on the right to be forgotten.",
        "The case law of 2019 applies.",
        "Please file 2024 reports.",
        "In case no one attends, the hearing goes on.",
    ],
)
def test_public_references_and_common_words_stay_visible(text: str) -> None:
    """Une citation publique ou un mot courant ne déclenche aucune référence privée."""
    assert _found(EnglishCaseNumberRecognizer("en"), text) == []


def test_phones_international_and_local_with_context() -> None:
    """Indicatif explicite : toujours ; format national : seulement près d'un mot de téléphone."""
    international = InternationalPhoneRecognizer("en")
    assert _found(international, "Tel: +44 20 7946 0958.") == [("+44 20 7946 0958", 0.90)]
    assert _found(international, "Office +1 (555) 123-4567") == [("+1 (555) 123-4567", 0.75)]
    assert _found(international, "Mobile +33 6 12 34 56 78") == []
    local = EnglishLocalPhoneRecognizer("en")
    assert _found(local, "please call (555) 123-4567") == [("(555) 123-4567", 0.90)]
    assert _found(local, "Tel: 020 7946 0958") == [("020 7946 0958", 0.90)]
    assert _found(local, "Invoice total 555-123-4567 units") == []


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("Employee No. EMP-40417", "EMP-40417"),
        ("his National Insurance number is QQ 12 34 56 C", "QQ 12 34 56 C"),
        ("SSN 123-45-6789", "123-45-6789"),
        ("Policy number: P-77810", "P-77810"),
    ],
)
def test_labelled_identifiers(text: str, value: str) -> None:
    """Un identifiant interne libellé est CUSTOM (0,90) ; le libellé reste visible."""
    assert _found(EnglishLabeledIdentifierRecognizer("en"), text) == [(value, 0.90)]


def test_unlabelled_or_digitless_values_are_ignored() -> None:
    """Sans chiffre ni libellé explicite, aucune valeur n'est retenue."""
    recognizer = EnglishLabeledIdentifierRecognizer("en")
    assert _found(recognizer, "Employee number unknown; Section 12 applies.") == []


def test_english_company_forms_anchor_an_organization() -> None:
    """Ltd, LLP et LLC précédés de mots à majuscule forment une société, sans "For" ni "The"."""
    text = "For Brightmoor Logistics Ltd and THORNBURY & PIKE LLP, The Acme Holdings LLC agrees."
    found = adjust_organizations(text, [], ENGLISH)
    assert [d.text for d in found] == [
        "Brightmoor Logistics Ltd",
        "THORNBURY & PIKE LLP",
        "Acme Holdings LLC",
    ]


@needs_english
@pytest.mark.parametrize("name", ["en_lettre.md", "en_contrat.md"])
def test_english_fixtures_pattern_entities_are_exact(name: str) -> None:
    """Les entités à motif des fixtures anglaises sont trouvées avec leurs bornes exactes."""
    document = parse_source(FIXTURES / name)
    found = {(d.start, d.end, d.entity_type) for d in detect(document.text, ENGLISH)}
    structured = {
        EntityType.ADDRESS,
        EntityType.BIRTH_DATE,
        EntityType.CASE_NUMBER,
        EntityType.EMAIL,
        EntityType.SIRET,
        EntityType.IBAN,
        EntityType.CUSTOM,
    }
    for gold in document.entities:
        if gold.type in structured:
            assert (gold.start, gold.end, gold.type) in found, gold.text


@needs_english
def test_english_fixtures_negatives_stay_visible() -> None:
    """Dates d'événements, pays, rôles, articles et références publiques restent lisibles."""
    text = parse_source(FIXTURES / "en_lettre.md").text
    text += "\n" + parse_source(FIXTURES / "en_contrat.md").text
    found = detect(text, ENGLISH)
    masked = "".join(
        char if any(d.start <= i < d.end for d in found) else " " for i, char in enumerate(text)
    )
    for visible in [
        "12 June 2026",
        "3 April 2026",
        "United Kingdom",
        "Section 94 of the Employment Rights Act 1996",
        "Case C-131/12",
        "the Company",
        "Monday",
        "District Court",
    ]:
        start = text.index(visible)
        assert masked[start : start + len(visible)].strip() == "", visible


@needs_english
def test_english_document_keeps_french_identifiers_and_names() -> None:
    """Un document anglais garde les identifiants français et ses civilités hors du span."""
    text = (
        "Dear Mr Oliver Hartwell, the claimant Ms Jane CALLOWAY lives at 12 rue des Lilas, "
        "75011 Paris. Her mobile is +33 6 12 34 56 78."
    )
    found = [(d.entity_type, d.text) for d in detect(text, ENGLISH)]
    assert (EntityType.PERSON, "Oliver Hartwell") in found
    assert (EntityType.PERSON, "Jane CALLOWAY") in found
    assert (EntityType.ADDRESS, "12 rue des Lilas, 75011 Paris") in found
    assert (EntityType.PHONE, "+33 6 12 34 56 78") in found
