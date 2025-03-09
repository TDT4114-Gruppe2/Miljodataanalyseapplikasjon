import os
import json
import pandas as pd
from pandasql import sqldf  # Brukes for SQL-lignende spørringer på DataFrame

# Bestemmer arbeidskatalog: Bruk __file__ hvis tilgjengelig, ellers nåværende arbeidskatalog (f.eks. i Jupyter)
try:
    script_dir = os.path.dirname(__file__)
except NameError:
    script_dir = os.getcwd()

# Angir filstien til JSON-filen (forutsatt at den ligger i ../raw/vaerdata.json)
file_path = os.path.join(script_dir, "..", "raw", "vaerdata.json")

# Generator for å lese JSON-filen linje for linje
def read_json_generator(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            yield line

# Leser filen linje for linje og setter sammen til én JSON-streng
lines = read_json_generator(file_path)
json_str = "".join(lines)

# Laster JSON-strengen til en Python-datastruktur
data = json.loads(json_str)

# Henter ut "data"-listen og filtrerer bort poster uten observasjoner
data_list = [entry for entry in data.get("data", []) if entry.get("observations")]
print("Antall poster i 'data':", len(data_list))

# "Flatten" dataene med list comprehension, inkludert timeOffset
flattened_data = [
    {
        "sourceId": entry["sourceId"],
        "referenceTime": entry["referenceTime"],
        "timeOffset": obs.get("timeOffset", None),  # Inkluderer timeOffset, None hvis mangler
        "elementId": obs["elementId"],
        "value": obs["value"],
        "unit": obs.get("unit", "N/A"),
    }
    for entry in data_list
    for obs in entry["observations"]
]

# Konverterer den flate listen til en Pandas DataFrame
df = pd.DataFrame(flattened_data)
print("\nDataFrame-oversikt:")
print(df.head())

# ------------------------------------------------
#   SQl-demos med pandasql (sqldf)
#   Vi mapper sourceId til lokasjonsnavn ved hjelp av CASE
# ------------------------------------------------

# Demo 1: Velg 5 rader fra df med lokasjonsnavn
print("\n--- Demo 1: Velg 5 rader med lokasjonsnavn ---")
q1 = """
SELECT 
    CASE 
        WHEN sourceId = 'SN90450:0' THEN 'Tromsø'
        WHEN sourceId = 'SN18700:0' THEN 'Oslo'
        ELSE sourceId 
    END AS location,
    referenceTime,
    timeOffset,
    elementId,
    value,
    unit
FROM df
LIMIT 5
"""
demo1 = sqldf(q1, locals())
print(demo1)

# Demo 2: Filtrer for temperaturdata (elementId som inneholder 'air_temperature') med lokasjonsnavn
print("\n--- Demo 2: Filtrer for air_temperature med lokasjonsnavn ---")
q2 = """
SELECT
    CASE 
        WHEN sourceId = 'SN90450:0' THEN 'Tromsø'
        WHEN sourceId = 'SN18700:0' THEN 'Oslo'
        ELSE sourceId 
    END AS location,
    referenceTime,
    elementId,
    value,
    unit
FROM df
WHERE elementId LIKE '%air_temperature%'
ORDER BY referenceTime DESC
LIMIT 5
"""
demo2 = sqldf(q2, locals())
print(demo2)

# Demo 3: Gruppér data etter sourceId og elementId, og beregn gjennomsnittlig value med lokasjonsnavn
print("\n--- Demo 3: Gjennomsnitt per kilde og element med lokasjonsnavn ---")
q3 = """
SELECT
    CASE 
        WHEN sourceId = 'SN90450:0' THEN 'Tromsø'
        WHEN sourceId = 'SN18700:0' THEN 'Oslo'
        ELSE sourceId 
    END AS location,
    elementId,
    AVG(value) AS avg_value
FROM df
GROUP BY sourceId, elementId
ORDER BY location, elementId
LIMIT 10
"""
demo3 = sqldf(q3, locals())
print(demo3)

# Demo 4: Summer nedbør per referenceTime og per lokasjon for elementId 'sum(precipitation_amount P1D)'
print("\n--- Demo 4: Summer nedbør per referenceTime med lokasjonsnavn ---")
q4 = """
SELECT
    CASE 
        WHEN sourceId = 'SN90450:0' THEN 'Tromsø'
        WHEN sourceId = 'SN18700:0' THEN 'Oslo'
        ELSE sourceId 
    END AS location,
    referenceTime,
    SUM(value) AS daily_precipitation
FROM df
WHERE elementId = 'sum(precipitation_amount P1D)'
GROUP BY sourceId, referenceTime
ORDER BY referenceTime DESC
LIMIT 5
"""
demo4 = sqldf(q4, locals())
print(demo4)

# ------------------------------------------------
#   Splitting av DataFrame til to CSV-filer basert på sourceId
# ------------------------------------------------

# Filtrér for Tromsø (sourceId 'SN90450:0')
df_tromso = df[df['sourceId'] == 'SN90450:0']
tromso_path = os.path.join(script_dir, "vaerdata_tromso.csv")
df_tromso.to_csv(tromso_path, index=False)
print(f"\nLagrer data for Tromsø til: {tromso_path}")

# Filtrér for Oslo (sourceId 'SN18700:0')
df_oslo = df[df['sourceId'] == 'SN18700:0']
oslo_path = os.path.join(script_dir, "vaerdata_oslo.csv")
df_oslo.to_csv(oslo_path, index=False)
print(f"Lagrer data for Oslo til: {oslo_path}")
