import os
import re
from functools import lru_cache
import pandas as pd

class DataLoader:
    #: Fast navne­mønster for filer – kan overstyres i sub‑klasser om nødvendig
    filename_template: str = "vaerdata_{city}.csv"

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    @lru_cache(maxsize=None)
    def _load_city(self, city: str) -> pd.DataFrame:
        path = os.path.join(self.data_dir, self.filename_template.format(city=city))
        if not os.path.exists(path):
            raise FileNotFoundError(f"Fant ikke datafil: {path}")

        df = pd.read_csv(path, low_memory=False)

        if "referenceTime" not in df.columns:
            raise KeyError(
                "Kolonnen 'referenceTime' mangler i "
                f"'{os.path.basename(path)}' – sjekk datagrunnlaget."
            )

        df["referenceTime"] = pd.to_datetime(
            df["referenceTime"], utc=True, errors="coerce"
        )
        return df

    def _get_min_offset(self, city: str, element_id: str) -> str:
        df = self._load_city(city)
        offsets = (
            df.loc[df["elementId"] == element_id, "timeOffset"]
            .dropna()
            .unique()
        )
        if len(offsets) == 0:
            raise ValueError(
                f"Ingen timeOffset funnet for city='{city}', element_id='{element_id}'"
            )
        pattern = re.compile(r"PT(\d+)H")
        hours: list[int] = []
        valid_offsets: list[str] = []

        for off in offsets:
            m = pattern.fullmatch(off)
            if m:
                hours.append(int(m.group(1)))
                valid_offsets.append(off)

        if not hours:
            raise ValueError(
                f"Fant ingen gyldige PT⟨n⟩H‑offsets i data for "
                f"{city=} {element_id=}. Råverdier: {offsets!r}"
            )

        lowest_idx = hours.index(min(hours))
        return valid_offsets[lowest_idx]

__all__ = ["DataLoader"]
