"""Mesure les ressources des deux configurations locales de détection.

Entrée : la démo fictive data/samples/demo_case_fr.txt, sans affichage de son contenu.
Sortie : tableau de mémoire résidente et de durées, sur CPU, dans un même processus.
Place dans le pipeline : mesure facultative de l'apport et du coût de CamemBERT.
"""

import os
import sys
from pathlib import Path
from time import perf_counter

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from huisclos.config import PRESETS  # noqa: E402
from huisclos.detection.pipeline import analyzer_for, detect  # noqa: E402


def main() -> None:
    """Affiche RSS en Mio et durées en secondes après chargement puis détection.

    Les modèles restent en mémoire entre les lignes : la seconde inclut spaCy et
    CamemBERT, comme lors d'une activation de l'option dans une session locale.
    """
    text = (ROOT / "data/samples/demo_case_fr.txt").read_text(encoding="utf-8")
    process = psutil.Process()
    print(
        "| Configuration | Chargement s | RSS chargée Mio | "
        "Détection s | RSS finale Mio | Entités |"
    )
    print("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name in ("hybrid", "hybrid_camembert"):
        config = PRESETS[name]
        started = perf_counter()
        analyzer_for(config)
        load_seconds = perf_counter() - started
        loaded_mib = process.memory_info().rss / 1024**2
        started = perf_counter()
        detections = detect(text, config)
        detection_seconds = perf_counter() - started
        final_mib = process.memory_info().rss / 1024**2
        print(
            f"| {name} | {load_seconds:.3f} | {loaded_mib:.1f} | "
            f"{detection_seconds:.3f} | {final_mib:.1f} | {len(detections)} |"
        )


if __name__ == "__main__":
    main()
