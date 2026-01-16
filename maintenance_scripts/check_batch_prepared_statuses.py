#!/usr/bin/env python3
"""
Check prepared statuses for records from selected batches.

Targets:
- last completed batch with size 500
- the completed batch immediately before it
- all completed batches newer than that last-500 batch
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root and updatemediadatabase to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "updatemediadatabase"))

from shared.file_operations import load_csv

from updatemedialdatabaselib.constants import (
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_LIMITS_CSV_PATH,
    COLUMN_FILENAME,
    COLUMN_TITLE,
    COLUMN_DESCRIPTION,
    COLUMN_KEYWORDS,
    COLUMN_WIDTH,
    COLUMN_HEIGHT,
    COLUMN_RESOLUTION,
    STATUS_PREPARED,
    TYPE_PHOTO,
    TYPE_VIDEO,
    TYPE_VECTOR,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VECTOR_EXTENSIONS
)
from updatemedialdatabaselib.photo_analyzer import validate_against_limits

# Default base directory for batch state
base_dir = project_root / "givephotobankreadymediafiles"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check prepared statuses for recent batches with size 500."
    )
    parser.add_argument("--media_csv", type=str, default=DEFAULT_MEDIA_CSV_PATH,
                        help="Path to PhotoMedia.csv")
    parser.add_argument("--limits_csv", type=str, default=DEFAULT_LIMITS_CSV_PATH,
                        help="Path to PhotoLimits.csv")
    parser.add_argument("--batch_registry", type=str,
                        default=str(base_dir / "batch_state" / "batch_registry.json"),
                        help="Path to batch_registry.json")
    parser.add_argument("--batches_dir", type=str,
                        default=str(base_dir / "batch_state" / "batches"),
                        help="Path to batch_state/batches directory")
    parser.add_argument("--report_csv", type=str, default="",
                        help="Optional path to write a CSV report")
    return parser.parse_args()


def load_registry(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_state_file(batches_dir: Path, batch_id: str) -> Dict[str, object]:
    state_path = batches_dir / batch_id / "state.json"
    if not state_path.exists():
        return {}
    with open(state_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def infer_media_type(path_value: str) -> str:
    ext = os.path.splitext(path_value)[1].lower()
    if ext in VIDEO_EXTENSIONS:
        return TYPE_VIDEO
    if ext in VECTOR_EXTENSIONS:
        return TYPE_VECTOR
    if ext in IMAGE_EXTENSIONS:
        return TYPE_PHOTO
    return ""


def build_metadata(record: Dict[str, str], file_path: str) -> Dict[str, object]:
    metadata: Dict[str, object] = {
        "Filename": record.get(COLUMN_FILENAME, ""),
        "Path": file_path,
        "Type": infer_media_type(file_path)
    }
    width = record.get(COLUMN_WIDTH, "").strip()
    height = record.get(COLUMN_HEIGHT, "").strip()
    if width.isdigit():
        metadata["Width"] = int(width)
    if height.isdigit():
        metadata["Height"] = int(height)
    resolution = record.get(COLUMN_RESOLUTION, "").strip()
    if resolution:
        metadata["Resolution"] = resolution
    return metadata


def find_target_batches(registry: Dict[str, object], batches_dir: Path) -> Tuple[List[str], str]:
    completed = registry.get("completed_batches", [])
    completed_sorted = sorted(completed, key=lambda x: x.get("completed_at", ""))

    batch_with_counts: List[Tuple[str, int]] = []
    for entry in completed_sorted:
        batch_id = entry.get("batch_id")
        if not batch_id:
            continue
        state = load_state_file(batches_dir, batch_id)
        files = state.get("files", [])
        batch_with_counts.append((batch_id, len(files)))

    last_500_index = -1
    for idx, (_batch_id, count) in enumerate(batch_with_counts):
        if count == 500:
            last_500_index = idx

    if last_500_index == -1:
        return [], ""

    target_ids = []
    last_500_batch = batch_with_counts[last_500_index][0]
    target_ids.append(last_500_batch)

    if last_500_index > 0:
        target_ids.append(batch_with_counts[last_500_index - 1][0])

    # all newer than last-500 batch
    for idx in range(last_500_index + 1, len(batch_with_counts)):
        target_ids.append(batch_with_counts[idx][0])

    return target_ids, last_500_batch


def has_complete_metadata(record: Dict[str, str]) -> bool:
    title = record.get(COLUMN_TITLE, "").strip()
    description = record.get(COLUMN_DESCRIPTION, "").strip()
    keywords = record.get(COLUMN_KEYWORDS, "").strip()
    return bool(title and description and keywords)


def main() -> None:
    args = parse_arguments()
    registry = load_registry(args.batch_registry)
    batches_dir = Path(args.batches_dir)
    media_csv = load_csv(args.media_csv)
    limits = load_csv(args.limits_csv)

    records_by_filename: Dict[str, List[Dict[str, str]]] = {}
    for record in media_csv:
        filename = record.get(COLUMN_FILENAME, "")
        if not filename:
            continue
        records_by_filename.setdefault(filename, []).append(record)

    target_batches, last_500 = find_target_batches(registry, batches_dir)
    if not target_batches:
        print("No completed batch with size 500 found.")
        return

    print(f"Last size-500 batch: {last_500}")
    print(f"Target batches: {len(target_batches)}")

    report_rows: List[Dict[str, str]] = []
    total_files = 0
    missing_records = 0
    prepared_mismatches = 0

    for batch_id in target_batches:
        state = load_state_file(batches_dir, batch_id)
        files = state.get("files", [])
        for entry in files:
            file_path = entry.get("file_path", "")
            filename = os.path.basename(file_path)
            total_files += 1
            candidates = records_by_filename.get(filename, [])
            if not candidates:
                missing_records += 1
                report_rows.append({
                    "batch_id": batch_id,
                    "file": filename,
                    "issue": "missing_record"
                })
                continue

            record = candidates[0]
            metadata = build_metadata(record, file_path)
            validation_results = validate_against_limits(metadata, limits)

            for status_col, status_value in record.items():
                if "status" not in status_col.lower():
                    continue
                bank_name = status_col.replace("status", "").strip()
                is_valid = validation_results.get(bank_name, True)
                if is_valid and status_value.strip().lower() != STATUS_PREPARED.lower():
                    prepared_mismatches += 1
                    report_rows.append({
                        "batch_id": batch_id,
                        "file": filename,
                        "bank": bank_name,
                        "status": status_value,
                        "expected": STATUS_PREPARED,
                        "metadata_complete": str(has_complete_metadata(record)),
                        "issue": "missing_prepared"
                    })

    print(f"Files scanned: {total_files}")
    print(f"Missing records in PhotoMedia.csv: {missing_records}")
    print(f"Missing prepared statuses: {prepared_mismatches}")

    if args.report_csv:
        with open(args.report_csv, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=sorted({k for row in report_rows for k in row.keys()}))
            writer.writeheader()
            writer.writerows(report_rows)
        print(f"Wrote report: {args.report_csv}")


if __name__ == "__main__":
    main()
