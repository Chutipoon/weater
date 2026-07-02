# The Anthropogenic Disruption Hypothesis
### Translating a 2,500-year-old causal cosmology into a testable climate-risk model

*Working paper — draft. Sections 1–3 are stable; Section 4 (Results) and 5
(Discussion) fill in as the analysis finalises.*

---

## Abstract *(to finalise with results)*

The Adhammika Sutta asserts a causal cascade from the conduct of rulers, through
the regularity of natural cycles, to agricultural yield and human health. We
restate this as a falsifiable scientific hypothesis — that **volatility in
natural systems imposes systemic risk on human agricultural and social systems,
conditional on governance** — and test it on a global country-year panel built
entirely from free, open data (1996–2022). *Headline findings pending.*

## 1. Introduction — from cosmology to hypothesis

The sutta's literal chain ("the sun and moon rotate irregularly → … → crops
ripen unevenly → people are short-lived and sick") is not a claim about orbital
mechanics. We reinterpret each link as a statement about the **regularity of an
observable natural cycle** that human systems depend on. So restated, the text
becomes the **Anthropogenic Disruption Hypothesis**:

> When collective human conduct degrades the regularity of natural systems
> (climate volatility ↑), the systemic risk to agriculture and human welfare
> rises — and weak governance amplifies that transmission.

This converts metaphysics into three empirical claims:
- **H1 (co-movement):** indicators of governance, climate regularity, crop
  stability, and health move together across countries and time.
- **H2 (moderation / risk core):** climate volatility harms crop stability *more*
  where governance is weak.
- **H3 (causality):** the climate→society effect survives controlling for
  national wealth (GDP) — i.e. it is not merely a development artifact.

## 2. Data map — ancient text → open datasets

Each cascade node is substituted with a free, programmatically-fetched proxy.

| Sutta node | Reinterpretation | Proxy | Source (open) |
|---|---|---|---|
| Rulers/officials/citizens "in dhamma" | governance quality | Rule of Law, Control of Corruption, Gov. Effectiveness, Voice | World Bank WGI |
| Collective conduct (driver) | consumption/emissions | CO₂ per capita | World Bank |
| "Sun & moon rotate irregularly" (A) | received solar signal; Earth-spin | surface solar radiation; sunspots; Length-of-Day | NASA POWER; SILSO; IERS |
| "Stars rotate irregularly" (B) | atmospheric transparency / sky brightness | aerosol optical depth; night-lights | MODIS; VIIRS |
| "Nights & days rotate irregularly" (C) | day–night balance | Diurnal Temperature Range | Open-Meteo ERA5 |
| "Months & fortnights irregular" (D) | sub-seasonal disruption | monthly anomaly variance; MJO | GISTEMP; NOAA/BoM |
| "Seasons & years rotate irregularly" (E) | interannual variability | ENSO (ONI) amplitude; phenology | NOAA CPC; MODIS |
| "Crops ripen unevenly" | yield instability | cereal yield + within-country variability | World Bank / FAOSTAT |
| "Short-lived, weak, diseased" | longevity / nutrition / disease | life expectancy; stunting; under-5 mortality | World Bank |
| Confounder | development level | GDP per capita; population | World Bank |

All fetching uses the stdlib (no proprietary clients); data is cached for
reproducibility. Implementation: `src/fetch_*.py`, panel in `src/build_panel.py`.

## 3. Methodology

- **Panel:** country × year, 1996–2022, ~200 countries.
- **Irregularity construction:** "rotate irregularly" is operationalised as
  standardized anomaly, rolling variability, coefficient of variation, and
  detrended residual magnitude (`src/irregularity.py`).
- **H1:** pooled correlation matrix across cascade nodes.
- **Weak governance ("Adhammika"):** bottom quartile of countries on WGI Control
  of Corruption + Rule of Law.
- **H2:** `PanelOLS` (country fixed effects, entity-clustered SEs) with an
  ENSO × weak-governance interaction on crop-yield anomalies and on health.
- **H3:** **ENSO (ONI)** as a planetary-scale exogenous instrument for
  agriculture (Hsiang-style), with IV/2SLS — *with explicit scrutiny of the
  exclusion restriction* (ENSO should reach health only via crops). Instrument
  power requires country-level ENSO-driven precipitation (CHIRPS/ERA5-Land, GEE).

## 4. Results

**Substitution validates (H1).** Proxies recover known reality (ENSO reproduces
the 1997/98 and 2015/16 super-El-Niños; rule of law correlates +0.65 with life
expectancy, −0.56 with under-5 mortality). Co-movement is present but tracks
development level.

**Climate shocks harm health more under weak governance (H2/H3 — reduced form).**
Defining weak governance as the **bottom WGI quartile** (Control of Corruption +
Rule of Law; 52/217 countries — the "Adhammika" group), a country-fixed-effects
model with GDP control gives:

> life expectancy response to ENSO amplitude = **−0.42 yr** in strong-governance
> countries vs **−0.86 yr** in weak-governance countries
> (interaction −0.44, **p = 0.033**).

So planetary climate shocks depress health **about twice as much** where
governance is weak, net of national wealth and country fixed effects — the
sutta's core claim, in reduced form. The crop-yield-anomaly interaction is
same-signed but not yet significant (national cereal yield is coarse).

**IV/2SLS (H3) — negative result.** ENSO instrumenting cereal yield → health is
correctly specified for the exclusion restriction (ENSO is exogenous; reaches
health mainly via crops) but the **first stage is weak (F = 1.49)** — global
ENSO has no cross-country variation, only time variation, so it cannot explain
the mostly-cross-country variance in cereal yield.

The natural fix is country-level, ENSO-driven growing-season precipitation
(CHIRPS via Google Earth Engine, 198 countries × 27 years, 1996–2022), which
should give the instrument cross-sectional power. **It doesn't.** Two links in
that chain were tested and both are weak:

> ENSO → local growing-season precipitation: coef = +0.031 (**p = 0.46**, not
> significant) — planetary ENSO amplitude does not detectably move country-level
> precipitation in this specification.
>
> Local precipitation → cereal yield (the actual IV first stage): **F = 1.16**
> — *weaker* than the global-ENSO instrument it was meant to replace.

The resulting 2SLS coefficient (+0.00018, p = 0.916) is directionally sane
(more yield associates with more life expectancy) but, with F this low, is not
statistically informative — weak instruments bias 2SLS toward the endogenous
OLS estimate and inflate variance, so neither the sign nor the magnitude should
be read as evidence for or against the causal channel. **We report this as a
negative result**: with the open data used here, we could not construct an
instrument for agricultural output strong enough to support credible 2SLS
identification of the crop → health link. Two concrete, untested candidate
fixes are noted in Limitations below; neither was pursued, since the paper's
central claim (H2/H3 reduced form, above) does not depend on this instrument.

**Caveat on the instrument.** ENSO may reach health partly through floods and
disease (cholera, malaria, disasters), not crops alone — so the exclusion
restriction is not airtight even where the first stage is strong. The
reduced-form H2/H3 result above does not depend on any of this.

## 5. Discussion *(to write)*

Honest framing target: what the open-data system *can* and *cannot* establish;
the gap between co-movement and causation; the confounding role of GDP; the
ecological-inference and proxy limitations; and what stronger identification
(valid instruments, sub-national resolution, agricultural-region climate) would
take. The point is not to "prove the sutta" but to show precisely how far
rigorous open data can carry an ancient causal intuition.

## Limitations (running list)

- Capital-point climate ≠ agricultural-region climate (v1 proxy).
- Country-year aggregation → ecological inference.
- Governance (WGI) is sticky → weak within-country identification.
- Several astronomical signals (ENSO, sunspots, LOD) are global-annual.
- IV exclusion restrictions are hard to satisfy with weather instruments.
- **ENSO amplitude is unsigned (mean/peak |ONI|), not signed.** Appropriate for
  the reduced-form "do bigger shocks hurt more" question, but a poor relevance
  regressor for a signed local-precipitation instrument — El Niño and La Niña
  push regional rainfall in opposite directions, and averaging away that sign
  before it ever reaches the precip-IV test plausibly explains why ENSO
  doesn't detectably predict local precipitation in that specification. Not
  yet tested with a signed ONI series.
- **The growing-season precipitation window doesn't wrap the calendar year.**
  "Wettest 3 consecutive months" is computed only over non-wrapping windows
  within Jan–Dec, so a true wet season straddling the Dec/Jan boundary (common
  in Southern Hemisphere growing seasons) is understated in exactly the years
  its peak crosses that boundary — a plausible, untested contributor to the
  weak precip → yield first stage above.
