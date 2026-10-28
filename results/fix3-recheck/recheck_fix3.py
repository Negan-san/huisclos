"""Lance les sondes indépendantes FIX3R sans corpus réservé.

Entrées : fixtures nouvelles des modules voisins et code FIX3 figé.
Sorties : JSON de comptes et booléens seulement, sans mentions ni positions.
La suite et les contrôles Git sont lancés séparément par check_controls.py.
"""

import json
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
os.environ.update(
    {
        "PYTHONUTF8": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "TOKENIZERS_PARALLELISM": "false",
    }
)

from guarded_pytest import guard  # noqa: E402

sys.addaudithook(guard)

from pipeline_probes import fixtures, invariants, matrix, memory  # noqa: E402
from ui_probes import ui  # noqa: E402

from scripts import gate8_measure  # noqa: E402


def worker() -> dict:
    """Lance le vrai worker séparé G8 sur une fixture nouvelle dans chaque langue."""
    rows = {}
    for language in ("fr", "en"):
        text = fixtures(language)[0][1]
        payload = gate8_measure.run_separate(
            {"preset": "hybrid", "threshold": 0.3}, [text], language, "dev"
        )
        document = payload["documents"][0]
        counts = {
            "documents": len(payload["documents"]),
            "detections": len(document["detections"]),
            "occurrences": len(document["occurrences"]),
        }
        rows[language] = counts | {
            "passed": counts == {"documents": 1, "detections": 3, "occurrences": 3},
            "network_blocked": payload["metadata"]["resources"]["network_blocked"],
            "final_check_available": payload["metadata"]["final_check"]["available"],
        }
    return rows


def no_network(*args: object, **kwargs: object) -> None:
    """Refuse DNS et connexions distantes ; AppTest conserve sa boucle locale native."""
    raise OSError("FIX3R: network forbidden")


if __name__ == "__main__":
    selected = sys.argv[1]
    if selected != "ui":
        for owner, key in (
            (socket, "getaddrinfo"),
            (socket, "create_connection"),
            (socket.socket, "connect"),
            (socket.socket, "connect_ex"),
            (socket.socket, "sendto"),
        ):
            setattr(owner, key, no_network)
    result = {
        "pipeline": matrix,
        "memory": memory,
        "invariants": invariants,
        "ui": ui,
        "worker": worker,
    }[selected]()
    path = ROOT / f"results/fix3-recheck/{selected}.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"section": selected, "rows": len(result), "output": path.name}))
    success = all(row.get("passed", row.get("runtime_error", False)) for row in result.values())
    raise SystemExit(0 if success else 1)
