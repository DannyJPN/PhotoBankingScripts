import logging
from tqdm import tqdm
from markmediaascheckedlib.constants import STATUS_READY, STATUS_CHECKED

def mark_files_as_checked(csv_data):
    try:
        logging.info("Starting to mark files as checked")
        with tqdm(csv_data, desc="Processing CSV Rows") as progress_bar:
            for row in progress_bar:
                for key, value in row.items():
                    if value == STATUS_READY:
                        row[key] = STATUS_CHECKED
                        logging.debug(f"Replaced {STATUS_READY} with {STATUS_CHECKED} in row {row}")
        logging.info("Completed marking files as checked")
        return csv_data
    except Exception as e:
        logging.error(f"An error occurred while marking files as checked: {e}", exc_info=True)
        raise