"""Tester basedata.py."""
import os
import pandas as pd
import tempfile
import unittest

from datetime import timezone

from src.analyseData.basedata import DataLoader


class TestDataLoader(unittest.TestCase):
    """Test DataLoader."""

    def setUp(self):
        """Lag en midlertidig katalog for testing."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.data_dir = self.tmpdir.name
        self.template = DataLoader.filename_template

    def tearDown(self):
        """Fjern den midlertidige katalogen."""
        self.tmpdir.cleanup()

    def _write_csv(self, city, df):
        """Skriv df til CSV i testkatalogen ved å bruke DataLoader-malen."""
        filename = self.template.format(city=city)
        path = os.path.join(self.data_dir, filename)
        df.to_csv(path, index=False)
        return path

    def test_load_nonexistent_raises(self):
        """Sjekk at DataLoader kaster feil om filen ikke finnes."""
        loader = DataLoader(self.data_dir)
        with self.assertRaises(FileNotFoundError) as cm:
            loader._load_city('missingcity')
        self.assertIn('Fant ikke datafil', str(cm.exception))

    def test_load_missing_referencetime_column(self):
        """Sjekk at DataLoader kaster feil om referenceTime mangler."""
        df = pd.DataFrame({'foo': [1, 2, 3]})
        self._write_csv('testcity', df)
        loader = DataLoader(self.data_dir)
        with self.assertRaises(KeyError) as cm:
            loader._load_city('testcity')
        self.assertIn("'referenceTime' mangler", str(cm.exception))

    def test_load_converts_referencetime(self):
        """Sjekk at referenceTime konverteres til datetime med UTC."""
        df = pd.DataFrame({
            'referenceTime': ['2021-01-01T00:00:00Z', '2021-01-02T12:30:00Z'],
            'elementId': ['e1', 'e2'],
            'timeOffset': ['PT1H', 'PT2H'],
            'value': ['10', '20'],
        })
        self._write_csv('city1', df)
        loader = DataLoader(self.data_dir)
        loaded = loader._load_city('city1')
        self.assertIn('referenceTime', loaded.columns)
        self.assertTrue(pd.api.types.is_datetime64_ns_dtype(
            loaded['referenceTime']))
        self.assertEqual(loaded['referenceTime'].dt.tz, timezone.utc)

    def test_get_min_offset_normal(self):
        """Lag en df med gyldig timeOffset."""
        df = pd.DataFrame({
            'referenceTime': ['2021-01-01T00:00:00Z']*3,
            'elementId': ['e']*3,
            'timeOffset': ['PT5H', 'PT2H', 'PT10H'],
            'value': ['1', '2', '3'],
        })
        self._write_csv('cityA', df)
        loader = DataLoader(self.data_dir)
        result = loader._get_min_offset('cityA', 'e')
        self.assertEqual(result, 'PT2H')

    def test_get_min_offset_no_offsets_raises(self):
        """Lag en df uten gyldige timeOffset for elementId."""
        df = pd.DataFrame({
            'referenceTime': ['2021-01-01T00:00:00Z'],
            'elementId': ['other'],
            'timeOffset': ['PT1H'],
            'value': ['5'],
        })
        self._write_csv('cityB', df)
        loader = DataLoader(self.data_dir)
        with self.assertRaises(ValueError) as cm:
            loader._get_min_offset('cityB', 'e')
        self.assertIn('Ingen timeOffset funnet', str(cm.exception))

    def test_get_min_offset_invalid_format_raises(self):
        """Lag en df med ugyldige format for timeOffset."""
        df = pd.DataFrame({
            'referenceTime': ['2021-01-01T00:00:00Z']*2,
            'elementId': ['e', 'e'],
            'timeOffset': ['BAD', 'WRONG'],
            'value': ['1', '2'],
        })
        self._write_csv('cityC', df)
        loader = DataLoader(self.data_dir)
        with self.assertRaises(ValueError) as cm:
            loader._get_min_offset('cityC', 'e')
        self.assertIn('Fant ingen gyldige PT', str(cm.exception))


if __name__ == '__main__':
    unittest.main()
