import requests
import json
import os
from dotenv import load_dotenv

# Last inn miljøvariabler
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(env_path)
client_id = os.getenv("CLIENT_ID")

def fetch_weather_data(client_id):
    """Henter værdata fra Frost API"""
    endpoint = 'https://frost.met.no/observations/v0.jsonld'
    parameters = {
        'sources': 'SN18700,SN90450',
        'elements': 'mean(air_temperature P1D),min(air_temperature P1D),max(air_temperature P1D),sum(precipitation_amount P1D),mean(wind_speed P1D)',
        'referencetime': '2000-01-01/2024-12-31',
    }

    response = requests.get(endpoint, params=parameters, auth=(client_id, ''))
    response.raise_for_status()  
    return response.json()

def write_json_to_file(json_data, filename):
    """Lagrer JSON-data til en fil"""
    with open(filename, "w", encoding="utf-8") as f:
        for chunk in json.JSONEncoder(indent=4).iterencode(json_data):
            f.write(chunk)