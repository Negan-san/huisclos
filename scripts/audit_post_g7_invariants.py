"""Audite indépendamment les garanties A1/A2 sur de nouvelles valeurs fictives.

Entrées : fixtures synthétiques définies ici, sans lecture de corpus réservé.
Sorties : assertions reproductibles et rapport de défauts hors dépôt.
Place : contrôle B3 ; aucune correction du moteur ni règle apprise des mesures.
"""

import argparse
import json
import re
import sys
from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from huisclos.config import DetectionConfig  # noqa: E402
from huisclos.detection.analysis_view import build_view  # noqa: E402
from huisclos.detection.merge import merge  # noqa: E402
from huisclos.detection.pipeline import detect  # noqa: E402
from huisclos.detection.windows import Window, best_views, mention  # noqa: E402
from huisclos.models import Detection, EntityType, Source  # noqa: E402
from huisclos.pseudonymize.grouping import group_mentions  # noqa: E402

CONFIG = DetectionConfig(threshold=0.3, use_spacy=False)


def candidate(text: str, start: int, end: int, kind: EntityType, score: float) -> Detection:
    """Construit une proposition fictive dont les bornes restent la seule référence."""
    return Detection(start, end, kind, score, Source.NER_CAMEMBERT, text[start:end])


def covered(detections: Sequence[Detection]) -> set[int]:
    """Renvoie les positions couvertes, sans confondre couverture et étiquette correcte."""
    return {i for d in detections for i in range(d.start, d.end)}


def audit_weak_candidate() -> None:
    """Un candidat faible intérieur ou frontal ne découvre aucune lettre déjà admissible."""
    text = "Éloïse Varenne"
    base = candidate(text, 0, len(text), EntityType.PERSON, 0.85)
    for threshold in (0.29, 0.3, 0.31, 0.6):
        config = replace(CONFIG, threshold=threshold)
        expected = covered(merge(text, [base], config))
        for start in range(len(text)):
            for end in range(start + 1, len(text) + 1):
                weak = candidate(text, start, end, EntityType.ORGANIZATION, 0.1)
                actual = merge(text, [weak, base], config)
                assert expected <= covered(actual), (threshold, start, end)
                assert all(d.text == text[d.start : d.end] for d in actual)


def audit_window_boundaries() -> None:
    """La meilleure fenêtre garde les bornes absolues et deux occurrences distinctes."""
    text = "xx Agathe Vernois yy Agathe Vernois zz"
    first = Window(0, 22, text[:22], False, True)
    second = Window(3, len(text), text[3:], True, False)
    found = best_views(
        [
            mention(first, 0, 3, 17, "PERSON", 0.9),
            mention(second, 1, 0, 14, "PERSON", 0.8),
            mention(second, 1, 18, 32, "PERSON", 0.9),
        ]
    )
    assert [(m.start, m.end) for m in found] == [(3, 17), (21, 35)]
    assert [text[m.start : m.end] for m in found] == ["Agathe Vernois"] * 2


def audit_unicode_projection() -> None:
    """Une ligature et une marque invisible sont reprojetées aux deux occurrences."""
    text = "Mme. O\ufb03line Va\u200brenne ; Mme. O\ufb03line Va\u200brenne"
    view = build_view(text)
    matches = list(re.finditer("Offiline Varenne", view.text))
    assert len(matches) == 2
    spans = [view.project(m.start(), m.end()) for m in matches]
    assert spans[0][1] < spans[1][0]
    assert all(text[s:e] == "O\ufb03line Va\u200brenne" for s, e in spans)
    found = detect(text, CONFIG)
    assert all(d.text == text[d.start : d.end] for d in found)
    assert all(set(range(s, e)) <= covered(found) for s, e in spans)


def audit_address_stop() -> None:
    """L'adresse entière comprend son complément et s'arrête avant le champ voisin."""
    address = "46 rue des Alouettes\nBâtiment C, appartement 8\n69007 Lyon"
    text = f"Domicile : {address}\nDestinataire : Madame Agathe Vernois"
    found = [d for d in detect(text, CONFIG) if d.entity_type == EntityType.ADDRESS]
    assert [d.text for d in found] == [address], [d.text for d in found]


def audit_english_address() -> None:
    """La règle anglaise couvre unité, ville et code postal sans le champ téléphone."""
    address = "Flat 5, 28 Alderwick Road, Bristol BS1 4QA"
    text = f"Address: {address}\nPhone: +44 20 7946 0128"
    config = replace(CONFIG, document_language="en")
    found = [d for d in detect(text, config) if d.entity_type == EntityType.ADDRESS]
    assert [d.text for d in found] == [address], [d.text for d in found]


def audit_public_reference() -> None:
    """Une citation publique reste visible et le numéro privé distinct reste protégé."""
    text = "Cass. soc., 18 mars 2020, n° 18-14.309 ; RG n° 26 / 04567."
    found = detect(text, CONFIG)
    cases = [d.text for d in found if d.entity_type == EntityType.CASE_NUMBER]
    assert cases == ["26 / 04567"], cases
    public_end = text.index(" ;")
    assert not covered(found).intersection(range(public_end))


def audit_distinct_dates() -> None:
    """Seule la date de naissance reçoit ce type ; l'audience reste visible."""
    text = (
        "Madame Agathe Vernois, née le 17 avril 1984. "
        "Audience le 9 novembre 2026. Signature le 10 novembre 2026."
    )
    found = detect(text, CONFIG)
    assert [d.text for d in found if d.entity_type == EntityType.BIRTH_DATE] == ["17 avril 1984"]
    assert all("novembre" not in d.text for d in found)


def audit_alias_ambiguity() -> None:
    """Un alias partagé ne regroupe pas deux personnes différentes."""
    text = (
        'Madame Agathe Vernois, alias "Lilas", écrit. '
        'Madame Éloïse Varenne, alias "Lilas", répond. Lilas revient.'
    )
    found = detect(text, CONFIG)
    groups = group_mentions(text, found)
    first = next(g for g in groups if "Agathe Vernois" in g.variants)
    second = next(g for g in groups if "Éloïse Varenne" in g.variants)
    assert first != second
    assert not set(first.mention_spans).intersection(second.mention_spans)
    for match in re.finditer("Lilas", text):
        assert set(range(match.start(), match.end())) <= covered(found)


def audit_different_people() -> None:
    """Deux noms complets partageant un prénom conservent des groupes distincts."""
    text = "Madame Agathe Vernois écrit à Madame Agathe Delcourt."
    found = detect(text, CONFIG)
    groups = [g for g in group_mentions(text, found) if g.entity_type == EntityType.PERSON]
    assert len(groups) == 2
    assert {d.text for d in found} == {"Agathe Vernois", "Agathe Delcourt"}


def audit_phone_bounds() -> None:
    """La ponctuation constitutive d'un téléphone reconnu appartient au span entier."""
    text = "Phone: (202) 555-0186"
    found = detect(text, replace(CONFIG, document_language="en"))
    actual = [d.text for d in found if d.entity_type == EntityType.PHONE]
    assert actual == ["(202) 555-0186"], actual


CASES: dict[str, Callable[[], None]] = {
    "weak_candidate": audit_weak_candidate,
    "window_boundaries": audit_window_boundaries,
    "unicode_projection": audit_unicode_projection,
    "address_stop": audit_address_stop,
    "english_address": audit_english_address,
    "public_reference": audit_public_reference,
    "distinct_dates": audit_distinct_dates,
    "alias_ambiguity": audit_alias_ambiguity,
    "different_people": audit_different_people,
    "phone_bounds": audit_phone_bounds,
}


def summarize(out: Path, language: str) -> None:
    """Mesure les unions et leurs apports marginaux avec les fonctions pures B1."""
    import itertools

    from huisclos.evaluation.coverage import (
        CoverageCounts,
        document_coverage,
        substituted_spans,
        sum_counts,
    )
    from huisclos.evaluation.coverage_reports import ProfileRun, build_report
    from huisclos.evaluation.metrics import Evaluation
    from huisclos.evaluation.run import load_unreserved, micro_partial
    from huisclos.pseudonymize.tokens import pseudonymize
    from scripts.benchmark_post_g7_pii import (
        CORPORA,
        GRID,
        checked_plan,
        digest,
        replay,
        save,
        unpack,
    )

    plan, documents = checked_plan(out), load_unreserved(CORPORA[language], "dev")
    payloads = [
        json.loads(p.read_text("utf-8"))
        for p in sorted(out.glob(f"{language}_*.json"))
        if p.name != f"{language}_report.json"
    ]
    for payload in payloads:
        if payload["plan_sha256"] != digest(out / "plan.json"):
            raise ValueError("Prédictions issues d'un autre plan.")
        if len(payload["documents"]) != len(documents):
            raise ValueError("Prédictions incomplètes.")
        repeats = [
            p
            for p in payloads
            if (p["backend"], p["environment"]) == (payload["backend"], payload["environment"])
        ]
        if {p["repeat"] for p in repeats} != {1, 2}:
            raise ValueError("Deux processus indépendants sont requis.")
        if any(p["documents"] != repeats[0]["documents"] for p in repeats):
            raise ValueError("Les répétitions ne sont pas déterministes.")
    cache = {(p["backend"], p["environment"]): p["documents"] for p in payloads if p["repeat"] == 1}
    baseline = cache["standard", "baseline"]
    sweep = []
    for threshold in plan["standard_thresholds"][language]:
        evaluation = Evaluation()
        for doc, raw in zip(documents, baseline, strict=True):
            evaluation.add_document(
                doc.entities, replay(doc.text, unpack(doc.text, raw), language, threshold)
            )
        sweep.append({"threshold": threshold, **micro_partial(evaluation.rows())})
    threshold = min(sweep, key=lambda r: (-r["f2"], r["threshold"]))["threshold"]
    runs, grid_rows = [], []
    for family in plan["families"][language]:
        candidates = []
        for cuts in itertools.product(GRID, repeat=len(family)):
            predictions, evaluation = [], Evaluation()
            for index, doc in enumerate(documents):
                raw = unpack(doc.text, baseline[index])
                for name, cut in zip(family, cuts, strict=True):
                    env = "baseline" if name == "camembert_ner" else "candidate"
                    raw += [d for d in unpack(doc.text, cache[name, env][index]) if d.score >= cut]
                predicted = replay(doc.text, raw, language, threshold)
                evaluation.add_document(doc.entities, predicted)
                predictions.append(predicted)
            row = {"family": family, "cuts": cuts, **micro_partial(evaluation.rows())}
            row["detection_coverage"] = sum_counts(
                (
                    document_coverage(len(doc.text), doc.entities, [(d.start, d.end) for d in ds])
                    for doc, ds in zip(documents, predictions, strict=True)
                ),
                CoverageCounts(),
            ).scores()
            grid_rows.append(row)
            candidates.append((row, predictions))
        row, predicted = min(candidates, key=lambda item: (-item[0]["f2"], item[0]["cuts"]))
        name = "+".join(family) or "standard"
        masks = [
            substituted_spans(
                [(o.start, o.end, len(o.original)) for o in pseudonymize(doc.text, ds).occurrences]
            )
            for doc, ds in zip(documents, predicted, strict=True)
        ]
        runs.append(ProfileRun(name, threshold, predicted, masks, None, {"cuts": row["cuts"]}))
    comparisons = [[r.name, "standard"] for r in runs[1:]]
    if language == "fr":
        union = "anonym_ia_v2+gliner_multi_pii_v1"
        comparisons += [[union, "anonym_ia_v2"], [union, "gliner_multi_pii_v1"]]
        comparisons += [[r.name, "camembert_ner"] for r in runs[2:]]
    report = build_report(
        documents, runs, comparisons, {"plan": plan, "plan_sha256": digest(out / "plan.json")}
    )
    report.update(
        standard_sweep=sweep,
        grid=grid_rows,
        resources=[{k: v for k, v in p.items() if k != "documents"} for p in payloads],
    )
    report["selected_threshold"]["criterion"] = (
        "fixed FR 0.30" if language == "fr" else "max partial micro F2 on EN dev; lowest tie"
    )
    by_name = {run.name: run.predictions for run in runs}
    report["coverage_losses"] = [
        {
            "candidate": a,
            "reference": b,
            "characters": sum(
                len(covered(before) - covered(after))
                for before, after in zip(by_name[b], by_name[a], strict=True)
            ),
        }
        for a, b in comparisons
    ]
    report["raw_migration_equal"] = (
        (cache.get(("camembert_ner", "baseline")) == cache.get(("camembert_ner", "candidate")))
        if language == "fr"
        else None
    )
    if language == "fr":
        before, after = cache["camembert_ner", "baseline"], cache["camembert_ner", "candidate"]
        report["migration_spans_equal"] = [[row[:3] for row in doc] for doc in before] == [
            [row[:3] for row in doc] for doc in after
        ]
        report["migration_final_equal"] = all(
            replay(
                doc.text,
                unpack(doc.text, base) + [d for d in unpack(doc.text, a) if d.score >= cut],
                language,
                threshold,
            )
            == replay(
                doc.text,
                unpack(doc.text, base) + [d for d in unpack(doc.text, b) if d.score >= cut],
                language,
                threshold,
            )
            for doc, base, a, b in zip(documents, baseline, before, after, strict=True)
            for cut in GRID
        )
    from huisclos.evaluation.metrics import EVALUATED_TYPES

    report["leakage_by_type"] = [
        {
            "config": r.name,
            "type": kind,
            **sum_counts(
                (
                    document_coverage(len(doc.text), doc.entities, masks, frozenset({kind}))
                    for doc, masks in zip(documents, r.substituted, strict=True)
                ),
                CoverageCounts(),
            ).scores(),
        }
        for r in runs
        for kind in EVALUATED_TYPES
    ]
    save(out / f"{language}_report.json", report)


def main() -> None:
    """Exécute tous les audits et conserve chaque défaut, sans le rendre artificiellement vert."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(ROOT):
        parser.error("Le rapport doit rester hors dépôt.")
    import socket

    from scripts.benchmark_post_g7_pii import refuse_network

    socket.socket.connect = refuse_network
    socket.create_connection = refuse_network
    socket.getaddrinfo = refuse_network
    results = {}
    for name, check in CASES.items():
        try:
            check()
            results[name] = {"passed": True}
        except AssertionError as error:
            results[name] = {"passed": False, "detail": str(error)}
    args.out.write_text(json.dumps(results, ensure_ascii=True, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=True))


if __name__ == "__main__":
    main()
