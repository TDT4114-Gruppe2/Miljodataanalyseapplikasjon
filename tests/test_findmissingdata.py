"""Denne koden tester findmissingdata.py ved å 'mocke' CSV-håndtering."""

import os
import sys
import unittest
from unittest.mock import patch

import pandas as pd


class TestFindMissingData(unittest.TestCase):
    """Testklasse for findmissingdata.py."""

    @patch("builtins.print")
    @patch("pandas.DataFrame.to_csv")
    @patch("pandas.read_csv")
    def test_find_missing_data(self, mock_read_csv, mock_to_csv, mock_print):
        """
        Test at findmissingdata.py leser de riktige CSV-filene.

        Gjør også at utskriftsfilene 'missing_in_both.csv' og
        'missing_summary.csv' blir skrevet.
        """
        # Dummy-data for Oslo og Tromsø slik at de ikke overlapper
        df_oslo = pd.DataFrame({
            "referenceTime": ["2020-01-01T00:00:00Z"],
            "timeOffset": ["0"],
            "elementId": ["temp"],
            "value": [20]
        })
        df_tromso = pd.DataFrame({
            "referenceTime": ["2020-01-01T00:00:00Z"],
            "timeOffset": ["0"],
            "elementId": ["temp"],
            "value": [15]
        })

        # Side effect for pd.read_csv returnerer dummy-data for to kall
        mock_read_csv.side_effect = [df_oslo, df_tromso]

        # Fjern findmissingdata fra sys.modules for å sikre fersk import
        if "findmissingdata" in sys.modules:
            del sys.modules["findmissingdata"]

        # Legg til mappen 'data/processed' i sys.path slik at
        # vi kan importere modulen
        script_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../data/processed")
        )
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        # Importer findmissingdata (koden kjøres ved import)
        import findmissingdata  # noqa: F401

        # Sjekk at pd.read_csv ble kalt to ganger med forventede filstier
        calls = mock_read_csv.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIn("vaerdata_oslo.csv", calls[0][0][0])
        self.assertIn("vaerdata_tromso.csv", calls[1][0][0])

        # Sjekk at DataFrame.to_csv ble kalt to ganger (én for hver CSV-fil)
        self.assertEqual(mock_to_csv.call_count, 2)
        first_call_filename = mock_to_csv.call_args_list[0][0][0]
        second_call_filename = mock_to_csv.call_args_list[1][0][0]
        self.assertEqual(os.path.basename(first_call_filename),
                         "missing_in_both.csv")
        self.assertEqual(os.path.basename(second_call_filename),
                         "missing_summary.csv")

        # Kombiner alle argumentene fra hvert print-kall til én streng
        printed_lines = [
            " ".join(str(arg) for arg in call.args)
            for call in mock_print.call_args_list
        ]
        self.assertTrue(any("missing_in_both.csv" in line
                            for line in printed_lines))
        self.assertTrue(any("missing_summary.csv" in line
                            for line in printed_lines))


if __name__ == "__main__":
    unittest.main()
