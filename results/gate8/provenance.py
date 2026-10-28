"""Archive la référence et vérifie les environnements sans installation.

Entrées : manifestes A1/A4, paquets installés et sorties historiques G7.
Sorties : versions réelles, hashes et copie neuve des rapports historiques.
Ce contrôle précède toute détection sur un corpus réservé.
"""

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ASSETS = ROOT.parent / "pilotage/post_g7_assets"


def digest(path: Path) -> str:
    """Hache les octets sur disque sans afficher leur contenu."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    """Vérifie freezes, dépendances, poids et ancêtres puis archive les agrégats G7."""
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    retained = json.loads(
        (ASSETS / "benchmarks/A4/retained-runtime-final.json").read_text(encoding="utf-8")
    )
    versions = {name: version(name) for name in retained["versions"]}
    assert versions == retained["versions"]
    environments = {}
    for label, python, freeze in (
        ("g7_reference", manifest["baseline_python"], ASSETS / "envs/baseline_python_freeze.txt"),
        ("current", sys.executable, ASSETS / "benchmarks/A4/shared-final-freeze.txt"),
    ):
        check = subprocess.run(
            [python, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        actual = subprocess.run(
            [python, "-m", "pip", "freeze", "--all"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout
        assert actual.splitlines() == freeze.read_text(encoding="utf-8").splitlines()
        environments[label] = {
            "python": python,
            "pip_check": check.stdout.strip(),
            "freeze_path": str(freeze),
            "freeze_sha256": digest(freeze),
            "freeze_normalized_equal": True,
        }
    files = []
    for key, entry in manifest["models"].items():
        for item in entry["files"]:
            path = Path(entry["local_path"]) / item["name"]
            assert digest(path) == item["sha256"]
            files.append({"model": key, "file": item["name"], "sha256": item["sha256"]})
    for descendant in ("08a2e83", "029caa9"):
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                retained.get("freeze_commit", "dc5b041"),
                descendant,
            ],
            cwd=ROOT,
            check=True,
        )
    changes = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "08a2e83"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.splitlines()
    assert all(
        path.startswith(("corpus/", "docs/parallel/", "docs/prompts/"))
        or path == "scripts/build_blind_post_g7.py"
        for path in changes
    )
    archive = OUT / "g7_archive"
    archive.mkdir(exist_ok=False)
    history = {}
    for source in (ROOT / "results").iterdir():
        if source.is_file():
            shutil.copyfile(source, archive / source.name)
            assert digest(source) == digest(archive / source.name)
            history[source.name] = digest(source)
    payload = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "python_version": platform.python_version(),
        "current_versions": versions,
        "environments": environments,
        "model_files": files,
        "c3_after_a4": True,
        "c3_logic_changes": 0,
        "c3_changed_file_count": len(changes),
        "g7_archive": history,
        "machine": platform.platform(),
        "processor": platform.processor(),
        "model_manifest_sha256": digest(ASSETS / "manifest.json"),
        "runtime_manifest_sha256": digest(ASSETS / "benchmarks/A4/retained-runtime-final.json"),
    }
    with (OUT / "provenance.json").open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(
        f"Provenance verified: {len(files)} model files, two unchanged environments, "
        f"{len(history)} archived reports."
    )


if __name__ == "__main__":
    main()
