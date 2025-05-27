"""Tester fetchvaerdata.py med negative og positive tester."""

import json
import os
import tempfile
import unittest

from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError

from src.fetchData.fetchvaerdata import WeatherFetcher


class TestWeatherFetcher(unittest.TestCase):
    """Klasse for alle tester til filen."""

    def setUp(self):
        """Sett opp testmiljø."""
        self.client_id = "test_id"
        self.fetcher = WeatherFetcher(self.client_id)

    @patch("requests.get")
    def test_fetch_weather_data_success(self, mock_get):
        """Test at værdata hentes korrekt fra Frost-API."""
        expected_json = {"key": "value"}
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = expected_json
        mock_get.return_value = mock_response

        result = self.fetcher.fetch_weather_data()

        mock_get.assert_called_once_with(
            "https://frost.met.no/observations/v0.jsonld",
            params={
                "sources": "SN18700,SN90450",
                "elements": (
                    "mean(air_temperature P1D),"
                    "min(air_temperature P1D),"
                    "max(air_temperature P1D),"
                    "sum(precipitation_amount P1D),"
                    "mean(wind_speed P1D)"
                ),
                "referencetime": "2000-01-01/2024-12-31",
            },
            auth=(self.client_id, ""),
        )
        self.assertEqual(result, expected_json)

    @patch("requests.get")
    def test_fetch_weather_data_http_error(self, mock_get):
        """Tester at HTTP-feil håndteres korrekt ved henting av værdata."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError(
            "Error fetching data"
        )
        mock_get.return_value = mock_response

        with self.assertRaises(HTTPError):
            self.fetcher.fetch_weather_data()

    def test_write_json_to_file(self):
        """Tester at JSON-data skrives til fil korrekt."""
        data = {"foo": [1, 2, 3], "bar": {"baz": True}}
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "output.json")

            self.fetcher.write_json_to_file(data, file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            loaded = json.loads(content)
            self.assertEqual(loaded, data)
            self.assertIn("\n", content)
            self.assertTrue(content.startswith("{"))
            self.assertIn("    \"foo\"", content)


if __name__ == "__main__":
    unittest.main()
