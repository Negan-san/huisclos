"""Produit des identifiants synthétiques reproductibles, sans données personnelles.

Entrées : générateur random.Random fourni par l'appelant et options de validité.
Sorties : chaînes compactes ou groupées avec des espaces usuels.
Ces valeurs alimentent les tests et la construction du corpus fictif d'évaluation.
"""

import random

from huisclos.detection.checksums import (
    digits_only,
    luhn_is_valid,
    nir_key,
    siren_is_valid,
    siret_is_valid,
)


def _random_digits(rng: random.Random, length: int) -> str:
    """Renvoie length chiffres tirés exclusivement dans rng."""
    return "".join(str(rng.randrange(10)) for _ in range(length))


def _wrong_key(value: str) -> str:
    """Change le dernier chiffre de value pour rendre sa clé fausse."""
    return value[:-1] + str((int(value[-1]) + 1) % 10)


def make_nir(rng: random.Random, valid: bool = True, corsica: str | None = None) -> str:
    """Crée avec rng un NIR ; corsica vaut 2A ou 2B, valid choisit la clé correcte."""
    if corsica not in (None, "2A", "2B"):
        raise ValueError("Le département corse doit être 2A ou 2B.")
    department = corsica or f"{rng.randint(1, 95):02d}"
    body = (
        rng.choice("123478")
        + f"{rng.randrange(100):02d}{rng.randint(1, 12):02d}"
        + department
        + f"{rng.randint(1, 999):03d}{rng.randint(1, 999):03d}"
    )
    value = body + nir_key(body)
    return value if valid else _wrong_key(value)


def make_siren(rng: random.Random, valid: bool = True) -> str:
    """Crée avec rng un SIREN à clé de Luhn correcte ou fausse selon valid."""
    body = str(rng.randint(1, 9)) + _random_digits(rng, 7)
    value = next(body + str(key) for key in range(10) if luhn_is_valid(body + str(key)))
    return value if valid else _wrong_key(value)


def make_siret(rng: random.Random, siren: str | None = None, valid: bool = True) -> str:
    """Crée avec rng un SIRET lié à siren ; refuse un SIREN fourni à clé fausse."""
    company = make_siren(rng) if siren is None else digits_only(siren)
    if not siren_is_valid(company):
        raise ValueError("Le SIREN fourni doit être valide.")
    body = company + _random_digits(rng, 4)
    value = next(body + str(key) for key in range(10) if siret_is_valid(body + str(key)))
    return value if valid else _wrong_key(value)


def make_iban_fr(rng: random.Random, valid: bool = True) -> str:
    """Crée avec rng un IBAN français numérique ; valid choisit sa clé IBAN."""
    bank = _random_digits(rng, 5)
    branch = _random_digits(rng, 5)
    account = _random_digits(rng, 11)
    rib_key = 97 - (89 * int(bank) + 15 * int(branch) + 3 * int(account)) % 97
    body = bank + branch + account + f"{rib_key:02d}"
    key = 98 - int(body + "152700") % 97
    value = f"FR{key:02d}" + body
    if not valid:
        value = value[:3] + str((int(value[3]) + 1) % 10) + value[4:]
    return value


def make_phone_fr(rng: random.Random, mobile: bool = True) -> str:
    """Crée avec rng dix chiffres français ; mobile choisit un préfixe 06 ou 07."""
    return "0" + rng.choice("67" if mobile else "12345") + _random_digits(rng, 8)


def _group(value: str, widths: tuple[int, ...]) -> str:
    """Groupe value selon widths ; refuse une longueur incompatible."""
    compact = digits_only(value)
    if len(compact) != sum(widths):
        raise ValueError("La longueur ne correspond pas au groupement demandé.")
    groups = []
    offset = 0
    for width in widths:
        groups.append(compact[offset : offset + width])
        offset += width
    return " ".join(groups)


def format_nir(value: str) -> str:
    """Renvoie value groupé en 1-2-2-2-3-3-2 caractères."""
    return _group(value, (1, 2, 2, 2, 3, 3, 2))


def format_siren(value: str) -> str:
    """Renvoie les neuf chiffres de value par groupes de trois."""
    return _group(value, (3, 3, 3))


def format_siret(value: str) -> str:
    """Renvoie les quatorze chiffres de value en groupes 3-3-3-5."""
    return _group(value, (3, 3, 3, 5))


def format_iban(value: str) -> str:
    """Renvoie value par groupes de quatre caractères, dernier groupe plus court."""
    compact = digits_only(value)
    return " ".join(compact[index : index + 4] for index in range(0, len(compact), 4))


def format_phone(value: str) -> str:
    """Renvoie les dix chiffres de value par groupes de deux."""
    return _group(value, (2, 2, 2, 2, 2))
