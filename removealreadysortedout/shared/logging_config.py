import logging
import colorlog
import json
import os
import sys

def setup_logging(debug=False, log_file="logs/logfile.log"):
    # Load color configuration from the JSON file
    try:
        with open(os.path.join(os.path.dirname(sys.argv[0]), 'shared/log_colors.json'), 'r') as f:
            color_config = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load color configuration: {e}", exc_info=True)
        raise

    # Set logging level based on the debug flag
    level = logging.DEBUG if debug else logging.INFO

    # Define a formatter using colorlog with a custom color scheme from the JSON
    log_format = '%(log_color)s%(levelname)s: %(message)s'
    formatter = colorlog.ColoredFormatter(
        log_format,
        log_colors={
            'DEBUG': color_config["DEBUG"],
            'INFO': color_config["INFO"],
            'WARNING': color_config["WARNING"],
            'ERROR': color_config["ERROR"],
            'CRITICAL': color_config["CRITICAL"],
        }
    )

    # Set up the console handler with the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Set up the file handler with the formatter
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Get the root logger
    root_logger = logging.getLogger()

    # Remove any existing handlers from the root logger
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add both handlers to the root logger
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.debug(f"Logging setup complete. Log file: {log_file}")