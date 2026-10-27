"""Étape Restore : texte à envoyer, restauration de la réponse, exports et remise à zéro.

Entrées : pseudo_result dans l'état de session, la réponse du LLM collée par l'utilisateur et,
facultativement, une table de correspondance JSON téléversée.
Sorties : restore_result dans l'état, le texte restauré affiché et les cinq téléchargements
(texte pseudonymisé et texte restauré en .txt et .docx, table en .json).
Place dans le pipeline : troisième et dernière étape ; appelle pseudonymize.reidentify.restore.
"""

import os
from collections import Counter
from dataclasses import dataclass

import streamlit as st

from app.i18n import t
from app.state import (
    KEY_LLM_RESPONSE,
    KEY_PSEUDO_RESULT,
    KEY_RESTORE_RESULT,
    KEY_TABLE_ERROR,
    KEY_UPLOAD_NONCE,
    KEY_UPLOADED_TABLE,
    STEP_IMPORT,
    STEP_REVIEW,
    go_to,
    reset_state,
)
from app.ui_common import entity_label, literal_markdown
from huisclos.io.writers import to_docx_bytes, to_txt_bytes
from huisclos.llm.mistral_client import DEFAULT_MODEL, MistralError, send_pseudonymized
from huisclos.models import EntityType, Occurrence, PseudonymizationResult
from huisclos.pseudonymize.mapping import Mapping, MappingError, sha256_of
from huisclos.pseudonymize.reidentify import RestoreResult, restore

# Clés propres à cette étape ; reset_state() les efface avec le reste de la session.
KEY_ANSWER_WIDGET = "restore_answer"
KEY_RESTORE_SIGNATURE = "restore_signature"
KEY_CONFIRM_NEW = "restore_confirm_new"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# Au-delà, le texte s'affiche dans un cadre à hauteur fixe qui défile.
LONG_TEXT_CHARS = 4000
LONG_TEXT_HEIGHT = 420


@dataclass(frozen=True)
class ActiveTable:
    """Table utilisée pour restaurer : celle du document, ou celle d'un fichier téléversé.

    occurrences n'est renseigné que pour la table du document ; file_name vaut None dans ce cas.
    """

    mapping: Mapping
    occurrences: tuple[Occurrence, ...] | None
    file_name: str | None


def _show_text(text: str) -> None:
    """Affiche un texte dans un bloc de code : bouton de copie intégré, retour à la ligne.

    Streamlit retire les espaces et sauts de ligne de début et de fin à l'affichage ; les
    téléchargements, eux, contiennent le texte complet.
    """
    height = "content" if len(text) <= LONG_TEXT_CHARS else LONG_TEXT_HEIGHT
    st.code(text, language=None, wrap_lines=True, height=height)


def _token_rows(result: PseudonymizationResult) -> list[dict[str, object]]:
    """Compte, par type d'entité, les jetons distincts et leurs occurrences dans le texte."""
    per_token = Counter(occurrence.token for occurrence in result.occurrences)
    rows: list[dict[str, object]] = []
    for kind in EntityType:
        groups = [group for group in result.groups if group.entity_type is kind]
        if groups:
            rows.append(
                {
                    t("restore.send.counts.type"): entity_label(kind),
                    t("restore.send.counts.tokens"): len(groups),
                    t("restore.send.counts.occurrences"): sum(per_token[g.token] for g in groups),
                }
            )
    return rows


def _render_send(result: PseudonymizationResult) -> None:
    """Bloc 1 : texte pseudonymisé à copier, jetons par type, consignes à coller avec lui."""
    st.subheader(t("restore.send.heading"))
    st.markdown(t("restore.send.intro"))
    if result.warnings:
        st.warning(t("restore.send.literal_tokens"))
    _show_text(result.text)
    st.info(t("restore.send.leaves"))
    st.caption(t("restore.send.check"))
    st.markdown(f"**{t('restore.send.counts.heading')}**")
    st.dataframe(_token_rows(result), hide_index=True)
    st.markdown(f"**{t('restore.send.instruction.heading')}**")
    st.caption(t("restore.send.instruction.help"))
    for language in ("fr", "en"):
        st.caption(t(f"restore.send.instruction.{language}.label"))
        st.code(t(f"restore.send.instruction.{language}"), language=None, wrap_lines=True)


def _keep_uploaded_table() -> None:
    """Conserve la table et son erreur en mémoire quand le téléverseur disparaît d'une page."""
    key = f"restore_table_upload_{st.session_state[KEY_UPLOAD_NONCE]}"
    uploaded = st.session_state.get(key)
    st.session_state[KEY_UPLOADED_TABLE] = None
    st.session_state[KEY_TABLE_ERROR] = None
    if uploaded is None:
        return
    try:
        mapping = Mapping.from_json(uploaded.getvalue().decode("utf-8-sig"))
    except UnicodeDecodeError:
        st.session_state[KEY_TABLE_ERROR] = "encoding"
    except (MappingError, ValueError, RecursionError):
        st.session_state[KEY_TABLE_ERROR] = "invalid"
    else:
        st.session_state[KEY_UPLOADED_TABLE] = ActiveTable(mapping, None, uploaded.name)


def _render_table_upload(result: PseudonymizationResult | None) -> ActiveTable | None:
    """Propose l'import facultatif d'une table JSON et renvoie la table à utiliser.

    Le fichier téléversé remplace la table du document. Une erreur de lecture est affichée en
    langage clair et ne lève jamais d'exception ; la table du document reste alors utilisée.
    """
    st.markdown(f"**{t('restore.table.heading')}**")
    st.caption(t("restore.table.help"))
    st.file_uploader(
        t("restore.table.upload"),
        type=["json"],
        key=f"restore_table_upload_{st.session_state[KEY_UPLOAD_NONCE]}",
        on_change=_keep_uploaded_table,
    )
    error = st.session_state.get(KEY_TABLE_ERROR)
    if error is not None:
        st.error(t(f"restore.table.error.{error}"))
    uploaded_table = st.session_state.get(KEY_UPLOADED_TABLE)
    if uploaded_table is not None:
        st.caption(t("restore.table.in_use_file", name=literal_markdown(uploaded_table.file_name)))
        return uploaded_table
    if result is None:
        return None
    st.caption(t("restore.table.in_use_document"))
    return ActiveTable(result.mapping, result.occurrences, None)


def _signature(table: ActiveTable, answer: str) -> str:
    """Empreinte de la table et de la réponse, pour ne montrer que la restauration à jour."""
    return sha256_of(f"{table.mapping.to_json()}\0{answer}")


def _keep_answer() -> None:
    """Rappel de la zone de collage : conserve la réponse quand le composant est recréé."""
    st.session_state[KEY_LLM_RESPONSE] = st.session_state[KEY_ANSWER_WIDGET]


def _forms(items: list[str]) -> str:
    """Met chaque forme de jeton entre accents graves, sans doublon, séparées par des virgules."""
    return ", ".join(f"`{item}`" for item in dict.fromkeys(items))


def _show_restored(restored: RestoreResult) -> None:
    """Affiche le texte restauré, son mode, les jetons inconnus, altérés ou absents."""
    st.markdown(f"**{t('restore.answer.restored_heading')}**")
    _show_text(restored.text)
    st.caption(t(f"restore.mode.{restored.mode}"))
    if not restored.replaced and not restored.unknown:
        st.info(t("restore.none_found"))
    if restored.unknown:
        forms = [form for form, _ in restored.unknown]
        st.warning(t("restore.unknown", count=len(set(forms)), forms=_forms(forms)))
    if restored.altered:
        pairs = list(dict.fromkeys(restored.altered))
        shown = ", ".join(
            t("restore.altered.pair", found=f"`{found}`", token=f"`{token}`")
            for found, token in pairs
        )
        st.info(t("restore.altered", count=len(pairs), pairs=shown))
    if restored.missing:
        st.caption(t("restore.missing", tokens=_forms(restored.missing)))


def _render_answer(table: ActiveTable) -> RestoreResult | None:
    """Bloc 2, partie réponse : zone de collage, bouton Restore, résultat à jour."""
    st.session_state.setdefault(KEY_ANSWER_WIDGET, st.session_state[KEY_LLM_RESPONSE])
    st.text_area(
        t("restore.answer.label"),
        placeholder=t("restore.answer.placeholder"),
        height=200,
        key=KEY_ANSWER_WIDGET,
        on_change=_keep_answer,
    )
    answer = st.session_state[KEY_ANSWER_WIDGET]
    if st.button(t("restore.answer.button"), key="restore_run", type="primary"):
        if answer.strip():
            st.session_state[KEY_RESTORE_RESULT] = restore(answer, table.mapping, table.occurrences)
            st.session_state[KEY_RESTORE_SIGNATURE] = _signature(table, answer)
        else:
            st.warning(t("restore.answer.empty"))
    restored = st.session_state[KEY_RESTORE_RESULT]
    # Une réponse modifiée ou une autre table rendent l'ancien résultat trompeur : il est masqué.
    if restored is None or st.session_state.get(KEY_RESTORE_SIGNATURE) != _signature(table, answer):
        return None
    _show_restored(restored)
    return restored


def _stem(mapping: Mapping) -> str:
    """Début commun des noms de fichiers : l'empreinte de la table, jamais le nom du document.

    Le nom du document source peut contenir celui d'un client, et le texte pseudonymisé part
    chez un tiers ; l'empreinte relie quand même le texte, sa table et la restauration.
    """
    return f"huisclos-{mapping.pseudonymized_sha256[:8]}"


def _text_downloads(kind: str, text: str, stem: str, disabled: bool) -> None:
    """Crée les boutons .txt et .docx d'un texte ; kind vaut "pseudonymized" ou "restored".

    Les boutons ne relancent pas la page. Le .docx est fabriqué au clic, pas à l'affichage.
    """
    title = t(f"restore.docx.title.{kind}")
    for extension, data, mime in (
        ("txt", to_txt_bytes(text), "text/plain"),
        ("docx", lambda: to_docx_bytes(text, title), DOCX_MIME),
    ):
        st.download_button(
            t(f"restore.download.{kind}_{extension}"),
            data,
            file_name=f"{stem}.{kind}.{extension}",
            mime=mime,
            key=f"download_{kind}_{extension}",
            on_click="ignore",
            disabled=disabled,
        )


def _render_downloads(
    result: PseudonymizationResult, restored: RestoreResult | None, table: ActiveTable | None
) -> None:
    """Bloc 3 : textes en .txt et .docx, puis la table avec son avertissement en rouge."""
    st.subheader(t("restore.download.heading"))
    left, right = st.columns(2)
    with left:
        _text_downloads("pseudonymized", result.text, _stem(result.mapping), False)
    with right:
        used = table.mapping if table is not None else result.mapping
        text = restored.text if restored is not None else ""
        _text_downloads("restored", text, _stem(used), restored is None)
        if restored is None:
            st.caption(t("restore.download.restored_wait"))
    st.error(t("restore.download.mapping.warning"))
    st.download_button(
        t("restore.download.mapping"),
        result.mapping.to_json().encode("utf-8"),
        file_name=f"{_stem(result.mapping)}.mapping.json",
        mime="application/json",
        key="download_mapping",
        on_click="ignore",
    )


def render_mistral_slot(pseudonymized_text: str) -> None:
    """Affiche l'envoi facultatif du seul texte fourni, si une clé est configurée.

    La confirmation porte sur ce texte et cette consigne ; une modification la révoque.
    La réponse remplit la zone de restauration au prochain affichage.
    """
    try:
        api_key = st.secrets["MISTRAL_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = None
    api_key = api_key or os.environ.get("MISTRAL_API_KEY")
    if not isinstance(api_key, str) or not api_key.strip():
        return
    st.subheader(t("mistral.heading"))
    st.warning(t("mistral.warning"))
    instruction = st.text_area(t("mistral.instruction"), key="mistral_instruction")
    signature = sha256_of(pseudonymized_text + "\0" + instruction)
    if st.session_state.get("mistral_signature") != signature:
        st.session_state["mistral_confirm"] = False
        st.session_state["mistral_signature"] = signature
    confirmed = st.checkbox(t("mistral.confirm"), value=False, key="mistral_confirm")
    if st.button(t("mistral.send"), key="mistral_send", disabled=not confirmed) and confirmed:
        try:
            with st.spinner(t("mistral.spinner")):
                answer = send_pseudonymized(pseudonymized_text, instruction, api_key, DEFAULT_MODEL)
        except MistralError as error:
            st.error(t(f"mistral.error.{error.code}"))
        else:
            st.session_state[KEY_LLM_RESPONSE] = answer
            # La zone de réponse a déjà été créée plus haut dans cette exécution.
            st.session_state.pop(KEY_ANSWER_WIDGET, None)
            st.session_state[KEY_RESTORE_RESULT] = None
            st.rerun()


def _ask_new_document() -> None:
    """Rappel du bouton de nouveau document : demande une confirmation."""
    st.session_state[KEY_CONFIRM_NEW] = True


def _cancel_new_document() -> None:
    """Rappel du bouton d'annulation : retire la demande de confirmation."""
    st.session_state[KEY_CONFIRM_NEW] = False


def _render_new_document() -> None:
    """Bloc 4 : remise à zéro de la session, après confirmation."""
    st.divider()
    if not st.session_state.get(KEY_CONFIRM_NEW):
        st.caption(t("restore.new.note"))
        st.button(t("restore.new.button"), key="restore_new", on_click=_ask_new_document)
        return
    st.warning(t("restore.new.confirm"))
    yes, cancel = st.columns(2)
    yes.button(
        t("restore.new.yes"), key="restore_new_confirm", on_click=reset_state, type="primary"
    )
    cancel.button(t("restore.new.cancel"), key="restore_new_cancel", on_click=_cancel_new_document)


def render() -> None:
    """Affiche l'étape Restore.

    Sans pseudonymisation, seul l'import d'une table enregistrée permet de restaurer une
    réponse reçue plus tard.
    """
    st.header(t("restore.title"))
    result = st.session_state[KEY_PSEUDO_RESULT]
    if result is None:
        st.info(t("restore.empty"))
        st.button(t("restore.back"), key="restore_back", on_click=go_to, args=(STEP_IMPORT,))
    else:
        _render_send(result)
    st.subheader(t("restore.answer.heading"))
    table = _render_table_upload(result)
    restored = _render_answer(table) if table is not None else None
    if result is not None:
        _render_downloads(result, restored, table)
        render_mistral_slot(result.text)
        st.button(
            t("restore.back_review"), key="restore_back_review", on_click=go_to, args=(STEP_REVIEW,)
        )
    _render_new_document()
