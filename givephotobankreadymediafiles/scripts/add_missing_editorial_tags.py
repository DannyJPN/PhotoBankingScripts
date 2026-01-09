#!/usr/bin/env python3
"""
Interactive tool to add missing editorial tags to photos in completed batches.

Scans completed batches for photos with editorial_data.city but missing editorial tag
in description, shows each photo to user for confirmation, then bulk-updates batch state files.

NOTE: This script ONLY updates batch state files. PhotoMedia.csv requires separate handling.

Usage:
    python add_missing_editorial_tags.py [--dry-run]

Example:
    python add_missing_editorial_tags.py --dry-run  # Preview changes without writing
    python add_missing_editorial_tags.py            # Interactive mode with confirmation
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent directories to path
script_dir = Path(__file__).parent  # givephotobankreadymediafiles/scripts/
module_dir = script_dir.parent  # givephotobankreadymediafiles/
root_dir = module_dir.parent  # Fotobanking/

# Add both paths:
# - module_dir for importing givephotobankreadymediafileslib
# - root_dir for importing shared
sys.path.insert(0, str(module_dir))
sys.path.insert(0, str(root_dir))

from givephotobankreadymediafileslib.batch_state import (
    BatchRegistry,
    BatchState,
)
from givephotobankreadymediafileslib.constants import (
    BATCH_STATE_DIR,
    DEFAULT_MEDIA_CSV_PATH,
    MAX_DESCRIPTION_LENGTH,
)
from shared.config import get_config
from shared.file_operations import save_json_with_backup
from givephotobankreadymediafileslib.metadata_generator import create_metadata_generator


def extract_date_from_exif(file_path: str) -> Optional[str]:
    """
    Extract DateTime from EXIF and format as DD MM YYYY.
    Uses PIL/Pillow - same method as batch mode.

    Args:
        file_path: Path to image file

    Returns:
        Formatted date string "DD MM YYYY" or None if not found
    """
    try:
        if not os.path.exists(file_path):
            return None

        from PIL import Image
        from PIL.ExifTags import TAGS

        with Image.open(file_path) as img:
            exif_data = img.getexif()

            if exif_data:
                # Try to extract date from DateTime tag
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)

                    if tag == 'DateTime' and value:
                        try:
                            # Convert EXIF datetime to DD MM YYYY format
                            dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                            return dt.strftime("%d %m %Y")
                        except ValueError:
                            continue

        return None

    except Exception as e:
        print(f"  Warning: Could not extract EXIF date from {file_path}: {e}")
        return None


def has_editorial_tag(description: str, city: str) -> bool:
    """
    Check if description starts with proper editorial tag for given city.

    Args:
        description: Description text to check
        city: City name to look for in tag

    Returns:
        True if description starts with "City, Czech - DD MM YYYY: "
    """
    if not description or not city:
        return False

    # Pattern: CITY, Czech - DD MM YYYY:
    # Case-insensitive city match
    pattern = rf"^{re.escape(city)},\s*Czech\s*-\s*\d{{2}}\s+\d{{2}}\s+\d{{4}}:\s*"
    return re.match(pattern, description, re.IGNORECASE) is not None


def scan_completed_batches(registry: BatchRegistry) -> List[Dict]:
    """
    Scan completed batches and find photos with editorial_data.city but missing tag.
    Also finds edited versions of those photos (files with _bw, _sharpen, etc. suffix).

    Args:
        registry: Batch registry instance

    Returns:
        Tuple of (candidates list, cities_found set)
    """
    candidates = []
    completed_batches = registry.data.get("completed_batches", [])

    if not completed_batches:
        return candidates, set()

    completed_batch_ids = [b["batch_id"] for b in completed_batches]

    print(f"\nScanning {len(completed_batch_ids)} completed batches for editorial photos...")

    cities_found = set()

    # PHASE 1: Collect ALL editorial originals across ALL batches
    # Maps: original_basename (without extension) -> (city, country, date)
    editorial_originals = {}

    print("Phase 1: Collecting editorial originals...")
    for batch_id in completed_batch_ids:
        try:
            batch_dir = registry.get_batch_dir(batch_id)
            if not os.path.exists(batch_dir):
                continue

            batch_state = BatchState(batch_id, batch_dir)
            files = batch_state.all_files()

            for file_entry in files:
                # Check if photo has editorial_data.city
                editorial_data = file_entry.get("editorial_data")
                if not editorial_data or not isinstance(editorial_data, dict):
                    continue

                city = editorial_data.get("city", "").strip()
                if not city:
                    continue

                cities_found.add(city)

                # Get current result
                result = file_entry.get("result")
                if not result:
                    continue

                file_path = file_entry.get("file_path", "")
                country = editorial_data.get("country", "Czech")

                # Extract basename without extension for matching
                # DSC01234.JPG -> DSC01234
                # DSC01234_bw.JPG -> DSC01234 (but we want just originals here)
                basename = os.path.basename(file_path)
                name_without_ext = os.path.splitext(basename)[0]

                # Skip if this looks like an edited version (contains underscore)
                if "_" in name_without_ext:
                    continue  # This is likely an edited version, skip in Phase 1

                # Extract date from EXIF
                date = extract_date_from_exif(file_path)
                if not date:
                    date = "UNKNOWN"

                # Store original info
                editorial_originals[name_without_ext] = (city, country, date)

        except Exception as e:
            print(f"  Warning: Error scanning batch {batch_id} in Phase 1: {e}")
            continue

    print(f"  Found {len(editorial_originals)} editorial originals")

    # PHASE 2: Find ALL files (originals + edited versions) that need tags
    print("Phase 2: Finding files missing editorial tags...")

    originals_fixed = 0
    edited_fixed = 0

    for batch_id in completed_batch_ids:
        try:
            batch_dir = registry.get_batch_dir(batch_id)
            if not os.path.exists(batch_dir):
                continue

            batch_state = BatchState(batch_id, batch_dir)
            files = batch_state.all_files()

            for file_entry in files:
                result = file_entry.get("result")
                if not result:
                    continue

                file_path = file_entry.get("file_path", "")
                custom_id = file_entry.get("custom_id", "")

                basename = os.path.basename(file_path)
                name_without_ext = os.path.splitext(basename)[0]

                # Check if this is an original or edited version
                if "_" in name_without_ext:
                    # Edited version: extract original basename
                    # DSC01234_bw -> DSC01234
                    parts = name_without_ext.split("_")
                    original_basename = parts[0]
                    edit_suffix = "_" + "_".join(parts[1:])  # Reconstruct full suffix
                else:
                    # Original file
                    original_basename = name_without_ext
                    edit_suffix = None

                # Check if this file belongs to an editorial original
                if original_basename not in editorial_originals:
                    continue  # Not an editorial photo

                city, country, date = editorial_originals[original_basename]

                current_description = result.get("description", "")

                # Check if editorial tag is already correct
                if has_editorial_tag(current_description, city):
                    continue  # Already has correct tag

                # Add to candidates
                candidates.append({
                    "file_path": file_path,
                    "batch_id": batch_id,
                    "custom_id": custom_id,
                    "city": city,
                    "country": country,
                    "date": date,
                    "current_description": current_description,
                    "current_title": result.get("title", ""),
                    "is_alternative": edit_suffix is not None,
                    "edit_tag": edit_suffix,
                    "original_basename": original_basename,
                })

                if edit_suffix:
                    edited_fixed += 1
                else:
                    originals_fixed += 1

        except Exception as e:
            print(f"  Warning: Error scanning batch {batch_id} in Phase 2: {e}")
            continue

    print(f"  Found {originals_fixed} originals + {edited_fixed} edited versions needing tags")

    return candidates, cities_found


def interactive_confirmation(candidates: List[Dict], cities_found: Set[str]) -> List[Dict]:
    """
    Show each candidate photo to user for confirmation.

    Logic:
    - Originals needing tags: ask user for confirmation
    - Edited versions whose original also needs tag: auto-confirm when original is confirmed
    - Edited versions whose original already has correct tag: auto-confirm immediately (no user interaction)

    Args:
        candidates: List of candidate photos (originals + alternatives)
        cities_found: Set of unique cities found

    Returns:
        List of confirmed photos (user-confirmed originals + auto-confirmed alternatives)
    """
    if not candidates:
        return []

    # Separate originals and alternatives
    originals = [c for c in candidates if not c.get('is_alternative')]
    alternatives = [c for c in candidates if c.get('is_alternative')]

    # Group alternatives by original basename
    alternatives_by_original = {}
    for alt in alternatives:
        original_basename = alt.get('original_basename', '')
        if original_basename not in alternatives_by_original:
            alternatives_by_original[original_basename] = []
        alternatives_by_original[original_basename].append(alt)

    # Find which originals are in the candidates (i.e., also need fixing)
    originals_needing_fix = set(c.get('original_basename', '') for c in originals)

    # Separate alternatives into two groups:
    # 1. Those whose original also needs fixing (wait for user confirmation)
    # 2. Those whose original already has correct tag (auto-confirm immediately)
    alternatives_waiting = []  # Wait for original confirmation
    alternatives_auto = []     # Auto-confirm immediately

    for alt in alternatives:
        original_basename = alt.get('original_basename', '')
        if original_basename in originals_needing_fix:
            alternatives_waiting.append(alt)
        else:
            alternatives_auto.append(alt)

    confirmed = []
    confirmed_originals = set()  # Track which originals were confirmed
    total_originals = len(originals)
    total_alternatives_waiting = len(alternatives_waiting)
    total_alternatives_auto = len(alternatives_auto)

    # Show detected cities
    print(f"\n{'='*70}")
    print(f"Detected {len(cities_found)} unique cities in completed batches:")
    for city in sorted(cities_found):
        print(f"  - {city}")
    print(f"\nFound photos missing editorial tags:")
    print(f"  - {total_originals} originals (will ask for confirmation)")
    print(f"  - {total_alternatives_waiting} edited versions (auto-confirm with their originals)")
    print(f"  - {total_alternatives_auto} edited versions (auto-confirm, original already correct)")
    print(f"{'='*70}\n")

    # Auto-confirm alternatives whose originals already have correct tags
    if total_alternatives_auto > 0:
        print(f"Auto-confirming {total_alternatives_auto} edited versions whose originals already have correct tags...")
        for alt in alternatives_auto:
            confirmed.append(alt)
        print(f"  ✓ Auto-confirmed {total_alternatives_auto} edited versions\n")

    # Ask only about originals
    for i, candidate in enumerate(originals, 1):
        original_basename = candidate.get('original_basename', '')

        # Count how many alternatives are waiting for this original
        num_alternatives = len([a for a in alternatives_waiting
                               if a.get('original_basename') == original_basename])

        print(f"\n{'='*70}")
        print(f"ORIGINAL Photo {i}/{total_originals}:")
        print(f"  File: {os.path.basename(candidate['file_path'])}")
        print(f"  Batch: {candidate['batch_id']}")
        print(f"  City (from editorial_data): {candidate['city']}")
        print(f"  Country: {candidate['country']}")
        print(f"  Date from EXIF: {candidate['date']}")

        if num_alternatives > 0:
            print(f"  → This photo has {num_alternatives} edited version(s) that will also be updated")

        print(f"\n  Current title: {candidate['current_title']}")
        print(f"  Current description: {candidate['current_description'][:100]}...")

        editorial_tag = f"{candidate['city']}, {candidate['country']} - {candidate['date']}: "
        print(f"\n  Editorial tag to ADD: '{editorial_tag}'")
        print(f"  New description: '{editorial_tag}{candidate['current_description'][:70]}...'")

        while True:
            response = input("\n  Confirm adding editorial tag? [y/n/skip]: ").strip().lower()

            if response == "y":
                confirmed.append(candidate)
                confirmed_originals.add(original_basename)
                print("  ✓ Confirmed")
                if num_alternatives > 0:
                    print(f"  ✓ Auto-confirming {num_alternatives} edited version(s)")
                break
            elif response == "skip" or response == "n":
                print("  ⊘ Skipped")
                if num_alternatives > 0:
                    print(f"  ⊘ Also skipping {num_alternatives} edited version(s)")
                break
            else:
                print("  Invalid input. Please enter y/n/skip")

    # Auto-confirm waiting alternatives whose originals were confirmed
    auto_confirmed_waiting = 0
    for original_basename in confirmed_originals:
        for alt in alternatives_waiting:
            if alt.get('original_basename') == original_basename:
                confirmed.append(alt)
                auto_confirmed_waiting += 1

    print(f"\n{'='*70}")
    print(f"Summary:")
    print(f"  Originals confirmed: {len(confirmed_originals)}/{total_originals}")
    print(f"  Edited versions auto-confirmed (waiting for original): {auto_confirmed_waiting}/{total_alternatives_waiting}")
    print(f"  Edited versions auto-confirmed (original already correct): {total_alternatives_auto}")
    print(f"  Total photos to update: {len(confirmed)}")

    return confirmed


def truncate_to_sentence(text: str, max_length: int) -> str:
    """
    Truncate text to complete sentences within max_length.

    Finds the last sentence-ending punctuation (. ! ?) before max_length
    and truncates there. If no sentence ending found, falls back to last word.

    Args:
        text: Text to truncate
        max_length: Maximum character length

    Returns:
        Truncated text ending with complete sentence or word boundary
    """
    if len(text) <= max_length:
        return text

    # Find last sentence-ending punctuation before max_length
    truncated = text[:max_length]

    # Look for sentence endings (. ! ?)
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')

    # Find the latest sentence ending
    last_sentence_end = max(last_period, last_exclamation, last_question)

    if last_sentence_end > 0:
        # Truncate at sentence ending (include the punctuation)
        return text[:last_sentence_end + 1].strip()

    # No sentence ending found - truncate at last word boundary
    import logging
    logging.warning("No sentence ending found in description, truncating at word boundary")
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return text[:last_space].strip() + "..."

    # Absolute fallback: hard truncate
    return truncated.strip() + "..."


def regenerate_description_with_ai(photo: Dict, model_key: str) -> Optional[str]:
    """
    Regenerate description using AI to fit within character limit with editorial tag.

    Args:
        photo: Photo dict containing file_path, current_title, current_description, editorial data
        model_key: AI model key (e.g., "openai/gpt-4o-mini")

    Returns:
        New description with editorial tag, or None if generation fails
    """
    try:
        file_path = photo["file_path"]
        title = photo["current_title"]
        original_description = photo["current_description"]

        # Prepare editorial data for AI generator
        editorial_data = {
            "city": photo["city"],
            "country": photo["country"],
            "date": photo["date"]
        }

        # Calculate editorial prefix length
        editorial_prefix = f"{photo['city']}, {photo['country']} - {photo['date']}: "
        available_chars = MAX_DESCRIPTION_LENGTH - len(editorial_prefix)

        if available_chars <= 20:
            print(f"    Warning: Editorial tag too long ({len(editorial_prefix)} chars), not enough space for description")
            return None

        print(f"    Regenerating description with AI (editorial tag: {len(editorial_prefix)} chars, available: {available_chars} chars)...")

        # Create metadata generator
        generator = create_metadata_generator(model_key)

        # Generate new description with editorial prefix
        # AI will automatically handle editorial_data and truncate to fit
        new_description = generator.generate_description(
            image_path=file_path,
            title=title,
            context=original_description,
            editorial_data=editorial_data
        )

        print(f"    ✓ AI generated description: {len(new_description)} chars")
        return new_description

    except Exception as e:
        print(f"    Error regenerating description with AI: {e}")
        return None


def bulk_update_batches(confirmed_photos: List[Dict], registry: BatchRegistry, media_csv_path: str, dry_run: bool = False):
    """
    Bulk update batch state files with editorial tags.
    Uses AI to regenerate descriptions to fit within character limit.

    Args:
        confirmed_photos: List of confirmed photos to update
        registry: Batch registry instance
        media_csv_path: Path to PhotoMedia.csv (unused but kept for compatibility)
        dry_run: If True, preview changes without writing
    """
    if not confirmed_photos:
        print("\nNo photos to update.")
        return

    if dry_run:
        print(f"\n{'='*70}")
        print("DRY RUN MODE - No changes will be written")
        print(f"{'='*70}\n")

    proceed = input(f"\nProceed with updating {len(confirmed_photos)} photos? [y/n]: ").strip().lower()

    if proceed != "y":
        print("Update cancelled.")
        return

    # Get AI model from config (use default model like batch mode)
    print("\nGetting default AI model from config...")
    try:
        config = get_config()
        provider, model = config.get_default_ai_model()
        if not provider or not model:
            print("Error: No default AI model configured")
            return
        model_key = f"{provider}/{model}"
        print(f"Using AI model: {model_key}")
    except Exception as e:
        print(f"Error getting AI model: {e}")
        return

    # Group by batch_id for efficient processing
    photos_by_batch = {}
    for photo in confirmed_photos:
        batch_id = photo["batch_id"]
        if batch_id not in photos_by_batch:
            photos_by_batch[batch_id] = []
        photos_by_batch[batch_id].append(photo)

    print(f"\nUpdating {len(confirmed_photos)} photos across {len(photos_by_batch)} batches...")
    print("=" * 70)

    updated_count = 0
    log_entries = []
    total_photos = len(confirmed_photos)
    current_photo = 0

    for batch_id, photos in photos_by_batch.items():
        try:
            batch_dir = registry.get_batch_dir(batch_id)
            batch_state = BatchState(batch_id, batch_dir)
            all_files = batch_state.all_files()

            for photo in photos:
                current_photo += 1
                custom_id = photo["custom_id"]
                city = photo["city"]
                country = photo["country"]
                date = photo["date"]

                # Find file entry by custom_id
                file_entry = None
                for f in all_files:
                    if f.get("custom_id") == custom_id:
                        file_entry = f
                        break

                if not file_entry:
                    print(f"  Warning: File {custom_id} not found in batch {batch_id}")
                    continue

                print(f"\n[{current_photo}/{total_photos}] Processing: {os.path.basename(photo['file_path'])}")
                print(f"  Batch: {batch_id}")

                # Update editorial_data with date
                if not file_entry.get("editorial_data"):
                    file_entry["editorial_data"] = {}

                file_entry["editorial_data"]["city"] = city
                file_entry["editorial_data"]["country"] = country
                file_entry["editorial_data"]["date"] = date
                file_entry["editorial"] = True

                # Regenerate description with AI to fit character limit
                result = file_entry.get("result", {})
                current_description = result.get("description", "")

                # Use AI to regenerate description with editorial tag
                new_description = regenerate_description_with_ai(photo, model_key)

                if new_description:
                    result["description"] = new_description
                    file_entry["result"] = result
                else:
                    # Fallback: Truncate current description and prepend editorial tag
                    print(f"    Warning: AI generation failed, using fallback with sentence truncation")
                    editorial_prefix = f"{city}, {country} - {date}: "
                    available_chars = MAX_DESCRIPTION_LENGTH - len(editorial_prefix)

                    if available_chars <= 20:
                        print(f"    Error: Editorial tag too long, cannot create valid description")
                        continue

                    # Truncate current description to fit, ending on sentence boundary
                    truncated_description = truncate_to_sentence(current_description, available_chars)
                    new_description = editorial_prefix + truncated_description

                    result["description"] = new_description
                    file_entry["result"] = result
                    print(f"    ✓ Fallback description: {len(new_description)} chars (truncated at sentence boundary)")

                # Log change
                log_entries.append({
                    "timestamp": datetime.now().isoformat(),
                    "batch_id": batch_id,
                    "custom_id": custom_id,
                    "file_path": photo["file_path"],
                    "city": city,
                    "country": country,
                    "date": date,
                    "editorial_tag": f"{city}, {country} - {date}: ",
                    "old_description": current_description,
                    "new_description": new_description,
                })

                updated_count += 1

            # Save batch state
            if not dry_run:
                batch_state.save()
                print(f"  ✓ Updated batch {batch_id}")

        except Exception as e:
            print(f"  Error updating batch {batch_id}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # NOTE: PhotoMedia.csv update intentionally skipped - requires separate handling

    # Save log file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"editorial_tag_additions_{timestamp}.json"
    log_path = os.path.join(BATCH_STATE_DIR, log_filename)

    if not dry_run:
        try:
            save_json_with_backup(log_entries, log_path, indent=2)
            print(f"  ✓ Log saved to: {log_path}")
        except Exception as e:
            print(f"  Warning: Could not save log file: {e}")

    print(f"\n{'='*70}")
    print(f"✓ Updated {updated_count} photos in {len(photos_by_batch)} batches")
    if dry_run:
        print("(Dry run - no changes written)")
    print(f"{'='*70}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Add missing editorial tags to photos in completed batches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without writing
  python add_missing_editorial_tags.py --dry-run

  # Interactive mode with confirmation
  python add_missing_editorial_tags.py
        """,
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to files")
    parser.add_argument("--media-csv", default=DEFAULT_MEDIA_CSV_PATH, help="Path to PhotoMedia.csv")

    args = parser.parse_args()

    print("=" * 70)
    print("ADD MISSING EDITORIAL TAGS TO COMPLETED BATCH PHOTOS")
    print("=" * 70)

    # Load batch registry
    try:
        registry = BatchRegistry()
    except Exception as e:
        print(f"\nError loading batch registry: {e}")
        return 1

    # Step 1: Scan completed batches
    result = scan_completed_batches(registry)
    if isinstance(result, tuple):
        candidates, cities_found = result
    else:
        candidates = result
        cities_found = set()

    if not candidates:
        print("\n✓ No photos found needing editorial tag correction.")
        print("  All editorial photos in completed batches have proper tags.")
        return 0

    # Step 2: Interactive confirmation
    confirmed_photos = interactive_confirmation(candidates, cities_found)

    if not confirmed_photos:
        print("\nNo photos confirmed for update.")
        return 0

    # Step 3: Bulk update
    bulk_update_batches(confirmed_photos, registry, args.media_csv, dry_run=args.dry_run)

    print("\n✓ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())