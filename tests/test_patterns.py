"""Teste les spans, scores et sources des reconnaisseurs français locaux.

Entrées : textes fictifs, identifiants synthétiques et pièges juridiques.
Sorties : assertions sur les résultats Presidio, sans service externe.
Ces tests vérifient le contrat avant toute fusion ou revue humaine.
"""

import random

import pytest
from presidio_analyzer import EntityRecognizer, RecognizerResult

from huisclos.detection.patterns import (
    AddressRecognizer,
    BirthDateRecognizer,
    CaseNumberRecognizer,
    EmailRecognizer,
    IbanRecognizer,
    NirRecognizer,
    PhoneFrRecognizer,
    SirenRecognizer,
    SiretRecognizer,
    build_pattern_recognizers,
)
from huisclos.evaluation.synthetic_ids import (
    format_iban,
    format_nir,
    format_siren,
    format_siret,
    make_iban_fr,
    make_nir,
    make_siren,
    make_siret,
)


def _analyze(recognizer: EntityRecognizer, text: str) -> list[RecognizerResult]:
    """Analyse text avec le seul type pris en charge par recognizer."""
    return recognizer.analyze(text, recognizer.supported_entities, None)


def _assert_detection(
    recognizer: EntityRecognizer,
    text: str,
    expected: str,
    score: float,
    source: str = "pattern",
) -> None:
    """Vérifie l'unique span de text, son score, son type et ses métadonnées."""
    results = _analyze(recognizer, text)
    assert len(results) == 1, [
        (text[result.start : result.end], result.score) for result in results
    ]
    result = results[0]
    assert text[result.start : result.end] == expected
    assert result.start == text.index(expected)
    assert result.end == result.start + len(expected)
    assert result.score == score
    assert result.entity_type == recognizer.supported_entities[0]
    assert result.recognition_metadata["recognizer_name"] == recognizer.name
    assert result.recognition_metadata["huisclos_source"] == source


def test_registry_and_offline_contract(no_network: None) -> None:
    """Vérifie l'ordre stable, le français et l'exécution sans accès réseau."""
    recognizers = build_pattern_recognizers()
    assert [recognizer.name for recognizer in recognizers] == [
        "NirRecognizer",
        "SirenRecognizer",
        "SiretRecognizer",
        "IbanRecognizer",
        "EmailRecognizer",
        "PhoneFrRecognizer",
        "BirthDateRecognizer",
        "CaseNumberRecognizer",
        "AddressRecognizer",
    ]
    for recognizer in recognizers:
        assert recognizer.supported_language == "fr"
        assert not recognizer.context
        assert recognizer.analyze("test@example.test", [], None) == []
        assert _analyze(recognizer, "") == []
        _analyze(recognizer, "née le 3 avril 1990, tél. 06.12.34.56.78, test@example.test")


@pytest.mark.parametrize("corsica", [None, "2A", "2B"])
@pytest.mark.parametrize("valid", [True, False])
def test_nir(corsica: str | None, valid: bool) -> None:
    """Vérifie les NIR groupés, corses et à clé fausse sans perdre le span."""
    value = format_nir(make_nir(random.Random(11), valid=valid, corsica=corsica))
    _assert_detection(
        NirRecognizer(),
        "N° SS : " + value + ".",
        value,
        1.0 if valid else 0.40,
        "checksum" if valid else "pattern",
    )
    dotted = value.replace(" ", ".")
    _assert_detection(
        NirRecognizer(), dotted, dotted, 1.0 if valid else 0.40, "checksum" if valid else "pattern"
    )


@pytest.mark.parametrize(
    "value", ["585039912345678", "185139912345678", "185032C12345678", "11850399123456789"]
)
def test_invalid_nir_structure(value: str) -> None:
    """Refuse les suites non plausibles même après le libellé NIR."""
    assert _analyze(NirRecognizer(), "NIR " + value) == []


@pytest.mark.parametrize("formatted", [False, True])
def test_company_identifiers(formatted: bool) -> None:
    """Vérifie les clés, le contexte accentué et les scores SIREN et SIRET."""
    rng = random.Random(111)
    company, establishment = make_siren(rng), make_siret(rng)
    if formatted:
        company, establishment = format_siren(company), format_siret(establishment)
    _assert_detection(SirenRecognizer(), company, company, 0.70, "checksum")
    _assert_detection(SirenRecognizer(), "IMMATRICULÉE : " + company, company, 1.0, "checksum")
    _assert_detection(SiretRecognizer(), establishment, establishment, 0.85, "checksum")
    _assert_detection(SiretRecognizer(), "SIRET : " + establishment, establishment, 1.0, "checksum")
    invalid = make_siret(rng, valid=False)
    _assert_detection(SiretRecognizer(), "ÉTABLISSEMENT " + invalid, invalid, 0.40)
    assert _analyze(SiretRecognizer(), invalid) == []
    assert _analyze(SirenRecognizer(), "123 456 789 euros") == []


def test_context_window_and_boundaries() -> None:
    """Limite le contexte aux 40 caractères précédents et exclut les chiffres collés."""
    company = make_siren(random.Random(11))
    _assert_detection(SirenRecognizer(), "SIREN" + " " * 35 + company, company, 1.0, "checksum")
    _assert_detection(SirenRecognizer(), "SIREN" + " " * 36 + company, company, 0.70, "checksum")
    _assert_detection(SirenRecognizer(), company + " SIREN", company, 0.70, "checksum")
    for value in ("0" + company, company + "0"):
        assert _analyze(SirenRecognizer(), value) == []
    establishment = make_siret(random.Random(11))
    for value in ("0" + establishment, establishment + "0"):
        assert _analyze(SiretRecognizer(), value) == []


@pytest.mark.parametrize("valid", [True, False])
@pytest.mark.parametrize("formatted", [True, False])
def test_iban_stops_before_bank_name(valid: bool, formatted: bool) -> None:
    """Laisse le mot BNP hors de l'IBAN, même lorsque la clé FR est fausse."""
    value = make_iban_fr(random.Random(11), valid=valid)
    if formatted:
        value = format_iban(value)
    _assert_detection(
        IbanRecognizer(),
        "IBAN : " + value + " BNP.",
        value,
        1.0 if valid else 0.40,
        "checksum" if valid else "pattern",
    )


@pytest.mark.parametrize(
    ("recognizer_class", "text", "expected", "score"),
    [
        (
            EmailRecognizer,
            "<cabinet.fictif+test@example.test>",
            "cabinet.fictif+test@example.test",
            0.95,
        ),
        (EmailRecognizer, "Contact : test@example.test.", "test@example.test", 0.95),
        (PhoneFrRecognizer, "+33 (0)1 23 45 67 89", "+33 (0)1 23 45 67 89", 0.75),
        (PhoneFrRecognizer, "06.12.34.56.78", "06.12.34.56.78", 0.75),
        (PhoneFrRecognizer, "Téléphone : 0033 (0)6 12 34 56 78", "0033 (0)6 12 34 56 78", 0.90),
        (PhoneFrRecognizer, "fixe : +33123456789", "+33123456789", 0.90),
        (PhoneFrRecognizer, "0033612345678", "0033612345678", 0.75),
        (PhoneFrRecognizer, "mobile : 06-12-34-56-78", "06-12-34-56-78", 0.90),
        (BirthDateRecognizer, "née le 3 avril 1990 à Lyon", "3 avril 1990", 0.90),
        (BirthDateRecognizer, "né le 1er mai 1985", "1er mai 1985", 0.90),
        (BirthDateRecognizer, "né(e) le 12/03/1985", "12/03/1985", 0.90),
        (BirthDateRecognizer, "NAISSANCE : 12.03.1985", "12.03.1985", 0.90),
        (BirthDateRecognizer, "NÉE le 29 février 2000", "29 février 2000", 0.90),
        (BirthDateRecognizer, "née le 12 aout 1985", "12 aout 1985", 0.90),
        (CaseNumberRecognizer, "RG n° 24/01873", "24/01873", 0.90),
        (CaseNumberRecognizer, "N° RG F 23/00456", "F 23/00456", 0.90),
        (CaseNumberRecognizer, "RG n° F 23/00456", "F 23/00456", 0.90),
        (CaseNumberRecognizer, "R.G. 2024/01873", "2024/01873", 0.90),
        (CaseNumberRecognizer, "N° Portalis DBVM-V-B7H-ABCD", "DBVM-V-B7H-ABCD", 0.90),
        (AddressRecognizer, "12 rue des Lilas, 75011 Paris", "12 rue des Lilas, 75011 Paris", 0.70),
        (
            AddressRecognizer,
            "3 bis avenue Jean Jaurès\n92400 Courbevoie",
            "3 bis avenue Jean Jaurès\n92400 Courbevoie",
            0.70,
        ),
        (AddressRecognizer, "5 rue de l\u2019Église", "5 rue de l\u2019Église", 0.55),
        (AddressRecognizer, "5 rue de l'Église", "5 rue de l'Église", 0.55),
        (AddressRecognizer, "75011 Paris", "75011 Paris", 0.45),
        (AddressRecognizer, "75011\u00a0Paris", "75011\u00a0Paris", 0.45),
        (AddressRecognizer, "12345 rue des Lilas", "12345 rue des Lilas", 0.55),
        (
            AddressRecognizer,
            "12345 rue des Lilas, 75011 Paris",
            "12345 rue des Lilas, 75011 Paris",
            0.70,
        ),
        (
            AddressRecognizer,
            "2 ter av. des Lilas, 75011 Paris CEDEX 11",
            "2 ter av. des Lilas, 75011 Paris CEDEX 11",
            0.70,
        ),
    ],
)
def test_exact_spans_and_scores(
    recognizer_class: type[EntityRecognizer],
    text: str,
    expected: str,
    score: float,
) -> None:
    """Vérifie chaque forme demandée et sa tranche exacte dans le texte original."""
    _assert_detection(recognizer_class(), text, expected, score)


@pytest.mark.parametrize(
    ("recognizer_class", "text"),
    [
        (EmailRecognizer, "<test@localhost>"),
        (EmailRecognizer, "test..test@example.test"),
        (PhoneFrRecognizer, "0612345678901"),
        (PhoneFrRecognizer, "10612345678"),
        (PhoneFrRecognizer, "+330123456789"),
        (BirthDateRecognizer, "audience du 12 mars 2025"),
        (BirthDateRecognizer, "né le 31/02/1990"),
        (BirthDateRecognizer, "née le 12/03.1985"),
        (BirthDateRecognizer, "nécessaire le 12 mars 2025"),
        (CaseNumberRecognizer, "Cass. soc., 12 mars 2020, n° 18-12.345"),
        (CaseNumberRecognizer, "24/01873 sans libellé"),
        (CaseNumberRecognizer, "RG n° 24/018730"),
        (CaseNumberRecognizer, "Portalis 24/01873"),
        (CaseNumberRecognizer, "RG DBVM-V-B7H-ABCD"),
        (AddressRecognizer, "Code du travail, article L. 1232-6"),
        (AddressRecognizer, "rue de l\u2019Église"),
    ],
)
def test_rejects_traps(recognizer_class: type[EntityRecognizer], text: str) -> None:
    """Refuse les pièges dépourvus de structure ou de contexte suffisant."""
    assert _analyze(recognizer_class(), text) == []


def test_repeated_occurrences_have_original_offsets() -> None:
    """Conserve les positions de deux occurrences identiques dans le même texte."""
    value = "test@example.test"
    text = f"<{value}>, puis {value}."
    results = _analyze(EmailRecognizer(), text)
    assert [(result.start, result.end) for result in results] == [(1, 18), (26, 43)]
    assert all(text[result.start : result.end] == value for result in results)


def test_multiple_ibans_and_nonbreaking_spaces() -> None:
    """Préserve deux IBAN proches et les séparateurs insécables dans les identifiants."""
    rng = random.Random(11)
    first, second = format_iban(make_iban_fr(rng)), make_iban_fr(rng)
    text = first + " " + second
    results = _analyze(IbanRecognizer(), text)
    assert [text[result.start : result.end] for result in results] == [first, second]
    for separator in ("\u00a0", "\u202f"):
        value = format_nir(make_nir(rng)).replace(" ", separator)
        _assert_detection(NirRecognizer(), value, value, 1.0, "checksum")
        value = format_siret(make_siret(rng)).replace(" ", separator)
        _assert_detection(SiretRecognizer(), value, value, 0.85, "checksum")


def test_generated_compact_identifiers(no_network: None) -> None:
    """Vérifie le rappel et les spans des identifiants compacts sur des graines fixes."""
    rng = random.Random(11027)
    for _ in range(100):
        for recognizer, generator, score in (
            (NirRecognizer(), make_nir, 1.0),
            (SirenRecognizer(), make_siren, 0.70),
            (SiretRecognizer(), make_siret, 0.85),
            (IbanRecognizer(), make_iban_fr, 1.0),
        ):
            value = generator(rng)
            _assert_detection(recognizer, "[" + value + "]", value, score, "checksum")
