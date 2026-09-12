"""K1: EDGAR full-text-search census of transfer-announcement 8-Ks, and the
EARNINGS CO-FILING fraction (does the transfer 8-K also carry Item 2.02?).

Controls reported beside every count:
  * an impossible phrase, which MUST return 0
  * a pre-EDGAR-FTS date window (1995), which MUST return 0
  * a two-phrase query whose second phrase is impossible, which MUST return 0
"""
import json, time, urllib.parse, urllib.request, sys

UA = "backtest-framework-research research@backtest-framework.org"
BASE = "https://efts.sec.gov/LATEST/search-index?"

def q(phrases, y0=None, y1=None, forms="8-K"):
    qs = " ".join(f'"{p}"' for p in phrases)
    params = {"q": qs, "forms": forms}
    if y0:
        params["startdt"] = f"{y0}-01-01"
        params["enddt"] = f"{y1}-12-31"
    url = BASE + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": UA}),
                timeout=40)
            d = json.loads(r.read())
            t = d["hits"]["total"]
            time.sleep(0.5)
            return t["value"], t["relation"]
        except Exception as e:
            time.sleep(3 * (attempt + 1))
    return None, f"ERR"

EARN = "Results of Operations and Financial Condition"
IMPOSSIBLE = "zzqxwv impossible control token"

print("=== CONTROLS ===")
print("  impossible phrase, all years        :", q([IMPOSSIBLE]))
print("  transfer phrase, 1995 (pre-FTS)     :", q(["transfer the listing"], 1995, 1995))
print("  transfer phrase AND impossible      :", q(["transfer the listing", IMPOSSIBLE]))
print("  earnings phrase alone, 2015 (sanity):", q([EARN], 2015, 2015))

PHRASES = [
    ["transfer the listing"],
    ["transfer its listing"],
    ["transfer of its listing"],
    ["voluntarily withdraw the listing"],
    ["transfer of listing"],            # = the Item 3.01 heading, a ceiling
]
print("\n=== phrase counts in 8-K, by year ===")
hdr = ["year"] + ["/".join(p)[:26] for p in PHRASES]
print("".join(f"{h:>28s}" for h in hdr))
tot = {tuple(p): 0 for p in PHRASES}
for y in range(2010, 2027):
    cells = []
    for p in PHRASES:
        v, rel = q(p, y, y)
        cells.append(f"{v}{'+' if rel!='eq' else ''}")
        if isinstance(v, int):
            tot[tuple(p)] += v
    print(f"{y:>28d}" + "".join(f"{c:>28s}" for c in cells))
print(f"{'TOTAL':>28s}" + "".join(f"{tot[tuple(p)]:>28d}" for p in PHRASES))

print("\n=== EARNINGS CO-FILING: phrase AND the Item 2.02 heading ===")
for p in PHRASES:
    a, _ = q(p, 2010, 2026)
    b, _ = q(p + [EARN], 2010, 2026)
    frac = (100.0 * b / a) if (a and isinstance(a, int) and a > 0) else float("nan")
    print(f"  {'/'.join(p)[:34]:36s} alone={a:<7} with Item 2.02 heading={b:<7} "
          f"({frac:.1f}%)")
