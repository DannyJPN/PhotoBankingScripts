"""
Simple cross-platform lock file for batch mode single-instance enforcement.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

from shared.file_operations import ensure_directory, open_file_handle


class BatchLock:
    """Exclusive lock using a lock file handle."""

    def __init__(self, lock_path: str):
        self.lock_path = lock_path
        self._handle: Optional[object] = None
        self._locked: bool = False

    def acquire(self) -> None:
        """Acquire exclusive lock (raises RuntimeError if not available)."""
        # Prevent double-acquire on same instance
        if self._locked:
            raise RuntimeError("Batch mode already running (lock already acquired on this instance)")

        ensure_directory(os.path.dirname(self.lock_path))
        self._handle = open_file_handle(self.lock_path, 'a+')

        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception as e:
            self.release()
            raise RuntimeError(f"Batch mode already running (lock unavailable): {e}") from e

        self._locked = True
        logging.debug("Acquired batch lock: %s", self.lock_path)

    def release(self) -> None:
        """Release lock and close handle."""
        if not self._handle:
            return

        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            logging.warning("Failed to release batch lock: %s", e)
        finally:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None
            self._locked = False

    def __enter__(self) -> 'BatchLock':
        """Context manager entry - acquire lock."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - release lock."""
        self.release()
        return None  # Don't suppress exceptions
