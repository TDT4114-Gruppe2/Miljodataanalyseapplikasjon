"""Finner manglende værdata i Oslo og Tromsø."""
import os
import pandas as pd
from pandasql import sqldf


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

        self.df_oslo["date"] = self.df_oslo["referenceTime"].str[:10]
        self.df_tromso["date"] = self.df_tromso["referenceTime"].str[:10]

    def identify_missing(self):
        """Identifiserer manglende data i Oslo og Tromsø."""
        oslo_small = self.df_oslo[["date", "timeOffset", "elementId",
                                   "value"]].copy()
        oslo_small.rename(columns={"value": "oslo_value"}, inplace=True)

        tromso_small = self.df_tromso[["date", "timeOffset",
                                       "elementId", "value"]].copy()
        tromso_small.rename(columns={"value": "tromso_value"}, inplace=True)

        merged = pd.merge(oslo_small, tromso_small,
                          on=["date", "timeOffset", "elementId"], how="outer")

        missing_oslo = merged[
            merged["oslo_value"].isnull() & merged["tromso_value"].notnull()
        ].copy()
        missing_oslo["city"] = "Oslo"

        missing_tromso = merged[
            merged["tromso_value"].isnull() & merged["oslo_value"].notnull()
        ].copy()
        missing_tromso["city"] = "Tromsø"

        self.df_missing = pd.concat([missing_oslo, missing_tromso],
                                    ignore_index=True)

    def save_missing_data(self):
        """Lagrer manglende data i CSV-filer."""
        os.makedirs(self.output_dir, exist_ok=True)
        missing_path = os.path.join(self.output_dir, "missing_in_both.csv")
        summary_path = os.path.join(self.output_dir, "missing_summary.csv")

        self.df_missing.to_csv(missing_path, index=False, encoding="utf-8")

        query = """
        SELECT
            city,
            elementId,
            COUNT(*) AS num_missing
        FROM df_missing
        GROUP BY city, elementId
        ORDER BY city, num_missing DESC
        """
        # Send en eksplisitt dictionary med 'df_missing'
        missing_grouped = sqldf(query, {"df_missing": self.df_missing})

        missing_grouped.to_csv(summary_path, index=False, encoding="utf-8")

        print("Ferdig! Følgende CSV-filer er opprettet:")
        print(" -", missing_path)
        print(" -", summary_path)

class MissingDataConverter:
    def __init__(self):
        pass

    def read_missing_values(
            self,
            path: str
        ) -> pd.DataFrame:
        df = pd.read_csv(path)

        missing_oslo = df["oslo_value"].isna()
        missing_tromso = df["tromso_value"].isna()

        df["missing"] = None
        df.loc[missing_oslo, "missing"] = "Oslo"
        df.loc[missing_tromso, "missing"] = "Tromsø"

        df_missing = df[df["missing"].notna()].copy()

        return df_missing[["date", "timeOffset", "elementId", "missing"]].reset_index(drop=True)
