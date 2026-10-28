"""Contrôle indépendant des pages et des contraintes d'interface de G7.

Entrées : application réelle, traductions et documentation du dépôt.
Sorties : assertions bilingues, sans consultation des corpus réservés.
Ces tests complètent les parcours et les contrôles de contraste existants.
"""

import re
import socket
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from app import i18n

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("import", "review", "restore", "evaluation", "method")
BUTTONS = (
    "Load sample case",
    "Detect sensitive data",
    "Add and mask everywhere",
    "Pseudonymize",
    "Back to Import",
    "Restore",
    "Start a new document",
    "Yes, start a new document",
    "Back to Review",
    "Reset session",
    "Yes, reset",
    "Cancel",
    "Send to Mistral",
    "Mask everywhere",
    "Remove the case table",
)


@pytest.fixture
def local_connections_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Autorise la boucle locale nécessaire à AppTest sous Windows, refuse l'extérieur."""
    original_connect = socket.socket.connect
    original_dns = socket.getaddrinfo

    def connect(connection: socket.socket, address: Any) -> None:
        """Transmet uniquement les connexions de contrôle locales du moteur de test."""
        assert isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}
        original_connect(connection, address)

    def resolve(host: Any, *args: Any, **kwargs: Any) -> Any:
        """Refuse la résolution d'un nom externe avant tout appel système."""
        assert host in {None, "localhost", "127.0.0.1", "::1"}
        return original_dns(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket, "getaddrinfo", resolve)


@pytest.mark.parametrize("language", ("en", "fr"))
@pytest.mark.parametrize("page", PAGES)
def test_every_page_in_both_languages(
    language: str, page: str, monkeypatch: pytest.MonkeyPatch, local_connections_only: None
) -> None:
    """Affiche chaque page réelle dans les deux langues, avec les résultats enregistrés.

    Le changement de langue termine le parcours : AppTest sérialise hors session le
    sélecteur manuel de Review, dont le formateur utilise alors la langue par défaut.
    La page française elle-même est rendue et contrôlée dans sa vraie session.
    """
    monkeypatch.setenv(i18n.STRICT_ENV, "1")
    monkeypatch.delenv("HUISCLOS_PUBLIC_DEMO", raising=False)
    app = AppTest.from_file(ROOT / "streamlit_app.py", default_timeout=120).run()
    if page in {"review", "restore"}:
        app.button(key="load_sample").click().run()
        app.button(key="detect").click().run()
    if page == "restore":
        app.button(key="review_pseudonymize").click().run()
    if page in {"evaluation", "method"}:
        app.switch_page(f"app/pages/{page}.py").run()
    if language == "fr":
        app.selectbox(key="language").select("fr").run()
    assert not app.exception
    translations = i18n.EN if language == "en" else i18n.FR
    # La carte de téléchargement présente volontairement la table comme sensible.
    expected_errors = (
        [translations["restore.download.mapping.warning"]] if page == "restore" else []
    )
    assert [item.value for item in app.error] == expected_errors
    assert translations[f"{page}.title"] in [item.value for item in app.header]
    blocks = [str(item.value) for item in [*app.get("html"), *app.markdown]]
    assert not any(re.search(r"https?://", block) for block in blocks)
    if page == "review":
        assert translations["review.manual.button"] == app.button(key="review_add_manual").label
    if page == "restore":
        assert translations["check.heading"] in [item.value for item in app.subheader]
    if page == "evaluation":
        assert app.dataframe


def test_interface_files_stay_below_four_hundred_lines() -> None:
    """Inclut le CSS dans la limite de taille pour garder la charte facile à relire."""
    for path in (ROOT / "app").rglob("*"):
        if path.suffix in {".py", ".css"}:
            assert len(path.read_text(encoding="utf-8").splitlines()) < 400, path


@pytest.mark.parametrize("label", BUTTONS)
def test_documented_application_buttons_have_exact_translations(label: str) -> None:
    """Vérifie les libellés cités par le guide et leur présence exacte dans i18n."""
    guide = (ROOT / "docs" / "USER_GUIDE.md").read_text(encoding="utf-8")
    assert label in guide
    assert label in i18n.EN.values()
