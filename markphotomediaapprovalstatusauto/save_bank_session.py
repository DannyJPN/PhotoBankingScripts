#!/usr/bin/env python3
"""Save browser session cookies after manual CAPTCHA solving.

This script opens a browser to protected photobank pages.
The user manually solves any CAPTCHA challenges.
Once the page loads successfully, cookies are saved for later use.

Usage:
    python save_bank_session.py [--bank BANK]

Banks: ShutterStock, Pond5, BigStockPhoto, Dreamstime
"""

import argparse
import logging

from markphotomediaapprovalstatusautolib.public_portfolio.constants import BLOCKED_BANKS
from markphotomediaapprovalstatusautolib.public_portfolio.session import run_session_saver

logger = logging.getLogger(__name__)


def main() -> None:
    """Entry point for save_bank_session CLI.

    :return: None
    """
    parser = argparse.ArgumentParser(description="Save browser session cookies for photobanks")
    parser.add_argument(
        "--bank",
        choices=BLOCKED_BANKS + ["all"],
        default="all",
        help="Bank to save session for (default: all)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds (default: 300)",
    )
    args = parser.parse_args()

    banks = BLOCKED_BANKS if args.bank == "all" else [args.bank]

    results = {}
    for bank in banks:
        success = run_session_saver(bank, args.timeout)
        results[bank] = "OK" if success else "FAILED"
        logger.info("")

    logger.info("=" * 60)
    logger.info("RESULTS:")
    for bank, status in results.items():
        logger.info("  %s: %s", bank, status)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()