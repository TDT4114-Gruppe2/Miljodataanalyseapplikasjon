import os
import pandas as pd


class TemperatureRangeConverter:
    """
    Beregner og erstatter daglig temperatursvingning (maks − min) i
    `vaerdata_oslo.csv` og `vaerdata_tromso.csv`.
    """

    def __init__(self, output_dir: str):
        """
        Parameters
        ----------
        output_dir : str
            Katalog der CSV‑filene ligger og hvor nye versjoner skrives.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _compute_daily_range(self, df_city: pd.DataFrame) -> pd.DataFrame:
        """
        Returnerer DataFrame med elementId == 'range(air_temperature P1D)'
        (maks − min), avrundet til én desimal og med opprinnelig timeOffset.

        Returns
        -------
        pd.DataFrame
        """
        df_mm = df_city[df_city["elementId"].isin([
            "max(air_temperature P1D)",
            "min(air_temperature P1D)",
        ])]

        df_piv = df_mm.pivot_table(
            index=["sourceId", "referenceTime", "timeOffset"],
            columns="elementId",
            values="value",
            aggfunc="first",
        )

        # Konverter til float
        t_max = pd.to_numeric(df_piv["max(air_temperature P1D)"], errors="coerce")
        t_min = pd.to_numeric(df_piv["min(air_temperature P1D)"], errors="coerce")

        # Beregn differanse
        df_piv["value"] = (t_max - t_min).round(1)

        # Tving visningsformat til én desimal (hindrer binær-støy i CSV)
        df_piv["value"] = df_piv["value"].apply(
            lambda x: f"{x:.1f}" if pd.notnull(x) else ""
        )

        df_out = df_piv.reset_index()
        df_out["elementId"] = "range(air_temperature P1D)"
        df_out["unit"] = "degC"

        return df_out[
            ["sourceId", "referenceTime", "timeOffset", "elementId", "value", "unit"]
        ]

    def _process_city(self, city: str):
        file_path = os.path.join(self.output_dir, f"vaerdata_{city}.csv")

        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"Fant ikke {file_path} – hopper over.")
            return

        df_other = df[~df["elementId"].isin([
            "min(air_temperature P1D)",
            "max(air_temperature P1D)",
        ])]

        df_range = self._compute_daily_range(df)
        df_final = (
            pd.concat([df_other, df_range], ignore_index=True)
            .sort_values(["referenceTime", "timeOffset", "elementId"])
        )

        df_final.to_csv(file_path, index=False)
        print(f"Oppdatert fil: {file_path}")

    def run(self):
        """Kalkulerer og lagrer nye versjoner av byfilene i output_dir."""
        for city in ["oslo", "tromso"]:
            self._process_city(city)
