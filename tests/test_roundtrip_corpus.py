"""Aller-retour sur tout le corpus fictif : restauration exacte, puis tolérante après altération.

Les messages d'échec ne montrent que l'identifiant du document et une position, jamais
le texte, pour que les journaux de test ne recopient pas le corpus.
"""

import random
import re

import pytest

from huisclos.config import PRESETS
from huisclos.detection.pipeline import detect
from huisclos.evaluation.corpus import CORPUS_DIR, CorpusDocument, load_corpus
from huisclos.models import PseudonymizationResult
from huisclos.pseudonymize.mapping import Mapping
from huisclos.pseudonymize.reidentify import EXACT, find_token_forms, restore
from huisclos.pseudonymize.tokens import pseudonymize

SPLIT_FILES = [CORPUS_DIR / "dev.jsonl", CORPUS_DIR / "test.jsonl"]
CREATED_AT = "2026-10-27T12:00:00+00:00"
# Jeton au format par défaut : crochets droits, libellé, tiret bas, indice.
TOKEN = re.compile(r"\[(?P<label>[A-Z]+(?:_[A-Z]+)*)_(?P<index>\d+|[A-Z]+)\]")


def first_difference(left: str, right: str) -> int:
    """Position du premier caractère qui diffère entre deux textes."""
    for position, (a, b) in enumerate(zip(left, right, strict=False)):
        if a != b:
            return position
    return min(len(left), len(right))


@pytest.fixture(scope="module")
def roundtrip_inputs() -> list[tuple[CorpusDocument, PseudonymizationResult]]:
    """Documents des deux splits et leur pseudonymisation, calculés une seule fois."""
    missing = [path.name for path in SPLIT_FILES if not path.exists()]
    if missing:
        pytest.skip(f"corpus absent ({', '.join(missing)}) : lancer scripts/build_corpus.py")
    documents = [document for path in SPLIT_FILES for document in load_corpus(path)]
    config = PRESETS["hybrid"]
    return [
        (
            document,
            pseudonymize(document.text, detect(document.text, config), created_at=CREATED_AT),
        )
        for document in documents
    ]


def alter(text: str, rng: random.Random) -> str:
    """Abîme chaque jeton comme pourrait le faire un LLM.

    Altérations tirées au hasard : minuscules, crochets retirés, espaces ajoutés dans les
    crochets, tirets bas échappés à la manière de Markdown. Les crochets restent quand le
    jeton touche une lettre ou un chiffre, car un LLM ne colle pas un nom à un mot.
    """

    def damage(match: re.Match[str]) -> str:
        core = f"{match['label']}_{match['index']}"
        escaped = rng.random() < 0.5
        if escaped:
            core = core.replace("_", "\\_")
        if rng.random() < 0.5:
            core = core.lower()
        before = text[match.start() - 1 : match.start()]
        after = text[match.end() : match.end() + 1]
        glued = any(char.isalnum() for char in before + after)
        if rng.random() < 0.5 and not glued:
            return core
        opening, closing = ("\\[", "\\]") if escaped else ("[", "]")
        if rng.random() < 0.5:
            opening, closing = opening + " ", " " + closing
        return opening + core + closing

    return TOKEN.sub(damage, text)


def test_exact_roundtrip_on_whole_corpus(
    roundtrip_inputs: list[tuple[CorpusDocument, PseudonymizationResult]],
) -> None:
    failures = []
    for document, result in roundtrip_inputs:
        restored = restore(result.text, result.mapping, result.occurrences)
        if restored.mode != EXACT or restored.text != document.text:
            position = first_difference(restored.text, document.text)
            failures.append(f"{document.id} (mode {restored.mode}, écart en {position})")
        loaded = Mapping.from_json(result.mapping.to_json())
        from_json = restore(result.text, loaded)
        if loaded != result.mapping or from_json.mode != EXACT or from_json.text != document.text:
            position = first_difference(from_json.text, document.text)
            failures.append(f"{document.id} (JSON, mode {from_json.mode}, écart en {position})")
    assert not failures, "aller-retour exact en échec : " + ", ".join(failures)


def test_tolerant_restore_after_random_damage(
    roundtrip_inputs: list[tuple[CorpusDocument, PseudonymizationResult]],
) -> None:
    rng = random.Random(22)
    failures = []
    for document, result in roundtrip_inputs:
        damaged = alter(result.text, rng)
        restored = restore(damaged, result.mapping)
        left = find_token_forms(restored.text)
        if restored.unknown or left:
            positions = [p for _, p in restored.unknown] + [f.start for f in left]
            failures.append(f"{document.id} (position {min(positions, default=-1)})")
    assert not failures, "restauration tolérante en échec : " + ", ".join(failures)
