"""Finner outliers i dataene ved hjelp av IQR-metoden."""

import pandas as pd

from basedata import DataLoader
from outlierdetector import OutlierDetector


class OutlierAnalysis(DataLoader):
    """Analyserer og rapporterer outliers per måned eller over statistic-variabler."""

    def __init__(
        self,
        data_dir: str,
        *,
        whisker: float | None = None,
    ) -> None:
        """
        Initialiserer OutlierAnalysis med data-katalog og whisker-verdi.

        Parametre:
            data_dir (str): Katalog med CSV-filer.
            whisker (float | None): Faktor for IQR-whisker. Hvis None, bruker default.
        """
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
        """
        Finn antall outliers per måned for gitt parameter.

        Parametre:
            city (str): Bykode, f.eks. "oslo".
            element_id (str): ElementId å analysere.
            time_offset (str | None): PT<n>H-offset. Finner minste hvis None.
            include_empty_months (bool): Ta med måneder uten datapunkter.

        Returnerer:
            pd.DataFrame: Kolonner ['year_month', 'outliers_removed',
            'total_count', 'outlier_percentage'].
        """
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
        df["year_month"] = (
            df["referenceTime"]
            .dt.tz_localize(None)
            .dt.to_period("M")
            .astype(str)
        )

        rows: list[dict[str, object]] = []
        for ym, grp in df.groupby("year_month"):
            mask = self.detector.detect_iqr(grp["value"], extreme=True)
            count = int(mask.sum())
            total = len(grp)
            if include_empty_months or count > 0:
                percentage = round(100 * count / total, 1) if total else 0.0
                rows.append(
                    {
                        "year_month": ym,
                        "outliers_removed": count,
                        "total_count": total,
                        "outlier_percentage": percentage,
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
        """
        Beregn en statistisk måleverdi med og uten outliers per måned.

        Parametre:
            city (str): Bykode.
            element_id (str): ElementId å analysere.
            time_offset (str | None): PT<n>H-offset. Finner minste hvis None.
            statistic (str): 'mean', 'median' eller 'std'.

        Returnerer:
            pd.DataFrame: Kolonner ['year_month',
            '<stat>_with_outliers', '<stat>_without_outliers',
            'outliers_removed', 'element_id'].

        Hever:
            ValueError: Hvis statistic ikke er gyldig.
        """
        valid_stats = {"mean", "median", "std"}
        if statistic not in valid_stats:
            raise ValueError(
                "statistic må være 'mean', 'median' eller 'std'"
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
        df["year_month"] = (
            df["referenceTime"]
            .dt.tz_localize(None)
            .dt.to_period("M")
            .astype(str)
        )

        rows: list[dict[str, object]] = []
        for ym, grp in df.groupby("year_month"):
            series = grp["value"]
            mask = self.detector.detect_iqr(series, extreme=True)

            non_na = series.dropna()
            if non_na.empty:
                continue

            cleaned = series[~mask].dropna()
            if statistic == "mean":
                full_val = series.mean()
                clean_val = cleaned.mean() if not cleaned.empty else None
            elif statistic == "median":
                full_val = series.median()
                clean_val = cleaned.median() if not cleaned.empty else None
            else:
                full_val = series.std(ddof=0)
                clean_val = (
                    cleaned.std(ddof=0)
                    if not cleaned.empty
                    else None
                )

            rows.append(
                {
                    "year_month": ym,
                    f"{statistic}_with_outliers": round(full_val, 3),
                    f"{statistic}_without_outliers": (
                        round(clean_val, 3) if clean_val is not None else None
                    ),
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


__all__ = ["OutlierAnalysis"]
