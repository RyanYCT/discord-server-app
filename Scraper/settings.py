import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


DATABASE_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

BASE_URL = "https://api.arsha.io/v2"
REGION = "tw"
LANGUAGE = "en"

ENDPOINTS = {
    "list": "GetWorldMarketList",
    "sub": "GetWorldMarketSubList",
    "bid": "GetBiddingInfoList",
    "price": "GetMarketPriceInfo",
}
