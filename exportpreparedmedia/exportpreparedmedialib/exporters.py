import os
import re
import csv
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from shared.file_operations import save_csv, load_csv
from shared.csv_sanitizer import sanitize_field
from exportpreparedmedialib.column_maps import get_column_map
from exportpreparedmedialib.banks_logic import (
    should_skip_editorial,
    is_editorial_item,
    extract_media_properties,
    load_category_map,
    load_pond_prices,
)

from exportpreparedmedialib.constants import (
    PHOTOBANK_SUPPORTED_FORMATS,
    PHOTOBANK_BATCH_SIZE_LIMITS,
    PHOTOBANK_EXPORT_FORMATS,
    FORMAT_SUBDIRS,
    ALTERNATIVE_EDIT_TAGS,
    ORIGINAL_EDIT_TYPE,
    EDIT_TYPE_ORDER,
    EDITORIAL_OUTPUT_TAG,
    DEFAULT_ADOBE_CATEGORY_PATH,
    DEFAULT_DREAMSTIME_CATEGORY_PATH,
    DEFAULT_POND_PRICES_PATH,
    DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH,
)


def get_edit_type(item: Dict[str, str]) -> str:
    """
    Return the edit type of an item from the suffix of its filename.

    Uses the same rule as the createbatch edit subfolders: the last edit tag wins,
    so ``X_sharpen_bw.jpg`` is ``bw``.

    :param item: Item from PhotoMedia.csv (``Cesta`` or ``Soubor`` is used).
    :return: Edit type without the leading underscore, or ``original``.
    """
    stem = Path(item.get('Cesta') or item.get('Soubor', '')).stem
    for tag in ALTERNATIVE_EDIT_TAGS:
        if stem.endswith(tag):
            return tag[1:]
    return ORIGINAL_EDIT_TYPE


def get_group_output_file(output_file: str, edit_type: str, editorial: bool, batch_index: Optional[int] = None) -> str:
    """
    Build the output path of one edit-type group of a bank export.

    :param output_file: Base bank output path, e.g. ``.../CSV_Pond5.csv``.
    :param edit_type: Edit type of the group, e.g. ``bw`` or ``original``.
    :param editorial: Whether the group holds editorial items.
    :param batch_index: Batch number when the group is split into several files.
    :return: Path such as ``.../CSV_Pond5_editorial_bw_2.csv``.
    """
    path = Path(output_file)
    parts = [path.stem]
    if editorial:
        parts.append(EDITORIAL_OUTPUT_TAG)
    parts.append(edit_type)
    if batch_index is not None:
        parts.append(str(batch_index))
    return str(path.parent / ("_".join(parts) + path.suffix))


def find_stale_outputs(output_file: str, written_files: List[str]) -> List[str]:
    """
    Find existing edit-type export files of a bank that the current run did not write.

    The deprecated single file ``<prefix>_<Bank>.csv`` and old ``<prefix>_<Bank>_<N>.csv`` batches
    are ignored.

    :param output_file: Base bank output path, e.g. ``.../CSV_Pond5.csv``.
    :param written_files: Paths written by the current run.
    :return: Sorted list of stale file paths.
    """
    path = Path(output_file)
    if not path.parent.is_dir():
        return []
    edit_types = "|".join(re.escape(t) for t in EDIT_TYPE_ORDER)
    pattern = re.compile(
        rf"^{re.escape(path.stem)}(?:_{re.escape(EDITORIAL_OUTPUT_TAG)})?_(?:{edit_types})(?:_\d+)?"
        rf"{re.escape(path.suffix)}$",
        re.IGNORECASE,
    )
    written = {os.path.normcase(os.path.abspath(f)) for f in written_files}
    stale = [
        str(path.parent / name)
        for name in os.listdir(path.parent)
        if pattern.match(name) and os.path.normcase(os.path.abspath(path.parent / name)) not in written
    ]
    return sorted(stale)


def group_records_by_edit_type(
    entries: List[Tuple[Dict[str, str], Dict[str, str]]]
) -> List[Tuple[str, List[Dict[str, str]]]]:
    """
    Group export records by edit type.

    :param entries: Pairs ``(expanded item, export record)`` in export order.
    :return: Non-empty groups ``(edit type, records)`` in ``EDIT_TYPE_ORDER``, records in input order.
    """
    groups: Dict[str, List[Dict[str, str]]] = {}
    for item, record in entries:
        groups.setdefault(get_edit_type(item), []).append(record)
    order = {t: i for i, t in enumerate(EDIT_TYPE_ORDER)}
    return [(edit_type, groups[edit_type]) for edit_type in sorted(groups, key=lambda t: order.get(t, len(order)))]


def split_into_batches(items: List[Dict[str, str]], batch_size_limit: int) -> List[List[Dict[str, str]]]:
    """
    Cut items into batches of at most ``batch_size_limit`` (one batch if there is no limit).

    :param items: Items in export order.
    :param batch_size_limit: Maximum items per batch; 0 or less means no limit.
    :return: List of batches; empty if there are no items.
    """
    if not items:
        return []
    if batch_size_limit <= 0:
        return [items]
    return [items[i:i + batch_size_limit] for i in range(0, len(items), batch_size_limit)]



def expand_item_with_alternative_formats(item: Dict[str, str], bank: str, include_alternatives: bool = False) -> List[Dict[str, str]]:
    """
    Expand single item with alternative format versions for given photobank.

    Args:
        item: Original item from CSV
        bank: Photobank name to check supported formats
        include_alternatives: Whether to search for alternative formats

    Returns:
        List of items (original + alternative formats that exist and are supported)
    """
    items = []

    source_file = item.get('Cesta', '')
    if not source_file or not os.path.exists(source_file):
        return items

    source_path = Path(source_file)
    source_ext = source_path.suffix.lower()

    # Get supported formats for this bank
    # Check export-specific formats first, fall back to general formats
    supported_formats = PHOTOBANK_EXPORT_FORMATS.get(bank, PHOTOBANK_SUPPORTED_FORMATS.get(bank, {'.jpg'}))
    logging.debug(f"Using export formats for {bank}: {supported_formats}")

    # Add source file only if its format is supported by this bank
    if source_ext in supported_formats:
        items.append(item)
    else:
        logging.debug(f"Source format {source_ext} not supported by {bank}, skipping: {source_file}")
        return items

    # If not including alternatives, return just the source
    if not include_alternatives:
        return items

    # Find format directory in path (case-insensitive)
    valid_format_dirs = {subdir.upper() for subdir in FORMAT_SUBDIRS.values()}
    source_parts = source_path.parts
    format_dir_index = None
    original_format_dir = None

    for i, part in enumerate(source_parts):
        if part.upper() in valid_format_dirs:
            format_dir_index = i
            original_format_dir = part
            break

    if format_dir_index is None:
        logging.debug(f"Could not identify format directory in path: {source_file}")
        return items

    # Determine case style from original format directory (lowercase or uppercase)
    use_lowercase = original_format_dir.islower()

    # Search for alternative formats
    for ext in supported_formats:
        if ext == source_ext:
            continue  # Skip source format

        # Build alternative file path with same case as original
        target_format_dir = FORMAT_SUBDIRS.get(ext, ext.lstrip('.').upper())
        if use_lowercase:
            target_format_dir = target_format_dir.lower()

        alternative_parts = list(source_parts)
        alternative_parts[format_dir_index] = target_format_dir
        alternative_parts[-1] = source_path.stem + ext

        alternative_file = Path(*alternative_parts)

        if alternative_file.exists():
            # Create copy of original item with updated path
            alt_item = item.copy()
            alt_item['Cesta'] = str(alternative_file)
            alt_item['Soubor'] = alternative_file.name
            items.append(alt_item)
            logging.debug(f"Added alternative format for {bank}: {alternative_file}")

    return items


def load_photobank_headers(headers_file: str) -> Dict[str, Dict[str, str]]:
    """
    Načte formáty exportu pro jednotlivé banky z CSV souboru.

    Args:
        headers_file: Cesta k CSV souboru s formáty exportu

    Returns:
        Slovník {název_banky: {headers: hlavička, delimiter: oddělovač}}
    """
    formats = {}
    try:
        logging.debug(f"Attempting to load export formats from: {headers_file}")
        logging.debug(f"File exists: {os.path.exists(headers_file)}")

        # Použij sdílenou funkci load_csv pro načtení CSV
        rows = load_csv(headers_file)

        for row in rows:
            # Zpracování oddělovače - převod escape sekvencí na skutečné znaky
            delimiter = row.get('delimiter', ',')
            if delimiter and '\\' in delimiter:
                try:
                    # Použij funkci decode_escapes pro převod escape sekvencí
                    delimiter = bytes(delimiter, 'utf-8').decode('unicode_escape')
                    logging.debug(f"Converted delimiter escape sequence '{row['delimiter']}' to actual character")
                except Exception as e:
                    logging.warning(f"Failed to decode delimiter escape sequence '{delimiter}': {e}")
                    # Pokud se převod nezdaří, použij původní hodnotu

            # Zpracování hlavičky - převod escape sekvencí na skutečné znaky v hlavičce
            headers = row.get('headers', '')
            if headers and '\\' in headers:
                try:
                    # Použij funkci decode_escapes pro převod escape sekvencí v hlavičce
                    headers = bytes(headers, 'utf-8').decode('unicode_escape')
                    logging.debug(f"Converted escape sequences in headers for {row.get('bank', 'unknown')}")
                except Exception as e:
                    logging.warning(f"Failed to decode escape sequences in headers for {row.get('bank', 'unknown')}: {e}")

            bank_name = row.get('bank')
            if bank_name:
                formats[bank_name] = {
                    'headers': headers,
                    'delimiter': delimiter
                }
                logging.debug(f"Loaded format for {bank_name}: headers={headers[:30] if headers else ''}..., delimiter='{delimiter}'")

        logging.info(f"Loaded export formats for {len(formats)} photobanks")
        logging.debug(f"Loaded formats: {json.dumps(formats, indent=2)}")
    except Exception as e:
        logging.error(f"Failed to load photobank headers: {e}")
        logging.debug(f"Exception details: {str(e)}", exc_info=True)
    return formats

def export_mediafile(bank: str, record: Dict[str, str], output_file: str, export_formats: Dict[str, Dict[str, str]]) -> bool:
    """
    Exportuje záznam do výstupního souboru pro danou banku.

    Args:
        bank: Název banky
        record: Rozšířený záznam s vlastnostmi média
        output_file: Cesta k výstupnímu souboru
        export_formats: Slovník formátů exportu

    Returns:
        True, pokud byl záznam úspěšně exportován, jinak False
    """
    try:
        logging.debug(f"Exporting record to {bank}, output file: {output_file}")
        logging.debug(f"Complete record object: {json.dumps(record, indent=2)}")

        # Získání mapy sloupců pro danou banku
        column_map = get_column_map(bank)

        # Vytvoření kopie mapy sloupců bez funkcí pro logování
        log_column_map = []
        for col in column_map:
            log_col = {}
            for k, v in col.items():
                if k != 'transform':
                    log_col[k] = v
                else:
                    log_col[k] = "<function>"  # Nahrazení funkce textem
            log_column_map.append(log_col)

        logging.debug(f"Column map for {bank}:\n{json.dumps(log_column_map, indent=2)}")

        # Kontrola, zda má záznam všechny potřebné hodnoty
        required_sources = [col['source'] for col in column_map if 'source' in col and 'value' not in col]
        missing_sources = [source for source in required_sources if source and source not in record]

        if missing_sources:
            logging.warning(f"Record is missing required sources for {bank}: {missing_sources}")
            logging.warning(f"Skipping record: {record.get('filename', 'unknown')}")
            return False

        # Získání oddělovače pro danou banku
        bank_format = export_formats.get(bank, {})
        delimiter = bank_format.get('delimiter', ',')

        # Oddělovač by měl být již převeden na skutečný znak v load_photobank_headers
        if delimiter == '\t':
            logging.debug(f"Using TAB delimiter for {bank}")
        else:
            logging.debug(f"Using delimiter for {bank}: '{delimiter}'")

        # Vytvoření záznamu podle mapy sloupců
        csv_record = {}
        for col in column_map:
            target_field = col['target']

            # Získání hodnoty ze záznamu nebo pevné hodnoty
            if "value" in col:
                value = col["value"]
                logging.debug(f"Using fixed value for {target_field}: '{value}'")
            else:
                source = col["source"]
                value = record.get(source, "")
                logging.debug(f"Using value from record for {target_field} (source: {source}): '{value}'")

            # Případná transformace hodnoty
            if "transform" in col and callable(col["transform"]):
                try:
                    old_value = value
                    value = col["transform"](value)
                    logging.debug(f"Transformed value for {target_field}: '{old_value}' -> '{value}'")
                except Exception as e:
                    logging.warning(f"Transform failed for {target_field}: {e}")
                    value = ""

            # Sanitize value to prevent CSV injection attacks
            value = sanitize_field(value)

            csv_record[target_field] = value

        # Zápis do souboru pomocí csv.DictWriter (QUOTE_ALL pro bezpečnost)
        logging.debug(f"Writing record to file: {output_file}")

        # Check if file exists and has content (defensive programming)
        file_exists = os.path.exists(output_file)
        file_is_empty = not file_exists or os.path.getsize(output_file) == 0

        logging.debug(f"File exists before write: {file_exists}, is empty: {file_is_empty}")

        # Get fieldnames from column map
        fieldnames = [col['target'] for col in column_map]

        # Open in append mode, but write header if file is empty
        with open(output_file, 'a', encoding='utf-8', newline='') as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=fieldnames,
                delimiter=delimiter,
                quotechar='"',
                quoting=csv.QUOTE_ALL  # Force quoting for all fields
            )

            # Write header if file is empty (defensive check)
            if file_is_empty:
                writer.writeheader()
                logging.debug(f"Wrote CSV header for empty file: {output_file}")

            writer.writerow(csv_record)

        logging.debug(f"Successfully exported to {bank}: {record.get('filename', '')}")
        logging.debug(f"File exists after write: {os.path.exists(output_file)}")
        logging.debug(f"File size after write: {os.path.getsize(output_file)} bytes")

        return True
    except Exception as e:
        logging.error(f"Failed to export to {bank}: {e}")
        logging.debug(f"Exception details: {str(e)}", exc_info=True)
        return False

def export_to_photobanks(items: List[Dict[str, str]], enabled_banks: List[str], output_paths: Dict[str, str],
                        filter_func=None, include_alternative_formats: bool = False) -> Dict[str, int]:
    """
    Exportuje záznamy do výstupních souborů pro aktivované banky.

    Args:
        items: Seznam původních položek ze vstupního CSV
        enabled_banks: Seznam aktivovaných bank
        output_paths: Slovník cest k výstupním souborům
        filter_func: Volitelná funkce pro filtrování záznamů podle banky
        include_alternative_formats: Zda zahrnout alternativní formáty (PNG, TIF, RAW)

    Returns:
        Summary with ``files_written``, ``files_failed`` and ``records_failed``
    """
    summary = {"files_written": 0, "files_failed": 0, "records_failed": 0}
    logging.debug(f"Starting export to photobanks. Enabled banks: {enabled_banks}")
    logging.debug(f"Output paths: {json.dumps(output_paths)}")
    logging.debug(f"Number of items to process: {len(items)}")

    # Načtení formátů exportu
    export_formats = load_photobank_headers(DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH)
    logging.info(f"Loaded export formats from {DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH}")

    # Načtení map kategorií
    category_maps = {
        'adobe': load_category_map(DEFAULT_ADOBE_CATEGORY_PATH, 'name', 'id'),
        'dreamstime': load_category_map(DEFAULT_DREAMSTIME_CATEGORY_PATH, 'path', 'id')
    }
    logging.info(f"Loaded category maps: {', '.join(category_maps.keys())}")

    # Načtení cen Pond5
    pond_prices = load_pond_prices(DEFAULT_POND_PRICES_PATH)
    logging.info(f"Loaded Pond5 prices from {DEFAULT_POND_PRICES_PATH}")

    # Log prvních 5 položek pro kontrolu
    if items:
        logging.debug("Sample of items to process (first 5):")
        for i, item in enumerate(items[:5]):
            logging.debug(f"Item {i+1}:\n{json.dumps(item, indent=2)}")

    for bank in enabled_banks:
        output_file = output_paths[bank]
        logging.debug(f"Processing bank: {bank}, output file: {output_file}")

        # Check if bank has batch size limit
        batch_size_limit = PHOTOBANK_BATCH_SIZE_LIMITS.get(bank, 0)

        # Filtruj položky podle banky, pokud je zadána filtrovací funkce
        bank_items = items
        if filter_func:
            bank_items = [item for item in items if filter_func(item, bank)]
            logging.info(f"Filtered {len(bank_items)}/{len(items)} items for {bank} based on status")

        # Filter out editorial content for banks that don't support it
        original_count = len(bank_items)
        bank_items = [item for item in bank_items if not should_skip_editorial(item, bank)]
        editorial_filtered = original_count - len(bank_items)
        if editorial_filtered > 0:
            logging.info(f"Filtered out {editorial_filtered} editorial items for {bank} (does not accept editorial)")

        # Batches are cut over records first (as createbatch batch_NNN folders), then split per edit type
        touched_files = []
        for editorial in (False, True):
            group_items = [item for item in bank_items if is_editorial_item(item) == editorial]
            batches = split_into_batches(group_items, batch_size_limit)
            if batch_size_limit > 0 and batches:
                logging.info(f"{bank} has batch size limit of {batch_size_limit}, created {len(batches)} batches")

            for batch_idx, batch_items in enumerate(batches, start=1):
                entries = []
                for item in batch_items:
                    for expanded_item in expand_item_with_alternative_formats(item, bank, include_alternative_formats):
                        record = extract_media_properties(expanded_item, category_maps, pond_prices)
                        entries.append((expanded_item, record))

                for edit_type, group_records in group_records_by_edit_type(entries):
                    batch_output_file = get_group_output_file(
                        output_file, edit_type, editorial, batch_idx if batch_size_limit > 0 else None
                    )
                    touched_files.append(batch_output_file)
                    header_ok, exported = _write_batch(bank, group_records, batch_output_file, export_formats)
                    if header_ok:
                        summary["files_written"] += 1
                    else:
                        summary["files_failed"] += 1
                    summary["records_failed"] += len(group_records) - exported

        for stale in find_stale_outputs(output_file, touched_files):
            logging.warning(f"{bank}: {stale} was not written by this export and is out of date")

    return summary


def _write_batch(bank: str, batch_records: List[Dict[str, str]], batch_output_file: str,
                 export_formats: Dict[str, Dict[str, str]]) -> Tuple[bool, int]:
    """
    Write the header and the records of one output file.

    A bank without a header is an error: nothing is written, so records are never appended
    to an existing file of an earlier run.

    :param bank: Photobank name.
    :param batch_records: Export records for this file.
    :param batch_output_file: Output CSV path.
    :param export_formats: Export formats loaded by ``load_photobank_headers``.
    :return: ``(header written, number of exported records)``.
    """
    logging.info(f"Writing {len(batch_records)} records to {batch_output_file}")

    header = export_formats.get(bank, {}).get('headers', '')
    if not header:
        logging.error(f"No header defined for {bank}, {batch_output_file} was not written")
        return False, 0

    try:
        with open(batch_output_file, 'w', encoding='utf-8') as f:
            f.write(header + '\n')
        logging.debug(f"Wrote header for {bank}: {batch_output_file}")
    except Exception as e:
        logging.error(f"Failed to write header for {bank} to {batch_output_file}: {e}")
        return False, 0

    export_count = 0
    for record in batch_records:
        if export_mediafile(bank, record, batch_output_file, export_formats):
            export_count += 1
            if export_count % 10 == 0:
                logging.debug(f"{batch_output_file}: exported {export_count}/{len(batch_records)} records")

    logging.info(f"Exported {export_count}/{len(batch_records)} records to {batch_output_file}")
    return True, export_count
