# Research design — substituting the Adhammika cascade with free data

## 1. The claim being tested

The Adhammika Sutta (`idea.txt`) states a top-down causal cascade:

> unrighteous **rulers → officials → householders → townsfolk →
> sun & moon rotate irregularly → constellations & stars rotate irregularly →
> nights & days rotate irregularly → months & fortnights rotate irregularly →
> seasons & years rotate irregularly → erratic winds → unseasonal rain →
> crops ripen unevenly → people short-lived, weak, diseased.**

**Research question:** can each abstract link be substituted with free public
data so the behavioural relationships can be examined empirically?

**Reframing (essential).** Human behaviour does not bend orbits — celestial
mechanics are fixed. So we do **not** test "bad governance slows the Earth."
Each line names a *natural cycle whose regularity people depend on*; for each we
measure how **regular vs. disrupted** the observable signal is. "Rotate
irregularly" is operationalised as **anomaly / variance / instability**, not
orbital motion. Read this way the astronomical chain becomes the
**anthropogenic disruption pathway**: collective behaviour → emissions / aerosols
/ land-use → measurable irregularity in solar signal, atmospheric transparency,
day-night balance, monthly & seasonal timing, interannual variability → crop
instability → health.

## 2. The five astronomical / temporal sub-nodes

For each: the literal claim, the measurable reinterpretation, and free data.
Nodes implemented in this repo are marked **[built]**; others are documented
extensions.

### A. "The sun and moon rotate irregularly"
- *Literal:* orbital motion — invariant (NASA JPL Horizons; a constant).
- *Measurable:* the **received** solar signal and the length of the day itself.
  - Surface solar radiation ("global dimming/brightening"): **NASA POWER**, CERES.
  - Solar activity (the sun *is* variable): **SILSO sunspot number** **[built, best-effort]**.
  - Length-of-Day excess (Earth's spin literally fluctuates): **IERS EOP**.
    *Real irregularity but not human-caused — the honest control.*
- *Irregularity metric:* irradiance anomaly/variance; sunspot anomaly; LOD variance.

### B. "The constellations and stars rotate irregularly"
- *Literal:* stellar positions — invariant.
- *Measurable:* whether stars can be **seen** (transparency + sky brightness).
  - Aerosol Optical Depth (sky turbidity): **MODIS AOD** (NASA Giovanni).
  - Light pollution / artificial sky brightness: **VIIRS** Day/Night Band, DMSP-OLS.
- *Note:* the nakṣatra were agricultural calendar markers; when sky/season signals
  drift, traditional timing fails → links forward to node E.

### C. "Nights and days rotate irregularly"
- *Literal:* photoperiod — deterministic by latitude (a control).
- *Measurable:* the day-night **balance** that has measurably shifted.
  - **Diurnal Temperature Range** (Tmax−Tmin), globally narrowing: **CRU TS**,
    Berkeley Earth, GHCN-Daily.
  - Cloud cover: ISCCP, MODIS cloud.
- *Irregularity metric:* DTR trend, anomaly, variance.

### D. "Months and fortnights rotate irregularly"
- *Literal:* synodic month / lunar fortnight — fixed.
- *Measurable:* month-to-month regularity & sub-seasonal disruption.
  - Monthly temp/precip anomaly variance, seasonal-cycle amplitude: **GISTEMP**,
    **CRU TS**, **ERA5** monthly.
  - Sub-seasonal (~fortnight–intraseasonal) oscillation: **MJO index** (NOAA/BoM).
  - Optional literal-lunar tie: spring–neap tidal signal (**PSMSL** tide gauges).

### E. "Seasons and years rotate irregularly"  *(richest, most literal)*
- Growing-season timing (start/end/length shifting): **MODIS phenology (MCD12Q2)**,
  NDVI series.
- Monsoon onset/withdrawal dates: APHRODITE, ERA5-derived, IMD.
- **Interannual variability — the master "irregular years" driver: ENSO**
  (ONI / Niño-3.4) **[built]**, plus PDO, IOD.
- Growing-degree-days, first/last frost: GHCN-Daily.
- *Irregularity metric:* interannual variance of season timing; ENSO amplitude.

## 3. Full concept → free-data map (implemented columns)

| Sutta node | Proxy | Source | Column |
|---|---|---|---|
| Rulers / officials / citizens "in dhamma" | Rule of Law, Control of Corruption, Gov. Effectiveness, Voice | World Bank WGI (`GOV_WGI_*`) | `rule_of_law`, `control_corruption`, `gov_effectiveness`, `voice_accountability` |
| Behavioural driver of "irregularity" | CO₂ per capita | World Bank `EN.GHG.CO2.PC.CE.AR5` | `co2_per_capita` |
| Seasons/years irregular (node E) | ENSO annual amplitude | NOAA CPC ONI | `enso_amplitude`, `enso_max_abs` |
| Sun irregular (node A) | sunspot number/anomaly | SILSO (best-effort) | `sunspot_number`, `sunspot_anomaly` |
| Crops "ripen unevenly" | cereal yield + within-country instability | World Bank `AG.YLD.CREL.KG` | `cereal_yield`, `cereal_yield_irreg` |
| Short-lived | life expectancy | World Bank `SP.DYN.LE00.IN` | `life_expectancy` |
| Weak / sick (nutrition & disease) | stunting, undernourishment, under-5 mortality | World Bank | `child_stunting`, `undernourishment`, `under5_mortality` |
| Confounders | GDP/capita, population | World Bank | `gdp_per_capita`, `population` |

## 4. Hypotheses & analysis

- **H1 co-movement:** irregularity/quality cluster across nodes (correlation heatmap).
- **H2 moderation (core):** governance *buffers* how ENSO swings translate into
  crop instability — negative `enso_amplitude × rule_of_law` interaction
  (`PanelOLS`, country FE; TimeEffects omitted so the year-global ENSO stays identified).
- **H3 downstream:** crop level/instability → health (two-way FE).
- **Between-country model:** because governance is sticky, also test its
  *cross-country* variation on country-mean outcomes (`statsmodels` OLS).

## 5. Caveats (read before interpreting)

- **No celestial causation.** The astronomical nodes are reframed as *observable
  regularity*; LOD/sunspots are real but not behaviour-driven.
- **Fixed-effects washout.** WGI governance barely moves within a country, so
  two-way FE can return spurious nulls — hence the between-country model.
- **Confounding by development.** Governance↔health is largely GDP-driven; always
  control GDP. The merge sanity check is *not* evidence for the claim.
- **Resolution mismatch.** ENSO/sunspots/LOD are global-annual, merged on `year`,
  not country panel columns — so they cannot be "explained" by country governance.
- **Ecological correlation, reverse causality.** Lagging predictors mitigates but
  does not identify causal effects.

## 6. What the data actually shows (this run)

- **Substitution is valid:** proxies recover known reality — ENSO amplitude
  reproduces the 1997/98 and 2015/16 super-El-Niños; `rule_of_law` correlates
  +0.65 with life expectancy, −0.56 with under-5 mortality.
- **Causality dissolves under controls:** `cereal_yield` is insignificant for
  longevity once GDP + FE are included; the `enso × rule_of_law` interaction is
  **negative as predicted** (better governance dampens ENSO→yield instability)
  but **not significant** (p≈0.28); between-country, `rule_of_law` is
  insignificant once GDP is held (R²≈0.70 from GDP alone).

## 7. Roadmap (from `goal.txt`) — three summits

1. **Climate Risk Model, not cosmic mechanism.** Reframe as: natural-system
   volatility (nodes A–D, esp. country-level **DTR** node C and **MJO** node D)
   → systemic risk to human systems (yields/governance, node E). Deliverable: a
   **Global Risk Map** flagging countries that turn vulnerable when climate
   volatility spikes under weak governance.
2. **Solve causality.** Beat the GDP confounding with **two-way fixed effects**
   (country+year) using within-country climate shocks as the exogenous variation
   (Dell–Jones–Olken logic), plus **IV/2SLS** (weather instruments agriculture).
   Claim target: "climate anomalies harm social stability *net of national wealth*."
3. **Whitepaper.** Sutta → "Anthropogenic Disruption Hypothesis"; methodology
   maps satellite/reanalysis data (Open-Meteo/ERA5, MODIS, VIIRS, NASA POWER) to
   the ancient text; honest Discussion of limits.

**Keystone:** #1 and #2 both gate on **country-level climate volatility** (ENSO
is global → no map, weak instrument). Source chosen: capital-point **DTR** from
**Open-Meteo ERA5 archive** (free, keyless), coordinates from World Bank country
metadata. Caveat: capital-point ≠ agricultural-region average — a stated v1 proxy.

## 8. Conclusion (v1, ENSO-only)

The Adhammika cascade can be substituted with free data and is
visible as a real *pattern of co-movement* — but it is largely explained by
development level, is not demonstrably a literal causal chain, and certainly not
celestial mechanics. The framework is a sound scaffold for examining the
behavioural relationships; stronger identification (instrumental variables, more
of nodes A–D, sub-national resolution) would be the next step.
