"""Genererer årlige data."""
import calendar
import pandas as pd
from basedata import DataLoader
from outlierdetector import OutlierDetector


class YearlyStats(DataLoader):
    """Genererer årlige data."""

    def __init__(
        self,
        data_dir: str,
        *,
        whisker: float | None = None,
    ) -> None:
        """Initialiserer YearlyStats med data-katalog."""
        super().__init__(data_dir)
        self.detector = OutlierDetector(whisker)

    def compute_yearly(
        self,
        city: str,
        element_id: str,
        year: int | None = None,
        *,
        time_offset: str | None = None,
        aggregate: str = "mean",
    ) -> pd.DataFrame:
        """Beregn årlig aggregert statistikk eller returner rådata."""
        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = (
            self._load_city(city)
            .query(
                "elementId == @element_id and "
                "timeOffset == @time_offset"
            )
            .assign(
                value=lambda d: pd.to_numeric(
                    d["value"], errors="coerce"
                )
            )
            .dropna(subset=["value"])
        )

        if aggregate is None:
            if year is None:
                raise ValueError(
                    "year må angis når aggregate=None (rå verdier)"
                )
            daily = df[df["referenceTime"].dt.year == year]
            if daily.empty:
                raise ValueError(
                    f"Ingen data for city='{city}', "
                    f"element_id='{element_id}', year={year}"
                )
            return daily.reset_index(drop=True)

        df["year"] = df["referenceTime"].dt.year
        if year is not None:
            df = df[df["year"] == year]

        if df.empty:
            raise ValueError(
                "Ingen data etter filtrering – sjekk parametrene"
            )

        agg_map = {
            "mean": df.groupby("year")["value"].mean,
            "sum": df.groupby("year")["value"].sum,
            "median": df.groupby("year")["value"].median,
            "std": df.groupby("year")["value"].std,
        }
        if aggregate not in agg_map:
            raise ValueError(
                "aggregate må være 'mean', 'sum', 'median', 'std' eller None"
            )

        out = agg_map[aggregate]().reset_index(name="value")
        return out

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
        """Beregn prosentvis endring for en gitt statistikk over tid."""
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

        df = self._load_city(city)
        df = df[
            (df["elementId"] == element_id)
            & (df["timeOffset"] == time_offset)
        ].copy()

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(
            df["referenceTime"], utc=True
        )
        df.set_index("referenceTime", inplace=True)
        df.sort_index(inplace=True)

        if start or end:
            mask = pd.Series(True, index=df.index)
            if start:
                mask &= df.index >= pd.to_datetime(start).tz_localize(
                    "UTC"
                )
            if end:
                mask &= df.index <= pd.to_datetime(end).tz_localize(
                    "UTC"
                )
            df = df[mask]

        resampled = df["value"].resample(frequency)
        agg_map = {
            "mean": resampled.mean,
            "median": resampled.median,
            "std": lambda: resampled.std(ddof=0),
        }
        series = agg_map[statistic]()

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
        """Beregn klimatologisk månedlig statistikk."""
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
                "elementId == @element_id and "
                "timeOffset == @time_offset"
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
        agg_map = {
            "mean": df.groupby("month")["value"].mean,
            "median": df.groupby("month")["value"].median,
            "std": lambda: df.groupby("month")["value"].std(
                ddof=0
            ),
        }
        clim = agg_map[statistic]().reset_index()
        clim = clim.rename(columns={"value": "value"})
        clim["month_name"] = clim["month"].apply(
            lambda m: calendar.month_abbr[m].capitalize()
        )
        return clim[["month", "month_name", "value"]]


__all__ = ["YearlyStats"]
