"""Complète les numéros RG par les références de parquet et de pourvoi.

Entrée : texte avec un libellé de procédure explicite.
Sortie : positions des valeurs sensibles, sans leur libellé.
Les citations de jurisprudence publiée restent visibles avant la revue humaine.
"""

import re
from collections.abc import Iterator

# Entre un libellé et sa valeur : des blancs et deux fins de ligne au plus, jamais un mot.
LABEL_GAP = r"[ \t]{0,3}(?:\r?\n[ \t]{0,3}){0,2}"

_PROCEDURE = re.compile(
    r"(?<!\w)(?P<label>pourvoi|parquet)"
    rf"(?:{LABEL_GAP}(?:n[°o]\.?|num[eé]ro))?{LABEL_GAP}:?{LABEL_GAP}"
    r"(?P<value>[0-9]{2}-[0-9]{2}\.[0-9]{3}|[0-9]{9,14}|[0-9]{2,4}/[0-9]{2,8})"
    r"(?![\w/-]|\.[0-9])",
    re.IGNORECASE,
)
_PUBLISHED = re.compile(r"\bCass\.|\bCour[ \t]+de[ \t]+cassation\b|\bECLI\b|\bBulletin\b", re.I)
_UNPUBLISHED = re.compile(r"\b(?:non[ \t]+publi[eé]e?|in[eé]dite?)\b", re.I)
# Fin de proposition : point-virgule, ou point après un mot de cinq lettres au moins ou un
# nombre ; "Cass.", "soc." ou "M." sont des abréviations et ne coupent pas la proposition.
_CLAUSE_END = re.compile(r";|(?:[^\W\d_]{5,}|[0-9]+)\.(?=\s)")


def clause_window(text: str, start: int, end: int) -> tuple[int, int]:
    """Bornes de la proposition qui contient [start, end) : ligne, 140 avant, 80 après.

    Paramètres : text, le texte ; start et end, les bornes du numéro.
    Valeur retournée : (début, fin) de la fenêtre où chercher une citation publiée. Elle
    s'arrête aux points-virgules et aux fins de phrase : dans "pourvoi n° 24-10.111 formé
    par M. X ; voir Cass. soc.", la citation suivante ne rend pas le pourvoi public.
    """
    line_start = text.rfind("\n", 0, start) + 1
    newline = text.find("\n", end)
    line_end = newline if newline >= 0 else len(text)
    window_start = max(line_start, start - 140)
    window_end = min(line_end, end + 80)
    for boundary in _CLAUSE_END.finditer(text, window_start, start):
        window_start = boundary.end()
    following = _CLAUSE_END.search(text, end, window_end)
    return window_start, following.start() if following else window_end


def procedure_candidates(text: str) -> Iterator[tuple[int, int]]:
    """Renvoie les numéros libellés de text en écartant les citations publiées proches.

    La fenêtre se limite à la proposition du numéro, dans sa ligne (clause_window).
    Un pourvoi explicitement inédit reste sensible même si la juridiction est citée.
    Une référence sans libellé n'est jamais repérée par cette règle.
    """
    for match in _PROCEDURE.finditer(text):
        if match["label"].lower() == "pourvoi":
            context = text[slice(*clause_window(text, match.start(), match.end()))]
            if _PUBLISHED.search(context) and not _UNPUBLISHED.search(context):
                continue
        yield match.span("value")
