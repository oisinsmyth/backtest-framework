"""D330 Part A -- how much of EVERY leg is a pinned takeover target? Diagnostic.

    uv run python scripts/run_d330a_pinned_decomposition.py

PRE-REGISTERED AT `112bebd`, committed before this file existed (R8).

LOOK-AHEAD, AND NEVER SCORED. Every label here uses the future -- whether the
name is dead within 60 bars of entry, and what it returned on the way. That is
legitimate for a decomposition and illegitimate for a rule, so nothing in this
file ranks, compares to a book, or writes a prediction. Part B is the causal
instrument; it reads these labels for one purpose, to measure what fraction of
the pinned trades its filter catches.

LABELS, per trade (row, entry, age, pnl, side) on the path-invariant ledger at
DEPTH 2, k = 20 -- the ledger D329 used:
  dies      last live bar within 60 bars of entry AND not the sample end
  pinned    dies, |return to death| < 5%, median daily range while held < 0.5%
  collapse  dies, return to death < -30%
  other     dies, neither
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


V9 = _load("d329", "run_d329_legwise.py")
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X

DEPTH, K = 2, 20
DEAD_WITHIN = 60
PIN_RET, PIN_RANGE, COLLAPSE_RET = 0.05, 0.005, -0.30
EXCLUDED = V9.EXCLUDED
OUT = REPO / "data" / "d330a_pinned_decomposition.json"


def last_live_bar(finT):
    T, n = finT.shape
    ll = np.full(n, -1)
    for i in range(n):
        w = np.flatnonzero(finT[:, i])
        if w.size:
            ll[i] = w[-1]
    return ll


def label_trades(trades, r1T, RANGE, HALF, last_live, T):
    """One row per trade: (side, pnl_bp, dies, ret_to_death, range_held,
    half_at_entry, group) with group in {0 alive, 1 pinned, 2 collapse, 3 other}."""
    out = np.empty((len(trades), 7))
    for j, (row, e0, age, pnl, side) in enumerate(trades):
        ll = last_live[row]
        dies = (ll - e0) <= DEAD_WITHIN and ll < T - 1
        ret = float(np.expm1(np.log1p(np.nan_to_num(r1T[e0:ll + 1, row], nan=0.0)).sum())) \
            if dies else np.nan
        rng = float(np.nanmedian(RANGE[e0:e0 + age, row]))
        if not dies:
            grp = 0
        elif abs(ret) < PIN_RET and rng < PIN_RANGE:
            grp = 1
        elif ret < COLLAPSE_RET:
            grp = 2
        else:
            grp = 3
        out[j] = (side, pnl * 1e4, float(dies), ret, rng, HALF[e0, row], grp)
    return out


def summarise(lab):
    """Per side: counts and P&L/half-spread by group."""
    res = {}
    for side in (0, 1):
        m = lab[:, 0] == side
        L = lab[m]
        d = {}
        d["trades"] = int(m.sum())
        d["dies_frac"] = float(L[:, 2].mean()) if L.size else np.nan
        for g, nm in ((0, "alive"), (1, "pinned"), (2, "collapse"), (3, "other")):
            mm = L[:, 6] == g
            d[nm] = dict(n=int(mm.sum()),
                         frac=float(mm.mean()) if L.size else np.nan,
                         pnl=float(L[mm, 1].mean()) if mm.any() else np.nan,
                         half=float(np.nanmedian(L[mm, 5])) if mm.any() else np.nan,
                         range_pct=float(100 * np.nanmedian(L[mm, 4])) if mm.any() else np.nan)
        d["pinned_by_return_only"] = int(((L[:, 2] > 0) & (np.abs(L[:, 3]) < PIN_RET)).sum())
        res[side] = d
    return res


def main() -> int:
    t0 = time.time()
    print("D330 A  pinned-name decomposition -- look-ahead, never scored")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    RANGE = np.ascontiguousarray(((g["high"] - g["low"]) / g["close"]).T)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    last_live = last_live_bar(finT)
    pool = [s for s in z.files if s not in ("key", "warm") and s not in EXCLUDED]
    assert len(pool) == 46
    print(f"  panel {finT.shape}, {len(pool)} signals, DEPTH {DEPTH}, k={K} "
          f"({time.time() - t0:.0f}s)")

    print("\nASSERTIONS")
    rk = Y.rank_single(z, base, "skew_63", n, T)
    _, res = V6.invariant(A, rk, finT, K, HALF)
    # P. the ledger spans the bars the labeller reads
    worst = 0.0
    for row, e0, age, pnl, side in res["trades"]:
        sgn = 1.0 if side == 0 else -1.0
        v = r1T[e0:e0 + age, row]
        worst = max(worst, abs(float(np.sum(sgn * (v - mkt[e0:e0 + age]))) - pnl))
    assert worst < 1e-12, f"[P] {worst:.2e}"
    print(f"    [P] every ledger P&L reproduced from (row, entry, age) to {worst:.1e}")
    # D. censoring -- a name alive at the sample end is never 'dying'
    i_alive = int(np.flatnonzero(last_live == T - 1)[0])
    fake = [(i_alive, T - 3, 1, 0.0, 1)]
    lab = label_trades(fake, r1T, RANGE, HALF, last_live, T)
    assert lab[0, 2] == 0.0 and lab[0, 6] == 0, "[D] a censored name was labelled dying"
    i_dead = int(np.flatnonzero((last_live > 100) & (last_live < T - 1))[0])
    lab = label_trades([(i_dead, int(last_live[i_dead]) - 3, 1, 0.0, 1)],
                       r1T, RANGE, HALF, last_live, T)
    assert lab[0, 2] == 1.0, "[D] a name dead in 3 bars was not labelled dying"
    print("    [D] CENSORING: a name alive at the sample end is not dying; one dead "
          "in 3 bars is")
    # G. the groups partition the dying trades
    lab = label_trades(res["trades"], r1T, RANGE, HALF, last_live, T)
    dying = lab[lab[:, 2] > 0]
    assert set(np.unique(dying[:, 6])) <= {1, 2, 3} and (lab[lab[:, 2] == 0, 6] == 0).all()
    print(f"    [G] pinned / collapse / other partition the {len(dying)} dying trades; "
          f"alive trades carry no group")
    # I. harness identity with D329 section 10
    S = summarise(lab)[1]
    assert (S["trades"], int(round(S["dies_frac"] * S["trades"])), S["collapse"]["n"]) \
        == (1024, 297, 0), f"[I] {S['trades']}, {S['dies_frac'] * S['trades']:.0f}, {S['collapse']['n']}"
    assert S["pinned_by_return_only"] == 284, f"[I] pinned by return {S['pinned_by_return_only']}"
    print(f"    [I] skew_63's short leg reproduces D329 section 10: 1,024 trades, 297 "
          f"dying, 284 within 5% of entry, 0 collapses; with the range condition "
          f"pinned = {S['pinned']['n']}")
    # 6. the self-test raises
    broke = False
    try:
        bad = lab.copy(); bad[0, 6] = 1; bad[0, 2] = 0
        assert not ((bad[:, 2] == 0) & (bad[:, 6] > 0)).any()
    except AssertionError:
        broke = True
    assert broke, "[6] a living trade with a dying label passed"
    print("    [6] and the check raises on a living trade given a dying label")

    # ---- the decomposition ----------------------------------------------
    ts = time.time()
    table = {}
    for j, s in enumerate(pool):
        rk = Y.rank_single(z, base, s, n, T)
        _, res = V6.invariant(A, rk, finT, K, HALF)
        lab = label_trades(res["trades"], r1T, RANGE, HALF, last_live, T)
        table[s] = summarise(lab)
        if (j + 1) % 10 == 0:
            print(f"  {j + 1}/{len(pool)} ({time.time() - ts:.0f}s)", flush=True)
    print(f"  46 signals x 2 legs labelled ({time.time() - ts:.0f}s)")

    for side, lbl in ((1, "SHORT"), (0, "LONG")):
        print(f"\n{lbl} LEGS, sorted by pinned fraction  (invariant, k=20; P&L gross bp/trade; "
              f"half = held median half-spread bp)")
        print("  %-14s %6s %6s | %6s %7s %6s | %6s %7s %6s | %6s %7s | %6s %7s %6s"
              % ("signal", "trades", "dies", "pinned", "pnl", "half",
                 "collap", "pnl", "half", "other", "pnl", "alive", "pnl", "half"))
        order = sorted(pool, key=lambda s: -table[s][side]["pinned"]["frac"])
        for s in order:
            d = table[s][side]
            print("  %-14s %6d %5.0f%% | %5.0f%% %+7.1f %6.1f | %5.0f%% %+7.1f %6.1f | "
                  "%5.0f%% %+7.1f | %5.0f%% %+7.1f %6.1f"
                  % (s, d["trades"], 100 * d["dies_frac"],
                     100 * d["pinned"]["frac"], d["pinned"]["pnl"], d["pinned"]["half"],
                     100 * d["collapse"]["frac"], d["collapse"]["pnl"], d["collapse"]["half"],
                     100 * d["other"]["frac"], d["other"]["pnl"],
                     100 * d["alive"]["frac"], d["alive"]["pnl"], d["alive"]["half"]))

    pin_s = np.array([table[s][1]["pinned"]["frac"] for s in pool])
    pin_l = np.array([table[s][0]["pinned"]["frac"] for s in pool])
    col_s = np.array([table[s][1]["collapse"]["frac"] for s in pool])
    print("\nSUMMARY (no predictions were registered for Part A)")
    print("  pinned fraction, short legs: median %.1f%%  max %.1f%% (%s)  |  long legs: median %.1f%%  max %.1f%% (%s)"
          % (100 * np.median(pin_s), 100 * pin_s.max(), pool[int(pin_s.argmax())],
             100 * np.median(pin_l), 100 * pin_l.max(), pool[int(pin_l.argmax())]))
    print("  collapse fraction, short legs: median %.1f%%  max %.1f%% (%s)"
          % (100 * np.median(col_s), 100 * col_s.max(), pool[int(col_s.argmax())]))
    print("  hist_L short leg: pinned %.1f%%  collapse %.1f%%  |  skew_63 short leg: pinned %.1f%%  collapse %.1f%%"
          % (100 * table["hist_L"][1]["pinned"]["frac"], 100 * table["hist_L"][1]["collapse"]["frac"],
             100 * table["skew_63"][1]["pinned"]["frac"], 100 * table["skew_63"][1]["collapse"]["frac"]))

    OUT.write_text(json.dumps(dict(
        note="D330 Part A: LOOK-AHEAD labels for a decomposition. Never a rule, "
             "never scored, never ranked.",
        depth=DEPTH, k=K, dead_within=DEAD_WITHIN,
        thresholds=dict(pin_ret=PIN_RET, pin_range=PIN_RANGE, collapse_ret=COLLAPSE_RET),
        pool=pool, table={s: {str(k): v for k, v in t.items()} for s, t in table.items()}),
        indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
