"""Éléments communs de la charte : feuille de style, en-tête, bandeau de démo, étapes, types.

Entrées : app/assets/style.css, les textes de app.i18n et l'état de session.
Sorties : fonctions d'affichage appelées par streamlit_app.py et par les pages, et le
dictionnaire ENTITY_STYLES (couleur et libellé de chaque type d'entité).
Place dans le pipeline : couche d'affichage partagée par les trois étapes.
"""

import html
import os
import re
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from app.i18n import t
from app.state import STEPS, is_step_available
from huisclos.models import EntityType

STYLE_PATH = Path(__file__).resolve().parent / "assets" / "style.css"
DEMO_VARIABLE = "HUISCLOS_PUBLIC_DEMO"


def literal_markdown(value: str) -> str:
    """Échappe une valeur utilisateur affichée dans un message Markdown, sans lien ni image."""
    return re.sub(r"([\\`*_{}\[\]()#+.!|])", r"\\\1", html.escape(value))


@dataclass(frozen=True)
class EntityStyle:
    """Couleur de surlignage d'un type d'entité et clé du texte de son libellé."""

    label_key: str
    color: str

    @property
    def label(self) -> str:
        """Libellé du type dans la langue de la session (anglais par défaut)."""
        return t(self.label_key)


# Un seul dictionnaire pour toute l'interface. Le texte du surlignage est #1B1F24 : chaque
# fond ci-dessous donne un contraste d'au moins 4,5:1 avec lui (vérifié par un test).
ENTITY_STYLES: dict[EntityType, EntityStyle] = {
    EntityType.PERSON: EntityStyle("entity.PERSON", "#DCE8F7"),
    EntityType.ORGANIZATION: EntityStyle("entity.ORGANIZATION", "#E3F1E7"),
    EntityType.ADDRESS: EntityStyle("entity.ADDRESS", "#F6EBD9"),
    EntityType.EMAIL: EntityStyle("entity.EMAIL", "#DDF0F0"),
    EntityType.PHONE: EntityStyle("entity.PHONE", "#FBE4E0"),
    EntityType.IBAN: EntityStyle("entity.IBAN", "#FFF2C2"),
    EntityType.NIR: EntityStyle("entity.NIR", "#F9D9D9"),
    EntityType.SIREN: EntityStyle("entity.SIREN", "#E6E6E6"),
    EntityType.SIRET: EntityStyle("entity.SIRET", "#E6E6E6"),
    EntityType.BIRTH_DATE: EntityStyle("entity.BIRTH_DATE", "#E0EEF0"),
    EntityType.CASE_NUMBER: EntityStyle("entity.CASE_NUMBER", "#EAE6DF"),
    EntityType.LOCATION: EntityStyle("entity.LOCATION", "#E8F0D9"),
    EntityType.CUSTOM: EntityStyle("entity.CUSTOM", "#EEEEEE"),
}


def entity_label(entity_type: EntityType) -> str:
    """Renvoie le libellé affichable d'un type d'entité."""
    return ENTITY_STYLES[entity_type].label


def entity_css() -> str:
    """Construit les règles CSS de surlignage à partir de ENTITY_STYLES, sans les dupliquer."""
    return "\n".join(
        f".hc-hl-{kind.value} {{ background: {style.color}; }}"
        for kind, style in ENTITY_STYLES.items()
    )


def entity_badge_html(entity_type: EntityType) -> str:
    """Renvoie une pastille HTML : fond de la couleur du type et libellé en texte."""
    label = html.escape(entity_label(entity_type))
    return f'<span class="hc-badge hc-hl-{entity_type.value}">{label}</span>'


def inject_style() -> None:
    """Injecte la feuille de style locale et les couleurs de surlignage dans la page."""
    css = STYLE_PATH.read_text(encoding="utf-8") + "\n" + entity_css()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def is_public_demo() -> bool:
    """Indique si l'application tourne en démonstration publique.

    La variable d'environnement HUISCLOS_PUBLIC_DEMO ou le secret du même nom doivent valoir
    "true". La lecture ne lève jamais d'exception.
    """
    if os.environ.get(DEMO_VARIABLE, "").strip().lower() == "true":
        return True
    try:
        value = st.secrets.get(DEMO_VARIABLE)
    except Exception:
        # Sans fichier de secrets, Streamlit lève une exception dont le type varie selon la
        # version. Un bandeau facultatif ne doit jamais empêcher l'application de démarrer.
        return False
    return str(value).strip().lower() == "true"


def render_header() -> None:
    """Affiche le bandeau de démo éventuel, le nom, l'accroche et la mention juridique."""
    if is_public_demo():
        st.warning(t("demo.banner"))
    st.title(t("app.title"))
    st.markdown(t("app.tagline"))
    st.caption(t("app.legal_note"))


def _step_item(number: int, step: str, current: str) -> str:
    """Construit l'élément de liste d'une étape selon qu'elle est courante, libre ou verrouillée."""
    name = f"{number}. {html.escape(t(f'steps.{step}'))}"
    if step == current:
        note = html.escape(t("steps.current"))
        return (
            f'<li class="hc-step hc-step-current" aria-current="step">{name} '
            f'<span class="hc-step-note">{note}</span></li>'
        )
    if is_step_available(step):
        return f'<li class="hc-step">{name}</li>'
    note = html.escape(t(f"steps.locked.{step}"))
    return (
        f'<li class="hc-step hc-step-locked">{name} <span class="hc-step-note">{note}</span></li>'
    )


def render_steps(current: str) -> None:
    """Affiche l'indicateur des trois étapes.

    L'étape courante est en gras, soulignée et suivie de "(current step)" pour les lecteurs
    d'écran. Une étape pas encore accessible est grisée et dit pourquoi. L'information ne
    repose jamais sur la couleur seule.
    """
    items = "".join(_step_item(number, step, current) for number, step in enumerate(STEPS, 1))
    label = html.escape(t("steps.label"))
    st.html(f'<ol class="hc-steps" aria-label="{label}">{items}</ol>')
