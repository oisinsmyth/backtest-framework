"""D280 PRE-CHECK, part 2 -- the principal's reparameterisation, tested directly.

    uv run python scripts/d280_delta_range_precheck.py

NOTHING HERE SCORES A CELL. Measurement only, same standing as part 1.

THE PROPOSED CHANGE, and it is a better parameterisation than part 1's:

    open(t+1) := close(t)                  anchored, not forecast
    delta     := close(t+1) - open(t+1)    the BODY -- this is the return
    high, low  forecast around that anchor

Part 1 forecast four LEVELS independently, which spends a degree of freedom on
`open` that the market hands you for free. This tests the reparameterisation on
its own terms and separates two questions part 1 ran together.

QUESTION 1 -- IS THE ANCHOR EVEN TRUE? `open(t+1) = close(t)` is exact only if
there is no overnight gap. The gap is measured here rather than assumed, because
if it is large the anchor is not free -- it is an unforecast term smuggled in.

QUESTION 2 -- DIRECTION vs RANGE, and this is the point of the exercise.

  DELTA is a DIRECTION problem. Part 1 already found naive persistence
  (delta = 0) beats every DEMA variant at predicting close(t+1), so the
  expectation here is failure. It is re-run in delta coordinates anyway,
  because "you tested it in the wrong coordinates" is a fair objection and
  costs one measurement to remove.

  RANGE (high - low) is a VOLATILITY problem, and volatility is autocorrelated
  where returns are not. **This is the part that has never been tested in this
  programme and is genuinely likely to succeed.**

WHAT SUCCESS WOULD AND WOULD NOT BUY. A working range forecast does NOT fix a
-0.432 gross Sharpe, because it carries no direction -- it cannot tell you which
name to short. What it could feed is SIZING or STOP PLACEMENT, which is a
different study with a different hurdle. That distinction is drawn here, before
the numbers, so a good range number is not later read as a directional edge.

  WICK ASYMMETRY is the one place range work could carry direction: if the
  upper wick (high - max(open,close)) and lower wick systematically differ
  before a fall, that is directional intrabar information a close-to-close
  series discards entirely. Tested, and declared as a long shot.

Baselines are the honest ones throughout: persistence for range, zero for delta,
and the |0.02| tradeability threshold from part 1.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
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


B = _load("d256", "run_book_single_names.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
RP = B.RP

OUT = REPO / "data" / "d280_delta_range_precheck.json"
N_GRID, SPLIT_DATE = P1.N_GRID, P1.SPLIT_DATE
ema, d1, skill = P1.ema, P1.d1, P1.skill


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    dates = np.array(panel.dates)
    oos_m = live & (dates >= SPLIT_DATE)[None, :]
    O, H, L, Cl = g["open"], g["high"], g["low"], g["close"]
    print(f"loaded {time.time() - t0:.0f}s\n", flush=True)

    def nxt(x):
        out = np.full_like(x, np.nan)
        ok = live[:, 1:] & live[:, :-1]
        out[:, :-1] = np.where(ok, x[:, 1:], np.nan)
        return out

    # ---- QUESTION 1: is open(t+1) = close(t) actually free? ----
    gap = (nxt(O) / Cl - 1.0)
    m = oos_m & np.isfinite(gap)
    ret_n = nxt(np.expm1(panel.total_log_returns) * 0 + np.expm1(panel.total_log_returns))
    body_n = (nxt(Cl) / nxt(O) - 1.0)
    mb = oos_m & np.isfinite(body_n) & np.isfinite(gap)
    print("  Q1 -- THE ANCHOR. open(t+1) vs close(t), out of sample:")
    print(f"     median |gap|      {np.median(np.abs(gap[m])):.4%}")
    print(f"     mean   |gap|      {np.abs(gap[m]).mean():.4%}")
    print(f"     |gap| / |body|    "
          f"{np.abs(gap[mb]).mean() / np.abs(body_n[mb]).mean():.3f}"
          "   <-- 0 would make the anchor free; 1 means half the move is the gap")
    print(f"     corr(gap, body)   {np.corrcoef(gap[mb], body_n[mb])[0, 1]:+.4f}\n",
          flush=True)

    results = {"gap_median_abs": float(np.median(np.abs(gap[m]))),
               "gap_mean_abs": float(np.abs(gap[m]).mean()),
               "gap_over_body": float(np.abs(gap[mb]).mean() / np.abs(body_n[mb]).mean()),
               "corr_gap_body": float(np.corrcoef(gap[mb], body_n[mb])[0, 1])}

    # ---- QUESTION 2a: DELTA, in the principal's coordinates ----
    print("  Q2a -- DELTA (direction). MAE skill vs the honest baseline delta = 0,")
    print("         and corr with the actual next-bar return. |corr| < 0.02 is untradeable.\n")
    print(f"  {'n':>4s} {'forecast':>16s} {'MAE skill':>11s} {'corr':>10s}")
    delta_true = nxt(Cl) - Cl
    for n in N_GRID:
        e1 = ema(Cl, live, n)
        dema = 2.0 * e1 - ema(e1, live, n)
        v, = (d1(dema, live),)
        a = d1(v, live)
        j = d1(a, live)
        for label, f in (("v", v), ("v+a", v + a / 2.0),
                         ("v+a+j", v + a / 2.0 + j / 6.0)):
            s, _ = skill(f - delta_true, 0.0 - delta_true, oos_m)
            mm = oos_m & np.isfinite(f) & np.isfinite(delta_true)
            r = float(np.corrcoef(f[mm] / Cl[mm], delta_true[mm] / Cl[mm])[0, 1])
            results[f"delta|n{n}|{label}"] = {"mae_skill": s, "corr": r}
            print(f"  {n:4d} {label:>16s} "
                  f"{(f'{s:+.4f}' if s is not None else '—'):>11s} {r:+10.4f}",
                  flush=True)
    print()

    # ---- QUESTION 2b: RANGE, the volatility question ----
    print("  Q2b -- RANGE (high - low). MAE skill vs persistence, out of sample.")
    print("         THIS IS THE ONE EXPECTED TO WORK, and it carries NO direction.\n")
    print(f"  {'n':>4s} {'forecast':>16s} {'MAE skill':>11s} {'corr':>10s}")
    rng = H - L
    rng_true = nxt(rng)
    for n in N_GRID:
        e1 = ema(rng, live, n)
        dema = 2.0 * e1 - ema(e1, live, n)
        v = d1(dema, live)
        a = d1(v, live)
        for label, f in (("DEMA only", dema), ("+v", dema + v),
                         ("+v+a", dema + v + a / 2.0)):
            s, _ = skill(f - rng_true, rng - rng_true, oos_m)
            mm = oos_m & np.isfinite(f) & np.isfinite(rng_true)
            r = float(np.corrcoef(f[mm], rng_true[mm])[0, 1])
            results[f"range|n{n}|{label}"] = {"mae_skill": s, "corr": r}
            print(f"  {n:4d} {label:>16s} "
                  f"{(f'{s:+.4f}' if s is not None else '—'):>11s} {r:+10.4f}",
                  flush=True)
    print()

    # ---- QUESTION 2c: WICK ASYMMETRY, the long shot ----
    print("  Q2c -- WICK ASYMMETRY (the long shot: does intrabar shape carry DIRECTION?)")
    print("         corr with the actual next-bar return; |corr| < 0.02 is untradeable.\n")
    body_hi = np.maximum(O, Cl)
    body_lo = np.minimum(O, Cl)
    upper, lower = H - body_hi, body_lo - L
    ret_next = nxt(np.expm1(panel.total_log_returns))
    feats = {"upper wick / range": upper / np.where(rng > 0, rng, np.nan),
             "lower wick / range": lower / np.where(rng > 0, rng, np.nan),
             "wick asymmetry": (upper - lower) / np.where(rng > 0, rng, np.nan),
             "body / range": (Cl - O) / np.where(rng > 0, rng, np.nan),
             "close position in range": (Cl - L) / np.where(rng > 0, rng, np.nan)}
    print(f"  {'feature':>26s} {'corr':>10s} {'bars':>13s}")
    for label, f in feats.items():
        mm = oos_m & np.isfinite(f) & np.isfinite(ret_next)
        r = float(np.corrcoef(f[mm], ret_next[mm])[0, 1])
        results[f"wick|{label}"] = {"corr": r, "bars": int(mm.sum())}
        print(f"  {label:>26s} {r:+10.4f} {int(mm.sum()):13,d}", flush=True)

    json.dump({"purpose": ("part 2 of the D280 pre-check, in the anchored "
                           "open/delta/range parameterisation; scores no cell"),
               "split_date": SPLIT_DATE, "results": results,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
