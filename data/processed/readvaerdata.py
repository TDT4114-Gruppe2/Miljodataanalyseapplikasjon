import os
import json
import pandas as pd

# Lager filsti basert på plasseringen
script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, "..", "raw", "vaerdata.json")

# Leser inn data
with open(file_path, "r") as f:
    data = json.load(f)

# Undersøker struktur – henter ut timeseries-delen
timeseries = data.get("properties", {}).get("timeseries", [])
df = pd.json_normalize(timeseries)

# Printer de første radene
print(df.head())

# Lagrer prosessert DataFrame til CSV for analyse
processed_path = os.path.join(script_dir, "vaerdata_processed.csv")
df.to_csv(processed_path, index=False)
print(f"Bearbeidede data lagret til {processed_path}")
