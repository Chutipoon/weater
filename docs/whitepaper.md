# The Anthropogenic Disruption Hypothesis
### Translating a 2,500-year-old causal cosmology into a testable climate-risk model

*Working paper — draft. Sections 1–5 are stable; the abstract still needs
finalising against the results below.*

---

## Abstract

The Adhammika Sutta asserts a causal cascade from the conduct of rulers, through
the regularity of natural cycles, to agricultural yield and human health. We
restate this as a falsifiable scientific hypothesis — that **volatility in
natural systems imposes systemic risk on human agricultural and social systems,
conditional on governance** — and test it on a global country-year panel built
entirely from free, open data (1996–2022). Proxies for each cascade node
recover known reality (ENSO reproduces the 1997/98 and 2015/16 super-El-Niños;
rule of law correlates with life expectancy and under-5 mortality at expected
magnitudes), confirming the substitution is valid. The core claim holds in
reduced form: a country-fixed-effects model with a GDP control shows ENSO
amplitude depresses life expectancy roughly twice as much in weak-governance
countries as in strong-governance ones (−0.86 vs −0.42 years; interaction
p = 0.033) — planetary climate shocks harm health more where institutions are
weak, net of national wealth. The causal version of this claim — instrumenting
crop yield with ENSO-driven precipitation to isolate the crop → health channel
— is a negative result: neither global ENSO nor country-level growing-season
precipitation (fetched via Google Earth Engine, 198 countries × 27 years) is a
strong enough predictor of cereal yield to support credible 2SLS (first-stage
F = 1.49 and 1.16 respectively, both far below the F > 10 rule of thumb). We
report this honestly rather than lean on an underpowered instrument, and find
that the paper's central result does not depend on it. The Adhammika cascade is,
in short, a real and governance-conditioned pattern in the open-data record —
not proof of the sutta's literal causal chain, but a demonstration of how far
that ancient intuition can be carried by rigorous testing before identification
runs out.

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

## 5. Discussion

**What the evidence supports.** Two things survive scrutiny. First, the
substitution itself is valid: free, programmatically-fetched proxies recover
known physical and social reality (ENSO reproduces both super-El-Niños; rule
of law tracks life expectancy and under-5 mortality at the magnitudes the
governance literature would predict). Second, the reduced-form H2/H3 result —
climate shocks depress life expectancy roughly twice as much in weak-governance
countries (−0.86 vs −0.42 yr, interaction p = 0.033) — holds up under country
fixed effects and a GDP control, and does not require the precipitation
instrument to be believed. That is the paper's actual finding: not that ENSO
*causes* governance to fail, but that a planetary-scale, plausibly-exogenous
shock is absorbed differently depending on institutional quality, net of
national wealth. This is the sutta's cascade in its most defensible form —
irregularity in a natural cycle, transmitted asymmetrically by governance, to
human welfare.

**What it doesn't support.** Everything upstream of that reduced-form result is
weaker than the headline number implies. H1 co-movement is real but is mostly a
development-level artifact — rule of law, income, and health all move together
because they share a common cause (state capacity), not because governance
disciplines celestial regularity. The crop-yield leg of H2 (`enso_amplitude ×
weak_gov` on yield anomalies) is same-signed but not significant (p = 0.367,
`outputs/iv_report.txt`), so the mechanism implied by the reduced form — shocks
hit crops harder, crops hit health harder, weak governance amplifies both legs
— is asserted by the whole-chain result but not independently confirmed at the
crop-yield step with country-level cereal statistics this coarse. And the causal
version of H3, the actual point of the multi-day GEE precipitation build, is a
clean negative result: neither ENSO → local precipitation (p = 0.46) nor local
precipitation → cereal yield (F = 1.16) is strong enough to support 2SLS. A
weak instrument doesn't just fail to help; it biases the 2SLS estimate toward
the (endogenous) OLS number and inflates its variance, so the +0.00018 (p =
0.916) coefficient in §4 is not evidence either way. The honest reading is that
this dataset cannot currently identify the crop → health causal link; it can
only show that the joint climate-shock → health response is governance-
dependent.

**Why the confound (GDP) matters more than it looks.** Every regression here
controls for GDP per capita precisely because governance and income are
collinear enough that an uncontrolled version of H2 would just be restating
"poor countries are more fragile." The interaction surviving a GDP control and
country fixed effects is the strongest evidence in the paper — it means weak
governance amplifies climate shocks *beyond* what national wealth alone would
predict. But fixed effects and a linear GDP control are not a complete defense:
governance is sticky within a country (`research_design.md` §5), so most of its
identifying variation is cross-country, and cross-country comparisons are
exactly where omitted development-adjacent confounders (institutional history,
colonial legacy, geography) are hardest to rule out with a two-variable control.

**Ecological inference and proxy limits.** Every number in this panel is a
national annual average: capital-point or country-mean climate merged with
country-mean crop yield merged with country-mean health. Three specific losses
follow from that choice, each already flagged narrowly in Limitations: (1)
agricultural regions are not capital cities, so climate exposure is mismeasured
for any country where farmland and the capital have different weather; (2)
ENSO amplitude is unsigned (|ONI|), which is the right regressor for "do bigger
shocks hurt more" but the wrong one for a signed local-precipitation
relevance test, since El Niño and La Niña push regional rainfall in opposite
directions and averaging away that sign before the precip-IV stage is a
plausible independent explanation for its weak first stage; (3) the
growing-season window search doesn't wrap Dec/Jan, understating Southern
Hemisphere wet seasons that straddle the calendar boundary. None of these is
fatal to the reduced-form result, which only needs country-year climate
severity, not a signed, regionally-precise precipitation series — but all
three would need fixing before the IV chain could be revisited credibly.

**What stronger identification would take.** Concretely: signed ONI (or a
country-specific ENSO-teleconnection index rather than a global amplitude) to
give the precipitation first stage a chance at cross-sectional power; a
wrapped wet-season search; sub-national crop and climate data (FAO GAUL admin-1
yields against gridded precipitation) to escape country-year ecological
aggregation entirely; and, if the goal is a genuinely causal crop → health
estimate, an instrument with a stronger and better-understood a priori
mechanism than ENSO-mediated rainfall — for example, a weather-generator-based
yield shock uncorrelated with contemporaneous local governance shifts. None of
this is a quick fix; it is why these fixes are listed as open, not attempted.

**What this paper is and isn't.** It is not a demonstration that the Adhammika
Sutta's causal chain is literally true, and the sutta's astronomical framing
(sun, moon, and stars "rotating irregularly") is not a claim this dataset
could ever adjudicate, because celestial mechanics don't respond to governance
— that reframing was stated as a precondition in §1 and research_design.md §1,
not relaxed here. What the paper does show is that the sutta's *functional*
claim — that societal conduct changes how much natural volatility hurts people,
and that the channel runs through governance rather than magic — survives an
honest, pre-registered-in-spirit attempt to falsify it with 27 years of global
open data, while the stronger causal version of the same claim currently
cannot be established with the instruments available. That gap, cleanly
measured rather than papered over, is the result.

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
