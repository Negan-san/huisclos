"""Tests du contenu sortant (pseudonymize.outbound_check) : composition et contrôle par segment.

Textes fictifs : identifiant présent seulement dans la consigne, jeton connu réutilisé,
jeton inconnu ou altéré, homonyme rejeté ailleurs, borne incomplète vue dans le contexte
d'origine, positions par segment et dans le contenu complet, statuts et autorisation.
"""

import re
from dataclasses import replace

import pytest

from huisclos.config import PRESETS
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.final_check import check_threshold, output_span
from huisclos.pseudonymize.outbound_check import (
    DOCUMENT,
    INSTRUCTION,
    SEPARATOR,
    CheckStatus,
    check_status,
    compose,
    context_residuals,
    document_alerts,
    instruction_alerts,
    known_token_spans,
    may_send,
    send_fingerprint,
    token_like_spans,
)
from huisclos.pseudonymize.tokens import pseudonymize

P = EntityType.PERSON
TEXT = "M. Pierre VERNOLAC écrit à Mme Hélène QUISTRAL. Témoin : M. Petit, voisin."
LOWERED = replace(PRESETS["hybrid"], threshold=check_threshold(PRESETS["hybrid"].threshold))


def mention(text: str, fragment: str, kind: EntityType = P, start: int = 0) -> Detection:
    """Détection manuelle d'un fragment, cherché à partir de start."""
    begin = text.index(fragment, start)
    return Detection(begin, begin + len(fragment), kind, 1.0, Source.MANUAL, fragment)


def result_of(text: str = TEXT, *fragments: str):
    """Pseudonymise text en masquant les fragments donnés (les trois noms par défaut)."""
    chosen = fragments or ("Pierre VERNOLAC", "Hélène QUISTRAL", "Petit")
    return pseudonymize(text, [mention(text, fragment) for fragment in chosen])


def words(pattern: str):
    """Fausse détection : chaque mot qui correspond au motif devient une personne."""

    def run(text: str) -> list[Detection]:
        return [
            Detection(m.start(), m.end(), P, 0.5, Source.HEURISTIC, m.group())
            for m in re.finditer(pattern, text)
        ]

    return run


def real_detect(text: str) -> list[Detection]:
    """Détection réelle du contrôle : hybrid au seuil abaissé."""
    return detect(text, LOWERED)


def test_compose_builds_the_exact_content_once() -> None:
    message = compose("[PERSONNE_1] écrit.", "Résume ce texte.")
    assert message.content == "[PERSONNE_1] écrit." + SEPARATOR + "Résume ce texte."
    assert message.content[message.offset(INSTRUCTION) :] == "Résume ce texte."
    assert message.offset(DOCUMENT) == 0
    empty = compose("[PERSONNE_1] écrit.", "  \n")
    assert empty.content == "[PERSONNE_1] écrit."
    assert empty.instruction_start is None
    with pytest.raises(ValueError):
        empty.offset(INSTRUCTION)


def test_identifier_only_in_the_instruction_is_reported_at_both_offsets() -> None:
    result = result_of()
    message = compose(result.text, "Écris à alice.fictivel@example.com pour [PERSONNE_1].")
    assert document_alerts(message, result, real_detect, TEXT) == []
    alerts = instruction_alerts(message, result, real_detect)
    assert [(a.segment, a.text, a.entity_type) for a in alerts] == [
        (INSTRUCTION, "alice.fictivel@example.com", EntityType.EMAIL)
    ]
    alert = alerts[0]
    assert message.instruction[alert.start : alert.end] == alert.text
    assert message.content[alert.content_start : alert.content_end] == alert.text
    assert alert.content_start == alert.start + len(result.text) + len(SEPARATOR)


def test_value_of_the_table_in_the_instruction_is_reported() -> None:
    result = result_of()
    message = compose(result.text, "Que pense Vernolac de la lettre ?")
    alerts = instruction_alerts(message, result, None)
    assert [(a.text, a.origin) for a in alerts] == [("Vernolac", "table")]


def test_known_token_reused_in_the_instruction_raises_no_alert() -> None:
    result = result_of()
    instruction = "Résume la position de [PERSONNE_1] envers [PERSONNE_2], en trois lignes."
    message = compose(result.text, instruction)
    # Une détection qui verrait les jetons comme des noms prouve qu'ils sont neutralisés.
    assert instruction_alerts(message, result, words(r"PERSONNE_\d")) == []
    assert instruction_alerts(message, result, real_detect) == []
    assert known_token_spans(instruction, {"[PERSONNE_1]", "[PERSONNE_2]"}) == [(22, 34), (42, 54)]


@pytest.mark.parametrize(
    "instruction, form",
    [
        ("Compare avec [PERSONNE_9].", "[PERSONNE_9]"),
        ("Compare avec PERSONNE_1 seul.", "PERSONNE_1"),
        ("Compare avec [Personne 1].", "[Personne 1]"),
        ("Compare avec [SOCIETE_B].", "[SOCIETE_B]"),
    ],
)
def test_unknown_or_altered_token_cannot_bypass_the_check(instruction: str, form: str) -> None:
    result = result_of()
    message = compose(result.text, instruction)
    alerts = instruction_alerts(message, result, None)
    assert [(a.text, a.origin) for a in alerts] == [(form, "unknown_token")]
    assert not alerts[0].can_acknowledge
    assert check_status(alerts, {alerts[0].key}) is CheckStatus.ALERTS


def test_ordinary_words_are_not_token_like() -> None:
    assert token_like_spans("In case 2, the other A party and place 3 apply.") == []


def test_rejected_homonym_elsewhere_stays_detectable() -> None:
    text = "Le petit dossier de M. Pierre VERNOLAC. Le témoin Petit habite rue Haute."
    result = result_of(text, "Pierre VERNOLAC")
    message = compose(result.text, "")
    detect_petit = words(r"(?i)\bpetit\b")
    first = text.index("petit")
    alerts = document_alerts(message, result, detect_petit, None, [(first, first + 5)])
    assert [a.text for a in alerts] == ["Petit"]
    assert result.text[alerts[0].start : alerts[0].end] == "Petit"
    both = [(first, first + 5), (text.index("Petit"), text.index("Petit") + 5)]
    assert document_alerts(message, result, detect_petit, None, both) == []


def test_incomplete_bound_is_found_in_the_source_context_and_projected() -> None:
    text = "Réf. Mme Hélène QUISTRAL. Puis Jean-Pierre DUPONT signe la lettre."
    result = result_of(text, "Hélène QUISTRAL", "DUPONT")
    whole = text.index("Jean-Pierre DUPONT")

    def source_detect(value: str) -> list[Detection]:
        if value != text:
            return []
        return [Detection(whole, whole + 18, P, 0.4, Source.NER_SPACY, value[whole : whole + 18])]

    found = context_residuals(result, text, source_detect)
    assert [d.text for d in found] == ["Jean-Pierre"]
    assert result.text[found[0].start : found[0].end] == "Jean-Pierre"
    message = compose(result.text, "")
    alerts = document_alerts(message, result, source_detect, text)
    assert [(a.text, a.origin) for a in alerts] == [("Jean-Pierre", "context")]
    with pytest.raises(ValueError):
        output_span(result, whole, whole + 18)


def test_a_failing_engine_never_returns_an_empty_check() -> None:
    result = result_of()

    def broken(_: str) -> list[Detection]:
        raise RuntimeError("moteur absent")

    with pytest.raises(RuntimeError):
        document_alerts(compose(result.text, ""), result, broken, TEXT)
    with pytest.raises(RuntimeError):
        instruction_alerts(compose(result.text, "Résume."), result, broken)


def test_message_must_carry_the_checked_text() -> None:
    result = result_of()
    with pytest.raises(ValueError):
        document_alerts(compose(result.text + " ajout", ""), result, None)


def test_status_authorization_and_fingerprint() -> None:
    result = result_of()
    message = compose(result.text, "Que pense Vernolac ?")
    alerts = instruction_alerts(message, result, None)
    assert check_status([], set()) is CheckStatus.CLEAR
    assert check_status(alerts, set()) is CheckStatus.ALERTS
    keys = {alert.key for alert in alerts}
    assert check_status(alerts, keys) is CheckStatus.REVIEWED
    current = send_fingerprint(message, "params", keys)
    assert may_send(current, current, CheckStatus.REVIEWED)
    assert not may_send(None, current, CheckStatus.CLEAR)
    assert not may_send(current, current, CheckStatus.ALERTS)
    assert not may_send(current, current, CheckStatus.UNAVAILABLE)
    assert not may_send(current, current, CheckStatus.RUNNING)
    assert not may_send(current, current, CheckStatus.NOT_RUN)
    other = compose(result.text, "Que pense Vernolac ? ")
    assert send_fingerprint(other, "params", keys) != current
    assert send_fingerprint(message, "params2", keys) != current
    assert send_fingerprint(message, "params", set()) != current


def test_same_value_in_another_context_has_another_key() -> None:
    text = "Le témoin Petit est venu. Plus loin, Petit SARL a payé M. Pierre VERNOLAC."
    result = result_of(text, "Pierre VERNOLAC")
    alerts = document_alerts(compose(result.text, ""), result, words(r"\bPetit\b"))
    assert len(alerts) == 2
    assert alerts[0].key != alerts[1].key
    assert check_status(alerts, {alerts[0].key}) is CheckStatus.ALERTS


def test_disabled_types_are_checked_only_when_asked() -> None:
    text = "Rendez-vous à Lyon avec M. Pierre VERNOLAC, puis M. Petit."
    result = result_of(text, "Pierre VERNOLAC", "Petit")
    message = compose(result.text, "")
    assert document_alerts(message, result, real_detect, text) == []
    every_type = replace(LOWERED, enabled_types=frozenset(EntityType))
    alerts = document_alerts(message, result, lambda value: detect(value, every_type), text)
    assert [(a.text, a.entity_type) for a in alerts] == [("Lyon", EntityType.LOCATION)]
    assert "Lyon" in result.text
