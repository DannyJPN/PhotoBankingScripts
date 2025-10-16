from shared.file_operations import list_files, move_file
import logging
import os
from shared.file_operations import get_hash_map_from_folder, compute_file_hash
from shared.name_utils import extract_numeric_suffix, generate_indexed_filename, find_next_available_number
from tqdm import tqdm
from shared.file_operations import list_files
from pullnewmediatounsortedlib.constants import DEFAULT_NUMBER_WIDTH, MAX_NUMBER


def replace_in_filenames(folder: str, search: str, replace: str, recursive: bool = True) -> None:
    """
    Přejmenuje soubory v `folder`, kde jejich název obsahuje `search`,
    nahraď tuto část řetězcem `replace`.
    """
    logging.info("Replacing '%s' with '%s' in filenames under: %s", search, replace, folder)
    paths = list_files(folder, pattern=search, recursive=recursive)
    if not paths:
        logging.info("No occurrences of '%s' found in %s, skipping.", search, folder)
        return
    for path in tqdm(paths, desc="Renaming files", unit="files"):
        name = os.path.basename(path)
        if search in name:
            new_name = name.replace(search, replace)
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                if os.path.exists(new_path):
                    os.remove(path)
                    logging.debug("Removed duplicate file: %s", path)
                else:
                    move_file(path, new_path, overwrite=True)
                    logging.debug("Renamed %s to %s", path, new_path)
            except Exception as e:
                logging.error("Error replacing name for %s: %s", path, e)
                raise



def normalize_indexed_filenames(
    source_folder: str,
    reference_folder: str,
    prefix: str = "PICT",
    width: int = DEFAULT_NUMBER_WIDTH,
    max_number: int = MAX_NUMBER
) -> None:
    """
    Upraví názvy souborů s daným `prefix` a číselným suffixem v `source_folder`:
      - Shodné obsahy podle hashů přejmenuje na stávající jméno z `reference_folder`.
      - Jiné přejmenuje na nejnižší dostupné číslo se zadanou `width`.
    Renaming proběhne přímo na místě (změní se jen název, ne cesta ke složce).
    """
    logging.info(
        "Normalizing indexed filenames in %s against %s (prefix=%s, width=%d)",
        source_folder, reference_folder, prefix, width
    )

    # 1) Sestav reference mapu: path -> hash
    try:
        ref_hash_map = get_hash_map_from_folder(reference_folder, pattern=prefix)
    except Exception as e:
        logging.error("Failed to build reference hash map: %s", e)
        return

    # 2) Otoč ji v hash->canonical_name (basenames)
    hash_to_canon: dict[str, str] = {}
    for path, h in ref_hash_map.items():
        if h not in hash_to_canon:
            hash_to_canon[h] = os.path.basename(path)
    logging.debug("Reference provides %d canonical names", len(hash_to_canon))

    # 3) Seznam všech souborů v source s daným prefixem
    paths = list_files(source_folder, pattern=prefix, recursive=True)
    if not paths:
        logging.info("No files matching '%s*' in %s, skipping.", prefix, source_folder)
        return

    # 4) Sestav množinu použitých čísel z referencí i aktuálních názvů
    used_nums = set(
        num
        for canon in hash_to_canon.values()
        if (num := extract_numeric_suffix(canon, prefix=prefix, width=width)) is not None
    )
    for path in paths:
        name = os.path.basename(path)
        if (num := extract_numeric_suffix(name, prefix=prefix, width=width)) is not None:
            used_nums.add(num)
    logging.debug("Combined used numbers: %s", sorted(used_nums))

    # 5) Projdi každý soubor a zjisti jeho hash
    for src_path in tqdm(paths, desc="Normalizing indexed files", unit="file"):
        name = os.path.basename(src_path)
        try:
            h = compute_file_hash(src_path)
            logging.debug("Computed hash %s for %s", h, name)
        except Exception as e:
            logging.error("Skipping %s due to hash error: %s", src_path, e)
            continue

        # 6) Vyber správné jméno
        if h in hash_to_canon:
            new_name = hash_to_canon[h]
            logging.debug("Hash match: using existing name %s", new_name)
        else:
            ext = os.path.splitext(name)[1]
            num = find_next_available_number(used_nums, max_number)
            used_nums.add(num)
            new_name = generate_indexed_filename(num, ext, prefix=prefix, width=width)
            logging.debug("No match: assigned new index %d -> %s", num, new_name)

        # 7) Přejmenuj soubor in‑place, pokud je třeba
        if new_name != name:
            dst = os.path.join(os.path.dirname(src_path), new_name)
            try:
                os.rename(src_path, dst)
                logging.debug("Renamed %s -> %s", name, new_name)
            except Exception as e:
                logging.error("Failed to rename %s to %s: %s", src_path, new_name, e)

    logging.info("Completed normalization for %s", source_folder)