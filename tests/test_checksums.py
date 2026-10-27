"""Teste les clés et les générateurs sur des valeurs exclusivement synthétiques.

Entrées : graines fixes, identifiants générés et pièges de format.
Sorties : assertions locales, comparées aux oracles python-stdnum installés.
Ces tests protègent la première étape de détection et le corpus d'évaluation.
"""

import random
from collections.abc import Callable

import pytest
from stdnum import iban
from stdnum.fr import nir, siren, siret

from huisclos.detection.checksums import (
    digits_only,
    iban_is_valid,
    luhn_is_valid,
    nir_is_valid,
    nir_key,
    nir_structure_is_plausible,
    siren_is_valid,
    siret_is_valid,
)
from huisclos.evaluation.synthetic_ids import (
    format_iban,
    format_nir,
    format_phone,
    format_siren,
    format_siret,
    make_iban_fr,
    make_nir,
    make_phone_fr,
    make_siren,
    make_siret,
)


@pytest.mark.parametrize("valid", [True, False])
@pytest.mark.parametrize(
    ("generator", "validator", "oracle", "formatter"),
    [
        (make_nir, nir_is_valid, nir.is_valid, format_nir),
        (make_siren, siren_is_valid, siren.is_valid, format_siren),
        (make_siret, siret_is_valid, siret.is_valid, format_siret),
        (make_iban_fr, iban_is_valid, iban.is_valid, format_iban),
    ],
)
def test_generated_identifiers_match_stdnum(
    generator: Callable[..., str],
    validator: Callable[[str], bool],
    oracle: Callable[[str], bool],
    formatter: Callable[[str], str],
    valid: bool,
) -> None:
    """Compare 500 valeurs par type et validité, compactes et groupées, à l'oracle."""
    rng = random.Random(11027)
    for _ in range(500):
        value = generator(rng, valid=valid)
        assert validator(value) == oracle(value) == valid
        assert validator(formatter(value)) == oracle(formatter(value)) == valid


@pytest.mark.parametrize("department", ["2A", "2B"])
def test_corsican_nir_matches_oracle(department: str) -> None:
    """Vérifie les deux conversions corses sur des NIR synthétiques groupés."""
    rng = random.Random(111)
    for _ in range(500):
        value = make_nir(rng, corsica=department)
        assert value[5:7] == department
        assert nir_is_valid(format_nir(value)) == nir.is_valid(value) is True
        assert nir_key(value[:13]) == nir.calc_check_digits(value)


@pytest.mark.parametrize("month", ["01", "12", "20", "29", "30", "42", "50", "99"])
@pytest.mark.parametrize("sex", ["1", "2", "3", "4", "7", "8"])
def test_nir_special_structures(month: str, sex: str) -> None:
    """Accepte les sexes et les mois particuliers expressément prévus par le contrat."""
    body = sex + "85" + month + "2A001001"
    value = body + nir_key(body)
    assert nir_is_valid(value)
    assert nir_structure_is_plausible(value[:-2] + "00")
    assert not nir_is_valid(value[:-2] + "00")


@pytest.mark.parametrize(
    "body",
    [
        "585032A001001",
        "185032A0010011",
        "185002A001001",
        "185132A001001",
        "185432A001001",
        "185492A001001",
        "185032C001001",
        "18503AA001001",
    ],
)
def test_nir_bad_structure(body: str) -> None:
    """Refuse les longueurs, départements, sexes et mois hors du contrat."""
    assert not nir_structure_is_plausible(body + "01")
    assert not nir_is_valid(body + "01")
    with pytest.raises(ValueError):
        nir_key(body)


def test_separators_and_luhn() -> None:
    """Retire seulement les séparateurs prévus et refuse les chiffres non ASCII."""
    assert digits_only("1 2\u00a03\u202f4.5-6A") == "123456A"
    assert digits_only("1/2\t3") == "1/2\t3"
    assert luhn_is_valid("79927398713")
    for value in ("", "79927398714", "123 456", "12A", "１２３", "123\n"):
        assert not luhn_is_valid(value)


@pytest.mark.parametrize("validator", [siren_is_valid, siret_is_valid, nir_is_valid, iban_is_valid])
@pytest.mark.parametrize("value", ["", "ABC", "123", "0" * 35, "１２３４５６７８９"])
def test_bad_identifiers(validator: Callable[[str], bool], value: str) -> None:
    """Refuse les formats sans rapport avec les identifiants attendus."""
    assert not validator(value)


def test_la_poste_exception() -> None:
    """Vérifie la somme spéciale de La Poste et le cas du siège conservant Luhn."""
    rng = random.Random(110)
    for _ in range(500):
        value = make_siret(rng, siren="356000000")
        assert sum(map(int, value)) % 5 == 0
        assert siret_is_valid(value) == siret.is_valid(value) is True
        invalid = value[:-1] + str((int(value[-1]) + 1) % 10)
        assert not siret_is_valid(invalid)
        assert not siret.is_valid(invalid)
    assert siret_is_valid("35600000000048")


def test_iban_boundaries() -> None:
    """Vérifie les longueurs du contrat IBAN, indépendantes d'un registre de pays."""
    for country, length in [("FR", 27), ("ZZ", 15), ("ZZ", 34)]:
        body = "1" * (length - 4)
        expanded_country = "".join(str(ord(letter) - 55) for letter in country)
        key = 98 - int(body + expanded_country + "00") % 97
        assert iban_is_valid(f"{country}{key:02d}{body}")
    for value in (
        "FR" + "0" * 24,
        "FR" + "0" * 26,
        "AA00" + "0" * 10,
        "AA00" + "0" * 31,
        "1A00" + "0" * 20,
        "AAAA" + "0" * 20,
    ):
        assert not iban_is_valid(value)


@pytest.mark.parametrize(
    "generator", [make_nir, make_siren, make_siret, make_iban_fr, make_phone_fr]
)
def test_generators_are_deterministic(generator: Callable[..., str]) -> None:
    """Vérifie que chaque générateur dépend uniquement du random.Random fourni."""
    first, second = random.Random(11), random.Random(11)
    assert [generator(first) for _ in range(20)] == [generator(second) for _ in range(20)]


def test_generators_options_and_formats() -> None:
    """Vérifie le rattachement SIRET, les groupements et les erreurs d'options."""
    rng = random.Random(11)
    company = make_siren(rng)
    assert make_siret(rng, siren=format_siren(company)).startswith(company)
    assert format_nir("185032A00100101") == "1 85 03 2A 001 001 01"
    assert format_siren("123456789") == "123 456 789"
    assert format_siret("12345678900001") == "123 456 789 00001"
    assert format_iban("FR001234567") == "FR00 1234 567"
    assert format_phone("0612345678") == "06 12 34 56 78"
    for mobile in (True, False):
        phone = make_phone_fr(rng, mobile=mobile)
        assert len(phone) == 10 and phone.isascii() and phone.isdigit()
        assert phone[:2] in (["06", "07"] if mobile else ["01", "02", "03", "04", "05"])
    with pytest.raises(ValueError):
        make_nir(rng, corsica="2C")
    with pytest.raises(ValueError):
        make_siret(rng, siren="123456789")
    for formatter in (format_nir, format_siren, format_siret, format_phone):
        with pytest.raises(ValueError):
            formatter("123")
