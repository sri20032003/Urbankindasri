"""
Structured logging configuration for Urbankinda.
Provides JSON logging for easy parsing and monitoring.
"""

import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from config import LOG_LEVEL, LOGS_DIR, DEBUG

# Create logs directory
LOGS_DIR.mkdir(exist_ok=True, parents=True)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(getattr(logging, LOG_LEVEL))

# JSON formatter for structured logging
json_formatter = jsonlogger.JsonFormatter(
    fmt='%(timestamp)s %(level)s %(name)s %(message)s'
)

# Console handler (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(getattr(logging, LOG_LEVEL))
console_handler.setFormatter(json_formatter)
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler(
    LOGS_DIR / 'urbankinda.log',
    mode='a'
)
file_handler.setLevel(getattr(logging, LOG_LEVEL))
file_handler.setFormatter(json_formatter)
logger.addHandler(file_handler)

# Error file handler
error_handler = logging.FileHandler(
    LOGS_DIR / 'urbankinda_errors.log',
    mode='a'
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(json_formatter)
logger.addHandler(error_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
