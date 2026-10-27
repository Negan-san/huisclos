"""Détection en ligne de commande sur un fichier texte.

Usage : python scripts/detect_cli.py <fichier> [--config hybrid]
Sortie : un tableau start, end, type, score, source, texte ; puis le nombre de détections
par type et le temps de calcul (chargement du modèle compté à part).
"""

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from huisclos.config import PRESETS  # noqa: E402
from huisclos.detection.pipeline import analyzer_for, detect  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Détecte les données personnelles d'un fichier.")
    parser.add_argument("path", type=Path, help="fichier texte UTF-8")
    parser.add_argument("--config", default="hybrid", choices=sorted(PRESETS))
    args = parser.parse_args(argv)
    text = args.path.read_text(encoding="utf-8")
    config = PRESETS[args.config]

    started = time.perf_counter()
    analyzer_for(config)
    loading = time.perf_counter() - started
    started = time.perf_counter()
    detections = detect(text, config)
    elapsed = time.perf_counter() - started

    print(f"{'start':>6} {'end':>6}  {'type':<13} {'score':>5}  {'source':<14} texte")
    for d in detections:
        shown = d.text.replace("\n", "\\n")
        print(
            f"{d.start:>6} {d.end:>6}  {d.entity_type.value:<13} {d.score:>5.2f}"
            f"  {d.source.value:<14} {shown}"
        )
    print()
    counts = Counter(d.entity_type.value for d in detections)
    for entity_type, count in sorted(counts.items()):
        print(f"{entity_type:<13} {count}")
    print(f"total         {len(detections)}")
    print(f"{len(text)} caractères ; chargement {loading:.2f} s ; détection {elapsed:.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
