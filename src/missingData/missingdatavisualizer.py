"""
missing_data_visualizer.py

Standalone module with MissingDataVisualizer class for creating summary bar plots,
heatmaps, and missing-data timelines.

Dependencies:
    pandas, matplotlib, missingno
"""

import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import missingno as msno


def _validate_csv_path(path: str) -> None:
    """
    Sjekk at CSV-filen finnes.

    Hever:
        FileNotFoundError: Hvis filen ikke finnes.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Missing-data CSV not found: {path}")


class MissingDataVisualizer:
    """
    Visualiserer manglende data fra en CSV-fil.

    Metoder:
        get_summary: Returnerer DataFrame med antall manglende per by/parameter.
        plot_summary_bar: Søyleplott av manglende antall.
        prepare_city_wide: Bred DataFrame med indikatorer.
        plot_heatmap: Korrelasjonsvarmekart for én by.
        get_timewide: Bred DataFrame over tid for råverdier.
        plot_missing_timeline: Tidslinje av manglende perioder.
    """

    def __init__(self, missing_csv_path: str) -> None:
        """
        Initialiser visualisator ved å laste inn CSV.

        Parametre:
            missing_csv_path (str): Sti til CSV med manglende data.
        """
        _validate_csv_path(missing_csv_path)
        self.df_missing = pd.read_csv(missing_csv_path)
        self.df_missing["date"] = pd.to_datetime(
            self.df_missing["date"], errors="coerce"
        )

    def get_summary(self) -> pd.DataFrame:
        """
        Beregn antall manglende pr by og parameter.

        Returnerer:
            pd.DataFrame: Kolonner ['city', 'elementId', 'num_missing'].
        """
        df = self.df_missing.copy()
        df["missing"] = None
        df.loc[df["oslo_value"].isna(), "missing"] = "Oslo"
        df.loc[df["tromso_value"].isna(), "missing"] = "Tromsø"

        summary = (
            df[df["missing"].notna()]
            .groupby(["missing", "elementId"], as_index=False)
            .size()
            .rename(columns={"missing": "city", "size": "num_missing"})
            .sort_values(["city", "num_missing"], ascending=[True, False])
        )
        return summary

    def plot_summary_bar(self, figsize: tuple[int, int] = (12, 6)) -> None:
        """
        Vis søyleplott av antall manglende pr parameter og by.
        """
        summary = self.get_summary()
        pivot = (
            summary.pivot(index="elementId", columns="city", values="num_missing")
            .fillna(0)
        )
        ax = pivot.plot.bar(figsize=figsize)
        ax.set_title("Manglende målinger per by og måletype")
        ax.set_xlabel("Måletype (elementId)")
        ax.set_ylabel("Antall manglende rader")
        ax.tick_params(axis="x", rotation=45)
        ax.legend(title="By")
        plt.tight_layout()
        plt.show()

    def prepare_city_wide(self, city_name: str) -> pd.DataFrame:
        """
        Lag bred DataFrame med indikatorer for en by.

        Parametre:
            city_name (str): "Oslo" eller "Tromsø".

        Returnerer:
            pd.DataFrame: Indikator (1) for manglende.
        """
        df = self.df_missing.copy()
        df["missing"] = None
        df.loc[df["oslo_value"].isna(), "missing"] = "Oslo"
        df.loc[df["tromso_value"].isna(), "missing"] = "Tromsø"
        df_city = df[df["missing"] == city_name].copy()
        df_city["indicator"] = 1.0

        all_elems = list(self.df_missing["elementId"].unique())
        wide = (
            df_city.pivot_table(
                index=["date", "timeOffset"],
                columns="elementId",
                values="indicator",
                aggfunc="first",
            )
            .reindex(columns=all_elems, fill_value=0)
        )
        return wide

    def plot_heatmap(
        self,
        city_name: str,
        figsize: tuple[int, int] = (6, 5),
        fontsize: int = 10,
    ) -> None:
        """
        Vis korrelasjonsvarmekart for manglende data i en by.

        Parametre:
            city_name (str): "Oslo" eller "Tromsø".
            figsize (tuple[int, int]): Figurstørrelse.
            fontsize (int): Aksens skriftstørrelse.
        """
        wide = self.prepare_city_wide(city_name)
        try:
            fig, ax = plt.subplots(figsize=figsize)
            msno.heatmap(
                wide,
                ax=ax,
                fontsize=fontsize
            )
            ax.set_title(
                f"Korrelasjonsvarmekart for manglende data – {city_name}"
            )
        except ValueError:
            corr = wide.isnull().corr()
        plt.tight_layout()
        plt.show()

    def get_timewide(
        self,
        city_name: str,
        param_order: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Lag bred DataFrame over tid med råverdier for en by.

        Parametre:
            city_name (str): "Oslo" eller "Tromsø".
            param_order (list[str] | None): Kolonne-rekkefølge.

        Returnerer:
            pd.DataFrame: Bred format med dato-indeks.
        """
        slug = (
            city_name.lower().replace("ø", "o").replace("æ", "ae").replace("å", "a")
        )
        col = f"{slug}_value"
        wide = (
            self.df_missing.copy()
            .set_index(["date", "timeOffset"])[col]
            .unstack(level=-1)
        )
        if param_order:
            cols = [p for p in param_order if p in wide.columns]
            wide = wide[cols]
        return wide

    def plot_missing_timeline(
        self,
        city_name: str,
        figsize: tuple[int, int] = (12, 5),
        line_width: int = 6,
    ) -> None:
        """
        Plott tidslinje av manglende-perioder for en by.
        """
        city_map = {"Oslo": "oslo_value", "Tromsø": "tromso_value"}
        if city_name not in city_map:
            raise ValueError(
                f"Støtter kun 'Oslo' og 'Tromsø', fikk '{city_name}'"
            )
        key = city_map[city_name]

        df_wide = (
            self.df_missing.pivot(
                index=["date", "timeOffset"],
                columns="elementId",
                values=key,
            )
            .reset_index(level="timeOffset", drop=True)
            .sort_index()
        )

        first, last = df_wide.index.min(), df_wide.index.max()
        years = pd.date_range(
            f"{first.year}-01-01", f"{last.year}-01-01", freq="YS"
        )

        fig, ax = plt.subplots(figsize=figsize)
        color = "tab:blue" if city_name == "Oslo" else "tab:orange"

        for i, param in enumerate(df_wide.columns):
            mask = df_wide[param].isna()
            if not mask.any():
                continue
            dates = df_wide.index[mask].sort_values()
            start = prev = dates[0]
            for d in dates[1:]:
                if (d - prev).days > 1:
                    ax.hlines(i, start, prev, color=color, linewidth=line_width)
                    start = d
                prev = d
            ax.hlines(i, start, prev, color=color, linewidth=line_width)

        for yr in years:
            ax.axvline(yr, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)

        ticks = [years[0]] + list(years[1::2])
        ax.set_xticks(ticks)
        ax.set_xticklabels([t.year for t in ticks], rotation=45)
        ax.set_yticks(range(len(df_wide.columns)))
        ax.set_yticklabels(df_wide.columns)
        ax.invert_yaxis()
        ax.set_title(f"Tidsmønstre i manglende data – {city_name}")
        ax.set_xlabel("År")
        ax.set_ylabel("Måletype")

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Visualize missing data from CSV"
    )
    parser.add_argument("csv", help="Path to missing-data CSV")
    parser.add_argument(
        "--city", nargs='+', default=None,
        help="City name(s) to plot heatmap/timeline for"
    )
    parser.add_argument(
        "--order", nargs='+', default=None,
        help="Custom parameter order for timeline"
    )
    args = parser.parse_args()

    viz = MissingDataVisualizer(args.csv)
    viz.plot_summary_bar()
    if args.city:
        for city in args.city:
            viz.plot_heatmap(city)
            viz.plot_missing_timeline(city, param_order=args.order)
