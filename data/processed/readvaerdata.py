"""Denne koden skriver om ønsket innhold fra JSON-filen til CSV-filer."""

import json
import os
import sys

import pandas as pd
from pandasql import sqldf


# Definerer arbeidskatalog og path til JSON-fil
script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, "..", "raw", "vaerdata.json")

try:
    # Åpner og parser JSON-filen
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Sjekker om JSON-filen er tom eller mangler "data"-nøkkel
    if not data or "data" not in data:
        raise ValueError("JSON-filen er tom eller mangler 'data'-nøkkel")

except (json.JSONDecodeError, ValueError) as e:
    # Dersom JSON er ugyldig eller tom:
    print(f"Feil i JSON-filen: {e}")
    print("Filen må genereres på nytt. Avslutter programmet.")
    sys.exit(1)  # Avslutter programmet

except Exception as e:
    # Viser uventede feil, f.eks. problemer med filtilgang
    print(f"Uventet feil ved lesing av filen: {e}")
    sys.exit(1)  # Avslutter programmet

# Lager en liste med poster som inneholder "observations"
data_list = [entry for entry in data.get("data", [])
             if entry.get("observations")]
# Skriver ut antall poster i "data_list"
print("Antall poster i 'data':", len(data_list))

# Opprett en flat liste med ønskede felter, inkludert timeOffset
flattened_data = [
    {
        "sourceId": entry["sourceId"],
        "referenceTime": entry["referenceTime"],
        "timeOffset": obs.get("timeOffset", None),
        # Bruker None hvis timeOffset mangler^
        "elementId": obs["elementId"],
        "value": obs["value"],
        "unit": obs.get("unit", "N/A"),  # Bruker "N/A" hvis enhet mangler
    }
    for entry in data_list
    for obs in entry["observations"]
]

# Konverterer listen til en Pandas DataFrame
df = pd.DataFrame(flattened_data)
print("\nDataFrame-oversikt:")
print(df.head())  # Viser topp 5 rader for å bekrefte struktur

# SQL-spørringer med Pandas DataFrame
# Her vil vi se hvor mange lokasjoner vi har og om
# det er kommet med flere eller færre lokasjoner enn forventet.
# I tillegg vil det skrives ut antall føringer per lokasjon
print("\n--- Verifiserer at vi har data fra begge lokasjoner ---")
q_verify_locations = """
SELECT sourceId, COUNT(*) AS num_entries
FROM df
GROUP BY sourceId
"""
verify_locations = sqldf(q_verify_locations, locals())
print(verify_locations)

# Antall unike dager med data per by
q_unique_days = """
SELECT sourceId, COUNT(DISTINCT referenceTime) AS unique_days
FROM df
GROUP BY sourceId
"""
unique_days = sqldf(q_unique_days, locals())
print("\n--- Antall unike dager med data per by ---")
print(unique_days)

# Filtrer for Tromsø
df_tromso = df[df["sourceId"] == "SN90450:0"]
# Lagrer data for Tromsø til en CSV-fil i samme mappe som scriptet
tromso_path = os.path.join(script_dir, "vaerdata_tromso.csv")
# index=False for å overskrive tildigere indeksering
df_tromso.to_csv(tromso_path, index=False)
print(f"\nLagrer data for Tromsø til: {tromso_path}")

# Filtrer for Oslo
df_oslo = df[df["sourceId"] == "SN18700:0"]
# Lagrer data for Oslo til en CSV-fil i samme mappe som scriptet
oslo_path = os.path.join(script_dir, "vaerdata_oslo.csv")
# index=False for å overskrive tildigere indeksering
df_oslo.to_csv(oslo_path, index=False)
print(f"Lagrer data for Oslo til: {oslo_path}")
