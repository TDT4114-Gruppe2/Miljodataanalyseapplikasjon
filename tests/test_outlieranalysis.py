import unittest
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from src.analysis.outlieranalysis import OutlierAnalysis


class MockOutlierAnalysis(OutlierAnalysis):
    def _load_city(self, city):
        # Lager en mock-dataserie med en outlier i januar
        data = {
            "elementId": ["temperature"] * 7,
            "timeOffset": ["PT0H"] * 7,
            "referenceTime": pd.to_datetime(
                [
                    "2022-01-01", "2022-01-02", "2022-01-03",
                    "2022-01-04", "2022-01-05", "2022-01-06",
                    "2022-01-07"
                ],
                utc=True
            ),
            "value": [1, 2, 2, 3, 100, 2, 1],  # 100 er outlier
        }
        return pd.DataFrame(data)

    def _get_min_offset(self, city, element_id):
        return "PT0H"


class TestOutlierAnalysis(unittest.TestCase):
    def setUp(self):
        self.analysis = MockOutlierAnalysis("mock_dir", whisker=1.5)

    def test_find_outliers_per_month(self):
        df = self.analysis.find_outliers_per_month(
            city="oslo", element_id="temperature"
        )
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["year_month"], "2022-01")
        self.assertEqual(df.iloc[0]["outliers_removed"], 1)
        self.assertEqual(df.iloc[0]["total_count"], 7)
        self.assertAlmostEqual(df.iloc[0]["outlier_percentage"], 14.3, places=1)

    def test_stats_with_without_outliers_mean(self):
        df = self.analysis.stats_with_without_outliers(
            city="oslo", element_id="temperature", statistic="mean"
        )
        row = df.iloc[0]
        self.assertEqual(row["year_month"], "2022-01")
        self.assertAlmostEqual(row["mean_with_outliers"], 15.857, places=3)
        self.assertAlmostEqual(row["mean_without_outliers"], 1.833, places=3)
        self.assertEqual(row["outliers_removed"], 1)
        self.assertEqual(row["element_id"], "temperature")

    def test_stats_with_invalid_statistic(self):
        with self.assertRaises(ValueError):
            self.analysis.stats_with_without_outliers(
                city="oslo", element_id="temperature", statistic="max"
            )


if __name__ == '__main__':
    unittest.main()
