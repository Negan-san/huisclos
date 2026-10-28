"""Teste les coordonnées et dates contextualisées avec des valeurs nouvelles.

Entrées : courriels masqués, postes téléphoniques, naissance et dates ordinaires.
Sorties : assertions de spans exacts et de scores D-07.
Ces tests précèdent l'intégration des motifs dans le pipeline hybride.
"""

import pytest

from huisclos.detection.patterns import BirthDateRecognizer, EmailRecognizer, PhoneFrRecognizer


@pytest.mark.parametrize("value", ["testeur [at] example.org", "TESTEUR@EXAMPLE.COM"])
def test_email_obfuscation_preserves_original_span(value: str) -> None:
    """Inclut la graphie masquée sans normaliser le texte retourné."""
    text = f"Courriel : {value}."
    results = EmailRecognizer().analyze(text, ["EMAIL"])
    assert [(text[r.start : r.end], r.score) for r in results] == [(value, 0.95)]


@pytest.mark.parametrize("value", ["testeur [at] localhost", "testeur..bis [at] example.org"])
def test_invalid_masked_email_is_ignored(value: str) -> None:
    """Conserve les exigences de domaine et de partie locale du courriel standard."""
    assert EmailRecognizer().analyze(value, ["EMAIL"]) == []


@pytest.mark.parametrize("suffix", [" poste 837", " ext. 729", " extension : 7361"])
@pytest.mark.parametrize("phone", ["+33 (0)6 92 73 84 15", "0033692738415", "0692738415"])
def test_phone_extension_is_part_of_the_sensitive_value(phone: str, suffix: str) -> None:
    """Étend le numéro jusqu'au poste annoncé, sans inclure le libellé téléphonique."""
    value = phone + suffix
    text = f"Tél. : {value}, disponible."
    results = PhoneFrRecognizer().analyze(text, ["PHONE"])
    assert [(text[r.start : r.end], r.score) for r in results] == [(value, 0.9)]


@pytest.mark.parametrize(
    "birth", ["né(e) le 8/9/1987", "née le 1er juillet 1982", "date de naissance : 08.09.1987"]
)
def test_birth_context_does_not_spread_to_the_next_date(birth: str) -> None:
    """Une date d'audience proche d'une naissance garde son sens et reste visible."""
    text = birth + "; audience le 12.10.2026."
    results = BirthDateRecognizer().analyze(text, ["BIRTH_DATE"])
    assert len(results) == 1
    assert text[results[0].start : results[0].end] == birth.split(" ")[-1] or (
        text[results[0].start : results[0].end] == "1er juillet 1982"
    )
