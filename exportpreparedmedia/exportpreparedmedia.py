import os
import argparse
import logging
import re

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, load_csv
from shared.logging_config import setup_logging

from exportpreparedmedialib.constants import (
    DEFAULT_PHOTO_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OUTPUT_PREFIX,
    DEFAULT_LOG_DIR,
    VALID_STATUS
)

from exportpreparedmedialib.banks_logic import (
    get_enabled_banks,
    get_output_paths,
    should_include_item
)

from exportpreparedmedialib.exporters import export_to_photobanks


def _is_not_edited(item: dict) -> bool:
    """Check if item is not from edited/processed folder."""
    path = item.get('Cesta', '')
    return 'upravené' not in path.lower()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Export prepared media to various stock photo banks."
    )
    # Základní parametry
    parser.add_argument("--photo_csv", type=str, default=DEFAULT_PHOTO_CSV,
                        help="Path to the input CSV file with photo metadata")
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help="Directory for output CSV files")
    parser.add_argument("--output_prefix", type=str, default=DEFAULT_OUTPUT_PREFIX,
                        help="Prefix for output CSV filenames")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing output files")

    # Přepínače pro jednotlivé banky
    parser.add_argument("--shutterstock", action="store_true",
                        help="Export to ShutterStock")
    parser.add_argument("--adobestock", action="store_true",
                        help="Export to Adobe Stock")
    parser.add_argument("--dreamstime", action="store_true",
                        help="Export to DreamsTime")
    parser.add_argument("--depositphotos", action="store_true",
                        help="Export to DepositPhotos")
    parser.add_argument("--bigstockphoto", action="store_true",
                        help="Export to BigStockPhoto")
    parser.add_argument("--123rf", dest="_123rf", action="store_true",
                        help="Export to 123RF")
    parser.add_argument("--canstockphoto", action="store_true",
                        help="Export to CanStockPhoto")
    parser.add_argument("--pond5", action="store_true",
                        help="Export to Pond5")
    parser.add_argument("--gettyimages", action="store_true",
                        help="Export to GettyImages")
    parser.add_argument("--alamy", action="store_true",
                        help="Export to Alamy")
    # New banks
    parser.add_argument("--pixta", action="store_true",
                        help="Export to Pixta")
    parser.add_argument("--freepik", action="store_true",
                        help="Export to Freepik")
    parser.add_argument("--vecteezy", action="store_true",
                        help="Export to Vecteezy")
    parser.add_argument("--storyblocks", action="store_true",
                        help="Export to StoryBlocks")
    parser.add_argument("--all", action="store_true",
                        help="Export to all supported banks (excluding web-only banks: Envato, 500px, MostPhotos)")

    # Filtering options
    parser.add_argument("--include-edited", action="store_true",
                        help="Include edited/processed photos from 'Upravené foto' folders (default: only original photos)")
    parser.add_argument("--include-alternative-formats", action="store_true",
                        help="Include alternative formats (PNG, TIFF, RAW) in export (default: only JPG)")

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Kontrola vzájemného vylučování parametrů
    individual_banks = [args.shutterstock, args.adobestock, args.dreamstime,
                       args.depositphotos, args.bigstockphoto, args._123rf,
                       args.canstockphoto, args.pond5, args.gettyimages, args.alamy,
                       args.pixta, args.freepik, args.vecteezy, args.storyblocks]

    if args.all and any(individual_banks):
        logging.error("Cannot use --all together with individual bank parameters")
        return

    # Pokud je zadaný přepínač --all, aktivuj všechny banky (kromě web-only)
    if args.all:
        args.shutterstock = True
        args.adobestock = True
        args.dreamstime = True
        args.depositphotos = True
        args.bigstockphoto = True
        args._123rf = True
        args.canstockphoto = True
        args.pond5 = True
        args.gettyimages = True
        args.alamy = True
        # New banks with CSV export support
        args.pixta = True
        args.freepik = True
        args.vecteezy = True
        args.storyblocks = True
        # Note: Envato, 500px, MostPhotos are web-only (no CSV export)

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("Starting export process")

    # Zajištění výstupní složky
    ensure_directory(args.output_dir)

    # Podrobné informace o běhu skriptu
    logging.debug(f"Script running from: {os.path.abspath(__file__)}")
    logging.debug(f"Current working directory: {os.getcwd()}")
    logging.debug(f"Command line arguments: {vars(args)}")

    # Získání aktivních bank
    enabled_banks = get_enabled_banks(args)
    if not enabled_banks:
        logging.warning("No banks enabled. Use --shutterstock, --adobestock, etc. to enable export.")
        return

    # Načtení cest k výstupním CSV
    output_paths = get_output_paths(enabled_banks, args.output_dir, args.output_prefix)

    # Načtení vstupního CSV
    try:
        items = load_csv(args.photo_csv)
        logging.info(f"Loaded {len(items)} items from {args.photo_csv}")
    except Exception as e:
        logging.error(f"Failed to load input CSV: {e}")
        return

    # Filtrování položek - základní filtrování, detailní filtrování podle banky bude provedeno později
    # Zde filtrujeme položky, které mají status 'kontrolováno' v jakémkoli sloupci
    filtered_items = [item for item in items if should_include_item(item)]
    logging.info(f"Filtered {len(filtered_items)} items with status '{VALID_STATUS}' in any column")

    # Apply additional filtering based on switches
    if not args.include_edited:
        original_count = len(filtered_items)
        filtered_items = [item for item in filtered_items if _is_not_edited(item)]
        excluded_count = original_count - len(filtered_items)
        logging.info(f"Excluded {excluded_count} edited photos (--include-edited not set)")

    # Export do fotobank - použij funkci should_include_item pro filtrování záznamů podle statusu pro každou fotobanku
    # Rozšířené záznamy budou vytvořeny uvnitř funkce export_to_photobanks
    # Alternative formats are handled per-bank by expand_item_with_alternative_formats based on bank's supported formats
    export_to_photobanks(filtered_items, enabled_banks, output_paths,
                        filter_func=should_include_item,
                        include_alternative_formats=args.include_alternative_formats)

    logging.info("Export process completed successfully")


if __name__ == "__main__":
    main()