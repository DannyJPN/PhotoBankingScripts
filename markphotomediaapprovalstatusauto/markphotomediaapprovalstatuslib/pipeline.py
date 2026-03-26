"""Orchestration pipeline: discovery → verification → decision → write."""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from markphotomediaapprovalstatuslib.constants import (
    COL_FILE,
    COL_PATH,
    DEFAULT_CONTRIBUTOR_NAME,
    DEFAULT_HASH_CACHE_PATH,
    DEFAULT_PREVIEW_CACHE_DIR,
    DEFAULT_REPORT_DIR,
    STATUS_APPROVED,
    STATUS_COLUMN_KEYWORD,
)
from markphotomediaapprovalstatuslib.decision import decide
from markphotomediaapprovalstatuslib.discovery.registry import get_adapter
from markphotomediaapprovalstatuslib.models import (
    Candidate,
    DetectionResult,
    Evidence,
    PhotoRecord,
)
from markphotomediaapprovalstatuslib.report.audit_models import AuditEntry
from markphotomediaapprovalstatuslib.report.audit_writer import AuditWriter
from markphotomediaapprovalstatuslib.transport.http_client import HttpClient
from markphotomediaapprovalstatuslib.verification.evidence_builder import build_evidence
from markphotomediaapprovalstatuslib.verification.hash_cache import HashCache
from shared.file_operations import save_csv_with_backup


def build_photo_record(row: dict, bank_name: str) -> Optional[PhotoRecord]:
    """Build a PhotoRecord from a CSV row for *bank_name*.

    :param row: Raw CSV row dictionary.
    :param bank_name: Name of the bank being processed.
    :return: PhotoRecord, or None when essential fields are missing.
    """
    file_name = row.get(COL_FILE, "").strip()
    path = row.get(COL_PATH, "").strip()
    if not file_name:
        return None
    local_path = os.path.join(path, file_name) if path else file_name
    status_col = f"{bank_name} {STATUS_COLUMN_KEYWORD}"
    return PhotoRecord(
        file=file_name,
        path=path,
        title=row.get("Název", ""),
        description=row.get("Popis", ""),
        keywords=row.get("Klíčová slova", ""),
        bank_statuses={bank_name: row.get(status_col, "")},
        local_file_path=local_path,
    )


def _select_best_evidence(evidences: List[Evidence]) -> Optional[Evidence]:
    """Pick the evidence with the lowest pHash distance that has contributor match.

    Falls back to any evidence with a computed distance if no contributor match
    exists (for logging purposes only — such evidence will yield NOT_FOUND).

    :param evidences: List of Evidence objects from all candidates.
    :return: Best Evidence, or None if the list is empty.
    """
    if not evidences:
        return None
    matched = [e for e in evidences if e.contributor_match and e.phash_distance is not None]
    if matched:
        return min(matched, key=lambda e: e.phash_distance)  # type: ignore[arg-type]
    with_distance = [e for e in evidences if e.phash_distance is not None]
    if with_distance:
        return min(with_distance, key=lambda e: e.phash_distance)  # type: ignore[arg-type]
    return evidences[0]


def run_detection(
    all_data: List[dict],
    filtered_data: List[dict],
    csv_path: str,
    banks: List[str],
    contributor_name: str = DEFAULT_CONTRIBUTOR_NAME,
    dry_run: bool = False,
    report_dir: str = DEFAULT_REPORT_DIR,
    headless: bool = True,
    hash_cache_path: str = DEFAULT_HASH_CACHE_PATH,
    preview_cache_dir: str = DEFAULT_PREVIEW_CACHE_DIR,
) -> List[DetectionResult]:
    """Run the full detection pipeline for every record × bank combination.

    :param all_data: Complete CSV data (used for writing results back).
    :param filtered_data: Records already filtered for the correct status.
    :param csv_path: Path to PhotoMedia.csv.
    :param banks: Canonical bank names to process.
    :param contributor_name: Your contributor username for identity matching.
    :param dry_run: When True, skip writing FOUND results back to the CSV.
    :param report_dir: Directory where the audit CSV is written.
    :param headless: Run browser headless when True.
    :param hash_cache_path: Path to the SQLite hash cache file.
    :param preview_cache_dir: Directory for caching downloaded preview images.
    :return: List of DetectionResult objects (one per record × bank pair).
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(report_dir, exist_ok=True)
    audit_path = os.path.join(report_dir, f"audit_{ts}.csv")
    audit_writer = AuditWriter(audit_path)
    hash_cache = HashCache(hash_cache_path)
    results: List[DetectionResult] = []

    file_to_index: Dict[str, int] = {row.get(COL_FILE, ""): i for i, row in enumerate(all_data)}

    with HttpClient() as http_client:
        for row in filtered_data:
            for bank_name in banks:
                adapter = get_adapter(bank_name)
                if adapter is None:
                    continue

                record = build_photo_record(row, bank_name)
                if record is None:
                    continue

                try:
                    candidates: List[Candidate] = adapter.discover(
                        record,
                        http_client=http_client,
                        headless=headless,
                    )
                except Exception as exc:
                    logging.error("Discovery error for %s / %s: %s", record.file, bank_name, exc)
                    candidates = []

                evidences: List[Evidence] = []
                for candidate in candidates:
                    ev = build_evidence(
                        local_file_path=record.local_file_path,
                        contributor_name=contributor_name,
                        candidate=candidate,
                        http_client=http_client,
                        hash_cache=hash_cache,
                        preview_cache_dir=preview_cache_dir,
                    )
                    evidences.append(ev)

                best = _select_best_evidence(evidences)
                outcome, reason = decide(best)
                now = datetime.now().isoformat()

                result = DetectionResult(
                    record_file=record.file,
                    bank=bank_name,
                    outcome=outcome,
                    matched_url=best.candidate.url if best and outcome == "FOUND" else None,
                    matched_id=best.candidate.asset_id if best and outcome == "FOUND" else None,
                    evidence=best,
                    reason=reason,
                    timestamp=now,
                )
                results.append(result)

                audit_writer.write(
                    AuditEntry(
                        timestamp=now,
                        local_file=record.file,
                        bank=bank_name,
                        result=outcome,
                        candidate_url=result.matched_url,
                        candidate_id=result.matched_id,
                        contributor_match=best.contributor_match if best else None,
                        phash_distance=best.phash_distance if best else None,
                        dhash_distance=best.dhash_distance if best else None,
                        dimension_match=best.dimension_match if best else None,
                        preview_url=best.candidate.preview_url if best else None,
                        reason=reason,
                    )
                )

                if outcome == "FOUND":
                    logging.info("FOUND: %s on %s → %s", record.file, bank_name, result.matched_url)
                    if not dry_run:
                        idx = file_to_index.get(record.file)
                        if idx is not None:
                            status_col = f"{bank_name} {STATUS_COLUMN_KEYWORD}"
                            all_data[idx][status_col] = STATUS_APPROVED
                            save_csv_with_backup(all_data, csv_path)
                else:
                    logging.debug("NOT_FOUND: %s on %s (%s)", record.file, bank_name, reason)

    logging.info("Detection pipeline complete. %d results. Audit: %s", len(results), audit_path)
    return results