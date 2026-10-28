"""Consigne les contrôles de G8R avec leurs sorties et leurs codes.

Entrées : interpréteur partagé validé après A4 et groupe de contrôles demandé.
Sorties : journaux UTF-8 neufs et reçu daté, y compris en cas d'échec.
Les tests ciblés précèdent la suite complète ; aucune métrique réservée n'est lancée.
"""

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
TARGETS = [
    "tests/test_gate8.py",
    "tests/test_no_network.py",
    "tests/test_mistral_client.py",
    "tests/test_detection_profiles.py",
    "tests/test_metamorphic_detection.py",
    "tests/test_analysis_view.py",
    "tests/test_gliner.py",
    "tests/test_detection_windows.py",
]


def main(group: str) -> int:
    """Lance les commandes du groupe et archive chaque résultat sans écrasement."""
    commands = (
        {"targeted": [sys.executable, "-m", "pytest", "-q", *TARGETS]}
        if group == "targeted"
        else {
            "pytest": [sys.executable, "-m", "pytest", "-q"],
            "ruff_check": [sys.executable, "-m", "ruff", "check", "."],
            "ruff_format": [sys.executable, "-m", "ruff", "format", "--check", "."],
            "style": [sys.executable, "scripts/check_style.py"],
            "diff": ["git", "diff", "--check"],
        }
    )
    if group == "final":
        commands.pop("pytest")
    results = {}
    for name, arguments in commands.items():
        completed = subprocess.run(
            arguments,
            cwd=ROOT,
            env=os.environ
            | {"PYTHONUTF8": "1", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        log = OUT / f"{group}-{name}.log"
        with log.open("x", encoding="utf-8") as handle:
            handle.write(completed.stdout + completed.stderr)
        results[name] = {"command": arguments, "exit_code": completed.returncode, "log": log.name}
        print(f"{name}: exit {completed.returncode}", flush=True)
        print(completed.stdout[-1800:], flush=True)
    with (OUT / f"{group}-checks.json").open("x", encoding="utf-8") as handle:
        json.dump(
            {"completed_at_utc": datetime.now(UTC).isoformat(), "checks": results}, handle, indent=2
        )
        handle.write("\n")
    return int(any(result["exit_code"] != 0 for result in results.values()))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
