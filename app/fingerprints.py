"""Empreintes communes de l'interface : détection, décisions de revue, contrôle et envoi.

Entrées : st.session_state (texte, table de dossier, décisions, ajouts, style des jetons) et
la configuration de la barre latérale.
Sorties : des empreintes SHA-256 et staleness(), qui dit si le texte pseudonymisé affiché
correspond encore aux réglages, au texte et aux décisions courants (D-AF-A3-2).
Place dans le pipeline : lues par Import, Review et Restore ; un résultat dont l'empreinte a
changé ne peut plus être présenté comme vérifié ni envoyé.
"""

import hashlib
from dataclasses import fields

import streamlit as st

from app.sidebar import build_config
from app.state import (
    KEY_CASE_TABLE,
    KEY_DETECTIONS,
    KEY_GROUP_DECISIONS,
    KEY_MANUAL_ENTITIES,
    KEY_PSEUDO_BASIS,
    KEY_PSEUDO_RESULT,
    KEY_SIGNATURE,
    KEY_SOURCE_TEXT,
    KEY_TOKEN_STYLE,
)
from huisclos.config import DetectionConfig
from huisclos.detection.pipeline import model_identity
from huisclos.pseudonymize.mapping import Mapping, sha256_of
from huisclos.pseudonymize.outbound_check import CHECK_VERSION


def _digest(*parts: object) -> str:
    """Empreinte SHA-256 de valeurs simples, séparées par un caractère nul."""
    raw = "\0".join(repr(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def config_parts(config: DetectionConfig) -> list[tuple[str, object]]:
    """Tous les champs de la configuration, types triés, puis l'identité des modèles.

    L'ordre d'un frozenset ne doit pas changer l'empreinte ; le modèle et sa révision en
    font partie, pour qu'un autre modèle refasse la détection.
    """
    parts: list[tuple[str, object]] = []
    for item in fields(config):
        value = getattr(config, item.name)
        if isinstance(value, frozenset):
            value = sorted(member.value for member in value)
        parts.append((item.name, value))
    parts.append(("models", model_identity(config)))
    return parts


def detection_signature(text: str, config: DetectionConfig, table: Mapping | None = None) -> str:
    """Empreinte du texte, de la configuration complète, des modèles et de la table de dossier.

    Changer la langue du document, le profil, les types, le seuil, la table ou le texte
    change l'empreinte : l'ancienne détection ne vaut plus pour ces réglages.
    """
    case = sha256_of(table.to_json()) if table is not None else ""
    return _digest(text, config_parts(config), case)


def current_detection_signature() -> str:
    """Empreinte que donnerait une détection faite maintenant, avec les réglages affichés."""
    return detection_signature(
        st.session_state[KEY_SOURCE_TEXT], build_config(), st.session_state[KEY_CASE_TABLE]
    )


def decisions_fingerprint() -> str:
    """Empreinte des décisions de revue, des ajouts manuels et du style des jetons."""
    decisions = sorted(
        (span, decision.masked, decision.entity_type.value if decision.entity_type else "")
        for span, decision in st.session_state[KEY_GROUP_DECISIONS].items()
    )
    manual = sorted(
        (d.start, d.end, d.entity_type.value, d.text) for d in st.session_state[KEY_MANUAL_ENTITIES]
    )
    return _digest(decisions, manual, st.session_state[KEY_TOKEN_STYLE])


def pseudonymization_basis() -> tuple[str | None, str]:
    """Base d'une pseudonymisation : empreinte de la détection et empreinte des décisions."""
    return st.session_state[KEY_SIGNATURE], decisions_fingerprint()


def staleness() -> str | None:
    """Dit pourquoi le texte pseudonymisé ne correspond plus à l'état courant, ou None.

    Valeur retournée : "detection" si le texte, un réglage de détection ou la table a changé
    depuis la détection (ou si aucune détection n'est connue) ; "review" si les décisions ou
    le style des jetons ont changé depuis la pseudonymisation ; None si tout est à jour.
    """
    if st.session_state.get(KEY_PSEUDO_RESULT) is None:
        return "detection"
    signature = st.session_state.get(KEY_SIGNATURE)
    if st.session_state.get(KEY_DETECTIONS) is None or signature != current_detection_signature():
        return "detection"
    if st.session_state.get(KEY_PSEUDO_BASIS) != pseudonymization_basis():
        return "review"
    return None


def check_parameters(check_config: DetectionConfig) -> str:
    """Empreinte des réglages du contrôle : version, détection, décisions et configuration.

    La table de dossier est comprise dans l'empreinte de détection ; le texte contrôlé et la
    consigne s'y ajoutent dans les empreintes de segment et d'envoi.
    """
    return _digest(
        CHECK_VERSION,
        st.session_state[KEY_SIGNATURE],
        decisions_fingerprint(),
        config_parts(check_config),
    )
