# utils/logger.py
import os
import logging
from rich.logging import RichHandler
from datetime import datetime
from utils.console import console

def get_logging():

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) 
    
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    console_handler = RichHandler(
        show_time=False,
        show_level=True,
        show_path=True, 
        console=console,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d")
    full_log_path = os.path.join(log_dir, f"global_{timestamp}.log")

    file_handler = logging.FileHandler(full_log_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger