"""Archive les contrôles et la preuve de non-régression de FIX3.

Entrées : commits figés et code local, sans corpus réservé.
Sorties : journaux et preuves JSON limités aux contrôles et identifiants Git.
Le worktree temporaire exclut entièrement corpus et est supprimé après l'essai.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/fix3-recheck"
OLD, FIX = "ae5dfe9", "bbfc6c1"
TOKEN = "src/huisclos/pseudonymize/tokens.py"
ENV = os.environ | {
    "PYTHONUTF8": "1",
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "TOKENIZERS_PARALLELISM": "false",
}
SIX = [
    "tests/test_fix2.py::test_same_value_in_text_and_file_name_is_pseudonymized",
    "tests/test_fix2.py::test_review_pseudonymizes_a_name_repeated_in_a_file_name",
    "tests/test_tokens.py::test_same_text_in_two_groups_takes_the_token_of_its_position",
    "tests/test_case_memory.py::"
    "test_name_also_in_a_file_name_loses_token_continuity_when_the_surname_returns",
]


def command(args: list[str], cwd: Path = ROOT, **kwargs: Any) -> subprocess.CompletedProcess:
    """Exécute une commande locale, capture les octets et refuse l'échec par défaut."""
    return subprocess.run(args, cwd=cwd, env=ENV, capture_output=True, check=True, **kwargs)


def git(*args: str, **kwargs: Any) -> bytes:
    """Renvoie la sortie Git brute, sans ouvrir de fichier du corpus."""
    return command(["git", *args], **kwargs).stdout


def save(name: str, value: Any) -> None:
    """Écrit un résultat JSON UTF-8 sans contenu de document."""
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def scope() -> None:
    """Compare les blobs avant, après patch et après la seule modification de docstring."""
    expected = sorted(
        [
            "app/i18n/workflow_review.py",
            "app/steps/review_step.py",
            "docs/DECISIONS.md",
            "docs/PROGRESS.md",
            "docs/PROMPTS.md",
            TOKEN,
            "tests/test_case_memory.py",
            "tests/test_fix2.py",
            "tests/test_tokens.py",
        ]
    )
    changed = git("diff", "--name-only", f"{OLD}..{FIX}").decode().splitlines()
    assert sorted(changed) == expected
    with tempfile.TemporaryDirectory(prefix="huisclos-fix3r-index-") as temporary:
        index = str(Path(temporary) / "index")
        index_env = ENV | {"GIT_INDEX_FILE": index}
        subprocess.run(["git", "read-tree", OLD], cwd=ROOT, env=index_env, check=True)
        patch = git("show", f"{OLD}:results/fix2/proposed_fix2_01.patch")
        subprocess.run(
            ["git", "apply", "--cached", "--whitespace=nowarn", "-"],
            cwd=ROOT,
            env=index_env,
            input=patch,
            check=True,
        )
        patched = subprocess.check_output(["git", "show", f":{TOKEN}"], cwd=ROOT, env=index_env)
        patched_blob = (
            subprocess.check_output(["git", "rev-parse", f":{TOKEN}"], cwd=ROOT, env=index_env)
            .decode()
            .strip()
        )
    needle = b"(D-S21-1)."
    assert patched.count(needle) == 1
    amended = patched.replace(needle, "(D-S21-1, amendée par D-FIX3-1).".encode())
    predicted = git("hash-object", "--stdin", input=amended).decode().strip()
    actual = git("rev-parse", f"{FIX}:{TOKEN}").decode().strip()
    assert predicted == actual
    save(
        "scope.json",
        {
            "base": git("rev-parse", OLD).decode().strip(),
            "fix": git("rev-parse", FIX).decode().strip(),
            "files": changed,
            "before_blob": git("rev-parse", f"{OLD}:{TOKEN}").decode().strip(),
            "patch_blob": patched_blob,
            "expected_amended_blob": predicted,
            "actual_blob": actual,
            "equal": True,
        },
    )


def logged(name: str, args: list[str], cwd: Path = ROOT) -> int:
    """Archive stdout et stderr d'un contrôle, y compris son code d'échec attendu."""
    result = subprocess.run(args, cwd=cwd, env=ENV, capture_output=True, check=False)
    header = f"Command: {' '.join(args)}\nExit: {result.returncode}\n"
    body = result.stdout.decode("utf-8", "replace") + result.stderr.decode("utf-8", "replace")
    clean = "\n".join(line.rstrip() for line in (header + body).splitlines()).rstrip() + "\n"
    (OUT / f"{name}.log").write_text(clean, encoding="utf-8", newline="\n")
    return result.returncode


def regressions() -> None:
    """Rejoue les six tests dans un checkout sans corpus, ancien tokens puis code corrigé."""
    with tempfile.TemporaryDirectory(prefix="huisclos-fix3r-parent-") as temporary:
        path = (Path(temporary) / "checkout").resolve()
        assert not path.is_relative_to(ROOT) and path.parent == Path(temporary).resolve()
        git("worktree", "add", "--detach", "--no-checkout", str(path), FIX)
        try:
            git(
                "sparse-checkout", "set", "--no-cone", "--stdin", cwd=path, input=b"/*\n!/corpus/\n"
            )
            git("checkout", FIX, cwd=path)
            assert not (path / "corpus").exists()
            (path / TOKEN).write_bytes(git("show", f"{OLD}:{TOKEN}"))
            arguments = [sys.executable, "-m", "pytest", "-q", *SIX]
            before = logged("six-before", arguments, path)
            (path / TOKEN).write_bytes(git("show", f"{FIX}:{TOKEN}"))
            after = logged("six-after", arguments, path)
            assert before == 1 and after == 0
        finally:
            # Le chemin absolu est vérifié avant la suppression récursive par Git.
            assert path.parent == Path(temporary).resolve() and not path.is_relative_to(ROOT)
            git("worktree", "remove", "--force", str(path))
        removed = not path.exists() and str(path).encode() not in git(
            "worktree", "list", "--porcelain"
        )
        assert removed
    save(
        "regressions.json",
        {
            "old_exit": before,
            "fixed_exit": after,
            "expected_count": 6,
            "corpus_excluded": True,
            "outside_repository": True,
            "worktree_removed": removed,
        },
    )


def checks() -> None:
    """Lance tous les contrôles demandés et archive chaque sortie séparément."""
    controls = {
        "pytest": [sys.executable, str(OUT / "guarded_pytest.py"), "-q"],
        "ruff-check": [sys.executable, "-m", "ruff", "check", "."],
        "ruff-format": [sys.executable, "-m", "ruff", "format", "--check", "."],
        "style": [sys.executable, "scripts/check_style.py"],
        "diff-check": ["git", "diff", "--check"],
        "staged-diff-check": ["git", "diff", "--cached", "--check"],
    }
    results = {name: logged(name, args) for name, args in controls.items()}
    save("controls.json", results)
    assert all(code == 0 for code in results.values())


if __name__ == "__main__":
    {"scope": scope, "regressions": regressions, "checks": checks}[sys.argv[1]]()
