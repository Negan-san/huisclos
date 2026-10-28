"""Vérifie les poids réellement lus par le code G7 intact.

Entrées : cache Hugging Face local et manifeste A1 préservé.
Sorties : révision et empreintes seulement, sans chargement ni réseau.
Ce contrôle utilise l'interpréteur baseline de la référence G7.
"""

import hashlib
import json
from pathlib import Path

from huggingface_hub.constants import HF_HUB_CACHE

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT.parent / "pilotage/post_g7_assets"


def main() -> None:
    """Exige l'égalité entre le cache historique et le snapshot CamemBERT A1."""
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    model = manifest["models"]["camembert_ner"]
    folder = Path(HF_HUB_CACHE) / "models--Jean-Baptiste--camembert-ner"
    revision = (folder / "refs/main").read_text(encoding="utf-8").strip()
    assert revision == model["revision"]
    hashes = {}
    for item in model["files"]:
        path = folder / "snapshots" / revision / item["name"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == item["sha256"]
        hashes[item["name"]] = actual
    with Path(__file__).with_suffix(".json").open("x", encoding="utf-8") as handle:
        json.dump(
            {"revision": revision, "file_sha256": hashes, "matches_a1": True}, handle, indent=2
        )
        handle.write("\n")
    print(f"G7 actual cache verified: revision fixed, {len(hashes)} matching files.")


if __name__ == "__main__":
    main()
