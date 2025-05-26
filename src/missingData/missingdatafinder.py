"""Modul for å analysere og konvertere manglende værdata i Oslo og Tromsø."""

import os
import pandas as pd

from pandasql import sqldf


class MissingWeatherDataAnalyzer:
    """Analyserer og finner manglende værdata i Oslo og Tromsø."""

    def __init__(self, oslo_path: str, tromso_path: str, output_dir: str):
        """
        Setter opp filbaner for Oslo- og Tromsø-data.

        Parametre:
            oslo_path (str): Sti til CSV med Oslo-data.
            tromso_path (str): Sti til CSV med Tromsø-data.
            output_dir (str): Målmappe for utdata.
        """
        self.oslo_path = oslo_path
        self.tromso_path = tromso_path
        self.output_dir = output_dir

    def load_data(self):
        """Laster inn værdata fra CSV-filer og ekstraherer dato."""
        self.df_oslo = pd.read_csv(self.oslo_path)
        self.df_tromso = pd.read_csv(self.tromso_path)

        # Ekstraher kun dato fra referenceTime (YYYY-MM-DD)
        self.df_oslo["date"] = self.df_oslo["referenceTime"].str[:10]
        self.df_tromso["date"] = self.df_tromso["referenceTime"].str[:10]

    def identify_missing(self):
        """Identifiserer hvilke målepunkter som mangler i den ene byen."""
        # Velg relevante kolonner og gi dem meningsfulle navn
        oslo_small = self.df_oslo[[
            "date", "timeOffset", "elementId", "value"]].copy()
        oslo_small.rename(columns={"value": "oslo_value"}, inplace=True)

        tromso_small = self.df_tromso[[
            "date", "timeOffset", "elementId", "value"]].copy()
        tromso_small.rename(columns={"value": "tromso_value"}, inplace=True)

        # Slå sammen på dato, tid, og parameter – behold alle rader
        merged = pd.merge(
            oslo_small,
            tromso_small,
            on=["date", "timeOffset", "elementId"],
            how="outer"
        )

        # Finn rader der Oslo mangler, men Tromsø har data
        missing_oslo = merged[
            merged["oslo_value"].isnull() & merged["tromso_value"].notnull()
        ].copy()
        missing_oslo["city"] = "Oslo"

        # Finn rader der Tromsø mangler, men Oslo har data
        missing_tromso = merged[
            merged["tromso_value"].isnull() & merged["oslo_value"].notnull()
        ].copy()
        missing_tromso["city"] = "Tromsø"

        # Slå sammen alle manglende-rader i én DataFrame
        self.df_missing = pd.concat(
            [missing_oslo, missing_tromso], ignore_index=True)

    def save_missing_data(self):
        """Lagrer manglende data og oppsummering i CSV-filer."""
        os.makedirs(self.output_dir, exist_ok=True)
        missing_path = os.path.join(self.output_dir, "missing_in_both.csv")
        summary_path = os.path.join(self.output_dir, "missing_summary.csv")

        # Skriv alle enkeltserier med manglende målinger
        self.df_missing.to_csv(missing_path, index=False, encoding="utf-8")

        # Oppsummer antall manglende målinger per by og parameter
        query = """
        SELECT
            city,
            elementId,
            COUNT(*) AS num_missing
        FROM df_missing
        GROUP BY city, elementId
        ORDER BY city, num_missing DESC
        """
        missing_grouped = sqldf(query, {"df_missing": self.df_missing})
        missing_grouped.to_csv(summary_path, index=False, encoding="utf-8")

        # Gi brukeren beskjed når alt er lagret
        print(
            f"Ferdig! Følgende CSV-filer er opprettet:\n"
            f" - {missing_path}\n"
            f" - {summary_path}"
        )


class MissingDataConverter:
    """Konverterer og filtrerer rader med manglende data."""

    def read_missing_values(self, path: str) -> pd.DataFrame:
        """
        Leser CSV med manglende-verdier og merker by.

        Parametre:
            path (str): Sti til CSV-fil med manglende verdier.

        Returnerer:
            pd.DataFrame: Kolonnene date, timeOffset, elementId og missing.
        """
        df = pd.read_csv(path)

        # Marker hvilke rader som mangler i Oslo eller Tromsø
        missing_oslo = df["oslo_value"].isna()
        missing_tromso = df["tromso_value"].isna()

        df["missing"] = None
        df.loc[missing_oslo, "missing"] = "Oslo"
        df.loc[missing_tromso, "missing"] = "Tromsø"

        # Filtrer ut kun de radene som faktisk mangler verdi
        df_missing = df[df["missing"].notna()].copy()

        return df_missing[["date", "timeOffset",
                           "elementId", "missing"]].reset_index(drop=True)
