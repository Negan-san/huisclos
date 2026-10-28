"""Éléments communs de la charte : feuille de style, ligne d'état, en-tête, étapes, types.

Entrées : app/assets/style.css, les textes de app.i18n et l'état de session.
Sorties : fonctions d'affichage appelées par streamlit_app.py et par les pages, et le
dictionnaire ENTITY_STYLES (couleur et libellé de chaque type d'entité).
Place dans le pipeline : couche d'affichage partagée par les trois étapes.
"""

import base64
import html
import os
import re
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from app.components.stepper import LOCKED, StepView, step_states, stepper_html
from app.i18n import t
from app.state import STEPS, is_step_available
from huisclos.models import EntityType

STYLE_PATH = Path(__file__).resolve().parent / "assets" / "style.css"
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo.svg"
DEMO_VARIABLE = "HUISCLOS_PUBLIC_DEMO"


def literal_markdown(value: str) -> str:
    """Échappe une valeur utilisateur affichée dans un message Markdown, sans lien ni image."""
    return re.sub(r"([\\`*_{}\[\]()#+.!|])", r"\\\1", html.escape(value))


@dataclass(frozen=True)
class EntityStyle:
    """Couleurs d'un type d'entité et clé du texte de son libellé.

    color est le fond doux du surlignage ; strong, la couleur franche du trait sous la
    mention, de la pastille de légende et du libellé de type écrit à côté de la mention.
    """

    label_key: str
    color: str
    strong: str

    @property
    def label(self) -> str:
        """Libellé du type dans la langue de la session (anglais par défaut)."""
        return t(self.label_key)


# Un seul dictionnaire pour toute l'interface. Le texte du surlignage est #1B1F24 : chaque
# fond doux donne un contraste d'au moins 4,5:1 avec lui, et chaque couleur franche un
# contraste d'au moins 4,5:1 sur fond blanc, car elle sert aussi de couleur de texte
# (vérifié par des tests).
ENTITY_STYLES: dict[EntityType, EntityStyle] = {
    EntityType.PERSON: EntityStyle("entity.PERSON", "#DCE8F7", "#2B5A8E"),
    EntityType.ORGANIZATION: EntityStyle("entity.ORGANIZATION", "#E3F1E7", "#2E6B47"),
    EntityType.ADDRESS: EntityStyle("entity.ADDRESS", "#F6EBD9", "#83561A"),
    EntityType.EMAIL: EntityStyle("entity.EMAIL", "#DDF0F0", "#1D6767"),
    EntityType.PHONE: EntityStyle("entity.PHONE", "#FBE4E0", "#A23B2A"),
    EntityType.IBAN: EntityStyle("entity.IBAN", "#FFF2C2", "#765900"),
    EntityType.NIR: EntityStyle("entity.NIR", "#F9D9D9", "#9B2C3C"),
    EntityType.SIREN: EntityStyle("entity.SIREN", "#E6E6E6", "#4A5260"),
    EntityType.SIRET: EntityStyle("entity.SIRET", "#E6E6E6", "#4A5260"),
    EntityType.BIRTH_DATE: EntityStyle("entity.BIRTH_DATE", "#E0EEF0", "#2F6670"),
    EntityType.CASE_NUMBER: EntityStyle("entity.CASE_NUMBER", "#EAE6DF", "#5E5446"),
    EntityType.LOCATION: EntityStyle("entity.LOCATION", "#E8F0D9", "#4A6620"),
    EntityType.CUSTOM: EntityStyle("entity.CUSTOM", "#EEEEEE", "#555B66"),
}


def entity_label(entity_type: EntityType) -> str:
    """Renvoie le libellé affichable d'un type d'entité."""
    return ENTITY_STYLES[entity_type].label


def entity_css() -> str:
    """Construit les règles CSS de surlignage à partir de ENTITY_STYLES, sans les dupliquer."""
    return "\n".join(
        f".hc-hl-{kind.value} {{ background: {style.color}; }}\n"
        f".hc-hl-{kind.value} .hc-swatch {{ background: {style.strong}; }}"
        for kind, style in ENTITY_STYLES.items()
    )


def entity_badge_html(entity_type: EntityType) -> str:
    """Renvoie une pastille HTML : fond doux du type, point de couleur et libellé en texte."""
    label = html.escape(entity_label(entity_type))
    return (
        f'<span class="hc-badge hc-hl-{entity_type.value}">'
        f'<span class="hc-swatch" aria-hidden="true"></span>{label}</span>'
    )


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


def render_header(hero: bool = False) -> None:
    """Affiche la ligne d'état fine puis l'en-tête de marque sur toute la largeur.

    La ligne d'état porte le mode de traitement (local, ou démonstration publique) et la
    mention juridique ; elle est placée au-dessus de l'en-tête pour laisser au logo, au nom,
    à l'accroche et à la description toute la largeur. Avec hero, l'en-tête d'accueil agrandit
    le logo et ajoute la description ; streamlit_app.py le demande seulement à l'étape Import
    de la première page.
    """
    st.html(status_strip_html(is_public_demo()))
    with st.container(key="hc-header"):
        # Un seul bloc HTML pour le logo, le nom et l'accroche : deux composants empilés dans
        # une rangée se chevauchent, car Streamlit réserve à un titre moins que sa hauteur.
        st.html(_brand_html(hero))


def status_strip_html(demo: bool) -> str:
    """Ligne fine et discrète au-dessus de l'en-tête : mode de traitement et mention RGPD.

    Sur la démonstration publique, le texte est traité sur un serveur distant : la ligne dit
    de n'utiliser que des données fictives et ne promet pas de traitement local. Ailleurs,
    elle rappelle le traitement local. Le texte porte l'information, la couleur ne fait que
    la souligner ; role="note" la signale aux lecteurs d'écran.
    """
    mode = "demo" if demo else "local"
    message = t("demo.banner") if demo else t("app.local_badge")
    return (
        f'<div class="hc-strip hc-strip-{mode}" role="note">'
        f"<strong>{html.escape(message)}</strong>"
        f"<span>{html.escape(t('app.legal_note'))}</span></div>"
    )


def _brand_html(hero: bool) -> str:
    """Bloc de marque : logo décoratif (le nom est écrit à côté), nom, accroche et description.

    Le logo vient de app/assets/logo.svg, intégré en image data: : st.html retire le SVG
    écrit en ligne, et aucune ressource externe n'est chargée.
    """
    description = (
        f'<p class="hc-description">{html.escape(t("app.description"))}</p>' if hero else ""
    )
    logo = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    brand = (
        f'<div class="hc-brand"><img class="hc-logo" src="data:image/svg+xml;base64,{logo}" '
        f'alt="">'
        f'<div class="hc-brand-text"><h1 class="hc-wordmark">{html.escape(t("app.title"))}</h1>'
        f'<p class="hc-tagline">{html.escape(t("app.tagline"))}</p>{description}</div></div>'
    )
    return f'<div class="hc-hero">{brand}</div>' if hero else brand


def render_steps(current: str) -> None:
    """Affiche l'indicateur des trois étapes.

    Chaque étape dit son état en toutes lettres (faite, courante, accessible) ; une étape
    verrouillée dit pourquoi. L'étape courante porte aria-current="step". L'information ne
    repose jamais sur la couleur seule.
    """
    available = {step: is_step_available(step) for step in STEPS}
    states = step_states(STEPS, current, available)
    views = [
        StepView(number, t(f"steps.{step}"), state, _step_note(step, state))
        for number, (step, state) in enumerate(zip(STEPS, states, strict=True), 1)
    ]
    st.html(stepper_html(views, t("steps.label")))


def _step_note(step: str, state: str) -> str:
    """Renvoie la mention écrite d'une étape : son état, ou la raison de son verrouillage."""
    if state == LOCKED:
        return t(f"steps.locked.{step}")
    return t(f"steps.state.{state}")
