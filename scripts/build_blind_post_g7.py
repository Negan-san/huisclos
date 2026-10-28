"""Construit le lot bilingue réservé à partir de ses seules sources annotées.

Les entrées sont seize fichiers fictifs ; les sorties sont deux JSONL et un manifeste.
Les transformations et clés sont déterministes, sans détecteur ni appel réseau.
Ce constructeur reste séparé du pipeline métier et des anciens corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "corpus" / "blind_post_g7"
DATASET_ID = "post_g7_blind_v1"
CONVENTIONS = "post_g7_fr_en_1.0"
FREEZE = "dc5b04146c9217bdd09da5064091e0cf638f5b37"
TYPES = frozenset(
    "PERSON ORGANIZATION ADDRESS EMAIL PHONE IBAN NIR SIREN SIRET "
    "BIRTH_DATE CASE_NUMBER CUSTOM".split()
)
GENRES = tuple(
    "consultation correspondence instrument_draft summary "
    "correspondence summary consultation instrument_draft".split()
)
MARKER = re.compile(r"\{\{(SIREN|SIRET|NIR|IBAN)#([1-9][0-9]*)\}\}")


def require(condition: bool, code: str) -> None:
    """Vérifie une condition ; lève un code sans valeur du corpus en cas d'échec."""
    if not condition:
        raise ValueError(code)


def digest(content: bytes) -> str:
    """Retourne l'empreinte SHA-256 des octets fournis."""
    return hashlib.sha256(content).hexdigest()


def luhn(value: str) -> int:
    """Retourne le reste Luhn d'une chaîne de chiffres fournie."""
    digits = [int(char) for char in value]
    total = 0
    for index, digit in enumerate(reversed(digits)):
        doubled = digit * 2 if index % 2 else digit
        total += doubled // 10 + doubled % 10
    return total % 10


def keyed_digits(prefix: str) -> str:
    """Ajoute à un préfixe numérique la clé Luhn calculée localement."""
    return next(prefix + str(key) for key in range(10) if not luhn(prefix + str(key)))


def synthetic_value(document_id: str, kind: str, number: str) -> str:
    """Produit un identifiant fictif à clé à partir de son espace de noms et numéro."""
    seed = int(digest(f"{DATASET_ID}:{document_id}:{number}".encode()), 16)
    siren = keyed_digits(f"9{seed % 10_000_000:07d}")
    if kind == "SIREN":
        return siren
    if kind == "SIRET":
        return keyed_digits(siren + f"{seed % 9999 + 1:04d}")
    if kind == "NIR":
        base = f"2{seed % 80 + 10:02d}{seed % 12 + 1:02d}99"
        base += f"{seed % 900 + 100:03d}{seed % 999 + 1:03d}"
        return base + f"{97 - int(base) % 97:02d}"
    require(kind == "IBAN", "marker_kind")
    account = f"{seed % 10**23:023d}"
    key = 98 - int(account + "152700") % 97
    compact = f"FR{key:02d}{account}"
    return " ".join(compact[index : index + 4] for index in range(0, len(compact), 4))


def expand_markers(body: str, document_id: str) -> str:
    """Remplace les marqueurs à clés du corps et refuse tout marqueur inconnu."""
    expanded = MARKER.sub(lambda match: synthetic_value(document_id, match[1], match[2]), body)
    require("{{" not in expanded and "}}" not in expanded, "unknown_marker")
    return expanded


def parse_source(source: str, expected_id: str) -> dict[str, Any]:
    """Convertit une source en document ; refuse balisage, types ou en-tête invalides."""
    lines = source.splitlines(keepends=True)
    require(bool(lines) and lines[0] == "---\n", "header_start")
    closing = next((index for index in range(1, len(lines)) if lines[index] == "---\n"), 0)
    require(closing == 5, "header_size")
    header: dict[str, str] = {}
    for line in lines[1:closing]:
        key, separator, value = line.rstrip("\n").partition(": ")
        require(bool(separator) and bool(value.strip()) and key not in header, "header_field")
        header[key] = value
    require(set(header) == {"id", "doc_type", "split", "title"}, "header_keys")
    require(header["id"] == expected_id and header["split"] == "challenge", "identity_split")
    body = "".join(lines[closing + 1 :])
    pieces: list[str] = []
    entities: list[dict[str, Any]] = []
    cursor = position = 0
    while cursor < len(body):
        opening = body.find("[[", cursor)
        if opening < 0:
            pieces.append(body[cursor:])
            break
        prefix = body[cursor:opening]
        require("]]" not in prefix, "unmatched_close")
        pieces.append(prefix)
        position += len(prefix)
        closing = body.find("]]", opening + 2)
        require(closing >= 0, "unmatched_open")
        annotation = body[opening + 2 : closing]
        require("[[" not in annotation and annotation.count("|") == 1, "annotation_syntax")
        value, kind = annotation.split("|")
        require(
            bool(value.strip()) and value == value.strip() and kind in TYPES,
            "annotation_value_type",
        )
        if "{{" in value or "}}" in value:
            marker = MARKER.fullmatch(value)
            require(marker is not None and marker[1] == kind, "marker_type")
            value = expand_markers(value, expected_id)
        entities.append(
            {"start": position, "end": position + len(value), "type": kind, "text": value}
        )
        pieces.append(value)
        position += len(value)
        cursor = closing + 2
    text = "".join(pieces)
    require(
        all(token not in text for token in ("[[", "]]", "{{", "}}")) and bool(text.strip()),
        "residual_markup",
    )
    document: dict[str, Any] = {**header, "text": text, "entities": entities}
    validate_document(document)
    return document


def validate_document(document: dict[str, Any]) -> None:
    """Vérifie les tranches exactes, l'ordre, les répétitions et les contacts du document."""
    text = document["text"]
    previous_end = 0
    for entity in document["entities"]:
        start, end, kind, value = (entity[key] for key in ("start", "end", "type", "text"))
        require(type(start) is int and type(end) is int, "offset_type")
        require(previous_end <= start < end <= len(text), "offset_range")
        require(kind in TYPES and text[start:end] == value, "exact_slice")
        previous_end = end
        if kind == "EMAIL":
            require(
                re.fullmatch(r"[A-Za-z0-9_.+-]+@example\.(com|org)", value) is not None,
                "email_domain",
            )
        for match in re.finditer(r"(?<!\w)" + re.escape(value) + r"(?!\w)", text):
            require(
                any(
                    other["start"] <= match.start()
                    and match.end() <= other["end"]
                    and other["type"] == kind
                    for other in document["entities"]
                ),
                "unannotated_repeat",
            )
    for match in re.finditer(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b", text):
        require(
            any(
                entity["type"] == "EMAIL"
                and entity["start"] == match.start()
                and entity["end"] == match.end()
                for entity in document["entities"]
            ),
            "unannotated_email",
        )


def serialise(value: Any, *, lines: bool = False) -> bytes:
    """Sérialise une valeur en UTF-8 et LF, en JSON ou en lignes JSON déterministes."""
    if lines:
        content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in value)
    else:
        content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    return content.encode("utf-8")


def build_outputs(sources: dict[str, str], conventions: bytes) -> dict[str, bytes]:
    """Construit les trois sorties depuis les seules entrées fournies, sans effet de bord."""
    manifest: dict[str, Any] = {
        "dataset_id": DATASET_ID,
        "split": "challenge",
        "a4_freeze_commit": FREEZE,
        "authored_on": "2026-10-28",
        "author": "Codex, fresh C3 session, single model-family author",
        "method": (
            "Fictional authoring after freeze; editorial second pass; no detector or measurement"
        ),
        "conventions": {"version": CONVENTIONS, "path": "README.md", "sha256": digest(conventions)},
        "reserved_for": ["C3 authoring", "explicitly authorised gate scripts"],
        "limitations": [
            "Single author and model-family style dependence",
            "No statistical independence claim",
            "Editorial completeness is not proven",
            "Synthetic keys may coincide with assigned numbers",
            "No isolated LOCATION or foreign national identifier coverage",
        ],
        "languages": {},
    }
    outputs: dict[str, bytes] = {}
    seen: dict[tuple[str, str], str] = {}
    expected_paths: set[str] = set()
    for language in ("fr", "en"):
        documents = []
        entries = []
        counts: Counter[str] = Counter()
        for index, genre in enumerate(GENRES, 1):
            document_id = f"aud_{language}_{index:02d}"
            path = f"{language}/source/{document_id}.md"
            expected_paths.add(path)
            require(path in sources, "missing_source")
            source = sources[path]
            document = parse_source(source, document_id)
            require(document["doc_type"] == genre, "genre")
            words = len(document["text"].split())
            minimum, maximum = (250, 450) if index <= 6 else (800, 1200)
            require(minimum <= words <= maximum, f"word_count_{document_id}_{words}")
            local_counts = Counter(entity["type"] for entity in document["entities"])
            counts.update(local_counts)
            for entity in document["entities"]:
                key = entity["type"], entity["text"].casefold()
                require(key not in seen or seen[key] == document_id, "cross_document_identity")
                seen[key] = document_id
            entries.append(
                {
                    "id": document_id,
                    "genre": genre,
                    "source": path,
                    "sha256": digest(source.encode("utf-8")),
                    "words": words,
                    "characters": len(document["text"]),
                    "entities": len(document["entities"]),
                    "entity_counts": dict(sorted(local_counts.items())),
                }
            )
            documents.append(document)
        require(set(counts) == TYPES, "language_type_coverage")
        output_path = f"{language}/challenge.jsonl"
        outputs[output_path] = serialise(documents, lines=True)
        manifest["languages"][language] = {
            "language": language,
            "path": output_path,
            "sha256": digest(outputs[output_path]),
            "document_count": len(documents),
            "entity_count": sum(counts.values()),
            "character_count": sum(entry["characters"] for entry in entries),
            "word_count": sum(entry["words"] for entry in entries),
            "genre_counts": dict(sorted(Counter(GENRES).items())),
            "entity_counts": dict(sorted(counts.items())),
            "documents": entries,
        }
    require(set(sources) == expected_paths, "unexpected_source")
    manifest["document_count"] = 16
    manifest["entity_count"] = sum(item["entity_count"] for item in manifest["languages"].values())
    manifest["character_count"] = sum(
        item["character_count"] for item in manifest["languages"].values()
    )
    outputs["manifest.json"] = serialise(manifest)
    return outputs


def self_test() -> int:
    """Teste les cas valides et invalides en mémoire ; retourne le nombre de vérifications."""
    header = "---\nid: unit\ndoc_type: summary\nsplit: challenge\ntitle: Essai\n---\n"
    source = (
        header + "Mme [[Zo\u00e9 VIRE|PERSON]] : [[12 rue X\nVille|ADDRESS]]. [[VIRE|PERSON]].\n"
    )
    document = parse_source(source, "unit")
    require(len(document["entities"]) == 3 and document["text"].endswith("VIRE.\n"), "test_unicode")
    invalid = [
        "[[x|UNKNOWN]]",
        "[[|PERSON]]",
        "[[a [[b|PERSON]]|PERSON]]",
        "[[x|PERSON",
        "x]]",
        "[[x|PERSON]] x",
        "{{BAD}}",
        "[[x@invalid.net|EMAIL]]",
        "[[x|PERSON|EMAIL]]",
        "[[ x|PERSON]]",
        "[[{{NIR#1}}|PHONE]]",
        "{{NIR#1}}",
    ]
    for body in invalid:
        try:
            parse_source(header + body, "unit")
        except ValueError:
            continue
        raise ValueError("test_invalid_accepted")
    for invalid_header in (
        header.replace("id: unit", "id: other"),
        header.replace("title: Essai", "id: unit"),
        header.replace("split: challenge", "split: dev"),
    ):
        try:
            parse_source(invalid_header + "Texte", "unit")
        except ValueError:
            continue
        raise ValueError("test_header_accepted")
    for kind in ("SIREN", "SIRET", "NIR", "IBAN"):
        value = synthetic_value("unit", kind, "1")
        compact = value.replace(" ", "")
        if kind in {"SIREN", "SIRET"}:
            require(luhn(compact) == 0, "test_luhn")
        elif kind == "NIR":
            require(
                len(compact) == 15 and int(compact[-2:]) == 97 - int(compact[:-2]) % 97, "test_nir"
            )
        else:
            require(
                len(compact) == 27 and int(compact[4:] + "1527" + compact[2:4]) % 97 == 1,
                "test_iban",
            )
        repeated = parse_source(
            header + f"[[{{{{{kind}#1}}}}|{kind}]] [[{{{{{kind}#1}}}}|{kind}]]", "unit"
        )
        require(repeated["entities"][0]["text"] == repeated["entities"][1]["text"], "test_repeat")
    require(
        synthetic_value("unit", "SIRET", "1").startswith(synthetic_value("unit", "SIREN", "1")),
        "test_link",
    )
    require(
        synthetic_value("unit", "NIR", "1") != synthetic_value("other", "NIR", "1"),
        "test_namespace",
    )
    email = parse_source(header + "[[x@example.org|EMAIL]].", "unit")
    require(email["text"].endswith("org" + "."), "test_email_punctuation")
    return 27


def main() -> int:
    """Exécute les arguments de construction ou de contrôle ; retourne le code de sortie."""
    parser = argparse.ArgumentParser(description="Construction locale du lot réservé C3.")
    parser.add_argument("--check", action="store_true", help="Comparer sans écrire.")
    parser.add_argument(
        "--self-test", action="store_true", help="Tester uniquement des exemples en mémoire."
    )
    arguments = parser.parse_args()
    try:
        if arguments.self_test:
            print(f"Contrôles en mémoire : {self_test()} vérifications réussies.")
            return 0
        sources = {
            f"{language}/source/aud_{language}_{index:02d}.md": (
                DATASET / language / "source" / f"aud_{language}_{index:02d}.md"
            ).read_text(encoding="utf-8")
            for language in ("fr", "en")
            for index in range(1, 9)
        }
        outputs = build_outputs(sources, (DATASET / "README.md").read_bytes())
        for relative, content in outputs.items():
            path = DATASET / relative
            if arguments.check:
                require(path.is_file() and path.read_bytes() == content, "output_mismatch")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        manifest = json.loads(outputs["manifest.json"])
        for language, metadata in manifest["languages"].items():
            print(
                f"{language} : {metadata['document_count']} documents, "
                f"{metadata['entity_count']} entités, "
                f"{metadata['character_count']} caractères, {metadata['word_count']} mots."
            )
        print("Contrôle déterministe réussi." if arguments.check else "Construction terminée.")
    except (ValueError, OSError) as error:
        code = str(error) if isinstance(error, ValueError) else "file_access"
        print(f"Construction refusée : {code}.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
