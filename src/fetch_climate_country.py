"""Fetch country-level climate volatility (cascade node C: nights & days irregular).

Capital-point Diurnal Temperature Range (DTR = Tmax - Tmin) per country-year from
the Open-Meteo ERA5 archive (free, keyless). Coordinates come from the World Bank
country metadata (capital lat/long) -- no extra dependency.

This is the keystone for the Climate Risk Model: unlike global ENSO, DTR varies
across countries, giving (a) within-country exogenous climate shocks for causal
identification and (b) a per-country signal for the risk map.

Caveat: capital-point != country/agricultural average -- a stated v1 proxy.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

CACHE = os.path.join(config.DATA_DIR, "climate_country.csv")
WB_COUNTRY = "https://api.worldbank.org/v2/country?format=json&per_page=400"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
_HEADERS = {"User-Agent": "Mozilla/5.0 (weater research pipeline)"}


def _get_json(url: str, retries: int = 5):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            # Open-Meteo rate limit: back off hard and wait for the window to reset.
            time.sleep(60 if e.code == 429 else 3 * (attempt + 1))
        except Exception as e:  # noqa: BLE001 - transient/network errors
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def _capitals() -> list[tuple[str, float, float]]:
    data = _get_json(WB_COUNTRY)[1]
    out = []
    for c in data:
        if c["region"]["value"] == "Aggregates":
            continue
        if c.get("latitude") and c.get("longitude"):
            out.append((c["id"], float(c["latitude"]), float(c["longitude"])))
    return out


def _country_dtr(lat: float, lon: float) -> pd.DataFrame:
    url = (f"{ARCHIVE}?latitude={lat}&longitude={lon}"
           f"&start_date={config.YEAR_START}-01-01&end_date={config.YEAR_END}-12-31"
           f"&daily=temperature_2m_max,temperature_2m_min&timezone=UTC")
    d = _get_json(url)["daily"]
    df = pd.DataFrame({
        "date": pd.to_datetime(d["time"]),
        "tmax": d["temperature_2m_max"],
        "tmin": d["temperature_2m_min"],
    }).dropna()
    df["year"] = df["date"].dt.year
    df["dtr"] = df["tmax"] - df["tmin"]
    g = df.groupby("year")
    return pd.DataFrame({
        "dtr_mean": g["dtr"].mean(),            # avg day-night swing
        "dtr_std": g["dtr"].std(),              # within-year day-to-day instability
        "temp_mean": g[["tmax", "tmin"]].mean().mean(axis=1),
    }).reset_index()


def fetch(force: bool = False, resume: bool = False) -> pd.DataFrame:
    """Fetch country DTR.

    - default: return cache if present, else fetch everything.
    - resume=True: fetch only the countries missing from cache (re-run after a
      rate-limited pass to fill gaps).
    - force=True: re-fetch all countries.
    """
    cached = pd.read_csv(CACHE) if os.path.exists(CACHE) else pd.DataFrame()
    if os.path.exists(CACHE) and not force and not resume:
        return cached

    done = set(cached["iso3"]) if not cached.empty else set()
    caps = [c for c in _capitals() if force or c[0] not in done]
    print(f"Fetching DTR for {len(caps)} countries (resuming; {len(done)} cached)...")

    new_frames, ok, fail = [], 0, 0
    for i, (iso3, lat, lon) in enumerate(caps, 1):
        try:
            df = _country_dtr(lat, lon)
            df.insert(0, "iso3", iso3)
            new_frames.append(df)
            ok += 1
        except Exception as e:  # noqa: BLE001 - best-effort per country
            fail += 1
            print(f"  [warn] {iso3} failed ({e})")
        if i % 10 == 0:        # flush periodically so progress survives interruption
            _flush(cached, new_frames)
            print(f"  ...{i}/{len(caps)} (ok={ok}, fail={fail})")
        time.sleep(1.2)        # slower pacing to respect the free rate limit

    out = _flush(cached, new_frames)
    print(f"Saved {out['iso3'].nunique()} countries / {len(out)} rows to {CACHE}")
    return out


def _flush(cached: pd.DataFrame, new_frames: list[pd.DataFrame]) -> pd.DataFrame:
    parts = ([cached] if not cached.empty else []) + new_frames
    out = (pd.concat(parts, ignore_index=True)
             .drop_duplicates(["iso3", "year"]).sort_values(["iso3", "year"]))
    out.to_csv(CACHE, index=False)
    return out


if __name__ == "__main__":
    # Direct run resumes by default (fills gaps); --force re-fetches everything.
    df = fetch(force="--force" in sys.argv, resume="--force" not in sys.argv)
    print(df.shape, "->", df["iso3"].nunique(), "countries")
    print(df.head())
