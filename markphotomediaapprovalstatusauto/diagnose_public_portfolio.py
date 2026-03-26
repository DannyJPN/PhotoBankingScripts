#!/usr/bin/env python3
"""Diagnose a single public portfolio page."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from markphotomediaapprovalstatusautolib.constants import DEFAULT_LOG_DIR
from markphotomediaapprovalstatusautolib.public_portfolio.banks import BANK_ADAPTERS
from markphotomediaapprovalstatusautolib.public_portfolio.browser import browser_context
from markphotomediaapprovalstatusautolib.public_portfolio.config_store import load_effective_config
from markphotomediaapprovalstatusautolib.public_portfolio.constants import DEFAULT_PUBLIC_PORTFOLIO_CONFIG
from markphotomediaapprovalstatusautolib.public_portfolio.diagnostics import detect_blocked_page, log_page_diagnostics
from markphotomediaapprovalstatusautolib.public_portfolio.runner import _contributor_from_url, fetch_public_portfolio_page
from shared.file_operations import ensure_directory
from shared.logging_config import setup_logging
from shared.utils import get_log_filename


def parse_arguments():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Diagnose a public portfolio page for one bank")
    parser.add_argument("--bank", choices=sorted(BANK_ADAPTERS.keys()), required=True, help="Bank to diagnose")
    parser.add_argument(
        "--public-portfolio-config",
        type=str,
        default=DEFAULT_PUBLIC_PORTFOLIO_CONFIG,
        help="Path to public portfolio config JSON",
    )
    parser.add_argument("--visible", action="store_true", help="Run browser with visible UI")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--log-dir", type=str, default=DEFAULT_LOG_DIR, help="Directory for log files")
    return parser.parse_args()


def main():
    """Run diagnosis for one configured bank."""
    args = parse_arguments()

    log_dir = args.log_dir
    try:
        ensure_directory(log_dir)
    except Exception:
        log_dir = str(Path(__file__).resolve().parent / "logs")
        ensure_directory(log_dir)

    setup_logging(debug=args.debug, log_file=get_log_filename(log_dir))
    if log_dir != args.log_dir:
        logging.warning("Requested log dir %s is not available. Using fallback %s", args.log_dir, log_dir)

    adapter_cls = BANK_ADAPTERS[args.bank]
    adapter = adapter_cls(None)
    if not adapter.is_supported():
        logging.error("%s does not support public portfolio mode.", args.bank)
        return

    config = load_effective_config(args.public_portfolio_config)
    bank_config = config.get("banks", {}).get(args.bank, {})
    portfolio_url = bank_config.get("portfolio_url")
    if not portfolio_url:
        logging.error("No portfolio URL configured for %s", args.bank)
        return

    contributor_id = bank_config.get("contributor_id") or _contributor_from_url(portfolio_url)
    logging.info("Diagnosing %s portfolio: %s", args.bank, portfolio_url)

    with browser_context(headless=not args.visible, bank=args.bank) as context:
        live_adapter = adapter_cls(context)
        html, diagnostics = fetch_public_portfolio_page(
            context,
            portfolio_url,
            item_url_regex=live_adapter.item_url_regex,
        )
        blocked, reason = detect_blocked_page(diagnostics)
        log_page_diagnostics(args.bank, diagnostics, reason=reason, blocked=blocked)

        if blocked:
            logging.warning("%s diagnosis result: page looks blocked or incomplete.", args.bank)
            return

        assets = live_adapter.extract_assets_from_portfolio(html, contributor_id)
        logging.info("%s diagnosis result: extracted %d assets", args.bank, len(assets))
        for asset in assets[:20]:
            logging.info("%s asset: %s | %s", args.bank, asset.url, asset.title)

        if len(assets) > 20:
            logging.info("%s diagnosis result: %d more assets omitted from log", args.bank, len(assets) - 20)


if __name__ == "__main__":
    main()
