"""Fenêtres recouvrantes pour un modèle de jetons à capacité bornée, comme CamemBERT.

Entrées : le texte, un tokenizer rapide qui donne la position de chaque jeton, et un
recouvrement en jetons. Sorties : des fenêtres qui couvrent tout le texte, puis une seule
vue de chaque mention trouvée par plusieurs fenêtres. Place dans le pipeline : utilisé par
detection.camembert avant la fusion ; sans dépendance à transformers, donc testable seul.
"""

import sys
from dataclasses import dataclass
from typing import Any

# Recouvrement entre deux fenêtres voisines, en jetons (D-AF-A1-2). Une mention de 32
# jetons au plus est vue entière, à au moins 16 jetons d'une coupure, par l'une d'elles.
OVERLAP_TOKENS = 64
MODEL_LIMIT = 512


@dataclass(frozen=True)
class Window:
    """Morceau du texte analysé en une fois : positions absolues et coupures éventuelles."""

    start: int
    end: int
    text: str
    cut_left: bool
    cut_right: bool


@dataclass(frozen=True)
class Mention:
    """Entité trouvée dans une fenêtre, en positions absolues du texte complet."""

    start: int
    end: int
    label: str
    score: float
    window: int
    margin: int


def capacity(tokenizer: Any) -> int:
    """Nombre de jetons de texte qu'une fenêtre peut contenir, jetons spéciaux déduits.

    Lève ValueError si le tokenizer ne laisse aucune place au texte.
    """
    limit = min(MODEL_LIMIT, tokenizer.model_max_length) - tokenizer.num_special_tokens_to_add()
    if limit < 1:
        raise ValueError("La limite du tokenizer ne laisse aucune place au texte.")
    return limit


def _count(tokenizer: Any, text: str) -> int:
    """Nombre de jetons de text, sans jetons spéciaux ni troncature."""
    encoded = tokenizer(text, add_special_tokens=False, truncation=False, verbose=False)
    return len(encoded["input_ids"])


def _token_starts(text: str, tokenizer: Any) -> list[int]:
    """Début absolu de chaque jeton du texte complet, calculé en une seule tokenisation."""
    encoded = tokenizer(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
        verbose=False,
    )
    return [int(start) for start, _ in encoded["offset_mapping"]]


def overlapping_windows(text: str, tokenizer: Any, overlap: int = OVERLAP_TOKENS) -> list[Window]:
    """Découpe text en fenêtres de capacité respectée qui se recouvrent de overlap jetons.

    Les fenêtres sont contiguës ou recouvrantes, de 0 à len(text) : tout caractère est
    analysé. Chaque fenêtre est retokenisée seule ; si un découpage différent à sa frontière
    dépasse la capacité, elle est réduite jeton par jeton, sans relire le reste du texte.
    Le recouvrement est plafonné à la moitié de la capacité pour garantir la progression.
    Exemple : 1 000 jetons, capacité 510, recouvrement 64 : fenêtres de jetons [0, 510),
    [446, 956) et [892, 1000).
    """
    if not text:
        return []
    size = capacity(tokenizer)
    overlap = max(0, min(overlap, size // 2))
    starts = _token_starts(text, tokenizer)
    count = len(starts)
    windows: list[Window] = []
    first = 0
    while True:
        last = min(count, first + size)
        while True:
            start = 0 if first == 0 else starts[first]
            end = len(text) if last >= count else starts[last]
            if end > start and _count(tokenizer, text[start:end]) <= size:
                break
            if last - first <= 1:
                raise ValueError("Aucun caractère ne tient dans la capacité du tokenizer.")
            last -= 1
        windows.append(Window(start, end, text[start:end], start > 0, end < len(text)))
        if last >= count:
            return windows
        first = max(first + 1, last - overlap)


def mention(window: Window, index: int, start: int, end: int, label: str, score: float) -> Mention:
    """Convertit une entité relative à la fenêtre en mention absolue, avec sa marge.

    La marge est la distance à la coupure la plus proche ; un bord du texte n'en est pas une.
    """
    left = start if window.cut_left else sys.maxsize
    right = len(window.text) - end if window.cut_right else sys.maxsize
    return Mention(window.start + start, window.start + end, label, score, index, min(left, right))


def best_views(mentions: list[Mention]) -> list[Mention]:
    """Garde une seule vue des mentions qu'ont vues plusieurs fenêtres.

    Entre deux mentions de fenêtres différentes qui se chevauchent, celle qui est la plus
    éloignée d'une coupure l'emporte : elle a le plus de contexte et n'est pas tronquée.
    Aucune mention n'est jamais réunie à une autre : deux noms voisins restent deux noms.
    Les mentions d'une même fenêtre ne s'éliminent pas entre elles.
    """
    ordered = sorted(
        mentions,
        key=lambda m: (-m.margin, -(m.end - m.start), -m.score, m.window, m.start, m.label),
    )
    kept: list[Mention] = []
    for candidate in ordered:
        if not any(
            other.window != candidate.window
            and other.start < candidate.end
            and candidate.start < other.end
            for other in kept
        ):
            kept.append(candidate)
    return sorted(kept, key=lambda m: (m.start, m.end, m.label))
