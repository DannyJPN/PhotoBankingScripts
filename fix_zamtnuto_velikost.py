"""
Fix 'zamítnuto - velikost' status values in PhotoMedia.csv.

Rules:
- If ALL other bank statuses on the same record are 'nezpracováno' or 'nedostupný'
  → replace 'zamítnuto - velikost' with 'nezpracováno'
- Otherwise (some other bank has a real status like připraveno/schváleno/záložní/...)
  → replace 'zamítnuto - velikost' with 'připraveno'
"""
from __future__ import annotations

import csv
import logging
import os
import shutil
import sys
from datetime import datetime
from typing import Dict, List

CSV_PATH = "L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv"
STATUS_KEYWORD = "status"
ZAMTNUTO = "zamítnuto - velikost"
EXEMPT_STATUSES = {"nezpracováno", "nedostupný", ""}


def load_csv(path: str) -> List[Dict[str, str]]:
    """Load CSV preserving column order."""
    records = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        for row in reader:
            records.append(dict(row))
    logging.info("Loaded %d records from %s", len(records), path)
    return records


def save_csv_with_backup(data: List[Dict[str, str]], path: str) -> None:
    """Create timestamped backup then overwrite original."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{os.path.splitext(path)[0]}_{timestamp}.csv"
    shutil.copy2(path, backup_path)
    logging.info("Backup created: %s", backup_path)

    fieldnames = list(data[0].keys()) if data else []
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=",", quotechar='"')
        writer.writeheader()
        writer.writerows(data)
    logging.info("Saved %d records to %s", len(data), path)


def fix_record(record: Dict[str, str]) -> int:
    """
    Apply fix to a single record in-place.
    Returns count of changed fields.
    """
    status_cols = [k for k in record if STATUS_KEYWORD in k.lower()]

    zam_cols = [c for c in status_cols if record[c] == ZAMTNUTO]
    if not zam_cols:
        return 0

    other_vals = {record[c] for c in status_cols if c not in zam_cols}
    all_exempt = other_vals <= EXEMPT_STATUSES

    new_status = "nezpracováno" if all_exempt else "připraveno"
    for col in zam_cols:
        record[col] = new_status

    return len(zam_cols)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    records = load_csv(CSV_PATH)

    changed_records = 0
    changed_fields = 0
    to_nezpracovano = 0
    to_pripraveno = 0

    for rec in records:
        status_cols = [k for k in rec if STATUS_KEYWORD in k.lower()]
        zam_cols = [c for c in status_cols if rec[c] == ZAMTNUTO]
        if not zam_cols:
            continue

        other_vals = {rec[c] for c in status_cols if c not in zam_cols}
        all_exempt = other_vals <= EXEMPT_STATUSES
        new_status = "nezpracováno" if all_exempt else "připraveno"

        for col in zam_cols:
            rec[col] = new_status

        changed_records += 1
        changed_fields += len(zam_cols)
        if all_exempt:
            to_nezpracovano += len(zam_cols)
        else:
            to_pripraveno += len(zam_cols)

    logging.info("Records changed:  %d", changed_records)
    logging.info("Fields changed:   %d", changed_fields)
    logging.info("  → nezpracováno: %d", to_nezpracovano)
    logging.info("  → připraveno:   %d", to_pripraveno)

    if changed_fields == 0:
        logging.info("Nothing to change.")
        sys.exit(0)

    save_csv_with_backup(records, CSV_PATH)
    logging.info("Done.")


if __name__ == "__main__":
    main()
