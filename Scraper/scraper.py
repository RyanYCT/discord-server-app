import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import psycopg2
import requests
from psycopg2.extras import execute_batch

import settings


class ScraperError(Exception):
    pass


class APIError(ScraperError):
    pass


class DatabaseError(ScraperError):
    pass


class ValidationError(ScraperError):
    pass


def load_item_list() -> Dict[str, Union[List[int], int]]:
    try:
        current_dir = Path(__file__).resolve().parent
        json_path = current_dir / "item_list.json"
        with open(json_path, "r") as file:
            item_list = json.load(file)

        if not item_list:
            raise ValueError("Item list is empty")
        return item_list

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {json_path}")


def get_item_id(item_name: str) -> List[int]:
    item_list = load_item_list()
    # Item id mapping
    item_id = item_list.get(item_name, None)
    if item_id is None:
        raise ValueError(f"Invalid item name: {item_name}")
    return item_id


def get_endpoint(endpoint_key: str) -> str:
    # Endpoint mapping
    endpoint = settings.ENDPOINTS.get(endpoint_key, None)
    if endpoint is None:
        raise ValueError(f"Invalid endpoint: {endpoint_key}")
    return endpoint


def get_table_name(endpoint_key: str) -> str:
    # Table name mapping
    table_name = settings.ENDPOINTS.get(endpoint_key, None)
    if table_name is None:
        raise ValueError(f"Invalid endpoint: {endpoint_key}")
    table_name = table_name.replace("Get", "").replace("List", "")
    return table_name


def get_payload(endpoint: str, **kwargs) -> Dict:
    # Validate kwargs (payload) based on endpoint
    if endpoint == "list":
        if kwargs.get("mainCategory") is None:
            raise ValueError(f"mainCategory is required for {endpoint}")
        # mainCategory is in range from 1 to 85
        mainCategoryRange = list(range(0, 86, 5))
        mainCategoryRange[0] = 1
        if kwargs.get("mainCategory") not in mainCategoryRange:
            raise ValueError("mainCategory should be in range from 1 to 85 step 5")

    if endpoint != "list" and kwargs.get("sid") is not None:
        # sid is in range from 0 to 20
        if kwargs.get("sid") not in range(0, 21):
            raise ValueError("sid should be in range from 0 to 20")

    payload = {}
    for key, value in kwargs.items():
        if value is not None:
            payload[key] = value
    logging.debug(f"{payload=}")
    return payload


def construct_url(endpoint: str) -> str:
    url = f"{settings.BASE_URL}/{settings.REGION}/{endpoint}"
    logging.debug(f"{url=}")
    return url


def fetch_data(url: str, payload: Dict) -> Optional[List[Dict]]:
    scrape_time = datetime.now()
    try:
        response = requests.get(url, params=payload, timeout=10)
        logging.debug(f"{response.url=}")
        logging.debug(f"{response.status_code=}")
        response.raise_for_status()

        data = response.json()
        if not data:
            raise APIError("Empty response from API")

        flattened_data = []
        for sublist in data:
            for item in sublist:
                flattened_data.append(item)

        # Add timestamp
        for i in range(len(flattened_data)):
            flattened_data[i]["scrapeTime"] = scrape_time
            flattened_data[i]["lastSoldTime"] = datetime.fromtimestamp(flattened_data[i]["lastSoldTime"])

        return flattened_data

    except requests.exceptions.HTTPError as httpe:
        logging.error(f"HTTP error: {httpe}")
        raise APIError(f"HTTP error: {httpe}")
    except requests.exceptions.RequestException as rqe:
        logging.error(f"Request error: {rqe}")
        raise APIError(f"Request failed: {rqe}")
    except ValueError as ve:
        logging.error(f"Value error: {ve}")
        raise APIError(f"Failed to parse API response: {ve}")


def store_data(data: Dict, table_name: str) -> None:
    if not data:
        logging.error("No data to store")
        raise ValidationError("No data to store")

    if not table_name:
        logging.error("No table name to store")
        raise ValidationError("No table name to store")

    try:
        with psycopg2.connect(**settings.DATABASE_CONFIG) as conn:
            logging.debug("Database connection established")
            with conn.cursor() as cur:
                try:
                    # Create table if not exists
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        scrapeTime TIMESTAMP,
                        name VARCHAR(255),
                        id INT,
                        sid INT,
                        minEnhance INT,
                        maxEnhance INT,
                        basePrice BIGINT,
                        currentStock INT,
                        totalTrades BIGINT,
                        priceMin BIGINT,
                        priceMax BIGINT,
                        lastSoldPrice BIGINT,
                        lastSoldTime TIMESTAMP
                    );
                    """
                    cur.execute(create_table_query)

                    # Prepare data for batch insert
                    insert_query = f"""
                    INSERT INTO {table_name} (
                        scrapeTime, name, id, sid, minEnhance, maxEnhance, basePrice, currentStock, totalTrades, priceMin, priceMax, lastSoldPrice, lastSoldTime
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                    records = []
                    for item in data:
                        record = (
                            item["scrapeTime"],
                            item["name"],
                            item["id"],
                            item["sid"],
                            item["minEnhance"],
                            item["maxEnhance"],
                            item["basePrice"],
                            item["currentStock"],
                            item["totalTrades"],
                            item["priceMin"],
                            item["priceMax"],
                            item["lastSoldPrice"],
                            item["lastSoldTime"],
                        )
                        records.append(record)

                    # Batch insert
                    execute_batch(cur, insert_query, records)
                    conn.commit()
                    logging.info(f"Successfully stored {len(data)} records in {table_name}")

                except psycopg2.Error as dbe:
                    logging.info(f"Roll back transaction")
                    conn.rollback()
                    logging.error(f"Database operation error: {dbe}")
                    raise DatabaseError(f"Database operation failed: {dbe}")

    except psycopg2.Error as dbe:
        logging.error(f"Database connection error: {dbe}")
        raise DatabaseError(f"Database connection error: {dbe}")


def scraper(endpoint_key: str, **kwargs):
    try:
        endpoint = get_endpoint(endpoint_key)

        if endpoint_key == "list":
            # Ensure the kwargs contain "mainCategory" or "mainCategory" & "subCategory"
            payload = get_payload(endpoint, **kwargs)

        else:
            # Ensure the kwargs contain item name
            item_id = get_item_id(kwargs["item_name"])
            payload = get_payload(endpoint, id=item_id)

        url = construct_url(endpoint)
        data = fetch_data(url, payload)
        table_name = get_table_name(endpoint_key)
        store_data(data, table_name)

    except ScraperError as se:
        logging.error(f"Scraper error: {se}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    scraper("sub", item_name="Deboreka Series")
