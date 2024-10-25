import pandas as pd
import settings


def parse_markdown(markdown):
    """
    Parse list in markdown format

    Parameters
    ----------
    markdown : string
        Black Desert Online key items in markdown list.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns: name, id, mainCategory, subCategory
    """
    # Parse the markdown list
    data_string = markdown.split("\n")
    data_string = [i.replace("|", ",") for i in data_string]
    data_string = [i.strip(",") for i in data_string]
    data_string = [i.strip(" ") for i in data_string]
    data_string = [i.split(",") for i in data_string]
    data_string = [[j.strip() for j in i] for i in data_string]
    data_rows = data_string[2:]

    # Extract columns data
    name_list = [d[0] for d in data_rows]
    id_list = [d[1] for d in data_rows]
    mainCategory = [d[2] for d in data_rows]
    subCategory = [d[3] for d in data_rows]

    # Create items df
    df = pd.DataFrame({"name": name_list, "id": id_list, "mainCategory": mainCategory, "subCategory": subCategory})
    return df

def generate_result(df, option, keyword, mainCategory, subCategory):
    file_name = "list.json"
    output_path = settings.ROOT_DIR / file_name

    result_df = pd.DataFrame()
    match option:
        case "k":
            # Search by keyword
            result_df = df[df["name"].str.contains(keyword)]
            result_df.to_json(output_path, orient="records", indent=4)
        case "m":
            # Search by mainCategory
            result_df = df[df["mainCategory"] == mainCategory]
        case "s":
            # Search by subCategory
            result_df = df[df["subCategory"] == subCategory]
        case option if "k" in option and "m" in option and "s" in option:
            # Search by multiple conditions
            result_df = df[(df["name"].str.contains(keyword)) & (df["mainCategory"] == mainCategory) & (df["subCategory"] == subCategory)]
        case option if "k" in option and "m" in option:
            # Search by keyword and mainCategory
            result_df = df[(df["name"].str.contains(keyword)) & (df["mainCategory"] == mainCategory)]
        case option if "k" in option and "s" in option:
            # Search by keyword and subCategory
            result_df = df[(df["name"].str.contains(keyword)) & (df["subCategory"] == subCategory)]
        case _:
            # Output whole df
            df.to_json(output_path, orient="records", indent=4)

    result_df.to_json(output_path, orient="records", indent=4)
    return result_df

def create(option, **kwargs):
    keyword = kwargs.get("keyword", "Deboreka")
    mainCategory = kwargs.get("mainCategory", "20")
    subCategory = kwargs.get("subCategory", "1")

    print(f"Creating items list with {option=}, {mainCategory=}, {subCategory=}")

    # Read the markdown file into a string variable
    with open(settings.ROOT_DIR / "items.md", "r", encoding="utf-8") as f:
        items = f.read()

    df = parse_markdown(items)
    generate_result(df, option=option, keyword=keyword, mainCategory=mainCategory, subCategory=subCategory)

if __name__ == "__main__":
    create("m", mainCategory="20")