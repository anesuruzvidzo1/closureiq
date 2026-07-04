"""Export precomputed ClosureIQ data for the static web demo.

Runs the existing analysis and the OR-Tools optimizer for a set of operators
across several budget levels, and writes one JSON file the static Next.js app
reads. No live backend: the web demo is fully precomputed.

Operators are ANONYMIZED in the public output (Operator A, B, ...). The real
names live in scripts/operators_local.py, which is gitignored and kept out of
the public repo. Reuses compute() and the optimizer functions so the website
can never disagree with the PDF or the optimizer.

Usage: python3 export_web.py
"""
import json
from pathlib import Path

import pandas as pd

from lib import COST_BANDS, DISCLAIMER
from analyze_operator import AS_OF
from report_pdf import compute
from optimize_closure import optimize, greedy_plan, summarize, VARIABLE_COST, MOBILIZATION

try:
    from operators_local import OPERATORS  # gitignored: real names kept out of the public repo
except ImportError:
    OPERATORS = []  # create scripts/operators_local.py with OPERATORS = [names] to regenerate

BUDGETS = [5_000_000, 10_000_000, 20_000_000, 40_000_000]

OUT = Path(__file__).resolve().parent.parent / "web" / "data" / "operators.json"


def scenario(wells, budget):
    opt, _, _ = optimize(wells, budget)
    naive = greedy_plan(wells, budget)
    ov, os_, oa = summarize(opt)
    gv, gs, ga = summarize(naive)
    return {
        "budget": budget,
        "optimizer": {"wells": len(opt), "areas": oa, "risk": ov, "spend": os_},
        "naive": {"wells": len(naive), "areas": ga, "risk": gv, "spend": gs},
    }


def operator_record(name, label):
    """Build one ANONYMIZED operator record. The real name only queries the data."""
    d = compute(name)
    op = d["op"]
    wells = op.rename(columns={"score": "value", "AER Field Centre": "area"})[["value", "area"]].copy()
    wells["cost"] = VARIABLE_COST
    top = op.sort_values(["score", "yrs_dormant"], ascending=False).head(20).reset_index(drop=True)

    return {
        "name": f"Operator {label}",
        "slug": f"operator-{label.lower()}",
        "n_wells": d["n"],
        "noncompliant_pct": round(d["noncomp"] / d["n"], 3),
        "near_certain": d["near"],
        "watch": d["watch"],
        "reactivatable": d["react"],
        "overdue": d["overdue"],
        "not_reported": d["not_reported"],
        "liability": {
            "low": COST_BANDS["low (OWA floor, 1x)"] * d["n"],
            "base": COST_BANDS["base (~3x actuals)"] * d["n"],
            "high": COST_BANDS["high (~5x actuals)"] * d["n"],
        },
        "geography": [{"area": a.title(), "count": int(c)} for a, c in d["geo"].items()],
        "scenarios": [scenario(wells, b) for b in BUDGETS],
        "top_wells": [
            {
                "licence": f"W{k + 1:03d}",  # synthetic id; real licence numbers are not published
                "area": str(r["AER Field Centre"]).title(),
                "risk": str(r["AER Deemed Risk Class"]),
                "d013": str(r["Directive 13 Compliance Status"]),
                "yrs_dormant": float(r["yrs_dormant"]) if pd.notna(r["yrs_dormant"]) else None,
                "score": int(r["score"]),
            }
            for k, r in top.iterrows()
        ],
    }


def main():
    if not OPERATORS:
        raise SystemExit("No operators. Create scripts/operators_local.py with OPERATORS = [names].")
    records = []
    for i, name in enumerate(OPERATORS):
        label = chr(65 + i)
        try:
            rec = operator_record(name, label)
        except SystemExit:
            print(f"skip: no wells found for '{name}'")
            continue
        records.append(rec)
        print(f"ok: {rec['name']} = {name} ({rec['n_wells']:,} wells)")  # mapping shown locally only

    payload = {
        "generated": AS_OF,
        "cost_model": {"variable": VARIABLE_COST, "mobilization": MOBILIZATION},
        "disclaimer": DISCLAIMER,
        "operators": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\n[wrote {len(records)} operators to {OUT}]")


if __name__ == "__main__":
    main()
