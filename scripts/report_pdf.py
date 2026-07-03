"""Render a sendable one to two page ClosureIQ PDF for a single operator.

Reuses the analysis logic from analyze_operator so the PDF and the markdown never
diverge. Usage: python3 report_pdf.py "AlphaBow"
"""
import sys
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable, KeepTogether)

from lib import load_inactive, COST_BANDS, COST_FLOOR, ABANDON_COST, RECLAIM_COST, DISCLAIMER
from analyze_operator import priority_score, closure_class, AS_OF, SOURCE
from optimize_closure import optimize, greedy_plan, summarize, VARIABLE_COST, MOBILIZATION

# Illustrative annual closure budget for the optimized-plan section (labelled estimate).
OPT_BUDGET = 20_000_000

# palette
INK    = HexColor("#1b2432")
ACCENT = HexColor("#b5561f")
MUTED  = HexColor("#6b7280")
LINE   = HexColor("#e5e7eb")
CARD   = HexColor("#f6f5f2")
GOOD   = HexColor("#7a3d12")

def S(name, **kw):
    return ParagraphStyle(name, **kw)

BODY   = S("body", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK)
MUTEDP = S("muted", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED)
H2     = S("h2", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=INK,
           spaceBefore=14, spaceAfter=5)
STATNUM= S("statnum", fontName="Helvetica-Bold", fontSize=19, leading=21, textColor=ACCENT)
STATLBL= S("statlbl", fontName="Helvetica", fontSize=7.5, leading=9.5, textColor=MUTED)
CALL   = S("call", fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK)

def m(x):      return f"${x:,.0f}"
def millions(x): return f"${x/1e6:,.0f}M"


def compute(name_substr):
    df = load_inactive(AS_OF)
    op = df[df["Licensee Name"].str.contains(name_substr, case=False, na=False)].copy()
    if op.empty:
        sys.exit(f"No wells found for '{name_substr}'")
    op["score"] = priority_score(op)
    op["closure_class"] = closure_class(op)
    n = len(op)
    cls = op["closure_class"].value_counts()
    d = dict(
        op=op, n=n,
        licensee=op["Licensee Name"].mode().iat[0],
        ba=", ".join(sorted(op["BA Code"].unique())),
        noncomp=int(op["Directive 13 Compliance Status"].eq("Non Compliant").sum()),
        near=int(cls.get("near-certain closure", 0)),
        watch=int(cls.get("watch / uncertain", 0)),
        react=int(cls.get("possibly reactivatable", 0)),
        overdue=int(op["inspection_overdue"].sum()),
        not_reported=int(op["AER Deemed Risk Class"].eq("Not Reported").sum()),
        geo=op["AER Field Centre"].value_counts().head(6),
    )
    return d


def stat_card(num, label):
    inner = Table([[Paragraph(num, STATNUM)], [Paragraph(label, STATLBL)]],
                  colWidths=[1.55*inch])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), CARD),
        ("LEFTPADDING", (0,0), (-1,-1), 9), ("RIGHTPADDING", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (0,0), 9), ("BOTTOMPADDING", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,1), (0,1), 0),
        ("LINEBELOW", (0,0), (-1,-1), 2, ACCENT),
    ]))
    return inner


def build(name_substr):
    d = compute(name_substr)
    n, near = d["n"], d["near"]
    low  = COST_BANDS["low (OWA floor, 1x)"]
    base = COST_BANDS["base (~3x actuals)"]
    high = COST_BANDS["high (~5x actuals)"]

    out = Path(__file__).resolve().parent.parent / "output" / f"{d['ba'].replace(', ','_')}_closure_report.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=LETTER,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.6*inch, bottomMargin=0.6*inch,
                            title=f"ClosureIQ — {d['licensee']}")
    E = []

    # header band
    hdr = Table([[Paragraph('Closure<font color="#b5561f">IQ</font>',
                            S("wm", fontName="Helvetica-Bold", fontSize=17, leading=20, textColor=colors.white)),
                  Paragraph("Alberta Closure Liability Analysis",
                            S("wmr", fontName="Helvetica", fontSize=9, textColor=HexColor("#c9ccd3"),
                              alignment=TA_RIGHT))]],
                colWidths=[3.3*inch, 3.8*inch])
    hdr.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), INK),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (0,0), 12), ("RIGHTPADDING", (-1,0), (-1,0), 12),
        ("TOPPADDING", (0,0), (-1,-1), 10), ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    E += [hdr, Spacer(1, 12)]

    E += [Paragraph(f"{d['licensee']}", S("title", fontName="Helvetica-Bold", fontSize=16,
                                          leading=20, spaceAfter=4, textColor=INK)),
          Paragraph(f"BA Code {d['ba']} &nbsp;·&nbsp; {n:,} inactive wells &nbsp;·&nbsp; as of {AS_OF}", MUTEDP),
          Spacer(1, 4),
          Paragraph(f"<i>{DISCLAIMER}</i>", MUTEDP),
          Spacer(1, 10)]

    # stat cards
    cards = Table([[stat_card(f"{d['noncomp']/n:.0%}", "Directive 013 non-compliant"),
                    stat_card(f"{near:,}", "Near-certain closures"),
                    stat_card(f"{d['overdue']:,}", "Inspections overdue"),
                    stat_card(millions(base*n), "Est. liability (base case)")]],
                  colWidths=[1.72*inch]*4)
    cards.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),4),
                               ("TOPPADDING",(0,0),(-1,-1),0),("BOTTOMPADDING",(0,0),(-1,-1),0)]))
    E += [cards, Spacer(1, 6)]

    # liability table
    E += [Paragraph("Estimated closure liability", H2),
          Paragraph(f"Per well = abandonment {m(ABANDON_COST)} + reclamation {m(RECLAIM_COST)} = "
                    f"{m(COST_FLOOR)} floor (Orphan Well Association 2023/24). Documented Alberta "
                    "actuals run 2 to 5 times the floor, so liability is shown as a band, not a "
                    "single figure.", BODY)]
    lt = [["Assumption", "Per well", "All inactive wells", "Near-certain only"]]
    for label, per in COST_BANDS.items():
        lt.append([label, m(per), m(per*n), m(per*near)])
    lt_tbl = Table(lt, colWidths=[1.9*inch, 1.2*inch, 1.9*inch, 1.7*inch])
    lt_tbl.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), "Helvetica-Bold", 8.5),
        ("FONT", (0,1), (-1,-1), "Helvetica", 8.5),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("BACKGROUND", (0,0), (-1,0), INK),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, CARD]),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("LINEBELOW", (0,0), (-1,-1), 0.4, LINE),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
    ]))
    E += [Spacer(1,4), lt_tbl]

    # likelihood split
    E += [Paragraph("Closure exposure by likelihood", H2),
          Paragraph("Inactive is not the same as must-abandon. Wells are split so the estimate is "
                    "honest about which are genuinely closure-bound.", BODY)]
    split = Table([["Near-certain closure", "Watch / uncertain", "Possibly reactivatable"],
                   [f"{near:,}", f"{d['watch']:,}", f"{d['react']:,}"]],
                  colWidths=[2.33*inch]*3)
    split.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica",8), ("TEXTCOLOR",(0,0),(-1,0),MUTED),
        ("FONT",(0,1),(-1,1),"Helvetica-Bold",15), ("TEXTCOLOR",(0,1),(-1,1),INK),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("BACKGROUND",(0,0),(-1,-1),CARD),
        ("LINEBELOW",(0,1),(0,1),2,ACCENT),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),8),
        ("LINEAFTER",(0,0),(-2,-1),4,colors.white),
    ]))
    E += [Spacer(1,4), split]

    # consolidator insight callout
    top_centre = d["geo"].index[0].title()
    top_share = d["geo"].iloc[0] / d["n"]
    noncomp_share = d["noncomp"] / d["n"]
    posture = ("a compliance profile that is already under regulatory pressure"
               if noncomp_share >= 0.5 else "a largely compliant inactive inventory")
    insight = Paragraph(
        f"<b>What the data shows:</b> this operator holds {posture} ({noncomp_share:.0%} of "
        f"inactive wells Directive 013 non-compliant), and the inventory concentrates "
        f"geographically, with {top_share:.0%} of wells in the {top_centre} field centre and most "
        "of the rest in a few others. That clustering is where cost savings hide: closure crews can "
        "mobilise once per area and batch nearby wells. Closing in the right order and geography is "
        "a materially cheaper path to the same quota than working the list one well at a time.", CALL)
    callout = Table([[insight]], colWidths=[7.0*inch])
    callout.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),HexColor("#faf3ec")),
        ("LINEBEFORE",(0,0),(0,-1),3,ACCENT),
        ("LEFTPADDING",(0,0),(-1,-1),12),("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),9),
    ]))
    E += [Spacer(1,10), callout]

    # geography
    E += [Paragraph("Where the wells are", H2)]
    geo_rows = [[c.title(), f"{int(v):,}"] for c, v in d["geo"].items()]
    geo_tbl = Table(geo_rows, colWidths=[2.2*inch, 0.9*inch])
    geo_tbl.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",9),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("LINEBELOW",(0,0),(-1,-1),0.4,LINE),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    E += [geo_tbl]

    # optimized closure plan (the batching payoff, computed by the OR-Tools optimizer)
    wells = d["op"].rename(columns={"score": "value", "AER Field Centre": "area"})[["value", "area"]].copy()
    wells["cost"] = VARIABLE_COST
    opt_plan, _, _ = optimize(wells, OPT_BUDGET)
    naive_plan = greedy_plan(wells, OPT_BUDGET)
    ov, os_, oa = summarize(opt_plan)
    gv, gs, ga = summarize(naive_plan)

    E += [Paragraph("Optimized closure plan", H2),
          Paragraph(f"For an illustrative {millions(OPT_BUDGET)} annual closure budget, at "
                    f"{m(VARIABLE_COST)} per well plus a {m(MOBILIZATION)} mobilization per field "
                    "area (labelled estimates), ClosureIQ selects the wells that retire the most risk "
                    "per dollar. Batching closures into fewer areas stretches the same budget further "
                    "than working straight down the priority list.", BODY)]
    ot = [["Approach", "Wells closed", "Areas", "Risk retired", "Budget used"],
          ["Straight down the list", f"{len(naive_plan):,}", f"{ga}", f"{gv:,}", m(gs)],
          ["ClosureIQ optimizer (batched)", f"{len(opt_plan):,}", f"{oa}", f"{ov:,}", m(os_)]]
    ot_tbl = Table(ot, colWidths=[2.5*inch, 1.2*inch, 0.7*inch, 1.2*inch, 1.4*inch])
    ot_tbl.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), "Helvetica-Bold", 8.5),
        ("FONT", (0,1), (-1,-1), "Helvetica", 8.5),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("BACKGROUND", (0,0), (-1,0), INK),
        ("BACKGROUND", (0,2), (-1,2), HexColor("#faf3ec")),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("LINEBELOW", (0,0), (-1,-1), 0.4, LINE),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
    ]))
    E += [Spacer(1,4), ot_tbl]
    if gv > 0 and ov > gv:
        E += [Spacer(1,3),
              Paragraph(f"Same budget: {ov-gv:,} more risk-points retired and "
                        f"{len(opt_plan)-len(naive_plan):,} more wells closed by batching into "
                        f"{oa} area{'s' if oa != 1 else ''} instead of {ga}.", MUTEDP)]

    # first prioritised list
    E += [Paragraph("First prioritised closure list", H2),
          Paragraph("Ranked by the ClosureIQ priority score (our methodology, not an AER ranking): "
                    "Directive 013 non-compliant +3; AER deemed risk High +3 / Medium +2 / Low +1; "
                    "dormant over 10 years +2, over 5 years +1; inspection overdue +1.", MUTEDP)]
    cols = ["Well Licence Number","AER Field Centre","AER Deemed Risk Class",
            "Directive 13 Compliance Status","yrs_dormant","score"]
    rows = [["Licence","Field centre","Risk","D013","Yrs dormant","Score"]]
    for _, r in d["op"].sort_values(["score","yrs_dormant"], ascending=False).head(10)[cols].iterrows():
        rows.append([str(r["Well Licence Number"]), r["AER Field Centre"].title(),
                     r["AER Deemed Risk Class"], r["Directive 13 Compliance Status"],
                     str(r["yrs_dormant"]), str(int(r["score"]))])
    ptbl = Table(rows, colWidths=[0.95*inch,1.5*inch,0.85*inch,1.35*inch,1.0*inch,0.6*inch])
    ptbl.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",8), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("BACKGROUND",(0,0),(-1,0),INK),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, CARD]),
        ("ALIGN",(4,0),(-1,-1),"CENTER"),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    E += [Spacer(1,4), ptbl]

    # footer
    E += [Spacer(1,12), HRFlowable(width="100%", thickness=0.5, color=LINE), Spacer(1,4),
          Paragraph(f"Source: {SOURCE}", MUTEDP),
          Paragraph("ClosureIQ · independent analysis from public data · not affiliated with or "
                    "endorsed by the Alberta Energy Regulator.", MUTEDP)]

    doc.build(E)
    print(f"[written to {out}]")
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "AlphaBow")
