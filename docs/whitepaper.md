# The Anthropogenic Disruption Hypothesis
### Translating a 2,500-year-old causal cosmology into a testable climate-risk model

*Working paper — draft. Abstract and Sections 1–5 are stable, including a
robustness check (§4/§5) that found the paper's headline reduced-form
interaction is not robust to standard controls — reported honestly rather than
smoothed over.*

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
magnitudes), confirming the substitution is valid. The core claim holds in the
*baseline* reduced-form specification: a country-fixed-effects model with a GDP
control shows ENSO amplitude depresses life expectancy roughly twice as much in
weak-governance countries as in strong-governance ones (−0.86 vs −0.42 years;
interaction p = 0.033). But this result is fragile, not settled: it survives
adding year fixed effects (p = 0.015), yet loses significance — and flips sign —
once weak- and strong-governance countries are allowed separate secular health
trends (p = 0.10, both controls together p = 0.39), and weakens substantially
once the two largest ENSO events (1997/98, 2015/16) are excluded (p = 0.20). We
report this rather than present the baseline p-value as final: the open-data
evidence here cannot currently rule out that the pattern reflects differential
health trends between the two governance groups over 1996–2022 rather than a
genuine governance-conditioned ENSO effect. The causal version of the claim —
instrumenting crop yield with ENSO-driven precipitation to isolate the crop →
health channel — is a cleaner negative result: neither global ENSO nor
country-level growing-season precipitation (fetched via Google Earth Engine,
198 countries × 27 years) is a strong enough predictor of cereal yield to
support credible 2SLS (first-stage F = 1.49 and 1.16 respectively, both far
below the F > 10 rule of thumb). The Adhammika cascade is, in short, a
*plausible but not yet robustly established* governance-conditioned pattern in
the open-data record — not proof of the sutta's literal causal chain, and, on
the strictest tests performed here, not yet proof of its functional core
either. What the exercise demonstrates is how far — and how precisely — that
ancient intuition can be carried by rigorous, honestly-reported open-data
testing before identification runs out.

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

So, in this *baseline* specification, planetary climate shocks depress health
**about twice as much** where governance is weak, net of national wealth and
country fixed effects. The crop-yield-anomaly interaction is same-signed but
not yet significant (national cereal yield is coarse).

**This result is fragile.** A robustness check (`src/analyze_iv.py`
`robustness_health`, `outputs/iv_report.txt` §2b) re-estimates the same
interaction under stricter, standard specifications:

> baseline (country FE only): interaction −0.44, **p = 0.033**
>
> + year fixed effects (two-way FE): interaction −0.44, **p = 0.015** (holds)
>
> + weak-gov-specific linear health trend: interaction **+0.28, p = 0.101**
> (sign flips, not significant)
>
> two-way FE + group trend together: interaction −0.13, **p = 0.390** (not
> significant)
>
> excluding the two largest ENSO events (1997/98, 2015/16): interaction −0.33,
> **p = 0.197** (not significant)

The interaction survives controlling for a common annual shock (year fixed
effects) but not for weak- and strong-governance countries simply being on
different secular health trajectories, and it weakens substantially once the
same two super-El-Niño years this paper elsewhere cites as proof the ENSO
proxy is valid (§4 above, H1) are dropped. The baseline p = 0.033 therefore
cannot currently be distinguished from (a) a group-specific health trend
coincident with, but not caused by, the ENSO cycle over this particular
27-year window, or (b) two outlier years driving the whole effect. This is
flagged here rather than treated as a settled finding; see Discussion (§5)
and Limitations.

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

**What the evidence supports.** One thing survives scrutiny cleanly: the
substitution itself is valid. Free, programmatically-fetched proxies recover
known physical and social reality (ENSO reproduces both super-El-Niños; rule
of law tracks life expectancy and under-5 mortality at the magnitudes the
governance literature would predict). The reduced-form H2/H3 result — climate
shocks depress life expectancy roughly twice as much in weak-governance
countries (−0.86 vs −0.42 yr, interaction p = 0.033) — is real in the sense
that it is not an artifact of omitting year effects (it holds, and tightens,
under two-way FE, p = 0.015). That much is a legitimate, suggestive signal:
a planetary-scale, plausibly-exogenous shock does appear to be absorbed
differently depending on institutional quality, net of a linear GDP control.
It is not, however, the paper's settled finding — see the next point.

**Why the headline health interaction is fragile.** The same interaction that
survives year fixed effects does not survive two further, equally standard
checks (`outputs/iv_report.txt` §2b, §4 above): letting weak- and
strong-governance countries have separate secular health trends flips its sign
and erases significance (p = 0.101, both controls together p = 0.390), and
dropping just the two largest ENSO events in the sample (1997/98, 2015/16)
cuts it roughly in half and erases significance (p = 0.197). Those are not
exotic robustness tests — a group-specific linear trend is the standard check
for "are these two groups just on different trajectories," and the two
super-El-Niños are the same two events this paper cites elsewhere (§4, H1) as
proof the ENSO proxy is meaningful, so excluding them is a natural check on
whether a couple of large events are carrying the whole result. Failing either
check would be a caveat; failing both, plus a sign flip under the trend
control, means the honest description is that **the data cannot currently
distinguish "weak governance amplifies climate shocks" from "weak- and
strong-governance countries had different health trajectories over this
particular 27-year window that happen to correlate with when the big ENSO
events fell."** The paper's own reduced-form claim in §4 is written with a
confidence this evidence does not yet earn.

**What it doesn't support.** Everything else is weaker still. H1 co-movement
is real but is mostly a development-level artifact — rule of law, income, and
health all move together because they share a common cause (state capacity),
not because governance disciplines celestial regularity. The crop-yield leg of
H2 (`enso_amplitude × weak_gov` on yield anomalies) is same-signed but not
significant (p = 0.367, `outputs/iv_report.txt`), so the mechanism implied by
the reduced form — shocks hit crops harder, crops hit health harder, weak
governance amplifies both legs — is asserted by the whole-chain result but not
independently confirmed at the crop-yield step with country-level cereal
statistics this coarse. And the causal version of H3, the actual point of the
multi-day GEE precipitation build, is a clean negative result: neither ENSO →
local precipitation (p = 0.46) nor local precipitation → cereal yield (F =
1.16) is strong enough to support 2SLS. A weak instrument doesn't just fail to
help; it biases the 2SLS estimate toward the (endogenous) OLS number and
inflates its variance, so the +0.00018 (p = 0.916) coefficient in §4 is not
evidence either way. The honest reading is that this dataset cannot currently
identify the crop → health causal link, and — per the point above — cannot
yet confidently establish the governance-conditioning of the reduced-form
health response either; the strongest defensible claim is that the two are
correlated in the baseline specification, with the mechanism unresolved.

**Why the GDP confound still matters, even though it isn't the binding
constraint.** Every regression here controls for GDP per capita precisely
because governance and income are collinear enough that an uncontrolled
version of H2 would just be restating "poor countries are more fragile." That
control is necessary but, as the fragility above shows, not sufficient:
governance is sticky within a country (`research_design.md` §5), so most of
its identifying variation is cross-country, and cross-country comparisons are
exactly where omitted development-adjacent confounders (institutional history,
colonial legacy, geography, and — concretely, now demonstrated — divergent
health trends) are hardest to rule out with a two-variable control plus fixed
effects alone.

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

**What stronger identification would take.** For the precipitation IV chain:
signed ONI (or a country-specific ENSO-teleconnection index rather than a
global amplitude) to give the precipitation first stage a chance at
cross-sectional power; a wrapped wet-season search; sub-national crop and
climate data (FAO GAUL admin-1 yields against gridded precipitation) to escape
country-year ecological aggregation entirely; and, if the goal is a genuinely
causal crop → health estimate, an instrument with a stronger and
better-understood a priori mechanism than ENSO-mediated rainfall. For the
health interaction specifically: the robustness checks above (two-way FE,
group-specific trends, outlier-year exclusion) should become the default
specification, not an optional appendix — report the trend-controlled and
outlier-robust estimate as the headline number, not the baseline one, and only
upgrade the language back to "holds" if it survives. None of this is a quick
fix; it is why these fixes are listed as open, not attempted.

**What this paper is and isn't.** It is not a demonstration that the Adhammika
Sutta's causal chain is literally true, and the sutta's astronomical framing
(sun, moon, and stars "rotating irregularly") is not a claim this dataset
could ever adjudicate, because celestial mechanics don't respond to governance
— that reframing was stated as a precondition in §1 and research_design.md §1,
not relaxed here. It is also not, yet, a demonstration that the sutta's
*functional* claim — that societal conduct changes how much natural volatility
hurts people, through governance rather than magic — is robustly established:
the reduced-form signal is present in a defensible baseline specification and
survives one standard check (year fixed effects) but fails two others
(group-specific trends, outlier-year exclusion) that this same paper's own
methodology would normally demand. What the paper does show is a precisely
measured, honestly reported gap — a suggestive but fragile reduced-form
correlation, a crop-yield mechanism that isn't independently confirmed, and a
causal instrument that doesn't work — rather than either a confirmed finding
or a swept-under-the-rug null. That gap, not a headline number, is the
result.

## Limitations (running list)

- **The headline ENSO × weak-governance health interaction (§4, p = 0.033) is
  not robust to two standard checks.** It survives year fixed effects
  (p = 0.015) but loses significance and flips sign under a weak-gov-specific
  linear trend (p = 0.101, or p = 0.390 combined with year FE), and weakens
  substantially when the two largest ENSO events (1997/98, 2015/16) are
  excluded (p = 0.197). See `src/analyze_iv.py` `robustness_health()` and §5.
  Not yet resolved: whether a differential secular health trend between the
  two governance groups, rather than ENSO, is driving the baseline result.
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
