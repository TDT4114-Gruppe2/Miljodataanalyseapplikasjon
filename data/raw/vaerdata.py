"""Henter værdata fra Frost API og lagrer det i en JSON-fil."""

import json
import os
import requests
from dotenv import load_dotenv

# Stien til .env-filen (to nivåer opp)
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".env")
)

# Henter variabler fra .env-fil
load_dotenv(env_path)

# Klient-ID for autentisering (Frost API krever en autentiseringsnøkkel)
client_id = os.getenv("CLIENT_ID")


def fetch_weather_data(client_id):
    """Henter værdata fra Frost API."""
    endpoint = "https://frost.met.no/observations/v0.jsonld"
    parameters = {
        # Velger værstasjoner det hentes data fra
        "sources": "SN18700,SN90450",
        # Velger måle-elementer
        "elements": (
            "mean(air_temperature P1D),min(air_temperature P1D),"
            "max(air_temperature P1D),sum(precipitation_amount P1D),"
            "mean(wind_speed P1D)"
        ),
        "referencetime": "2000-01-01/2024-12-31",  # Tidsperiode for data
    }
    response = requests.get(endpoint, params=parameters, auth=(client_id, ""))
    response.raise_for_status()
    return response.json()


def write_json_to_file(json_data, filename):
    """Skriver JSON-data til en fil."""
    with open(filename, "w", encoding="utf-8") as f:
        for chunk in json.JSONEncoder(indent=4).iterencode(json_data):
            f.write(chunk)


if __name__ == "__main__":
    # Henter værdata
    data = fetch_weather_data(client_id)

    # Bruker funksjonen til å lagre værdata i en fil
    write_json_to_file(data, "data/raw/vaerdata.json")

    # Bekrefter at data er lagret
    print("Data lagret til data/raw/vaerdata.json")
