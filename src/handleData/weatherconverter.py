"""Konverterer værdata fra JSON til to CSV-filer, én per by."""
import json
import os
import pandas as pd
from pandasql import sqldf
import sys


class WeatherConverter:
    """Konverterer JSON til DataFrame og lagrer CSV per by."""

    def __init__(self, json_path: str, output_dir: str) -> None:
        """
        Initialiserer converter med sti til JSON og utmappe.

        Parametre:
            json_path (str): Sti til input-JSON.
            output_dir (str): Katalog for utdata CSV-filer.
        """
        self.json_path = json_path
        self.output_dir = output_dir
        self.data: dict | None = None
        self.df: pd.DataFrame | None = None

    def load_data(self) -> dict:
        """
        Leser og validerer JSON-filen.

        Returnerer:
            dict: Lastet JSON-innhold under nøkkel 'data'.

        Avslutter programmet ved feil.
        """
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

            if "data" not in self.data or not self.data["data"]:
                raise ValueError("JSON-filen mangler 'data' eller er tom")
        except json.JSONDecodeError as exc:
            print(f"JSON-dekodingsfeil: {exc}")
            sys.exit(1)
        except ValueError as exc:
            print(f"Valideringsfeil: {exc}")
            sys.exit(1)
        except Exception as exc:
            print(f"Uventet feil: {exc}")
            sys.exit(1)

        print("JSON-data lastet inn.")
        return self.data

    def convert_to_dataframe(self) -> pd.DataFrame:
        """
        Flater ut observasjoner til en pandas DataFrame.

        Returnerer:
            pd.DataFrame: Kolonner:
                sourceId, referenceTime, timeOffset,
                elementId, value, unit
        """
        if self.data is None:
            raise RuntimeError("Data ikke lastet – kjør load_data() først")

        entries = self.data.get("data", [])
        flattened = []
        for entry in entries:
            observations = entry.get("observations", [])
            for obs in observations:
                flattened.append({
                    "sourceId": entry["sourceId"],
                    "referenceTime": entry["referenceTime"],
                    "timeOffset": obs.get("timeOffset"),
                    "elementId": obs["elementId"],
                    "value": obs["value"],
                    "unit": obs.get("unit", "N/A"),
                })

        self.df = pd.DataFrame(flattened)
        print("DataFrame opprettet.")
        return self.df

    def run_queries(self) -> None:
        """
        Kjører en enkel SQL-spørring mot DataFrame og skriver resultat.
        """
        if self.df is None:
            raise RuntimeError(
                "DataFrame ikke klar – kjør convert_to_dataframe() først")

        query = (
            "SELECT sourceId, COUNT(*) AS num_entries "
            "FROM df GROUP BY sourceId"
        )
        result = sqldf(query, {"df": self.df})
        print(result)

    def save_city_data(self) -> None:
        """
        Lagrer CSV for hver by basert på sourceId.
        """
        if self.df is None:
            raise RuntimeError(
                "DataFrame ikke klar – kjør convert_to_dataframe() først")

        os.makedirs(self.output_dir, exist_ok=True)

        # Definer by og tilhørende sourceId
        cities = {"tromso": "SN90450:0", "oslo": "SN18700:0"}

        for city, source_id in cities.items():
            df_city = self.df[self.df["sourceId"] == source_id]
            filename = f"vaerdata_{city}.csv"
            path = os.path.join(self.output_dir, filename)
            df_city.to_csv(path, index=False)
            print(f"Lagrer data for {city.capitalize()} til: {path}")
