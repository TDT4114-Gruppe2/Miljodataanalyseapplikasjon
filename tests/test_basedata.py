import os
import pandas as pd
import pytest
from datetime import datetime
import sys
# Legg til prosjektets rotmappe i sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.analysis.basedata import DataLoader


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Oppretter en midlertidig mappe for CSV-filer."""
    d = tmp_path / "data"
    d.mkdir()
    return d


def write_csv(path, df):
    """Hjelpefunksjon: skriver en DataFrame til gitt sti."""
    df.to_csv(path, index=False)


def test_load_city_success(tmp_data_dir):
    # Lag en enkel CSV med referenceTime-kolonne
    df = pd.DataFrame({
        "sourceId": ["A"],
        "referenceTime": ["2023-01-01T12:00:00Z"],
        "elementId": ["foo"],
        "value": [1.0],
        "timeOffset": ["PT0H"]
    })
    csv_path = tmp_data_dir / "vaerdata_oslo.csv"
    write_csv(csv_path, df)

    dl = DataLoader(data_dir=str(tmp_data_dir))
    out = dl._load_city("oslo")

    # Sjekk at vi får en DataFrame tilbake
    assert isinstance(out, pd.DataFrame)
    # referenceTime er konvertert til datetime64[ns, UTC]
    assert out["referenceTime"].dtype == "datetime64[ns, UTC]"
    # Verdien skal være korrekt
    assert out["referenceTime"].iloc[0] == pd.Timestamp("2023-01-01T12:00:00Z")


def test_load_city_missing_file(tmp_data_dir):
    dl = DataLoader(data_dir=str(tmp_data_dir))
    with pytest.raises(FileNotFoundError) as exc:
        dl._load_city("oslo")
    assert "Fant ikke datafil" in str(exc.value)


def test_load_city_missing_referenceTime(tmp_data_dir):
    # Skriv en CSV uten referenceTime-kolonnen
    df = pd.DataFrame({
        "sourceId": ["A"],
        "elementId": ["foo"],
        "value": [1.0],
        "timeOffset": ["PT0H"]
    })
    csv_path = tmp_data_dir / "vaerdata_oslo.csv"
    write_csv(csv_path, df)

    dl = DataLoader(data_dir=str(tmp_data_dir))
    with pytest.raises(KeyError) as exc:
        dl._load_city("oslo")
    msg = str(exc.value)
    assert "Kolonnen 'referenceTime' mangler" in msg


def test_get_min_offset_success(tmp_data_dir):
    # Lag en CSV med flere timeOffset-verdier for én elementId
    df = pd.DataFrame({
        "sourceId": ["A", "A", "A"],
        "referenceTime": ["2023-01-01", "2023-01-01", "2023-01-01"],
        "elementId": ["foo", "foo", "foo"],
        "value": [1, 2, 3],
        "timeOffset": ["PT6H", "PT0H", "PT12H"]
    })
    write_csv(tmp_data_dir / "vaerdata_oslo.csv", df)

    dl = DataLoader(data_dir=str(tmp_data_dir))
    offset = dl._get_min_offset("oslo", "foo")
    assert offset == "PT0H"


def test_get_min_offset_no_offsets(tmp_data_dir):
    # CSV finnes, men ingen rad med elementId "bar"
    df = pd.DataFrame({
        "sourceId": ["A"],
        "referenceTime": ["2023-01-01"],
        "elementId": ["foo"],
        "value": [1],
        "timeOffset": ["PT0H"]
    })
    write_csv(tmp_data_dir / "vaerdata_oslo.csv", df)

    dl = DataLoader(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError) as exc:
        dl._get_min_offset("oslo", "bar")
    assert "Ingen timeOffset funnet" in str(exc.value)


def test_get_min_offset_no_valid_pt(tmp_data_dir):
    # CSV har elementId, men timeOffset er ikke PTnH-format
    df = pd.DataFrame({
        "sourceId": ["A", "A"],
        "referenceTime": ["2023-01-01", "2023-01-01"],
        "elementId": ["foo", "foo"],
        "value": [1, 2],
        "timeOffset": ["ABC", "123"]
    })
    write_csv(tmp_data_dir / "vaerdata_oslo.csv", df)

    dl = DataLoader(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError) as exc:
        dl._get_min_offset("oslo", "foo")
    msg = str(exc.value)
    assert "Fant ingen gyldige PT⟨n⟩H‑offsets" in msg
