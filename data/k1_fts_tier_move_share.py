"""K1: is the post-2022 surge in 'transfer the listing' 8-Ks an INTER-exchange
phenomenon, or is it the INTRA-Nasdaq tier transfer (Global Select/Global Market
-> Capital Market) that deficiency-hit sub-$1 issuers use to buy more time?
"""
import json, time, urllib.parse, urllib.request

UA = "backtest-framework-research research@backtest-framework.org"
BASE = "https://efts.sec.gov/LATEST/search-index?"

def q(phrases, y0, y1, forms="8-K"):
    params = {"q": " ".join(f'"{p}"' for p in phrases), "forms": forms,
              "startdt": f"{y0}-01-01", "enddt": f"{y1}-12-31"}
    url = BASE + urllib.parse.urlencode(params)
    for a in range(4):
        try:
            d = json.loads(urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": UA}),
                timeout=40).read())
            time.sleep(0.6)
            t = d["hits"]["total"]
            return t["value"], t["relation"]
        except Exception:
            time.sleep(3 * (a + 1))
    return None, "ERR"

IMP = "zzqxwv impossible control token"
print("CONTROL: 'transfer the listing' + impossible, 2010-2026 ->",
      q(["transfer the listing", IMP], 2010, 2026))
print("CONTROL: 'Nasdaq Capital Market' + impossible, 2023 ->",
      q(["Nasdaq Capital Market", IMP], 2023, 2023))

COLS = [
    ("all", ["transfer the listing"]),
    ("+Nasdaq Capital Market", ["transfer the listing", "Nasdaq Capital Market"]),
    ("+minimum bid price", ["transfer the listing", "minimum bid price"]),
    ("+New York Stock Exchange", ["transfer the listing", "New York Stock Exchange"]),
    ("+NYSE American", ["transfer the listing", "NYSE American"]),
]
print("\nyear " + "".join(f"{n:>26s}" for n, _ in COLS))
tot = [0] * len(COLS)
for y in range(2010, 2027):
    cells = []
    for i, (n, p) in enumerate(COLS):
        v, r = q(p, y, y)
        cells.append(f"{v}{'+' if r != 'eq' else ''}")
        if isinstance(v, int):
            tot[i] += v
    print(f"{y:>4d} " + "".join(f"{c:>26s}" for c in cells))
print("TOT  " + "".join(f"{t:>26d}" for t in tot))
