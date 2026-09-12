"""B2 lane: targeted SEC XBRL frames census for the tags each profitability
definition needs. Public endpoint, no credentials. Paced well under the SEC's
10 req/s guidance (0.25 s between calls => 4 req/s).

Measures: number of distinct entities reporting each us-gaap tag in each
calendar-year frame. Duration tags use CY####; instant (balance-sheet) tags use
CY####Q4I. Includes a deliberate negative-control tag that MUST return 0/404
every year.
"""

import json
import time
import urllib.request
import urllib.error

UA = "BacktestFrameworkResearch/1.0 (research@backtest-framework.org)"
BASE = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/{unit}/{frame}.json"

YEARS = [2011, 2013, 2015, 2016, 2017, 2018, 2019, 2020, 2022, 2024, 2025]

# (tag, unit, kind)  kind: 'D' duration (income stmt), 'I' instant (bal sheet)
TAGS = [
    # --- Gross profitability: REVT, COGS, AT
    ("Revenues", "USD", "D"),
    ("RevenueFromContractWithCustomerExcludingAssessedTax", "USD", "D"),
    ("RevenueFromContractWithCustomerIncludingAssessedTax", "USD", "D"),
    ("SalesRevenueNet", "USD", "D"),
    ("CostOfGoodsSold", "USD", "D"),
    ("CostOfGoodsAndServicesSold", "USD", "D"),
    ("CostOfRevenue", "USD", "D"),
    ("GrossProfit", "USD", "D"),
    ("Assets", "USD", "I"),
    # --- Operating profitability adds XSGA, XRD
    ("SellingGeneralAndAdministrativeExpense", "USD", "D"),
    ("GeneralAndAdministrativeExpense", "USD", "D"),
    ("SellingAndMarketingExpense", "USD", "D"),
    ("OperatingExpenses", "USD", "D"),
    ("OperatingIncomeLoss", "USD", "D"),
    ("ResearchAndDevelopmentExpense", "USD", "D"),
    # --- Cash-based operating profitability adds RECT, INVT, XPP, DRC+DRLT, AP, XACC
    ("AccountsReceivableNetCurrent", "USD", "I"),
    ("ReceivablesNetCurrent", "USD", "I"),
    ("InventoryNet", "USD", "I"),
    ("PrepaidExpenseCurrent", "USD", "I"),
    ("PrepaidExpenseAndOtherAssetsCurrent", "USD", "I"),
    ("DeferredRevenueCurrent", "USD", "I"),
    ("DeferredRevenueNoncurrent", "USD", "I"),
    ("ContractWithCustomerLiabilityCurrent", "USD", "I"),
    ("ContractWithCustomerLiabilityNoncurrent", "USD", "I"),
    ("AccountsPayableCurrent", "USD", "I"),
    ("AccountsPayableTradeCurrent", "USD", "I"),
    ("AccountsPayableAndAccruedLiabilitiesCurrent", "USD", "I"),
    ("AccruedLiabilitiesCurrent", "USD", "I"),
    # --- cash-flow-statement variant of CbOP (RECCH, INVCH, APALCH)
    ("IncreaseDecreaseInAccountsReceivable", "USD", "D"),
    ("IncreaseDecreaseInInventories", "USD", "D"),
    ("IncreaseDecreaseInAccountsPayableAndAccruedLiabilities", "USD", "D"),
    # --- negative controls: MUST be 0 / 404 every year
    ("ZZZZNotATagB2Control", "USD", "D"),
    ("AccountsReceivableNetCurrent", "EUR", "I"),  # wrong-unit control
]


def fetch(tag, unit, frame):
    url = BASE.format(tag=tag, unit=unit, frame=frame)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Encoding": "gzip, deflate"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            enc = r.headers.get("Content-Encoding", "")
            if "gzip" in enc:
                import gzip
                raw = gzip.decompress(raw)
            d = json.loads(raw.decode("utf-8"))
            if "data" not in d:
                return ("NODATAKEY", r.status, len(raw))
            return (len({x.get("cik") for x in d["data"]}), r.status, len(raw))
    except urllib.error.HTTPError as e:
        return ("HTTP%d" % e.code, e.code, 0)
    except Exception as e:
        return ("ERR:%s" % type(e).__name__, -1, 0)


rows = {}
for tag, unit, kind in TAGS:
    key = f"{tag}|{unit}"
    rows[key] = {}
    for y in YEARS:
        frame = f"CY{y}" if kind == "D" else f"CY{y}Q4I"
        n, status, nbytes = fetch(tag, unit, frame)
        rows[key][y] = n
        time.sleep(0.25)
    print(key, rows[key], flush=True)

with open("B2_tag_census.json", "w", encoding="utf-8") as f:
    json.dump({"years": YEARS, "counts": rows, "endpoint": BASE,
               "ua": UA}, f, indent=1)
print("DONE")
