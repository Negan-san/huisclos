"""Vérifie le reconnaisseur CamemBERT facultatif sans accès au réseau.

Entrées : textes fictifs, pipeline simulé et modèle local si disponible.
Sorties : assertions sur les positions, types, probabilités et limites de jetons.
Place dans le pipeline : contrôle de la source NER avant fusion et propagation.
"""

import importlib.util
import os
import re
import subprocess
import sys
import textwrap
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from huisclos.detection import camembert
from huisclos.detection.windows import overlapping_windows

pytestmark = [
    pytest.mark.skipif(
        importlib.util.find_spec("transformers") is None,
        reason="Option transformers absente de cet environnement.",
    ),
    pytest.mark.usefixtures("no_network"),
]


class CharacterTokenizer:
    """Simule un jeton par caractère pour rendre les frontières vérifiables."""

    model_max_length = 512

    def num_special_tokens_to_add(self) -> int:
        """Renvoie les deux jetons réservés au début et à la fin du morceau."""
        return 2

    def __call__(self, text: str, **kwargs: Any) -> dict[str, Any]:
        """Renvoie les jetons et, sur demande, les positions exactes de text."""
        encoded = {"input_ids": list(range(len(text)))}
        if kwargs.get("return_offsets_mapping"):
            encoded["offset_mapping"] = [(index, index + 1) for index in range(len(text))]
        return encoded


class FakePipeline:
    """Simule les sorties agrégées avec une probabilité connue par type."""

    tokenizer = CharacterTokenizer()

    def __call__(self, text: str) -> list[dict[str, Any]]:
        """Détecte seulement les quatre mentions fictives attendues dans text."""
        labels = {"Alice Martin": "PER", "Acme SARL": "ORG", "Lyon": "LOC", "Objet": "MISC"}
        return [
            {"entity_group": label, "start": match.start(), "end": match.end(), "score": 0.93}
            for value, label in labels.items()
            for match in re.finditer(value, text)
        ]


@pytest.fixture
def recognizer(monkeypatch: pytest.MonkeyPatch) -> camembert.CamembertRecognizer:
    """Renvoie un reconnaisseur simulé sans charger de poids ni modifier le cache."""
    monkeypatch.setattr(camembert, "load_pipeline", lambda: FakePipeline())
    return camembert.CamembertRecognizer()


@pytest.fixture
def local_pipeline(no_network: None) -> Iterator[Any]:
    """Charge une seule fois les poids locaux ; ignore proprement un cache absent."""
    loader = camembert.load_pipeline
    try:
        loaded = loader()
    except RuntimeError as error:
        pytest.skip(str(error))
    yield loaded
    loader.cache_clear()


def test_exact_offsets_on_3000_characters(recognizer: camembert.CamembertRecognizer) -> None:
    """Garde les positions après paragraphes, phrases et blancs Unicode sur 3 000 caractères."""
    paragraph = "Alice Martin rencontre Acme SARL à Lyon.\n\n"
    text = (paragraph * 80)[:3000]
    assert len(text) == 3000
    results = recognizer.analyze(text, ["PERSON", "ORGANIZATION", "LOCATION"])
    expected = sorted(
        (match.start(), match.end(), entity_type)
        for value, entity_type in (
            ("Alice Martin", "PERSON"),
            ("Acme SARL", "ORGANIZATION"),
            ("Lyon", "LOCATION"),
        )
        for match in re.finditer(value, text)
    )
    assert sorted((item.start, item.end, item.entity_type) for item in results) == expected
    assert all(item.score == 0.93 for item in results)
    assert all(item.recognition_metadata["huisclos_source"] == "ner_camembert" for item in results)
    assert all(text[item.start : item.end] in paragraph for item in results)


@pytest.mark.parametrize(
    "text",
    ["x" * 3000, "mot " * 1000, "Été\u00a0à Paris.\n\n" * 300, "a" * 510, "a" * 511],
)
def test_windows_cover_text_within_limit(text: str) -> None:
    """Fenêtres de 510 jetons au plus, recouvrantes, du premier au dernier caractère."""
    windows = overlapping_windows(text, CharacterTokenizer())
    assert windows[0].start == 0 and windows[-1].end == len(text)
    assert all(0 < len(window.text) <= 510 for window in windows)
    for left, right in zip(windows, windows[1:], strict=False):
        assert left.end - right.start == 64


def test_types_empty_and_unknown(recognizer: camembert.CamembertRecognizer) -> None:
    """Ignore MISC, les types non demandés et les textes vides."""
    assert recognizer.supported_language == "fr"
    results = recognizer.analyze("Objet Alice Martin, Acme SARL à Lyon.", ["ORGANIZATION"])
    assert [(item.entity_type, item.start, item.end) for item in results] == [
        ("ORGANIZATION", 20, 29)
    ]
    assert recognizer.analyze("   ", ["PERSON"]) == []
    assert recognizer.analyze("Alice Martin", ["EMAIL"]) == []


def test_invalid_spans_ignored(
    recognizer: camembert.CamembertRecognizer, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Écarte les positions négatives, vides et extérieures au morceau."""

    class InvalidPipeline:
        """Produit des positions invalides pour éprouver la conversion Presidio."""

        tokenizer = CharacterTokenizer()

        def __call__(self, text: str) -> list[dict[str, Any]]:
            """Renvoie trois spans invalides à partir de la longueur de text."""
            return [
                {"entity_group": "PER", "start": start, "end": end, "score": 0.9}
                for start, end in [(-1, 3), (2, 2), (0, len(text) + 1)]
            ]

    monkeypatch.setattr(recognizer, "pipeline", InvalidPipeline())
    assert recognizer.analyze("Alice Martin", ["PERSON"]) == []


def test_offline_loading_and_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force les deux variables hors ligne et les deux chargements depuis le cache seul."""
    import transformers

    calls = []

    def fake_load(name: str, **kwargs: Any) -> object:
        """Enregistre les options de chargement et renvoie un objet local fictif complet."""
        calls.append((name, kwargs))
        return SimpleNamespace(vocab_size=32005, config=SimpleNamespace(vocab_size=32005))

    def fake_pipeline(task: str, **kwargs: Any) -> FakePipeline:
        """Contrôle la tâche, l'agrégation et le choix explicite du CPU."""
        assert task == "token-classification"
        assert kwargs["aggregation_strategy"] == "simple"
        assert kwargs["device"] == -1
        return FakePipeline()

    camembert.load_pipeline.cache_clear()
    monkeypatch.setenv("HF_HUB_OFFLINE", "0")
    monkeypatch.setenv("TRANSFORMERS_OFFLINE", "0")
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", fake_load)
    monkeypatch.setattr(transformers.AutoModelForTokenClassification, "from_pretrained", fake_load)
    monkeypatch.setattr(transformers, "pipeline", fake_pipeline)
    try:
        first = camembert.CamembertRecognizer()
        second = camembert.CamembertRecognizer()
        assert first.pipeline is second.pipeline
        assert len(calls) == 2
        assert all(name == camembert.MODEL_NAME for name, _ in calls)
        assert all(
            options == {"local_files_only": True, "trust_remote_code": False}
            for _, options in calls
        )
        assert os.environ["HF_HUB_OFFLINE"] == "1"
        assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
    finally:
        camembert.load_pipeline.cache_clear()


def test_hybrid_does_not_import_transformers() -> None:
    """Vérifie dans un processus neuf que le mode habituel garde l'option paresseuse."""
    code = textwrap.dedent(
        """
        import sys
        import socket
        import importlib.abc

        class MissingTransformers(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == 'transformers' or fullname.startswith('transformers.'):
                    raise ModuleNotFoundError('transformers absent', name=fullname)

        def no_network(*args, **kwargs):
            raise AssertionError('network forbidden')

        sys.meta_path.insert(0, MissingTransformers())
        socket.socket.connect = no_network
        socket.create_connection = no_network
        from huisclos.config import PRESETS
        from huisclos.detection.pipeline import analyzer_for
        analyzer_for(PRESETS['hybrid'])
        assert 'transformers' not in sys.modules
        assert 'huisclos.detection.camembert' not in sys.modules
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "PYTHONPATH": str(Path(camembert.__file__).resolve().parents[2])},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_missing_cache_fails_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explique un cache absent sans tenter de télécharger ni changer de configuration."""
    import transformers

    def missing_model(name: str, **kwargs: Any) -> None:
        """Simule un modèle absent et contrôle le refus des téléchargements."""
        assert kwargs["local_files_only"] is True
        raise OSError("cache absent")

    camembert.load_pipeline.cache_clear()
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", missing_model)
    try:
        with pytest.raises(RuntimeError, match="cache local"):
            camembert.CamembertRecognizer()
    finally:
        camembert.load_pipeline.cache_clear()


def test_incomplete_tokenizer_fails_clearly() -> None:
    """Un tokenizer réduit aux jetons spéciaux (vocabulaire absent) est refusé, pas utilisé."""
    model = SimpleNamespace(config=SimpleNamespace(vocab_size=32005))
    with pytest.raises(RuntimeError, match="incomplet"):
        camembert.check_vocabulary(SimpleNamespace(vocab_size=6), model)
    camembert.check_vocabulary(SimpleNamespace(vocab_size=32005), model)


def test_real_local_model_positions(local_pipeline: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Vérifie sur poids locaux les positions après 512 jetons, fenêtres recouvrantes."""
    monkeypatch.setattr(camembert, "load_pipeline", lambda: local_pipeline)
    recognizer = camembert.CamembertRecognizer()
    text = ("Le contrat est signé. " * 200)[:2950] + "\n\nAlice Martin travaille pour Acme à Paris."
    windows = overlapping_windows(text, local_pipeline.tokenizer)
    assert len(windows) > 1
    assert windows[0].start == 0 and windows[-1].end == len(text)
    assert all(len(local_pipeline.tokenizer(w.text)["input_ids"]) <= 512 for w in windows)
    results = recognizer.analyze(text, ["PERSON", "ORGANIZATION", "LOCATION"])
    assert any(text[item.start : item.end] == "Alice Martin" for item in results)
    assert any(text[item.start : item.end] == "Paris" for item in results)
    assert all(0 <= item.start < item.end <= len(text) for item in results)
    assert all(0 <= item.score <= 1 for item in results)
