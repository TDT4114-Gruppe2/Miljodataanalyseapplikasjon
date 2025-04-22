"""Finner månedlig data."""
import os
from functools import lru_cache
import numpy as np
import pandas as pd


class MonthlyStatistics:
    """Leser CSV‑filer og beregner viktige statistiske tall."""

    def __init__(self, data_dir: str):
        """Setter opp data‑katalogen for CSV‑filer."""
        self.data_dir = data_dir

    @lru_cache(maxsize=None)
    def _load_city(self, city: str) -> pd.DataFrame:
        """Leser filen `vaerdata_{city}.csv` én gang og cacher resultatet."""
        path = os.path.join(self.data_dir, f"vaerdata_{city}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fant ikke '{path}'")

        df = pd.read_csv(path, low_memory=False)

        # Konverter tidsstempel til datetime for enkel gruppering
        df["referenceTime"] = pd.to_datetime(
            df["referenceTime"], utc=True, errors="coerce"
        )

        return df

    @staticmethod
    def _select_values(
            df: pd.DataFrame,
            year_month: str | None,
            element_id: str,
            time_offset: str
        ) -> pd.Series:
        mask = (
            df["elementId"].eq(element_id) &
            df["timeOffset"].eq(time_offset)
        )
        """Filtrerer og returnerer verdier uten manglende data."""
        if year_month is not None:
            mask &= df["referenceTime"].dt.strftime("%Y-%m").eq(year_month)

        values = pd.to_numeric(df.loc[mask, "value"], errors="coerce").dropna()

        if values.empty:
            raise ValueError(
                "Ingen datapunkter funnet for "
                f"elementId='{element_id}', timeOffset='{time_offset}'"
                f"{f', år‑måned={year_month!r}' if year_month else ''}"
            )
        return values

    def compute_single_month(
            self,
            year_month: str,
            element_id: str,
            city: str,
            time_offset: str
        ) -> dict[str, float]:
        """Returnerer statistikk for en enkelt måned som dictionary."""
        df = self._load_city(city)
        vals = self._select_values(df, year_month, element_id, time_offset)

        return {
            "mean": float(vals.mean()),
            "median": float(vals.median()),
            "std": float(vals.std(ddof=0)),  # pop‑std
        }

    def compute_all_months(
            self,
            element_id: str,
            city: str,
            time_offset: str
        ) -> pd.DataFrame:
        """Returnerer statistikk for alle måneder som finnes i filen."""
        df = self._load_city(city)
        vals = self._select_values(df, None, element_id, time_offset)
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
