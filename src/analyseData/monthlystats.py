"""Genererer månedlige statistikker fra værdata."""

import numpy as np
import pandas as pd

from basedata import DataLoader


class MonthlyStats(DataLoader):
    """Utvider DataLoader med metoder for månedlig statistikk."""

    @staticmethod
    def _select_values(
        df: pd.DataFrame,
        year_month: str | None,
        element_id: str,
        time_offset: str,
    ) -> pd.Series:
        """
        Filtrerer rader etter element, tidsoffset og måned.

        Parametre:
            df (pd.DataFrame): DataFrame med rådata.
            year_month (str | None): År-måned streng (YYYY-MM)
            eller None for alle.
            element_id (str): ElementId å filtrere på.
            time_offset (str): PT<n>H offset.

        Returnerer:
            pd.Series: Numeriske verdier for valgte rader.

        Hever:
            ValueError: Hvis ingen datapunkter finnes.
        """
        mask = (
            df["elementId"].eq(element_id)
            & df["timeOffset"].eq(time_offset)
        )
        if year_month is not None:
            mask &= (
                df["referenceTime"]
                .dt.strftime("%Y-%m")
                .eq(year_month)
            )

        vals = (
            pd.to_numeric(
                df.loc[mask, "value"], errors="coerce"
            )
            .dropna()
        )
        if vals.empty:
            raise ValueError(
                "Ingen datapunkter for "
                f"element_id={element_id!r}, time_offset={time_offset!r}, "
                f"month={year_month!r}"
            )

        return vals

    def compute_single_month(
        self,
        year_month: str,
        element_id: str,
        city: str,
        time_offset: str | None = None,
    ) -> dict[str, float]:
        """
        Beregn statistikk for én måned.

        Parametre:
            year_month (str): "YYYY-MM".
            element_id (str): Element å beregne for.
            city (str): Bykode.
            time_offset (str | None): Offset, finner minste hvis None.

        Returnerer:
            dict[str, float]: mean, median og std.
        """
        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = self._load_city(city)
        vals = self._select_values(
            df, year_month, element_id, time_offset
        )
        return {
            "mean": float(vals.mean()),
            "median": float(vals.median()),
            "std": float(vals.std(ddof=0)),
        }

    def compute_all_months(
        self,
        element_id: str,
        city: str,
        time_offset: str | None = None,
    ) -> pd.DataFrame:
        """
        Beregn statistikk for alle måneder.

        Parametre:
            element_id (str): Element å beregne for.
            city (str): Bykode.
            time_offset (str | None): Offset, finner minste hvis None.

        Returnerer:
            pd.DataFrame: Kolonner ['year_month', 'mean', 'median', 'std'].
        """
        if time_offset is None:
            time_offset = self._get_min_offset(city, element_id)

        df = self._load_city(city)
        vals = self._select_values(
            df, None, element_id, time_offset
        )
        df_filtered = df.loc[vals.index].copy()
        df_filtered["year_month"] = (
            df_filtered["referenceTime"]
            .dt.tz_localize(None)
            .dt.to_period("M")
        )
        df_filtered["value"] = vals.to_numpy(dtype=np.float64)

        out = (
            df_filtered.groupby("year_month")["value"]
            .agg(["mean", "median", "std"])
            .reset_index()
        )
        out["year_month"] = out["year_month"].astype(str)

        return out


__all__ = ["MonthlyStats"]
