"""
Unit tests for uploadtophotobanksslib/credentials_manager.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanksslib.credentials_manager as credentials_manager


def test_load_from_environment(monkeypatch):
    monkeypatch.setenv("SHUTTERSTOCK_USERNAME", "user")
    monkeypatch.setenv("SHUTTERSTOCK_PASSWORD", "pass")

    manager = credentials_manager.CredentialsManager(credentials_file=None)
    assert manager.get_credentials("ShutterStock") == {"username": "user", "password": "pass"}


def test_load_missing_from_file(monkeypatch, tmp_path):
    file_path = tmp_path / "creds.json"
    file_path.write_text(json.dumps({"Pond5": {"username": "u", "password": "p"}}), encoding="utf-8")

    manager = credentials_manager.CredentialsManager(credentials_file=str(file_path))
    assert manager.get_credentials("Pond5") == {"username": "u", "password": "p"}


def test_save_and_remove_credentials(tmp_path):
    file_path = tmp_path / "creds.json"
    manager = credentials_manager.CredentialsManager(credentials_file=str(file_path))
    manager.set_credentials("Test", "u", "p")
    assert manager.save_credentials() is True
    assert manager.remove_credentials("Test") is True


def test_validate_credentials_format():
    manager = credentials_manager.CredentialsManager(credentials_file=None)
    manager.set_credentials("AdobeStock", "not-numeric", "p")
    assert manager.validate_credentials_format("AdobeStock") is True


def test_create_credentials_template(tmp_path):
    file_path = tmp_path / "template.json"
    manager = credentials_manager.CredentialsManager(credentials_file=None)
    assert manager.create_credentials_template(str(file_path)) is True
