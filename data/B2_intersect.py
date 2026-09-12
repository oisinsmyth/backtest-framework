"""B2 lane: how many SEC filers carry EVERY tag each profitability definition
needs, in the same calendar year? Frames endpoint returns the CIK list, so the
intersection is directly measurable.

Definitions priced (all per the source papers, see brief):
  GP_direct : GrossProfit, Assets
  GP_chain  : (revenue family) & (cost family) & Assets
  OP        : GP route & SG&A & Assets          (XRD optional -> zero if missing)
  CbOP_bs   : OP route & RECT & INVT & XPP & DeferredRev(either vintage)
              & AP & XACC                      (balance-sheet version)
  CbOP_cf   : OP route & RECCH & INVCH & APALCH (cash-flow-statement version)

Note: BGLN set missing balance-sheet CHANGES to zero, so CbOP_bs as they
implement it does not require every term. Both the strict intersection and the
BGLN-style relaxed count are reported.
"""

import json
import time
import urllib.request
import urllib.error
import gzip

UA = "BacktestFrameworkResearch/1.0 (research@backtest-framework.org)"
BASE = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{frame}.json"
YEARS = [2013, 2016, 2019, 2022, 2024]

DUR = {  # income-statement / cash-flow (duration) tags
    "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
    "CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue",
    "GrossProfit", "SellingGeneralAndAdministrativeExpense",
    "ResearchAndDevelopmentExpense",
    "IncreaseDecreaseInAccountsReceivable", "IncreaseDecreaseInInventories",
    "IncreaseDecreaseInAccountsPayableAndAccruedLiabilities",
}

TAGS = sorted(DUR | {
    "Assets", "AccountsReceivableNetCurrent", "InventoryNet",
    "PrepaidExpenseCurrent", "PrepaidExpenseAndOtherAssetsCurrent",
    "DeferredRevenueCurrent", "DeferredRevenueNoncurrent",
    "ContractWithCustomerLiabilityCurrent", "AccountsPayableCurrent",
    "AccruedLiabilitiesCurrent",
})


def ciks(tag, year):
    frame = f"CY{year}" if tag in DUR else f"CY{year}Q4I"
    url = BASE.format(tag=tag, frame=frame)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            if "gzip" in r.headers.get("Content-Encoding", ""):
                raw = gzip.decompress(raw)
            d = json.loads(raw.decode("utf-8"))
            if "data" not in d:
                return set(), "NODATAKEY"
            return {x["cik"] for x in d["data"]}, "ok"
    except urllib.error.HTTPError as e:
        return set(), f"HTTP{e.code}"
    except Exception as e:
        return set(), f"ERR:{type(e).__name__}"


out = {}
for y in YEARS:
    S = {}
    for t in TAGS:
        S[t], st = ciks(t, y)
        time.sleep(0.25)
    rev = S["Revenues"] | S["RevenueFromContractWithCustomerExcludingAssessedTax"] \
        | S["RevenueFromContractWithCustomerIncludingAssessedTax"] | S["SalesRevenueNet"]
    cost = S["CostOfGoodsSold"] | S["CostOfGoodsAndServicesSold"] | S["CostOfRevenue"]
    gp_any = S["GrossProfit"] | (rev & cost)
    xpp_any = S["PrepaidExpenseCurrent"] | S["PrepaidExpenseAndOtherAssetsCurrent"]
    drev_any = S["DeferredRevenueCurrent"] | S["DeferredRevenueNoncurrent"] \
        | S["ContractWithCustomerLiabilityCurrent"]
    res = {
        "Assets": len(S["Assets"]),
        "GrossProfit_tag": len(S["GrossProfit"]),
        "rev_family": len(rev),
        "cost_family": len(cost),
        "rev&cost": len(rev & cost),
        "GP_direct (GrossProfit & Assets)": len(S["GrossProfit"] & S["Assets"]),
        "GP_chain (rev&cost&Assets)": len(rev & cost & S["Assets"]),
        "GP_any (either route)": len(gp_any & S["Assets"]),
        "SGA": len(S["SellingGeneralAndAdministrativeExpense"]),
        "OP (GP_any & SGA & Assets)": len(gp_any & S["SellingGeneralAndAdministrativeExpense"] & S["Assets"]),
        "CbOP_bs STRICT (OP & RECT & INVT & XPP & DRev & AP & XACC)": len(
            gp_any & S["SellingGeneralAndAdministrativeExpense"] & S["Assets"]
            & S["AccountsReceivableNetCurrent"] & S["InventoryNet"] & xpp_any
            & drev_any & S["AccountsPayableCurrent"] & S["AccruedLiabilitiesCurrent"]),
        "CbOP_bs BGLN-relaxed (OP & RECT & AP)": len(
            gp_any & S["SellingGeneralAndAdministrativeExpense"] & S["Assets"]
            & S["AccountsReceivableNetCurrent"] & S["AccountsPayableCurrent"]),
        "CbOP_cf (OP & RECCH & INVCH & APALCH)": len(
            gp_any & S["SellingGeneralAndAdministrativeExpense"] & S["Assets"]
            & S["IncreaseDecreaseInAccountsReceivable"]
            & S["IncreaseDecreaseInInventories"]
            & S["IncreaseDecreaseInAccountsPayableAndAccruedLiabilities"]),
        "DeferredRev_any": len(drev_any),
        "DeferredRev_old_only": len(S["DeferredRevenueCurrent"] | S["DeferredRevenueNoncurrent"]),
        "DeferredRev_new_only": len(S["ContractWithCustomerLiabilityCurrent"]),
    }
    out[y] = res
    print(y, json.dumps(res, indent=1), flush=True)

with open("B2_intersect.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print("DONE")
