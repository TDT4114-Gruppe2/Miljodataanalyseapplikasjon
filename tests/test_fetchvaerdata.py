import json
import os
import pytest
import requests
import sys

# Legg til prosjektets rotmappe i sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.fetchData.fetchvaerdata import WeatherFetcher

# Dummy-response for å simulere requests.get-svar
class DummyResponse:
    def __init__(self, json_data, raise_error=False):
        self._json_data = json_data
        self._raise_error = raise_error

    def raise_for_status(self):
        # Dersom _raise_error er True, skal metoden kaste en HTTPError
        if self._raise_error:
            raise requests.HTTPError("HTTP error simulated")

    def json(self):
        return self._json_data

def test_fetch_weather_data(monkeypatch):
    """
    Tester at fetch_weather_data returnerer forventede data ved suksess.
    """
    dummy_data = {"status": "ok", "data": {"key": "value"}}

    # Definerer en dummy-get funksjon som returnerer et kontrollert DummyResponse.
    def dummy_get(url, params, auth):
        return DummyResponse(dummy_data)

    # Monkeypatch requests.get slik at den bruker dummy_get
    monkeypatch.setattr(requests, "get", dummy_get)

    # Oppretter instans av WeatherFetcher med en dummy client_id
    wf = WeatherFetcher("dummy_client_id")
    result = wf.fetch_weather_data()
    assert result == dummy_data

def test_write_json_to_file(tmp_path):
    """
    Tester at write_json_to_file skriver JSON-data korrekt til en fil.
    """
    wf = WeatherFetcher("dummy_client_id")
    json_data = {"a": 1, "b": 2}
    file_path = tmp_path / "output.json"
    wf.write_json_to_file(json_data, str(file_path))

    # Leser filen og laster inn innholdet som JSON for å verifisere korrekt formatering
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        loaded = json.loads(content)
    assert loaded == json_data

def test_fetch_weather_data_http_error(monkeypatch):
    """
    Tester at fetch_weather_data kaster en HTTPError hvis requests.get gir et HTTP-feil-svar.
    """
    # Dummy-funksjonen som simulerer et svar hvor raise_for_status kaster en error
    def dummy_get_error(url, params, auth):
        return DummyResponse({}, raise_error=True)

    monkeypatch.setattr(requests, "get", dummy_get_error)
    wf = WeatherFetcher("dummy_client_id")
    with pytest.raises(requests.HTTPError):
        wf.fetch_weather_data()
