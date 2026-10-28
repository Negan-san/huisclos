"""Outils de texte partagés : repliement sans accents, civilités, formes juridiques, dates.

Entrées : chaînes de caractères. Sorties : chaînes repliées, constantes et tests simples.
Place dans le pipeline : utilisés par la fusion et la propagation des détections, puis par
la pseudonymisation pour comparer des formes écrites différemment.
"""

import re
import unicodedata
from datetime import date

# Apostrophe droite, apostrophes typographiques et accent grave employé comme apostrophe.
APOSTROPHES = frozenset("'\u2019\u2018\u02bc`")
# Trait d'union, tirets typographiques et signe moins.
DASHES = frozenset("-\u2010\u2011\u2012\u2013\u2014\u2212")

# Civilités repliées (minuscules, sans accent ni point) : "M.", "Mme", "Maître", "Me"...
# Les civilités anglaises restent hors du span comme les françaises (D-09, D-AF-A2-6).
CIVILITIES = frozenset(
    {
        "m",
        "mm",
        "mmes",
        "messieurs",
        "mesdames",
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
        "mrs",
        "ms",
        "miss",
        "mx",
        "prof",
        "sir",
        "dame",
        "lady",
        "lord",
    }
)

# Formes juridiques usuelles, en casse exacte : françaises, toujours en majuscules dans les
# actes, puis anglo-saxonnes, qui figurent aussi dans des contrats français.
LEGAL_FORMS = frozenset(
    {"SAS", "SASU", "SARL", "EURL", "SA", "SCI", "SNC", "SCP", "SELARL", "SELAS", "SCA", "GIE"}
    | {"Ltd", "LTD", "Limited", "LIMITED", "LLP", "LLC", "Inc", "INC", "PLC", "plc", "Plc"}
    | {"Corp", "CORP", "Corporation", "CORPORATION"}
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


def full_year(year: str) -> int:
    """Année sur quatre chiffres : "81" donne 1981 et "08" donne 2008 (pivot à 30)."""
    value = int(year)
    if len(year) == 2:
        return value + (2000 if value <= 30 else 1900)
    return value


def is_calendar_date(year: int, month: int, day: int) -> bool:
    """Vrai si le jour existe dans le calendrier ("31/02/1990" n'existe pas)."""
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True
