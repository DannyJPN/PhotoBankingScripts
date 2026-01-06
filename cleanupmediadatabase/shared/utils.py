"""
Utility helpers for CleanupMediaDatabase.
"""

from datetime import datetime
import os
import sys
import logging


def get_script_name() -> str:
    """
    Determine the running script name.
    """
    script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    logging.debug("Script name determined as: %s", script_name)
    return script_name


def get_log_filename(log_dir: str) -> str:
    """
    Build a log filename based on script name and timestamp.
    """
    script_name = get_script_name()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{script_name}_Log_{current_time}.log"
    log_full_path = os.path.join(log_dir, log_filename)
    logging.debug("Log filename generated as: %s", log_full_path)
    return log_full_path
