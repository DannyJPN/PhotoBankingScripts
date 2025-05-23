﻿import os
import argparse
import logging
import re

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory, load_csv
from shared.logging_config import setup_logging

from exportpreparedmedialib.constants import (
    DEFAULT_PHOTO_CSV,
    DEFAULT_OUTPUT_FOLDER,
    VALID_STATUS
)

from exportpreparedmedialib.banks_logic import (
    get_enabled_banks,
    get_output_paths,
    should_include_item
)

from exportpreparedmedialib.exporters import export_to_photobanks


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Export prepared media to various stock photo banks."
    )
    # Základní parametry
    parser.add_argument("--photo_csv", type=str, default=DEFAULT_PHOTO_CSV,
                        help="Path to the input CSV file with photo metadata")
    parser.add_argument("--output_folder", type=str, default=DEFAULT_OUTPUT_FOLDER,
                        help="Path to the output folder for CSV files")
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
    parser.add_argument("--all", action="store_true",
                        help="Export to all supported banks")

    return parser.parse_args()


def main():
    # 1. Načtení argumentů
    args = parse_arguments()

    # Pokud je zadaný přepínač --all, aktivuj všechny banky
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

    # 2. Zajištění výstupní složky
    ensure_directory(args.output_folder)

    # 3. Aktivace logování - TATO ČÁST SE NESMÍ MĚNIT
    LOG_FILE = get_log_filename(args.output_folder)
    setup_logging(args.debug, LOG_FILE)
    logging.info("Starting export process")

    # Podrobné informace o běhu skriptu
    logging.debug(f"Script running from: {os.path.abspath(__file__)}")
    logging.debug(f"Current working directory: {os.getcwd()}")
    logging.debug(f"Command line arguments: {vars(args)}")

    # 4. Získání aktivních bank
    enabled_banks = get_enabled_banks(args)
    if not enabled_banks:
        logging.warning("No banks enabled. Use --shutterstock, --adobestock, etc. to enable export.")
        return

    # 5. Načtení cest k výstupním CSV
    output_paths = get_output_paths(enabled_banks, args.output_folder)

    # 6. Načtení vstupního CSV
    try:
        items = load_csv(args.photo_csv)
        logging.info(f"Loaded {len(items)} items from {args.photo_csv}")
    except Exception as e:
        logging.error(f"Failed to load input CSV: {e}")
        return

    # 7. Filtrování položek - základní filtrování, detailní filtrování podle banky bude provedeno později
    # Zde filtrujeme položky, které mají status 'kontrolováno' v jakémkoli sloupci
    filtered_items = [item for item in items if should_include_item(item)]
    logging.info(f"Filtered {len(filtered_items)} items with status '{VALID_STATUS}' in any column")

    # 8. Export do fotobank - použij funkci should_include_item pro filtrování záznamů podle statusu pro každou fotobanku
    # Rozšířené záznamy budou vytvořeny uvnitř funkce export_to_photobanks
    export_to_photobanks(filtered_items, enabled_banks, output_paths, filter_func=should_include_item)

    logging.info("Export process completed successfully")


if __name__ == "__main__":
    main()
