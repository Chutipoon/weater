"""Figures for the cascade analysis. Saves PNGs to outputs/."""
from __future__ import annotations

import os
import sys

import matplotlib
matplotlib.use("Agg")          # headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def _save(fig, name: str) -> None:
    path = os.path.join(config.OUT_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"  wrote {path}")


def plot_enso(df: pd.DataFrame) -> None:
    """Node E: 'seasons & years rotate irregularly' as annual ENSO amplitude."""
    s = df.groupby("year")["enso_amplitude"].first()
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.bar(s.index, s.values, color="#c44")
    ax.set_title("Node E — interannual irregularity (ENSO amplitude per year)")
    ax.set_xlabel("year"); ax.set_ylabel("mean |ONI anomaly|")
    _save(fig, "node_E_enso.png")


def plot_heatmap(df: pd.DataFrame) -> None:
    cols = ["rule_of_law", "co2_per_capita", "enso_amplitude",
            "cereal_yield_irreg", "cereal_yield", "life_expectancy",
            "under5_mortality"]
    corr = df[cols].corr().values
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=45, ha="right")
    ax.set_yticks(range(len(cols))); ax.set_yticklabels(cols)
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("Cascade co-movement (pooled correlations)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    _save(fig, "cascade_heatmap.png")


def plot_governance_health(df: pd.DataFrame) -> None:
    """Cross-country: governance vs life expectancy (confounded by GDP -- shown
    as the headline correlation the sutta predicts, caveated in the docs)."""
    m = df.groupby("iso3")[["rule_of_law", "life_expectancy"]].mean().dropna()
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(m["rule_of_law"], m["life_expectancy"], s=14, alpha=0.6)
    b, a = np.polyfit(m["rule_of_law"], m["life_expectancy"], 1)
    xs = np.linspace(m["rule_of_law"].min(), m["rule_of_law"].max(), 50)
    ax.plot(xs, a + b * xs, "r-", lw=2)
    ax.set_xlabel("rule of law (country mean)")
    ax.set_ylabel("life expectancy (country mean)")
    ax.set_title("Governance vs longevity (cross-country)")
    _save(fig, "governance_vs_health.png")


def main() -> None:
    df = pd.read_csv(config.PANEL_CSV)
    plot_enso(df)
    plot_heatmap(df)
    plot_governance_health(df)
    print("Figures done.")


if __name__ == "__main__":
    main()
