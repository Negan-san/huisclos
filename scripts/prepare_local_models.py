"""Prépare hors dépôt les modèles locaux étudiés après G7 et écrit leur manifeste.

Entrées : identifiants Hugging Face à révision figée, cache local de CamemBERT, interpréteurs
des environnements baseline et candidat. Sorties : fichiers de modèles vérifiés dans un
dossier d'actifs hors dépôt, empreintes et manifest.json. Place : préparation des études,
jamais appelée par l'application ; seul fetch utilise le réseau, et sans envoyer de texte.
Usage : PY scripts/prepare_local_models.py fetch|export|envs|verify --assets <dossier>
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

HUB = "https://huggingface.co"
CAMEMBERT_CACHE = Path.home() / ".cache/huggingface/hub/models--Jean-Baptiste--camembert-ner"

# Révisions immuables relevées sur Hugging Face le 28 octobre 2026 ; seuls les fichiers
# nécessaires au chargement sont copiés, avec la carte du modèle pour la licence.
MODELS: dict[str, dict[str, Any]] = {
    "camembert_ner": {
        "repo": "Jean-Baptiste/camembert-ner",
        "revision": "ef35fe7767c1dad71f5c853838cdd80d0b3441ed",
        "kind": "token_classification",
        "files": [
            "config.json",
            "model.safetensors",
            "sentencepiece.bpe.model",
            "special_tokens_map.json",
            "tokenizer_config.json",
        ],
    },
    "anonym_ia_v2": {
        "repo": "Anonym-IA/V2-camembert-ner-pii-french",
        "revision": "b39848ccac582505a33dc859084f49a27bcd1402",
        "kind": "token_classification",
        "files": [
            "README.md",
            "added_tokens.json",
            "config.json",
            "model.safetensors",
            "sentencepiece.bpe.model",
            "special_tokens_map.json",
            "tokenizer.json",
            "tokenizer_config.json",
        ],
    },
    "gliner_multi_pii_v1": {
        "repo": "urchade/gliner_multi_pii-v1",
        "revision": "1fcf13e85f4eef5394e1fcd406cf2ca9ea82351d",
        "kind": "gliner",
        "files": ["README.md", "gliner_config.json", "pytorch_model.bin"],
    },
    # Le backbone de GLiNER fournit sa configuration et son tokenizer, pas ses poids.
    "mdeberta_v3_base": {
        "repo": "microsoft/mdeberta-v3-base",
        "revision": "a0484667b22365f84929a935b5e50a51f71f159d",
        "kind": "auxiliary",
        "files": ["README.md", "config.json", "spm.model", "tokenizer_config.json"],
    },
}
# Fichier retiré d'une copie temporaire pour vérifier qu'un manque échoue clairement : dans
# le dossier du modèle, ou dans celui du backbone pour GLiNER (ses poids sont trop lourds).
MISSING_PROBE = {
    "camembert_ner": ("model", "sentencepiece.bpe.model"),
    "anonym_ia_v2": ("model", "config.json"),
    "gliner_multi_pii_v1": ("backbone", "spm.model"),
}
REQUIRED = {
    "baseline_python": ("en_core_web_sm", "camembert_ner"),
    "candidate_python": ("en_core_web_sm", "gliner_multi_pii_v1"),
}
NOTES = {
    "baseline_python": (
        "Référence G7 : versions exactes du venv partagé au commit 4fc14cc (Transformers "
        "5.21.0, Hub 2.3.0). Seule addition déclarée : en_core_web_sm 3.8.0, absent de G7."
    ),
    "candidate_python": (
        "Étude B3 seulement : base G7 avec Transformers 5.16.1, Hub 1.9.2 et GLiNER 0.2.29 ; "
        "httpx2 et httpcore2, propres à Hub 2.x, retirés. Aucune migration appliquée au projet."
    ),
}
SAMPLE_FR = "Alice Martin travaille pour Acme SARL à Lyon."
SAMPLE_EN = "Alice Martin works for Acme Ltd in London."


def file_digests(path: Path) -> tuple[str, str]:
    """Renvoie l'empreinte SHA-256 du fichier et son identifiant de blob git (SHA-1)."""
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(f"blob {path.stat().st_size}\0".encode(), usedforsecurity=False)
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            sha256.update(chunk)
            blob.update(chunk)
    return sha256.hexdigest(), blob.hexdigest()


def remote_metadata(repo: str, revision: str) -> dict[str, Any]:
    """Lit la licence et les empreintes publiées des fichiers à une révision donnée."""
    url = f"{HUB}/api/models/{repo}/revision/{revision}?blobs=true"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.load(response)
    files = {
        item["rfilename"]: {
            "size": item.get("size"),
            "blob_id": item.get("blobId"),
            "lfs_sha256": (item.get("lfs") or {}).get("sha256"),
        }
        for item in data.get("siblings", [])
    }
    return {"license": (data.get("cardData") or {}).get("license"), "files": files}


def check_file(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    """Compare un fichier local aux empreintes publiées ; lève ValueError en cas d'écart."""
    sha256, blob_id = file_digests(path)
    if expected.get("lfs_sha256"):
        verified, ok = "lfs_sha256", sha256 == expected["lfs_sha256"]
    else:
        verified, ok = "git_blob_sha1", blob_id == expected.get("blob_id")
    if not ok:
        raise ValueError(f"empreinte différente pour {path.name}")
    return {"name": path.name, "size": path.stat().st_size, "sha256": sha256, "verified": verified}


def download(url: str, target: Path) -> None:
    """Télécharge url dans target par un fichier temporaire, sans cache partagé."""
    partial = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as handle:
        shutil.copyfileobj(response, handle, 1 << 20)
    partial.replace(target)


def provide_model(name: str, assets: Path, from_cache: bool) -> dict[str, Any]:
    """Copie ou télécharge les fichiers d'un modèle, vérifie chaque empreinte publiée.

    Valeur retournée : l'entrée du manifeste, au statut available ou unavailable.
    """
    spec = MODELS[name]
    target = assets / "models" / name
    entry: dict[str, Any] = {
        "repo": spec["repo"],
        "revision": spec["revision"],
        "kind": spec["kind"],
        "local_path": str(target),
    }
    try:
        metadata = remote_metadata(spec["repo"], spec["revision"])
        entry["license"] = metadata["license"]
        target.mkdir(parents=True, exist_ok=True)
        records = []
        for filename in spec["files"]:
            destination = target / filename
            if from_cache:
                source = CAMEMBERT_CACHE / "snapshots" / spec["revision"] / filename
                shutil.copyfile(source, destination)
            elif not destination.exists():
                url = f"{HUB}/{spec['repo']}/resolve/{spec['revision']}/{filename}"
                download(url, destination)
            records.append(check_file(destination, metadata["files"][filename]))
        entry.update(status="available", files=records)
    except (OSError, KeyError, ValueError) as error:
        entry.update(status="unavailable", error=f"{type(error).__name__}: {error}")
    return entry


def read_manifest(assets: Path) -> dict[str, Any]:
    """Relit manifest.json, ou renvoie un manifeste vide."""
    path = assets / "manifest.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema": 1, "assets_dir": str(assets), "models": {}, "environments": {}}


def summarize(manifest: dict[str, Any]) -> None:
    """Renseigne baseline_python et candidate_python, avec un statut net pour B3 et A2-A4.

    Un interpréteur est available si pip check passe et si ses modèles requis se chargent
    hors ligne ; sinon unavailable, jamais un succès supposé.
    """
    for key, required in REQUIRED.items():
        environment = manifest["environments"].get(key)
        results = manifest.get("checks", {}).get(key, {}).get("results", {})
        ready = (
            environment is not None
            and environment["pip_check"] == "ok"
            and all(results.get(model, {}).get("status") == "ok" for model in required)
        )
        manifest[key] = environment["interpreter"] if environment else None
        manifest[f"{key}_status"] = "available" if ready else "unavailable"
        manifest[f"{key}_note"] = NOTES[key]


def write_manifest(assets: Path, manifest: dict[str, Any]) -> None:
    """Écrit manifest.json de façon lisible et stable."""
    summarize(manifest)
    path = assets / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def describe_environment(python: Path, assets: Path, key: str) -> dict[str, Any]:
    """Relève version, paquets exacts et pip check d'un interpréteur, sans rien installer."""
    freeze = subprocess.run(
        [str(python), "-m", "pip", "freeze", "--all"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    check = subprocess.run(
        [str(python), "-m", "pip", "check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    version = subprocess.run(
        [str(python), "-c", "import sys; print(sys.version.split()[0])"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    freeze_path = assets / "envs" / f"{key}_freeze.txt"
    freeze_path.write_text(freeze, encoding="utf-8")
    pins = dict(line.split("==", 1) for line in freeze.splitlines() if "==" in line)
    watched = ("torch", "transformers", "huggingface_hub", "tokenizers", "spacy", "gliner")
    return {
        "interpreter": str(python),
        "python": version,
        "freeze": str(freeze_path),
        "freeze_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
        "key_versions": {name: pins.get(name) for name in watched},
        "spacy_models": [line.split(" @ ")[0] for line in freeze.splitlines() if "_core_" in line],
        "pip_check": "ok" if check.returncode == 0 else check.stdout.strip(),
    }


def probe(model: str, folder: str, backbone: str) -> dict[str, Any]:
    """Charge un modèle local dans ce processus, réseau coupé, et lance une inférence fictive.

    Exécutée dans un processus neuf par verify ; renvoie les entités trouvées.
    """
    import socket

    def refuse(*args: object, **kwargs: object) -> None:
        """Refuse toute connexion pendant la sonde."""
        raise OSError("réseau interdit pendant la vérification")

    socket.socket.connect = refuse  # type: ignore[method-assign]
    socket.create_connection = refuse  # type: ignore[assignment]
    if model == "en_core_web_sm":
        import spacy

        doc = spacy.load("en_core_web_sm")(SAMPLE_EN)
        return {"entities": [(ent.text, ent.label_) for ent in doc.ents]}
    if model == "gliner_multi_pii_v1":
        return probe_gliner(Path(folder), backbone)
    from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

    options = {"local_files_only": True, "trust_remote_code": False}
    tokenizer = AutoTokenizer.from_pretrained(folder, **options)
    network = AutoModelForTokenClassification.from_pretrained(folder, **options)
    # Transformers 5.21 accepte sans erreur un dossier privé de son vocabulaire.
    if tokenizer.vocab_size < network.config.vocab_size:
        raise ValueError(f"tokenizer incomplet : {tokenizer.vocab_size} jetons")
    runner = pipeline(
        "token-classification",
        model=network,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=-1,
    )
    found = runner(SAMPLE_FR)
    labels = sorted(set(network.config.id2label.values()))
    return {"entities": [(item["word"], item["entity_group"]) for item in found], "labels": labels}


def probe_gliner(folder: Path, backbone: str) -> dict[str, Any]:
    """Charge GLiNER depuis un dossier d'exécution temporaire, sans modifier les fichiers.

    GLiNER lit le nom du backbone dans gliner_config.json et ne permet pas de le remplacer
    au chargement. Le dossier temporaire lie donc les poids officiels (lien physique, sans
    copie) et ne change que model_name, qui pointe vers le backbone local.
    """
    from gliner import GLiNER

    with tempfile.TemporaryDirectory(prefix="gliner-runtime-") as runtime:
        weights = Path(runtime) / "pytorch_model.bin"
        try:
            os.link(folder / "pytorch_model.bin", weights)
        except OSError:
            shutil.copyfile(folder / "pytorch_model.bin", weights)
        config = json.loads((folder / "gliner_config.json").read_text(encoding="utf-8"))
        config["model_name"] = backbone
        target = Path(runtime) / "gliner_config.json"
        target.write_text(json.dumps(config), encoding="utf-8")
        gliner = GLiNER.from_pretrained(runtime, local_files_only=True, load_tokenizer=True)
    tokenizer = gliner.data_processor.transformer_tokenizer
    # Un vocabulaire réduit aux jetons spéciaux signale un fichier spm.model absent.
    if tokenizer.vocab_size < 250000:
        raise ValueError(f"tokenizer incomplet : {tokenizer.vocab_size} jetons")
    labels = ["person", "organization", "location"]
    found = [
        (item["text"], item["label"])
        for sample in (SAMPLE_FR, SAMPLE_EN)
        for item in gliner.predict_entities(sample, labels)
    ]
    return {"entities": found, "tokenizer_vocab": tokenizer.vocab_size}


def run_probe(python: Path, model: str, folder: Path, backbone: Path) -> dict[str, Any]:
    """Lance probe dans un processus neuf, caches HF vides et mode hors ligne forcé."""
    with tempfile.TemporaryDirectory(prefix="hf-empty-") as empty:
        env = {
            **os.environ,
            "HF_HOME": empty,
            "HF_HUB_CACHE": empty,
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONUTF8": "1",
        }
        command = [str(python), __file__, "_probe", model, str(folder), str(backbone)]
        done = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8", env=env, check=False
        )
    if done.returncode != 0:
        lines = done.stderr.strip().splitlines()
        return {"status": "failed", "error": lines[-1] if lines else "erreur inconnue"}
    return {"status": "ok", **json.loads(done.stdout.strip().splitlines()[-1])}


def verify(python: Path, key: str, assets: Path, models: list[str]) -> dict[str, Any]:
    """Vérifie le chargement hors ligne de chaque modèle, puis l'échec sur fichier manquant."""
    backbone = assets / "models" / "mdeberta_v3_base"
    results: dict[str, Any] = {}
    for model in models:
        folder = assets / "models" / model
        result = run_probe(python, model, folder, backbone)
        if model in MISSING_PROBE and result["status"] == "ok":
            place, filename = MISSING_PROBE[model]
            source = backbone if place == "backbone" else folder
            with tempfile.TemporaryDirectory(prefix="hf-missing-") as copy:
                partial = Path(copy) / source.name
                shutil.copytree(source, partial, ignore=shutil.ignore_patterns(".cache"))
                (partial / filename).unlink()
                if place == "backbone":
                    missing = run_probe(python, model, folder, partial)
                else:
                    missing = run_probe(python, model, partial, backbone)
            result["missing_file_check"] = {
                "removed": f"{source.name}/{filename}",
                "fails_clearly": missing["status"] == "failed",
                "error": missing.get("error"),
            }
        results[model] = result
    return {"interpreter": str(python), "environment": key, "results": results}


def main() -> None:
    """Point d'entrée : fetch, export, envs, verify, ou la sonde interne _probe."""
    if len(sys.argv) == 5 and sys.argv[1] == "_probe":
        sys.stdout.write(json.dumps(probe(*sys.argv[2:5]), ensure_ascii=False) + "\n")
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["fetch", "export", "envs", "verify"])
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--models", nargs="*", default=[])
    parser.add_argument("--env", action="append", default=[], help="clé=chemin de python")
    args = parser.parse_args()
    assets = args.assets.resolve()
    manifest = read_manifest(assets)
    if args.action in {"fetch", "export"}:
        names = ["camembert_ner"] if args.action == "export" else args.models
        for name in names:
            manifest["models"][name] = provide_model(name, assets, args.action == "export")
    for pair in args.env:
        key, python = pair.split("=", 1)
        if args.action == "envs":
            manifest["environments"][key] = describe_environment(Path(python), assets, key)
        elif args.action == "verify":
            checks = manifest.setdefault("checks", {})
            checks[key] = verify(Path(python), key, assets, args.models)
    write_manifest(assets, manifest)
    sys.stdout.write(json.dumps(manifest, indent=2, ensure_ascii=False)[:4000] + "\n")


if __name__ == "__main__":
    main()
