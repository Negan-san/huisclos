"""Pilote de robustesse : mesure la protection effective d'un corpus fictif, profil par profil.

Entrées : corpus JSONL, identifiant du jeu, plan figé (langue du document, profils, seuils,
comparaisons) et dossier de sortie, tous obligatoires ; mode dev par défaut.
Sorties : robustness.json et robustness.md ; expositions détaillées en mode dev seulement.
Place dans le pipeline : mesure hors interface, une détection par document et par profil ; un
profil de référence (commit G7) tourne dans un processus séparé avec son propre code.
"""

import argparse
import json
import os
import platform
import re
import subprocess
import sys
from dataclasses import asdict, fields, replace
from datetime import UTC, datetime
from enum import Enum
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# Seule la bibliothèque standard est importée ici : le processus séparé d'un profil importe
# ensuite huisclos depuis le commit mesuré, qui ne connaît pas les modules de mesure récents.
ROOT = Path(__file__).resolve().parents[1]
MODES = ("dev", "gate")
DATASET_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
OFFLINE = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
PACKAGES = "spacy presidio-analyzer presidio-anonymizer transformers torch huggingface-hub"
REPORT_NAME = "robustness.json"


class PlanError(ValueError):
    """Refus d'une demande de mesure : préréglage inconnu ou langue non prise en charge."""


def package_version(name: str) -> str | None:
    """Renvoie la version installée du paquet, ou None s'il est absent."""
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def git_output(folder: Path, *arguments: str) -> str | None:
    """Renvoie la sortie d'une commande git lancée dans folder, ou None en cas d'échec."""
    options = {"cwd": folder, "capture_output": True, "text": True, "encoding": "utf-8"}
    try:
        return subprocess.run(["git", *arguments], check=True, **options).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def plain(value: Any) -> Any:
    """Rend une valeur de configuration lisible en JSON : énumérations, ensembles triés."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, set | frozenset):
        return sorted((plain(item) for item in value), key=str)
    if isinstance(value, list | tuple):
        return [plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    return value if value is None or isinstance(value, str | int | float | bool) else str(value)


def configured(config: Any, threshold: float, language: str) -> tuple[Any, bool]:
    """Fixe le seuil et la langue du document ; refuse l'anglais si la configuration l'ignore.

    Avant A2, DetectionConfig n'a pas de champ document_language et le moteur ne traite que
    le français : simuler l'anglais avec ce moteur fausserait la mesure. Renvoie la
    configuration et un booléen qui dit si le champ de langue existe.
    """
    if "document_language" in {item.name for item in fields(config)}:
        return replace(config, threshold=threshold, document_language=language), True
    if language != "fr":
        raise PlanError(
            "English documents are not supported by the measured code: DetectionConfig has "
            "no document_language field."
        )
    return replace(config, threshold=threshold), False


def cached_revision(model_name: str) -> str | None:
    """Renvoie la révision locale (refs/main) d'un modèle Hugging Face, lue sans réseau."""
    try:
        from huggingface_hub.constants import HF_HUB_CACHE
    except ImportError:
        return None
    path = Path(HF_HUB_CACHE) / f"models--{model_name.replace('/', '--')}" / "refs" / "main"
    return path.read_text(encoding="utf-8").strip() if path.is_file() else None


def model_identity(config: Any) -> dict[str, Any]:
    """Nomme les modèles réellement utilisés : version du modèle spaCy, révision de CamemBERT."""
    name = getattr(config, "spacy_model", None)
    identity: dict[str, Any] = {
        "spacy": {"name": name, "version": package_version(name) if name else None}
    }
    if getattr(config, "use_camembert", False):
        try:
            from huisclos.detection.camembert import MODEL_NAME as camembert
        except ImportError:
            camembert = None
        revision = cached_revision(camembert) if camembert else None
        identity["camembert"] = {"name": camembert, "revision": revision}
    return identity


def measured_metadata(config: Any, language_field: bool, lowered: Any) -> dict[str, Any]:
    """Décrit le code réellement mesuré : commit, propreté, configuration, versions, modèles."""
    import huisclos

    source = Path(huisclos.__file__).resolve().parents[2]
    status = git_output(source, "status", "--porcelain")
    return {
        "source": str(source),
        "git_commit": git_output(source, "rev-parse", "HEAD"),
        "git_clean": None if status is None else status == "",
        "python": platform.python_version(),
        "configuration": plain(asdict(config)),
        "document_language_field": language_field,
        "final_check_threshold": None if lowered is None else lowered.threshold,
        "versions": {name: package_version(name) for name in PACKAGES.split()},
        "models": model_identity(config),
    }


def load_api() -> SimpleNamespace:
    """Importe les fonctions du code mesuré ; le contrôle final manque dans un code ancien."""
    from huisclos.config import PRESETS
    from huisclos.detection.pipeline import detect
    from huisclos.pseudonymize.tokens import pseudonymize

    try:
        from huisclos.pseudonymize.final_check import check_threshold, final_check
    except ImportError:
        check_threshold = final_check = None
    return SimpleNamespace(
        presets=PRESETS,
        detect=detect,
        pseudonymize=pseudonymize,
        check_threshold=check_threshold,
        final_check=final_check,
    )


def stage_outputs(
    texts: list[str], preset: str, threshold: float, language: str, api: Any = None
) -> dict[str, Any]:
    """Exécute les trois stades sur chaque texte, avec une seule détection par texte.

    Toutes les propositions sont pseudonymisées automatiquement ; aucune revue humaine n'est
    simulée. Le contrôle final relit le texte produit au seuil abaissé, comme l'interface.
    La réponse ne contient que des positions et des types : détections, jetons du texte
    produit (début, fin, longueur d'origine) et alertes, placées dans le texte produit.
    """
    api = api or load_api()
    if preset not in api.presets:
        raise PlanError(f"Unknown preset in the measured code: {preset}.")
    config, language_field = configured(api.presets[preset], threshold, language)
    lowered = None
    if api.final_check is not None:
        lowered = replace(config, threshold=api.check_threshold(config.threshold))
    documents = []
    for text in texts:
        detected = list(api.detect(text, config))
        result = api.pseudonymize(text, detected)
        alerts = None
        if lowered is not None:
            found = api.final_check(result, lambda value: api.detect(value, lowered))
            alerts = [[item.start, item.end] for item in found]
        documents.append(
            {
                "detections": [
                    [item.start, item.end, item.entity_type.value, item.score, item.source.value]
                    for item in detected
                ],
                "occurrences": [[o.start, o.end, len(o.original)] for o in result.occurrences],
                "alerts": alerts,
            }
        )
    return {"documents": documents, "metadata": measured_metadata(config, language_field, lowered)}


def worker(checkout: Path) -> None:
    """Point d'entrée du processus séparé : demande sur l'entrée standard, réponse JSON.

    Le code mesuré est importé depuis checkout/src. La sortie standard réelle est réservée
    à la réponse ; les messages éventuels des bibliothèques partent sur la sortie d'erreur.
    """
    os.environ.update(OFFLINE)
    source = (checkout / "src").resolve()
    sys.path.insert(0, str(source))
    import huisclos

    if not Path(huisclos.__file__).resolve().is_relative_to(source):
        raise SystemExit("The measured package was not imported from the requested checkout.")
    request = json.loads(sys.stdin.read())
    answer, sys.stdout = sys.stdout, sys.stderr
    try:
        payload = stage_outputs(
            request["texts"], request["preset"], request["threshold"], request["language"]
        )
    except PlanError as error:
        payload = {"error": str(error)}
    answer.write(json.dumps(payload) + "\n")
    answer.flush()


def run_separate(
    profile: dict[str, Any], texts: list[str], language: str, mode: str
) -> dict[str, Any]:
    """Mesure un profil dans un processus séparé, avec son propre code et son interpréteur.

    Les textes passent par un tube, jamais par un fichier. En mode gate, la sortie d'erreur
    du processus n'est pas recopiée : elle pourrait contenir un extrait de document.
    """
    script = str(Path(__file__).resolve())
    checkout = str(Path(profile.get("checkout", ROOT)).resolve())
    command = [profile.get("python", sys.executable), "-I", "-X", "utf8", script, "--worker"]
    command.append(checkout)
    request = {"texts": texts, "preset": profile["preset"], "language": language}
    request["threshold"] = float(profile["threshold"])
    completed = subprocess.run(
        command,
        input=json.dumps(request),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ | OFFLINE,
        check=False,
    )
    if completed.returncode != 0:
        detail = "" if mode == "gate" else "\n" + completed.stderr[-3000:]
        raise RuntimeError(
            f"Separate profile process failed (code {completed.returncode}).{detail}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Separate profile process returned no answer.")
    payload = json.loads(lines[-1])
    if "error" in payload:
        raise PlanError(payload["error"])
    return payload


def run_metadata(
    options: argparse.Namespace, plan: dict[str, Any], documents: list[Any], runs: list[Any]
) -> dict[str, Any]:
    """Décrit la mesure : jeu, mode, langue, plan, corpus, commit et profils mesurés."""
    from huisclos.evaluation.coverage import SCOPES
    from huisclos.evaluation.reports import file_sha256, git_commit

    profiles = {run.name: {"preset": plan["profiles"][run.name]["preset"]} for run in runs}
    return {
        "date": datetime.now(UTC).isoformat(),
        "dataset_id": options.dataset_id,
        "mode": options.mode,
        "document_language": plan["document_language"],
        "split": documents[0].split,
        "document_count": len(documents),
        "git_commit": git_commit(ROOT),
        "corpus_sha256": {options.corpus.name: file_sha256(options.corpus)},
        "plan_sha256": file_sha256(options.plan),
        "plan": plan,
        "stages": {
            "detection": "proposals of detect(), one call per document and profile",
            "pseudonymization": "automatic substitution of every proposal, no human review",
            "final_check": "alerts on the pseudonymized text; an alert masks nothing",
        },
        "scopes": {name: sorted(types) for name, types in SCOPES.items()},
        "profiles": {run.name: profiles[run.name] | run.metadata for run in runs},
    }


def measure(options: argparse.Namespace, api: Any = None) -> dict[str, Any]:
    """Exécute la mesure et écrit le rapport ; les refus ont lieu avant toute détection.

    En mode gate, chaque profil tourne dans un processus séparé ; en dev, seuls les profils
    qui nomment un autre checkout ou interpréteur le font. api remplace le moteur en test.
    """
    from huisclos.evaluation.coverage_reports import (
        build_report,
        exposure_details,
        profile_run,
        write_report,
    )
    from huisclos.evaluation.run import load_plan, load_unreserved

    if not DATASET_ID.fullmatch(options.dataset_id):
        raise PlanError("dataset-id: 1 to 64 letters, digits, dots, hyphens or underscores.")
    if (options.out / REPORT_NAME).exists():
        raise PlanError("The output folder already holds a robustness report; use a new one.")
    plan = load_plan(options.plan)
    documents = load_unreserved(options.corpus, options.mode)
    texts, language = [document.text for document in documents], plan["document_language"]
    runs = []
    for name, profile in plan["profiles"].items():
        threshold = float(profile["threshold"])
        if options.mode == "gate" or {"checkout", "python"} & profile.keys():
            payload = run_separate(profile, texts, language, options.mode)
        else:
            payload = stage_outputs(texts, profile["preset"], threshold, language, api)
        runs.append(profile_run(name, threshold, documents, payload))
    metadata = run_metadata(options, plan, documents, runs)
    report = build_report(documents, runs, plan["comparisons"], metadata)
    details = exposure_details(documents, runs) if options.mode == "dev" else None
    write_report(options.out, report, details)
    return report


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    """Lit les options ; corpus, identifiant du jeu, plan et dossier de sortie sont exigés."""
    parser = argparse.ArgumentParser(
        description="Measure full coverage on a fictional corpus, profile by profile.",
        epilog="Dev mode refuses reserved corpora (test, challenge, blind_post_g7). Gate mode "
        "is for authorised gates only and writes aggregates without document content.",
    )
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mode", choices=MODES, default="dev")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None, api: Any = None) -> int:
    """Lance le pilote, ou le processus séparé d'un profil avec --worker ; renvoie le code."""
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) == 2 and arguments[0] == "--worker":
        worker(Path(arguments[1]))
        return 0
    options = parse_arguments(arguments)
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))
    os.environ.update(OFFLINE)
    try:
        report = measure(options, api)
    except (RuntimeError, ValueError, OSError) as error:
        print(f"Robustness measurement refused or failed: {error}", file=sys.stderr)
        return 2
    count = report["metadata"]["document_count"]
    print(f"Robustness report written to {options.out} ({count} documents).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
