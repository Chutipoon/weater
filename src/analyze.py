"""Analyse the cascade relationships in the panel.

Outputs printed tables + outputs/regression_report.txt. Each block maps to a
link in the reframed Adhammika cascade. Read the caveats in docs/research_design.md
before interpreting: governance is sticky (FE may wash it out), correlations are
confounded by development level, and several astro signals are global-annual.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

REPORT = os.path.join(config.OUT_DIR, "regression_report.txt")
_lines: list[str] = []


def say(s: str = "") -> None:
    print(s)
    _lines.append(s)


def load() -> pd.DataFrame:
    df = pd.read_csv(config.PANEL_CSV)
    df["log_gdp"] = np.log(df["gdp_per_capita"])
    df["log_pop"] = np.log(df["population"])
    return df


def sanity_check(df: pd.DataFrame) -> None:
    """Merge validation only -- NOT evidence for the sutta (see caveats)."""
    say("=" * 70)
    say("MERGE SANITY CHECK (validates joins, not the hypothesis)")
    say("=" * 70)
    expect = {"life_expectancy": "+", "cereal_yield": "+", "under5_mortality": "-"}
    for col, sign in expect.items():
        r = df[["rule_of_law", col]].corr().iloc[0, 1]
        ok = "OK" if (r > 0) == (sign == "+") else "!! UNEXPECTED SIGN"
        say(f"  corr(rule_of_law, {col:<16}) = {r:+.3f}  expect {sign}  [{ok}]")
    say("")


def correlations(df: pd.DataFrame) -> None:
    say("=" * 70)
    say("CASCADE CO-MOVEMENT (pooled correlations across nodes)")
    say("=" * 70)
    cols = ["rule_of_law", "co2_per_capita", "enso_amplitude",
            "cereal_yield_irreg", "cereal_yield", "life_expectancy",
            "under5_mortality"]
    corr = df[cols].corr()
    say(corr.round(2).to_string())
    say("")


def panel_fe(df: pd.DataFrame) -> None:
    """Downstream link health ~ crops, with two-way FE + clustered SEs."""
    say("=" * 70)
    say("DOWNSTREAM: life_expectancy ~ cereal_yield  (country+year FE)")
    say("=" * 70)
    d = df.dropna(subset=["life_expectancy", "cereal_yield", "log_gdp"]).copy()
    d = d.set_index(["iso3", "year"])
    res = PanelOLS.from_formula(
        "life_expectancy ~ 1 + cereal_yield + log_gdp + EntityEffects + TimeEffects",
        d, drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    say(str(res.summary.tables[1]))
    say("")


def moderation(df: pd.DataFrame) -> None:
    """Core reframed claim: does governance BUFFER ENSO's effect on yield
    instability? Interaction enso_amplitude x rule_of_law. EntityEffects only
    (no TimeEffects) so the year-global ENSO signal stays identified."""
    say("=" * 70)
    say("MODERATION: cereal_yield_irreg ~ enso_amplitude * rule_of_law  (country FE)")
    say("=" * 70)
    d = df.dropna(subset=["cereal_yield_irreg", "enso_amplitude",
                          "rule_of_law", "log_gdp"]).copy()
    d = d.set_index(["iso3", "year"])
    res = PanelOLS.from_formula(
        "cereal_yield_irreg ~ 1 + enso_amplitude + rule_of_law "
        "+ enso_amplitude:rule_of_law + log_gdp + EntityEffects",
        d, drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    say(str(res.summary.tables[1]))
    say("  Interpretation: a negative interaction term = better governance")
    say("  dampens how much ENSO swings translate into yield instability.")
    say("")


def between_effects(df: pd.DataFrame) -> None:
    """Addresses the FE-washout caveat: governance barely moves within a country,
    so test its CROSS-COUNTRY variation on country-mean outcomes."""
    say("=" * 70)
    say("BETWEEN-COUNTRY: mean life_expectancy ~ mean rule_of_law + mean log_gdp")
    say("=" * 70)
    m = (df.groupby("iso3")[["life_expectancy", "rule_of_law", "log_gdp"]]
           .mean().dropna())
    res = smf.ols("life_expectancy ~ rule_of_law + log_gdp", data=m).fit()
    say(res.summary().tables[1].as_text())
    say(f"  n countries = {int(res.nobs)},  R^2 = {res.rsquared:.3f}")
    say("")


def main() -> None:
    df = load()
    sanity_check(df)
    correlations(df)
    panel_fe(df)
    moderation(df)
    between_effects(df)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(_lines))
    print(f"\nFull report written to {REPORT}")


if __name__ == "__main__":
    main()
