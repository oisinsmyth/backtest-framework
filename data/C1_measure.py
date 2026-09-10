"""C1 lane measurement on SEC Financial Statement Data Sets (as-filed, point-in-time).

Endpoint: https://www.sec.gov/files/dera/data/financial-statement-data-sets/<yyyy>q<n>.zip
Files used inside each zip: sub.txt (submissions), num.txt (numeric facts).

M1  filing-lag distribution: accepted-date minus fiscal-period-end, for 10-Q and 10-K
M2  coverage curve: share of a fiscal quarter's 10-Q filers knowable at lag L days
M2b acceptance clock: share of those 10-Qs accepted at/after 16:00 ET with same-day `filed`
M3  tag census at QUARTERLY frequency, as filed, split by the `qtrs` duration field
M4  which balance-sheet dates a single 10-Q actually carries (the deflator-timing question)

Negative controls are computed and reported beside every count.
"""
import zipfile, io, csv, sys, json, datetime as dt
from collections import defaultdict, Counter

ERAS = [
    ("2013", "20130630", ["C1_fsds_2013q3.zip", "C1_fsds_2013q4.zip"], "C1_fsds_2013q3.zip"),
    ("2019", "20190630", ["C1_fsds_2019q3.zip", "C1_fsds_2019q4.zip"], "C1_fsds_2019q3.zip"),
    ("2025", "20250630", ["C1_fsds_2025q3.zip", "C1_fsds_2025q4.zip"], "C1_fsds_2025q3.zip"),
]

TAGS = [
    # gross profitability, direct and component routes
    "GrossProfit", "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "CostOfGoodsSold", "CostOfGoodsAndServicesSold", "CostOfRevenue",
    # operating profitability extras
    "SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense",
    "ResearchAndDevelopmentExpense", "OperatingIncomeLoss",
    # CbOP accrual terms
    "AccountsReceivableNetCurrent", "InventoryNet", "PrepaidExpenseCurrent",
    "DeferredRevenueCurrent", "DeferredRevenueNoncurrent",
    "ContractWithCustomerLiabilityCurrent", "ContractWithCustomerLiabilityNoncurrent",
    "AccountsPayableCurrent", "AccruedLiabilitiesCurrent",
    "IncreaseDecreaseInAccountsReceivable", "IncreaseDecreaseInInventories",
    "IncreaseDecreaseInAccountsPayableAndAccruedLiabilities",
    # deflator
    "Assets",
    # negative controls
    "ZZZZNotATagC1Control", "GrossProfitZZZZ",
]
TAGSET = set(TAGS)


def read_sub(zf):
    with zipfile.ZipFile(zf) as z, z.open("sub.txt") as f:
        rdr = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                             delimiter="\t")
        for row in rdr:
            yield row


def parse_accepted(s):
    # "2019-08-07 17:21:00.0"  -- FSDS documents this as ET
    return dt.datetime.strptime(s.split(".")[0], "%Y-%m-%d %H:%M:%S")


def parse_period(s):
    return dt.datetime.strptime(s, "%Y%m%d")


def pct(x, n):
    return round(100.0 * x / n, 2) if n else None


out = {"endpoint": "https://www.sec.gov/files/dera/data/financial-statement-data-sets/",
       "note": "FSDS `accepted` is the EDGAR acceptance timestamp; FSDS documents it in ET.",
       "eras": {}}

for era, period, zips, census_zip in ERAS:
    print(f"\n===== ERA {era}  fiscal period {period} =====", flush=True)
    rec = {"period": period, "zips": zips}

    # ---------- M1 / M2 / M2b ----------
    lags, hours, adsh_target, forms_seen = [], [], set(), Counter()
    k_lags = []           # 10-K lags for the same era, any period, for contrast
    n_sub_total = 0
    for zf in zips:
        for r in read_sub(zf):
            n_sub_total += 1
            forms_seen[r["form"]] += 1
            if r["form"] == "10-Q" and r["period"] == period:
                acc = parse_accepted(r["accepted"])
                lag = (acc.date() - parse_period(period).date()).days
                lags.append(lag)
                hours.append((acc.hour, r["filed"] == acc.strftime("%Y%m%d")))
                adsh_target.add(r["adsh"])
            if r["form"] == "10-K":
                acc = parse_accepted(r["accepted"])
                try:
                    k_lags.append((acc.date() - parse_period(r["period"]).date()).days)
                except Exception:
                    pass

    lags.sort()
    n = len(lags)
    rec["n_10Q_for_period"] = n
    rec["n_submissions_in_zips"] = n_sub_total
    rec["form_counts_top"] = dict(forms_seen.most_common(8))
    if n:
        q = lambda p: lags[min(n - 1, int(p * n))]
        rec["lag_days_quantiles"] = {"min": lags[0], "p05": q(.05), "p25": q(.25),
                                     "p50": q(.50), "p75": q(.75), "p90": q(.90),
                                     "p95": q(.95), "p99": q(.99), "max": lags[-1]}
        rec["coverage_by_lag_days"] = {str(L): pct(sum(1 for x in lags if x <= L), n)
                                       for L in [0, 20, 30, 40, 45, 50, 60, 75, 90,
                                                 100, 105, 120, 135, 150, 184]}
        # negative control on the coverage curve: lag < 0 must be ~0
        rec["control_coverage_negative_lag"] = pct(sum(1 for x in lags if x < 0), n)
        after16 = sum(1 for h, same in hours if h >= 16)
        after16_same = sum(1 for h, same in hours if h >= 16 and same)
        rec["accept_after_1600_pct"] = pct(after16, n)
        rec["accept_after_1600_and_filed_same_day_pct"] = pct(after16_same, n)
        rec["accept_hour_hist"] = dict(sorted(Counter(h for h, _ in hours).items()))
    k_lags.sort()
    if k_lags:
        m = len(k_lags)
        qk = lambda p: k_lags[min(m - 1, int(p * m))]
        rec["n_10K_any_period"] = m
        rec["lag_days_10K_quantiles"] = {"p25": qk(.25), "p50": qk(.50), "p75": qk(.75),
                                         "p90": qk(.90), "p95": qk(.95), "p99": qk(.99)}

    # ---------- M3 / M4 : tag census over the target-period 10-Qs ----------
    # restrict to the census zip; adsh of 10-Qs for the target period filed in it
    adsh_census, cik_of = set(), {}
    for r in read_sub(census_zip):
        if r["form"] == "10-Q" and r["period"] == period:
            adsh_census.add(r["adsh"])
            cik_of[r["adsh"]] = r["cik"]
    rec["n_10Q_in_census_zip"] = len(adsh_census)

    # tag -> qtrs -> set(cik), restricted to consolidated (no segment, no coreg)
    tagq = defaultdict(lambda: defaultdict(set))
    assets_ddate = Counter()          # M4
    assets_ddate_ciks = defaultdict(set)
    gp_q1_ciks, at_cur_ciks = set(), set()
    n_rows = 0
    with zipfile.ZipFile(census_zip) as z, z.open("num.txt") as f:
        rdr = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"),
                             delimiter="\t")
        for row in rdr:
            n_rows += 1
            a = row["adsh"]
            if a not in adsh_census:
                continue
            if row["segments"] or row["coreg"]:
                continue
            if row["uom"] != "USD":
                continue
            tag = row["tag"]
            cik = cik_of[a]
            if tag == "Assets" and row["qtrs"] == "0":
                assets_ddate[row["ddate"]] += 1
                assets_ddate_ciks[row["ddate"]].add(cik)
            if tag not in TAGSET:
                continue
            if row["ddate"] != period:      # current-period value only
                continue
            tagq[tag][row["qtrs"]].add(cik)
            if tag == "GrossProfit" and row["qtrs"] == "1":
                gp_q1_ciks.add(cik)
            if tag == "Assets" and row["qtrs"] == "0":
                at_cur_ciks.add(cik)
    rec["num_rows_scanned"] = n_rows
    rec["tag_census_ciks_by_qtrs"] = {t: {k: len(v) for k, v in sorted(d.items())}
                                      for t, d in sorted(tagq.items())}
    rec["assets_ddate_top"] = {d: len(assets_ddate_ciks[d])
                               for d, _ in assets_ddate.most_common(8)}
    rec["gross_prof_q1_and_current_assets_ciks"] = len(gp_q1_ciks & at_cur_ciks)
    out["eras"][era] = rec
    print(json.dumps(rec, indent=1)[:4000], flush=True)

with open("C1_fsds_measurement.json", "w") as f:
    json.dump(out, f, indent=1)
print("\nWROTE C1_fsds_measurement.json", flush=True)
