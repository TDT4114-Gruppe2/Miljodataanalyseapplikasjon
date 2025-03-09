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

# Gjør en HTTP GET-forespørsel
r = requests.get(endpoint, params=parameters, auth=(client_id, ''))
r.raise_for_status()  # Avbryt hvis HTTP-feil oppstår

# Hent JSON-data fra svaret
data = r.json()

# Eksempel på en generator-funksjon for å skrive JSON data "bit for bit"
def write_json_to_file(json_data, filename):
    """
    Skriver data til en fil ved hjelp av en generator
    for å unngå at hele datastrukturen må konverteres i én stor operasjon.
    """
    with open(filename, "w", encoding="utf-8") as f:
        # json.JSONEncoder(indent=4).iterencode(...) gir en generator
        # som returnerer JSON i små biter ("chunks").
        for chunk in json.JSONEncoder(indent=4).iterencode(json_data):
            f.write(chunk)

# Bruk generator-funksjonen til å lagre data
write_json_to_file(data, "data/raw/vaerdata.json")

print("Data lagret til data/raw/vaerdata.json")
