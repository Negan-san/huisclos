"""Résume les preuves FIX3R sans recopier les documents de sondage.

Entrées : sorties JSON et journaux locaux déjà produits.
Sorties : synthèse, contrôles finaux et vérification du périmètre autorisé.
Le verdict reste négatif si un résultat est conservé après l'échec de substitution.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/fix3-recheck"


def read(name: str) -> Any:
    """Lit une preuve JSON locale, jamais un corpus ou une table de correspondance."""
    return json.loads((OUT / f"{name}.json").read_text(encoding="utf-8"))


def summarize() -> None:
    """Consolide le verdict et contrôle les messages de clôture des tests existants."""
    controls = {}
    for name in ("pytest", "ruff-check", "ruff-format", "style", "diff-check", "staged-diff-check"):
        log = (OUT / f"{name}.log").read_text(encoding="utf-8")
        controls[name] = int(re.search(r"^Exit: (\d+)$", log, re.MULTILINE)[1])
    assert all(code == 0 for code in controls.values())
    pytest_log = (OUT / "pytest.log").read_text(encoding="utf-8")
    assert "1720 passed" in pytest_log and "reserved opens refused: 0" in pytest_log
    assert not re.search(r"\d+ xfailed", pytest_log)
    pipeline, ui = read("pipeline"), read("ui")
    required = {k: v for k, v in pipeline.items() if not k.endswith("numeric-suffix")}
    assert len(required) == 20 and all(row["passed"] for row in required.values())
    memory, invariants, worker = read("memory"), read("invariants"), read("worker")
    assert all(row["passed"] for row in memory.values())
    assert all(
        row["runtime_error"] and row["current_function_located"] for row in invariants.values()
    )
    assert all(row["passed"] for row in worker.values())
    assert all(row["passed"] for key, row in ui.items() if key.endswith("fresh"))
    stale = sum(row["previous_result_retained"] for row in ui.values())
    assert stale == 2
    changed = (
        subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT)
        .decode()
        .splitlines()
    )
    allowed_docs = {"docs/PROGRESS.md", "docs/PROMPTS.md", "docs/DECISIONS.md"}
    assert changed and all(
        p.startswith("results/fix3-recheck/") or p in allowed_docs for p in changed
    )
    summary = {
        "fix3_sha": read("scope")["fix"],
        "scope_and_patch_verified": read("scope")["equal"],
        "controls": controls,
        "pytest_passed": 1720,
        "xfail": 0,
        "corpus_roundtrip_scope": "dev_only",
        "reserved_opens": 0,
        "regressions": read("regressions"),
        "required_pipeline_cases_passed": len(required),
        "pipeline_orders": sum(row["orders"] for row in required.values()),
        "exploratory_pipeline_count_mismatches": sum(
            not row["passed"] for row in pipeline.values()
        ),
        "memory_languages_passed": len(memory),
        "presidio_refusals": len(invariants),
        "fresh_ui_cases_passed": 4,
        "retry_ui_stale_results": stale,
        "worker_languages_passed": len(worker),
        "scope_paths": changed,
        "fix3_verdict": "NO-GO",
        "blocking_finding": "FIX3R-01",
        "challenge_gate_authorized": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    summarize()
