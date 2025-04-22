"""Finner outliers i dataene ved hjelp av IQR-metoden."""
import pandas as pd


class OutlierDetector:
    """
    IQR‑basert deteksjon/fjerning av outliers.

    whisker = 1.5 (vanlige) eller 3.0 (ekstreme). None = velg dynamisk.
    """

    def __init__(self, whisker: float | None = None):
        """Definerer hva verdien for en outlier er."""
        if whisker not in (None, 1.5, 3.0):
            raise ValueError("whisker må være 1.5, 3.0 eller None")
        self.whisker = whisker

    def summarize(self, series: pd.Series) -> dict[str, float]:
        """Returnerer grunnleggende IQR-statistikk for en serie."""
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        q1 = numeric.quantile(0.25)
        q3 = numeric.quantile(0.75)
        iqr = q3 - q1
        return {
            "Q1": q1,
            "Q3": q3,
            "IQR": iqr,
            "lower_inner": q1 - 1.5 * iqr,
            "upper_inner": q3 + 1.5 * iqr,
            "lower_outer": q1 - 3.0 * iqr,
            "upper_outer": q3 + 3.0 * iqr,
        }

    def detect_iqr(
        self,
        series: pd.Series,
        *,
        extreme: bool = False,
        whisker: float | None = None,
    ) -> pd.Series:
        """Finner outliers i serien."""
        whisker = whisker if whisker is not None else (
            self.whisker or (3.0 if extreme else 1.5)
        )
        if whisker <= 0:
            raise ValueError("whisker må være positiv")

        numeric = pd.to_numeric(series, errors="coerce")
        q1, q3 = numeric.quantile([0.25, 0.75])
        iqr = q3 - q1

        lower = q1 - whisker * iqr
        upper = q3 + whisker * iqr
        return (numeric < lower) | (numeric > upper)

    # Teller og fjerner outliers
    def count_outliers_iqr(self, series, **kwargs) -> int:
        """Returnerer antall outliers i serien."""
        return int(self.detect_iqr(series, **kwargs).sum())

    def remove_outliers_iqr(self, series, **kwargs) -> pd.Series:
        """Fjerner outliers fra serien."""
        mask = self.detect_iqr(series, **kwargs)
        return series.where(~mask)

    @staticmethod
    def detect(series, extreme: bool = False):
        """Finner outliers i serien."""
        return OutlierDetector().detect_iqr(series, extreme=extreme)

__all__ = ["OutlierDetector"]
