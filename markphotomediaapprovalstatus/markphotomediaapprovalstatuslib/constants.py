"""
Constants for the markphotomediaapprovalstatus script.
"""

# List of photobanks to check
BANKS = [
    "ShutterStock",
    "AdobeStock",
    "Dreamstime",
    "DepositPhotos",
    "BigStockPhoto",
    "123RF",
    "CanStockPhoto",
    "Pond5",
    "GettyImages",
    "Alamy"
]

# Default paths
DEFAULT_PHOTO_CSV_PATH = "L:/Můj disk/XLS/Fotobanky/PhotoMedia.csv"
DEFAULT_LOG_DIR = "H:/Logs"

# Column identifiers
STATUS_COLUMN_KEYWORD = "status"

# Status values
STATUS_CHECKED = "kontrolováno"
STATUS_APPROVED = "schváleno"
STATUS_REJECTED = "zamítnuto"
STATUS_MAYBE = "schváleno?"

# User input options
INPUT_APPROVE = "a"
INPUT_REJECT = "n"
INPUT_MAYBE = "m"

