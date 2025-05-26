"""Tester missingdatafinder.py."""

import os
import pandas as pd
import tempfile
import unittest

from pandas.testing import assert_frame_equal

from src.missingData.missingdatafinder import MissingWeatherDataAnalyzer
from src.missingData.missingdatafinder import MissingDataConverter


class TestMissingWeatherDataAnalyzer(unittest.TestCase):
    """Testene for MissingWeatherDataAnalyzer."""

    def setUp(self):
        """Laerg midlertidig mappe og testdata."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.oslo_path = os.path.join(self.tempdir.name, 'oslo.csv')
        self.tromso_path = os.path.join(self.tempdir.name, 'tromso.csv')
        self.output_dir = os.path.join(self.tempdir.name, 'out')

        df_oslo = pd.DataFrame({
            'referenceTime': ['2025-05-01T00:00:00Z', '2025-05-01T01:00:00Z'],
            'timeOffset': [0, 60],
            'elementId': ['e1', 'e2'],
            'value': [10, None]
        })
        df_tromso = pd.DataFrame({
            'referenceTime': ['2025-05-01T00:00:00Z', '2025-05-01T01:00:00Z'],
            'timeOffset': [0, 60],
            'elementId': ['e1', 'e2'],
            'value': [None, 20]
        })
        df_oslo.to_csv(self.oslo_path, index=False)
        df_tromso.to_csv(self.tromso_path, index=False)

        self.analyzer = MissingWeatherDataAnalyzer(
            self.oslo_path, self.tromso_path, self.output_dir
        )

    def tearDown(self):
        """Fjerner midlertidig mappe."""
        self.tempdir.cleanup()

    def test_load_and_identify_missing(self):
        """Tester at manglende data blir identifisert riktig."""
        # Act
        self.analyzer.load_data()
        self.analyzer.identify_missing()
        df_missing = self.analyzer.df_missing

        # Assert
        expected_cols = ['date', 'timeOffset', 'elementId',
                         'oslo_value', 'tromso_value', 'city']
        self.assertListEqual(
            sorted(df_missing.columns.tolist()), sorted(expected_cols))

        actual = set(zip(df_missing['elementId'], df_missing['city']))
        expected = {('e1', 'Tromsø'), ('e2', 'Oslo')}
        self.assertSetEqual(actual, expected)


def test_save_missing_data(self):
    """Tester at manglende data blir lagret riktig."""
    self.analyzer.df_missing = pd.DataFrame({
        'date': ['2025-05-01'],
        'timeOffset': [0],
        'elementId': ['e1'],
        'oslo_value': [None],
        'tromso_value': [15],
        'city': ['Oslo']
    })
    # Act
    self.analyzer.save_missing_data()

    # Assert
    missing_path = os.path.join(self.output_dir, 'missing_in_both.csv')
    summary_path = os.path.join(self.output_dir, 'missing_summary.csv')
    self.assertTrue(os.path.exists(missing_path))
    self.assertTrue(os.path.exists(summary_path))

    df_missing = pd.read_csv(missing_path)
    df_summary = pd.read_csv(summary_path)
    assert_frame_equal(df_missing, self.analyzer.df_missing)
    self.assertEqual(len(df_summary), 1)
    self.assertEqual(df_summary.loc[0, 'city'], 'Oslo')
    self.assertEqual(df_summary.loc[0, 'elementId'], 'e1')
    self.assertEqual(df_summary.loc[0, 'num_missing'], 1)


class TestMissingDataConverter(unittest.TestCase):
    """Tester MissingDataConverter."""

    def setUp(self):
        """Lager midlertidig mappe og testdata."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.tempdir.name, 'missing.csv')

        df = pd.DataFrame({
            'date': ['2025-05-01', '2025-05-02', '2025-05-03'],
            'timeOffset': [0, 0, 0],
            'elementId': ['e1', 'e2', 'e3'],
            'oslo_value': [None, 5, None],
            'tromso_value': [10, None, None]
        })
        df.to_csv(self.csv_path, index=False)
        self.converter = MissingDataConverter()

    def tearDown(self):
        """Fjerner midlertidig mappe."""
        self.tempdir.cleanup()

    def test_read_missing_values(self):
        """Tester at manglende verdier blir lest riktig."""
        # Act
        df_out = self.converter.read_missing_values(self.csv_path)

        # Assert
        self.assertEqual(len(df_out), 3)
        self.assertListEqual(df_out.columns.tolist(), [
                             'date', 'timeOffset', 'elementId', 'missing'])
        self.assertEqual(df_out.iloc[0]['missing'], 'Oslo')
        self.assertEqual(df_out.iloc[1]['missing'], 'Tromsø')
        self.assertEqual(df_out.iloc[2]['missing'], 'Tromsø')


if __name__ == '__main__':
    unittest.main()
