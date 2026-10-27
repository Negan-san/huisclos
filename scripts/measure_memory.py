"""Mesure la mémoire résidente et les durées de la détection, sur CPU, dans un même processus.

Entrée : la démo fictive data/samples/demo_case_fr.txt, sans affichage de son contenu.
Sortie : un tableau Markdown ; par défaut, la configuration déployée (hybrid) au démarrage,
après la première détection et après dix détections ; avec --camembert, la comparaison D-06.
Place dans le pipeline : mesure hors application, pour D-05 (mémoire du cloud) et D-S44-1.
"""

import argparse
import os
import sys
from pathlib import Path
from time import perf_counter

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import streamlit  # noqa: E402, F401  (chargé comme dans l'application, pour un démarrage fidèle)

from huisclos.config import PRESETS  # noqa: E402
from huisclos.detection.pipeline import analyzer_for, detect  # noqa: E402

SAMPLE = ROOT / "data" / "samples" / "demo_case_fr.txt"
# Limite basse annoncée pour Community Cloud (D-05) : la mesure doit rester en dessous.
TARGET_MIB = 1024
REPEATS = 10


def rss_mib(process: psutil.Process) -> float:
    """Renvoie la mémoire résidente du processus en Mio."""
    return process.memory_info().rss / 1024**2


def measure_deployed(text: str) -> list[tuple[str, float, float]]:
    """Mesure la configuration hybrid comme dans l'application.

    Paramètre : text, le cas d'exemple.
    Valeur retournée : des lignes (étape, durée en secondes, RSS en Mio). Le démarrage
    compte l'import de Streamlit et du code métier ; le modèle spaCy se charge à la
    première détection, comme dans l'interface.
    """
    process = psutil.Process()
    rows = [("startup", 0.0, rss_mib(process))]
    config = PRESETS["hybrid"]
    started = perf_counter()
    count = len(detect(text, config))
    rows.append((f"first detection ({count} entities)", perf_counter() - started, rss_mib(process)))
    started = perf_counter()
    for _ in range(REPEATS):
        detect(text, config)
    rows.append((f"after {REPEATS} more detections", perf_counter() - started, rss_mib(process)))
    return rows


def print_deployed(text: str) -> None:
    """Affiche le tableau de la configuration déployée et la comparaison à la cible."""
    rows = measure_deployed(text)
    print("| Step | Duration s | RSS MiB |")
    print("| --- | ---: | ---: |")
    for step, seconds, mib in rows:
        print(f"| {step} | {seconds:.3f} | {mib:.1f} |")
    peak = max(mib for _, _, mib in rows)
    verdict = "below" if peak < TARGET_MIB else "above"
    print(f"\nPeak RSS {peak:.1f} MiB, {verdict} the {TARGET_MIB} MiB target.")


def print_camembert(text: str) -> None:
    """Affiche RSS et durées après chargement puis détection, sans puis avec CamemBERT.

    Les modèles restent en mémoire entre les lignes : la seconde inclut spaCy et
    CamemBERT, comme lors d'une activation de l'option dans une session locale.
    """
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
        loaded_mib = rss_mib(process)
        started = perf_counter()
        detections = detect(text, config)
        detection_seconds = perf_counter() - started
        print(
            f"| {name} | {load_seconds:.3f} | {loaded_mib:.1f} | "
            f"{detection_seconds:.3f} | {rss_mib(process):.1f} | {len(detections)} |"
        )


def main() -> None:
    """Lit les options puis lance la mesure demandée."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--camembert", action="store_true", help="compare hybrid and hybrid_camembert (D-06)"
    )
    args = parser.parse_args()
    text = SAMPLE.read_text(encoding="utf-8")
    if args.camembert:
        print_camembert(text)
    else:
        print_deployed(text)


if __name__ == "__main__":
    main()
