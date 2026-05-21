
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

def copy_folder(src: str, dest: str, overwrite: bool = True, pattern: str = "") -> None:
    """
    Copies files from src to dest folder (recursively).
    Only copies files matching the regex `pattern`. If pattern is empty, all files are copied.
    Shows a progress bar for each file.
    """
    logging.debug("Copying folder from %s to %s (overwrite=%s, pattern=%s)", src, dest, overwrite, pattern)
    try:
        if os.path.exists(dest) and not overwrite:
            logging.debug("Destination folder exists and overwrite is disabled, skipping copy.")
            return

        files = list_files(src, recursive=True)
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            files = [f for f in files if regex.search(os.path.basename(f))]

        if not files:
            logging.info("No files to copy from %s to %s", src, dest)
            return

        for file_path in tqdm(files, desc="Copying folder", unit="file"):
            rel_path = os.path.relpath(file_path, src)
            dest_path = os.path.join(dest, rel_path)
            copy_file(file_path, dest_path, overwrite=overwrite)

        logging.info("Copied folder from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy folder from %s to %s: %s", src, dest, e)
        raise

def delete_folder(path: str) -> None:
    """
    Smaže celou složku a její obsah.
    """
    logging.debug("Deleting folder: %s", path)
    try:
        shutil.rmtree(path)
        logging.info("Deleted folder: %s", path)
    except Exception as e:
        logging.error("Failed to delete folder %s: %s", path, e)
        raise

def move_folder(src: str, dest: str, overwrite: bool = False, pattern: str = "") -> None:
    """
    Moves files from src to dest folder (recursively).
    Only moves files matching the regex `pattern`. If pattern is empty, all files are moved.
    Shows a progress bar for each file.
    """
    logging.debug("Moving folder from %s to %s (overwrite=%s, pattern=%s)", src, dest, overwrite, pattern)
    try:
        if os.path.exists(dest):
            if overwrite:
                shutil.rmtree(dest)
                logging.debug("Existing destination folder deleted: %s", dest)
            else:
                logging.debug("Destination folder exists and overwrite is disabled, skipping move.")
                return

        files = list_files(src, recursive=True)
        if pattern:
            regex = re.compile(pattern, re.IGNORECASE)
            files = [f for f in files if regex.search(os.path.basename(f))]

        if not files:
            logging.info("No files to move from %s to %s", src, dest)
            return

        for file_path in tqdm(files, desc="Moving folder", unit="file"):
            rel_path = os.path.relpath(file_path, src)
            dest_path = os.path.join(dest, rel_path)
            move_file(file_path, dest_path, overwrite=overwrite)

        delete_folder(src)
        logging.info("Moved folder from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to move folder from %s to %s: %s", src, dest, e)
        raise


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

def move_file(src: str, dest: str, overwrite: bool = False) -> None:
    """
    Přesune soubor src do dest. Přepíše, pokud overwrite=True.
    Používá shutil.move a ensure_directory pro vytvoření chybějící cesty.
    """
    logging.debug("Moving file from %s to %s (overwrite=%s)", src, dest, overwrite)

    # Vytvoří cílovou složku, pokud neexistuje
    dest_folder = os.path.dirname(dest)
    if dest_folder:
        ensure_directory(dest_folder)

    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping move: %s", dest)
        return

    try:
        shutil.move(src, dest)
        logging.debug("Moved file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to move file from %s to %s: %s", src, dest, e)
        raise


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

def unify_duplicate_files(folder: str, recursive: bool = True) -> None:
    """
    V dané složce (a volitelně jejích podsložkách) sjednotí
    soubory se stejným obsahem tak, že všechny budou mít
    stejný basename podle toho, jehož basename je nejkratší.
    """
    logging.info("Unifying duplicates in %s (recursive=%s)", folder, recursive)

    # 1) Mapa path->hash pro všechny soubory
    path_hash_map = get_hash_map_from_folder(folder, pattern="", recursive=recursive)
    if not path_hash_map:
        logging.info("No files found in %s, skipping unification.", folder)
        return

    # 2) Seskup cesty podle hashů
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for path, h in path_hash_map.items():
        hash_groups[h].append(path)

    # Check if there are any duplicate groups
    duplicate_groups = [(h, group) for h, group in hash_groups.items() if len(group) >= 2]
    if not duplicate_groups:
        logging.info("No duplicate files found in %s", folder)
        return

    renamed_count = 0
    # 3) Pro každou skupinu ≥2 souborů zvol canonical podle délky názvu
    for h, group in hash_groups.items():
        if len(group) < 2:
            continue

        # Najdi cestu s nejkratším basename, potom z ní vezmi basename
        canonical_path = min(group, key=lambda p: len(os.path.basename(p)))
        canonical_basename = os.path.basename(canonical_path)
        logging.debug("Hash %s has %d duplicates, canonical = %s", h, len(group), canonical_basename)

        for path in group:
            current_name = os.path.basename(path)
            if current_name == canonical_basename:
                continue

            dst = os.path.join(os.path.dirname(path), canonical_basename)
            try:
                os.replace(path, dst)
                renamed_count += 1
                logging.info("Renamed %s -> %s", path, dst)
            except Exception as e:
                logging.error("Failed to rename %s to %s: %s", path, dst, e)

    logging.info("Unification complete: renamed %d duplicate files in %s", renamed_count, folder)

def get_hash_map_from_folder(folder: str, pattern: str = "PICT",recursive: bool = True) -> Dict[str, str]:
    """
    Projde složku `folder` rekurzivně (podle patternu) a vrátí slovník
    {full_path: hash} pro každý nalezený soubor.
    """
    logging.info("Building hash map from folder: %s (pattern=%s)", folder, pattern)
    # 1) Seber všechny soubory podle patternu
    paths = list_files(folder, pattern, recursive=recursive)
    if not paths:
        logging.info("No files matching pattern '%s' in %s, skipping.", pattern, folder)
        return {}
    result: Dict[str, str] = {}
    # 2) Pro každý soubor spočti hash a ulož ho pod klíč cesty
    for path in tqdm(paths, desc="Hashing files", unit="files"):
        try:
            file_hash = compute_file_hash(path)
            result[path] = file_hash
        except Exception as e:
            logging.error("Failed to hash %s: %s", path, e)
    logging.info("Built hash map with %d entries from %s", len(result), folder)
    return result


def save_csv_with_backup(data: List[Dict[str, str]], path: str) -> None:
    """
    Creates a backup of the original CSV and saves the new data.

    Args:
        data: List of dictionaries representing CSV rows
        path: Path to the CSV file
    """
    from datetime import datetime

    logging.info("Saving CSV with backup: %s", path)

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{os.path.splitext(path)[0]}_{timestamp}.csv"

    # Create backup
    copy_file(path, backup_path)
    logging.info("Created backup at: %s", backup_path)

    # Ensure the directory exists
    ensure_directory(os.path.dirname(path))

    # Write the updated CSV
    try:
        # Get fieldnames from the first row
        fieldnames = list(data[0].keys()) if data else []

        # Sanitize data to prevent CSV injection
        sanitized_data = sanitize_records(data)

        with open(path, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
            writer.writeheader()
            writer.writerows(sanitized_data)

        logging.info("Successfully saved %d records to %s", len(data), path)
    except Exception as e:
        logging.error("Failed to save CSV file %s: %s", path, e)
        raise
