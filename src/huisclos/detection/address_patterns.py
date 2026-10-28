"""Décrit les bornes des adresses françaises complètes et de leurs compléments.

Entrées : motifs assemblés par le reconnaisseur ADDRESS.
Sorties : expressions bornées, sans modification du texte ni de ses positions.
Ces motifs regroupent voie, compléments postaux et ville avant la fusion.
"""

WORD = (
    r"[^\W\d_]{1,40}"
    r"(?:['\u2019-](?:[ \t]*\r?\n[ \t]*)?[^\W\d_]{1,40}){0,4}"
)
CAPITAL_WORD = (
    r"(?!(?i:CEDEX)\b)[A-ZÀ-ÖØ-Þ][^\W\d_]{0,39}"
    r"(?:['\u2019-][^\W\d_]{1,40}){0,4}"
)
CITY = (
    rf"{CAPITAL_WORD}(?:[ ]{{1,3}}(?:{CAPITAL_WORD}|sur|sous|en|les|le|la|de|du|aux)){{0,7}}"
    r"(?:[ ]{1,3}(?i:CEDEX)(?:[ ]{1,3}[0-9]{1,2})?)?"
)
LINE_SPACE = r"(?:[ \t]{1,3}|[ \t]{0,3}\r?\n[ \t]{0,3})"
POSTAL_CITY = rf"[0-9]{{5}}{LINE_SPACE}{CITY}"
STREET_TYPE = (
    r"(?:rue|avenue|av\.|boulevard|bd\.?|place|allée|allee|chemin|impasse|quai|cours|"
    r"route|square|villa|passage|voie|venelle|sentier|cité|cite|résidence|residence|lieu-dit|"
    r"hameau|faubourg|esplanade|promenade)"
)
STREET_START = rf"[0-9]{{1,5}}[ ]{{0,3}}(?:(?:bis|ter|quater)[ ]{{1,3}})?{STREET_TYPE}"
STREET = rf"{STREET_START}[ ]{{1,3}}{WORD}(?:[ ]{{1,3}}{WORD}){{0,5}}"
FULL_STREET = rf"{STREET_START}{LINE_SPACE}{WORD}(?:{LINE_SPACE}{WORD}){{0,5}}"
SEPARATOR = r"[ ,\t\r\n]{1,6}"
POSTBOX = r"(?:BP|CS)[ ]{0,3}[0-9]{1,6}"
COMPLEMENT = (
    rf"(?:{POSTBOX}|(?:résidence|residence|bâtiment|batiment|bât\.|bat\.|immeuble|"
    rf"appartement|app\.|étage|etage|escalier|entrée|entree|porte|lieu-dit|hameau)"
    rf"[ ]{{1,3}}(?:{WORD}|[A-Z0-9]{{1,6}})"
    rf"(?:[ ]{{1,3}}(?:{WORD}|[A-Z0-9]{{1,6}})){{0,5}})"
)
EXPRESSION = (
    rf"(?<![\w/])(?:(?i:{FULL_STREET}(?:{SEPARATOR}{COMPLEMENT}){{0,6}})"
    rf"{SEPARATOR}{POSTAL_CITY}|(?i:{POSTBOX}){SEPARATOR}{POSTAL_CITY}|"
    rf"(?i:{STREET})|{POSTAL_CITY})(?!\w)"
)
