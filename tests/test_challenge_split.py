"""Vérifie l'outillage challenge sur des sources temporaires entièrement fictives.

Entrées : Markdown et JSONL créés ici ; moteur de détection simulé.
Sorties : assertions de validation, seuil figé et conservation des résultats.
Aucun fichier réservé du dépôt n'est lu ou évalué par ces tests.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from huisclos.evaluation import run
from huisclos.evaluation.corpus import CorpusDocument, GoldEntity
from huisclos.models import Detection, EntityType, Source
from scripts import build_corpus as builder

pytestmark = pytest.mark.usefixtures("no_network")


def source(directory: Path, split: str, name: str = "Ivo") -> Path:
    """Écrit une courte source temporaire du split demandé et renvoie son chemin."""
    path = directory / f"fixture_{split}.md"
    path.write_text(
        f"---\nid: fixture_{split}\ndoc_type: letter\nsplit: {split}\ntitle: Fiction\n---\n"
        f"[[{name}|PERSON]] confirme.\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def test_challenge_build_is_optional_deterministic_and_validated(tmp_path: Path) -> None:
    """Construit le split seulement s'il existe, puis recharge ses spans et statistiques."""
    dev = source(tmp_path, "dev")
    output = tmp_path / "output"
    builder.build_corpus([dev], output)
    assert not (output / "challenge.jsonl").exists()
    challenge = source(tmp_path, "challenge", "Una")
    builder.build_corpus([dev, challenge], tmp_path / "check", check=True)
    assert not (tmp_path / "check").exists()
    documents = builder.build_corpus([dev, challenge], output)
    saved = (output / "challenge.jsonl").read_bytes()
    assert b"\r" not in saved
    builder.build_corpus([challenge, dev], output)
    assert (output / "challenge.jsonl").read_bytes() == saved
    loaded = run.load_challenge_corpus(output / "challenge.jsonl")
    assert loaded == [doc for doc in documents if doc.split == "challenge"]
    assert loaded[0].split == "challenge"
    assert loaded[0].entities[0].text == loaded[0].text[:3]
    stats = (output / "stats.md").read_text(encoding="utf-8")
    assert "| challenge | 1 | 1 |" in stats
    assert "| Entity type | dev | test | demo | challenge |" in stats


@pytest.mark.parametrize(
    "changes",
    [
        {"split": "dev"},
        {"id": ""},
        {"text": 14},
        {"entities": [{"start": 0, "end": 3, "type": "PERSON", "text": "xyz"}]},
        {"entities": [{"start": -1, "end": 3, "type": "PERSON", "text": "Ivo"}]},
        {"entities": [{"start": 0, "end": 3, "type": "LOCATION", "text": "Ivo"}]},
        {"entities": [{"start": 0, "end": 3, "type": "OTHER", "text": "Ivo"}]},
    ],
)
def test_reserved_loader_preserves_common_validation(
    tmp_path: Path, changes: dict[str, Any]
) -> None:
    """Refuse les mêmes erreurs de contenu et un split usurpé sans afficher les données."""
    record = {
        "id": "fiction",
        "doc_type": "letter",
        "split": "challenge",
        "title": "Fiction",
        "text": "Ivo confirme.",
        "entities": [{"start": 0, "end": 3, "type": "PERSON", "text": "Ivo"}],
    } | changes
    path = tmp_path / "reserved.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r":1: document challenge invalide"):
        run.load_challenge_corpus(path)


def test_challenge_duplicate_ids_and_dev_error_export_are_rejected(tmp_path: Path) -> None:
    """Les identifiants restent uniques et les erreurs détaillées restent réservées à dev."""
    document = run.ChallengeDocument(
        "fixture", "letter", "challenge", "Fiction", "Ivo", [GoldEntity(0, 3, "PERSON", "Ivo")]
    )
    path = tmp_path / "duplicate.jsonl"
    path.write_text((json.dumps(asdict(document)) + "\n") * 2, encoding="utf-8")
    with pytest.raises(ValueError, match=r":2: document challenge invalide"):
        run.load_challenge_corpus(path)
    with pytest.raises(ValueError, match="réservées"):
        run.dev_errors([document], [[]])


def test_challenge_preserves_dev_test_without_loading_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ajoute challenge au seuil enregistré sans changer les sorties ou relire dev et test."""
    corpus, out = tmp_path / "corpus", tmp_path / "results"
    builder.build_corpus(
        [
            source(tmp_path, "dev", "Ivo"),
            source(tmp_path, "test", "Una"),
            source(tmp_path, "challenge", "Lio"),
        ],
        corpus,
    )
    calls: list[tuple[str, float]] = []

    def fake_detect(text: str, config: Any) -> list[Detection]:
        """Enregistre chaque appel et repère le prénom fictif sans modèle."""
        calls.append((text, config.threshold))
        return [Detection(0, 3, EntityType.PERSON, 0.85, Source.NER_SPACY, text[:3])]

    def forbidden_loader(path: Path) -> list[CorpusDocument]:
        """Signale toute tentative de chargement d'un split commun pendant challenge."""
        raise AssertionError(f"Chargement interdit pendant challenge : {path.name}")

    monkeypatch.setattr(run, "detect", fake_detect)
    run.run_evaluation("dev", ["hybrid", "patterns_only"], out, corpus)
    previous = run.run_evaluation("test", ["hybrid", "patterns_only"], out, corpus)
    preserved = {
        name: (out / name).read_bytes()
        for name in ("threshold.json", "threshold_sweep.csv", "errors_dev.csv")
    }
    calls.clear()
    monkeypatch.setattr(run, "load_corpus", forbidden_loader)
    report = run.run_evaluation("challenge", ["hybrid"], out, corpus)
    assert calls == [("Lio confirme.\n", previous["selected_threshold"]["threshold"])]
    assert [row for row in report["metrics_by_type"] if row["split"] != "challenge"] == (
        previous["metrics_by_type"]
    )
    assert {name: (out / name).read_bytes() for name in preserved} == preserved
    assert report["selected_threshold"] == previous["selected_threshold"]
    assert report["threshold_sweep"] == previous["threshold_sweep"]
    assert report["metadata"]["document_counts"] == {"dev": 1, "test": 1, "challenge": 1}
    for name, digest in previous["metadata"]["corpus_sha256"].items():
        assert report["metadata"]["corpus_sha256"][name] == digest
    assert not (out / "errors_challenge.csv").exists()
    summary = (out / "summary.md").read_text(encoding="utf-8")
    assert all(f"| {split} | hybrid |" in summary for split in ("dev", "test", "challenge"))
    saved_rows = (out / "metrics_by_type.csv").read_bytes()
    again = run.run_evaluation("challenge", ["hybrid"], out, corpus)
    assert again["metrics_by_type"] == report["metrics_by_type"]
    assert (out / "metrics_by_type.csv").read_bytes() == saved_rows


def test_challenge_requires_a_saved_consistent_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuse un seuil absent ou divergent avant toute détection et toute écriture de résultat."""
    out = tmp_path / "out"
    with pytest.raises(ValueError, match="threshold.json est absent"):
        run.run_evaluation("challenge", ["hybrid"], out, tmp_path)
    assert not out.exists()
    out.mkdir()
    run.write_json(out / "threshold.json", {"threshold": 0.65})
    run.write_json(out / "results.json", {"selected_threshold": {"threshold": 0.3}})
    with pytest.raises(ValueError, match="seuils différents"):
        run.run_evaluation("challenge", ["hybrid"], out, tmp_path)
    assert sorted(path.name for path in out.iterdir()) == ["results.json", "threshold.json"]
