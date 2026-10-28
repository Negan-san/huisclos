"""Teste les intervalles, le split challenge et les comparaisons dans la page.

AppTest utilise des rapports fictifs et ne lance aucune detection.
Les assertions couvrent les langues anglaise et francaise et les anciens rapports.
Ces tests valident la consultation des resultats apres les gates.
"""

import copy
import json
from typing import Any

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from test_app_evaluation import evaluation_app
from test_app_evaluation import saved_results as saved_results

from app.i18n import EN, FR
from app.pages import evaluation
from huisclos.evaluation.comparison import compare_reports
from huisclos.evaluation.intervals import INTERVAL_METRICS


@pytest.mark.parametrize("language", ["en", "fr"])
@pytest.mark.parametrize("challenge", [False, True])
@pytest.mark.parametrize("intervals", [False, True])
def test_extended_results_bilingual(
    saved_results: dict[str, Any],
    language: str,
    challenge: bool,
    intervals: bool,
) -> None:
    """Affiche les résultats anciens ou enrichis dans les deux langues, avec ou sans challenge."""
    translations = EN if language == "en" else FR
    if challenge:
        saved_results["metrics_by_type"].extend(
            [
                dict(row, split="challenge", recall=0.4)
                for row in saved_results["metrics_by_type"]
                if row["split"] == "dev"
            ]
        )
        saved_results["metadata"]["document_counts"]["challenge"] = 3
    if intervals:
        saved_results["bootstrap_intervals"] = [
            {key: row[key] for key in ("split", "config", "threshold", "mode", "type")}
            | {
                "documents": 3,
                **{
                    name: {"lower": row[name] - 0.05, "upper": row[name] + 0.05}
                    for name in INTERVAL_METRICS
                },
            }
            for row in saved_results["metrics_by_type"]
            if row["mode"] == "partial" and row["type"] == "micro"
        ]
    (evaluation.RESULTS_DIR / "results.json").write_text(
        json.dumps(saved_results), encoding="utf-8"
    )
    app = AppTest.from_function(evaluation_app, default_timeout=15)
    app.session_state["language"] = language
    app.run()
    assert not app.exception
    assert not app.error
    assert app.header[0].value == translations["evaluation.title"]
    assert app.selectbox[0].options == ["dev", "test", *(["challenge"] if challenge else [])]
    for split in app.selectbox[0].options:
        app.selectbox[0].select(split).run()
        assert not app.exception
        assert not app.error
        assert len(app.dataframe) == (2 if intervals else 1)
        assert len(app.get("vega_lite_chart")) == (3 if intervals else 2)
        assert (translations["evaluation.challenge_note"] in [item.value for item in app.info]) == (
            split == "challenge"
        )
        if intervals:
            table = app.dataframe[1].value
            assert len(table) == 8
            assert translations["evaluation.lower"] in table.columns
            assert (
                table.iloc[1][translations["evaluation.estimate"]]
                == {"dev": "80.00%", "test": "60.00%", "challenge": "40.00%"}[split]
            )


@pytest.mark.parametrize("language", ["en", "fr"])
def test_comparison_table_bilingual(saved_results: dict[str, Any], language: str) -> None:
    """Lit la comparaison enregistrée du split, y compris les intervalles absents."""
    saved_results["selected_threshold"] = {"threshold": 0.37}
    before = copy.deepcopy(saved_results)
    for row in saved_results["metrics_by_type"]:
        row["recall"] += 0.1
    comparison = compare_reports(before, saved_results, "dev")
    (evaluation.RESULTS_DIR / "dev_comparison.json").write_text(
        json.dumps(comparison), encoding="utf-8"
    )
    app = AppTest.from_function(evaluation_app, default_timeout=15)
    app.session_state["language"] = language
    app.run()
    translations = EN if language == "en" else FR
    assert not app.exception
    assert not app.error
    assert len(app.dataframe) == 2
    table = app.dataframe[1].value
    assert len(table) == 10
    assert translations["evaluation.delta"] in table.columns
    assert translations["evaluation.not_recorded"] in table.iloc[0].values
    recall = table[table[translations["evaluation.metric"]] == translations["evaluation.recall"]]
    assert recall[translations["evaluation.delta"]].tolist() == ["+10.00", "+10.00"]
    assert translations["evaluation.comparison_corpus_sha256_missing"] in [
        item.value for item in app.info
    ]
    app.selectbox[0].select("test").run()
    assert not app.exception
    assert len(app.dataframe) == 1


def test_interval_chart_uses_saved_bounds() -> None:
    """Le graphique porte les deux bornes distinctes de la valeur ponctuelle."""
    data = pd.DataFrame([{"label": "hybrid / Recall", "estimate": 0.8, "lower": 0.6, "upper": 0.9}])
    chart = evaluation.interval_chart(data).to_dict()
    assert chart["layer"][0]["mark"]["type"] == "rule"
    assert chart["layer"][0]["encoding"]["x"]["field"] == "lower"
    assert chart["layer"][0]["encoding"]["x2"]["field"] == "upper"
    assert chart["layer"][1]["encoding"]["x"]["field"] == "estimate"
