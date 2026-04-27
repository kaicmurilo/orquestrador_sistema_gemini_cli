import logging
from datetime import datetime
from pathlib import Path


def get_logger(agent_name: str, logs_dir: str = "logs") -> logging.Logger:
    Path(logs_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(logs_dir) / f"{agent_name}_{timestamp}.log"

    logger = logging.getLogger(f"{agent_name}_{timestamp}")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
