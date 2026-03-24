"""Unit tests for public portfolio session refresh retry logic."""

import sys
from contextlib import contextmanager
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "markphotomediaapprovalstatus"
sys.path.insert(0, str(package_root))

from markphotomediaapprovalstatuslib.constants import (
    STATUS_APPROVED,
    STATUS_CHECKED,
    STATUS_COLUMN_KEYWORD,
)
from markphotomediaapprovalstatuslib.public_portfolio import runner
from markphotomediaapprovalstatuslib.public_portfolio.models import MatchResult, PublicAsset


class _DummyAdapter:
    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.bank = "ShutterStock"

    def is_supported(self) -> bool:
        return True


@contextmanager
def _fake_browser_context(headless=True, bank=None):
    yield object()


def test_runner__blocked_bank_runs_session_saver_and_retries(monkeypatch):
    status_column = f"ShutterStock {STATUS_COLUMN_KEYWORD}"
    record = {
        "Název": "Forest trail at sunrise",
        "Popis": "Morning sunlight in misty woodland",
        status_column: STATUS_CHECKED,
    }
    all_data = [record]
    filtered_data = [record]
    crawl_results = [
        ([], True),
        ([PublicAsset("ShutterStock", "https://example.com/a", "user1", "Forest trail at sunrise", "")], False),
    ]
    calls = {"session": 0, "save": 0}

    monkeypatch.setattr(runner, "BANK_ADAPTERS", {"ShutterStock": _DummyAdapter})
    monkeypatch.setattr(runner, "browser_context", _fake_browser_context)
    monkeypatch.setattr(
        runner,
        "load_config",
        lambda path: {"banks": {"ShutterStock": {"portfolio_url": "https://example.com/portfolio", "contributor_id": "user1"}}},
    )
    monkeypatch.setattr(runner, "filter_records_by_bank_status", lambda data, bank, status: filtered_data)
    monkeypatch.setattr(runner, "_crawl_portfolio", lambda adapter, context, url, contributor_id: crawl_results.pop(0))
    monkeypatch.setattr(
        runner,
        "match_record_to_public_assets",
        lambda *args, **kwargs: MatchResult(approved=True, matched_by="TITLE", public_url="https://example.com/a"),
    )
    monkeypatch.setattr(runner, "save_csv_with_backup", lambda data, path: calls.__setitem__("save", calls["save"] + 1))

    def _fake_run_session_saver(bank: str) -> bool:
        calls["session"] += 1
        assert bank == "ShutterStock"
        return True

    monkeypatch.setattr(runner, "run_session_saver", _fake_run_session_saver)

    changed = runner.process_public_portfolio_approval(all_data, filtered_data, "PhotoMedia.csv")

    assert changed is True
    assert record[status_column] == STATUS_APPROVED
    assert calls["session"] == 1
    assert calls["save"] == 1
    assert crawl_results == []
