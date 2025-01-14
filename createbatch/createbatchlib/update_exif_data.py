import os
import subprocess
import logging
import sys
from tqdm import tqdm

def load_extensions(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file]
    except Exception as e:
        logging.error(f"Error loading extensions from {file_path}: {e}", exc_info=True)
        sys.exit(1)

def update_exif_data(media_items, exif_tool_folder):
    try:
        image_extensions = load_extensions(os.path.join(os.path.dirname(__file__), 'image_extensions.txt'))
        video_extensions = load_extensions(os.path.join(os.path.dirname(__file__), 'video_extensions.txt'))
        illustration_extensions = load_extensions(os.path.join(os.path.dirname(__file__), 'illustration_extensions.txt'))

        exif_tool_path = os.path.join(exif_tool_folder, "exiftool-12.30", "exiftool.exe")

        total_items = len(media_items)

        with tqdm(total=total_items, desc="Processing files", unit="file") as pbar:
            for item in media_items:
                try:
                    file_path = item['Cesta']
                    if not file_path.lower().endswith(tuple(image_extensions + video_extensions + illustration_extensions)):
                        logging.warning(f"Skipping unsupported file type: {file_path}")
                        pbar.update(1)
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

                    logging.debug(f"ExifTool output: {result.stdout}")
                    logging.debug(f"ExifTool errors: {result.stderr}")

                    result.check_returncode()
                    logging.debug(f"Updated EXIF data for {file_path}")
                except Exception as e:
                    logging.error(f"Error updating EXIF data for {file_path}: {e}", exc_info=True)
                finally:
                    pbar.update(1)

        logging.info(f"Updated EXIF data for {total_items} media items.")
    except Exception as e:
        logging.error(f"Error updating EXIF data: {e}", exc_info=True)
        sys.exit(1)