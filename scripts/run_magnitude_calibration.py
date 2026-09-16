"""D267 -- the magnitude-calibration screen. Pre-registered in
`docs/decisions/D267-the-magnitude-calibration-screen.md`, commit e35486f,
BEFORE this file was written.

    uv run python scripts/run_magnitude_calibration.py

Screens a PROPERTY OF SIGNALS, not strategies. No book is built, no rule is
proposed, no position series is scored.

THE QUESTION: does a signal's strength predict the MAGNITUDE of the forward
move? That is what selectivity needs, and it is a different property from
predicting direction. D265 derived the bar and it is a magnitude bar --
`mean move per trade >= 2c`, with the trade count cancelling and hit rate not
appearing at all.

NINE SCORES, THREE STRATA, 27 CELLS, all counted. Horizon H = 8 bars, fixed
because D265 measured the marginal edge at +0.641 bp/bar over bars 1-8 against a
CONSTANT +0.316 bp/bar variance tax.

R9 IS THE DEFECT THAT KILLED D248's MOTIVATING ANALYSIS AND IT IS HANDLED HERE:
the score is lagged one bar. `s[t-1]` decides the bucket; the forward window
starts at `t`. No bar is read that a rule could not have seen.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import structure as ST  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


R = _load("d264", "run_single_name_intraday.py")
D, M, U = R.D, R.M, R.U
pivots = R.pivots

OUT = REPO / "data" / "d267_calibration_summary.json"
RESULTS = REPO / "docs" / "results" / "MAGNITUDE_CALIBRATION_RESULTS.md"

H = 8                 # bars; D265's measured horizon, fixed and not swept
N_Q = 5               # quintiles
N_SIMS = 500          # shuffle null draws
SEED = 0

SCORES = ("impulse_hist", "impulse_md", "impulse_nodz", "macd_hist",
          "macd_line", "trailing_return", "rsi", "g_lo", "g_min")


def build_scores(panel, cleaned):
    """The nine scores, from committed primitives. Nothing is tuned."""
    n, T = panel.closes.shape
    out = {k: np.full((n, T), np.nan) for k in SCORES}
    for i, sym in enumerate(panel.symbols):
        bars = cleaned[sym]
        imp = M.impulse_macd_series(bars)
        out["impulse_hist"][i] = np.asarray(M.impulse_signal_score(imp), dtype=float)
        out["impulse_md"][i] = np.asarray(M.impulse_band_score(imp), dtype=float)
        out["impulse_nodz"][i] = np.asarray(M.impulse_no_deadzone_score(imp), dtype=float)
        mac = M.macd_series(bars)
        out["macd_hist"][i] = np.asarray(M.signal_line_score(mac), dtype=float)
        out["macd_line"][i] = np.asarray(M.zero_line_score(mac), dtype=float)
        out["trailing_return"][i] = np.asarray(
            M.trailing_return_score(bars, M.MATCHED_MOMENTUM_LOOKBACK), dtype=float)
        out["rsi"][i] = np.asarray(ST.rsi(bars), dtype=float)
        ps = pivots(bars, U.K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        g_lo, _ = U.rolling_fit(T, li,
                                np.log([p.price for p in ps if p.sign < 0])
                                if len(li) else np.array([]), U.K)
        g_hi, _ = U.rolling_fit(T, hj,
                                np.log([p.price for p in ps if p.sign > 0])
                                if len(hj) else np.array([]), U.K)
        out["g_lo"][i] = g_lo
        out["g_min"][i] = np.minimum(g_lo, g_hi)
    return out


def forward(panel, first, start):
    """Sum of the next H log returns from bar t, truncated at the session close."""
    rets = panel.total_log_returns
    n, T = rets.shape
    starts = list(np.flatnonzero(first)) + [T]
    sess_end = np.empty(T, dtype=int)
    for a, b in zip(starts[:-1], starts[1:]):
        sess_end[a:b] = b
    fwd = np.full((n, T), np.nan)
    csum = np.zeros((n, T + 1))
    csum[:, 1:] = np.cumsum(rets, axis=1)
    for t in range(start, T):
        e = min(sess_end[t], t + H)
        if e > t:
            fwd[:, t] = csum[:, e] - csum[:, t]
    return fwd


def quintile_means(score, fwd, start, n_q=N_Q):
    """Mean forward move per quintile, quintiled WITHIN each symbol.

    The score is lagged: bucket `t` on `s[t-1]`, measure the move from `t`."""
    n, T = score.shape
    buckets = [[] for _ in range(n_q)]
    for i in range(n):
        s = score[i, start - 1:T - 1]
        f = fwd[i, start:T]
        ok = np.isfinite(s) & np.isfinite(f)
        if ok.sum() < n_q * 20:
            continue
        sv, fv = s[ok], f[ok]
        edges = np.quantile(sv, np.linspace(0, 1, n_q + 1)[1:-1])
        idx = np.searchsorted(edges, sv, side="right")
        for q in range(n_q):
            buckets[q].append(fv[idx == q])
    return [np.concatenate(b) if b else np.array([]) for b in buckets]


def main() -> int:
    rng = np.random.default_rng(SEED)
    raw_panel, raw_cleaned = R.load_full()
    panel_all, cleaned_all = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    first, _ = D.session_structure(panel_all.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    cells, spreads = {}, {}
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel_all, cleaned_all) if st == "ALL"
                 else R.subset(raw_panel, raw_cleaned, R.STRATA[st]))
        sc = build_scores(p, cl)
        fwd = forward(p, first, start)
        c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
        print("=" * 92)
        print(f"{st}   cost bar 2c = {c2:.2f} bp   horizon H = {H} bars   "
              f"{len(p.symbols)} symbols")
        print("=" * 92)
        print(f"  {'score':16s} {'Q1':>8s} {'Q2':>8s} {'Q3':>8s} {'Q4':>8s} {'Q5':>8s} "
              f"{'spread':>8s} {'M1':>4s} {'M2':>4s}")
        for name in SCORES:
            qs = quintile_means(sc[name], fwd, start)
            if any(q.size == 0 for q in qs):
                print(f"  {name:16s} -- insufficient data")
                continue
            means = np.array([q.mean() for q in qs]) * 1e4
            d = np.diff(means)
            mono = bool(np.all(d > 0) or np.all(d < 0))
            extreme = means[-1] if abs(means[-1]) >= abs(means[0]) else means[0]
            m2 = bool(abs(extreme) >= c2)
            spread = float(means[-1] - means[0])
            spreads[f"{st}:{name}"] = spread
            cells[f"{st}:{name}"] = {
                "quintile_means_bp": means.tolist(), "spread_bp": spread,
                "extreme_bp": float(extreme), "cost_bar_bp": c2,
                "M1_monotone": mono, "M2_clears_bar": m2,
                "n_per_quintile": [int(q.size) for q in qs]}
            print(f"  {name:16s} " + " ".join(f"{m:7.2f}b" for m in means)
                  + f" {spread:7.2f}b {'YES' if mono else 'no':>4s} "
                    f"{'YES' if m2 else 'no':>4s}")
        print()

    # ---- M3: best-of-27 floor, ONE SHARED shuffle per simulation (D228) ----
    print("computing the best-of-27 shuffle null ...", flush=True)
    best = np.empty(N_SIMS)
    cache = {}
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel_all, cleaned_all) if st == "ALL"
                 else R.subset(raw_panel, raw_cleaned, R.STRATA[st]))
        cache[st] = (build_scores(p, cl), forward(p, first, start), len(p.symbols))
    for s in range(N_SIMS):
        perm_seed = int(rng.integers(0, 2 ** 31 - 1))
        vals = []
        for st, (sc, fwd, nsym) in cache.items():
            r2 = np.random.default_rng(perm_seed)     # SHARED across scores
            perm = [r2.permutation(sc[SCORES[0]].shape[1] - start) for _ in range(nsym)]
            for name in SCORES:
                sh = sc[name].copy()
                for i in range(nsym):
                    sh[i, start - 1:-1] = sh[i, start - 1:-1][perm[i]]
                qs = quintile_means(sh, fwd, start)
                if any(q.size == 0 for q in qs):
                    continue
                m = np.array([q.mean() for q in qs]) * 1e4
                vals.append(abs(float(m[-1] - m[0])))
        best[s] = max(vals) if vals else 0.0
        if (s + 1) % 100 == 0:
            print(f"  {s + 1}/{N_SIMS}", flush=True)
    floor = float(np.percentile(best, 95))
    print(f"\nBEST-OF-27 FLOOR (p95 of the max |spread| under a shared shuffle): "
          f"{floor:.2f} bp\n")

    print(f"  {'cell':22s} {'spread':>8s} {'M1':>4s} {'M2':>4s} {'M3':>4s} {'ALL THREE':>10s}")
    survivors = []
    for k, c in cells.items():
        m3 = abs(c["spread_bp"]) > floor
        c["M3_beats_floor"] = m3
        allthree = c["M1_monotone"] and c["M2_clears_bar"] and m3
        c["clears_all"] = allthree
        if allthree:
            survivors.append(k)
        print(f"  {k:22s} {c['spread_bp']:7.2f}b "
              f"{'YES' if c['M1_monotone'] else 'no':>4s} "
              f"{'YES' if c['M2_clears_bar'] else 'no':>4s} "
              f"{'YES' if m3 else 'no':>4s} {'** YES **' if allthree else 'no':>10s}")

    print(f"\nSURVIVORS: {survivors or 'NONE'}")
    payload = {"preregistration": "docs/decisions/D267-the-magnitude-calibration-screen.md",
               "commit": "e35486f", "horizon_bars": H, "n_sims": N_SIMS, "seed": SEED,
               "best_of_27_floor_bp": floor, "cells": cells, "survivors": survivors}
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
