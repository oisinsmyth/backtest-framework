"""Inventory: databento job dirs -> schema/span; micro costs; MJY census; status schema peek."""
import os, json, collections, sys
ROOT = r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento"
REPO = r"C:/Users/O/Desktop/Projects/Backtest Framework/.claude/worktrees/after-d674"

print("== job dirs ==")
for d in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, d)
    if not os.path.isdir(p):
        continue
    fs = [f for f in os.listdir(p) if f.endswith(".dbn.zst")]
    sch = collections.Counter(f.split(".")[-3] for f in fs)
    spans = sorted(f.split(".")[0].replace("glbx-mdp3-", "") for f in fs)
    sz = sum(os.path.getsize(os.path.join(p, f)) for f in fs) / 1e9
    cond = ""
    cj = os.path.join(p, "condition.json")
    mj = os.path.join(p, "manifest.json")
    if os.path.exists(mj):
        try:
            m = json.load(open(mj, encoding="utf-8"))
            cond = str(m.get("query", m.get("symbols", "")))[:120] if isinstance(m, dict) else ""
        except Exception as e:
            cond = f"manifest? {e}"
    print(f"{d:28s} n={len(fs):3d} {sz:7.2f}GB {dict(sch)} {spans[0] if spans else ''}..{spans[-1] if spans else ''} {cond}")

print("\n== micro costs ==")
c = json.load(open(os.path.join(REPO, "data/futures_costs.json"), encoding="utf-8"))
for root, ent in c["roots"].items():
    if "micro" in ent:
        m = ent["micro"]
        rt = {k: v for k, v in m.items() if "round_trip" in k or "default" in k or k in ("symbol", "tick_usd", "commission_rt_usd")}
        print(root, json.dumps(rt)[:400])

print("\n== census for micro FX ==")
cen = json.load(open(os.path.join(REPO, "data/cme_product_census.json"), encoding="utf-8"))
items = cen if isinstance(cen, list) else cen.get("products", cen)
if isinstance(items, dict):
    items = list(items.values()) if not all(isinstance(v, (int, float)) for v in items.values()) else [{"k": k, "v": v} for k, v in items.items()]
for it in items:
    s = json.dumps(it)
    if any(k in s for k in ('"MJY"', '"M6E"', '"M6A"', '"M6B"', '"MCD"', '"MSF"', '"MES"', '"MCL"', '"MNG"', '"MGC"', '"SIL"', '"MHG"', '"M2K"', '"MYM"', '"MNQ"', '"MBT"', '"10Y"', '"2YY"')):
        print(s[:300])
