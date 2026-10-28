"""Teste les identifiants libellés avec des valeurs indépendantes du corpus.

Entrées : libellés administratifs, codes fictifs et pièges sans contexte.
Sorties : assertions de bornes, type, score et absence de détection injustifiée.
Ces tests couvrent les motifs CUSTOM puis leur priorité dans la fusion.
"""

import random
from collections.abc import Callable

import pytest

from huisclos.config import DetectionConfig
from huisclos.detection.labeled_identifiers import LabeledIdentifierRecognizer
from huisclos.detection.merge import merge
from huisclos.detection.pipeline import detect
from huisclos.evaluation.synthetic_ids import make_siren, make_siret
from huisclos.models import Detection, EntityType, Source


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("matricule n° ", "RH-837-Z"),
        ("Numéro de salarié : ", "72948"),
        ("numéro de contrat ", "LX/2845"),
        ("police d'assurance n° ", "AS-38192"),
        ("numéro de police : ", "QP-29"),
        ("N° client : ", "CLT-879"),
        ("numéro d'adhérent ", "M-983"),
        ("Immatriculation du véhicule : ", "ZT-927-BK"),
        ("immatriculation ", "9273 LP 75"),
        ("numéro de passeport : ", "31EF92738"),
        ("carte d'identité n° ", "328719640582"),
        ("Numéro fiscal : ", "8724196305827"),
        ("numéro de client est ", "R-827-Q"),
        ("véhicule immatriculé ", "9273 LP 75"),
        ("identifiant de badge est ", "BX-729-T"),
        ("identifiant ", "PORT-837-Z"),
    ],
)
def test_labeled_custom_value(label: str, value: str) -> None:
    """Garde seulement la valeur avec la source pattern et le score justifié par le libellé."""
    text = label + value + ". Suite."
    recognizer = LabeledIdentifierRecognizer()
    results = recognizer.analyze(text, ["CUSTOM"])
    assert [(r.start, r.end, r.score) for r in results] == [(len(label), len(label + value), 0.9)]
    assert results[0].recognition_metadata["huisclos_source"] == "pattern"
    assert recognizer.analyze(value, ["CUSTOM"]) == []
    assert recognizer.analyze(text, ["PERSON"]) == []


@pytest.mark.parametrize(
    "text",
    [
        "numéro de facture 872419638",
        "numéro de commande 872419638",
        "montant 872419638 euros",
        "article 872419638",
        "contrat conclu le 28 octobre 2026",
        "client absent",
        "matricule : inconnu",
        "matricule :\n\n879321",
        "matricule : " + " " * 20 + "AB-937",
        "numéro de clientèle : 879321",
        "client837291",
        "matricule7291",
        "matricule AB-" + "9" * 45,
    ],
)
def test_unlabeled_or_incomplete_value_is_ignored(text: str) -> None:
    """Écarte les mots, libellés voisins, valeurs trop longues et contexte éloigné."""
    assert LabeledIdentifierRecognizer().analyze(text, ["CUSTOM"]) == []


def test_labeled_identifier_beats_ner_name_but_manual_edit_wins() -> None:
    """Un code explicitement libellé reste CUSTOM face au NER ; la revue humaine prime."""
    text = "matricule UT-948-K"
    start = text.index("UT")
    code = Detection(start, len(text), EntityType.CUSTOM, 0.9, Source.PATTERN, text[start:])
    name = Detection(
        start, len(text), EntityType.ORGANIZATION, 0.85, Source.NER_SPACY, text[start:]
    )
    assert merge(text, [name, code], DetectionConfig()) == [code]
    manual = Detection(start, len(text), EntityType.PERSON, 1.0, Source.MANUAL, text[start:])
    assert merge(text, [manual, code], DetectionConfig()) == [manual]


@pytest.mark.parametrize("generator", [make_siren, make_siret])
def test_employee_number_is_custom_even_if_a_checksum_coincides(
    generator: Callable[[random.Random], str], no_network: None
) -> None:
    """Une clé fortuite ne transforme pas le numéro de salarié libellé en numéro de société."""
    value = generator(random.Random(14837))
    results = detect("numéro de salarié : " + value)
    assert [(d.text, d.entity_type) for d in results] == [(value, EntityType.CUSTOM)]
