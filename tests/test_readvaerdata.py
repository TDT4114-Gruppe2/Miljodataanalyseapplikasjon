"""Denne koden tester readvaerdata.py ved å 'mocke' filhåndtering."""

import importlib
import json
import os
import sys
import unittest
from unittest.mock import patch, mock_open

# Legg til 'data/processed' i sys.path slik at vi kan importere
# readvaerdata.py
path_processed = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../data/processed")
)
sys.path.insert(0, path_processed)


class TestReadVaerdata(unittest.TestCase):
    """Testklasse for readvaerdata.py."""

    @patch("pandas.DataFrame.to_csv")
    def test_read_and_process(self, mock_to_csv):
        """Test at readvaerdata.py leser JSON.

        Håndterer data til CSV korrekt.
        """
        # Dummy JSON-data som skal leses fra fil.
        dummy_data = {
            "data": [
                {
                    "observations": [
                        {"value": 20, "elementId": "air_temperature"}
                    ],
                    "sourceId": "SN18700",
                    "referenceTime": "2020-01-01T00:00:00Z",
                }
            ]
        }

        dummy_json_str = json.dumps(dummy_data)

        # 'open' slik at lesing av JSON-filen returnerer
        # dummy_json_str.
        m = mock_open(read_data=dummy_json_str)
        with patch("builtins.open", m):
            # Importer readvaerdata mens patchen er aktiv.
            import readvaerdata
            # Tvinger reimport
            importlib.reload(readvaerdata)

        # Sjekker at to_csv-metoden på DataFrame ble kalt.
        self.assertTrue(mock_to_csv.called)
        args, kwargs = mock_to_csv.call_args
        self.assertIn("vaerdata_oslo.csv", args[0])


if __name__ == "__main__":
    unittest.main()
