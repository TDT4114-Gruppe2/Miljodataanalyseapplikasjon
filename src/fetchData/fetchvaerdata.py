"""Henter værdata fra met.no og lagrer det i en JSON-fil."""

import json

import requests


class WeatherFetcher:
    """Henter værdata fra Meteorologisk institutt (Frost API)."""

    def __init__(self, client_id: str):
        """
        Initialiserer instansen med klient-ID for autentisering.

        Parametre:
            client_id (str): Klient-ID for Frost API.
        """
        self.client_id = client_id

    def fetch_weather_data(self) -> dict:
        """Henter værdata fra Frost API innenfor angitt tidsperiode."""
        endpoint = "https://frost.met.no/observations/v0.jsonld"
        parameters = {
            # Stasjoner som skal forespørres
            "sources": "SN18700,SN90450",
            # Måleparametere: daglige snitt, min, maks, sum og vind
            "elements": (
                "mean(air_temperature P1D),"
                "min(air_temperature P1D),"
                "max(air_temperature P1D),"
                "sum(precipitation_amount P1D),"
                "mean(wind_speed P1D)"
            ),
            # Tidsperiode for data (YYYY-MM-DD/YYY-MM-DD)
            "referencetime": "2000-01-01/2024-12-31",
        }

        response = requests.get(
            endpoint,
            params=parameters,
            auth=(self.client_id, ""),
        )
        response.raise_for_status()
        return response.json()

    def write_json_to_file(self, json_data: dict, filename: str) -> None:
        """
        Skriver JSON-data til angitt fil med innrykk for lesbarhet.

        Parametre:
            json_data (dict): Data som skal serialiseres til JSON.
            filename (str): Filbane for output-filen.
        """
        with open(filename, "w", encoding="utf-8") as f:
            encoder = json.JSONEncoder(indent=4)
            for chunk in encoder.iterencode(json_data):
                f.write(chunk)
