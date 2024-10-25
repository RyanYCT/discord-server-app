import json
import os
import pathlib
import sys
import unittest

import pandas as pd

# Add the bdo-guild-application directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Analyzer.analyzer import overall_analyzer


class TestAnalyzer(unittest.TestCase):
    def test_analyzer(self):
        data_path = pathlib.Path(__file__).cwd() / "data" / "WorldMarketSubList" / "20241017_13.json"

        # Read data
        with open(data_path, "r", encoding="utf-8") as f:
            json_data = json.loads(data_path.read_text())

        result_shape = pd.DataFrame(overall_analyzer(json_data)).shape
        expected_shape = (210, 6)
        self.assertEqual(result_shape, expected_shape)


if __name__ == "__main__":
    unittest.main()
