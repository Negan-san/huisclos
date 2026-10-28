"""Carte "Final check" de l'étape Restore : contrôle du contenu exact qui quitterait le poste.

Entrées : pseudo_result, la consigne libre, les décisions de Review, la configuration de la
barre latérale et la politique visible du contrôle (types désactivés, liste d'exclusions).
Sorties : evaluate_outbound() compose une seule fois le message, le contrôle et renvoie son
statut et l'empreinte que doit porter une autorisation d'envoi ; render_final_check() affiche
la carte. "Mask everywhere" ajoute la valeur comme entité manuelle et pseudonymise à nouveau.
Place dans le pipeline : entre pseudonymize.tokens et tout envoi ou export (D-S24-3, D-AF-A3-3
à D-AF-A3-5).
"""

from collections.abc import Callable
from dataclasses import dataclass, replace

import streamlit as st

from app.components.highlight import render_highlighted
from app.engine import prepare_engine
from app.fingerprints import check_parameters, staleness
from app.i18n import t
from app.sidebar import build_config
from app.state import (
    KEY_CHECK_ACKS,
    KEY_CHECK_ALL_TYPES,
    KEY_CHECK_DOCUMENT,
    KEY_CHECK_INSTRUCTION,
    KEY_CHECK_NO_EXCLUSIONS,
    KEY_CHECK_NOTICE,
    KEY_DETECTIONS,
    KEY_INSTRUCTION,
    KEY_PSEUDO_RESULT,
    KEY_RESTORE_RESULT,
    KEY_SEND_AUTH,
    KEY_SOURCE_TEXT,
    STEP_IMPORT,
    STEP_REVIEW,
    go_to,
)
from app.steps.review_decisions import (
    add_manual,
    current_detections,
    is_masked,
    pseudonymize_session,
)
from app.steps.review_step import KEY_TABLE_VERSION
from app.ui_common import literal_markdown
from huisclos.config import DetectionConfig
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, PseudonymizationResult, Source
from huisclos.pseudonymize.final_check import check_threshold, excerpt
from huisclos.pseudonymize.mapping import sha256_of
from huisclos.pseudonymize.outbound_check import (
    DOCUMENT,
    SENDABLE,
    Alert,
    CheckStatus,
    DetectText,
    OutboundMessage,
    check_status,
    compose,
    document_alerts,
    instruction_alerts,
    send_fingerprint,
)

# Politique du contrôle : (clé gardée en session, clé du composant, clé de texte).
POLICY = (
    (KEY_CHECK_ALL_TYPES, "check_policy_all_types", "check.policy.all_types"),
    (KEY_CHECK_NO_EXCLUSIONS, "check_policy_no_exclusions", "check.policy.no_exclusions"),
)


@dataclass(frozen=True)
class CheckOutcome:
    """Contrôle du contenu sortant, pour l'affichage, les exports et l'envoi.

    message est la chaîne exacte à envoyer ; stale vaut "detection", "review" ou None ;
    fingerprint est l'empreinte qu'une autorisation d'envoi doit porter, vide tant que le
    contrôle n'est pas terminé ; scope préfixe les décisions explicites de ce contrôle.
    """

    message: OutboundMessage
    status: CheckStatus
    alerts: tuple[Alert, ...]
    stale: str | None
    fingerprint: str
    scope: str

    @property
    def ready(self) -> bool:
        """Vrai si le contenu peut être présenté comme vérifié : statut sûr et empreinte."""
        return self.status in SENDABLE and bool(self.fingerprint)


def check_config() -> DetectionConfig:
    """Configuration du contrôle : seuil abaissé, politique des types et des exclusions visible."""
    config = build_config()
    kinds = frozenset(EntityType) if st.session_state[KEY_CHECK_ALL_TYPES] else config.enabled_types
    return replace(
        config,
        threshold=check_threshold(config.threshold),
        enabled_types=kinds,
        use_exclusions=not st.session_state[KEY_CHECK_NO_EXCLUSIONS],
    )


def _rejected_spans() -> list[tuple[int, int]]:
    """Positions d'origine des mentions rejetées en revue ; seules elles ne sont pas signalées."""
    if st.session_state.get(KEY_DETECTIONS) is None:
        return []
    return [(d.start, d.end) for d in current_detections() if not is_masked(d)]


def _segment(
    key: str,
    fingerprint: str,
    config: DetectionConfig,
    compute: Callable[[DetectText], list[Alert]],
) -> list[Alert] | None:
    """Alertes d'un segment, recalculées seulement si son empreinte a changé.

    Valeur retournée : la liste, vide si rien n'est trouvé, ou None si le contrôle n'a pas
    pu aboutir. L'état "en cours" est enregistré avant le calcul : interrompu, il ne vaut
    jamais un contrôle terminé.
    """
    cached = st.session_state.get(key)
    if cached is not None and cached[0] == fingerprint and cached[1] is not CheckStatus.RUNNING:
        return cached[2]
    st.session_state[key] = (fingerprint, CheckStatus.RUNNING, None)
    try:
        with st.spinner(t("check.spinner")):
            prepare_engine(config)
            alerts = compute(lambda text: detect(text, config))
    except Exception:
        # Moteur absent, modèle refusé ou incohérence : aucune exception ne doit passer pour
        # une absence d'alerte.
        st.session_state[key] = (fingerprint, CheckStatus.UNAVAILABLE, None)
        return None
    st.session_state[key] = (fingerprint, CheckStatus.CLEAR, alerts)
    return alerts


def acknowledged(scope: str) -> frozenset[str]:
    """Mentions gardées en clair par décision explicite, pour ce contrôle seulement."""
    stored = st.session_state.get(KEY_CHECK_ACKS)
    if stored is None or stored[0] != scope:
        return frozenset()
    return frozenset(stored[1])


def evaluate_outbound(result: PseudonymizationResult) -> CheckOutcome:
    """Compose le message une seule fois et le contrôle, segment par segment.

    Un texte périmé n'est pas contrôlé : il faut d'abord refaire la détection ou la revue.
    Valeur retournée : le contrôle, dont le statut n'est jamais un succès par défaut.
    """
    message = compose(result.text, st.session_state.get(KEY_INSTRUCTION) or "")
    stale = staleness()
    if stale is not None:
        return CheckOutcome(message, CheckStatus.NOT_RUN, (), stale, "", "")
    config = check_config()
    parameters = check_parameters(config)
    document_key = sha256_of(f"{parameters}\0{result.text}")
    instruction_key = sha256_of(f"{parameters}\0{result.text}\0{message.instruction}")
    source = st.session_state.get(KEY_SOURCE_TEXT) or None
    found = _segment(
        KEY_CHECK_DOCUMENT,
        document_key,
        config,
        lambda run: document_alerts(message, result, run, source, _rejected_spans()),
    )
    extra = _segment(
        KEY_CHECK_INSTRUCTION,
        instruction_key,
        config,
        lambda run: instruction_alerts(message, result, run),
    )
    scope = sha256_of(f"{document_key}\0{instruction_key}")
    if found is None or extra is None:
        return CheckOutcome(message, CheckStatus.UNAVAILABLE, (), None, "", scope)
    alerts = tuple(found + extra)
    kept = acknowledged(scope)
    fingerprint = send_fingerprint(message, parameters, kept)
    return CheckOutcome(message, check_status(alerts, kept), alerts, None, fingerprint, scope)


def _on_mask(value: str, kind: EntityType) -> None:
    """Rappel de "Mask everywhere" : ajoute la valeur partout, puis pseudonymise à nouveau."""
    added, _ = add_manual(st.session_state[KEY_SOURCE_TEXT], value, kind)
    st.session_state[KEY_SEND_AUTH] = None
    try:
        result = pseudonymize_session()
    except ValueError:
        st.session_state[KEY_CHECK_NOTICE] = ("", value, -1)
        return
    st.session_state[KEY_PSEUDO_RESULT] = result
    st.session_state[KEY_RESTORE_RESULT] = None
    # Le tableau de Review repart des nouvelles décisions, comme après un ajout manuel.
    st.session_state[KEY_TABLE_VERSION] = st.session_state.get(KEY_TABLE_VERSION, 0) + 1
    st.session_state[KEY_CHECK_NOTICE] = (sha256_of(result.text), value, added)


def _on_ack(scope: str, key: str, widget: str) -> None:
    """Rappel d'une décision explicite : garde ou retire la mention ; l'autorisation tombe."""
    keys = set(acknowledged(scope))
    if st.session_state.get(widget):
        keys.add(key)
    else:
        keys.discard(key)
    st.session_state[KEY_CHECK_ACKS] = (scope, frozenset(keys))
    st.session_state[KEY_SEND_AUTH] = None


def _copy_policy(key: str, widget: str) -> None:
    """Rappel d'un choix de politique : le garde en session ; l'autorisation tombe."""
    st.session_state[key] = bool(st.session_state[widget])
    st.session_state[KEY_SEND_AUTH] = None


def _retry() -> None:
    """Rappel du bouton de nouvel essai : oublie le résultat indisponible."""
    st.session_state[KEY_CHECK_DOCUMENT] = None
    st.session_state[KEY_CHECK_INSTRUCTION] = None


def _render_policy() -> None:
    """Choix visibles du contrôle : tous les types ou ceux de la barre latérale, exclusions."""
    summary = t(
        "check.policy.summary",
        types=t(
            "check.policy.types.all"
            if st.session_state[KEY_CHECK_ALL_TYPES]
            else "check.policy.types.sidebar"
        ),
        exclusions=t(
            "check.policy.exclusions.off"
            if st.session_state[KEY_CHECK_NO_EXCLUSIONS]
            else "check.policy.exclusions.on"
        ),
    )
    st.caption(summary)
    with st.expander(t("check.policy.heading"), icon=":material/tune:"):
        for key, widget, label in POLICY:
            st.checkbox(
                t(label),
                value=bool(st.session_state[key]),
                key=widget,
                help=t(f"{label}.help"),
                on_change=_copy_policy,
                args=(key, widget),
            )


def _render_notice(text: str) -> None:
    """Affiche le résultat du dernier masquage, s'il concerne le texte affiché."""
    notice = st.session_state.get(KEY_CHECK_NOTICE)
    if notice is None:
        return
    signature, value, added = notice
    if added < 0:
        st.error(t("check.mask.error"))
    elif signature == sha256_of(text):
        st.success(t("check.mask.done", value=literal_markdown(value), count=added))


def _render_alert(index: int, alert: Alert, outcome: CheckOutcome) -> None:
    """Une alerte : extrait surligné, origine, segment, masquage et décision explicite."""
    message = outcome.message
    text = message.document if alert.segment == DOCUMENT else message.instruction
    kind = alert.entity_type or EntityType.CUSTOM
    residual = Detection(alert.start, alert.end, kind, 1.0, Source.MANUAL, alert.text)
    piece, local = excerpt(text, residual)
    with st.container(key=f"hc-check-item-{index}", border=True):
        st.html(render_highlighted(piece, [local], {}))
        st.caption(f"{t(f'check.origin.{alert.origin}')} {t(f'check.segment.{alert.segment}')}")
        if alert.segment == DOCUMENT:
            st.button(
                t("check.mask"),
                key=f"check_mask_{index}",
                on_click=_on_mask,
                args=(alert.text, kind),
                icon=":material/visibility_off:",
            )
        else:
            st.caption(t("check.instruction.edit"))
        if alert.can_acknowledge:
            widget = f"check_ack_{outcome.scope[:12]}_{alert.key[:16]}"
            st.checkbox(
                t("check.ack"),
                value=alert.key in acknowledged(outcome.scope),
                key=widget,
                on_change=_on_ack,
                args=(outcome.scope, alert.key, widget),
            )


def _render_status(outcome: CheckOutcome) -> bool:
    """Affiche le statut ; renvoie vrai s'il reste des alertes à montrer."""
    if outcome.stale is not None:
        st.warning(t(f"check.stale.{outcome.stale}"), icon=":material/update:")
        target = STEP_IMPORT if outcome.stale == "detection" else STEP_REVIEW
        st.button(
            t(f"check.stale.{outcome.stale}.button"),
            key="check_stale_back",
            on_click=go_to,
            args=(target,),
        )
        return False
    if outcome.status is CheckStatus.UNAVAILABLE:
        st.error(t("check.error"))
        st.button(t("check.retry"), key="check_retry", on_click=_retry)
        return False
    if outcome.status is CheckStatus.CLEAR:
        st.success(t("check.clear"), icon=":material/task_alt:")
        st.caption(t("check.clear.note"))
        return False
    if outcome.status is CheckStatus.REVIEWED:
        st.info(t("check.reviewed", count=len(outcome.alerts)), icon=":material/fact_check:")
        st.caption(t("check.clear.note"))
    else:
        st.warning(t("check.found", count=len(outcome.alerts)), icon=":material/report:")
    return True


def render_final_check(outcome: CheckOutcome) -> None:
    """Carte du contrôle final : statut, politique, alertes à traiter, sans promettre l'anonymat."""
    with st.container(key="hc-card-check"):
        st.subheader(t("check.heading"), anchor=False)
        st.caption(t("check.intro"))
        _render_policy()
        _render_notice(outcome.message.document)
        if _render_status(outcome):
            for index, alert in enumerate(outcome.alerts):
                _render_alert(index, alert, outcome)
