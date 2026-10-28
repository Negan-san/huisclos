"""Reconnaissance locale des personnes, sociétés et lieux avec CamemBERT.

Entrées : texte français et modèle Jean-Baptiste/camembert-ner déjà en cache.
Sorties : résultats Presidio aux positions du texte original, avec leurs probabilités.
Place dans le pipeline : source statistique facultative, avant fusion et propagation.
"""

import os
from functools import lru_cache
from typing import Any

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from huisclos.detection.windows import best_views, mention, overlapping_windows
from huisclos.models import Source

MODEL_NAME = "Jean-Baptiste/camembert-ner"
LABEL_MAPPING = {"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION"}


def check_vocabulary(tokenizer: Any, model: Any) -> None:
    """Refuse un tokenizer local incomplet, plus petit que le vocabulaire du modèle.

    Sans son fichier sentencepiece, Transformers 5.21 construit sans erreur un tokenizer
    réduit aux jetons spéciaux (constaté en A1) : le modèle lirait alors un texte vide de
    sens et ne trouverait plus rien, en silence.
    """
    expected = int(model.config.vocab_size)
    if int(tokenizer.vocab_size) < expected:
        raise RuntimeError(
            f"Tokenizer local incomplet : {tokenizer.vocab_size} jetons pour {expected} "
            "attendus ; le fichier du vocabulaire manque dans le cache."
        )


@lru_cache(maxsize=1)
def load_pipeline() -> Any:
    """Charge une fois le modèle CPU depuis le cache ; aucun téléchargement permis.

    Renvoie le pipeline transformers. Une dépendance ou un cache absent produit une
    erreur explicite, sans remplacer silencieusement la configuration demandée.
    """
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
    except ImportError as error:
        raise RuntimeError(
            "CamemBERT nécessite les dépendances locales de requirements-transformers.txt."
        ) from error
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME, local_files_only=True, trust_remote_code=False
        )
        model = AutoModelForTokenClassification.from_pretrained(
            MODEL_NAME, local_files_only=True, trust_remote_code=False
        )
    except OSError as error:
        raise RuntimeError(
            f"Le modèle {MODEL_NAME} doit être présent dans le cache local ; réseau désactivé."
        ) from error
    check_vocabulary(tokenizer, model)
    return pipeline(
        "token-classification",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=-1,
    )


class CamembertRecognizer(EntityRecognizer):
    """Reconnaisseur Presidio français dont les scores sont les probabilités du modèle."""

    def __init__(self) -> None:
        """Déclare les trois types reconnus et charge le pipeline partagé en mémoire."""
        super().__init__(
            supported_entities=list(LABEL_MAPPING.values()),
            supported_language="fr",
            name="CamembertRecognizer",
        )

    def load(self) -> None:
        """Récupère le pipeline CPU partagé, chargé uniquement pour cette option."""
        self.pipeline = load_pipeline()

    def analyze(
        self,
        text: str,
        entities: list[str],
        nlp_artifacts: NlpArtifacts | None = None,
    ) -> list[RecognizerResult]:
        """Renvoie les types demandés dans text avec leurs positions absolues exactes.

        Le texte est lu par fenêtres recouvrantes (detection.windows) ; les positions
        rendues par le modèle sont décalées du début de leur fenêtre, jamais recherchées
        dans le texte. Une mention vue par deux fenêtres n'est rendue qu'une fois.
        """
        if not text.strip() or not set(entities).intersection(self.supported_entities):
            return []
        mentions = []
        for index, window in enumerate(overlapping_windows(text, self.pipeline.tokenizer)):
            for item in self.pipeline(window.text):
                entity_type = LABEL_MAPPING.get(item["entity_group"])
                start, end = int(item["start"]), int(item["end"])
                if entity_type not in entities or not 0 <= start < end <= len(window.text):
                    continue
                mentions.append(
                    mention(window, index, start, end, entity_type, float(item["score"]))
                )
        return [
            RecognizerResult(
                entity_type=found.label,
                start=found.start,
                end=found.end,
                score=found.score,
                recognition_metadata={
                    "recognizer_name": self.name,
                    "huisclos_source": Source.NER_CAMEMBERT.value,
                },
            )
            for found in best_views(mentions)
        ]


def build_camembert_recognizers() -> list[EntityRecognizer]:
    """Renvoie le reconnaisseur français facultatif attendu par detection.pipeline."""
    return [CamembertRecognizer()]
