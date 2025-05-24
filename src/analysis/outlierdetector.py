"""IQR-basert deteksjon og fjerning av outliers i pandas-serier."""

import pandas as pd


class OutlierDetector:
    """
    Utfører outlier-analyse basert på inter-kvartilbredde (IQR).

    whisker = 1.5 (standard) eller 3.0 (ekstreme). None = dynamisk valg.
    """

    def __init__(self, whisker: float | None = None) -> None:
        """
        Initialiserer detektor med valgt IQR-whisker.

        Parametre:
            whisker (float | None): Faktor for whisker. Må være 1.5, 3.0 eller None.

        Hever:
            ValueError: Hvis whisker ikke er gyldig.
        """
        valid = {None, 1.5, 3.0}
        if whisker not in valid:
            raise ValueError("whisker må være 1.5, 3.0 eller None")
        self.whisker = whisker

    def summarize(self, series: pd.Series) -> dict[str, float]:
        """
        Beregn IQR og standard whisker-grenser for en pandas-serie.

        Parametre:
            series (pd.Series): Numeriske data.

        Returnerer:
            dict[str, float]: Q1, Q3, IQR, lower_inner, upper_inner,
                               lower_outer, upper_outer.
        """
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
        """
        Identifiser outliers basert på IQR-whisker for serien.

        Parametre:
            series (pd.Series): Numeriske data.
            extreme (bool): Hvis True, bruk whisker=3.0; ellers 1.5 (hvis self.whisker=None).
            whisker (float | None): Overstyr self.whisker hvis oppgitt.

        Returnerer:
            pd.Series: Boolsk maske der True indikerer outlier.

        Hever:
            ValueError: Hvis whisker <= 0.
        """
        # Bestem whisker-verdi
        w = whisker if whisker is not None else (
            self.whisker or (3.0 if extreme else 1.5)
        )
        if w <= 0:
            raise ValueError("whisker må være positiv")

        numeric = pd.to_numeric(series, errors="coerce")
        q1, q3 = numeric.quantile([0.25, 0.75])
        iqr = q3 - q1

        lower = q1 - w * iqr
        upper = q3 + w * iqr
        return (numeric < lower) | (numeric > upper)

    def count_outliers_iqr(self, series: pd.Series, **kwargs) -> int:
        """
        Telle antall IQR-outliers i en serie.

        Parametre:
            series (pd.Series): Numeriske data.
            **kwargs: Ekstra argumenter til detect_iqr.

        Returnerer:
            int: Antall outliers.
        """
        return int(self.detect_iqr(series, **kwargs).sum())

    def remove_outliers_iqr(
        self,
        series: pd.Series,
        **kwargs,
    ) -> pd.Series:
        """
        Fjern IQR-outliers fra serien.

        Parametre:
            series (pd.Series): Numeriske data.
            **kwargs: Ekstra argumenter til detect_iqr.

        Returnerer:
            pd.Series: Serie med outliers erstattet av NaN.
        """
        mask = self.detect_iqr(series, **kwargs)
        return series.where(~mask)

    @staticmethod
    def detect(series: pd.Series, extreme: bool = False) -> pd.Series:
        """
        Enkel deteksjon av outliers med standard whisker.

        Parametre:
            series (pd.Series): Numeriske data.
            extreme (bool): Bruk ekstreme whiskers (3.0) hvis True.

        Returnerer:
            pd.Series: Boolsk maske for outliers.
        """
        return OutlierDetector().detect_iqr(series, extreme=extreme)


__all__ = ["OutlierDetector"]
