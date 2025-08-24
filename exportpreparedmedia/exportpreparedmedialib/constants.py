import os

# Výchozí hodnoty pro vstupní a výstupní soubory
DEFAULT_PHOTO_CSV = r"L:\Můj disk\XLS\Fotobanky\PhotoMediaTest.csv"
DEFAULT_OUTPUT_DIR = r"L:\Můj disk\XLS\Fotobanky\CSV"
DEFAULT_OUTPUT_PREFIX = "CSV"

# Výchozí hodnoty pro metadata
DEFAULT_LOCATION = "Czech republic"
DEFAULT_USERNAME = "DannyJPN"
DEFAULT_COPYRIGHT_AUTHOR = "Dan K."

# Cesty k mapám kategorií
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ADOBE_CATEGORY_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "adobe_stock_categories.csv")
DEFAULT_DREAMSTIME_CATEGORY_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "dreams_time_categories.csv")

# Cesty k CSV souborům pro exporty
DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "photobank_export_formats.csv")
DEFAULT_POND_PRICES_PATH = os.path.join(BASE_DIR, "exportpreparedmedialib", "data", "pond_prices.csv")

# Regulární výrazy pro detekci typů souborů
EDITORIAL_REGEX = r"^[A-Za-z]{1,}, [A-Za-z]{1,} - \d{2} \d{2} \d{4}:"
VECTOREXT_REGEX = r"(cdr|ai|eps|svg)$"

# Validní hodnota pro status
VALID_STATUS = "připraveno"

# Default log directory
DEFAULT_LOG_DIR = "H:/Logs"