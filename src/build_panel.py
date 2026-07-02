"""Assemble the analysis panel.

Merges the World Bank country-year frame with the global-annual astro/temporal
series (by year), then derives the "irregularity" columns the cascade is about:
  - cereal_yield_irreg : within-country rolling instability of yields
                         ("crops ripen unevenly")
ENSO amplitude already encodes "seasons & years rotate irregularly" (node E).
Output: data/panel.csv (one row per country-year).
"""
from __future__ import annotations

import os
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))   # project root (for config)
sys.path.insert(0, _HERE)                     # src/ (for sibling modules)
import config
import fetch_astro_temporal
import fetch_climate_country
import fetch_worldbank
import irregularity as ir


def _load_precip() -> pd.DataFrame | None:
    """Load precipitation cache: prefer GEE CHIRPS grid, else Open-Meteo proxy."""
    gee = os.path.join(config.DATA_DIR, "precip_country_gee.csv")
    om = os.path.join(config.DATA_DIR, "precip_country.csv")
    for path, src in [(gee, "GEE CHIRPS grid"), (om, "Open-Meteo capital-point")]:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df.attrs["source"] = src
            return df
    return None


def build(force: bool = False) -> pd.DataFrame:
    wb = fetch_worldbank.fetch(force=force)
    astro = fetch_astro_temporal.fetch(force=force)
    climate = fetch_climate_country.fetch(force=force)   # node C: country DTR

    panel = wb.merge(astro, on="year", how="left")
    panel = panel.merge(climate, on=["iso3", "year"], how="left")

    # Precipitation (ENSO->crop channel): prefer GEE CHIRPS grid, else Open-Meteo
    # capital-point proxy. Either is optional; panel builds without it.
    precip = _load_precip()
    if precip is not None:
        panel = panel.merge(precip, on=["iso3", "year"], how="left")
        if "precip_wet3" in panel:
            panel["precip_anom"] = ir.panel_irregularity(panel, "precip_wet3", window=5)
        print(f"  merged precipitation from {precip.attrs.get('source')}: "
              f"{precip['iso3'].nunique()} countries")

    # "Crops ripen unevenly": instability of yield within each country.
    panel["cereal_yield_irreg"] = ir.panel_irregularity(
        panel, "cereal_yield", window=5)

    # Node C "irregularity": within-country instability of the day-night swing.
    panel["dtr_irreg"] = ir.panel_irregularity(panel, "dtr_mean", window=5)

    panel = panel.sort_values(["iso3", "year"]).reset_index(drop=True)
    panel.to_csv(config.PANEL_CSV, index=False)

    print(f"\nPanel: {panel.shape[0]} rows x {panel.shape[1]} cols -> {config.PANEL_CSV}")
    print(f"Countries: {panel.iso3.nunique()}  Years: {panel.year.min()}-{panel.year.max()}")
    nn = panel.notna().sum().sort_values()
    print("\nNon-null counts (sparsest first):")
    print(nn.to_string())
    return panel


if __name__ == "__main__":
    build(force="--force" in sys.argv)
