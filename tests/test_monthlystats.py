"""Tester monthlystats.py."""
import numpy as np
import unittest
import pandas as pd

from src.analysis.monthlystats import MonthlyStats


class DummyLoader(MonthlyStats):
    """Dummy loader som tester MonthlyStats."""

    def __init__(self, df, min_offset):
        """Initialisér DummyLoader."""
        self._df = df
        self._min_offset = min_offset

    def _load_city(self, city):
        """Hent data for en by."""
        return self._df

    def _get_min_offset(self, city, element_id):
        """Hent minste offset for en by og element."""
        return self._min_offset


class TestMonthlyStats(unittest.TestCase):
    """Tester MonthlyStats."""

    def setUp(self):
        """Setter opp testdata."""
        dates = (
            pd.date_range("2021-01-01", periods=4, freq="D").tolist()
            + pd.date_range("2021-02-01", periods=4, freq="D").tolist()
        )
        data = {
            "elementId": ["rain"] * 8,
            "timeOffset": ["PT1H"] * 8,
            "referenceTime": dates,
            "value": [1, 2, 3, 4, 5, 6, 7, 8],
        }
        self.df = pd.DataFrame(data)
        self.df["referenceTime"] = pd.to_datetime(
            self.df["referenceTime"]
        ).dt.tz_localize("UTC")

    def test_compute_single_month_with_offset(self):
        """Tester compute_single_month med offset."""
        loader = DummyLoader(self.df, min_offset="PT1H")
        stats = loader.compute_single_month(
            "2021-02", "rain", "cityX", time_offset="PT1H"
        )
        self.assertAlmostEqual(stats["mean"], 6.5)
        self.assertAlmostEqual(stats["median"], 6.5)
        expected_std = np.std([5, 6, 7, 8], ddof=0)
        self.assertAlmostEqual(stats["std"], expected_std)

    def test_compute_single_month_without_offset(self):
        """Tester compute_single_month uten offset."""
        loader = DummyLoader(self.df, min_offset="PT1H")
        stats = loader.compute_single_month(
            "2021-01", "rain", "cityX", time_offset=None
        )
        self.assertAlmostEqual(stats["mean"], 2.5)

    def test_compute_all_months(self):
        """Tester compute_all_months."""
        loader = DummyLoader(self.df, min_offset="PT1H")
        df_stats = loader.compute_all_months("rain", "cityX", time_offset=None)
        self.assertListEqual(
            list(df_stats["year_month"]), ["2021-01", "2021-02"]
        )
        # Sjekker mean
        self.assertAlmostEqual(df_stats.loc[0, "mean"], 2.5)
        self.assertAlmostEqual(df_stats.loc[1, "mean"], 6.5)
        # Sjekker median
        self.assertAlmostEqual(df_stats.loc[0, "median"], 2.5)
        self.assertAlmostEqual(df_stats.loc[1, "median"], 6.5)
        # Sjekker standardavvik
        self.assertAlmostEqual(
            df_stats.loc[0, "std"], np.std([1, 2, 3, 4], ddof=1)
        )
        self.assertAlmostEqual(
            df_stats.loc[1, "std"], np.std([5, 6, 7, 8], ddof=1)
        )


if __name__ == "__main__":
    unittest.main()
