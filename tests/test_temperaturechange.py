"""Test temperaturechange.py."""

import os
import pandas as pd
import tempfile
import unittest

from pandas.testing import assert_frame_equal

from src.handleData.temperaturechange import TemperatureRangeConverter


class TestTemperatureRangeConverter(unittest.TestCase):
    """Test TemperatureRangeConverter."""

    def setUp(self):
        """Sett opp testmiljø."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.output_dir = self.tempdir.name
        self.converter = TemperatureRangeConverter(self.output_dir)

    def tearDown(self):
        """Fjern testmiljø."""
        self.tempdir.cleanup()

    def test_compute_daily_range(self):
        """Test at daglig temperaturintervall beregnes riktig."""
        data = {
            'sourceId': ['S1', 'S1'],
            'referenceTime': ['2025-05-01', '2025-05-01'],
            'timeOffset': [0, 0],
            'elementId': ['max(air_temperature P1D)',
                          'min(air_temperature P1D)'],
            'value': [15.2, 5.7],
            'unit': ['degC', 'degC']
        }
        df_city = pd.DataFrame(data)
        result = self.converter._compute_daily_range(df_city)
        expected = pd.DataFrame({
            'sourceId': ['S1'],
            'referenceTime': ['2025-05-01'],
            'timeOffset': [0],
            'elementId': ['range(air_temperature P1D)'],
            'value': [(15.2 - 5.7)],
            'unit': ['degC']
        })
        expected['value'] = expected['value'].round(1)

        assert_frame_equal(
            result.reset_index(drop=True).sort_index(axis=1),
            expected.reset_index(drop=True).sort_index(axis=1),
            check_names=False
        )

    def test_process_city_creates_range_rows(self):
        """Test at prosessering av by skaper range-rader."""
        city = 'oslo'
        file_path = os.path.join(self.output_dir, f"vaerdata_{city}.csv")
        df_input = pd.DataFrame({
            'sourceId': ['S1', 'S1'],
            'referenceTime': ['2025-05-02', '2025-05-02'],
            'timeOffset': [0, 0],
            'elementId': ['max(air_temperature P1D)',
                          'min(air_temperature P1D)'],
            'value': [20.0, 10.0],
            'unit': ['degC', 'degC']
        })
        df_input.to_csv(file_path, index=False)

        self.converter.run()
        df_updated = pd.read_csv(file_path)
        range_rows = df_updated[df_updated['elementId']
                                == 'range(air_temperature P1D)']
        self.assertEqual(len(range_rows), 1)
        self.assertAlmostEqual(range_rows.iloc[0]['value'], 10.0, places=1)
        self.assertEqual(range_rows.iloc[0]['unit'], 'degC')

        original_rows = df_updated[df_updated['elementId']
                                   == 'max(air_temperature P1D)']
        self.assertEqual(len(original_rows), 1)


if __name__ == '__main__':
    unittest.main()
