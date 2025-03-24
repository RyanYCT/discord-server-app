import os

from dotenv import load_dotenv

load_dotenv()


DATABASE_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

ENDPOINTS = {
    "list": "GetWorldMarketList",
    "sub": "GetWorldMarketSubList",
    "bid": "GetBiddingInfoList",
    "price": "GetMarketPriceInfo",
}

SCRAPE_TABLES = {
    "list": "marketlist",
    "sub": "marketsublist",
    "bid": "biddinginfo",
    "price": "priceinfo",
}

ALLOWED_TABLES = set(SCRAPE_TABLES.values())

ALLOWED_FIELDS = {"scrapetime", "name", "id", "sid", "currentstock", "lastsoldprice"}

REPORT_TABLES = {
    "profit": "profitabilityreport",
    # "trend": "trendsreport",
}

REPORT_TABLES_MAPPING = {
    "profit": "marketsublist",
}
