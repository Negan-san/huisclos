"""Construit le corpus de référence à partir des sources Markdown annotées.

Entrées : sources fictives, marqueurs et options de ligne de commande.
Sorties : JSONL et statistiques déterministes, ou simple validation.
Ce script prépare l'évaluation locale sans afficher le contenu des documents.
"""

import argparse
import json
import random
import re
import sys
import zlib
from collections import Counter
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from huisclos.detection import checksums  # noqa: E402
from huisclos.evaluation import synthetic_ids as ids  # noqa: E402
from huisclos.evaluation.corpus import (  # noqa: E402
    CORPUS_TYPES,
    SPLITS,
    CorpusDocument,
    GoldEntity,
)

HEADER_KEYS = frozenset({"id", "doc_type", "split", "title"})
MARKERS = re.compile(r"\{\{([^{}]*?)\}\}|(\{\{|\}\})")
ANNOTATIONS = re.compile(r"\[\[|\]\]")


def _fail(path: Path, source: str, offset: int, problem: str) -> ValueError:
    """Localise problem dans source et renvoie une erreur fichier:ligne."""
    return ValueError(f"{path}:{source.count(chr(10), 0, offset) + 1}: {problem}")


def _header(path: Path, source: str) -> tuple[dict[str, str], int]:
    """Lit l'en-tête de source et renvoie ses champs et le début du corps."""
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise _fail(path, source, 0, "En-tête absent : ligne --- attendue.")
    metadata: dict[str, str] = {}
    offset = len(lines[0])
    for line in lines[1:]:
        if line.rstrip("\r\n") == "---":
            if metadata.keys() != HEADER_KEYS:
                raise _fail(path, source, offset, "En-tête incomplet.")
            return metadata, offset + len(line)
        key, separator, value = line.rstrip("\r\n").partition(":")
        value = value.strip()
        if not separator or key not in HEADER_KEYS or key in metadata or not value:
            raise _fail(path, source, offset, "Champ d'en-tête inconnu, vide ou répété.")
        if key == "split" and value not in SPLITS:
            raise _fail(path, source, offset, "Split inconnu.")
        metadata[key] = value
        offset += len(line)
    raise _fail(path, source, offset, "En-tête non fermé.")


def _identifier(marker: str, rng: random.Random, companies: dict[str, str]) -> str:
    """Génère marker avec rng ; companies conserve les liens SIREN/SIRET locaux."""
    company_match = re.fullmatch(r"(SIREN|SIRET)#([1-9][0-9]*)", marker)
    if company_match:
        kind, index = company_match.groups()
        if index not in companies:
            companies[index] = ids.make_siren(rng)
        if kind == "SIREN":
            return ids.format_siren(companies[index])
        return ids.format_siret(ids.make_siret(rng, siren=companies[index]))
    match marker:
        case "NIR" | "NIR_2A" | "NIR_BADKEY":
            return ids.format_nir(
                ids.make_nir(
                    rng, valid=marker != "NIR_BADKEY", corsica="2A" if marker == "NIR_2A" else None
                )
            )
        case "IBAN" | "IBAN_BADKEY":
            return ids.format_iban(ids.make_iban_fr(rng, valid=marker == "IBAN"))
        case "SIREN_BADKEY" | "DIGITS9":
            value = ids.make_siren(rng, valid=False)
            return value if marker == "DIGITS9" else ids.format_siren(value)
        case "PHONE_MOBILE" | "PHONE_FIXE":
            return ids.format_phone(ids.make_phone_fr(rng, mobile=marker == "PHONE_MOBILE"))
        case _:
            raise ValueError("Marqueur inconnu.")


def _validate_identifier(marker: str, value: str) -> None:
    """Vérifie value selon la famille et la validité annoncées par marker."""
    if marker.startswith("NIR"):
        valid = checksums.nir_is_valid(value)
    elif marker.startswith("IBAN"):
        valid = checksums.iban_is_valid(value)
    elif marker.startswith("SIREN") or marker == "DIGITS9":
        valid = checksums.siren_is_valid(value)
    elif marker.startswith("SIRET"):
        valid = checksums.siret_is_valid(value)
    else:
        if not re.fullmatch(
            r"0[67][0-9]{8}" if marker == "PHONE_MOBILE" else r"0[1-5][0-9]{8}",
            checksums.digits_only(value),
        ):
            raise ValueError("Téléphone généré invalide.")
        return
    expected = not (marker.endswith("_BADKEY") or marker == "DIGITS9")
    if valid != expected:
        raise ValueError("La clé générée ne respecte pas le marqueur.")


def _replace_markers(path: Path, source: str, body_start: int, identifier: str) -> str:
    """Remplace les marqueurs du corps, avec une graine stable propre à identifier."""
    rng = random.Random(zlib.crc32(identifier.encode("utf-8")))
    companies: dict[str, str] = {}
    values: dict[str, str] = {}
    body = source[body_start:]

    def replace(match: re.Match[str]) -> str:
        """Renvoie la valeur du marqueur match ou signale sa ligne source."""
        marker = match.group(1)
        try:
            if marker is None:
                raise ValueError("Marqueur non équilibré.")
            prefix = body[: match.start()]
            if marker == "DIGITS9" and prefix.rfind("[[") > prefix.rfind("]]"):
                raise ValueError("DIGITS9 doit rester hors annotation.")
            if marker not in values:
                values[marker] = _identifier(marker, rng, companies)
            _validate_identifier(marker, values[marker])
            return values[marker]
        except ValueError as error:
            raise _fail(path, source, body_start + match.start(), str(error)) from error

    return MARKERS.sub(replace, body)


def parse_source(path: str | Path) -> CorpusDocument:
    """Construit un document depuis path, en calculant les spans après substitution."""
    path = Path(path)
    source = path.read_text(encoding="utf-8")
    metadata, body_start = _header(path, source)
    body = _replace_markers(path, source, body_start, metadata["id"])
    # Les substitutions ne changent pas les sauts de ligne : la localisation reste exacte.
    expanded = source[:body_start] + body
    pieces: list[str] = []
    entities: list[GoldEntity] = []
    opening: int | None = None
    cursor = 0
    length = 0
    for match in ANNOTATIONS.finditer(body):
        offset = body_start + match.start()
        if match.group() == "[[":
            if opening is not None:
                raise _fail(path, expanded, offset, "Balisage imbriqué interdit.")
            piece = body[cursor : match.start()]
            pieces.append(piece)
            length += len(piece)
            opening = match.end()
        else:
            if opening is None:
                raise _fail(path, expanded, offset, "Fermeture sans ouverture.")
            annotation = body[opening : match.start()]
            value, separator, kind = annotation.rpartition("|")
            if not separator or not value or "|" in value:
                raise _fail(path, expanded, offset, "Annotation attendue : [[valeur|TYPE]].")
            if kind not in CORPUS_TYPES:
                raise _fail(path, expanded, offset, "Type d'entité inconnu.")
            entities.append(GoldEntity(length, length + len(value), kind, value))
            pieces.append(value)
            length += len(value)
            opening = None
            cursor = match.end()
    if opening is not None:
        raise _fail(path, expanded, body_start + opening - 2, "Annotation non fermée.")
    pieces.append(body[cursor:])
    return CorpusDocument(**metadata, text="".join(pieces), entities=entities)


def _statistics(documents: list[CorpusDocument]) -> str:
    """Renvoie les effectifs de documents et d'entités par split et par type."""
    lines = ["# Corpus statistics", "", "| Split | Documents | Entities |", "| --- | ---: | ---: |"]
    counts = Counter((doc.split, entity.type) for doc in documents for entity in doc.entities)
    for split in sorted(SPLITS):
        selected = [doc for doc in documents if doc.split == split]
        lines.append(
            f"| {split} | {len(selected)} | {sum(len(doc.entities) for doc in selected)} |"
        )
    lines.extend(["", "| Entity type | dev | test | demo |", "| --- | ---: | ---: | ---: |"])
    for kind in sorted(CORPUS_TYPES):
        lines.append(
            f"| {kind.value} | {counts['dev', kind]} | {counts['test', kind]} "
            f"| {counts['demo', kind]} |"
        )
    return "\n".join(lines) + "\n"


def build_corpus(
    sources: list[Path], output_dir: Path, *, check: bool = False, demo_path: Path | None = None
) -> list[CorpusDocument]:
    """Valide sources puis écrit output_dir et éventuellement demo_path, sauf si check."""
    if not sources:
        raise ValueError(f"{output_dir}:1: Aucune source Markdown.")
    documents: list[CorpusDocument] = []
    identifiers: set[str] = set()
    for path in sorted(sources):
        document = parse_source(path)
        if document.id in identifiers:
            raise ValueError(f"{path}:1: Identifiant de document dupliqué.")
        identifiers.add(document.id)
        documents.append(document)
    documents.sort(key=lambda document: document.id)
    demos = [document for document in documents if document.split == "demo"]
    if demo_path is not None and len(demos) != 1:
        raise ValueError(f"{demo_path}:1: L'export exige exactement un document demo.")
    if check:
        return documents
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in ("dev", "test"):
        content = "".join(
            json.dumps(asdict(document), ensure_ascii=False) + "\n"
            for document in documents
            if document.split == split
        )
        (output_dir / f"{split}.jsonl").write_text(content, encoding="utf-8", newline="\n")
    (output_dir / "stats.md").write_text(_statistics(documents), encoding="utf-8", newline="\n")
    if demo_path is not None:
        demo_path.parent.mkdir(parents=True, exist_ok=True)
        demo_path.write_text(demos[0].text, encoding="utf-8", newline="\n")
    return documents


def main(argv: list[str] | None = None) -> int:
    """Exécute les options argv et renvoie zéro si la construction est valide."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sources", nargs="*", type=Path, help="Sources explicites, sinon corpus/source/*.md"
    )
    parser.add_argument("--source-dir", type=Path, default=ROOT / "corpus" / "source")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "corpus")
    parser.add_argument("--export-demo", action="store_true")
    parser.add_argument(
        "--demo-path", type=Path, default=ROOT / "data" / "samples" / "demo_case_fr.txt"
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        documents = build_corpus(
            args.sources or list(args.source_dir.glob("*.md")),
            args.output_dir,
            check=args.check,
            demo_path=args.demo_path if args.export_demo else None,
        )
    except (ValueError, OSError, UnicodeError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Corpus validé : {len(documents)} document(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
