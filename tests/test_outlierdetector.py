import unittest
import pandas as pd
import numpy as np
from pandas.testing import assert_series_equal
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.analysis.outlierdetector import OutlierDetector


class TestOutlierDetector(unittest.TestCase):
    def setUp(self):
        self.data = pd.Series([10, 12, 12, 13, 12, 11, 100]) #100 er outlier her
        self.clean_data = pd.Series([10, 12, 12, 13, 12, 11])

    def test_init_valid(self):
        OutlierDetector()  # None
        OutlierDetector(1.5)
        OutlierDetector(3.0)

    def test_init_invalid(self):
        with self.assertRaises(ValueError):
            OutlierDetector(2.0)

    def test_summarize(self):
        detector = OutlierDetector()
        stats = detector.summarize(self.data)
        self.assertIn("Q1", stats)
        self.assertIn("Q3", stats)
        self.assertIn("IQR", stats)
        self.assertIn("lower_inner", stats)
        self.assertIn("upper_outer", stats)

    def test_detect_iqr_regular(self):
        detector = OutlierDetector(1.5)
        outliers = detector.detect_iqr(self.data)
        self.assertTrue(outliers.iloc[-1])  # 100 er outlier
        self.assertFalse(outliers.iloc[0])  # 10 er ikke outlier
        self.assertEqual(outliers.sum(), 1)

    def test_detect_iqr_extreme(self):
        detector = OutlierDetector(3.0)
        outliers = detector.detect_iqr(self.data)
        self.assertFalse(outliers.any())  # Ingen ekstreme outliers

    def test_detect_iqr_override_whisker(self):
        detector = OutlierDetector()
        outliers = detector.detect_iqr(self.data, whisker=1.5)
        self.assertEqual(outliers.sum(), 1)

    def test_detect_iqr_invalid_whisker(self):
        detector = OutlierDetector()
        with self.assertRaises(ValueError):
            detector.detect_iqr(self.data, whisker=-1)

    def test_count_outliers(self):
        detector = OutlierDetector(1.5)
        count = detector.count_outliers_iqr(self.data)
        self.assertEqual(count, 1)

    def test_remove_outliers(self):
        detector = OutlierDetector(1.5)
        result = detector.remove_outliers_iqr(self.data).dropna().reset_index(drop=True)
        expected = self.clean_data.reset_index(drop=True)
        assert_series_equal(result, expected)

    def test_static_detect(self):
        result = OutlierDetector.detect(self.data)
        self.assertEqual(result.sum(), 1)


if __name__ == '__main__':
    unittest.main()
