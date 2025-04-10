import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from fetchvaerdata import WeatherFetcher


class TestWeatherFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = WeatherFetcher("dummy_client_id")
        self.sample_data = {
            "data": [
                {"sourceId": "TEST", "observations": [{"elementId": "temp", "value": 10}], "referenceTime": "2022-01-01T00:00:00Z"}
            ]
        }

    @patch("weather_fetcher.requests.get")
    def test_fetch_weather_data(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_data
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        result = self.fetcher.fetch_weather_data()
        self.assertEqual(result, self.sample_data)

    def test_write_json_to_file(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w+", encoding="utf-8") as tmp_file:
            filename = tmp_file.name

        try:
            self.fetcher.write_json_to_file(self.sample_data, filename)
            with open(filename, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertEqual(loaded, self.sample_data)
        finally:
            os.remove(filename)


if __name__ == "__main__":
    unittest.main()
