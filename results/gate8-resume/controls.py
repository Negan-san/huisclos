"""Archive les prérequis de G8R2 sans ouvrir les corpus réservés.

Entrées : commits figés, preuves FIX3R et environnement local existant.
Sorties : périmètre, identité des modèles et journaux de contrôles.
La mesure réservée dispose d'un lanceur distinct à reçu exclusif.
"""

import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/gate8-resume"
BASE = "4b8a686"
FIX = "930c414dd7ae1e7128b292bfa7bac1e45f27b1e9"
ENVIRONMENT = {
    "PYTHONUTF8": "1",
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "OMP_NUM_THREADS": "2",
    "MKL_NUM_THREADS": "2",
    "TOKENIZERS_PARALLELISM": "false",
    "HUISCLOS_MODELS_DIR": str(ROOT.parent / "pilotage/post_g7_assets"),
}


def git(*args: str) -> str:
    """Renvoie une sortie Git sans lire le contenu des corpus."""
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def digest(path: Path) -> str:
    """Calcule une empreinte de preuve ou de modèle, jamais celle d'un corpus."""
    assert not path.resolve().is_relative_to(ROOT / "corpus")
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path: str) -> Any:
    """Relit une preuve JSON autorisée, sans texte de document."""
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def save(name: str, value: Any) -> None:
    """Crée exclusivement une nouvelle preuve JSON, sans écraser les essais précédents."""
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def scope() -> None:
    """Vérifie le diff FIX4 et fige les empreintes des anciennes archives inchangées."""
    assert git("rev-parse", "HEAD") == FIX
    assert git("branch", "--show-current") == "lane-b"
    changed = git("diff", "--name-only", BASE, FIX).splitlines()
    permitted = {
        "app/state.py",
        "app/steps/review_step.py",
        "tests/test_fix4.py",
        "docs/PROGRESS.md",
        "docs/PROMPTS.md",
        "docs/DECISIONS.md",
    }
    assert all(path in permitted or path.startswith("results/fix4/") for path in changed)
    protected = (
        "src",
        "scripts",
        "corpus",
        "data",
        ".streamlit",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-enhanced.txt",
        "requirements-enhanced-lock.txt",
        "requirements-transformers.txt",
        "pyproject.toml",
        "streamlit_app.py",
    )
    trees = {path: git("rev-parse", f"HEAD:{path}") for path in protected}
    assert all(git("rev-parse", f"{BASE}:{path}") == blob for path, blob in trees.items())
    old = git("ls-files", "results").splitlines()
    hashes = {
        path: digest(ROOT / path) for path in old if not path.startswith("results/gate8-resume/")
    }
    reused = [
        "results/fix3-recheck/report.md",
        "results/fix3-recheck/scope.json",
        "results/fix3-recheck/regressions.json",
        "results/fix3-recheck/pipeline.json",
        "results/fix3-recheck/memory.json",
        "results/fix3-recheck/invariants.json",
        "results/gate8-recheck/offline.json",
        "results/gate8/provenance.json",
    ]
    save(
        "scope.json",
        {
            "verified_at_utc": datetime.now(UTC).isoformat(),
            "recorded_dev_sha": FIX,
            "initial_lane_b_sha": git("rev-parse", BASE),
            "initial_tree_clean": True,
            "merge_fast_forward": True,
            "head_equals_recorded_dev": True,
            "changed_since_fix3r": changed,
            "protected_git_objects": trees,
            "protected_objects_unchanged": True,
            "tokens_blob": git("rev-parse", "HEAD:src/huisclos/pseudonymize/tokens.py"),
            "reused_evidence_sha256": {path: hashes[path] for path in reused},
            "historical_artifacts_sha256": hashes,
            "passed": True,
        },
    )
    print("Scope verified; historical archives fingerprinted; no reserved corpus opened.")


def environment() -> None:
    """Vérifie versions et fichiers locaux contre les manifestes conservés de G8/A4."""
    os.environ.update(ENVIRONMENT)
    assets = Path(ENVIRONMENT["HUISCLOS_MODELS_DIR"])
    manifest = assets / "benchmarks/A4/retained-runtime-final.json"
    assert digest(manifest) == read("results/gate8/provenance.json")["runtime_manifest_sha256"]
    runtime = json.loads(manifest.read_text(encoding="utf-8"))
    expected = read("results/gate8/provenance.json")["current_versions"]
    versions = {name: importlib.metadata.version(name) for name in expected}
    assert versions == expected
    files = []
    for model, description in runtime["models"].items():
        for item in description["files"]:
            actual = digest(Path(description["local_path"]) / item["name"])
            assert actual == item["sha256"]
            files.append({"model": model, "file": item["name"], "sha256": actual})
    pip = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert pip.returncode == 0
    save(
        "environment.json",
        {
            "python": sys.executable,
            "python_version": platform.python_version(),
            "python_sha256": digest(Path(sys.executable)),
            "versions": versions,
            "environment": ENVIRONMENT,
            "machine": platform.platform(),
            "processor": platform.processor(),
            "logical_cpus": os.cpu_count(),
            "runtime_manifest_sha256": digest(manifest),
            "model_files": files,
            "pip_check": pip.stdout.strip(),
            "passed": True,
        },
    )
    print(f"Environment verified; {len(files)} local model files match A4.")


def checks(label: str, full: bool = True) -> None:
    """Lance les contrôles et garde des journaux UTF-8 sous un nom neuf."""
    os.environ.update(ENVIRONMENT)
    commands = {
        "ruff-check": [sys.executable, "-m", "ruff", "check", "."],
        "ruff-format": [sys.executable, "-m", "ruff", "format", "--check", "."],
        "style": [sys.executable, "scripts/check_style.py"],
        "diff": ["git", "diff", "--check"],
        "staged-diff": ["git", "diff", "--cached", "--check"],
    }
    if full:
        commands = {
            "pytest": [
                sys.executable,
                "results/fix3-recheck/guarded_pytest.py",
                "-q",
                "tests",
                "results/gate8-resume/test_recheck.py",
                "results/gate8-resume/test_launch_safety.py",
            ]
        } | commands
    results = {}
    for name, args in commands.items():
        environment = os.environ.copy()
        if name == "pytest":
            # Les tests du cache choisissent explicitement leur chemin. Seules les
            # sondes worker déclarent le paquet de modèles local dans leur propre portée.
            environment.pop("HUISCLOS_MODELS_DIR", None)
        completed = subprocess.run(
            args,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=environment,
        )
        with (OUT / f"{label}-{name}.log").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(completed.stdout + completed.stderr)
        results[name] = {"command": args, "exit_code": completed.returncode}
        print(f"{label} {name}: {completed.returncode}", flush=True)
    save(f"{label}-checks.json", results)
    assert all(result["exit_code"] == 0 for result in results.values())


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "scope":
        scope()
    elif action == "environment":
        environment()
    elif action == "checks":
        checks(sys.argv[2], "--static" not in sys.argv)
