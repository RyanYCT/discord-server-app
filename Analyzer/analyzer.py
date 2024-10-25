import json
import pathlib
from datetime import datetime

import pandas as pd


def cal_stat(df, sid, merchant=False):
    if sid == 0:
        stat = {
            "cost": 0, 
            "profit": 0, 
            "rate": 0, 
        }
        return stat
    if merchant:
        after_tax = 0.88725
    else:
        after_tax = 0.85475
    # Current enhance level lastSoldPrice
    current_lv = sid
    current_lv_price = df["lastSoldPrice"].iloc[current_lv]
    # Previous enhance level lastSoldPrice
    previous_lv = current_lv - 1
    previous_lv_price = df["lastSoldPrice"].iloc[previous_lv]
    # Clean enhance level lastSoldPrice
    clean_price = df["lastSoldPrice"].iloc[0]

    # Calculate cost
    cost = previous_lv_price + clean_price
    # Calculate profit
    profit = (current_lv_price - cost) * after_tax
    # Calculate rate of return
    rate_of_return = 1 + (profit / cost)

    stat = {
        "cost": cost, 
        "profit": profit, 
        "rate": rate_of_return, 
    }
    return stat

def overall_analyzer(json_data):
    """
    Produce overall performance report.

    Parameters
    ----------
    json_data : list
        The list of json data from the API response.

    Returns
    -------
    list
        The list of dictionaries containing the overall performance report.
    """
    # Data flattening
    flattened_data = [dict(item) for sublist in json_data for item in sublist]

    # Data ingestion
    raw_df = pd.json_normalize(flattened_data)

    # Datetime parsing
    raw_df["lastSoldTime"] = pd.to_datetime(raw_df["lastSoldTime"], unit="s")

    # Feature Engineering
    df = pd.DataFrame(columns=["name", "enhance", "price", "profit", "rate", "stock"])
    for i in range(raw_df.shape[0]):
        stat = cal_stat(raw_df, i)
        profit = stat["profit"]
        rate = stat["rate"]
        row = [[raw_df.iloc[i]["name"], raw_df.iloc[i]["sid"], raw_df.iloc[i]["lastSoldPrice"], profit, rate, raw_df.iloc[i]["currentStock"]]]
        df = pd.concat([pd.DataFrame(row, columns=df.columns), df], ignore_index=True)
    df["profit"] = df["profit"].astype(int)
    # df.style.format(thousands=",", precision=3)

    # Sort by rate of return
    df.sort_values(by=["rate"], ascending=False, inplace=True)
    output_df = df.to_dict(orient="records")

    return output_df

def analyze_helper(endpoint):
    """
    Parse argument and handle input and output for the analyzer function.

    Parameters
    ----------
    endpoint : str
        The endpoint of the API request.
    file_name : str
        The file_name of the data file.

    Returns
    -------
    pathlib.Path
        The path of the output report.
    """
    # Parse argument
    report_type = None
    data_category = None
    match endpoint:
        case "sub" | "WorldMarketSubList" | "/GetWorldMarketSubList":
            report_type = "overall"
            data_category = "WorldMarketSubList"
        case _:
            report_type = "overall"
            data_category = "WorldMarketSubList"

    # Read file
    timestamp = datetime.now()
    year = timestamp.strftime("%Y")
    month = timestamp.strftime("%m")
    day = timestamp.strftime("%d")
    hour = timestamp.strftime("%H")
    file_name = f"{hour}.json"
    file_path = pathlib.Path(__file__).cwd() / "data" / data_category / year / month / day / file_name
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.loads(file_path.read_text())

    # Process data
    output_df = overall_analyzer(json_data)

    # Create directory structure
    output_dir = pathlib.Path(__file__).cwd() / "report" / report_type / year / month / day
    output_dir.mkdir(parents=True, exist_ok=True)

    # Output report
    file_name = f"{hour}.json"
    output_path = output_dir / file_name
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_df, f, ensure_ascii=False, indent=4)

    return output_path

if __name__ == "__main__":
    endpoint = "sub"
    print(analyze_helper(endpoint))
