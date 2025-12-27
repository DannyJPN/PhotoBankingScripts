"""
Batch registry and per-batch state handling for batch mode.
"""
from __future__ import annotations

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from uuid import uuid4

from givephotobankreadymediafileslib.constants import (
    BATCH_REGISTRY_FILE,
    BATCH_STATE_DIR,
    DEFAULT_BATCH_CLEANUP_DAYS
)
from shared.file_operations import ensure_directory, read_json, write_json


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


def _normalize_path(path: str) -> str:
    return os.path.abspath(path).replace("\\", "/")


class BatchRegistry:
    """Global registry of all batch runs and active files."""

    def __init__(self, registry_path: str = BATCH_REGISTRY_FILE):
        self.registry_path = registry_path
        self.data = self._load_registry()

    def _load_registry(self) -> dict:
        data = read_json(self.registry_path, default={})
        data.setdefault("active_batches", {})
        data.setdefault("completed_batches", [])
        data.setdefault("file_registry", {})
        data.setdefault("daily_counts", {})
        data.setdefault("alternatives_generated", {})
        return data

    def save(self) -> None:
        write_json(self.registry_path, self.data)

    def get_daily_count(self, date_key: str) -> int:
        return int(self.data.get("daily_counts", {}).get(date_key, 0))

    def increment_daily_count(self, date_key: str, delta: int = 1) -> None:
        current = self.get_daily_count(date_key)
        self.data["daily_counts"][date_key] = current + delta
        self.save()

    def create_batch(self, batch_type: str, batch_size_limit: int) -> str:
        ensure_directory(BATCH_STATE_DIR)
        batch_id = f"batch_{uuid4().hex[:8]}"
        self.data["active_batches"][batch_id] = {
            "status": "collecting",
            "created_at": _utcnow_iso(),
            "batch_type": batch_type,
            "file_count": 0,
            "batch_size_limit": batch_size_limit,
            "openai_batch_id": None
        }
        self.save()
        return batch_id

    def get_active_batches(self, status: Optional[str] = None) -> Dict[str, dict]:
        batches = self.data.get("active_batches", {})
        if status is None:
            return batches
        return {bid: info for bid, info in batches.items() if info.get("status") == status}

    def set_batch_status(self, batch_id: str, status: str, **kwargs) -> None:
        batch = self.data["active_batches"].get(batch_id)
        if not batch:
            raise KeyError(f"Batch not found: {batch_id}")
        batch["status"] = status
        batch.update(kwargs)
        self.save()

    def increment_batch_file_count(self, batch_id: str) -> None:
        batch = self.data["active_batches"].get(batch_id)
        if not batch:
            raise KeyError(f"Batch not found: {batch_id}")
        batch["file_count"] = int(batch.get("file_count", 0)) + 1
        self.save()

    def register_file(self, file_path: str, batch_id: str) -> None:
        normalized = _normalize_path(file_path)
        existing = self.data.get("file_registry", {}).get(normalized)
        if existing and existing != batch_id:
            raise ValueError(f"File already in active batch: {existing}")
        self.data["file_registry"][normalized] = batch_id
        self.save()

    def update_file_batch(self, file_path: str, batch_id: str) -> None:
        normalized = _normalize_path(file_path)
        self.data["file_registry"][normalized] = batch_id
        self.save()

    def unregister_files_for_batch(self, batch_id: str) -> None:
        registry = self.data.get("file_registry", {})
        to_remove = [path for path, bid in registry.items() if bid == batch_id]
        for path in to_remove:
            registry.pop(path, None)
        self.save()

    def unregister_file(self, file_path: str) -> None:
        normalized = _normalize_path(file_path)
        if normalized in self.data.get("file_registry", {}):
            self.data["file_registry"].pop(normalized, None)
            self.save()

    def complete_batch(self, batch_id: str) -> None:
        completed = {
            "batch_id": batch_id,
            "completed_at": _utcnow_iso()
        }
        self.data["completed_batches"].append(completed)
        self.data["active_batches"].pop(batch_id, None)
        self.unregister_files_for_batch(batch_id)
        self.save()

    def get_batch_dir(self, batch_id: str) -> str:
        return os.path.join(BATCH_STATE_DIR, "batches", batch_id)

    def cleanup_completed(self, cleanup_days: int = DEFAULT_BATCH_CLEANUP_DAYS) -> None:
        cutoff = datetime.utcnow().timestamp() - (cleanup_days * 86400)
        remaining = []
        for item in self.data.get("completed_batches", []):
            completed_at = item.get("completed_at")
            try:
                ts = datetime.fromisoformat(completed_at).timestamp()
            except Exception:
                remaining.append(item)
                continue
            if ts < cutoff:
                batch_id = item.get("batch_id")
                if batch_id:
                    batch_dir = self.get_batch_dir(batch_id)
                    if os.path.exists(batch_dir):
                        try:
                            from shared.file_operations import delete_folder
                            delete_folder(batch_dir)
                        except Exception as e:
                            logging.warning("Failed to delete old batch dir %s: %s", batch_dir, e)
            else:
                remaining.append(item)
        self.data["completed_batches"] = remaining
        self.save()


class BatchState:
    """Per-batch state stored in a batch folder."""

    def __init__(self, batch_id: str, batch_dir: str):
        self.batch_id = batch_id
        self.batch_dir = batch_dir
        self.state_path = os.path.join(batch_dir, "state.json")
        self.descriptions_path = os.path.join(batch_dir, "descriptions.json")
        self.results_path = os.path.join(batch_dir, "results.json")
        ensure_directory(batch_dir)
        self.state = self._load()

    def _load(self) -> dict:
        # FIX: read_json() returns {} when file doesn't exist (not None)
        # Use explicit empty dict as default and check for empty dict
        data = read_json(self.state_path, default={})
        if not data:  # Empty dict when file doesn't exist or is empty
            data = {
                "batch_id": self.batch_id,
                "created_at": _utcnow_iso(),
                "files": []
            }
            write_json(self.state_path, data)
        return data

    def save(self) -> None:
        write_json(self.state_path, self.state)
        self._save_descriptions()
        self._save_results()

    def _save_descriptions(self) -> None:
        descriptions = {}
        for item in self.state.get("files", []):
            if item.get("user_description"):
                descriptions[item.get("custom_id")] = {
                    "file_path": item.get("file_path"),
                    "user_description": item.get("user_description"),
                    "editorial": bool(item.get("editorial")),
                    "editorial_data": item.get("editorial_data")
                }
        write_json(self.descriptions_path, descriptions)

    def _save_results(self) -> None:
        results = {}
        for item in self.state.get("files", []):
            if item.get("result") is not None:
                results[item.get("custom_id")] = {
                    "file_path": item.get("file_path"),
                    "result": item.get("result")
                }
        write_json(self.results_path, results)

    def add_file(self, file_path: str, custom_id: str, user_description: str = "",
                 editorial: bool = False, editorial_data: Optional[dict] = None,
                 entry_type: str = "original", extra: Optional[dict] = None) -> None:
        if any(item["file_path"] == file_path for item in self.state["files"]):
            return
        payload = {
            "file_path": file_path,
            "custom_id": custom_id,
            "status": "pending",
            "user_description": user_description or "",
            "editorial": bool(editorial),
            "editorial_data": editorial_data or None,
            "result": None,
            "error": None,
            "entry_type": entry_type
        }
        if extra:
            payload.update(extra)
        self.state["files"].append(payload)
        self.save()

    def update_file(self, file_path: str, **kwargs) -> None:
        for item in self.state["files"]:
            if item["file_path"] == file_path:
                item.update(kwargs)
                break
        self.save()

    def update_file_by_custom_id(self, custom_id: str, **kwargs) -> None:
        for item in self.state["files"]:
            if item["custom_id"] == custom_id:
                item.update(kwargs)
                break
        self.save()

    def list_by_status(self, status: str) -> List[dict]:
        return [item for item in self.state["files"] if item.get("status") == status]

    def all_files(self) -> List[dict]:
        return list(self.state.get("files", []))
