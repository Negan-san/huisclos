"""Lance la comparaison locale des configurations et le choix du seuil.

Entrées : split, noms des configurations et dossier de sortie en arguments.
Sorties : fichiers de résultats agrégés ; erreurs détaillées pour dev seulement.
Place dans le pipeline : commande d'accès à huisclos.evaluation.run.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huisclos.config import PRESETS  # noqa: E402
from huisclos.evaluation.run import run_evaluation  # noqa: E402


def main() -> None:
    """Lit les options, exécute l'évaluation locale et indique le dossier produit."""
    parser = argparse.ArgumentParser(description="Evaluate local detection on fictional corpora.")
    parser.add_argument("--split", choices=("dev", "test", "challenge", "all"), default="dev")
    parser.add_argument("--configs", nargs="+", choices=tuple(PRESETS))
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    parser.epilog = (
        "Saved reports include 95% document bootstrap intervals (2,000 draws, seed 45). "
        "Challenge requires the threshold already selected on dev; all means dev then test."
    )
    arguments = parser.parse_args()
    try:
        report = run_evaluation(arguments.split, arguments.configs, arguments.out)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"Evaluation failed: {error}\n")
    print(f"Selected threshold: {report['selected_threshold']['threshold']:.2f}")
    print(f"Results: {arguments.out.resolve()}")
    for note in report["notes"]:
        print(note)


if __name__ == "__main__":
    main()
