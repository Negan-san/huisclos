"""État de session de l'interface : clés, valeurs initiales, remise à zéro et navigation.

Entrées : st.session_state, que les étapes lisent et écrivent par les constantes KEY_*.
Sorties : init_state(), reset_state(), go_to(), is_step_available() et clear_results().
Place dans le pipeline : relie les étapes Import, Review et Restore, qui n'échangent rien
d'autre qu'à travers cet état.
"""

import streamlit as st

from huisclos.config import default_threshold
from huisclos.models import DEFAULT_ENABLED_TYPES, EntityType

STEP_IMPORT = "import"
STEP_REVIEW = "review"
STEP_RESTORE = "restore"
STEPS = (STEP_IMPORT, STEP_REVIEW, STEP_RESTORE)

# Clés du parcours.
KEY_STEP = "step"
KEY_SOURCE_TEXT = "source_text"
KEY_SOURCE_NAME = "source_name"
KEY_DETECTIONS = "detections"
KEY_SIGNATURE = "detection_signature"
KEY_GROUP_DECISIONS = "group_decisions"
KEY_MANUAL_ENTITIES = "manual_entities"
KEY_PSEUDO_RESULT = "pseudo_result"
KEY_LLM_RESPONSE = "llm_response"
KEY_RESTORE_RESULT = "restore_result"
KEY_LANGUAGE = "language"
KEY_TOKEN_STYLE = "token_style"

# Clés des réglages de la barre latérale et du retour de lecture.
KEY_ENABLED_TYPES = "enabled_types"
KEY_THRESHOLD = "threshold"
KEY_READ_ERROR = "read_error"
KEY_READ_WARNINGS = "read_warnings"
# Zone de saisie de l'étape Import : absente des valeurs initiales, car Streamlit oublie
# son état quand une autre page est affichée et l'étape la réalimente alors elle-même.
KEY_PASTE_WIDGET = "paste_widget"
KEY_UPLOAD_NONCE = "upload_nonce"
KEY_CONFIRM_RESET = "confirm_reset"
KEY_LANGUAGE_NOTICE = "language_notice"

THRESHOLD_MIN = 0.30
THRESHOLD_MAX = 0.95
THRESHOLD_STEP = 0.05


def initial_threshold() -> float:
    """Renvoie le seuil par défaut ramené sur la grille du curseur (0,30 à 0,95, pas de 0,05)."""
    clamped = min(max(default_threshold(), THRESHOLD_MIN), THRESHOLD_MAX)
    return round(round(clamped / THRESHOLD_STEP) * THRESHOLD_STEP, 2)


def _defaults() -> dict[str, object]:
    """Construit les valeurs initiales ; les conteneurs sont neufs à chaque appel."""
    ordered_types = [kind for kind in EntityType if kind in DEFAULT_ENABLED_TYPES]
    return {
        KEY_STEP: STEP_IMPORT,
        KEY_SOURCE_TEXT: "",
        KEY_SOURCE_NAME: "",
        KEY_DETECTIONS: None,
        KEY_SIGNATURE: None,
        KEY_GROUP_DECISIONS: {},
        KEY_MANUAL_ENTITIES: [],
        KEY_PSEUDO_RESULT: None,
        KEY_LLM_RESPONSE: "",
        KEY_RESTORE_RESULT: None,
        KEY_LANGUAGE: "en",
        KEY_TOKEN_STYLE: "fr",
        KEY_ENABLED_TYPES: ordered_types,
        KEY_THRESHOLD: initial_threshold(),
        KEY_READ_ERROR: None,
        KEY_READ_WARNINGS: (),
        KEY_UPLOAD_NONCE: 0,
        KEY_CONFIRM_RESET: False,
        KEY_LANGUAGE_NOTICE: False,
    }


def init_state() -> None:
    """Crée les clés manquantes de la session sans toucher à celles qui existent déjà."""
    for key, value in _defaults().items():
        st.session_state.setdefault(key, value)


def reset_state() -> None:
    """Vide toute la session puis remet les valeurs initiales.

    À appeler depuis un rappel de bouton (on_click), avant que les composants de la page
    ne soient recréés. Le compteur du sélecteur de fichier augmente : une nouvelle clé de
    composant fait oublier le fichier chargé, ce que la simple suppression de l'état ne
    ferait pas.
    """
    nonce = st.session_state.get(KEY_UPLOAD_NONCE, 0) + 1
    st.session_state.clear()
    init_state()
    st.session_state[KEY_UPLOAD_NONCE] = nonce


def clear_results() -> None:
    """Efface tout ce qui dépend des détections : décisions, ajouts, texte et restauration."""
    st.session_state[KEY_GROUP_DECISIONS] = {}
    st.session_state[KEY_MANUAL_ENTITIES] = []
    st.session_state[KEY_PSEUDO_RESULT] = None
    st.session_state[KEY_LLM_RESPONSE] = ""
    st.session_state[KEY_RESTORE_RESULT] = None


def go_to(step: str) -> None:
    """Passe à l'étape donnée ; lève ValueError si le nom n'est pas celui d'une étape."""
    if step not in STEPS:
        raise ValueError(f"étape inconnue : {step!r}")
    st.session_state[KEY_STEP] = step


def is_step_available(step: str) -> bool:
    """Indique si l'étape est accessible.

    Review exige une détection faite, Restore une pseudonymisation faite.
    """
    if step == STEP_REVIEW:
        return st.session_state.get(KEY_DETECTIONS) is not None
    if step == STEP_RESTORE:
        return st.session_state.get(KEY_PSEUDO_RESULT) is not None
    return True
