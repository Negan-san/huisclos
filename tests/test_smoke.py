import socket

import pytest

import huisclos


def test_package_version() -> None:
    assert huisclos.__version__ == "0.1.0"


def test_no_network_fixture_blocks_sockets(no_network: None) -> None:
    with pytest.raises(RuntimeError, match="Network access is forbidden"):
        socket.create_connection(("example.com", 80))
    with pytest.raises(RuntimeError, match="Network access is forbidden"):
        socket.getaddrinfo("example.com", 80)
    with pytest.raises(RuntimeError, match="Network access is forbidden"):
        socket.socket().connect(("127.0.0.1", 9))
