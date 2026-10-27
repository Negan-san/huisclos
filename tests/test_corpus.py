"""Vérifie la construction et le chargement du corpus fictif.

Entrées : fixture Markdown et documents temporaires volontairement incorrects.
Sorties : assertions sur les positions, les clés et les diagnostics localisés.
Ces tests préparent l'évaluation sans consulter les sources réservées au test.
"""

import json
import re
from dataclasses import asdict
from pathlib import Path

import pytest

from huisclos.detection.checksums import (
    digits_only,
    iban_is_valid,
    nir_is_valid,
    siren_is_valid,
    siret_is_valid,
)
from huisclos.evaluation import corpus
from huisclos.evaluation.corpus import CorpusDocument, GoldEntity, load_corpus, load_split
from huisclos.models import EntityType
from scripts import build_corpus as builder

EXAMPLE = Path(__file__).parent / "fixtures" / "corpus_source_example.md"
HEADER = "---\nid: example\ndoc_type: lettre\nsplit: dev\ntitle: Fiction\n---\n"


def write_source(tmp_path: Path, body: str, header: str = HEADER) -> Path:
    """Écrit header et body dans une source temporaire et renvoie son chemin."""
    path = tmp_path / "example.md"
    path.write_text(header + body, encoding="utf-8")
    return path


def test_example_positions_and_identifiers(no_network: None) -> None:
    """Contrôle les personnes, l'adresse multiligne et les clés de la fixture."""
    document = builder.parse_source(EXAMPLE)
    assert document.id == "fixture_01"
    assert [entity.text for entity in document.entities if entity.type == EntityType.PERSON] == [
        "Alice BRUME",
        "Benoît LUCIOLE",
        "Clara NUAGE",
        "BRUME",
    ]
    assert "[[" not in document.text and "{{" not in document.text
    for entity in document.entities:
        assert document.text[entity.start : entity.end] == entity.text
    address = next(entity for entity in document.entities if entity.type == EntityType.ADDRESS)
    assert address.text == "17 rue des Lanternes\n75012 Paris"
    assert document.text[address.start - 4 : address.start] == "est "
    sirets = [entity.text for entity in document.entities if entity.type == EntityType.SIRET]
    sirens = [entity.text for entity in document.entities if entity.type == EntityType.SIREN]
    assert sirets[0] == sirets[1]
    assert digits_only(sirets[0]).startswith(digits_only(sirens[0]))
    assert siret_is_valid(sirets[0]) and siren_is_valid(sirens[0])
    assert not siren_is_valid(sirens[1])
    nirs = [entity.text for entity in document.entities if entity.type == EntityType.NIR]
    assert not nir_is_valid(nirs[0])
    assert nir_is_valid(nirs[1]) and nir_is_valid(nirs[2])
    assert "2A" in nirs[2]
    ibans = [entity.text for entity in document.entities if entity.type == EntityType.IBAN]
    assert iban_is_valid(ibans[0]) and not iban_is_valid(ibans[1])
    trap = re.search(r"non sensible : ([0-9]{9})", document.text)
    assert trap is not None and not siren_is_valid(trap[1])
    assert all(entity.end <= trap.start(1) for entity in document.entities)


@pytest.mark.parametrize(
    ("body", "line", "message"),
    [
        ("Texte\n[[Alice [[BRUME|PERSON]]|PERSON]]", 8, "imbriqué"),
        ("Texte\n[[Alice|ALIEN]]", 8, "Type"),
        ("Texte\n[[Paris|LOCATION]]", 8, "Type"),
        ("Texte\n{{UNKNOWN}}", 8, "Marqueur inconnu"),
        ("Texte\n{{NIR", 8, "équilibré"),
        ("Texte\nNIR}}", 8, "équilibré"),
        ("Texte\n[[Alice|PERSON]", 8, "non fermée"),
        ("Texte\nAlice|PERSON]]", 8, "sans ouverture"),
        ("Texte\n[[Alice]]", 8, "Annotation attendue"),
        ("Texte\n[[|PERSON]]", 8, "Annotation attendue"),
        ("Texte\n[[A|B|PERSON]]", 8, "Annotation attendue"),
        ("Texte\n[[{{DIGITS9}}|SIREN]]", 8, "hors annotation"),
        ("{{NIR}}\n[[Alice|UNKNOWN]]", 8, "Type"),
        ("{{SIREN#0}}", 7, "Marqueur inconnu"),
    ],
)
def test_source_errors_have_line_numbers(
    tmp_path: Path, body: str, line: int, message: str
) -> None:
    """Exige un diagnostic localisé pour chaque forme de balisage incorrecte."""
    path = write_source(tmp_path, body)
    with pytest.raises(ValueError, match=rf"{re.escape(str(path))}:{line}: .*{message}"):
        builder.parse_source(path)


@pytest.mark.parametrize(
    ("header", "line"),
    [
        ("id: example\n", 1),
        (HEADER.replace("title: Fiction\n", ""), 5),
        (HEADER.replace("split: dev", "split: train"), 4),
        (HEADER.replace("title: Fiction", "title:"), 5),
        (HEADER.replace("title: Fiction", "id: second"), 5),
        (HEADER.replace("title: Fiction", "other: Fiction"), 5),
        (HEADER.removesuffix("---\n"), 6),
    ],
)
def test_invalid_headers(tmp_path: Path, header: str, line: int) -> None:
    """Refuse les en-têtes incomplets, inconnus, répétés ou non fermés."""
    path = write_source(tmp_path, "", header)
    with pytest.raises(ValueError, match=rf":{line}: "):
        builder.parse_source(path)


def test_deterministic_build_and_roundtrip(tmp_path: Path) -> None:
    """Compare deux constructions en octets et recharge leurs positions exactes."""
    second = write_source(tmp_path, "[[Zoé ÉCLAT|PERSON]]\n", HEADER.replace("example", "z_last"))
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    documents = builder.build_corpus([second, EXAMPLE], first_dir)
    builder.build_corpus([EXAMPLE, second], second_dir)
    for name in ("dev.jsonl", "test.jsonl", "stats.md"):
        assert (first_dir / name).read_bytes() == (second_dir / name).read_bytes()
        assert b"\r\n" not in (first_dir / name).read_bytes()
    assert load_corpus(first_dir / "dev.jsonl") == documents
    assert [doc.id for doc in documents] == ["fixture_01", "z_last"]
    assert load_corpus(first_dir / "test.jsonl") == []
    stats = (first_dir / "stats.md").read_text(encoding="utf-8")
    assert "| dev | 2 | 18 |" in stats
    assert "| PERSON | 5 | 0 | 0 |" in stats


def test_checks_and_demo_export(tmp_path: Path) -> None:
    """Vérifie l'absence d'écriture en check et la séparation des trois splits."""
    demo = write_source(
        tmp_path, "M. [[Émile AUBE|PERSON]]\n", HEADER.replace("split: dev", "split: demo")
    )
    held_out = tmp_path / "held_out.md"
    held_out.write_text(
        HEADER.replace("example", "held_out").replace("split: dev", "split: test")
        + "[[Fiction|CUSTOM]]",
        encoding="utf-8",
    )
    output, demo_path = tmp_path / "output", tmp_path / "sample" / "demo.txt"
    sources = [EXAMPLE, demo, held_out]
    builder.build_corpus(sources, output, check=True, demo_path=demo_path)
    assert not output.exists() and not demo_path.exists()
    builder.build_corpus(sources, output, demo_path=demo_path)
    assert demo_path.read_text(encoding="utf-8") == "M. Émile AUBE\n"
    assert [doc.split for doc in load_corpus(output / "dev.jsonl")] == ["dev"]
    assert [doc.split for doc in load_corpus(output / "test.jsonl")] == ["test"]
    assert "| CUSTOM | 0 | 1 | 0 |" in (output / "stats.md").read_text(encoding="utf-8")


def test_validation_precedes_all_writes(tmp_path: Path) -> None:
    """Refuse les doublons et les exports ambigus avant toute sortie."""
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="dupliqué"):
        builder.build_corpus([EXAMPLE, EXAMPLE], output)
    with pytest.raises(ValueError, match="exactement un"):
        builder.build_corpus([EXAMPLE], output, demo_path=tmp_path / "demo.txt")
    with pytest.raises(ValueError, match="Aucune source"):
        builder.build_corpus([], output)
    assert not output.exists()


def test_generated_keys_are_checked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Simule une régression du générateur pour vérifier le contrôle de sa clé."""
    path = write_source(tmp_path, "[[{{NIR}}|NIR]]")
    monkeypatch.setattr(builder.ids, "make_nir", lambda *args, **kwargs: "100010100100100")
    with pytest.raises(ValueError, match=":7: .*clé générée"):
        builder.parse_source(path)


def test_company_indices_and_occurrence_order(tmp_path: Path) -> None:
    """Contrôle plusieurs entreprises et les deux ordres de leurs marqueurs."""
    path = write_source(tmp_path, "{{SIREN#1}}\n{{SIRET#1}}\n{{SIRET#2}}\n{{SIREN#2}}")
    first, first_site, second_site, second = builder.parse_source(path).text.splitlines()
    assert digits_only(first_site).startswith(digits_only(first))
    assert digits_only(second_site).startswith(digits_only(second))
    assert first != second
    assert all(siren_is_valid(value) for value in (first, second))
    assert all(siret_is_valid(value) for value in (first_site, second_site))


@pytest.mark.parametrize(
    "entities",
    [
        [{"start": -1, "end": 2, "type": "PERSON", "text": "abc"}],
        [{"start": 0, "end": 0, "type": "PERSON", "text": ""}],
        [{"start": True, "end": 2, "type": "PERSON", "text": "b"}],
        [{"start": 0, "end": 3, "type": "PERSON", "text": "abd"}],
        [{"start": 3, "end": 4, "type": "PERSON", "text": "d"}],
        [{"start": 0, "end": 3, "type": "OTHER", "text": "abc"}],
        [{"start": 0, "end": 3, "type": "LOCATION", "text": "abc"}],
        [{"start": 0, "end": 3, "type": "PERSON", "text": "ab"}],
        [
            {"start": 0, "end": 2, "type": "PERSON", "text": "ab"},
            {"start": 1, "end": 3, "type": "PERSON", "text": "bc"},
        ],
    ],
)
def test_loader_rejects_invalid_spans(tmp_path: Path, entities: list[dict[str, object]]) -> None:
    """Refuse bornes invalides, mauvais types, chevauchements et tranches fausses."""
    path = tmp_path / "bad.jsonl"
    record = {
        "id": "bad",
        "doc_type": "lettre",
        "split": "dev",
        "title": "Fiction",
        "text": "abc",
        "entities": entities,
    }
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=":1: document JSONL invalide"):
        load_corpus(path)


@pytest.mark.parametrize("content", ["{}\n", "[]\n", "null\n", "not JSON\n", "\n"])
def test_loader_rejects_invalid_records(tmp_path: Path, content: str) -> None:
    """Signale les enregistrements JSONL incorrects sans erreur non localisée."""
    path = tmp_path / "bad.jsonl"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError, match=":1: document JSONL invalide"):
        load_corpus(path)


def test_load_split_and_duplicate_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Charge les deux splits isolés, refuse les noms inconnus et les doublons."""
    monkeypatch.setattr(corpus, "CORPUS_DIR", tmp_path)
    document = CorpusDocument(
        "one", "lettre", "dev", "Fiction", "abc", [GoldEntity(0, 3, EntityType.PERSON, "abc")]
    )
    line = json.dumps(asdict(document)) + "\n"
    (tmp_path / "dev.jsonl").write_text(line, encoding="utf-8")
    (tmp_path / "test.jsonl").write_text(line.replace('"dev"', '"test"'), encoding="utf-8")
    assert load_split("dev") == [document]
    assert load_split("test")[0].split == "test"
    with pytest.raises(ValueError, match="dev ou test"):
        load_split("demo")
    (tmp_path / "test.jsonl").write_text(line, encoding="utf-8")
    with pytest.raises(ValueError, match="split incohérent"):
        load_split("test")
    (tmp_path / "dev.jsonl").write_text(line * 2, encoding="utf-8")
    with pytest.raises(ValueError, match=":2: .*dupliqué"):
        load_split("dev")


def test_cli_check_fixture(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exécute --check sur la fixture et contrôle les codes de retour du CLI."""
    output = tmp_path / "output"
    assert builder.main(["--check", "--output-dir", str(output), str(EXAMPLE)]) == 0
    assert "1 document(s)" in capsys.readouterr().out
    assert not output.exists()
    path = write_source(tmp_path, "{{UNKNOWN}}")
    assert builder.main(["--check", str(path)]) == 1
    assert f"{path}:7:" in capsys.readouterr().err
