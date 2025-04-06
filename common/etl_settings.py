import os

from .base_settings import *

# ETL configuration
# External API configuration
BASE_URL = os.getenv("BASE_URL", "https://api.arsha.io/v2")
REGION = os.getenv("REGION", "na")
LANGUAGE = os.getenv("LANGUAGE", "en")

# Endpoint key and actual endpoint mapping
ENDPOINTS = {
    # "list": "GetWorldMarketList",
    "sub": "GetWorldMarketSubList",
    # "bid": "GetBiddingInfoList",
    # "price": "GetMarketPriceInfo",
}

# Endpoint key and table name mapping
SCRAPE_TABLES = {
    "list": "scraped_marketlist",
    "sub": "scraped_marketsublist",
    "bid": "scraped_biddinginfo",
    "price": "scraped_priceinfo",
}

# Report type and output table name mapping
REPORT_TABLES = {
    "profit": "report_profitability",
}


# Report type and data source table name mapping
REPORT_DATA_SOURCE = {
    "profit": "scraped_marketsublist",
    "trend": "scraped_marketsublist",
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
        "loggers": {
            "scraper": {
                "level": "INFO",
                "handlers": ["console", "file"],
            }
        },
    }
)
