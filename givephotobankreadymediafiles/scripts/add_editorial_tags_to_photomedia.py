#!/usr/bin/env python3
"""
Add Missing Editorial Tags to PhotoMedia.csv

Scans batches for editorial cities, finds photos in PhotoMedia.csv that mention
those cities in title/description, and adds editorial tags + regenerates descriptions.

Usage:
    python add_editorial_tags_to_photomedia.py --dry-run   # Preview changes
    python add_editorial_tags_to_photomedia.py             # Apply changes
"""

import sys
import argparse
import re
import csv
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# Progress bar
try:
    from tqdm import tqdm
except ImportError:
    print("WARNING: tqdm not installed. Install with: pip install tqdm")
    # Fallback: no progress bar
    def tqdm(iterable, **kwargs):
        return iterable

# Add paths for imports
script_dir = Path(__file__).parent
module_dir = script_dir.parent
root_dir = module_dir.parent
sys.path.insert(0, str(module_dir))
sys.path.insert(0, str(root_dir))

from givephotobankreadymediafileslib.batch_state import BatchState, BatchRegistry
from givephotobankreadymediafileslib.metadata_generator import MetadataGenerator, create_metadata_generator
from givephotobankreadymediafileslib.constants import (
    COL_FILE,
    COL_TITLE,
    COL_DESCRIPTION,
    COL_PATH,
    DEFAULT_MEDIA_CSV_PATH,
)
from shared.config import Config
from shared.file_operations import load_csv, save_csv_with_backup
from shared.logging_config import setup_logging

# PIL for EXIF extraction
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    print("ERROR: PIL/Pillow not installed. Install with: pip install Pillow")
    sys.exit(1)

# Setup logging
import logging
setup_logging(debug=False, log_file="logs/add_editorial_tags_to_photomedia.log")
logger = logging.getLogger(__name__)

# Constants
MAX_DESCRIPTION_LENGTH = 200


def collect_editorial_cities(csv_path: str) -> Set[str]:
    """
    Scan completed batches AND PhotoMedia.csv for unique editorial cities.

    Args:
        csv_path: Path to PhotoMedia.csv

    Returns:
        Set of city names found in editorial_data (batches) and existing editorial tags (PhotoMedia.csv)
    """
    import os
    from givephotobankreadymediafileslib.constants import BATCH_STATE_DIR

    cities = set()

    # SOURCE 1: Completed batches
    registry = BatchRegistry()
    completed_batches = registry.data.get("completed_batches", [])

    logger.info(f"Scanning {len(completed_batches)} completed batches for editorial cities...")

    for batch_info in completed_batches:
        batch_id = batch_info.get('batch_id')
        if not batch_id:
            continue

        batch_dir = os.path.join(BATCH_STATE_DIR, "batches", batch_id)

        if not os.path.exists(batch_dir):
            logger.debug(f"Batch directory not found: {batch_dir}")
            continue

        try:
            batch_state = BatchState(batch_id, batch_dir)

            for file_entry in batch_state.all_files():
                if not file_entry:
                    continue
                editorial_data = file_entry.get('editorial_data')
                if editorial_data and isinstance(editorial_data, dict):
                    city = editorial_data.get('city', '').strip()
                    if city:
                        cities.add(city)
        except Exception as e:
            logger.debug(f"Skipping batch {batch_id}: {e}")
            continue

    batch_cities_count = len(cities)
    logger.info(f"Found {batch_cities_count} cities from completed batches")

    # SOURCE 2: Existing editorial tags in PhotoMedia.csv
    logger.info(f"Scanning PhotoMedia.csv for existing editorial tags...")

    try:
        records = load_csv(csv_path)

        for record in records:
            description = record.get(COL_DESCRIPTION, "")
            if not description:
                continue

            # Extract city from editorial tag pattern: "CITY, Czech - DD MM YYYY: "
            match = re.match(r'^([A-Za-z]+),\s*Czech\s*-\s*\d{2}\s+\d{2}\s+\d{4}:\s*', description)
            if match:
                city = match.group(1).strip()
                if city:
                    cities.add(city)

        photomedia_cities_count = len(cities) - batch_cities_count
        logger.info(f"Found {photomedia_cities_count} additional cities from PhotoMedia.csv")
    except Exception as e:
        logger.warning(f"Failed to scan PhotoMedia.csv for cities: {e}")

    logger.info(f"Total: {len(cities)} unique editorial cities: {sorted(cities)}")
    return cities


def build_batch_description_map() -> Dict[str, str]:
    """
    Build mapping of file paths to their batch descriptions (for photos with editorial tags).

    Returns:
        Dict mapping file_path -> batch description with editorial tag
    """
    import os
    from givephotobankreadymediafileslib.constants import BATCH_STATE_DIR

    batch_descriptions = {}

    # Load batch registry to get completed batches
    registry = BatchRegistry()
    completed_batches = registry.data.get("completed_batches", [])

    logger.info(f"Building batch description map from {len(completed_batches)} completed batches...")

    for batch_info in completed_batches:
        batch_id = batch_info.get('batch_id')
        if not batch_id:
            continue

        batch_dir = os.path.join(BATCH_STATE_DIR, "batches", batch_id)

        if not os.path.exists(batch_dir):
            logger.debug(f"Batch directory not found: {batch_dir}")
            continue

        try:
            batch_state = BatchState(batch_id, batch_dir)

            for file_entry in batch_state.all_files():
                if not file_entry:
                    continue

                file_path = file_entry.get('file_path', '')
                editorial_data = file_entry.get('editorial_data')

                if editorial_data and isinstance(editorial_data, dict):
                    result = file_entry.get('result', {})
                    description = result.get('description', '')

                    # Check if description has editorial tag
                    city = editorial_data.get('city', '').strip()
                    if city and description:
                        pattern = rf"^{re.escape(city)},\s*Czech\s*-\s*\d{{2}}\s+\d{{2}}\s+\d{{4}}:\s*"
                        if re.match(pattern, description, re.IGNORECASE):
                            # Normalize path for comparison
                            normalized_path = Path(file_path).as_posix().lower()
                            batch_descriptions[normalized_path] = description
        except Exception as e:
            logger.debug(f"Skipping batch {batch_id}: {e}")
            continue

    logger.info(f"Found {len(batch_descriptions)} photos with editorial tags in batches")
    return batch_descriptions


def extract_exif_date(file_path: str) -> Optional[str]:
    """
    Extract date from EXIF metadata in DD MM YYYY format.
    Uses PIL/Pillow (same method as batch mode).

    Args:
        file_path: Path to image file

    Returns:
        Date string in "DD MM YYYY" format or None if not found
    """
    try:
        with Image.open(file_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return None

            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTime' and value:
                    try:
                        dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        return dt.strftime("%d %m %Y")
                    except ValueError:
                        continue
        return None
    except Exception as e:
        logger.warning(f"Failed to extract EXIF date from {file_path}: {e}")
        return None


def find_city_in_text(text: str, cities: Set[str]) -> Optional[str]:
    """
    Find if any city name appears in the given text.

    Args:
        text: Text to search in (title or description)
        cities: Set of city names to look for

    Returns:
        First matching city name or None
    """
    if not text:
        return None

    text_lower = text.lower()

    for city in cities:
        # Search for city name as whole word
        pattern = rf"\b{re.escape(city.lower())}\b"
        if re.search(pattern, text_lower):
            return city

    return None


def truncate_to_sentence(text: str, max_length: int) -> str:
    """
    Truncate text at sentence boundary before max_length.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text ending on sentence boundary
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]

    # Find last sentence ending
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')
    last_sentence_end = max(last_period, last_exclamation, last_question)

    if last_sentence_end > 0:
        return text[:last_sentence_end + 1].strip()

    # Fallback to word boundary
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return text[:last_space].strip() + "..."

    return text[:max_length].strip() + "..."


def regenerate_description_with_editorial(
    file_path: str,
    city: str,
    exif_date: str,
    title: str,
    current_description: str,
    ai_generator: MetadataGenerator
) -> str:
    """
    Regenerate description with editorial tag using AI.

    Args:
        file_path: Path to image file
        city: City name
        exif_date: Date in "DD MM YYYY" format
        title: Current title
        current_description: Current description (without editorial tag)
        ai_generator: MetadataGenerator instance

    Returns:
        New description with editorial tag
    """
    editorial_data = {
        'city': city,
        'country': 'Czech',
        'date': exif_date
    }

    # Generate new description with AI
    new_description = ai_generator.generate_description(
        image_path=file_path,
        title=title,
        context=current_description,
        editorial_data=editorial_data,
        user_description=None
    )

    return new_description


def interactive_confirmation(candidates: List[Dict]) -> List[Dict]:
    """
    Ask user to confirm each candidate before processing.

    Args:
        candidates: List of candidate records

    Returns:
        List of confirmed candidates
    """
    if not candidates:
        return []

    print(f"\n{'='*80}")
    print(f"Found {len(candidates)} photos potentially needing editorial tags")
    print(f"Please review each one to avoid false positives")
    print(f"{'='*80}\n")

    confirmed = []

    for i, candidate in enumerate(candidates, 1):
        print(f"\n{'-'*80}")
        print(f"Photo {i}/{len(candidates)}")
        print(f"{'-'*80}")
        print(f"File: {candidate['filename']}")
        print(f"City detected: {candidate['city']}")
        print(f"Current title: {candidate['current_title']}")
        print(f"Current description: {candidate['current_description'][:100]}..." if len(candidate['current_description']) > 100 else f"Current description: {candidate['current_description']}")
        print(f"Source: {candidate['source']}")

        if candidate['source'] == 'batch':
            print(f"New description: {candidate['batch_description'][:100]}..." if len(candidate['batch_description']) > 100 else f"New description: {candidate['batch_description']}")
        else:
            print(f"New description: [Will be AI-generated with editorial tag: '{candidate['city']}, Czech - [DATE]: ...']")

        while True:
            response = input("\nConfirm this change? [y/n/skip/quit]: ").lower().strip()

            if response == 'y':
                confirmed.append(candidate)
                print("✓ Confirmed")
                break
            elif response == 'n':
                print("✗ Rejected")
                break
            elif response == 'skip':
                print("○ Skipped")
                break
            elif response == 'quit':
                print(f"\n{'='*80}")
                print(f"Confirmation stopped. {len(confirmed)} photos confirmed so far.")
                print(f"{'='*80}\n")
                return confirmed
            else:
                print("Invalid input. Please enter 'y', 'n', 'skip', or 'quit'")

    print(f"\n{'='*80}")
    print(f"Confirmation complete: {len(confirmed)}/{len(candidates)} photos confirmed")
    print(f"{'='*80}\n")

    return confirmed


def process_photomedia_csv(
    csv_path: str,
    cities: Set[str],
    batch_descriptions: Dict[str, str],
    ai_generator: Optional[MetadataGenerator],
    dry_run: bool
) -> List[Dict]:
    """
    Process PhotoMedia.csv and find records needing editorial tags.

    Args:
        csv_path: Path to PhotoMedia.csv
        cities: Set of editorial cities to search for
        batch_descriptions: Mapping of file paths to batch descriptions
        ai_generator: MetadataGenerator instance (None for dry-run)
        dry_run: If True, only report changes without applying

    Returns:
        List of records that were processed
    """
    logger.info(f"Loading PhotoMedia.csv from {csv_path}")
    records = load_csv(csv_path)  # Returns List[Dict[str, str]]

    if not records:
        logger.warning("PhotoMedia.csv is empty or could not be loaded")
        return []

    # PHASE 1: Scan and collect candidates
    logger.info(f"Scanning {len(records)} records for city mentions...")
    candidates = []

    for i, record in enumerate(records):
        filename = record.get(COL_FILE, "")
        full_path = record.get(COL_PATH, "")
        title = record.get(COL_TITLE, "")
        description = record.get(COL_DESCRIPTION, "")

        # Skip if both title and description are empty
        if not title and not description:
            continue

        # Search for city in title or description
        city = find_city_in_text(title, cities)
        if not city:
            city = find_city_in_text(description, cities)

        if not city:
            continue

        # Check if description already has editorial tag for this city
        pattern = rf"^{re.escape(city)},\s*Czech\s*-\s*\d{{2}}\s+\d{{2}}\s+\d{{4}}:\s*"
        if re.match(pattern, description, re.IGNORECASE):
            # Already has correct editorial tag
            continue

        # Found a record needing editorial tag
        normalized_path = Path(full_path).as_posix().lower() if full_path else Path(filename).as_posix().lower()

        # Check if photo is in batch with editorial tag
        if normalized_path in batch_descriptions:
            source = "batch"
            batch_description = batch_descriptions[normalized_path]
        else:
            source = "ai"
            batch_description = None

        candidates.append({
            'record_index': i,  # Index in records list
            'filename': filename,  # For display
            'full_path': full_path,  # For EXIF extraction
            'city': city,
            'current_title': title,
            'current_description': description,
            'source': source,
            'batch_description': batch_description
        })

    if not candidates:
        logger.info("No records need editorial tags")
        return []

    logger.info(f"Found {len(candidates)} records needing editorial tags")

    # Interactive confirmation (only in live mode)
    if not dry_run:
        logger.info("Starting interactive confirmation...")
        candidates = interactive_confirmation(candidates)

        if not candidates:
            logger.info("No candidates confirmed. Exiting.")
            return []

        logger.info(f"{len(candidates)} candidates confirmed by user")

    # PHASE 2: Process candidates with progress bar
    processed = []
    ai_candidates = [c for c in candidates if c['source'] == 'ai']
    batch_candidates = [c for c in candidates if c['source'] == 'batch']

    logger.info(f"  - {len(batch_candidates)} will use batch descriptions")
    logger.info(f"  - {len(ai_candidates)} will be AI-regenerated")

    # Process batch candidates (no AI needed)
    for candidate in batch_candidates:
        candidate['new_description'] = candidate['batch_description']
        processed.append(candidate)

        if not dry_run:
            # Update the record dictionary directly
            records[candidate['record_index']][COL_DESCRIPTION] = candidate['new_description']

    # Process AI candidates with progress bar
    if ai_candidates:
        if dry_run:
            # Dry-run: just mark for AI generation
            for candidate in ai_candidates:
                candidate['new_description'] = "[WILL BE AI GENERATED]"
                processed.append(candidate)
        else:
            # Live mode: AI regenerate with progress bar
            logger.info("Regenerating descriptions with AI...")
            for candidate in tqdm(ai_candidates, desc="AI generation", unit="photo"):
                # Extract EXIF date
                exif_date = extract_exif_date(candidate['full_path'])
                if not exif_date:
                    logger.warning(f"Could not extract EXIF date from {candidate['filename']}, skipping")
                    continue

                # Regenerate with AI
                new_description = regenerate_description_with_editorial(
                    candidate['full_path'],
                    candidate['city'],
                    exif_date,
                    candidate['current_title'],
                    candidate['current_description'],
                    ai_generator
                )

                candidate['new_description'] = new_description
                processed.append(candidate)

                # Update the record dictionary directly
                records[candidate['record_index']][COL_DESCRIPTION] = new_description

    if not dry_run and processed:
        logger.info(f"Writing {len(processed)} updates to PhotoMedia.csv...")
        save_csv_with_backup(records, csv_path)

    return processed


def print_dry_run_results(processed: List[Dict]) -> None:
    """
    Print dry-run results showing what would be changed.

    Args:
        processed: List of records that would be processed
    """
    if not processed:
        print("\n✓ No records need editorial tags")
        return

    print(f"\n{'='*80}")
    print(f"DRY RUN: Found {len(processed)} records needing editorial tags")
    print(f"{'='*80}\n")

    # Group by source
    batch_sources = [p for p in processed if p['source'] == 'batch']
    ai_sources = [p for p in processed if p['source'] == 'ai']

    if batch_sources:
        print(f"\n{len(batch_sources)} records will use batch descriptions:")
        for rec in batch_sources[:10]:  # Show first 10
            print(f"\n  File: {rec['filename']}")
            print(f"  City: {rec['city']}")
            print(f"  Current title: {rec['current_title']}")
            print(f"  Current description: {rec['current_description']}")
            print(f"  New description: {rec['new_description']}")
        if len(batch_sources) > 10:
            print(f"\n  ... and {len(batch_sources) - 10} more")

    if ai_sources:
        print(f"\n{len(ai_sources)} records will be AI-regenerated:")
        for rec in ai_sources[:10]:  # Show first 10
            print(f"\n  File: {rec['filename']}")
            print(f"  City: {rec['city']}")
            print(f"  Current title: {rec['current_title']}")
            print(f"  Current description: {rec['current_description']}")
        if len(ai_sources) > 10:
            print(f"\n  ... and {len(ai_sources) - 10} more")

    print(f"\n{'='*80}")
    print(f"Total: {len(processed)} records will be updated")
    print(f"Run without --dry-run to apply changes")
    print(f"{'='*80}\n")


def print_live_run_summary(processed: List[Dict]) -> None:
    """
    Print summary of live run results.

    Args:
        processed: List of records that were processed
    """
    if not processed:
        print("\n✓ No records needed editorial tags")
        return

    batch_sources = [p for p in processed if p['source'] == 'batch']
    ai_sources = [p for p in processed if p['source'] == 'ai']

    print(f"\n{'='*80}")
    print(f"COMPLETED: Updated {len(processed)} records in PhotoMedia.csv")
    print(f"{'='*80}")
    print(f"  - {len(batch_sources)} used batch descriptions")
    print(f"  - {len(ai_sources)} AI-regenerated")
    print(f"{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add missing editorial tags to PhotoMedia.csv"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser.add_argument(
        '--csv',
        type=str,
        default=DEFAULT_MEDIA_CSV_PATH,
        help='Path to PhotoMedia.csv'
    )

    args = parser.parse_args()

    logger.info("="*80)
    logger.info("Add Editorial Tags to PhotoMedia.csv")
    logger.info("="*80)
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    logger.info(f"CSV: {args.csv}")
    logger.info("="*80)

    # Step 1: Collect editorial cities from batches and PhotoMedia.csv
    cities = collect_editorial_cities(args.csv)

    if not cities:
        logger.warning("No editorial cities found. Nothing to do.")
        return 0

    # Step 2: Build batch description map
    batch_descriptions = build_batch_description_map()

    # Step 3: Initialize AI generator (only for live mode)
    ai_generator = None
    if not args.dry_run:
        try:
            config = Config()
            provider, model = config.get_default_ai_model()
            logger.info(f"Initializing AI generator: {provider}/{model}")
            model_key = f"{provider}/{model}"
            api_key = config.get_ai_api_key(provider)
            ai_generator = create_metadata_generator(model_key, api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize AI generator: {e}")
            return 1

    # Step 4: Process PhotoMedia.csv
    try:
        processed = process_photomedia_csv(
            args.csv,
            cities,
            batch_descriptions,
            ai_generator,
            args.dry_run
        )
    except Exception as e:
        logger.error(f"Error processing PhotoMedia.csv: {e}")
        return 1

    # Step 5: Print results
    if args.dry_run:
        print_dry_run_results(processed)
    else:
        print_live_run_summary(processed)

    logger.info("Done")
    return 0


if __name__ == '__main__':
    sys.exit(main())