from shared.file_operations import list_files, move_file
import logging
import os
from datetime import datetime
from shared.file_operations import get_hash_map_from_folder, compute_file_hash
from shared.name_utils import (
    extract_camera_number,
    extract_dated_parts,
    generate_dated_filename,
    name_key,
    resolve_name_conflict,
)
from shared.exif_handler import get_best_creation_date
from shared.exif_downloader import ensure_exiftool
from tqdm import tqdm
from removealreadysortedoutlib.constants import DATE_FORMAT


def replace_in_filenames(folder: str, search: str, replace: str, recursive: bool = True) -> None:
    """
    Rename files in `folder` whose name contains `search` by substituting `replace`.
    If the target name already exists the source file is removed as a duplicate.
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
) -> None:
    """
    Rename files with the given `prefix` in `source_folder` to the dated format
    ``<prefix><YYYYMMDD>_<cam_seq>.<ext>`` (e.g. ``NIK_20260612_8888.JPG``).

    Rules:
    - If the file's hash is found in `reference_folder`, use the reference's canonical name.
    - Otherwise derive the shoot date from EXIF (oldest available tag, same algorithm used
      for chronological sorting) and keep the original 4-digit camera sequence number.
    - Files already in the dated format are idempotent: the generated name equals the
      current name and no rename is performed.
    - Same-day counter collision (camera rollover within one day) is resolved by appending
      _B, _C, … to the stem – this case is practically impossible in normal use.
    """
    logging.info(
        "Normalizing indexed filenames in %s against %s (prefix=%s)",
        source_folder,
        reference_folder,
        prefix,
    )

    # 1) Skip early if nothing to do
    paths = list_files(source_folder, pattern=prefix, recursive=True)
    if not paths:
        logging.info("No files matching '%s*' in %s, skipping.", prefix, source_folder)
        return

    # 2) Build reference hash map and derive canonical names
    try:
        ref_hash_map = get_hash_map_from_folder(reference_folder, pattern=prefix)
    except Exception as e:
        logging.error("Failed to build reference hash map: %s", e)
        return

    hash_to_canon: dict[str, str] = {}
    for path, h in ref_hash_map.items():
        if h not in hash_to_canon:
            hash_to_canon[h] = os.path.basename(path)
    logging.debug("Reference provides %d canonical names", len(hash_to_canon))

    # 3) Seed used_names (case-insensitive name key -> owning path) from source AND reference
    #    folders; the reference wins because final names live there.
    used_names: dict[str, str] = {name_key(os.path.basename(p)): p for p in paths}
    used_names.update({name_key(os.path.basename(p)): p for p in ref_hash_map})
    known_hash: dict[str, str] = dict(ref_hash_map)

    def _hash_of(path: str) -> str | None:
        if path not in known_hash:
            try:
                known_hash[path] = compute_file_hash(path)
            except Exception as e:
                logging.error("Cannot hash %s: %s", path, e)
                return None
        return known_hash[path]

    # 4) Locate ExifTool once
    try:
        exiftool_path = ensure_exiftool()
        logging.debug("ExifTool located at: %s", exiftool_path)
    except FileNotFoundError as e:
        logging.warning("ExifTool not found, will use filesystem dates only: %s", e)
        exiftool_path = None

    def _file_date(path: str) -> datetime:
        date = get_best_creation_date(path, tool_path=exiftool_path)
        if date is None:
            try:
                date = datetime.fromtimestamp(os.path.getmtime(path))
            except Exception:
                date = datetime.fromtimestamp(0)
        return date

    # 5) Sort chronologically and cache dates to avoid double EXIF reads
    logging.info("Reading EXIF dates for %d files...", len(paths))
    path_to_date: dict[str, datetime] = {p: _file_date(p) for p in paths}
    sorted_paths = sorted(paths, key=lambda p: path_to_date[p])

    # 6) Rename each file
    for src_path in tqdm(sorted_paths, desc="Normalizing indexed files", unit="file"):
        name = os.path.basename(src_path)
        try:
            h = compute_file_hash(src_path)
        except Exception as e:
            logging.error("Skipping %s due to hash error: %s", src_path, e)
            continue
        known_hash[src_path] = h

        if h in hash_to_canon:
            new_name = hash_to_canon[h]
            logging.debug("Hash match: using canonical name %s", new_name)
        else:
            ext = os.path.splitext(name)[1]

            # Derive camera sequence number – support both old and new filename formats
            dated = extract_dated_parts(name, prefix=prefix)
            if dated:
                cam_num = dated[1]
            else:
                cam_num = extract_camera_number(name, prefix=prefix)
                if cam_num is None:
                    logging.warning("Cannot extract camera number from '%s', skipping", name)
                    continue

            date_str = path_to_date[src_path].strftime(DATE_FORMAT)
            try:
                base_name = generate_dated_filename(cam_num, date_str, ext, prefix=prefix)
            except ValueError as e:
                logging.error("Cannot build dated name for '%s': %s, skipping", name, e)
                continue
            own_key = name_key(name)
            if used_names.get(own_key) == src_path:
                del used_names[own_key]
            try:
                new_name = resolve_name_conflict(
                    base_name, used_names, same_content=lambda key: _hash_of(used_names[key]) == h
                )
            except ValueError:
                logging.error("No name variant available for %s, skipping", base_name)
                continue
            used_names[name_key(new_name)] = src_path
            logging.debug("No hash match: assigned dated name %s", new_name)

        if name_key(new_name) != name_key(name):
            dst = os.path.join(os.path.dirname(src_path), new_name)
            try:
                move_file(src_path, dst, overwrite=False)
                new_key = name_key(new_name)
                if os.path.exists(src_path):
                    logging.warning("Rename skipped, destination already exists: %s -> %s", src_path, dst)
                    if used_names.get(new_key) == src_path:
                        del used_names[new_key]
                        used_names[name_key(name)] = src_path
                else:
                    logging.debug("Renamed %s -> %s", name, new_name)
                    if used_names.get(new_key) == src_path:
                        used_names[new_key] = dst
                        known_hash[dst] = known_hash[src_path]
            except Exception as e:
                logging.error("Failed to rename %s to %s: %s", src_path, new_name, e)

    logging.info("Completed normalization for %s", source_folder)
