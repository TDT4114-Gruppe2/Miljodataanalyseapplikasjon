"""Tester yearlystats.py."""

import pandas as pd
import unittest

from src.analysis.yearlystats import YearlyStats
from src.analysis.outlierdetector import OutlierDetector


class DummyYearlyStats(YearlyStats):
    """Gi dummy-data for testing."""

    def __init__(self, df):
        """Initialisér DummyYearlyStats."""
        super().__init__(data_dir="", whisker=None)
        self._df = df
        self.detector = OutlierDetector(whisker=None)

    def _load_city(self, city):
        """Hent data for en by."""
        return self._df.copy()

    def _get_min_offset(self, city, element_id):
        """Hent minste offset for en by og element."""
        return self._df['timeOffset'].iloc[0]


class TestYearlyStats(unittest.TestCase):
    """Tester YearlyStats."""

    @classmethod
    def setUpClass(cls):
        """Setter opp testdata."""
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
        """Tester compute_yearly med mean."""
        df = self.loader.compute_yearly('city', 'e', aggregate='mean')
        years = set(df['year'])
        self.assertEqual(years, {2020, 2021})
        mean2020 = df[df['year'] == 2020]['value'].iloc[0]
        self.assertAlmostEqual(mean2020, 6.5)

    def test_compute_yearly_sum(self):
        """Tester compute_yearly med sum."""
        df = self.loader.compute_yearly('city', 'e', aggregate='sum')
        total = df[df['year'] == 2021]['value'].iloc[0]
        self.assertEqual(total, sum(range(13, 25)))

    def test_compute_yearly_median(self):
        """Tester compute_yearly med median."""
        df = self.loader.compute_yearly('city', 'e', aggregate='median')
        med2020 = df[df['year'] == 2020]['value'].iloc[0]
        self.assertEqual(med2020, 6.5)

    def test_compute_yearly_std(self):
        """Tester compute_yearly med std."""
        df = self.loader.compute_yearly('city', 'e', aggregate='std')
        std2020 = df[df['year'] == 2020]['value'].iloc[0]
        self.assertAlmostEqual(std2020, pd.Series(range(1, 13)).std())

    def test_compute_yearly_raw_requires_year(self):
        """Tester compute_yearly uten aggregat."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', aggregate=None)

    def test_compute_yearly_raw_no_data(self):
        """Tester compute_yearly uten aggregat og uten data."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', year=1999, aggregate=None)

    def test_invalid_aggregate_raises(self):
        """Tester compute_yearly med ugyldig aggregat."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', aggregate='invalid')


class TestPercentChange(unittest.TestCase):
    """Tester percent_change metoden."""

    @classmethod
    def setUpClass(cls):
        """Setter opp testdata for prosentvis endring."""
        times = pd.date_range('2021-01-01', periods=3, freq='D', tz='UTC')
        records = []
        for i, t in enumerate(times):
            records.append({'referenceTime': t, 'elementId': 'e',
                           'timeOffset': 'PT1H', 'value': str(i+1)})
        df = pd.DataFrame(records)
        cls.loader = DummyYearlyStats(df)

    def test_percent_change_daily(self):
        """Tester prosentvis endring per dag."""
        df = self.loader.percent_change(
            'city', 'e', statistic='mean', frequency='D')
        pct = list(df['percent_change'])
        self.assertAlmostEqual(pct[0], 100.0)
        self.assertAlmostEqual(pct[1], 50.0)

    def test_invalid_statistic(self):
        """Tester prosentvis endring med ugyldig statistikk."""
        with self.assertRaises(ValueError):
            self.loader.percent_change('city', 'e', statistic='sum')

    def test_invalid_frequency(self):
        """Tester prosentvis endring med ugyldig frekvens."""
        with self.assertRaises(ValueError):
            self.loader.percent_change('city', 'e', frequency='X')

    def test_percent_change_with_range(self):
        """Tester prosentvis endring med tidsintervall."""
        df = self.loader.percent_change(
            'city', 'e', statistic='mean',
            frequency='D', start='2021-01-02', end='2021-01-03')
        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df['percent_change'].iloc[0], 50.0)


class TestClimatologicalMonthlyMean(unittest.TestCase):
    """Tester klimatiske månedlige gjennomsnitt."""

    @classmethod
    def setUpClass(cls):
        """Setter opp testdata for klimatiske månedlige gjennomsnitt."""
        times = pd.date_range('2021-01-01', periods=6, freq='M', tz='UTC')
        records = []
        for i, t in enumerate(times):
            records.append({'referenceTime': t, 'elementId': 'e',
                           'timeOffset': 'PT1H', 'value': str(i+1)})
        df = pd.DataFrame(records)
        cls.loader = DummyYearlyStats(df)

    def test_climatological_mean(self):
        """Tester klimatiske månedlige gjennomsnitt."""
        df = self.loader.climatological_monthly_mean(
            'city', 'e', statistic='mean')
        self.assertEqual(set(df['month']), set(range(1, 7)))
        for idx, row in df.iterrows():
            self.assertEqual(row['value'], row['month'])
            self.assertEqual(row['month_name'], pd.Timestamp(
                f"2021-{row['month']:02d}-01").month_name()[:3])

    def test_invalid_statistic(self):
        """Tester klimatiske månedlige gjennomsnitt med ugyldig statistikk."""
        with self.assertRaises(ValueError):
            self.loader.climatological_monthly_mean(
                'city', 'e', statistic='sum')


if __name__ == '__main__':
    unittest.main()
