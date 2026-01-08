#!/usr/bin/env python3
"""
Interactive tool to add missing editorial tags to photos in completed batches.

Scans completed batches for photos with editorial_data.city but missing editorial tag
in description, shows each photo to user for confirmation, then bulk-updates batch + PhotoMedia.csv.

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
    COL_DESCRIPTION,
    COL_FILE,
    DEFAULT_MEDIA_CSV_PATH,
    MAX_DESCRIPTION_LENGTH,
)
from shared.file_operations import load_csv, save_csv_with_backup
from shared.config import get_config
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
            exif_data = img._getexif()

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
    Also finds alternative (edited) versions of those photos.

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

    for batch_id in completed_batch_ids:
        try:
            batch_dir = registry.get_batch_dir(batch_id)
            if not os.path.exists(batch_dir):
                continue

            batch_state = BatchState(batch_id, batch_dir)
            files = batch_state.all_files()

            # First pass: Find originals with editorial_data.city needing tags
            originals_needing_tags = {}  # file_path -> (city, country, date)

            for file_entry in files:
                # Skip alternative entries in first pass
                if file_entry.get("entry_type") == "alternative":
                    continue

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
                    # Batch not completed for this file - skip
                    continue

                current_description = result.get("description", "")

                # Check if editorial tag is already correct
                if has_editorial_tag(current_description, city):
                    continue  # Already has correct tag - skip

                # This photo needs tag correction
                file_path = file_entry.get("file_path", "")
                custom_id = file_entry.get("custom_id", "")

                # Extract date from EXIF
                date = extract_date_from_exif(file_path)
                if not date:
                    date = "UNKNOWN"

                # Store original info
                country = editorial_data.get("country", "Czech")
                originals_needing_tags[file_path] = (city, country, date)

                # Add original to candidates
                candidates.append({
                    "file_path": file_path,
                    "batch_id": batch_id,
                    "custom_id": custom_id,
                    "city": city,
                    "country": country,
                    "date": date,
                    "current_description": current_description,
                    "current_title": result.get("title", ""),
                    "is_alternative": False,
                    "edit_tag": None,
                })

            # Second pass: Find alternative entries for those originals
            for file_entry in files:
                if file_entry.get("entry_type") != "alternative":
                    continue

                original_path = file_entry.get("original_file_path", "")
                if not original_path:
                    continue

                # Check if this alternative's original needs tags
                if original_path not in originals_needing_tags:
                    continue

                # Get result for alternative
                result = file_entry.get("result")
                if not result:
                    continue

                city, country, date = originals_needing_tags[original_path]

                current_description = result.get("description", "")

                # Check if editorial tag is already correct for alternative
                if has_editorial_tag(current_description, city):
                    continue

                # Add alternative to candidates
                file_path = file_entry.get("file_path", "")
                custom_id = file_entry.get("custom_id", "")
                edit_tag = file_entry.get("edit_tag", "")

                candidates.append({
                    "file_path": file_path,
                    "batch_id": batch_id,
                    "custom_id": custom_id,
                    "city": city,
                    "country": country,
                    "date": date,
                    "current_description": current_description,
                    "current_title": result.get("title", ""),
                    "is_alternative": True,
                    "edit_tag": edit_tag,
                    "original_file_path": original_path,
                })

        except Exception as e:
            print(f"  Warning: Error scanning batch {batch_id}: {e}")
            continue

    return candidates, cities_found


def interactive_confirmation(candidates: List[Dict], cities_found: Set[str]) -> List[Dict]:
    """
    Show each candidate photo to user for confirmation.

    Args:
        candidates: List of candidate photos
        cities_found: Set of unique cities found

    Returns:
        List of confirmed photos
    """
    if not candidates:
        return []

    confirmed = []
    total = len(candidates)

    # Show detected cities
    print(f"\n{'='*70}")
    print(f"Detected {len(cities_found)} unique cities in completed batches:")
    for city in sorted(cities_found):
        print(f"  - {city}")
    print(f"\nFound {total} photos with editorial_data.city but missing proper tag")
    print(f"{'='*70}\n")

    for i, candidate in enumerate(candidates, 1):
        print(f"\n{'='*70}")
        print(f"Photo {i}/{total}:")
        print(f"  File: {os.path.basename(candidate['file_path'])}")

        # Show if it's an edited version
        if candidate.get('is_alternative'):
            edit_tag = candidate.get('edit_tag', '')
            edit_name = edit_tag.replace('_', '').upper() if edit_tag else 'EDITED'
            print(f"  Type: {edit_name} version (alternative)")
            print(f"  Original: {os.path.basename(candidate.get('original_file_path', ''))}")
        else:
            print(f"  Type: ORIGINAL")

        print(f"  Batch: {candidate['batch_id']}")
        print(f"  City (from editorial_data): {candidate['city']}")
        print(f"  Country: {candidate['country']}")
        print(f"  Date from EXIF: {candidate['date']}")
        print(f"\n  Current title: {candidate['current_title']}")
        print(f"  Current description: {candidate['current_description'][:100]}...")

        editorial_tag = f"{candidate['city']}, {candidate['country']} - {candidate['date']}: "
        print(f"\n  Editorial tag to ADD: '{editorial_tag}'")
        print(f"  New description: '{editorial_tag}{candidate['current_description'][:70]}...'")

        while True:
            response = input("\n  Confirm adding editorial tag? [y/n/skip]: ").strip().lower()

            if response == "y":
                confirmed.append(candidate)
                print("  ✓ Confirmed")
                break
            elif response == "skip" or response == "n":
                print("  ⊘ Skipped")
                break
            else:
                print("  Invalid input. Please enter y/n/skip")

    print(f"\n{'='*70}")
    print(f"Summary: Confirmed {len(confirmed)}/{total} photos")

    return confirmed


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
    Bulk update batch state files and PhotoMedia.csv with editorial tags.
    Uses AI to regenerate descriptions to fit within character limit.

    Args:
        confirmed_photos: List of confirmed photos to update
        registry: Batch registry instance
        media_csv_path: Path to PhotoMedia.csv
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
                    # Fallback: just prepend editorial tag (may exceed limit)
                    print(f"    Warning: AI generation failed, using simple prepend (may exceed {MAX_DESCRIPTION_LENGTH} chars)")
                    editorial_prefix = f"{city}, {country} - {date}: "
                    result["description"] = editorial_prefix + current_description
                    file_entry["result"] = result
                    new_description = result["description"]

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

    # Update PhotoMedia.csv
    if not dry_run:
        print("\nUpdating PhotoMedia.csv...")
        try:
            # Load CSV
            records = load_csv(media_csv_path)

            # Update records
            updates_applied = 0
            for log_entry in log_entries:
                file_path = log_entry["file_path"]
                new_description = log_entry["new_description"]

                for record in records:
                    record_path = record.get(COL_FILE, "")
                    if os.path.normpath(record_path).lower() == os.path.normpath(file_path).lower():
                        record[COL_DESCRIPTION] = new_description
                        updates_applied += 1
                        break

            # Save with backup
            save_csv_with_backup(records, media_csv_path)
            print(f"  ✓ Applied {updates_applied} updates to PhotoMedia.csv")

        except Exception as e:
            print(f"  Error updating PhotoMedia.csv: {e}")

    # Save log file
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = f"editorial_tag_additions_{timestamp}.json"
    log_path = os.path.join(BATCH_STATE_DIR, log_filename)

    if not dry_run:
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(log_entries, f, indent=2, ensure_ascii=False)
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