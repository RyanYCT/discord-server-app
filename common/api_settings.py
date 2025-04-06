import os

from .base_settings import *

# API logging configuration
API_LOGGING_CONFIG = BASE_LOGGING_CONFIG.copy()
API_LOGGING_CONFIG.update(
    {
        "handlers": {
            **BASE_LOGGING_CONFIG["handlers"],
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "default",
                "filename": os.path.join(LOG_DIR, "api.log"),
                "mode": "a",
            },
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            },
        },
        "loggers": {
            "flask": {
                "level": "INFO",
                "handlers": ["console", "file", "wsgi"],
            },
            "werkzeug": {
                "level": "INFO",
                "handlers": ["console", "file", "wsgi"],
            },
            "analyzer": {
                "level": "INFO",
                "handlers": ["console", "file"],
            },
            "scraper": {
                "level": "INFO",
                "handlers": ["console", "file"],
            },
        },
    }
)

ALLOWED_REPORTS = {
    "profit": "report_profitability",
}
