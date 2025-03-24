import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest

import analyzer
import pandas as pd


class TestAnalyzerExceptions(unittest.TestCase):
    def test_exception_hierarchy(self):
        self.assertTrue(issubclass(analyzer.DatabaseError, analyzer.AnalyzerError))
        self.assertTrue(issubclass(analyzer.ValidationError, analyzer.AnalyzerError))


class TestAnalyzer(unittest.TestCase):
    def test_get_table_name(self):
        test_cases = [
            # Valid case
            ("profit", "marketsublist"),
        ]

        for endpoint_key, expected in test_cases:
            with self.subTest(msg=f"Testing table name for: {endpoint_key}"):
                # Valid case
                result = analyzer.get_table_name(endpoint_key)
                self.assertEqual(result, expected)

    def test_get_report_table_name(self):
        test_cases = [
            # Valid case
            ("profit", "profitabilityreport"),
        ]

        for endpoint_key, expected in test_cases:
            with self.subTest(msg=f"Testing table name for: {endpoint_key}"):
                # Valid case
                result = analyzer.get_report_table_name(endpoint_key)
                self.assertEqual(result, expected)

    def test_calculate_stats(self):
        test_data = {
            "name": ["item1", "item2", "item3"],
            "sid": [0, 1, 2],
            "lastsoldprice": [100, 200, 500],
            "currentstock": [20, 7, 3],
        }
        df = pd.DataFrame(test_data)

        # Normal case
        stats = analyzer.calculate_stats(df, sid=2)
        self.assertIsInstance(stats, dict)
        self.assertIn("profit", stats)
        self.assertIn("rate", stats)

        # Base case sid: 0
        base_stats = analyzer.calculate_stats(df, sid=0)
        self.assertEqual(base_stats["profit"], 0)
        self.assertEqual(base_stats["rate"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
