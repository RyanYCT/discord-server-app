import sys
from pathlib import Path

import requests

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import unittest
from unittest.mock import MagicMock, patch

import scraper


class TestScraperExceptions(unittest.TestCase):
    def test_exception_hierarchy(self):
        self.assertTrue(issubclass(scraper.APIError, scraper.ScraperError))
        self.assertTrue(issubclass(scraper.DatabaseError, scraper.ScraperError))
        self.assertTrue(issubclass(scraper.ValidationError, scraper.ScraperError))


class TestScraper(unittest.TestCase):
    def setUp(self):
        self.valid_response_data = [
            [
                {
                    "name": "Deboreka Ring",
                    "id": 12094,
                    "sid": 0,
                    "minEnhance": 0,
                    "maxEnhance": 0,
                    "basePrice": 630000000,
                    "currentStock": 726,
                    "totalTrades": 413344,
                    "priceMin": 35000000,
                    "priceMax": 825000000,
                    "lastSoldPrice": 640000000,
                    "lastSoldTime": 1741760005,
                },
                {
                    "name": "Deboreka Ring",
                    "id": 12094,
                    "sid": 1,
                    "minEnhance": 1,
                    "maxEnhance": 1,
                    "basePrice": 1450000000,
                    "currentStock": 50,
                    "totalTrades": 13020,
                    "priceMin": 105000000,
                    "priceMax": 2470000000,
                    "lastSoldPrice": 1460000000,
                    "lastSoldTime": 1741760000,
                },
            ],
            [
                {
                    "name": "Deboreka Necklace",
                    "id": 11653,
                    "sid": 0,
                    "minEnhance": 0,
                    "maxEnhance": 0,
                    "basePrice": 565000000,
                    "currentStock": 316,
                    "totalTrades": 202088,
                    "priceMin": 35000000,
                    "priceMax": 825000000,
                    "lastSoldPrice": 580000000,
                    "lastSoldTime": 1741760058,
                },
                {
                    "name": "Deboreka Necklace",
                    "id": 11653,
                    "sid": 1,
                    "minEnhance": 1,
                    "maxEnhance": 1,
                    "basePrice": 1130000000,
                    "currentStock": 36,
                    "totalTrades": 11334,
                    "priceMin": 105000000,
                    "priceMax": 2470000000,
                    "lastSoldPrice": 1140000000,
                    "lastSoldTime": 1741760055,
                },
            ],
        ]

        self.test_url = "https://testscraper.com/mockendpoint"
        self.test_payload = {
            "id": [11653, 11882],
            "sid": None,
        }

    def test_get_item_id(self):
        test_cases = [
            # Valid case
            ("Deboreka Series", [11653, 11882, 12094, 12276]),
            ("Deboreka Necklace", 11653),
            ("Deboreka Earring", 11882),
            ("Deboreka Ring", 12094),
            ("Deboreka Belt", 12276),
            # Invalid case
            ("Invalid Item", ValueError),
        ]

        for item_name, expected in test_cases:
            with self.subTest(msg=f"Testing item : {item_name}"):
                # Valid case
                if isinstance(expected, (list, int)):
                    result = scraper.get_item_id(item_name)
                    self.assertEqual(result, expected)

                # Invalid case
                else:
                    with self.assertRaises(expected):
                        scraper.get_item_id(item_name)

    def test_get_endpoint(self):
        test_cases = [
            # Valid case
            ("list", "GetWorldMarketList"),
            ("sub", "GetWorldMarketSubList"),
            ("bid", "GetBiddingInfoList"),
            ("price", "GetMarketPriceInfo"),
            # Invalid case
            ("invalidKey", ValueError),
            ("", ValueError),
            (1, ValueError),
            (None, ValueError),
        ]

        for endpoint_key, expected in test_cases:
            with self.subTest(msg=f"Testing endpoint: {endpoint_key}"):
                # Valid case
                if isinstance(expected, str):
                    result = scraper.get_endpoint(endpoint_key)
                    self.assertEqual(result, expected)

                # Invalid case
                else:
                    with self.assertRaises(expected):
                        scraper.get_endpoint(endpoint_key)

    def test_get_table_name(self):
        test_cases = [
            # Valid case
            ("list", "marketlist"),
            ("sub", "marketsublist"),
            ("bid", "biddinginfo"),
            ("price", "priceinfo"),
        ]

        for endpoint_key, expected in test_cases:
            with self.subTest(msg=f"Testing table name for: {endpoint_key}"):
                # Valid case
                result = scraper.get_table_name(endpoint_key)
                self.assertEqual(result, expected)

    def test_get_payload(self):
        test_cases = [
            # Valid case
            ("list", {"mainCategory": 1}, {"mainCategory": 1}),
            ("list", {"mainCategory": 85}, {"mainCategory": 85}),
            ("sub", {"id": 11653, "sid": 0}, {"id": 11653, "sid": 0}),
            ("sub", {"id": 11653, "sid": 20}, {"id": 11653, "sid": 20}),
            ("sub", {"id": 11653, "sid": None}, {"id": 11653}),
            ("sub", {"id": 11653}, {"id": 11653}),
            # Invalid case
            ("list", {"mainCategory": 0}, ValueError),
            ("list", {"mainCategory": 2}, ValueError),
            ("list", {"mainCategory": 86}, ValueError),
            ("list", {"mainCategory": None}, ValueError),
            ("list", {}, ValueError),
            ("sub", {"id": 11653, "sid": -1}, ValueError),
            ("sub", {"id": 11653, "sid": 21}, ValueError),
            ("sub", {"id": 11653, "sid": 99}, ValueError),
        ]

        for endpoint, kwargs, expected in test_cases:
            with self.subTest(msg=f"Testing payload with: {endpoint} {kwargs}"):
                # Valid case
                if isinstance(expected, dict):
                    result = scraper.get_payload(endpoint, **kwargs)
                    self.assertEqual(result, expected)

                # Invalid case
                else:
                    with self.assertRaises(expected):
                        scraper.get_payload(endpoint, **kwargs)

    @patch("scraper.requests.get")
    def test_fetch_data(self, mock_get):
        # Mock successful response object
        mock_response = MagicMock()
        mock_response.json.return_value = self.valid_response_data
        mock_get.return_value = mock_response

        # Successful case
        result = scraper.fetch_data(self.test_url, self.test_payload)

        # Build the expected data
        expected_data = []
        # Simulate the process in fetch_data()
        for sublist in self.valid_response_data:
            for item in sublist:
                item["scrapeTime"] = result[0]["scrapeTime"]  # Use the actual scrape time
                expected_data.append(item)

        self.assertEqual(result, expected_data)

        # Error case
        error_cases = [
            (requests.exceptions.HTTPError, scraper.APIError),
            (requests.exceptions.RequestException, scraper.APIError),
            (ValueError, scraper.APIError),
        ]
        for error, expected_error in error_cases:
            with self.subTest(msg=f"Testing error: {error.__class__.__name__}"):
                mock_get.side_effect = error
                with self.assertRaises(expected_error):
                    scraper.fetch_data(self.test_url, self.test_payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
