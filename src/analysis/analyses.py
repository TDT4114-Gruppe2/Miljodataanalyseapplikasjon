"""data_analyzer.py

Avansert analysemotor som bygger videre på *MonthlyStatistics* og
*OutlierDetector* for å utføre hyppig brukte analyser i prosjektet.

Funksjonalitet som tidligere lå spredt i notebook‑celler er samlet i én klasse
slik at den kan importeres fra både skript, notebooks og tests uten gjentakelse
av kode.
"""

import re
import pandas as pd
from outlier_detector import OutlierDetector
from monthly_statistics import MonthlyStatistics


class DataAnalyzer:
    def __init__(self, data_dir):
        self.stats = MonthlyStatistics(data_dir)
        self.detector = OutlierDetector()

    def finn_outliers_per_maaned(
            self,
            by: str,
            element_id: str,
            time_offset: str,
            vis_tomme_maaneder: bool = False
        ) -> pd.DataFrame:
        """
        Returnerer en DataFrame med oversikt over hvor mange outliers som ble
        fjernet per måned for en gitt by, elementId og timeOffset.

        Parametre:
        - vis_tomme_maaneder: Hvis True, inkluder også måneder uten outliers.

        Kolonner: year_month, outliers_removed, antall_totalt, andel_outliers_%%
        """
        df = self.stats._load_city(by)
        df = df[
            (df["elementId"] == element_id) &
            (df["timeOffset"] == time_offset)
        ].copy()

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(df["referenceTime"], utc=True)
        df["year_month"] = df["referenceTime"].dt.tz_localize(None).dt.to_period("M").astype(str)

        resultater = []
        for ym, gruppe in df.groupby("year_month"):
            original = gruppe["value"]
            mask = self.detector.detect_iqr(original, extreme=True)
            antall_outliers = int(mask.sum())

            if vis_tomme_maaneder or antall_outliers > 0:
                resultater.append({
                    "year_month": ym,
                    "outliers_removed": antall_outliers,
                    "antall_totalt": len(original),
                    "andel_outliers_%": round(100 * antall_outliers / len(original), 1) if len(original) > 0 else 0.0,
                })

        return pd.DataFrame(resultater).sort_values("year_month").reset_index(drop=True)

    def statistikk_med_og_uten_outliers(
            self,
            by: str,
            element_id: str,
            time_offset: str,
            statistikk: str
        ) -> pd.DataFrame:
        """
        Returnerer en DataFrame med månedlige statistiske mål
        (mean, median eller std), både med og uten outliers.

        Kolonner: year_month, <stat>_with_outliers, <stat>_without_outliers,
                  outliers_removed, elementId
        """
        if statistikk not in {"mean", "median", "std"}:
            raise ValueError("statistikk må være 'mean', 'median' eller 'std'")

        df = self.stats._load_city(by)
        df = df[
            (df["elementId"] == element_id) &
            (df["timeOffset"] == time_offset)
        ].copy()

        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(df["referenceTime"], utc=True)
        df["year_month"] = df["referenceTime"].dt.tz_localize(None).dt.to_period("M").astype(str)

        resultater = []

        for ym, gruppe in df.groupby("year_month"):
            serie = gruppe["value"]
            outlier_mask = self.detector.detect_iqr(serie, extreme=True)

            if serie.dropna().empty:
                continue

            renset = serie.where(~outlier_mask).dropna()

            if statistikk == "mean":
                verdi_full = serie.mean()
                verdi_renset = renset.mean() if not renset.empty else None
            elif statistikk == "median":
                verdi_full = serie.median()
                verdi_renset = renset.median() if not renset.empty else None
            else:
                verdi_full = serie.std(ddof=0)
                verdi_renset = renset.std(ddof=0) if not renset.empty else None

            resultater.append({
                "year_month": ym,
                f"{statistikk}_with_outliers": round(verdi_full, 3),
                f"{statistikk}_without_outliers": round(verdi_renset, 3) if verdi_renset is not None else None,
                "outliers_removed": int(outlier_mask.sum()),
                "elementId": element_id
            })

        kolonnenavn = [
            "year_month",
            f"{statistikk}_with_outliers",
            f"{statistikk}_without_outliers",
            "outliers_removed",
            "elementId"
        ]

        return pd.DataFrame(resultater, columns=kolonnenavn).sort_values("year_month").reset_index(drop=True)

    def les_manglende_verdier(
            self,
            path: str
        ) -> pd.DataFrame:
        """
        Leser en CSV med manglende verdier og returnerer rader
        der enten 'oslo_value' eller 'tromso_value' mangler.

        Returnerer en DataFrame med:
        - date
        - timeOffset
        - elementId
        - mangler (Oslo eller Tromsø)
        """
        df = pd.read_csv(path)

        mangler_oslo = df["oslo_value"].isna()
        mangler_tromso = df["tromso_value"].isna()

        df["mangler"] = None
        df.loc[mangler_oslo, "mangler"] = "Oslo"
        df.loc[mangler_tromso, "mangler"] = "Tromsø"

        df_mangler = df[df["mangler"].notna()].copy()

        return df_mangler[["date", "timeOffset", "elementId", "mangler"]].reset_index(drop=True)

    """
    Mangelfull funksjon laget for store analyser, men mangler upraktisk kombinering av data
    """

    def kombiner_variabler_analyse(
        self,
        city: str,
        element_id1: str,
        element_id2: str,
        element_id3: str,
        statistic: str = "mean",        # "mean", "median" eller "std"
        frequency: str = "ME",           # "D", "W", "ME", "YE"
        remove_outliers: bool = True,
        start: str | None = None,       # "YYYY-MM" eller "YYYY-MM-DD"
        end: str | None = None,         # samme format som start
    ) -> pd.DataFrame:
        """
        Kombinerer (element_id1 + element_id2) og sammenligner med element_id3.

        Resultatet er én DataFrame med:
            periode | komb12_<stat> | elem3_<stat> | n_outliers

        Parametre:
        city, element_id1/2/3, statistic, frequency, remove_outliers, start, end
        """
        df = self.stats._load_city(city)

        if start or end:
            mask_period = pd.Series(True, index=df.index)
            if start:
                start_ts = pd.to_datetime(start).tz_localize("UTC")
                mask_period &= df["referenceTime"] >= start_ts
            if end:
                end_ts = pd.to_datetime(end).tz_localize("UTC")
                mask_period &= df["referenceTime"] <= end_ts
            df = df[mask_period]

        def _laveste_offset(elem):
            offs = df.loc[df["elementId"] == elem, "timeOffset"].dropna().unique()
            hours = [int(re.search(r"PT(\\d+)H", o).group(1)) for o in offs]
            return offs[hours.index(min(hours))]

        off1 = _laveste_offset(element_id1)
        off2 = _laveste_offset(element_id2)
        off3 = _laveste_offset(element_id3)

        sub1 = df[(df["elementId"] == element_id1) & (df["timeOffset"] == off1)].copy()
        sub2 = df[(df["elementId"] == element_id2) & (df["timeOffset"] == off2)].copy()
        sub3 = df[(df["elementId"] == element_id3) & (df["timeOffset"] == off3)].copy()

        for sub in (sub1, sub2, sub3):
            sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
            sub["referenceTime"] = pd.to_datetime(sub["referenceTime"], utc=True)
            sub.set_index("referenceTime", inplace=True)

        def _agg(sub):
            ser = sub["value"]
            if remove_outliers:
                ser = ser[~self.detector.detect_iqr(ser, extreme=True)]
            if statistic == "mean":
                return ser.resample(frequency).mean()
            elif statistic == "median":
                return ser.resample(frequency).median()
            else:
                return ser.resample(frequency).std(ddof=0)

        s1 = _agg(sub1)
        s2 = _agg(sub2)
        s3 = _agg(sub3)

        df_out = pd.DataFrame({
            "komb12_" + statistic: (s1 + s2),
            f"{element_id3}_{statistic}": s3,
        }).dropna(how="all")

        if remove_outliers:
            outlier_count = (
                self.detector.detect_iqr(sub1["value"], extreme=True).resample(frequency).sum() +
                self.detector.detect_iqr(sub2["value"], extreme=True).resample(frequency).sum() +
                self.detector.detect_iqr(sub3["value"], extreme=True).resample(frequency).sum()
            )
            df_out["n_outliers"] = outlier_count.astype("Int64")

        df_out.index.name = "periode"
        df_out.reset_index(inplace=True)
        return df_out

    def prosentvis_endring(
            self,
            by: str,
            element_id: str,
            time_offset: str,
            statistikk: str = "mean",
            frekvens: str = "D",
            start: str | None = None,
            end: str | None = None   
        ) -> pd.DataFrame:
        """
        Returnerer prosentvis endring i en valgt statistikk (mean, median, std)
        mellom påfølgende perioder (dag, måned, år).

        Parametre:
        - by: f.eks. "oslo"
        - element_id: f.eks. "mean(air_temperature P1D)"
        - time_offset: f.eks. "PT0H"
        - statistikk: "mean", "median" eller "std"
        - frekvens: "D" (daglig), "ME" (månedlig), "YE" (årlig)

        Returnerer en DataFrame med:
        - periode
        - verdi
        - prosent_endring
        """
        if statistikk not in {"mean", "median", "std"}:
            raise ValueError("statistikk må være 'mean', 'median' eller 'std'")
        
        if frekvens not in {"D", "ME", "YE"}:
            raise ValueError("frekvens må være 'D', 'ME' eller 'YE'")

        df = self.stats._load_city(by)
        if "referenceTime" not in df.columns:
            raise KeyError("Kolonnen 'referenceTime' mangler i datasettet")
        
        df = df[(df["elementId"] == element_id) & (df["timeOffset"] == time_offset)].copy()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(df["referenceTime"], utc=True)

        if df["referenceTime"].isna().all():
            raise ValueError("Alle verdier i 'referenceTime' er NaT – sjekk kildefilene")

        df.set_index("referenceTime", inplace=True)
        df.sort_index(inplace=True)

        if start or end:
            mask = pd.Series(True, index=df.index)
            if start:
                mask &= df.index >= pd.to_datetime(start).tz_localize("UTC")
            if end:
                mask &= df.index <= pd.to_datetime(end).tz_localize("UTC")
            df = df[mask]

        agg_map = {
            "mean": df["value"].resample(frekvens).mean,
            "median": df["value"].resample(frekvens).median,
            "std": lambda: df["value"].resample(frekvens).std(ddof=0),
        }
        agg_series = agg_map[statistikk]()

        df_endring = pd.DataFrame({"verdi": agg_series})
        df_endring["prosent_endring"] = (
            df_endring["verdi"].pct_change(fill_method=None) * 100
        )

        df_endring.index.name = "periode"
        df_endring = df_endring.reset_index()

        return df_endring.dropna(subset=["verdi", "prosent_endring"]).reset_index(drop=True)