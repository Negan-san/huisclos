"""Vérifie le seuil anglais figé avant toute mesure réservée.

Entrées : dev anglais public au réglage, quatorze seuils Standard préenregistrés.
Sorties : balayage agrégé et seuil compatible avec le format historique.
Aucun changement de paramètre n'est permis si le seuil diffère du gel A4.
"""

import json
import os
import socket
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from huisclos.config import profile_config  # noqa: E402
from huisclos.evaluation.metrics import Evaluation  # noqa: E402
from huisclos.evaluation.run import THRESHOLDS, choose_threshold, load_unreserved, micro_partial  # noqa: E402
from scripts.gate8_measure import refuse_network  # noqa: E402


def main() -> None:
    """Mesure le dev seulement et refuse tout seuil autre que le 0,30 déjà gelé."""
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    socket.socket.connect = socket.getaddrinfo = socket.create_connection = refuse_network
    from huisclos.detection.pipeline import detect

    documents = load_unreserved(ROOT / "corpus/english_dev/dev.jsonl", "dev")
    rows = []
    for threshold in THRESHOLDS:
        config = replace(profile_config("standard", "en"), threshold=threshold)
        evaluation = Evaluation()
        for document in documents:
            evaluation.add_document(document.entities, detect(document.text, config))
        rows.append({"threshold": threshold, **micro_partial(evaluation.rows())})
    chosen = choose_threshold(rows)
    assert chosen == 0.3, "Seuil anglais différent du gel : arrêt avant mesure réservée"
    out = Path(__file__).resolve().parent / "dev_en_threshold"
    out.mkdir(exist_ok=False)
    payload = {"threshold": chosen, "criterion": "max F2 (partial, micro) on EN dev; lowest tie"}
    (out / "threshold.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out / "sweep.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"EN dev threshold verified: {chosen:.2f}; {len(documents)} documents.")


if __name__ == "__main__":
    main()
