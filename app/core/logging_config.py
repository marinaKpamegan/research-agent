import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def setup_logging():
    """
    Configure logging to both console and a daily rotating file.
    Logs are stored in the 'logs/' directory at the project root.
    """
    # Get project root (assuming this file is in app/core/)
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    
    # Create logs directory if it doesn't exist
    if not log_dir.exists():
        os.makedirs(log_dir)
        
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"app_{current_date}.log"
    
    # Define format
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers if any (to avoid duplicates during reload)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # Timed Rotating File Handler (Daily rotation)
    file_handler = TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        interval=1,
        backupCount=30,  # Keep logs for 30 days
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    logging.info("Logging initialized: console and daily rotation file (logs/app.log)")
