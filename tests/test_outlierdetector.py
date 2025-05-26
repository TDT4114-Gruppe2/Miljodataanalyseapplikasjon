"""Test outlierdeteector.py."""

import calendar
import pandas as pd
import unittest

from src.analysis.yearlystats import YearlyStats
from src.analysis.outlierdetector import OutlierDetector


class DummyYearlyStats(YearlyStats):
    """Bruk dummydata for testing."""

    def __init__(self, df):
        """Initialisér dummydata."""
        super().__init__(data_dir="", whisker=None)
        self._df = df
        self.detector = OutlierDetector(whisker=None)

    def _load_city(self, city):
        """Hent data for en by."""
        return self._df.copy()

    def _get_min_offset(self, city, element_id):
        """Hent minste timeoffset for et element."""
        return self._df['timeOffset'].iloc[0]


class TestYearlyStats(unittest.TestCase):
    """Test YearlyStats."""

    @classmethod
    def setUpClass(cls):
        """Sett opp testdata."""
        times = pd.date_range('2020-01-01', periods=24, freq='M', tz='UTC')
        records = []
        for i, t in enumerate(times):
            records.append({
                'referenceTime': t,
                'elementId': 'e',
                'timeOffset': 'PT1H',
                'value': str(i+1)
            })
        cls.df = pd.DataFrame(records)
        cls.loader = DummyYearlyStats(cls.df)

    def test_compute_yearly_mean(self):
        """Test at årlig mean beregnes riktig."""
        df = self.loader.compute_yearly('city', 'e', aggregate='mean')
        self.assertEqual(set(df['year']), {2020, 2021})
        self.assertAlmostEqual(df[df['year'] == 2020]['value'].iloc[0], 6.5)

    def test_compute_yearly_sum(self):
        """Test at årlig sum beregnes riktig."""
        df = self.loader.compute_yearly('city', 'e', aggregate='sum')
        self.assertEqual(df[df['year'] == 2021]['value'].iloc[0],
                         sum(range(13, 25)))

    def test_compute_yearly_std(self):
        """Test at årlig standardavvik beregnes riktig."""
        df = self.loader.compute_yearly('city', 'e',
                                        aggregate='std')
        expected = pd.Series(range(1, 13)).std()
        self.assertAlmostEqual(df[df['year'] == 2020]
                               ['value'].iloc[0], expected)

    def test_raw_requires_year(self):
        """Test at rådata krever år."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', aggregate=None)

    def test_invalid_aggregate(self):
        """Test at ugyldig aggregat hever feil."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', aggregate='foo')


class TestPercentChange(unittest.TestCase):
    """Test prosentvis endring i YearlyStats."""

    @classmethod
    def setUpClass(cls):
        """Sett opp testdata for prosentvis endring."""
        times = pd.date_range('2021-01-01', periods=3,
                              freq='D', tz='UTC')
        records = [
            {'referenceTime': t, 'elementId': 'e',
                'timeOffset': 'PT1H', 'value': str(i+1)}
            for i, t in enumerate(times)
        ]
        cls.loader = DummyYearlyStats(pd.DataFrame(records))

    def test_daily_change(self):
        """Test at daglig prosentvis endring beregnes riktig."""
        df = self.loader.percent_change(
            'city', 'e', statistic='mean', frequency='D')
        self.assertAlmostEqual(df['percent_change'].iloc[0], 100.0)
        self.assertAlmostEqual(df['percent_change'].iloc[1], 50.0)

    def test_invalid_statistic(self):
        """Test at ugyldig statistikk hever feil."""
        with self.assertRaises(ValueError):
            self.loader.percent_change('city', 'e', statistic='sum')

    def test_invalid_frequency(self):
        """Test at ugyldig frekvens hever feil."""
        with self.assertRaises(ValueError):
            self.loader.percent_change('city', 'e', frequency='X')

    def test_with_date_filter(self):
        """Test at prosentvis endring med datofilter fungerer."""
        df = self.loader.percent_change(
            'city', 'e', statistic='mean', frequency='D',
            start='2021-01-02', end='2021-01-03'
        )
        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df['percent_change'].iloc[0], 50.0)


class TestClimatology(unittest.TestCase):
    """Test klimadata i YearlyStats."""

    @classmethod
    def setUpClass(cls):
        """Sett opp testdata for klimadata."""
        times = pd.date_range('2021-01-01',
                              periods=6, freq='M', tz='UTC')
        records = [
            {'referenceTime': t, 'elementId': 'e',
                'timeOffset': 'PT1H', 'value': str(i+1)}
            for i, t in enumerate(times)
        ]
        cls.loader = DummyYearlyStats(pd.DataFrame(records))

    def test_monthly_mean(self):
        """Test at månedlig mean beregnes riktig."""
        df = self.loader.climatological_monthly_mean(
            'city', 'e', statistic='mean')
        self.assertEqual(set(df['month']), set(range(1, 7)))
        for row in df.itertuples():
            self.assertEqual(row.value, row.month)
            self.assertEqual(
                row.month_name,
                calendar.month_abbr[row.month].capitalize())

    def test_remove_outliers(self):
        """Test at outliers fjernes riktig i klimadata."""
        df = self.loader.climatological_monthly_mean(
            'city', 'e', remove_outliers=True)
        self.assertTrue(all(df['value'].notna()))

    def test_invalid_statistic(self):
        """Test at ugyldig statistikk hever feil."""
        with self.assertRaises(ValueError):
            self.loader.climatological_monthly_mean(
                'city', 'e', statistic='sum')


class TestOutlierDetector(unittest.TestCase):
    """Test OutlierDetector."""

    def test_valid_initialization(self):
        """Test at gyldige whisker-verdier initialiseres riktig."""
        for w in (None, 1.5, 3.0):
            det = OutlierDetector(whisker=w)
            self.assertEqual(det.whisker, w)

    def test_invalid_initialization(self):
        """Test at ugyldige whisker-verdier hever feil."""
        with self.assertRaises(ValueError):
            OutlierDetector(whisker=2.0)

    def test_summarize(self):
        """Test at oppsummering av serie fungerer som forventet."""
        series = pd.Series([1, 2, 3, 4])
        det = OutlierDetector()
        summ = det.summarize(series)
        self.assertAlmostEqual(summ['Q1'], 1.75)
        self.assertAlmostEqual(summ['Q3'], 3.25)
        self.assertAlmostEqual(summ['IQR'], 1.5)
        self.assertAlmostEqual(summ['lower_inner'], 1.75 - 1.5*1.5)
        self.assertAlmostEqual(summ['upper_outer'], 3.25 + 3.0*1.5)

    def test_detect_iqr_extreme_and_custom(self):
        """Test at ekstreme og tilpassede whisker fungerer som forventet."""
        series = pd.Series([0, 1, 2, 3, 4, 100])
        det = OutlierDetector()
        mask_ext = det.detect_iqr(series, extreme=True)
        self.assertEqual(mask_ext.sum(), 1)
        mask_cust = det.detect_iqr(series, whisker=3.0)
        self.assertEqual(mask_cust.sum(), 1)

    def test_detect_iqr_invalid_whisker(self):
        """Test at ugyldig whisker hever feil ved deteksjon."""
        series = pd.Series([1, 2, 3])
        det = OutlierDetector()
        with self.assertRaises(ValueError):
            det.detect_iqr(series, whisker=0)

    def test_count_and_remove_outliers(self):
        """Test telling og fjerning av outliers."""
        series = pd.Series([1, 2, 3, 4, 20])
        det = OutlierDetector()
        count = det.count_outliers_iqr(series)
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 1)
        cleaned = det.remove_outliers_iqr(series)
        self.assertTrue(pd.isna(cleaned.iloc[-1]))
        self.assertFalse(pd.isna(cleaned.iloc[0]))


if __name__ == '__main__':
    unittest.main()
