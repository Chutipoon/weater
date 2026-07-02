# Handoff — weater (Adhammika cascade → free-data climate-risk model)

_Last updated: 2026-07-02 (Discussion section added below). The GEE
debugging narrative further down is a historical record frozen as of
2026-07-01 — intentionally not rewritten; see SESSION_HANDOFF.md for current
live status. For a fresh agent continuing this work._

## What this project is
Tests the **Adhammika Sutta**'s causal cascade (governance → climate → crops →
health) with free open data, reframed as the **Anthropogenic Disruption
Hypothesis** ("rotate irregularly" = variance/anomaly metrics, not orbital
mechanics). Full context, mapping tables, and caveats already written — do not
re-derive:
- `idea.txt` (the sutta), `goal.txt` (the three summit goals)
- `docs/research_design.md` (concept→data map, 5 astro nodes, §5 Discussion,
  caveats, roadmap §8 — renumbered since this file was last updated)
- `docs/whitepaper.md` (summit #3 draft — Intro/Data-Map/Methods stable; Results updated)
- Plan: `C:\Users\acer\.claude\plans\look-in-idea-txt-can-it-mossy-cherny.md`
- Memory: `weater-project-state.md`, `leverage-full-skillset.md` (proactively use skills)

## Pipeline state (all runs end-to-end)
`python src/build_panel.py` → `src/analyze.py` / `src/analyze_iv.py` / `src/plot.py`.
- Panel: 217 countries × 1996–2022, free sources only (World Bank WGI+ag+health+CO₂,
  NOAA ENSO). Stdlib fetch + pandas/statsmodels/linearmodels/matplotlib.
- Note: World Bank deprecated old WGI codes → now `GOV_WGI_*`; CO₂ = `EN.GHG.CO2.PC.CE.AR5`.

## Key finding so far (summit #2, reduced form) — in `outputs/iv_report.txt`
Weak governance = bottom WGI quartile (Control of Corruption + Rule of Law; 52/217
= "Adhammika"). ENSO×weak-gov on life expectancy = **−0.44, p=0.033** (strong-gov
−0.42/yr vs weak-gov −0.86/yr), net of GDP + country FE. → climate shocks harm
health ~2× more under weak governance. Honest caveats baked into the code
(exclusion restriction, GDP confounding, FE washout).

**Superseded by Discussion below**: this number turned out to be fragile
under robustness checks added later (year FE, group-specific trends,
outlier-year exclusion). Read Discussion, not this section alone, before
citing the −0.44/p=0.033 figure.

## IN PROGRESS — pick up here
Prior job `be7xnpebe` (started 2026-06-30) hung for 14+ hours and never produced
output. Root-caused via smoke tests (2026-07-01): a single `reduceRegions()`
over all ~292 GAUL country polygons at once exceeds Earth Engine's synchronous
interactive-compute budget (hangs indefinitely rather than erroring). There's
also an independent bug — at least one GAUL polygon has an invalid ring that
throws a reprojection error ("Unable to transform edge...") under some
scale/tileScale combos; fixed with a per-feature `geometry().buffer(0, 1)` repair.

`src/fetch_precip_gee.py` was rewritten to chunk countries into batches of
`CHUNK_SIZE=25` (confirmed ~10s per chunk at native ~5.5km scale vs. an
indefinite hang for all 292 at once), with per-chunk flushed progress logging
and a `data/precip_country_gee_raw.jsonl` checkpoint so a restart resumes from
the last completed year instead of losing all progress.

Second rewrite (job `b6572nj63`) hit a second issue: some GAUL countries have
complex/large geometries that hit GEE's "User memory limit exceeded", and a few
requests hang indefinitely (no exception) rather than erroring. Added
`tileScale=8`, `_reduce_recursive()` (halve+retry on failure, isolating a
pathological country down to size 1), and a hard 120s timeout around every
`getInfo()` call (one-shot `ThreadPoolExecutor`, abandoned not joined on
timeout, so a hang can't block forever) -- job `biqzqr81j`.

That *still* wasn't enough: the recursive splitter kept cascading (many failed
attempts before isolating a bad country), because GAUL splits exactly 4
countries into several disconnected polygon features under one ADM0_NAME --
**Canada (10 features), USA (5), Australia (3), West Bank (2)** (found via a
one-off `reduceColumns` query over area/name, see `_gaul_areas.json`). Batched
`reduceRegions()` has no `bestEffort` option and genuinely can't handle these
even in isolation; singular `reduceRegion(bestEffort=True)` handles them fine
(confirmed: Canada full-year in ~60s). Also switched the working scale from
native CHIRPS (~5566m) to **22264m** (4x coarser) -- plenty for country-level
annual/seasonal aggregates and ~16x less compute per pixel.

Final design in `src/fetch_precip_gee.py`:
- `MULTI_FRAGMENT_COUNTRIES` (the 4 above) are filtered out of the main
  collection and processed separately per-year via `_reduce_multi_fragment()`
  -- merges their fragments with `FeatureCollection.geometry()` (which unions
  member geometries) then `reduceRegion(bestEffort=True)`.
- The remaining ~272 "simple" countries go through the original chunked
  `reduceRegions` + `_reduce_recursive` pipeline, which (with the 4 troublemakers
  removed) now succeeds on the first try for every chunk -- confirmed via a
  1996-only smoke test: all chunks 26-94s, zero splits/failures.
- Checkpoint (`data/precip_country_gee_raw.jsonl`) marks a year "complete" once
  every chunk/fragment-country has been *attempted* (not "zero gaps" -- a
  permanently-bad geometry fails identically every year, so gating on zero
  gaps would make that year, and therefore every resume, never converge).

Job `bop38388k` ran with this version and got further, but hit one more issue
partway through 1997: `_reduce_multi_fragment`'s merge (`FeatureCollection
.geometry()` unioning full-precision fragments) produces a geometry with
millions of edges for Canada (6.7M) and USA (3.3M) -- over GEE's 2,000,000-edge
hard limit. That failure happens *during geometry construction*, before
`reduceRegion`/`bestEffort` ever run, so simplifying afterward is too late.
Fix: simplify each fragment (`.simplify(5000)`, 5km tolerance) *before*
merging -- confirmed Canada then succeeds in ~108s. Note **1996 is already
checkpoint-sealed (`year_complete`) without this fix, so it's permanently
missing Canada + USA** -- needs a small separate backfill pass for just those
2 countries in 1996 once the main run finishes (everything else about 1996 is
fine). Australia and West Bank never had this problem (fewer/simpler
fragments) and succeeded throughout.

Background job **`bizzevp38`** (started 2026-07-01, ~2:15pm) is running the
fully-fixed version for years 1997-2022 (1996 already sealed); live log at the
job's tmp dir (`precip_gee_fetch4.log`); Monitor `b7e94cbd3` watches for year
headers/warnings/completion. Rough pace from observed chunk timings:
~15-20 min/year x 26 remaining years ≈ 6-9 hours.

**When it finishes:**
1. Read the job output; note any "GAUL names had no ISO3 match" warnings.
2. `GEE_PROJECT=<id> python src/build_panel.py` — auto-merges precip, adds
   `precip_wet3` / `precip_anom`.
3. `python src/analyze_iv.py` — the guarded **PRECIP IV** block (result #4) now
   runs: ENSO→local-precip relevance + 2SLS where precip instruments yield→health.
   Goal: first-stage F should jump from **1.49** (weak, global ENSO) into strong
   (>10) territory → the GDP-robust causal estimate summit #2 wants.
4. If GAUL→ISO3 left countries unmatched, patch the crosswalk in
   `src/fetch_precip_gee.py` (`_name_to_iso3`) and re-run.
5. Update `docs/whitepaper.md` §4 Results with the precip-IV numbers.

If this job also stalls/fails, `data/precip_country_gee_raw.jsonl` preserves
whatever years already completed — just re-run `fetch_precip_gee.py` and it
will skip years already in the checkpoint.

**Status: the above is historical.** Job `bizzevp38` finished; the "When it
finishes" steps 1–4 all happened; step 5 happened too, repeatedly, as the
result changed. See Discussion immediately below for how this actually
turned out — spoiler: the first-stage F did **not** jump into strong (>10)
territory as hoped.

## Discussion — how the causal chain (summit #2) actually turned out

Matches `docs/whitepaper.md` §5 / `docs/research_design.md` §5 / `README.md`
Discussion; this is the same conclusion, framed for someone picking up mid-debug.

- **The reduced-form finding above (−0.44, p=0.033) is real but fragile, not
  settled.** It holds — and tightens (p=0.015) — under year fixed effects, so
  it isn't an artifact of omitting them. But it loses significance and flips
  sign once weak-gov and strong-gov countries are allowed separate secular
  health trends (p=0.101), and weakens hard once the two biggest ENSO events
  (1997/98, 2015/16) are excluded (p=0.197). Added in `src/analyze_iv.py`
  `robustness_health()`. Honest read: cannot yet rule out that the two
  governance groups were just on different health trajectories that happen
  to line up with the ENSO cycle over this particular 27-year window.
- **The GEE precip fetch above succeeded completely (198 countries, 27
  years) but didn't rescue the IV as hoped.** First-stage F sequence: global
  ENSO 1.49 → local precipitation 1.16 → local precipitation after fixing
  BOTH identified weaknesses 0.87. All far below the F>10 threshold this
  whole debugging saga was fought to reach.
  - *Weakness 1, ENSO amplitude unsigned:* fixed (`enso_signed_mean` in
    `src/fetch_astro_temporal.py`). Confirmed the diagnosis — signed ONI
    predicts local precip strongly (p<0.001) where unsigned didn't (p=0.46)
    — but this only fixes the ENSO→precip *diagnostic* link, not the actual
    bottleneck.
  - *Weakness 2, wet-season window doesn't wrap Dec/Jan:* fixed
    (`_finalize()` in `src/fetch_precip_gee.py`, recomputed from the
    existing raw checkpoint with `--recompute`, no new GEE calls). Confirmed
    mechanically real — hits Southern Hemisphere countries hardest (Namibia
    +28% avg, Zimbabwe +29% avg) — but the actual first stage went from
    F=1.16 to **F=0.87**, slightly worse, not better.
  - Conclusion: the multi-day fight to get GEE precipitation working (this
    whole file) was necessary to even test the hypothesis, but the
    hypothesis itself — that country-level precipitation would give the IV
    cross-sectional power — didn't pan out. The bottleneck was never really
    "can we get precipitation data," it was "does precipitation predict
    national cereal yield," and the answer, after all that, is no.
- **Bottom line:** the paper's honest finding is a real, governance-
  conditioned but fragile reduced-form pattern, plus a fully-tested causal
  negative result. Neither is the outcome summit #2 was aiming for when this
  debugging saga started, and that's reported plainly rather than smoothed
  over — see `docs/whitepaper.md` for the full writeup.

## Known issues / decisions
- Open-Meteo capital-point fetchers (`fetch_climate_country.py` /
  `fetch_precip_country.py`) are **rate-limited (429s)** — superseded by GEE. Keep
  as fallback only. `data/climate_country.csv` has DTR for only 71 countries.
- CCKP API was probed for no-auth precip but its identifier format wouldn't yield
  data — abandoned in favor of GEE.
- User priority: finish summit #2 (causality), then #3 (whitepaper). Summit #1
  (Global Risk Map) is after those.
- Interrupted mid-task earlier: a `/loop-me` grilling session
  (`C:\Users\acer\.claude\skills\loop-me\`, `NOTES.md` + `workflows/`). Resume only
  if the user asks.

## Suggested skills
- **scrutinize** — before accepting any strengthened causal result, sanity-check
  the IV (first-stage strength, exclusion restriction, sign plausibility).
- **karpathy-guidelines** / **ponytail** — keep changes surgical, avoid new deps
  (project deliberately uses stdlib fetch).
- **post-mortem** — if a fix/bug emerges worth recording.

## Redactions
GEE Cloud project id and user email intentionally omitted here; project id lives in
the shell env/history and is required to run the GEE script.
