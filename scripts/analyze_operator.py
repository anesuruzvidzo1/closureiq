"""ClosureIQ step 1: closure exposure analysis for one operator, from public AER data.

Writes a markdown report to output/. The five credibility must-fixes are baked in:
  1. Splits near-certain closures from possibly reactivatable wells
     (inactive is not the same as must-abandon).
  2. The priority score is our published methodology, not an AER ranking.
  3. Stamps the as-of date and the data source.
  4. Carries the independent-estimate disclaimer.
  5. Treats per well cost as a labelled band, never a precise figure.

Usage: python3 analyze_operator.py "AlphaBow"
"""
import sys
from datetime import date
from lib import load_inactive, COST_BANDS, COST_FLOOR, DISCLAIMER

AS_OF = "2026-07-01"
SOURCE = ("AER Inactive Well Licence List (report created 2026-06-30, "
          "Petrinex data valid to 2026-05-31); OWA Fiscal Responsibility 2023/24; "
          "AER Directive 011 (Aug 2025).")

# Priority weights. This is OUR methodology, stated openly (must-fix #2).
RISK_PTS = {"High": 3, "Medium": 2, "Low": 1, "Not Reported": 0, "nan": 0}
WEIGHTS_NOTE = ("Priority score (ClosureIQ methodology, not an AER ranking): "
                "Directive 013 non-compliant +3; AER deemed risk High +3 / Medium +2 / "
                "Low +1; dormant over 10 years +2, over 5 years +1; inspection overdue +1.")


def priority_score(op):
    s = op["Directive 13 Compliance Status"].eq("Non Compliant").astype(int) * 3
    s += op["AER Deemed Risk Class"].map(RISK_PTS).fillna(0)
    s += op["yrs_dormant"].apply(lambda x: 2 if x > 10 else (1 if x > 5 else 0))
    s += op["inspection_overdue"].astype(int)
    return s


def closure_class(op):
    """Must-fix #1: inactive is not the same as must-abandon."""
    noncomp = op["Directive 13 Compliance Status"].eq("Non Compliant")
    near_certain = noncomp & (op["yrs_dormant"] > 10)
    reactivatable = op["yrs_dormant"] <= 5
    label = op.index.to_series().map(lambda _: "watch / uncertain")
    label[reactivatable] = "possibly reactivatable"
    label[near_certain] = "near-certain closure"
    return label


def money(x):
    return f"${x:,.0f}"


def build_report(name_substr):
    df = load_inactive(AS_OF)
    op = df[df["Licensee Name"].str.contains(name_substr, case=False, na=False)].copy()
    if op.empty:
        sys.exit(f"No wells found for '{name_substr}'")
    op["score"] = priority_score(op)
    op["closure_class"] = closure_class(op)

    n = len(op)
    licensee = op["Licensee Name"].mode().iat[0]
    ba = ", ".join(sorted(op["BA Code"].unique()))
    classes = op["closure_class"].value_counts()
    near_n = int(classes.get("near-certain closure", 0))
    noncomp_n = int(op["Directive 13 Compliance Status"].eq("Non Compliant").sum())
    not_reported_n = int(op["AER Deemed Risk Class"].eq("Not Reported").sum())
    overdue_n = int(op["inspection_overdue"].sum())

    L = []
    L.append(f"# Closure Exposure Snapshot: {licensee}")
    L.append(f"BA Code {ba}  |  {n:,} inactive wells  |  as of {AS_OF}")
    L.append("")
    L.append(f"_{DISCLAIMER}_")
    L.append(f"\nSource: {SOURCE}")

    L.append("\n## Headline")
    L.append(f"- {noncomp_n:,} of {n:,} inactive wells ({noncomp_n/n:.0%}) are Directive 013 non-compliant.")
    L.append(f"- {near_n:,} wells are near-certain closures (non-compliant and dormant over 10 years).")
    L.append(f"- {overdue_n:,} wells are overdue for inspection.")

    L.append("\n## Closure exposure by likelihood (inactive is not the same as must-abandon)")
    for cls in ["near-certain closure", "watch / uncertain", "possibly reactivatable"]:
        L.append(f"- {cls}: {int(classes.get(cls, 0)):,}")

    L.append("\n## Estimated closure liability (labelled estimate, range not precise figure)")
    L.append(f"Per well = abandonment ${16500:,} + reclamation ${27400:,} = ${COST_FLOOR:,} floor "
             "(OWA 2023/24). Actuals run 2 to 5 times the floor, so we report a band.")
    L.append("")
    L.append("| Assumption | Per well | All inactive wells | Near-certain closures only |")
    L.append("|---|---|---|---|")
    for label, per in COST_BANDS.items():
        L.append(f"| {label} | {money(per)} | {money(per*n)} | {money(per*near_n)} |")

    L.append("\n## AER deemed risk mix")
    for cls, cnt in op["AER Deemed Risk Class"].value_counts().items():
        L.append(f"- {cls}: {int(cnt):,}")
    L.append(f"\n_Data gap: {not_reported_n:,} wells have no reported risk class; "
             "they are scored 0 on risk and may be under-prioritised._")

    L.append("\n## Geography (AER field centres, closure can be batched by area)")
    for centre, cnt in op["AER Field Centre"].value_counts().head(6).items():
        L.append(f"- {centre}: {int(cnt):,}")

    L.append("\n## First prioritised closure list")
    L.append(WEIGHTS_NOTE)
    L.append("")
    L.append("| Licence | Field centre | Risk | D013 | Yrs dormant | Score |")
    L.append("|---|---|---|---|---|---|")
    cols = ["Well Licence Number", "AER Field Centre", "AER Deemed Risk Class",
            "Directive 13 Compliance Status", "yrs_dormant", "score"]
    for _, r in op.sort_values(["score", "yrs_dormant"], ascending=False).head(15)[cols].iterrows():
        L.append(f"| {r['Well Licence Number']} | {r['AER Field Centre']} | "
                 f"{r['AER Deemed Risk Class']} | {r['Directive 13 Compliance Status']} | "
                 f"{r['yrs_dormant']} | {int(r['score'])} |")

    tranche = op[op["score"] >= 7]
    base_per = COST_BANDS["base (~3x actuals)"]
    L.append(f"\nHighest-urgency tranche (score 7+): {len(tranche):,} wells, "
             f"about {money(len(tranche)*base_per)} base-case to close first.")

    return licensee, ba, "\n".join(L)


def main(name_substr):
    licensee, ba, report = build_report(name_substr)
    from pathlib import Path
    out = Path(__file__).resolve().parent.parent / "output" / f"{ba.replace(', ', '_')}_closure_snapshot.md"
    out.write_text(report)
    print(report)
    print(f"\n[written to {out}]")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "AlphaBow")
