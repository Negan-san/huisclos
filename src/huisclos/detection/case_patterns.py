"""Complète les numéros RG par les références de parquet et de pourvoi.

Entrée : texte français avec un libellé de procédure explicite.
Sortie : positions des valeurs sensibles, sans leur libellé.
Les citations de jurisprudence publiée restent visibles avant la revue humaine.
"""

import re
from collections.abc import Iterator

_PROCEDURE = re.compile(
    r"(?<!\w)(?P<label>pourvoi|parquet)"
    r"(?:[ \t]{1,3}(?:n[°o]\.?|num[eé]ro))?[ \t]{0,3}:?[ \t]{0,3}"
    r"(?P<value>[0-9]{2}-[0-9]{2}\.[0-9]{3}|[0-9]{9,14}|[0-9]{2,4}/[0-9]{2,8})"
    r"(?![\w/-]|\.[0-9])",
    re.IGNORECASE,
)
_PUBLISHED = re.compile(r"\bCass\.|\bCour[ \t]+de[ \t]+cassation\b|\bECLI\b|\bBulletin\b", re.I)
_UNPUBLISHED = re.compile(r"\b(?:non[ \t]+publi[eé]e?|in[eé]dite?)\b", re.I)


def procedure_candidates(text: str) -> Iterator[tuple[int, int]]:
    """Renvoie les numéros libellés de text en écartant les citations publiées proches.

    La fenêtre se limite à la ligne courante, 140 caractères avant et 80 après.
    Un pourvoi explicitement inédit reste sensible même si la juridiction est citée.
    Une référence sans libellé n'est jamais repérée par cette règle.
    """
    for match in _PROCEDURE.finditer(text):
        if match["label"].lower() == "pourvoi":
            start = max(text.rfind("\n", 0, match.start()) + 1, match.start() - 140)
            newline = text.find("\n", match.end())
            end = min(newline if newline >= 0 else len(text), match.end() + 80)
            context = text[start:end]
            if _PUBLISHED.search(context) and not _UNPUBLISHED.search(context):
                continue
        yield match.span("value")
