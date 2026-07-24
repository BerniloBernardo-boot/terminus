"""
utils/logger.py — Session logger.
"""

import logging
import json
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "logs"


def get_logger(name: str = "terminus") -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_DIR / f"{datetime.now():%Y-%m-%d}.log")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(fh)
    return logger


def log_interaction(user_input: str, response: dict):
    get_logger().info(json.dumps({
        "input":  user_input,
        "module": response.get("_module", ""),
        "type":   response.get("type", ""),
        "source": response.get("_source", "local"),
    }, ensure_ascii=False))
