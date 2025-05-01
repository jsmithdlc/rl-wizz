import logging
import sys
from pathlib import Path


def setup_logger(name: str = None) -> logging.Logger:
    """
    Configure and return a logger instance for the application.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Get the logger
    logger = logging.getLogger(name)

    # Only configure if handlers haven't been set up
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_formatter = logging.Formatter("%(name)s - [%(levelname)s]: %(message)s")

        # File handler
        file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
