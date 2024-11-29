# Guild Applications
An application server design to serve my another project [Discord Guild Bot](https://github.com/RyanYCT/discord-guild-bot)

## About This Project
This project is designed to cooperate with a bot to provide insights of the Black Desert Central Market to my community.

## Features
It monitors key product information regularly, calculates rates of return, reveals trends, compares items, and generates reports to support decision making.

## Getting Started
### Prerequisites
- Python 3.10 or higher
- Other dependencies listed in `requirements.txt`

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/RyanYCT/guild-application.git
    cd guild-application
    ```

2. Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

### Running the server
To start the server, run the `run.bat`

## Project Structure
```
guild-applications/
├─ Analyzer/
│  ├─ __init__.py
│  └─ analyzer.py
├─ data/
│  ├─ MarketPriceInfo/
│  │  └─ YYYY/
│  │     └─ mm/
│  │        └─ dd/
│  │           └─ H.json
│  └─ WorldMarketSubList/
│     └─ YYYY/
│        └─ mm/
│           └─ dd/
│              └─ H.json
├─ MonitoringList/
│  ├─ items.md
│  ├─ list.json
│  └─ list_creater.py
├─ report/
│  ├─ category/
│  │  └─ YYYY/
│  │     └─ mm/
│  │        └─ dd/
│  │           └─ H.json
│  ├─ item/
│  │  └─ YYYY/
│  │     └─ mm/
│  │        └─ dd/
│  │           └─ H.json
│  └─ overall/
│     └─ YYYY/
│        └─ mm/
│           └─ dd/
│              └─ H.json
├─ Scraper/
│  ├─ __init__.py
│  └─ scraper.py
├─ tests/
│  ├─ test_analyzer.py
│  └─ test_path.py
├─ app.py
├─ README.md
├─ requirements.txt
├─ run.bat
└─ scheduler.py
```

## Workflow
1. **Define Target**:
    - Noteworthy items are listed as markdown in `MonitoringList/items.md`. This list is intended to help filter out unwant items at first when searching by category.
    - The `MonitoringList/list_creater.py` script generates and updates the list of items to be monitored. That list is stored in `MonitoringList/list.json` and can be referenced by the scraper.

2. **Collect Data**:
    - The `Scraper` module is responsible for collecting data from the market. It fetches information and stores the data in the `data` directory under corresponding subdirectories such as `BiddingInfoList`, `MarketPriceInfo`, and `WorldMarketSubList`.

3. **Analyze Data**:
    - The `Analyzer` module processes the collected data. It analyze the statistics of items.

4. **Generate Reports**:
    - The analyzed data is organized into reports. These reports are stored in the `report` directory, categorized in `overall`, `category`, and `item`.

5. **Render Reports via RESTful API**:
    - The Flask application `app.py` serves as the backend, exposing RESTful API endpoints.
    - These endpoints allow the Discord bot to request the reports. The bot then render these reports in Discord channels.

## Report Templates
The reports that would be posted by the bot are similar to the following:

### Top Performers (Overall)
Overall ranking list that sorted by rate of return, reveal the best item at the time.

| name   | enhance | price        | profit          | rate     | stock |
|--------|---------|--------------|-----------------|----------|-------|
| item01 | 5       | 35200000000  | 26535867605.0   | 7.386767 | 4     |
| item02 | 3       | 12500000000  | 9372487605.0    | 7.106571 | 0     |
| item03 | 1       | 150000000000 | 111284330105.0  | 6.619053 | 0     |
| ...    | ...     | ...          | ...             | ...      | ...   |
| item97 | 0       | 4440000      | -23420474805.0  | 0.145388 | 63    |
| item98 | 0       | 8250000      | -227360568207.5 | 0.145277 | 101   |
| item99 | 5       | 0            | -8124244895.0   | 0.14525  | 0     |

### Top Performers (Category)
Similar to overall ranking with a smaller scope for particular type of item.

| name   | enhance | price        | profit          | rate     | stock |
|--------|---------|--------------|-----------------|----------|-------|
| item02 | 3       | 12500000000  | 9372487605.0    | 7.106571 | 0     |
| item03 | 1       | 150000000000 | 111284330105.0  | 6.619053 | 0     |
| item05 | 5       | 31400000000  | 23133962605.0   | 6.336776 | 4     |


### Details (Specific Item)
Focus on a item provide more detail information.

### Trend
| datetime    | price     |
|-------------|-----------|
| 20241005_07 | 657065602 |
| 20241005_06 | 688917682 |
| 20241005_05 | 726806220 |
| 20241005_04 | 776671826 |
| 20241005_03 | 753078048 |
| 20241005_02 | 700504587 |
| 20241005_01 | 695478468 |

### BBO (Best Bid and Offer)
| buyers | price     | sellers |
|--------|-----------|---------|
| 1      | 650000000 | 0       |
| 0      | 700000000 | 0       |
| 0      | 710000000 | 10      |
| 0      | 720000000 | 2       |
| 0      | 725000000 | 16      |
| 0      | 730000000 | 32      |
| 0      | 735000000 | 36      |
| 0      | 740000000 | 14      |
| 0      | 745000000 | 46      |
| 0      | 750000000 | 120     |

### Volume
| interval            | trades    |
|---------------------|-----------|
| 20241008 - 20241009 | 45678     |
| 20241007 - 20241008 | 34567     |
| 20241006 - 20241007 | 23456     |
| 20241005 - 20241006 | 12345     |

# References
BDO API: [veliainn](https://developers.veliainn.com/)

BDO Market API: [BDO Market API](https://documenter.getpostman.com/view/4028519/TzK2bEVg#intro)
