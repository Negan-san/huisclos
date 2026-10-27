import socket
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import huisclos

APP_PATH = Path(__file__).resolve().parent.parent / "streamlit_app.py"


def test_package_version() -> None:
    assert huisclos.__version__ == "0.1.0"


def test_home_page_renders() -> None:
    app = AppTest.from_file(str(APP_PATH)).run()
    assert not app.exception
    assert app.title[0].value == "HuisClos"
    texts = [element.value for element in app.get("markdown") + app.get("caption")]
    assert any("Pseudonymization is not anonymization" in text for text in texts)
    assert [header.value for header in app.subheader] == ["1. Import", "2. Review", "3. Restore"]


def test_no_network_fixture_blocks_sockets(no_network: None) -> None:
    with pytest.raises(RuntimeError, match="Network access is forbidden"):
        socket.create_connection(("example.com", 80))
    with pytest.raises(RuntimeError, match="Network access is forbidden"):
        socket.getaddrinfo("example.com", 80)
    with pytest.raises(RuntimeError, match="Network access is forbidden"):
        socket.socket().connect(("127.0.0.1", 9))
