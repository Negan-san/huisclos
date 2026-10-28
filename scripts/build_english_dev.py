"""Construit le jeu de développement anglais sans appeler de détecteur.

Entrées : huit sources anglaises fictives annotées dans un dossier séparé.
Sorties : JSONL compatible avec le corpus et manifeste de provenance déterministe.
Les fonctions de construction sont pures ; seule la commande écrit les fichiers.
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[1] / "corpus" / "english_dev"
DATASET_ID = "english_dev_v1"
TYPES = frozenset(
    {
        "PERSON",
        "ORGANIZATION",
        "ADDRESS",
        "EMAIL",
        "PHONE",
        "IBAN",
        "NIR",
        "SIREN",
        "SIRET",
        "BIRTH_DATE",
        "CASE_NUMBER",
        "LOCATION",
        "CUSTOM",
    }
)
GENRES = {
    "employment_correspondence",
    "commercial_agreement",
    "case_memorandum",
    "management_minutes",
}
MARKER = re.compile(r"\[\[([^\[\]|]+)\|([A-Z_]+)\]\]")


class Annotation(TypedDict):
    """Associe une valeur au type existant et à ses positions Unicode dans le texte."""

    start: int
    end: int
    type: str
    text: str


class Document(TypedDict):
    """Décrit une ligne dev selon les six champs du schéma de corpus existant."""

    id: str
    doc_type: str
    split: str
    title: str
    text: str
    entities: list[Annotation]


def parse_source(source: str) -> Document:
    """Retire les annotations reçues et valide les offsets, sans détection automatique.

    Les en-têtes sont ceux du corpus existant. Une annotation mal formée, un type
    inconnu ou une occurrence répétée laissée sans annotation provoque un refus.
    """
    lines = source.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)
    if not lines or lines[0] != "---\n":
        raise ValueError("En-tête absent")
    header: dict[str, str] = {}
    end = 1
    while end < len(lines) and lines[end].rstrip("\n") != "---":
        key, separator, value = lines[end].rstrip("\n").partition(": ")
        if not separator or key in header or not value.strip():
            raise ValueError("Champ d'en-tête invalide")
        header[key] = value
        end += 1
    if end == len(lines) or set(header) != {"id", "doc_type", "split", "title"}:
        raise ValueError("En-tête incomplet")
    if header["split"] != "dev" or header["doc_type"] not in GENRES:
        raise ValueError("Split ou genre invalide")
    body = "".join(lines[end + 1 :])
    text_parts: list[str] = []
    entities: list[Annotation] = []
    cursor = 0
    length = 0
    for marker in MARKER.finditer(body):
        before = body[cursor : marker.start()]
        value, kind = marker.groups()
        if kind not in TYPES or not value.strip() or value != value.strip():
            raise ValueError("Type ou valeur d'annotation invalide")
        text_parts.extend((before, value))
        start = length + len(before)
        entities.append({"start": start, "end": start + len(value), "type": kind, "text": value})
        length = start + len(value)
        cursor = marker.end()
    text_parts.append(body[cursor:])
    text = "".join(text_parts)
    if "[[" in text or "]]" in text or not text.strip() or not entities:
        raise ValueError("Annotation mal formée ou corps vide")
    _validate_occurrences(text, entities)
    return Document(
        id=header["id"],
        doc_type=header["doc_type"],
        split="dev",
        title=header["title"],
        text=text,
        entities=entities,
    )


def _validate_occurrences(text: str, entities: list[Annotation]) -> None:
    """Vérifie les tranches exactes et les répétitions connues hors des spans annotés."""
    masked = list(text)
    previous_end = 0
    for entity in entities:
        start, end = entity["start"], entity["end"]
        if start < previous_end or text[start:end] != entity["text"] or start >= end:
            raise ValueError("Positions invalides ou chevauchantes")
        masked[start:end] = " " * (end - start)
        previous_end = end
        if entity["type"] == "EMAIL" and entity["text"].rsplit("@", 1)[-1] not in {
            "example.com",
            "example.org",
        }:
            raise ValueError("Domaine de courriel non fictif")
    remaining = "".join(masked)
    for value in {entity["text"] for entity in entities}:
        if re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", remaining, re.IGNORECASE):
            raise ValueError("Occurrence connue sans annotation")


def build_dataset(sources: Mapping[str, str]) -> tuple[str, str]:
    """Renvoie JSONL et manifeste reproductibles depuis les huit sources reçues.

    Les comptes de mots portent sur le texte sans balises. Le manifeste décrit les
    formats présents et les limites ; aucune métrique de détection n'est calculée.
    """
    expected = {f"en_dev_{number:02}.md" for number in range(1, 9)}
    if set(sources) != expected:
        raise ValueError("Huit sources en_dev_01.md à en_dev_08.md sont requises")
    documents: list[Document] = []
    provenance: list[dict[str, object]] = []
    for filename, source in sorted(sources.items()):
        try:
            document = parse_source(source)
            word_count = len(document["text"].split())
            if document["id"] != Path(filename).stem or not 250 <= word_count <= 450:
                raise ValueError("Identifiant ou nombre de mots invalide")
        except ValueError as error:
            raise ValueError(f"{filename}: {error}") from None
        documents.append(document)
        provenance.append(
            {
                "id": document["id"],
                "source": f"source/{filename}",
                "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                "word_count": word_count,
                "entity_count": len(document["entities"]),
                "doc_type": document["doc_type"],
            }
        )
    genres = Counter(document["doc_type"] for document in documents)
    if genres != Counter(dict.fromkeys(GENRES, 2)):
        raise ValueError("Deux documents de chacun des quatre genres sont requis")
    jsonl = "".join(json.dumps(document, ensure_ascii=False) + "\n" for document in documents)
    manifest = {
        "dataset_id": DATASET_ID,
        "language": "en",
        "split": "dev",
        "fictional": True,
        "purpose": "Development and tuning before freeze; not blind validation.",
        "jurisdiction": "Language does not determine country: US, UK and French case contexts.",
        "licence": "CC-BY-4.0",
        "document_count": len(documents),
        "entity_count": sum(len(document["entities"]) for document in documents),
        "entity_counts": dict(
            sorted(
                Counter(
                    entity["type"] for document in documents for entity in document["entities"]
                ).items()
            )
        ),
        "jsonl_sha256": hashlib.sha256(jsonl.encode("utf-8")).hexdigest(),
        "conventions": {
            "offsets": (
                "Python Unicode characters, start inclusive, end exclusive; exact text slice."
            ),
            "occurrences": "Every sensitive occurrence; no nested or overlapping annotations.",
            "persons": "Titles outside spans; full names, initials and shortened repeats included.",
            "organizations": "Attached legal form inside the span; public institutions excluded.",
            "addresses": "Whole address, including unit, locality, postcode/state and line breaks.",
            "dates": "Birth dates only; ordinary event dates and public legal references excluded.",
            "case_numbers": "Private case references annotated; labels outside spans.",
            "email": "Only example.com and example.org.",
            "foreign_identifiers": (
                "No SSN, UK NIN or invented foreign social-security entity type."
            ),
        },
        "formats_present": {
            "addresses": [
                "US street/unit/city/state/ZIP",
                "UK street/city/postcode",
                "French street/postcode/city",
            ],
            "phones": ["US +1 and domestic", "UK +44 and domestic", "French +33"],
            "birth_dates": ["DD Month YYYY", "Month DD, YYYY", "DD/MM/YYYY", "YYYY-MM-DD"],
            "private_cases": [
                "US civil docket style",
                "UK alphanumeric case reference",
                "French RG",
            ],
            "french_identifiers": ["IBAN FR", "NIR", "SIREN", "SIRET"],
            "custom": ["Labelled internal employee and supplier identifiers"],
        },
        "limits": [
            "One author; small fictional development set; no independent validation claim.",
            "Builder validates syntax, offsets and known repeats, "
            "not semantic annotation exhaustiveness.",
            "Formats present describe annotations, not a claim of detector support.",
            "Synthetic identifiers and addresses may coincide accidentally; "
            "never contact or transact.",
        ],
        "documents": provenance,
    }
    return jsonl, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    """Construit les seuls fichiers anglais, ou vérifie leur conformité sans écriture."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        sources = {
            path.name: path.read_text(encoding="utf-8") for path in (ROOT / "source").glob("*.md")
        }
        jsonl, manifest = build_dataset(sources)
        outputs = {"dev.jsonl": jsonl, "manifest.json": manifest}
        for name, content in outputs.items():
            path = ROOT / name
            if args.check:
                if not path.exists() or path.read_bytes() != content.encode("utf-8"):
                    raise ValueError(f"{name}: reconstruction nécessaire")
            else:
                path.write_text(content, encoding="utf-8", newline="\n")
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print("English dev: 8 documents validés ; offsets et manifeste conformes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
