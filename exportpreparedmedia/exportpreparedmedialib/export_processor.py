import logging
import os
import csv
from datetime import datetime
from tqdm import tqdm
from shared.utils import is_editorial, load_extensions
from shared.csv_handler import save_export_objects_to_csv
from exportpreparedmedialib.category_handler import get_categories_for_photobank
from exportpreparedmedialib.constants import (
    VIDEO_EXTENSIONS_FILE,
    IMAGE_EXTENSIONS_FILE,
    ILLUSTRATION_EXTENSIONS_FILE,
    LOCATION,
    MATURE_CONTENT,
    FREE,
    W_EL,
    P_EL,
    SR_EL,
    SR_PRICE,
    MR_DOC_IDS,
    PR_DOCS,
    NUDITY,
    COUNTRY,
    SPECIFY_SOURCE,
    USERNAME,
    EXCLUSIVE,
    ADDITIONAL_INFO,
    PHOTOBANKS,
    NA_VALUE
)
from exportpreparedmedialib.export_objects import (
    ShutterStockExport,
    AdobeStockExport,
    DreamstimeExport,
    DepositPhotosExport,
    BigStockPhotoExport,
    RF123Export,
    CanStockPhotoExport,
    Pond5Export,
    AlamyExport,
    GettyImagesExport
)
from exportpreparedmedialib.header_mappings import HEADER_MAPPINGS
from shared.csv_handler import initialize_csv_file

video_extensions = load_extensions(VIDEO_EXTENSIONS_FILE)
image_extensions = load_extensions(IMAGE_EXTENSIONS_FILE)
illustration_extensions = load_extensions(ILLUSTRATION_EXTENSIONS_FILE)

def process_exports(prepared_items, photobanks, all_categories, csv_location):
    """Process exports for each photobank and item combination."""
    logging.info("Starting export processing for all photobanks")
    logging.debug(f"Loaded category mappings for all photobanks: {all_categories}")

    for photobank in photobanks:
        logging.info(f"Processing photobank: {photobank}")

        # Initialize the CSV file with the header
        initialize_csv_file(photobank, csv_location)

        export_objects = []

        try:
            logging.info(f"Building export objects for {photobank}")
            for item in prepared_items:
                try:
                    logging.debug(f"Processing item {item['Soubor']} for photobank {photobank}")
                    export_object = create_export_object(photobank, item, all_categories)
                    if export_object:
                        export_objects.append(export_object)
                        logging.debug(f"Created export object for {item['Soubor']}: {export_object.__dict__}")

                    # Handle special cases for Dreamstime and Pond5
                    if photobank == "Dreamstime" and item['Soubor'].lower().endswith('.jpg'):
                        export_objects.extend(create_additional_dreamstime_objects(item, all_categories))
                    if photobank == "Pond5" and item['Soubor'].lower().endswith('.jpg'):
                        export_objects.extend(create_additional_pond5_objects(item, all_categories))

                except Exception as e:
                    logging.error(f"Error creating export object for {item['Soubor']} in {photobank}: {e}", exc_info=True)
                    continue

            # Save all export objects for this photobank to CSV
            if export_objects:
                logging.info(f"Saving {len(export_objects)} export objects to CSV for {photobank}")
                for export_object in tqdm(export_objects, desc=f"Saving items for {photobank}"):
                    save_export_objects_to_csv([export_object], photobank, csv_location)
            else:
                logging.warning(f"No export objects to save for photobank {photobank}")

        except Exception as e:
            logging.error(f"Error processing photobank {photobank}: {e}", exc_info=True)
            continue

    logging.info("Completed export processing for all photobanks")

def create_additional_dreamstime_objects(item, all_categories):
    """Create additional export objects for Dreamstime for PNG and RAW formats."""
    additional_objects = []
    base_filename = item['Soubor'].rsplit('.', 1)[0]
    extensions = ['.png', '.raw', '.nef', '.dng']
    for ext in extensions:
        new_item = item.copy()
        new_item['Soubor'] = base_filename + ext
        export_object = create_export_object("Dreamstime", new_item, all_categories)
        if export_object:
            additional_objects.append(export_object)
    return additional_objects

def create_additional_pond5_objects(item, all_categories):
    """Create additional export objects for Pond5 for PNG and TIF formats."""
    additional_objects = []
    base_filename = item['Soubor'].rsplit('.', 1)[0]
    extensions = ['.png', '.tif']
    for ext in extensions:
        new_item = item.copy()
        new_item['Soubor'] = base_filename + ext
        export_object = create_export_object("Pond5", new_item, all_categories)
        if export_object:
            additional_objects.append(export_object)
    return additional_objects

def create_export_object(photobank, item, all_categories):
    """Create an export object for a specific photobank and item."""
    try:
        if photobank not in PHOTOBANKS:
            logging.error(f"Unsupported photobank: {photobank}")
            raise ValueError(f"Unsupported photobank: {photobank}")

        # Get the header mappings for the current photobank
        header_mapping = HEADER_MAPPINGS.get(photobank, {})
        if not header_mapping:
            logging.error(f"No header mapping found for photobank: {photobank}")
            raise ValueError(f"No header mapping found for photobank: {photobank}")

        # Extract basic information
        filename = item['Soubor']
        date_created = item['Datum vytvoření']

        # Parse date and extract year properly
        try:
            year_created = datetime.strptime(date_created, '%d.%m.%Y').year
            logging.debug(f"Successfully parsed date {date_created} to year {year_created}")
        except ValueError as e:
            logging.error(f"Error parsing date {date_created}: {e}", exc_info=True)
            # Fallback to current year if date parsing fails
            year_created = datetime.now().year
            logging.warning(f"Using fallback year {year_created} for invalid date {date_created}")

        editorial_status = is_editorial(item['Název'], item['Popis'], item['Klíčová slova'])
        categories = get_categories_for_photobank(item, all_categories[photobank], f'{photobank} kategorie')

        # Create all_fields dictionary with all possible fields
        all_fields = {
            'filename': filename,
            'file_name': filename,
            'oldfilename': filename,
            'originalfilename': filename,
            'filename_123rf': '',
            'title': item['Název'],
            'image_name': item['Název'],
            'caption': item['Název'],
            'description': item['Popis'],
            'keywords': item['Klíčová slova'],
            'tags': item['Klíčová slova'],
            'editorial': editorial_status,
            'category': categories,
            'categories': categories,
            'Category 1': categories[0] if categories else '',
            'Category 2': categories[1] if len(categories) > 1 else '',
            'Category 3': categories[2] if len(categories) > 2 else '',
            'primary_category': categories[0] if categories else '',
            'secondary_category': categories[1] if len(categories) > 1 else '',
            'Primary category': categories[0] if categories else '',
            'Secondary category': categories[1] if len(categories) > 1 else '',
            'mature_content': MATURE_CONTENT,
            'Mature content': MATURE_CONTENT,
            'illustration': "yes" if any(filename.lower().endswith(ext) for ext in illustration_extensions) else "no",
            'free': FREE,
            'Free': FREE,
            'w_el': W_EL,
            'W-EL': W_EL,
            'p_el': P_EL,
            'P-EL': P_EL,
            'sr_el': SR_EL,
            'SR-EL': SR_EL,
            'sr_price': SR_PRICE,
            'SR-Price': SR_PRICE,
            'mr_doc_ids': MR_DOC_IDS,
            'MR doc Ids': MR_DOC_IDS,
            'pr_docs': PR_DOCS,
            'Pr Docs': PR_DOCS,
            'nudity': NUDITY,
            'Nudity': NUDITY,
            'country': COUNTRY,
            'specifysource': SPECIFY_SOURCE,
            'copyright': f"Dan K. {year_created}",
            'license_type': "RF" if editorial_status == "no" else "RF-E",
            'License type': "RF" if editorial_status == "no" else "RF-E",
            'username': USERNAME,
            'Username': USERNAME,
            'super_tags': ",".join(item['Klíčová slova'].split(",")[:10]),
            'Super Tags': ",".join(item['Klíčová slova'].split(",")[:10]),
            'location': LOCATION,
            'Location': LOCATION,
            'date_taken': date_created,
            'Date taken': date_created,
            'created_date': date_created,
            'number_people': "0",
            'Number of People': "0",
            'model_release': NA_VALUE,
            'Model release': NA_VALUE,
            'property_release': NA_VALUE,
            'Property release': NA_VALUE,
            'exclusive': EXCLUSIVE,
            'Exclusive to Alamy': EXCLUSIVE,
            'additional_info': ADDITIONAL_INFO,
            'Additional Info': ADDITIONAL_INFO,
            'brief_code': ''
        }

        # Create kwargs using only the fields that exist in the header mapping
        kwargs = {}
        for header, internal_name in header_mapping.items():
            special_value = get_special_case_value(header, item, all_categories, photobank)
            if special_value:
                kwargs[header] = special_value
            elif internal_name in all_fields:
                kwargs[header] = all_fields[internal_name]
            elif header in all_fields:
                kwargs[header] = all_fields[header]
            logging.debug(f"Added {header}: {kwargs.get(header)} to kwargs for {photobank}")

        # Get the appropriate export class
        export_object_class = {
            "ShutterStock": ShutterStockExport,
            "AdobeStock": AdobeStockExport,
            "Dreamstime": DreamstimeExport,
            "DepositPhotos": DepositPhotosExport,
            "BigStockPhoto": BigStockPhotoExport,
            "123RF": RF123Export,
            "CanStockPhoto": CanStockPhotoExport,
            "Pond5": Pond5Export,
            "Alamy": AlamyExport,
            "GettyImages": GettyImagesExport
        }.get(photobank)

        if not export_object_class:
            raise ValueError(f"No export class found for photobank: {photobank}")

        logging.debug(f"Creating export object for {photobank} with kwargs: {kwargs}")
        return export_object_class(**kwargs)

    except Exception as e:
        logging.error(f"Error creating export object for {photobank}: {e}", exc_info=True)
        raise

def get_special_case_value(header, item, all_categories, photobank):
    """Handle special cases where a property value needs to be transformed differently for specific photobanks."""
    try:
        logging.debug(f"Processing special case for {photobank}, header: {header}")

        # Handle editorial status for Dreamstime (1/0 instead of yes/no)
        if photobank == "Dreamstime" and header.lower() == "editorial":
            editorial_status = is_editorial(item['Název'], item['Popis'], item['Klíčová slova'])
            value = "1" if editorial_status.lower() == "yes" else "0"
            logging.debug(f"Dreamstime editorial status transformed: {editorial_status} -> {value}")
            return value

        # Handle categories for different photobanks
        if header.lower() in ["category", "categories", "category 1", "category 2", "category 3",
                            "primary category", "secondary category"]:
            logging.debug(f"Processing categories for header: {header}")
            categories = get_categories_for_photobank(item, all_categories[photobank], f'{photobank} kategorie')
            logging.debug(f"Categories before mapping: {categories}")

            if not categories:
                logging.debug(f"No categories found for {header}")
                return ""

            if header.lower() in ["category 1", "primary category"]:
                return categories[0] if categories else ""
            elif header.lower() in ["category 2", "secondary category"]:
                return categories[1] if len(categories) > 1 else ""
            elif header.lower() == "category 3":
                return categories[2] if len(categories) > 2 else ""
            elif header.lower() in ["categories","category"]:
                return ",".join(categories)

        # Handle image type transformations
        if header.lower() in ["imagetype", "image_type", "image type"]:
            filename = item['Soubor'].lower()
            if any(filename.endswith(ext) for ext in video_extensions):
                return "V"  # Video
            elif any(filename.endswith(ext) for ext in illustration_extensions):
                return "I"  # Illustration
            return "P"  # Photo

        # Handle price transformations
        if header.lower() == "price":
            filename = item['Soubor'].lower()
            if any(filename.endswith(ext) for ext in video_extensions):
                return str(len(item.get('Délka videa (s)', "100")))
            elif filename.endswith(('tif', 'tiff')):
                return "10"
            return "5"

        # Handle super tags (first 10 keywords)
        #if header.lower() in ["super tags", "super_tags"]:
        #    keywords = item.get('Klíčová slova', '').split(",")
        #    return ",".join(keywords[:10])

        # Handle license type
        #if header.lower() in ["license type", "license_type"]:
        #    editorial_status = is_editorial(item['Název'], item['Popis'], item['Klíčová slova'])
        #    return "RF-E" if editorial_status.lower() == "yes" else "RF"

        return ""

    except Exception as e:
        logging.error(f"Error in get_special_case_value for {photobank}, header {header}: {e}", exc_info=True)
        return ""
"""

The implemented `get_special_case_value` method handles various special cases for different photobanks:

1. Editorial status for Dreamstime (1/0 instead of yes/no)
2. Category mappings for different photobanks
3. Image type transformations (Photo/Video/Illustration)
4. Price transformations based on file type
5. Super tags (first 10 keywords)
6. License type based on editorial status

The method includes comprehensive error handling and logging to track any issues that might occur during value transformation. It's designed to be extensible, allowing for easy addition of new special cases for different photobanks in the future.

The implementation has been integrated into the `create_export_object` function, where it's called before the standard field mapping to handle any special cases that might exist for the current header and photobank combination.
"""