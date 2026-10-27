"""Aller-retour pseudonymisation puis restauration sur un fichier texte.

Usage : python scripts/roundtrip_cli.py <fichier> [--llm <réponse>]
Sortie : le texte pseudonymisé, puis le résultat de la restauration exacte (code 1 si le
texte restauré diffère de l'original) ; avec --llm, la réponse restaurée en mode tolérant,
les formes altérées et les formes inconnues.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from huisclos.config import PRESETS  # noqa: E402
from huisclos.detection.pipeline import detect  # noqa: E402
from huisclos.pseudonymize.reidentify import restore  # noqa: E402
from huisclos.pseudonymize.tokens import pseudonymize  # noqa: E402


def first_difference(left: str, right: str) -> int:
    """Position du premier caractère qui diffère entre deux textes."""
    for position, (a, b) in enumerate(zip(left, right, strict=False)):
        if a != b:
            return position
    return min(len(left), len(right))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pseudonymise puis restaure un fichier.")
    parser.add_argument("path", type=Path, help="fichier texte UTF-8")
    parser.add_argument("--llm", type=Path, help="réponse du LLM à restaurer (texte UTF-8)")
    args = parser.parse_args(argv)
    text = args.path.read_text(encoding="utf-8")

    result = pseudonymize(text, detect(text, PRESETS["hybrid"]))
    print(result.text)
    for warning in result.warnings:
        print(f"Avertissement : {warning}")
    restored = restore(result.text, result.mapping, result.occurrences)
    if restored.text != text:
        position = first_difference(restored.text, text)
        print(f"ECHEC : mode {restored.mode}, premier écart à la position {position}.")
        return 1
    total = sum(restored.replaced.values())
    print(f"\nAller-retour exact : OK (mode {restored.mode}, {total} remplacements).")

    if args.llm:
        response = restore(args.llm.read_text(encoding="utf-8"), result.mapping)
        print(f"\nRéponse restaurée (mode {response.mode}) :\n{response.text}")
        print(f"Formes altérées ({len(response.altered)}) :")
        for form, token in response.altered:
            print(f"  {form!r} -> {token}")
        print(f"Formes inconnues ({len(response.unknown)}) :")
        for form, position in response.unknown:
            print(f"  {form!r} à la position {position}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
