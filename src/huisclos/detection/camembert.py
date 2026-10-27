"""Reconnaissance locale des personnes, sociétés et lieux avec CamemBERT.

Entrées : texte français et modèle Jean-Baptiste/camembert-ner déjà en cache.
Sorties : résultats Presidio aux positions du texte original, avec leurs probabilités.
Place dans le pipeline : source statistique facultative, avant fusion et propagation.
"""

import os
import re
from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from huisclos.models import Source

MODEL_NAME = "Jean-Baptiste/camembert-ner"
LABEL_MAPPING = {"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION"}
BOUNDARY = re.compile(r"\n\s*\n|[.!?](?:[\"')\]]*)\s+")


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
    return pipeline(
        "token-classification",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=-1,
    )


def iter_chunks(text: str, tokenizer: Any) -> Iterator[tuple[int, str]]:
    """Découpe text sans le modifier et renvoie chaque morceau avec son début absolu.

    Les paragraphes ou phrases sont privilégiés. Une phrase trop longue est coupée
    sur un blanc, puis sur un caractère si nécessaire. Chaque morceau est retokenisé
    pour garantir la limite, même si la segmentation change à sa nouvelle frontière.
    """
    limit = min(512, tokenizer.model_max_length) - tokenizer.num_special_tokens_to_add()
    if limit < 1:
        raise ValueError("La limite du tokenizer ne laisse aucune place au texte.")
    start = 0
    while start < len(text):
        remaining = text[start:]
        encoded = tokenizer(
            remaining,
            add_special_tokens=False,
            return_offsets_mapping=True,
            truncation=False,
            verbose=False,
        )
        if len(encoded["input_ids"]) <= limit:
            yield start, remaining
            return
        end = encoded["offset_mapping"][limit][0]
        if end <= 0:
            end = encoded["offset_mapping"][limit - 1][1]
        boundaries = list(BOUNDARY.finditer(remaining, 0, end))
        if boundaries:
            end = boundaries[-1].end()
        else:
            blanks = list(re.finditer(r"\s+", remaining[:end]))
            if blanks:
                end = blanks[-1].end()
        while end > 0:
            size = len(tokenizer(remaining[:end], add_special_tokens=False)["input_ids"])
            if size <= limit:
                break
            end -= 1
        if end == 0:
            raise ValueError("Un caractère dépasse la capacité du tokenizer.")
        yield start, remaining[:end]
        start += end


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
        """Renvoie les types demandés dans text avec leurs positions absolues exactes."""
        if not text.strip() or not set(entities).intersection(self.supported_entities):
            return []
        results = []
        for offset, chunk in iter_chunks(text, self.pipeline.tokenizer):
            for item in self.pipeline(chunk):
                entity_type = LABEL_MAPPING.get(item["entity_group"])
                start, end = int(item["start"]), int(item["end"])
                if entity_type not in entities or not 0 <= start < end <= len(chunk):
                    continue
                results.append(
                    RecognizerResult(
                        entity_type=entity_type,
                        start=offset + start,
                        end=offset + end,
                        score=float(item["score"]),
                        recognition_metadata={
                            "recognizer_name": self.name,
                            "huisclos_source": Source.NER_CAMEMBERT.value,
                        },
                    )
                )
        return results


def build_camembert_recognizers() -> list[EntityRecognizer]:
    """Renvoie le reconnaisseur français facultatif attendu par detection.pipeline."""
    return [CamembertRecognizer()]
