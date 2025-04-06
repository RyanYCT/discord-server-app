import json
import logging
from datetime import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional, Union

import psycopg2
import requests
from psycopg2 import sql
from psycopg2.extras import execute_batch

from common import etl_settings

logger = logging.getLogger("scraper")


class ScraperError(Exception):
    pass


class APIError(ScraperError):
    pass


class DatabaseError(ScraperError):
    pass


class ValidationError(ScraperError):
    pass


def load_item_list() -> Dict[str, Union[List[int], int]]:
    logger.info("Loading item list")
    try:
        # Locate the JSON file, assuming the JSON file is in the same directory
        current_dir = Path(__file__).resolve().parent
        json_path = current_dir / "item_list.json"
        with open(json_path, "r") as file:
            item_list = json.load(file)

        # Deduplicate item id for each category
        changes_made = False
        for category, ids in item_list.items():
            if isinstance(ids, list):
                # Deduplicates by converting to set and back to list
                deduplicated_ids = sorted(list(set(ids)))
                # If any duplicates be removed
                if len(deduplicated_ids) != len(ids):
                    logger.info(f"Deduplicated '{len(ids) - len(deduplicated_ids)}' item ids")
                    changes_made = True
                item_list[category] = deduplicated_ids
            else:
                item_list[category] = ids

        # Update the JSON file if duplicates removed
        if changes_made:
            with open(json_path, "w") as file:
                json.dump(item_list, file, indent=4)
            logger.info("Successfully deduplicate and update item list")

        if not item_list:
            raise ValueError("Item list is empty")
        return item_list

    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {json_path}")


def get_item_id(item_name: str = "all") -> List[int]:
    """Get item id from item list"""
    logger.info(f"Getting item id for '{item_name}'")
    item_list = load_item_list()
    # Item id mapping
    item_id = item_list.get(item_name, None)
    if item_id is None:
        raise ValueError(f"Invalid item name: {item_name}")
    logger.debug(f"{item_id=}")
    return item_id


def get_item_category(item_list: list, item_id: int) -> str:
    """Determine category of an item based on classification"""
    # Check if item id is in any game shop item categories
    if item_id in item_list["buff"]:
        return "buff"
    elif item_id in item_list["costume"]:
        return "costume"
    elif item_id in item_list["accessory"]:
        return "accessory"
    return "unknown"


def get_endpoint(endpoint_key: str) -> str:
    """Endpoint mapping"""
    logger.info(f"Getting endpoint for '{endpoint_key}'")
    endpoint = etl_settings.ENDPOINTS.get(endpoint_key, None)
    if endpoint is None:
        raise ValueError(f"Invalid endpoint key: {endpoint_key}")
    logger.debug(f"{endpoint=}")
    return endpoint


def get_table_name(endpoint_key: str) -> str:
    """Table name mapping"""
    logger.info(f"Getting table name for '{endpoint_key}'")
    table_name = etl_settings.SCRAPE_TABLES.get(endpoint_key, None)
    if table_name is None:
        raise ValueError(f"Invalid endpoint key: {endpoint_key}")
    logger.debug(f"{table_name=}")
    return table_name


def get_payload(endpoint: str, **kwargs) -> Dict:
    """Validate kwargs and construct payload based on endpoint"""
    logger.info(f"Getting payload for '{endpoint}' with '{kwargs}'")
    # Validate kwargs (payload) based on endpoint
    if endpoint == "list":
        if kwargs.get("mainCategory") is None:
            raise ValueError(f"mainCategory is required for '{endpoint}'")
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
    logger.debug(f"{payload=}")
    return payload


def construct_url(endpoint: str) -> str:
    """Construct API URL based on endpoint"""
    url = f"{etl_settings.BASE_URL}/{etl_settings.REGION}/{endpoint}"
    logger.debug(f"{url=}")
    return url


def fetch_data(url: str, payload: Dict) -> Optional[List[Dict]]:
    """
    Fetch data from the API endpoint.

    Parameters
    ----------
    url : str
        API endpoint URL
    payload : dict
        Query parameters for the API request

    Returns
    -------
    list of dict or None
        List of dictionaries containing item data if successful,
        None if no data is returned

    Raises
    ------
    APIError
        If API request fails or returns invalid data
    """
    logger.info(f"Fetching data from '{url}' with '{payload}'")
    current_time = dt.now()
    scrape_time = current_time.replace(minute=0, second=0, microsecond=0)

    try:
        response = requests.get(url, params=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data:
            raise APIError("Empty response from API")

        flattened_data = []
        for sublist in data:
            for item in sublist:
                flattened_data.append(item)

        # Add timestamp, category, and convert lastSoldTime to datetime
        item_list = load_item_list()
        for i in range(len(flattened_data)):
            flattened_data[i]["scrapeTime"] = scrape_time
            flattened_data[i]["category"] = get_item_category(item_list, flattened_data[i]["id"])
            flattened_data[i]["lastSoldTime"] = dt.fromtimestamp(flattened_data[i]["lastSoldTime"])

        logger.debug(f"{len(flattened_data)=}")
        return flattened_data

    except requests.exceptions.HTTPError as httpe:
        logger.error(f"HTTP error: {httpe}")
        raise APIError(f"HTTP error: {httpe}")
    except requests.exceptions.RequestException as rqe:
        logger.error(f"Request error: {rqe}")
        raise APIError(f"Request failed: {rqe}")
    except ValueError as ve:
        logger.error(f"Value error: {ve}")
        raise APIError(f"Failed to parse API response: {ve}")


def store_data(data: Dict, table_name: str) -> None:
    """
    Store scraped data in the database.

    Parameters
    ----------
    data : dict
        Data to be stored in the database
    table_name : str
        Name of the target database table

    Raises
    ------
    ValidationError
        If data or table_name is empty
    DatabaseError
        If database operation fails
    """
    logger.info(f"Storing data in '{table_name}'")
    if not data:
        logger.error("No data to store")
        raise ValidationError("No data to store")

    if not table_name:
        logger.error("No table name to store")
        raise ValidationError("No table name to store")

    try:
        with psycopg2.connect(**etl_settings.DATABASE_CONFIG) as conn:
            logger.debug("Database connection established")
            with conn.cursor() as cur:
                try:
                    # Create table if not exists
                    create_table_query = sql.SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            scrapeID SERIAL PRIMARY KEY,
                            scrapeTime TIMESTAMP,
                            category VARCHAR(16),
                            name VARCHAR(255),
                            id INT,
                            sid INT,
                            minEnhance INT,
                            maxEnhance INT,
                            basePrice BIGINT,
                            currentStock BIGINT,
                            totalTrades BIGINT,
                            priceMin BIGINT,
                            priceMax BIGINT,
                            lastSoldPrice BIGINT,
                            lastSoldTime TIMESTAMP,
                            UNIQUE (scrapeTime, id, sid)
                        )
                        """
                    ).format(table_name=sql.Identifier(table_name))
                    cur.execute(create_table_query)

                    # Batch insert
                    # Prepare for batch insert
                    insert_query = sql.SQL(
                        """
                        INSERT INTO {table_name} (
                            scrapeTime, category, name, id, sid, minEnhance, 
                            maxEnhance, basePrice, currentStock, 
                            totalTrades, priceMin, priceMax, 
                            lastSoldPrice, lastSoldTime
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s
                        )
                        """
                    ).format(table_name=sql.Identifier(table_name))

                    # Prepare records for batch insert
                    records = []
                    for item in data:
                        records.append(
                            (
                                item["scrapeTime"],
                                item["category"],
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
                        )

                    execute_batch(cur, insert_query, records)
                    conn.commit()
                    logger.info(f"Successfully stored '{len(data)}' records in '{table_name}'")

                except psycopg2.Error as dbe:
                    logger.info(f"Roll back transaction")
                    conn.rollback()
                    logger.error(f"Database operation error: {dbe}")
                    raise DatabaseError(f"Database operation failed: {dbe}")

    except psycopg2.Error as dbe:
        logger.error(f"Database connection error: {dbe}")
        raise DatabaseError(f"Database connection error: {dbe}")


def scraper(endpoint_key: str, **kwargs) -> None:
    logger.debug(f"scraper({endpoint_key=}, {kwargs=})")
    try:
        endpoint = get_endpoint(endpoint_key)
        # Ensure the kwargs contain item name
        item_id = get_item_id(kwargs["item_name"])
        payload = get_payload(endpoint, id=item_id)
        url = construct_url(endpoint)
        data = fetch_data(url, payload)
        table_name = get_table_name(endpoint_key)
        store_data(data, table_name)

    except (ValidationError, DatabaseError, APIError, ScraperError) as e:
        logger.error(f"Scraper error: {e}")
