"""Exécute la suite existante sans ouvrir les corpus réservés.

Entrées : arguments pytest et racine du checkout courant.
Sortie : résultat pytest ; la fixture d'aller-retour utilise dev seulement.
Ce garde de session ne modifie ni les tests ni le pipeline.
"""

import os
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path.cwd().resolve()
DENIED: list[str] = []


def guard(event: str, arguments: tuple[Any, ...]) -> None:
    """Refuse toute ouverture du corpus hors dev et english_dev, sans lire son contenu."""
    if event != "open" or not isinstance(arguments[0], (str, bytes, os.PathLike)):
        return
    path = Path(os.fsdecode(arguments[0])).resolve()
    if not path.is_relative_to(ROOT / "corpus"):
        return
    relative = path.relative_to(ROOT / "corpus").as_posix()
    dev_sources = {f"source/doc_{number}.md" for number in range(19, 27)}
    if relative == "dev.jsonl" or relative.startswith("english_dev/") or relative in dev_sources:
        return
    DENIED.append("reserved_open")
    raise PermissionError("FIX3R: reserved corpus access forbidden")


class ScopePlugin:
    """Conserve toute la collecte pytest, avec une restriction explicite des données."""

    def pytest_collection_modifyitems(self, items: list[Any]) -> None:
        """Remplace la liste des données de roundtrip, jamais les assertions des tests."""
        for item in items:
            if item.module.__name__ == "test_roundtrip_corpus":
                item.module.SPLIT_FILES = [ROOT / "corpus/dev.jsonl"]

    def pytest_sessionfinish(self) -> None:
        """Affiche le nombre d'ouvertures refusées, sans chemin ni contenu."""
        print(f"FIX3R reserved opens refused: {len(DENIED)}")


if __name__ == "__main__":
    sys.addaudithook(guard)
    print("FIX3R: full test collection; corpus roundtrip restricted to dev by session policy")
    raise SystemExit(pytest.main(sys.argv[1:], plugins=[ScopePlugin()]))
