"""Finner outliers i dataene ved hjelp av IQR-metoden."""
import pandas as pd
from base_data import DataLoader


class OutlierDetector:
    """
    IQR‑basert deteksjon/fjerning av utliggere.

    whisker = 1.5 (vanlige) eller 3.0 (ekstreme). None = velg dynamisk.
    """

    def __init__(self, whisker: float | None = None):
        """Definerer hva verdien for en outlier er."""
        if whisker not in (None, 1.5, 3.0):
            raise ValueError("whisker må være 1.5, 3.0 eller None")
        self.whisker = whisker

    def summarize(self, series: pd.Series) -> dict[str, float]:
        """Returnerer grunnleggende IQR-statistikk for en serie."""
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)
        iqr = q3 - q1
        return {
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "lower_inner": q1 - 1.5 * iqr,
            "upper_inner": q3 + 1.5 * iqr,
            "lower_outer": q1 - 3.0 * iqr,
            "upper_outer": q3 + 3.0 * iqr,
        }

    def detect_iqr(
        self,
        series: pd.Series,
        *,
        extreme: bool = False,
        whisker: float | None = None,
    ) -> pd.Series:
        """Finner outliers i serien."""
        whisker = whisker if whisker is not None else (
            self.whisker or (3.0 if extreme else 1.5)
        )
        if whisker <= 0:
            raise ValueError("whisker må være positiv")

        numeric = pd.to_numeric(series, errors="coerce")
        q1, q3 = numeric.quantile([0.25, 0.75])
        iqr = q3 - q1

        lower = q1 - whisker * iqr
        upper = q3 + whisker * iqr
        return (numeric < lower) | (numeric > upper)

    # Teller og fjerner outliers
    def count_outliers_iqr(self, series, **kwargs) -> int:
        """Returnerer antall outliers i serien."""
        return int(self.detect_iqr(series, **kwargs).sum())

    def remove_outliers_iqr(self, series, **kwargs) -> pd.Series:
        """Fjerner outliers fra serien."""
        mask = self.detect_iqr(series, **kwargs)
        return series.where(~mask)

    @staticmethod
    def detect(series, extreme: bool = False):
        """Finner outliers i serien."""
        return OutlierDetector().detect_iqr(series, extreme=extreme)


class OutlierAnalysis(DataLoader):
    """Analyserer outliers."""

    def __init__(self, data_dir: str, *, whisker: float | None = None):
        """Initialiserer OutlierAnalysis med data_dir og whisker."""
        super().__init__(data_dir)
        self.detector = OutlierDetector(whisker)

    def find_outliers_per_month(
        self,
        city: str,
        element_id: str,
        *,
        time_offset: str | None = None,
        include_empty_months: bool = False,
    ) -> pd.DataFrame:
        """Finner outliers per måned."""
        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = self._load_city(city)
        df = df[
            (df["elementId"] == element_id)
            & (df["timeOffset"] == time_offset)
        ].copy()

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(df["referenceTime"], utc=True)
        df["year_month"] = (
            df["referenceTime"]
            .dt.tz_localize(None)
            .dt.to_period("M")
            .astype(str)
        )

        rows: list[dict] = []
        for ym, grp in df.groupby("year_month"):
            mask = self.detector.detect_iqr(grp["value"], extreme=True)
            count = int(mask.sum())
            if include_empty_months or count > 0:
                rows.append(
                    {
                        "year_month": ym,
                        "outliers_removed": count,
                        "total_count": len(grp),
                        "outlier_percentage": round(100 * count / len(grp), 1)
                        if len(grp)
                        else 0.0,
                    }
                )

        return (
            pd.DataFrame(rows)
            .sort_values("year_month")
            .reset_index(drop=True)
        )

    def stats_with_without_outliers(
        self,
        city: str,
        element_id: str,
        *,
        time_offset: str | None = None,
        statistic: str,
    ) -> pd.DataFrame:
        """Finner statistikk med og uten utliggere."""
        if statistic not in {"mean", "median", "std"}:
            raise ValueError("statistic må være 'mean', 'median' eller 'std'")

        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = self._load_city(city)
        df = df[
            (df["elementId"] == element_id)
            & (df["timeOffset"] == time_offset)
        ].copy()

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(df["referenceTime"], utc=True)
        df["year_month"] = (
            df["referenceTime"]
            .dt.tz_localize(None)
            .dt.to_period("M")
            .astype(str)
        )

        rows: list[dict] = []
        for ym, grp in df.groupby("year_month"):
            series = grp["value"]
            mask = self.detector.detect_iqr(series, extreme=True)

            if series.dropna().empty:
                continue

            cleaned = series.where(~mask).dropna()
            if statistic == "mean":
                full_val = series.mean()
                clean_val = cleaned.mean() if not cleaned.empty else None
            elif statistic == "median":
                full_val = series.median()
                clean_val = cleaned.median() if not cleaned.empty else None
            else:
                full_val = series.std(ddof=0)
                clean_val = (
                    cleaned.std(ddof=0) if not cleaned.empty else None
                )

            rows.append(
                {
                    "year_month": ym,
                    f"{statistic}_with_outliers": round(full_val, 3),
                    f"{statistic}_without_outliers": round(clean_val, 3)
                    if clean_val is not None
                    else None,
                    "outliers_removed": int(mask.sum()),
                    "element_id": element_id,
                }
            )

        cols = [
            "year_month",
            f"{statistic}_with_outliers",
            f"{statistic}_without_outliers",
            "outliers_removed",
            "element_id",
        ]
        return (
            pd.DataFrame(rows, columns=cols)
            .sort_values("year_month")
            .reset_index(drop=True)
        )

__all__ = ["OutlierDetector", "OutlierAnalysis"]
