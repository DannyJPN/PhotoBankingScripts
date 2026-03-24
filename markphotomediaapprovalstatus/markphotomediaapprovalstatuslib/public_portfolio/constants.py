"""Constants for public portfolio approval detection."""

from pathlib import Path

DEFAULT_PUBLIC_PORTFOLIO_CONFIG = "public_portfolios.json"
DEFAULT_PUBLIC_PORTFOLIO_DEFAULTS = str(Path(__file__).resolve().parents[2] / "public_portfolios.defaults.json")
