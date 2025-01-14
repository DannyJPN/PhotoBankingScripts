import os
import shutil
import logging
import sys
from tqdm import tqdm

def copy_media_items_to_batch(media_items, processed_media_folder):
    try:
        updated_media_items = []
        total_items = len(media_items)

        with tqdm(total=total_items, desc="Copying files", unit="file") as pbar:
            for index, item in enumerate(media_items):
                logging.debug(f"Processing media item {index + 1}/{total_items}: {item}")
                source_path = item['Cesta']
                destination_path = os.path.join(processed_media_folder, os.path.basename(source_path))

                if not os.path.exists(destination_path):
                    try:
                        source_metadata = os.stat(source_path)
                        logging.debug(f"Source file metadata before copy - {source_path}: "
                                      f"Creation time: {source_metadata.st_ctime}, "
                                      f"Last modification time: {source_metadata.st_mtime}, "
                                      f"Last access time: {source_metadata.st_atime}")
                    except Exception as e:
                        logging.error(f"Error retrieving source file metadata for {source_path}: {e}", exc_info=True)

                    shutil.copy2(source_path, destination_path)
                    logging.debug(f"Copied {source_path} to {destination_path}")

                    try:
                        destination_metadata = os.stat(destination_path)
                        logging.debug(f"Destination file metadata after copy - {destination_path}: "
                                      f"Creation time: {destination_metadata.st_ctime}, "
                                      f"Last modification time: {destination_metadata.st_mtime}, "
                                      f"Last access time: {destination_metadata.st_atime}")
                    except Exception as e:
                        logging.error(f"Error retrieving destination file metadata for {destination_path}: {e}", exc_info=True)

                    try:
                        os.utime(destination_path, (source_metadata.st_atime, source_metadata.st_mtime))
                        logging.debug(f"Manually set timestamps for {destination_path}: "
                                      f"Access time: {source_metadata.st_atime}, "
                                      f"Modification time: {source_metadata.st_mtime}")
                    except Exception as e:
                        logging.error(f"Error setting timestamps for {destination_path}: {e}", exc_info=True)
                else:
                    logging.info(f"File already exists at {destination_path}, skipping copy.")

                item['Cesta'] = destination_path
                updated_media_items.append(item)
                logging.debug(f"Updated media item: {item}")

                pbar.update(1)

        logging.info(f"Copied {len(updated_media_items)} media items to the batch folder.")
        return updated_media_items
    except Exception as e:
        logging.error(f"Error copying media items: {e}", exc_info=True)
        sys.exit(1)