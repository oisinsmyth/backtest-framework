"""D392 addendum -- the cost line the atlas owed: what each price tercile COSTS to trade.

    uv run python scripts/d392_tercile_cost.py

The atlas reports GROSS mean per trade. A random long on the cheap tercile earns +19.22 bp at the
median, and that number is uninterpretable without the spread of the names it holds -- D285 missed
a guessed 15 bp/side bar by 0.65 and the held names measured 33.8.

So: per tercile, the price bounds in dollars and the MEASURED Corwin-Schultz half-spread (D285's
estimator, the programme's own, via d348_prep's HALF), under both conventions. No kernel runs.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


ATL = _load("d392", "run_d392_base_rate_atlas.py")
PREP = _load("d348p", "d348_prep.py")
OUT = REPO / "data" / "d392_tercile_cost.json"

P = PREP.prep(need_grids=True)
elig = np.asarray(P["elig"])
CLOSE = np.asarray(P["CLOSE"])
pools = ATL.tercile_pools(P, elig)

atlas = json.loads((REPO / "data" / "d392_atlas.json").read_text())


def cell(pool, side="long"):
    k = ATL.cell_key("cond", 30_000, 20, side, pool, 1.0)
    return atlas["cells"].get(k, {})


rows = {}
print("\nPRICE TERCILES -- the gross floor beside what it costs to reach it\n")
print(f"  {'tercile':<10s} {'p10 $':>8s} {'median $':>9s} {'p90 $':>8s} "
      f"{'half-spread bp/side':>20s} {'round trip':>11s} {'gross p50':>10s} {'NET p50':>9s}")
for nm in ("price_lo", "price_mid", "price_hi"):
    m = pools[nm] & elig
    px = CLOSE[m]
    px = px[np.isfinite(px)]
    out = dict(price_p10=float(np.percentile(px, 10)), price_median=float(np.median(px)),
               price_p90=float(np.percentile(px, 90)), cells=int(m.sum()))
    for cv in ("PB", "PUB"):
        h = np.asarray(P["HALF"][cv])[m]
        h = h[np.isfinite(h)]
        out[f"half_{cv}"] = float(np.median(h))
    g = cell(nm).get("p50")
    # the 2-crossing line: a hedged single name charged its OWN round trip (D358's convention)
    rt = 2.0 * out["half_PUB"]
    out.update(gross_p50=g, round_trip_PUB=rt, net_p50=(g - rt) if g is not None else None)
    rows[nm] = out
    print(f"  {nm:<10s} {out['price_p10']:>8.2f} {out['price_median']:>9.2f} {out['price_p90']:>8.2f} "
          f"{out['half_PUB']:>20.2f} {rt:>11.2f} {g:>+10.2f} {out['net_p50']:>+9.2f}")

print("\n  half-spread is the MEASURED Corwin-Schultz median over that tercile's eligible cells")
print("  (PUB convention); round trip = 2 x half-spread, the name's own 2-crossing line (D358).")
OUT.write_text(json.dumps(rows, indent=1))
print(f"\n  wrote {OUT.relative_to(REPO)}")
