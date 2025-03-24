import logging
from pathlib import Path
from typing import Dict

import pandas as pd
import requests

import common.base_settings as base_settings

logger = logging.getLogger(__name__)


class ScraperError(Exception):
    pass


class APIError(ScraperError):
    pass


class ValidationError(ScraperError):
    pass


def construct_url(endpoint: str) -> str:
    """Construct API URL based on endpoint"""
    url = f"{base_settings.BASE_URL}/{base_settings.REGION}/{endpoint}"
    logging.debug(f"{url=}")
    return url


def fetch_data(url: str, payload: Dict) -> pd.DataFrame:
    try:
        logging.info("Fetching data from API")
        response = requests.get(url, params=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data:
            raise APIError("Empty response from API")

        df = pd.DataFrame(data)
        logging.debug(f"{df.shape=}")
        return df

    except requests.RequestException as e:
        raise requests.RequestException(f"Error fetching data: {str(e)}")
    except ValueError as e:
        raise ValueError(f"Error parsing JSON data: {str(e)}")


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    try:
        logging.info("Cleaning data")
        # Drop the unnecessary columns
        df = df.drop(columns=["currentStock", "totalTrades", "basePrice"], axis=1)
        df = df.reset_index(drop=True)
        logging.debug(f"{df.head()=}")
        return df

    except Exception as e:
        raise ScraperError(f"Error cleaning data: {str(e)}")


def store_data(df: pd.DataFrame, file_name: str) -> None:
    try:
        logging.info("Storing data")
        df = df.drop_duplicates(subset=["id"])

        logging.debug(f"{df.shape=}")
        df.to_json(file_name, orient="records", indent=4)
        logging.info(f"Data stored in {file_name}")

    except Exception as e:
        raise ScraperError(f"Error storing data: {str(e)}")


def scraper(file_name: str) -> None:
    script_dir = Path(__file__).parent
    output_file = script_dir / file_name
    try:
        endpoint = "GetWorldMarketList"
        url = construct_url(endpoint)

        # loop fetch data for each mainCategory
        mainCategories = [i for i in range(0, 86, 5)]
        mainCategories[0] = 1

        item_df_list = []
        for cat in mainCategories:
            payload = {"mainCategory": cat}
            raw_df = fetch_data(url, payload)
            cleaned_df = clean_data(raw_df)
            item_df_list.append(cleaned_df)

        item_list = pd.concat(item_df_list, ignore_index=True)

        store_data(item_list, output_file)

    except (ValidationError, APIError, ScraperError) as e:
        print(f"Scraper error: {e}")
        raise ScraperError(f"Scraper error: {e}")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    file_name = "full_item_list.json"
    scraper(file_name)
