import json
import os
import tempfile
import unittest
from unittest.mock import patch
import io
import pandas as pd

from weatherconverter import WeatherConverter


class TestWeatherConverter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

        self.sample_data = {
            "data": [
                {
                    "sourceId": "SN18700:0",
                    "referenceTime": "2022-01-01T12:00:00Z",
                    "observations": [
                        {"timeOffset": "PT0H", "elementId": "temp", "value": 5, "unit": "C"},
                        {"timeOffset": "PT1H", "elementId": "wind", "value": 2, "unit": "m/s"}
                    ]
                },
                {
                    "sourceId": "SN90450:0",
                    "referenceTime": "2022-01-01T12:00:00Z",
                    "observations": [
                        {"timeOffset": "PT0H", "elementId": "temp", "value": 3, "unit": "C"}
                    ]
                }
            ]
        }

        self.json_path = os.path.join(self.test_dir.name, "vaerdata.json")
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_data, f)

        self.converter = WeatherConverter(self.json_path, self.test_dir.name)

    def test_load_data(self):
        data = self.converter.load_data()
        self.assertIn("data", data)

    def test_convert_to_dataframe(self):
        data = self.converter.load_data()
        self.converter.convert_to_dataframe(data)
        self.assertEqual(len(self.converter.df), 3)
        self.assertIn("sourceId", self.converter.df.columns)

    def test_run_queries(self):
        data = self.converter.load_data()
        self.converter.convert_to_dataframe(data)
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            self.converter.run_queries()
            output = fake_out.getvalue()
            self.assertIn("SN18700:0", output)

    def test_save_city_data(self):
        data = self.converter.load_data()
        self.converter.convert_to_dataframe(data)
        self.converter.save_city_data()

        oslo_path = os.path.join(self.test_dir.name, "vaerdata_oslo.csv")
        tromso_path = os.path.join(self.test_dir.name, "vaerdata_tromso.csv")

        self.assertTrue(os.path.exists(oslo_path))
        self.assertTrue(os.path.exists(tromso_path))

        df_oslo = pd.read_csv(oslo_path)
        self.assertTrue((df_oslo["sourceId"] == "SN18700:0").all())


if __name__ == "__main__":
    unittest.main()
