"""Test outlieranalysis.py."""

import calendar
import pandas as pd
import unittest

from src.analyseData.yearlystats import YearlyStats
from src.analyseData.outlieranalysis import OutlierAnalysis
from src.analyseData.outlierdetector import OutlierDetector


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
        """Test at yearly mean beregnes riktig."""
        df = self.loader.compute_yearly('city', 'e', aggregate='mean')
        self.assertEqual(set(df['year']), {2020, 2021})
        self.assertAlmostEqual(df[df['year'] == 2020]['value'].iloc[0], 6.5)

    def test_compute_yearly_sum(self):
        """Test at årlig sum beregnes riktig."""
        df = self.loader.compute_yearly('city', 'e', aggregate='sum')
        self.assertEqual(df[df['year'] == 2021]
                         ['value'].iloc[0], sum(range(13, 25)))

    def test_compute_yearly_median(self):
        """Test at årlig median beregnes riktig."""
        df = self.loader.compute_yearly('city', 'e', aggregate='median')
        self.assertEqual(df[df['year'] == 2020]['value'].iloc[0], 6.5)

    def test_compute_yearly_std(self):
        """Tester at årlig standardavvik beregnes riktig."""
        df = self.loader.compute_yearly('city', 'e', aggregate='std')
        self.assertAlmostEqual(
            df[df['year'] == 2020]['value'].iloc[0],
            pd.Series(range(1, 13)).std())

    def test_raw_requires_year(self):
        """Test at raw data krever år."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', aggregate=None)

    def test_raw_no_data(self):
        """Test at ingen data gir feil."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', year=1999, aggregate=None)

    def test_invalid_aggregate(self):
        """Test at ugyldig aggregat gir feil."""
        with self.assertRaises(ValueError):
            self.loader.compute_yearly('city', 'e', aggregate='foo')


class TestPercentChange(unittest.TestCase):
    """Test percent_change i YearlyStats."""

    @classmethod
    def setUpClass(cls):
        """Sett opp testdata."""
        times = pd.date_range('2021-01-01', periods=3, freq='D', tz='UTC')
        records = [{'referenceTime': t, 'elementId': 'e', 'timeOffset': 'PT1H',
                    'value': str(i+1)} for i, t in enumerate(times)]
        cls.loader = DummyYearlyStats(pd.DataFrame(records))

    def test_daily_change(self):
        """Test at daglig endring beregnes riktig."""
        df = self.loader.percent_change(
            'city', 'e', statistic='mean', frequency='D')
        self.assertAlmostEqual(df['percent_change'].iloc[0], 100.0)
        self.assertAlmostEqual(df['percent_change'].iloc[1], 50.0)

    def test_invalid_statistic(self):
        """Test at ugyldig statistikk gir feil."""
        with self.assertRaises(ValueError):
            self.loader.percent_change('city', 'e', statistic='sum')

    def test_invalid_frequency(self):
        """Test at ugyldig frekvens gir feil."""
        with self.assertRaises(ValueError):
            self.loader.percent_change('city', 'e', frequency='X')

    def test_with_date_filter(self):
        """Test at prosentvis endring med datofilter fungerer."""
        df = self.loader.percent_change(
            'city', 'e', statistic='mean',
            frequency='D', start='2021-01-02', end='2021-01-03')
        self.assertEqual(len(df), 1)
        self.assertAlmostEqual(df['percent_change'].iloc[0], 50.0)


class TestClimatology(unittest.TestCase):
    """Test climatological_monthly_mean i YearlyStats."""

    @classmethod
    def setUpClass(cls):
        """Sett opp testdata."""
        times = pd.date_range('2021-01-01', periods=6, freq='M', tz='UTC')
        records = [{'referenceTime': t, 'elementId': 'e', 'timeOffset': 'PT1H',
                    'value': str(i+1)} for i, t in enumerate(times)]
        cls.loader = DummyYearlyStats(pd.DataFrame(records))

    def test_monthly_mean(self):
        """Test at månedlig gjennomsnitt beregnes riktig."""
        df = self.loader.climatological_monthly_mean(
            'city', 'e', statistic='mean')
        self.assertEqual(set(df['month']), set(range(1, 7)))
        for row in df.itertuples():
            self.assertEqual(row.value, row.month)
            self.assertEqual(
                row.month_name, calendar.month_abbr[row.month].capitalize())

    def test_remove_outliers(self):
        """Test at månedlig gjennomsnitt uten utliggere fungerer."""
        df = self.loader.climatological_monthly_mean(
            'city', 'e', remove_outliers=True)
        self.assertTrue(all(df['value'].notna()))

    def test_invalid_statistic(self):
        """Test at ugyldig statistikk gir feil."""
        with self.assertRaises(ValueError):
            self.loader.climatological_monthly_mean(
                'city', 'e', statistic='sum')


class DummyOutlierAnalysis(OutlierAnalysis):
    """Bruk dummydata for testing OutlierAnalysis."""

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


class TestOutlierAnalysis(unittest.TestCase):
    """Test OutlierAnalysis methods."""

    @classmethod
    def setUpClass(cls):
        """Sett opp testdata for OutlierAnalysis."""
        times = pd.date_range('2021-01-01', periods=4, freq='M', tz='UTC')
        records = []
        for i, t in enumerate(times):
            # Create two values, one extreme
            records += [
                {'referenceTime': t, 'elementId': 'e',
                    'timeOffset': 'PT1H', 'value': '10'},
                {'referenceTime': t, 'elementId': 'e',
                    'timeOffset': 'PT1H', 'value': str(100+i)}
            ]
        cls.df = pd.DataFrame(records)
        cls.loader = DummyOutlierAnalysis(cls.df)

    def test_find_outliers(self):
        """Test at utliggere finnes riktig."""
        df = self.loader.find_outliers_per_month(
            'city', 'e', time_offset='PT1H', include_empty_months=True)
        # Expect no outliers detected with default IQR settings
        self.assertEqual(len(df), 4)
        self.assertTrue(all(df['outliers_removed'] == 0))

    def test_stats_with_without(self):
        """Test at statistikk med og uten utliggere fungerer."""
        df = self.loader.stats_with_without_outliers(
            'city', 'e', time_offset='PT1H', statistic='mean')
        # No outliers removed with default IQR settings
        self.assertTrue(all(df['outliers_removed'] == 0))
        self.assertIn('mean_with_outliers', df.columns)

    def test_invalid_statistic(self):
        """Test at ugyldig statistikk gir feil."""
        with self.assertRaises(ValueError):
            self.loader.stats_with_without_outliers(
                'city', 'e', statistic='sum')


if __name__ == '__main__':
    unittest.main()
