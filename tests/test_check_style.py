from pathlib import Path

import pytest

from scripts import check_style

DOCSTRING = '"""Un module.\n\nSecond paragraphe.\nTroisième ligne.\n"""\n'


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Faux dépôt : le script le traite comme sa racine, avec ses dossiers src/ et app/."""
    monkeypatch.setattr(check_style, "ROOT", tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    return tmp_path


def codes(path: Path) -> list[str]:
    errors, _ = check_style.check_file(path)
    return [error[3] for error in errors]


def write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_c1_dash_ellipsis_emoji(repo: Path) -> None:
    for bad in ("a — b", "a…", "ok \U0001f600", "ok ✅", "ok ️"):
        assert codes(write(repo / "docs" / "n.md", bad + "\n")) == ["C1"]
    assert codes(write(repo / "docs" / "n.md", "Texte propre, avec accents é.\n")) == []


def test_c2_typographic_quotes_only_in_code(repo: Path) -> None:
    quotes = "“ ” ‘ ’ « »"
    assert codes(write(repo / "a.toml", f'key = "{quotes}"\n')) == ["C2"] * 6
    assert codes(write(repo / "a.css", f"/* {quotes} */\n")) == ["C2"] * 6
    assert codes(write(repo / "docs" / "n.md", f"{quotes}\n")) == []
    assert codes(write(repo / "a.toml", 'key = "l\'été"\n')) == []


def test_c3_banner(repo: Path) -> None:
    assert codes(write(repo / "a.toml", "# " + "=" * 5 + "\n")) == ["C3"]
    assert codes(write(repo / "a.css", "/* " + "-" * 6 + " */\n")) == ["C3"]
    assert codes(write(repo / "a.toml", "# " + "=" * 4 + "\n")) == []
    assert codes(write(repo / "a.toml", 'line = "' + "=" * 5 + '"\n')) == []


def test_c4_banned_phrases(repo: Path) -> None:
    assert codes(write(repo / "docs" / "n.md", "Un outil Puissant.\n")) == ["C4"]
    assert codes(write(repo / "docs" / "n.md", "Seamlessly done, it is worth noting.\n")) == [
        "C4",
        "C4",
    ]
    assert codes(write(repo / "docs" / "n.md", "Une puissance de calcul.\n")) == []


def test_c5_print_and_markers(repo: Path) -> None:
    bad = write(repo / "src" / "m.py", DOCSTRING + "print('x')\n# TODO later\n# FIXME\n# XXX\n")
    assert codes(bad) == ["C5"] * 4
    good = write(repo / "src" / "m.py", DOCSTRING + "def blueprint():\n    return 1\n")
    assert codes(good) == []
    outside = write(repo / "tests_m.py", "print('x')\n")
    assert codes(outside) == []


def test_c6_module_docstring(repo: Path) -> None:
    assert codes(write(repo / "src" / "m.py", "x = 1\n")) == ["C6"]
    assert codes(write(repo / "src" / "m.py", '"""Une ligne.\n"""\n')) == ["C6"]
    assert codes(write(repo / "src" / "m.py", '"""A\n\nB\n"""\n')) == ["C6"]
    assert codes(write(repo / "src" / "m.py", DOCSTRING)) == []
    assert codes(write(repo / "x.py", "x = 1\n")) == []


def test_c7_length(repo: Path) -> None:
    body = DOCSTRING + "x = 1\n" * 300
    errors, warnings = check_style.check_file(write(repo / "src" / "m.py", body))
    assert (errors, [w[3] for w in warnings]) == ([], ["C7"])
    errors, warnings = check_style.check_file(write(repo / "src" / "m.py", body + "y = 1\n" * 100))
    assert [e[3] for e in errors] == ["C7"] and warnings == []


def test_exclusions(repo: Path) -> None:
    write(repo / "docs" / "MASTER_PLAN.md", "a — b\n")
    write(repo / "docs" / "PROMPTS.md", "a — b\n")
    (repo / "docs" / "prompts").mkdir()
    write(repo / "docs" / "prompts" / "s.md", "a — b\n")
    write(repo / "docs" / "off.md", "<!-- style-check: off -->\na — b\n")
    write(repo / "docs" / "late.md", "1\n2\n3\n4\n5\nstyle-check: off —\n")
    names = [p.name for p in check_style.collect_files([repo / "docs"])]
    assert names == ["late.md"]


def test_main_exit_codes_and_output(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(repo / "docs" / "n.md", "ok\nx — y\n")
    assert check_style.main(["--paths", str(repo / "docs")]) == 1
    out = capsys.readouterr().out
    assert "docs/n.md:2:3: C1 tiret cadratin" in out
    assert "Total : 1 erreur(s)" in out
    write(repo / "docs" / "n.md", "ok\n")
    assert check_style.main(["--paths", str(repo / "docs")]) == 0


def test_real_repository_is_clean() -> None:
    assert check_style.main([]) == 0
