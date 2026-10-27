"""Vérifie localement les clés des identifiants français et des IBAN.

Entrées : chaînes avec ou sans séparateurs usuels. Sorties : booléens ou clé NIR.
Ces fonctions pures servent aux reconnaisseurs avant la revue humaine.
Une clé correcte ne prouve ni l'attribution ni l'existence de l'identifiant.
"""

import re

_SEPARATORS = str.maketrans("", "", " \u00a0\u202f.-")
_NIR_BODY = re.compile(
    r"[123478][0-9]{2}(?:0[1-9]|1[0-2]|2[0-9]|3[0-9]|4[0-2]|[5-9][0-9])"
    r"(?:[0-9]{2}|2[AB])[0-9]{6}"
)


def digits_only(value: str) -> str:
    """Retire de value les espaces, points et tirets ; conserve les lettres corses."""
    return value.translate(_SEPARATORS)


def luhn_is_valid(digits: str) -> bool:
    """Renvoie si une chaîne de chiffres ASCII non vide satisfait la clé de Luhn."""
    if not re.fullmatch(r"[0-9]+", digits):
        return False
    total = 0
    # Luhn double un chiffre sur deux depuis la droite, en laissant la clé inchangée.
    for index, character in enumerate(reversed(digits)):
        number = int(character)
        if index % 2:
            number *= 2
            # Soustraire neuf revient à additionner les chiffres du produit à deux chiffres.
            number = number - 9 if number > 9 else number
        total += number
    return total % 10 == 0


def siren_is_valid(value: str) -> bool:
    """Renvoie si value contient neuf chiffres et une clé de Luhn correcte."""
    digits = digits_only(value)
    return len(digits) == 9 and luhn_is_valid(digits)


def siret_is_valid(value: str) -> bool:
    """Vérifie les quatorze chiffres de value, avec la règle spéciale de La Poste."""
    digits = digits_only(value)
    if not re.fullmatch(r"[0-9]{14}", digits):
        return False
    # Le siège conserve Luhn ; les autres établissements de La Poste ont une exception.
    if digits.startswith("356000000") and digits != "35600000000048":
        return sum(map(int, digits)) % 5 == 0
    return luhn_is_valid(digits)


def nir_key(nir13: str) -> str:
    """Calcule la clé à deux chiffres de nir13 ; refuse une structure incorrecte."""
    body = digits_only(nir13).upper()
    if not _NIR_BODY.fullmatch(body):
        raise ValueError("Le NIR sans clé doit avoir une structure plausible sur 13 caractères.")
    # La Corse conserve ses lettres à l'affichage, mais utilise un département numérique.
    numeric = body[:5] + body[5:7].replace("2A", "19").replace("2B", "18") + body[7:]
    return f"{97 - int(numeric) % 97:02d}"


def nir_structure_is_plausible(value: str) -> bool:
    """Vérifie la structure des quinze caractères de value, sans contrôler sa clé."""
    compact = digits_only(value).upper()
    return (
        len(compact) == 15
        and _NIR_BODY.fullmatch(compact[:13]) is not None
        and re.fullmatch(r"[0-9]{2}", compact[13:]) is not None
    )


def nir_is_valid(value: str) -> bool:
    """Renvoie si value a une structure plausible et une clé NIR correcte."""
    compact = digits_only(value).upper()
    return nir_structure_is_plausible(compact) and nir_key(compact[:13]) == compact[13:]


def iban_is_valid(value: str) -> bool:
    """Vérifie le format et le modulo 97 de value, avec 27 caractères pour la France."""
    compact = digits_only(value).upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", compact):
        return False
    if compact.startswith("FR") and len(compact) != 27:
        return False
    # Le calcul progressif évite de construire un grand entier à partir d'un texte libre.
    remainder = 0
    for character in compact[4:] + compact[:4]:
        expanded = character if character.isdigit() else str(ord(character) - ord("A") + 10)
        for digit in expanded:
            remainder = (remainder * 10 + int(digit)) % 97
    return remainder == 1
