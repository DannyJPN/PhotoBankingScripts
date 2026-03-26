"""Writes AuditEntry objects to a CSV file.

The report is always generated, both during --dry-run and real runs.
"""

import csv
import logging
import os
from typing import List

from markphotomediaapprovalstatuslib.report.audit_models import AuditEntry

_HEADERS: List[str] = [
    "timestamp",
    "local_file",
    "bank",
    "result",
    "candidate_url",
    "candidate_id",
    "contributor_match",
    "phash_distance",
    "dhash_distance",
    "dimension_match",
    "preview_url",
    "reason",
]


class AuditWriter:
    """Appends AuditEntry rows to a CSV audit file.

    :param output_path: Full path to the audit CSV file.
    """

    def __init__(self, output_path: str) -> None:
        self._output_path = output_path
        self._header_written = os.path.exists(output_path)

    def write(self, entry: AuditEntry) -> None:
        """Append one AuditEntry to the audit file.

        :param entry: AuditEntry to write.
        """
        os.makedirs(os.path.dirname(self._output_path), exist_ok=True)
        with open(self._output_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=_HEADERS, quoting=csv.QUOTE_ALL)
            if not self._header_written:
                writer.writeheader()
                self._header_written = True
            writer.writerow(
                {
                    "timestamp": entry.timestamp,
                    "local_file": entry.local_file,
                    "bank": entry.bank,
                    "result": entry.result,
                    "candidate_url": entry.candidate_url or "",
                    "candidate_id": entry.candidate_id or "",
                    "contributor_match": "" if entry.contributor_match is None else str(entry.contributor_match),
                    "phash_distance": "" if entry.phash_distance is None else str(entry.phash_distance),
                    "dhash_distance": "" if entry.dhash_distance is None else str(entry.dhash_distance),
                    "dimension_match": "" if entry.dimension_match is None else str(entry.dimension_match),
                    "preview_url": entry.preview_url or "",
                    "reason": entry.reason,
                }
            )
        logging.debug(
            "Audit: %s / %s → %s (%s)", entry.local_file, entry.bank, entry.result, entry.reason
        )