"""Vérifie les avertissements d'import dans les deux langues de l'interface.

AppTest charge des octets fictifs via le rappel réel puis affiche le retour de lecture.
Ces essais n'utilisent ni navigateur, ni modèle, ni connexion réseau.
"""

import asyncio
from collections.abc import Iterator

import pytest
from streamlit.testing.v1 import AppTest
from test_import_quality import docx_bytes, pdf_bytes


@pytest.fixture(autouse=True)
def offline_app_loop(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    """Prépare la boucle locale Windows avant de bloquer le réseau pendant AppTest.

    socketpair utilise une connexion locale sur Windows. La boucle est donc créée
    avant la garde, puis fournie à AppTest ; toute lecture reste sous no_network.
    """
    loop = asyncio.new_event_loop()
    request.getfixturevalue("no_network")
    monkeypatch.setattr(asyncio, "new_event_loop", lambda: loop)
    yield
    if not loop.is_closed():
        loop.close()


def import_feedback(filename: str, data: bytes, language: str) -> None:
    """Charge le fichier reçu et affiche son état de lecture dans la langue demandée."""
    import streamlit as st

    from app.state import KEY_READ_ERROR, KEY_READ_WARNINGS, KEY_SOURCE_NAME, KEY_SOURCE_TEXT
    from app.steps.import_step import _load_bytes, _render_source_feedback

    st.session_state["language"] = language
    st.session_state.setdefault(KEY_SOURCE_TEXT, "Previous fictional text")
    st.session_state.setdefault(KEY_SOURCE_NAME, "previous.txt")
    st.session_state.setdefault(KEY_READ_WARNINGS, ())
    st.session_state.setdefault(KEY_READ_ERROR, None)
    _load_bytes(filename, data)
    _render_source_feedback()


@pytest.mark.parametrize("language", ["en", "fr"])
def test_pdf_page_warnings_and_payload_scope(language: str) -> None:
    """Affiche les deux pages douteuses et distingue complétude et contenu envoyé."""
    data = pdf_bytes(("Fictional long selectable text", None, "End"))
    app = AppTest.from_function(
        import_feedback, args=("fiction.pdf", data, language), default_timeout=30
    ).run()
    assert not app.exception
    assert not app.error
    warnings = [item.value for item in app.warning]
    assert len(warnings) == 2
    assert "PDF pages: 2" in warnings[0] if language == "en" else "pages PDF : 2" in warnings[0]
    assert "PDF pages: 3" in warnings[1] if language == "en" else "pages PDF : 3" in warnings[1]
    assert "unknown" in warnings[0] if language == "en" else "inconnue" in warnings[0]
    assert "does not prove" in warnings[1] if language == "en" else "ne prouve pas" in warnings[1]
    scope = app.caption[0].value
    assert "AI request" in scope if language == "en" else "requête IA" in scope
    assert "Fictional long" not in " ".join(warnings)


@pytest.mark.parametrize("language", ["en", "fr"])
@pytest.mark.parametrize(
    "structure,expected_en,expected_fr",
    [
        ('<w:r><w:footnoteReference w:id="1"/></w:r>', "footnotes", "notes de bas"),
        ('<w:commentRangeStart w:id="0"/>', "comments", "commentaires"),
        ("<w:r><w:pict><w:txbxContent/></w:pict></w:r>", "text boxes", "zones de texte"),
        ('<w:ins w:id="0"/>', "tracked changes", "révisions"),
        ("<w:r><w:object/></w:r>", "embedded content", "contenus intégrés"),
    ],
    ids=["notes", "comments", "text-boxes", "revisions", "embedded"],
)
def test_docx_unsupported_warnings(
    language: str, structure: str, expected_en: str, expected_fr: str
) -> None:
    """Traduit chaque limite Word à partir du résultat du véritable lecteur."""
    app = AppTest.from_function(
        import_feedback, args=("fiction.docx", docx_bytes(structure), language), default_timeout=30
    ).run()
    assert not app.exception
    assert not app.error
    assert len(app.warning) == 1
    message = app.warning[0].value
    assert (expected_en if language == "en" else expected_fr) in message
    assert "Partial" in message if language == "en" else "partielle" in message


@pytest.mark.parametrize("language", ["en", "fr"])
@pytest.mark.parametrize(
    "filename,data,warning_count",
    [
        ("fiction.txt", b"Fictional readable text", 0),
        ("fiction.txt", "Texte fictif accentué".encode("cp1252"), 1),
        ("fiction.docx", docx_bytes(), 0),
        ("fiction.pdf", pdf_bytes(("Fictional long selectable text",)), 0),
    ],
    ids=["txt", "cp1252", "docx", "pdf"],
)
def test_legacy_read_feedback(
    language: str, filename: str, data: bytes, warning_count: int
) -> None:
    """Conserve les lectures usuelles et l'ancien avertissement Windows-1252."""
    app = AppTest.from_function(
        import_feedback, args=(filename, data, language), default_timeout=30
    ).run()
    assert not app.exception
    assert not app.error
    assert len(app.warning) == warning_count
    assert len(app.caption) == 1
    if warning_count:
        assert "Windows-1252" in app.warning[0].value


@pytest.mark.parametrize("language", ["en", "fr"])
def test_empty_pdf_error_preserves_previous_text(language: str) -> None:
    """Traduit le refus sans affirmer un scan et garde le texte chargé auparavant."""
    app = AppTest.from_function(
        import_feedback, args=("empty.pdf", pdf_bytes((None,)), language), default_timeout=30
    ).run()
    assert not app.exception
    assert len(app.error) == 1
    assert "OCR" in app.error[0].value
    assert "probably" not in app.error[0].value
    assert len(app.warning) == 1
    assert app.session_state["source_text"] == "Previous fictional text"
