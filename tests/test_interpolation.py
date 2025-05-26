"""Tester interpolering.py."""

import os
import pandas as pd
import tempfile
import unittest

from pandas.testing import assert_frame_equal

from src.interpolation.interpolation import WeatherDataPipeline
import src.interpolation.interpolation as interp_mod


class DummyDecomp:
    """Klasse for å simulere uten ekte data."""

    def __init__(self, trend, resid, seasonal):
        """Initialiserer DummyDecomp."""
        self.trend = trend
        self.resid = resid
        self.seasonal = seasonal


class TestWeatherDataPipeline(unittest.TestCase):
    """Tester WeatherDataPipeline-funksjonalitet."""

    def setUp(self):
        """Setter opp testmiljøet med en pipeline."""
        self.pipeline = WeatherDataPipeline(
            small_gap_days=1, seasonal_period=2, model='additive')

    def test_infer_source_id(self):
        """Tester at kilder blir tolket riktig fra filnavn."""
        self.assertEqual(self.pipeline._infer_source_id(
            'path/to/oslo_data.csv'), 'SN18700:0')
        self.assertEqual(self.pipeline._infer_source_id(
            'TROMSO-file.csv'), 'SN90450:0')
        with self.assertRaises(ValueError):
            self.pipeline._infer_source_id('unknown.csv')

    def test_format_time_offset(self):
        """Tester at tidsforskyvning formateres riktig."""
        dt = pd.Timestamp('2025-05-01T13:30:00')
        self.assertEqual(self.pipeline._format_time_offset(dt), 'PT13H30M')
        dt2 = pd.Timestamp('2025-05-01T00:00:00')
        self.assertEqual(self.pipeline._format_time_offset(dt2), 'PT0H')

    def test_map_unit(self):
        """Tester at enheter er riktige."""
        self.assertEqual(self.pipeline._map_unit(
            'max(air_temperature P1D)'), 'degC')
        self.assertEqual(self.pipeline._map_unit(
            'mean(wind_speed P1D)'), 'm/s')
        self.assertEqual(self.pipeline._map_unit(
            'sum(precipitation_amount P1D)'), 'mm')
        self.assertEqual(self.pipeline._map_unit('other_element'), '')

    def test_impute_wide_no_missing(self):
        """Tester at breddeformat uten manglende verdier ikke endres."""
        dates = pd.date_range('2025-01-01', periods=3, freq='D')
        wide = pd.DataFrame({'e1': [1, 2, 3], 'e2': [4, 5, 6]}, index=dates)
        out = self.pipeline.impute_wide(wide)
        assert_frame_equal(out, wide)

    def test_impute_wide_with_missing_and_seasonal(self):
        """Tester at breddeformat med manglende verdier interpoleres riktig."""
        def fake_decompose(series,
                           model=None, period=None, extrapolate_trend=None):
            """Simulerer decomp uten ekte data."""
            return DummyDecomp(trend=series,
                               resid=pd.Series(0, index=series.index),
                               seasonal=pd.Series(0, index=series.index))
        interp_mod.seasonal_decompose = fake_decompose

        dates = pd.date_range('2025-01-01', periods=3, freq='D')
        wide = pd.DataFrame({'e1': [1, None, 3]}, index=dates)
        out = self.pipeline.impute_wide(wide)
        self.assertAlmostEqual(out.loc[dates[1], 'e1'], 2.0)

    def test_process_end_to_end(self):
        """Tester hele prosessen fra CSV til utdata."""
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, 'oslo.csv')
            output_path = os.path.join(tmp, 'out.csv')
            df = pd.DataFrame({
                'referenceTime': ['2025-05-01T00:00:00.000Z',
                                  '2025-05-01T01:00:00.000Z'],
                'timeOffset': ['PT0H', 'PT1H'],
                'elementId': ['max(air_temperature P1D)',
                              'min(air_temperature P1D)'],
                'value': [10, 6]
            })
            df.to_csv(input_path, index=False)

            def fake_decompose(series, model=None,
                               period=None, extrapolate_trend=None):
                """Simulerer decomp uten ekte data."""
                return DummyDecomp(trend=series.fillna(method='ffill'),
                                   resid=pd.Series(0, index=series.index),
                                   seasonal=pd.Series(0, index=series.index))
            interp_mod.seasonal_decompose = fake_decompose

            pipeline = WeatherDataPipeline()
            pipeline.process(input_path, output_path)

            self.assertTrue(os.path.exists(output_path))
            out = pd.read_csv(output_path)
            unique_pairs = out.drop_duplicates(
                subset=['referenceTime', 'elementId'])
            self.assertEqual(len(unique_pairs), 2)
            self.assertListEqual(out.columns.tolist(), [
                                 'sourceId', 'referenceTime',
                                 'timeOffset', 'elementId', 'value', 'unit'])
            self.assertEqual(out.loc[0, 'sourceId'], 'SN18700:0')
            self.assertIn(out.loc[0, 'unit'], ['degC'])


if __name__ == '__main__':
    unittest.main()
