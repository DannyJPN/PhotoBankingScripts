"""Launch photobank login pages in web browser."""
import os
import argparse
import logging
import sys

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.utils import get_log_filename
from shared.file_operations import ensure_directory
from shared.logging_config import setup_logging

from launchphotobankslib.constants import (
    DEFAULT_BANK_CSV,
    DEFAULT_LOG_DIR,
    DEFAULT_DELAY_BETWEEN_OPENS
)
from launchphotobankslib.bank_launcher import BankLauncher


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Launch photobank login pages in web browser."
    )
    parser.add_argument("--bank_csv", type=str, default=DEFAULT_BANK_CSV,
                        help="Path to CSV file with bank URLs")
    parser.add_argument("--log_dir", type=str, default=DEFAULT_LOG_DIR,
                        help="Directory for log files")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--delay", type=int, default=DEFAULT_DELAY_BETWEEN_OPENS,
                        help="Delay between opening tabs (seconds)")
    parser.add_argument("--banks", nargs='*',
                        help="Specific banks to open (default: all)")
    parser.add_argument("--dry_run", action="store_true",
                        help="Show what would be opened without actually opening")
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()

    # Setup logging
    ensure_directory(args.log_dir)
    log_file = get_log_filename(args.log_dir)
    setup_logging(debug=args.debug, log_file=log_file)

    logging.info("Starting LaunchPhotobanks process")
    logging.info(f"Bank CSV: {args.bank_csv}")
    logging.info(f"Delay between opens: {args.delay}s")

    try:
        # Load bank configuration
        launcher = BankLauncher(args.bank_csv)

        # Filter banks if specified
        banks_to_open = args.banks if args.banks else launcher.get_all_bank_names()
        logging.info(f"Will open {len(banks_to_open)} banks: {', '.join(banks_to_open)}")

        # Validate selected banks
        all_banks = launcher.get_all_bank_names()
        invalid_banks = [b for b in banks_to_open if b not in all_banks]
        if invalid_banks:
            logging.error(f"Unknown banks specified: {', '.join(invalid_banks)}")
            logging.info(f"Available banks: {', '.join(all_banks)}")
            return 1

        # Launch banks
        if args.dry_run:
            logging.info("DRY RUN: Would open the following URLs:")
            for bank_name in banks_to_open:
                url = launcher.get_bank_url(bank_name)
                logging.info(f"  {bank_name}: {url}")
        else:
            results = launcher.launch_banks(banks_to_open, delay=args.delay)

            # Check if any failed
            failed_banks = [name for name, success in results.items() if not success]
            if failed_banks:
                logging.warning(f"Failed to open: {', '.join(failed_banks)}")
                return 1

        logging.info("LaunchPhotobanks process completed successfully")
        return 0

    except Exception as e:
        logging.error("LaunchPhotobanks process failed: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())