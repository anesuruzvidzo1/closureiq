# ClosureIQ

ClosureIQ analyzes Alberta oil and gas closure liability from public AER data. It ranks
operators by their inactive well count, estimates each operator's closure exposure, and
produces a prioritised closure list. Every figure traces to a public source.

## Data source

AER Inactive Well Licence List, a free daily Excel file:
https://static.aer.ca/prd/data/codes/Inactive_Well_Licence_List.xlsx

The real header sits on row index 2 (rows 0 and 1 are metadata). As of 2026-06-30 the file
holds 77,869 inactive wells across 817 operators. Readings were cross checked against ST37
(List of Wells in Alberta), a separate AER dataset, and agreed on licensee, status, and vintage.

## Layout

- data/ raw AER files (gitignored, refetchable)
- scripts/lib.py load and clean the file, plus the public cost figures
- scripts/operator_targetlist.py rank operators by inactive well count (the target list)
- scripts/analyze_operator.py closure exposure snapshot for one operator
- output/ generated snapshots (gitignored)

## Cost basis (labelled estimates)

Per well closure = abandonment 16,500 plus reclamation 27,400 = 43,900 floor
(Orphan Well Association 2023/24 averages). Documented Alberta actuals run 2 to 5 times the
floor, so cost is always reported as a low, base, high band, never a single precise figure.

## Run

    python3 scripts/operator_targetlist.py 25
    python3 scripts/analyze_operator.py "AlphaBow"

## Honesty rules baked into the output

- Inactive is not the same as must abandon. Wells are split into near certain closure, watch,
  and possibly reactivatable.
- The priority score is ClosureIQ methodology, stated openly, not an AER ranking.
- All numbers are independent estimates from public data, not endorsed by the AER and not any
  operator's actual or confidential figures.
