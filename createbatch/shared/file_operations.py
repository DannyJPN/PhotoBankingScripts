
import logging
import csv
import sys
import tempfile
from typing import List, Dict
from tqdm import tqdm
import os
import shutil
from shared.csv_sanitizer import sanitize_records

if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes as _wt

    _WIN32_FILE_WRITE_ATTRIBUTES = 0x0100
    _WIN32_OPEN_EXISTING = 3
    _WIN32_FILE_ATTRIBUTE_NORMAL = 0x80
    _WIN32_FILETIME_EPOCH_DIFF = 116_444_736_000_000_000


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

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateFileW.argtypes = [
        _wt.LPCWSTR, _wt.DWORD, _wt.DWORD, ctypes.c_void_p,
        _wt.DWORD, _wt.DWORD, _wt.HANDLE,
    ]
    kernel32.CreateFileW.restype = _wt.HANDLE
    kernel32.SetFileTime.argtypes = [
        _wt.HANDLE,
        ctypes.POINTER(_wt.FILETIME),
        ctypes.POINTER(_wt.FILETIME),
        ctypes.POINTER(_wt.FILETIME),
    ]
    kernel32.SetFileTime.restype = _wt.BOOL
    kernel32.CloseHandle.argtypes = [_wt.HANDLE]
    kernel32.CloseHandle.restype = _wt.BOOL

    # Convert Unix timestamp to Windows FILETIME (100-ns intervals since 1601-01-01)
    t100ns = int(ctime_unix * 10_000_000) + _WIN32_FILETIME_EPOCH_DIFF
    ft = _wt.FILETIME(t100ns & 0xFFFFFFFF, t100ns >> 32)

    handle = kernel32.CreateFileW(
        os.path.abspath(path),
        _WIN32_FILE_WRITE_ATTRIBUTES,
        0,
        None,
        _WIN32_OPEN_EXISTING,
        _WIN32_FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == _wt.HANDLE(-1).value:
        raise OSError(f"SetFileTime: cannot open {path!r} (WinError {kernel32.GetLastError()})")
    try:
        # Pass None for atime and mtime — Win32 treats NULL as "do not change"
        if not kernel32.SetFileTime(handle, ctypes.byref(ft), None, None):
            raise OSError(f"SetFileTime failed on {path!r} (WinError {kernel32.GetLastError()})")
    finally:
        kernel32.CloseHandle(handle)


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

    # Read creation time before the copy — on Windows st_ctime is creation time
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
            _set_creation_time_windows(dest, src_ctime)
        logging.debug("Copied file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy file from %s to %s: %s", src, dest, e)
        raise
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
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


def load_csv(path: str) -> List[Dict[str, str]]:
    """
    Load a CSV file and return a list of records as dictionaries.
    Assumes comma delimiter and UTF-8 with BOM (utf-8-sig).
    Shows a progress bar during loading.
    """
    logging.debug("Loading CSV file from %s", path)
    records: List[Dict[str, str]] = []
    try:
        # Count total data rows (excluding header)
        with open(path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            total_rows = sum(1 for _ in csvfile) - 1
        # Read and load records with progress bar
        with open(path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
            for row in tqdm(reader, total=total_rows, desc="Loading CSV", unit="rows"):
                records.append(row)
        logging.info("Loaded %d records from CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to load CSV file %s: %s", path, e)
        raise
    return records


def save_csv(records: List[Dict[str, str]], path: str, sanitize: bool = True) -> None:
    """
    Save a list of records as CSV (UTF-8 with BOM).
    Preserves header and column order.
    All values are quoted, not just those containing delimiters.

    Args:
        records: List of dictionaries to save
        path: Output file path
        sanitize: Whether to sanitize data to prevent CSV injection (default: True)
    """
    logging.debug("Saving CSV file to %s (sanitize=%s)", path, sanitize)
    try:
        if not records:
            logging.warning("No records to save to CSV file %s", path)
            return

        # Sanitize records to prevent CSV injection attacks
        if sanitize:
            records = sanitize_records(records)
            logging.debug("Applied CSV injection protection to %d records", len(records))

        # Get fieldnames from the first record
        fieldnames = list(records[0].keys())

        with open(path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=',',
                quotechar='"',
                quoting=csv.QUOTE_ALL  # Force quoting for all fields
            )
            writer.writeheader()
            for row in tqdm(records, desc="Saving CSV", unit="rows"):
                writer.writerow(row)

        logging.info("Saved %d sanitized records to CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to save CSV file %s: %s", path, e)
        raise