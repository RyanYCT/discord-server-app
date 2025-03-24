import datetime
import logging
from datetime import datetime as dt
from typing import Dict, Optional

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch

from common import etl_settings

logger = logging.getLogger(__name__)


class AnalyzerError(Exception):
    pass


class DatabaseError(AnalyzerError):
    pass


class ValidationError(AnalyzerError):
    pass


def get_table_name(report_type: str) -> str:
    """Table name mapping"""
    logger.info(f"Getting data source table name for '{report_type}'")
    table_name = etl_settings.REPORT_DATA_SOURCE.get(report_type, None)
    if table_name is None:
        raise ValueError(f"Invalid endpoint key: '{report_type}'")
    logger.debug(f"{table_name=}")
    return table_name


def get_report_table_name(report_type: str) -> str:
    """Table name mapping"""
    logger.info(f"Getting report table name for '{report_type}'")
    report_table_name = etl_settings.REPORT_TABLES.get(report_type, None)
    if report_table_name is None:
        raise ValueError(f"Invalid endpoint key: '{report_type}'")
    logger.debug(f"{report_table_name=}")
    return report_table_name


def fetch_data(
    table_name: str,
    name: Optional[str] = None,
    sid: Optional[int] = None,
    date: Optional[str] = None,
    hour: Optional[int] = None,
) -> pd.DataFrame:
    """
    Fetch data from the database based on given parameters.

    Parameters
    ----------
    table_name : str
        Name of the database table to query
    name : str, optional
        Item name to filter results
    sid : int, optional
        Enhancement level to filter results
    date : str, optional
        Date to filter results (format: YYYY-MM-DD)
    hour : int, optional
        Hour to filter results (0-23)

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the query results

    Raises
    ------
    ValueError
        If invalid table name or parameters are provided
    DatabaseError
        If database operation fails
    """
    logger.info(f"Fetching data from '{table_name}'")
    logger.debug(f"{table_name=}, {name=}, {sid=}, {date=}, {hour=}")
    try:
        with psycopg2.connect(**etl_settings.DATABASE_CONFIG) as conn:
            # Validate input to prevent dynamic injection
            if table_name not in etl_settings.REPORT_DATA_SOURCE.values():
                raise ValueError("Invalid table name provided")

            # Initialize parameters list
            params = []

            # Base query
            query = sql.SQL("SELECT {fields} FROM {table_name} WHERE 1=1").format(
                fields=sql.SQL(",").join(
                    [
                        sql.Identifier("scrapetime"),
                        sql.Identifier("name"),
                        sql.Identifier("id"),
                        sql.Identifier("sid"),
                        sql.Identifier("currentstock"),
                        sql.Identifier("lastsoldprice"),
                    ]
                ),
                table_name=sql.Identifier(table_name),
            )

            # Search by name
            if name:
                query = sql.SQL(" ").join([query, sql.SQL("AND name ILIKE %s")])
                params.append(f"%{name}%")

            # Search by sid (enhancement level)
            if sid:
                query = sql.SQL(" ").join([query, sql.SQL("AND sid = %s")])
                params.append(sid)

            # Date handling
            # Case 1: no date, no hour. Get the latest data.
            if not date and not hour:
                current_datetime = dt.now()
                start_time = current_datetime.replace(minute=0, second=0, microsecond=0)
                query = sql.SQL(" ").join([query, sql.SQL("AND scrapetime >= %s")])
                params.append(start_time)

            # Case 2: both date and hour
            elif date and hour:
                parsed_date = dt.strptime(date, "%Y-%m-%d")
                start_time = parsed_date.replace(hour=int(hour), minute=0, second=0, microsecond=0)
                end_time = parsed_date.replace(hour=int(hour), minute=59, second=59, microsecond=999999)
                query = sql.SQL(" ").join([query, sql.SQL("AND scrapetime >= %s AND scrapetime < %s")])
                params.extend([start_time, end_time])

            # Execute query
            logger.debug(f"pd.read_sql_query({query.as_string(conn)}, {params=})")
            df = pd.read_sql_query(query.as_string(conn), conn, params=params)

            if df.empty:
                logger.warning("Query returned no results")

            logger.info(f"Successfully fetched data from '{table_name}'")
            logger.debug(f"{df.shape=}")
            return df

    except psycopg2.Error as dbe:
        logger.error(f"Database operation error: {dbe}")
        raise DatabaseError(f"Database operation failed: {dbe}")


def calculate_stats(df: pd.DataFrame, sid: int, merchant: bool = False) -> Dict:
    """
    Calculate profit and rate of return by comparing enhancement levels.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing item data
    sid : int
        Enhancement level to analyze
    merchant : bool, optional
        Whether to use merchant tax rate (default False)

    Returns
    -------
    dict
        Dictionary containing:
        - profit: float
            Calculated profit
        - rate: float
            Rate of return

    Raises
    ------
    AnalyzerError
        If calculation fails due to missing data
    """
    logger.debug(f"calculate_stats({df.shape=}, {sid=}, {merchant=})")
    NORMAL_TAX_RATE = 0.88725
    MERCHANT_TAX_RATE = 0.85475

    # If sid is 0, there is no previous enhancement level and no need to compare
    if sid == 0:
        stat = {"profit": 0, "rate": 0}
        return stat

    after_tax = NORMAL_TAX_RATE
    if merchant:
        after_tax = MERCHANT_TAX_RATE

    try:
        # Current enhance level lastSoldPrice
        current_lv_price = df[df["sid"] == sid]["lastsoldprice"].iloc[0]
        # Previous enhance level lastSoldPrice
        previous_lv_price = df[df["sid"] == (sid - 1)]["lastsoldprice"].iloc[0]
        # 0 enhance level lastSoldPrice
        clean_price = df[df["sid"] == 0]["lastsoldprice"].iloc[0]

        # Calculate stats
        cost = previous_lv_price + clean_price
        profit = (current_lv_price - cost) * after_tax
        rate_of_return = 1 + (profit / cost)

        stat = {"profit": profit, "rate": rate_of_return}
        return stat

    except IndexError as ie:
        logger.error(f"IndexError: {ie}")
        raise AnalyzerError(f"IndexError: {ie}")
    except KeyError as ke:
        logger.error(f"KeyError: {ke}")
        raise AnalyzerError(f"KeyError: {ke}")


def profit_analyzer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze profit and rate of return for each item.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the analyzed results
    """
    logger.info("Analyzing profit")
    if df.empty:
        logger.warning("No data to analyze")
        return pd.DataFrame()

    current_time = dt.now()
    # Round to nearest minute
    analyze_time = current_time.strftime("%Y-%m-%d %H:00")

    records = []
    try:
        # Group by item id to ensure processing the same item
        for item_id in df["id"].unique():
            # Create item dataframe
            item_df = df[df["id"] == item_id].copy()
            item_df = item_df.sort_values(by="sid")

            # Process each enhancement level
            for _, row in item_df.iterrows():
                stats = calculate_stats(item_df, row["sid"])
                records.append(
                    {
                        "analyzetime": analyze_time,
                        "name": row["name"],
                        "enhance": row["sid"],
                        "price": row["lastsoldprice"],
                        "profit": stats["profit"],
                        "rate": stats["rate"],
                        "stock": row["currentstock"],
                    }
                )

        analyzed_df = pd.DataFrame.from_records(records)
        logger.debug(f"{analyzed_df.shape=}")
        return analyzed_df.sort_values(by="rate", ascending=False)

    except IndexError as ie:
        logger.error(f"IndexError: {ie}")
        raise AnalyzerError(f"IndexError: {ie}")
    except KeyError as ke:
        logger.error(f"KeyError: {ke}")
        raise AnalyzerError(f"KeyError: {ke}")


def store_data(analyzed_df: pd.DataFrame, table_name: str) -> None:
    """
    Store analyzed data in the database.

    Parameters
    ----------
    analyzed_df : pandas.DataFrame
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
    logger.info(f"Storing data to '{table_name}'")
    if analyzed_df.empty:
        logger.error("No data to store")
        return

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
                            analyzeTime TIMESTAMP(0),
                            name VARCHAR(255),
                            enhance INT,
                            price BIGINT,
                            profit BIGINT,
                            rate FLOAT,
                            stock BIGINT,
                            UNIQUE (analyzetime, name, enhance)
                        );
                    """
                    ).format(table_name=sql.Identifier(table_name))
                    cur.execute(create_table_query)

                    # Batch insert
                    # Prepare for batch insert
                    insert_query = sql.SQL(
                        """
                        INSERT INTO {table} (analyzeTime, name, enhance, price, profit, rate, stock)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (analyzetime, name, enhance) DO NOTHING;
                        """
                    ).format(table=sql.Identifier(table_name))
                    records = []
                    for item in analyzed_df.to_dict(orient="records"):
                        record = (
                            item["analyzetime"],
                            item["name"],
                            item["enhance"],
                            item["price"],
                            item["profit"],
                            item["rate"],
                            item["stock"],
                        )
                        records.append(record)

                    execute_batch(cur, insert_query, records)
                    conn.commit()
                    logger.info(f"Successfully stored '{len(analyzed_df)}' records in '{table_name}'")

                except psycopg2.Error as dbe:
                    logger.error(f"Database operation error: {dbe}")
                    raise DatabaseError(f"Database operation failed: {dbe}")

    except psycopg2.Error as dbe:
        logger.error(f"Database connection error: {dbe}")
        raise DatabaseError(f"Database connection error: {dbe}")


def analyzer(report_type: str) -> None:
    logger.debug(f"analyzer({report_type=})")
    try:
        table_name = get_table_name(report_type)
        df = fetch_data(table_name)
        analyzed_df = profit_analyzer(df)
        report_table_name = get_report_table_name(report_type)
        store_data(analyzed_df, report_table_name)

    except (ValidationError, DatabaseError, AnalyzerError) as e:
        logger.error(f"Analyzer error: {e}")


if __name__ == "__main__":
    logger.basicConfig(level=logging.INFO)
    analyzer(report_type="profit")
