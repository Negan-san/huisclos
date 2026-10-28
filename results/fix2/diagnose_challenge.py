"""Diagnostic FIX2 : situe l'échec challenge G8 sans exporter le moindre contenu.

Entrées : code métier figé de G8R, plan historique G8, corpus challenge (par script seulement).
Sorties : pour chaque profil, les lieux d'échec distincts (stade, classe d'erreur, fichier du
dépôt, fonction, ligne) et l'état de la construction du rapport, sans métrique ni texte.
Un enregistrement précède l'unique essai ; un reçu d'essai interdit toute relance.
"""

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import traceback
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from scripts import evaluate_robustness as pilot  # noqa: E402
from scripts import gate8_measure  # noqa: E402

REFERENCE_SHA = "84bb7f0a5faaaf494a170c385c3c677777a4c41d"
CORPUS = ROOT / "corpus/challenge.jsonl"
PLAN = ROOT / "results/gate8/plan_historical_fr.json"
EXPECTED = {
    "corpus": "c47502d65bf05b6f3e0bd7e0bf9ccd9e58b046787fa2252e6a49ece85a03d609",
    "plan": "747c37211f92a02d4eef473e1019b894a88c5d83fff163acebe4975501394da2",
}
BUSINESS_PATHS = ("src", "app", "data", ".streamlit", "streamlit_app.py", "requirements.txt")
HARNESS = (
    "results/fix2/diagnose_challenge.py",
    "scripts/gate8_measure.py",
    "scripts/evaluate_robustness.py",
)
STAGES = ("load", "detection", "pseudonymization", "final_check", "metadata", "report", "worker")
CODE_PATH = re.compile(r"(?:src|scripts|results/fix2)/[A-Za-z0-9_/]{1,120}\.py")
IDENTIFIER = re.compile(r"<module>|[A-Za-z_][A-Za-z0-9_]{0,63}")
ENVIRONMENT = {
    "PYTHONUTF8": "1",
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "OMP_NUM_THREADS": "2",
    "MKL_NUM_THREADS": "2",
    "TOKENIZERS_PARALLELISM": "false",
}


def digest(path: Path) -> str:
    """Hache un fichier sans afficher son contenu."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any) -> None:
    """Crée un artefact neuf ; un fichier existant n'est jamais remplacé."""
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def block_network() -> None:
    """Refuse connexions, DNS et datagrammes dans le processus courant."""
    for owner, name in (
        (socket, "getaddrinfo"),
        (socket, "create_connection"),
        (socket.socket, "connect"),
        (socket.socket, "connect_ex"),
        (socket.socket, "sendto"),
    ):
        setattr(owner, name, gate8_measure.refuse_network)


def site(stage: str, error: BaseException) -> dict[str, Any]:
    """Lieu validé d'une erreur : stade, classe, dernier cadre du dépôt, jamais le message.

    Un cadre hors du dépôt (bibliothèque) n'est pas cité ; un nom non conforme est remplacé
    par "unvalidated", pour qu'aucune chaîne libre ne quitte le processus.
    """
    frames = [
        frame
        for frame in traceback.extract_tb(error.__traceback__)
        if Path(frame.filename).resolve().is_relative_to(ROOT)
    ]
    path, function, line = "unvalidated", "unvalidated", None
    if frames:
        relative = Path(frames[-1].filename).resolve().relative_to(ROOT).as_posix()
        if CODE_PATH.fullmatch(relative) and IDENTIFIER.fullmatch(frames[-1].name):
            path, function, line = relative, frames[-1].name, int(frames[-1].lineno or 0)
    name = type(error).__name__
    return {
        "stage": stage,
        "error_type": name if gate8_measure.ERROR_TYPE.fullmatch(name) else "unvalidated",
        "path": path,
        "function": function,
        "line": line,
    }


def valid_site(value: Any) -> bool:
    """Vérifie qu'un lieu relu d'un worker ne contient que des champs attendus et conformes."""
    keys = {"stage", "error_type", "path", "function", "line"}
    if not isinstance(value, dict) or set(value) != keys:
        return False
    checks = (
        value["stage"] in STAGES,
        value["error_type"] == "unvalidated"
        or bool(gate8_measure.ERROR_TYPE.fullmatch(str(value["error_type"]))),
        value["path"] == "unvalidated" or bool(CODE_PATH.fullmatch(str(value["path"]))),
        value["function"] == "unvalidated" or bool(IDENTIFIER.fullmatch(str(value["function"]))),
        value["line"] is None or (type(value["line"]) is int and value["line"] >= 0),
    )
    return all(checks)


def profile_sequence(texts: list[str], preset: str, threshold: float) -> dict[str, Any]:
    """Rejoue les stades G8 d'un profil ; garde chaque lieu d'échec distinct et continue.

    Un document en échec n'empêche pas les suivants d'être essayés. Les prédictions ne sont
    rendues que si tous les documents ont franchi détection et substitution.
    """
    sites: list[dict[str, Any]] = []
    try:
        api = pilot.load_api()
        config, _ = pilot.configured(api.presets[preset], threshold, "fr")
        from huisclos.detection import pipeline

        pipeline.analyzer_for(config)
        if config.use_camembert:
            from huisclos.detection.camembert import load_pipeline

            load_pipeline()
        lowered = replace(config, threshold=api.check_threshold(threshold))
    except Exception as error:
        return {"sites": [site("load", error)], "documents": None}
    documents: list[dict[str, Any]] | None = []
    check_failed = False
    for text in texts:
        stage = "detection"
        try:
            detected = list(api.detect(text, config))
            stage = "pseudonymization"
            result = api.pseudonymize(text, detected)
        except Exception as error:
            sites.append(site(stage, error))
            documents = None
            continue
        alerts = None
        try:
            alerts = gate8_measure.final_alerts(api, result, text, lowered)
        except Exception as error:
            sites.append(site("final_check", error))
            check_failed = True
        if documents is not None:
            documents.append(
                {
                    "detections": [
                        [d.start, d.end, d.entity_type.value, d.score, d.source.value]
                        for d in detected
                    ],
                    "occurrences": [[o.start, o.end, len(o.original)] for o in result.occurrences],
                    "alerts": alerts,
                }
            )
    if documents is not None and check_failed:
        for document in documents:
            document["alerts"] = None
    try:
        pilot.measured_metadata(config, True, lowered)
    except Exception as error:
        sites.append(site("metadata", error))
    unique = [dict(item) for item in {json.dumps(s, sort_keys=True): s for s in sites}.values()]
    return {"sites": unique, "documents": documents}


def worker() -> int:
    """Processus isolé d'un profil : réseau refusé, demande sur l'entrée, réponse sur le tube."""
    block_network()
    request = json.loads(sys.stdin.read())
    answer, sys.stdout = sys.stdout, sys.stderr
    payload = profile_sequence(request["texts"], request["preset"], request["threshold"])
    answer.write(json.dumps(payload) + "\n")
    answer.flush()
    return 0


def run_profile(profile: dict[str, Any], texts: list[str]) -> dict[str, Any]:
    """Lance le worker ; sa sortie d'erreur est jetée, sa réponse est revalidée champ par champ."""
    completed = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
        input=json.dumps(
            {"texts": texts, "preset": profile["preset"], "threshold": profile["threshold"]}
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ | ENVIRONMENT,
        check=False,
    )
    failure = {"stage": "worker", "error_type": "unvalidated", "path": "unvalidated"}
    failure |= {"function": "unvalidated", "line": None}
    try:
        payload = json.loads([line for line in completed.stdout.splitlines() if line.strip()][-1])
        sites, documents = payload["sites"], payload["documents"]
    except (IndexError, KeyError, TypeError, ValueError):
        return {"exit_code": completed.returncode, "sites": [failure], "documents": None}
    if not isinstance(sites, list) or not all(valid_site(item) for item in sites):
        return {"exit_code": completed.returncode, "sites": [failure], "documents": None}
    return {"exit_code": completed.returncode, "sites": sites, "documents": documents}


def report_stage(
    name: str, profile: dict[str, Any], documents: list[Any], answer: dict[str, Any]
) -> dict[str, Any] | str:
    """Construit en mémoire le rapport G8 du profil, puis l'oublie ; renvoie "ok" ou le lieu."""
    from huisclos.evaluation.coverage_reports import build_report, profile_run

    if answer["documents"] is None:
        return "not_reached"
    try:
        run = profile_run(
            name,
            float(profile["threshold"]),
            documents,
            {"documents": answer["documents"], "metadata": {}},
        )
        build_report(documents, [run], [], {})
    except Exception as error:
        return site("report", error)
    return "ok"


def diagnose(corpus: Path, plan_path: Path, mode: str) -> dict[str, Any]:
    """Diagnostique chaque profil du plan sur corpus ; aucune métrique n'est conservée."""
    from huisclos.evaluation.run import load_plan, load_unreserved

    block_network()
    plan = load_plan(plan_path)
    documents = load_unreserved(corpus, mode)
    texts = [document.text for document in documents]
    profiles = {}
    for name, profile in plan["profiles"].items():
        answer = run_profile(profile, texts)
        profiles[name] = {
            "preset": profile["preset"],
            "worker_exit_code": answer["exit_code"],
            "all_documents_through_pseudonymization": answer["documents"] is not None,
            "failure_sites": answer["sites"],
            "report_construction": report_stage(name, profile, documents, answer),
        }
    return {"profiles": profiles}


def register() -> None:
    """Enregistre la référence, les empreintes et les paramètres avant l'unique essai."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    same = subprocess.run(
        ["git", "diff", "--quiet", REFERENCE_SHA, "--", *BUSINESS_PATHS], cwd=ROOT, check=False
    )
    assert same.returncode == 0, "Business code differs from G8R"
    assert digest(CORPUS) == EXPECTED["corpus"] and digest(PLAN) == EXPECTED["plan"]
    save(
        OUT / "diagnostic_registration.json",
        {
            "registered_at_utc": datetime.now(UTC).isoformat(),
            "reference_sha": REFERENCE_SHA,
            "head_at_registration": head.stdout.strip(),
            "business_paths_identical_to_reference": list(BUSINESS_PATHS),
            "harness_sha256": {path: digest(ROOT / path) for path in HARNESS},
            "corpus": {"path": "corpus/challenge.jsonl", "sha256": EXPECTED["corpus"]},
            "plan": {"path": "results/gate8/plan_historical_fr.json", "sha256": EXPECTED["plan"]},
            "parameters": {"threshold": 0.3, "final_check": 0.1, "environment": ENVIRONMENT},
            "attempt": {
                "historical_challenge_execution_in_project": 3,
                "predecessors": ["G7 (complete)", "G8 (failed, exit 2)"],
                "nature": "diagnostic reuse of a known corpus, not a fresh blind validation",
                "repeat_forbidden": True,
            },
            "export_allowed": ["stage", "error_type", "path", "function", "line"],
        },
    )
    print("FIX2 diagnostic registered; one attempt may begin.")


def run_reserved() -> None:
    """Unique essai diagnostique : empreintes revérifiées, reçu créé avant le lancement."""
    registration = json.loads((OUT / "diagnostic_registration.json").read_text(encoding="utf-8"))
    for path, expected in registration["harness_sha256"].items():
        assert digest(ROOT / path) == expected, "Diagnostic harness changed after registration"
    assert digest(CORPUS) == EXPECTED["corpus"] and digest(PLAN) == EXPECTED["plan"]
    save(
        OUT / "diagnostic_attempt.json",
        {"started_at_utc": datetime.now(UTC).isoformat(), "repeat_forbidden": True},
    )
    try:
        outcome: dict[str, Any] = {"completed": True} | diagnose(CORPUS, PLAN, "gate")
    except Exception as error:
        outcome = {"completed": False, "parent_failure": site("load", error)}
    save(
        OUT / "diagnostic_challenge.json",
        {"finished_at_utc": datetime.now(UTC).isoformat()} | outcome,
    )
    print("FIX2 diagnostic finished; sites only, no content.")


def main() -> int:
    """register, run (essai réservé unique) ou rehearse <corpus non réservé> <sortie neuve>."""
    if sys.argv[1:] == ["--worker"]:
        return worker()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("register", "run", "rehearse"))
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    if args.action == "register":
        register()
    elif args.action == "run":
        run_reserved()
    else:
        corpus, out = args.paths
        save(out, diagnose(corpus, PLAN, "dev"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
