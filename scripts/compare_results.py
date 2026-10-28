"""Compare deux dossiers de résultats sans lancer le moteur de détection.

Entrées : dossiers référence et actuel, split explicite, dossier de sortie facultatif.
Sorties : results/<split>_comparison.md et .json par défaut.
Place dans le pipeline : commande de comparaison avant/après destinée aux gates.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huisclos.evaluation.comparison import compare_result_folders  # noqa: E402


def main() -> None:
    """Lit les dossiers et le split, puis écrit les deux rapports de comparaison."""
    parser = argparse.ArgumentParser(
        description="Compare saved evaluation results, without detection."
    )
    parser.add_argument("reference", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--split", choices=("dev", "test", "challenge"), required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    try:
        compare_result_folders(
            arguments.reference, arguments.current, arguments.split, arguments.out
        )
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Comparison failed: {error}\n")
    print(f"Comparison: {arguments.out.resolve() / (arguments.split + '_comparison.md')}")


if __name__ == "__main__":
    main()
