"""Consigne les contrôles complets avant la première mesure réservée.

Entrées : journal pytest terminé et commandes locales de lint, style et diff.
Sorties : reçu vert seulement si chaque commande réussit.
Les journaux PowerShell sont archivés puis normalisés en UTF-8.
"""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main() -> None:
    """Exige les 1680 tests verts et tous les contrôles avant de produire le reçu."""
    log = OUT / "preflight-pytest.log"
    if log.read_bytes().startswith(b"\xff\xfe"):
        original = (
            ROOT.parent / "pilotage/post_g7_assets/benchmarks/G8/preflight-pytest-original.log"
        )
        original.write_bytes(log.read_bytes())
        log.write_text(log.read_text(encoding="utf-16"), encoding="utf-8")
    assert "1680 passed, 1 warning" in log.read_text(encoding="utf-8")
    commands = {
        "ruff_check": [sys.executable, "-m", "ruff", "check", "."],
        "ruff_format": [sys.executable, "-m", "ruff", "format", "--check", "."],
        "style": [sys.executable, "scripts/check_style.py"],
        "diff": ["git", "diff", "--check"],
    }
    statuses = {}
    for name, command in commands.items():
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False
        )
        (OUT / f"preflight-{name}.log").write_text(
            completed.stdout + completed.stderr, encoding="utf-8"
        )
        assert completed.returncode == 0, f"Preflight failed: {name}"
        statuses[name] = "passed"
    with (OUT / "checks_before_reserved.json").open("x", encoding="utf-8") as handle:
        json.dump(
            {
                "completed_at_utc": datetime.now(UTC).isoformat(),
                "pytest_passed": 1680,
                "warnings": ["torch.jit.script deprecated"],
                "checks": statuses,
                "all_green": True,
            },
            handle,
            indent=2,
        )
        handle.write("\n")
    print("Preflight green: 1680 tests, Ruff, format, style and diff.")


if __name__ == "__main__":
    main()
