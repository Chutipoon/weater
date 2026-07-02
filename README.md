# weater — testing the Adhammika cascade with free data

Can a 2,500-year-old Buddhist causal chain be examined with modern open data?
The **Adhammika Sutta** (`idea.txt`) claims that when leaders and society stop
behaving righteously, the **sun, moon, stars, days, months, seasons rotate
irregularly**, rain falls out of season, **crops ripen unevenly**, and people
become **short-lived, weak, and sick**.

This repo substitutes each link with a free public dataset and tests the
relationships. See [`docs/research_design.md`](docs/research_design.md) for the
full concept→data mapping, the five astronomical/temporal sub-nodes, hypotheses,
and (important) caveats.

## What it does

1. **Fetches** free data — World Bank (governance, crops, health, CO₂, GDP),
   NOAA ENSO (interannual irregularity), SILSO sunspots (best-effort).
2. **Builds** a country-year panel (217 countries, 1996–2022) with derived
   *irregularity* indices (`src/irregularity.py`).
3. **Analyses** the cascade: co-movement correlations, a downstream FE
   regression, the core ENSO×governance moderation, and a between-country
   model that addresses the fixed-effects washout caveat.
4. **Plots** the ENSO irregularity series, a co-movement heatmap, and the
   governance↔longevity scatter.

## Run it

```bash
pip install -r requirements.txt

python src/build_panel.py     # fetch + merge -> data/panel.csv (cached)
python src/analyze.py         # tables -> outputs/regression_report.txt
python src/plot.py            # figures -> outputs/*.png
```

Re-fetch from source with `--force`. Data is cached under `data/` so reruns are
offline.

## Precision precipitation via Google Earth Engine (the IV first-stage fix)

The causal IV needs country-level, ENSO-driven growing-season precipitation.
Capital-point Open-Meteo works but is rate-limited; CHIRPS via GEE is the
grid-bulk, no-rate-limit source. One-time setup (free, non-commercial):

```bash
pip install earthengine-api                 # (already installed)
# 1. Register (free): https://earthengine.google.com  -> note your Cloud project id
# 2. Authenticate (opens a browser; run via the `!` prefix in-session):
earthengine authenticate
# 3. Point the script at your project, then run:
#    PowerShell:  $env:GEE_PROJECT="your-project-id"
python src/fetch_precip_gee.py              # -> data/precip_country_gee.csv
python src/build_panel.py                   # panel auto-merges precipitation
python src/analyze_iv.py                    # re-runs the IV with the strong first stage
```

`build_panel.py` automatically prefers `precip_country_gee.csv` (GEE) over the
Open-Meteo proxy when present, and adds `precip_anom` (growing-season anomaly).

## Honest finding

The substitution works — proxies recover known reality (ENSO reproduces the
1997/98 and 2015/16 El Niños; governance correlates with longevity). But the
*causal* claims largely dissolve under controls: governance loses significance
once GDP is held constant, and the ENSO×governance buffering effect points the
predicted direction but is **not** statistically significant. The cascade is a
real pattern of co-movement driven by development, not a proven causal chain —
and definitely not literal celestial mechanics. Details in the research design.
