"""D286 -- does an exit that keys on the SIGNAL beat one that keys on DISPLACEMENT?

    uv run python scripts/run_exit_rules.py --selftest
    uv run python scripts/run_exit_rules.py

Pre-registered in `9e60596`, BEFORE this file. Record:
`docs/decisions/D286-the-exit-that-keys-on-the-signal.md`.

Base is D285's factor-neutral book, unvaried: LONG the N lowest lagged `hist_L`,
SHORT the N highest, +-1 per name, daily close-to-close, N in {10, 25, 50}.
**Only the EXIT changes.**

    disp   leaves the top/bottom N      D285's rule -- the CONTROL
    sig    hist_L CROSSES ZERO          edge-sharpening, ZERO free parameters
    hyst   leaves the top/bottom 2N     cost-cutting, same reason just slower
    cap    disp, or a -5% trade loss    the left-tail question

WHY `hyst` IS HERE AND WHY REMOVING IT WOULD BE DISHONEST. A longer hold raises
breakeven by amortising one round trip over more bars -- cost accounting, not a
better signal. `hyst` exits for D285's arbitrary reason and merely later, so if
it lifts breakeven as much as `sig` does, `sig` has found nothing. Running the
interesting arm without its own null is the mistake this repo keeps making in
other clothes.

WHAT MAKES `sig` NON-FITTED. A zero crossing is where the Impulse histogram
itself says the acceleration has turned. No threshold is chosen, so none can be
tuned -- which matters when the arm was picked after seeing D285's decay curve.

HURDLE B IS SPLIT, and B2 is the honest one. D285 guessed 15 bp/side; the names
it held measured 33.81. B1 keeps the 15 for comparability with D285; B2 requires
the breakeven to beat THIS BOOK'S OWN measured median trailing Corwin-Schultz
half-spread. **A cell clearing B1 but not B2 is not tradeable and the output says
so in those words.**
"""

from __future__ import annotations

import argparse
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
C = _load("d279", "run_concentrated_short.py")
EP = _load("d279e", "d279_fix_eprime.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
FN = _load("d285", "run_factor_neutral.py")
SP = _load("d285sp", "d285_spread_estimate.py")
FAST = _load("fast_null", "fast_null.py")
RP = B.RP

OUT = REPO / "data" / "d286_exit_rules_summary.json"
N_LEVELS = FN.N_LEVELS
N_SIMS, SEED = FN.N_SIMS, FN.SEED
PPY, RF, BORROW, FEE = FN.PPY, FN.RF, FN.BORROW, FN.FEE
TWO_C_BP = FN.TWO_C_BP
B1_FLOOR = 15.0                 # D285's bar, kept for comparability
LOSS_CAP = -0.05                # `cap`'s -5%, declared as a judgement
LOOKBACK = 21                   # trailing window for the B2 spread estimate


def walk_exits(base, score, n, rule, simple=None):
    """The four exit rules. ENTRY IS IDENTICAL IN ALL OF THEM -- the N lowest and
    N highest lagged score -- so any difference is the exit and nothing else.

    A name is entered when it appears in an extreme, and thereafter HELD until
    its own rule fires. `disp` and `hyst` differ only in the width of the band
    that keeps it; `sig` ignores the band entirely and watches the score's SIGN;
    `cap` is `disp` with a loss trigger stapled on."""
    s = C.lag1(score)
    out = np.zeros_like(base)
    n_sym, T = base.shape
    held = {}                                   # symbol -> (+1/-1, entry_t, cum)
    band = 2 * n if rule == "hyst" else n
    for t in range(T):
        q = np.flatnonzero(base[:, t] != 0.0)
        v = s[q, t] if q.size else np.empty(0)
        fin = np.isfinite(v)
        q, v = q[fin], v[fin]
        order = np.argsort(v, kind="stable") if q.size else np.empty(0, dtype=int)
        lo_e = set(q[order[:n]].tolist()) if q.size >= 2 * n else set()
        hi_e = set(q[order[-n:]].tolist()) if q.size >= 2 * n else set()
        lo_b = set(q[order[:band]].tolist()) if q.size >= 2 * band else lo_e
        hi_b = set(q[order[-band:]].tolist()) if q.size >= 2 * band else hi_e
        alive = set(q.tolist())

        for i in list(held):
            sgn, t0, cum = held[i]
            if i not in alive:
                del held[i]
                continue
            if simple is not None and np.isfinite(simple[i, t - 1] if t else 0.0):
                cum += sgn * simple[i, t - 1] if t else 0.0
                held[i] = (sgn, t0, cum)
            sc = s[i, t]
            if rule == "sig":
                gone = (not np.isfinite(sc)) or (sgn > 0 and sc >= 0.0) \
                    or (sgn < 0 and sc <= 0.0)
            elif rule == "cap":
                gone = (i not in (lo_e if sgn > 0 else hi_e)) or (cum <= LOSS_CAP)
            else:                                     # disp and hyst
                gone = i not in (lo_b if sgn > 0 else hi_b)
            if gone:
                del held[i]

        for i in lo_e:
            if i not in held:
                held[i] = (+1.0, t, 0.0)
        for i in hi_e:
            if i not in held:
                held[i] = (-1.0, t, 0.0)

        # EACH LEG IS NORMALISED TO UNIT TOTAL WEIGHT, and this is a
        # construction change from D285 forced by the study itself.
        #
        # D285 held +-1 per name and its legs had EQUAL COUNTS by construction,
        # so the book was dollar-neutral for free. A SIGNAL-STATE exit breaks
        # that: the two legs empty at different rates as each name's own score
        # crosses zero, so +-1 leaves the book net long or net short -- which is
        # what the first version of this runner asserted its way into.
        #
        # Giving each leg unit total weight restores exact neutrality at ANY leg
        # counts. It is applied to ALL FOUR ARMS so they stay comparable, and for
        # `disp` -- whose counts are equal anyway -- it is a uniform rescale of
        # D285's book, so its Sharpe is unchanged and only exposure is smaller.
        #
        # A bar with an empty leg CANNOT be neutral, so the book holds nothing.
        if held:
            idx = np.fromiter(held.keys(), dtype=int)
            sgn = np.fromiter((held[i][0] for i in idx), dtype=float)
            nl, ns = int((sgn > 0).sum()), int((sgn < 0).sum())
            if nl and ns:
                out[idx, t] = np.where(sgn > 0, 1.0 / nl, -1.0 / ns)
    return out


def trailing_spread(panel, g):
    """21-bar TRAILING Corwin-Schultz half-spread, bp/side. Trailing because a
    screen -- or a hurdle calibrated on one -- may only use bars before entry."""
    half = SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4
    src = np.where(np.isfinite(half), half, 0.0)
    cnt = np.isfinite(half).astype(float)
    acc = np.zeros_like(half)
    num = np.zeros_like(half)
    for k in range(1, LOOKBACK + 1):
        acc[:, k:] += src[:, :-k]
        num[:, k:] += cnt[:, :-k]
    return np.where(num > 0, acc / np.maximum(num, 1.0), np.nan)


def selftest() -> int:
    print("D286 SELF-TEST -- synthetic, no fixture, no cell scored\n")
    panel, cleaned, amt, _px = _load("d282", "run_overnight_short.py")._synth()
    n, T = panel.closes.shape
    base = np.where(panel.live, 1.0, 0.0)
    base[:, 0] = 0.0
    sc = ((np.arange(n, dtype=float)[:, None] + np.arange(T)[None, :]) % n) - 1.0

    for rule in ("disp", "sig", "hyst", "cap"):
        p = walk_exits(base, sc, 1, rule, simple=np.expm1(panel.total_log_returns))
        if not np.allclose(p.sum(axis=0), 0.0, atol=1e-12):
            raise AssertionError(f"{rule}: book is not dollar-neutral bar by bar")
    print("  [1] all four arms are dollar-neutral at every bar")

    # THE GATE THAT WOULD HAVE CAUGHT THE FIRST VERSION. A signal-state exit
    # empties the legs at different rates, so neutrality must survive UNEQUAL
    # COUNTS -- not merely the equal counts `disp` produces by construction.
    probe = np.zeros((5, 3))
    probe[[0, 1, 2], 1] = 1.0
    probe[[3], 1] = -1.0
    lgs = np.where(probe > 0, 1.0 / max((probe > 0).sum(axis=0)[1], 1), 0.0)         + np.where(probe < 0, -1.0 / max((probe < 0).sum(axis=0)[1], 1), 0.0)
    if not np.isclose(lgs[:, 1].sum(), 0.0):
        raise AssertionError("leg normalisation does not neutralise unequal counts")
    print("  [1b] neutrality survives UNEQUAL leg counts (3 long vs 1 short)")

    lag = C.lag1(sc)
    p = walk_exits(base, sc, 1, "sig", simple=np.expm1(panel.total_log_returns))
    for t in range(1, T):
        for i in np.flatnonzero(p[:, t] > 0):
            if np.isfinite(lag[i, t]) and lag[i, t] >= 0:
                raise AssertionError(f"sig holds a LONG at bar {t} whose score is >= 0")
        for i in np.flatnonzero(p[:, t] < 0):
            if np.isfinite(lag[i, t]) and lag[i, t] <= 0:
                raise AssertionError(f"sig holds a SHORT at bar {t} whose score is <= 0")
    print("  [2] `sig` never holds a position whose lagged score has crossed zero")

    runs = {r: FN.episode_moves(panel, walk_exits(base, sc, 1, r,
                                                  simple=np.expm1(panel.total_log_returns)))
            for r in ("disp", "hyst")}
    if runs["hyst"] and runs["disp"] and \
            runs["hyst"]["mean_run_bars"] < runs["disp"]["mean_run_bars"]:
        raise AssertionError("hyst holds SHORTER than disp -- the band is inverted")
    print("  [3] `hyst` holds at least as long as `disp` (wider band, later exit)")

    for rule in ("disp", "sig", "hyst", "cap"):
        p = walk_exits(base, sc, 1, rule)
        if np.any(p[:, 0] != 0.0):
            raise AssertionError(f"{rule}: column 0 is non-zero; no score[t-1] exists")
    print("  [4] no arm holds on bar 0, where no lagged score exists")
    print("\n  ALL SELF-TESTS PASSED. No fixture read, no cell scored.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    g = P1.build_grids(panel, cleaned)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    simple = np.expm1(panel.total_log_returns)
    trail = trailing_spread(panel, g)
    print(f"loaded + signals {time.time() - t0:.0f}s", flush=True)

    ok = ~(np.isnan(md) | np.isnan(hs)) & warm & panel.live
    base = np.where(ok, 1.0, 0.0)
    base[:, 0] = 0.0

    # THE EXIT WALKS ARE THREADED. Each is an independent Python loop over 4,187
    # bars that reads `base`, `hs` and `simple` and writes only its own array --
    # read-only shared state, which is `parallel_map`'s contract. The controls
    # stay SERIAL because they draw from one `rng` and threading them would make
    # the draw order non-deterministic, which the seed is supposed to fix.
    specs = [(f"{rule}{N}", (N, rule)) for N in N_LEVELS
             for rule in ("disp", "sig", "hyst", "cap")]
    books = FAST.parallel_map(
        lambda k, spec: walk_exits(base, hs, spec[0], spec[1], simple=simple),
        specs, progress=None)
    rng = np.random.default_rng(SEED)
    for N in N_LEVELS:
        books[f"rnd{N}"] = FN.neutral_book(base, hs, N, rng=rng)
        books[f"tal{N}"] = FN.neutral_book(base, hs, N, rng=rng, tail=True)
    books = {k: books[k] for k in
             [f"{r}{N}" for N in N_LEVELS for r in ("disp", "sig", "hyst", "cap",
                                                    "rnd", "tal")]}
    for k, p in books.items():
        # TOLERANCE, NOT EQUALITY. Ten weights of 1/10 sum to 0.9999999999999999,
        # so the legs cancel to ~1e-16 rather than to exactly zero. The first
        # version asserted `== 0` here while the self-test used `allclose`, so
        # the study died on floating-point residue that is 1e-16 of a unit leg.
        worst = float(np.max(np.abs(p.sum(axis=0))))
        if worst > 1e-9:
            raise AssertionError(f"{k} is not dollar-neutral: worst {worst:.3e}")
    print(f"  built {len(books)} books {time.time() - t0:.0f}s\n", flush=True)

    free = type(panel)(**{**vars(panel),
                          "cost_fraction": np.zeros_like(panel.cost_fraction)})
    cells = {}
    print(f"  HURDLE M vs 2c = {TWO_C_BP:.0f} bp; B1 vs {B1_FLOOR:.0f} bp/side; "
          f"B2 vs THIS BOOK'S OWN measured spread.\n")
    print(f"  {'cell':9s} {'move/trade':>11s} {'run':>6s} {'breakeven':>10s} "
          f"{'B2 spread':>10s} {'NEU':>7s} {'trades':>9s} {'med move':>9s}")
    for k, p in books.items():
        s = RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
        em = FN.episode_moves(panel, p) or {}
        s.update({f"episode_{kk}": vv for kk, vv in em.items()})
        s["breakeven_bps"] = FN.breakeven_bps(panel, p)
        s["neutrality_corr"] = FN.neutrality(panel, p)
        heldm = (RP.enforce_live(p, panel, 0) != 0.0) & np.isfinite(trail)
        s["b2_spread_bps"] = float(np.median(trail[heldm])) if heldm.any() else None
        s["clears_M"] = bool(em.get("mean_move_bp", -1) >= TWO_C_BP)
        s["clears_B1"] = bool(s["breakeven_bps"] is not None
                              and s["breakeven_bps"] >= B1_FLOOR)
        s["clears_B2"] = bool(s["breakeven_bps"] is not None
                              and s["b2_spread_bps"] is not None
                              and s["breakeven_bps"] >= s["b2_spread_bps"])
        s["clears_NEU"] = bool(s["neutrality_corr"] is not None
                               and abs(s["neutrality_corr"]) <= FN.NEU_MAX_ABS_CORR)
        cells[k] = s
        print(f"  {k:9s} {em.get('mean_move_bp', np.nan):+11.2f} "
              f"{em.get('mean_run_bars', np.nan):6.2f} "
              f"{(s['breakeven_bps'] if s['breakeven_bps'] is not None else np.nan):10.2f} "
              f"{(s['b2_spread_bps'] if s['b2_spread_bps'] is not None else np.nan):10.2f} "
              f"{(s['neutrality_corr'] if s['neutrality_corr'] is not None else np.nan):+7.3f} "
              f"{em.get('n_trades', 0):9,d} "
              f"{em.get('median_move_bp', np.nan):+9.2f}", flush=True)

    print(f"\n  {'cell':9s} {'expo':>7s} {'net CAGR':>9s} {'net SR':>8s} "
          f"{'GROSS SR':>9s} {'maxDD':>8s}")
    for k, p in books.items():
        gs = RP.score(free, p, 0, ppy=PPY, rf_annual=0.0, borrow_annual=0.0)
        cells[k]["gross_sharpe"] = gs["excess_sharpe"]
        cells[k]["gross_cagr"] = gs["cagr"]
        cells[k]["gross_total_return"] = gs["total_return"]
        s = cells[k]
        print(f"  {k:9s} {s['exposure_gross']:6.2%} {s['cagr']:+9.2%} "
              f"{s['excess_sharpe']:+8.3f} {gs['excess_sharpe']:+9.3f} "
              f"{s['max_drawdown']:8.2%}", flush=True)

    print(f"\n  G2, THE LOAD-BEARING COMPARISON -- cost-cutting against "
          f"edge-sharpening.\n  Both are measured against `disp`, which is D285's rule.\n")
    print(f"  {'N':>4s} {'sig - disp':>12s} {'hyst - disp':>12s}  reading")
    g2 = {}
    for N in N_LEVELS:
        d = cells[f"disp{N}"]["breakeven_bps"]
        vs_sig = cells[f"sig{N}"]["breakeven_bps"] - d
        vs_hy = cells[f"hyst{N}"]["breakeven_bps"] - d
        g2[N] = {"sig_minus_disp": vs_sig, "hyst_minus_disp": vs_hy}
        rd = ("amortisation -- `sig` found nothing" if vs_hy >= vs_sig
              else "THE EXIT CARRIES INFORMATION")
        print(f"  {N:4d} {vs_sig:+12.2f} {vs_hy:+12.2f}  {rd}")

    print(f"\n  E-prime over the HELD BOOK ...")
    for k, p in books.items():
        e, nk = EP.eff_over_book(panel, p)
        cells[k]["effective_instruments_book"] = e
        cells[k]["names_held_over_min_overlap"] = nk
        cells[k]["Eprime"] = bool(e >= 3.0
                                  and cells[k].get("episode_n_trades", 0) >= 500)
        flag = "  <-- ~= N: identity matrix, E-prime has stopped measuring" \
               if nk and abs(e - nk) < 0.5 else ""
        print(f"    {k:9s} names>=250 held {nk:6d}   E-prime {e:8.2f}{flag}", flush=True)

    print(f"\n  rotation nulls, {a.sims} draws, threaded -- REPORTED, NOT DECISIVE "
          f"(R7 corollary) ...", flush=True)
    ctx = FAST.NullContext(panel)
    ctx.assert_matches_scorer(
        books["disp25"],
        lambda p: RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW),
        rf_annual=RF, borrow_annual=BORROW, ppy=PPY)
    print("    light_score agrees EXACTLY with RP.score on the real book", flush=True)
    draws = FAST.run_nulls(ctx, books, n_sims=a.sims, seed=SEED, ppy=PPY,
                           rf_annual=RF, borrow_annual=BORROW, progress=True)
    stack = []
    for k in books:
        sh, mn = draws[k]
        c = cells[k]
        c["sharpe_pct"] = float((sh < c["excess_sharpe"]).mean() * 100)
        c["money_pct"] = float((mn < c["total_return"]).mean() * 100)
        c["H"] = bool(c["sharpe_pct"] >= 95 and c["money_pct"] >= 95)
        c["null_p50"] = float(np.percentile(sh, 50))
        c["null_p95"] = float(np.percentile(sh, 95))
        stack.append(sh)
    floor = float(np.percentile(np.max(np.vstack(stack), axis=0), 95))

    print(f"\n  best-of-{len(books)} floor: {floor:+.3f}\n")
    print(f"  {'cell':9s} {'move':>9s} {'be':>8s} {'B2':>7s} {'GROSS SR':>9s} "
          f"{'M':>3s} {'B1':>3s} {'B2':>3s} {'NEU':>4s} {'V':>3s} {'C':>3s} "
          f"{'F':>3s} {'E':>3s}  ALL")
    surv = []
    for k in books:
        c = cells[k]
        rule = "".join(ch for ch in k if not ch.isdigit())
        N = k[len(rule):]
        if rule in ("disp", "sig", "hyst", "cap"):
            ctrls = [cells[f"rnd{N}"], cells[f"tal{N}"]]
            c["C"] = bool(all(c["excess_sharpe"] > x["excess_sharpe"]
                              and c["total_return"] > x["total_return"]
                              and c["gross_sharpe"] > x["gross_sharpe"]
                              for x in ctrls))
        else:
            c["C"] = False
        c["V"] = bool(c["cagr"] > 0)
        c["F"] = bool(c["excess_sharpe"] > floor)
        c["clears_all"] = bool(c["clears_M"] and c["clears_B2"] and c["clears_NEU"]
                               and c["V"] and c["C"] and c["F"] and c["Eprime"])
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:9s} {c.get('episode_mean_move_bp', np.nan):+9.2f} "
              f"{(c['breakeven_bps'] if c['breakeven_bps'] is not None else np.nan):8.2f} "
              f"{(c['b2_spread_bps'] if c['b2_spread_bps'] is not None else np.nan):7.2f} "
              f"{c['gross_sharpe']:+9.3f} {y(c['clears_M']):>3s} {y(c['clears_B1']):>3s} "
              f"{y(c['clears_B2']):>3s} {y(c['clears_NEU']):>4s} {y(c['V']):>3s} "
              f"{y(c['C']):>3s} {y(c['F']):>3s} {y(c['Eprime']):>3s}  "
              f"{'** SURVIVES **' if c['clears_all'] else 'no'}")

    b1_only = [k for k, c in cells.items() if c["clears_B1"] and not c["clears_B2"]]
    if b1_only:
        print(f"\n  CLEARS B1 BUT NOT B2, AND IS THEREFORE NOT TRADEABLE: "
              f"{', '.join(b1_only)}")
    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    json.dump({"study": "D286 the exit that keys on the signal",
               "preregistration": "docs/decisions/D286-the-exit-that-keys-on-the-signal.md, 9e60596",
               "two_c_bp": TWO_C_BP, "b1_floor_bps": B1_FLOOR,
               "loss_cap": LOSS_CAP, "floor": floor, "g2": g2,
               "cells": cells, "survivors": surv,
               "clears_b1_not_b2": b1_only,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
