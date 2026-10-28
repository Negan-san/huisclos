"""Archive le recontrôle technique sans nouvelle mesure réservée.

Entrées : commit FIX, rapports G8, environnements et modèles locaux inchangés.
Sorties : preuves d'intégrité et sondes hors ligne sur des textes fictifs.
Les rapports antérieurs restent intacts et aucun corpus n'est ouvert ici.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ASSETS = ROOT.parent / "pilotage/post_g7_assets"
FIX = "37f98f15bd82ac2edf4c4d6ebe03d2ec0c58cb10"
G8 = "1ecb063"


def digest(path: Path) -> str:
    """Renvoie l'empreinte des octets d'un fichier sans afficher son contenu."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(arguments: list[str]) -> str:
    """Exécute une lecture locale et retourne sa sortie UTF-8 après contrôle du code."""
    return subprocess.run(
        arguments, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout


def save(name: str, payload: Any) -> None:
    """Crée un reçu neuf ; refuse d'écraser un essai antérieur."""
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def integrity() -> None:
    """Vérifie le gel, les rapports archivés, les deux environnements et vingt poids."""
    changed = command(["git", "diff", "--name-only", G8, FIX]).splitlines()
    assert set(changed) == {
        "docs/DECISIONS.md",
        "docs/POST_G7_PROTOCOL.md",
        "docs/PROGRESS.md",
        "docs/PROMPTS.md",
        "scripts/gate8_measure.py",
        "tests/test_gate8.py",
    }
    protected = ["src", "app", "data", ".streamlit"]
    trees = {}
    for path in protected:
        original = command(["git", "rev-parse", f"e3d13bd:{path}"]).strip()
        assert original == command(["git", "rev-parse", f"{FIX}:{path}"]).strip()
        trees[path] = original
    reports = {}
    for line in command(["git", "ls-tree", "-r", G8, "results/gate8"]).splitlines():
        header, name = line.split("\t", 1)
        blob = header.split()[2]
        raw_blob = command(["git", "hash-object", "--no-filters", name]).strip()
        assert command(["git", "hash-object", name]).strip() == blob
        if Path(name).suffix != ".py":
            assert raw_blob == blob
        reports[name] = {
            "git_blob": blob,
            "sha256": digest(ROOT / name),
            "raw_equal_to_blob": raw_blob == blob,
        }
    old = json.loads((ROOT / "results/gate8/provenance.json").read_text(encoding="utf-8"))
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    environments = {}
    for label, python in (
        ("current", sys.executable),
        ("g7_reference", manifest["baseline_python"]),
    ):
        expected = old["environments"][label]
        freeze = Path(expected["freeze_path"])
        assert digest(freeze) == expected["freeze_sha256"]
        assert (
            command([python, "-m", "pip", "freeze", "--all"]).splitlines()
            == freeze.read_text(encoding="utf-8").splitlines()
        )
        environments[label] = {
            "python": python,
            "pip_check": command([python, "-m", "pip", "check"]).strip(),
            "freeze_sha256": digest(freeze),
            "freeze_equal_to_g8": True,
        }
    models = []
    for key, entry in manifest["models"].items():
        for item in entry["files"]:
            assert digest(Path(entry["local_path"]) / item["name"]) == item["sha256"]
            models.append({"model": key, "file": item["name"], "sha256": item["sha256"]})
    assert digest(ASSETS / "manifest.json") == old["model_manifest_sha256"]
    save(
        "integrity.json",
        {
            "verified_at_utc": datetime.now(UTC).isoformat(),
            "freeze_commit": FIX,
            "changed_since_g8": changed,
            "protected_trees_equal": trees,
            "g8_artifacts_unchanged": reports,
            "environments": environments,
            "model_files": models,
            "measurement_choice": "reuse G8; no reserved detection",
            "new_reserved_attempts": 0,
            "c3_status": "previously measured holdout; no fresh blind validation",
            "g8_registration_sha256": digest(ROOT / "results/gate8/registration.json"),
            "fix_harness_sha256": digest(ROOT / "scripts/gate8_measure.py"),
        },
    )
    print(f"Integrity: {len(reports)} G8 artifacts, {len(models)} model files, two environments.")


def offline() -> None:
    """Relance les sondes techniques G8, en processus neufs et sans corpus réservé."""
    # Le worker G8 n'écrit aucun reçu lorsqu'il reçoit une langue et un état de paquet.
    probe = ROOT / "results/gate8/offline_probe.py"
    results = {}
    for language in ("fr", "en"):
        for missing in (False, True):
            with (
                tempfile.TemporaryDirectory(prefix="g8r-package-") as package_name,
                tempfile.TemporaryDirectory(prefix="g8r-cache-") as cache_name,
            ):
                package, cache = Path(package_name).resolve(), Path(cache_name).resolve()
                if missing:
                    (package / "manifest.json").write_bytes((ASSETS / "manifest.json").read_bytes())
                    for source in (ASSETS / "models").rglob("*"):
                        if source.is_file():
                            target = package / source.relative_to(ASSETS)
                            target.parent.mkdir(parents=True, exist_ok=True)
                            os.link(source, target)
                    absent = (
                        package
                        / "models"
                        / (
                            "camembert_ner/sentencepiece.bpe.model"
                            if language == "fr"
                            else "mdeberta_v3_base/spm.model"
                        )
                    )
                    assert absent.resolve().is_relative_to(package)
                    absent.unlink()
                else:
                    package = ASSETS
                environment = os.environ | {
                    "PYTHONUTF8": "1",
                    "HUISCLOS_MODELS_DIR": str(package),
                    "HF_HOME": str(cache),
                    "HF_HUB_CACHE": str(cache / "hub"),
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                    "OMP_NUM_THREADS": "2",
                    "MKL_NUM_THREADS": "2",
                    "TOKENIZERS_PARALLELISM": "false",
                }
                completed = subprocess.run(
                    [sys.executable, str(probe), language, "missing" if missing else "complete"],
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                key = language + ("_missing" if missing else "_complete")
                save(
                    f"offline-{key}.json",
                    {
                        "completed_at_utc": datetime.now(UTC).isoformat(),
                        "exit_code": completed.returncode,
                        "synthetic_only": True,
                    },
                )
                assert completed.returncode == 0, f"Offline probe failed: {key}"
                results[key] = json.loads(completed.stdout.strip().splitlines()[-1])
                assert not [path for path in cache.rglob("*") if path.is_file()]
                results[key]["cache_files"] = 0
                print(f"Offline {key}: OK", flush=True)
    save("offline.json", results)


if __name__ == "__main__":
    {"integrity": integrity, "offline": offline}[sys.argv[1]]()
