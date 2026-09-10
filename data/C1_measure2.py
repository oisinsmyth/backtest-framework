"""C1 pass 2: quarterly-frequency computability intersections, as-filed.

Same endpoint/files as C1_measure.py. Restricted to 10-Q submissions whose `period`
is the target fiscal quarter end, consolidated facts only (segments=='' and coreg==''),
USD, and the CURRENT-period `ddate` for flows / current quarter end for instants.

Answers:
  - single-quarter (qtrs=1) vs YTD-only (qtrs=2 present, qtrs=1 absent) populations
  - how many CIKs can compute each profitability definition at quarterly frequency
  - how many carry the one-quarter-lagged deflator inside the SAME filing
Negative controls reported beside every count.
"""
import zipfile, io, csv, json
from collections import defaultdict

ERAS = [("2013", "20130630", "20130331", "C1_fsds_2013q3.zip"),
        ("2019", "20190630", "20190331", "C1_fsds_2019q3.zip"),
        ("2025", "20250630", "20250331", "C1_fsds_2025q3.zip")]

REV = ["Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
       "RevenueFromContractWithCustomerExcludingAssessedTax",
       "RevenueFromContractWithCustomerIncludingAssessedTax"]
COST = ["CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue"]
CBOP_BS = ["AccountsReceivableNetCurrent", "InventoryNet", "PrepaidExpenseCurrent",
           "DeferredRevenueCurrent", "DeferredRevenueNoncurrent",
           "ContractWithCustomerLiabilityCurrent", "ContractWithCustomerLiabilityNoncurrent",
           "AccountsPayableCurrent", "AccruedLiabilitiesCurrent"]
CONTROLS = ["ZZZZNotATagC1Control", "AssetsZZZZ"]

out = {}
for era, period, prevq, zf in ERAS:
    adsh, cik_of = set(), {}
    with zipfile.ZipFile(zf) as z, z.open("sub.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                                delimiter="\t"):
            if r["form"] == "10-Q" and r["period"] == period:
                adsh.add(r["adsh"]); cik_of[r["adsh"]] = r["cik"]

    # (tag, qtrs, ddate) -> set(cik)
    S = defaultdict(set)
    with zipfile.ZipFile(zf) as z, z.open("num.txt") as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                                delimiter="\t"):
            if r["adsh"] not in adsh or r["segments"] or r["coreg"] or r["uom"] != "USD":
                continue
            S[(r["tag"], r["qtrs"], r["ddate"])].add(cik_of[r["adsh"]])

    def g(tag, qtrs, ddate=period):
        return S.get((tag, qtrs, ddate), set())

    def anyof(tags, qtrs, ddate=period):
        u = set()
        for t in tags:
            u |= g(t, qtrs, ddate)
        return u

    at_cur = g("Assets", "0", period)
    at_prevq = g("Assets", "0", prevq)
    gp1, gp2 = g("GrossProfit", "1"), g("GrossProfit", "2")
    rev1, cost1 = anyof(REV, "1"), anyof(COST, "1")
    comp1 = rev1 & cost1
    either1 = gp1 | comp1
    xsga1 = g("SellingGeneralAndAdministrativeExpense", "1")

    r = {
        "n_10Q": len(adsh),
        "Assets_current_qend": len(at_cur),
        "Assets_prior_qend_in_same_filing": len(at_prevq),
        "Assets_prior_qend_pct_of_current": round(100 * len(at_prevq) / max(1, len(at_cur)), 2),
        "GrossProfit_q1": len(gp1),
        "GrossProfit_q2_YTD": len(gp2),
        "GrossProfit_YTD_only_no_q1": len(gp2 - gp1),
        "revenue_family_q1": len(rev1),
        "cost_family_q1": len(cost1),
        "component_route_q1 (rev AND cost)": len(comp1),
        "either_route_q1": len(either1),
        "component_route_adds_over_GrossProfit": len(comp1 - gp1),
        "GROSS_PROF_computable_q1 = either_route AND Assets_current": len(either1 & at_cur),
        "GROSS_PROF_with_ONE_QUARTER_LAGGED_deflator_same_filing": len(either1 & at_prevq),
        "XSGA_q1": len(xsga1),
        "OPER_PROF_computable_q1": len(either1 & at_cur & xsga1),
        "CbOP_strict_all_bs_terms_q1": len(
            either1 & at_cur & xsga1
            & g("AccountsReceivableNetCurrent", "0") & g("InventoryNet", "0")
            & g("PrepaidExpenseCurrent", "0") & g("AccountsPayableCurrent", "0")
            & g("AccruedLiabilitiesCurrent", "0")
            & (g("DeferredRevenueCurrent", "0") | g("ContractWithCustomerLiabilityCurrent", "0"))),
        "CbOP_HXZ_style_4_terms_q1": len(
            either1 & at_cur & xsga1
            & g("AccountsReceivableNetCurrent", "0") & g("InventoryNet", "0")
            & g("AccountsPayableCurrent", "0")
            & (g("DeferredRevenueCurrent", "0") | g("ContractWithCustomerLiabilityCurrent", "0"))),
        "control_invented_tags": {c: len(g(c, "1")) + len(g(c, "0")) for c in CONTROLS},
        "control_SalesRevenueNet_q1": len(g("SalesRevenueNet", "1")),
        "control_ddate_never_in_future": len(g("Assets", "0", "20991231")),
    }
    out[era] = r
    print("=" * 18, era, period)
    for k, v in r.items():
        print(f"  {k:<62} {v}")

json.dump(out, open("C1_fsds_intersections.json", "w"), indent=1)
print("\nWROTE C1_fsds_intersections.json")
