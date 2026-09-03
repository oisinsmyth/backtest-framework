"""D295 -- why the trailing stop loses. The edge decay curve, measured.

    uv run python scripts/d295_why_trailing_fails.py

Two candidate explanations, and they are distinguishable:

  A. THE EDGE IS FRONT-LOADED. If a position earns most of its return in the
     first few bars and nothing after, then any rule that extends the hold is
     diluting a fixed amount of edge over more exposure -- and a trailing stop,
     which by construction waits for a GIVEBACK before exiting, exits after the
     edge is gone AND after handing part of it back.
  B. IT HOLDS NAMES OUT OF SELECTION. The book is pinned to the selected 19, so
     an uncapped rule is the only kind that holds a name after the composite has
     stopped selecting it.

Measured here:

  1. mean per-bar return BY POSITION AGE, under the no-exit control -- the decay
     curve itself, with no rule interfering
  2. the same, split by whether the name is still IN the selected set that bar
  3. for the trailing stop: how its held bars distribute across age, and how
     many are spent out of selection

If the curve is flat, neither explanation holds and the loss is something else.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


E = _load("d295", "run_d295_exits.py")
R, M = E.R, E.M
OUT = REPO / "data" / "d295_why_trailing_fails.json"
MAXAGE = 25


def trace(ctx, r1, vol, rule, param, n, T):
    """Re-run the book, recording each held bar's (age, return, in-selection)."""
    by_age = {}          # age -> [signed returns]
    by_age_in = {}       # age -> [signed returns, name still selected]
    by_age_out = {}
    open_ = {"lo": {}, "hi": {}}
    for t in range(1, T):
        for side in ("lo", "hi"):
            sel, rk, prim = (ctx[side]["sel"], ctx[side]["rank"],
                             ctx[side]["primary"])
            held = open_[side]
            sgn = 1.0 if side == "lo" else -1.0
            for row in list(held):
                age, cum, pk, tgt = held[row]
                u = vol[row, t]
                u = u if (np.isfinite(u) and u > 0) else np.nan
                cap = age >= E.BASE_HOLD
                trig = False
                if rule == "trailing":
                    cap = False
                    trig = np.isfinite(u) and (pk - cum) >= param * u
                if (trig or cap) and age > 0:
                    held.pop(row)
            for row in list(held):
                if not np.isfinite(r1[row, t]):
                    held.pop(row)
            free = E.N_SLOTS - len(held)
            if free > 0:
                cand = np.flatnonzero(sel[:, t] & np.isfinite(r1[:, t]))
                if cand.size:
                    cand = cand[np.argsort(rk[cand, t], kind="stable")]
                    for row in cand:
                        if free == 0:
                            break
                        r = int(row)
                        if r in held:
                            continue
                        held[r] = [0, 0.0, 0.0, E.BASE_HOLD]
                        free -= 1
            for row in held:
                v = r1[row, t]
                st = held[row]
                st[0] += 1
                st[1] += sgn * v
                st[2] = max(st[2], st[1])
                a = min(st[0], MAXAGE)
                by_age.setdefault(a, []).append(sgn * v)
                (by_age_in if sel[row, t] else by_age_out).setdefault(
                    a, []).append(sgn * v)
    return by_age, by_age_in, by_age_out


def main() -> int:
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    n = base.shape[0]
    ctx, r1, vol, plan = E.build_inputs(z, base, panel, live, T)

    print("1. THE DECAY CURVE -- mean signed return per position-bar, BY AGE\n")
    print("   Held with NO exit rule and no cap, so the curve is the signal's")
    print("   own, not a rule's. 'in sel' = the composite still selects it.\n")
    # A never-exiting rule never turns the book over, so every bar piles into
    # the oldest bucket and there is no curve. Measure it with a LONG FIXED
    # hold instead: every position lives exactly MAXAGE bars, so each age is
    # sampled by the same population and the curve is the signal's own.
    hold = E.BASE_HOLD
    E.BASE_HOLD = MAXAGE
    try:
        ba, bin_, bout = trace(ctx, r1, vol, "none", None, n, T)
    finally:
        E.BASE_HOLD = hold
    print(f"   {'age':>4s} {'bars':>8s} {'bp/bar':>8s} | {'in sel':>8s} "
          f"{'bp':>7s} | {'out':>8s} {'bp':>7s}")
    rows = []
    for a in range(1, MAXAGE + 1):
        v = np.array(ba.get(a, []))
        if v.size < 200:
            continue
        vi = np.array(bin_.get(a, []))
        vo = np.array(bout.get(a, []))
        print(f"   {a:4d} {v.size:8d} {v.mean() * 1e4:+8.2f} | "
              f"{vi.size:8d} {(vi.mean() * 1e4 if vi.size else float('nan')):+7.2f} | "
              f"{vo.size:8d} {(vo.mean() * 1e4 if vo.size else float('nan')):+7.2f}")
        rows.append(dict(age=a, bars=int(v.size), bp=float(v.mean() * 1e4),
                         n_in=int(vi.size),
                         bp_in=float(vi.mean() * 1e4) if vi.size else None,
                         n_out=int(vo.size),
                         bp_out=float(vo.mean() * 1e4) if vo.size else None))

    early = np.concatenate([np.array(ba[a]) for a in range(1, 6) if a in ba])
    late = np.concatenate([np.array(ba[a]) for a in range(6, MAXAGE + 1)
                           if a in ba])
    print(f"\n   age 1-5   : {early.mean() * 1e4:+7.2f} bp/bar over "
          f"{early.size:,} position-bars")
    print(f"   age 6+    : {late.mean() * 1e4:+7.2f} bp/bar over "
          f"{late.size:,} position-bars")

    allin = np.concatenate([np.array(v) for v in bin_.values()])
    allout = np.concatenate([np.array(v) for v in bout.values()])
    print(f"\n2. IN SELECTION vs OUT")
    print(f"   in  : {allin.mean() * 1e4:+7.2f} bp/bar over {allin.size:,} bars")
    print(f"   out : {allout.mean() * 1e4:+7.2f} bp/bar over {allout.size:,} bars")

    print(f"\n3. WHERE EACH RULE SPENDS ITS EXPOSURE")
    print(f"   {'rule':16s} {'mean age':>9s} {'% bars age<=5':>14s} "
          f"{'% bars out of sel':>18s}")
    for rule, param, lab in (("none", None, "B0 (5-bar hold)"),
                             ("trailing", 1.0, "B4@1.0"),
                             ("trailing", 2.0, "B4@2.0")):
        ba2, bi2, bo2 = trace(ctx, r1, vol, rule, param, n, T)
        tot = sum(len(v) for v in ba2.values())
        le5 = sum(len(ba2.get(a, [])) for a in range(1, 6))
        out = sum(len(v) for v in bo2.values())
        wm = sum(a * len(ba2.get(a, [])) for a in ba2) / max(tot, 1)
        print(f"   {lab:16s} {wm:9.2f} {le5 / max(tot, 1):13.1%} "
              f"{out / max(tot, 1):17.1%}")

    json.dump({"purpose": "D295: why the trailing stop loses -- the edge decay "
                          "curve by position age, and where each rule spends "
                          "its exposure.",
               "curve": rows,
               "in_bp": float(allin.mean() * 1e4), "in_bars": int(allin.size),
               "out_bp": float(allout.mean() * 1e4), "out_bars": int(allout.size),
               "early_bp": float(early.mean() * 1e4),
               "late_bp": float(late.mean() * 1e4)}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
