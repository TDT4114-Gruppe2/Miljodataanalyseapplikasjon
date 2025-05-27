"""Interpolering av værdata."""

import pandas as pd

from statsmodels.tsa.seasonal import seasonal_decompose


class WeatherDataPipeline:
    """
    Pipeline for interpolering og konvertering av værdata.

    fra rå, langt format til imputert, langt format. Kombinerer
    interpolering (lineær + sesong) med konvertering mellom bredt
    og langt CSV-format.
    """

    def __init__(
        self,
        small_gap_days: int = 3,
        seasonal_period: int = 365,
        model: str = "additive",
    ) -> None:
        """Initialisér pipelinen."""
        self.small_gap_days = small_gap_days
        self.seasonal_period = seasonal_period
        self.model = model

    def _infer_source_id(self, path: str) -> str:
        """Utled sourceId fra filsti basert på bynavn."""
        p = path.lower()
        if "oslo" in p:
            return "SN18700:0"
        if "troms" in p:
            return "SN90450:0"
        raise ValueError(f"Kunne ikke utlede sourceId fra '{path}'")

    def _format_time_offset(self, dt: pd.Timestamp) -> str:
        """Formatér tidsdifferanse fra midnatt som ISO 8601-periode."""
        hours = dt.hour
        minutes = dt.minute
        offset = f"PT{hours}H"
        if minutes:
            offset += f"{minutes}M"
        return offset

    def _map_unit(self, element: str) -> str:
        """Map elementId til måleenhet."""
        if "temperature" in element:
            return "degC"
        if "wind_speed" in element:
            return "m/s"
        if "precipitation_amount" in element:
            return "mm"
        return ""

    def _seasonal_impute(self, series: pd.Series) -> pd.Series:
        """Utfør sesongdekomponering og fyll større hull i serien."""
        temp = series.interpolate(
            method="time",
            limit_direction="both",
        )
        decomp = seasonal_decompose(
            temp,
            model=self.model,
            period=self.seasonal_period,
            extrapolate_trend="freq",
        )
        comp = (
            decomp.trend
            .add(decomp.resid)
            .interpolate(method="time", limit_direction="both")
        )
        imputed = comp.add(decomp.seasonal)
        return imputed.ffill().bfill()

    def impute_wide(self, wide_df: pd.DataFrame) -> pd.DataFrame:
        """Imputer df på bredt format (DatetimeIndex, kolonner=elementId)."""
        df = wide_df.copy()
        df = df.interpolate(
            method="time",
            limit=self.small_gap_days,
        )
        for col in df.columns:
            if df[col].isna().any():
                df[col] = self._seasonal_impute(df[col])
        return df

    def process(self, input_file: str, output_file: str) -> None:
        """Les CSV, interpolér og skriv imputert CSV."""
        # Les inn data
        df_long = pd.read_csv(
            input_file,
            parse_dates=["referenceTime"],
        )

        # Ekstraher timer og minutter
        time_parts = df_long["timeOffset"].str.extract(
            r"PT(?:(\d+)H)?(?:(\d+)M)?"
        )
        hours = (
            pd.to_numeric(
                time_parts[0],
                errors="coerce",
            )
            .fillna(0)
            .astype("Int64")
        )
        minutes = (
            pd.to_numeric(
                time_parts[1],
                errors="coerce",
            )
            .fillna(0)
            .astype("Int64")
        )

        # Lag full datetime-kolonne
        df_long["datetime"] = (
            df_long["referenceTime"]
            + pd.to_timedelta(hours, unit="h")
            + pd.to_timedelta(minutes, unit="m")
        )

        # Pivot til bredt format
        wide = (
            df_long
            .pivot(
                index="datetime",
                columns="elementId",
                values="value",
            )
            .sort_index()
            .infer_objects()
        )

        # Imputer
        filled = self.impute_wide(wide)

        # Melt tilbake til langt format
        out = (
            filled
            .reset_index()
            .melt(
                id_vars=["datetime"],
                var_name="elementId",
                value_name="value",
            )
        )

        # Legg på metadata
        out["sourceId"] = self._infer_source_id(input_file)
        out["referenceTime"] = (
            out["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        )
        out["timeOffset"] = out["datetime"].apply(
            self._format_time_offset
        )
        out["unit"] = out["elementId"].apply(self._map_unit)

        # Sorter rader
        out = (
            out
            .sort_values(
                by=["referenceTime", "timeOffset", "elementId"]
            )
            .reset_index(drop=True)
        )

        # Avrund til 3 desimaler
        out["value"] = out["value"].round(3)

        # Skriv til CSV
        cols = [
            "sourceId",
            "referenceTime",
            "timeOffset",
            "elementId",
            "value",
            "unit",
        ]
        out[cols].to_csv(
            output_file,
            index=False,
            float_format="%.3f",
        )
