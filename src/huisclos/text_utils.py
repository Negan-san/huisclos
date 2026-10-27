"""Outils de texte partagés : repliement sans accents, civilités et formes juridiques.

Entrées : chaînes de caractères. Sorties : chaînes repliées, constantes et tests simples.
Place dans le pipeline : utilisés par la fusion et la propagation des détections, puis par
la pseudonymisation pour comparer des formes écrites différemment.
"""

import re
import unicodedata

# Apostrophe droite, apostrophes typographiques et accent grave employé comme apostrophe.
APOSTROPHES = frozenset("'\u2019\u2018\u02bc`")
# Trait d'union, tirets typographiques et signe moins.
DASHES = frozenset("-\u2010\u2011\u2012\u2013\u2014\u2212")

# Civilités repliées (minuscules, sans accent ni point) : "M.", "Mme", "Maître", "Me"...
CIVILITIES = frozenset(
    {
        "m",
        "mr",
        "mme",
        "mlle",
        "monsieur",
        "madame",
        "mademoiselle",
        "me",
        "maitre",
        "dr",
        "docteur",
        "pr",
        "professeur",
    }
)

# Formes juridiques françaises usuelles, toujours écrites en majuscules dans les actes.
LEGAL_FORMS = frozenset(
    {"SAS", "SASU", "SARL", "EURL", "SA", "SCI", "SNC", "SCP", "SELARL", "SELAS", "SCA", "GIE"}
)

_SPACES = re.compile(r" +")
# Particule élidée en tête d'un nom : "d'", "l'", "qu'", avec toute forme d'apostrophe.
_ELISION = re.compile("^(?:[dDlL]|[qQ]u)[" + "".join(sorted(APOSTROPHES)) + "]")


def fold_char(char: str) -> str:
    """Replie un caractère : minuscule sans accent, apostrophe et tiret unifiés.

    Paramètre : char, un seul caractère.
    Valeur retournée : toujours un seul caractère, pour garder les positions du texte.
    Exemple : fold_char("É") == "e".
    """
    if char in APOSTROPHES:
        return "'"
    if char in DASHES:
        return "-"
    if char.isspace():
        return " "
    decomposed = unicodedata.normalize("NFD", char.lower())
    base = "".join(c for c in decomposed if not unicodedata.combining(c))
    return base[0] if base else char


def fold_same_length(text: str) -> str:
    """Replie chaque caractère sans changer la longueur du texte.

    Les positions d'un motif trouvé dans le résultat valent donc dans le texte d'origine,
    ce dont la propagation a besoin.
    """
    return "".join(fold_char(char) for char in text)


def fold(text: str) -> str:
    """Forme de comparaison : minuscules, sans accents, apostrophes et tirets unifiés.

    Paramètre : text, une chaîne quelconque.
    Valeur retournée : la chaîne repliée, espaces consécutifs réduits à un seul.
    Exemple : fold("  L\u2019Étude   Durand ") == "l'etude durand".
    """
    return _SPACES.sub(" ", fold_same_length(text)).strip()


def is_capitalized_form(word: str) -> bool:
    """Dit si un mot commence par une majuscule (forme "Dupont" ou "DUPONT").

    Paramètre : word, un mot qui peut commencer par une particule élidée ("d'Aubigné").
    Valeur retournée : vrai si sa première lettre, après l'élision, est une majuscule ;
    faux sans lettre.
    Exemple : is_capitalized_form("petit") est faux, is_capitalized_form("Petit") est vrai.
    """
    for char in _ELISION.sub("", word, count=1):
        if char.isalpha():
            return char.isupper()
    return False


def letter_count(text: str) -> int:
    """Renvoie le nombre de lettres de text (chiffres, espaces et ponctuation exclus)."""
    return sum(1 for char in text if char.isalpha())
