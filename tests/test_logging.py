import sys
import os
from pathlib import Path

# Add app directory to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.core.logging_config import setup_logging
import logging

def test_logging():
    print("Testing logging setup...")
    setup_logging()
    
    logger = logging.getLogger("test_logger")
    logger.info("This is a test log message.")
    logger.error("This is a test error message.")
    
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_dir = project_root / "logs"
    log_file = log_dir / f"app_{current_date}.log"
    
    if log_dir.exists() and log_dir.is_dir():
        print(f"✅ Success: 'logs/' directory exists.")
    else:
        print(f"❌ Failure: 'logs/' directory does not exist.")
        return

    if log_file.exists():
        print(f"✅ Success: 'logs/app.log' exists.")
        with open(log_file, "r") as f:
            content = f.read()
            if "This is a test log message." in content:
                print(f"✅ Success: Log message found in file.")
            else:
                print(f"❌ Failure: Log message NOT found in file.")
    else:
        print(f"❌ Failure: 'logs/app.log' does not exist.")

if __name__ == "__main__":
    test_logging()
