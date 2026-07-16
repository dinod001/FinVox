import sys
from loguru import logger

def setup_logger():
    """Configure loguru with beautiful colored outputs."""
    # Remove the default logger
    logger.remove()

    # Define a colorful format
    # - Time in green
    # - Level in its default color (Red for ERROR, Green for SUCCESS, etc.)
    # - Module/Function in cyan
    # - Message in level color
    custom_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Add console logger
    logger.add(
        sys.stdout,
        format=custom_format,
        level="INFO",
        colorize=True,
    )

    # Optionally add a file logger to save errors
    logger.add(
        "logs/error.log",
        format=custom_format,
        level="ERROR",
        rotation="10 MB",
        retention="1 week"
    )

    return logger

# Initialize the logger to be imported across the project
log = setup_logger()
