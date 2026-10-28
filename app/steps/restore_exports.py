"""Téléchargements de l'étape Restore : message contrôlé, réponse restaurée, table locale.

Entrées : le contrôle du contenu sortant, le texte restauré éventuel et la table utilisée.
Sorties : les cinq boutons de téléchargement, regroupés dans une carte, et l'avertissement
qui précède la table. Le message n'est téléchargeable comme prêt pour un LLM que si le
contrôle l'autorise (D-AF-A3-5) ; la table et la réponse restaurée restent locales.
Place dans le pipeline : fin du parcours ; rien n'est écrit sur le disque par l'application,
c'est le navigateur qui enregistre le fichier choisi.
"""

import streamlit as st

from app.i18n import t
from app.steps.restore_check import CheckOutcome
from huisclos.io.writers import to_docx_bytes, to_txt_bytes
from huisclos.models import PseudonymizationResult
from huisclos.pseudonymize.mapping import Mapping

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ICONS = {"txt": ":material/description:", "docx": ":material/article:"}


def stem(mapping: Mapping) -> str:
    """Début commun des noms de fichiers : l'empreinte de la table, jamais le nom du document.

    Le nom du document source peut contenir celui d'un client, et le texte pseudonymisé part
    chez un tiers ; l'empreinte relie quand même le texte, sa table et la restauration.
    """
    return f"huisclos-{mapping.pseudonymized_sha256[:8]}"


def _text_downloads(kind: str, text: str, name: str, disabled: bool) -> None:
    """Crée les boutons .txt et .docx d'un texte ; kind vaut "message" ou "restored".

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
            file_name=f"{name}.{kind}.{extension}",
            mime=mime,
            key=f"download_{kind}_{extension}",
            on_click="ignore",
            disabled=disabled,
            icon=ICONS[extension],
            width="stretch",
        )


def render_downloads(
    result: PseudonymizationResult,
    restored_text: str | None,
    used: Mapping,
    outcome: CheckOutcome,
) -> None:
    """Carte des téléchargements : message contrôlé, réponse restaurée, puis la table.

    Paramètres : result, la pseudonymisation du document ; restored_text, le texte restauré
    à jour ou None ; used, la table qui a servi à restaurer (son empreinte nomme le fichier) ;
    outcome, le contrôle du message, dont le contenu exact est le seul téléchargé pour un LLM.
    """
    with st.container(key="hc-card-downloads"):
        st.subheader(t("restore.download.heading"), anchor=False)
        pseudonymized, restored, table = st.columns(3, gap="medium")
        with pseudonymized:
            st.markdown(f"**{t('restore.download.group.message')}**")
            content = outcome.message.content
            _text_downloads("message", content, stem(result.mapping), not outcome.ready)
            if not outcome.ready:
                st.caption(t("restore.download.message_wait"))
        with restored:
            # Un titre distinct de "Restored text", qui annonce le résultat restauré plus haut.
            st.markdown(f"**{t('restore.download.group.restored')}**")
            _text_downloads("restored", restored_text or "", stem(used), restored_text is None)
            if restored_text is None:
                st.caption(t("restore.download.restored_wait"))
        with table:
            st.markdown(f"**{t('restore.download.mapping.heading')}**")
            st.error(t("restore.download.mapping.warning"), icon=":material/key:")
            st.download_button(
                t("restore.download.mapping"),
                result.mapping.to_json().encode("utf-8"),
                file_name=f"{stem(result.mapping)}.mapping.json",
                mime="application/json",
                key="download_mapping",
                on_click="ignore",
                icon=":material/download:",
                width="stretch",
            )
