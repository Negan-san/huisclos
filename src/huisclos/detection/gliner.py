"""Renfort PII GLiNER local, facultatif, chargé uniquement à la demande.

Entrées : texte d'analyse, langue, seuil propre au backend et snapshots locaux vérifiés.
Sorties : candidats Presidio aux offsets absolus, source ner_gliner, sans téléchargement.
Place : complète règles et spaCy avant projection canonique, fusion et propagation.
"""

import hashlib
import importlib.metadata
import json
import os
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path
from threading import RLock
from typing import Any

from presidio_analyzer import RecognizerResult

from huisclos.detection.pii_labels import LABELS, OVERLAP_TOKENS, SNAPSHOTS, WINDOW_TOKENS
from huisclos.detection.windows import best_views, mention, overlapping_windows
from huisclos.models import Source

ASSETS_ENV = "HUISCLOS_MODELS_DIR"
VERSIONS = {
    "gliner": "0.2.29",
    "transformers": "5.16.1",
    "huggingface-hub": "1.9.2",
    "torch": "2.14.1+cpu",
    "tokenizers": "0.23.3",
    "sentencepiece": "0.2.2",
}


def assets_root() -> Path:
    """Retourne le dossier explicite des actifs, ou le dossier local par défaut."""
    return Path(os.environ.get(ASSETS_ENV, Path.home() / ".cache" / "huisclos")).resolve()


def identity() -> str:
    """Décrit révisions, versions et fichiers locaux sans charger de modèle.

    Les fichiers absents sont représentés, pour invalider les anciens résultats sans faire
    échouer l'affichage. La validation cryptographique précède tout chargement réel.
    """
    root = assets_root()
    versions = {}
    for name in VERSIONS:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "absent"
    stamps = {}
    for key, (_, revision, files) in SNAPSHOTS.items():
        for name in files:
            path = root / "models" / key / name
            stat = path.stat() if path.is_file() else None
            stamps[f"{key}@{revision}/{name}"] = (stat.st_size, stat.st_mtime_ns) if stat else None
    manifest = root / "manifest.json"
    return json.dumps(
        {
            "root": str(root),
            "versions": versions,
            "files": stamps,
            "manifest": hashlib.sha256(manifest.read_bytes()).hexdigest()
            if manifest.is_file()
            else None,
            "labels": LABELS,
            "window": WINDOW_TOKENS,
            "overlap": OVERLAP_TOKENS,
            "encoder_limit": 512,
            "implementation": "A4.2",
        },
        sort_keys=True,
    )


@lru_cache(maxsize=32)
def _digest(path: str, size: int, modified: int) -> str:
    """Hache un fichier une fois par taille et date de modification, sans cache de texte."""
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def check_snapshot(root: Path) -> None:
    """Refuse manifeste, révision, fichier ou empreinte invalides avant tout chargement."""
    from huisclos.detection.pipeline import ModelUnavailableError

    try:
        models = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["models"]
        for key, (repo, revision, files) in SNAPSHOTS.items():
            entry = models[key]
            if (entry["repo"], entry["revision"]) != (repo, revision):
                raise ModelUnavailableError("local_revision")
            for name, expected in files.items():
                path = root / "models" / key / name
                stat = path.stat()
                if _digest(str(path), stat.st_size, stat.st_mtime_ns) != expected:
                    raise ModelUnavailableError("local_revision")
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ModelUnavailableError("local_missing") from error


@lru_cache(maxsize=2)
def _load(model_identity: str) -> tuple[Any, Any, RLock]:
    """Charge le moteur CPU vérifié ; la clé comprend les fichiers et versions exactes."""
    from huisclos.detection.pipeline import ModelUnavailableError

    spec = json.loads(model_identity)
    if spec["versions"] != VERSIONS:
        raise ModelUnavailableError("local_dependency")
    root = Path(spec["root"])
    check_snapshot(root)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from gliner import GLiNER

    with tempfile.TemporaryDirectory(prefix="huisclos-gliner-") as folder:
        runtime = Path(folder)
        weights = root / "models" / "gliner_multi_pii_v1" / "pytorch_model.bin"
        try:
            os.link(weights, runtime / weights.name)
        except OSError:
            shutil.copyfile(weights, runtime / weights.name)
        config = json.loads((weights.parent / "gliner_config.json").read_text(encoding="utf-8"))
        config["model_name"] = str(root / "models" / "mdeberta_v3_base")
        (runtime / "gliner_config.json").write_text(json.dumps(config), encoding="utf-8")
        model = GLiNER.from_pretrained(
            str(runtime),
            local_files_only=True,
            load_tokenizer=True,
            map_location="cpu",
            strict=True,
        )
    model.eval()
    tokenizer = model.data_processor.transformer_tokenizer
    if (
        tokenizer.vocab_size != 250101
        or model.config.max_len != 384
        or model.config.max_width != 12
    ):
        raise ModelUnavailableError("local_revision")
    tokenizer.model_max_length = int(
        model.model.token_rep_layer.bert_layer.model.config.max_position_embeddings
    )
    if tokenizer.model_max_length != 512:
        raise ModelUnavailableError("local_revision")
    return model, tokenizer, RLock()


def prepare() -> tuple[Any, Any, RLock]:
    """Renvoie le moteur en cache après vérification locale, sans conserver de document."""
    return _load(identity())


def validate_window(model: Any, tokenizer: Any, text: str) -> None:
    """Vérifie les vrais mots et l'encodage avec labels avant toute inférence.

    GLiNER active lui-même truncation=True. Sa limite native doit donc rester à 512,
    distincte de la fenêtre de texte à 256 ; le prompt des labels compte dans les 512.
    """
    words = [word for word, _, _ in model.data_processor.words_splitter(text)]
    if len(words) > model.config.max_len:
        raise RuntimeError("Fenêtre GLiNER trop longue ; aucune troncature autorisée.")
    prompted, _ = model.data_processor.prepare_inputs([words], [list(LABELS)])
    encoded = tokenizer(
        prompted, is_split_into_words=True, add_special_tokens=True, truncation=False
    )
    if len(encoded["input_ids"][0]) > min(512, tokenizer.model_max_length):
        raise RuntimeError("Texte et labels GLiNER trop longs ; troncature interdite.")


def analyze(text: str, threshold: float) -> list[RecognizerResult]:
    """Détecte les labels figés dans text et renvoie leurs positions absolues validées.

    Les fenêtres réservent le contexte des labels ; toute troncature ou tout offset invalide
    produit une erreur explicite. Aucun nom de ville ni date générique n'est demandé.
    """
    if not text.strip():
        return []
    model, tokenizer, lock = prepare()
    found = []
    with lock:
        for index, window in enumerate(
            overlapping_windows(text, tokenizer, OVERLAP_TOKENS, max_tokens=WINDOW_TOKENS)
        ):
            validate_window(model, tokenizer, window.text)
            items = model.predict_entities(
                window.text, list(LABELS), threshold=threshold, flat_ner=False, multi_label=True
            )
            for item in items:
                label = LABELS.get(item["label"])
                if label is None:
                    continue
                start, end, score = int(item["start"]), int(item["end"]), float(item["score"])
                if not 0 <= start < end <= len(window.text) or not 0 <= score <= 1:
                    raise RuntimeError("Offset ou score GLiNER invalide ; détection interrompue.")
                if item["text"] != window.text[start:end]:
                    raise RuntimeError("Texte GLiNER incohérent avec ses offsets.")
                found.append(mention(window, index, start, end, label, score))
    return [
        RecognizerResult(
            item.label,
            item.start,
            item.end,
            item.score,
            recognition_metadata={"huisclos_source": Source.NER_GLINER.value},
        )
        for item in best_views(found)
    ]
