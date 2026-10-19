"""
Unit tests for PhotobankUploader._find_export_csvs and the export CSV check in _upload_to_photobank.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "uploadtophotobanks"
sys.path.insert(0, str(package_root))

import uploadtophotobanksslib.uploader as uploader


def touch(folder, *names):
    for name in names:
        (folder / name).write_text("Filename\n", encoding="utf-8")


def test_find_export_csvs__collects_single_and_split_files(tmp_path):
    touch(tmp_path, "CSV_Pond5.csv", "CSV_Pond5_bw.csv", "CSV_Pond5_editorial_original.csv", "CSV_Pond5_bw_2.csv")
    touch(tmp_path, "CSV_Pond55.csv", "CSV_Pixta_bw.csv", "CSV_Pond5.csv.bak_20260624", "other.txt")

    up = uploader.PhotobankUploader(credentials={})
    result = up._find_export_csvs(str(tmp_path), "Pond5")

    assert [Path(p).name for p in result] == [
        "CSV_Pond5.csv",
        "CSV_Pond5_bw.csv",
        "CSV_Pond5_bw_2.csv",
        "CSV_Pond5_editorial_original.csv",
    ]


def test_find_export_csvs__bank_name_prefix_of_other_bank(tmp_path):
    touch(tmp_path, "CSV_BigStockPhoto_bw.csv")

    up = uploader.PhotobankUploader(credentials={})

    assert up._find_export_csvs(str(tmp_path), "BigStock") == []


def test_find_export_csvs__legacy_output_file_wins(tmp_path):
    touch(tmp_path, "Pond5Output.csv", "CSV_Pond5_bw.csv")

    up = uploader.PhotobankUploader(credentials={})

    assert up._find_export_csvs(str(tmp_path), "Pond5") == [str(tmp_path / "Pond5Output.csv")]


def test_find_export_csvs__missing_dir(tmp_path):
    up = uploader.PhotobankUploader(credentials={})

    assert up._find_export_csvs(str(tmp_path / "missing"), "Pond5") == []


def make_uploader(monkeypatch):
    monkeypatch.setattr(uploader, "PHOTOBANK_CONFIGS", {"Bank": {"supported_formats": [".jpg"]}})
    up = uploader.PhotobankUploader(credentials={"Bank": {"username": "u", "password": "p"}})
    up.file_validator.validate_file_for_photobank = lambda *_a, **_k: True
    return up


def test_upload_to_photobank__split_csvs_are_accepted(monkeypatch, tmp_path):
    touch(tmp_path, "CSV_Bank_bw.csv", "CSV_Bank_original.csv")
    loaded = []
    monkeypatch.setattr(uploader, "load_csv", lambda p: loaded.append(Path(p).name) or [{"Filename": "a.jpg"}])
    up = make_uploader(monkeypatch)

    stats = up._upload_to_photobank("Bank", ["C:/a.jpg"], str(tmp_path), dry_run=True)

    assert loaded == ["CSV_Bank_bw.csv", "CSV_Bank_original.csv"]
    assert stats["success"] == 1


def test_upload_to_photobank__no_export_csv_is_error(monkeypatch, tmp_path, caplog):
    up = make_uploader(monkeypatch)

    stats = up._upload_to_photobank("Bank", ["C:/a.jpg"], str(tmp_path), dry_run=True)

    assert stats == {"error": 1}
    assert "Export CSV not found for Bank" in caplog.text


def test_upload_to_photobank__unreadable_export_csv_is_error(monkeypatch, tmp_path):
    touch(tmp_path, "CSV_Bank_bw.csv")

    def fail(_p):
        raise OSError("locked")

    monkeypatch.setattr(uploader, "load_csv", fail)
    up = make_uploader(monkeypatch)

    assert up._upload_to_photobank("Bank", ["C:/a.jpg"], str(tmp_path), dry_run=True) == {"error": 1}
