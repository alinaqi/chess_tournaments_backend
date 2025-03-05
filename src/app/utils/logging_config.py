import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging():
    """
    Configure logging for the application.
    
    Uses LOG_LEVEL from environment variables, defaults to INFO.
    """
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("chess_crawler.log")
        ]
    )
    
    # Set level for specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level_name}") 