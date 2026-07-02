"""No-auth country precipitation (the ENSO->crop channel), capital-point proxy.

Open-Meteo ERA5 daily precipitation per capital -> annual total and wettest-quarter
("growing-season" proxy). Resumable + rate-limit aware (reuses the helpers in
fetch_climate_country). Independent cache so it never clashes with the DTR fetch.

This is the fast no-auth path to strengthen the IV first stage; the GEE CHIRPS
grid pull (fetch_precip_gee.py) is the precision upgrade.

Caveat: capital-point precip != agricultural-region/growing-season precip -- a
stated v1 proxy, superseded by the grid version once GEE auth is set up.
"""
from __future__ import annotations

import os
import sys
import time

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)
import config
from fetch_climate_country import ARCHIVE, _capitals, _get_json  # reuse helpers

CACHE = os.path.join(config.DATA_DIR, "precip_country.csv")


def _country_precip(lat: float, lon: float) -> pd.DataFrame:
    url = (f"{ARCHIVE}?latitude={lat}&longitude={lon}"
           f"&start_date={config.YEAR_START}-01-01&end_date={config.YEAR_END}-12-31"
           f"&daily=precipitation_sum&timezone=UTC")
    d = _get_json(url)["daily"]
    df = pd.DataFrame({"date": pd.to_datetime(d["time"]),
                       "p": d["precipitation_sum"]}).dropna()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby(["year", "month"])["p"].sum().reset_index()
    rows = []
    for yr, g in monthly.groupby("year"):
        vals = g["p"].values
        # wettest 3 consecutive months = growing-season precipitation proxy
        wet3 = max((vals[i:i + 3].sum() for i in range(max(1, len(vals) - 2))),
                   default=float("nan"))
        rows.append({"year": int(yr), "precip_annual": float(vals.sum()),
                     "precip_wet3": float(wet3)})
    return pd.DataFrame(rows)


def fetch(force: bool = False, resume: bool = False) -> pd.DataFrame:
    cached = pd.read_csv(CACHE) if os.path.exists(CACHE) else pd.DataFrame()
    if os.path.exists(CACHE) and not force and not resume:
        return cached
    done = set(cached["iso3"]) if not cached.empty else set()
    caps = [c for c in _capitals() if force or c[0] not in done]
    print(f"Fetching capital-point precipitation for {len(caps)} countries "
          f"(resuming; {len(done)} cached)...")

    new, ok, fail = [], 0, 0
    for i, (iso3, lat, lon) in enumerate(caps, 1):
        try:
            df = _country_precip(lat, lon); df.insert(0, "iso3", iso3)
            new.append(df); ok += 1
        except Exception as e:  # noqa: BLE001 - best-effort per country
            fail += 1; print(f"  [warn] {iso3} failed ({e})")
        if i % 10 == 0:
            _flush(cached, new); print(f"  ...{i}/{len(caps)} (ok={ok}, fail={fail})")
        time.sleep(1.2)
    out = _flush(cached, new)
    print(f"Saved {out['iso3'].nunique()} countries / {len(out)} rows to {CACHE}")
    return out


def _flush(cached: pd.DataFrame, new: list[pd.DataFrame]) -> pd.DataFrame:
    parts = ([cached] if not cached.empty else []) + new
    out = (pd.concat(parts, ignore_index=True)
             .drop_duplicates(["iso3", "year"]).sort_values(["iso3", "year"]))
    out.to_csv(CACHE, index=False)
    return out


if __name__ == "__main__":
    df = fetch(force="--force" in sys.argv, resume="--force" not in sys.argv)
    print(df.shape, "->", df["iso3"].nunique(), "countries")
