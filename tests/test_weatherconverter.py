import json
import os
import sys
import pytest
import pandas as pd

# Legg til prosjektets rotmappe i sys.path slik at vi kan importere WeatherConverter.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.handleData.weatherconverter import WeatherConverter  # Endre modulnavn ved behov


# -------------------------------
# Test for load_data
# -------------------------------

def test_load_data_valid(tmp_path):
    """
    Tester at load_data leser og returnerer JSON-data korrekt fra en gyldig fil.
    """
    # Opprett midlertidig JSON-fil med gyldig innhold
    valid_data = {
        "data": [
            {
                "sourceId": "SN90450:0",
                "referenceTime": "2023-01-01",
                "observations": [
                    {"timeOffset": None, "elementId": "temp", "value": 10, "unit": "C"}
                ]
            }
        ]
    }
    file_path = tmp_path / "valid.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)
    
    wc = WeatherConverter(str(file_path), output_dir=str(tmp_path))
    data = wc.load_data()
    
    assert data == valid_data


def test_load_data_missing_key(tmp_path, capsys):
    """
    Tester at load_data avslutter (sys.exit) hvis JSON-filen mangler 'data'-nøkkel.
    """
    invalid_data = {"ikke_data": []}
    file_path = tmp_path / "invalid.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)
    
    wc = WeatherConverter(str(file_path), output_dir=str(tmp_path))
    
    with pytest.raises(SystemExit):
        wc.load_data()
    
    # Optionelt: sjekk at det ble printet en feilmelding
    captured = capsys.readouterr().out
    assert "mangler 'data'-nøkkel" in captured


def test_load_data_bad_json(tmp_path, capsys):
    """
    Tester at load_data avslutter ved ugyldig JSON (JSONDecodeError).
    """
    file_path = tmp_path / "bad.json"
    # Skriv inn ugyldig JSON (for eksempel manglende avsluttende klammeparentes)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write('{"data": [1, 2, 3]')
    
    wc = WeatherConverter(str(file_path), output_dir=str(tmp_path))
    
    with pytest.raises(SystemExit):
        wc.load_data()
    
    captured = capsys.readouterr().out
    assert "Feil i JSON-filen:" in captured


# -------------------------------
# Test for convert_to_dataframe
# -------------------------------

def test_convert_to_dataframe(capsys):
    """
    Tester at convert_to_dataframe skaper en DataFrame med de forventede kolonnene.
    """
    # Dummy-data med to poster, med observasjoner for testing.
    test_data = {
        "data": [
            {
                "sourceId": "SN90450:0",
                "referenceTime": "2023-01-01",
                "observations": [
                    {"timeOffset": 0, "elementId": "temp", "value": 10, "unit": "C"},
                    {"timeOffset": 1, "elementId": "wind", "value": 5, "unit": "m/s"}
                ]
            },
            {
                "sourceId": "SN18700:0",
                "referenceTime": "2023-01-02",
                "observations": [
                    {"timeOffset": 0, "elementId": "temp", "value": 8, "unit": "C"}
                ]
            },
        ]
    }
    # Vi kan opprette WeatherConverter uten filbane (filinnlasting skal kjøres separat)
    wc = WeatherConverter(json_path="dummy", output_dir="dummy")
    wc.convert_to_dataframe(test_data)
    
    # Test at df er en pandas DataFrame
    df = wc.df
    assert isinstance(df, pd.DataFrame)
    
    # Forventede kolonner
    expected_cols = {"sourceId", "referenceTime", "timeOffset", "elementId", "value", "unit"}
    assert set(df.columns) == expected_cols
    
    # Sjekk at antall rader er som forventet
    # Totalt: 2 observasjoner fra den første posten og 1 observasjon fra den andre
    assert len(df) == 3
    
    # Fange utskriftene (eventuelt)
    output = capsys.readouterr().out
    assert "Antall poster i 'data':" in output
    assert "DataFrame-oversikt:" in output


# -------------------------------
# Test for run_queries
# -------------------------------

def test_run_queries(capsys):
    """
    Tester at run_queries skriver ut forventet informasjon.
    """
    # Opprett en liten DataFrame direkte og sett wc.df
    data = {
        "sourceId": ["SN90450:0", "SN18700:0", "SN90450:0"],
        "referenceTime": ["2023-01-01", "2023-01-02", "2023-01-01"],
        "timeOffset": [0, 0, 1],
        "elementId": ["temp", "temp", "wind"],
        "value": [10, 8, 5],
        "unit": ["C", "C", "m/s"]
    }
    df = pd.DataFrame(data)
    wc = WeatherConverter(json_path="dummy", output_dir="dummy")
    wc.df = df
    
    # Kjør run_queries
    wc.run_queries()
    
    # Sjekk at utskriften inneholder kjente deler av spørringsresultatene
    output = capsys.readouterr().out
    assert "Verifiserer at vi har data fra begge lokasjoner" in output
    assert "Antall unike dager med data per by" in output


# -------------------------------
# Test for save_city_data
# -------------------------------

def test_save_city_data(tmp_path):
    """
    Tester at save_city_data filtrerer df og lagrer CSV-filer for de gitte byene.
    """
    # Opprett en DataFrame som inneholder data for både Tromsø og Oslo.
    data = {
        "sourceId": ["SN90450:0", "SN18700:0", "SN90450:0", "SN18700:0"],
        "referenceTime": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "timeOffset": [0, 0, 1, 1],
        "elementId": ["temp", "temp", "wind", "wind"],
        "value": [10, 8, 5, 6],
        "unit": ["C", "C", "m/s", "m/s"]
    }
    df = pd.DataFrame(data)
    wc = WeatherConverter(json_path="dummy", output_dir=str(tmp_path))
    wc.df = df

    wc.save_city_data()
    
    # Definer stiene til lagrede filer for Tromsø og Oslo
    path_tromso = os.path.join(str(tmp_path), "vaerdata_tromso.csv")
    path_oslo = os.path.join(str(tmp_path), "vaerdata_oslo.csv")
    
    # Sjekk at filene eksisterer
    assert os.path.exists(path_tromso)
    assert os.path.exists(path_oslo)
    
    # Les inn og sjekk at data for Tromsø kun inneholder rader med sourceId "SN90450:0"
    df_tromso = pd.read_csv(path_tromso)
    assert all(df_tromso["sourceId"] == "SN90450:0")
    
    # For Oslo skal sourceId være "SN18700:0"
    df_oslo = pd.read_csv(path_oslo)
    assert all(df_oslo["sourceId"] == "SN18700:0")
