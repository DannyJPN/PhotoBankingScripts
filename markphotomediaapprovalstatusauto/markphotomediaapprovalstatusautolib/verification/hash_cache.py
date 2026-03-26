"""SQLite-backed cache for perceptual hashes of local photo files."""

import logging
import os
import sqlite3
from typing import Optional, Tuple

import imagehash

from markphotomediaapprovalstatusautolib.verification.image_hasher import generate_dhash, generate_phash
from shared.file_operations import ensure_directory


class HashCache:
    """Persistent cache that maps local file paths to their pHash and dHash values.

    Hashes are invalidated automatically when the file modification time changes.

    :param db_path: Path to the SQLite database file (created if absent).
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        ensure_directory(os.path.dirname(db_path))
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hashes (
                    file_path TEXT PRIMARY KEY,
                    phash     TEXT NOT NULL,
                    dhash     TEXT NOT NULL,
                    mtime     REAL NOT NULL
                )
                """
            )

    def get_or_compute(
        self, file_path: str
    ) -> Optional[Tuple[imagehash.ImageHash, imagehash.ImageHash]]:
        """Return cached hashes or compute them fresh if the file changed.

        :param file_path: Absolute path to the local image file.
        :return: Tuple of (pHash, dHash), or None if the file is missing or
            hashing fails.
        """
        try:
            mtime = os.path.getmtime(file_path)
        except OSError:
            logging.warning("File not found for hashing: %s", file_path)
            return None

        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT phash, dhash, mtime FROM hashes WHERE file_path = ?",
                (file_path,),
            ).fetchone()
            if row and abs(row[2] - mtime) < 1.0:
                return imagehash.hex_to_hash(row[0]), imagehash.hex_to_hash(row[1])

            try:
                ph = generate_phash(file_path)
                dh = generate_dhash(file_path)
            except Exception as exc:
                logging.error("Failed to compute hashes for %s: %s", file_path, exc)
                return None

            conn.execute(
                "INSERT OR REPLACE INTO hashes (file_path, phash, dhash, mtime) VALUES (?, ?, ?, ?)",
                (file_path, str(ph), str(dh), mtime),
            )
            logging.debug("Cached hashes for %s (pHash=%s)", file_path, ph)
            return ph, dh
