"""Sonde FIX2 du profil Enhanced EN, sur corpus/english_dev seulement (aucun corpus réservé).

Entrées : dev anglais, profils hybrid et hybrid_gliner au seuil 0,30, GLiNER 0,70 inchangé.
Sorties : faux positifs partiels par catégorie, source et type ; spans GLiNER rendus avec
plusieurs labels ou imbriqués. Comptes seulement ; aucun réglage ni seuil n'est choisi ici.
"""

import json
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src")]

from huisclos.config import PRESETS  # noqa: E402
from huisclos.detection import gliner  # noqa: E402
from huisclos.detection.analysis_view import build_view  # noqa: E402
from huisclos.detection.pipeline import detect  # noqa: E402
from huisclos.evaluation.corpus import CorpusDocument, load_corpus  # noqa: E402
from huisclos.evaluation.metrics import (  # noqa: E402
    evaluated_predictions,
    evaluated_references,
    match_entities,
)

CORPUS = ROOT / "corpus/english_dev/dev.jsonl"


def categories(documents: list[CorpusDocument], preset: str) -> dict[str, Any]:
    """Classe chaque prédiction : vrai positif partiel, type faux, double ou sans référence."""
    config = replace(PRESETS[preset], threshold=0.3, document_language="en")
    counts: Counter[str] = Counter()
    for document in documents:
        predictions = evaluated_predictions(detect(document.text, config))
        pairs = match_entities(evaluated_references(document.entities), predictions, "partial")
        matched = {index for _, index in pairs}
        for index, prediction in enumerate(predictions):
            if index in matched:
                counts[f"tp|{prediction.source.value}"] += 1
                continue
            overlapping = [
                reference
                for reference in document.entities
                if reference.start < prediction.end and prediction.start < reference.end
            ]
            if not overlapping:
                kind = "no_reference"
            elif all(reference.type != prediction.entity_type for reference in overlapping):
                kind = "wrong_type"
            else:
                kind = "duplicate_or_split"
            counts[f"fp|{kind}|{prediction.source.value}|{prediction.entity_type.value}"] += 1
    tp = sum(value for key, value in counts.items() if key.startswith("tp|"))
    fp = sum(value for key, value in counts.items() if key.startswith("fp|"))
    return {"tp": tp, "fp": fp, "precision": round(tp / (tp + fp), 6), "counts": dict(counts)}


def label_shapes(texts: list[str]) -> dict[str, int]:
    """Compte les spans GLiNER à plusieurs labels et les paires imbriquées, au seuil 0,70."""
    results = same_span = nested = 0
    for text in texts:
        found = gliner.analyze(build_view(text).text, 0.70)
        results += len(found)
        spans: dict[tuple[int, int], list[str]] = defaultdict(list)
        for item in found:
            spans[item.start, item.end].append(item.entity_type)
        same_span += sum(1 for labels in spans.values() if len(labels) > 1)
        keys = sorted(spans)
        nested += sum(1 for a in keys for b in keys if a != b and a[0] <= b[0] and b[1] <= a[1])
    return {"gliner_results": results, "same_span_multi_label": same_span, "nested_pairs": nested}


def main() -> int:
    """Écrit le registre JSON de la sonde dans le fichier neuf passé en argument."""
    documents = load_corpus(CORPUS)
    record = {
        "corpus": "corpus/english_dev/dev.jsonl",
        "documents": len(documents),
        "profiles": {name: categories(documents, name) for name in ("hybrid", "hybrid_gliner")},
        "gliner_label_shapes_dev": label_shapes([document.text for document in documents]),
    }
    with Path(sys.argv[1]).open("x", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
