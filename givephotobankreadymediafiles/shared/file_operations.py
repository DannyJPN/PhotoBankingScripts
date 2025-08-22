import csv
import logging
import os
import re
import shutil
from collections import defaultdict
from datetime import datetime

from shared.hash_utils import compute_file_hash
from tqdm import tqdm


def list_files(folder: str, pattern: str | None = None, recursive: bool = True) -> list[str]:
    """List files in the specified folder.

    :param folder: Path to the folder to search
    :type folder: str
    :param pattern: Optional regex pattern to filter files
    :type pattern: Optional[str]
    :param recursive: Whether to search recursively
    :type recursive: bool
    :returns: List of file paths
    :rtype: List[str]
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
            if pattern is None or pattern == "" or re.search(pattern, name):
                matched.append(os.path.join(root, name))
    return matched


def copy_folder(src: str, dest: str, overwrite: bool = True, pattern: str = "") -> None:
    """Kopíruje soubory ze složky src do dest (rekurzivně).

    :param src: Zdrojová složka
    :type src: str
    :param dest: Cílová složka
    :type dest: str
    :param overwrite: Zda přepsat existující soubory
    :type overwrite: bool
    :param pattern: Regex pattern pro filtrování souborů
    :type pattern: str
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

        for file_path in tqdm(files, desc="Copying folder", unit="file"):
            rel_path = os.path.relpath(file_path, src)
            dest_path = os.path.join(dest, rel_path)
            copy_file(file_path, dest_path, overwrite=overwrite)

        logging.info("Copied folder from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy folder from %s to %s: %s", src, dest, e)
        raise


def delete_folder(path: str) -> None:
    """Smaže celou složku a její obsah.

    :param path: Cesta ke složce
    :type path: str
    """
    logging.debug("Deleting folder: %s", path)
    try:
        shutil.rmtree(path)
        logging.info("Deleted folder: %s", path)
    except Exception as e:
        logging.error("Failed to delete folder %s: %s", path, e)
        raise


def move_folder(src: str, dest: str, overwrite: bool = False, pattern: str = "") -> None:
    """Přesune soubory ze složky src do dest (rekurzivně).

    :param src: Zdrojová složka
    :type src: str
    :param dest: Cílová složka
    :type dest: str
    :param overwrite: Zda přepsat existující soubory
    :type overwrite: bool
    :param pattern: Regex pattern pro filtrování souborů
    :type pattern: str
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

        for file_path in tqdm(files, desc="Moving folder", unit="file"):
            rel_path = os.path.relpath(file_path, src)
            dest_path = os.path.join(dest, rel_path)
            move_file(file_path, dest_path, overwrite=overwrite)

        delete_folder(src)
        logging.info("Moved folder from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to move folder from %s to %s: %s", src, dest, e)
        raise


def copy_file(src: str, dest: str, overwrite: bool = True) -> None:
    """Zkopíruje soubor src do dest.

    :param src: Zdrojový soubor
    :type src: str
    :param dest: Cílový soubor
    :type dest: str
    :param overwrite: Zda přepsat existující soubor
    :type overwrite: bool
    """
    logging.debug("Copying file from %s to %s (overwrite=%s)", src, dest, overwrite)
    if not overwrite and os.path.exists(dest):
        logging.debug("File exists and overwrite disabled, skipping: %s", dest)
        return

    # Vytvoří cílovou složku, pokud neexistuje
    dest_folder = os.path.dirname(dest)
    if dest_folder:
        ensure_directory(dest_folder)

    try:
        shutil.copy2(src, dest)
        logging.debug("Copied file from %s to %s", src, dest)
    except Exception as e:
        logging.error("Failed to copy file from %s to %s: %s", src, dest, e)
        raise


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


def load_csv(path: str) -> list[dict[str, str]]:
    """
    Load a CSV file and return a list of records as dictionaries.
    Assumes comma delimiter and UTF-8 with BOM (utf-8-sig).
    Shows a progress bar during loading.
    """
    logging.debug("Loading CSV file from %s", path)
    records: list[dict[str, str]] = []
    try:
        # Count total data rows (excluding header)
        with open(path, encoding="utf-8-sig", newline="") as csvfile:
            total_rows = sum(1 for _ in csvfile) - 1
        # Read and load records with progress bar
        with open(path, encoding="utf-8-sig", newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=",", quotechar='"')
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


def get_hash_map_from_folder(folder: str, pattern: str = "PICT", recursive: bool = True) -> dict[str, str]:
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
    result: dict[str, str] = {}
    # 2) Pro každý soubor spočti hash a ulož ho pod klíč cesty
    for path in tqdm(paths, desc="Hashing files", unit="files"):
        try:
            file_hash = compute_file_hash(path)
            result[path] = file_hash
        except Exception as e:
            logging.error("Failed to hash %s: %s", path, e)
    logging.info("Built hash map with %d entries from %s", len(result), folder)
    return result


def save_csv(records: list[dict[str, str]], path: str) -> None:
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

        # Ensure the directory exists
        ensure_directory(os.path.dirname(path))

        with open(path, "w", encoding="utf-8-sig", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_ALL,  # Force quoting for all fields
            )
            writer.writeheader()
            for row in tqdm(records, desc="Saving CSV", unit="rows"):
                writer.writerow(row)

        logging.info("Saved %d records to CSV %s", len(records), path)
    except Exception as e:
        logging.error("Failed to save CSV file %s: %s", path, e)
        raise


# Tato funkce je duplicitní a byla nahrazena funkcí load_csv výše


def save_csv_with_backup(data: list[dict[str, str]], path: str) -> None:
    """
    Creates a backup of the original CSV and saves the new data.

    Args:
        data: List of dictionaries representing CSV rows
        path: Path to the CSV file
    """
    logging.info(f"Saving CSV with backup: {path}")

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{os.path.splitext(path)[0]}_{timestamp}.csv"

    # Create backup if original file exists
    if os.path.exists(path):
        copy_file(path, backup_path)
        logging.info(f"Created backup at: {backup_path}")

    # Ensure the directory exists
    ensure_directory(os.path.dirname(path))

    # Write the updated CSV
    try:
        # Get fieldnames from the first row
        fieldnames = list(data[0].keys()) if data else []

        with open(path, "w", encoding="utf-8-sig", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=",",
                quotechar='"',
                quoting=csv.QUOTE_ALL,  # Force quoting for all fields
            )
            writer.writeheader()
            for row in tqdm(data, desc="Saving CSV with backup", unit="rows"):
                writer.writerow(row)

        logging.info(f"Successfully saved {len(data)} records to {path}")
    except Exception as e:
        logging.error(f"Failed to save CSV file {path}: {e}")
        raise
