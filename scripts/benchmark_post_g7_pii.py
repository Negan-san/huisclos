"""Compare hors ligne les renforts PII sur les seuls corpus de développement.

Entrées : manifeste A1, plan préenregistré et prédictions locales en processus séparés.
Sorties : mesures, coûts échantillonnés et rapport B1 hors du dépôt.
Place : expérience B3 ; aucun adaptateur de ce fichier ne sert à la production.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
ASSETS = ROOT.parent / "pilotage/post_g7_assets"
GRID = (0.3, 0.5, 0.7)
LABELS = {
    "person": "PERSON",
    "organization": "ORGANIZATION",
    "address": "ADDRESS",
    "email": "EMAIL",
    "phone number": "PHONE",
    "date of birth": "BIRTH_DATE",
}
ANONYM = {
    "NOM_PERSONNE": "PERSON",
    "PRENOM_PERSONNE": "PERSON",
    "NOM_SOCIETE": "ORGANIZATION",
    "DOB": "BIRTH_DATE",
    "EMAIL": "EMAIL",
    "TELEPHONE": "PHONE",
}
CAM = {"PER": "PERSON", "ORG": "ORGANIZATION", "LOC": "LOCATION"}
CORPORA = {"fr": ROOT / "corpus/dev.jsonl", "en": ROOT / "corpus/english_dev/dev.jsonl"}


def digest(path: Path) -> str:
    """Renvoie le SHA-256 de path en lisant les poids par blocs."""
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def save(path: Path, value: Any) -> None:
    """Écrit un résultat neuf en UTF-8 ; refuse tout écrasement."""
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=True, indent=2)


def prepare(out: Path) -> None:
    """Fige la matrice, les labels et les empreintes avant toute extraction."""
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    for model in manifest["models"].values():
        for item in model["files"]:
            if digest(Path(model["local_path"]) / item["name"]) != item["sha256"]:
                raise ValueError("Empreinte locale différente du manifeste A1.")
    save(
        out / "plan.json",
        {
            "commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "manifest_sha256": digest(ASSETS / "manifest.json"),
            "grid": GRID,
            "labels": LABELS,
            "anonym_mapping": ANONYM,
            "cam_mapping": CAM,
            "corpora": {lang: digest(path) for lang, path in CORPORA.items()},
            "families": {
                "fr": [
                    [],
                    ["camembert_ner"],
                    ["anonym_ia_v2"],
                    ["gliner_multi_pii_v1"],
                    ["anonym_ia_v2", "gliner_multi_pii_v1"],
                ],
                "en": [[], ["gliner_multi_pii_v1"]],
            },
            "selection": (
                "B1 criterion versus best existing A1/A2; F2 then lowest thresholds within family"
            ),
            "standard_thresholds": {"fr": [0.3], "en": [n / 100 for n in range(30, 96, 5)]},
            "repetitions": 2,
            "threads": 2,
            "window_tokens_with_specials": 256,
            "overlap": 64,
            "gliner_max_width": 12,
            "rss_sampling_seconds": 0.02,
            "adapter": "prototype; A2 projection/merge/propagation; no isolated address components",
            "extra_cam": "only if best FR union still leaks and Cam covers an uncovered character",
        },
    )
    save(out / "plan_hash.json", digest(out / "plan.json"))


def checked_plan(out: Path) -> dict[str, Any]:
    """Refuse un plan ou des entrées modifiés depuis le préenregistrement."""
    if digest(out / "plan.json") != json.loads((out / "plan_hash.json").read_text("utf-8")):
        raise ValueError("Plan modifié.")
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    expected = (LABELS, ANONYM, CAM, list(GRID))
    if tuple(plan[k] for k in ("labels", "anonym_mapping", "cam_mapping", "grid")) != expected:
        raise ValueError("Labels ou grille du code différents du plan préenregistré.")
    if digest(ASSETS / "manifest.json") != plan["manifest_sha256"]:
        raise ValueError("Manifeste modifié.")
    if any(digest(CORPORA[lang]) != sha for lang, sha in plan["corpora"].items()):
        raise ValueError("Corpus dev modifié.")
    return plan


def refuse_network(*args: Any, **kwargs: Any) -> Any:
    """Interdit DNS et sockets avant tout chargement de bibliothèque."""
    raise OSError("B3 : réseau interdit")


def pack(detections: Any) -> list[list[Any]]:
    """Sérialise les positions sans valeurs ; la source expérimentale reste séparée."""
    return [[d.start, d.end, d.entity_type.value, d.score, d.source.value] for d in detections]


def unpack(text: str, rows: list[list[Any]]) -> list[Any]:
    """Reconstruit les détections depuis les positions exactes, sans recherche de texte."""
    from huisclos.models import Detection, EntityType, Source

    return [Detection(s, e, EntityType(k), p, Source(src), text[s:e]) for s, e, k, p, src in rows]


def load_backend(name: str, manifest: dict[str, Any]) -> tuple[Any, Any, dict[str, str], Any]:
    """Charge les poids CPU locaux ; renvoie modèle, tokenizer, labels et identité réelle."""
    folder = manifest["models"][name]["local_path"]
    if name == "gliner_multi_pii_v1":
        from gliner import GLiNER

        with tempfile.TemporaryDirectory(prefix="b3-gliner-") as runtime:
            os.link(Path(folder) / "pytorch_model.bin", Path(runtime) / "pytorch_model.bin")
            config = json.loads((Path(folder) / "gliner_config.json").read_text("utf-8"))
            config["model_name"] = manifest["models"]["mdeberta_v3_base"]["local_path"]
            (Path(runtime) / "gliner_config.json").write_text(json.dumps(config), encoding="utf-8")
            model = GLiNER.from_pretrained(runtime, local_files_only=True, load_tokenizer=True)
        tokenizer = model.data_processor.transformer_tokenizer
        identity = {
            "class": type(model).__name__,
            "parameters": sum(p.numel() for p in model.parameters()),
            "max_width": model.config.max_width,
            "max_len": model.config.max_len,
            "labels": LABELS,
        }
        mapping = LABELS
    else:
        from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

        from huisclos.detection.camembert import check_vocabulary

        options = {"local_files_only": True, "trust_remote_code": False}
        tokenizer = AutoTokenizer.from_pretrained(folder, **options)
        network = AutoModelForTokenClassification.from_pretrained(folder, **options)
        check_vocabulary(tokenizer, network)
        identity = {
            "class": type(network).__name__,
            "labels": network.config.id2label,
            "parameters": sum(p.numel() for p in network.parameters()),
        }
        model = pipeline(
            "token-classification",
            model=network,
            tokenizer=tokenizer,
            aggregation_strategy="simple",
            device=-1,
        )
        mapping = CAM if name == "camembert_ner" else ANONYM
    tokenizer.model_max_length = 256
    identity["tokenizer_vocab"] = tokenizer.vocab_size
    return model, tokenizer, mapping, identity


def proposals(text: str, backend: tuple[Any, Any, dict[str, str], Any], gliner: bool) -> list[Any]:
    """Projette les fenêtres A1 dans le texte canonique A2 ; ignore les labels hors politique."""
    from presidio_analyzer import RecognizerResult

    from huisclos.detection import pipeline as engine
    from huisclos.detection.analysis_view import build_view
    from huisclos.detection.windows import best_views, mention, overlapping_windows

    model, tokenizer, mapping, _ = backend
    view, found = build_view(text), []
    for index, window in enumerate(overlapping_windows(view.text, tokenizer)):
        if gliner:
            if len(list(model.data_processor.words_splitter(window.text))) > model.config.max_len:
                raise ValueError("Fenêtre GLiNER tronquée.")
            items = model.predict_entities(
                window.text, list(mapping), threshold=min(GRID), flat_ner=False, multi_label=True
            )
        else:
            items = model(window.text)
        for item in items:
            label = mapping.get(item["label"] if gliner else item["entity_group"])
            start, end = int(item["start"]), int(item["end"])
            if label and 0 <= start < end <= len(window.text):
                found.append(mention(window, index, start, end, label, float(item["score"])))
    projected = [
        engine._projected(
            text,
            view,
            RecognizerResult(
                m.label,
                m.start,
                m.end,
                m.score,
                recognition_metadata={"huisclos_source": "ner_camembert"},
            ),
        )
        for m in best_views(found)
    ]
    return [d for d in projected if d is not None]


def extract(
    out: Path,
    language: str,
    names: str,
    environment: str,
    repeat: int,
    full_profile: bool = False,
    production_cam: bool = False,
) -> None:
    """Mesure une extraction en processus neuf, caches vides, CPU et RSS échantillonné."""
    import psutil

    plan = checked_plan(out)
    if names != "standard" and names.split("+") not in plan["families"][language]:
        raise ValueError("Backend absent de la matrice de cette langue.")
    scope = "full_" if full_profile else ""
    prefix = "production_" if production_cam else ""
    if production_cam and names != "camembert_ner":
        raise ValueError("Le contrôle 512 est réservé au comparateur CamemBERT existant.")
    target = out / f"{prefix}{language}_{scope}{names}_{environment}_{repeat}.json"
    source_sha = digest(Path(__file__))
    if target.exists():
        raise ValueError("Résultat déjà présent.")
    process, stop, samples = psutil.Process(), threading.Event(), []

    def sample() -> None:
        """Échantillonne réellement le RSS jusqu'à l'arrêt du worker."""
        while not stop.is_set():
            samples.append(process.memory_info().rss)
            stop.wait(0.02)

    sampler = threading.Thread(target=sample, daemon=True)
    sampler.start()
    with tempfile.TemporaryDirectory(prefix="b3-empty-hf-") as empty:
        os.environ.update(
            HF_HOME=empty,
            HF_HUB_CACHE=str(Path(empty) / "hub"),
            HF_HUB_OFFLINE="1",
            TRANSFORMERS_OFFLINE="1",
            TOKENIZERS_PARALLELISM="false",
        )
        socket.socket.connect = refuse_network
        socket.socket.connect_ex = refuse_network
        socket.socket.sendto = refuse_network
        socket.create_connection = refuse_network
        socket.getaddrinfo = refuse_network
        started = time.perf_counter()
        import torch

        from huisclos.config import PRESETS
        from huisclos.detection import pipeline as engine
        from huisclos.detection.analysis_view import build_view
        from huisclos.evaluation.run import load_unreserved

        torch.set_num_threads(plan["threads"])
        torch.manual_seed(45)
        manifest = json.loads((ASSETS / "manifest.json").read_text("utf-8"))
        if Path(sys.executable).resolve() != Path(manifest[environment + "_python"]).resolve():
            raise ValueError("Interpréteur différent du manifeste.")
        documents = load_unreserved(CORPORA[language], "dev")
        config = replace(PRESETS["hybrid"], document_language=language, threshold=0.3)
        backends = (
            {}
            if names == "standard"
            else {name: load_backend(name, manifest) for name in names.split("+")}
        )
        if production_cam:
            backends["camembert_ner"][1].model_max_length = 512
            backends["camembert_ner"][3]["window_tokens_with_specials"] = 512
        if not backends or full_profile:
            analyzer = engine.analyzer_for(config)
            spacy_meta = analyzer.nlp_engine.nlp[language].meta
        else:
            spacy_meta = None
        loaded = time.perf_counter()
        rows = [
            pack(
                [
                    d
                    for name, backend in backends.items()
                    for d in proposals(doc.text, backend, name == "gliner_multi_pii_v1")
                ]
            )
            if backends
            else pack(engine._analyze(doc.text, build_view(doc.text), config))
            for doc in documents
        ]
        if full_profile and backends:
            for doc in documents:
                engine._analyze(doc.text, build_view(doc.text), config)
        elapsed = time.perf_counter() - loaded
        cache_files = [str(p.relative_to(empty)) for p in Path(empty).rglob("*") if p.is_file()]
        versions = {
            n: importlib.metadata.version(n)
            for n in ("torch", "transformers", "huggingface_hub", "spacy", "tokenizers")
        }
        if "gliner_multi_pii_v1" in backends:
            versions["gliner"] = importlib.metadata.version("gliner")
    stop.set()
    sampler.join()
    save(
        target,
        {
            "language": language,
            "backend": names,
            "environment": environment,
            "repeat": repeat,
            "resource_scope": "standard_plus_backends" if full_profile else "backend_only",
            "production_cam": production_cam,
            "load_seconds": loaded - started,
            "infer_seconds": elapsed,
            "peak_rss_bytes": max(samples),
            "rss_samples": len(samples),
            "cache_files": cache_files,
            "versions": versions,
            "python": sys.version,
            "identity": {k: v[3] for k, v in backends.items()},
            "spacy": spacy_meta,
            "documents": rows,
            "script_sha256": source_sha,
            "plan_sha256": digest(out / "plan.json"),
        },
    )


def replay(text: str, raw: list[Any], language: str, threshold: float) -> list[Any]:
    """Réexécute la logique A2 depuis les candidats bruts, sans réinférence ni text.find."""
    from huisclos.config import PRESETS
    from huisclos.detection import pipeline as engine

    with patch.object(engine, "_analyze", return_value=raw):
        return engine.detect(
            text, replace(PRESETS["hybrid"], document_language=language, threshold=threshold)
        )


def main() -> None:
    """Expose préparation, worker isolé et synthèse, sans aucune option de corpus réservé."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "extract", "summarize"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--language", choices=("fr", "en"), default="fr")
    parser.add_argument("--backend", default="standard")
    parser.add_argument("--environment", choices=("baseline", "candidate"), default="baseline")
    parser.add_argument("--repeat", type=int, choices=(1, 2), default=1)
    parser.add_argument("--full-profile", action="store_true")
    parser.add_argument("--production-cam", action="store_true")
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(ROOT):
        parser.error("Les rapports doivent rester hors dépôt.")
    if args.action == "prepare":
        prepare(args.out)
    elif args.action == "extract":
        extract(
            args.out,
            args.language,
            args.backend,
            args.environment,
            args.repeat,
            args.full_profile,
            args.production_cam,
        )
    else:
        from scripts.audit_post_g7_invariants import summarize

        summarize(args.out, args.language)


if __name__ == "__main__":
    main()
