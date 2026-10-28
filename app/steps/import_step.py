"""Étape Import : texte collé, fichier ou cas d'exemple, puis détection des données sensibles.

Entrées : texte saisi, fichier TXT, DOCX ou PDF, ou data/samples/demo_case_fr.txt ; la
configuration de détection de la barre latérale.
Sorties : source_text et detections dans l'état de session, puis passage à l'étape Review.
Place dans le pipeline : première étape ; appelle io.readers puis detection.pipeline.detect.
"""

import hashlib
from dataclasses import fields
from pathlib import Path

import streamlit as st

from app.engine import prepare_engine
from app.i18n import t
from app.sidebar import build_config
from app.state import (
    KEY_DETECTIONS,
    KEY_PASTE_WIDGET,
    KEY_READ_ERROR,
    KEY_READ_WARNINGS,
    KEY_SIGNATURE,
    KEY_SOURCE_NAME,
    KEY_SOURCE_TEXT,
    KEY_UPLOAD_NONCE,
    STEP_REVIEW,
    clear_results,
    go_to,
)
from app.ui_common import entity_badge_html, is_public_demo, literal_markdown
from huisclos.config import DetectionConfig
from huisclos.detection.pipeline import detect
from huisclos.io.readers import DocumentReadError, read_document, read_pasted_text
from huisclos.models import EntityType

SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "samples" / "demo_case_fr.txt"
UPLOAD_TYPES = ["txt", "docx", "pdf"]


def detection_signature(text: str, config: DetectionConfig) -> str:
    """Renvoie l'empreinte du texte et de la configuration, pour ne recalculer qu'au besoin.

    Les types activés sont triés : l'ordre d'un frozenset ne doit pas changer l'empreinte.
    """
    parts = []
    for item in fields(config):
        value = getattr(config, item.name)
        if isinstance(value, frozenset):
            value = sorted(member.value for member in value)
        parts.append((item.name, value))
    return hashlib.sha256(f"{text}\0{parts!r}".encode()).hexdigest()


def _set_source(text: str, name: str, warnings: tuple[str, ...] = ()) -> None:
    """Enregistre le texte à traiter et le recopie dans la zone de saisie.

    À appeler depuis un rappel (on_click ou on_change), avant que la zone de saisie ne soit
    recréée : c'est le seul moment où l'on peut modifier la valeur d'un composant.
    """
    st.session_state[KEY_SOURCE_TEXT] = text
    st.session_state[KEY_SOURCE_NAME] = name
    st.session_state[KEY_PASTE_WIDGET] = text
    st.session_state[KEY_READ_ERROR] = None
    st.session_state[KEY_READ_WARNINGS] = warnings


def _load_bytes(name: str, data: bytes) -> None:
    """Lit un fichier et en fait le texte à traiter ; garde l'ancien texte en cas d'erreur."""
    try:
        result = read_document(name, data)
    except DocumentReadError as error:
        st.session_state[KEY_READ_ERROR] = error.code
        st.session_state[KEY_READ_WARNINGS] = ()
        return
    _set_source(result.text, name, result.warnings)


def _on_paste() -> None:
    """Rappel de la zone de saisie : le texte collé devient le texte à traiter."""
    _set_source(st.session_state[KEY_PASTE_WIDGET], t("import.source.pasted"))


def _on_sample() -> None:
    """Rappel du bouton "Load sample case" : charge le cas fictif de démonstration."""
    try:
        data = SAMPLE_PATH.read_bytes()
    except OSError:
        st.session_state[KEY_READ_ERROR] = "sample_missing"
        return
    _load_bytes(SAMPLE_PATH.name, data)


def _upload_key() -> str:
    """Renvoie la clé du sélecteur de fichier, qui change à chaque remise à zéro."""
    return f"upload_widget_{st.session_state[KEY_UPLOAD_NONCE]}"


def _on_upload() -> None:
    """Rappel du sélecteur de fichier : lit le fichier choisi."""
    uploaded = st.session_state.get(_upload_key())
    if uploaded is not None:
        _load_bytes(uploaded.name, uploaded.getvalue())


def _render_tabs() -> None:
    """Affiche les deux onglets : zone de saisie et sélecteur de fichier."""
    # La zone de saisie perd son état quand on visite une autre page : on la réalimente
    # depuis le texte conservé, avant de la créer.
    st.session_state.setdefault(KEY_PASTE_WIDGET, st.session_state[KEY_SOURCE_TEXT])
    paste_tab, upload_tab = st.tabs([t("import.tab.paste"), t("import.tab.upload")])
    with paste_tab:
        st.text_area(
            t("import.paste.label"),
            placeholder=t("import.paste.placeholder"),
            height=240,
            key=KEY_PASTE_WIDGET,
            on_change=_on_paste,
        )
    with upload_tab:
        st.file_uploader(
            t("import.upload.label"),
            type=UPLOAD_TYPES,
            key=_upload_key(),
            on_change=_on_upload,
        )
        st.caption(t("import.upload.note"))


def _render_source_feedback() -> None:
    """Affiche l'erreur de lecture, les avertissements, le cas fictif et le résumé du texte."""
    code = st.session_state[KEY_READ_ERROR]
    if code:
        st.error(t(f"import.error.{code}"))
    for warning in st.session_state[KEY_READ_WARNINGS]:
        st.warning(t(f"import.warning.{warning}"))
    text = st.session_state[KEY_SOURCE_TEXT]
    if not text.strip():
        st.info(t("import.empty"), icon=":material/upload_file:")
        return
    name = st.session_state[KEY_SOURCE_NAME]
    if name == SAMPLE_PATH.name:
        st.info(t("import.sample.notice"), icon=":material/science:")
    st.caption(t("import.source.summary", name=literal_markdown(name), count=f"{len(text):,}"))


def _run_detection(config: DetectionConfig) -> None:
    """Détecte les données sensibles, sauf si le texte et la configuration n'ont pas changé.

    Quand la détection est refaite, les décisions et les résultats de l'ancienne détection
    sont effacés : ils ne correspondraient plus aux nouvelles positions.
    """
    try:
        text = read_pasted_text(st.session_state[KEY_SOURCE_TEXT]).text
    except DocumentReadError as error:
        st.error(t(f"import.error.{error.code}"))
        return
    signature = detection_signature(text, config)
    unchanged = (
        signature == st.session_state[KEY_SIGNATURE]
        and st.session_state[KEY_DETECTIONS] is not None
    )
    if not unchanged:
        try:
            # Le premier passage charge le modèle de langue (plusieurs secondes) : l'état
            # détaillé dit ce qui se passe plutôt qu'une simple roue.
            with st.status(t("import.detect.spinner")) as status:
                status.write(t("import.detect.step.engine"))
                prepare_engine(config)
                status.write(t("import.detect.step.search"))
                detections = detect(text, config)
                status.update(label=t("import.detect.done"), state="complete")
        except RuntimeError:
            st.error(t("import.error.engine"))
            return
        clear_results()
        st.session_state[KEY_DETECTIONS] = detections
        st.session_state[KEY_SIGNATURE] = signature
    # Le texte normalisé est celui dont les positions sont les bonnes.
    st.session_state[KEY_SOURCE_TEXT] = text
    go_to(STEP_REVIEW)
    st.rerun()


def _render_document_card(config: DetectionConfig) -> None:
    """Carte de saisie : exemple, onglets de saisie, retour de lecture et bouton de détection."""
    with st.container(key="hc-card-import"):
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader(t("import.card.title"), anchor=False)
            st.button(
                t("import.sample.button"),
                key="load_sample",
                on_click=_on_sample,
                icon=":material/description:",
            )
        _render_tabs()
        _render_source_feedback()
        if not config.enabled_types:
            st.warning(t("import.detect.no_types"))
        if st.button(
            t("import.detect.button"),
            key="detect",
            type="primary",
            icon=":material/manage_search:",
            disabled=not config.enabled_types,
        ):
            _run_detection(config)
        st.caption(t("import.detect.note"))


def _render_aside(config: DetectionConfig) -> None:
    """Panneau de droite : types recherchés et garantie de confidentialité."""
    with st.container(key="hc-card-detects"):
        st.subheader(t("import.detects.title"), anchor=False)
        st.caption(t("import.detects.intro"))
        badges = "".join(
            entity_badge_html(kind) for kind in EntityType if kind in config.enabled_types
        )
        st.html(f'<div class="hc-legend">{badges}</div>')
        st.caption(t("import.detects.settings"))
    # Sur la démonstration publique, le texte est traité par le serveur de démonstration :
    # l'encadré ne doit pas promettre un traitement local.
    demo = is_public_demo()
    with st.container(key="hc-card-privacy"):
        icon = ":material/science:" if demo else ":material/lock:"
        title = t("import.privacy.demo.title" if demo else "import.privacy.title")
        st.markdown(f"{icon} **{title}**")
        st.markdown(t("import.privacy.demo" if demo else "import.privacy"))
        st.caption(t("import.privacy.detail"))


def render() -> None:
    """Affiche l'étape Import : saisie à gauche, explications à droite."""
    st.header(t("import.title"), anchor=False)
    st.markdown(t("import.intro"))
    config = build_config()
    main, aside = st.columns([2, 1], gap="medium")
    with main:
        _render_document_card(config)
    with aside:
        _render_aside(config)
