import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Shared configurations
ROOT_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

# Logging configuration
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

BASE_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}
