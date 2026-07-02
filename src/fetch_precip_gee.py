"""Precision precipitation: country-level CHIRPS via Google Earth Engine (grid bulk).

This is the upgrade over the capital-point Open-Meteo proxy: true zonal-mean
growing-season precipitation per country from the CHIRPS daily grid, with no rate
limits. Requires one-time GEE setup (see README / the auth steps printed below).

Pipeline:
  CHIRPS daily (UCSB-CHG/CHIRPS/DAILY) -> monthly sums -> reduceRegions over
  country polygons (FAO GAUL level 0) -> monthly precip per country-year.
  Python then derives annual total + wettest-quarter ("growing-season") and maps
  GAUL country names to ISO3 (crosswalk from World Bank metadata; unmatched names
  are reported for a quick manual fix).

Run:
  pip install earthengine-api
  earthengine authenticate            # opens a browser (do this once)
  set GEE_PROJECT=your-cloud-project  # PowerShell: $env:GEE_PROJECT="..."
  python src/fetch_precip_gee.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import pandas as pd

CALL_TIMEOUT_S = 120  # some GEE requests hang past the interactive compute budget
                     # instead of erroring; treat a stuck call as a failure so
                     # _reduce_recursive can split/skip instead of blocking forever.
                     # A fresh one-shot executor per call means a thread stuck on
                     # a hung request is simply abandoned (not reused / blocking).


def _get_info_with_timeout(fc, timeout_s=CALL_TIMEOUT_S):
    # NOTE: not a context manager -- shutdown(wait=True) on exit would block on
    # an abandoned/hung thread, defeating the timeout.
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(fc.getInfo)
    try:
        return future.result(timeout=timeout_s)
    except FutureTimeoutError:
        raise TimeoutError(f"getInfo() exceeded {timeout_s}s") from None
    finally:
        pool.shutdown(wait=False)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)
import config

CACHE = os.path.join(config.DATA_DIR, "precip_country_gee.csv")
RAW_CHECKPOINT = os.path.join(config.DATA_DIR, "precip_country_gee_raw.jsonl")
GAUL = "FAO/GAUL/2015/level0"          # country polygons; property: ADM0_NAME
CHIRPS = "UCSB-CHG/CHIRPS/DAILY"       # daily precip grid (~5 km), mm
CHUNK_SIZE = 25  # a single reduceRegions() over all ~292 GAUL features hangs past
                 # GEE's interactive compute budget; small batches return in ~seconds.

# GAUL splits a handful of countries into several disconnected polygon features
# (mainland + exclaves/remote islands/territories under the same ADM0_NAME).
# Confirmed via a one-off area/name-count query: Canada=10 features, USA=5,
# Australia=3, West Bank=2 -- everything else is a single feature. Batched
# reduceRegions() reliably hangs or hits GEE's memory limit on these even
# alone (no bestEffort option there); routing them to a dedicated per-country
# reduceRegion(bestEffort=True) path (merging their fragments into one
# geometry first) avoids wasting time on doomed batch/split/retry cascades.
MULTI_FRAGMENT_COUNTRIES = ["Canada", "United States of America", "Australia",
                            "West Bank"]

# GAUL names that _name_to_iso3's normalised-exact-match misses because the
# World Bank uses a different official name/spelling for the same country
# (confirmed one-to-one real-country matches only -- disputed territories,
# dependent territories, and sub-national regions like "Jammu and Kashmir" or
# "Puerto Rico"'s French/Dutch/UK equivalents are deliberately left unmapped:
# WB doesn't track them separately, so guessing would risk silently merging
# two different GAUL polygons into one country-year row downstream. Gaza
# Strip is a similar case: WB's "West Bank and Gaza" is a single ISO3 (PSE)
# already covered by "West Bank" above via MULTI_FRAGMENT_COUNTRIES, so
# aliasing "Gaza Strip" too would create a duplicate PSE row per year.
GAUL_ISO3_OVERRIDES = {
    "United States of America": "USA",
    "Bahamas": "BHS",
    "Cape Verde": "CPV",
    "Congo": "COG",
    "Czech Republic": "CZE",
    "Côte d'Ivoire": "CIV",
    "Dem People's Rep of Korea": "PRK",
    "Democratic Republic of the Congo": "COD",
    "Egypt": "EGY",
    "Gambia": "GMB",
    "Hong Kong": "HKG",
    "Iran  (Islamic Republic of)": "IRN",
    "Kyrgyzstan": "KGZ",
    "Lao People's Democratic Republic": "LAO",
    "Macau": "MAC",
    "Micronesia (Federated States of)": "FSM",
    "Moldova, Republic of": "MDA",
    "Puerto Rico": "PRI",
    "Republic of Korea": "KOR",
    "Saint Kitts and Nevis": "KNA",
    "Saint Lucia": "LCA",
    "Saint Vincent and the Grenadines": "VCT",
    "Slovakia": "SVK",
    "Somalia": "SOM",
    "Swaziland": "SWZ",
    "The former Yugoslav Republic of Macedonia": "MKD",
    "Turkey": "TUR",
    "U.K. of Great Britain and Northern Ireland": "GBR",
    "United Republic of Tanzania": "TZA",
    "United States Virgin Islands": "VIR",
    "Venezuela": "VEN",
    "West Bank": "PSE",
    "Yemen": "YEM",
}


def _init_ee():
    try:
        import ee
    except ImportError:
        sys.exit("earthengine-api not installed. Run: pip install earthengine-api")
    project = os.environ.get("GEE_PROJECT")
    if not project:
        sys.exit("Set GEE_PROJECT to your Google Cloud project id "
                 "(PowerShell: $env:GEE_PROJECT=\"my-project\").")
    try:
        ee.Initialize(project=project)
    except Exception:
        sys.exit("GEE not authenticated. Run: earthengine authenticate")
    return ee


def _name_to_iso3() -> dict[str, str]:
    """Normalised country-name -> ISO3, from World Bank metadata (no auth)."""
    url = "https://api.worldbank.org/v2/country?format=json&per_page=400"
    data = json.loads(urllib.request.urlopen(url, timeout=60).read())[1]
    norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
    return {norm(c["name"]): c["id"] for c in data
            if c["region"]["value"] != "Aggregates"}


def _load_checkpoint(raw_checkpoint: str) -> tuple[list[dict], set[int]]:
    """Only years marked complete (all chunks succeeded, no skips) are trusted;
    rows from a year that was interrupted mid-way are discarded so that year
    gets refetched cleanly on resume instead of silently missing countries."""
    if not os.path.exists(raw_checkpoint):
        return [], set()
    lines = [json.loads(line) for line in open(raw_checkpoint, encoding="utf-8")]
    done_years = {r["year_complete"] for r in lines if "year_complete" in r}
    records = [r for r in lines if "adm0_name" in r and r["year"] in done_years]
    print(f"[resume] {len(records)} rows cached for completed years "
          f"{sorted(done_years)}", flush=True)
    return records, done_years


def _reduce_recursive(ee, img, country_list, start, end, scale, tile_scale):
    """reduceRegions over country_list[start:end]; halves the batch and retries
    on failure (e.g. 'User memory limit exceeded' from one oversized/complex
    country) until it isolates the problem to a single country."""
    collection = ee.FeatureCollection(country_list.slice(start, end))
    last_err = None
    for _attempt in range(2):
        try:
            fc = img.reduceRegions(collection=collection, reducer=ee.Reducer.mean(),
                                   scale=scale, tileScale=tile_scale)
            return _get_info_with_timeout(fc)["features"]
        except Exception as e:  # noqa: BLE001 - transient server/timeouts/memory
            last_err = e
    if end - start <= 1:
        # Batched reduceRegions() has no bestEffort option and genuinely can't
        # handle some complex geometries (e.g. Canada's GAUL GeometryCollection)
        # even alone. Singular reduceRegion(bestEffort=True) is more forgiving
        # (confirmed: Canada full-year succeeds in ~60s this way) -- try it as
        # a last resort before giving up on this country.
        try:
            feature = ee.Feature(country_list.get(start))
            props = ee.Dictionary(img.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=feature.geometry(), scale=scale,
                tileScale=16, bestEffort=True, maxPixels=1e9,
            )).set("ADM0_NAME", feature.get("ADM0_NAME"))
            return [{"properties": _get_info_with_timeout(props, timeout_s=180)}]
        except Exception as e2:
            last_err = e2
        print(f"    [warn] country index {start} permanently failed: "
              f"{str(last_err)[:100]}", flush=True)
        return []
    mid = start + (end - start) // 2
    print(f"    [split] indices {start}-{end} failed twice ({str(last_err)[:60]}), "
          f"splitting", flush=True)
    return (_reduce_recursive(ee, img, country_list, start, mid, scale, tile_scale)
            + _reduce_recursive(ee, img, country_list, mid, end, scale, tile_scale))


def _reduce_multi_fragment(ee, img, all_countries, name, scale):
    """Merge a country's disconnected GAUL fragments and reduce with the more
    forgiving singular bestEffort path. Simplifying each fragment BEFORE
    merging is essential: unioning full-precision fragments directly (e.g.
    Canada's 10 pieces) produces a geometry with millions of edges, over GEE's
    2,000,000-edge hard limit, and that failure happens during geometry
    construction itself -- simplifying after the failed merge is too late."""
    fragments = all_countries.filter(ee.Filter.eq("ADM0_NAME", name)).map(
        lambda f: f.setGeometry(f.geometry().simplify(5000)))
    geom = fragments.geometry()
    try:
        props = ee.Dictionary(img.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=scale,
            tileScale=16, bestEffort=True, maxPixels=1e9,
        )).set("ADM0_NAME", name)
        return {"properties": _get_info_with_timeout(props, timeout_s=180)}
    except Exception as e:
        print(f"    [warn] {name} permanently failed: {str(e)[:100]}", flush=True)
        return None


def fetch(years=None, raw_checkpoint=None, cache=None) -> pd.DataFrame:
    years = years if years is not None else config.YEARS
    raw_checkpoint = raw_checkpoint or RAW_CHECKPOINT
    cache = cache or CACHE
    ee = _init_ee()
    # FAO GAUL has at least one invalid polygon (bad ring -> reprojection errors
    # inside reduceRegions); buffer(0, 1) repairs it with a 1m error margin.
    all_countries = ee.FeatureCollection(GAUL).map(
        lambda f: f.setGeometry(f.geometry().buffer(0, 1)))
    countries = all_countries.filter(
        ee.Filter.inList("ADM0_NAME", MULTI_FRAGMENT_COUNTRIES).Not())
    n_countries = countries.size().getInfo()
    country_list = countries.toList(n_countries)

    # Native CHIRPS (~5566m) is far finer than needed for country-level annual/
    # growing-season aggregates, and is prohibitively expensive for large/complex
    # countries (Canada's GAUL geometry is a GeometryCollection; a single-month,
    # single-country reduceRegion() for it alone took 25-67s even bestEffort).
    # ~22km (4x native) keeps ample precision for country means while cutting
    # per-country compute roughly 16x (pixel count scales with scale^2).
    scale = 22264
    records, done_years = _load_checkpoint(raw_checkpoint)
    ckpt = open(raw_checkpoint, "a", encoding="utf-8")
    t_start = time.monotonic()
    n_chunks = (n_countries + CHUNK_SIZE - 1) // CHUNK_SIZE
    for i, year in enumerate(years):
        if year in done_years:
            continue
        print(f"[{i + 1}/{len(years)}] {year}: {n_chunks} chunks of "
              f"{CHUNK_SIZE} countries...", flush=True)
        t_year = time.monotonic()
        # 12-band image: monthly precipitation sums for this year. Multi-band keeps
        # band names (m01..m12) as output properties (a single band would be 'mean').
        months = []
        for m in range(1, 13):
            start = ee.Date.fromYMD(year, m, 1)
            monthly = (ee.ImageCollection(CHIRPS)
                       .filterDate(start, start.advance(1, "month"))
                       .sum().rename(f"m{m:02d}"))
            months.append(monthly)
        img = ee.Image.cat(months)

        year_rows = 0
        missing_count = 0
        for c in range(n_chunks):
            start, end = c * CHUNK_SIZE, min((c + 1) * CHUNK_SIZE, n_countries)
            t_chunk = time.monotonic()
            feats = _reduce_recursive(ee, img, country_list, start, end, scale,
                                       tile_scale=8)
            missing_count += (end - start) - len(feats)
            for feat in feats:
                p = feat["properties"]
                name = p.get("ADM0_NAME")
                vals = [p.get(f"m{m:02d}") for m in range(1, 13)]
                if name and all(v is not None for v in vals):
                    row = {"adm0_name": name, "year": year,
                           **{f"m{m:02d}": vals[m - 1] for m in range(1, 13)}}
                    records.append(row)
                    ckpt.write(json.dumps(row) + "\n")
            year_rows += len(feats)
            ckpt.flush()
            print(f"    chunk {c + 1}/{n_chunks}: {len(feats)} countries "
                  f"({time.monotonic() - t_chunk:.1f}s)", flush=True)

        for name in MULTI_FRAGMENT_COUNTRIES:
            t_mf = time.monotonic()
            feat = _reduce_multi_fragment(ee, img, all_countries, name, scale)
            if feat is None:
                missing_count += 1
                continue
            p = feat["properties"]
            vals = [p.get(f"m{m:02d}") for m in range(1, 13)]
            if all(v is not None for v in vals):
                row = {"adm0_name": name, "year": year,
                       **{f"m{m:02d}": vals[m - 1] for m in range(1, 13)}}
                records.append(row)
                ckpt.write(json.dumps(row) + "\n")
                ckpt.flush()
                year_rows += 1
            print(f"    {name} (multi-fragment): "
                  f"{time.monotonic() - t_mf:.1f}s", flush=True)

        # "complete" means every chunk was attempted (incl. exhausting the
        # split/retry/timeout fallbacks), not zero gaps -- a permanently-bad
        # geometry fails identically every year, so gating completion on zero
        # gaps would make that year (and thus all resumes) never converge.
        ckpt.write(json.dumps({"year_complete": year}) + "\n")
        ckpt.flush()
        dt = time.monotonic() - t_year
        elapsed = time.monotonic() - t_start
        print(f"  {year}: {year_rows} countries total "
              f"({dt:.1f}s, elapsed {elapsed / 60:.1f}m)"
              f"{f' [{missing_count} permanently missing]' if missing_count else ''}",
              flush=True)
    ckpt.close()

    df = pd.DataFrame(records)
    mcols = [f"m{m:02d}" for m in range(1, 13)]
    df["precip_annual"] = df[mcols].sum(axis=1)
    df["precip_wet3"] = df[mcols].apply(
        lambda r: max(r.values[i:i + 3].sum() for i in range(10)), axis=1)

    # map GAUL names -> ISO3
    x = _name_to_iso3()
    norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
    df["iso3"] = df["adm0_name"].map(
        lambda n: GAUL_ISO3_OVERRIDES.get(n) or x.get(norm(n)))
    miss = sorted(df.loc[df["iso3"].isna(), "adm0_name"].unique())
    if miss:
        print(f"\n[!] {len(miss)} GAUL names had no ISO3 match (fix manually if "
              f"needed): {miss[:20]}{'...' if len(miss) > 20 else ''}", flush=True)
    out = df.dropna(subset=["iso3"])[["iso3", "year", "precip_annual", "precip_wet3"]]
    out.to_csv(cache, index=False)
    print(f"\nSaved {out['iso3'].nunique()} countries / {len(out)} rows to {cache}",
          flush=True)
    return out


if __name__ == "__main__":
    # Optional light-parallelism split: `python fetch_precip_gee.py 2009 2015 a`
    # runs only years 2009-2015, checkpointing to precip_country_gee_raw_a.jsonl
    # (and precip_country_gee_a.csv) instead of the shared default files, so
    # a second process can run a different year range concurrently without
    # write conflicts. No args = original full-range, default-file behaviour.
    arg_start = int(sys.argv[1]) if len(sys.argv) > 1 else config.YEAR_START
    arg_end = int(sys.argv[2]) if len(sys.argv) > 2 else config.YEAR_END
    arg_suffix = sys.argv[3] if len(sys.argv) > 3 else ""
    arg_years = list(range(arg_start, arg_end + 1))
    suffix = f"_{arg_suffix}" if arg_suffix else ""
    fetch(
        years=arg_years,
        raw_checkpoint=os.path.join(config.DATA_DIR, f"precip_country_gee_raw{suffix}.jsonl"),
        cache=os.path.join(config.DATA_DIR, f"precip_country_gee{suffix}.csv"),
    )
