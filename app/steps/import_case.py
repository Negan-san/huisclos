"""Bloc "Continue a case" de l'étape Import : table d'un document précédent du dossier.

Entrées : le fichier .mapping.json téléversé par l'utilisateur (exporté par l'étape Restore).
Sorties : case_table, case_table_name et case_table_error dans l'état de session.
Place dans le pipeline : avant la détection ; les valeurs de la table sont ensuite cherchées
dans le nouveau texte et gardent leur jeton (D-S24-2). La table n'est jamais écrite sur le
disque ni ajoutée au texte à envoyer.
"""

import streamlit as st

from app.i18n import t
from app.state import (
    KEY_CASE_ERROR,
    KEY_CASE_NAME,
    KEY_CASE_NONCE,
    KEY_CASE_TABLE,
    KEY_UPLOAD_NONCE,
)
from app.ui_common import literal_markdown
from huisclos.pseudonymize.case_memory import TableFileError, read_table_file


def case_upload_key() -> str:
    """Clé du téléverseur : elle change à la remise à zéro et au retrait de la table."""
    return (
        f"case_table_upload_{st.session_state[KEY_UPLOAD_NONCE]}_{st.session_state[KEY_CASE_NONCE]}"
    )


def _on_case_upload() -> None:
    """Rappel du téléverseur : valide le fichier et le garde en mémoire s'il est correct.

    Un fichier refusé laisse la session telle quelle : la table chargée avant reste en
    service et seule l'erreur est affichée. Retirer un fichier refusé efface l'erreur ;
    retirer un fichier accepté retire la table.
    """
    uploaded = st.session_state.get(case_upload_key())
    if uploaded is None:
        if st.session_state[KEY_CASE_ERROR] is None:
            _clear_case()
        st.session_state[KEY_CASE_ERROR] = None
        return
    try:
        table = read_table_file(uploaded.getvalue())
    except TableFileError as error:
        st.session_state[KEY_CASE_ERROR] = error.code
        return
    st.session_state[KEY_CASE_TABLE] = table
    st.session_state[KEY_CASE_NAME] = uploaded.name
    st.session_state[KEY_CASE_ERROR] = None


def _clear_case() -> None:
    """Oublie la table de dossier et son nom."""
    st.session_state[KEY_CASE_TABLE] = None
    st.session_state[KEY_CASE_NAME] = ""


def _on_remove() -> None:
    """Rappel du bouton de retrait : oublie la table et vide le téléverseur (nouvelle clé)."""
    _clear_case()
    st.session_state[KEY_CASE_ERROR] = None
    st.session_state[KEY_CASE_NONCE] += 1


def render_case_table() -> None:
    """Affiche le bloc facultatif de table de dossier, ouvert dès qu'il y a quelque chose à lire."""
    table = st.session_state[KEY_CASE_TABLE]
    error = st.session_state[KEY_CASE_ERROR]
    opened = table is not None or error is not None
    with st.expander(t("import.case.heading"), expanded=opened, icon=":material/folder_open:"):
        st.caption(t("import.case.help"))
        st.file_uploader(
            t("import.case.upload"),
            type=["json"],
            key=case_upload_key(),
            on_change=_on_case_upload,
        )
        if error is not None:
            st.error(t(f"import.case.error.{error}"))
            if table is not None:
                st.caption(t("import.case.kept"))
        if table is None:
            return
        name = literal_markdown(st.session_state[KEY_CASE_NAME])
        st.info(
            t("import.case.loaded", name=name, count=len(table.entities)), icon=":material/key:"
        )
        st.caption(t("import.case.style"))
        st.button(
            t("import.case.remove"), key="case_remove", on_click=_on_remove, icon=":material/close:"
        )
