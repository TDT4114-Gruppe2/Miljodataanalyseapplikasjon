"""Laster inn data fra CSV-filer."""

import os
import pandas as pd
import re

from functools import lru_cache


class DataLoader:
    """Laster værdata per by fra CSV-filer med standard filnavnmønster."""

    try:
        # Første forsøk: imputert data
        filename_template: str = "vaerdata_{city}_imputert.csv"
    except FileNotFoundError:
        # Andre forsøk: rådata
        filename_template: str = "vaerdata_{city}.csv"

    def __init__(self, data_dir: str) -> None:
        """
        Initialiserer DataLoader med katalog for datafilene.

        Parametre:
            data_dir (str): Mappe der CSV-filene ligger.
        """
        self.data_dir = data_dir

    @lru_cache(maxsize=None)
    def _load_city(self, city: str) -> pd.DataFrame:
        """
        Leser inn én by sin CSV og validerer innhold.

        Parametre:
            city (str): Bykode, f.eks. "oslo" eller "tromso".

        Returnerer:
            pd.DataFrame: Rådata med konvertert "referenceTime".
        """
        path = os.path.join(
            self.data_dir,
            self.filename_template.format(city=city),
        )
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fant ikke datafil: {path}")

        df = pd.read_csv(path, low_memory=False)

        if "referenceTime" not in df.columns:
            filename = os.path.basename(path)
            raise KeyError(
                "Kolonnen 'referenceTime' mangler i "
                f"'{filename}' – sjekk datagrunnlaget."
            )

        df["referenceTime"] = pd.to_datetime(
            df["referenceTime"], utc=True, errors="coerce"
        )
        return df

    def _get_min_offset(self, city: str, element_id: str) -> str:
        """
        Henter minste timeOffset (PT<n>H) for gitt element i gitt by.

        Parametre:
            city (str): Bykode for data.
            element_id (str): ElementId å sjekke,
            f.eks. "mean(air_temperature P1D)".

        Returnerer:
            str: Den gyldige timeOffset med lavest timer.

        Hever:
            ValueError: Hvis ingen gyldige offsets finnes.
        """
        df = self._load_city(city)
        offsets = (
            df.loc[df["elementId"] == element_id, "timeOffset"]
            .dropna()
            .unique()
        )
        if offsets.size == 0:
            raise ValueError(
                f"Ingen timeOffset funnet for city={city!r}, "
                f"element_id={element_id!r}"
            )

        pattern = re.compile(r"PT(\d+)H")
        parsed: list[tuple[int, str]] = []

        for off in offsets:
            match = pattern.fullmatch(off)
            if match:
                hours = int(match.group(1))
                parsed.append((hours, off))

        if not parsed:
            raise ValueError(
                "Fant ingen gyldige PT<n>H-offsets i data for "
                f"city={city!r}, element_id={element_id!r}. "
                f"Råverdier: {offsets!r}"
            )

        # Velg offset med minste antall timer
        _, min_offset = min(parsed, key=lambda x: x[0])
        return min_offset


__all__ = ["DataLoader"]
