"""Affiche les résultats précalculés de l'évaluation locale.

Entrées : résultats JSON, seuil retenu et CSV dans results/.
Sorties : tableaux, graphiques et téléchargements, sans lancer de mesure.
Place dans le pipeline : consultation des mesures hors du parcours des documents.
"""

import json
from io import StringIO
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from app.i18n import t

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
OKABE_ITO = (
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#D55E00",
    "#CC79A7",
    "#56B4E9",
    "#F0E442",
    "#000000",
)
METRICS = ("precision", "recall", "f1", "f2")
TABLE_COLUMNS = (*METRICS, "leak_rate", "exposed_entities")


def load_results() -> tuple[dict[str, Any], pd.DataFrame, float]:
    """Lit les fichiers locaux et renvoie les mesures, le balayage et le seuil."""
    results = json.loads((RESULTS_DIR / "results.json").read_text(encoding="utf-8"))
    threshold = json.loads((RESULTS_DIR / "threshold.json").read_text(encoding="utf-8"))[
        "threshold"
    ]
    sweep = pd.read_csv(StringIO((RESULTS_DIR / "threshold_sweep.csv").read_text(encoding="utf-8")))
    return results, sweep, float(threshold)


def recall_chart(rows: pd.DataFrame) -> alt.LayerChart:
    """Construit les barres groupées et étiquetées depuis les mesures par type."""
    data = rows.copy()
    data["entity"] = data["type"].map(lambda kind: t(f"entity.{kind}"))
    data["label"] = data.apply(
        lambda row: t(
            "evaluation.recall_label", config=row["config"], recall=f"{row['recall']:.0%}"
        ),
        axis=1,
    )
    configurations = data["config"].drop_duplicates().tolist()
    base = alt.Chart(data).encode(
        x=alt.X(
            "recall:Q",
            title=t("evaluation.recall"),
            scale=alt.Scale(domain=[0, 1.15]),
            axis=alt.Axis(format="%", values=[0, 0.25, 0.5, 0.75, 1]),
        ),
        y=alt.Y("entity:N", title=t("evaluation.type")),
        yOffset=alt.YOffset("config:N", sort=configurations),
        tooltip=[
            alt.Tooltip("entity:N", title=t("evaluation.type")),
            alt.Tooltip("config:N", title=t("evaluation.config")),
            alt.Tooltip("recall:Q", title=t("evaluation.recall"), format=".1%"),
        ],
    )
    bars = base.mark_bar().encode(
        color=alt.Color(
            "config:N",
            title=t("evaluation.config"),
            scale=alt.Scale(domain=configurations, range=list(OKABE_ITO[: len(configurations)])),
            legend=alt.Legend(orient="bottom"),
        )
    )
    # Les étiquettes hors des barres gardent le même contraste pour chaque couleur.
    labels = base.mark_text(align="left", dx=4, color="#1B1F24").encode(text=alt.Text("label:N"))
    return alt.layer(bars, labels).properties(height=alt.Step(72))


def threshold_chart(sweep: pd.DataFrame, threshold: float) -> alt.LayerChart:
    """Trace le balayage dev et une règle portant le seuil lu dans le fichier."""
    data = sweep.melt(
        id_vars="threshold", value_vars=list(METRICS), var_name="metric", value_name="score"
    )
    data["metric"] = data["metric"].map(lambda name: t(f"evaluation.{name}"))
    lines = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X("threshold:Q", title=t("evaluation.threshold")),
            y=alt.Y(
                "score:Q",
                title=t("evaluation.score"),
                scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format="%"),
            ),
            color=alt.Color(
                "metric:N",
                title=t("evaluation.metric"),
                scale=alt.Scale(range=list(OKABE_ITO[: len(METRICS)])),
            ),
            strokeDash=alt.StrokeDash("metric:N", title=t("evaluation.metric")),
            tooltip=[
                alt.Tooltip("threshold:Q", title=t("evaluation.threshold")),
                alt.Tooltip("metric:N", title=t("evaluation.metric")),
                alt.Tooltip("score:Q", title=t("evaluation.score"), format=".1%"),
            ],
        )
    )
    selected = alt.Chart(pd.DataFrame({"threshold": [threshold]})).encode(x="threshold:Q")
    rule = selected.mark_rule(color="#1B1F24", strokeDash=[5, 3])
    label = selected.mark_text(
        align="left",
        dx=5,
        dy=12,
        text=t("evaluation.selected", threshold=f"{threshold:g}"),
    ).encode(y=alt.value(0))
    return alt.layer(lines, rule, label).properties(height=320)


def render_metadata(metadata: dict[str, Any], split: str, entities: int) -> None:
    """Affiche les métadonnées enregistrées et les effectifs du split sélectionné."""
    documents = metadata.get("document_counts", {}).get(split)
    missing = t("evaluation.not_recorded")
    st.info(
        t(
            "evaluation.limits",
            split=split,
            documents=documents if documents is not None else missing,
            entities=entities,
        ),
        title=t("evaluation.limits_title"),
    )
    st.subheader(t("evaluation.metadata"))
    values = {
        "date": metadata.get("date", missing),
        "commit": metadata.get("git_commit", missing),
        "documents": documents if documents is not None else missing,
        "entities": entities,
    }
    for key, value in values.items():
        st.markdown(t("evaluation.metadata_line", label=t(f"evaluation.{key}"), value=value))
    if documents is None:
        st.caption(t("evaluation.documents_missing"))
    with st.expander(t("evaluation.versions"), expanded=True):
        for name, version in metadata.get("versions", {}).items():
            if isinstance(version, dict):
                version = ", ".join(f"{key}: {value}" for key, value in version.items())
            st.markdown(t("evaluation.version_line", name=name, version=version))


def render_downloads() -> None:
    """Propose chaque CSV enregistré, sans exporter de nouvelle mesure."""
    st.subheader(t("evaluation.downloads"))
    for path in sorted(RESULTS_DIR.glob("*.csv")):
        st.download_button(
            t("evaluation.download", filename=path.name),
            data=path.read_bytes(),
            file_name=path.name,
            mime="text/csv",
            on_click="ignore",
        )


def render_results(results: dict[str, Any], sweep: pd.DataFrame, threshold: float) -> None:
    """Affiche les mesures partielles du split choisi et le balayage dev enregistré."""
    rows = pd.DataFrame(results["metrics_by_type"])
    rows = rows[(rows["mode"] == "partial") & (rows["threshold"] == threshold)]
    micro = rows[rows["type"] == "micro"]
    splits = [split for split in ("dev", "test") if split in micro["split"].values]
    if not splits:
        raise ValueError("Aucun split disponible au seuil retenu.")
    split = st.selectbox(t("evaluation.split"), splits, key="evaluation_split")
    chosen = micro[micro["split"] == split]
    hybrid = chosen[chosen["config"] == "hybrid"].iloc[0]
    st.markdown(
        t(
            "evaluation.lead",
            split=split,
            recall=f"{hybrid['recall']:.2%}",
            leak_rate=f"{hybrid['leak_rate']:.2%}",
            threshold=f"{threshold:g}",
        )
    )
    st.subheader(t("evaluation.table"))
    st.caption(t("evaluation.matching"))
    table = chosen[["config", *TABLE_COLUMNS]].copy()
    for name in (*METRICS, "leak_rate"):
        table[name] = table[name].map(lambda value: f"{value:.2%}")
    table = table.rename(columns={name: t(f"evaluation.{name}") for name in table.columns})
    st.dataframe(table, hide_index=True)
    st.subheader(t("evaluation.recall_chart"))
    types = rows[(rows["split"] == split) & ~rows["type"].isin(["micro", "macro"])]
    st.altair_chart(
        recall_chart(types), width="stretch", theme=None, alt=t("evaluation.recall_alt")
    )
    st.subheader(t("evaluation.sweep_chart"))
    st.altair_chart(
        threshold_chart(sweep, threshold),
        width="stretch",
        theme=None,
        alt=t("evaluation.sweep_alt"),
    )
    st.info(t("evaluation.choice"), title=t("evaluation.choice_title"))
    render_metadata(results["metadata"], split, int(hybrid["tp"] + hybrid["fn"]))
    render_downloads()


def render() -> None:
    """Affiche la page et un état clair si les fichiers sont absents ou invalides."""
    st.header(t("evaluation.title"))
    if not (RESULTS_DIR / "results.json").is_file():
        st.info(t("evaluation.empty"))
        return
    try:
        with st.spinner(t("evaluation.loading")):
            results, sweep, threshold = load_results()
        render_results(results, sweep, threshold)
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        st.error(t("evaluation.invalid"))


if __name__ == "__main__":
    render()
