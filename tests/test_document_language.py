"""Vérifie la langue du document : configuration, moteurs séparés, refus clairs et dossier.

Entrées : configurations fr et en, faux modèle absent, table de dossier fictive.
Sorties : assertions sur les modèles choisis, les caches, les registres et les jetons.
La langue du document reste distincte de la langue de l'interface et du style des jetons.
"""

from dataclasses import replace

import pytest
import spacy.util

from huisclos.config import PRESETS, DetectionConfig
from huisclos.detection import ner
from huisclos.detection.exclusions import load_exclusions, load_exclusions_for
from huisclos.detection.languages import default_model_for, profile
from huisclos.detection.patterns import build_pattern_recognizers
from huisclos.detection.person_heuristics import CivilityPersonRecognizer
from huisclos.detection.pipeline import analyzer_for, build_analyzer, detect
from huisclos.models import EntityType, TokenStyle
from huisclos.pseudonymize.case_memory import find_known
from huisclos.pseudonymize.tokens import pseudonymize

HAS_ENGLISH_MODEL = spacy.util.is_package("en_core_web_sm")
needs_english = pytest.mark.skipif(not HAS_ENGLISH_MODEL, reason="en_core_web_sm absent")


def test_french_remains_the_default() -> None:
    """Sans réglage, le document est français et le modèle reste fr_core_news_md."""
    config = DetectionConfig(threshold=0.3)
    assert (config.document_language, config.spacy_model) == ("fr", "fr_core_news_md")
    assert all(preset.document_language == "fr" for preset in PRESETS.values())


def test_default_model_follows_the_language_both_ways() -> None:
    """replace() change le modèle par défaut avec la langue, dans les deux sens."""
    english = replace(PRESETS["hybrid"], document_language="en")
    assert english.spacy_model == "en_core_web_sm"
    assert replace(english, document_language="fr").spacy_model == "fr_core_news_md"
    assert default_model_for("en", "en_core_web_md") == "en_core_web_md"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"document_language": "de"}, "fr ou en"),
        ({"document_language": "en", "spacy_model": "fr_core_news_lg"}, "ne correspond pas"),
        ({"document_language": "fr", "spacy_model": "en_core_web_md"}, "ne correspond pas"),
    ],
)
def test_inconsistent_language_or_model_is_refused(changes: dict[str, str], message: str) -> None:
    """Une langue inconnue ou un modèle d'une autre langue lèvent une erreur claire."""
    with pytest.raises(ValueError, match=message):
        DetectionConfig(threshold=0.3, **changes)


def test_registries_are_built_for_the_document_language() -> None:
    """Chaque reconnaisseur déclare la langue du document ; l'anglais a ses motifs propres."""
    french = build_pattern_recognizers("fr")
    english = build_pattern_recognizers("en")
    assert {r.supported_language for r in french} == {"fr"}
    assert {r.supported_language for r in english} == {"en"}
    names = [r.name for r in english]
    assert "NirRecognizer" in names and "SiretRecognizer" in names
    assert {"EnglishBirthDateRecognizer", "EnglishCaseNumberRecognizer"} <= set(names)
    assert ner.build_ner_recognizers("en")[0].name == "EnglishSpacyRecognizer"


def test_exclusions_are_loaded_per_language() -> None:
    """Le français garde sa liste ; l'anglais ajoute la sienne aux juridictions françaises."""
    assert load_exclusions_for("fr") is load_exclusions()
    text = "Cour de cassation ; High Court ; Companies House"
    french = {text[s:e] for s, e in load_exclusions_for("fr").spans(text)}
    english = {text[s:e] for s, e in load_exclusions_for("en").spans(text)}
    assert french == {"Cour de cassation"}
    assert english == {"Cour de cassation", "High Court", "Companies House"}
    assert "LLP" in load_exclusions_for("en").acronyms


def test_english_civilities_and_pronoun_me() -> None:
    """En anglais, "Ms" et "Dr." annoncent un nom ; "Me" seul y reste un pronom."""
    recognizer = CivilityPersonRecognizer(language="en")
    text = "Dear Ms Jane CALLOWAY and Dr. Samuel K. Whitaker. Give Me Hope."
    spans = [text[r.start : r.end] for r in recognizer.analyze(text, ["PERSON"])]
    assert spans == ["Jane CALLOWAY", "Samuel K. Whitaker"]


def test_camembert_is_refused_for_english_documents() -> None:
    """CamemBERT, modèle français, n'est jamais appliqué à un document anglais."""
    with pytest.raises(ValueError, match="CamemBERT"):
        build_analyzer(True, True, False, True, "en_core_web_sm", "en")


def test_missing_english_model_fails_clearly(
    monkeypatch: pytest.MonkeyPatch, no_network: None
) -> None:
    """Un modèle absent donne une erreur explicite, jamais un téléchargement."""
    monkeypatch.setattr(spacy.util, "is_package", lambda name: False)
    with pytest.raises(RuntimeError, match="en_core_web_sm n'est pas installé"):
        ner.build_nlp_engine("en_core_web_sm", "en")


def test_language_profiles_map_types_conservatively() -> None:
    """DATE n'est pas une date de naissance ; GPE, LOC et FAC restent des lieux."""
    english = profile("en")
    assert "DATE" in english.labels_to_ignore
    assert {english.label_mapping[label] for label in ("GPE", "LOC", "FAC")} == {"LOCATION"}


def test_robustness_pilot_sets_the_language_field() -> None:
    """Le pilote B1 fixe document_language par replace() et le signale comme présent."""
    from scripts.evaluate_robustness import configured

    config, present = configured(PRESETS["hybrid"], 0.3, "en")
    assert present and config.document_language == "en"
    assert config.spacy_model == "en_core_web_sm"


@needs_english
def test_engines_and_caches_are_separated_by_language() -> None:
    """Un analyseur par langue, chacun avec son modèle et sa langue Presidio."""
    french = analyzer_for(PRESETS["hybrid"])
    english = analyzer_for(replace(PRESETS["hybrid"], document_language="en"))
    assert french is not english
    assert english.supported_languages == ["en"] and french.supported_languages == ["fr"]
    assert analyzer_for(replace(PRESETS["hybrid"], document_language="en")) is english


@needs_english
def test_case_table_keeps_tokens_from_french_to_english() -> None:
    """La table d'un document français garde le jeton d'une identité dans un document anglais."""
    french_text = "Madame Ysaline FERRAND, née le 3 mars 1981, réside à Valbrune."
    french = pseudonymize(french_text, detect(french_text, DetectionConfig(threshold=0.3)))
    english_text = (
        "Ms Ysaline FERRAND wrote again. Ms FERRAND confirmed the hearing on 12 June 2026."
    )
    config = DetectionConfig(threshold=0.3, document_language="en")
    known = find_known(english_text, french.mapping)
    english = pseudonymize(english_text, detect(english_text, config, known), known=french.mapping)
    token = next(o.token for o in french.occurrences if o.original == "Ysaline FERRAND")
    assert english.text.count(token) == 2
    assert english.mapping.token_style == TokenStyle()
    assert all(o.original != "12 June 2026" for o in english.occurrences)
    assert {g.entity_type for g in english.groups} == {EntityType.PERSON}
