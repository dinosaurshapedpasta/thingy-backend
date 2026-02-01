import logging
import sys


def setup_logging():
    """Configure application-wide logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("thingy-backend")


logger = setup_logging()
