import os
import sys
import logging
import colorlog
from datetime import datetime
import argparse
import pandas as pd
import shutil
from tqdm import tqdm
import subprocess

# Function to setup logging
def setup_logging(log_filename, log_level):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.FileHandler(log_filename)
    handler.setLevel(log_level)

    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG': 'bold_white',
            'INFO': 'bold_green',
            'WARNING': 'bold_yellow',
            'ERROR': 'bold_red',
            'CRITICAL': 'bold_purple',
        }
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger

# Function to ensure necessary directories exist
def ensure_directories(processed_media_folder, log_dir):
    try:
        if not os.path.exists(processed_media_folder):
            os.makedirs(processed_media_folder)
            logging.info(f"Created directory: {processed_media_folder}")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logging.info(f"Created directory: {log_dir}")
    except Exception as e:
        logging.error(f"Error ensuring directories: {e}", exc_info=True)
        sys.exit(1)

# Function to load CSV file
def load_csv(filepath):
    try:
        # Load CSV with na_filter=False to prevent NaN values
        df = pd.read_csv(filepath, na_filter=False)
        logging.info(f"CSV file loaded successfully: {filepath}")
        media_items = df.to_dict(orient='records')

        # Log first few media items for verification
        logging.debug(f"First few media items: {media_items[:5]}")

        return media_items
    except Exception as e:
        logging.error(f"Error loading CSV file: {e}", exc_info=True)
        sys.exit(1)

# Define constant for 'připraveno' status
PREPARED_STATUS = 'připraveno'

# Function to get prepared media items
def get_prepared_media_items(media_items):
    try:
        prepared_media_items = []
        for item in media_items:
            logging.debug(f"Checking media item: {item}")
            item_prepared = False  # Flag to check if the item is prepared
            for key, value in item.items():
                logging.debug(f"Checking property: {key} with value: {value}")
                if 'status' in key.lower() and value.lower() == PREPARED_STATUS:
                    item_prepared = True
            if item_prepared:
                prepared_media_items.append(item)
                logging.debug(f"Added media item to prepared list: {item}")
        logging.info(f"Filtered {len(prepared_media_items)} prepared media items.")
        return prepared_media_items
    except Exception as e:
        logging.error(f"Error filtering prepared media items: {e}", exc_info=True)
        sys.exit(1)

# Function to copy media items to batch folder and update paths
def copy_media_items_to_batch(media_items, processed_media_folder):
    try:
        updated_media_items = []
        total_items = len(media_items)

        for index, item in enumerate(tqdm(media_items, desc="Copying media items", unit="item")):
            logging.debug(f"Processing media item {index + 1}/{total_items}: {item}")
            source_path = item['Cesta']
            destination_path = os.path.join(processed_media_folder, os.path.basename(source_path))

            if not os.path.exists(destination_path):
                # Log file metadata before copying
                try:
                    source_metadata = os.stat(source_path)
                    logging.debug(f"Source file metadata before copy - {source_path}: "
                                  f"Creation time: {source_metadata.st_ctime}, "
                                  f"Last modification time: {source_metadata.st_mtime}, "
                                  f"Last access time: {source_metadata.st_atime}")
                except Exception as e:
                    logging.error(f"Error retrieving source file metadata for {source_path}: {e}", exc_info=True)

                shutil.copy2(source_path, destination_path)
                logging.info(f"Copied {source_path} to {destination_path}")

                # Log file metadata after copying
                try:
                    destination_metadata = os.stat(destination_path)
                    logging.debug(f"Destination file metadata after copy - {destination_path}: "
                                  f"Creation time: {destination_metadata.st_ctime}, "
                                  f"Last modification time: {destination_metadata.st_mtime}, "
                                  f"Last access time: {destination_metadata.st_atime}")
                except Exception as e:
                    logging.error(f"Error retrieving destination file metadata for {destination_path}: {e}", exc_info=True)

                # Manually set the timestamps
                try:
                    os.utime(destination_path, (source_metadata.st_atime, source_metadata.st_mtime))
                    logging.debug(f"Manually set timestamps for {destination_path}: "
                                  f"Access time: {source_metadata.st_atime}, "
                                  f"Modification time: {source_metadata.st_mtime}")
                except Exception as e:
                    logging.error(f"Error setting timestamps for {destination_path}: {e}", exc_info=True)
            else:
                logging.info(f"File already exists at {destination_path}, skipping copy.")

            # Update the Cesta property
            item['Cesta'] = destination_path
            updated_media_items.append(item)
            logging.debug(f"Updated media item: {item}")

        logging.info(f"Copied {len(updated_media_items)} media items to the batch folder.")
        return updated_media_items
    except Exception as e:
        logging.error(f"Error copying media items: {e}", exc_info=True)
        sys.exit(1)

# Function to update EXIF data using exiftool
def update_exif_data(media_items, exif_tool_folder, debug):
    try:
        total_items = len(media_items)
        exif_tool_path = os.path.join(exif_tool_folder, "exiftool-12.30", "exiftool.exe")

        for index, item in enumerate(tqdm(media_items, desc="Updating EXIF data", unit="item")):
            try:
                file_path = item['Cesta']
                if not file_path.lower().endswith(('jpg', 'jpeg', 'png', 'tiff','tif','raw','nef','dng','psd','ai','svg', 'bmp', 'gif', 'webp', 'heic', 'mp4', 'mkv', 'mov', 'avi', 'wmv', 'flv', 'webm', 'm4v', '3gp', 'ogv', 'mpg', 'mpeg', 'mts', 'm2ts')):
                    logging.warning(f"Skipping non-image file: {file_path}")
                    continue

                nazev = item.get('Název', '')
                klicova_slova = item.get('Klíčová slova', '')
                popis = item.get('Popis', '')

                command = [
                    exif_tool_path,
                    file_path,
                    f"-filecreatedate<datetimeoriginal",
                    f"-title=\"{nazev}\"",
                    f"-keywords=\"{klicova_slova}\"",
                    f"-Description=\"{popis}\"",
                    "-sep", ","
                ]

                logging.debug(f"Executing command: {' '.join(command)}")
                result = subprocess.run(command, capture_output=True, text=True)

                if debug:
                    logging.debug(f"ExifTool output: {result.stdout}")
                    logging.debug(f"ExifTool errors: {result.stderr}")

                result.check_returncode()  # Raise an error if the command failed
                if debug:
                    logging.debug(f"Updated EXIF data for {file_path}")
            except Exception as e:
                logging.error(f"Error updating EXIF data for {file_path}: {e}", exc_info=True)

        
        logging.info(f"Updated EXIF data for {total_items} media items.")
    except Exception as e:
        logging.error(f"Error updating EXIF data: {e}", exc_info=True)
        sys.exit(1)

def main():
    # Argument parsing
    parser = argparse.ArgumentParser(description="CreateBatch Script")
    parser.add_argument("--PhotoCsvFile", type=str, default="F:/Disk Google (krupadan.jp@gmail.com)/XLS/Fotobanky/PhotoMediaTest.csv")
    parser.add_argument("--ProcessedMediaFolder", type=str, default="F:/Disk Google (krupadan.jp@gmail.com)/PhotoBankMediaTest")
    parser.add_argument("--LogFile", type=str, default=f"H:/Logs/{os.path.basename(__file__).replace('.py', '')}_Log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    parser.add_argument("--ExifToolFolder", type=str, default="F:/Dropbox/")
    parser.add_argument("--Debug", action="store_true")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.Debug else logging.INFO
    logger = setup_logging(args.LogFile, log_level)

    logger.info("Script started with the following parameters:")
    logger.info(f"PhotoCsvFile: {args.PhotoCsvFile}")
    logger.info(f"ProcessedMediaFolder: {args.ProcessedMediaFolder}")
    logger.info(f"LogFile: {args.LogFile}")
    logger.info(f"ExifToolFolder: {args.ExifToolFolder}")
    logger.info(f"Debug: {args.Debug}")
    debug = args.Debug
    # Ensure necessary directories exist
    ensure_directories(args.ProcessedMediaFolder, os.path.dirname(args.LogFile))
    logger.info("Necessary directories ensured.")

    # Load the CSV file
    media_items = load_csv(args.PhotoCsvFile)
    logger.info(f"Loaded {len(media_items)} media items from CSV.")

    # Filter prepared media items
    prepared_media_items = get_prepared_media_items(media_items)
    if debug:
        logger.debug(f"Filtered {len(prepared_media_items)} prepared media items.")

    # Copy media items to batch folder and update paths
    updated_media_items = copy_media_items_to_batch(prepared_media_items, args.ProcessedMediaFolder)
    if debug:
        logger.debug(f"Updated paths for {len(updated_media_items)} media items.")

    # Update EXIF data
    update_exif_data(updated_media_items, args.ExifToolFolder, args.Debug)
    if debug:
        logger.debug(f"Updated EXIF data for {len(updated_media_items)} media items.")

    # Prepare calls for other scripts
    scripts = ["export_prepared_media.py", "mark_media_as_checked.py", "launch_photobanks.py"]
    for script in scripts:
        try:
            script_path = os.path.join(os.path.dirname(__file__), script)
            logger.info(f"Launching script: {script_path}")
            #subprocess.run(["python", script_path], check=True)
            logger.info(f"Successfully launched script: {script_path}")
        except Exception as e:
            logger.error(f"Error launching script {script}: {e}", exc_info=True)

if __name__ == "__main__":
    main()