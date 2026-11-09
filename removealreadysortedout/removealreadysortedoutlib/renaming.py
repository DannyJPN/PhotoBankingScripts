import logging
import os

from tqdm import tqdm

from shared.file_operations import list_files, move_file


def replace_in_filenames(folder: str, search: str, replace: str, recursive: bool = True) -> None:
    """
    Rename files in `folder` whose name contains `search` by substituting `replace`.
    An existing target is never replaced, and a source is never deleted on a name collision.

    :param folder: Root folder to scan.
    :param search: Literal substring to replace.
    :param replace: Replacement substring.
    :param recursive: Whether to scan subdirectories.
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
                if os.path.lexists(new_path):
                    logging.warning("Name collision, keeping both files: %s and %s", path, new_path)
                else:
                    move_file(path, new_path, overwrite=False)
                    if os.path.lexists(path):
                        logging.warning("Rename skipped, source retained: %s", path)
                    else:
                        logging.debug("Renamed %s to %s", path, new_path)
            except FileExistsError:
                logging.warning("Name collision, keeping both files: %s and %s", path, new_path)
            except Exception as e:
                logging.error("Error replacing name for %s: %s", path, e)
                raise
