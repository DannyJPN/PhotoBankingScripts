import os
import re
import logging
import json
from argparse import Namespace

from shared.file_operations import load_csv
from exportpreparedmedialib.constants import (
    EDITORIAL_REGEX,
    VECTOREXT_REGEX,
    VALID_STATUS,
    DEFAULT_LOCATION,
    DEFAULT_USERNAME,
    DEFAULT_COPYRIGHT_AUTHOR
)

def get_enabled_banks(args: Namespace) -> list[str]:
    """
    Vrátí seznam aktivovaných bank na základě argumentů příkazové řádky.

    Args:
        args: Argumenty příkazové řádky

    Returns:
        Seznam názvů aktivovaných bank
    """
    enabled_banks = []

    # Kontrola jednotlivých přepínačů pro banky
    if hasattr(args, 'shutterstock') and args.shutterstock:
        enabled_banks.append("ShutterStock")

    if hasattr(args, 'adobestock') and args.adobestock:
        enabled_banks.append("AdobeStock")

    if hasattr(args, 'dreamstime') and args.dreamstime:
        enabled_banks.append("DreamsTime")

    if hasattr(args, 'depositphotos') and args.depositphotos:
        enabled_banks.append("DepositPhotos")

    if hasattr(args, 'bigstockphoto') and args.bigstockphoto:
        enabled_banks.append("BigStockPhoto")

    if hasattr(args, '123rf') and args._123rf:
        enabled_banks.append("123RF")

    if hasattr(args, 'canstockphoto') and args.canstockphoto:
        enabled_banks.append("CanStockPhoto")

    if hasattr(args, 'pond5') and args.pond5:
        enabled_banks.append("Pond5")

    if hasattr(args, 'gettyimages') and args.gettyimages:
        enabled_banks.append("GettyImages")

    if hasattr(args, 'alamy') and args.alamy:
        enabled_banks.append("Alamy")

    logging.info(f"Enabled banks: {', '.join(enabled_banks)}")
    return enabled_banks

def get_output_paths(enabled_banks: list[str], output_dir: str, file_prefix: str) -> dict[str, str]:
    """
    Vytvoří cesty k výstupním CSV souborům pro každou aktivovanou banku.

    Args:
        enabled_banks: Seznam aktivovaných bank
        base_prefix: Prefix cesty pro výstupní soubory

    Returns:
        Slovník {název_banky: cesta_k_souboru}
    """
    logging.debug(f"Creating output paths for banks: {enabled_banks}")
    logging.debug(f"Output directory: {output_dir}")
    logging.debug(f"File prefix: {file_prefix}")

    output_paths = {}

    for bank in enabled_banks:
        # Kombinuj adresář, prefix a název banky
        output_file = os.path.join(output_dir, f"{file_prefix}_{bank}.csv")
        output_paths[bank] = output_file
        logging.debug(f"Created output path for {bank}: {output_file}")
        logging.debug(f"Output directory exists: {os.path.exists(output_dir)}")
        logging.info(f"Output path for {bank}: {output_file}")

    return output_paths

def should_include_item(item: dict[str, str], bank: str = None) -> bool:
    """
    Určí, zda má být položka zahrnuta do exportu na základě jejího statusu.

    Args:
        item: Položka ze vstupního CSV
        bank: Název fotobanky, pro kterou se kontroluje status

    Returns:
        True, pokud má být položka zahrnuta, jinak False
    """
    filename = item.get('Soubor', item.get('filename', item.get('Filename', item.get('file', item.get('File', 'unknown')))))

    # Pokud je zadána konkrétní fotobanka, kontroluj pouze její status
    if bank:
        # Hledej sloupec se statusem pro danou fotobanku
        bank_status_column = None
        for key in item.keys():
            if "status" in key.lower() and bank.lower() in key.lower():
                bank_status_column = key
                break

        # Pokud byl nalezen sloupec se statusem pro danou fotobanku
        if bank_status_column:
            status_value = item[bank_status_column].strip().lower()
            is_valid = status_value == VALID_STATUS.lower()
            logging.debug(f"Checking if item {filename} should be included for {bank}: status='{status_value}', valid={is_valid}")
            return is_valid
        else:
            # Pokud nebyl nalezen sloupec se statusem pro danou fotobanku, použij obecný status
            logging.debug(f"No specific status column found for {bank}, using general status")

    # Pokud není zadána konkrétní fotobanka nebo nebyl nalezen sloupec se statusem pro danou fotobanku,
    # projdi všechny sloupce, které obsahují "status" v názvu
    logging.debug(f"Checking if item {filename} should be included (general check)")
    status_columns = [key for key in item.keys() if "status" in key.lower()]

    for key in status_columns:
        status_value = item[key].strip().lower()
        # Pokud je hodnota ve sloupci status rovna validnímu statusu, vrať True
        if status_value == VALID_STATUS.lower():
            logging.debug(f"Item {filename} included: status '{status_value}' in column '{key}' matches valid status '{VALID_STATUS.lower()}'")
            return True

    logging.debug(f"Item {filename} excluded: no matching status found")
    return False

def load_category_map(path: str, key_column: str, value_column: str) -> dict[str, str]:
    """
    Načte mapu kategorií z CSV souboru.

    Args:
        path: Cesta k CSV souboru
        key_column: Název sloupce, který bude použit jako klíč
        value_column: Název sloupce, který bude použit jako hodnota

    Returns:
        Slovník {klíč: hodnota} z CSV souboru
    """
    category_map = {}

    try:
        # Použij sdílenou funkci load_csv pro načtení CSV
        rows = load_csv(path)
        for row in rows:
            if key_column in row and value_column in row:
                category_map[row[key_column]] = row[value_column]
    except Exception as e:
        logging.error(f"Failed to load category map from {path}: {e}")
        return {}

    logging.info(f"Loaded {len(category_map)} categories from {path}")
    return category_map


def load_pond_prices(csv_path: str) -> dict[str, str]:
    """
    Načte ceny Pond5 z CSV souboru.

    Args:
        csv_path: Cesta k CSV souboru s cenami Pond5

    Returns:
        Slovník {přípona_souboru: cena}
    """
    price_map = {}

    try:
        items = load_csv(csv_path)
        for item in items:
            extension = item.get('extension', '').strip().lower()
            price = item.get('price', '').strip()
            if extension and price:
                price_map[extension] = price
        logging.info(f"Loaded {len(price_map)} Pond5 prices from {csv_path}")
        logging.debug(f"Pond5 prices: {json.dumps(price_map)}")
    except Exception as e:
        logging.error(f"Failed to load Pond5 prices from {csv_path}: {e}")
        # Nastav výchozí ceny
        price_map = {
            'jpg': '5', 'jpeg': '5', 'png': '5', 'gif': '5', 'webp': '5',
            'tif': '10', 'tiff': '10',
            'ai': '5', 'eps': '5', 'svg': '5', 'pdf': '5',
            'mp4': '30', 'mov': '30', 'avi': '30', 'wmv': '30', 'flv': '30', 'mkv': '30'
        }
        logging.info("Using default Pond5 prices")

    return price_map

def remove_duplicate_keywords(keywords: str) -> str:
    """
    Odstraní duplicitní klíčová slova a omezí jejich počet na 50.

    Args:
        keywords: Řetězec klíčových slov oddělených čárkami

    Returns:
        Řetězec unikátních klíčových slov oddělených čárkami
    """
    if not keywords:
        return ""

    # Rozdělení klíčových slov a odstranění duplicit
    keyword_set = set()
    for keyword in keywords.split(','):
        keyword = keyword.strip()
        if len(keyword) > 2:  # Ignoruj příliš krátká klíčová slova
            keyword_set.add(keyword)

    # Omezení počtu klíčových slov na 50
    unique_keywords = list(keyword_set)[:50]

    return ','.join(unique_keywords)


def get_pond_price(filename: str, pond_prices: dict[str, str] = None) -> str:
    """
    Získá cenu Pond5 podle přípony souboru.

    Args:
        filename: Název souboru
        pond_prices: Slovník cen Pond5 pro různé přípony souborů

    Returns:
        Cena Pond5 jako řetězec
    """
    if not filename:
        return "5"  # Výchozí cena

    # Získej příponu souboru
    extension = os.path.splitext(filename)[1].lower().lstrip('.')

    # Pokud nejsou k dispozici ceny Pond5, použij výchozí ceny
    if not pond_prices:
        # Výchozí ceny
        if extension in ['tif', 'tiff']:
            return "10"
        elif extension in ['mp4', 'mov', 'avi', 'wmv', 'flv', 'mkv']:
            return "30"
        else:
            return "5"

    # Použij ceny z konfigurace
    return pond_prices.get(extension, "5")  # Výchozí cena je 5

def extract_media_properties(item: dict[str, str], category_maps: dict[str, dict[str, str]], pond_prices: dict[str, str] = None) -> dict[str, str]:
    """
    Extrahuje vlastnosti média z položky a vytvoří rozšířený záznam.

    Args:
        item: Položka ze vstupního CSV
        category_maps: Slovník map kategorií pro různé banky
        pond_prices: Slovník cen Pond5 pro různé přípony souborů

    Returns:
        Rozšířený záznam s vlastnostmi média
    """
    logging.debug(f"Extracting media properties from complete item:\n{json.dumps(item, indent=2)}")
    logging.debug(f"Category maps available: {list(category_maps.keys())}")

    # Základní vlastnosti
    filename = item.get('Soubor', item.get('filename', item.get('Filename', item.get('file', item.get('File', '')))))
    title = item.get('Název', item.get('title', item.get('Title', '')))
    description = item.get('Popis', item.get('description', item.get('Description', '')))
    keywords = item.get('Klíčová slova', item.get('keywords', item.get('Keywords', '')))

    logging.debug(f"Extracted basic properties for {filename}:")
    logging.debug(f"  - title: {title}")
    logging.debug(f"  - description: {description}")
    logging.debug(f"  - keywords: {keywords}")

    # Detekce typu souboru (editorial prefix can be in title OR description)
    is_editorial = bool(re.search(EDITORIAL_REGEX, title)) or bool(re.search(EDITORIAL_REGEX, description))
    is_vector = bool(re.search(VECTOREXT_REGEX, filename, re.IGNORECASE)) if filename else False

    # Kategorie pro DreamsTime
    dreamstime_cats = []
    dreamstime_category = item.get('DreamsTime kategorie', '').strip()
    if dreamstime_category:
        # Použij kategorie z položky, pokud existují
        dreamstime_cats = dreamstime_category.split(',')
    elif 'dreamstime' in category_maps and keywords:
        # Hledání až 3 kategorií podle klíčových slov
        for keyword in keywords.split(','):
            keyword = keyword.strip()
            for path, cat_id in category_maps['dreamstime'].items():
                if keyword.lower() in path.lower():
                    dreamstime_cats.append(cat_id)
                    if len(dreamstime_cats) >= 3:  # Maximálně 3 kategorie
                        break
            if len(dreamstime_cats) >= 3:
                break

    # Kategorie pro Adobe Stock
    adobe_cat_id = ""
    adobe_category = item.get('AdobeStock kategorie', '').strip()
    if adobe_category and 'adobe' in category_maps:
        # Použij kategorii z položky, pokud existuje
        adobe_cat_id = category_maps['adobe'].get(adobe_category, "")
    elif 'adobe' in category_maps and keywords:
        # Hledání kategorie podle klíčových slov
        for keyword in keywords.split(','):
            keyword = keyword.strip()
            for name, cat_id in category_maps['adobe'].items():
                if keyword.lower() in name.lower():
                    adobe_cat_id = cat_id
                    break
            if adobe_cat_id:
                break

    # Kategorie pro ShutterStock
    shutterstock_cats = item.get('ShutterStock kategorie', '').strip()
    logging.debug(f"ShutterStock categories: {shutterstock_cats}")

    # Kategorie pro BigStockPhoto
    bigstock_cat = item.get('BigStockPhoto kategorie', '').strip()
    logging.debug(f"BigStockPhoto categories: {bigstock_cat}")

    # Kategorie pro 123RF
    rf123_cat = item.get('123RF kategorie', '').strip()
    logging.debug(f"123RF categories: {rf123_cat}")

    # Kategorie pro CanStockPhoto
    canstock_cat = item.get('CanStockPhoto kategorie', '').strip()
    logging.debug(f"CanStockPhoto categories: {canstock_cat}")

    # Kategorie pro Pond5
    pond5_cat = item.get('Pond5 kategorie', '').strip()
    logging.debug(f"Pond5 categories: {pond5_cat}")

    # Kategorie pro GettyImages
    getty_cat = item.get('GettyImages kategorie', '').strip()
    logging.debug(f"GettyImages categories: {getty_cat}")

    # Kategorie pro DepositPhotos
    deposit_cat = item.get('DepositPhotos kategorie', '').strip()
    logging.debug(f"DepositPhotos categories: {deposit_cat}")

    # Kategorie pro Alamy
    alamy_categories = item.get('Alamy kategorie', '').strip()
    alamy_cats_list = [cat.strip() for cat in alamy_categories.split(',')] if alamy_categories else []

    # První kategorie je primární, druhá sekundární
    alamy_primary_cat = alamy_cats_list[0] if len(alamy_cats_list) > 0 else ''
    alamy_secondary_cat = alamy_cats_list[1] if len(alamy_cats_list) > 1 else ''

    logging.debug(f"Alamy categories: {alamy_categories}")
    logging.debug(f"Alamy primary category: {alamy_primary_cat}")
    logging.debug(f"Alamy secondary category: {alamy_secondary_cat}")

    # Datum vytvoření
    creation_date = item.get('Datum vytvoření', '')
    year = ""
    getty_date = ""
    if creation_date:
        try:
            # Datum je vždy řetězec ve formátu DD.MM.YYYY
            # Extrahuj rok (poslední 4 znaky)
            if isinstance(creation_date, str) and len(creation_date) >= 4:
                # Pokud je formát DD.MM.YYYY, vezmi posledních 4 znaky
                if '.' in creation_date:
                    year = creation_date.split('.')[-1]
                    # Getty Images vyžaduje formát MM/DD/YYYY HH:MM:SS +/-ZZZZ
                    parts = creation_date.split('.')
                    if len(parts) == 3:
                        day, month, year_part = parts
                        # Převod na MM/DD/YYYY 12:00:00 +0000 (GMT)
                        getty_date = f"{month.zfill(2)}/{day.zfill(2)}/{year_part} 12:00:00 +0000"
                        logging.debug(f"Converted date '{creation_date}' to Getty format '{getty_date}'")
                else:
                    # Pro jiné formáty zkus extrahovat rok
                    year = ''.join(c for c in creation_date if c.isdigit())[-4:]

                logging.debug(f"Extracted year '{year}' from date '{creation_date}'")
        except Exception as e:
            logging.warning(f"Failed to extract year from date '{creation_date}': {e}")
            # Pokud se extrakce nezdaří, ponech prázdný řetězec

    # Vytvoření rozšířeného záznamu
    extended_record = {
        # Základní vlastnosti
        'filename': filename,
        'title': title,
        'description': description,
        'keywords': remove_duplicate_keywords(keywords),
        'editorial': 'yes' if is_editorial else 'no',
        'vector': 'yes' if is_vector else 'no',
        'location': item.get('location', item.get('Location', DEFAULT_LOCATION)),
        'year': year,
        'getty_date': getty_date,  # Getty Images formát MM/DD/YYYY HH:MM:SS +/-ZZZZ

        # DreamsTime kategorie (ID kategorií)
        'dreamstime_cat1': dreamstime_cats[0] if len(dreamstime_cats) > 0 else '',
        'dreamstime_cat2': dreamstime_cats[1] if len(dreamstime_cats) > 1 else '',
        'dreamstime_cat3': dreamstime_cats[2] if len(dreamstime_cats) > 2 else '',

        # Adobe Stock kategorie (ID kategorie)
        'adobe_cat_id': adobe_cat_id,

        # ShutterStock kategorie (názvy kategorií oddělené čárkou)
        'shutterstock_cats': shutterstock_cats,

        # BigStockPhoto kategorie (názvy kategorií oddělené čárkou)
        'bigstock_cat': bigstock_cat,

        # 123RF kategorie
        'rf123_cat': rf123_cat,

        # CanStockPhoto kategorie
        'canstock_cat': canstock_cat,

        # Pond5 kategorie
        'pond5_cat': pond5_cat,

        # GettyImages kategorie
        'getty_cat': getty_cat,

        # DepositPhotos kategorie
        'deposit_cat': deposit_cat,

        # Alamy kategorie (názvy kategorií)
        'primary_category': alamy_primary_cat,
        'secondary_category': alamy_secondary_cat,

        # Obecné metadata
        'username': DEFAULT_USERNAME,
        'copyright': f"{DEFAULT_COPYRIGHT_AUTHOR} {year}" if year else DEFAULT_COPYRIGHT_AUTHOR,
        'mature': 'no',
        'nudity': '0',  # DepositPhotos expects "0" for no nudity, not "no"
        'country': 'CZ',

        # Alamy specifické pole
        'super_keywords': ','.join(keywords.split(',')[:10]) if keywords else '',

        # Pond5 specifické pole - cena podle přípony souboru
        'pond5_price': get_pond_price(filename, pond_prices)
    }

    logging.debug(f"Created complete extended record for {filename}:\n{json.dumps(extended_record, indent=2)}")

    return extended_record
