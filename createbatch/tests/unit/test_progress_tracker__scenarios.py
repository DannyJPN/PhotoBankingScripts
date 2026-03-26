"""
Unit tests for UnifiedProgressTracker.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
createbatch_root = project_root / "createbatch"
sys.path.insert(0, str(createbatch_root))

import createbatchlib.progress_tracker as tracker_module


class DummyTqdm:
    def __init__(self, total, desc, unit, position=0, leave=True):
        self.total = total
        self.desc = desc
        self.unit = unit
        self.position = position
        self.leave = leave
        self.updates = 0
        self.closed = False

    def update(self, count):
        self.updates += count

    def close(self):
        self.closed = True


def test_progress_tracker__tracks_updates(monkeypatch):
    monkeypatch.setattr(tracker_module, "tqdm", DummyTqdm)

    tracker = tracker_module.UnifiedProgressTracker(["A", "B"], {"A": 2, "B": 1})
    tracker.start_bank("A")
    tracker.update_progress(1)
    tracker.finish_bank()
    tracker.start_bank("B")
    tracker.update_progress(1)
    tracker.finish_all()

    assert tracker.processed_records == 2
    assert tracker.main_pbar is None


def test_progress_tracker__summary_zero_total(monkeypatch):
    monkeypatch.setattr(tracker_module, "tqdm", DummyTqdm)

    tracker = tracker_module.UnifiedProgressTracker([], {})

    assert tracker.get_summary() == "Processed 0/0 files (0.0%)"
