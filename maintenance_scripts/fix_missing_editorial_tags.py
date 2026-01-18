#!/usr/bin/env python3
"""
Fix missing editorial tags in PhotoMedia.csv and batch state files.

Checks files with editorial_data in completed batches and ensures:
1. The batch result description has the editorial tag
2. The PhotoMedia.csv description has the same editorial tag

For files missing the tag, regenerates description using AI (individual processing).

Usage:
    python maintenance_scripts/fix_missing_editorial_tags.py --dry-run   # Preview changes
    python maintenance_scripts/fix_missing_editorial_tags.py             # Apply fixes
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from tqdm import tqdm
except ImportError:
    print("WARNING: tqdm not installed. Install with: pip install tqdm")
    def tqdm(iterable, **kwargs):
        return iterable

# Add paths for imports (script is in maintenance_scripts/)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "sortunsortedmedia"))
sys.path.insert(0, str(project_root / "givephotobankreadymediafiles"))
sys.path.insert(0, str(project_root))

from givephotobankreadymediafileslib.batch_state import BatchRegistry, BatchState
from givephotobankreadymediafileslib.constants import (
    BATCH_STATE_DIR,
    MAX_DESCRIPTION_LENGTH,
)
from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator
from shared.config import get_config
from shared.file_operations import load_csv, save_csv_with_backup
from shared.exif_handler import get_best_creation_date
from shared.logging_config import setup_logging

# Column names for PhotoMedia.csv
COL_FILE = "Soubor"
COL_PATH = "Cesta"
COL_TITLE = "Název"
COL_DESCRIPTION = "Popis"

# Setup logging
setup_logging(debug=False, log_file="logs/fix_missing_editorial_tags.log")
logger = logging.getLogger(__name__)


def has_editorial_tag(description: str, city: str, country: str = "Czech") -> bool:
    """
    Check if description starts with proper editorial tag.

    Args:
        description: Description text to check
        city: City name to look for
        country: Country name (default Czech)

    Returns:
        True if description starts with "CITY, COUNTRY - DD MM YYYY: "
    """
    if not description or not city:
        return False

    # Pattern: CITY, COUNTRY - DD MM YYYY:
    pattern = rf"^{re.escape(city)},\s*{re.escape(country)}\s*-\s*\d{{2}}\s+\d{{2}}\s+\d{{4}}:\s*"
    return re.match(pattern, description, re.IGNORECASE) is not None


def extract_date_from_exif(file_path: str) -> Optional[str]:
    """
    Extract date from EXIF and format as DD MM YYYY.

    Args:
        file_path: Path to image file

    Returns:
        Date string "DD MM YYYY" or None
    """
    try:
        exif_date = get_best_creation_date(file_path)
        if exif_date:
            return exif_date.strftime("%d %m %Y")
        return None
    except Exception as e:
        logger.warning(f"Failed to extract EXIF date from {file_path}: {e}")
        return None


def scan_batches_for_editorial_files(registry: BatchRegistry) -> List[Dict]:
    """
    Scan completed batches for files with editorial_data.

    Args:
        registry: Batch registry instance

    Returns:
        List of file info dicts with editorial data
    """
    editorial_files = []
    completed_batches = registry.data.get("completed_batches", [])

    logger.info(f"Scanning {len(completed_batches)} completed batches for editorial files...")

    for batch_info in completed_batches:
        batch_id = batch_info.get("batch_id")
        if not batch_id:
            continue

        batch_dir = os.path.join(BATCH_STATE_DIR, "batches", batch_id)
        if not os.path.exists(batch_dir):
            continue

        try:
            batch_state = BatchState(batch_id, batch_dir)

            for file_entry in batch_state.all_files():
                editorial_data = file_entry.get("editorial_data")
                if not editorial_data or not isinstance(editorial_data, dict):
                    continue

                city = editorial_data.get("city", "").strip()
                if not city:
                    continue

                country = editorial_data.get("country", "Czech").strip()
                result = file_entry.get("result", {})

                editorial_files.append({
                    "batch_id": batch_id,
                    "file_path": file_entry.get("file_path", ""),
                    "custom_id": file_entry.get("custom_id", ""),
                    "city": city,
                    "country": country,
                    "batch_title": result.get("title", ""),
                    "batch_description": result.get("description", ""),
                    "batch_state": batch_state,
                    "file_entry": file_entry,
                })
        except Exception as e:
            logger.warning(f"Error scanning batch {batch_id}: {e}")
            continue

    logger.info(f"Found {len(editorial_files)} files with editorial_data")
    return editorial_files


def check_editorial_consistency(
    editorial_files: List[Dict],
    photomedia_records: Dict[str, Dict]
) -> Tuple[List[Dict], List[Dict]]:
    """
    Check consistency of editorial tags across batch and PhotoMedia.csv.

    Args:
        editorial_files: List of files with editorial data from batches
        photomedia_records: Dict mapping filename to PhotoMedia.csv record

    Returns:
        Tuple of (files_needing_batch_fix, files_needing_csv_fix)
    """
    batch_fixes = []
    csv_fixes = []

    for file_info in editorial_files:
        filename = os.path.basename(file_info["file_path"])
        city = file_info["city"]
        country = file_info["country"]
        batch_description = file_info["batch_description"]

        # Check batch result has editorial tag
        batch_has_tag = has_editorial_tag(batch_description, city, country)

        # Check PhotoMedia.csv has editorial tag
        csv_record = photomedia_records.get(filename)
        csv_description = csv_record.get(COL_DESCRIPTION, "") if csv_record else ""
        csv_has_tag = has_editorial_tag(csv_description, city, country) if csv_record else False

        if not batch_has_tag:
            batch_fixes.append(file_info)

        if csv_record and not csv_has_tag:
            file_info["csv_record"] = csv_record
            file_info["csv_description"] = csv_description
            csv_fixes.append(file_info)

    return batch_fixes, csv_fixes


def regenerate_description_with_ai(
    file_path: str,
    title: str,
    original_description: str,
    city: str,
    country: str,
    date_str: str,
    ai_generator
) -> Optional[str]:
    """
    Regenerate description with editorial tag using AI.

    Args:
        file_path: Path to image file
        title: Current title
        original_description: Current description (without tag)
        city: City name
        country: Country name
        date_str: Date in DD MM YYYY format
        ai_generator: MetadataGenerator instance

    Returns:
        New description with editorial tag or None on failure
    """
    try:
        editorial_data = {
            "city": city,
            "country": country,
            "date": date_str
        }

        new_description = ai_generator.generate_description(
            image_path=file_path,
            title=title,
            context=original_description,
            editorial_data=editorial_data,
            user_description=None
        )

        return new_description
    except Exception as e:
        logger.error(f"AI generation failed for {file_path}: {e}")
        return None


def create_fallback_description(
    original_description: str,
    city: str,
    country: str,
    date_str: str
) -> str:
    """
    Create fallback description with editorial tag using simple truncation.

    Args:
        original_description: Original description
        city: City name
        country: Country name
        date_str: Date in DD MM YYYY format

    Returns:
        Description with editorial tag prepended, truncated to fit limit
    """
    editorial_prefix = f"{city}, {country} - {date_str}: "
    available_chars = MAX_DESCRIPTION_LENGTH - len(editorial_prefix)

    if available_chars <= 20:
        return editorial_prefix + original_description[:available_chars]

    # Truncate at sentence boundary
    if len(original_description) <= available_chars:
        return editorial_prefix + original_description

    truncated = original_description[:available_chars]
    last_period = truncated.rfind(".")
    last_exclamation = truncated.rfind("!")
    last_question = truncated.rfind("?")
    last_sentence = max(last_period, last_exclamation, last_question)

    if last_sentence > 0:
        return editorial_prefix + original_description[:last_sentence + 1]

    last_space = truncated.rfind(" ")
    if last_space > 0:
        return editorial_prefix + original_description[:last_space] + "..."

    return editorial_prefix + truncated + "..."


def fix_editorial_tags(
    batch_fixes: List[Dict],
    csv_fixes: List[Dict],
    photomedia_records: List[Dict],
    photomedia_path: str,
    ai_generator,
    dry_run: bool
) -> Tuple[int, int]:
    """
    Fix missing editorial tags in batch state and PhotoMedia.csv.

    Args:
        batch_fixes: Files needing batch state fix
        csv_fixes: Files needing CSV fix
        photomedia_records: Full list of PhotoMedia.csv records
        photomedia_path: Path to PhotoMedia.csv
        ai_generator: MetadataGenerator instance
        dry_run: If True, only preview changes

    Returns:
        Tuple of (batch_fixes_count, csv_fixes_count)
    """
    batch_fixed = 0
    csv_fixed = 0

    # Build filename -> record index mapping
    record_index_map = {}
    for i, record in enumerate(photomedia_records):
        filename = record.get(COL_FILE, "")
        if filename:
            record_index_map[filename] = i

    # Track batch states that need saving
    modified_batch_states = set()

    logger.info(f"Processing {len(batch_fixes)} batch fixes and {len(csv_fixes)} CSV fixes...")

    # Combine all files that need processing
    all_files_to_fix = {}
    for f in batch_fixes:
        key = f["file_path"]
        all_files_to_fix[key] = {"batch": True, "csv": False, "info": f}
    for f in csv_fixes:
        key = f["file_path"]
        if key in all_files_to_fix:
            all_files_to_fix[key]["csv"] = True
        else:
            all_files_to_fix[key] = {"batch": False, "csv": True, "info": f}

    # Build filename -> path mapping for finding originals
    filename_to_path = {}
    for record in photomedia_records:
        fname = record.get(COL_FILE, "")
        fpath = record.get(COL_PATH, "")
        if fname and fpath:
            filename_to_path[fname] = fpath

    # Edit suffixes that indicate edited versions
    EDIT_SUFFIXES = ["_bw", "_negative", "_sharpen", "_misty", "_blurred"]

    total = len(all_files_to_fix)
    pbar = tqdm(all_files_to_fix.items(), total=total, desc="Fixing editorial tags", unit="file")
    for file_path, fix_info in pbar:
        info = fix_info["info"]
        filename = os.path.basename(file_path)
        city = info["city"]
        country = info["country"]

        # Update progress bar with current file
        pbar.set_postfix_str(filename[:40])

        # Check if this is an edited file
        name_without_ext = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        is_edited = any(suffix in name_without_ext for suffix in EDIT_SUFFIXES)

        # Get EXIF date - for edited files, try to get from original
        date_str = None
        if is_edited:
            # Find original filename by removing edit suffix
            original_name = name_without_ext
            for suffix in EDIT_SUFFIXES:
                original_name = original_name.replace(suffix, "")
            original_filename = original_name + ext

            # Try to get date from original file
            original_path = filename_to_path.get(original_filename)
            if original_path and os.path.exists(original_path):
                date_str = extract_date_from_exif(original_path)

        # If no date yet, try from the file itself
        if not date_str:
            date_str = extract_date_from_exif(file_path)

        if not date_str:
            logger.debug(f"No EXIF date for {filename}, skipping")
            continue

        # Get current data
        title = info.get("batch_title", "") or info.get("csv_record", {}).get(COL_TITLE, "")
        original_description = info.get("batch_description", "") or info.get("csv_description", "")

        # Remove existing broken/partial editorial tags if present
        # Pattern matches: "CITY, COUNTRY - DD MM YYYY:" or partial versions
        original_description = re.sub(
            rf"^{re.escape(city)},?\s*{re.escape(country)}?\s*-?\s*(\d{{2}}\s+\d{{2}}\s+\d{{4}})?\s*:?\s*",
            "",
            original_description,
            flags=re.IGNORECASE
        ).strip()
        # Also remove any standalone date prefix like "04 08 2016:"
        original_description = re.sub(
            r"^\d{2}\s+\d{2}\s+\d{4}\s*:\s*",
            "",
            original_description
        ).strip()

        # Generate new description with AI
        new_description = None
        if ai_generator:
            new_description = regenerate_description_with_ai(
                file_path, title, original_description, city, country, date_str, ai_generator
            )

        # Fallback if AI failed
        if not new_description:
            logger.debug(f"Using fallback for {filename}")
            new_description = create_fallback_description(
                original_description, city, country, date_str
            )

        logger.debug(f"New description ({len(new_description)} chars): {new_description[:80]}...")

        if dry_run:
            if fix_info["batch"]:
                batch_fixed += 1
            if fix_info["csv"]:
                csv_fixed += 1
            continue

        # Update batch state
        if fix_info["batch"]:
            batch_state = info["batch_state"]
            file_entry = info["file_entry"]
            if "result" not in file_entry:
                file_entry["result"] = {}
            file_entry["result"]["description"] = new_description
            modified_batch_states.add(batch_state)
            batch_fixed += 1

        # Update PhotoMedia.csv record
        if fix_info["csv"]:
            record_idx = record_index_map.get(filename)
            if record_idx is not None:
                photomedia_records[record_idx][COL_DESCRIPTION] = new_description
                csv_fixed += 1

    # Save modified batch states
    if not dry_run:
        for batch_state in modified_batch_states:
            try:
                batch_state.save()
                logger.info(f"Saved batch state: {batch_state.batch_id}")
            except Exception as e:
                logger.error(f"Failed to save batch {batch_state.batch_id}: {e}")

        # Save PhotoMedia.csv
        if csv_fixed > 0:
            save_csv_with_backup(photomedia_records, photomedia_path)
            logger.info(f"Saved PhotoMedia.csv with {csv_fixed} fixes")

    return batch_fixed, csv_fixed


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 success, 1 error)
    """
    parser = argparse.ArgumentParser(
        description="Fix missing editorial tags in batch state and PhotoMedia.csv"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--media-csv",
        type=str,
        default="L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv",
        help="Path to PhotoMedia.csv"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("FIX MISSING EDITORIAL TAGS")
    logger.info("=" * 70)
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info(f"PhotoMedia.csv: {args.media_csv}")
    logger.info("=" * 70)

    # Load batch registry
    try:
        registry = BatchRegistry()
    except Exception as e:
        logger.error(f"Failed to load batch registry: {e}")
        return 1

    # Scan batches for editorial files
    editorial_files = scan_batches_for_editorial_files(registry)
    if not editorial_files:
        logger.info("No files with editorial_data found in batches")
        return 0

    # Load PhotoMedia.csv
    try:
        photomedia_records = load_csv(args.media_csv)
        logger.info(f"Loaded {len(photomedia_records)} records from PhotoMedia.csv")
    except Exception as e:
        logger.error(f"Failed to load PhotoMedia.csv: {e}")
        return 1

    # Build filename -> record mapping
    photomedia_by_filename = {}
    for record in photomedia_records:
        filename = record.get(COL_FILE, "")
        if filename:
            photomedia_by_filename[filename] = record

    # Check consistency
    batch_fixes, csv_fixes = check_editorial_consistency(editorial_files, photomedia_by_filename)

    logger.info(f"Files needing batch fix: {len(batch_fixes)}")
    logger.info(f"Files needing CSV fix: {len(csv_fixes)}")

    if not batch_fixes and not csv_fixes:
        logger.info("All editorial tags are consistent. Nothing to fix.")
        return 0

    # Initialize AI generator
    ai_generator = None
    if not args.dry_run:
        try:
            config = get_config()
            provider, model = config.get_default_ai_model()
            logger.info(f"Initializing AI generator: {provider}/{model}")
            model_key = f"{provider}/{model}"
            api_key = config.get_ai_api_key(provider)
            ai_generator = create_metadata_generator(model_key, api_key=api_key)
        except Exception as e:
            logger.warning(f"Could not initialize AI generator: {e}")
            logger.info("Will use fallback description generation")

    # Fix editorial tags
    batch_fixed, csv_fixed = fix_editorial_tags(
        batch_fixes, csv_fixes, photomedia_records, args.media_csv,
        ai_generator, args.dry_run
    )

    # Summary
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Batch state fixes: {batch_fixed}")
    logger.info(f"PhotoMedia.csv fixes: {csv_fixed}")
    if args.dry_run:
        logger.info("(DRY RUN - no changes written)")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())