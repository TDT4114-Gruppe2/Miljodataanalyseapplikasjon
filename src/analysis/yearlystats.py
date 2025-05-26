"""Genererer årlige og periodiske statistikker fra værdata."""

import calendar
import pandas as pd

from basedata import DataLoader
from outlierdetector import OutlierDetector


class YearlyStats(DataLoader):
    """Utvider DataLoader med metoder for årlige og periodiske analyser."""

    def __init__(
        self,
        data_dir: str,
        *,
        whisker: float | None = None,
    ) -> None:
        """
        Initialiserer YearlyStats med data-katalog og whisker.

        Parametre:
            data_dir (str): Katalog med CSV-filer.
            whisker (float | None): Faktor for IQR-whisker
            (1.5, 3.0 eller None).
        """
        super().__init__(data_dir)
        self.detector = OutlierDetector(whisker)

    def compute_yearly(
        self,
        city: str,
        element_id: str,
        year: int | None = None,
        *,
        time_offset: str | None = None,
        aggregate: str | None = "mean",
    ) -> pd.DataFrame:
        """
        Beregn eller hent årlig statistikk.

        Parametre:
            city (str): Bykode, f.eks. 'oslo'.
            element_id (str): ElementId å analysere.
            year (int | None): År for rådata (krever aggregate=None).
            time_offset (str | None): PT<n>H-offset. Finner minste hvis None.
            aggregate (str | None): 'mean', 'sum', 'median', 'std' eller None.

        Returnerer:
            pd.DataFrame: Kolonner ['year', 'value']
            eller rådata hvis aggregate=None.

        Hever:
            ValueError: Ved manglende data eller ugyldige parametre.
        """
        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = (
            self._load_city(city)
            .query(
                "elementId == @element_id and timeOffset == @time_offset"
            )
            .assign(
                value=lambda d: pd.to_numeric(d["value"], errors="coerce")
            )
            .dropna(subset=["value"])
        )

        if aggregate is None:
            if year is None:
                raise ValueError(
                    "year må angis når aggregate=None (rådata)"
                )

            daily = df[df["referenceTime"].dt.year == year]
            if daily.empty:
                msg = (
                    f"Ingen data for city={city!r}, "
                    f"element_id={element_id!r}, "
                    f"year={year}"
                )
                raise ValueError(msg)
            return daily.reset_index(drop=True)

        # Filtrer på år hvis spesifisert
        df["year"] = df["referenceTime"].dt.year
        if year is not None:
            df = df[df["year"] == year]

        if df.empty:
            raise ValueError("Ingen data etter filtrering – sjekk parametrene")

        agg_funcs = {
            "mean": df.groupby("year")["value"].mean,
            "sum": df.groupby("year")["value"].sum,
            "median": df.groupby("year")["value"].median,
            "std": df.groupby("year")["value"].std,
        }
        if aggregate not in agg_funcs:
            raise ValueError(
                "aggregate må være 'mean', 'sum', 'median', 'std' eller None"
            )

        result = agg_funcs[aggregate]().reset_index(name="value")
        return result

    def percent_change(
        self,
        city: str,
        element_id: str,
        *,
        time_offset: str | None = None,
        statistic: str = "mean",
        frequency: str = "ME",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        Beregn prosentvis endring for en statistikk over perioder.

        Parametre:
            city (str): Bykode.
            element_id (str): ElementId å analysere.
            time_offset (str | None): PT<n>H-offset. Finner minste hvis None.
            statistic (str): 'mean', 'median' eller 'std'.
            frequency (str): 'D', 'ME' (måned) eller 'YE' (år).
            start (str | None): Startperiode som ISO-dato.
            end (str | None): Sluttperiode som ISO-dato.

        Returnerer:
            pd.DataFrame: Kolonner
            ['referenceTime', 'value', 'percent_change'].
        """
        valid_stats = {"mean", "median", "std"}
        if statistic not in valid_stats:
            raise ValueError(
                "statistic må være 'mean', 'median' eller 'std'"
            )
        valid_freq = {"D", "ME", "YE"}
        if frequency not in valid_freq:
            raise ValueError(
                "frequency må være 'D', 'ME' eller 'YE'"
            )

        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = (
            self._load_city(city)
            .query(
                "elementId == @element_id and timeOffset == @time_offset"
            )
            .assign(
                value=lambda d: pd.to_numeric(d["value"], errors="coerce"),
                referenceTime=lambda d: pd.to_datetime(
                    d["referenceTime"], utc=True
                ),
            )
            .set_index("referenceTime")
            .sort_index()
        )

        # Filtrer periode
        if start or end:
            mask = pd.Series(True, index=df.index)
            if start:
                mask &= df.index >= pd.to_datetime(start).tz_localize("UTC")
            if end:
                mask &= df.index <= pd.to_datetime(end).tz_localize("UTC")
            df = df[mask]

        resampled = df["value"].resample(frequency)
        agg_funcs = {
            "mean": resampled.mean,
            "median": resampled.median,
            "std": lambda: resampled.std(ddof=0),
        }
        series = agg_funcs[statistic]()

        out = pd.DataFrame({"value": series})
        out["percent_change"] = out["value"].pct_change() * 100
        out = (
            out.dropna()
            .reset_index()
            .rename(columns={"referenceTime": "period"})
        )
        return out

    def climatological_monthly_mean(
        self,
        city: str,
        element_id: str,
        *,
        time_offset: str | None = None,
        remove_outliers: bool = False,
        statistic: str = "mean",
    ) -> pd.DataFrame:
        """
        Beregn gjennomsnittelig månedlig statistisk verdi (klimatologi).

        Parametre:
            city (str): Bykode.
            element_id (str): ElementId å analysere.
            time_offset (str | None): PT<n>H-offset. Finner minste hvis None.
            remove_outliers (bool): Om outliers skal fjernes.
            statistic (str): 'mean', 'median' eller 'std'.

        Returnerer:
            pd.DataFrame: Kolonner ['month', 'month_name', 'value'].
        """
        valid_stats = {"mean", "median", "std"}
        if statistic not in valid_stats:
            raise ValueError(
                "statistic må være 'mean', 'median' eller 'std'"
            )

        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = (
            self._load_city(city)
            .query(
                "elementId == @element_id and timeOffset == @time_offset"
            )
            .copy()
        )
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(
            df["referenceTime"], utc=True
        )

        if remove_outliers:
            mask = self.detector.detect_iqr(
                df["value"], extreme=True
            )
            df.loc[mask, "value"] = pd.NA

        df["month"] = df["referenceTime"].dt.month
        agg_funcs = {
            "mean": df.groupby("month")["value"].mean,
            "median": df.groupby("month")["value"].median,
            "std": lambda: df.groupby("month")["value"].std(ddof=0),
        }
        result = agg_funcs[statistic]().reset_index(name="value")
        result["month_name"] = result["month"].apply(
            lambda m: calendar.month_abbr[m].capitalize()
        )
        return result[["month", "month_name", "value"]]


__all__ = ["YearlyStats"]
