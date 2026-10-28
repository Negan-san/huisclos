"""Page Method & limits : schéma du pipeline, méthode, cadre juridique et limites.

Entrées : les textes anglais de app/i18n/method.py.
Sorties : un schéma Graphviz rendu dans le navigateur et des sections de texte.
Place dans le pipeline : page d'explication destinée à l'avocat qui décide d'utiliser l'outil.
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

LOCAL_NODES = ("document", "read", "detect", "review", "pseudonymize", "restore", "result")
FLOW = ("document", "read", "detect", "review", "pseudonymize", "llm", "restore", "result")
HOW_KEYS = tuple(f"method.how.{number}" for number in range(1, 7))
HYBRID_KEYS = ("method.hybrid.rules", "method.hybrid.ner", "method.hybrid.propagation")
LEGAL_KEYS = ("method.legal.secrecy", "method.legal.gdpr", "method.legal.cnb")
LIMIT_KEYS = (
    "method.limits.context",
    "method.limits.errors",
    "method.limits.tokens",
    "method.limits.demo",
)


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


def render() -> None:
    """Affiche la page Method & limits : sections en encadrés, deux par ligne sur grand écran.

    Le texte courant garde une largeur de lecture limitée ; l'ordre des sections est celui
    de la lecture : schéma, méthode, humain, types, cadre juridique, limites.
    """
    st.header(t("method.title"), anchor=False)
    with st.container(key="hc-reading"):
        st.markdown(t("method.intro"))
    with st.container(key="hc-card-pipeline"):
        st.subheader(t("method.diagram.title"), anchor=False)
        st.graphviz_chart(pipeline_dot(), width="stretch", alt=t("method.diagram.alt"))
    how, hybrid = st.columns(2, gap="medium")
    with how:
        _render_section("method.how.title", HOW_KEYS, "hc-card-how")
    with hybrid:
        _render_section("method.hybrid.title", HYBRID_KEYS, "hc-card-hybrid")
    _render_human_and_types()
    legal, limits = st.columns(2, gap="medium")
    with legal:
        _render_section("method.legal.title", LEGAL_KEYS, "hc-card-legal")
    with limits:
        _render_section("method.limits.title", LIMIT_KEYS, "hc-card-limits")
    st.caption(t("method.disclaimer"))


render()
