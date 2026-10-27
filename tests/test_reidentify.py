"""Tests de pseudonymize.reidentify : modes exact et tolérant, bornes, formes inconnues."""

from pathlib import Path

import pytest

from huisclos.config import PRESETS
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, Occurrence, Source, TokenStyle
from huisclos.pseudonymize.mapping import Mapping, MappingEntry, sha256_of
from huisclos.pseudonymize.reidentify import EXACT, TOLERANT, find_token_forms, restore
from huisclos.pseudonymize.tokens import make_token, pseudonymize

FIXTURES = Path(__file__).parent / "fixtures"
CREATED_AT = "2026-10-27T12:00:00+00:00"
PERSON = EntityType.PERSON
COMPANY = EntityType.ORGANIZATION


def build_mapping(*entries: tuple[EntityType, int, str]) -> Mapping:
    """Table fictive sans occurrences : (type, rang, forme canonique) par entité."""
    return Mapping(
        created_at=CREATED_AT,
        token_style=TokenStyle(),
        entities=tuple(
            MappingEntry(make_token(entity_type, rank), entity_type, canonical, (canonical,))
            for entity_type, rank, canonical in entries
        ),
        occurrences=(),
        pseudonymized_sha256=sha256_of(""),
    )


MAPPING = build_mapping(
    (PERSON, 1, "Jean DUPONT"),
    (PERSON, 2, "Marie MARTIN"),
    (COMPANY, 1, "Valmont SARL"),
    (EntityType.BIRTH_DATE, 1, "3 mai 1980"),
)


@pytest.mark.parametrize(
    "form",
    [
        "[PERSONNE_1]",
        "personne_1",
        "PERSONNE 1",
        "PERSONNE-1",
        "( PERSONNE_1 )",
        "\\(PERSONNE_1\\)",
        "{PERSONNE_1}",
        "<personne 1>",
        "\u00ab\u00a0PERSONNE_1\u00a0\u00bb",
        "PERSONNE\\_1",
        "[PERSON_1]",
        "[Personne 1]",
    ],
)
def test_altered_person_forms_are_restored(form: str) -> None:
    result = restore(f"Vu {form}.", MAPPING)
    assert result.mode == TOLERANT
    assert result.text == "Vu Jean DUPONT."
    assert result.replaced == {"[PERSONNE_1]": 1}
    assert result.unknown == []


@pytest.mark.parametrize(
    "form",
    [
        "\\[SOCIETE\\_A\\]",
        "Societe_A",
        "societe_a",
        "[SOCIÉTÉ_A]",
        "SOCIÉTÉ A",
        "[société a]",
        "[COMPANY_A]",
    ],
)
def test_altered_company_forms_are_restored(form: str) -> None:
    assert restore(f"La {form} paie.", MAPPING).text == "La Valmont SARL paie."


@pytest.mark.parametrize(
    "form", ["[DATE_NAISSANCE_1]", "DATE NAISSANCE 1", "[date naissance_1]", "BIRTH_DATE_1"]
)
def test_multiword_labels_accept_every_separator(form: str) -> None:
    assert restore(f"Née le {form}.", MAPPING).text == "Née le 3 mai 1980."


@pytest.mark.parametrize(
    "text",
    [
        "aucune personne 1 n'est concernée",
        "Personne 1 ne vient",
        "la personne-1 seule",
        "SIRET 732 829 320 00074",
        "DOSSIER 2024/15",
        "LA SOCIETE ANONYME",
        "XPERSONNE_1",
        "PERSONNE_1er",
        "PERSONNE A",
        "SOCIETE_1",
    ],
)
def test_ordinary_text_is_left_intact(text: str) -> None:
    result = restore(text, MAPPING)
    assert result.text == text
    assert result.unknown == []


def test_fixture_response_is_restored() -> None:
    raw = (FIXTURES / "llm_response_altered.txt").read_text(encoding="utf-8")
    result = restore(raw, MAPPING)
    assert result.mode == TOLERANT
    assert result.replaced == {
        "[PERSONNE_1]": 4,
        "[PERSONNE_2]": 1,
        "[SOCIETE_A]": 2,
        "[DATE_NAISSANCE_1]": 1,
    }
    assert ("personne_1", "[PERSONNE_1]") in result.altered
    assert ("PERSONNE 1", "[PERSONNE_1]") in result.altered
    assert ("( PERSONNE_1 )", "[PERSONNE_1]") in result.altered
    assert ("\\[SOCIETE\\_A\\]", "[SOCIETE_A]") in result.altered
    assert ("Societe_A", "[SOCIETE_A]") in result.altered
    assert ("[PERSONNE_1]", "[PERSONNE_1]") not in result.altered
    assert result.unknown == [("[PERSONNE_9]", raw.index("[PERSONNE_9]"))]
    assert "[PERSONNE_9]" in result.text
    assert "aucune personne 1 n'est concernée" in result.text
    assert "avec Valmont SARL le 3 mars" in result.text
    assert "Le temoin Jean DUPONT confirme" in result.text
    assert result.missing == []


def test_bounds_keep_longer_indexes_apart() -> None:
    mapping = build_mapping(
        (PERSON, 1, "Jean DUPONT"),
        (PERSON, 12, "Luc BERNARD"),
        (COMPANY, 1, "Valmont SARL"),
        (COMPANY, 28, "Orsay SAS"),
    )
    text = "[PERSONNE_12], PERSONNE_1, [SOCIETE_AB] et SOCIETE_A ; personne_12 et societe_ab."
    assert restore(text, mapping).text == (
        "Luc BERNARD, Jean DUPONT, Orsay SAS et Valmont SARL ; Luc BERNARD et Orsay SAS."
    )


def test_longer_index_absent_from_table_is_unknown() -> None:
    result = restore("Vu [PERSONNE_12] et SOCIETE_AB.", MAPPING)
    assert result.text == "Vu [PERSONNE_12] et SOCIETE_AB."
    assert result.unknown == [("[PERSONNE_12]", 3), ("SOCIETE_AB", 20)]


@pytest.mark.parametrize("form", ["[PERSONNE_9]", "[IBAN_1]", "[SOCIETE_1]", "[PERSONNE_A]"])
def test_unknown_index_or_type_is_left_as_is(form: str) -> None:
    result = restore(f"Voir {form}.", MAPPING)
    assert result.text == f"Voir {form}."
    assert result.unknown == [(form, 5)]
    assert result.replaced == {}


def test_unpaired_brackets_stay_in_the_text() -> None:
    result = restore("(PERSONNE_1, PERSONNE_2) et [PERSONNE_1)", MAPPING)
    assert result.text == "(Jean DUPONT, Marie MARTIN) et [Jean DUPONT)"


def test_missing_lists_tokens_never_seen() -> None:
    result = restore("Seule [PERSONNE_2] signe.", MAPPING)
    assert result.missing == ["[PERSONNE_1]", "[SOCIETE_A]", "[DATE_NAISSANCE_1]"]


def test_find_token_forms_reports_positions() -> None:
    forms = find_token_forms("vu ( personne_1 ) et [SOCIETE_AB]")
    assert [(f.text, f.start, f.entity_type, f.index) for f in forms] == [
        ("( personne_1 )", 3, PERSON, "1"),
        ("[SOCIETE_AB]", 21, COMPANY, "AB"),
    ]


def manual(text: str, value: str, entity_type: EntityType = PERSON, nth: int = 0) -> Detection:
    """Détection manuelle de la nième apparition de value dans text."""
    start = -1
    for _ in range(nth + 1):
        start = text.index(value, start + 1)
    return Detection(start, start + len(value), entity_type, 1.0, Source.MANUAL, value)


def test_exact_mode_keeps_each_written_variant() -> None:
    text = "Jean DUPONT écrit ; M. Dupont signe ; DUPONT paie."
    detections = [
        manual(text, "Jean DUPONT"),
        manual(text, "Dupont"),
        manual(text, "DUPONT", nth=1),
    ]
    result = pseudonymize(text, detections, created_at=CREATED_AT)
    for occurrences in (result.occurrences, None):
        restored = restore(result.text, result.mapping, occurrences)
        assert restored.mode == EXACT
        assert restored.text == text
        assert restored.altered == [] and restored.unknown == []


def test_literal_token_in_source_needs_positions() -> None:
    text = "Le modèle [PERSONNE_1] vise Jean DUPONT."
    result = pseudonymize(text, [manual(text, "Jean DUPONT")], created_at=CREATED_AT)
    assert restore(result.text, result.mapping, result.occurrences).text == text
    without_positions = restore(result.text, result.mapping)
    assert without_positions.mode == TOLERANT


def test_inconsistent_occurrences_fall_back_to_tolerant() -> None:
    text = "Jean DUPONT écrit."
    result = pseudonymize(text, [manual(text, "Jean DUPONT")], created_at=CREATED_AT)
    shifted = (Occurrence("[PERSONNE_1]", "Jean DUPONT", 1, 13),)
    restored = restore(result.text, result.mapping, shifted)
    assert restored.mode == TOLERANT
    assert restored.text == text


def test_modified_text_uses_tolerant_mode() -> None:
    text = "Jean DUPONT écrit."
    result = pseudonymize(text, [manual(text, "Jean DUPONT")], created_at=CREATED_AT)
    restored = restore(result.text + " Fin.", result.mapping, result.occurrences)
    assert restored.mode == TOLERANT
    assert restored.text == "Jean DUPONT écrit. Fin."


HANDMADE_TEXTS = [
    "Jean DUPONT, salarié de la société Valmont SARL, conteste son licenciement.",
    "Madame Claire LEROUX demeure 12 rue des Lilas, 69003 Lyon.",
    "Contact : claire.leroux@exemple.fr ou 06 12 34 56 78.",
    "M. Paul MARCHAND et Mme Sophie MARCHAND sont mariés depuis 2004.",
    "Le dossier RG n\u00b0 24/01234 est renvoyé au 5 novembre.",
    "Pierre GAUTIER a écrit à Pierre GAUTIER, puis M. Gautier a signé.",
    "Aucune donnée personnelle dans cette phrase.",
    "",
    "L\u2019employeur, la société Orsay Conseil SAS, a notifié la rupture.",
    "Me Hélène FAURE représente M.\u00a0Karim BENALI devant le conseil.",
    "Né le 14 février 1979 à Rennes, Louis PERRIN est cadre.",
    "SIREN 732 829 320 ; SIRET 732 829 320 00074.",
    "Aucune personne 1 n'est concernée par [PERSONNE_1] ni par SOCIETE_A.",
    "Première ligne : Anne ROUSSEL.\nDeuxième ligne : Marc ROUSSEL.\n",
    "Le gérant de Bastide Immobilier SARL, Thomas LEFEBVRE, réside à Bordeaux.",
    "Joindre Julie MOREAU au 01 23 45 67 89 ou julie.moreau@cabinet-exemple.fr.",
    "Mme Isabelle CHEVALIER (née FONTAINE) a saisi le juge le 3 juin 2025.",
    "IBAN FR76 3000 6000 0112 3456 7890 189 au nom de Nicolas GIRARD.",
    "Antoine MERCIER, Antoine MERCIER et encore A. MERCIER.",
    "\u00ab\u00a0Je confirme\u00a0\u00bb, déclare Lucie BLANCHARD, gérante.",
]


@pytest.mark.parametrize("text", HANDMADE_TEXTS)
def test_exact_roundtrip_on_handmade_texts(text: str) -> None:
    result = pseudonymize(text, detect(text, PRESETS["hybrid"]), created_at=CREATED_AT)
    restored = restore(result.text, result.mapping, result.occurrences)
    assert restored.mode == EXACT
    assert restored.text == text
