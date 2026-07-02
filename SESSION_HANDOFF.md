# Session Handoff — GEE precip fetch debugging (weater)

_Written 2026-07-01 ~3:05pm. For a fresh agent picking up this specific
conversation. For the full project background and deep technical history of
everything below, read `HANDOFF.md` first — it has been kept up to date
throughout this session and is the canonical detail source. This file only
covers what's live/in-flight right now so a fresh agent doesn't have to
re-derive it from the conversation transcript._

## What this session did

Picked up from a prior session's stalled background job (`be7xnpebe`, CHIRPS
precip fetch via `src/fetch_precip_gee.py`, hung 14+ hours). Root-caused and
fixed through several rounds — full blow-by-blow is in `HANDOFF.md`'s
"IN PROGRESS" section, not repeated here. Short version: batched
`reduceRegions()` over all ~292 GAUL country polygons exceeds GEE's
synchronous compute budget; 4 countries (Canada, USA, Australia, West Bank)
are split into disconnected multi-part GAUL features that need special
handling; merging those parts at full precision blew past GEE's edge-count
limit; one GAUL polygon has permanently corrupt coordinates. All fixed in the
current `src/fetch_precip_gee.py`.

## FETCH COMPLETE (UPDATED 2026-07-02 ~2:15am)

All 27 years (1996-2022) are fetched, checkpointed, and merged.
`data/precip_country_gee.csv` exists: **165 countries / 4453 rows**. The two
parallel processes (A, B) both finished all their years successfully but then
hung as zombies (`HasExited: False`, near-zero CPU) after crashing in their
final CSV-write step — root cause and fix below. Both zombies were killed
after their checkpoint data was confirmed safe and merged; monitors stopped.
**No fetch process should be running anymore** — if a future check-in finds
one, that's unexpected and worth investigating fresh, not assumed-expected.

**Bug found and fixed:** `fetch_precip_gee.py`'s row-building code named
monthly columns via `{f"m{m:02d}": vals[m-1] for m in range(12)}` (m=0..11),
which produced keys `m00..m11` instead of the intended `m01..m12` — `m00`
silently held *December's* value (via `vals[-1]` wraparound) while `m01-m11`
happened to already be correct. This is why both parallel processes crashed
at the very end with `KeyError: "['m12'] not in index"` when building
`precip_annual` — but only after fully completing all their GEE fetching and
checkpoint writes, so **no data was lost**, only mislabeled. Fixed in the
script (`range(12)` → `range(1, 13)`, both occurrences: the main chunk loop
and the multi-fragment loop) and retroactively in all existing checkpoint
data via a one-time key-rename pass (`m00`→`m12`, verified 100% consistent
across all 6288 rows, 0 conflicts). Originals backed up as
`data/precip_country_gee_raw*.pre_m12fix_backup.jsonl`.

**ISO3 name-matching gap: FIXED (2026-07-02).** Of the original 68 unmatched
GAUL names, 32 were real countries missed only because the World Bank uses a
different official spelling (`"United States of America"` vs. WB's `"United
States"`, `"Congo"` vs. `"Congo, Rep."`, `"Czech Republic"` vs. `"Czechia"`,
etc. — not encoding corruption; `"Côte d'Ivoire"`'s `�` was just a terminal
display artifact, the underlying JSON already had the correct `ô`
escape). Added `GAUL_ISO3_OVERRIDES` (explicit name→ISO3 dict, checked before
the normalized-match fallback) in `fetch_precip_gee.py`. Verified zero ISO3
collisions before applying (a real risk here: e.g. aliasing both `"West
Bank"` and `"Gaza Strip"` to WB's single combined `"West Bank and Gaza"`
(PSE) would have silently created duplicate PSE rows per year — the same
class of bug as the earlier 1996-98 dedup issue. Deliberately only aliased
`"West Bank"`, left `"Gaza Strip"` unmapped). Rebuilt CSV:
**165 → 198 countries, 4453 → 5343 rows**. USA confirmed present (26/27
years, missing only 1996 same as Canada). Remaining 35 unmatched names are
genuinely correct to exclude — disputed territories (Jammu and Kashmir, Aksai
Chin, Abyei...), dependent territories WB doesn't track separately
(Martinique, Guernsey, Jersey...), Taiwan (WB doesn't track it), and
Netherlands Antilles (dissolved 2010, ambiguous successor state).

## Merge history / how we got here (superseded by "FETCH COMPLETE" above)

Before merging, switched to 2-process parallelism at the user's request once
years 1996-2008 were done (13/27) — see below for that history, plus a
separate real bug (duplicate checkpoint rows for 1996-1998 from pre-session
crash history) that was found and fixed before the split. All checkpoint
files (`precip_country_gee_raw.jsonl`, `_a.jsonl`, `_b.jsonl`) were merged
into the single `data/precip_country_gee_raw.jsonl` (6315 lines: 6288 data
rows + 27 `year_complete` markers, one per year). `fetch_precip_gee.py` was
then re-run with no args; since every year was already checkpointed, it did
zero new GEE calls and just rebuilt the CSV from cache — confirming the
merge and m12 fix both worked.

## Superseded: live state during the parallel split (2026-07-01 ~11:05pm)

**Switched to 2-process parallelism** at the user's request once years
1996-2008 were done (13/27). Before splitting, discovered and fixed a real
bug: the checkpoint file had genuine duplicate `(country, year)` rows for
1996/1997/1998 (194/172/218 dup pairs, some countries up to 4x) — leftover
debris from the pre-session crash/resume history, where a year's `adm0_name`
rows from an earlier *interrupted* attempt were never purged, and once that
year later got a real `year_complete` marker, *all* historical rows for that
year (stale + fresh) became "valid" per `_load_checkpoint`'s filter. This was
silent — no error, no log line — and would have corrupted `build_panel.py`'s
merge. Fixed by de-duplicating (keep-last-occurrence per country-year) and
dropping orphan rows for years without a `year_complete` marker. Original
preserved at `data/precip_country_gee_raw.pre_dedupe_backup.jsonl`; cleaned
version is now the live `data/precip_country_gee_raw.jsonl` (3026 rows: 231
for 1996, 232 for 2007 — both exactly matching the already-known Canada/USA
gaps — 233 for every other 1996-2008 year). **This dedup logic is a one-off
manual fix, not built into the script** — if `fetch_precip_gee.py` is ever
interrupted mid-year again, re-run the same audit before trusting row counts.

Also note: `year_rows` in the script's own per-year log line (e.g. "1999:
275 countries total") counts every feature GEE *returned*, not rows actually
*written* — CHIRPS only covers 50°S-50°N, so ~43 countries have all-None
monthly values every year and are silently dropped before the checkpoint
write, with no log line for it. This is expected/deterministic (233 valid
countries/year, confirmed identical across 1999-2008) and not a bug, but the
log line is misleading — don't use it to sanity-check row counts, use the
jsonl directly.

`fetch_precip_gee.py` now takes optional CLI args: `python
src/fetch_precip_gee.py <start_year> <end_year> <suffix>` — restricts the run
to that year range and checkpoints to `precip_country_gee_raw_<suffix>.jsonl`
/ `precip_country_gee_<suffix>.csv` instead of the shared default files (no
args = original full-range default-file behavior, unchanged). `CHUNK_SIZE`
(25) was left untouched per instruction.

- **Process A**: PID `27720`, years 2009-2015, log
  `precip_gee_fetch_a.log`, checkpoint `data/precip_country_gee_raw_a.jsonl`.
- **Process B**: PID `13724`, years 2016-2022, log
  `precip_gee_fetch_b.log`, checkpoint `data/precip_country_gee_raw_b.jsonl`.
- Both are detached `Start-Process` processes (same durability caveat as
  below applies — verify liveness each check-in, not guaranteed to survive
  an arbitrarily long session gap).
- **When both finish:** concatenate `data/precip_country_gee_raw.jsonl` +
  `_a.jsonl` + `_b.jsonl` into one file (no dedup needed this time — disjoint
  year ranges, no overlap), then run `python src/fetch_precip_gee.py` with no
  args (defaults) — since every year will already have a `year_complete`
  marker, it does zero GEE calls and just rebuilds the final
  `precip_country_gee.csv` from the merged checkpoint.

### Prior (pre-parallel-split) state, superseded by the above

**The original job (`bizzevp38` / job dir `610046d4`) died silently** between
the first handoff and this update — no `python.exe` process was running, and
the job directory had been garbage-collected. Root cause suspected: it was
launched in a way tied to the prior session's process tree (PowerShell
`Start-Job` / Claude Code job-manager-tracked process), which got torn down
when that session ended — background jobs launched this way are **not**
guaranteed to survive a session boundary. Confirmed safe on restart: checkpoint
logic (`_load_checkpoint` in `fetch_precip_gee.py`) only trusts rows from years
with a `year_complete` marker, so the partial in-progress year (1998) was
automatically discarded and cleanly refetched — no manual cleanup was needed.

- **Relaunched as PID `20784`**, a detached `Start-Process` (not tied to a
  PowerShell job object), with stdout/stderr redirected straight to files
  (not piped — piping without an active reader risks a full-buffer deadlock,
  which was a bug in an intermediate relaunch attempt this session, caught
  and fixed before it ran long). Started ~5:18pm.
  - **Note:** a Windows Scheduled Task (`schtasks`) was tried first for
    stronger cross-session durability but was blocked by the auto-mode safety
    classifier as an unauthorized persistence mechanism; the user was asked
    and explicitly chose the detached-process approach instead over
    authorizing schtasks. **This means the same failure mode could recur** —
    if this process is also gone next check-in, that's why; the fix is either
    to re-launch again the same way, or ask the user to authorize a
    Scheduled Task for a version that's guaranteed to survive.
  - PID recorded in `C:\Code\weater\precip_gee_fetch5.pid`.
- **Monitor task `bxxijji70`** watches the new log for year headers, warnings,
  and completion (regex on `^[n/n]`, `warn`, `split`, `permanently`, `Saved`,
  `Traceback`, `Error`), and will surface a task-notification on events. Same
  session-boundary caveat as above applies to this monitor — if it's gone,
  re-arm by tailing `precip_gee_fetch5.log`.
- **Log files** (not project-tracked, plain UTF-8 this time since file
  redirection was used instead of `Tee-Object`):
  `C:\Code\weater\precip_gee_fetch5.log` (stdout) and
  `C:\Code\weater\precip_gee_fetch5.err.log` (stderr). Read directly, no
  `iconv` needed.
- **On resume, confirmed:** `[resume] 830 rows cached for completed years
  [1996, 1997]` then restarted year 1998 cleanly (chunk 1/11 succeeded in
  32.2s) — pace consistent with prior run.
- **Observed pace:** ~24 min/year (from the original run). ~24 years remain
  (1998–2022, since 1997 is now sealed) → rough estimate ~9-10 hours to full
  completion from this relaunch.
- **A fresh `ScheduleWakeup` should be armed** after this update for ~1 hour
  out to check progress, confirm PID 20784 is still alive, and reschedule.
- **Expected, already-diagnosed warnings** (do not re-investigate these as if
  novel — see `HANDOFF.md` for why):
  - `country index 271 permanently failed` — one GAUL polygon has corrupt
    lat/lon coordinates; deterministic, harmless, expected every year.
  - Occasional `[split]` lines for other countries — the recursive
    halve-and-retry safety net working as designed, not a failure.
- **Known gaps needing a follow-up patch** (both are one-off transient misses,
  not the deterministic index-271 failure — fix the same way, by calling
  `_reduce_multi_fragment` for the specific country/year and appending the
  row to `data/precip_country_gee_raw.jsonl`, or just re-derive the CSV after
  a manual re-run of those cells):
  - **1996: Canada + USA.** Year was marked complete (`year_complete`
    checkpoint entry) *before* the Canada/USA merge-simplify fix landed, so
    it's permanently missing those two countries specifically.
  - **2007: Canada.** During this relaunch, GEE was running unusually slow for
    a stretch (chunk 11/11 took 1001.8s vs. the typical ~450s), and Canada's
    dedicated `_reduce_multi_fragment` path — normally reliable in ~60s —
    timed out at 180s (`[warn] Canada permanently failed: getInfo() exceeded
    180s`). Not a code defect, just a slow-GEE transient; 2007 will need
    Canada backfilled the same way as 1996's gap.
  - Check for more of these when the fetch finishes: `grep -v "index 271"
    data/precip_country_gee_raw.jsonl` won't work directly since failures
    aren't logged to the jsonl (only to the log file) — instead diff each
    year's country count against 275 (276 minus the 1 permanent index-271
    miss) using the final CSV, or grep `precip_gee_fetch5.log` for
    `permanently failed` and exclude the `country index 271` lines.

## Data pipeline status: fully clean, ready for `build_panel.py`

`data/precip_country_gee.csv`: **198 countries / 5346 rows**, all 27 years
(1996-2022), Canada and USA both at full 27/27 coverage. **1996+2007 Canada/USA
gaps backfilled (2026-07-02)** — called `_reduce_multi_fragment` directly for
`("Canada", 1996)`, `("United States of America", 1996)`, `("Canada", 2007)`,
verified all three returned complete 12-month data (no `None`s) and sane
magnitudes (Canada ~900-1000mm/yr, USA ~800mm/yr, consistent with other
years), appended to the checkpoint, and rebuilt the CSV. No more known gaps.

## `build_panel.py` ran (2026-07-02): `data/panel.csv` — 5859 rows × 24 cols,
217 countries, 1996-2022. Precip merged cleanly (198 countries, 5346 non-null
`precip_annual`/`precip_wet3` rows — matches the precip CSV exactly, no loss).

## Next steps

1. `python src/analyze_iv.py` — check the precip-IV first-stage F statistic
   (goal: >10 for a strong instrument; was 1.49 with global-ENSO before this
   whole precip effort).
2. Update `docs/whitepaper.md` §4 Results with the new precip-IV numbers.

## Redactions

GEE Cloud project id and user email intentionally omitted from this file
(consistent with `HANDOFF.md`'s existing redaction policy). The project id is
required as `$env:GEE_PROJECT` to run any GEE script — get it from shell
history or ask the user.

## Suggested skills for the next agent

- **scrutinize** — once the precip IV result is in hand, sanity-check it
  before accepting: first-stage F strength, exclusion-restriction plausibility
  (does ENSO→local precip→crops→health still make sense), sign/magnitude
  sanity relative to the existing reduced-form result (−0.44, p=0.033).
- **karpathy-guidelines** / **ponytail** — if further fixes to the fetch
  script are needed, keep them surgical; this file/HANDOFF.md already show a
  long chain of narrowly-targeted fixes rather than rewrites — keep that
  pattern, and resist the urge to refactor the whole script now that it works.
- **post-mortem** — this GEE debugging saga (hang → memory limits → GAUL
  multi-fragment countries → edge-count overflow → corrupt geometry) is a
  good candidate for a written post-mortem once fully resolved, given how many
  distinct root causes stacked up and how each was diagnosed.
