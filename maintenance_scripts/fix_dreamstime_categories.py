#!/usr/bin/env python
"""
Maintenance script to re-validate and fix Dreamstime category assignments.

Processes all batch-processed files with complete metadata (title, description, keywords)
and regenerates Dreamstime categories using AI based on text metadata.

Edited files (_bw, _negative, etc.) inherit categories from their originals.

Usage:
    python fix_dreamstime_categories.py [--dry-run] [--limit N]
"""
import argparse
import csv
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from givephotobankreadymediafiles.givephotobankreadymediafileslib.constants import (
    DEFAULT_MEDIA_CSV_PATH,
    DEFAULT_CATEGORIES_CSV_PATH,
    BATCH_STATE_DIR,
    ALTERNATIVE_EDIT_TAGS,
    COL_FILE,
    COL_TITLE,
    COL_DESCRIPTION,
    COL_KEYWORDS,
    COL_PATH,
    COL_ORIGINAL,
    ORIGINAL_YES,
    ORIGINAL_NO,
    get_category_column,
)
from givephotobankreadymediafiles.shared.logging_config import setup_logging

# Constants
DREAMSTIME_CATEGORY_COLUMN = get_category_column("Dreamstime")
OPENAI_MODEL = "gpt-4o-mini"
BATCH_DIR = os.path.join(BATCH_STATE_DIR, "batches")


def load_valid_dreamstime_categories(csv_path: str) -> List[str]:
    """Load valid Dreamstime categories from PhotoCategories.csv."""
    categories = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        try:
            dreamstime_idx = header.index("Dreamstime")
        except ValueError:
            logging.error("Dreamstime column not found in PhotoCategories.csv")
            return []

        for row in reader:
            if len(row) > dreamstime_idx and row[dreamstime_idx].strip():
                categories.append(row[dreamstime_idx].strip())

    logging.info(f"Loaded {len(categories)} valid Dreamstime categories")
    return categories


def load_photomedia_csv(csv_path: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Load PhotoMedia.csv and return fieldnames and rows."""
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    logging.info(f"Loaded {len(rows)} records from PhotoMedia.csv")
    return fieldnames, rows


def save_photomedia_csv(
    csv_path: str, fieldnames: List[str], rows: List[Dict[str, str]]
) -> None:
    """Save PhotoMedia.csv."""
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logging.info(f"Saved {len(rows)} records to PhotoMedia.csv")


def get_batch_processed_files() -> Set[str]:
    """Get set of file paths that appear in any batch state.json."""
    batch_files = set()

    if not os.path.exists(BATCH_DIR):
        logging.warning(f"Batch directory not found: {BATCH_DIR}")
        return batch_files

    for batch_id in os.listdir(BATCH_DIR):
        state_path = os.path.join(BATCH_DIR, batch_id, "state.json")
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                for file_entry in state.get("files", []):
                    file_path = file_entry.get("file_path", "")
                    if file_path:
                        batch_files.add(normalize_path(file_path))
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Error reading {state_path}: {e}")

    logging.info(f"Found {len(batch_files)} files in batch states")
    return batch_files


def normalize_path(path: str) -> str:
    """Normalize path for comparison (lowercase, forward slashes)."""
    return path.lower().replace("\\", "/")


def has_complete_metadata(row: Dict[str, str]) -> bool:
    """Check if row has title, description, and keywords filled."""
    title = row.get(COL_TITLE, "").strip()
    description = row.get(COL_DESCRIPTION, "").strip()
    keywords = row.get(COL_KEYWORDS, "").strip()
    return bool(title and description and keywords)


def is_edited_file(row: Dict[str, str]) -> bool:
    """Check if file is an edited version (not original)."""
    original_flag = row.get(COL_ORIGINAL, "").strip().lower()
    if original_flag == ORIGINAL_NO.lower():
        return True

    filename = row.get(COL_FILE, "")
    for suffix in ALTERNATIVE_EDIT_TAGS.keys():
        if suffix in filename.lower():
            return True

    return False


def get_original_path(edited_path: str) -> Optional[str]:
    """Get original file path from edited file path by removing edit suffix."""
    path_lower = edited_path.lower()
    for suffix in ALTERNATIVE_EDIT_TAGS.keys():
        if suffix in path_lower:
            base, ext = os.path.splitext(edited_path)
            for s in ALTERNATIVE_EDIT_TAGS.keys():
                if base.lower().endswith(s):
                    original_base = base[: -len(s)]
                    return original_base + ext
    return None


def parse_categories_string(categories_str: str) -> Set[str]:
    """Parse categories string to set (comma-separated)."""
    if not categories_str or not categories_str.strip():
        return set()
    return {c.strip() for c in categories_str.split(",") if c.strip()}


def categories_to_string(categories: List[str]) -> str:
    """Convert categories list to comma-separated string."""
    return ", ".join(sorted(categories))


def regenerate_categories_via_ai(
    title: str,
    description: str,
    keywords: str,
    valid_categories: List[str],
    api_key: str,
) -> List[str]:
    """
    Use OpenAI API to regenerate Dreamstime categories based on text metadata.

    Args:
        title: Photo title
        description: Photo description
        keywords: Keywords string
        valid_categories: List of valid Dreamstime categories
        api_key: OpenAI API key

    Returns:
        List of selected Dreamstime categories (up to 3)
    """
    logging.debug(f"Regenerating categories for: title='{title[:50]}...'")

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        logging.debug("OpenAI client created successfully")
    except ImportError as e:
        logging.error(f"OpenAI package not installed: {e}. Run: pip install openai")
        return []
    except Exception as e:
        logging.error(f"Failed to create OpenAI client: {e}")
        return []

    # Build hierarchical category display
    hierarchy: Dict[str, List[str]] = {}
    for cat in valid_categories:
        if " -> " in cat:
            main, sub = cat.split(" -> ", 1)
            if main not in hierarchy:
                hierarchy[main] = []
            hierarchy[main].append(sub)

    if not hierarchy:
        logging.error("No valid hierarchical categories found in valid_categories list")
        return []

    categories_text = ""
    for main_cat in sorted(hierarchy.keys()):
        subs = ", ".join(sorted(hierarchy[main_cat]))
        categories_text += f"{main_cat.upper()}: {subs}\n"

    prompt = f"""Based on the following photo metadata, select UP TO 3 most appropriate Dreamstime categories.

PHOTO METADATA:
Title: {title}
Description: {description}
Keywords: {keywords}

AVAILABLE CATEGORIES (select in format "MainCategory -> SubCategory"):
{categories_text}

RULES:
- Select categories based on the VISUAL CONTENT described in the metadata
- You may select from ANY main category - not limited to one
- Output format MUST be exactly: "MainCategory -> SubCategory"
- If only 1-2 categories truly fit, select only those
- DO NOT select unrelated categories just to reach 3

Return ONLY the selected categories, one per line, nothing else."""

    logging.debug(f"Sending request to OpenAI model: {OPENAI_MODEL}")

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )

        content = response.choices[0].message.content.strip()
        logging.debug(f"OpenAI raw response:\n{content}")

        selected = []
        # Build case-insensitive lookup: lowercase -> original
        valid_lookup = {cat.lower(): cat for cat in valid_categories}
        rejected_lines = []

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Try exact match first
            if line in valid_lookup.values():
                selected.append(line)
                logging.debug(f"  Accepted category (exact): {line}")
            # Try case-insensitive match
            elif line.lower() in valid_lookup:
                original_cat = valid_lookup[line.lower()]
                selected.append(original_cat)
                logging.debug(f"  Accepted category (case-fixed): {line} -> {original_cat}")
            else:
                rejected_lines.append(line)
                logging.debug(f"  Rejected (not in valid set): {line}")

        if rejected_lines:
            logging.warning(
                f"OpenAI returned invalid categories: {rejected_lines}. "
                f"Valid selected: {selected}"
            )

        if not selected:
            logging.warning(
                f"No valid categories extracted from OpenAI response. "
                f"Raw response: {content[:200]}"
            )

        return selected[:3]

    except Exception as e:
        logging.error(f"OpenAI API error: {type(e).__name__}: {e}", exc_info=True)
        return []


def find_batch_files_for_path(file_path: str) -> List[Tuple[str, str, str]]:
    """
    Find all batch files (state.json, results.json) containing this file.

    Returns:
        List of tuples: (batch_id, state_path, results_path)
    """
    matches = []
    normalized = normalize_path(file_path)

    if not os.path.exists(BATCH_DIR):
        return matches

    for batch_id in os.listdir(BATCH_DIR):
        batch_path = os.path.join(BATCH_DIR, batch_id)
        state_path = os.path.join(batch_path, "state.json")
        results_path = os.path.join(batch_path, "results.json")

        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                for file_entry in state.get("files", []):
                    if normalize_path(file_entry.get("file_path", "")) == normalized:
                        matches.append((batch_id, state_path, results_path))
                        break
            except (json.JSONDecodeError, IOError):
                continue

    return matches


def update_batch_files(
    file_path: str, new_categories: List[str], dry_run: bool = False
) -> int:
    """
    Update Dreamstime categories in batch state.json and results.json files.

    Returns:
        Number of batch files updated
    """
    updated = 0
    normalized = normalize_path(file_path)

    for batch_id, state_path, results_path in find_batch_files_for_path(file_path):
        # Update state.json
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)

                modified = False
                for file_entry in state.get("files", []):
                    if normalize_path(file_entry.get("file_path", "")) == normalized:
                        result = file_entry.get("result", {})
                        if isinstance(result, dict):
                            categories = result.get("categories", {})
                            if isinstance(categories, dict):
                                categories["dreamstime"] = new_categories
                                result["categories"] = categories
                                file_entry["result"] = result
                                modified = True

                if modified and not dry_run:
                    with open(state_path, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2, ensure_ascii=False)
                    updated += 1
                    logging.debug(f"Updated state.json in {batch_id}")

            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Error updating {state_path}: {e}")

        # Update results.json
        if os.path.exists(results_path):
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    results = json.load(f)

                modified = False
                for custom_id, entry in results.items():
                    if normalize_path(entry.get("file_path", "")) == normalized:
                        result = entry.get("result", {})
                        if isinstance(result, dict):
                            categories = result.get("categories", {})
                            if isinstance(categories, dict):
                                categories["dreamstime"] = new_categories
                                result["categories"] = categories
                                entry["result"] = result
                                modified = True

                if modified and not dry_run:
                    with open(results_path, "w", encoding="utf-8") as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    logging.debug(f"Updated results.json in {batch_id}")

            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Error updating {results_path}: {e}")

    return updated


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Re-validate and fix Dreamstime categories for batch-processed files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of files to process (0 = unlimited)",
    )
    parser.add_argument(
        "--media-csv",
        type=str,
        default=DEFAULT_MEDIA_CSV_PATH,
        help="Path to PhotoMedia.csv",
    )
    parser.add_argument(
        "--categories-csv",
        type=str,
        default=DEFAULT_CATEGORIES_CSV_PATH,
        help="Path to PhotoCategories.csv",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="Directory for log files",
    )
    args = parser.parse_args()

    # Setup logging using shared module
    log_file = os.path.join(
        args.log_dir, f"fix_dreamstime_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    os.makedirs(args.log_dir, exist_ok=True)
    setup_logging(debug=args.debug, log_file=log_file)
    logging.info("=" * 60)
    logging.info("Dreamstime Category Maintenance Script")
    logging.info("=" * 60)

    if args.dry_run:
        logging.info("DRY RUN MODE - no changes will be made")

    # Get OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logging.error("OPENAI_API_KEY environment variable not set")
        return 1

    # Load valid categories
    valid_categories = load_valid_dreamstime_categories(args.categories_csv)
    if not valid_categories:
        return 1

    # Load PhotoMedia.csv
    if not os.path.exists(args.media_csv):
        logging.error(f"PhotoMedia.csv not found: {args.media_csv}")
        return 1

    fieldnames, rows = load_photomedia_csv(args.media_csv)

    # Create backup
    if not args.dry_run:
        backup_path = args.media_csv + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(args.media_csv, backup_path)
        logging.info(f"Created backup: {backup_path}")

    # Get batch-processed files
    batch_files = get_batch_processed_files()

    # Build path-to-row index
    path_to_row: Dict[str, Dict[str, str]] = {}
    for row in rows:
        path = row.get(COL_PATH, "")
        if path:
            path_to_row[normalize_path(path)] = row

    # Separate originals and edited files
    originals_to_process = []
    edited_to_process = []

    for row in rows:
        path = row.get(COL_PATH, "")
        if not path:
            continue

        normalized = normalize_path(path)
        if normalized not in batch_files:
            continue

        if not has_complete_metadata(row):
            continue

        if is_edited_file(row):
            edited_to_process.append(row)
        else:
            originals_to_process.append(row)

    logging.info(f"Found {len(originals_to_process)} originals to process")
    logging.info(f"Found {len(edited_to_process)} edited files to process")

    if args.limit > 0:
        originals_to_process = originals_to_process[: args.limit]
        logging.info(f"Limited to {len(originals_to_process)} originals")

    # Statistics
    stats = {
        "processed": 0,
        "updated": 0,
        "unchanged": 0,
        "errors": 0,
        "edited_updated": 0,
    }

    # Process originals with progress bar
    updated_originals: Dict[str, List[str]] = {}  # path -> new categories

    logging.info("Processing originals...")
    pbar = tqdm(originals_to_process, desc="Originals", unit="file")
    for row in pbar:
        stats["processed"] += 1

        title = row.get(COL_TITLE, "").strip()
        description = row.get(COL_DESCRIPTION, "").strip()
        keywords = row.get(COL_KEYWORDS, "").strip()
        file_path = row.get(COL_PATH, "")
        filename = os.path.basename(file_path)
        pbar.set_postfix_str(filename[:40])

        current_cats = parse_categories_string(row.get(DREAMSTIME_CATEGORY_COLUMN, ""))

        # Regenerate categories
        new_cats = regenerate_categories_via_ai(
            title, description, keywords, valid_categories, api_key
        )

        if not new_cats:
            stats["errors"] += 1
            logging.warning(f"Failed to regenerate categories for: {file_path}")
            continue

        new_cats_set = set(new_cats)

        # Compare (order-independent)
        if new_cats_set == current_cats:
            stats["unchanged"] += 1
            logging.debug(f"Unchanged: {file_path}")
        else:
            stats["updated"] += 1
            logging.info(
                f"Updated: {file_path}\n  Old: {current_cats}\n  New: {new_cats_set}"
            )

            # Store for edited files lookup
            updated_originals[normalize_path(file_path)] = new_cats

            if not args.dry_run:
                # Update PhotoMedia.csv row
                row[DREAMSTIME_CATEGORY_COLUMN] = categories_to_string(new_cats)

                # Update batch files
                update_batch_files(file_path, new_cats)

    # Process edited files - inherit from originals
    logging.info("Processing edited files...")
    pbar_edited = tqdm(edited_to_process, desc="Edited files", unit="file")
    for row in pbar_edited:
        file_path = row.get(COL_PATH, "")
        filename = os.path.basename(file_path)
        pbar_edited.set_postfix_str(filename[:40])
        original_path = get_original_path(file_path)

        if not original_path:
            logging.debug(f"Could not determine original for: {file_path}")
            continue

        normalized_original = normalize_path(original_path)

        # Check if original was updated in this run
        if normalized_original in updated_originals:
            new_cats = updated_originals[normalized_original]
        elif normalized_original in path_to_row:
            # Get categories from original row
            original_row = path_to_row[normalized_original]
            new_cats = list(
                parse_categories_string(
                    original_row.get(DREAMSTIME_CATEGORY_COLUMN, "")
                )
            )
        else:
            logging.debug(f"Original not found in CSV: {original_path}")
            continue

        current_cats = parse_categories_string(row.get(DREAMSTIME_CATEGORY_COLUMN, ""))

        if set(new_cats) != current_cats:
            stats["edited_updated"] += 1
            logging.info(
                f"Edited updated: {file_path}\n  Inherited from: {original_path}"
            )

            if not args.dry_run:
                row[DREAMSTIME_CATEGORY_COLUMN] = categories_to_string(new_cats)
                update_batch_files(file_path, new_cats)

    # Save PhotoMedia.csv
    if not args.dry_run and (stats["updated"] > 0 or stats["edited_updated"] > 0):
        save_photomedia_csv(args.media_csv, fieldnames, rows)

    # Print summary
    logging.info("=" * 60)
    logging.info("SUMMARY")
    logging.info("=" * 60)
    logging.info(f"Total processed:    {stats['processed']}")
    logging.info(f"Originals updated:  {stats['updated']}")
    logging.info(f"Originals unchanged:{stats['unchanged']}")
    logging.info(f"Edited updated:     {stats['edited_updated']}")
    logging.info(f"Errors:             {stats['errors']}")

    if args.dry_run:
        logging.info("\nDRY RUN - no changes were made")

    return 0


if __name__ == "__main__":
    sys.exit(main())