"""Tests de la mémoire de dossier (pseudonymize.case_memory) et des jetons stables entre documents.

Deux documents fictifs d'un même dossier : une personne commune garde son jeton, une
personne nouvelle prend le premier numéro libre, et la table fusionnée restaure une réponse
qui mêle les deux documents.
"""

import json
from dataclasses import replace

import pytest

from huisclos.config import PRESETS
from huisclos.detection.pipeline import add_known, detect
from huisclos.models import Detection, EntityType, PseudonymizationResult, Source, TokenStyle
from huisclos.pseudonymize.case_memory import (
    MAX_TABLE_BYTES,
    TableFileError,
    find_known,
    find_value,
    read_table_file,
    token_number,
)
from huisclos.pseudonymize.mapping import Mapping
from huisclos.pseudonymize.reidentify import EXACT, TOLERANT, restore
from huisclos.pseudonymize.tokens import pseudonymize

P = EntityType.PERSON
ORG = EntityType.ORGANIZATION
FIXED_TIME = "2026-10-28T09:00:00+00:00"
FRENCH = TokenStyle()

DOC1 = (
    "Note du 3 mars 2026. M. Pierre VERNOLAC, salarié de la société Atelier Brunel SARL, "
    "conteste son licenciement. Mme Élodie MÉRANSAC, sa collègue, témoigne pour M. Vernolac."
)
DOC2 = (
    "Courrier du 9 avril 2026. Après l'audience, elodie meransac a remis ses pièces. "
    "M. Pierre VERNOLAC répond. Mme Hélène QUISTRAL, nouvelle témoin, confirme."
)


def mentions(text: str, *items: tuple[str, EntityType]) -> list[Detection]:
    """Construit une détection par fragment, cherché à la suite du précédent."""
    detections, cursor = [], 0
    for fragment, entity_type in items:
        start = text.index(fragment, cursor)
        cursor = start + len(fragment)
        detections.append(Detection(start, cursor, entity_type, 0.9, Source.MANUAL, fragment))
    return detections


def first_document() -> Mapping:
    """Pseudonymise le premier document et renvoie sa table."""
    detections = mentions(
        DOC1,
        ("Pierre VERNOLAC", P),
        ("Atelier Brunel SARL", ORG),
        ("Élodie MÉRANSAC", P),
        ("Vernolac", P),
    )
    return pseudonymize(DOC1, detections, created_at=FIXED_TIME).mapping


def second_document(table: Mapping, style: TokenStyle = FRENCH) -> PseudonymizationResult:
    """Pseudonymise le second document avec la table du premier."""
    detections = mentions(
        DOC2,
        ("elodie meransac", P),
        ("Pierre VERNOLAC", P),
        ("Hélène QUISTRAL", P),
    )
    return pseudonymize(DOC2, detections, style, created_at=FIXED_TIME, known=table)


def token_for(mapping: Mapping, canonical: str) -> str:
    """Jeton de l'entité dont la forme canonique est donnée."""
    return next(e.token for e in mapping.entities if e.canonical == canonical)


def test_common_person_keeps_token_and_new_person_takes_next_free_number() -> None:
    table = first_document()
    assert token_for(table, "Pierre VERNOLAC") == "[PERSONNE_1]"
    assert token_for(table, "Élodie MÉRANSAC") == "[PERSONNE_2]"
    result = second_document(table)
    assert result.text == (
        "Courrier du 9 avril 2026. Après l'audience, [PERSONNE_2] a remis ses pièces. "
        "M. [PERSONNE_1] répond. Mme [PERSONNE_3], nouvelle témoin, confirme."
    )


def test_merged_table_keeps_known_entities_and_adds_new_ones() -> None:
    table = first_document()
    merged = second_document(table).mapping
    assert [e.token for e in merged.entities] == [
        "[PERSONNE_1]",
        "[SOCIETE_A]",
        "[PERSONNE_2]",
        "[PERSONNE_3]",
    ]
    meransac = next(e for e in merged.entities if e.token == "[PERSONNE_2]")
    assert meransac.canonical == "Élodie MÉRANSAC"
    assert "elodie meransac" in meransac.variants
    assert Mapping.from_json(merged.to_json()) == merged


def test_answer_mixing_both_documents_is_restored_with_merged_table() -> None:
    merged = second_document(first_document()).mapping
    answer = "[PERSONNE_1] travaille chez [SOCIETE_A] ; [PERSONNE_2] et [PERSONNE_3] témoignent."
    restored = restore(answer, merged)
    assert restored.mode == TOLERANT
    assert restored.text == (
        "Pierre VERNOLAC travaille chez Atelier Brunel SARL ; Élodie MÉRANSAC et "
        "Hélène QUISTRAL témoignent."
    )
    assert not restored.unknown


def test_second_document_text_still_restores_exactly() -> None:
    result = second_document(first_document())
    restored = restore(result.text, result.mapping)
    assert restored.mode == EXACT
    assert restored.text == DOC2


def test_known_table_style_wins_over_requested_style() -> None:
    detections = mentions(DOC1, ("Pierre VERNOLAC", P))
    english = pseudonymize(DOC1, detections, TokenStyle(language="en")).mapping
    result = second_document(english, TokenStyle(language="fr"))
    assert "[PERSON_1]" in result.text
    assert "[PERSON_2]" in result.text
    assert "PERSONNE" not in result.text
    assert result.mapping.token_style.language == "en"


def test_surname_alone_is_attached_to_the_known_full_name() -> None:
    table = pseudonymize(DOC1, mentions(DOC1, ("Pierre VERNOLAC", P))).mapping
    text = "Le conseil de M. VERNOLAC a écrit."
    result = pseudonymize(text, mentions(text, ("VERNOLAC", P)), known=table)
    assert result.text == "Le conseil de M. [PERSONNE_1] a écrit."


def test_surname_shared_by_two_known_persons_gets_a_new_token() -> None:
    first = "Jean DUPONT et Marie DUPONT signent."
    table = pseudonymize(first, mentions(first, ("Jean DUPONT", P), ("Marie DUPONT", P))).mapping
    text = "M. Dupont a signé."
    result = pseudonymize(text, mentions(text, ("Dupont", P)), known=table)
    assert result.text == "M. [PERSONNE_3] a signé."


def test_two_groups_of_the_same_known_entity_share_one_token() -> None:
    # Sans nom complet dans le texte, le regroupement garde "VERNOLAC" et "P. VERNOLAC"
    # séparés ; la table les rattache tous deux à Pierre VERNOLAC.
    table = first_document()
    text = "M. VERNOLAC a écrit, signé P. VERNOLAC."
    detections = mentions(text, ("VERNOLAC", P), ("P. VERNOLAC", P))
    result = pseudonymize(text, detections, known=table)
    assert result.text == "M. [PERSONNE_1] a écrit, signé [PERSONNE_1]."
    assert len(result.groups) == 1
    assert result.groups[0].mention_spans == ((3, 11), (27, 38))


def test_name_also_in_a_file_name_loses_token_continuity_when_the_surname_returns() -> None:
    # D-FIX3-2 : le nom de fichier garde son jeton (D-AF-A2-7), donc la table porte deux
    # entrées pour "FALVERAC". Le nom seul a alors deux candidats et reçoit un jeton neuf :
    # continuité perdue, mais ni fuite ni confusion entre deux personnes.
    first = "M. Lucien FALVERAC conteste. M. FALVERAC signe. Pièce : conclusions_FALVERAC.pdf."
    detections = mentions(first, ("Lucien FALVERAC", P), ("FALVERAC", P), ("FALVERAC", P))
    detections[2] = replace(detections[2], source=Source.PROPAGATION)
    table = pseudonymize(first, detections, created_at=FIXED_TIME).mapping
    assert [(e.token, e.canonical) for e in table.entities] == [
        ("[PERSONNE_1]", "Lucien FALVERAC"),
        ("[PERSONNE_2]", "FALVERAC"),
    ]
    full = "Lucien FALVERAC signe."
    alone = pseudonymize(full, mentions(full, ("Lucien FALVERAC", P)), known=table)
    assert alone.text == "[PERSONNE_1] signe."
    both = "M. FALVERAC répond. Lucien FALVERAC signe."
    result = pseudonymize(
        both, mentions(both, ("FALVERAC", P), ("Lucien FALVERAC", P)), known=table
    )
    assert result.text == "M. [PERSONNE_3] répond. [PERSONNE_3] signe."
    assert "FALVERAC" not in result.text
    assert restore(result.text, result.mapping).text == both


def test_new_organization_takes_next_free_letter() -> None:
    table = first_document()
    text = "La société Garnier Logistique SAS et Atelier Brunel SARL."
    detections = mentions(text, ("Garnier Logistique SAS", ORG), ("Atelier Brunel SARL", ORG))
    result = pseudonymize(text, detections, known=table)
    assert result.text == "La société [SOCIETE_B] et [SOCIETE_A]."


def test_find_value_tolerates_case_accents_and_blanks_with_word_bounds() -> None:
    text = "Vu elodie\nmeransac, puis MÉRANSACS et Méransac."
    assert find_value(text, "Élodie MÉRANSAC") == [(3, 18)]
    assert find_value(text, "Méransac") == [(10, 18), (38, 46)]
    assert find_value(text, "   ") == []


def test_known_value_found_in_lower_case_without_accents() -> None:
    known = find_known(DOC2, first_document())
    found = {(d.text, d.entity_type, d.source, d.score) for d in known}
    assert ("elodie meransac", P, Source.CASE_TABLE, 1.0) in found
    assert ("Pierre VERNOLAC", P, Source.CASE_TABLE, 1.0) in found
    assert all(DOC2[d.start : d.end] == d.text for d in known)


def test_find_known_prefers_the_longest_form() -> None:
    text = "M. Pierre VERNOLAC, puis M. Vernolac."
    known = find_known(text, first_document())
    assert [d.text for d in known] == ["Pierre VERNOLAC", "Vernolac"]


def test_detection_proposes_a_value_no_recognizer_sees() -> None:
    text = "Le dossier de elodie meransac est transmis au service."
    table = first_document()
    assert not any(d.text == "elodie meransac" for d in detect(text, PRESETS["hybrid"]))
    result = detect(text, PRESETS["hybrid"], known=find_known(text, table))
    assert any(d.text == "elodie meransac" and d.entity_type is P for d in result)


def test_add_known_skips_covered_values_and_extends_partial_overlaps() -> None:
    text = "M. Pierre VERNOLAC Jr signe."
    existing = mentions(text, ("Pierre VERNOLAC", P))
    covered = [Detection(10, 18, P, 1.0, Source.CASE_TABLE, "VERNOLAC")]
    assert add_known(text, existing, covered) == existing
    crossing = [Detection(10, 21, P, 1.0, Source.CASE_TABLE, "VERNOLAC Jr")]
    merged = add_known(text, existing, crossing)
    assert [(d.text, d.source) for d in merged] == [("Pierre VERNOLAC Jr", Source.CASE_TABLE)]


@pytest.mark.parametrize(
    ("token", "kind", "style", "expected"),
    [
        ("[PERSONNE_3]", P, TokenStyle(), 3),
        ("[SOCIETE_AB]", ORG, TokenStyle(), 28),
        ("[PERSON_2]", P, TokenStyle(language="en"), 2),
        ("[PERSON_2]", P, TokenStyle(), None),
        ("[PERSONNE_0]", P, TokenStyle(), None),
        ("[SOCIETE_1]", ORG, TokenStyle(), None),
        ("PERSONNE_1", P, TokenStyle(), None),
    ],
)
def test_token_number(
    token: str, kind: EntityType, style: TokenStyle, expected: int | None
) -> None:
    assert token_number(token, kind, style) == expected


def test_read_table_file_accepts_the_exported_format() -> None:
    table = first_document()
    assert read_table_file(table.to_json().encode("utf-8")) == table
    assert read_table_file(b"\xef\xbb\xbf" + table.to_json().encode("utf-8")) == table


def table_with(change: dict[str, object]) -> bytes:
    """Table exportée dont un champ de la première entité est modifié."""
    data = first_document().to_dict()
    data["entities"][0].update(change)
    return json.dumps(data).encode("utf-8")


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (b"x" * (MAX_TABLE_BYTES + 1), "too_large"),
        ("Élodie".encode("latin-1"), "encoding"),
        (b"not json", "invalid"),
        (b"[]", "invalid"),
        (b'{"schema": "other", "version": 1}', "invalid"),
        (b"[" * 100_000 + b"]" * 100_000, "invalid"),
        (table_with({"token": "[FOO_1]"}), "invalid"),
        (table_with({"type": "SECRET"}), "invalid"),
        (table_with({"canonical": "  "}), "invalid"),
        (table_with({"variants": [1, 2]}), "invalid"),
    ],
    ids=[
        "too_large",
        "latin1",
        "not_json",
        "list",
        "schema",
        "deep_nesting",
        "token",
        "type",
        "blank_canonical",
        "variants",
    ],
)
def test_invalid_table_is_refused_with_a_code(data: bytes, code: str) -> None:
    with pytest.raises(TableFileError) as caught:
        read_table_file(data)
    assert caught.value.code == code
