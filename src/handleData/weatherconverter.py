"""Konverterer værdata fra JSON til to CSV-filer, én per by."""
import json
import os
import sys

import pandas as pd
from pandasql import sqldf


class WeatherConverter:
    """Konverterer JSON til DataFrame‑ og CSV‑filer per by."""

    def __init__(self, json_path: str, output_dir: str):
        self.json_path = json_path
        self.output_dir = output_dir
        self.data = None
        self.df = None

    def load_data(self) -> dict:
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

            if not self.data or "data" not in self.data:
                raise ValueError("JSON-filen er tom eller mangler 'data'")
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"Feil i JSON-filen: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"Uventet feil: {exc}")
            sys.exit(1)

        print("JSON-data lastet inn.")
        return self.data

    def convert_to_dataframe(self) -> pd.DataFrame:
        if self.data is None:
            raise RuntimeError("Data ikke lastet – kjør load_data() først.")

        data_list = [
            entry for entry in self.data.get("data", [])
            if entry.get("observations")
        ]
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
        self.df = pd.DataFrame(flattened)
        print("DataFrame opprettet.")
        return self.df

    def run_queries(self) -> None:
        if self.df is None:
            raise RuntimeError("DataFrame ikke klar – kjør convert_to_dataframe() først.")

        print(sqldf(
            "SELECT sourceId, COUNT(*) as num_entries FROM df GROUP BY sourceId",
            {"df": self.df}
        ))

    def save_city_data(self) -> None:
        if self.df is None:
            raise RuntimeError("DataFrame ikke klar – kjør convert_to_dataframe() først.")

        os.makedirs(self.output_dir, exist_ok=True)
        cities = {"tromso": "SN90450:0", "oslo": "SN18700:0"}
        for city, source_id in cities.items():
            df_city = self.df[self.df["sourceId"] == source_id]
            path = os.path.join(self.output_dir, f"vaerdata_{city}.csv")
            df_city.to_csv(path, index=False)
            print(f"Lagrer data for {city.capitalize()} til: {path}")