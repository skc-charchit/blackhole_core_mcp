"""
Logging utility for the Blackhole Core project.
This module provides a centralized logging configuration for the entire project.
"""

import os
import sys
import logging
import platform
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Define log file path with timestamp
log_file = os.path.join(logs_dir, f'blackhole_{datetime.now().strftime("%Y%m%d")}.log')

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Determine if we can use UTF-8 in console output
use_utf8 = True
if platform.system() == 'Windows':
    # Windows console might have issues with UTF-8
    use_utf8 = False

# Create console handler with appropriate encoding
if use_utf8:
    console_handler = logging.StreamHandler(sys.stdout)
else:
    # For Windows, use a custom handler that avoids emoji characters
    class ASCIIStreamHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                msg = self.format(record)
                # Replace emoji characters with ASCII equivalents
                msg = msg.replace('✅', '[SUCCESS]')
                msg = msg.replace('❌', '[ERROR]')
                msg = msg.replace('⚠️', '[WARNING]')
                stream = self.stream
                stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

    console_handler = ASCIIStreamHandler(sys.stdout)

console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
console_handler.setFormatter(console_format)

# Create file handler
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'  # Explicitly set UTF-8 encoding for log files
)
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(file_format)

# Add handlers to root logger
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

def get_logger(name):
    """
    Get a logger with the specified name.

    Args:
        name (str): The name of the logger, typically __name__ of the calling module.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    return logger

# Example usage
if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    print(f"Log file created at: {log_file}")
