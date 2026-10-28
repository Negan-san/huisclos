"""Décrit les motifs élémentaires des adresses françaises et anglophones.

Entrées : aucune. Sorties : expressions régulières bornées, sans modification du texte ni de
ses positions.
Place dans le pipeline : detection.address_bounds les assemble autour d'ancrages solides
(numéro et type de voie, boîte postale, code postal validé) avant la fusion.
"""

WORD = (
    r"[^\W\d_]{1,40}"
    r"(?:['\u2019-](?:[ \t]*\r?\n[ \t]*)?[^\W\d_]{1,40}){0,4}"
)
# Un libellé de champ ("Tél", "Destinataire :") n'appartient jamais au nom d'une ville.
_LABEL_WORDS = (
    r"(?i:t[eé]l|t[eé]l[eé]phone|fax|portable|mobile|e-?mail|courriel|mail|rcs|siret|siren|"
    r"tva|rg|destinataire|exp[eé]diteur|objet|r[eé]f|date|nom|pr[eé]nom|adresse|ville|phone)"
)
NOT_LABEL = rf"(?!{_LABEL_WORDS}\b)(?![^\W\d_]+\.?[ \t]*:)"
CAPITAL_WORD = (
    rf"(?!(?i:CEDEX)\b){NOT_LABEL}[A-ZÀ-ÖØ-Þ][^\W\d_]{{0,39}}"
    r"(?:['\u2019-][^\W\d_]{1,40}){0,4}"
)
_CITY_PARTICLE = r"(?:sur|sous|en|les|le|la|de|du|aux|lès)"
# Arrondissement écrit après la ville : "Paris 8e", "Lyon 3ème", "Paris 1er".
ARRONDISSEMENT = r"[0-9]{1,2}(?:er|e|ème|eme)(?!\w)"
CITY = (
    rf"{CAPITAL_WORD}(?:[ ]{{1,3}}(?:{_CITY_PARTICLE}[ ]{{1,3}})?{CAPITAL_WORD}){{0,5}}"
    r"(?:[ ]{1,3}(?i:CEDEX)(?:[ ]{1,3}[0-9]{1,2}(?!\w))?)?"
    rf"(?:[ ]{{1,3}}{ARRONDISSEMENT})?"
)
LINE_SPACE = r"(?:[ \t]{1,3}|[ \t]{0,3}\r?\n[ \t]{0,3})"
# Codes postaux français existants : départements 01 à 95, outre-mer 97 et 98.
POSTAL_CODE = r"(?:0[1-9]|[1-8][0-9]|9[0-5]|97|98)[0-9]{3}"
POSTAL_CITY = rf"(?<![\w/]){POSTAL_CODE}{LINE_SPACE}{CITY}(?!\w)"
STREET_TYPE = (
    r"(?:rue|avenue|av\.|boulevard|bd\.?|place|allée|allee|chemin|impasse|quai|cours|"
    r"route|square|villa|passage|voie|venelle|sentier|cité|cite|résidence|residence|lieu-dit|"
    r"hameau|faubourg|esplanade|promenade|rond-point|parvis|sente|ruelle|traverse|montée|"
    r"montee|carrefour|lotissement)"
)
# Numéro, plage ("12-14"), indice (bis, ter, quater ou lettre) et virgule facultative.
STREET_HEAD = (
    r"(?<![\w/])[0-9]{1,5}(?:[ ]?-[ ]?[0-9]{1,5})?"
    r"(?:[ ]{0,3}(?:bis|ter|quater|[A-D])(?![^\W_]))?[ ]{0,3},?[ ]{0,3}"
    rf"{STREET_TYPE}(?!\w)"
)
# Lieu nommé sans numéro, accepté seulement s'il est suivi de sa ligne postale.
NAMED_PLACE = (
    r"(?:lieu-dit|lieudit|hameau|résidence|residence|domaine|quartier|lotissement|"
    r"zone[ ]industrielle|zone[ ]artisanale|zone[ ]d['\u2019]activités?|ZI|ZA|ZAC)(?!\w)"
)
POSTBOX = r"(?<![\w/])(?:BP|CS|TSA)[ ]{0,3}[0-9]{1,6}(?!\w)"
FLOOR = (
    r"(?:[0-9]{1,2}(?:er|e|ème|eme|re)[ ]{1,3}(?:étage|etage)|"
    r"rez-de-chaussée|rez-de-chaussee|RDC)(?!\w)"
)
# Un mot de complément n'avale jamais un code postal : la ligne postale reste reconnue.
_COMPLEMENT_WORD = rf"(?:{WORD}|(?![0-9]{{5}}(?!\w))[A-Z0-9]{{1,6}})"
COMPLEMENT = (
    rf"(?:{POSTBOX}|{FLOOR}|(?:résidence|residence|bâtiment|batiment|bât\.|bât|bat\.|"
    r"immeuble|appartement|appart\.|appt\.?|apt\.?|app\.|étage|etage|escalier|esc\.|"
    r"entrée|entree|porte|tour|bloc|aile|bureau|local|lieu-dit|hameau)"
    rf"[ ]{{1,3}}{_COMPLEMENT_WORD}(?:[ ]{{1,3}}{_COMPLEMENT_WORD}){{0,5}})"
)

# Documents anglais : la voie suit son nom ("17 Kingsmere Road"), le code postal britannique
# ou l'État et le ZIP américains terminent l'adresse.
EN_WORD = r"(?:[A-Z][a-z'\u2019]+(?:-[A-Za-z][a-z'\u2019]*)*|[A-Z]{2,}|[0-9]{1,3}(?:st|nd|rd|th))"
EN_STREET_TYPE = (
    r"(?i:road|rd|street|st|lane|ln|avenue|ave|close|drive|dr|way|court|ct|place|pl|"
    r"crescent|cres|terrace|gardens|grove|square|sq|mews|row|hill|park|walk|parade|"
    r"boulevard|blvd|highway|hwy|parkway|pkwy|circle|cir|trail|green|rise|wharf|quay)\.?"
)
EN_UNIT = r"(?:Flat|Apartment|Apt\.?|Unit|Suite|Ste\.?|Floor|Fl\.?|Building|Bldg\.?|Room|Rm\.?)"
EN_STREET_HEAD = (
    rf"(?<![\w/])(?:{EN_UNIT}[ ]{{1,3}}[A-Z0-9]{{1,6}}[ ]{{0,3}},?[ ]{{0,3}})?"
    r"[0-9]{1,5}[A-Za-z]?(?:-[0-9]{1,5})?[ ]{1,3}"
    rf"(?:{EN_WORD}[ ]{{1,3}}){{1,4}}{EN_STREET_TYPE}"
    r"(?:[ ]{1,3}(?:North|South|East|West|NW|NE|SW|SE))?(?!\w)"
)
EN_COMPLEMENT = rf"(?:{EN_UNIT}[ ]{{1,3}}[A-Z0-9]{{1,6}}|#[ ]?[A-Z0-9]{{1,6}})(?!\w)"
EN_POSTBOX = r"(?<![\w/])(?:P\.?[ ]?O\.?[ ]?Box|POB)[ ]{1,3}[0-9]{1,8}(?!\w)"
_EN_CITY_WORD = (
    r"(?:[A-Z][a-z'\u2019]+(?:-(?:[a-z]+-)*[A-Z][a-z'\u2019]+)*|[A-Z]{2,}(?:-[A-Z]{2,})*)"
)
EN_CITY = (
    rf"{NOT_LABEL}{_EN_CITY_WORD}"
    rf"(?:[ ]{{1,3}}(?:(?:upon|on|in|under|by|le)[ ]{{1,3}})?{NOT_LABEL}{_EN_CITY_WORD}){{0,3}}"
)
UK_POSTCODE = (
    r"(?<![A-Za-z0-9])(?:[A-Z]{1,2}[0-9][A-Z0-9]?[ ]?[0-9][ABD-HJLNP-UW-Z]{2})(?![A-Za-z0-9])"
)
UK_POSTAL = rf"(?:{EN_CITY}[ ]{{0,3}},?[ ]{{1,3}})?{UK_POSTCODE}"
US_STATE = (
    r"(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|"
    r"NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|PR)"
)
US_POSTAL = (
    rf"{EN_CITY}[ ]{{0,3}},?[ ]{{1,3}}{US_STATE}[ ]{{1,3}}[0-9]{{5}}(?:-[0-9]{{4}})?(?![\w-])"
)
