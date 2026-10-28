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
from huisclos.evaluation.intervals import INTERVAL_METRICS

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
# Palette des graphiques : le bleu marine de la charte, puis des teintes de la palette
# Okabe-Ito, distinguables par les daltoniens. Elle est reprise dans chartCategoricalColors
# du thème (.streamlit/config.toml).
CHART_COLORS = (
    "#1F3A5F",
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#CC79A7",
    "#D55E00",
    "#F0E442",
    "#000000",
)
INK = "#1B1F24"
MUTED = "#596270"
GRID = "#E6E9EE"
DOMAIN = "#8A94A3"
CHART_FONT = "-apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
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
            scale=alt.Scale(domain=configurations, range=list(CHART_COLORS[: len(configurations)])),
            legend=alt.Legend(orient="bottom"),
        )
    )
    # Les étiquettes hors des barres gardent le même contraste pour chaque couleur.
    labels = base.mark_text(align="left", dx=4, color=INK).encode(text=alt.Text("label:N"))
    # Le pas porte sur chaque barre (une par configuration et par type) : 18 px garde le
    # graphique lisible sans qu'il occupe plusieurs écrans.
    return _styled(alt.layer(bars, labels).properties(height=alt.Step(18)))


def _styled(chart: alt.LayerChart) -> alt.LayerChart:
    """Applique la charte aux graphiques : polices du système, axes et grille discrets."""
    return (
        chart.configure(font=CHART_FONT, background="#FFFFFF")
        .configure_axis(
            labelColor=MUTED,
            titleColor=INK,
            gridColor=GRID,
            domainColor=DOMAIN,
            tickColor=DOMAIN,
            labelFontSize=12,
            titleFontSize=12,
            titleFontWeight=600,
        )
        .configure_legend(labelColor=INK, titleColor=INK, labelFontSize=12, titleFontSize=12)
        .configure_view(stroke=None)
    )


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
                scale=alt.Scale(range=list(CHART_COLORS[: len(METRICS)])),
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
    rule = selected.mark_rule(color=INK, strokeDash=[5, 3])
    label = selected.mark_text(
        align="left",
        dx=5,
        dy=12,
        text=t("evaluation.selected", threshold=f"{threshold:g}"),
    ).encode(y=alt.value(0))
    return _styled(alt.layer(lines, rule, label).properties(height=320))


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
        icon=":material/info:",
    )
    st.subheader(t("evaluation.metadata"), anchor=False)
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
    st.subheader(t("evaluation.downloads"), anchor=False)
    with st.container(horizontal=True):
        for path in sorted(RESULTS_DIR.glob("*.csv")):
            st.download_button(
                t("evaluation.download", filename=path.name),
                data=path.read_bytes(),
                file_name=path.name,
                mime="text/csv",
                on_click="ignore",
                icon=":material/download:",
            )


def render_key_figures(hybrid: pd.Series, threshold: float) -> None:
    """Affiche les chiffres clés de la configuration hybrid en cartes, sous le texte d'accroche."""
    st.caption(t("evaluation.kpis", threshold=f"{threshold:g}"))
    figures = (
        ("recall", f"{hybrid['recall']:.1%}", ":material/search:"),
        ("leak_rate", f"{hybrid['leak_rate']:.1%}", ":material/lock_open:"),
        ("exposed_entities", f"{int(hybrid['exposed_entities'])}", ":material/person_search:"),
        ("f2", f"{hybrid['f2']:.1%}", ":material/balance:"),
    )
    for column, (name, value, icon) in zip(st.columns(len(figures)), figures, strict=True):
        column.metric(t(f"evaluation.{name}"), value, icon=icon, border=True)


def interval_chart(data: pd.DataFrame) -> alt.LayerChart:
    """Trace les bornes enregistrées et les valeurs ponctuelles, avec des libellés écrits."""
    base = alt.Chart(data).encode(
        y=alt.Y("label:N", title=None, sort=None),
        tooltip=[
            alt.Tooltip("label:N", title=t("evaluation.label")),
            *[
                alt.Tooltip(f"{key}:Q", title=t(f"evaluation.{key}"), format=".2%")
                for key in ("estimate", "lower", "upper")
            ],
        ],
    )
    limits = base.mark_rule(color=CHART_COLORS[0], strokeWidth=2).encode(
        x=alt.X(
            "lower:Q",
            title=t("evaluation.score"),
            scale=alt.Scale(domain=[0, 1]),
            axis=alt.Axis(format="%"),
        ),
        x2="upper:Q",
    )
    points = base.mark_point(color=CHART_COLORS[0], filled=True, size=60).encode(x="estimate:Q")
    return _styled(alt.layer(limits, points).properties(height=alt.Step(24)))


def render_intervals(
    results: dict[str, Any], chosen: pd.DataFrame, split: str, threshold: float
) -> None:
    """Affiche les intervalles disponibles en tableau et en barres, sans calcul sur le corpus."""
    records = []
    for row in results.get("bootstrap_intervals", []):
        if row["mode"] != "partial" or row["type"] != "micro":
            continue
        estimates = chosen[chosen["config"] == row["config"]]
        if row["split"] != split or row["threshold"] != threshold or estimates.empty:
            continue
        for name in INTERVAL_METRICS:
            records.append(
                {
                    "label": f"{row['config']} / {t(f'evaluation.{name}')}",
                    "estimate": estimates.iloc[0][name],
                    **row[name],
                }
            )
    if not records:
        return
    with st.container(key="hc-card-eval-intervals"):
        st.subheader(t("evaluation.intervals"), anchor=False)
        st.caption(t("evaluation.intervals_note"))
        data = pd.DataFrame(records)
        table = data.copy()
        for key in ("estimate", "lower", "upper"):
            table[key] = table[key].map(lambda value: f"{value:.2%}")
        st.dataframe(
            table.rename(columns={key: t(f"evaluation.{key}") for key in table.columns}),
            hide_index=True,
            width="stretch",
        )
        st.altair_chart(
            interval_chart(data), width="stretch", theme=None, alt=t("evaluation.intervals_alt")
        )


def render_comparison(split: str) -> None:
    """Affiche le tableau avant/après du split si le script de comparaison l'a enregistré."""
    path = RESULTS_DIR / f"{split}_comparison.json"
    if not path.is_file():
        return
    comparison = json.loads(path.read_text(encoding="utf-8"))
    if comparison["split"] != split:
        raise ValueError("Split incohérent dans la comparaison.")
    with st.container(key="hc-card-eval-comparison"):
        st.subheader(t("evaluation.comparison"), anchor=False)
        st.caption(t("evaluation.comparison_note"))
        for side, source in comparison["sources"].items():
            st.caption(
                t(
                    "evaluation.comparison_source",
                    side=t(f"evaluation.{side}"),
                    commit=source["git_commit"],
                    threshold=source["threshold"],
                    documents=source["documents"],
                )
            )
        for warning in comparison["warnings"]:
            st.info(t(f"evaluation.comparison_{warning}"))
        table = pd.DataFrame(comparison["rows"])
        for key in ("reference_interval", "current_interval"):
            table[key] = table[key].map(
                lambda value: (
                    t("evaluation.not_recorded")
                    if value is None
                    else f"[{value['lower']:.2%}, {value['upper']:.2%}]"
                )
            )
        for key in ("reference", "current", "delta"):
            table[key] = table.apply(
                lambda row, column=key: comparison_value(row[column], row["metric"], column), axis=1
            )
        table["metric"] = table["metric"].map(lambda name: t(f"evaluation.{name}"))
        st.dataframe(
            table.rename(columns={key: t(f"evaluation.{key}") for key in table.columns}),
            hide_index=True,
            width="stretch",
        )


def comparison_value(value: float | None, metric: str, column: str) -> str:
    """Formate un compte ou un ratio, avec un signe pour les écarts et une absence explicite."""
    if pd.isna(value):
        return t("evaluation.not_recorded")
    if metric == "exposed_entities":
        return f"{value:+.0f}" if column == "delta" else f"{value:.0f}"
    return f"{value * 100:+.2f}" if column == "delta" else f"{value:.2%}"


def render_results(results: dict[str, Any], sweep: pd.DataFrame, threshold: float) -> None:
    """Affiche les mesures partielles du split choisi et le balayage dev enregistré."""
    rows = pd.DataFrame(results["metrics_by_type"])
    rows = rows[(rows["mode"] == "partial") & (rows["threshold"] == threshold)]
    micro = rows[rows["type"] == "micro"]
    splits = [split for split in ("dev", "test", "challenge") if split in micro["split"].values]
    if not splits:
        raise ValueError("Aucun split disponible au seuil retenu.")
    split = st.selectbox(t("evaluation.split"), splits, key="evaluation_split", width=240)
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
    render_key_figures(hybrid, threshold)
    if split == "challenge":
        st.info(t("evaluation.challenge_note"))
    with st.container(key="hc-card-eval-table"):
        st.subheader(t("evaluation.table"), anchor=False)
        st.caption(t("evaluation.matching"))
        table = chosen[["config", *TABLE_COLUMNS]].copy()
        for name in (*METRICS, "leak_rate"):
            table[name] = table[name].map(lambda value: f"{value:.2%}")
        table = table.rename(columns={name: t(f"evaluation.{name}") for name in table.columns})
        st.dataframe(table, hide_index=True, width="stretch")
    render_intervals(results, chosen, split, threshold)
    render_comparison(split)
    types = rows[(rows["split"] == split) & ~rows["type"].isin(["micro", "macro"])]
    with st.container(key="hc-card-eval-recall"):
        st.subheader(t("evaluation.recall_chart"), anchor=False)
        st.altair_chart(
            recall_chart(types), width="stretch", theme=None, alt=t("evaluation.recall_alt")
        )
    with st.container(key="hc-card-eval-sweep"):
        st.subheader(t("evaluation.sweep_chart"), anchor=False)
        st.altair_chart(
            threshold_chart(sweep, threshold),
            width="stretch",
            theme=None,
            alt=t("evaluation.sweep_alt"),
        )
        st.info(t("evaluation.choice"), title=t("evaluation.choice_title"), icon=":material/tune:")
    render_metadata(results["metadata"], split, int(hybrid["tp"] + hybrid["fn"]))
    render_downloads()


def render() -> None:
    """Affiche la page et un état clair si les fichiers sont absents ou invalides."""
    st.header(t("evaluation.title"), anchor=False)
    if not (RESULTS_DIR / "results.json").is_file():
        st.info(t("evaluation.empty"))
        return
    st.info(t("evaluation.languages"), icon=":material/translate:")
    try:
        with st.spinner(t("evaluation.loading")):
            results, sweep, threshold = load_results()
        render_results(results, sweep, threshold)
    except (OSError, ValueError, KeyError, TypeError, IndexError):
        st.error(t("evaluation.invalid"))


if __name__ == "__main__":
    render()
