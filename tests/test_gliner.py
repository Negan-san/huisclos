"""Contrôle le backend GLiNER sans dépendance neuronale ni modèle réel.

Entrées : modèles fictifs, offsets répétés, fenêtres bornées et petits paquets locaux.
Sorties : provenance exacte, projection et refus des paquets ou résultats invalides.
Place : validation indépendante avant les essais CPU hors ligne du paquet complet.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from typing import Any

import pytest

from huisclos.config import DetectionConfig, profile_config
from huisclos.detection import gliner, pipeline
from huisclos.detection.pii_labels import LABELS
from huisclos.models import Source


class Tokenizer:
    """Tokenizer fictif à un jeton par caractère, fenêtres de 256 au plus."""

    model_max_length = 512

    def num_special_tokens_to_add(self) -> int:
        """Réserve les deux jetons spéciaux du contrat des fenêtres."""
        return 2

    def __call__(self, text: str | list[list[str]], **kwargs: Any) -> dict[str, Any]:
        """Retourne une position unique pour chaque caractère."""
        if isinstance(text, list):
            return {"input_ids": [list(range(sum(len(word) for word in row))) for row in text]}
        return {
            "input_ids": list(range(len(text))),
            "offset_mapping": [(i, i + 1) for i in range(len(text))],
        }


class Model:
    """Modèle fictif qui retrouve toutes les répétitions d'un nom sans civilité."""

    def __init__(self) -> None:
        """Expose la capacité et le découpage utilisés avant l'inférence réelle."""
        self.config = SimpleNamespace(max_len=384)
        self.data_processor = SimpleNamespace(
            words_splitter=lambda text: [
                (m.group(), m.start(), m.end()) for m in re.finditer(r"\S+", text)
            ],
            prepare_inputs=lambda texts, labels: ([["header", *row] for row in texts], [1]),
        )
        self.calls: list[dict[str, Any]] = []

    def predict_entities(self, text: str, labels: list[str], **kwargs: Any) -> list[dict[str, Any]]:
        """Retourne des noms aux positions de la fenêtre et une date générique hors politique."""
        self.calls.append({"labels": labels, **kwargs})
        return [
            {"text": m.group(), "start": m.start(), "end": m.end(), "score": 0.9, "label": "person"}
            for m in re.finditer("Adrian Kellaway", text)
        ] + [{"start": 0, "end": 1, "label": "date", "score": 0.99}]


@pytest.fixture
def backend(monkeypatch: pytest.MonkeyPatch) -> Model:
    """Remplace le chargement lourd par un moteur sans réseau ni cache de document."""
    model = Model()
    monkeypatch.setattr(gliner, "prepare", lambda: (model, Tokenizer(), RLock()))
    return model


def test_windows_repetitions_and_provenance(backend: Model, no_network: None) -> None:
    """Une mention coupée et sa répétition gardent leurs vrais offsets et leur source."""
    text = "x" * 248 + " Adrian Kellaway ; Adrian Kellaway"
    results = gliner.analyze(text, 0.7)
    assert [text[r.start : r.end] for r in results] == ["Adrian Kellaway", "Adrian Kellaway"]
    assert [r.start for r in results] == [249, 267]
    assert all(
        r.recognition_metadata["huisclos_source"] == Source.NER_GLINER.value for r in results
    )
    assert all(
        c == {"labels": list(LABELS), "threshold": 0.7, "flat_ner": False, "multi_label": True}
        for c in backend.calls
    )


@pytest.mark.parametrize("change", ["start", "end", "score", "text"])
def test_invalid_predictions_fail_closed(
    backend: Model, monkeypatch: pytest.MonkeyPatch, change: str, no_network: None
) -> None:
    """Un offset, score ou texte incohérent interrompt le contrôle au lieu d'être ignoré."""
    item = {"text": "Adrian Kellaway", "start": 0, "end": 15, "score": 0.9, "label": "person"}
    item[change] = {"start": -1, "end": 99, "score": float("nan"), "text": "wrong"}[change]
    monkeypatch.setattr(backend, "predict_entities", lambda *a, **k: [item])
    with pytest.raises(RuntimeError):
        gliner.analyze("Adrian Kellaway", 0.7)


def test_truncation_is_refused(backend: Model, no_network: None) -> None:
    """La capacité de mots est contrôlée avant l'appel au modèle."""
    backend.config.max_len = 1
    with pytest.raises(RuntimeError, match="troncature"):
        gliner.analyze("Adrian Kellaway", 0.7)
    assert not backend.calls


def test_labels_and_text_must_fit_the_native_encoder(backend: Model, no_network: None) -> None:
    """Le texte seul peut tenir mais son prompt de labels faire déborder les 512 jetons."""
    backend.data_processor.prepare_inputs = lambda *args: ([["x" * 600]], [1])
    with pytest.raises(RuntimeError, match="troncature"):
        gliner.analyze("Adrian Kellaway", 0.7)
    assert not backend.calls


def test_unicode_projection_uses_the_production_pipeline(
    backend: Model, monkeypatch: pytest.MonkeyPatch, no_network: None
) -> None:
    """Les offsets de la vue normalisée reviennent à chaque occurrence canonique."""
    analyzer = SimpleNamespace(analyze=lambda **kwargs: [])
    monkeypatch.setattr(pipeline, "analyzer_for", lambda config: analyzer)
    text = "Adri\u200ban Kellaway ; Adri\u200ban Kellaway"
    config = DetectionConfig(document_language="en", use_gliner=True, use_propagation=False)
    result = pipeline.detect(text, config)
    assert [d.text for d in result] == ["Adri\u200ban Kellaway"] * 2
    assert all(d.source == Source.NER_GLINER for d in result)
    assert [(d.start, d.end) for d in result] == [(0, 16), (19, 35)]


@pytest.fixture
def local_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Crée un paquet fictif vérifiable sans réutiliser les poids réels."""
    folder = tmp_path / "models" / "toy"
    folder.mkdir(parents=True)
    data = b"fictitious model"
    (folder / "weights.bin").write_bytes(data)
    spec = {"toy": ("public/toy", "revision", {"weights.bin": hashlib.sha256(data).hexdigest()})}
    monkeypatch.setattr(gliner, "SNAPSHOTS", spec)
    (tmp_path / "manifest.json").write_text(
        json.dumps({"models": {"toy": {"repo": "public/toy", "revision": "revision"}}}),
        encoding="utf-8",
    )
    monkeypatch.setenv(gliner.ASSETS_ENV, str(tmp_path))
    return tmp_path


def test_package_validation_and_fingerprint(local_package: Path, no_network: None) -> None:
    """Un poids modifié invalide l'identité et son hash ; aucun fallback n'est permis."""
    gliner.check_snapshot(local_package)
    before = gliner.identity()
    (local_package / "models/toy/weights.bin").write_bytes(b"changed model with another size")
    assert gliner.identity() != before
    with pytest.raises(pipeline.ModelUnavailableError) as error:
        gliner.check_snapshot(local_package)
    assert error.value.code == "local_revision"


def test_missing_file_fails_before_loading(local_package: Path, no_network: None) -> None:
    """Un fichier auxiliaire absent refuse le paquet, même avec les poids principaux."""
    (local_package / "models/toy/weights.bin").unlink()
    with pytest.raises(pipeline.ModelUnavailableError) as error:
        gliner.check_snapshot(local_package)
    assert error.value.code == "local_missing"


def test_wrong_stack_is_refused_before_gliner_import(no_network: None) -> None:
    """Une pile non validée n'est pas utilisée en silence pour le renfort."""
    with pytest.raises(pipeline.ModelUnavailableError) as error:
        gliner._load(json.dumps({"root": "missing", "versions": {}}))
    assert error.value.code == "local_dependency"


def test_loading_keeps_room_for_labels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_network: None
) -> None:
    """La limite native reste 512 au chargement, sans la réduire à la fenêtre de texte."""
    folder = tmp_path / "models" / "gliner_multi_pii_v1"
    folder.mkdir(parents=True)
    (folder / "pytorch_model.bin").write_bytes(b"fictitious")
    (folder / "gliner_config.json").write_text("{}", encoding="utf-8")
    tokenizer = Tokenizer()
    tokenizer.vocab_size = 250101
    tokenizer.model_max_length = 10**20
    model = Model()
    model.eval = lambda: None
    model.config.max_width = 12
    model.data_processor.transformer_tokenizer = tokenizer
    model.model = SimpleNamespace(
        token_rep_layer=SimpleNamespace(
            bert_layer=SimpleNamespace(
                model=SimpleNamespace(config=SimpleNamespace(max_position_embeddings=512))
            )
        )
    )

    def load(folder: str, **options: Any) -> Model:
        """Refuse les options autorisant réseau, poids incomplets ou calcul non CPU."""
        assert options == {
            "local_files_only": True,
            "load_tokenizer": True,
            "map_location": "cpu",
            "strict": True,
        }
        return model

    monkeypatch.setitem(
        sys.modules, "gliner", SimpleNamespace(GLiNER=SimpleNamespace(from_pretrained=load))
    )
    monkeypatch.setattr(gliner, "check_snapshot", lambda root: None)
    gliner._load.cache_clear()
    try:
        loaded, actual, _ = gliner._load(
            json.dumps({"root": str(tmp_path), "versions": gliner.VERSIONS})
        )
        assert loaded is model
        assert actual.model_max_length == 512
    finally:
        gliner._load.cache_clear()


def test_public_demo_refuses_gliner_before_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Le mode public refuse le backend lourd même si la session le demande directement."""
    from app import engine

    monkeypatch.setattr(engine, "is_public_demo", lambda: True)
    with pytest.raises(pipeline.ModelUnavailableError) as error:
        engine.prepare_engine(profile_config("enhanced", "en"))
    assert error.value.code == "public_demo"


def test_standard_english_works_without_neural_packages() -> None:
    """Le profil anglais léger reste fonctionnel quand tous les imports lourds sont refusés."""
    code = textwrap.dedent(
        """
        import importlib.abc
        import socket
        import sys

        class MissingHeavy(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.split('.')[0] in {'torch', 'transformers', 'gliner'}:
                    raise ModuleNotFoundError('optional package absent', name=fullname)

        def blocked(*args, **kwargs):
            raise AssertionError('network forbidden')

        sys.meta_path.insert(0, MissingHeavy())
        socket.socket.connect = socket.create_connection = socket.getaddrinfo = blocked
        from huisclos.config import profile_config
        from huisclos.detection.pipeline import detect
        found = detect('Mr Adrian KELLAWAY: adrian@example.org', profile_config('standard', 'en'))
        assert any(d.entity_type.value == 'PERSON' for d in found)
        assert any(d.entity_type.value == 'EMAIL' for d in found)
        assert not {'gliner', 'transformers', 'torch'} & sys.modules.keys()
        assert 'huisclos.detection.gliner' not in sys.modules
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
