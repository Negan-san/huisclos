"""Reconnaissance locale des personnes, sociétés et lieux avec CamemBERT.

Entrées : texte français et modèle Jean-Baptiste/camembert-ner déjà en cache.
Sorties : résultats Presidio aux positions du texte original, avec leurs probabilités.
Place dans le pipeline : source statistique facultative, avant fusion et propagation.
"""

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from presidio_analyzer import EntityRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpArtifacts

from huisclos.config import CAMEMBERT_REPO, CAMEMBERT_REVISION
from huisclos.detection.windows import best_views, mention, overlapping_windows
from huisclos.models import Source

MODEL_NAME = "Jean-Baptiste/camembert-ner"
LABEL_MAPPING = {"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION"}
PACKAGE_FILES = {
    "config.json": "17ec2dd3a642bfc839f3f94bd5ba2e996700aa69b06b3937b0e80b458b962207",
    "model.safetensors": "decc811bc764b0e94f1adc16b37a127300201eb8b5e4b733a89185d68b9d81c9",
    "sentencepiece.bpe.model": "988bc5a00281c6d210a5d34bd143d0363741a432fefe741bf71e61b1869d4314",
    "special_tokens_map.json": "645708b160268d79dbc31bc05bc93f77fda8dfd45dc806b5c3a86e17cfcc5a7a",
    "tokenizer_config.json": "a47e711439fb76c78b60929e8baa3a487a36b476c01886934d5dd2ec5d0c8f8f",
}


@lru_cache(maxsize=32)
def _package_digest(path: str, size: int, modified: int) -> str:
    """Calcule le SHA-256 d'un fichier par version locale, sans conserver de texte."""
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def local_package() -> str | None:
    """Vérifie le paquet explicite A1 ; None signifie utiliser le cache historique.

    HUISCLOS_MODELS_DIR permet un chargement autonome avec caches Hugging Face vides.
    Un paquet explicitement demandé mais incomplet est refusé sans repli vers le cache.
    """
    from huisclos.detection.pipeline import ModelUnavailableError

    location = os.environ.get("HUISCLOS_MODELS_DIR")
    if not location:
        return None
    root = Path(location).resolve()
    folder = root / "models" / "camembert_ner"
    try:
        entry = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["models"][
            "camembert_ner"
        ]
        if (entry["repo"], entry["revision"]) != (CAMEMBERT_REPO, CAMEMBERT_REVISION):
            raise ModelUnavailableError("revision")
        for name, expected in PACKAGE_FILES.items():
            path = folder / name
            stat = path.stat()
            if _package_digest(str(path), stat.st_size, stat.st_mtime_ns) != expected:
                raise ModelUnavailableError("revision")
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ModelUnavailableError("missing") from error
    return str(folder)


def package_identity() -> str:
    """Identifie le chemin explicite et ses fichiers sans charger ni valider un modèle."""
    location = os.environ.get("HUISCLOS_MODELS_DIR")
    if not location:
        return "huggingface_cache"
    root = Path(location).resolve()
    stamps = {}
    for name in PACKAGE_FILES:
        path = root / "models" / "camembert_ner" / name
        stat = path.stat() if path.is_file() else None
        stamps[name] = (stat.st_size, stat.st_mtime_ns) if stat else None
    return json.dumps({"root": str(root), "files": stamps}, sort_keys=True)


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
        location = local_package() or MODEL_NAME
        tokenizer = AutoTokenizer.from_pretrained(
            location, revision=CAMEMBERT_REVISION, local_files_only=True, trust_remote_code=False
        )
        model = AutoModelForTokenClassification.from_pretrained(
            location, revision=CAMEMBERT_REVISION, local_files_only=True, trust_remote_code=False
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
