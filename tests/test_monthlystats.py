import pandas as pd
import pytest
from pathlib import Path
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.analysis.monthlystats import MonthlyStats


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Oppretter en midlertidig data-mappe."""
    d = tmp_path / "data"
    d.mkdir()
    return d


def write_csv(city: str, df: pd.DataFrame, data_dir: Path):
    """Hjelpefunksjon for å skrive vaerdata_{city}.csv."""
    path = data_dir / f"vaerdata_{city}.csv"
    df.to_csv(path, index=False)
    return path


def test_select_values_success():
    # Lager DataFrame med tre datapunkter i 2023-01 og 2023-02
    df = pd.DataFrame({
        "elementId": ["e", "e", "e", "e"],
        "timeOffset": ["PT0H"] * 4,
        "referenceTime": pd.to_datetime([
            "2023-01-05", "2023-01-20", "2023-02-10", "2023-02-15"
        ], utc=True),
        "value": [1.5, 2.5, 3.0, 4.0],
    })
    # Test for januar
    jan = MonthlyStats._select_values(df, "2023-01", "e", "PT0H")
    assert list(jan) == [1.5, 2.5]
    # Test for februar
    feb = MonthlyStats._select_values(df, "2023-02", "e", "PT0H")
    assert list(feb) == [3.0, 4.0]


def test_select_values_no_data_raises():
    df = pd.DataFrame({
        "elementId": ["x"],
        "timeOffset": ["PT0H"],
        "referenceTime": pd.to_datetime(["2023-01-01"], utc=True),
        "value": [1.0],
    })
    # Ingen datapunkter for element 'e'
    with pytest.raises(ValueError) as exc:
        MonthlyStats._select_values(df, "2023-01", "e", "PT0H")
    assert "Ingen datapunkter" in str(exc.value)


def test_compute_single_month(tmp_data_dir):
    # To målinger i januar 2023 for element 't'
    df = pd.DataFrame({
        "sourceId": ["S", "S"],
        "referenceTime": ["2023-01-01", "2023-01-15"],
        "timeOffset": ["PT0H", "PT0H"],
        "elementId": ["t", "t"],
        "value": [10, 20],
    })
    write_csv("city", df, tmp_data_dir)

    ms = MonthlyStats(data_dir=str(tmp_data_dir))
    stats = ms.compute_single_month("2023-01", "t", "city", time_offset="PT0H")
    # Gjennomsnitt 15, median 15, std = sqrt(((10-15)^2+(20-15)^2)/2) = 5
    assert stats == {"mean": 15.0, "median": 15.0, "std": pytest.approx(5.0)}


def test_compute_single_month_default_offset(tmp_data_dir):
    # Én offset PT6H, så default _get_min_offset bør plukke denne
    df = pd.DataFrame({
        "sourceId": ["S"],
        "referenceTime": ["2023-03-01"],
        "timeOffset": ["PT6H"],
        "elementId": ["u"],
        "value": [7],
    })
    write_csv("c", df, tmp_data_dir)

    ms = MonthlyStats(data_dir=str(tmp_data_dir))
    stats = ms.compute_single_month("2023-03", "u", "c")
    assert stats == {"mean": 7.0, "median": 7.0, "std": pytest.approx(0.0)}


def test_compute_single_month_empty_raises(tmp_data_dir):
    df = pd.DataFrame({
        "elementId": ["e"],
        "timeOffset": ["PT0H"],
        "referenceTime": ["2023-01-01"],
        "value": [5],
        "sourceId": ["S"],
    })
    write_csv("city", df, tmp_data_dir)

    ms = MonthlyStats(data_dir=str(tmp_data_dir))
    # Ber om month der det ikke finnes datapunkter
    with pytest.raises(ValueError):
        ms.compute_single_month("2023-02", "e", "city", time_offset="PT0H")


def test_compute_all_months(tmp_data_dir):
    # Fire datapunkter fordelt på to måneder
    df = pd.DataFrame({
        "sourceId": ["S"] * 4,
        "referenceTime": [
            "2023-01-10", "2023-01-20", "2023-02-05", "2023-02-25"
        ],
        "timeOffset": ["PT0H"] * 4,
        "elementId": ["m"] * 4,
        "value": [2, 4, 6, 8],
    })
    write_csv("oslo", df, tmp_data_dir)

    ms = MonthlyStats(data_dir=str(tmp_data_dir))
    out = ms.compute_all_months("m", "oslo", time_offset="PT0H")

    # Forvent to rader: '2023-01' og '2023-02'
    assert list(out["year_month"]) == ["2023-01", "2023-02"]
    # Januar: mean=(2+4)/2=3, median=3, std=1; Februar: mean=(6+8)/2=7, std=1
    jan = out[out["year_month"] == "2023-01"].iloc[0]
    feb = out[out["year_month"] == "2023-02"].iloc[0]
    assert jan["mean"] == 3.0
    assert jan["median"] == 3.0
    assert jan["std"] == pytest.approx(1.414)
    assert feb["mean"] == 7.0
    assert feb["median"] == 7.0
    assert feb["std"] == pytest.approx(1.414)


def test_compute_all_months_default_offset(tmp_data_dir):
    # Kun én offset PT12H, default vil plukke denne
    df = pd.DataFrame({
        "sourceId": ["S"],
        "referenceTime": ["2024-05-01"],
        "timeOffset": ["PT12H"],
        "elementId": ["z"],
        "value": [100],
    })
    write_csv("t", df, tmp_data_dir)

    ms = MonthlyStats(data_dir=str(tmp_data_dir))
    out = ms.compute_all_months("z", "t")
    # En rad med year_month "2024-05"
    assert out.shape[0] == 1
    assert out["year_month"].iloc[0] == "2024-05"
    assert out["mean"].iloc[0] == 100.0


def test_compute_all_months_no_data_raises(tmp_data_dir):
    # CSV finnes, men ingen records for element 'q'
    df = pd.DataFrame({
        "sourceId": ["S"],
        "referenceTime": ["2025-01-01"],
        "timeOffset": ["PT0H"],
        "elementId": ["p"],
        "value": [1],
    })
    write_csv("oslo", df, tmp_data_dir)

    ms = MonthlyStats(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError):
        ms.compute_all_months("q", "oslo", time_offset="PT0H")
