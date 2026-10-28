"""Lance l'unique reprise challenge autorisée par G8R2.

Entrées : prérequis verts et plan historique FR inchangé.
Sorties : registre, reçu exclusif, agrégats du harnais et diagnostic validé.
Une deuxième invocation refuse avant toute lecture du corpus réservé.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

from controls import ENVIRONMENT, FIX, OUT, ROOT, digest, git, read, save

PLAN = ROOT / "results/gate8/plan_historical_fr.json"
COMMAND = [
    sys.executable,
    "scripts/gate8_measure.py",
    "--corpus",
    "corpus/challenge.jsonl",
    "--dataset-id",
    "gate8_resume_challenge",
    "--plan",
    str(PLAN.relative_to(ROOT)),
    "--out",
    "results/gate8-resume/challenge",
    "--mode",
    "gate",
]


def validated_diagnostic(stderr: str) -> dict[str, Any]:
    """Extrait seulement le stade, la classe et un lieu technique conformes au harnais."""
    match = re.search(
        r"G8 worker failed: exit ([0-9]+) at stage "
        r"(load|detection|pseudonymization|metadata) \(([A-Za-z_][A-Za-z0-9_]{0,63})\)"
        r"(?: in ((?:src/huisclos|scripts)/[A-Za-z0-9_/]{1,120}\.py):"
        r"(<module>|[A-Za-z_][A-Za-z0-9_]{0,63}):([1-9][0-9]*))?"
        r"; no reserved output shown",
        stderr,
    )
    if match is None:
        return {"available": False}
    exit_code, stage, error_type, path, function, line = match.groups()
    return {
        "available": True,
        "worker_exit_code": int(exit_code),
        "stage": stage,
        "error_type": error_type,
        "path": path,
        "function": function,
        "line": int(line) if line else None,
    }


def prerequisites() -> dict[str, Any]:
    """Refuse avant tout reçu si une preuve demandée manque ou n'est pas conforme."""
    assert git("rev-parse", "HEAD") == FIX
    assert git("branch", "--show-current") == "lane-b"
    assert read("results/gate8-resume/scope.json")["passed"]
    assert read("results/gate8-resume/environment.json")["passed"]
    independent = read("results/gate8-resume/independent-current.json")
    assert independent["exit_code"] == 0 and independent["passed"] == 12
    checks = read("results/gate8-resume/preflight2-checks.json")
    assert all(item["exit_code"] == 0 for item in checks.values())
    assert not git(
        "diff",
        FIX,
        "--name-only",
        "src",
        "app",
        "tests",
        "scripts",
        "corpus",
        "data",
        ".streamlit",
        "streamlit_app.py",
        "pyproject.toml",
        "requirements*",
    )
    expected = read("results/gate8-resume/scope.json")["historical_artifacts_sha256"]
    assert all(digest(ROOT / path) == value for path, value in expected.items())
    frozen = read("results/gate8/registration.json")
    assert (
        read("results/fix2/diagnostic_registration.json")["attempt"][
            "historical_challenge_execution_in_project"
        ]
        == 3
    )
    assert digest(PLAN) == frozen["artifact_sha256"]["results\\gate8\\plan_historical_fr.json"]
    assert json.loads(PLAN.read_text(encoding="utf-8")) == {
        "document_language": "fr",
        "profiles": {
            "standard": {"preset": "hybrid", "threshold": 0.3},
            "enhanced": {"preset": "hybrid_camembert", "threshold": 0.3},
        },
        "comparisons": [["enhanced", "standard"]],
    }
    assert frozen["bootstrap"] == {"draws": 2000, "seed": 45, "paired": True}
    assert frozen["margins"] == {"partial_precision": 0.02, "overmasking": 0.01}
    return {"all_passed": True, "independent": independent, "checks": checks}


def measure() -> None:
    """Crée registre et reçu avant la seule exécution du CLI historique actuel."""
    # Même si le premier essai échoue avant son premier profil, il reste consommé.
    if any(
        (OUT / name).exists()
        for name in ("registration.json", "attempt_challenge.json", "challenge")
    ):
        raise SystemExit("G8R2: second attempt refused before reserved access")
    prereqs = prerequisites()
    os.environ.update(ENVIRONMENT)
    scripts = [
        "scripts/gate8_measure.py",
        "scripts/evaluate_robustness.py",
        "src/huisclos/evaluation/run.py",
        "src/huisclos/evaluation/coverage_reports.py",
        "src/huisclos/evaluation/intervals.py",
        "results/gate8-resume/run_resume.py",
        "results/gate8-resume/controls.py",
        "results/gate8-resume/test_recheck.py",
        "results/gate8-resume/test_launch_safety.py",
        "results/gate8-resume/summarize.py",
        "results/fix3-recheck/guarded_pytest.py",
        "results/gate8/plan_historical_fr.json",
    ]
    registration = {
        "registered_at_utc": datetime.now(UTC).isoformat(),
        "measured_sha": FIX,
        "git_status": git("status", "--porcelain"),
        "git_diff_names": git("diff", "--name-only"),
        "command": COMMAND,
        "dataset_id": "gate8_resume_challenge",
        "mode": "gate",
        "plan": json.loads(PLAN.read_text(encoding="utf-8")),
        "artifact_sha256": {path: digest(ROOT / path) for path in scripts},
        "environment": read("results/gate8-resume/environment.json"),
        "parameters": {
            "threshold": 0.3,
            "final_check_threshold": 0.1,
            "bootstrap": {"draws": 2000, "seed": 45, "paired": True},
            "precision_margin": 0.02,
            "overmasking_margin": 0.01,
        },
        "prerequisites": prereqs,
        "attempt_history": [
            {"number": 1, "session": "G7", "status": "complete"},
            {
                "number": 2,
                "session": "G8",
                "status": "failed",
                "cli_exit_code": 2,
                "receipt": "results/gate8/attempt_challenge.json",
            },
            {
                "number": 3,
                "session": "FIX2",
                "status": "diagnostic_only",
                "receipt": "results/fix2/diagnostic_attempt.json",
            },
            {"number": 4, "session": "G8R2", "status": "registered_unique_resume"},
        ],
        "historical_challenge_execution_in_project": 4,
        "nature": "known historical corpus; not a fresh blind validation",
        "new_test_series": 0,
        "new_c3_series": 0,
        "repeat_forbidden": True,
        "threshold_selection_allowed": False,
    }
    save("registration.json", registration)
    save(
        "attempt_challenge.json",
        {
            "started_at_utc": datetime.now(UTC).isoformat(),
            "attempt_number": 4,
            "measured_sha": FIX,
            "registration_sha256": digest(OUT / "registration.json"),
            "plan_sha256": digest(PLAN),
            "exclusive_creation": True,
            "repeat_forbidden": True,
        },
    )
    # Le reçu existe déjà. Seule cette fonction de provenance lit l'empreinte réservée.
    with (ROOT / "corpus/challenge.jsonl").open("rb") as handle:
        corpus_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    save(
        "challenge-provenance.json",
        {
            "corpus_sha256": corpus_hash,
            "attempt_number": 4,
            "matches_g8": corpus_hash
            == read("results/gate8/attempt_challenge.json")["corpus_sha256"],
        },
    )
    assert read("results/gate8-resume/challenge-provenance.json")["matches_g8"]
    completed = subprocess.run(
        COMMAND,
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    report = OUT / "challenge/robustness.json"
    outcome = {
        "finished_at_utc": datetime.now(UTC).isoformat(),
        "attempt_number": 4,
        "cli_exit_code": completed.returncode,
        "report_produced": report.exists(),
        "raw_stdout_retained": False,
        "raw_stderr_retained": False,
        "diagnostic": validated_diagnostic(completed.stderr) if completed.returncode else None,
        "repeat_forbidden": True,
    }
    save("complete_challenge.json", outcome)
    with (OUT / "measurement.log").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(outcome, ensure_ascii=True, indent=2) + "\n")
    print(json.dumps(outcome, ensure_ascii=True))
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    measure()
