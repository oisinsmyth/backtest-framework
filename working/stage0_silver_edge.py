"""STAGE 0 for component #2: does the MACD signal have a DAY-SESSION edge on silver?

D515 ran this ladder on eight roots -- ES NQ YM ZN ZB GC CL 6E -- and silver, gas and copper were
not among them, because until today we had no expressible instrument for any of the three. Now we
do (SIL/MNG/MHG are CME-verified in futures_contract_specs.json), so the question is live.

Everything here is IMPORTED from D515 and D506's runners -- flat_series, cell, rotation, edge_sigma
and the day/night segment split -- so this is D515's measurement on three more roots, not a new
statistic. NQ is carried as the reference the others must be read against.

A SIGNAL measurement: no cost, no flatten, no position, no P&L (R15). It answers "is there anything
there", which is the question that must precede "can this book trade it". Window 2016-2023; the
2024+ slice is RESERVED and is not read.

    python working/stage0_silver_edge.py
"""
from __future__ import annotations
import importlib.util
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

NEW = ["SI", "NG", "HG"]              # the three the micro census opened
REF = ["NQ", "GC", "CL"]              # D515 roots for calibration: the winner, and two that failed
HOLDS = [1, 2, 3, 5, 8, 13, 21, 34]


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


D515 = _load("d515s", "run_d515_horizon_ladder.py")
D506B = _load("d506bs", "d506_macd_breadth.py")
edge_sigma = D515.edge_sigma

t0 = time.time()
meta = json.loads(D506B.META.read_text(encoding="utf-8"))
specs = meta["specs"]
d_all = pd.read_csv(D506B.FIX)
ROOTS = NEW + REF
missing = [r for r in ROOTS if r not in specs]
assert not missing, f"no day_window in the breadth meta for {missing}"
print(f"D515's ladder on three new roots. window {D506B.IN_LO}..{D506B.IN_HI}; "
      f"a SIGNAL measurement -- no cost, no flatten, no P&L\n")

S = {r: D515.flat_series(d_all, r, specs[r]["day_window"]) for r in ROOTS}

print("  edge_sigma by root and horizon (segments); the arm's window is ~7, a session is 23")
print(f"  {'root':5s} " + " ".join(f"{('H' + str(h)):>8s}" for h in HOLDS) + "   peak")
ladder = {}
for r in ROOTS:
    sig, og, ns, nseg = S[r]
    vals = [D515.cell(sig, og, H)["edge_sigma"] for H in HOLDS]
    ladder[r] = dict(zip(HOLDS, vals))
    tag = "  <-- NEW" if r in NEW else ""
    print(f"  {r:5s} " + " ".join(f"{v:+8.4f}" for v in vals) + f"   {HOLDS[int(np.nanargmax(vals))]:>4d}{tag}")

print("\n  WHERE IN THE CLOCK, at H = 1: the day segments the arm would trade vs the overnight it never does")
print(f"  {'root':5s} {'window':>9s} | {'DAY':>9s} {'n':>8s} | {'NIGHT':>9s} {'n':>8s} |  reading")
rows = []
for r in ROOTS:
    sig, og, ns, nseg = S[r]
    w = specs[r]["day_window"]
    first, last = D506B.seg_index(w[0]), D506B.seg_index(w[1])
    day = np.zeros(nseg, bool)
    day[first:last + 1] = True
    f1 = D515.forward(og, 1)

    def e(mask):
        s = np.where(mask[None, :], sig, 0.0).ravel()
        ff = f1.ravel()
        m = np.isfinite(s) & np.isfinite(ff) & (s != 0)
        return edge_sigma(s, ff), int(m.sum())

    ed, nd = e(day)
    en, nn = e(~day)
    tag = "edge is in the NIGHT" if en > ed + 0.004 else ("edge is in the DAY" if ed > en + 0.004 else "even")
    rows.append(dict(root=r, day_edge=ed, day_n=nd, night_edge=en, night_n=nn, reading=tag, new=r in NEW))
    print(f"  {r:5s} {str(w[0])}-{str(w[1]):>3s} | {ed:+9.4f} {nd:>8,} | {en:+9.4f} {nn:>8,} |  {tag}")

print("\n  N1 -- exact enumerated rotation of the signal along the SESSION axis, day segments only, H = 1")
print(f"  {'root':5s} {'day edge':>10s} {'p50':>9s} {'p95':>9s} {'SE(p95)':>9s}   verdict")
null = {}
for r in ROOTS:
    sig, og, ns, nseg = S[r]
    w = specs[r]["day_window"]
    first, last = D506B.seg_index(w[0]), D506B.seg_index(w[1])
    day = np.zeros(nseg, bool)
    day[first:last + 1] = True
    sd = np.where(day[None, :], sig, 0.0)
    f1 = D515.forward(og, 1).ravel()
    obs = edge_sigma(sd.ravel(), f1)
    draws = np.array([edge_sigma(np.roll(sd, k, axis=0).ravel(), f1) for k in range(1, ns)])
    p95 = float(np.quantile(draws, 0.95))
    se = float(np.std(draws, ddof=1) / np.sqrt(len(draws)) * 1.96)      # rough SE on the quantile
    null[r] = dict(obs=float(obs), p50=float(np.median(draws)), p95=p95, n_offsets=len(draws),
                   clears=bool(obs > p95), share_ge=float((draws >= obs).mean()))
    v = "CLEARS" if obs > p95 else "inside the null"
    print(f"  {r:5s} {obs:+10.4f} {np.median(draws):+9.4f} {p95:+9.4f} {se:>9.4f}   {v}"
          + ("  <-- NEW" if r in NEW else ""))

D = pd.DataFrame(rows)
D.to_csv(REPO / "working" / "stage0_silver_edge.csv", index=False)
print(f"\n  NQ's day edge is the bar the new roots must be read against: {D.loc[D.root=='NQ','day_edge'].iloc[0]:+.4f}")
for r in NEW:
    x = D[D.root == r].iloc[0]
    rel = x.day_edge / D.loc[D.root == "NQ", "day_edge"].iloc[0]
    print(f"    {r}: day {x.day_edge:+.4f} ({rel:.2f}x NQ), night {x.night_edge:+.4f}, {x.reading}, "
          f"{'clears' if null[r]['clears'] else 'INSIDE'} its own rotation null")
print(f"\n  {(time.time()-t0)/60:.1f} min")
