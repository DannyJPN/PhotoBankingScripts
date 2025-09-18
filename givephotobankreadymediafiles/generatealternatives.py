#!/usr/bin/env python
"""
Generate Alternatives - Standalone script for generating alternative versions of media files.
Creates format conversions (PNG, TIF) and edit alternatives (BW, negative, sharpen, misty, blurred).
"""
import os
import sys
import argparse
import logging
from typing import List, Optional

from shared.logging_config import setup_logging
from shared.file_operations import ensure_directory
from givephotobankreadymediafileslib.constants import (
    DEFAULT_LOG_DIR, IMAGE_EXTENSIONS,
    DEFAULT_ALTERNATIVE_EFFECTS, DEFAULT_ALTERNATIVE_FORMATS,
    EFFECT_NAME_MAPPING, FORMAT_NAME_MAPPING, ALTERNATIVE_EDIT_TAGS, ALTERNATIVE_FORMATS
)
from givephotobankreadymediafileslib.alternative_generator import AlternativeGenerator, get_alternative_output_dirs


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate alternative versions of media files (format conversions + edit effects)."
    )
    parser.add_argument("--file", type=str, help="Path to the source media file")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Format options
    available_formats = ', '.join(sorted(FORMAT_NAME_MAPPING.keys()))
    parser.add_argument("--formats", type=str,
                        default=DEFAULT_ALTERNATIVE_FORMATS,
                        help=f"Comma-separated output formats to generate. Available: {available_formats} (default: {DEFAULT_ALTERNATIVE_FORMATS})")

    # Edit effect options
    available_effects = ', '.join(sorted(EFFECT_NAME_MAPPING.keys()))
    parser.add_argument("--effects", type=str,
                        default=DEFAULT_ALTERNATIVE_EFFECTS,
                        help=f"Comma-separated edit effects to generate. Available: {available_effects} (default: {DEFAULT_ALTERNATIVE_EFFECTS})")

    # Output control
    parser.add_argument("--formats-only", action="store_true",
                        help="Generate only format conversions, no edit effects")
    parser.add_argument("--effects-only", action="store_true",
                        help="Generate only edit effects, no format conversions")

    return parser.parse_args()


def parse_comma_separated(value: str) -> List[str]:
    """Parse comma-separated string into list, trimming whitespace."""
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]


def map_user_effects_to_tags(user_effects: List[str]) -> List[str]:
    """Map user-friendly effect names to technical tags."""
    technical_tags = []
    for effect in user_effects:
        effect_lower = effect.lower()
        if effect_lower in EFFECT_NAME_MAPPING:
            technical_tags.append(EFFECT_NAME_MAPPING[effect_lower])
        else:
            # Check if it's already a technical tag
            if effect in ALTERNATIVE_EDIT_TAGS:
                technical_tags.append(effect)
            else:
                available_names = ', '.join(sorted(EFFECT_NAME_MAPPING.keys()))
                raise ValueError(f"Unknown effect '{effect}'. Available effects: {available_names}")
    return technical_tags


def map_user_formats_to_extensions(user_formats: List[str]) -> List[str]:
    """Map user-friendly format names to technical extensions."""
    technical_extensions = []
    for format_name in user_formats:
        format_lower = format_name.lower()
        if format_lower in FORMAT_NAME_MAPPING:
            technical_extensions.append(FORMAT_NAME_MAPPING[format_lower])
        else:
            # Check if it's already a technical extension
            if format_name in ALTERNATIVE_FORMATS:
                technical_extensions.append(format_name)
            else:
                available_formats = ', '.join(sorted(FORMAT_NAME_MAPPING.keys()))
                raise ValueError(f"Unknown format '{format_name}'. Available formats: {available_formats}")
    return technical_extensions


def validate_file(file_path: str) -> bool:
    """Validate that the file exists and is supported."""
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        print(f"ERROR: File not found: {file_path}")
        return False

    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in [ext.lower() for ext in IMAGE_EXTENSIONS]:
        logging.error(f"Unsupported file type: {file_ext}")
        print(f"ERROR: Unsupported file type: {file_ext}")
        print(f"Supported extensions: {', '.join(IMAGE_EXTENSIONS)}")
        return False

    return True


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = os.path.join(args.log_dir, "generatealternatives.log")
    setup_logging(debug=args.debug, log_file=log_file)

    # Log startup
    logging.info("Starting generatealternatives.py")
    logging.info(f"Processing file: {args.file}")

    # Validate input file
    if not validate_file(args.file):
        return 1

    try:
        # Parse comma-separated strings into lists
        formats_list = parse_comma_separated(args.formats)
        effects_list = parse_comma_separated(args.effects)

        # Map user-friendly names to technical tags/extensions
        mapped_formats = map_user_formats_to_extensions(formats_list) if formats_list else []
        mapped_effects = map_user_effects_to_tags(effects_list) if effects_list else []

        # Determine what to generate
        enabled_formats = [] if args.effects_only else mapped_formats
        enabled_effects = [] if args.formats_only else mapped_effects

        if not enabled_formats and not enabled_effects:
            print("ERROR: Nothing to generate. Use --formats-only or --effects-only, or specify formats/effects.")
            return 1

        logging.info(f"Enabled formats: {enabled_formats}")
        logging.info(f"Enabled effects: {enabled_effects}")

        # Get output directories
        target_dir, edited_dir = get_alternative_output_dirs(args.file)
        logging.info(f"Target directory: {target_dir}")
        logging.info(f"Edited directory: {edited_dir}")

        # Initialize generator
        generator = AlternativeGenerator(
            enabled_alternatives=enabled_effects,
            enabled_formats=enabled_formats
        )

        print(f"Processing: {os.path.basename(args.file)}")
        print(f"Source: {args.file}")
        print(f"Target directory: {target_dir}")
        print(f"Edited directory: {edited_dir}")
        print()

        # Generate alternatives
        alternatives = generator.generate_all_versions(args.file, target_dir, edited_dir)

        if alternatives:
            print(f"Successfully generated {len(alternatives)} alternative versions:")
            print()

            # Group and display results
            format_conversions = [alt for alt in alternatives if alt['type'] == 'format']
            edit_effects = [alt for alt in alternatives if alt['type'] == 'edit']

            if format_conversions:
                print("Format Conversions:")
                for alt in format_conversions:
                    filename = os.path.basename(alt['path'])
                    size_mb = os.path.getsize(alt['path']) / (1024 * 1024)
                    print(f"  {filename} ({size_mb:.1f} MB) - {alt['description']}")
                print()

            if edit_effects:
                print("Edit Effects:")
                # Group by original format
                effects_by_format = {}
                for alt in edit_effects:
                    format_ext = alt['format']
                    if format_ext not in effects_by_format:
                        effects_by_format[format_ext] = []
                    effects_by_format[format_ext].append(alt)

                for format_ext, effects in effects_by_format.items():
                    print(f"  {format_ext.upper()} format:")
                    for alt in effects:
                        filename = os.path.basename(alt['path'])
                        size_mb = os.path.getsize(alt['path']) / (1024 * 1024)
                        effect_name = alt['edit'].replace('_', '')
                        print(f"    {filename} ({size_mb:.1f} MB) - {alt['description']}")
                    print()

            print(f"All files saved successfully!")
            logging.info(f"Generated {len(alternatives)} alternatives successfully")

        else:
            print("No alternatives were generated.")
            logging.warning("No alternatives were generated")
            return 1

        return 0

    except Exception as e:
        logging.error(f"Error generating alternatives: {e}")
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())