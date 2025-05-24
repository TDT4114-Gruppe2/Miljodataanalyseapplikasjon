import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose


class WeatherDataPipeline:
    """
    Pipeline for interpolering og konvertering av værdata fra rå, langt format
    til imputert, langt format. Kombinerer interpolering (lineær + sesong) med
    konvertering mellom bredt og langt CSV-format.
    """

    def __init__(
        self,
        small_gap_days: int = 3,
        seasonal_period: int = 365,
        model: str = "additive",
    ) -> None:
        """
        Initialiser pipelinen.

        Args:
            small_gap_days (int): Maks antall dager for lineær interpolering.
            seasonal_period (int): Periode for sesongdekomponering (årsdøgn).
            model (str): Modelltype ('additive' eller 'multiplicative').
        """
        self.small_gap_days = small_gap_days
        self.seasonal_period = seasonal_period
        self.model = model

    def _infer_source_id(self, path: str) -> str:
        """
        Utled sourceId fra filsti basert på bynavn.
        """
        p = path.lower()
        if "oslo" in p:
            return "SN18700:0"
        if "troms" in p:
            return "SN90450:0"
        raise ValueError(f"Kunne ikke utlede sourceId fra '{path}'")

    def _format_time_offset(self, dt: pd.Timestamp) -> str:
        """
        Formater tidsdifferanse fra midnatt som ISO 8601-periode.
        """
        hours = dt.hour
        minutes = dt.minute
        offset = f"PT{hours}H"
        if minutes:
            offset += f"{minutes}M"
        return offset

    def _map_unit(self, element: str) -> str:
        """
        Map elementId til måleenhet.
        """
        if "temperature" in element:
            return "degC"
        if "wind_speed" in element:
            return "m/s"
        if "precipitation_amount" in element:
            return "mm"
        return ""

    def _seasonal_impute(self, series: pd.Series) -> pd.Series:
        """
        Utfør sesongdekomponering og fyll større hull i serien.
        """
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
        """
        Imputer bredt format DataFrame (DatetimeIndex, kolonner=elementId).
        """
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
        """
        Les et langt-format CSV, interpoler og skriv imputert CSV i langt format.

        Args:
            input_file (str): Raw CSV med kolonner
                [sourceId, referenceTime, timeOffset, elementId, value, unit]
            output_file (str): CSV for imputert output i samme langt-format.
        """
        df_long = pd.read_csv(
            input_file,
            parse_dates=["referenceTime"],
        )
        hours = (
            df_long["timeOffset"]
            .str.extract(r"PT(\d+)H")[0]
            .fillna(0)
            .astype(int)
        )
        df_long["datetime"] = (
            df_long["referenceTime"]
            + pd.to_timedelta(hours, unit="h")
        )

        wide = df_long.pivot(
            index="datetime",
            columns="elementId",
            values="value",
        )
        wide = wide.infer_objects()
        filled = self.impute_wide(wide)

        out = filled.reset_index().melt(
            id_vars=["datetime"],
            var_name="elementId",
            value_name="value",
        )
        out["sourceId"] = self._infer_source_id(input_file)
        out["referenceTime"] = (
            out["datetime"]
            .dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        )
        out["timeOffset"] = out["datetime"].apply(
            self._format_time_offset
        )
        out["unit"] = out["elementId"].apply(self._map_unit)

        cols = [
            "sourceId",
            "referenceTime",
            "timeOffset",
            "elementId",
            "value",
            "unit",
        ]
        out[cols].to_csv(output_file, index=False)
