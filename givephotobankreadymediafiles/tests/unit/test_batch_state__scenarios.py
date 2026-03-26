"""
Unit tests for givephotobankreadymediafileslib/batch_state.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
package_root = project_root / "givephotobankreadymediafiles"
sys.path.insert(0, str(package_root))

from givephotobankreadymediafileslib import batch_state


def test__utcnow_iso__returns_iso_format():
    value = batch_state._utcnow_iso()
    assert "T" in value
    assert value.count(":") >= 2


def test__normalize_path__uses_forward_slashes():
    normalized = batch_state._normalize_path(r"C:\Temp\file.jpg")
    assert "\\" not in normalized


def test_batch_registry__create_and_update(tmp_path, monkeypatch):
    registry_path = tmp_path / "registry.json"
    monkeypatch.setattr(batch_state, "BATCH_STATE_DIR", str(tmp_path / "batch_state"))

    registry = batch_state.BatchRegistry(registry_path=str(registry_path))
    batch_id = registry.create_batch("originals", batch_size_limit=5)

    assert batch_id in registry.data["active_batches"]
    registry.increment_batch_file_count(batch_id)
    assert registry.data["active_batches"][batch_id]["file_count"] == 1

    registry.set_batch_status(batch_id, "ready", openai_batch_id="abc")
    assert registry.data["active_batches"][batch_id]["status"] == "ready"
    assert registry.data["active_batches"][batch_id]["openai_batch_id"] == "abc"


def test_batch_registry__register_and_complete(tmp_path, monkeypatch):
    registry_path = tmp_path / "registry.json"
    monkeypatch.setattr(batch_state, "BATCH_STATE_DIR", str(tmp_path / "batch_state"))

    registry = batch_state.BatchRegistry(registry_path=str(registry_path))
    batch_id = registry.create_batch("originals", batch_size_limit=5)

    registry.register_file("C:/files/a.jpg", batch_id)
    assert registry.data["file_registry"]

    registry.complete_batch(batch_id)
    assert batch_id not in registry.data["active_batches"]
    assert registry.data["file_registry"] == {}


def test_batch_registry__register_file_conflict(tmp_path):
    registry = batch_state.BatchRegistry(registry_path=str(tmp_path / "registry.json"))
    registry.data["file_registry"] = {"C:/files/a.jpg": "batch_1"}

    try:
        registry.register_file("C:/files/a.jpg", "batch_2")
    except ValueError as exc:
        assert "already in active batch" in str(exc)
    else:
        raise AssertionError("Expected ValueError for conflicting file registration")


def test_batch_registry__cleanup_completed(tmp_path, monkeypatch):
    registry_path = tmp_path / "registry.json"
    monkeypatch.setattr(batch_state, "BATCH_STATE_DIR", str(tmp_path / "batch_state"))

    registry = batch_state.BatchRegistry(registry_path=str(registry_path))
    registry.data["completed_batches"] = [
        {"batch_id": "batch_old", "completed_at": "2000-01-01T00:00:00"},
        {"batch_id": "batch_new", "completed_at": "2999-01-01T00:00:00"},
        {"batch_id": "batch_bad", "completed_at": "not-a-date"},
    ]

    deleted = []

    def fake_delete(path):
        deleted.append(path)

    import shared.file_operations as file_operations

    monkeypatch.setattr(batch_state.os.path, "exists", lambda _p: True)
    monkeypatch.setattr(file_operations, "delete_folder", fake_delete)

    registry.cleanup_completed(cleanup_days=1)
    assert any("batch_old" in path for path in deleted)
    assert any(item["batch_id"] == "batch_new" for item in registry.data["completed_batches"])
    assert any(item["batch_id"] == "batch_bad" for item in registry.data["completed_batches"])


def test_batch_state__add_and_update(tmp_path):
    batch_dir = tmp_path / "batch_1"
    state = batch_state.BatchState("batch_1", str(batch_dir))

    state.add_file("C:/files/a.jpg", "custom_1", user_description="desc", editorial=True)
    assert state.state["files"]

    state.update_file("C:/files/a.jpg", status="done")
    assert state.state["files"][0]["status"] == "done"

    state.update_file_by_custom_id("custom_1", error="oops")
    assert state.state["files"][0]["error"] == "oops"

    assert state.list_by_status("done")
    assert state.all_files()
