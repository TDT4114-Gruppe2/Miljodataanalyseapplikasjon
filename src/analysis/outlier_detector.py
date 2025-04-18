"""
outlier_detector.py

Gjenbrukbar klasse for å oppdage og/eller fjerne outliers
ved hjelp av IQR-metoden (interkvartilspennet).
Støtter både "vanlige" og ekstreme outliers (ytre gjerder).
"""

import numpy as np
import pandas as pd


class OutlierDetector:
    def __init__(self, whisker=None):
        """
        Parametre
        ---------
        whisker : float, optional
            Faktor som multipliseres med IQR for å sette grensene.
            Vanligvis:
              - 1.5 for vanlige outliers
              - 3.0 for ekstreme outliers
        """
        if whisker not in (None, 1.5, 3.0):
            raise ValueError("whisker må være 1.5, 3.0 eller None")
        self.whisker = whisker

    def summarize(self, series):
        """
        Returnerer Q1, Q3, IQR og grenser (indre/ytre gjerder).
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

    def detect_iqr(self, series, extreme=False, whisker=None):
        """
        Returnerer en boolsk maske som er True for outliers.

        Parametre
        ---------
        series : pd.Series
            Verdiene som skal undersøkes.
        extreme : bool
            Hvis True brukes 3.0 × IQR, ellers 1.5 × IQR.
        whisker : float, optional
            Overstyr standard whisker-verdi.

        Returnerer
        ----------
        pd.Series[bool]
        """
        whisker = whisker if whisker is not None else (self.whisker or (3.0 if extreme else 1.5))
        if whisker <= 0:
            raise ValueError("whisker må være positiv")

        numeric = pd.to_numeric(series, errors="coerce")
        q1, q3 = numeric.quantile([0.25, 0.75])
        iqr = q3 - q1

        lower = q1 - whisker * iqr
        upper = q3 + whisker * iqr
        return (numeric < lower) | (numeric > upper)
    
    def count_outliers_iqr(self, series, extreme=False, whisker=None):
        """
        Returnerer heltall = antall verdier som klassifiseres som outliers.
        """
        mask = self.detect_iqr(series, extreme=extreme, whisker=whisker)
        return int(mask.sum())
    
    def remove_outliers_iqr(self, series, extreme=False, whisker=None):
        """
        Returnerer en ny serie der outliers er satt til NaN.
        """
        mask = self.detect_iqr(series, extreme=extreme, whisker=whisker)
        return series.where(~mask)

    @staticmethod
    def detect(series, extreme=False):
        """
        Statisk snarvei – kjør direkte uten å instansiere klassen.
        """
        return OutlierDetector().detect_iqr(series, extreme=extreme)