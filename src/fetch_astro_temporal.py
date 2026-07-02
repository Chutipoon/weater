"""Fetch the astronomical / temporal "irregularity" signals (nodes A & E).

These cycles are global, so the outputs are GLOBAL-ANNUAL series merged onto the
country panel by year (not country-specific columns). Each source is best-effort:
if one endpoint is unreachable the others still produce a usable file.

Node E (seasons & years rotate irregularly):  ENSO Oceanic Nino Index -> annual
    amplitude/instability of the master interannual driver.
Node A (sun & moon rotate irregularly):        SILSO sunspot number -> solar
    activity level and its anomaly (the sun *is* variable; humans aside).
"""
from __future__ import annotations

import io
import os
import sys
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

CACHE = os.path.join(config.DATA_DIR, "astro_temporal.csv")
_HEADERS = {"User-Agent": "Mozilla/5.0 (weater research pipeline)"}


def _get_text(url: str) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")


def fetch_enso() -> pd.DataFrame:
    """Annual ENSO irregularity from the monthly ONI ascii table.

    Columns: enso_amplitude (mean |anomaly| in the year, how far from neutral)
             enso_max_abs   (peak |anomaly|, strength of the year's extreme).
    """
    txt = _get_text(config.ENSO_ONI_URL)
    rows = []
    for line in txt.splitlines()[1:]:          # skip header
        parts = line.split()
        if len(parts) == 4 and parts[1].isdigit():
            rows.append((int(parts[1]), float(parts[3])))   # year, anomaly
    m = pd.DataFrame(rows, columns=["year", "anom"])
    g = m.groupby("year")["anom"]
    out = pd.DataFrame({
        "enso_amplitude": g.apply(lambda s: s.abs().mean()),
        "enso_max_abs": g.apply(lambda s: s.abs().max()),
    }).reset_index()
    return out


def fetch_sunspots() -> pd.DataFrame:
    """Annual mean sunspot number + standardised anomaly (SILSO V2.0)."""
    txt = _get_text(config.SUNSPOT_URL)
    df = pd.read_csv(io.StringIO(txt), sep=";", header=None,
                     usecols=[0, 1], names=["year_frac", "sunspot_number"])
    df["year"] = df["year_frac"].astype(float).astype(int)
    df = df[df["sunspot_number"] >= 0]          # -1 = missing
    mu, sd = df["sunspot_number"].mean(), df["sunspot_number"].std(ddof=0)
    df["sunspot_anomaly"] = (df["sunspot_number"] - mu) / sd
    return df[["year", "sunspot_number", "sunspot_anomaly"]]


def fetch(force: bool = False) -> pd.DataFrame:
    if os.path.exists(CACHE) and not force:
        return pd.read_csv(CACHE)

    base = pd.DataFrame({"year": config.YEARS})
    for name, fn in [("ENSO", fetch_enso), ("sunspots", fetch_sunspots)]:
        try:
            df = fn()
            base = base.merge(df, on="year", how="left")
            print(f"  {name:>9}: merged {df.shape[1]-1} cols, {len(df)} years")
        except Exception as e:  # noqa: BLE001 - best-effort source
            print(f"  [warn] {name} source unavailable, skipping ({e})")

    base.to_csv(CACHE, index=False)
    print(f"Saved global-annual astro/temporal series to {CACHE}")
    return base


if __name__ == "__main__":
    df = fetch(force="--force" in sys.argv)
    print(df.tail(8).to_string(index=False))
