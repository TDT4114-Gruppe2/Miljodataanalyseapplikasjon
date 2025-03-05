import requests
import json

# Klient-ID for autentisering
client_id = "5173c281-ddc9-4f8d-88bb-4b752c31c043"

# Define endpoint and parameters
endpoint = 'https://frost.met.no/observations/v0.jsonld'
parameters = {
    'sources': 'SN18700,SN90450',
    'elements': 'mean(air_temperature P1D),min(air_temperature P1D),max(air_temperature P1D),sum(precipitation_amount P1D),mean(wind_speed P1D)',
    'referencetime': '2000-01-01/2024-12-31',
}

# Issue an HTTP GET request
r = requests.get(endpoint, params=parameters, auth=(client_id, ''))
r.raise_for_status()  # Sjekker for HTTP-feil

# Extract JSON data
data = r.json()

# Lagre JSON-data til fil
with open("data/raw/vaerdata.json", "w") as f:
    json.dump(data, f, indent=4)

print("Data lagret til data/raw/vaerdata.json")
