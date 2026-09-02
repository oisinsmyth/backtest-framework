"""D280 PRE-CHECK -- can a DEMA derivative stack forecast the next bar at all?

    uv run python scripts/d280_forecast_precheck.py

NOTHING HERE SCORES A CELL, RANKS A NAME OR PROPOSES A RULE. It is a measurement
instrument in the sense `d268_score_independence.py` is one, and it runs before
any pre-registration because it decides whether there is anything to
pre-register.

WHY IT EXISTS. D279's top-N ranking was look-ahead: it ranked with `hist_L` at
bar t and earned bar t's return. The honest repair is not to abandon ranking but
to FORECAST the score one bar ahead from information through t-1 and trade it at
t. That is exactly "the next bar in the sequence", and it is R9-clean by
construction.

THE BAR THE FORECAST HAS TO CLEAR, from the corrected D279 decomposition, in
GROSS Sharpe at zero fees / zero borrow / zero rf:

    random selection, matched turnover      -0.635
    + the hist_L ranking as it stands       +0.203   ->  -0.432
    still needed to reach BREAKEVEN GROSS   +0.432
    and only then do costs get charged      +0.206

**A better score must contribute more than TWICE what the entire existing
ranking does, merely to reach zero before costs.** That is the target, and it is
why this pre-check is worth running before anything is built.

THE CONSTRUCTION UNDER TEST, and every weight in it is FIXED, not fitted
---------------------------------------------------------------------------
For each candle component c in {open, high, low, close}:

    DEMA_n(c) = 2*EMA_n(c) - EMA_n(EMA_n(c))     lag-reduced level
    v = DEMA(t)   - DEMA(t-1)                     velocity
    a = v(t)      - v(t-1)                        acceleration
    j = a(t)      - a(t-1)                        jerk
    c_hat(t+1) = DEMA(t) + v + a/2 + j/6          Taylor extrapolation

Taylor's 1, 1, 1/2, 1/6 are used UNFITTED so this pre-check cannot overfit. If
it needs fitted weights to work, that is a different study with a train/test
split, and this one will have said so.

n is reported over a FIXED, DECLARED grid {9, 21, 34} -- 34 and 9 because the
strategy under repair is Impulse MACD 34/9, 21 as a midpoint. All three are
reported; none is selected.

WHAT WOULD KILL IT, declared before the numbers are read
--------------------------------------------------------
  G1  If Taylor extrapolation does not beat NAIVE PERSISTENCE (c_hat = c(t)) at
      predicting c(t+1) out of sample, every derivative term is noise and the
      construction is dead. Each difference of a white series multiplies noise
      variance by C(2k,k): velocity x2, acceleration x6, JERK x20. The jerk term
      is the most likely thing to sink this.

  G2  If the forecast RETURN has no correlation with the actual next-bar return,
      nothing built on it can trade. The baseline it must beat is the honest
      lagged score, measured in D279 at corr = -0.0103. Below |0.02| is not
      tradeable at any size.

  G3  If the 16 terms collapse below 3 effective inputs, then "four components"
      is one component in costume -- D268 found nine price scores carry 2.87
      effective inputs, and O/H/L/C are far more collinear than those nine.
      The one thing that could save it: range (H-L), body (C-O) and wick
      asymmetry carry INTRABAR information that close-to-close discards, and
      that axis is genuinely untested in this programme.
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
RP = B.RP

OUT = REPO / "data" / "d280_forecast_precheck.json"
N_GRID = (9, 21, 34)
COMPONENTS = ("open", "high", "low", "close")
# The span is split so G1 and G2 are reported OUT OF SAMPLE even though nothing
# is fitted. A parameter-free rule cannot overfit, but the split costs nothing
# and removes the objection before it is made.
SPLIT_DATE = "2018-01-01"


def ema(x, live, n):
    """EMA down the time axis, advancing state only on a symbol's LIVE bars.

    A ragged panel has NaN outside each name's window and 134 names carry
    internal holes. Advancing the recursion through those would blend a price
    across a gap, which is the ETF spin-off failure mode in a different costume."""
    alpha = 2.0 / (n + 1.0)
    out = np.full_like(x, np.nan)
    state = np.full(x.shape[0], np.nan)
    for t in range(x.shape[1]):
        col, lv = x[:, t], live[:, t]
        fresh = lv & np.isnan(state)
        state = np.where(fresh, col,
                         np.where(lv, alpha * col + (1 - alpha) * state, state))
        out[:, t] = np.where(lv, state, np.nan)
    return out


def d1(x, live):
    """First difference within the live window; NaN at a window's first bar."""
    out = np.full_like(x, np.nan)
    ok = live[:, 1:] & live[:, :-1]
    out[:, 1:] = np.where(ok, x[:, 1:] - x[:, :-1], np.nan)
    return out


def build_grids(panel, cleaned):
    """(n, T) grids for each OHLC component, aligned to the panel's date grid."""
    pos = {d: i for i, d in enumerate(panel.dates)}
    n, T = panel.closes.shape
    g = {c: np.full((n, T), np.nan) for c in COMPONENTS}
    for i, s in enumerate(panel.symbols):
        for st in cleaned[s]:
            t = pos[st.timestamp[:10]]
            b = st.bar
            g["open"][i, t], g["high"][i, t] = b.open, b.high
            g["low"][i, t], g["close"][i, t] = b.low, b.close
    return g


def skill(err_model, err_base, mask):
    """1 - MAE(model)/MAE(base). Positive means the model beats the baseline."""
    m = mask & np.isfinite(err_model) & np.isfinite(err_base)
    if m.sum() < 1000:
        return None, int(m.sum())
    a, b = np.abs(err_model[m]).mean(), np.abs(err_base[m]).mean()
    return (float(1.0 - a / b) if b > 0 else None), int(m.sum())


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    g = build_grids(panel, cleaned)
    print(f"loaded {time.time() - t0:.0f}s   {len(panel.symbols)} names x "
          f"{len(panel.dates):,} bars\n", flush=True)

    dates = np.array(panel.dates)
    oos = np.zeros(len(dates), dtype=bool)
    oos[dates >= SPLIT_DATE] = True
    oos_m = live & oos[None, :]
    print(f"  out-of-sample span from {SPLIT_DATE}: "
          f"{int(oos.sum()):,} of {len(dates):,} bars\n", flush=True)

    # actual next-bar values, and the next-bar return the forecast must predict
    nxt = {c: np.full_like(g[c], np.nan) for c in COMPONENTS}
    for c in COMPONENTS:
        ok = live[:, 1:] & live[:, :-1]
        nxt[c][:, :-1] = np.where(ok, g[c][:, 1:], np.nan)
    ret_next = np.full_like(g["close"], np.nan)
    ok = live[:, 1:] & live[:, :-1]
    ret_next[:, :-1] = np.where(ok, np.expm1(panel.total_log_returns[:, 1:]), np.nan)

    results = {}
    print(f"  G1 -- MAE skill vs NAIVE PERSISTENCE at predicting c(t+1), "
          f"out of sample.\n     positive = the model wins. "
          f"'DEMA only' drops v, a and j.\n")
    print(f"  {'n':>4s} {'component':>10s} {'DEMA only':>11s} {'+v':>9s} "
          f"{'+v+a':>9s} {'+v+a+j (full)':>15s}")
    for n in N_GRID:
        for c in COMPONENTS:
            x = g[c]
            e1 = ema(x, live, n)
            dema = 2.0 * e1 - ema(e1, live, n)
            v = d1(dema, live)
            a = d1(v, live)
            j = d1(a, live)
            cand = {"dema": dema, "v": dema + v, "va": dema + v + a / 2.0,
                    "vaj": dema + v + a / 2.0 + j / 6.0}
            base_err = x - nxt[c]                      # naive persistence
            row = {}
            for k, f in cand.items():
                s, cnt = skill(f - nxt[c], base_err, oos_m)
                row[k] = s
            results[f"G1|n{n}|{c}"] = row
            fmt = lambda z: f"{z:+.4f}" if z is not None else "     —"  # noqa: E731
            print(f"  {n:4d} {c:>10s} {fmt(row['dema']):>11s} {fmt(row['v']):>9s} "
                  f"{fmt(row['va']):>9s} {fmt(row['vaj']):>15s}", flush=True)
        print()

    print(f"  G2 -- corr(forecast return, ACTUAL next-bar return), out of sample.\n"
          f"     baseline to beat: the honest lagged hist_L at -0.0103.\n"
          f"     |corr| below 0.02 is not tradeable at any size.\n")
    print(f"  {'n':>4s} {'forecast':>16s} {'corr':>10s} {'bars':>12s}")
    for n in N_GRID:
        e1 = ema(g["close"], live, n)
        dema = 2.0 * e1 - ema(e1, live, n)
        v = d1(dema, live)
        a = d1(v, live)
        j = d1(a, live)
        for label, f in (("DEMA only", dema), ("+v", dema + v),
                         ("+v+a", dema + v + a / 2.0),
                         ("+v+a+j (full)", dema + v + a / 2.0 + j / 6.0)):
            fr = f / g["close"] - 1.0            # forecast return from today's close
            m = oos_m & np.isfinite(fr) & np.isfinite(ret_next)
            if m.sum() < 1000:
                continue
            r = float(np.corrcoef(fr[m], ret_next[m])[0, 1])
            results[f"G2|n{n}|{label}"] = {"corr": r, "bars": int(m.sum())}
            print(f"  {n:4d} {label:>16s} {r:+10.4f} {int(m.sum()):12,d}", flush=True)
    # the trivial baseline, so G2 is read against something
    m = oos_m & np.isfinite(panel.total_log_returns) & np.isfinite(ret_next)
    r_mom = float(np.corrcoef(np.expm1(panel.total_log_returns)[m], ret_next[m])[0, 1])
    results["G2|baseline_momentum"] = r_mom
    print(f"  {'':4s} {'return(t) alone':>16s} {r_mom:+10.4f}   <-- trivial baseline\n")

    print(f"  G3 -- effective independent inputs among the 16 terms "
          f"(D268's instrument, R10's count).\n")
    for n in N_GRID:
        feats, names = [], []
        for c in COMPONENTS:
            e1 = ema(g[c], live, n)
            dema = 2.0 * e1 - ema(e1, live, n)
            v = d1(dema, live)
            a = d1(v, live)
            j = d1(a, live)
            for lab, arr in (("lvl", dema), ("v", v), ("a", a), ("j", j)):
                feats.append(arr)
                names.append(f"{c[:1].upper()}.{lab}")
        M = np.stack([f[oos_m] for f in feats], axis=1)
        keep = np.all(np.isfinite(M), axis=1)
        M = M[keep]
        M = (M - M.mean(axis=0)) / np.where(M.std(axis=0) > 0, M.std(axis=0), 1.0)
        R = np.corrcoef(M, rowvar=False)
        eff = float(len(names) ** 2 / R.sum())
        results[f"G3|n{n}"] = {"effective_inputs": eff, "terms": len(names),
                               "rows": int(keep.sum())}
        print(f"  n={n:<3d}  {len(names)} terms -> {eff:5.2f} effective inputs   "
              f"({keep.sum():,} complete rows)", flush=True)

    json.dump({"purpose": ("pre-check for the DEMA derivative forecast; scores no "
                           "cell, ranks no name, proposes no rule"),
               "split_date": SPLIT_DATE, "n_grid": list(N_GRID),
               "weights": "Taylor 1, 1, 1/2, 1/6 -- FIXED, not fitted",
               "gross_gap_to_close": 0.432, "results": results,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
