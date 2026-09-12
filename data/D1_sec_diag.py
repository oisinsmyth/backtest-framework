"""D1: diagnose the control that fired (Assets <= 0) and test era stability."""
import json, urllib.request
UA = "backtest-framework research research@backtest-framework.org"


def fr(tag, per, tx="us-gaap"):
    u = "https://data.sec.gov/api/xbrl/frames/%s/%s/USD/%s.json" % (tx, tag, per)
    r = urllib.request.Request(u, headers={"User-Agent": UA})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())


A = fr("Assets", "CY2023Q4I")
GP = fr("GrossProfit", "CY2023")
a = {e["cik"]: (e["val"], e["entityName"]) for e in A["data"]}
neg = [(c, v, n) for c, (v, n) in a.items() if v < 0]
zero = [(c, v, n) for c, (v, n) in a.items() if v == 0]
print("Assets STRICTLY NEGATIVE: %d of %d" % (len(neg), len(a)))
print("Assets EXACTLY ZERO     : %d of %d  (= %.2f%%)" % (len(zero), len(a), 100 * len(zero) / len(a)))
for c, v, n in zero[:6]:
    print("   cik %s  %r  assets %s" % (c, n, v))
g = {e["cik"]: e["val"] for e in GP["data"]}
both = set(g) & set(a)
z = [c for c in both if a[c][0] == 0]
print("in GP n AT (%d): assets==0 -> %d  (GP/AT UNDEFINED, not merely extreme)" % (len(both), len(z)))
for c in z:
    print("   cik %s %r  GP %s  AT %s" % (c, a[c][1], g[c], a[c][0]))
for per in ["CY2011Q4I", "CY2015Q4I", "CY2019Q4I", "CY2023Q4I", "CY2025Q4I"]:
    try:
        SE = fr("StockholdersEquity", per)
        d = [e["val"] for e in SE["data"]]
        print("StockholdersEquity %s: n %d  share<0 %.1f%%"
              % (per, len(d), 100 * sum(1 for v in d if v < 0) / len(d)))
    except Exception as e:
        print(per, "->", e)
