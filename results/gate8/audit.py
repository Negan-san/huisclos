"""Fige puis compare les littéraux sans exposer de contenu réservé.

Entrées : diff Git depuis G7 et fichiers de corpus lus uniquement par ce script.
Sorties : classification préalable, empreintes et comptes agrégés de recouvrement.
L'audit ne charge aucun détecteur et ne modifie aucune règle.
"""

import argparse
import ast
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = "422a2cd"
FREEZE = "dc5b04146c9217bdd09da5064091e0cf638f5b37"


def git(*arguments: str) -> str:
    """Lit uniquement l'historique Git demandé, en UTF-8."""
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def digest(path: Path) -> str:
    """Calcule une empreinte binaire sans afficher le fichier."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name: str, value: Any) -> None:
    """Crée un artefact neuf et refuse de remplacer un résultat existant."""
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=True, indent=2)
        handle.write("\n")


def classify() -> None:
    """Classe le diff avant toute lecture de corpus, selon le rôle syntaxique des valeurs.

    Toutes les formulations complètes non techniques restent candidates par prudence.
    Les identités en majuscules et courriels fictifs sont aussi isolés des fixtures.
    Une rencontre lexicale seule n'établit jamais une copie orientant une règle.
    """
    paths = git("diff", "--name-only", BASE, FREEZE, "--", "src", "tests").splitlines()
    previous = set()
    for path in git("ls-tree", "-r", "--name-only", BASE, "--", "src", "tests").splitlines():
        if path.endswith(".py"):
            previous.update(
                node.value
                for node in ast.walk(ast.parse(git("show", f"{BASE}:{path}")))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
            )
    rows = []
    for path in paths:
        if not path.endswith(".py"):
            continue
        source = git("show", f"{FREEZE}:{path}")
        changed = set()
        for line in git("diff", "--unified=0", BASE, FREEZE, "--", path).splitlines():
            match = re.match(r"@@ .* \+(\d+)(?:,(\d+))? @@", line)
            if match:
                start, count = int(match[1]), int(match[2] or 1)
                changed.update(range(start, start + count))
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            value = node.value.strip()
            if not value or not changed.intersection(range(node.lineno, node.end_lineno + 1)):
                continue
            if value in previous:
                category = "preexisting"
            elif "\\" in value or value.startswith(("(?", "^")):
                category = "generic_pattern"
            elif (
                len(value) < 16 or re.fullmatch(r"[A-Za-z0-9_.:/{} -]+", value) and " " not in value
            ):
                category = "generic_atomic_or_technical"
            else:
                category = "conservative_complete_candidate"
            rows.append({"path": path, "line": node.lineno, "value": value, "category": category})
            if path.startswith("tests/"):
                fragments = set(re.findall(r"\b[A-Z][A-Z'-]{4,}\b", value))
                fragments.update(re.findall(r"[\w.+-]+@example\.(?:org|com)", value))
                for fragment in sorted(fragments - previous):
                    if fragment not in {
                        "PERSON",
                        "ORGANIZATION",
                        "ADDRESS",
                        "EMAIL",
                        "PHONE",
                        "CUSTOM",
                        "LOCATION",
                        "BIRTH_DATE",
                        "CASE_NUMBER",
                    }:
                        rows.append(
                            {
                                "path": path,
                                "line": node.lineno,
                                "value": fragment,
                                "category": "conservative_fixture_fragment",
                            }
                        )
    save(
        "literal-classification.json",
        {
            "base": BASE,
            "freeze": FREEZE,
            "method": (
                "AST constants touching added lines; categories frozen before corpus comparison"
            ),
            "limitations": (
                "Generic short atoms and pattern syntax are classified by role; "
                "this is not a proof of authorship"
            ),
            "rows": rows,
        },
    )
    save(
        "literal-freeze.json",
        {
            "sha256": digest(OUT / "literal-classification.json"),
            "category_counts": dict(Counter(r["category"] for r in rows)),
        },
    )
    print("Literal classification frozen; no corpus read.")


def compare() -> None:
    """Compare la classification figée aux textes et annotations, avec comptes seulement."""
    frozen = json.loads((OUT / "literal-freeze.json").read_text(encoding="utf-8"))
    assert digest(OUT / "literal-classification.json") == frozen["sha256"]
    rows = json.loads((OUT / "literal-classification.json").read_text(encoding="utf-8"))["rows"]
    reports = {}
    paths = {
        "test": "corpus/test.jsonl",
        "challenge": "corpus/challenge.jsonl",
        "blind_fr": "corpus/blind_post_g7/fr/challenge.jsonl",
        "blind_en": "corpus/blind_post_g7/en/challenge.jsonl",
    }
    for split, relative in paths.items():
        documents = [
            json.loads(line)
            for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        texts = [doc["text"] for doc in documents]
        spans = [doc["text"][e["start"] : e["end"]] for doc in documents for e in doc["entities"]]
        counts = {}
        for category in sorted({row["category"] for row in rows}):
            values = {row["value"] for row in rows if row["category"] == category}
            counts[category] = {
                "values": len(values),
                "exact_text": sum(any(value in text for text in texts) for value in values),
                "folded_text": sum(
                    any(value.casefold() in text.casefold() for text in texts) for value in values
                ),
                "folded_annotation": sum(
                    any(value.casefold() in text.casefold() for text in spans) for value in values
                ),
            }
        reports[split] = {
            "documents": len(documents),
            "sha256": digest(ROOT / relative),
            "counts": counts,
        }
    save("literal-comparison.json", {"classification_sha256": frozen["sha256"], "splits": reports})
    print(json.dumps(reports, ensure_ascii=True))


def integrity() -> None:
    """Vérifie C3, les sources et les plans sans afficher identifiant ni contenu réservé."""
    assets = ROOT.parent / "pilotage/post_g7_assets"
    manifest_path = ROOT / "corpus/blind_post_g7/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["a4_freeze_commit"] == FREEZE
    assert (
        git(
            "diff",
            "--name-only",
            FREEZE,
            "HEAD",
            "--",
            "src",
            "app",
            "data",
            "requirements.txt",
            "requirements-enhanced-lock.txt",
        )
        == ""
    )
    corpus = {}
    for language, record in manifest["languages"].items():
        folder = manifest_path.parent
        assert digest(folder / record["path"]) == record["sha256"]
        for entry in record["documents"]:
            assert digest(folder / entry["source"]) == entry["sha256"]
        corpus[language] = {k: v for k, v in record.items() if k not in {"documents", "path"}}
    assert (
        digest(manifest_path.parent / manifest["conventions"]["path"])
        == manifest["conventions"]["sha256"]
    )
    plans = {}
    temporary_reference = assets / "benchmarks/G8/reference_g7"
    assert git("-C", str(temporary_reference), "rev-parse", "HEAD").strip().startswith(BASE)
    for language in ("fr", "en"):
        path = assets / f"benchmarks/A4/frozen_{language}.json"
        plan = json.loads(path.read_text(encoding="utf-8"))
        original_hash = digest(path)
        expected = {
            "fr": "7fd554ae608eb5e3231a9663ee7fe8f6b3303bfe42adb5e4559d2bc43ffbb453",
            "en": "ce2af6dec9f395b7c26ad5e924ba5b4762451d939a2aa749197585301708fdd1",
        }
        assert original_hash == expected[language]
        for profile in plan["profiles"].values():
            assert profile["threshold"] == 0.3
            if "checkout" in profile:
                profile["checkout"] = str(temporary_reference)
        save(f"plan_{language}.json", plan)
        plans[language] = {
            "a4_sha256": original_hash,
            "gate_sha256": digest(OUT / f"plan_{language}.json"),
        }
    save(
        "integrity.json",
        {
            "measured_commit": git("rev-parse", "HEAD").strip(),
            "freeze": FREEZE,
            "corpora": corpus,
            "plans": plans,
            "logic_unchanged_since_a4": True,
            "source_hashes_verified": 16,
            "temporary_reference": str(temporary_reference),
        },
    )
    print("Integrity verified; 16 sources and two frozen plans, no corpus content displayed.")


def main() -> None:
    """Exécute une étape indépendante ; la comparaison exige un gel déjà écrit."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("classify", "compare", "integrity"))
    action = parser.parse_args().action
    {"classify": classify, "compare": compare, "integrity": integrity}[action]()


if __name__ == "__main__":
    main()
