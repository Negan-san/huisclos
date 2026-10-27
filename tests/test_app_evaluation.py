"""Vérifie la consultation des résultats enregistrés avec AppTest.

Entrées : résultats du dépôt et petits fichiers fictifs dans un dossier temporaire.
Sorties : assertions sur les mesures affichées, les états vides et les graphiques.
Place dans le pipeline : tests de l'interface, sans détection ni lecture du corpus.
"""

import ast
import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.i18n import EN, t
from app.pages import evaluation


def evaluation_app() -> None:
    """Exécute la page importée pour conserver le chemin remplacé par monkeypatch."""
    from app.pages.evaluation import render

    render()


@pytest.fixture
def saved_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Écrit des résultats fictifs distincts selon le split et le mode de mesure."""
    rows = []
    for split, recall in (("dev", 0.8), ("test", 0.6)):
        for config in ("hybrid", "patterns_only"):
            for kind in ("micro", "PERSON", "macro"):
                for mode in ("partial", "exact"):
                    rows.append(
                        {
                            "split": split,
                            "config": config,
                            "threshold": 0.37,
                            "mode": mode,
                            "type": kind,
                            "tp": 8,
                            "fp": 2,
                            "fn": 2,
                            "precision": 0.75,
                            "recall": recall if mode == "partial" else 0.1,
                            "f1": 0.72,
                            "f2": 0.77,
                            "leak_rate": 0.12,
                            "exposed_entities": 3,
                        }
                    )
    results = {
        "metrics_by_type": rows,
        "metadata": {
            "date": "2026-10-27",
            "git_commit": "fictional-commit",
            "document_counts": {"dev": 7, "test": 4},
            "versions": {"python": "fictional", "model": {"name": "local"}},
        },
    }
    (tmp_path / "results.json").write_text(json.dumps(results), encoding="utf-8")
    (tmp_path / "threshold.json").write_text('{"threshold": 0.37}', encoding="utf-8")
    (tmp_path / "threshold_sweep.csv").write_text(
        "threshold,precision,recall,f1,f2\n0.37,0.75,0.8,0.72,0.77\n0.67,0.9,0.5,0.64,0.55\n",
        encoding="utf-8",
    )
    (tmp_path / "metrics_by_type.csv").write_text("split,config\ndev,hybrid\n", encoding="utf-8")
    monkeypatch.setattr(evaluation, "RESULTS_DIR", tmp_path)
    monkeypatch.setenv("HUISCLOS_I18N_STRICT", "1")
    return results


def run_page() -> AppTest:
    """Renvoie une exécution AppTest de la page au chemin courant."""
    return AppTest.from_function(evaluation_app, default_timeout=15).run()


def test_repository_results_render(monkeypatch: pytest.MonkeyPatch) -> None:
    """Affiche les fichiers existants sans exception et avec leurs valeurs réelles."""
    monkeypatch.setenv("HUISCLOS_I18N_STRICT", "1")
    results, _, threshold = evaluation.load_results()
    hybrid = next(
        row
        for row in results["metrics_by_type"]
        if row["config"] == "hybrid"
        and row["type"] == "micro"
        and row["mode"] == "partial"
        and row["split"] == "dev"
        and row["threshold"] == threshold
    )
    app = AppTest.from_file(evaluation.__file__, default_timeout=15).run()
    assert not app.exception
    assert not app.error
    assert app.header[0].value == t("evaluation.title")
    assert app.markdown[0].value == t(
        "evaluation.lead",
        split="dev",
        recall=f"{hybrid['recall']:.2%}",
        leak_rate=f"{hybrid['leak_rate']:.2%}",
        threshold=f"{threshold:g}",
    )
    expected_splits = [
        split
        for split in ("dev", "test")
        if any(row["split"] == split for row in results["metrics_by_type"])
    ]
    assert app.selectbox[0].options == expected_splits
    assert len(app.dataframe) == 1
    assert len(app.get("vega_lite_chart")) == 2
    assert len(app.get("download_button")) == len(list(evaluation.RESULTS_DIR.glob("*.csv")))
    if "dev" not in results["metadata"].get("document_counts", {}):
        assert any(t("evaluation.documents_missing") == item.value for item in app.caption)


@pytest.mark.parametrize("missing_directory", [False, True])
def test_empty_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, missing_directory: bool
) -> None:
    """Un dossier vide ou absent donne un message clair et aucune exception."""
    directory = tmp_path / "absent" if missing_directory else tmp_path
    monkeypatch.setattr(evaluation, "RESULTS_DIR", directory)
    app = run_page()
    assert not app.exception
    assert app.info[0].value == t("evaluation.empty")
    assert not app.dataframe
    assert not app.selectbox


@pytest.mark.parametrize("content", ["{", "{}", '{"metrics_by_type": []}', "[]"])
def test_invalid_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: str) -> None:
    """Des résultats invalides produisent une erreur compréhensible sans exception."""
    monkeypatch.setattr(evaluation, "RESULTS_DIR", tmp_path)
    (tmp_path / "results.json").write_text(content, encoding="utf-8")
    app = run_page()
    assert not app.exception
    assert app.error[0].value == t("evaluation.invalid")


def test_split_selection_and_partial_metrics(saved_results: dict[str, Any]) -> None:
    """Le sélecteur change les mesures affichées sans utiliser le mode exact."""
    app = run_page()
    assert not app.exception
    assert not app.error
    assert app.selectbox[0].options == ["dev", "test"]
    table = app.dataframe[0].value
    assert table[t("evaluation.recall")].tolist() == ["80.00%", "80.00%"]
    assert table[t("evaluation.exposed_entities")].tolist() == [3, 3]
    assert list(table.columns) == [
        t(f"evaluation.{name}") for name in ("config", *evaluation.TABLE_COLUMNS)
    ]
    app.selectbox[0].select("test").run()
    assert not app.exception
    assert not app.error
    assert app.dataframe[0].value[t("evaluation.recall")].tolist() == ["60.00%", "60.00%"]
    assert "On test" in app.markdown[0].value
    assert "0.37" in app.markdown[0].value
    assert any(
        item.value == t("evaluation.metadata_line", label=t("evaluation.documents"), value=4)
        for item in app.markdown
    )
    assert any(
        item.value == t("evaluation.metadata_line", label=t("evaluation.entities"), value=10)
        for item in app.markdown
    )
    assert not any(item.value == t("evaluation.documents_missing") for item in app.caption)


def test_charts_preserve_metrics_and_threshold(saved_results: dict[str, Any]) -> None:
    """Les graphiques portent les valeurs enregistrées, libellés et palette demandés."""
    results, sweep, threshold = evaluation.load_results()
    rows = pd.DataFrame(results["metrics_by_type"])
    rows = rows[(rows["mode"] == "partial") & (rows["split"] == "dev") & (rows["type"] == "PERSON")]
    bars = evaluation.recall_chart(rows).to_dict()
    assert bars["layer"][0]["mark"]["type"] == "bar"
    assert bars["layer"][0]["encoding"]["yOffset"]["field"] == "config"
    colors = bars["layer"][0]["encoding"]["color"]["scale"]["range"]
    assert colors == list(evaluation.OKABE_ITO[:2])
    assert bars["layer"][1]["mark"]["type"] == "text"
    assert bars["layer"][1]["encoding"]["text"]["field"] == "label"
    labels = next(iter(bars["datasets"].values()))
    assert {row["label"] for row in labels} == {"hybrid: 80%", "patterns_only: 80%"}
    chart = evaluation.threshold_chart(sweep, threshold).to_dict()
    assert chart["layer"][1]["mark"]["type"] == "rule"
    assert chart["layer"][2]["mark"]["text"] == t("evaluation.selected", threshold="0.37")
    datasets = list(chart["datasets"].values())
    assert [{"threshold": threshold}] in datasets
    scores = next(data for data in datasets if "metric" in data[0])
    assert {row["metric"] for row in scores} == {
        t(f"evaluation.{key}") for key in evaluation.METRICS
    }
    assert len(scores) == len(sweep) * len(evaluation.METRICS)


def test_test_split_requires_partial_metrics(saved_results: dict[str, Any]) -> None:
    """Un split sans mesures partielles au seuil retenu n'est pas proposé."""
    saved_results["metrics_by_type"] = [
        row
        for row in saved_results["metrics_by_type"]
        if row["split"] != "test" or row["mode"] == "exact"
    ]
    (evaluation.RESULTS_DIR / "results.json").write_text(
        json.dumps(saved_results), encoding="utf-8"
    )
    app = run_page()
    assert not app.exception
    assert not app.error
    assert app.selectbox[0].options == ["dev"]


@pytest.mark.parametrize(
    "filename,content",
    [
        ("results.json", "{}"),
        ("results.json", '{"metrics_by_type": []}'),
        ("threshold.json", '{"threshold": 0.99}'),
        ("threshold_sweep.csv", "threshold,recall\n0.37,0.8\n"),
    ],
)
def test_incomplete_saved_results(
    saved_results: dict[str, Any], filename: str, content: str
) -> None:
    """Des fichiers lisibles mais incomplets donnent un état d'erreur explicite."""
    (evaluation.RESULTS_DIR / filename).write_text(content, encoding="utf-8")
    app = run_page()
    assert not app.exception
    assert app.error[0].value == t("evaluation.invalid")


def test_all_translation_keys_exist(saved_results: dict[str, Any]) -> None:
    """Vérifie les clés littérales et les familles de clés calculées par la page."""
    tree = ast.parse(Path(evaluation.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "t"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            assert node.args[0].value in EN
    dynamic = ("config", *evaluation.TABLE_COLUMNS, "date", "commit", "documents", "entities")
    assert all(f"evaluation.{key}" in EN for key in dynamic)
    assert all(
        f"entity.{row['type']}" in EN
        for row in saved_results["metrics_by_type"]
        if row["type"] not in {"micro", "macro"}
    )
    app = run_page()
    assert not app.exception
    assert not app.error
