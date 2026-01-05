"""
Integration tests for uploadtophotobanks main dry-run flow.
"""

import types
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanks


class DummyCredentialsManager:
    def __init__(self, *_a, **_k):
        pass

    def list_photobanks(self):
        return ["ShutterStock"]

    def get_all_credentials(self):
        return {"ShutterStock": {"user": "u"}}


class DummyUploader:
    def __init__(self, _creds):
        self.creds = _creds

    def upload_to_photobanks(self, _media_folder, photobanks, _export_dir, _dry_run):
        return {name: {"success": 1, "failure": 0, "skipped": 0, "error": 0} for name in photobanks}


def test_main_dry_run_success(monkeypatch):
    args = types.SimpleNamespace(
        media_folder="X:/media",
        export_dir="X:/export",
        log_dir="X:/logs",
        credentials_file="X:/creds.json",
        debug=False,
        dry_run=True,
        all=False,
        shutterstock=True,
        pond5=False,
        rf123=False,
        depositphotos=False,
        alamy=False,
        dreamstime=False,
        adobestock=False,
        canstockphoto=False,
        setup_credentials=False,
        test_connections=False,
        list_uploadable=False,
        create_credentials_template=False,
    )

    monkeypatch.setattr(uploadtophotobanks, "parse_arguments", lambda: args)
    monkeypatch.setattr(uploadtophotobanks, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(uploadtophotobanks, "get_log_filename", lambda _p: "log.txt")
    monkeypatch.setattr(uploadtophotobanks, "CredentialsManager", DummyCredentialsManager)
    monkeypatch.setattr(uploadtophotobanks, "PhotobankUploader", DummyUploader)
    monkeypatch.setattr(uploadtophotobanks, "validate_input_files", lambda _a: True)

    assert uploadtophotobanks.main() == 0
