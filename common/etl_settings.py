import os

from .base_settings import *

# ETL configuration
# External API configuration
BASE_URL = os.getenv("BASE_URL", "https://api.arsha.io/v2")
REGION = os.getenv("REGION", "na")
LANGUAGE = os.getenv("LANGUAGE", "en")

ENDPOINTS = {
    # "list": "GetWorldMarketList",
    "sub": "GetWorldMarketSubList",
    # "bid": "GetBiddingInfoList",
    # "price": "GetMarketPriceInfo",
}

SCRAPE_TABLES = {
    "list": "marketlist",
    "sub": "marketsublist",
    "bid": "biddinginfo",
    "price": "priceinfo",
}

REPORT_TABLES = {
    "profit": "profitabilityreport",
    # "trend": "trendsreport",
}

REPORT_DATA_SOURCE = {
    "profit": "marketsublist",
}

# Logging configuration
ETL_LOGGING_CONFIG = BASE_LOGGING_CONFIG.copy()
ETL_LOGGING_CONFIG.update(
    {
        "handlers": {
            **BASE_LOGGING_CONFIG["handlers"],
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "default",
                "filename": os.path.join(LOG_DIR, "etl.log"),
                "mode": "a",
            },
        },
    }
)
