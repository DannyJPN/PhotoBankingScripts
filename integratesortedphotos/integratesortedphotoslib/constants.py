"""
Configuration constants for integrate sorted photos script.

This module contains all configurable paths and settings used by the
integrate sorted photos functionality.
"""

# Default directory paths
DEFAULT_SORTED_FOLDER = "I:/Roztříděno"
DEFAULT_TARGET_FOLDER = "J:/"
DEFAULT_LOG_DIR = "H:/Logs"

# Copy operation settings
DEFAULT_COPY_METHOD = "streaming"  # "streaming" or "batch" or "estimated"
DEFAULT_PROGRESS_ESTIMATION = True  # Enable progress estimation
DEFAULT_OVERWRITE = False  # Don't overwrite existing files by default
BATCH_SIZE_LIMIT = 10000  # Switch to streaming if more files detected (for batch mode)
SAMPLE_SIZE = 100  # Number of directories to sample for file count estimation
