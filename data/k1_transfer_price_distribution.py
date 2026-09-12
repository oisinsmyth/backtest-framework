"""K1: (1) MEASURE the survivors-only hazard in SEC company_tickers.json against
the transfer CIKs, and (2) for the CIKs it does cover, pull the close on the
announcement date from the Yahoo chart endpoint and report the PRICE
distribution (not the size distribution).

Negative controls:
  * a CIK that cannot exist (9999999999) must not appear in company_tickers.json
  * a symbol that cannot exist must return an explicit Yahoo error, not a price
Caveats recorded, not papered over:
  * company_tickers.json is a CURRENT map: any CIK whose ticker is gone is
    simply absent, so the covered subset is survivor-biased UPWARD in price
  * the Yahoo `close` series is SPLIT-adjusted, so a later forward split
    understates the as-traded price and a later reverse split overstates it
"""
import csv, json, os, statistics, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "backtest-framework-research research@backtest-framework.org"
BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

def get(url, ua):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": ua}), timeout=40).read()

ctp = os.path.join(HERE, "K1_company_tickers.json")
if not os.path.exists(ctp):
    open(ctp, "wb").write(get("https://www.sec.gov/files/company_tickers.json", UA))
ct = json.load(open(ctp, encoding="utf-8"))
cik2t = {}
for v in ct.values():
    cik2t.setdefault(str(int(v["cik_str"])), v["ticker"])
print("company_tickers.json entries:", len(ct), " distinct CIKs:", len(cik2t))
print("NEGATIVE CONTROL: CIK 9999999999 present?",
      "9999999999" in cik2t, "(must be False)")

tr = list(csv.DictReader(open(os.path.join(HERE, "K1_transfers.tsv"),
                             encoding="utf-8"), delimiter="\t"))
print("\ntransfers in census:", len(tr))
ciks = sorted({r["cik"] for r in tr})
have = [c for c in ciks if c in cik2t]
print(f"distinct CIKs: {len(ciks)};  present in company_tickers.json: {len(have)} "
      f"({100.0*len(have)/max(1,len(ciks)):.1f}%)")
print(f"*** SILENTLY DROPPED BY THE FREE TICKER MAP: {len(ciks)-len(have)} CIKs "
      f"({100.0*(len(ciks)-len(have))/max(1,len(ciks)):.1f}%) ***")

print("\nNEGATIVE CONTROL: Yahoo on an impossible symbol:")
try:
    b = get("https://query1.finance.yahoo.com/v8/finance/chart/ZZQXWVNOTASYM"
            "?period1=1500000000&period2=1510000000&interval=1d", BROWSER)
    print("  ", b[:120])
except Exception as e:
    print("   HTTPError ->", e, "(an explicit error, not a price: control PASSES)")

def close_on(sym, iso):
    import datetime as dt
    d = dt.date.fromisoformat(iso)
    p1 = int(time.mktime((d - dt.timedelta(days=12)).timetuple()))
    p2 = int(time.mktime((d + dt.timedelta(days=5)).timetuple()))
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?period1={p1}&period2={p2}&interval=1d")
    try:
        d2 = json.loads(get(url, BROWSER))
    except Exception:
        return None, None
    res = (d2.get("chart") or {}).get("result")
    if not res:
        return None, None
    q = res[0]["indicators"]["quote"][0]
    ts = res[0]["timestamps"] if "timestamps" in res[0] else res[0]["timestamp"]
    import datetime as dt2
    best = None
    for t, c, v in zip(ts, q.get("close") or [], q.get("volume") or []):
        if c is None:
            continue
        dd = dt2.datetime.utcfromtimestamp(t).date()
        if dd <= d:
            best = (c, v, dd)
    return (best[0], best[1]) if best else (None, None)

rows = []
for r in tr:
    sym = cik2t.get(r["cik"])
    if not sym:
        continue
    px, vol = close_on(sym, r["a_date"])
    time.sleep(0.25)
    if px is None:
        continue
    rows.append((r["a_date"], r["orig"], r["dest"], sym, px,
                 (px * vol / 1e6) if vol else None, r["company"]))
print(f"\nprices recovered for {len(rows)} of {len(tr)} census rows")

def describe(label, vals):
    if not vals:
        print(f"  {label}: n=0")
        return
    v = sorted(vals)
    n = len(v)
    pct = lambda p: v[min(n - 1, int(p * n))]
    print(f"  {label}: n={n}  min={v[0]:.2f}  p10={pct(.10):.2f}  "
          f"p25={pct(.25):.2f}  MEDIAN={statistics.median(v):.2f}  "
          f"p75={pct(.75):.2f}  p90={pct(.90):.2f}  max={v[-1]:.2f}  "
          f"| share < $5: {100.0*sum(1 for x in v if x < 5)/n:.1f}%"
          f"  share < $10: {100.0*sum(1 for x in v if x < 10)/n:.1f}%")

print("\n=== PRICE (split-adjusted close) on the 8-A12B date, BY DIRECTION ===")
describe("ALL", [r[4] for r in rows])
for o, d in sorted({(r[1], r[2]) for r in rows}):
    describe(f"{o}->{d}", [r[4] for r in rows if r[1] == o and r[2] == d])

print("\n=== DOLLAR VOLUME ($m) on that date, BY DIRECTION ===")
dv = [r[5] for r in rows if r[5] is not None]
describe("ALL ($m)", dv)
for o, d in sorted({(r[1], r[2]) for r in rows}):
    describe(f"{o}->{d} ($m)",
             [r[5] for r in rows if r[1] == o and r[2] == d and r[5] is not None])

print("\n=== joint screen: price >= $5 AND dollar volume >= $1m ===")
for o, d in sorted({(r[1], r[2]) for r in rows}):
    s = [r for r in rows if r[1] == o and r[2] == d]
    p = [r for r in s if r[4] >= 5 and (r[5] or 0) >= 1.0]
    print(f"  {o:14s}->{d:14s} n={len(s):4d}  passing={len(p):4d} "
          f"({100.0*len(p)/max(1,len(s)):.0f}%)")

with open(os.path.join(HERE, "K1_prices.tsv"), "w", encoding="utf-8",
          newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(["a_date", "orig", "dest", "symbol", "close", "dollar_vol_m",
                "company"])
    w.writerows(sorted(rows))
print("\nwrote K1_prices.tsv")
