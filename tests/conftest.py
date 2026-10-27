import socket

import pytest


def _forbidden(*args: object, **kwargs: object) -> None:
    raise RuntimeError("Network access is forbidden in tests")


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Interdit toute connexion réseau pendant le test qui demande cette fixture."""
    monkeypatch.setattr(socket.socket, "connect", _forbidden)
    monkeypatch.setattr(socket, "create_connection", _forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", _forbidden)
