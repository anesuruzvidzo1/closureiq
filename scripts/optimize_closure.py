"""ClosureIQ optimizer: pick the closure plan that retires the most risk on budget.

Each inactive well has:
  - value: how much risk/liability closing it retires (the priority score)
  - cost:  a per-well variable field cost, plus a one-time mobilization cost
           paid once per field area a crew is sent to (area batching)

The optimizer is a fixed-charge integer program solved with OR-Tools CP-SAT:
  decision:   close[i] in {0,1} per well, used[a] in {0,1} per field area
  link:       close[i] <= used[area_of_i]      (closing a well 'opens' its area)
  constraint: sum(variable*close) + sum(mobilization*used) <= budget
  objective:  maximize sum(value*close)         (total risk retired)

We also print a naive 'sort by score' baseline so the batching payoff is visible.

Usage: python3 optimize_closure.py "InPlay" 20000000
       (operator name substring, then the closure budget in dollars)
"""
import sys

import pandas as pd
from ortools.sat.python import cp_model

from lib import load_inactive
from analyze_operator import priority_score, closure_class, AS_OF

# Closure cost has two parts (both labelled, illustrative, tunable estimates):
#   VARIABLE_COST  per well  -> the field work on that specific well
#   MOBILIZATION   per area  -> paid ONCE per field area a crew is sent to
# The mobilization is why closing a cluster of wells is cheaper per well than
# closing scattered ones, and it is the structure the optimizer exploits.
VARIABLE_COST = 110_000
MOBILIZATION = 400_000


def prepare(name_substr):
    """Return (licensee_name, per-well table) for one operator."""
    df = load_inactive(AS_OF)
    op = df[df["Licensee Name"].str.contains(name_substr, case=False, na=False)].copy()
    if op.empty:
        sys.exit(f"No wells found for '{name_substr}'")

    op["value"] = priority_score(op)          # risk retired if we close this well
    op["closure_class"] = closure_class(op)
    op["cost"] = VARIABLE_COST                 # per-well variable cost (mobilization is per area)

    wells = op[["Well Licence Number", "AER Field Centre", "closure_class",
                "value", "cost"]].reset_index(drop=True)
    wells.columns = ["licence", "area", "closure_class", "value", "cost"]
    return op["Licensee Name"].mode().iat[0], wells


def optimize(wells, budget):
    """Pick the wells that retire the most risk on budget, accounting for area batching.

    Returns (chosen rows, solver, status).
    """
    model = cp_model.CpModel()
    n = len(wells)
    areas = sorted(wells["area"].unique())
    area_of = {a: k for k, a in enumerate(areas)}

    close = [model.NewBoolVar(f"close_{i}") for i in range(n)]          # per well
    used = [model.NewBoolVar(f"used_{k}") for k in range(len(areas))]   # per field area

    values = wells["value"].tolist()
    well_area = [area_of[a] for a in wells["area"].tolist()]

    # Link: a well can only be closed if its field area has been opened (mobilized).
    for i in range(n):
        model.Add(close[i] <= used[well_area[i]])

    # Budget: per-well field work + one mobilization per opened area.
    model.Add(
        sum(VARIABLE_COST * close[i] for i in range(n))
        + sum(MOBILIZATION * used[k] for k in range(len(areas)))
        <= budget
    )

    # Objective: retire as much risk/liability as the budget allows.
    model.Maximize(sum(values[i] * close[i] for i in range(n)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20     # safety cap; trivial at this size
    status = solver.Solve(model)

    chosen_idx = [i for i in range(n) if solver.Value(close[i]) == 1]
    return wells.iloc[chosen_idx].copy(), solver, status


def greedy_plan(wells, budget):
    """Naive baseline: close wells in strict priority order, batching opportunistically.

    This is what 'sort by score and start closing' looks like once mobilization is
    real. It obeys score order, so it can waste budget opening an area for a single
    high-score well.
    """
    chosen, spent, opened = [], 0, set()
    for _, w in wells.sort_values("value", ascending=False).iterrows():
        extra = VARIABLE_COST + (0 if w["area"] in opened else MOBILIZATION)
        if spent + extra <= budget:
            chosen.append(w)
            spent += extra
            opened.add(w["area"])
    return pd.DataFrame(chosen)


def summarize(plan):
    """Return (risk retired, spend, areas touched) for a plan under the batching cost model."""
    if len(plan) == 0:
        return 0, 0, 0
    areas = plan["area"].nunique()
    spend = len(plan) * VARIABLE_COST + areas * MOBILIZATION
    return int(plan["value"].sum()), spend, areas


def main(name, budget):
    licensee, wells = prepare(name)

    opt, solver, status = optimize(wells, budget)
    greedy = greedy_plan(wells, budget)
    ov, os_, oa = summarize(opt)
    gv, gs, ga = summarize(greedy)

    print(f"Operator: {licensee}")
    print(f"Inactive wells considered: {len(wells):,}")
    print(f"Budget: ${budget:,}")
    print(f"Cost model: ${VARIABLE_COST:,}/well + ${MOBILIZATION:,} mobilization per area "
          "(labelled estimates)")
    print(f"Solver status: {solver.StatusName(status)}")
    print()
    print("Naive (sort by score):")
    print(f"  {len(greedy):,} wells | {ga} areas | risk retired {gv:,} | spend ${gs:,}")
    print("Optimizer (batching-aware):")
    print(f"  {len(opt):,} wells | {oa} areas | risk retired {ov:,} | spend ${os_:,}")
    print()
    if gv > 0:
        print(f"Same budget: the optimizer retires {ov - gv:,} more risk-points "
              f"({(ov - gv) / gv:+.0%}) and closes {len(opt) - len(greedy):+,} more wells.")
    print("\nTop of the optimizer's closure plan:")
    cols = ["licence", "area", "closure_class", "value", "cost"]
    print(opt.sort_values("value", ascending=False).head(12)[cols].to_string(index=False))


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "InPlay"
    budget = int(sys.argv[2]) if len(sys.argv) > 2 else 20_000_000
    main(name, budget)
