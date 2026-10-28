"""Étape Restore : texte à envoyer, restauration de la réponse, exports et remise à zéro.

Entrées : pseudo_result dans l'état de session, la réponse du LLM collée par l'utilisateur et,
facultativement, une table de correspondance JSON téléversée.
Sorties : restore_result dans l'état, le texte restauré affiché et les cinq téléchargements
(texte pseudonymisé et texte restauré en .txt et .docx, table en .json).
Place dans le pipeline : troisième et dernière étape ; appelle pseudonymize.reidentify.restore.
"""

from collections import Counter
from dataclasses import dataclass

import streamlit as st

from app.components.highlight import render_restored
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
from app.steps.restore_exports import render_downloads
from app.steps.restore_mistral import KEY_ANSWER_WIDGET, render_mistral_slot
from app.ui_common import entity_label, literal_markdown
from huisclos.models import EntityType, Occurrence, PseudonymizationResult
from huisclos.pseudonymize.mapping import Mapping, MappingError, sha256_of
from huisclos.pseudonymize.reidentify import RestoreResult, restore

# Clés propres à cette étape ; reset_state() les efface avec le reste de la session.
KEY_RESTORE_SIGNATURE = "restore_signature"
KEY_CONFIRM_NEW = "restore_confirm_new"

# Au-delà, le texte s'affiche dans un cadre à hauteur fixe qui défile. Le texte à envoyer
# défile plus tôt, pour que les deux colonnes de l'étape restent de hauteur comparable.
LONG_TEXT_CHARS = 4000
LONG_TEXT_HEIGHT = 420
SEND_TEXT_CHARS = 1200
SEND_TEXT_HEIGHT = 360


@dataclass(frozen=True)
class ActiveTable:
    """Table utilisée pour restaurer : celle du document, ou celle d'un fichier téléversé.

    occurrences n'est renseigné que pour la table du document ; file_name vaut None dans ce cas.
    """

    mapping: Mapping
    occurrences: tuple[Occurrence, ...] | None
    file_name: str | None


def _show_text(text: str, limit: int = LONG_TEXT_CHARS, height: int = LONG_TEXT_HEIGHT) -> None:
    """Affiche un texte dans un bloc de code : bouton de copie intégré, retour à la ligne.

    Au-delà de limit caractères, le bloc prend la hauteur fixe height et défile. Streamlit
    retire les espaces et sauts de ligne de début et de fin à l'affichage ; les
    téléchargements, eux, contiennent le texte complet.
    """
    st.code(
        text, language=None, wrap_lines=True, height="content" if len(text) <= limit else height
    )


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
    """Carte 1 : texte pseudonymisé à copier, consignes à coller avec lui, jetons par type."""
    with st.container(key="hc-card-send"):
        st.subheader(t("restore.send.heading"), anchor=False)
        st.markdown(t("restore.send.intro"))
        if result.warnings:
            st.warning(t("restore.send.literal_tokens"))
        _show_text(result.text, SEND_TEXT_CHARS, SEND_TEXT_HEIGHT)
        st.caption(t("restore.send.copy"))
        st.info(t("restore.send.leaves"), icon=":material/lock:")
        st.caption(t("restore.send.check"))
        st.markdown(f"**{t('restore.send.instruction.heading')}**")
        st.caption(t("restore.send.instruction.help"))
        for language in ("fr", "en"):
            st.caption(t(f"restore.send.instruction.{language}.label"))
            st.code(t(f"restore.send.instruction.{language}"), language=None, wrap_lines=True)
        rows = _token_rows(result)
        with st.expander(t("restore.send.counts.heading"), icon=":material/token:"):
            st.dataframe(rows, hide_index=True, width="stretch")


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
    Sans document dans la session, le bloc est ouvert : c'est le seul moyen de restaurer.
    """
    uploaded_table = st.session_state.get(KEY_UPLOADED_TABLE)
    error = st.session_state.get(KEY_TABLE_ERROR)
    opened = result is None or uploaded_table is not None or error is not None
    with st.expander(t("restore.table.heading"), expanded=opened, icon=":material/key:"):
        st.caption(t("restore.table.help"))
        st.file_uploader(
            t("restore.table.upload"),
            type=["json"],
            key=f"restore_table_upload_{st.session_state[KEY_UPLOAD_NONCE]}",
            on_change=_keep_uploaded_table,
        )
        if error is not None:
            st.error(t(f"restore.table.error.{error}"))
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


def _restored_values(restored: RestoreResult, mapping: Mapping) -> dict[str, EntityType]:
    """Formes réelles que la restauration a pu remettre, avec leur type, pour le surlignage."""
    kinds = {entry.token: entry.entity_type for entry in mapping.entities if entry.token}
    values: dict[str, EntityType] = {}
    for entry in mapping.entities:
        if entry.token in restored.replaced:
            for form in (entry.canonical, *entry.variants):
                values[form] = entry.entity_type
    for occurrence in mapping.occurrences:
        if occurrence.token in restored.replaced:
            values[occurrence.original] = kinds[occurrence.token]
    return values


def _show_notices(restored: RestoreResult) -> None:
    """Affiche le mode de restauration et les jetons inconnus, altérés ou absents."""
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


def _show_restored(restored: RestoreResult, table: ActiveTable) -> None:
    """Carte du résultat : texte restauré surligné, texte brut à copier, puis les messages."""
    with st.container(key="hc-card-restored"):
        st.markdown(f"**{t('restore.answer.restored_heading')}**")
        highlighted, plain = st.tabs([t("restore.tab.highlighted"), t("restore.tab.plain")])
        with highlighted:
            st.caption(t("restore.highlight.note"))
            values = _restored_values(restored, table.mapping)
            height = "content" if len(restored.text) <= LONG_TEXT_CHARS else LONG_TEXT_HEIGHT
            with st.container(height=height, key="hc-document-restored"):
                st.html(render_restored(restored.text, values))
        with plain:
            _show_text(restored.text)
        _show_notices(restored)


def _render_answer(table: ActiveTable) -> RestoreResult | None:
    """Zone de collage et bouton Restore ; renvoie le résultat s'il est à jour."""
    st.session_state.setdefault(KEY_ANSWER_WIDGET, st.session_state[KEY_LLM_RESPONSE])
    st.text_area(
        t("restore.answer.label"),
        placeholder=t("restore.answer.placeholder"),
        height=240,
        key=KEY_ANSWER_WIDGET,
        on_change=_keep_answer,
    )
    answer = st.session_state[KEY_ANSWER_WIDGET]
    if st.button(
        t("restore.answer.button"),
        key="restore_run",
        type="primary",
        icon=":material/settings_backup_restore:",
    ):
        if answer.strip():
            st.session_state[KEY_RESTORE_RESULT] = restore(answer, table.mapping, table.occurrences)
            st.session_state[KEY_RESTORE_SIGNATURE] = _signature(table, answer)
        else:
            st.warning(t("restore.answer.empty"))
    restored = st.session_state[KEY_RESTORE_RESULT]
    # Une réponse modifiée ou une autre table rendent l'ancien résultat trompeur : il est masqué.
    if restored is None or st.session_state.get(KEY_RESTORE_SIGNATURE) != _signature(table, answer):
        return None
    return restored


def _render_answer_card(
    result: PseudonymizationResult | None,
) -> tuple[ActiveTable | None, RestoreResult | None]:
    """Carte 2 : table facultative, réponse collée et bouton Restore."""
    with st.container(key="hc-card-answer"):
        st.subheader(t("restore.answer.heading"), anchor=False)
        table = _render_table_upload(result)
        restored = _render_answer(table) if table is not None else None
    return table, restored


def _ask_new_document() -> None:
    """Rappel du bouton de nouveau document : demande une confirmation."""
    st.session_state[KEY_CONFIRM_NEW] = True


def _cancel_new_document() -> None:
    """Rappel du bouton d'annulation : retire la demande de confirmation."""
    st.session_state[KEY_CONFIRM_NEW] = False


def _render_new_document(with_review: bool) -> None:
    """Barre de fin : retour à Review et remise à zéro de la session, après confirmation."""
    with st.container(key="hc-card-end"):
        if st.session_state.get(KEY_CONFIRM_NEW):
            st.warning(t("restore.new.confirm"))
            with st.container(horizontal=True):
                st.button(
                    t("restore.new.yes"),
                    key="restore_new_confirm",
                    on_click=reset_state,
                    type="primary",
                )
                st.button(
                    t("restore.new.cancel"), key="restore_new_cancel", on_click=_cancel_new_document
                )
            return
        st.caption(t("restore.new.note"))
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            if with_review:
                st.button(
                    t("restore.back_review"),
                    key="restore_back_review",
                    on_click=go_to,
                    args=(STEP_REVIEW,),
                    icon=":material/arrow_back:",
                )
            st.button(
                t("restore.new.button"),
                key="restore_new",
                on_click=_ask_new_document,
                icon=":material/note_add:",
            )


def render() -> None:
    """Affiche l'étape Restore.

    Sans pseudonymisation, seul l'import d'une table enregistrée permet de restaurer une
    réponse reçue plus tard.
    """
    st.header(t("restore.title"), anchor=False)
    result = st.session_state[KEY_PSEUDO_RESULT]
    if result is None:
        st.info(t("restore.empty"), icon=":material/inbox:")
        st.button(t("restore.back"), key="restore_back", on_click=go_to, args=(STEP_IMPORT,))
        table, restored = _render_answer_card(None)
    else:
        send, answer = st.columns(2, gap="medium")
        with send:
            _render_send(result)
        with answer:
            table, restored = _render_answer_card(result)
    if restored is not None and table is not None:
        _show_restored(restored, table)
    if result is not None:
        used = table.mapping if table is not None else result.mapping
        render_downloads(result, restored.text if restored is not None else None, used)
        render_mistral_slot(result.text)
    _render_new_document(result is not None)
