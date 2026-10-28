"""Reconnaissance d'entités nommées avec spaCy, via Presidio, en français ou en anglais.

Entrées : le nom d'un modèle spaCy installé (fr_core_news_md ou en_core_web_sm), la langue
du document et un texte.
Sorties : un moteur NLP Presidio et un reconnaisseur de personnes, sociétés et lieux dont
chaque résultat porte la source "ner_spacy".
Place dans le pipeline : première source de détection statistique, avant les exclusions et la
fusion ; ses scores suivent le barème D-07 (voir D-S12-1).
"""

import spacy.util
from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngine, NlpEngineProvider
from presidio_analyzer.predefined_recognizers import SpacyRecognizer

from huisclos.detection.languages import profile
from huisclos.models import Source

DEFAULT_MODEL = "fr_core_news_md"
LANGUAGE = "fr"

# Score fixe que Presidio attribue à toute entité spaCy (NerModelConfiguration.default_score).
NER_SCORE = 0.85

# Étiquettes du modèle français vers les types Presidio. MISC (divers) est écarté : trop
# bruité pour être proposé à l'utilisateur.
LABEL_MAPPING = profile("fr").label_mapping
SUPPORTED_ENTITIES = ["PERSON", "ORGANIZATION", "LOCATION"]
# Nom du reconnaisseur par langue ; le nom français est vérifié par test_no_network.
RECOGNIZER_NAMES = {"fr": "FrenchSpacyRecognizer", "en": "EnglishSpacyRecognizer"}


class FrenchSpacyRecognizer(SpacyRecognizer):
    """Reconnaisseur NER spaCy qui marque ses résultats avec la source ner_spacy.

    Le nom historique est conservé ; la langue servie est celle passée au constructeur.
    """

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None = None,
    ) -> list[RecognizerResult]:
        """Délègue à Presidio puis ajoute la source huisclos_source à chaque résultat."""
        results = super().analyze(text, entities, nlp_artifacts)
        for result in results:
            result.recognition_metadata["huisclos_source"] = Source.NER_SPACY.value
        return results


def build_nlp_engine(model_name: str = DEFAULT_MODEL, language: str = LANGUAGE) -> NlpEngine:
    """Construit le moteur spaCy de Presidio pour la langue du document.

    Paramètres : model_name, le modèle spaCy déjà installé ; language, fr ou en.
    Valeur retournée : le moteur NLP chargé, étiquettes converties selon le profil de langue
    (PER, ORG et LOC en français ; PERSON, ORG, GPE, LOC et FAC en anglais), autres ignorées.
    Lève RuntimeError si le modèle manque : Presidio le téléchargerait, ce qui romprait le
    principe d'absence d'appel réseau à l'exécution.
    """
    settings = profile(language)
    if not spacy.util.is_package(model_name):
        raise RuntimeError(
            f"Le modèle spaCy {model_name} n'est pas installé ; "
            "installez-le localement (aucun téléchargement automatique)."
        )
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": settings.code, "model_name": model_name}],
        "ner_model_configuration": {
            "model_to_presidio_entity_mapping": dict(settings.label_mapping),
            "labels_to_ignore": list(settings.labels_to_ignore),
            "default_score": NER_SCORE,
        },
    }
    return NlpEngineProvider(nlp_configuration=configuration).create_engine()


def build_ner_recognizers(language: str = LANGUAGE) -> list[SpacyRecognizer]:
    """Renvoie les reconnaisseurs NER de la seule langue du document.

    Aucun reconnaisseur d'une autre langue n'est créé : le registre Presidio par défaut en
    ajoute, ce qui produirait des détections hors sujet.
    """
    return [
        FrenchSpacyRecognizer(
            supported_language=profile(language).code,
            supported_entities=list(SUPPORTED_ENTITIES),
            ner_strength=NER_SCORE,
            name=RECOGNIZER_NAMES[language],
        )
    ]
