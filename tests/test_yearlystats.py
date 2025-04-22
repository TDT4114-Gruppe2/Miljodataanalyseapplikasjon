import pandas as pd
import pytest
from pathlib import Path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from src.analysis.yearlystats import YearlyStats


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Oppretter en midlertidig data-mappe."""
    d = tmp_path / "data"
    d.mkdir()
    return d


def write_csv_for(city: str, df: pd.DataFrame, data_dir: Path):
    """Hjelpefunksjon: skriver DataFrame til vaerdata_{city}.csv."""
    path = data_dir / f"vaerdata_{city}.csv"
    df.to_csv(path, index=False)
    return path


def test_compute_yearly_mean_default(tmp_data_dir):
    # Lager to år med to målinger hver
    df = pd.DataFrame({
        "sourceId": ["S"] * 4,
        "referenceTime": ["2020-01-01", "2020-06-01", "2021-01-01", "2021-06-01"],
        "timeOffset": ["PT0H"] * 4,
        "elementId": ["el"] * 4,
        "value": [1, 3, 2, 4],
    })
    write_csv_for("city", df, tmp_data_dir)

    ys = YearlyStats(data_dir=str(tmp_data_dir))
    out = ys.compute_yearly("city", "el")

    # Skal ha to år: 2020 og 2021
    assert list(out["year"]) == [2020, 2021]
    # Gjennomsnitt: 2020 → (1+3)/2=2, 2021 → (2+4)/2=3
    assert out.loc[out["year"] == 2020, "value"].iloc[0] == 2
    assert out.loc[out["year"] == 2021, "value"].iloc[0] == 3


def test_compute_yearly_specific_sum(tmp_data_dir):
    # To poster for 2020, én for 2021
    df = pd.DataFrame({
        "sourceId": ["S", "S", "S"],
        "referenceTime": ["2020-01-01", "2020-02-01", "2021-01-01"],
        "timeOffset": ["PT0H"] * 3,
        "elementId": ["el"] * 3,
        "value": [1, 2, 10],
    })
    write_csv_for("c", df, tmp_data_dir)

    ys = YearlyStats(data_dir=str(tmp_data_dir))
    out = ys.compute_yearly("c", "el", year=2020, aggregate="sum")

    assert len(out) == 1
    assert out["value"].iloc[0] == 3  # 1 + 2


def test_compute_yearly_none_aggregate_requires_year(tmp_data_dir):
    df = pd.DataFrame({
        "sourceId": ["S"],
        "referenceTime": ["2020-01-01"],
        "timeOffset": ["PT0H"],
        "elementId": ["x"],
        "value": [1],
    })
    write_csv_for("c", df, tmp_data_dir)

    ys = YearlyStats(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError):
        ys.compute_yearly("c", "x", aggregate=None)


def test_compute_yearly_none_raw_and_no_data(tmp_data_dir):
    df = pd.DataFrame({
        "sourceId": ["S"],
        "referenceTime": ["2020-01-01"],
        "timeOffset": ["PT0H"],
        "elementId": ["y"],
        "value": [1],
    })
    write_csv_for("c", df, tmp_data_dir)

    ys = YearlyStats(data_dir=str(tmp_data_dir))
    # Ber om rådata for år som ikke finnes
    with pytest.raises(ValueError):
        ys.compute_yearly("c", "y", year=2021, aggregate=None)


def test_invalid_aggregate(tmp_data_dir):
    df = pd.DataFrame({
        "sourceId": ["S"],
        "referenceTime": ["2020-01-01"],
        "timeOffset": ["PT0H"],
        "elementId": ["i"],
        "value": [1],
    })
    write_csv_for("c", df, tmp_data_dir)

    ys = YearlyStats(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError):
        ys.compute_yearly("c", "i", aggregate="foo")


def test_percent_change(tmp_data_dir):
    # Enkel to‑dagers serie: 1 → 2
    df = pd.DataFrame({
        "sourceId": ["S", "S"],
        "referenceTime": ["2020-01-01", "2020-01-02"],
        "timeOffset": ["PT0H", "PT0H"],
        "elementId": ["e", "e"],
        "value": [1, 2],
    })
    write_csv_for("ct", df, tmp_data_dir)

    ys = YearlyStats(data_dir=str(tmp_data_dir))
    out = ys.percent_change("ct", "e", frequency="D", statistic="mean")

    # Én prosent‑endradsrad: (2/1 - 1) * 100 = 100%
    assert len(out) == 1
    assert out["percent_change"].iloc[0] == pytest.approx(100.0)


def test_percent_change_invalid_statistic(tmp_data_dir):
    ys = YearlyStats(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError):
        ys.percent_change("any", "any", statistic="foo")


def test_percent_change_invalid_frequency(tmp_data_dir):
    ys = YearlyStats(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError):
        ys.percent_change("any", "any", frequency="XYZ")


def test_climatological_monthly_mean_default(tmp_data_dir):
    df = pd.DataFrame({
        "sourceId": ["S", "S", "S"],
        "referenceTime": ["2020-01-01", "2020-02-01", "2020-02-15"],
        "timeOffset": ["PT0H"] * 3,
        "elementId": ["z"] * 3,
        "value": [10, 20, 30],
    })
    write_csv_for("city", df, tmp_data_dir)

    ys = YearlyStats(data_dir=str(tmp_data_dir))
    out = ys.climatological_monthly_mean("city", "z")

    # Skal ha måned 1 og 2
    assert set(out["month"]) == {1, 2}
    # Måned 1: 10, måned 2: (20+30)/2 = 25
    assert out.loc[out["month"] == 1, "value"].iloc[0] == 10
    assert out.loc[out["month"] == 2, "value"].iloc[0] == 25


def test_climatological_monthly_mean_invalid_statistic(tmp_data_dir):
    ys = YearlyStats(data_dir=str(tmp_data_dir))
    with pytest.raises(ValueError):
        ys.climatological_monthly_mean("x", "y", statistic="foo")
