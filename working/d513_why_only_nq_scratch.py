"""Why does the arm work on NQ and not on the other roots? GROSS beside NET, per root, which D513 reported only net.

If gross is positive everywhere and net is negative, the answer is cost. If gross is flat or negative, the signal itself is absent.
A decomposition of an already-read window (2016-2023); nothing new is read and 2024+ is untouched.

    uv run python -u working/d513_why_only_nq_scratch.py
"""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D506B = _load("d506b", "d506_macd_breadth.py")
ROOTS = ["NQ", "YM", "ZN", "ZB", "GC", "CL", "6E"]        # NQ included as the reference; its 2016-2023 is in-sample for the arm

meta = json.loads(D506B.META.read_text(encoding="utf-8")); specs = meta["specs"]
d_all = pd.read_csv(D506B.FIX)
rows = []
for r in ROOTS:
    sp = specs[r]; b = D506B.build_root(d_all, r, sp["day_window"])
    if b is None or b.get("skipped"):
        continue
    if D506B.M_PRIMARY > D506B.max_hold_available(b["first"], b["last"]):
        continue
    tickv = sp["tick_usd"]; cost_tk = D506B.COMMISSION_RT / tickv + D506B.CROSS_TICKS_ASSUMED; tk = sp["tick_price_units"]
    O, C = b["O"] / tk, b["C"] / tk
    pg, tg = D506B.simulate_window(O, C, b["AGREE"], b["first"], b["last"], D506B.M_PRIMARY, 0.0)
    pn, tn = D506B.simulate_window(O, C, b["AGREE"], b["first"], b["last"], D506B.M_PRIMARY, cost_tk)
    g = D506B.score(pg, tg, tickv, b["n_sessions"]); n = D506B.score(pn, tn, tickv, b["n_sessions"])
    # the per-trade move scale: mean |gross P&L| per trade, in dollars
    ntr = float(tg.sum())
    e_abs = float(np.abs(pg[tg > 0]).sum() / ntr) * tickv if ntr else np.nan
    rows.append(dict(root=r, sessions=b["n_sessions"], trades=int(ntr), trips=ntr / b["n_sessions"],
                     tick_usd=tickv, cost_usd=cost_tk * tickv, cost_ticks=cost_tk,
                     gross_usd_trade=g["mean_usd_per_trade"], net_usd_trade=n["mean_usd_per_trade"],
                     gross_sharpe=g["sharpe"], net_sharpe=n["sharpe"],
                     e_abs_move_usd=e_abs, cost_over_move=cost_tk * tickv / e_abs if e_abs else np.nan,
                     gross_over_cost=g["mean_usd_per_trade"] / (cost_tk * tickv) if cost_tk * tickv else np.nan))
D = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print("WHY NQ AND NOT THE OTHERS -- gross beside net, 2016-2023, the frozen arm at minimum size\n")
print(f"  {'root':5s} {'sess':>5s} {'trades':>6s} {'trips':>5s} | {'GROSS $/tr':>10s} {'gross Sh':>8s} | {'cost $':>7s} {'cost tk':>7s} | {'NET $/tr':>8s} {'net Sh':>7s} | {'E|move| $':>9s} {'cost/move':>9s} {'gross/cost':>10s}")
for r in D.itertuples():
    print(f"  {r.root:5s} {r.sessions:5d} {r.trades:6d} {r.trips:5.2f} | {r.gross_usd_trade:+10.2f} {r.gross_sharpe:+8.3f} | {r.cost_usd:7.2f} {r.cost_ticks:7.2f} | {r.net_usd_trade:+8.2f} {r.net_sharpe:+7.3f} | {r.e_abs_move_usd:9.2f} {100*r.cost_over_move:8.1f}% {r.gross_over_cost:+10.2f}")

print("\nREAD:")
pos_gross = D[D.gross_usd_trade > 0]
print(f"  gross is POSITIVE on {len(pos_gross)} of {len(D)} roots: {list(pos_gross.root)}")
print(f"  net is positive on {len(D[D.net_usd_trade > 0])} of {len(D)}: {list(D[D.net_usd_trade > 0].root)}")
nq = D[D.root == 'NQ'].iloc[0]
print(f"  NQ pays {100*nq.cost_over_move:.1f}% of its per-trade move in cost; the others pay "
      f"{100*D[D.root != 'NQ'].cost_over_move.min():.1f}% to {100*D[D.root != 'NQ'].cost_over_move.max():.1f}%")
print(f"  the cheapest non-NQ root is {D[D.root != 'NQ'].sort_values('cost_over_move').iloc[0].root} at "
      f"{100*D[D.root != 'NQ'].cost_over_move.min():.1f}%")
print("\n  what would each root need for its GROSS to cover its cost? (gross/cost > 1)")
for r in D.itertuples():
    need = r.cost_usd / r.gross_usd_trade if r.gross_usd_trade > 0 else np.nan
    print(f"     {r.root:5s} gross ${r.gross_usd_trade:+7.2f} against a ${r.cost_usd:6.2f} cost -> "
          + (f"needs {need:.1f}x its gross" if np.isfinite(need) and need > 0 else "no gross edge to scale"))
D.to_csv(REPO / "working" / "d513_why_only_nq.csv", index=False, float_format="%.5f")
print(f"\nwrote working/d513_why_only_nq.csv")
