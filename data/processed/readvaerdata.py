import pandas as pd

def lagre_data_csv(data, filnavn="vaerdata.csv"):
    if "properties" in data and "timeseries" in data["properties"]:
        # Trekker ut relevant data
        df = pd.json_normalize(data["properties"]["timeseries"])  

        # Lagre til CSV
        df.to_csv(filnavn, index=False)
        print(f"Data lagret til {filnavn}")
    else:
        print("Feil: Ugyldig datastruktur.")

# Sjekk at `data` eksisterer før lagring
if data:
    lagre_data_csv(data)

# Les inn CSV-filen for å sjekke at den fungerer
try:
    df = pd.read_csv("vaerdata.csv")
    print(df.head())  # Viser de første 5 radene
except FileNotFoundError:
    print("CSV-filen ble ikke funnet.")
