"""C1 pass 3, on the same FSDS zips.

(a) THE STITCH: the one-quarter-lagged deflator has to come from the PRIOR 10-Q.
    How many CIKs that can compute a single-quarter gross profit at Jun-30 also
    have Assets at Mar-31 from the Mar-31 filing?
(b) FISCAL-PHASE SPREAD: within one calendar quarter of 10-Q acceptances, how many
    distinct fiscal-period-end months does the cross-section span?
Negative controls reported beside each count.
"""
import zipfile, io, csv, json
from collections import defaultdict, Counter

ERAS = [("2013", "C1_fsds_2013q3.zip", "20130630", "C1_fsds_2013q2.zip", "20130331"),
        ("2019", "C1_fsds_2019q3.zip", "20190630", "C1_fsds_2019q2.zip", "20190331"),
        ("2025", "C1_fsds_2025q3.zip", "20250630", "C1_fsds_2025q2.zip", "20250331")]

REV = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
       "RevenueFromContractWithCustomerExcludingAssessedTax",
       "RevenueFromContractWithCustomerIncludingAssessedTax"]
COST = ["CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue"]


def facts(zf, period, tags, qtrs_wanted):
    """cik sets for (tag) at the given ddate/qtrs among 10-Qs of that period."""
    adsh, cik_of = set(), {}
    with zipfile.ZipFile(zf) as z, z.open("sub.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                                delimiter="\t"):
            if r["form"] == "10-Q" and r["period"] == period:
                adsh.add(r["adsh"]); cik_of[r["adsh"]] = r["cik"]
    got = defaultdict(set)
    with zipfile.ZipFile(zf) as z, z.open("num.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                                delimiter="\t"):
            if r["adsh"] not in adsh or r["segments"] or r["coreg"] or r["uom"] != "USD":
                continue
            if r["ddate"] != period or r["tag"] not in tags:
                continue
            if r["qtrs"] != qtrs_wanted.get(r["tag"], "1"):
                continue
            got[r["tag"]].add(cik_of[r["adsh"]])
    return got, len(adsh)


out = {}
for era, zc, pc, zp, pp in ERAS:
    tags_flow = set(["GrossProfit"] + REV + COST + ["ZZZZNotATagC1Control"])
    qw = {t: "1" for t in tags_flow}
    cur, n_cur = facts(zc, pc, tags_flow, qw)
    gp = cur["GrossProfit"]
    comp = set().union(*[cur[t] for t in REV]) & set().union(*[cur[t] for t in COST])
    numerator_ciks = gp | comp

    prev, n_prev = facts(zp, pp, {"Assets", "ZZZZNotATagC1Control"}, {"Assets": "0"})
    at_prev = prev["Assets"]

    curA, _ = facts(zc, pc, {"Assets"}, {"Assets": "0"})
    at_cur = curA["Assets"]

    # fiscal-phase spread among ALL 10-Qs accepted in the census zip
    per = Counter()
    with zipfile.ZipFile(zc) as z, z.open("sub.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                                delimiter="\t"):
            if r["form"] == "10-Q":
                per[r["period"]] += 1
    tot = sum(per.values())
    top = per.most_common(6)

    r = {
        "n_10Q_current_quarter": n_cur,
        "n_10Q_prior_quarter": n_prev,
        "single_quarter_GP_numerator_ciks": len(numerator_ciks),
        "with_CURRENT_quarter_Assets (Novy-Marx 2013 deflator)": len(numerator_ciks & at_cur),
        "with_PRIOR_quarter_Assets from prior 10-Q (HXZ/OSAP deflator)":
            len(numerator_ciks & at_prev),
        "stitch_rate_pct": round(100 * len(numerator_ciks & at_prev)
                                 / max(1, len(numerator_ciks)), 2),
        "control_invented_tag_current": len(cur.get("ZZZZNotATagC1Control", set())),
        "control_invented_tag_prior": len(prev.get("ZZZZNotATagC1Control", set())),
        "fiscal_period_spread_in_one_calendar_quarter": {
            "total_10Q": tot,
            "top_periods": [(p, c, round(100 * c / tot, 1)) for p, c in top],
            "n_distinct_periods": len(per),
            "share_in_modal_period_pct": round(100 * top[0][1] / tot, 1),
        },
    }
    out[era] = r
    print("=" * 18, era)
    for k, v in r.items():
        print(f"  {k:<62} {v}")

json.dump(out, open("C1_fsds_stitch.json", "w"), indent=1)
print("\nWROTE C1_fsds_stitch.json")
