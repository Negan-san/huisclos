"""Reconnaissance d'entités nommées en français avec spaCy, via Presidio.

Entrées : le nom d'un modèle spaCy installé (fr_core_news_md par défaut) et un texte.
Sorties : un moteur NLP Presidio et un reconnaisseur de personnes, sociétés et lieux dont
chaque résultat porte la source "ner_spacy".
Place dans le pipeline : première source de détection statistique, avant les exclusions et la
fusion ; ses scores suivent le barème D-07 (voir D-S12-1).
"""

import spacy.util
from presidio_analyzer import RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts, NlpEngine, NlpEngineProvider
from presidio_analyzer.predefined_recognizers import SpacyRecognizer

from huisclos.models import Source

DEFAULT_MODEL = "fr_core_news_md"
LANGUAGE = "fr"

# Score fixe que Presidio attribue à toute entité spaCy (NerModelConfiguration.default_score).
NER_SCORE = 0.85

# Étiquettes du modèle français vers les types Presidio. MISC (divers) est écarté : trop
# bruité pour être proposé à l'utilisateur.
LABEL_MAPPING = {"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION"}
SUPPORTED_ENTITIES = ["PERSON", "ORGANIZATION", "LOCATION"]


class FrenchSpacyRecognizer(SpacyRecognizer):
    """Reconnaisseur NER spaCy qui marque ses résultats avec la source ner_spacy."""

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


def build_nlp_engine(model_name: str = DEFAULT_MODEL) -> NlpEngine:
    """Construit le moteur spaCy de Presidio pour le français.

    Paramètre : model_name, le modèle spaCy déjà installé.
    Valeur retournée : le moteur NLP chargé, avec PER, ORG et LOC convertis et MISC ignoré.
    Lève RuntimeError si le modèle manque : Presidio le téléchargerait, ce qui romprait le
    principe d'absence d'appel réseau à l'exécution.
    """
    if not spacy.util.is_package(model_name):
        raise RuntimeError(
            f"Le modèle spaCy {model_name} n'est pas installé ; "
            "installez-le avec requirements.txt (aucun téléchargement automatique)."
        )
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": LANGUAGE, "model_name": model_name}],
        "ner_model_configuration": {
            "model_to_presidio_entity_mapping": LABEL_MAPPING,
            "labels_to_ignore": ["MISC"],
            "default_score": NER_SCORE,
        },
    }
    return NlpEngineProvider(nlp_configuration=configuration).create_engine()


def build_ner_recognizers() -> list[SpacyRecognizer]:
    """Renvoie les reconnaisseurs NER, uniquement en langue française.

    Aucun reconnaisseur anglais n'est créé : le registre Presidio par défaut en ajoute, ce
    qui produirait des détections hors sujet.
    """
    return [
        FrenchSpacyRecognizer(
            supported_language=LANGUAGE,
            supported_entities=list(SUPPORTED_ENTITIES),
            ner_strength=NER_SCORE,
            name="FrenchSpacyRecognizer",
        )
    ]
