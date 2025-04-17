import json
import os
import sys

import pandas as pd
from pandasql import sqldf


class WeatherConverter:
    """Konverterer Frost‑JSON til flate DataFrame‑ og CSV‑filer per by."""

    def __init__(self, json_path: str, output_dir: str):
        # Lagre stiene slik de ble gitt (kan være relative eller absolutte)
        self.json_path = json_path
        self.output_dir = output_dir
        # Sørg for at output‑katalogen finnes. Bruk relativt navn slik at det ikke
        # skrives personlige brukernavn i loggene eller i notebooks som pushes.
        os.makedirs(self.output_dir, exist_ok=True)

        self.df: pd.DataFrame | None = None

    def load_data(self):
        """Laster og validerer JSON‑filen, returnerer en dict."""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not data or "data" not in data:
                raise ValueError("JSON‑filen er tom eller mangler 'data'-nøkkel")

        except (json.JSONDecodeError, ValueError) as exc:
            print(f"Feil i JSON‑filen: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"Uventet feil ved lesing av filen: {exc}")
            sys.exit(1)

        print("JSON‑data lastet inn.")
        return data

    def convert_to_dataframe(self, data):
        """Flatner Frost‑JSON til en Pandas DataFrame."""
        data_list = [entry for entry in data.get("data", []) if entry.get("observations")]
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

        self.df = pd.DataFrame(flattened)
        print("\nDataFrame‑oversikt:")
        print(self.df.head())

    def run_queries(self):
        """Kjører enkle SQL‑spørringer for validering."""
        if self.df is None:
            raise RuntimeError("DataFrame er ikke initialisert. Kjør convert_to_dataframe() først.")

        print("\n--- Verifiserer at vi har data fra begge lokasjoner ---")
        q1 = "SELECT sourceId, COUNT(*) AS num_entries FROM df GROUP BY sourceId"
        print(sqldf(q1, {"df": self.df}))

        print("\n--- Antall unike dager med data per by ---")
        q2 = "SELECT sourceId, COUNT(DISTINCT referenceTime) AS unique_days FROM df GROUP BY sourceId"
        print(sqldf(q2, {"df": self.df}))

    def save_city_data(self):
        """Lagrer værdata for Oslo og Tromsø til CSV‑filer i `output_dir`."""
        if self.df is None:
            raise RuntimeError("DataFrame er ikke initialisert. Kjør convert_to_dataframe() først.")

        cities = {"tromso": "SN90450:0", "oslo": "SN18700:0"}

        for city, source_id in cities.items():
            df_city = self.df[self.df["sourceId"] == source_id]
            output_path = os.path.join(self.output_dir, f"vaerdata_{city}.csv")
            df_city.to_csv(output_path, index=False)
            print(f"Lagrer data for {city.capitalize()} til: {output_path}")