#!/usr/bin/env python
"""
One-time script to fix date format in PhotoMedia.csv.
Converts "Datum přípravy" from various formats to DD.MM.YYYY
"""
import csv
import os
import shutil
from datetime import datetime

CSV_PATH = r"L:\Můj disk\XLS\Fotobanky\PhotoMedia.csv"
COL_PREP_DATE = "Datum přípravy"

def parse_date(date_str):
    """Parse date from various formats and return DD.MM.YYYY format."""
    if not date_str or not date_str.strip():
        return ""

    date_str = date_str.strip()

    # Already in correct format DD.MM.YYYY
    if len(date_str) == 10 and date_str[2] == '.' and date_str[5] == '.':
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            return date_str  # Already correct
        except:
            pass

    # Try various formats
    formats = [
        "%Y-%m-%d %H:%M:%S",     # 2025-01-15 14:30:45
        "%Y-%m-%d",              # 2025-01-15
        "%Y:%m:%d %H:%M:%S",     # 2025:01:15 14:30:45 (EXIF)
        "%Y:%m:%d",              # 2025:01:15
        "%d.%m.%Y %H:%M:%S",     # 15.01.2025 14:30:45
        "%d/%m/%Y",              # 15/01/2025
        "%m/%d/%Y",              # 01/15/2025 (US format)
    ]

    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%d.%m.%Y")
        except ValueError:
            continue

    # If nothing worked, return original
    print(f"WARNING: Could not parse date: '{date_str}'")
    return date_str

def main():
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV file not found: {CSV_PATH}")
        return 1

    # Create backup
    backup_path = CSV_PATH + ".backup_before_date_fix"
    shutil.copy2(CSV_PATH, backup_path)
    print(f"Created backup: {backup_path}")

    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} records")

    # Fix dates
    fixed_count = 0
    for row in rows:
        if COL_PREP_DATE in row:
            original = row[COL_PREP_DATE]
            fixed = parse_date(original)
            if fixed != original:
                row[COL_PREP_DATE] = fixed
                fixed_count += 1
                print(f"Fixed: '{original}' -> '{fixed}'")

    print(f"\nFixed {fixed_count} dates")

    # Write back
    with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated CSV: {CSV_PATH}")
    return 0

if __name__ == "__main__":
    exit(main())