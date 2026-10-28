"""Vérifie les alias explicites et les noms de fichiers : liens certains, doutes séparés.

Entrées : définitions fictives ("ci-après", "dit", "hereinafter"), rôles génériques, sigles
ambigus et pièces jointes. Sorties : assertions sur les liens, la propagation et les jetons.
Aucun dictionnaire de surnoms : seul un lien écrit dans le texte relie deux formes.
"""

import pytest

from huisclos.config import DetectionConfig
from huisclos.detection.aliases import filename_spans, find_aliases, in_filename, is_name_like
from huisclos.detection.pipeline import detect
from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.grouping import group_mentions
from huisclos.pseudonymize.tokens import pseudonymize

CONFIG = DetectionConfig(threshold=0.30)


def _org(text: str, value: str) -> Detection:
    """Société fictive repérée à la première occurrence de value."""
    start = text.index(value)
    return Detection(
        start, start + len(value), EntityType.ORGANIZATION, 0.85, Source.NER_SPACY, value
    )


@pytest.mark.parametrize(
    ("suffix", "alias"),
    [
        (" (ci-après \u00ab BLX \u00bb)", "BLX"),
        (" (ci-après dénommée \u00ab BLX \u00bb)", "BLX"),
        (" (\u00ab BLX \u00bb)", "BLX"),
        (' ("BLX")', "BLX"),
        (" (hereinafter \u201cBLX\u201d)", "BLX"),
        (', also known as "Brightmoor"', "Brightmoor"),
    ],
)
def test_explicit_definition_links_alias(suffix: str, alias: str) -> None:
    """Une définition accolée au nom relie l'alias à l'entité, sans ambiguïté."""
    text = f"Brightmoor Logistique SAS{suffix} a signé."
    links = find_aliases(text, [_org(text, "Brightmoor Logistique SAS")])
    assert [(link.alias, link.ambiguous) for link in links] == [(alias, False)]
    assert text[links[0].start : links[0].end] == alias


@pytest.mark.parametrize(
    "suffix",
    [
        ' (the "Company")',
        " (ci-après la \u00ab Société \u00bb)",
        " (ci-après \u00ab le client \u00bb)",
    ],
)
def test_generic_roles_are_not_aliases(suffix: str) -> None:
    """Un rôle contractuel n'est pas un nom propre : il n'est ni relié ni propagé."""
    text = f"Acme Holdings LLC{suffix} paie."
    assert find_aliases(text, [_org(text, "Acme Holdings LLC")]) == []
    assert not is_name_like("la Société")


def test_same_alias_for_two_entities_is_ambiguous() -> None:
    """Un sigle défini pour deux sociétés reste protégé, sans jeton commun imposé."""
    text = (
        "Les sociétés Blanchard Levasseur SAS (\u00ab BL \u00bb) et "
        "Bureau Lemercier SARL (\u00ab BL \u00bb) "
        "utilisent le même sigle ; BL a répondu."
    )
    origins = [_org(text, "Blanchard Levasseur SAS"), _org(text, "Bureau Lemercier SARL")]
    assert [link.ambiguous for link in find_aliases(text, origins)] == [True, True]
    found = detect(text, CONFIG)
    assert [d.text for d in found if d.text == "BL"] == ["BL", "BL", "BL"]
    groups = group_mentions(text, found)
    bl_groups = [g for g in groups if "BL" in g.variants]
    assert len(bl_groups) == 1 and bl_groups[0].variants == ("BL",)


def test_alias_occurrences_share_the_entity_token() -> None:
    """Toutes les occurrences d'un alias non ambigu prennent le jeton de la société."""
    text = (
        "La société Brightmoor Logistique SAS (ci-après \u00ab BLX \u00bb) a résilié le contrat. "
        "BLX a écrit le 3 mai. Plus tard, BLX a relancé."
    )
    found = detect(text, CONFIG)
    blx = [d for d in found if d.text == "BLX"]
    assert len(blx) == 3 and {d.entity_type for d in blx} == {EntityType.ORGANIZATION}
    result = pseudonymize(text, found)
    assert "[SOCIETE_A] (ci-après \u00ab [SOCIETE_A] \u00bb)" in result.text
    assert result.text.count("[SOCIETE_A]") == 4


def test_person_alias_after_dit() -> None:
    """ "dit \u00ab Théo Grandclément \u00bb" relie le surnom écrit à la personne."""
    text = (
        "Monsieur Théophane GRANDCLÉMENT, dit \u00ab Théo Grandclément \u00bb, gérant, a signé. "
        "Théo Grandclément a ensuite écrit."
    )
    found = detect(text, CONFIG)
    result = pseudonymize(text, found)
    assert "Grandclément" not in result.text and "GRANDCLÉMENT" not in result.text
    assert result.text.count("[PERSONNE_1]") == 3


def test_alias_retypes_a_person_reading() -> None:
    """Un alias défini pour une société garde le type société, même lu comme personne."""
    text = 'Northfield Partners LLP ("Northfield") invoices monthly. Northfield pays.'
    config = DetectionConfig(threshold=0.30, use_spacy=False)
    found = detect(text, config)
    assert [(d.entity_type, d.text) for d in found] == [
        (EntityType.ORGANIZATION, "Northfield Partners LLP"),
        (EntityType.ORGANIZATION, "Northfield"),
        (EntityType.ORGANIZATION, "Northfield"),
    ]


def test_file_names_are_found_and_kept_separate() -> None:
    """Un nom dans un nom de fichier est protégé, sous un jeton distinct de la personne."""
    text = (
        "Monsieur Théophane GRANDCLÉMENT a signé.\n"
        "Pièces : attestation_GRANDCLEMENT_Theophane_2026.pdf, DURANDEL_Agathe_releve.docx"
    )
    spans = filename_spans(text)
    assert [text[s:e] for s, e in spans] == [
        "attestation_GRANDCLEMENT_Theophane_2026.pdf",
        "DURANDEL_Agathe_releve.docx",
    ]
    found = detect(text, CONFIG)
    texts = [d.text for d in found if d.entity_type is EntityType.PERSON]
    assert texts == ["Théophane GRANDCLÉMENT", "GRANDCLEMENT_Theophane", "DURANDEL_Agathe"]
    assert in_filename(found[1], spans) and not in_filename(found[0], spans)
    result = pseudonymize(text, found)
    assert "attestation_[PERSONNE_2]_2026.pdf" in result.text
    assert "[PERSONNE_3]_releve.docx" in result.text


def test_validated_value_in_file_name_keeps_its_token() -> None:
    """Une valeur déjà validée (ajout manuel) dans un nom de fichier garde le lien."""
    text = "Jean DUPONT écrit.\nPièce : note_Jean_DUPONT.pdf"
    start = text.index("Jean_DUPONT")
    manual = Detection(start, start + 11, EntityType.PERSON, 1.0, Source.MANUAL, "Jean_DUPONT")
    first = Detection(0, 11, EntityType.PERSON, 0.85, Source.NER_SPACY, "Jean DUPONT")
    assert in_filename(manual, filename_spans(text))
    assert len(group_mentions(text, [first, manual])) == 1
    automatic = Detection(
        start, start + 11, EntityType.PERSON, 0.85, Source.PROPAGATION, "Jean_DUPONT"
    )
    assert len(group_mentions(text, [first, automatic])) == 2
