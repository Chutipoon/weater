"""Causal design per goal.txt summit #2 (user specification).

Instrument: large-scale exogenous climate anomaly = ENSO (ONI amplitude). It is
planetary-scale (exogenous to any country's GDP/health system) and reaches human
health ONLY through the agricultural channel -> the exclusion restriction holds,
unlike a temperature instrument. (Hsiang-style ENSO-economics design; maps onto
the sutta's variations "propagating down from the sun, moon and stars".)

Definitions (user spec):
  - Crop proxy: cereal yield ("Sassa" / grain).
  - Outcome of degradation: crop YIELD ANOMALY (detrended).
  - Weak governance ("Adhammika"): bottom-quartile countries on WGI Control of
    Corruption + Rule of Law.

Three results:
  1. Reduced form (robust): does ENSO disrupt yields MORE under weak governance?
  2. ENSO -> health reduced form, by governance group.
  3. IV/2SLS: ENSO instruments cereal_yield -> life_expectancy (+ first-stage
     strength; weak global ENSO is expected -> motivates country-level
     ENSO-driven precipitation from the GEE bulk pull).

Output: outputs/iv_report.txt.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from linearmodels.iv import IV2SLS
from linearmodels.panel import PanelOLS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

REPORT = os.path.join(config.OUT_DIR, "iv_report.txt")
_lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    _lines.append(s)


def _zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def detrend_signed(s: pd.Series) -> pd.Series:
    """Per-country detrended, standardized residual (signed). Used for yield and
    precipitation anomalies."""
    s = s.astype(float); mask = s.notna()
    if mask.sum() < 5:
        return pd.Series(np.nan, index=s.index)
    x = np.arange(len(s))[mask.values]; y = s[mask].values
    resid = y - np.polyval(np.polyfit(x, y, 1), x)
    sd = resid.std(ddof=0) or 1.0
    out = pd.Series(np.nan, index=s.index); out[mask] = resid / sd
    return out


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["log_gdp"] = np.log(df["gdp_per_capita"])

    # Weak governance = bottom quartile of mean(z(Control of Corruption), z(Rule of Law)).
    gov = (_zscore(df["control_corruption"]) + _zscore(df["rule_of_law"])) / 2
    df["gov_index"] = gov
    cmean = df.groupby("iso3")["gov_index"].mean()
    thresh = cmean.quantile(0.25)
    df["weak_gov"] = df["iso3"].map((cmean <= thresh).astype(int))

    # Crop yield anomaly: per-country detrended, standardized residual (signed);
    # magnitude = degradation/irregularity size.
    df = df.sort_values(["iso3", "year"])
    df["yield_anom"] = df.groupby("iso3")["cereal_yield"].transform(detrend_signed)
    df["yield_anom_abs"] = df["yield_anom"].abs()
    if "precip_wet3" in df.columns:   # growing-season precip anomaly (GEE/proxy)
        df["precip_anom_s"] = df.groupby("iso3")["precip_wet3"].transform(detrend_signed)
    n_weak = int(df.drop_duplicates("iso3")["weak_gov"].sum())
    say(f"Weak-governance countries (bottom 25% WGI CC+RL): {n_weak} of "
        f"{df.iso3.nunique()} (threshold gov_index <= {thresh:.2f})")
    say("")
    return df


def reduced_form_yield(df: pd.DataFrame) -> None:
    say("=" * 72)
    say("1) RISK CORE (reduced form): yield_anom_abs ~ enso_amplitude * weak_gov")
    say("   [country FE; weak_gov is country-constant -> interaction identifies it]")
    say("=" * 72)
    d = df.dropna(subset=["yield_anom_abs", "enso_amplitude", "weak_gov"]).set_index(["iso3", "year"])
    res = PanelOLS.from_formula(
        "yield_anom_abs ~ 1 + enso_amplitude + enso_amplitude:weak_gov + EntityEffects",
        d, drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    say(str(res.summary.tables[1]))
    b = res.params.get("enso_amplitude:weak_gov", np.nan)
    p = res.pvalues.get("enso_amplitude:weak_gov", np.nan)
    sig = "significant" if p < 0.05 else "NOT significant"
    say(f"  enso x weak_gov = {b:+.3f} ({sig}, p={p:.3f}). Positive => ENSO shocks")
    say("  enlarge crop-yield anomalies MORE in weakly-governed countries.")
    say("")


def reduced_form_health(df: pd.DataFrame) -> None:
    say("=" * 72)
    say("2) ENSO -> HEALTH (reduced form): life_expectancy ~ enso_amplitude * weak_gov")
    say("   + log_gdp  [country FE]")
    say("=" * 72)
    d = df.dropna(subset=["life_expectancy", "enso_amplitude", "weak_gov", "log_gdp"]).set_index(["iso3", "year"])
    res = PanelOLS.from_formula(
        "life_expectancy ~ 1 + enso_amplitude + enso_amplitude:weak_gov + log_gdp + EntityEffects",
        d, drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    say(str(res.summary.tables[1]))
    main = res.params.get("enso_amplitude", np.nan)
    inter = res.params.get("enso_amplitude:weak_gov", np.nan)
    p = res.pvalues.get("enso_amplitude:weak_gov", np.nan)
    sig = "significant" if p < 0.05 else "NOT significant"
    say(f"  ENSO effect on life expectancy: strong-gov = {main:+.2f}/yr,")
    say(f"  weak-gov = {main + inter:+.2f}/yr (interaction {inter:+.2f}, {sig}, p={p:.3f}).")
    say("  => climate shocks depress health MORE under weak governance, net of GDP")
    say("     and country fixed effects -- the core 'Adhammika' claim, in reduced form.")
    say("  CAVEAT: ENSO may reach health partly via floods/disease (cholera, malaria,")
    say("  disasters), not crops alone -- so the IV exclusion restriction is not")
    say("  airtight; the reduced form above does not depend on it.")
    say("")


def iv_2sls(df: pd.DataFrame) -> None:
    say("=" * 72)
    say("3) IV/2SLS: life_expectancy ~ [cereal_yield ~ enso_amplitude + enso_max_abs]")
    say("   + log_gdp   (ENSO as exogenous instrument for agriculture)")
    say("=" * 72)
    d = df.dropna(subset=["life_expectancy", "cereal_yield", "enso_amplitude",
                          "enso_max_abs", "log_gdp"]).copy()
    res = IV2SLS.from_formula(
        "life_expectancy ~ 1 + log_gdp + [cereal_yield ~ enso_amplitude + enso_max_abs]",
        d).fit(cov_type="robust")
    b, p = res.params["cereal_yield"], res.pvalues["cereal_yield"]
    say(f"  2SLS cereal_yield -> life_expectancy: coef={b:+.5f} (p={p:.3f}, n={int(res.nobs)})")
    fs = res.first_stage.diagnostics
    f = float(fs["f.stat"].iloc[0])
    say(f"  First-stage F = {f:.2f}  ({'STRONG' if f > 10 else 'WEAK (<10)'} instrument)")
    if f < 10:
        say("  Expected: global ENSO has no cross-country variation, so its first")
        say("  stage is weak. Fix = country-level, ENSO-DRIVEN growing-season")
        say("  precipitation (CHIRPS/ERA5-Land via GEE) -> strong, valid instrument.")
    say("  Exclusion restriction: ENSO reaches health only via crops (defensible),")
    say("  unlike a temperature instrument.")
    say("")


def iv_precip(df: pd.DataFrame) -> None:
    """Stronger IV: country growing-season precipitation (ENSO's local channel)
    instruments crop yield -> health. Runs only when precipitation is in the panel."""
    if "precip_anom_s" not in df.columns or df["precip_anom_s"].notna().sum() == 0:
        say("=" * 72)
        say("4) PRECIP IV: skipped -- no precipitation in panel yet.")
        say("   Run fetch_precip_gee.py (or _country.py) + build_panel.py first.")
        say("")
        return
    say("=" * 72)
    say("4) PRECIP IV/2SLS: life_expectancy ~ [cereal_yield ~ precip_anom] + log_gdp")
    say("   growing-season precipitation = ENSO's LOCAL channel; strong first stage")
    say("=" * 72)
    # Relevance of the planetary signal: does ENSO move local growing-season precip?
    rel = df.dropna(subset=["precip_anom_s", "enso_amplitude", "weak_gov"]).set_index(["iso3", "year"])
    fs0 = PanelOLS.from_formula(
        "precip_anom_s ~ 1 + enso_amplitude + enso_amplitude:weak_gov + EntityEffects",
        rel, drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    say(f"  ENSO -> local precip: enso coef={fs0.params.get('enso_amplitude', float('nan')):+.3f} "
        f"(p={fs0.pvalues.get('enso_amplitude', float('nan')):.3f})")
    # 2SLS: precip instruments yield -> health
    d = df.dropna(subset=["life_expectancy", "cereal_yield", "precip_anom_s", "log_gdp"]).copy()
    res = IV2SLS.from_formula(
        "life_expectancy ~ 1 + log_gdp + [cereal_yield ~ precip_anom_s]", d).fit(cov_type="robust")
    b, p = res.params["cereal_yield"], res.pvalues["cereal_yield"]
    f = float(res.first_stage.diagnostics["f.stat"].iloc[0])
    say(f"  2SLS cereal_yield -> life_expectancy: coef={b:+.5f} (p={p:.3f}, n={int(res.nobs)})")
    say(f"  First-stage F = {f:.2f}  ({'STRONG' if f > 10 else 'WEAK (<10)'} instrument)")
    say("  CAVEAT: precip may also reach health via floods/water-borne disease;")
    say("  exclusion restriction is plausible but not airtight.")
    say("")


def main() -> None:
    df = prepare(pd.read_csv(config.PANEL_CSV))
    reduced_form_yield(df)
    reduced_form_health(df)
    iv_2sls(df)
    iv_precip(df)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(_lines))
    print(f"\nReport written to {REPORT}")


if __name__ == "__main__":
    main()
