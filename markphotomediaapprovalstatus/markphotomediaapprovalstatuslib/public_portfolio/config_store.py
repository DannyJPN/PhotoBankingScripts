"""Load/save public portfolio configuration."""

from __future__ import annotations

import json
import logging
from typing import Dict, Any


def load_config(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        logging.info("Public portfolio config not found: %s", path)
        return {}
    except Exception as exc:
        logging.warning("Failed to read public portfolio config %s: %s", path, exc)
        return {}


def save_config(path: str, data: Dict[str, Any]) -> None:
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=True)
        logging.info("Saved public portfolio config to %s", path)
    except Exception as exc:
        logging.warning("Failed to save public portfolio config %s: %s", path, exc)
