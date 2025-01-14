import logging
import sys
from tqdm import tqdm
from createbatchlib.constants import PREPARED_STATUS

def get_prepared_media_items(media_items):
    try:
        prepared_media_items = []
        with tqdm(total=len(media_items), desc="Filtering media items", unit="item") as pbar:
            for item in media_items:
                logging.debug(f"Checking media item: {item}")
                item_prepared = False
                for key, value in item.items():
                    logging.debug(f"Checking property: {key} with value: {value}")
                    if 'status' in key.lower() and value.lower() == PREPARED_STATUS:
                        item_prepared = True
                if item_prepared:
                    prepared_media_items.append(item)
                    logging.debug(f"Added media item to prepared list: {item}")
                pbar.update(1)
        logging.info(f"Filtered {len(prepared_media_items)} prepared media items.")
        return prepared_media_items
    except Exception as e:
        logging.error(f"Error filtering prepared media items: {e}", exc_info=True)
        sys.exit(1)