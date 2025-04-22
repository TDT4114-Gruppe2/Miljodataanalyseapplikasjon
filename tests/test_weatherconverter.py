import os
import json
import tempfile
import pytest
import pandas as pd
from src.handleData.weatherconverter import WeatherConverter


def test_load_data_success():
    data = {"data": [{"sourceId": "SN18700:0", "observations": [{"elementId": "temp", "value": 5}]}]}
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
        json.dump(data, f)
        f_path = f.name

    wc = WeatherConverter(json_path=f_path, output_dir="dummy")
    loaded = wc.load_data()
    assert "data" in loaded
    os.remove(f_path)


def test_load_data_missing_key():
    bad_data = {"invalid": []}
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
        json.dump(bad_data, f)
        f_path = f.name

    wc = WeatherConverter(json_path=f_path, output_dir="dummy")
    with pytest.raises(SystemExit):
        wc.load_data()
    os.remove(f_path)


def test_convert_to_dataframe():
    wc = WeatherConverter(json_path="dummy", output_dir="dummy")
    wc.data = {
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
    df = wc.convert_to_dataframe()
    assert len(df) == 3
    assert set(df.columns) == {"sourceId", "referenceTime", "timeOffset", "elementId", "value", "unit"}


def test_run_queries(capsys):
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

    wc.run_queries()
    captured = capsys.readouterr().out
    assert "sourceId" in captured
    assert "SN90450:0" in captured
    assert "SN18700:0" in captured


def test_save_city_data(tmp_path):
    df = pd.DataFrame({
        "sourceId": ["SN90450:0", "SN18700:0"],
        "referenceTime": ["2023-01-01", "2023-01-02"],
        "timeOffset": [0, 0],
        "elementId": ["temp", "temp"],
        "value": [10, 8],
        "unit": ["C", "C"]
    })
    output_dir = tmp_path / "output"
    wc = WeatherConverter(json_path="dummy", output_dir=str(output_dir))
    wc.df = df
    wc.save_city_data()

    for city in ["tromso", "oslo"]:
        file_path = output_dir / f"vaerdata_{city}.csv"
        assert file_path.exists()
