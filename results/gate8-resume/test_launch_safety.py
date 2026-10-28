"""Vérifie le verrou d'essai et le diagnostic du lanceur G8R2.

Entrées : reçus temporaires et sorties entièrement fictives.
Sorties : refus avant les prérequis et diagnostic technique filtré.
Aucun lancement de profil ou accès à un corpus n'est effectué.
"""

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_resume  # noqa: E402


@pytest.mark.parametrize("receipt", ("registration.json", "attempt_challenge.json", "challenge"))
def test_existing_receipt_refuses_before_prerequisites(
    receipt: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tout reçu déjà présent interdit même d'atteindre les prérequis de la mesure."""
    (tmp_path / receipt).write_text("fictional", encoding="utf-8")
    monkeypatch.setattr(run_resume, "OUT", tmp_path)

    def forbidden() -> Any:
        """Signale un passage interdit au-delà du verrou exclusif."""
        raise AssertionError("prerequisites reached")

    monkeypatch.setattr(run_resume, "prerequisites", forbidden)
    with pytest.raises(SystemExit, match="second attempt refused before reserved access"):
        run_resume.measure()


@pytest.mark.parametrize(
    "stderr",
    (
        "fictional sensitive payload",
        "G8 worker failed: exit 3 at stage unknown (RuntimeError)",
        "G8 worker failed: exit 3 at stage detection (RuntimeError secret)",
    ),
)
def test_unvalidated_diagnostic_is_discarded(stderr: str) -> None:
    """Une sortie non conforme ne produit aucun message ni contenu dans le diagnostic."""
    assert run_resume.validated_diagnostic(stderr) == {"available": False}


def test_valid_diagnostic_keeps_only_code_location() -> None:
    """Un lieu connu ne conserve que les champs techniques validés."""
    stderr = (
        "fictional preamble\nG8 worker failed: exit 3 at stage pseudonymization (RuntimeError)"
        " in src/huisclos/pseudonymize/tokens.py:_substitute:171; no reserved output shown\n"
        "fictional trailing payload"
    )
    assert run_resume.validated_diagnostic(stderr) == {
        "available": True,
        "worker_exit_code": 3,
        "stage": "pseudonymization",
        "error_type": "RuntimeError",
        "path": "src/huisclos/pseudonymize/tokens.py",
        "function": "_substitute",
        "line": 171,
    }
