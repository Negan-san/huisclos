"""Produit le verdict G8R à partir des preuves et agrégats existants.

Entrées : reçus du recontrôle et rapports G8 conservés sans modification.
Sorties : registre de réutilisation et verdict séparé par langue et profil.
Aucun détecteur ni corpus n'est chargé par cette synthèse pure.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OUT = Path(__file__).resolve().parent
G8 = OUT.parent / "gate8"


def read(path: Path) -> Any:
    """Relit un agrégat ou reçu UTF-8, jamais un document du corpus."""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """Vérifie les points ouverts et archive un verdict sans nouvelle mesure."""
    summary = read(G8 / "summary.json")
    registration = read(G8 / "registration.json")
    integrity = read(OUT / "integrity.json")
    checks = read(OUT / "full-checks.json")
    final = read(OUT / "final-checks.json")
    targeted = read(OUT / "targeted-checks.json")
    offline = read(OUT / "offline.json")
    assert checks["checks"]["pytest"]["exit_code"] == 0
    assert all(row["exit_code"] == 0 for row in final["checks"].values())
    assert all(row["exit_code"] == 0 for row in targeted["checks"].values())
    for name, evidence in integrity["g8_artifacts_unchanged"].items():
        assert (
            hashlib.sha256((OUT.parents[1] / name).read_bytes()).hexdigest() == evidence["sha256"]
        )
    assert all(row["network_blocked"] for key, row in offline.items() if key.endswith("complete"))
    english = summary["blind_en"]["profiles"]
    standard, enhanced = english["standard"], english["enhanced"]
    precision_drop = standard["partial"]["precision"] - enhanced["partial"]["precision"]
    margin = registration["margins"]["partial_precision"]
    assert precision_drop > margin
    assert (
        enhanced["coverage"]["entities_fully_covered"]
        > standard["coverage"]["entities_fully_covered"]
    )
    assert enhanced["coverage"]["leaked_characters"] < standard["coverage"]["leaked_characters"]
    failed = read(G8 / "failed_challenge.json")
    assert failed["available"] is False and failed["predictions_recoverable"] is False
    assert not (G8 / "challenge/robustness.json").exists()
    registry = []
    for split in registration["reserved_series"]:
        attempt = G8 / f"attempt_{split}.json"
        complete = G8 / f"complete_{split}.json"
        assert attempt.is_file()
        registry.append(
            {
                "session": "G8",
                "split": split,
                "attempt": str(attempt.relative_to(OUT.parent)),
                "completed": complete.is_file(),
                "g8r_action": "reuse" if complete.is_file() else "keep unavailable; no retry",
            }
        )
    payload = {
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "decision": "D-G8R-1",
        "global": "NO-GO",
        "freeze_commit": integrity["freeze_commit"],
        "metrics_describe": "G8 measured HEAD e3d13bd; business trees identical to FIX",
        "new_reserved_attempts": 0,
        "registry": registry,
        "historical_test_measurement_number": 4,
        "c3_status": "previously measured holdout; no fresh blind validation",
        "technical_workflow_controls": "GO for observed FR/EN controls",
        "g8_01": (
            "closed: exact predictions/substitutions survive early, middle "
            "and late final-check failures"
        ),
        "worker_diagnostic": (
            "verified at load, detection, pseudonymization and metadata; message excluded"
        ),
        "fr_standard": "G8 gains retained; historical challenge validation remains open",
        "fr_enhanced": "G8 point criterion retained; historical challenge validation remains open",
        "en_standard": "experimental; 22/100 evaluated entities exposed before human review",
        "en_enhanced": "NO-GO recommendation; frozen precision margin exceeded",
        "english_precision_drop": precision_drop,
        "english_precision_margin": margin,
        "historical_challenge": (
            "unavailable; root cause unknown; no causal link to G8-01 established"
        ),
        "automatic_correction_measurement_loop": False,
        "fallback": "Standard, full human review and manual additions; no anonymity guarantee",
        "tag_or_push": False,
    }
    with (OUT / "verdict.json").open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
        handle.write("\n")
    print(
        "NO-GO: G8-01 closed; challenge unavailable; "
        f"EN precision loss {precision_drop:.6f} > {margin}."
    )


if __name__ == "__main__":
    main()
