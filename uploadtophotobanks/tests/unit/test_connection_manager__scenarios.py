"""
Unit tests for uploadtophotobanksslib/connection_manager.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanksslib.connection_manager as connection_manager


def test_detect_content_type():
    config = {"protocol": "ftp", "host": "example", "port": 21}
    connection_manager.PHOTOBANK_CONFIGS["TestBank"] = config
    conn = connection_manager.FTPConnection("TestBank", {"username": "u", "password": "p"})

    assert conn._detect_content_type("file.mp4") == "video"
    assert conn._detect_content_type("file.mp3") == "audio"
    assert conn._detect_content_type("file.jpg") == "photos"


def test_get_connection__unsupported():
    manager = connection_manager.ConnectionManager()
    assert manager.get_connection("Unknown", {"username": "u", "password": "p"}) is None


def test_get_host__uses_hosts():
    config = {"protocol": "ftp", "hosts": {"photos": "a", "video": "b"}, "port": 21}
    connection_manager.PHOTOBANK_CONFIGS["TestBank"] = config
    conn = connection_manager.FTPConnection("TestBank", {"username": "u", "password": "p"})
    assert conn._get_host("file.mp4") == "b"


def test_disconnect_all__clears():
    manager = connection_manager.ConnectionManager()

    class DummyConn:
        def __init__(self):
            self.closed = False

        def disconnect(self):
            self.closed = True

    manager.connections["Bank"] = DummyConn()
    manager.disconnect_all()
    assert manager.connections == {}
