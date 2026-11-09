"""
Unit tests for the export summary handling in exportpreparedmedia.main().
"""

import logging
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "exportpreparedmedia"
sys.path.insert(0, str(package_root))

import exportpreparedmedia


@pytest.fixture
def patched_main(monkeypatch, tmp_path):
    monkeypatch.setattr(
        sys,
        "argv",
        ["exportpreparedmedia.py", "--shutterstock", "--output_dir", str(tmp_path), "--log_dir", str(tmp_path)],
    )
    monkeypatch.setattr(exportpreparedmedia, "setup_logging", lambda **_k: None)
    monkeypatch.setattr(exportpreparedmedia, "load_csv", lambda _p: [])

    def set_summary(summary):
        monkeypatch.setattr(exportpreparedmedia, "export_to_photobanks", lambda *_a, **_k: summary)

    return set_summary


def test_main__export_summary_without_errors(patched_main, caplog):
    patched_main({"files_written": 3, "files_failed": 0, "records_failed": 0})

    with caplog.at_level(logging.INFO):
        exportpreparedmedia.main()

    assert "completed successfully: 3 files written" in caplog.text


@pytest.mark.parametrize("files_failed, records_failed", [(1, 0), (0, 2)])
def test_main__export_summary_with_errors_exits(patched_main, caplog, files_failed, records_failed):
    patched_main({"files_written": 1, "files_failed": files_failed, "records_failed": records_failed})

    with caplog.at_level(logging.INFO), pytest.raises(SystemExit) as exc:
        exportpreparedmedia.main()

    assert exc.value.code == 1
    assert "Export finished with errors" in caplog.text
    assert "completed successfully" not in caplog.text
