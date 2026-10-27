"""Tests du regroupement des mentions (pseudonymize.grouping), sur des données fictives."""

import pytest

from huisclos.models import Detection, EntityType, Source
from huisclos.pseudonymize.grouping import group_mentions, normalized_key, person_words

P = EntityType.PERSON
ORG = EntityType.ORGANIZATION


def mentions(text: str, *items: tuple[str, EntityType]) -> list[Detection]:
    """Construit une détection par fragment, cherché à la suite du précédent."""
    detections, cursor = [], 0
    for fragment, entity_type in items:
        start = text.index(fragment, cursor)
        cursor = start + len(fragment)
        detections.append(Detection(start, cursor, entity_type, 1.0, Source.MANUAL, fragment))
    return detections


def test_all_dupont_forms_form_one_group() -> None:
    text = (
        "Jean DUPONT a signé. M. Dupont confirme. DUPONT refuse. Dupont accepte. "
        "DUPONT Jean conteste. J. Dupont paie."
    )
    forms = ["Jean DUPONT", "M. Dupont", "DUPONT", "Dupont", "DUPONT Jean", "J. Dupont"]
    groups = group_mentions(text, mentions(text, *((f, P) for f in forms)))
    assert len(groups) == 1
    group = groups[0]
    assert group.canonical == "Jean DUPONT"
    assert group.variants == tuple(sorted(set(forms)))
    assert len(group.mention_spans) == 6
    assert group.ambiguous_with == ()
    assert group.token == ""


def test_two_people_with_same_surname_and_ambiguous_surname() -> None:
    text = "Jean DUPONT et Marie DUPONT. Dupont a payé."
    groups = group_mentions(
        text, mentions(text, ("Jean DUPONT", P), ("Marie DUPONT", P), ("Dupont", P))
    )
    assert [g.canonical for g in groups] == ["Jean DUPONT", "Marie DUPONT", "Dupont"]
    assert [g.group_id for g in groups] == [1, 2, 3]
    assert groups[2].ambiguous_with == (1, 2)
    assert groups[0].ambiguous_with == ()


def test_initial_is_ambiguous_between_two_first_names() -> None:
    text = "Jean DUPONT, Jacques DUPONT et J. Dupont."
    groups = group_mentions(
        text, mentions(text, ("Jean DUPONT", P), ("Jacques DUPONT", P), ("J. Dupont", P))
    )
    assert len(groups) == 3
    assert groups[2].ambiguous_with == (1, 2)


def test_initial_matches_compound_first_name() -> None:
    text = "Jean-Pierre DUPONT puis J. Dupont."
    groups = group_mentions(text, mentions(text, ("Jean-Pierre DUPONT", P), ("J. Dupont", P)))
    assert len(groups) == 1


def test_first_name_alone_attached_to_single_candidate() -> None:
    text = "Claire FONTAINE est arrivée. Claire a signé."
    groups = group_mentions(text, mentions(text, ("Claire FONTAINE", P), ("Claire", P)))
    assert len(groups) == 1
    assert groups[0].canonical == "Claire FONTAINE"


def test_first_name_that_is_someone_else_surname_stays_apart() -> None:
    text = "Martin DURAND et P. Martin. Martin a menti."
    groups = group_mentions(
        text, mentions(text, ("Martin DURAND", P), ("P. Martin", P), ("Martin", P))
    )
    assert len(groups) == 3
    assert groups[2].canonical == "Martin"
    assert groups[2].ambiguous_with == (1,)


def test_lone_surname_without_full_name_is_its_own_group() -> None:
    text = "Lefort et Jean DUPONT."
    groups = group_mentions(text, mentions(text, ("Lefort", P), ("Jean DUPONT", P)))
    assert len(groups) == 2
    assert all(g.ambiguous_with == () for g in groups)


def test_longer_name_is_not_merged_with_shorter_full_name() -> None:
    text = "Jean Paul DUPONT et Jean DUPONT."
    groups = group_mentions(text, mentions(text, ("Jean Paul DUPONT", P), ("Jean DUPONT", P)))
    assert len(groups) == 2


def test_company_forms_form_one_group() -> None:
    text = "Atelier Verlaine SAS contre la société Atelier Verlaine, dite ATELIER VERLAINE."
    groups = group_mentions(
        text,
        mentions(
            text,
            ("Atelier Verlaine SAS", ORG),
            ("la société Atelier Verlaine", ORG),
            ("ATELIER VERLAINE", ORG),
        ),
    )
    assert len(groups) == 1
    assert groups[0].canonical == "Atelier Verlaine SAS"


def test_same_text_with_different_types_stays_apart() -> None:
    text = "Valmont a écrit à Valmont."
    groups = group_mentions(text, mentions(text, ("Valmont", P), ("Valmont", ORG)))
    assert [g.entity_type for g in groups] == [P, ORG]


def test_phone_and_date_variants_merge() -> None:
    text = "01 23 45 67 89, 01.23.45.67.89, +33 1 23 45 67 89 ; né le 12/03/1985 ou 12 mars 1985."
    phone, date = EntityType.PHONE, EntityType.BIRTH_DATE
    groups = group_mentions(
        text,
        mentions(
            text,
            ("01 23 45 67 89", phone),
            ("01.23.45.67.89", phone),
            ("+33 1 23 45 67 89", phone),
            ("12/03/1985", date),
            ("12 mars 1985", date),
        ),
    )
    assert [g.entity_type for g in groups] == [phone, date]
    assert [len(g.mention_spans) for g in groups] == [3, 2]


@pytest.mark.parametrize(
    ("entity_type", "first", "second"),
    [
        (EntityType.PHONE, "0033 1 23 45 67 89", "01 23 45 67 89"),
        (EntityType.PHONE, "+33 (0)1 23 45 67 89", "0123456789"),
        (EntityType.EMAIL, "Jean.Dupont@Example.com", "jean.dupont@example.com"),
        (EntityType.IBAN, "FR76 3000 6000 0112 3456 7890 189", "FR7630006000011234567890189"),
        (EntityType.SIRET, "123 456 789 00012", "12345678900012"),
        (EntityType.BIRTH_DATE, "1er mars 1985", "01/03/1985"),
        (EntityType.BIRTH_DATE, "12 Février 1985", "1985-02-12"),
        (
            EntityType.ADDRESS,
            "12 av. Victor Hugo, 75016 Paris",
            "12 avenue Victor Hugo 75016 Paris",
        ),
        (EntityType.ADDRESS, "3 bd Voltaire", "3 Boulevard Voltaire"),
        (EntityType.ORGANIZATION, "S.A.S. Atelier Verlaine", "Atelier Verlaine"),
        (EntityType.CUSTOM, "Projet  ÉTOILE", "projet etoile"),
    ],
)
def test_equivalent_forms_share_a_key(entity_type: EntityType, first: str, second: str) -> None:
    assert normalized_key(entity_type, first) == normalized_key(entity_type, second)


@pytest.mark.parametrize(
    ("entity_type", "first", "second"),
    [
        (EntityType.PHONE, "01 23 45 67 89", "01 23 45 67 88"),
        (EntityType.BIRTH_DATE, "12/03/1985", "03/12/1985"),
        (EntityType.ORGANIZATION, "Atelier Verlaine", "Atelier Rimbaud"),
        (EntityType.ADDRESS, "12 rue Voltaire", "14 rue Voltaire"),
    ],
)
def test_different_values_keep_different_keys(
    entity_type: EntityType, first: str, second: str
) -> None:
    assert normalized_key(entity_type, first) != normalized_key(entity_type, second)


def test_invalid_date_falls_back_to_folded_text() -> None:
    assert normalized_key(EntityType.BIRTH_DATE, "31/02/1985") == "31/02/1985"


def test_key_never_empty() -> None:
    assert normalized_key(ORG, "SAS") == "sas"


def test_person_words_drops_leading_civilities_only() -> None:
    assert person_words("Maître Hélène DE LA TOUR") == ("helene", "de", "la", "tour")
    assert person_words("M.") == ("m",)


def test_inconsistent_detection_is_refused() -> None:
    detection = Detection(0, 4, P, 1.0, Source.MANUAL, "Jean")
    with pytest.raises(ValueError, match="incohérente"):
        group_mentions("Paul DUPONT", [detection])
