"""Vérifie les métriques et rapports sur des spans fictifs sans charger de modèle.

Entrées : petits exemples construits à la main et corpus temporaires synthétiques.
Sorties : assertions sur les comptes, la fuite, le seuil et les fichiers produits.
Place dans le pipeline : validation indépendante de l'évaluation locale.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from huisclos.evaluation import run
from huisclos.evaluation.corpus import CorpusDocument, GoldEntity
from huisclos.evaluation.metrics import Counts, Evaluation, match_entities, uncovered_characters
from huisclos.models import Detection, EntityType, Source

pytestmark = pytest.mark.usefixtures("no_network")


def gold(start: int, end: int, kind: str = "PERSON") -> GoldEntity:
    """Construit une référence fictive du type demandé sur le span fourni."""
    return GoldEntity(start, end, EntityType(kind), "x" * (end - start))


def prediction(start: int, end: int, kind: str = "PERSON") -> Detection:
    """Construit une prédiction fictive sans reconnaisseur ni modèle."""
    return Detection(start, end, EntityType(kind), 0.8, Source.MANUAL, "x" * (end - start))


def metric(evaluation: Evaluation, mode: str, kind: str = "micro") -> dict[str, Any]:
    """Extrait la ligne du mode et du type demandés dans les résultats."""
    return next(row for row in evaluation.rows() if row["mode"] == mode and row["type"] == kind)


def test_hand_calculated_exact_partial_and_leakage() -> None:
    """Compare les comptes et caractères manquants à un exemple de seize caractères."""
    references = [gold(0, 4), gold(6, 10), gold(12, 16, "EMAIL"), gold(18, 22, "PHONE")]
    predictions = [
        prediction(0, 4),
        prediction(6, 9),
        prediction(12, 16, "PHONE"),
        prediction(24, 26),
    ]
    evaluation = Evaluation()
    evaluation.add_document(references, predictions)
    exact = metric(evaluation, "exact")
    partial = metric(evaluation, "partial")
    assert (exact["tp"], exact["fp"], exact["fn"]) == (1, 3, 3)
    assert (partial["tp"], partial["fp"], partial["fn"]) == (2, 2, 2)
    for name in ("precision", "recall", "f1", "f2"):
        assert exact[name] == pytest.approx(0.25)
        assert partial[name] == pytest.approx(0.5)
    for row in (exact, partial):
        assert row["leaked_characters"] == 5
        assert row["reference_characters"] == 16
        assert row["leak_rate"] == pytest.approx(5 / 16)
        assert row["exposed_entities"] == 1
    assert metric(evaluation, "partial", "PERSON")["leak_rate"] == pytest.approx(1 / 8)
    assert metric(evaluation, "partial", "EMAIL")["recall"] == 0
    assert metric(evaluation, "partial", "EMAIL")["leak_rate"] == 0
    assert metric(evaluation, "partial", "PHONE")["exposed_entities"] == 1


def test_f2_weights_false_negatives_four_times() -> None:
    """Vérifie F2 = 5 VP / (5 VP + FP + 4 FN) avec des comptes asymétriques."""
    row = Counts(tp=2, fp=1, fn=3).scores()
    assert row["precision"] == pytest.approx(2 / 3)
    assert row["recall"] == pytest.approx(2 / 5)
    assert row["f1"] == pytest.approx(1 / 2)
    assert row["f2"] == pytest.approx(10 / 23)


def test_one_prediction_covering_two_references_matches_largest_overlap() -> None:
    """Une grande prédiction protège deux références mais n'en valide qu'une."""
    references = [gold(0, 3), gold(5, 11)]
    predictions = [prediction(0, 11)]
    assert match_entities(references, predictions, "partial") == [(1, 0)]
    evaluation = Evaluation()
    evaluation.add_document(references, predictions)
    row = metric(evaluation, "partial")
    assert (row["tp"], row["fp"], row["fn"]) == (1, 0, 1)
    assert row["leak_rate"] == 0
    assert row["exposed_entities"] == 0


def test_reference_takes_greatest_overlap_only_once() -> None:
    """Deux candidats sur la même référence laissent le moins couvrant en FP."""
    references = [gold(0, 10)]
    predictions = [prediction(0, 3), prediction(3, 10)]
    assert match_entities(references, predictions, "partial") == [(0, 1)]
    assert uncovered_characters(references[0], predictions) == 0


def test_overlapping_predictions_do_not_double_count_coverage() -> None:
    """La couverture est une union d'intersections, même avec des doublons."""
    predictions = [prediction(1, 6), prediction(4, 8), prediction(1, 6, "EMAIL")]
    assert uncovered_characters(gold(0, 10), predictions) == 3


def test_touching_spans_do_not_match_or_cover() -> None:
    """Deux spans qui ne partagent qu'une borne n'ont aucun caractère commun."""
    assert match_entities([gold(0, 3)], [prediction(3, 6)], "partial") == []
    assert uncovered_characters(gold(0, 3), [prediction(3, 6)]) == 3


def test_same_boundaries_wrong_type_protect_without_recall() -> None:
    """Un mauvais type protège les caractères mais produit un FP et un FN."""
    evaluation = Evaluation()
    evaluation.add_document([gold(0, 5)], [prediction(0, 5, "ORGANIZATION")])
    for mode in ("exact", "partial"):
        row = metric(evaluation, mode)
        assert (row["tp"], row["fp"], row["fn"]) == (0, 1, 1)
        assert row["recall"] == row["leak_rate"] == row["exposed_entities"] == 0


def test_excluded_types_are_not_scored_or_used_for_coverage() -> None:
    """LOCATION et CUSTOM sont hors du périmètre, y compris pour la couverture."""
    evaluation = Evaluation()
    evaluation.add_document(
        [gold(0, 3), gold(4, 7, "CUSTOM")],
        [prediction(0, 3, "LOCATION"), prediction(4, 7, "CUSTOM")],
    )
    row = metric(evaluation, "partial")
    assert (row["tp"], row["fp"], row["fn"]) == (0, 0, 1)
    assert row["leak_rate"] == row["exposed_entities"] == 1
    assert row["reference_characters"] == 3
    assert match_entities([gold(0, 3, "CUSTOM")], [prediction(0, 3, "CUSTOM")], "exact") == []


def test_macro_uses_fixed_types_and_micro_sums_counts() -> None:
    """La macro moyenne les onze types ; le micro cumule les comptes."""
    evaluation = Evaluation()
    evaluation.add_document([gold(0, 3)], [prediction(0, 3)])
    macro = metric(evaluation, "exact", "macro")
    assert macro["tp"] == pytest.approx(1 / 11)
    assert macro["f2"] == pytest.approx(1 / 11)
    assert metric(evaluation, "exact")["f2"] == 1


def test_documents_never_match_each_other() -> None:
    """Des positions identiques dans deux documents ne créent pas de VP."""
    evaluation = Evaluation()
    evaluation.add_document([gold(0, 3)], [])
    evaluation.add_document([], [prediction(0, 3)])
    assert metric(evaluation, "partial")["tp"] == 0
    assert metric(evaluation, "partial")["fp"] == 1
    assert metric(evaluation, "partial")["fn"] == 1


def test_empty_evaluation_and_invalid_mode() -> None:
    """Les divisions vides valent zéro et un mode inconnu est refusé."""
    assert all(value == 0 for value in Counts().scores().values())
    assert metric(Evaluation(), "partial")["f2"] == 0
    with pytest.raises(ValueError, match="Mode"):
        match_entities([], [], "unknown")


def test_matching_ties_follow_positions() -> None:
    """À recouvrement égal, la référence la plus à gauche gagne."""
    assert match_entities([gold(4, 7), gold(0, 3)], [prediction(0, 7)], "partial") == [(1, 0)]


def test_threshold_tie_prefers_lowest_and_rejects_empty() -> None:
    """La priorité au rappel départage les F2 identiques par le seuil le plus bas."""
    assert (
        run.choose_threshold(
            [
                {"threshold": 0.55, "f2": 0.8},
                {"threshold": 0.3, "f2": 0.8},
                {"threshold": 0.4, "f2": 0.7},
            ]
        )
        == 0.3
    )
    with pytest.raises(ValueError, match="vide"):
        run.choose_threshold([])
    assert run.THRESHOLDS == tuple(round(0.3 + 0.05 * index, 2) for index in range(14))


def synthetic_document(split: str = "dev") -> CorpusDocument:
    """Construit un document temporaire, sans accès au vrai corpus test."""
    return CorpusDocument(
        "fiction",
        "letter",
        split,
        "Fiction",
        "Ada writes.",
        [GoldEntity(0, 3, EntityType.PERSON, "Ada")],
    )


def synthetic_corpus(path: Path, split: str = "dev") -> Path:
    """Écrit un seul document fictif au format du chargeur dans un dossier temporaire."""
    path.mkdir(parents=True, exist_ok=True)
    record = {
        "id": "fiction",
        "doc_type": "letter",
        "split": split,
        "title": "Fiction",
        "text": "Ada writes.",
        "entities": [{"start": 0, "end": 3, "type": "PERSON", "text": "Ada"}],
    }
    (path / f"{split}.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    return path


def test_dev_runner_uses_real_thresholds_and_deterministic_csv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deux passages sans modèle donnent les mêmes CSV et balayent via detect."""
    calls = []

    def fake_detect(text: str, config: Any) -> list[Detection]:
        """Simule une détection qui disparaît strictement au-dessus de 0,55."""
        calls.append((text, config.threshold))
        return [prediction(0, 3)] if config.threshold <= 0.55 else []

    monkeypatch.setattr(run, "detect", fake_detect)
    corpus = synthetic_corpus(tmp_path / "corpus")
    out = tmp_path / "results"
    report = run.run_evaluation("dev", ["hybrid", "patterns_only"], out, corpus)
    assert report["selected_threshold"] == {"threshold": 0.3, "criterion": run.CRITERION}
    assert set(threshold for _, threshold in calls) == set(run.THRESHOLDS)
    assert len(calls) == 15
    assert report["metadata"]["corpus_sha256"].keys() == {"dev.jsonl"}
    assert report["metadata"]["versions"]["python"]
    before = {path.name: path.read_bytes() for path in out.glob("*.csv")}
    run.run_evaluation("dev", ["hybrid", "patterns_only"], out, corpus)
    assert before == {path.name: path.read_bytes() for path in out.glob("*.csv")}
    assert set(before) == {"metrics_by_type.csv", "threshold_sweep.csv", "errors_dev.csv"}
    assert (out / "summary.md").is_file()
    assert json.loads((out / "results.json").read_text(encoding="utf-8"))["metrics_by_type"]
    assert json.loads((out / "threshold.json").read_text(encoding="utf-8"))["threshold"] == 0.3


def test_synthetic_test_split_requires_saved_threshold_and_never_sweeps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Un split test entièrement temporaire emploie uniquement le seuil sauvegardé."""
    corpus = synthetic_corpus(tmp_path / "fake-corpus", "test")
    out = tmp_path / "results"
    with pytest.raises(ValueError, match="threshold.json"):
        run.run_evaluation("test", ["hybrid"], out, corpus)
    out.mkdir()
    run.write_json(out / "threshold.json", {"threshold": 0.65, "criterion": run.CRITERION})
    calls = []

    def fake_detect(text: str, config: Any) -> list[Detection]:
        """Enregistre le seul seuil employé sans charger de modèle."""
        calls.append(config.threshold)
        return []

    monkeypatch.setattr(run, "detect", fake_detect)
    report = run.run_evaluation("test", ["hybrid"], out, corpus)
    assert calls == [0.65]
    assert report["threshold_sweep"] == []
    assert not (out / "errors_dev.csv").exists()
    assert report["selected_threshold"]["threshold"] == 0.65


def test_error_export_refuses_test_and_limits_context() -> None:
    """L'export refuse tout document test et coupe le contexte à trente caractères."""
    with pytest.raises(ValueError, match="réservées"):
        run.dev_errors([synthetic_document("test")], [[]])
    with pytest.raises(ValueError, match="réservées"):
        run.dev_errors([synthetic_document()], [])
    document = CorpusDocument(
        "fiction",
        "letter",
        "dev",
        "Fiction",
        "a" * 80,
        [GoldEntity(35, 40, EntityType.PERSON, "a" * 5)],
    )
    errors = run.dev_errors([document], [[prediction(35, 39)]])
    assert [error["nature"] for error in errors] == ["FN", "FP"]
    assert [len(error["text"]) for error in errors] == [5, 4]
    assert [error["category"] for error in errors] == ["boundary", "boundary"]
    assert all(
        len(error["context_before"]) == len(error["context_after"]) == 30 for error in errors
    )


def test_missing_camembert_is_omitted_with_note(monkeypatch: pytest.MonkeyPatch) -> None:
    """Une option absente ne produit aucune ligne et explique son absence."""
    monkeypatch.setattr(run, "find_spec", lambda name: None)
    names, notes = run.available_configs(["hybrid", "hybrid_camembert"])
    assert names == ["hybrid"]
    assert len(notes) == 1
    assert "hybrid_camembert omitted" in notes[0]
    with pytest.raises(ValueError, match="inconnues"):
        run.available_configs(["unknown"])


def test_runner_rejects_invalid_split_and_empty_configuration(tmp_path: Path) -> None:
    """Les paramètres invalides échouent avant toute lecture du corpus."""
    with pytest.raises(ValueError, match="Split"):
        run.run_evaluation("unknown", out=tmp_path)
    with pytest.raises(ValueError, match="Aucune"):
        run.run_evaluation(configs=[], out=tmp_path)


def test_all_on_synthetic_documents_freezes_threshold_and_omits_missing_local_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Le mode all garde le seuil dev pour le test fictif et omet une option inutilisable."""
    corpus = synthetic_corpus(tmp_path / "fake-corpus")
    synthetic_corpus(corpus, "test")
    test_path = corpus / "test.jsonl"
    record = json.loads(test_path.read_text(encoding="utf-8"))
    record["text"] = "Eva writes."
    record["entities"][0]["text"] = "Eva"
    test_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    calls = []

    def fake_detect(text: str, config: Any) -> list[Detection]:
        """Simule des scores distincts et un modèle optionnel absent du disque."""
        if config.use_camembert:
            raise RuntimeError("Fictional local model missing")
        calls.append((text[:3], config.threshold))
        return [prediction(0, 3)] if text.startswith("Ada") and config.threshold <= 0.55 else []

    monkeypatch.setattr(run, "detect", fake_detect)
    monkeypatch.setattr(run, "find_spec", lambda name: object())
    out = tmp_path / "results"
    report = run.run_evaluation("all", ["hybrid", "hybrid_camembert"], out, corpus)
    assert report["selected_threshold"]["threshold"] == 0.3
    assert [threshold for name, threshold in calls if name == "Eva"] == [0.3]
    assert {row["config"] for row in report["metrics_by_type"]} == {"hybrid"}
    assert {row["split"] for row in report["metrics_by_type"]} == {"dev", "test"}
    assert (
        run.micro_partial([row for row in report["metrics_by_type"] if row["split"] == "test"])[
            "f2"
        ]
        == 0
    )
    assert report["metadata"]["corpus_sha256"].keys() == {"dev.jsonl", "test.jsonl"}
    assert "local model unavailable" in report["notes"][0]
    assert (out / "errors_dev.csv").is_file()
    assert not (out / "errors_test.csv").exists()


def test_dev_error_categories_follow_unmatched_spans() -> None:
    """Distingue absence, ajout, bornes et mauvais type sans changer les comptes exacts."""
    document = CorpusDocument(
        "errors",
        "letter",
        "dev",
        "Fiction",
        "x" * 40,
        [gold(0, 3), gold(5, 10), gold(12, 16), gold(20, 24)],
    )
    detected = [
        prediction(5, 9),
        prediction(12, 16, "EMAIL"),
        prediction(20, 24),
        prediction(30, 32),
    ]
    errors = run.dev_errors([document], [detected])
    assert [(row["nature"], row["category"]) for row in errors] == [
        ("FN", "missed"),
        ("FN", "boundary"),
        ("FN", "type_confusion"),
        ("FP", "boundary"),
        ("FP", "type_confusion"),
        ("FP", "extra"),
    ]
