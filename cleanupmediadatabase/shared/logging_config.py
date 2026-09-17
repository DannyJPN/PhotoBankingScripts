import logging
import colorlog
import json
import os


def setup_logging(debug: bool = False, log_file: str = "logs/logfile.log") -> None:
    """
    Configure console and file logging with color support.
    """
    try:
        config_path = os.path.join(os.path.dirname(__file__), "log_colors.json")
        with open(config_path, "r", encoding="utf-8") as config_file:
            color_config = json.load(config_file)
    except Exception as exc:
        logging.error("Failed to load color configuration: %s", exc, exc_info=True)
        raise

    level = logging.DEBUG if debug else logging.INFO
    log_format = "%(log_color)s%(levelname)s: %(message)s"
    formatter = colorlog.ColoredFormatter(
        log_format,
        log_colors={
            "DEBUG": color_config["DEBUG"],
            "INFO": color_config["INFO"],
            "WARNING": color_config["WARNING"],
            "ERROR": color_config["ERROR"],
            "CRITICAL": color_config["CRITICAL"],
        },
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.debug("Logging setup complete. Log file: %s", log_file)
