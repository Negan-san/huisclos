"""Vérifie les fenêtres recouvrantes et la sélection des mentions, sans modèle réel.

Entrées : textes fictifs, faux tokenizer à faible capacité et faux modèle qui ne reconnaît
un nom que s'il est entier dans sa fenêtre. Sorties : assertions sur la couverture, la
capacité, la progression, les positions absolues et l'unicité des mentions.
"""

import re
from typing import Any

import pytest

from huisclos.detection import camembert
from huisclos.detection.windows import (
    Window,
    best_views,
    capacity,
    mention,
    overlapping_windows,
)

NAMES = ("Paul Martin", "Marie Durand", "Élodie Nuñez")


class PieceTokenizer:
    """Faux tokenizer : morceaux de trois lettres au plus, ponctuation seule, blancs ignorés.

    prefix ajoute un jeton vide en tête de chaque appel, comme le préfixe de sentencepiece :
    une fenêtre retokenisée compte alors un jeton de plus que sa tranche.
    """

    def __init__(self, max_length: int = 12, prefix: bool = False) -> None:
        """Fixe la capacité (deux jetons spéciaux déduits) et le jeton de préfixe."""
        self.model_max_length = max_length
        self.prefix = prefix
        self.characters_read = 0

    def num_special_tokens_to_add(self) -> int:
        """Deux jetons réservés, comme CamemBERT."""
        return 2

    def __call__(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Renvoie les jetons et, sur demande, leurs positions dans text."""
        self.characters_read += len(text)
        spans = [(0, 0)] if self.prefix else []
        for match in re.finditer(r"\w+|[^\w\s]", text):
            for start in range(match.start(), match.end(), 3):
                spans.append((start, min(start + 3, match.end())))
        encoded: dict[str, Any] = {"input_ids": list(range(len(spans)))}
        if kwargs.get("return_offsets_mapping"):
            encoded["offset_mapping"] = spans
        return encoded


class WholeNameModel:
    """Faux pipeline : un nom n'est reconnu que s'il est entier dans le texte reçu.

    truncated reconnaît aussi un début de nom coupé à la fin de la fenêtre ("Paul Mar").
    """

    def __init__(self, tokenizer: PieceTokenizer, truncated: bool = False) -> None:
        """Associe le tokenizer et choisit le comportement aux coupures."""
        self.tokenizer = tokenizer
        self.truncated = truncated

    def __call__(self, text: str) -> list[dict[str, Any]]:
        """Renvoie les noms entiers trouvés, et éventuellement un nom tronqué en fin."""
        found = [
            {"entity_group": "PER", "start": m.start(), "end": m.end(), "score": 0.9}
            for name in NAMES
            for m in re.finditer(re.escape(name), text)
        ]
        if self.truncated:
            for name in NAMES:
                for size in range(4, len(name)):
                    if text.endswith(name[:size]):
                        start = len(text) - size
                        found.append(
                            {"entity_group": "PER", "start": start, "end": len(text), "score": 0.6}
                        )
        return found


def recognizer_for(monkeypatch: pytest.MonkeyPatch, model: Any) -> camembert.CamembertRecognizer:
    """Reconnaisseur CamemBERT branché sur un faux pipeline, sans poids ni réseau."""
    monkeypatch.setattr(camembert, "load_pipeline", lambda: model)
    return camembert.CamembertRecognizer()


def expected_names(text: str) -> list[tuple[int, int]]:
    """Positions attendues de chaque nom fictif dans le texte complet."""
    return sorted(
        (m.start(), m.end()) for name in NAMES for m in re.finditer(re.escape(name), text)
    )


@pytest.mark.parametrize(
    "text",
    [
        "a",
        "x" * 300,
        "mot " * 200,
        "Été\u00a0à Paris.\n\n" * 40,
        "  début et fin avec blancs  ",
        "abc" * 10,
        "abc" * 11,
    ],
)
@pytest.mark.parametrize("prefix", [False, True])
def test_windows_cover_text_within_capacity(text: str, prefix: bool) -> None:
    """Tout caractère est couvert, chaque fenêtre tient dans la capacité et progresse."""
    tokenizer = PieceTokenizer(prefix=prefix)
    windows = overlapping_windows(text, tokenizer, overlap=4)
    assert windows[0].start == 0 and windows[-1].end == len(text)
    for window in windows:
        assert window.text == text[window.start : window.end]
        assert len(tokenizer(window.text)["input_ids"]) <= capacity(tokenizer)
    for left, right in zip(windows, windows[1:], strict=False):
        assert left.start < right.start <= left.end
        assert right.start < left.end, "deux fenêtres voisines doivent se recouvrir"
    assert not windows[0].cut_left and not windows[-1].cut_right


def test_empty_text_and_capacity_errors() -> None:
    """Texte vide sans fenêtre ; tokenizer sans place ou caractère trop gros : erreur claire."""
    assert overlapping_windows("", PieceTokenizer()) == []
    with pytest.raises(ValueError, match="aucune place"):
        overlapping_windows("Paul", PieceTokenizer(max_length=2))

    class Exploding(PieceTokenizer):
        """Chaque caractère coûte deux jetons une fois isolé : rien ne tient en capacité 1."""

        def __call__(self, text: str, **kwargs: Any) -> dict[str, Any]:
            """Double les jetons des textes retokenisés seuls."""
            encoded = super().__call__(text, **kwargs)
            if not kwargs.get("return_offsets_mapping"):
                encoded["input_ids"] = encoded["input_ids"] * 2
            return encoded

    with pytest.raises(ValueError, match="capacité"):
        overlapping_windows("abc", Exploding(max_length=3))


def test_overlap_is_bounded_and_progress_guaranteed() -> None:
    """Un recouvrement trop grand est plafonné à la moitié de la capacité."""
    text = "abc " * 40
    windows = overlapping_windows(text, PieceTokenizer(), overlap=1000)
    starts = [window.start for window in windows]
    assert starts == sorted(set(starts))
    assert len(windows) <= 40 // 5 + 1


def test_tokenization_cost_is_linear() -> None:
    """Le texte complet est lu une fois, puis chaque fenêtre seule : coût linéaire."""
    tokenizer = PieceTokenizer(max_length=66)
    text = "Paul Martin signe le bail. " * 400
    overlapping_windows(text, tokenizer, overlap=16)
    assert tokenizer.characters_read < 3 * len(text)


@pytest.mark.parametrize("shift", range(0, 12))
def test_name_across_a_cut_is_found_once_with_exact_offsets(
    monkeypatch: pytest.MonkeyPatch, shift: int
) -> None:
    """Un nom à cheval sur une coupure est vu entier par la fenêtre suivante, une seule fois."""
    text = "x " * shift + "abc " * 3 + "Paul Martin et Marie Durand " + "fin " * 3
    tokenizer = PieceTokenizer()
    recognizer = recognizer_for(monkeypatch, WholeNameModel(tokenizer))
    results = recognizer.analyze(text, ["PERSON"])
    assert sorted((r.start, r.end) for r in results) == expected_names(text)
    assert {text[r.start : r.end] for r in results} == {"Paul Martin", "Marie Durand"}


def test_without_overlap_a_cut_name_is_missed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Témoin : sans recouvrement, le faux modèle perd le nom coupé ; avec, il le trouve."""
    text = "abc " * 7 + "Paul Martin fin"
    tokenizer = PieceTokenizer()
    windows = overlapping_windows(text, tokenizer, overlap=0)
    assert "Paul Mar" in windows[0].text
    assert not any("Paul Martin" in window.text for window in windows)
    results = recognizer_for(monkeypatch, WholeNameModel(tokenizer)).analyze(text, ["PERSON"])
    assert [(r.start, r.end) for r in results] == [(28, 39)]


@pytest.mark.parametrize("truncated", [False, True])
def test_repetitions_unicode_and_text_edges(
    monkeypatch: pytest.MonkeyPatch, truncated: bool
) -> None:
    """Répétitions, noms au tout début et à la fin, Unicode : chaque nom une fois, exact."""
    text = "Élodie Nuñez\u00a0: " + "Paul Martin, Marie Durand. " * 15 + "Élodie Nuñez"
    tokenizer = PieceTokenizer(max_length=14)
    model = WholeNameModel(tokenizer, truncated=truncated)
    results = recognizer_for(monkeypatch, model).analyze(text, ["PERSON"])
    assert sorted((r.start, r.end) for r in results) == expected_names(text)
    assert all(r.score == 0.9 for r in results)


def test_best_view_prefers_the_window_far_from_a_cut() -> None:
    """La vue entière loin d'une coupure bat la vue tronquée ; deux noms voisins restent deux."""
    left = Window(0, 20, "x" * 20, False, True)
    right = Window(10, 40, "x" * 30, True, False)
    truncated = mention(left, 0, 12, 20, "PERSON", 0.6)
    whole = mention(right, 1, 2, 13, "PERSON", 0.9)
    neighbour = mention(right, 1, 14, 26, "PERSON", 0.9)
    assert truncated.margin == 0 and whole.margin == 2
    assert best_views([truncated, whole, neighbour]) == [whole, neighbour]
    assert mention(left, 0, 0, 4, "PERSON", 0.9).margin == 16
    whole_text = Window(0, 20, "x" * 20, False, False)
    assert mention(whole_text, 0, 0, 4, "PERSON", 0.9).margin > 1000, (
        "un bord n'est pas une coupure"
    )
