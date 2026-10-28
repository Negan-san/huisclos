"""Prépare les renforts facultatifs choisis pendant l'installation du kit.

Entrées : choix FR ou FR/EN, dépendances et révisions déjà fixées par A4.
Sortie : poids vérifiés et chargés hors ligne avant de confirmer l'installation.
Les téléchargements restent limités à cette action explicite de préparation.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / ".venv-toolkit" / "model-assets"
CHOICE = ROOT / ".venv-toolkit" / "huisclos-model-choice.json"
MODELS = {
    "enhanced-fr": ["camembert_ner"],
    "enhanced": ["camembert_ner", "gliner_multi_pii_v1", "mdeberta_v3_base"],
}


def torch_command() -> list[str]:
    """Choisit PyTorch CPU Windows ou le paquet natif macOS, sans verrou Windows sur Mac."""
    command = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check"]
    if sys.platform == "darwin":
        return [*command, "torch==2.14.1"]
    return [
        *command,
        "torch==2.14.1+cpu",
        "--index-url",
        "https://download.pytorch.org/whl/cpu",
    ]


def run(command: list[str]) -> None:
    """Lance une étape de préparation visible et interrompt la suite en cas d'erreur."""
    subprocess.run(command, cwd=ROOT, check=True)


def verify_models(choice: str) -> None:
    """Vérifie le manifeste téléchargé puis teste les vrais backends de l'application hors ligne."""
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    if any(manifest["models"][name]["status"] != "available" for name in MODELS[choice]):
        raise RuntimeError(
            "An Enhanced model could not be downloaded or verified; retry installation."
        )
    # La sonde du vrai pipeline vérifie aussi les versions, offsets et fichiers auxiliaires.
    probe = """
import os
import socket
import sys
sys.path.insert(0, 'src')
os.environ['HUISCLOS_MODELS_DIR'] = sys.argv[1]
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
def refuse(*args, **kwargs):
    raise OSError('Network forbidden during model verification')
socket.socket.connect = refuse
socket.create_connection = refuse
from huisclos.config import profile_config
from huisclos.detection.pipeline import detect
samples = {'fr': 'Mme Alice Martin signe.', 'en': 'Ms Alice Martin signs.'}
for language in sys.argv[2:]:
    detect(samples[language], profile_config('enhanced', language))
print('Enhanced models verified offline.')
"""
    languages = ["fr", "en"] if choice == "enhanced" else ["fr"]
    run([sys.executable, "-c", probe, str(ASSETS), *languages])


def prepare(choice: str, repair: bool = False, check_only: bool = False) -> None:
    """Installe les paquets et poids choisis, ou contrôle seulement les fichiers existants."""
    if check_only:
        verify_models(choice)
        return
    if not repair and CHOICE.is_file():
        previous = json.loads(CHOICE.read_text(encoding="utf-8"))
        if previous.get("models") == choice:
            if not (ASSETS / "manifest.json").is_file():
                raise RuntimeError("Enhanced model files are missing. Start again with --repair.")
            return
    print("Installing optional Enhanced packages and model weights. This can take several minutes.")
    run(torch_command())
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            "requirements-toolkit-enhanced.txt",
        ]
    )
    ASSETS.mkdir(parents=True, exist_ok=True)
    run(
        [
            sys.executable,
            "scripts/prepare_local_models.py",
            "fetch",
            "--assets",
            str(ASSETS),
            "--models",
            *MODELS[choice],
        ]
    )
    run([sys.executable, "-m", "pip", "check"])
    verify_models(choice)
    CHOICE.write_text(json.dumps({"models": choice}) + "\n", encoding="utf-8")


def main() -> None:
    """Prépare le profil demandé et renvoie un échec clair sans lancer l'application."""
    parser = argparse.ArgumentParser(description="Prepare optional local Enhanced models.")
    parser.add_argument("--models", choices=MODELS, required=True)
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    os.environ["PYTHONUTF8"] = "1"
    prepare(arguments.models, arguments.repair, arguments.check)


if __name__ == "__main__":
    main()
