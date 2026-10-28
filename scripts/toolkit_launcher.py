"""Installe puis lance HuisClos depuis le kit Windows ou macOS.

Entrées : dépendances épinglées et options de lancement de la ligne de commande.
Sorties : environnement isolé, diagnostic ou serveur Streamlit limité à la boucle locale.
Ce script de distribution ne reçoit aucun document et ne modifie pas le pipeline.
"""

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT = ROOT / ".venv-toolkit"
MARKER = ENVIRONMENT / "huisclos-install.json"
MODEL_CHOICES = ("standard", "enhanced-fr", "enhanced")
VERSION_CHECK = "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8"
HEALTH_CHECK = """
import importlib.metadata as metadata
import json
import sys

from packaging.requirements import Requirement

for line in open(sys.argv[1], encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    requirement = Requirement(line)
    version = metadata.version(requirement.name)
    if requirement.specifier and not requirement.specifier.contains(version):
        raise RuntimeError("Dependency version mismatch: " + requirement.name)
    if requirement.url and version != "3.8.0":
        raise RuntimeError("Model version mismatch: " + requirement.name)
if "--load" in sys.argv:
    import spacy
    import streamlit
    import presidio_analyzer
    import presidio_anonymizer
    import docx
    import pypdf
    import pandas
    import requests

    for name in ("fr_core_news_md", "en_core_web_sm"):
        spacy.load(name)
print(json.dumps({"python": sys.version.split()[0], "status": "ready"}))
"""


def environment_python(directory: Path | None = None) -> Path:
    """Renvoie le chemin de Python pour le dossier virtuel donné et le système courant."""
    return (directory or ENVIRONMENT) / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def runtime_environment() -> dict[str, str]:
    """Prépare un environnement sans télémétrie ni téléchargement de modèles à l'exécution."""
    values = os.environ.copy()
    values.update(
        PYTHONUTF8="1",
        PYTHONNOUSERSITE="1",
        STREAMLIT_BROWSER_GATHER_USAGE_STATS="false",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        DO_NOT_TRACK="1",
    )
    if saved_model_choice() in ("enhanced-fr", "enhanced"):
        values["HUISCLOS_MODELS_DIR"] = str(ENVIRONMENT / "model-assets")
    return values


def saved_model_choice() -> str | None:
    """Relit le choix local, ou renvoie None si aucune installation n'est confirmée."""
    try:
        choice = json.loads(
            (ENVIRONMENT / "huisclos-model-choice.json").read_text(encoding="utf-8")
        )["models"]
        return choice if choice in MODEL_CHOICES else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def choose_models(explicit: str | None) -> str:
    """Propose les renforts au premier lancement ; le défaut non interactif reste Standard."""
    if explicit is not None:
        return explicit
    previous = saved_model_choice()
    if previous is not None:
        return previous
    print("Choose which local models to install:")
    print("1. Standard FR/EN (default, smaller installation).")
    print("2. Standard + Enhanced French (CamemBERT, larger download).")
    print("3. Standard + Enhanced French/English (CamemBERT + GLiNER, several GB).")
    print("English is experimental. English Enhanced is not recommended.")
    if not sys.stdin.isatty():
        print(
            "Non-interactive installation: Standard. "
            "Use --models enhanced-fr or enhanced to change."
        )
        return "standard"
    while True:
        answer = input("Your choice [1/2/3, Enter = 1]: ").strip() or "1"
        if answer in {"1", "2", "3"}:
            return MODEL_CHOICES[int(answer) - 1]
        print("Enter 1, 2 or 3.")


def prepare_models(choice: str, repair: bool = False, check_only: bool = False) -> None:
    """Prépare les modèles facultatifs, puis confirme le choix uniquement après succès."""
    if choice == "standard":
        if not check_only:
            (ENVIRONMENT / "huisclos-model-choice.json").write_text(
                json.dumps({"models": choice}) + "\n", encoding="utf-8"
            )
        return
    command = [
        str(environment_python()),
        "scripts/toolkit_enhanced.py",
        "--models",
        choice,
    ]
    if repair:
        command.append("--repair")
    if check_only:
        command.append("--check")
    run(command)


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """Exécute une commande du kit à sa racine, avec sortie visible sauf diagnostic."""
    return subprocess.run(
        command,
        cwd=ROOT,
        env=runtime_environment(),
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=capture,
    )


def installation_identity() -> dict[str, str]:
    """Identifie les dépendances et la révision du protocole d'installation du kit."""
    return {
        "requirements_sha256": hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest(),
        "installer": "1",
    }


def installation_current() -> bool:
    """Vérifie le reçu et les versions installées sans installer ni utiliser le réseau."""
    try:
        if json.loads(MARKER.read_text(encoding="utf-8")) != installation_identity():
            return False
        run([str(environment_python()), "-c", VERSION_CHECK], capture=True)
        run(
            [str(environment_python()), "-c", HEALTH_CHECK, str(ROOT / "requirements.txt")],
            capture=True,
        )
        return True
    except (OSError, ValueError, subprocess.CalledProcessError):
        return False


def verify_installation() -> None:
    """Contrôle hors ligne les dépendances et le chargement réel des deux modèles spaCy."""
    executable = str(environment_python())
    run([executable, "-c", VERSION_CHECK])
    run([executable, "-m", "pip", "check"])
    run([executable, "-c", HEALTH_CHECK, str(ROOT / "requirements.txt"), "--load"])


def prepare_installation(repair: bool = False) -> None:
    """Crée le venv et installe les dépendances seulement si nécessaire ou réparation explicite."""
    if not repair and installation_current():
        print("HuisClos is installed. Starting locally; no dependency download.", flush=True)
        return
    if ENVIRONMENT.exists():
        if not environment_python().is_file():
            raise RuntimeError(
                "Incomplete .venv-toolkit. Rename that folder and start again; see START_HERE.md."
            )
        try:
            run([str(environment_python()), "-c", VERSION_CHECK], capture=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                "The toolkit environment needs Python 3.12 64-bit. Rename .venv-toolkit and retry."
            ) from error
    else:
        print("Creating the private Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(ENVIRONMENT)
    MARKER.unlink(missing_ok=True)
    print("Installing dependencies and French/English models. Internet is needed now.", flush=True)
    executable = str(environment_python())
    run([executable, "-m", "ensurepip", "--upgrade"])
    run(
        [
            executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            "requirements.txt",
        ]
    )
    verify_installation()
    MARKER.write_text(json.dumps(installation_identity(), indent=2) + "\n", encoding="utf-8")


def streamlit_command(port: int) -> list[str]:
    """Construit la commande du serveur local, avec ouverture du navigateur et port donné."""
    return [
        str(environment_python()),
        "-m",
        "streamlit",
        "run",
        "streamlit_app.py",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--browser.serverAddress=127.0.0.1",
        "--server.headless=false",
        "--server.showEmailPrompt=false",
        "--browser.gatherUsageStats=false",
    ]


def main(argv: list[str] | None = None) -> int:
    """Traite les options ; renvoie zéro après succès ou arrêt volontaire, un après erreur."""
    parser = argparse.ArgumentParser(description="Install and launch the local HuisClos toolkit.")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--check", action="store_true", help="Check offline; never install or launch."
    )
    actions.add_argument("--install-only", action="store_true", help="Install without launching.")
    actions.add_argument(
        "--repair", action="store_true", help="Run pip installation again, then launch."
    )
    parser.add_argument("--port", type=int, default=8501, help="Local port (default: 8501).")
    parser.add_argument(
        "--models", choices=MODEL_CHOICES, help="Choose or change the installed models."
    )
    arguments = parser.parse_args(argv)
    if not 1 <= arguments.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if sys.version_info[:2] != (3, 12) or struct.calcsize("P") != 8:
        print("Install Python 3.12 64-bit, then reopen the launcher. See START_HERE.md.")
        return 1
    try:
        if arguments.check:
            verify_installation()
            prepare_models(arguments.models or saved_model_choice() or "standard", check_only=True)
            return 0
        choice = choose_models(arguments.models)
        prepare_installation(arguments.repair)
        prepare_models(choice, repair=arguments.repair)
        if not arguments.install_only:
            print(f"Opening http://127.0.0.1:{arguments.port} - keep this window open.", flush=True)
            print("Press Ctrl+C here to stop HuisClos.", flush=True)
            run(streamlit_command(arguments.port))
        return 0
    except KeyboardInterrupt:
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Installation or launch failed ({type(error).__name__}). See the output above.")
        if isinstance(error, RuntimeError):
            print(str(error))
        print("Check Python 3.12, your connection during installation and START_HERE.md.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
