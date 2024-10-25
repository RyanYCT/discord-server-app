import json
import pathlib
from datetime import datetime

import pandas as pd
import requests


def scraper(url, payload):
    """
    Scrapes data from the BDO Market API.

    As the project is not finished, this is a simple scraper for minimum viable product (MVP).

    Parameters
    ----------
    url : string
        The url of the API endpoint
    payload : dict
        The payload for the API request

    Returns
    -------
    data : dict
        The data returned by the API
    """
    # Request data
    response = requests.get(url=url, params=payload)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")

    data = response.json()

    return data

def scrape_helper(endpoint, **kwargs):
    """
    Parse arguments and handle input and output for the scraper function.

    Parameters
    ----------
    endpoint : string
        The endpoint of the API, by default "sub" to get the sub category 1 of the main category 20 (accessory)
    region : string
        The region of the game server, by default "tw"
    lang : string
        The language of the item data, by default "en"
    mainCategory : string
        The main category of the item, by default "20" (accessory)
    subCategory : string
        The sub category of the item, by default "1"
    id : int
        The id of the item, by default 12094 (Deboreka Ring's id)
    ids : list
        The list of item ids, by default [11653, 11882, 12094, 12276] (Deboreka series)
    sid : int
        The sub id of the item, by default 0 (enhancement level)

    Returns
    -------
    pathlib.Path
        The path to the output JSON file
    """
    # Read the target list
    list_path = pathlib.Path(__file__).cwd() / "MonitoringList" / "list.json"
    monitoring_df = pd.read_json(list_path)
    id_list = monitoring_df["id"]

    # Parse arguments
    payload = None
    lang = "en"
    mainCategory = kwargs.get("mainCategory", "20")
    subCategory = kwargs.get("subCategory", "1")
    id = kwargs.get("id", 12094)
    ids = kwargs.get("ids", [11653, 11882, 12094, 12276])
    sid = kwargs.get("sid", 0)

    data_category = None
    payload = {}
    match endpoint:
        case "sub" | "WorldMarketSubList" | "/GetWorldMarketSubList":
            endpoint = "/GetWorldMarketSubList"
            data_category = "WorldMarketSubList"
            payload = {"id": id_list, "lang": lang}

        case "wait" | "WorldMarketWaitList" | "/GetWorldMarketWaitList":
            endpoint = "/GetWorldMarketWaitList"
            data_category = "WorldMarketWaitList"
            payload = None
        case "hot" | "WorldMarketHotList" | "/GetWorldMarketHotList":
            endpoint = "/GetWorldMarketHotList"
            data_category = "WorldMarketHotList"
            payload = None
        case "list" | "WorldMarketList" | "/GetWorldMarketList":
            endpoint = "/GetWorldMarketList"
            data_category = "WorldMarketList"
            payload = {"mainCategory": mainCategory, "subCategory": subCategory}
        case "search" | "WorldMarketSearchList" | "/GetWorldMarketSearchList":
            endpoint = "/GetWorldMarketSearchList"
            data_category = "WorldMarketSearchList"
            payload = {"ids": ids}
        case "bidding" | "BiddingInfoList" | "/GetBiddingInfoList":
            endpoint = "/GetBiddingInfoList"
            data_category = "BiddingInfoList"
            payload = {"id": id, "sid": sid}
        case "price" | "MarketPriceInfo" | "/GetMarketPriceInfo":
            endpoint = "/GetMarketPriceInfo"
            data_category = "MarketPriceInfo"
            payload = {"id": id, "sid": sid}
        case _:
            endpoint = "/GetWorldMarketSubList"
            data_category = "WorldMarketSubList"
            payload = {"id": id_list, "lang": lang}

    region = "tw"
    url = f"https://api.arsha.io/v2/{region}"
    url += endpoint

    # Create directory structure
    timestamp = datetime.now()
    year = timestamp.strftime("%Y")
    month = timestamp.strftime("%m")
    day = timestamp.strftime("%d")
    hour = timestamp.strftime("%H")
    output_dir = pathlib.Path(__file__).cwd() / "data" / data_category / year / month / day
    output_dir.mkdir(parents=True, exist_ok=True)

    # Scrape data
    data = scraper(url=url, payload=payload)


    # Output data
    file_name = f"{hour}.json"
    output_path = output_dir / file_name
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return output_path


if __name__ == "__main__":
    endpoint = "sub"
    print(scrape_helper(endpoint))
