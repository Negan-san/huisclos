"""Construit une archive partageable depuis les seuls fichiers Git autorisés.

Entrée : commit du dépôt ; aucun environnement, secret ni document de travail local.
Sorties : ZIP avec sources, lanceurs et manifeste de provenance, puis empreinte SHA-256.
Le constructeur ne lit aucun corpus réservé et n'installe aucune dépendance.
"""

import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORIES = ("app", "src", "scripts", "tests", "docs")
FILES = (
    "streamlit_app.py",
    "README.md",
    "START_HERE.md",
    "LICENSE",
    "AGENTS.md",
    "CLAUDE.md",
    "pyproject.toml",
    ".gitignore",
    ".streamlit/config.toml",
    "Start-HuisClos-Windows.bat",
    "Start-HuisClos-macOS.command",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-transformers.txt",
    "requirements-enhanced.txt",
    "requirements-enhanced-lock.txt",
    "requirements-toolkit-enhanced.txt",
    "data/exclusions_fr.txt",
    "data/exclusions_en.txt",
    "data/samples/demo_case_fr.txt",
    "results/threshold.json",
    "results/results.json",
    "results/threshold_sweep.csv",
    "results/metrics_by_type.csv",
    "results/summary.md",
    "results/challenge_comparison.json",
    "results/challenge_comparison.md",
    "results/gate8/report.md",
    "results/gate8-resume/report.md",
)
REQUIRED = frozenset(
    {
        "streamlit_app.py",
        "requirements.txt",
        "START_HERE.md",
        "Start-HuisClos-Windows.bat",
        "Start-HuisClos-macOS.command",
        "scripts/toolkit_launcher.py",
        ".streamlit/config.toml",
        "data/exclusions_fr.txt",
        "data/exclusions_en.txt",
        "data/samples/demo_case_fr.txt",
        "results/threshold.json",
    }
)


def allowed_path(name: str) -> bool:
    """Accepte uniquement les sources et ressources publiques, même si un secret était suivi."""
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        return False
    if any(
        part.startswith(".env")
        or part in {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "secrets.toml"}
        or part.startswith(".venv")
        for part in path.parts
    ):
        return False
    if name.endswith((".mapping.json", ".pyc", ".pyo")):
        return False
    return name in FILES or (len(path.parts) > 1 and path.parts[0] in SOURCE_DIRECTORIES)


def git_bytes(root: Path, *arguments: str) -> bytes:
    """Renvoie la sortie binaire de Git dans le dépôt donné, sans invoquer un shell."""
    return subprocess.run(
        ["git", "-C", str(root), *arguments], capture_output=True, check=True
    ).stdout


def source_files(root: Path, revision: str) -> dict[str, bytes]:
    """Lit seulement les chemins autorisés du commit ; refuse les liens et archives incomplètes."""
    names = git_bytes(root, "ls-tree", "-r", "--name-only", revision).decode("utf-8").splitlines()
    selected = sorted(name for name in names if allowed_path(name))
    missing = REQUIRED.difference(selected)
    if missing:
        raise ValueError("Toolkit files missing from commit: " + ", ".join(sorted(missing)))
    archive = git_bytes(
        root,
        "-c",
        "core.autocrlf=false",
        "-c",
        "core.eol=lf",
        "archive",
        "--format=tar",
        revision,
        "--",
        *selected,
    )
    payload = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as source:
        for member in source:
            if member.isdir():
                continue
            if not member.isfile() or member.name not in selected:
                raise ValueError("Non-regular or unexpected toolkit file")
            file = source.extractfile(member)
            if file is None:
                raise ValueError("Unreadable archive member")
            payload[member.name] = file.read()
    if set(payload) != set(selected):
        raise ValueError("Incomplete source archive")
    return payload


def build_toolkit(root: Path, destination: Path) -> Path:
    """Produit le ZIP du commit HEAD et son empreinte ; renvoie le chemin absolu du ZIP."""
    revision = git_bytes(root, "rev-parse", "HEAD").decode("ascii").strip()
    payload = source_files(root, revision)
    for name, content in payload.items():
        if name.endswith(".bat"):
            payload[name] = content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        elif name.endswith(".command"):
            payload[name] = content.replace(b"\r\n", b"\n")
    manifest = {
        "source_commit": revision,
        "python": "3.12 (64-bit)",
        "profile": "Standard FR/EN; English experimental",
        "omitted": ["corpora", "git history", "environments", "secrets", "neural model weights"],
        "files_sha256": {
            name: hashlib.sha256(content).hexdigest() for name, content in sorted(payload.items())
        },
    }
    payload["TOOLKIT_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    destination.mkdir(parents=True, exist_ok=True)
    output = destination.resolve() / f"HuisClos-Toolkit-{revision[:8]}.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for name, content in sorted(payload.items()):
            info = zipfile.ZipInfo(f"HuisClos-Toolkit/{name}", date_time=(2026, 10, 28, 0, 0, 0))
            info.create_system = 3
            mode = 0o755 if name.endswith(".command") else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, content)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{checksum}  {output.name}\n", encoding="utf-8")
    return output


def main() -> None:
    """Construit le kit du dépôt courant et affiche le fichier à partager."""
    parser = argparse.ArgumentParser(description="Build the toolkit from committed sources only.")
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    arguments = parser.parse_args()
    print(build_toolkit(ROOT, arguments.out))


if __name__ == "__main__":
    main()
