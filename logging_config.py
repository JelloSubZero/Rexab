import logging

from config import LOG_LEVEL, LOGS_DIR


def setup_logging() -> None:
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                LOGS_DIR / "rexab.log",
                encoding="utf-8",
            ),
        ],
    )
