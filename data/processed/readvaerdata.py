import os
import json
import pandas as pd

# Bruk __file__ hvis den finnes, ellers bruk nåværende arbeidskatalog (f.eks. i Jupyter)
try:
    script_dir = os.path.dirname(__file__)
except NameError:
    script_dir = os.getcwd()

# Angir filstien til JSON-filen; her antas filen å ligge i "../raw/vaerdata.json" relativt til skriptets plassering
file_path = os.path.join(script_dir, "..", "raw", "vaerdata.json")

# Leser inn data fra JSON-filen
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Henter ut dataene fra nøkkelen "data"
data_list = data.get("data", [])
print("Antall poster i 'data':", len(data_list))

# Flate ut observasjonene slik at hver rad blir en observasjon
df = pd.json_normalize(
    data_list,
    record_path=["observations"],
    meta=["sourceId", "referenceTime"],
    errors="ignore"
)

# Sjekker de første radene
print(df.head())

# Lagre den prosesserte DataFrame til CSV
processed_path = os.path.join(script_dir, "vaerdata_processed.csv")
df.to_csv(processed_path, index=False)
print(f"Bearbeidede data lagret til {processed_path}")