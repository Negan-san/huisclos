"""Vérifie les empreintes des environnements locaux sans installer de paquet.

Entrées : sorties pip fictives et fichiers temporaires avec fins de ligne imposées.
Sorties : métadonnées dont le SHA-256 correspond aux octets réellement écrits.
Place : préparation reproductible des environnements avant une migration A4.
"""

import hashlib
import subprocess
from pathlib import Path

import pytest

from scripts.prepare_local_models import describe_environment


@pytest.mark.parametrize("line_ending", ["\n", "\r\n"])
def test_environment_freeze_hashes_written_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, line_ending: str
) -> None:
    """L'empreinte reste vérifiable même si l'écriture convertit les fins de ligne."""
    original_write = Path.write_text

    def write_with_line_ending(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        """Simule les écritures LF ou CRLF sans modifier le contenu pip fictif."""
        return original_write(path, data, encoding=encoding, errors=errors, newline=line_ending)

    def run_fake(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        """Fournit des versions et contrôles fictifs, sans exécuter pip ni ouvrir le réseau."""
        if "freeze" in command:
            output = "spacy==3.8.18\ntransformers==5.21.0\n"
        elif "check" in command:
            output = "No broken requirements found.\n"
        else:
            output = "3.12.10\n"
        return subprocess.CompletedProcess(command, 0, stdout=output)

    monkeypatch.setattr(Path, "write_text", write_with_line_ending)
    monkeypatch.setattr(subprocess, "run", run_fake)
    (tmp_path / "envs").mkdir()
    result = describe_environment(tmp_path / "python.exe", tmp_path, "baseline_python")
    written = Path(result["freeze"]).read_bytes()
    assert line_ending.encode("utf-8") in written
    assert result["freeze_sha256"] == hashlib.sha256(written).hexdigest()
    assert result["key_versions"]["spacy"] == "3.8.18"
    assert result["pip_check"] == "ok"
