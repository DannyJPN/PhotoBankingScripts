import logging
import os

from createbatchlib.constants import PREPARED_STATUS_VALUE, STATUS_FIELD_KEYWORD
from shared.exif_handler import update_exif_metadata
from shared.file_operations import copy_file, ensure_directory


def prepare_media_file(
    record: dict[str, str], output_folder: str, exif_tool_path: str, overwrite: bool = True, bank: str = None
) -> list[str]:
    """
    Copy a media file into output_folder/<photobank> and update its EXIF metadata.
    If 'bank' is specified, only files for that photobank are processed.

    Returns a list of paths where the file was copied.
    """
    src = record.get("Cesta")
    filename = os.path.basename(src)
    processed_paths: list[str] = []

    for key, value in record.items():
        if (
            STATUS_FIELD_KEYWORD in key.lower()
            and isinstance(value, str)
            and PREPARED_STATUS_VALUE.lower() in value.lower()
        ):
            bank_name = key[: key.lower().find(STATUS_FIELD_KEYWORD)].strip()
            if bank and bank_name != bank:
                continue

            bank_folder = os.path.join(output_folder, bank_name)
            ensure_directory(bank_folder)
            dest = os.path.join(bank_folder, filename)

            logging.debug("Copying %s to %s for bank %s (overwrite=%s)", src, dest, bank_name, overwrite)
            copy_file(src, dest, overwrite=overwrite)

            metadata = {
                "title": record.get("Název", ""),
                "keywords": record.get("Klíčová slova", ""),
                "description": record.get("Popis", ""),
                "datetimeoriginal": record.get("Datum pořízení", ""),
            }
            update_exif_metadata(dest, metadata, exif_tool_path)

            processed_paths.append(dest)
            logging.debug("Prepared media file for %s: %s", bank_name, dest)

    return processed_paths
