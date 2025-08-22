import json
import logging
import os

from exportpreparedmedialib.column_maps import get_column_map


def load_photobank_headers(headers_file: str) -> dict[str, dict[str, str]]:
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
        from shared.file_operations import load_csv

        rows = load_csv(headers_file)

        for row in rows:
            # Zpracování oddělovače - převod escape sekvencí na skutečné znaky
            delimiter = row.get("delimiter", ",")
            if delimiter and "\\" in delimiter:
                try:
                    # Použij funkci decode_escapes pro převod escape sekvencí
                    delimiter = bytes(delimiter, "utf-8").decode("unicode_escape")
                    logging.debug(f"Converted delimiter escape sequence '{row['delimiter']}' to actual character")
                except Exception as e:
                    logging.warning(f"Failed to decode delimiter escape sequence '{delimiter}': {e}")
                    # Pokud se převod nezdaří, použij původní hodnotu

            # Zpracování hlavičky - převod escape sekvencí na skutečné znaky v hlavičce
            headers = row.get("headers", "")
            if headers and "\\" in headers:
                try:
                    # Použij funkci decode_escapes pro převod escape sekvencí v hlavičce
                    headers = bytes(headers, "utf-8").decode("unicode_escape")
                    logging.debug(f"Converted escape sequences in headers for {row.get('bank', 'unknown')}")
                except Exception as e:
                    logging.warning(
                        f"Failed to decode escape sequences in headers for {row.get('bank', 'unknown')}: {e}"
                    )

            bank_name = row.get("bank")
            if bank_name:
                formats[bank_name] = {"headers": headers, "delimiter": delimiter}
                logging.debug(
                    f"Loaded format for {bank_name}: headers={headers[:30] if headers else ''}..., delimiter='{delimiter}'"
                )

        logging.info(f"Loaded export formats for {len(formats)} photobanks")
        logging.debug(f"Loaded formats: {json.dumps(formats, indent=2)}")
    except Exception as e:
        logging.error(f"Failed to load photobank headers: {e}")
        logging.debug(f"Exception details: {str(e)}", exc_info=True)
    return formats


def export_mediafile(
    bank: str, record: dict[str, str], output_file: str, export_formats: dict[str, dict[str, str]]
) -> bool:
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
                if k != "transform":
                    log_col[k] = v
                else:
                    log_col[k] = "<function>"  # Nahrazení funkce textem
            log_column_map.append(log_col)

        logging.debug(f"Column map for {bank}:\n{json.dumps(log_column_map, indent=2)}")

        # Kontrola, zda má záznam všechny potřebné hodnoty
        required_sources = [col["source"] for col in column_map if "source" in col and "value" not in col]
        missing_sources = [source for source in required_sources if source and source not in record]

        if missing_sources:
            logging.warning(f"Record is missing required sources for {bank}: {missing_sources}")
            logging.warning(f"Skipping record: {record.get('filename', 'unknown')}")
            return False

        # Získání oddělovače pro danou banku
        bank_format = export_formats.get(bank, {})
        delimiter = bank_format.get("delimiter", ",")

        # Oddělovač by měl být již převeden na skutečný znak v load_photobank_headers
        if delimiter == "\t":
            logging.debug(f"Using TAB delimiter for {bank}")
        else:
            logging.debug(f"Using delimiter for {bank}: '{delimiter}'")

        # Vytvoření řádku podle mapy sloupců
        row = []
        for col in column_map:
            # Získání hodnoty ze záznamu nebo pevné hodnoty
            if "value" in col:
                value = col["value"]
                logging.debug(f"Using fixed value for {col['target']}: '{value}'")
            else:
                source = col["source"]
                value = record.get(source, "")
                logging.debug(f"Using value from record for {col['target']} (source: {source}): '{value}'")

            # Případná transformace hodnoty
            if "transform" in col and callable(col["transform"]):
                try:
                    old_value = value
                    value = col["transform"](value)
                    logging.debug(f"Transformed value for {col['target']}: '{old_value}' -> '{value}'")
                except Exception as e:
                    logging.warning(f"Transform failed for {col['target']}: {e}")
                    value = ""

            # Uvozovky kolem hodnoty, pokud obsahuje oddělovač nebo uvozovky
            if isinstance(value, str) and (delimiter in value or '"' in value):
                # Escapuj uvozovky a obal hodnotu uvozovkami
                value = f'"{value.replace("\"", "\"\"")}"'
                logging.debug(f"Escaped value for {col['target']}: {value}")

            row.append(str(value))

        # Spojení řádku pomocí oddělovače
        line = delimiter.join(row)
        logging.debug(f"Final line for {bank}: {line}")

        # Zápis do souboru
        logging.debug(f"Writing to file: {output_file}")
        logging.debug(f"File exists before write: {os.path.exists(output_file)}")

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        logging.debug(f"Successfully exported to {bank}: {record.get('filename', '')}")
        logging.debug(f"File exists after write: {os.path.exists(output_file)}")
        logging.debug(f"File size after write: {os.path.getsize(output_file)} bytes")

        return True
    except Exception as e:
        logging.error(f"Failed to export to {bank}: {e}")
        logging.debug(f"Exception details: {str(e)}", exc_info=True)
        return False


def export_to_photobanks(
    items: list[dict[str, str]], enabled_banks: list[str], output_paths: dict[str, str], filter_func=None
) -> None:
    """
    Exportuje záznamy do výstupních souborů pro aktivované banky.

    Args:
        items: Seznam původních položek ze vstupního CSV
        enabled_banks: Seznam aktivovaných bank
        output_paths: Slovník cest k výstupním souborům
        filter_func: Volitelná funkce pro filtrování záznamů podle banky
    """
    logging.debug(f"Starting export to photobanks. Enabled banks: {enabled_banks}")
    logging.debug(f"Output paths: {json.dumps(output_paths)}")
    logging.debug(f"Number of items to process: {len(items)}")

    # Načtení potřebných dat pro vytváření rozšířených záznamů
    from exportpreparedmedialib.banks_logic import extract_media_properties, load_category_map, load_pond_prices
    from exportpreparedmedialib.constants import (
        DEFAULT_ADOBE_CATEGORY_PATH,
        DEFAULT_DREAMSTIME_CATEGORY_PATH,
        DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH,
        DEFAULT_POND_PRICES_PATH,
    )

    # Načtení formátů exportu
    export_formats = load_photobank_headers(DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH)
    logging.info(f"Loaded export formats from {DEFAULT_PHOTOBANK_EXPORT_FORMATS_PATH}")

    # Načtení map kategorií
    category_maps = {
        "adobe": load_category_map(DEFAULT_ADOBE_CATEGORY_PATH, "name", "id"),
        "dreamstime": load_category_map(DEFAULT_DREAMSTIME_CATEGORY_PATH, "path", "id"),
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

        # Zápis hlavičky
        try:
            bank_format = export_formats.get(bank, {})
            header = bank_format.get("headers", "")
            delimiter = bank_format.get("delimiter", ",")

            # Oddělovač by měl být již převeden na skutečný znak v load_photobank_headers
            if delimiter == "\t":
                logging.debug(f"Using TAB delimiter for {bank} header")
            else:
                logging.debug(f"Using delimiter for {bank} header: '{delimiter}'")

            logging.debug(f"Bank format for {bank}:\n{json.dumps(bank_format, indent=2)}")

            if header:
                logging.debug(f"Writing header to file: {output_file}")
                logging.debug(f"Header content: {repr(header)}")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(header + "\n")
                logging.debug(f"Wrote header for {bank}")
                logging.debug(f"File exists after header write: {os.path.exists(output_file)}")
                logging.debug(f"File size after header write: {os.path.getsize(output_file)} bytes")
            else:
                logging.warning(f"No header defined for {bank}")
        except Exception as e:
            logging.error(f"Failed to write header for {bank}: {e}")
            logging.debug(f"Exception details: {str(e)}", exc_info=True)

        # Export záznamů
        export_count = 0
        attempted_count = 0

        # Filtruj položky podle banky, pokud je zadána filtrovací funkce
        bank_items = items
        if filter_func:
            bank_items = [item for item in items if filter_func(item, bank)]
            logging.info(f"Filtered {len(bank_items)}/{len(items)} items for {bank} based on status")

        # Pro každou položku vytvoř rozšířený záznam a exportuj ho
        for item in bank_items:
            attempted_count += 1
            # Vytvoření rozšířeného záznamu pro aktuální položku
            record = extract_media_properties(item, category_maps, pond_prices)

            if export_mediafile(bank, record, output_file, export_formats):
                export_count += 1
                if export_count % 10 == 0:
                    logging.debug(
                        f"Successfully exported {export_count}/{attempted_count} records to {bank} (total items: {len(items)})"
                    )

        logging.info(
            f"Exported {export_count}/{attempted_count} records to {bank} (success rate: {export_count/attempted_count*100:.1f}%)"
        )
        if os.path.exists(output_file):
            logging.debug(f"Final file size for {bank}: {os.path.getsize(output_file)} bytes")
        else:
            logging.warning(f"Output file for {bank} does not exist after export: {output_file}")
