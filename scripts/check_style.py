"""Contrôle automatique des interdits de style du projet (règles C1 à C7).

Usage : python scripts/check_style.py [--paths chemin ...]
Sortie : une ligne "chemin:ligne:colonne: CODE message" par problème, puis un total.
Code de sortie 1 si au moins une erreur est trouvée.
"""

import argparse
import ast
import re
import sys
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = ("src", "app", "docs", "README.md")
EXTENSIONS = {".py", ".md", ".toml", ".css", ".txt"}
CODE_EXTENSIONS = {".py", ".toml", ".css"}
EXCLUDED = ("docs/MASTER_PLAN.md", "docs/PROMPTS.md", "docs/prompts/", "scripts/banned_phrases.txt")
OFF_MARKER = "style-check: off"
BANNED_FILE = Path(__file__).resolve().parent / "banned_phrases.txt"

# Les caractères interdits sont écrits en échappements pour que ce fichier se contrôle lui-même.
DASH_OR_ELLIPSIS = {"\u2014": "tiret cadratin", "\u2026": "points de suspension typographiques"}
EMOJI_PATTERN = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\ufe0f]")
TYPOGRAPHIC_QUOTES = "\u201c\u201d\u2018\u2019\u00ab\u00bb"
BANNER_PATTERN = re.compile(r"([=\-*#~_])\1{4}")
DEBUG_PATTERN = re.compile(r"\bprint\s*\(|\b(?:TODO|FIXME|XXX)\b")
COMMENT_STARTS = ("#", "/*", "*", "//")
WARN_LINES = 300
MAX_LINES = 400
MIN_DOCSTRING_LINES = 3

Problem = tuple[Path, int, int, str, str]


def relative_name(path: Path) -> str:
    """Chemin relatif au dépôt avec des barres obliques, ou chemin brut hors du dépôt."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def is_excluded(path: Path) -> bool:
    """Indique si le fichier est exclu par la liste fixe ou par le marqueur style-check: off."""
    name = relative_name(path)
    if any(name == item or name.startswith(item) for item in EXCLUDED):
        return True
    head = path.read_text(encoding="utf-8").splitlines()[:5]
    return any(OFF_MARKER in line for line in head)


def collect_files(paths: Iterable[Path]) -> list[Path]:
    """Liste les fichiers contrôlables (extensions retenues) sous les chemins donnés."""
    files: list[Path] = []
    for path in paths:
        candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
        files.extend(p for p in candidates if p.is_file() and p.suffix in EXTENSIONS)
    return [p for p in files if "__pycache__" not in p.parts and not is_excluded(p)]


def load_banned_phrases() -> list[re.Pattern[str]]:
    """Compile les expressions de banned_phrases.txt en motifs de mots entiers."""
    patterns = []
    for line in BANNED_FILE.read_text(encoding="utf-8").splitlines():
        phrase = line.strip()
        if phrase and not phrase.startswith("#"):
            patterns.append(re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)", re.IGNORECASE))
    return patterns


def check_characters(path: Path, lines: list[str]) -> list[Problem]:
    """Règles C1 (tous fichiers) et C2 (code) : caractères interdits."""
    problems: list[Problem] = []
    for number, line in enumerate(lines, start=1):
        for column, char in enumerate(line, start=1):
            if char in DASH_OR_ELLIPSIS:
                problems.append((path, number, column, "C1", DASH_OR_ELLIPSIS[char]))
            elif EMOJI_PATTERN.match(char):
                problems.append((path, number, column, "C1", "emoji"))
            elif char in TYPOGRAPHIC_QUOTES and path.suffix in CODE_EXTENSIONS:
                problems.append((path, number, column, "C2", "guillemet typographique"))
    return problems


def check_banners(path: Path, lines: list[str]) -> list[Problem]:
    """Règle C3 : ligne de commentaire contenant cinq fois de suite le même caractère."""
    if path.suffix not in CODE_EXTENSIONS:
        return []
    problems: list[Problem] = []
    for number, line in enumerate(lines, start=1):
        match = BANNER_PATTERN.search(line)
        if match and line.lstrip().startswith(COMMENT_STARTS):
            problems.append((path, number, match.start() + 1, "C3", "bannière décorative"))
    return problems


def check_banned_phrases(path: Path, lines: list[str]) -> list[Problem]:
    """Règle C4 : expressions listées dans banned_phrases.txt."""
    problems: list[Problem] = []
    patterns = load_banned_phrases()
    for number, line in enumerate(lines, start=1):
        for pattern in patterns:
            for match in pattern.finditer(line):
                message = f"expression interdite : {match.group(0)}"
                problems.append((path, number, match.start() + 1, "C4", message))
    return problems


def needs_python_checks(path: Path) -> bool:
    """Active C5 et C6 pour src/, app/ et les fichiers Python externes explicitement visés."""
    if path.suffix != ".py":
        return False
    try:
        relative = path.resolve().relative_to(ROOT)
    except ValueError:
        # Un chemin externe fourni par --paths doit recevoir les mêmes contrôles.
        return True
    return relative.parts[0] in {"src", "app"}


def check_debug_markers(path: Path, lines: list[str]) -> list[Problem]:
    """Règle C5 : appel print( et marqueurs TODO, FIXME, XXX."""
    problems: list[Problem] = []
    for number, line in enumerate(lines, start=1):
        for match in DEBUG_PATTERN.finditer(line):
            message = f"interdit : {match.group(0)}"
            problems.append((path, number, match.start() + 1, "C5", message))
    return problems


def check_module_docstring(path: Path, source: str) -> list[Problem]:
    """Règle C6 : docstring de module présente et d'au moins trois lignes non vides."""
    try:
        docstring = ast.get_docstring(ast.parse(source), clean=True)
    except SyntaxError as error:
        return [(path, error.lineno or 1, 1, "C6", "fichier illisible par ast")]
    non_empty = [line for line in (docstring or "").splitlines() if line.strip()]
    if len(non_empty) < MIN_DOCSTRING_LINES:
        return [(path, 1, 1, "C6", "docstring de module absente ou de moins de 3 lignes")]
    return []


def check_length(path: Path, lines: list[str]) -> tuple[list[Problem], list[Problem]]:
    """Règle C7 : plus de 400 lignes est une erreur, plus de 300 un avertissement."""
    if path.suffix != ".py":
        return [], []
    if len(lines) > MAX_LINES:
        return [(path, 1, 1, "C7", f"{len(lines)} lignes, maximum {MAX_LINES}")], []
    if len(lines) > WARN_LINES:
        return [], [(path, 1, 1, "C7", f"{len(lines)} lignes, au-delà de {WARN_LINES}")]
    return [], []


def check_file(path: Path) -> tuple[list[Problem], list[Problem]]:
    """Applique toutes les règles à un fichier ; renvoie (erreurs, avertissements)."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    errors = check_characters(path, lines)
    errors += check_banners(path, lines)
    errors += check_banned_phrases(path, lines)
    if needs_python_checks(path):
        errors += check_debug_markers(path, lines)
        errors += check_module_docstring(path, source)
    length_errors, warnings = check_length(path, lines)
    return errors + length_errors, warnings


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée : contrôle les chemins demandés et renvoie le code de sortie."""
    parser = argparse.ArgumentParser(description="Contrôle des interdits de style de HuisClos.")
    parser.add_argument("--paths", nargs="+", type=Path, help="fichiers ou dossiers à contrôler")
    args = parser.parse_args(argv)
    targets = args.paths or [ROOT / name for name in DEFAULT_PATHS]
    errors: list[Problem] = []
    warnings: list[Problem] = []
    for path in collect_files(targets):
        file_errors, file_warnings = check_file(path)
        errors += file_errors
        warnings += file_warnings
    for kind, problems in (("", errors), ("avertissement ", warnings)):
        for path, line, column, code, message in problems:
            sys.stdout.write(f"{relative_name(path)}:{line}:{column}: {kind}{code} {message}\n")
    sys.stdout.write(f"Total : {len(errors)} erreur(s), {len(warnings)} avertissement(s)\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
