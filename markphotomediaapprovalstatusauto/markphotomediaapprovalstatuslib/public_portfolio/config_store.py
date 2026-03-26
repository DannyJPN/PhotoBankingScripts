"""Load/save public portfolio configuration."""

from __future__ import annotations

import logging
from typing import Dict, Any

from markphotomediaapprovalstatuslib.public_portfolio.constants import DEFAULT_PUBLIC_PORTFOLIO_DEFAULTS
from shared.file_operations import load_json_file, save_json_file


def load_config(path: str) -> Dict[str, Any]:
    """
    Load public portfolio configuration from JSON.

    :param path: Path to the configuration file.
    :return: Parsed configuration dictionary or an empty dict on failure.
    """
    try:
        return load_json_file(path)
    except FileNotFoundError:
        logging.info("Public portfolio config not found: %s", path)
        return {}
    except Exception as exc:
        logging.warning("Failed to read public portfolio config %s: %s", path, exc)
        return {}


def save_config(path: str, data: Dict[str, Any]) -> None:
    """
    Save public portfolio configuration to JSON.

    :param path: Path to the destination file.
    :param data: Configuration data to serialize.
    """
    try:
        save_json_file(path, data, indent=2, ensure_ascii=True)
        logging.info("Saved public portfolio config to %s", path)
    except Exception as exc:
        logging.warning("Failed to save public portfolio config %s: %s", path, exc)


def load_effective_config(path: str) -> Dict[str, Any]:
    """
    Load the effective configuration with committed defaults and user overrides.

    :param path: Path to the user override configuration.
    :return: Merged configuration dictionary.
    """
    config = load_config(DEFAULT_PUBLIC_PORTFOLIO_DEFAULTS)
    config.setdefault("banks", {})

    user_config = load_config(path)
    user_banks = user_config.get("banks", {})
    for bank, bank_config in user_banks.items():
        merged_bank = dict(config["banks"].get(bank, {}))
        merged_bank.update(bank_config)
        config["banks"][bank] = merged_bank

    return config
