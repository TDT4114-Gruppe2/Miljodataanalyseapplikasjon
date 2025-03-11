"""Denne koden tester vaerdata.py ved å 'mocke' API-håndtering."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Legger til `data/raw/` i sys.path for å kunne importere vaerdata.py
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/raw")
    )
)

import vaerdata  # Denne bryter med PEP8, men må defineres etter sys.path


class TestVaerdata(unittest.TestCase):
    """Testklasse for vaerdata.py."""

    @patch("vaerdata.requests.get")  # Mocker API-kall
    def test_fetch_weather_data(self, mock_get):
        """Tester at API-kallet returnerer forventet JSON-data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = vaerdata.fetch_weather_data("fake_client_id")
        self.assertEqual(result, {"data": "test"})  # Forventer dummy JSON-data

    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_write_json_to_file(self, mock_open):
        """Test at JSON skrives til fil."""
        data = {"key": "value"}
        vaerdata.write_json_to_file(data, "test.json")

        # Sjekk at filen blir åpnet med riktig navn
        mock_open.assert_called_once_with("test.json", "w",
                                          encoding="utf-8")

        # Sjekk at data blir skrevet til filen
        handle = mock_open()
        written_data = "".join(
            call.args[0] for call in handle.write.call_args_list
        )
        self.assertIn('"key": "value"', written_data)


if __name__ == "__main__":
    unittest.main()
