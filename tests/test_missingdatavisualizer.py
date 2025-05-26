"""Tester missingdatavisualizer.py."""

import matplotlib.pyplot as plt
import missingno as msno
import os
import pandas as pd
import tempfile
import unittest

from src.missingData.missingdatavisualizer import (
    _validate_csv_path,
    MissingDataVisualizer
)


class TestValidateCSVPath(unittest.TestCase):
    """Tester _validate_csv_path."""

    def test_validate_existing(self):
        """Tester at eksisterende fil ikke viser feil."""
        with tempfile.NamedTemporaryFile() as tmp:
            _validate_csv_path(tmp.name)

    def test_validate_missing(self):
        """Tester at manglende fil viser FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            _validate_csv_path('nonexistent_file.csv')


class TestMissingDataVisualizer(unittest.TestCase):
    """Tester MissingDataVisualizer."""

    def setUp(self):
        """Setter opp testmiljø med midlertidig CSV-fil."""
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

    def tearDown(self):
        """Fjerner midlertidig mappe."""
        self.tempdir.cleanup()

    def test_init_and_date_conversion(self):
        """Tester init og at dato blir konvertert til datetime."""
        viz = MissingDataVisualizer(self.csv_path)
        self.assertTrue(hasattr(viz, 'df_missing'))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(
            viz.df_missing['date']))

    def test_get_summary(self):
        """Tester at sammendrag-df blir generert riktig."""
        viz = MissingDataVisualizer(self.csv_path)
        summary = viz.get_summary()
        self.assertListEqual(list(summary.columns), [
                             'city', 'elementId', 'num_missing'])
        totals = summary.groupby('city')['num_missing'].sum()
        self.assertEqual(int(totals['Oslo']), 1)
        self.assertEqual(int(totals['Tromsø']), 2)

    def test_prepare_city_wide(self):
        """Tester at bred df for by genereres korrekt."""
        viz = MissingDataVisualizer(self.csv_path)
        wide_oslo = viz.prepare_city_wide('Oslo')
        self.assertTrue((wide_oslo['e1'] == 1.0).any())
        self.assertTrue((wide_oslo['e2'] == 0.0).all())
        expected_cols = list(pd.read_csv(self.csv_path)['elementId'].unique())
        self.assertListEqual(
            sorted(wide_oslo.columns.tolist()), sorted(expected_cols))

    def test_plot_methods_no_error(self):
        """Tester at plot-metoder ikke kaster feil."""
        viz = MissingDataVisualizer(self.csv_path)
        with unittest.mock.patch.object(plt, 'show'), \
                unittest.mock.patch.object(msno, 'heatmap'):
            viz.plot_summary_bar()
            viz.plot_heatmap('Oslo')
            viz.plot_missing_timeline('Tromsø')

    def test_plot_missing_timeline_invalid_city(self):
        """Tester at plot_missing_timeline viser feil for ugyldig by."""
        viz = MissingDataVisualizer(self.csv_path)
        with self.assertRaises(ValueError):
            viz.plot_missing_timeline('Bergen')


if __name__ == '__main__':
    unittest.main()
