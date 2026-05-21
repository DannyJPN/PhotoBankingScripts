import os
import re
import sys
import shutil
import logging
import csv
import tempfile
from typing import List, Dict
from collections import defaultdict
from tqdm import tqdm

from shared.hash_utils import compute_file_hash
from shared.csv_sanitizer import sanitize_field, sanitize_record, sanitize_records, is_dangerous

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as _wt

    _WIN32_FILE_WRITE_ATTRIBUTES = 0x0100
    _WIN32_OPEN_EXISTING = 3
    _WIN32_FILE_ATTRIBUTE_NORMAL = 0x80
    _WIN32_FILETIME_EPOCH_DIFF = 116_444_736_000_000_000
    _WIN32_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    _kernel32 = ctypes.windll.kernel32
    _kernel32.CreateFileW.argtypes = [
        _wt.LPCWSTR, _wt.DWORD, _wt.DWORD, ctypes.c_void_p,
        _wt.DWORD, _wt.DWORD, _wt.HANDLE,
    ]
    _kernel32.CreateFileW.restype = _wt.HANDLE
    _kernel32.SetFileTime.argtypes = [
        _wt.HANDLE,
        ctypes.POINTER(_wt.FILETIME),
        ctypes.POINTER(_wt.FILETIME),
        ctypes.POINTER(_wt.FILETIME),
    ]
    _kernel32.SetFileTime.restype = _wt.BOOL
    _kernel32.CloseHandle.argtypes = [_wt.HANDLE]
    _kernel32.CloseHandle.restype = _wt.BOOL


def list_files(folder: str, pattern: str | None = None, recursive: bool = True) -> list[str]:
    """
    Vrátí seznam souborů ve složce `folder`.
    Pokud je zadán `pattern` (regex), vrátí jen soubory, jejichž jméno odpovídá výrazu.
    Rekurzivní prohledávání lze ovládat parametrem `recursive`.
    """
    logging.debug("Listing files in folder: %s (pattern=%s, recursive=%s)", folder, pattern, recursive)
    matched: list[str] = []
    if recursive:
        iterator = os.walk(folder)
    else:
        try:
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            iterator = [(folder, [], files)]
        except FileNotFoundError:
            logging.error("Folder not found: %s", folder)
            return []
    for root, _, files in iterator:
        for name in files:
            # pokud není zadán pattern, nebo odpovídá regexu, přidej
            if pattern is None or pattern == "" or re.search(pattern, name):
                matched.append(os.path.join(root, name))
    return matched

def _set_creation_time_windows(path: str, ctime_unix: float) -> None:
    """Set file creation time on Windows using Win32 SetFileTime via ctypes.

    Python stdlib (shutil.copy2 / os.utime) cannot set creation time on Windows.
    This function calls CreateFileW -> SetFileTime -> CloseHandle directly.

    :param path: Target file path.
    :param ctime_unix: Creation time as Unix timestamp (seconds since Unix epoch).
    :raises OSError: If the handle cannot be opened or SetFileTime fails.
    :raises NotImplementedError: If called on a non-Windows platform.
    """
    if sys.platform != "win32":
        raise NotImplementedError("_set_creation_time_windows is only supported on Windows")

    t100ns = int(ctime_unix * 10_000_000) + _WIN32_FILETIME_EPOCH_DIFF
    ft = _wt.FILETIME(t100ns & 0xFFFFFFFF, t100ns >> 32)

    handle = _kernel32.CreateFileW(
        os.path.abspath(path),
        _WIN32_FILE_WRITE_ATTRIBUTES,
        0,
        None,
        _WIN32_OPEN_EXISTING,
        _WIN32_FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == _WIN32_INVALID_HANDLE_VALUE:
        raise OSError(f"SetFileTime: cannot open {path!r} (WinError {_kernel32.GetLastError()})")
    try:
        if not _kernel32.SetFileTime(handle, ctypes.byref(ft), None, None):
            raise OSError(f"SetFileTime failed on {path!r} (WinError {_kernel32.GetLastError()})")
    finally:
        _kernel32.CloseHandle(handle)


def copy_file(src: str, dest: str, overwrite: bool = True) -> None:
    """Copy *src* to *dest*, preserving all metadata including creation time on Windows.

    Uses an atomic write pattern (temp file -> fsync -> os.replace) so that *dest*
    never contains partial data if the operation is interrupted by a full disk,
    an exception, or a process kill.

    On Windows, creation time is explicitly restored via Win32 SetFileTime after
    the rename, because shutil.copy2 / os.utime cannot set creation time on Windows.

    :param src: Path to the source file.
    :param dest: Path to the destination file.
    :param overwrite: If False, skip when *dest* already exists.
    :raises OSError: If the copy fails; any incomplete temp file is removed before raising.
    """
    logging.debug("Copying file from %s to %s (overwrite=%s)", src, dest, overwrite)
    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping: %s", dest)
        return

    dest_folder = os.path.dirname(dest) or "."
    ensure_directory(dest_folder)

    src_ctime: float | None = os.stat(src).st_ctime if sys.platform == "win32" else None

    temp_path = None
    try:
        temp_fd, temp_path = tempfile.mkstemp(dir=dest_folder, prefix=".tmp_copy_")
        os.close(temp_fd)
        shutil.copy2(src, temp_path)
        with open(temp_path, "r+b") as f:
            os.fsync(f.fileno())
        os.replace(temp_path, dest)
        temp_path = None
        if src_ctime is not None:
            try:
                _set_creation_time_windows(dest, src_ctime)
            except OSError as ctime_err:
                logging.warning("Could not preserve creation time for %s: %s", dest, ctime_err)
        logging.debug("Copied file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy file from %s to %s: %s", src, dest, e)
        raise
    finally:
        if temp_path:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass
            except OSError:
                logging.warning("Failed to clean up temp file: %s", temp_path)

def ensure_directory(path: str) -> None:
    """
    Ensure that a directory exists at the given path.
    Creates the directory if it does not exist.
    """
    logging.debug("Ensuring directory exists: %s", path)
    try:
        os.makedirs(path, exist_ok=True)
        logging.debug("Directory ready: %s", path)
    except Exception as e:
        logging.error("Failed to ensure directory %s: %s", path, e)
        raise

def load_csv(path: str, encoding: str = 'utf-8-sig', delimiter: str = ',', quotechar: str = '"') -> List[Dict[str, str]]:
    """
    Load a CSV file and return a list of records as dictionaries.

    Args:
        path: Path to the CSV file
        encoding: File encoding (default: 'utf-8-sig' - UTF-8 with BOM)
        delimiter: CSV delimiter character (default: ',')
        quotechar: CSV quote character (default: '"')

    Returns:
        List of dictionaries representing CSV records

    Shows a progress bar during loading.
    """
    logging.debug("Loading CSV file from %s (encoding=%s, delimiter=%s, quotechar=%s)", path, encoding, delimiter, quotechar)
    records: List[Dict[str, str]] = []
    try:
        # Count total data rows (excluding header)
        with open(path, 'r', encoding=encoding, newline='') as csvfile:
            total_rows = sum(1 for _ in csvfile) - 1
        # Read and load records with progress bar
        with open(path, 'r', encoding=encoding, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter, quotechar=quotechar)
            for row in tqdm(reader, total=total_rows, desc="Loading CSV", unit="rows"):
                records.append(row)
        logging.info("Loaded %d records from CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to load CSV file %s: %s", path, e)
        raise
    return records

def save_csv(records: List[Dict[str, str]], path: str) -> None:
    """
    Uloží seznam záznamů jako CSV (UTF-8 s BOM).
    Zachová hlavičku a pořadí sloupců.
    Všechny hodnoty jsou uloženy v uvozovkách, nejen ty obsahující delimiter.
    """
    logging.debug("Saving CSV file to %s", path)
    try:
        if not records:
            logging.warning("No records to save to CSV file %s", path)
            return

        # Get fieldnames from the first record
        fieldnames = list(records[0].keys())

        # Sanitize data to prevent CSV injection
        sanitized_data = sanitize_records(records)

        with open(path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_ALL  # Force quoting for all fields
            )
            writer.writeheader()
            for row in tqdm(sanitized_data, desc="Saving CSV", unit="rows"):
                writer.writerow(row)

        logging.info("Saved %d records to CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to save CSV file %s: %s", path, e)
        raise