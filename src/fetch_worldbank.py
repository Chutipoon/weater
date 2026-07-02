"""Fetch World Bank indicators into a tidy country-year frame.

Uses only the stdlib + pandas (the World Bank REST API is plain JSON, so the
`wbgapi` package is an avoidable dependency). Results are cached to data/ so
re-runs are offline and fast.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

API = "https://api.worldbank.org/v2"
CACHE = os.path.join(config.DATA_DIR, "worldbank.csv")


def _get_json(url: str, retries: int = 3):
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - network flakiness, retry
            last = e
            time.sleep(2 * (attempt + 1))
    raise last


def _real_countries() -> set[str]:
    """ISO3 codes of actual countries (excludes regional/income aggregates)."""
    data = _get_json(f"{API}/country?format=json&per_page=400")[1]
    return {c["id"] for c in data if c["region"]["value"] != "Aggregates"}


def _fetch_indicator(code: str) -> pd.DataFrame:
    date = f"{config.YEAR_START}:{config.YEAR_END}"
    url = f"{API}/country/all/indicator/{code}?format=json&date={date}&per_page=20000"
    payload = _get_json(url)
    if not isinstance(payload, list) or len(payload) < 2:
        msg = payload[0].get("message") if isinstance(payload, list) and payload else payload
        print(f"  [warn] {code}: API returned no data ({msg})")
        return pd.DataFrame()
    rows = payload[1] or []
    recs = [
        {"iso3": r["countryiso3code"], "year": int(r["date"]), code: r["value"]}
        for r in rows
        if r["value"] is not None and r["countryiso3code"]
    ]
    return pd.DataFrame(recs)


def fetch(force: bool = False) -> pd.DataFrame:
    """Return wide country-year frame for all config.WB_INDICATORS (cached)."""
    if os.path.exists(CACHE) and not force:
        return pd.read_csv(CACHE)

    countries = _real_countries()
    merged: pd.DataFrame | None = None
    for code in config.WB_INDICATORS:
        df = _fetch_indicator(code)
        if df.empty:
            print(f"  [warn] no data returned for {code}")
            continue
        df = df[df["iso3"].isin(countries)]
        merged = df if merged is None else merged.merge(df, on=["iso3", "year"], how="outer")
        print(f"  {code:>18} -> {config.WB_INDICATORS[code]:<20} rows={len(df)}")

    merged = merged.rename(columns=config.WB_INDICATORS).sort_values(["iso3", "year"])
    merged.to_csv(CACHE, index=False)
    print(f"Saved {len(merged)} country-year rows to {CACHE}")
    return merged


if __name__ == "__main__":
    df = fetch(force="--force" in sys.argv)
    print(df.shape)
    print(df.head())
