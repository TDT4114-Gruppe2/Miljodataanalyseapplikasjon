import os
import pandas as pd
import pytest
from src.handleData.temperaturechange import TemperatureRangeConverter

@pytest.fixture
def sample_df():
    # Daglig min og maks for én dag
    return pd.DataFrame([
        {
            "sourceId": "SN18700:0",
            "referenceTime": "2023-01-01",
            "timeOffset": 0,
            "elementId": "max(air_temperature P1D)",
            "value": 5.0,
            "unit": "degC",
        },
        {
            "sourceId": "SN18700:0",
            "referenceTime": "2023-01-01",
            "timeOffset": 0,
            "elementId": "min(air_temperature P1D)",
            "value": -3.2,
            "unit": "degC",
        },
        # Samme for tromsø for å teste flere filer
        {
            "sourceId": "SN90450:0",
            "referenceTime": "2023-01-01",
            "timeOffset": 0,
            "elementId": "max(air_temperature P1D)",
            "value": 2.5,
            "unit": "degC",
        },
        {
            "sourceId": "SN90450:0",
            "referenceTime": "2023-01-01",
            "timeOffset": 0,
            "elementId": "min(air_temperature P1D)",
            "value": -1.5,
            "unit": "degC",
        },
    ])

def test__compute_daily_range(sample_df):
    """Test at _compute_daily_range returnerer korrekt range-DataFrame."""
    conv = TemperatureRangeConverter(output_dir=".")
    # Vi plukker kun ut data for én city for å teste metoden isolert
    df_oslo = sample_df[sample_df["sourceId"] == "SN18700:0"]
    df_range = conv._compute_daily_range(df_oslo)

    # Skal være eksakt én rad per kombinasjon sourceId+referenceTime+timeOffset
    assert len(df_range) == 1

    row = df_range.iloc[0]
    assert row["sourceId"] == "SN18700:0"
    assert row["referenceTime"] == "2023-01-01"
    assert row["timeOffset"] == 0
    assert row["elementId"] == "range(air_temperature P1D)"
    # 5.0 − (−3.2) = 8.2
    assert pytest.approx(row["value"], rel=1e-3) == 8.2
    assert row["unit"] == "degC"

def test_process_city_and_run(tmp_path, sample_df, capsys):
    """
    Lager to CSV-filer (oslo og tromso) med kun min/max,
    kjører run(), og sjekker at det nå finnes en ekstra 'range'-rad.
    """
    outdir = tmp_path / "out"
    outdir.mkdir()

    # Skriv originale CSV-er
    df = sample_df
    for city, sid in [("oslo", "SN18700:0"), ("tromso", "SN90450:0")]:
        df_city = df[df["sourceId"] == sid]
        path = outdir / f"vaerdata_{city}.csv"
        df_city.to_csv(path, index=False)

    # Kjøre converter
    conv = TemperatureRangeConverter(output_dir=str(outdir))
    conv.run()

    # Sjekk at melding om oppdatert fil ble printet for begge
    captured = capsys.readouterr().out
    assert f"Oppdatert fil: {outdir}/vaerdata_oslo.csv" in captured
    assert f"Oppdatert fil: {outdir}/vaerdata_tromso.csv" in captured

    # Les inn oppdatert CSV og sjekk at den har én ekstra rad per fil
    for city in ["oslo", "tromso"]:
        path = outdir / f"vaerdata_{city}.csv"
        df_final = pd.read_csv(path)

        # Opprinnelig hadde 2 rader (min+max), nå 3 (min+max+range)
        assert len(df_final) == 3

        # Sjekk at 'range(air_temperature P1D)' er med
        assert "range(air_temperature P1D)" in df_final["elementId"].values

def test_missing_file_skips(tmp_path, capsys):
    """Hvis fil ikke finnes, skal den hoppe over uten å kaste feil."""
    outdir = tmp_path / "empty"
    outdir.mkdir()

    conv = TemperatureRangeConverter(output_dir=str(outdir))
    # Slett alle filer om det skulle ligge noe
    # (det er ingen vaerdata_oslo.csv her)
    conv.run()

    captured = capsys.readouterr().out
    # Skal oppgi at den ikke fant fil for begge byene
    assert "Fant ikke" in captured
    assert "vaerdata_oslo.csv" in captured
    assert "vaerdata_tromso.csv" in captured
