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
SURFACE = "#F4F5F7"

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


def _render_section(title_key: str, text_keys: tuple[str, ...]) -> None:
    """Affiche un sous-titre suivi d'une liste de paragraphes."""
    st.subheader(t(title_key))
    for key in text_keys:
        st.markdown(f"- {t(key)}")


def render() -> None:
    """Affiche la page Method & limits."""
    st.header(t("method.title"))
    st.markdown(t("method.intro"))
    st.subheader(t("method.diagram.title"))
    st.graphviz_chart(pipeline_dot(), width="stretch", alt=t("method.diagram.alt"))
    _render_section("method.how.title", HOW_KEYS)
    _render_section("method.hybrid.title", HYBRID_KEYS)
    st.subheader(t("method.human.title"))
    st.markdown(t("method.human.text"))
    st.subheader(t("method.types.title"))
    st.markdown(t("method.types.intro"))
    badges = "".join(entity_badge_html(kind) for kind in EntityType)
    st.html(f'<div class="hc-legend">{badges}</div>')
    _render_section("method.legal.title", LEGAL_KEYS)
    _render_section("method.limits.title", LIMIT_KEYS)
    st.caption(t("method.disclaimer"))


render()
