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
from givephotobankreadymediafileslib.constants import DEFAULT_LOG_DIR, IMAGE_EXTENSIONS
from givephotobankreadymediafileslib.alternative_generator import AlternativeGenerator, get_alternative_output_dirs


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate alternative versions of media files (format conversions + edit effects)."
    )
    parser.add_argument("file", type=str, help="Path to the source media file")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Format options
    parser.add_argument("--formats", type=str, nargs="+",
                        choices=[".png", ".tif"], default=[".png", ".tif"],
                        help="Output formats to generate (default: .png .tif)")

    # Edit effect options
    parser.add_argument("--effects", type=str, nargs="+",
                        choices=["_bw", "_negative", "_sharpen", "_misty", "_blurred"],
                        default=["_bw", "_negative", "_sharpen", "_misty", "_blurred"],
                        help="Edit effects to generate (default: all)")

    # Output control
    parser.add_argument("--formats-only", action="store_true",
                        help="Generate only format conversions, no edit effects")
    parser.add_argument("--effects-only", action="store_true",
                        help="Generate only edit effects, no format conversions")

    return parser.parse_args()


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
        # Determine what to generate
        enabled_formats = [] if args.effects_only else args.formats
        enabled_effects = [] if args.formats_only else args.effects

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