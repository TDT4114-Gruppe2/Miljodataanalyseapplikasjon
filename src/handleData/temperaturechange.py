"""Lager range-verdier for temperatur i CSV-filer."""

import os
import pandas as pd


class TemperatureRangeConverter:
    """Beregner og erstatter daglig temperatursvingning (maks − min) i CSV."""

    def __init__(self, output_dir: str) -> None:
        """Oppretter output-mappe hvis den ikke finnes."""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _compute_daily_range(self, df_city: pd.DataFrame) -> pd.DataFrame:
        """Returnerer df med nytt element 'range(air_temperature P1D)'."""
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

        # Beregn differansen og rund av
        max_vals = pd.to_numeric(
            df_piv["max(air_temperature P1D)"], errors="coerce"
        )
        min_vals = pd.to_numeric(
            df_piv["min(air_temperature P1D)"], errors="coerce"
        )
        df_piv["value"] = (max_vals - min_vals).round(1)

        df_out = df_piv.reset_index()
        df_out["elementId"] = "range(air_temperature P1D)"
        df_out["unit"] = "degC"

        return df_out[
            [
                "sourceId",
                "referenceTime",
                "timeOffset",
                "elementId",
                "value",
                "unit",
            ]
        ]

    def _process_city(self, city: str) -> None:
        """Leser by-CSV, legger på range-verdier og skriver tilbake."""
        file_path = os.path.join(
            self.output_dir, f"vaerdata_{city}.csv"
        )

        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            print(f"Fant ikke {file_path} – hopper over.")
            return

        df_range = self._compute_daily_range(df)
        df_final = (
            pd.concat([df, df_range], ignore_index=True)
            .sort_values(
                ["referenceTime", "timeOffset", "elementId"]
            )
        )

        df_final.to_csv(file_path, index=False)
        print(f"Oppdatert fil: {file_path}")

    def run(self) -> None:
        """Kjør range-beregning for Oslo og Tromsø."""
        for city in ["oslo", "tromso"]:
            self._process_city(city)
