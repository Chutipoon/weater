"""Single source of truth for the weater pipeline.

Plain-Python config (no YAML dependency). Edit indicator codes / scope here.
"""

# --- Scope -------------------------------------------------------------------
YEAR_START = 1996          # WGI governance data starts in 1996
YEAR_END = 2022
YEARS = list(range(YEAR_START, YEAR_END + 1))

# --- World Bank indicators (country-year) ------------------------------------
# code -> short column name used throughout the panel.
WB_INDICATORS = {
    # Governance ("rulers / officials / citizens in dhamma")
    "GOV_WGI_RL.EST": "rule_of_law",
    "GOV_WGI_CC.EST": "control_corruption",
    "GOV_WGI_GE.EST": "gov_effectiveness",
    "GOV_WGI_VA.EST": "voice_accountability",
    # Crops ("ripen unevenly")
    "AG.YLD.CREL.KG": "cereal_yield",
    # Health (short-lived / weak / diseased)
    "SP.DYN.LE00.IN": "life_expectancy",
    "SH.DYN.MORT": "under5_mortality",
    "SH.STA.STNT.ZS": "child_stunting",
    "SN.ITK.DEFC.ZS": "undernourishment",
    # Upstream behavioural driver + confounders
    "EN.GHG.CO2.PC.CE.AR5": "co2_per_capita",   # consumption/behaviour proxy
    "NY.GDP.PCAP.KD": "gdp_per_capita",
    "SP.POP.TOTL": "population",
}

# Indicator groups, used to label the cascade in analysis/plots.
CHAIN_GROUPS = {
    "governance": ["rule_of_law", "control_corruption", "gov_effectiveness", "voice_accountability"],
    "driver": ["co2_per_capita"],
    "crops": ["cereal_yield"],
    "health": ["life_expectancy", "under5_mortality", "child_stunting", "undernourishment"],
    "control": ["gdp_per_capita", "population"],
}

# --- Astronomical / temporal sources (mostly global-annual) -------------------
# Node E (seasons/years): ENSO Oceanic Nino Index, monthly anomaly ascii.
ENSO_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
# Node A (sun): SILSO yearly mean total sunspot number, semicolon CSV.
SUNSPOT_URL = "https://www.silso.be/datafiles/SN_y_tot_V2.0.csv"

# --- Paths -------------------------------------------------------------------
import os
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(ROOT, "outputs")
PANEL_CSV = os.path.join(DATA_DIR, "panel.csv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
