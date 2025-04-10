import os
import tempfile
import unittest
import pandas as pd

from missingdatafinder import MissingWeatherDataAnalyzer


class TestMissingWeatherDataAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

        self.output_dir = os.path.join(self.test_dir.name, "output")
        os.makedirs(self.output_dir, exist_ok=True)

        # Lag testdata
        df_oslo = pd.DataFrame({
            "referenceTime": ["2022-01-01T12:00:00Z", "2022-01-02T12:00:00Z"],
            "timeOffset": ["PT0H", "PT0H"],
            "elementId": ["temp", "temp"],
            "value": [5, 6],
        })

        df_tromso = pd.DataFrame({
            "referenceTime": ["2022-01-01T12:00:00Z", "2022-01-02T12:00:00Z", "2022-01-03T12:00:00Z"],
            "timeOffset": ["PT0H", "PT0H", "PT0H"],
            "elementId": ["temp", "temp", "temp"],
            "value": [5, 6, 7],
        })

        self.oslo_csv = os.path.join(self.test_dir.name, "vaerdata_oslo.csv")
        self.tromso_csv = os.path.join(self.test_dir.name, "vaerdata_tromso.csv")

        df_oslo.to_csv(self.oslo_csv, index=False)
        df_tromso.to_csv(self.tromso_csv, index=False)

        self.analyzer = MissingWeatherDataAnalyzer(
            oslo_path=self.oslo_csv,
            tromso_path=self.tromso_csv,
            output_dir=self.output_dir
        )

    def test_load_data(self):
        self.analyzer.load_data()
        self.assertIn("date", self.analyzer.df_oslo.columns)

    def test_identify_missing(self):
        self.analyzer.load_data()
        self.analyzer.identify_missing()
        self.assertFalse(self.analyzer.df_missing.empty)

    def test_save_missing_data(self):
        self.analyzer.load_data()
        self.analyzer.identify_missing()
        self.analyzer.save_missing_data()

        missing_csv = os.path.join(self.output_dir, "missing_in_both.csv")
        summary_csv = os.path.join(self.output_dir, "missing_summary.csv")

        self.assertTrue(os.path.exists(missing_csv))
        self.assertTrue(os.path.exists(summary_csv))

        df_summary = pd.read_csv(summary_csv)
        self.assertIn("num_missing", df_summary.columns)


if __name__ == "__main__":
    unittest.main()
