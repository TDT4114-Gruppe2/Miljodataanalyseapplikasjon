"""Konverterer værdata fra JSON til to CSV-filer, én per by."""
import json
import os
import sys

import pandas as pd
from pandasql import sqldf


class WeatherConverter:
    """Konverterer JSON til DataFrame‑ og CSV‑filer per by."""

    @staticmethod
    def load_data(json_path: str) -> dict:
        """Laster og validerer JSON‑filen, returnerer en dict."""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not data or "data" not in data:
                raise ValueError(
                    "JSON‑filen er tom eller mangler 'data'-nøkkel"
                )

        except (json.JSONDecodeError, ValueError) as exc:
            print(f"Feil i JSON‑filen: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"Uventet feil ved lesing av filen: {exc}")
            sys.exit(1)

        print("JSON‑data lastet inn.")
        return data

    @staticmethod
    def convert_to_dataframe(data: dict) -> pd.DataFrame:
        """Gjør JSON-data om til en Pandas DataFrame."""
        data_list = [
            entry
            for entry in data.get("data", [])
            if entry.get("observations")
        ]
        print("Antall poster i 'data':", len(data_list))

        flattened = [
            {
                "sourceId": entry["sourceId"],
                "referenceTime": entry["referenceTime"],
                "timeOffset": obs.get("timeOffset"),
                "elementId": obs["elementId"],
                "value": obs["value"],
                "unit": obs.get("unit", "N/A"),
            }
            for entry in data_list
            for obs in entry["observations"]
        ]

        df = pd.DataFrame(flattened)
        print("\nDataFrame‑oversikt:")
        print(df.head())
        return df

    @staticmethod
    def run_queries(df: pd.DataFrame) -> None:
        """Kjører enkle SQL‑spørringer for validering."""
        if df is None:
            raise RuntimeError(
                "DataFrame er ikke initialisert. "
                "Kjør convert_to_dataframe() først."
            )

        print("\n--- Verifiserer at vi har data fra begge lokasjoner ---")
        q1 = (
            "SELECT sourceId, COUNT(*) AS num_entries "
            "FROM df GROUP BY sourceId"
        )
        print(sqldf(q1, {"df": df}))

        print("\n--- Antall unike dager med data per by ---")
        q2 = (
            "SELECT sourceId, COUNT(DISTINCT referenceTime) "
            "AS unique_days FROM df GROUP BY sourceId"
        )
        print(sqldf(q2, {"df": df}))

    @staticmethod
    def save_city_data(df: pd.DataFrame, output_dir: str) -> None:
        """Lagrer værdata for Oslo og Tromsø til CSV‑filer i `output_dir`."""
        if df is None:
            raise RuntimeError(
                "DataFrame er ikke initialisert. "
                "Kjør convert_to_dataframe() først."
            )

        os.makedirs(output_dir, exist_ok=True)
        cities = {"tromso": "SN90450:0", "oslo": "SN18700:0"}

        for city, source_id in cities.items():
            df_city = df[df["sourceId"] == source_id]
            output_path = os.path.join(
                output_dir, f"vaerdata_{city}.csv"
            )
            df_city.to_csv(output_path, index=False)
            print(
                f"Lagrer data for {city.capitalize()} til: {output_path}"
            )
