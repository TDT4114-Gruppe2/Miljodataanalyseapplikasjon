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
import calendar

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
    
    def _laveste_offset(self, by: str, element_id: str) -> str:
        """Returnerer offset‑strengen (PT⧸H) med minste timetall."""
        df = self.stats._load_city(by)
        offs = df.loc[df["elementId"] == element_id, "timeOffset"].dropna().unique()
        if not len(offs):
            raise ValueError(f"Ingen timeOffset funnet for {by=}, {element_id=}")
        hours = [int(re.search(r"PT(\d+)H", o).group(1)) for o in offs]
        return offs[hours.index(min(hours))]

    def langtidsmiddel_per_måned(
        self,
        by: str,
        element_id: str,
        remove_outliers: bool = False,
        statistikk: str = "mean",      # "mean", "median", "std"
    ) -> pd.DataFrame:
        """
        Returnerer 12‑rads DataFrame (month, month_name, verdi).

        *Velger alltid laveste timeOffset automatisk.*
        *Kan beregne med eller uten ekstreme outliers.*
        """
        if statistikk not in {"mean", "median", "std"}:
            raise ValueError("statistikk må være 'mean', 'median' eller 'std'")

        off = self._laveste_offset(by, element_id)   # auto‑offset

        # -- hent rådata for byen/element/offset
        df = self.stats._load_city(by)
        df = df[(df["elementId"] == element_id) & (df["timeOffset"] == off)].copy()
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["referenceTime"] = pd.to_datetime(df["referenceTime"], utc=True)

        if remove_outliers:         # fjern ekstreme outliers (3 × IQR)
            mask = self.detector.detect_iqr(df["value"], extreme=True)
            df.loc[mask, "value"] = pd.NA

        # -- gruppér på kalendermåned
        df["month"] = df["referenceTime"].dt.month
        agg_map = {
            "mean": df.groupby("month")["value"].mean,
            "median": df.groupby("month")["value"].median,
            "std": lambda: df.groupby("month")["value"].std(ddof=0),
        }
        klima = agg_map[statistikk]().reset_index().rename(columns={"value": "verdi"})

        klima["month_name"] = klima["month"].apply(
            lambda m: calendar.month_abbr[m].capitalize()
        )
        return klima[["month", "month_name", "verdi"]]
    
    def compute_yearly (
            self,
            by: str,
            element_id: str,
            year: int | None = None,
            *,
            time_offset: str | None = None,
            aggregate: str | None = "mean",     # "mean", "sum", "median", "std" eller None
        ) -> pd.DataFrame:
        """
        Henter data og gjør én av to ting:

        1) Hvis *aggregate* settes til "mean" (standard), "sum" eller "median":
           - Returnerer én rad per år med valgt statistikk.
           - Hvis *year* oppgis, får du én rad for det året.

        2) Hvis *aggregate* = None:
           - Returnerer **alle daglige verdier** for oppgitt *year*.
             (Krever da at *year* er satt.)

        Parametre
        ---------
        by           : By/filnavn, f.eks. "oslo"
        element_id   : Element‑streng, f.eks. "sum(precipitation_amount P1D)"
        year         : int eller None
        time_offset  : f.eks. "PT0H". Hvis None velges laveste via _laveste_offset()
        aggregate    : "mean", "sum", "median" eller None (rå verdier)

        Returnerer
        ----------
        pd.DataFrame
            - Scenario 1: kolonner ["year", "verdi"]
            - Scenario 2: kolonner ["referenceTime", "value", "elementId", "timeOffset"]
        """
        # ---------- finn offset --------------------------------------
        if time_offset is None:
            time_offset = self._laveste_offset(by, element_id)

        # ---------- hent og filtrer rådata ---------------------------
        df = (
            self.stats._load_city(by)
              .query("elementId == @element_id and timeOffset == @time_offset")
              .assign(value=lambda d: pd.to_numeric(d["value"], errors="coerce"))
              .dropna(subset=["value"])
        )

        # ---------- særbehandling hvis råverdier ønskes -------------
        if aggregate is None:
            if year is None:
                raise ValueError("year må angis når aggregate=None (rå verdier)")
            df = df[df["referenceTime"].dt.year == year]
            if df.empty:
                raise ValueError(f"Ingen verdier for {by=} {element_id=} {year=}")
            return df.reset_index(drop=True)

        # ---------- legg til årskolonne ------------------------------
        df["year"] = df["referenceTime"].dt.year
        if year is not None:
            df = df[df["year"] == year]

        if df.empty:
            raise ValueError("Ingen data etter filtrering – sjekk input")

        # ---------- aggreger per år ----------------------------------
        agg_map = {
            "mean": df.groupby("year")["value"].mean,
            "sum": df.groupby("year")["value"].sum,
            "median": df.groupby("year")["value"].median,
            "std": df.groupby("year")["value"].std,
        }
        if aggregate not in agg_map:
            raise ValueError("aggregate må være 'mean', 'sum', 'median' eller None")

        out = agg_map[aggregate]().reset_index(name="verdi")
        return out
