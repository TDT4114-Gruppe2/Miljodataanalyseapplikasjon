"""Tester missingdatfinder.py."""
import os
import pandas as pd


class MissingWeatherDataAnalyzer:
    """Analyserer og finner manglende værdata i Oslo og Tromsø."""

    def __init__(self, oslo_path: str, tromso_path: str, output_dir: str):
        """Setter opp filbaner for Oslo og Tromsø data."""
        self.oslo_path = oslo_path
        self.tromso_path = tromso_path
        self.output_dir = output_dir

    def load_data(self):
        """Laster inn værdata fra CSV-filer."""
        self.df_oslo = pd.read_csv(self.oslo_path)
        self.df_tromso = pd.read_csv(self.tromso_path)

        # Legg til date-kolonne ved å hente de første 10 tegn fra referenceTime
        self.df_oslo["date"] = self.df_oslo["referenceTime"].str[:10]
        self.df_tromso["date"] = self.df_tromso["referenceTime"].str[:10]

    def identify_missing(self):
        """Identifiserer manglende data i Oslo og Tromsø."""
        # Forbered dataframes med verdier for Oslo og Tromsø
        oslo_small = (
            self.df_oslo
            [["date", "timeOffset", "elementId", "value"]]
            .copy()
            .rename(columns={"value": "oslo_value"})
        )
        tromso_small = (
            self.df_tromso
            [["date", "timeOffset", "elementId", "value"]]
            .copy()
            .rename(columns={"value": "tromso_value"})
        )

        # Slå sammen outer for å finne alle kombinasjoner
        merged = pd.merge(
            oslo_small,
            tromso_small,
            on=["date", "timeOffset", "elementId"],
            how="outer"
        )

        # Filtrer der Oslo mangler men Tromsø har verdi
        missing_oslo = merged[
            merged["oslo_value"].isna() & merged["tromso_value"].notna()
        ].copy()
        missing_oslo["city"] = "Oslo"

        # Filtrer der Tromsø mangler men Oslo har verdi
        missing_tromso = merged[
            merged["tromso_value"].isna() & merged["oslo_value"].notna()
        ].copy()
        missing_tromso["city"] = "Tromsø"

        # Slå sammen manglende rader
        self.df_missing = pd.concat(
            [missing_oslo, missing_tromso],
            ignore_index=True
        )

    def save_missing_data(self):
        """Lagrer manglende data i CSV-filer."""
        os.makedirs(self.output_dir, exist_ok=True)
        missing_path = os.path.join(self.output_dir, "missing_in_both.csv")
        summary_path = os.path.join(self.output_dir, "missing_summary.csv")

        # Skriv ut alle manglende data
        self.df_missing.to_csv(missing_path, index=False, encoding="utf-8")

        # Lag en oppsummering med antall manglende per by og element
        missing_grouped = (
            self.df_missing
            .groupby(["city", "elementId"])
            .size()
            .reset_index(name="num_missing")
            .sort_values(["city", "num_missing"], ascending=[True, False])
        )
        missing_grouped.to_csv(summary_path, index=False, encoding="utf-8")

        print("Ferdig! Følgende CSV-filer er opprettet:")
        print(" -", missing_path)
        print(" -", summary_path)


class MissingDataConverter:
    """Konverterer lagrede manglende verdier til et enklere format."""

    def __init__(self):
        pass

    def read_missing_values(self, path: str) -> pd.DataFrame:
        df = pd.read_csv(path)

        # Marker hvilken by som mangler verdi
        df["missing"] = None
        df.loc[df["oslo_value"].isna(), "missing"] = "Oslo"
        df.loc[df["tromso_value"].isna(), "missing"] = "Tromsø"

        # Returner relevant kolonner
        return (
            df[["date", "timeOffset", "elementId", "missing"]]
            .reset_index(drop=True)
        )
