"""
Normalize photobank names across codebase.

This script finds and replaces inconsistent photobank naming patterns
with canonical names (no spaces, proper capitalization).

Usage:
    python scripts/normalize_photobank_names.py --dry-run  # Preview changes
    python scripts/normalize_photobank_names.py            # Apply changes
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Normalization map: old_name -> canonical_name
NORMALIZATION_MAP = {
    "GettyImages": "GettyImages",
    "Dreamstime": "Dreamstime",
    "AdobeStock": "AdobeStock",
    "DepositPhotos": "DepositPhotos",
    "BigStockPhoto": "BigStockPhoto",
    "ShutterStock": "ShutterStock",  # In case of space variant
    # Note: "CanStockPhoto" is already canonical, no normalization needed
}

# File patterns to scan
PYTHON_FILE_PATTERN = "**/*.py"
CSV_FILES = [
    "launchphotobanks/bank_urls.csv",
]

# Directories to exclude from scanning
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "backups_issue_116",
    "batch_state",
}


class NormalizationReport:
    """Track normalization changes for reporting."""

    def __init__(self) -> None:
        """Initialize empty report."""
        self.changes: List[Tuple[str, int, str, str]] = []  # (file, line, old, new)
        self.files_modified: set = set()

    def add_change(self, file_path: str, line_num: int, old_text: str, new_text: str) -> None:
        """Add a change to the report.

        Args:
            file_path: Path to modified file
            line_num: Line number where change occurred
            old_text: Original text
            new_text: Replacement text
        """
        self.changes.append((file_path, line_num, old_text, new_text))
        self.files_modified.add(file_path)

    def print_summary(self) -> None:
        """Print summary of all changes."""
        if not self.changes:
            print("No changes needed - all photobank names are already normalized.")
            return

        print(f"\n=== Normalization Report ===")
        print(f"Total changes: {len(self.changes)}")
        print(f"Files modified: {len(self.files_modified)}")
        print(f"\nChanges by file:")

        current_file = None
        for file_path, line_num, old_text, new_text in sorted(self.changes):
            if file_path != current_file:
                print(f"\n{file_path}:")
                current_file = file_path
            print(f"  Line {line_num}: '{old_text}' -> '{new_text}'")


def should_exclude_path(path: Path) -> bool:
    """Check if path should be excluded from scanning.

    Args:
        path: Path to check

    Returns:
        True if path should be excluded
    """
    parts = path.parts
    return any(excluded in parts for excluded in EXCLUDE_DIRS)


def normalize_python_file(file_path: Path, dry_run: bool, report: NormalizationReport) -> None:
    """Normalize photobank names in a Python file.

    Args:
        file_path: Path to Python file
        dry_run: If True, only report changes without modifying
        report: Report object to track changes
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_lines = f.readlines()
    except UnicodeDecodeError:
        # Skip binary or non-UTF8 files
        return

    modified_lines = []
    file_modified = False

    for line_num, line in enumerate(original_lines, start=1):
        modified_line = line

        # Replace each old name with canonical name
        for old_name, new_name in NORMALIZATION_MAP.items():
            # Pattern 1: String literals "old_name" or 'old_name'
            pattern1 = re.compile(rf'(["\'])({re.escape(old_name)})\1')
            if pattern1.search(modified_line):
                replacement = rf'\1{new_name}\1'
                new_line = pattern1.sub(replacement, modified_line)
                if new_line != modified_line:
                    report.add_change(str(file_path), line_num, old_name, new_name)
                    modified_line = new_line
                    file_modified = True

            # Pattern 2: Dictionary keys or variable names (word boundary)
            # Match old_name only when it's a complete word
            pattern2 = re.compile(rf'\b{re.escape(old_name)}\b')
            if pattern2.search(modified_line) and old_name not in modified_line.replace(new_name, ""):
                # Double check this isn't inside a string we already replaced
                # This handles cases like: BANKS = ["GettyImages", ...]
                new_line = pattern2.sub(new_name, modified_line)
                if new_line != modified_line and modified_line.count('"') % 2 == 0:
                    # Only apply if not breaking string literals
                    report.add_change(str(file_path), line_num, old_name, new_name)
                    modified_line = new_line
                    file_modified = True

        modified_lines.append(modified_line)

    # Write changes if not dry-run
    if file_modified and not dry_run:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(modified_lines)


def normalize_csv_file(file_path: Path, dry_run: bool, report: NormalizationReport) -> None:
    """Normalize photobank names in CSV file headers and data.

    Args:
        file_path: Path to CSV file
        dry_run: If True, only report changes without modifying
        report: Report object to track changes
    """
    if not file_path.exists():
        print(f"Warning: CSV file not found: {file_path}")
        return

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    if not rows:
        return

    # Normalize headers and data
    modified = False
    for row_num, row in enumerate(rows):
        for col_num, cell in enumerate(row):
            for old_name, new_name in NORMALIZATION_MAP.items():
                if old_name in cell:
                    new_cell = cell.replace(old_name, new_name)
                    if new_cell != cell:
                        report.add_change(
                            str(file_path),
                            row_num + 1,
                            f"{cell}",
                            f"{new_cell}"
                        )
                        rows[row_num][col_num] = new_cell
                        modified = True

    # Write changes if not dry-run
    if modified and not dry_run:
        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


def normalize_photomedia_csv(dry_run: bool, report: NormalizationReport) -> None:
    """Normalize PhotoMedia.csv column headers.

    Args:
        dry_run: If True, only report changes without modifying
        report: Report object to track changes
    """
    csv_path = Path(r"L:\Můj disk\XLS\Fotobanky\PhotoMedia.csv")

    if not csv_path.exists():
        print(f"Warning: PhotoMedia.csv not found at {csv_path}")
        return

    print(f"Normalizing PhotoMedia.csv column headers...")

    try:
        # Read CSV
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        if not fieldnames:
            return

        # Normalize column names
        new_fieldnames = []
        for field in fieldnames:
            new_field = field
            for old_name, new_name in NORMALIZATION_MAP.items():
                if old_name in field:
                    new_field = field.replace(old_name, new_name)
                    if new_field != field:
                        report.add_change(
                            str(csv_path),
                            1,  # Header row
                            field,
                            new_field
                        )
            new_fieldnames.append(new_field)

        # Write back if modified and not dry-run
        if new_fieldnames != list(fieldnames) and not dry_run:
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=new_fieldnames)
                writer.writeheader()

                # Write rows with updated fieldnames
                for row in rows:
                    new_row = {}
                    for old_field, new_field in zip(fieldnames, new_fieldnames):
                        new_row[new_field] = row[old_field]
                    writer.writerow(new_row)

    except Exception as e:
        print(f"Error processing PhotoMedia.csv: {e}")


def normalize_codebase(dry_run: bool = True) -> None:
    """Scan and normalize all photobank names in the codebase.

    Args:
        dry_run: If True, only report changes without modifying files
    """
    repo_root = Path(__file__).parent.parent
    report = NormalizationReport()

    print(f"{'DRY RUN: ' if dry_run else ''}Normalizing photobank names...")
    print(f"Repository root: {repo_root}")

    # 1. Scan all Python files
    print("\nScanning Python files...")
    python_files = [
        p for p in repo_root.rglob(PYTHON_FILE_PATTERN)
        if not should_exclude_path(p)
    ]

    for py_file in python_files:
        normalize_python_file(py_file, dry_run, report)

    # 2. Normalize specific CSV files
    print("\nNormalizing CSV files...")
    for csv_file in CSV_FILES:
        csv_path = repo_root / csv_file
        normalize_csv_file(csv_path, dry_run, report)

    # 3. Normalize PhotoMedia.csv headers
    normalize_photomedia_csv(dry_run, report)

    # 4. Print report
    report.print_summary()

    if dry_run and report.changes:
        print(f"\n{'='*60}")
        print("This was a DRY RUN - no files were modified.")
        print("Run without --dry-run to apply changes.")
        print(f"{'='*60}")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success)
    """
    parser = argparse.ArgumentParser(
        description="Normalize photobank names across codebase"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )

    args = parser.parse_args()

    try:
        normalize_codebase(dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())