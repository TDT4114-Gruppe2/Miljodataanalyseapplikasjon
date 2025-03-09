import unittest
from unittest.mock import patch, mock_open
import json
import os
import sys
import importlib

# Legg til 'data/processed' i sys.path slik at vi kan importere readvaerdata.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/processed")))

class TestReadVaerdata(unittest.TestCase):
    @patch("pandas.DataFrame.to_csv")
    def test_read_and_process(self, mock_to_csv):
        """Test at readvaerdata.py leser JSON og prosesserer data til CSV korrekt"""
        # Dummy JSON-data med en post og en observasjon
        dummy_data = {
            "data": [
                {
                    "observations": [{"temp": 20}],
                    "sourceId": "SN18700",
                    "referenceTime": "2020-01-01T00:00:00Z"
                }
            ]
        }
        dummy_json_str = json.dumps(dummy_data)
        
        # Patch 'open' slik at lesing av JSON-filen returnerer dummy_json_str.
        m = mock_open(read_data=dummy_json_str)
        with patch("builtins.open", m):
            # Importer readvaerdata mens patchen er aktiv.
            # Merk: readvaerdata.py kjører all kode ved import,
            # så importen vil trigge lesing av JSON og skriving av CSV.
            import readvaerdata
            # For å teste på nytt om nødvendig, kan vi tvinge en reimport:
            importlib.reload(readvaerdata)
        
        # Sjekk at to_csv-metoden på DataFrame ble kalt,
        # dvs. at CSV-fil skriving ble forsøkt.
        self.assertTrue(mock_to_csv.called)
        args, kwargs = mock_to_csv.call_args
        # Forvent at filnavnet til CSV inneholder "vaerdata_processed.csv"
        self.assertIn("vaerdata_processed.csv", args[0])

if __name__ == "__main__":
    unittest.main()
