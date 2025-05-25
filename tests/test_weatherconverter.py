"""Test weatherconverter.py."""
import json
import os
import pandas as pd
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.handleData.weatherconverter import WeatherConverter


class TestWeatherConverter(unittest.TestCase):
    """Test WeatherConverter."""

    def setUp(self):
        """Set opp testmiljø."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tempdir.name, "input.json")
        self.output_dir = os.path.join(self.tempdir.name, "out")

    def tearDown(self):
        """Fjern testmiljø."""
        self.tempdir.cleanup()

    def write_json(self, data: dict):
        """Skriv testdata til JSON-fil."""
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def test_load_data_success(self):
        """Test at data lastes inn riktig fra JSON."""
        data = {"data": [{"sourceId": "A", "observations": []}]}
        self.write_json(data)
        conv = WeatherConverter(self.json_path, self.output_dir)
        loaded = conv.load_data()
        self.assertEqual(loaded, data)
        self.assertEqual(conv.data, data)

    def test_load_data_errors(self):
        """Test at load_data håndterer feil riktig."""
        with open(self.json_path, "w", encoding="utf-8") as f:
            f.write("{invalid json}")
        conv = WeatherConverter(self.json_path, self.output_dir)
        with patch.object(sys, 'exit') as mock_exit:
            conv.load_data()
            mock_exit.assert_called_once_with(1)
        mock_exit.reset_mock()

        self.write_json({})
        conv = WeatherConverter(self.json_path, self.output_dir)
        with patch.object(sys, 'exit') as mock_exit:
            conv.load_data()
            mock_exit.assert_called_once_with(1)
        mock_exit.reset_mock()

        self.write_json({"data": []})
        conv = WeatherConverter(self.json_path, self.output_dir)
        with patch.object(sys, 'exit') as mock_exit:
            conv.load_data()
            mock_exit.assert_called_once_with(1)

    def test_convert_to_dataframe_without_load(self):
        """Test at konvertering til df uten lastet data gir feil."""
        conv = WeatherConverter(self.json_path, self.output_dir)
        with self.assertRaises(RuntimeError):
            conv.convert_to_dataframe()

    def test_convert_to_dataframe_success(self):
        """Test at konvertering til df fungerer som forventet."""
        data = {
            "data": [
                {
                    "sourceId": "S1:0",
                    "referenceTime": "2025-05-01",
                    "observations": [
                        {"timeOffset": 0, "elementId": "e1",
                            "value": 1, "unit": "u1"},
                        {"timeOffset": 1, "elementId": "e2",
                            "value": 2, "unit": "u2"},
                    ]
                }
            ]
        }
        self.write_json(data)
        conv = WeatherConverter(self.json_path, self.output_dir)
        conv.load_data()
        df = conv.convert_to_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertListEqual(sorted(df.columns.tolist()),
                             ['elementId', 'referenceTime',
                              'sourceId', 'timeOffset', 'unit', 'value'])
        self.assertTrue(((df['elementId'] == 'e1') & (df['value'] == 1)).any())
        self.assertTrue(((df['elementId'] == 'e2') & (df['value'] == 2)).any())

    def test_run_queries_no_exception(self):
        """Test at run_queries kjører uten unntak."""
        conv = WeatherConverter(self.json_path, self.output_dir)
        conv.df = pd.DataFrame({
            'sourceId': ['A', 'A', 'B'],
            'value': [1, 2, 3]
        })
        self.assertIsNone(conv.run_queries())

    def test_save_city_data_without_df(self):
        """Test at save_city_data uten df gir feil."""
        conv = WeatherConverter(self.json_path, self.output_dir)
        with self.assertRaises(RuntimeError):
            conv.save_city_data()

    def test_save_city_data_creates_files(self):
        """Test at save_city_data lager filer for hver by."""
        df = pd.DataFrame({
            'sourceId': ['SN90450:0', 'SN18700:0', 'OTHER'],
            'referenceTime': ['t0', 't1', 't2'],
            'timeOffset': [0, 0, 0],
            'elementId': ['e', 'e', 'e'],
            'value': [1, 2, 3],
            'unit': ['u', 'u', 'u']
        })
        conv = WeatherConverter(self.json_path, self.output_dir)
        conv.df = df
        conv.save_city_data()
        tromso_file = os.path.join(self.output_dir, 'vaerdata_tromso.csv')
        oslo_file = os.path.join(self.output_dir, 'vaerdata_oslo.csv')
        self.assertTrue(os.path.exists(tromso_file))
        self.assertTrue(os.path.exists(oslo_file))
        df_tromso = pd.read_csv(tromso_file)
        df_oslo = pd.read_csv(oslo_file)
        self.assertTrue((df_tromso['sourceId'] == 'SN90450:0').all())
        self.assertTrue((df_oslo['sourceId'] == 'SN18700:0').all())


if __name__ == '__main__':
    unittest.main()
