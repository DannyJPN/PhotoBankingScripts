import logging
import colorlog
import os
from datetime import datetime

def setup_logging():
    log_filename = f"H:/Logs/export_prepared_media_Log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.INFO)

    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'INFO': 'bold_green',
        }
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger

if __name__ == "__main__":
    logger = setup_logging()
    logger.info("ExportPreparedMedia script launched.")