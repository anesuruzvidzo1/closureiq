"""Shared helpers for ClosureIQ step 1.

Loads and cleans the AER Inactive Well Licence List, and holds the public
cost figures used across scripts. Every cost number here is a labelled
estimate drawn from public sources (see README).
"""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data" / "Inactive_Well_Licence_List.xlsx"

# Public per well closure cost figures (Orphan Well Association 2023/24 averages).
ABANDON_COST = 16_500          # average well decommissioning (downhole plugging)
RECLAIM_COST = 27_400          # average site reclamation (surface)
COST_FLOOR = ABANDON_COST + RECLAIM_COST            # 43,900 clean at scale floor

# Documented Alberta actuals run 2 to 5 times the floor, so we report a band.
COST_BANDS = {"low (OWA floor, 1x)": COST_FLOOR,
              "base (~3x actuals)": COST_FLOOR * 3,
              "high (~5x actuals)": COST_FLOOR * 5}

DISCLAIMER = (
    "Independent estimate built from public AER and Orphan Well Association data. "
    "Not endorsed by the AER and not the operator's actual or confidential figures. "
    "Closure costs are estimates only and vary widely by well depth, type, and site."
)

_TEXT_COLS = ["BA Code", "Licensee Name", "Licence Status", "AER Field Centre",
              "AER Deemed Risk Class", "Directive 13 Compliance Status"]


def load_inactive(as_of="2026-07-01"):
    """Return the cleaned inactive well table with derived dormancy and inspection flags.

    The real header sits on row index 2 (rows 0 and 1 are metadata). BA Code
    carries a stray leading tab that we strip.
    """
    df = pd.read_excel(DATA, sheet_name=0, header=2)
    df.columns = [str(c).strip() for c in df.columns]
    for c in _TEXT_COLS:
        df[c] = df[c].astype(str).str.strip()
    now = pd.Timestamp(as_of)
    last_vol = pd.to_datetime(df["Last Volumetric Activity Date"], errors="coerce")
    df["yrs_dormant"] = ((now - last_vol).dt.days / 365.25).round(1)
    next_insp = pd.to_datetime(df["Next Inspection Due Date"], errors="coerce")
    df["inspection_overdue"] = next_insp < now
    return df
