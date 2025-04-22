"""Henter værdata fra met.no og lagrer det i en JSON-fil."""

import json
import requests


class WeatherFetcher:
    """Henter værdata fra Frost API og skriver det ut på JSON-format."""

    def __init__(self, client_id):
        """Initialiserer instansen med klient-ID for autentisering."""
        self.client_id = client_id

    def fetch_weather_data(self):
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
        response = requests.get(endpoint, params=parameters,
                                auth=(self.client_id, ""))
        response.raise_for_status()
        return response.json()

    def write_json_to_file(self, json_data, filename):
        """Skriver JSON-data til angitt fil med innrykk for lesbarhet."""
        with open(filename, "w", encoding="utf-8") as f:
            for chunk in json.JSONEncoder(indent=4).iterencode(json_data):
                f.write(chunk)
