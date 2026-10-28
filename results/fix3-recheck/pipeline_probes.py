"""Recontrôle FIX3 sur des documents entièrement fictifs et nouveaux.

Entrées : fixtures ci-dessous et vrais profils Standard FR et EN, hors ligne.
Sorties : booléens et comptes, sans texte, mention ni position exportée.
La restauration et l'ordre des détections sont contrôlés après la détection réelle.
"""

import itertools
import random
import re
from typing import Any

import pytest
from presidio_anonymizer.entities import EngineResult, OperatorResult

from huisclos.config import profile_config
from huisclos.detection.pipeline import detect
from huisclos.models import TOKEN_LABELS, Detection, EntityType, Source, TokenStyle
from huisclos.pseudonymize import tokens
from huisclos.pseudonymize.case_memory import find_known, read_table_file
from huisclos.pseudonymize.reidentify import EXACT, TOLERANT, restore

FIXED = "2026-10-28T21:00:00+00:00"


def run(text: str, language: str, known: Any = None, style: str = "fr") -> tuple[Any, list]:
    """Détecte avec Standard puis pseudonymise, avec une éventuelle table chargée en mémoire."""
    config = profile_config("standard", language)
    detections = detect(text, config, known=find_known(text, known) if known else ())
    result = tokens.pseudonymize(
        text, detections, TokenStyle(language=style), known=known, created_at=FIXED
    )
    return result, detections


def verify(
    text: str,
    language: str,
    values: tuple[str, ...],
    expected: int,
    known: Any = None,
    style: str = "fr",
) -> tuple[dict, Any]:
    """Vérifie couverture, occurrences, restauration exacte et permutations, sans rien révéler."""
    result, detections = run(text, language, known, style)
    restored = restore(result.text, result.mapping)
    orderings = list(itertools.permutations(detections)) if len(detections) <= 5 else []
    if not orderings:
        rng = random.Random(313)
        orderings = [tuple(detections), tuple(reversed(detections))]
        for _ in range(20):
            orderings.append(tuple(rng.sample(detections, len(detections))))
    deterministic = all(
        tokens.pseudonymize(text, order, TokenStyle(language=style), known=known, created_at=FIXED)
        == result
        for order in orderings
    )
    checks = {
        "original_values_absent": all(value not in result.text for value in values),
        "exact_restore": restored.text == text and restored.mode == EXACT,
        "occurrence_count": len(result.occurrences) == len(detections) == expected,
        "occurrences_aligned": all(
            o.original == d.text and result.text[o.start : o.end] == o.token
            for o, d in zip(result.occurrences, detections, strict=True)
        ),
        "deterministic": deterministic,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "orders": len(orderings),
        "detections": len(detections),
        "expected": expected,
        "groups": len(result.groups),
        "language": language,
        "token_style": style,
    }, result


def fixtures(language: str) -> list[tuple[str, str, tuple[str, ...], int]]:
    """Définit sept formes nouvelles et trois témoins par langue, avant toute mesure."""
    if language == "fr":
        name, title, first = "ZELVORIEN", "M.", "Abel"
        stem, company, alias = "demande", "Talverne Transit SAS", "TTX"
        organization = f'La société {company} (ci-après "{alias}") signe.'
    else:
        name, title, first = "QUERNAVICK", "Mr", "Orin"
        stem, company, alias = "schedule", "Velsora Freight Ltd", "VFL"
        organization = f'{company} (hereinafter "{alias}") signs.'
    main = f"{title} {first} {name} signe. {title} {name} confirme."
    file_text = f"{main} {stem}_{name}.pdf."
    return [
        ("text-file", file_text, (first, name), 3),
        ("acronym-file", f"{organization} {stem}_{alias}_2026.pdf.", (company, alias), 3),
        ("two-files", f"note_{first}_{name}.pdf ; lettre_{first}_{name}.docx.", (first, name), 2),
        ("file-only", f"note_{first}_{name}.pdf.", (first, name), 1),
        ("adjacent", "case47@example.com case91@example.org", ("case47@", "case91@"), 2),
        ("english-tokens", file_text, (first, name), 3),
        ("known", file_text, (first, name), 3),
        ("control-person", main, (first, name), 2),
        ("control-org", organization, (company, alias), 2),
        ("control-email", "case62@example.org", ("case62@",), 1),
        ("numeric-suffix", f"{main} {stem}_{name}_47.pdf.", (first, name), 3),
    ]


def matrix() -> dict:
    """Exécute vingt-deux cas et distingue les contrats des observations de spans du NER."""
    rows = {}
    for language in ("fr", "en"):
        seed = fixtures(language)[7][1]
        known = read_table_file(run(seed, language)[0].mapping.to_json().encode("utf-8"))
        for label, text, values, count in fixtures(language):
            row, result = verify(
                text,
                language,
                values,
                count,
                known if label == "known" else None,
                "en" if label == "english-tokens" else "fr",
            )
            if label in {"text-file", "english-tokens", "acronym-file", "two-files"}:
                row["checks"]["separate_file_token"] = len(result.groups) == 2
            if label == "english-tokens":
                row["checks"]["english_labels"] = all(
                    TOKEN_LABELS[entry.entity_type][1] in entry.token
                    for entry in result.mapping.entities
                )
            if label == "known":
                row["checks"]["loaded_token_reused"] = (
                    result.occurrences[0].token == known.entities[0].token
                )
            if label == "numeric-suffix":
                row["same_original_distinct_tokens_observed"] = (
                    result.occurrences[1].original == result.occurrences[-1].original
                    and result.occurrences[1].token != result.occurrences[-1].token
                )
            row["passed"] = all(row["checks"].values())
            rows[f"{language}-{label}"] = row
    return rows


def memory() -> dict:
    """Isole la mémoire par mentions automatiques contrôlées, indépendamment du NER."""
    rows = {}
    for language, first, second, name, title in (
        ("fr", "Azel", "Nola", "VELQUERAC", "M."),
        ("en", "Oren", "Mira", "ZURTHERICK", "Mr"),
    ):

        def reviewed(
            value: str,
            known: Any = None,
            fragments: tuple[str, ...] = (f"{first} {name}", f"{second} {name}", name),
        ) -> tuple[Any, list]:
            """Fournit les spans attendus pour isoler D-FIX3-2 des différences de NER."""
            pattern = "|".join(re.escape(fragment) for fragment in fragments)
            detections = [
                Detection(m.start(), m.end(), EntityType.PERSON, 0.9, Source.PROPAGATION, m.group())
                for m in re.finditer(pattern, value)
            ]
            return tokens.pseudonymize(value, detections, known=known, created_at=FIXED), detections

        text = f"{title} {first} {name} signe. {title} {name} répond. preuve_{name}.pdf."
        original, _ = reviewed(text)
        table = read_table_file(original.mapping.to_json().encode("utf-8"))
        full, _ = reviewed(f"{title} {first} {name} signe.", table)
        alone_text = f"{title} {name} répond."
        alone, _ = reviewed(alone_text, table)
        third_text = f"{title} {second} {name} signe."
        distinct, _ = reviewed(third_text, alone.mapping)
        mixed = " / ".join(
            o.token
            for o in (original.occurrences[0], alone.occurrences[0], distinct.occurrences[0])
        )
        restored = restore(mixed, distinct.mapping)
        both_text = (
            f"{title} {first} {name} signe. {title} {second} {name} répond. preuve_{name}.pdf."
        )
        both, _ = reviewed(both_text)
        checks = {
            "two_entries_share_spelling": sum(
                name in (e.canonical, *e.variants) for e in table.entities
            )
            == 2,
            "full_name_keeps_token": full.occurrences[0].token == original.occurrences[0].token,
            "surname_gets_new_token": alone.occurrences[0].token
            not in {e.token for e in table.entities},
            "distinct_people_distinct_tokens": distinct.occurrences[0].token
            != original.occurrences[0].token,
            "same_document_no_confusion": len({o.token for o in both.occurrences}) == 3,
            "mixed_tolerant": restored.mode == TOLERANT
            and not restored.unknown
            and restored.text == f"{first} {name} / {name} / {second} {name}",
            "exact_both": restore(both.text, both.mapping).text == both_text,
            "no_leak": all(name not in r.text for r in (original, alone, distinct, both)),
        }
        rows[language] = {
            "checks": checks,
            "passed": all(checks.values()),
            "method": "controlled_automatic_detections",
        }
    return rows


class ForgedEngine:
    """Fournit une réponse Presidio contrôlée pour tester les refus de D-S21-1."""

    def __init__(self, mode: str, engine: Any) -> None:
        """Conserve le moteur réel pour falsifier uniquement sa sortie finale."""
        self.mode, self.engine, self.merge_disabled = mode, engine, False

    def anonymize(self, **kwargs: Any) -> EngineResult:
        """Supprime un élément ou corrompt le jeton, sans toucher aux détections."""
        self.merge_disabled = kwargs["merge_entities_with_spaces"] is False
        result = self.engine.anonymize(**kwargs)
        if self.mode == "missing":
            return EngineResult(result.text, result.items[:-1])
        item = result.items[0]
        wrong = OperatorResult(item.start, item.end, item.entity_type, "[PERSONNE_999]", "replace")
        return EngineResult(result.text, [wrong, *result.items[1:]])


def invariants() -> dict:
    """Injecte les deux sorties falsifiées demandées par monkeypatch et vérifie RuntimeError."""
    from scripts import gate8_measure

    text = "M. Izel NERQUAVAL signe."
    _, detections = run(text, "fr")
    real, rows = tokens._engine(), {}
    for mode in ("missing", "wrong-token"):
        fake = ForgedEngine(mode, real)
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(tokens, "_engine", lambda engine=fake: engine)
            try:
                tokens.pseudonymize(text, detections)
            except RuntimeError as error:
                site = gate8_measure.code_location(error)
                rows[mode] = {
                    "runtime_error": True,
                    "merge_disabled": fake.merge_disabled,
                    "site": site,
                    "current_function_located": site["function"] == "_substitute",
                }
            else:
                rows[mode] = {"runtime_error": False, "merge_disabled": fake.merge_disabled}
    return rows
