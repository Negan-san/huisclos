"""Étape Import : texte collé, fichier ou cas d'exemple, puis détection des données sensibles.

Entrées : texte saisi, fichier TXT, DOCX ou PDF, ou data/samples/demo_case_fr.txt ; la
configuration de détection de la barre latérale ; la table de dossier facultative.
Sorties : source_text et detections dans l'état de session, puis passage à l'étape Review.
Place dans le pipeline : première étape ; appelle io.readers puis detection.pipeline.detect.
"""

from pathlib import Path

import streamlit as st

from app.engine import prepare_engine
from app.fingerprints import current_detection_signature, detection_signature
from app.i18n import current_language, t
from app.sidebar import build_config, document_language, selected_profile
from app.state import (
    KEY_CASE_TABLE,
    KEY_DETECTIONS,
    KEY_DOCUMENT_LANGUAGE,
    KEY_PASTE_WIDGET,
    KEY_READ_ERROR,
    KEY_READ_WARNINGS,
    KEY_SIGNATURE,
    KEY_SOURCE_NAME,
    KEY_SOURCE_TEXT,
    KEY_UPLOAD_NONCE,
    STEP_REVIEW,
    clear_check,
    clear_results,
    go_to,
)
from app.steps.import_case import render_case_table
from app.ui_common import entity_badge_html, is_public_demo, literal_markdown
from huisclos.config import DetectionConfig
from huisclos.detection.pipeline import ModelUnavailableError, detect
from huisclos.io.read_quality import warning_parameters
from huisclos.io.readers import DocumentReadError, read_document, read_pasted_text
from huisclos.models import EntityType
from huisclos.pseudonymize.case_memory import find_known

SAMPLE_PATH = Path(__file__).resolve().parents[2] / "data" / "samples" / "demo_case_fr.txt"
UPLOAD_TYPES = ["txt", "docx", "pdf"]
# Avis affiché après le chargement du cas fictif, qui est un document français.
KEY_SAMPLE_NOTICE = "import_sample_language_notice"


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
        st.session_state[KEY_READ_WARNINGS] = error.warnings
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
    # Le cas fictif est un document français, quelle que soit la langue de l'interface ; le
    # changement de langue du document est annoncé, jamais silencieux.
    if st.session_state.get(KEY_DOCUMENT_LANGUAGE) != "fr":
        st.session_state[KEY_DOCUMENT_LANGUAGE] = "fr"
        st.session_state[KEY_SAMPLE_NOTICE] = True


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
        if st.session_state[KEY_SOURCE_TEXT].strip():
            st.caption(t("import.error.previous_kept"))
    for warning in st.session_state[KEY_READ_WARNINGS]:
        warning_code, parameters = warning_parameters(warning)
        st.warning(t(f"import.warning.{warning_code}", **parameters))
    if any(
        warning.startswith(("pdf_", "docx_")) for warning in st.session_state[KEY_READ_WARNINGS]
    ):
        st.caption(t("import.warning.extraction_scope"))
    text = st.session_state[KEY_SOURCE_TEXT]
    if not text.strip():
        st.info(t("import.empty"), icon=":material/upload_file:")
        return
    name = st.session_state[KEY_SOURCE_NAME]
    if name == SAMPLE_PATH.name:
        st.info(t("import.sample.notice"), icon=":material/science:")
    if st.session_state.pop(KEY_SAMPLE_NOTICE, False):
        st.info(t("import.sample.language"), icon=":material/translate:")
    st.caption(t("import.source.summary", name=literal_markdown(name), count=_count(len(text))))


def _count(number: int) -> str:
    """Écrit un nombre avec le séparateur de milliers de la langue : 2,057 ou 2 057.

    En français, la virgule est le séparateur décimal ; les milliers sont séparés par une
    espace fine insécable.
    """
    written = f"{number:,}"
    return written.replace(",", "\u202f") if current_language() == "fr" else written


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
    table = st.session_state[KEY_CASE_TABLE]
    signature = detection_signature(text, config, table)
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
                known = find_known(text, table) if table is not None else []
                if table is not None:
                    status.write(t("import.detect.step.case", count=len(known)))
                detections = detect(text, config, known=known)
                status.update(label=t("import.detect.done"), state="complete")
        except ModelUnavailableError as error:
            # Aucun repli vers un autre profil : l'utilisateur choisit lui-même.
            st.error(t(f"import.error.model.{error.code}"))
            return
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


def _render_stale_notice() -> None:
    """Signale qu'une détection existe mais ne correspond plus au texte ou aux réglages.

    Les décisions et le contrôle déjà faits ne valent plus pour un envoi vérifié : une
    nouvelle détection les remplace, sans accepter d'office les nouvelles propositions.
    """
    if st.session_state[KEY_DETECTIONS] is None or not st.session_state[KEY_SOURCE_TEXT].strip():
        return
    if st.session_state[KEY_SIGNATURE] != current_detection_signature():
        clear_check()
        st.warning(t("import.stale"), icon=":material/update:")


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
        render_case_table()
        if not config.enabled_types:
            st.warning(t("import.detect.no_types"))
        _render_stale_notice()
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
        st.caption(
            t(
                "import.detects.profile",
                language=t(f"sidebar.document_language.{document_language()}"),
                profile=t(f"sidebar.profile.{selected_profile()}"),
            )
        )
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
