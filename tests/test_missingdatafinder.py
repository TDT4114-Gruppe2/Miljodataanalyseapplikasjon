import os
import sys
import pandas as pd
import pytest

# Gjør src tilgjengelig
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.missingdatafinder import MissingWeatherDataAnalyzer


def test_load_data(tmp_path):
    """
    Tester at load_data laster inn begge CSV-filene og legger til 'date'-kolonnen.
    """
    # Lag dummy CSV for Oslo og Tromsø
    oslo_data = pd.DataFrame({
        "referenceTime": ["2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z"],
        "timeOffset": [0, 1],
        "elementId": ["temp", "temp"],
        "value": [5, 6],
    })
    tromso_data = pd.DataFrame({
        "referenceTime": ["2023-01-01T00:00:00Z"],
        "timeOffset": [0],
        "elementId": ["temp"],
        "value": [4],
    })

    oslo_path = tmp_path / "oslo.csv"
    tromso_path = tmp_path / "tromso.csv"
    oslo_data.to_csv(oslo_path, index=False)
    tromso_data.to_csv(tromso_path, index=False)

    analyzer = MissingWeatherDataAnalyzer(str(oslo_path), str(tromso_path), output_dir=str(tmp_path))
    analyzer.load_data()

    assert "date" in analyzer.df_oslo.columns
    assert analyzer.df_oslo.loc[0, "date"] == "2023-01-01"
    assert "date" in analyzer.df_tromso.columns
    assert len(analyzer.df_oslo) == 2
    assert len(analyzer.df_tromso) == 1


def test_identify_missing():
    """
    Tester at identify_missing korrekt finner manglende verdier for Oslo og Tromsø.
    """
    analyzer = MissingWeatherDataAnalyzer("dummy1", "dummy2", "dummy_out")

    # Direkte sett DataFrames
    analyzer.df_oslo = pd.DataFrame({
        "referenceTime": ["2023-01-01T00:00:00Z"],
        "timeOffset": [0],
        "elementId": ["temp"],
        "value": [5],
        "date": ["2023-01-01"],
    })

    analyzer.df_tromso = pd.DataFrame({
        "referenceTime": ["2023-01-01T01:00:00Z"],
        "timeOffset": [1],
        "elementId": ["temp"],
        "value": [6],
        "date": ["2023-01-01"],
    })

    analyzer.identify_missing()

    df_missing = analyzer.df_missing
    assert len(df_missing) == 2

    # Oslo mangler tid 1, Tromsø mangler tid 0
    assert set(df_missing["city"]) == {"Oslo", "Tromsø"}
    assert set(df_missing["timeOffset"]) == {0, 1}


def test_save_missing_data(tmp_path, capsys):
    """
    Tester at save_missing_data lagrer to CSV-filer og at innholdet er som forventet.
    """
    analyzer = MissingWeatherDataAnalyzer("dummy1", "dummy2", str(tmp_path))

    analyzer.df_missing = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-01", "2023-01-01"],
        "timeOffset": [0, 1, 2],
        "elementId": ["temp", "wind", "temp"],
        "oslo_value": [None, None, 7],
        "tromso_value": [1, 2, None],
        "city": ["Oslo", "Tromsø"],
    })

    analyzer.save_missing_data()

    # Sjekk at begge filer ble opprettet
    missing_file = tmp_path / "missing_in_both.csv"
    summary_file = tmp_path / "missing_summary.csv"

    assert missing_file.exists()
    assert summary_file.exists()

    df_summary = pd.read_csv(summary_file)
    assert set(df_summary.columns) == {"city", "elementId", "num_missing"}

    # Sjekk at riktig antall manglende oppføringer er talt
    assert df_summary[df_summary["city"] == "Oslo"]["num_missing"].values[0] == 2
    assert df_summary[df_summary["city"] == "Tromsø"]["num_missing"].values[0] == 1

    # Sjekk utskrift til terminal
    output = capsys.readouterr().out
    assert "missing_in_both.csv" in output
    assert "missing_summary.csv" in output
