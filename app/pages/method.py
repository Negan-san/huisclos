"""Page Method & limits : fonctionnement expliqué pas à pas, technologies, droit et limites.

Entrées : les textes de app/i18n/method.py, method_guide.py et method_glossary.py.
Sorties : un schéma Graphviz rendu dans le navigateur, des sections en encadrés et un lien
vers la page des résultats détaillés, retirée de la barre de navigation.
Place dans le pipeline : page d'explication destinée au juriste, sans formation technique,
qui décide d'utiliser l'outil.
"""

from itertools import pairwise

import streamlit as st

from app.i18n import t
from app.ui_common import entity_badge_html
from huisclos.models import EntityType

# Couleurs du schéma : celles de la charte (voir app/assets/style.css).
INK = "#1B1F24"
PRIMARY = "#1F3A5F"
SURFACE = "#F1F3F6"

EVALUATION_PAGE = "app/pages/evaluation.py"
LOCAL_NODES = ("document", "read", "detect", "review", "pseudonymize", "restore", "result")
FLOW = ("document", "read", "detect", "review", "pseudonymize", "llm", "restore", "result")
SUMMARY_KEYS = tuple(f"method.summary.{item}" for item in ("problem", "solution", "limits"))
EXAMPLE_PARTS = (("original", "sent"), ("answer", "restored"))
HOW_KEYS = tuple(f"method.how.{number}" for number in range(1, 7))
DATA_KEYS = tuple(f"method.data.{item}" for item in ("stays", "leaves", "check", "offline"))
HYBRID_KEYS = ("method.hybrid.rules", "method.hybrid.ner", "method.hybrid.propagation")
LANGUAGE_KEYS = tuple(f"method.languages.{item}" for item in ("supported", "profiles", "limits"))
GLOSSARY_KEYS = tuple(
    f"method.glossary.{item}"
    for item in (
        "pseudonymization",
        "anonymization",
        "token",
        "mapping",
        "llm",
        "ner",
        "score",
        "metrics",
    )
)
LEGAL_KEYS = ("method.legal.secrecy", "method.legal.gdpr", "method.legal.cnb")
LIMIT_KEYS = (
    "method.limits.context",
    "method.limits.errors",
    "method.limits.tokens",
    "method.limits.demo",
)
PRACTICE_KEYS = tuple(f"method.practices.{number}" for number in range(1, 7))
TESTING_KEYS = tuple(f"method.testing.{item}" for item in ("corpus", "protocol", "results"))


def pipeline_dot() -> str:
    """Construit le schéma du pipeline au format DOT.

    Le navigateur dessine le schéma lui-même : aucune dépendance système n'est requise.
    Le cadre "On this computer" montre ce qui ne quitte jamais la machine ; l'outil d'IA est
    en dehors, et la table de correspondance ne le traverse pas.
    """
    label = {name: t(f"method.diagram.{name}") for name in FLOW}
    local = "; ".join(LOCAL_NODES)
    lines = [
        "digraph pipeline {",
        "  rankdir=LR;",
        f'  graph [fontname="Helvetica", color="{PRIMARY}", fontcolor="{INK}"];',
        f'  node [shape=box, style="rounded,filled", fillcolor="{SURFACE}", color="{PRIMARY}",'
        f' fontname="Helvetica", fontcolor="{INK}"];',
        f'  edge [color="{PRIMARY}", fontname="Helvetica", fontcolor="{INK}"];',
        f'  subgraph cluster_local {{ label="{t("method.diagram.local")}"; {local}; }}',
        f'  subgraph cluster_remote {{ label="{t("method.diagram.remote")}"; style=dashed; llm; }}',
    ]
    lines += [f'  {name} [label="{text}"];' for name, text in label.items()]
    lines += [f"  {source} -> {target};" for source, target in pairwise(FLOW)]
    mapping = t("method.diagram.mapping")
    lines.append(f'  pseudonymize -> restore [style=dashed, label="{mapping}"];')
    lines.append("}")
    return "\n".join(lines)


def _render_section(title_key: str, text_keys: tuple[str, ...], key: str) -> None:
    """Affiche une section en encadré : un sous-titre suivi d'une liste de paragraphes."""
    with st.container(key=key):
        st.subheader(t(title_key), anchor=False)
        st.markdown("\n".join(f"- {t(item)}" for item in text_keys))


Section = tuple[str, tuple[str, ...], str]


def _render_pair(left: Section, right: Section) -> None:
    """Affiche deux sections côte à côte sur grand écran, l'une sous l'autre sur mobile.

    Chaque section est un triplet : clé du titre, clés des paragraphes, clé de l'encadré.
    """
    for column, section in zip(st.columns(2, gap="medium"), (left, right), strict=True):
        with column:
            _render_section(*section)


def _render_summary_and_pipeline() -> None:
    """Résumé en trois paragraphes, puis le schéma et la manière de le lire."""
    with st.container(key="hc-card-summary"):
        st.subheader(t("method.summary.title"), anchor=False)
        for item in SUMMARY_KEYS:
            st.markdown(t(item))
    with st.container(key="hc-card-pipeline"):
        st.subheader(t("method.diagram.title"), anchor=False)
        st.graphviz_chart(pipeline_dot(), width="stretch", alt=t("method.diagram.alt"))
        st.caption(t("method.diagram.how_to_read"))


def _render_example() -> None:
    """Exemple commenté en quatre encadrés : document, envoi, réponse, restauration.

    Les textes sont affichés tels quels (bloc de code sans coloration) pour que les jetons
    se lisent exactement comme l'outil d'IA les reçoit ; les lignes longues reviennent à la
    ligne pour rester lisibles sur mobile.
    """
    with st.container(key="hc-card-example"):
        st.subheader(t("method.example.title"), anchor=False)
        st.markdown(t("method.example.intro"))
        for row in EXAMPLE_PARTS:
            for column, part in zip(st.columns(2, gap="medium"), row, strict=True):
                with column:
                    st.markdown(t(f"method.example.{part}_label"))
                    st.code(t(f"method.example.{part}"), language=None, wrap_lines=True)
        st.info(t("method.example.note"), icon=":material/lightbulb:")


def _render_technologies() -> None:
    """Tableau des composants employés, chacun avec son rôle en langage courant."""
    with st.container(key="hc-card-tech"):
        st.subheader(t("method.tech.title"), anchor=False)
        st.markdown(t("method.tech.intro"))
        st.markdown(t("method.tech.table"))
        st.caption(t("method.tech.note"))


def _render_human_and_types() -> None:
    """Deux encadrés côte à côte : la place de l'humain, puis les types recherchés."""
    human, types = st.columns(2, gap="medium")
    with human, st.container(key="hc-card-human"):
        st.subheader(t("method.human.title"), anchor=False)
        st.info(t("method.human.text"), icon=":material/person_check:")
    with types, st.container(key="hc-card-method-types"):
        st.subheader(t("method.types.title"), anchor=False)
        st.markdown(t("method.types.intro"))
        badges = "".join(entity_badge_html(kind) for kind in EntityType)
        st.html(f'<div class="hc-legend">{badges}</div>')


def _render_practices_and_testing() -> None:
    """Bonnes pratiques, puis la méthode de mesure et le lien vers les résultats détaillés.

    La page des résultats chiffrés ne figure plus dans la barre de navigation : elle intéresse
    surtout un lecteur technique. Ce lien est son seul accès depuis l'interface.
    """
    practices, testing = st.columns(2, gap="medium")
    with practices:
        _render_section("method.practices.title", PRACTICE_KEYS, "hc-card-practices")
    with testing, st.container(key="hc-card-testing"):
        st.subheader(t("method.testing.title"), anchor=False)
        st.markdown("\n".join(f"- {t(item)}" for item in TESTING_KEYS))
        st.page_link(EVALUATION_PAGE, label=t("method.testing.link"), icon=":material/monitoring:")


def render() -> None:
    """Affiche la page Method & limits : sections en encadrés, deux par ligne sur grand écran.

    L'ordre suit la lecture d'un juriste qui découvre l'outil : résumé, schéma, exemple,
    étapes, circulation des données, techniques, langues, place de l'humain, lexique, droit,
    limites, bonnes pratiques et mesures.
    """
    st.header(t("method.title"), anchor=False)
    with st.container(key="hc-reading"):
        st.markdown(t("method.intro"))
    _render_summary_and_pipeline()
    _render_example()
    _render_pair(
        ("method.how.title", HOW_KEYS, "hc-card-how"),
        ("method.data.title", DATA_KEYS, "hc-card-data"),
    )
    _render_pair(
        ("method.hybrid.title", HYBRID_KEYS, "hc-card-hybrid"),
        ("method.languages.title", LANGUAGE_KEYS, "hc-card-languages"),
    )
    _render_technologies()
    _render_human_and_types()
    _render_section("method.glossary.title", GLOSSARY_KEYS, "hc-card-glossary")
    _render_pair(
        ("method.legal.title", LEGAL_KEYS, "hc-card-legal"),
        ("method.limits.title", LIMIT_KEYS, "hc-card-limits"),
    )
    _render_practices_and_testing()
    st.caption(t("method.disclaimer"))


render()
