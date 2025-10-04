import logging


def get_logger(log_file="logs/log.log"):
    logger = logging.getLogger("orderbook")
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger
