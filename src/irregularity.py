"""Irregularity-index builders.

The Adhammika cascade says cycles "rotate irregularly". We operationalise
"irregularity" as departure-from-normal and instability metrics. These are pure
functions over pandas Series/DataFrames so they can be unit-tested offline.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def anomaly(s: pd.Series) -> pd.Series:
    """Standardised anomaly: (x - mean) / std over the series' own history."""
    std = s.std(ddof=0)
    if std == 0 or np.isnan(std):
        return s * 0.0
    return (s - s.mean()) / std


def rolling_variability(s: pd.Series, window: int = 5) -> pd.Series:
    """Rolling standard deviation = how unstable the signal is over `window` years."""
    return s.rolling(window, min_periods=max(2, window // 2)).std()


def coef_of_variation(s: pd.Series) -> float:
    """Coefficient of variation (std/mean). Scale-free instability of a series."""
    m = s.mean()
    if m == 0 or np.isnan(m):
        return np.nan
    return float(s.std(ddof=0) / abs(m))


def detrended_variability(s: pd.Series) -> pd.Series:
    """Residual magnitude after removing a linear trend.

    Separates "irregularity" (scatter) from "steady change" (trend), so a
    smoothly shifting baseline is not mistaken for an erratic one.
    """
    s = s.astype(float)
    mask = s.notna()
    if mask.sum() < 3:
        return s * np.nan
    x = np.arange(len(s))[mask.values]
    y = s[mask].values
    coef = np.polyfit(x, y, 1)
    resid = y - np.polyval(coef, x)
    out = pd.Series(np.nan, index=s.index)
    out[mask] = np.abs(resid)
    return out


def panel_irregularity(df: pd.DataFrame, value_col: str,
                       entity_col: str = "iso3", time_col: str = "year",
                       window: int = 5) -> pd.Series:
    """Per-entity rolling variability of `value_col`, aligned to df's index.

    Used to turn level series (e.g. cereal_yield) into "ripens unevenly"
    instability series within each country.
    """
    return (df.sort_values([entity_col, time_col])
              .groupby(entity_col)[value_col]
              .transform(lambda s: rolling_variability(s, window)))
