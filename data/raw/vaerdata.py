import requests
import json

# Klient-ID for autentisering (Frost API krever en autentiseringsnøkkel)
client_id = "5173c281-ddc9-4f8d-88bb-4b752c31c043"

# Definer API-endepunktet og parametere for forespørselen
endpoint = 'https://frost.met.no/observations/v0.jsonld'
parameters = {
    'sources': 'SN18700,SN90450',  # Spesifiserer hvilke værstasjoner vi henter data fra
    'elements': 'mean(air_temperature P1D),min(air_temperature P1D),max(air_temperature P1D),sum(precipitation_amount P1D),mean(wind_speed P1D)',  
    # Velger hvilke værdata vi ønsker: snitt-, min- og makstemperatur, nedbørsmengde og vindhastighet per dag (P1D)
    'referencetime': '2000-01-01/2024-12-31',  # Tidsperiode for data
}

# Gjør en HTTP GET-forespørsel til Frost API med autentisering
r = requests.get(endpoint, params=parameters, auth=(client_id, ''))
r.raise_for_status()  # Stopper programmet hvis det oppstår en HTTP-feil

# Hent JSON-data fra svaret
data = r.json()

# Funksjon for å skrive JSON-data til en fil ved hjelp av en generator
def write_json_to_file(json_data, filename):
    # Skriver data til en fil ved hjelp av en generator for å unngå 
    # at hele JSON-strukturen må konverteres i én stor operasjon.
    with open(filename, "w", encoding="utf-8") as f:
        # json.JSONEncoder(indent=4).iterencode(...) returnerer JSON-data i små biter ("chunks"),
        # noe som er mer effektivt for store datasett.
        for chunk in json.JSONEncoder(indent=4).iterencode(json_data):
            f.write(chunk)

# Bruk funksjonen til å lagre værdata i en fil
write_json_to_file(data, "data/raw/vaerdata.json")

# Bekreft at data er lagret
print("Data lagret til data/raw/vaerdata.json")