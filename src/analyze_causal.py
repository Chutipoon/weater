"""Causal-identification analysis (goal.txt summit #2).

Beats the GDP-confounding found in the v1 analysis using within-country climate
variation as plausibly exogenous shocks (Dell-Jones-Olken logic):

  1. Two-way FE (country+year): does climate volatility hit yields, and is the
     effect STABLE when GDP is added? (stability => not a wealth artifact)
  2. The risk-model core: does weak governance AMPLIFY climate damage?
     interaction dtr_irreg x rule_of_law, two-way FE.
  3. IV / 2SLS: instrument cereal_yield with weather (DTR/temp) to estimate the
     causal yield -> health link, purged of GDP-correlated endogeneity; reports
     first-stage strength (weak-instrument check).

Output: outputs/causal_report.txt. Read docs/research_design.md for caveats
(capital-point climate proxy; ENSO/global signals; ecological inference).
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

REPORT = os.path.join(config.OUT_DIR, "causal_report.txt")
_lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    _lines.append(s)


def load() -> pd.DataFrame:
    df = pd.read_csv(config.PANEL_CSV)
    df["log_gdp"] = np.log(df["gdp_per_capita"])
    return df


def fe_climate_yield(df: pd.DataFrame) -> None:
    """Climate -> yield with two-way FE; show stability with/without GDP."""
    say("=" * 72)
    say("1) TWO-WAY FE: cereal_yield ~ dtr_mean (+temp)  [country + year FE]")
    say("   GDP-robustness: does the climate coefficient survive adding log_gdp?")
    say("=" * 72)
    d = df.dropna(subset=["cereal_yield", "dtr_mean", "temp_mean"]).copy()
    d = d.set_index(["iso3", "year"])
    specs = {
        "no GDP":   "cereal_yield ~ 1 + dtr_mean + temp_mean + EntityEffects + TimeEffects",
        "with GDP": "cereal_yield ~ 1 + dtr_mean + temp_mean + log_gdp + EntityEffects + TimeEffects",
    }
    coefs, ps = {}, {}
    for name, f in specs.items():
        dd = d.dropna(subset=["log_gdp"]) if "with GDP" in name else d
        res = PanelOLS.from_formula(f, dd, drop_absorbed=True).fit(
            cov_type="clustered", cluster_entity=True)
        b, p = res.params.get("dtr_mean", np.nan), res.pvalues.get("dtr_mean", np.nan)
        coefs[name], ps[name] = b, p
        say(f"  [{name:>8}] dtr_mean coef = {b:+.2f}  (p={p:.3f}, n={int(res.nobs)})")
    sig = all(p < 0.05 for p in ps.values())
    if sig and coefs["no GDP"] * coefs["with GDP"] > 0:
        say("  Verdict: significant and same-signed with/without GDP => the climate")
        say("  effect on yields is robust to controlling for national wealth.")
    else:
        say("  Verdict: NOT significant => capital-point mean DTR does not explain")
        say("  yield levels here. Likely needs ag-region/growing-season climate &")
        say("  precipitation, not capital-point annual DTR (see caveats).")
    say("")


def fe_moderation(df: pd.DataFrame) -> None:
    """Risk-model core: does weak governance amplify climate damage to yields?"""
    say("=" * 72)
    say("2) RISK CORE: cereal_yield_irreg ~ dtr_irreg * rule_of_law  [country+year FE]")
    say("=" * 72)
    d = df.dropna(subset=["cereal_yield_irreg", "dtr_irreg", "rule_of_law", "log_gdp"]).copy()
    d = d.set_index(["iso3", "year"])
    res = PanelOLS.from_formula(
        "cereal_yield_irreg ~ 1 + dtr_irreg + rule_of_law + dtr_irreg:rule_of_law "
        "+ log_gdp + EntityEffects + TimeEffects",
        d, drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    say(str(res.summary.tables[1]))
    b = res.params.get("dtr_irreg:rule_of_law", np.nan)
    p = res.pvalues.get("dtr_irreg:rule_of_law", np.nan)
    direction = ("dampens" if b < 0 else "AMPLIFIES (unexpected sign)")
    sig = "significant" if p < 0.05 else "NOT significant (p>=0.05)"
    say(f"  Interaction = {b:+.2f} ({sig}). A negative term = governance dampens")
    say(f"  climate's hit to yield stability; here governance {direction} it.")
    say("")


def iv_yield_health(df: pd.DataFrame) -> None:
    """2SLS: weather instruments cereal_yield to estimate causal yield->health."""
    say("=" * 72)
    say("3) IV/2SLS: life_expectancy ~ [cereal_yield ~ dtr_mean + temp_mean] + log_gdp")
    say("   (year dummies; weather as exogenous instrument for agriculture)")
    say("=" * 72)
    d = df.dropna(subset=["life_expectancy", "cereal_yield", "dtr_mean",
                          "temp_mean", "log_gdp"]).copy()
    d["year"] = d["year"].astype("category")
    res = IV2SLS.from_formula(
        "life_expectancy ~ 1 + log_gdp + C(year) "
        "+ [cereal_yield ~ dtr_mean + temp_mean]", d).fit(cov_type="robust")
    b = res.params["cereal_yield"]; p = res.pvalues["cereal_yield"]
    say(f"  2SLS cereal_yield -> life_expectancy: coef={b:+.5f} (p={p:.3f}, n={int(res.nobs)})")
    fs = res.first_stage.diagnostics
    say("  First-stage instrument strength (F should be >> 10 to avoid weak IV):")
    say(fs[["f.stat", "f.pval"]].round(2).to_string())
    say("  CAVEAT: weather (temp especially) plausibly affects health through")
    say("  channels OTHER than crop yield (heat mortality, disease) -> the")
    say("  exclusion restriction is likely VIOLATED, so this 2SLS coefficient is")
    say("  illustrative, not a credible causal estimate. A defensible instrument")
    say("  would shift agriculture without directly touching health.")
    say("")


def main() -> None:
    df = load()
    if "dtr_mean" not in df.columns or df["dtr_mean"].notna().sum() == 0:
        say("[error] No country climate data in panel. Run build_panel.py after "
            "fetch_climate_country.py completes.")
    else:
        fe_climate_yield(df)
        fe_moderation(df)
        iv_yield_health(df)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(_lines))
    print(f"\nReport written to {REPORT}")


if __name__ == "__main__":
    main()
