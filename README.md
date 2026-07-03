# ClosureIQ

ClosureIQ analyzes Alberta oil and gas closure liability from public AER data. It ranks
operators by their inactive well count, estimates each operator's closure exposure, scores and
prioritises wells, runs an optimizer that picks the closure plan retiring the most risk on a
fixed budget, and renders a sendable PDF report. Every figure traces to a public source.

## Data source

AER Inactive Well Licence List, a free daily Excel file:
https://static.aer.ca/prd/data/codes/Inactive_Well_Licence_List.xlsx

The real header sits on row index 2 (rows 0 and 1 are metadata). As of 2026-06-30 the file
holds 77,869 inactive wells across 817 operators. Readings were cross checked against ST37
(List of Wells in Alberta), a separate AER dataset, and agreed on licensee, status, and vintage.

## What it does

- Ranks operators by inactive well count to surface the largest closure inventories.
- Scores every inactive well by a published priority heuristic (Directive 013 compliance, AER
  deemed risk, dormancy, overdue inspection) and splits wells into near certain closure, watch,
  and possibly reactivatable.
- Estimates closure liability as a labelled low, base, high band from public cost figures.
- Optimizes which wells to close first under a budget, accounting for area batching.
- Renders a branded two page PDF report for a single operator.

## The optimizer

`scripts/optimize_closure.py` solves the closure planning problem with Google OR-Tools
(CP-SAT). It is a binary integer program:

- decision: close each well, yes or no; open each field area, yes or no
- link: a well can only be closed if its field area is opened (mobilized)
- constraint: total spend stays within budget, where spend is a per well field cost plus a one
  time mobilization cost per field area (area batching)
- objective: maximize the total risk retired

Because mobilization is a shared cost per area, closing a cluster of wells is cheaper per well
than closing scattered ones. The optimizer exploits that, so it beats a naive sort by priority
score: on InPlay Oil at a 20 million dollar budget it retires more risk and closes more wells
by batching closures into fewer areas. The script prints the naive baseline next to the
optimized plan so the difference is visible.

## The report

`scripts/report_pdf.py` renders a sendable two page PDF for one operator: headline stats, the
liability band, the closure likelihood split, geography, the optimized closure plan, and a
prioritised well list, with the data source and an independent estimate disclaimer.

## Cost basis (labelled estimates)

Per well closure = abandonment 16,500 plus reclamation 27,400 = 43,900 floor (Orphan Well
Association 2023/24 averages). Documented Alberta actuals run 2 to 5 times the floor, so cost is
always reported as a low, base, high band, never a single precise figure. The optimizer splits
cost into a per well field cost plus a per area mobilization, both labelled tunable estimates.

## Layout

- data/ raw AER files (gitignored, refetchable)
- scripts/lib.py load and clean the file, plus the public cost figures
- scripts/operator_targetlist.py rank operators by inactive well count
- scripts/analyze_operator.py closure exposure snapshot for one operator
- scripts/optimize_closure.py OR-Tools closure optimizer
- scripts/report_pdf.py branded PDF report generator
- output/ generated snapshots and reports (gitignored)

## Run

    pip3 install -r requirements.txt

    python3 scripts/operator_targetlist.py 25
    python3 scripts/analyze_operator.py "InPlay"
    python3 scripts/optimize_closure.py "InPlay" 20000000
    python3 scripts/report_pdf.py "InPlay"

## Honesty rules baked into the output

- Inactive is not the same as must abandon. Wells are split into near certain closure, watch,
  and possibly reactivatable.
- The priority score is ClosureIQ methodology, stated openly, not an AER ranking.
- All numbers are independent estimates from public data, not endorsed by the AER and not any
  operator's actual or confidential figures.
