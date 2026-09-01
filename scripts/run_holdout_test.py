"""D278 -- the instrument holdout. Pre-registered in
`docs/decisions/D278-the-instrument-holdout.md`, commit f8407c3, BEFORE the
holdout bars existed.

    uv run python scripts/run_holdout_test.py --validate   # in-sample, must reproduce D277
    uv run python scripts/run_holdout_test.py              # the holdout

THE VALIDATION GATE RUNS FIRST AND CAN VOID THE STUDY. `--validate` points this
runner at the IN-SAMPLE fixture and requires it to reproduce D277's twelve
corresponding cells to within 0.02 CAGR points. If it does not, the runner is not
the thing that produced the mine's numbers and no holdout reading means anything.
Same discipline as D265's Gate G, which caught nothing but could have.

THE CONSTRUCTION IS FROZEN AND NOTHING HERE MAY RETUNE IT: S2_short_intra, three
filter scores at their BOTTOM quintile plus the unfiltered base, three strata.
12 cells, judged against a best-of-12 floor and never individually.

H5 -- THE SIGN MUST AGREE WITH IN-SAMPLE -- is read from the committed mine
summary, not from anything computed here, so it cannot drift.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
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


Q = _load("d277", "d277_mine.py")
R, M, D, X, V, C, P, I = Q.R, Q.M, Q.D, Q.X, Q.V, Q.C, Q.P, Q.I

MINE = json.loads((REPO / "data" / "d277_mine_summary.json").read_text())["cells"]
OUT_HOLD = REPO / "data" / "d278_holdout_summary.json"
OUT_VAL = REPO / "data" / "d278_validation.json"

FIX = REPO / "data" / "fixtures"
HOLD_PANEL = FIX / "holdout_intraday_15m_panel.csv.gz"
HOLD_EVENTS = FIX / "holdout_intraday_15m_panel_events.json"

FILTERS = ("none", "impulse_hist", "macd_line", "mass_imbalance")
N_SIMS, SEED = 500, 0
VALIDATE_TOL = 0.0002        # 0.02 CAGR points


def strata_of(symbols, low, high):
    return {"ALL": tuple(symbols), "LOW": tuple(low), "HIGH": tuple(high)}


def trade_weighted_2c(panel, pos, start, sess_end):
    """`2c` weighted by each symbol's TRADE COUNT, not by symbol.

    Declared in D278's addendum BEFORE the holdout bars existed. The left-hand
    side of H1 -- mean move per TRADE -- is trade-weighted, so the right-hand
    side must be, or the comparison weights two things differently. It barely
    mattered in-sample, where four names' costs spanned 1.8x; on the holdout HIGH
    they span 2.9x (RIG 15.32 bp against TRGP 5.27), because commission is
    charged per SHARE and RIG trades at $4.62."""
    n_by_sym = []
    for i in range(pos.shape[0]):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        n = 0
        for tt in ent:
            close = int(sess_end[tt])
            z = np.flatnonzero(s[tt:close] == 0.0)
            if (tt + int(z[0]) if z.size else close) > tt:
                n += 1
        n_by_sym.append(n)
    w = np.asarray(n_by_sym, dtype=float)
    if w.sum() == 0:
        return 2.0 * float(np.mean(panel.cost_fraction) * 1e4)
    return 2.0 * float((w * panel.cost_fraction).sum() / w.sum() * 1e4)


def run(panel, cleaned, strata, first, gap, start, ppy, sess_end, vol, px, bod, label):
    scores = {**C.build_scores(panel, cleaned),
              **V.build_volume_scores(panel, vol, px, bod, panel.total_log_returns),
              **P.build_profile_scores(panel, cleaned, vol, start)}
    masks = {f: Q.quintile_mask(scores[f], start, "bot")
             for f in FILTERS if f != "none"}
    books_all = R.build_books(panel, cleaned, start, first)
    base_all = books_all["S2_short_intra"]

    cells, keep_of = {}, {}
    for st, syms in strata.items():
        p, _ = R.subset(panel, cleaned, syms) if st != "ALL" else (panel, cleaned)
        keep = [panel.symbols.index(s) for s in p.symbols]
        keep_of[st] = (p, keep, R.borrow_vector(p.symbols))
        for f in FILTERS:
            pos = base_all[keep] if f == "none" else base_all[keep] * masks[f][keep]
            if not (pos != 0).any():
                continue
            sc = R.score(p, pos, start, first, gap, ppy, R.borrow_vector(p.symbols))
            tr = Q.S.per_trade(pos, p.total_log_returns, start, sess_end)
            mv = float(tr.mean()) if tr.size else 0.0
            c2 = trade_weighted_2c(p, pos, start, sess_end)   # D278 addendum
            cells[f"{st}|{f}"] = {**sc, "cost_bp": c2, "n_trades": int(tr.size),
                                  "move_bp": mv, "move_vs_cost": mv / c2,
                                  "H1": bool(mv >= c2), "H2": bool(sc["cagr"] > 0)}
    return cells, keep_of, masks, base_all


def nulls(cells, keep_of, masks, base_all, panel, first, gap, start, ppy):
    rng = np.random.default_rng(SEED)
    T = panel.closes.shape[1]
    keys = list(cells)
    ps = {k: np.empty(N_SIMS) for k in keys}
    pm = {k: np.empty(N_SIMS) for k in keys}
    best = np.empty(N_SIMS)
    for s in range(N_SIMS):
        off = rng.integers(1, T - start, size=len(panel.symbols))
        vals = []
        for k in keys:
            st, f = k.split("|")
            p, keep, borrow = keep_of[st]
            pos = base_all[keep] if f == "none" else base_all[keep] * masks[f][keep]
            rot = np.zeros_like(pos)
            for i, j in enumerate(keep):
                rot[i, start:] = np.roll(pos[i, start:], int(off[j]))
            tot = X.signed_log_returns(p, rot, total_return=True)[start:]
            ex, _ = R.excess_vec(tot, rot, start, first, gap, ppy, borrow)
            ps[k][s] = R._sharpe(ex, ppy)
            pm[k][s] = float(np.sum(tot))
            vals.append(ps[k][s])
        best[s] = max(vals)
        if (s + 1) % 125 == 0:
            print(f"    {s + 1}/{N_SIMS}", flush=True)
    return ps, pm, float(np.percentile(best, 95))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true",
                    help="run on the IN-SAMPLE fixture; must reproduce D277")
    a = ap.parse_args()

    if a.validate:
        rp, rc = R.load_full()
        panel, cleaned = R.subset(rp, rc, R.STRATA["ALL"])
        strata = R.STRATA
        label = "IN-SAMPLE (validation)"
    else:
        if not HOLD_PANEL.exists():
            raise SystemExit(f"{HOLD_PANEL.name} not built yet — run\n"
                             "  fetch_single_name_intraday.py --holdout --build\n"
                             "  build_intraday_panel.py --holdout")
        saved = (R.L.FIXTURE, R.L.EVENTS)
        try:
            R.L.FIXTURE, R.L.EVENTS = HOLD_PANEL, HOLD_EVENTS
            panel, cleaned = R.L.load_panel()
        finally:
            R.L.FIXTURE, R.L.EVENTS = saved
        h = json.loads((REPO / "data" / "holdout_name_selection.json").read_text())
        low = [x["symbol"] for x in h["low"]]
        high = [x["symbol"] for x in h["high"]]
        strata = strata_of(panel.symbols, low, high)

        # THE STRATUM MAP AND THE COST VECTOR MUST BOTH BE REPOINTED, and missing
        # the second would have been silent. `load_panel` builds cost_fraction
        # from `L.per_side_bps`, which adds the ETF half-spread of 1.0 bp -- not
        # D264's 1.5 (low) / 4.5 (high). Left alone, the holdout would have been
        # costed 2.5x too cheaply on its high stratum and H1 would have been
        # trivially easier to clear. Caught by `borrow_vector` raising KeyError on
        # ANF, which is the loud failure D226's guards are written to produce.
        R.STRATUM = {**{s: "low" for s in low}, **{s: "high" for s in high}}
        panel = type(panel)(
            symbols=panel.symbols, closes=panel.closes,
            log_returns=panel.log_returns,
            cost_fraction=R.cost_vector(panel.symbols, panel.closes),
            dates=panel.dates, total_log_returns=panel.total_log_returns)
        print("cost per side, from the holdout panel's own median close:")
        for i, s in enumerate(panel.symbols):
            print(f"    {s:6s} {R.STRATUM[s]:5s} {panel.cost_fraction[i] * 1e4:5.2f} bp")
        label = "HOLDOUT"

    first, gap = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    T = panel.closes.shape[1]
    ppy = (T / int(first.sum())) * 252.0
    sess_end, _ = Q.A.session_maps(first, T)
    vol, px, stamps = V.load_volume(panel) if a.validate else _hold_volume(panel)
    bod = V.bar_of_day(stamps)

    print(f"{label}: {len(panel.symbols)} names x {T:,} bars, "
          f"{int(first.sum()):,} sessions\n", flush=True)
    cells, keep_of, masks, base_all = run(panel, cleaned, strata, first, gap, start,
                                          ppy, sess_end, vol, px, bod, label)

    if a.validate:
        print("VALIDATION GATE -- must reproduce D277's cells\n")
        print(f"  {'cell':28s} {'this run':>10s} {'D277':>10s} {'delta':>9s}  ok")
        worst, ok_all = 0.0, True
        for k, c in sorted(cells.items()):
            st, f = k.split("|")
            mk = f"{st}|S2_short_intra|{'none' if f == 'none' else f + '|bot'}"
            if mk not in MINE:
                continue
            d = c["cagr"] - MINE[mk]["cagr"]
            worst = max(worst, abs(d))
            ok = abs(d) <= VALIDATE_TOL
            ok_all &= ok
            print(f"  {k:28s} {c['cagr']:+9.4%} {MINE[mk]['cagr']:+9.4%} "
                  f"{d * 100:+8.4f}p  {'ok' if ok else 'MISMATCH'}")
        print(f"\n  worst delta {worst * 100:.4f} points, tolerance "
              f"{VALIDATE_TOL * 100:.2f}  ->  {'PASS' if ok_all else 'FAIL'}")
        json.dump({"pass": bool(ok_all), "worst_delta": worst,
                   "cells": {k: v["cagr"] for k, v in cells.items()}},
                  open(OUT_VAL, "w"), indent=1)
        if not ok_all:
            print("\n  GATE FAILED. The runner does not reproduce the mine; "
                  "no holdout reading may be taken.")
            return 1
        print("\n  Gate passed. The runner is faithful to D277 and may be pointed "
              "at the holdout.")
        return 0

    print("rotation nulls ...", flush=True)
    ps, pm, floor = nulls(cells, keep_of, masks, base_all, panel, first, gap, start, ppy)
    print(f"\nbest-of-{len(cells)} floor: {floor:+.3f}\n")
    print(f"  {'cell':18s} {'move':>8s} {'xcost':>6s} {'CAGR':>8s} {'SR':>7s} "
          f"{'H1':>3s} {'H2':>3s} {'H3':>3s} {'H4':>3s} {'H5':>3s}  ALL FIVE")
    surv = []
    for k, c in cells.items():
        st, f = k.split("|")
        mk = f"{st}|S2_short_intra|{'none' if f == 'none' else f + '|bot'}"
        in_sign = np.sign(MINE[mk]["cagr"]) if mk in MINE else 0.0
        a_s, a_m = c["excess_sharpe"], None
        p, keep, borrow = keep_of[st]
        pos = base_all[keep] if f == "none" else base_all[keep] * masks[f][keep]
        a_m = float(np.sum(X.signed_log_returns(p, pos, total_return=True)[start:]))
        c["H3"] = bool(a_s > np.percentile(ps[k], 95) and a_m > np.percentile(pm[k], 95))
        c["H4"] = bool(a_s > floor)
        c["H5"] = bool(np.sign(c["cagr"]) == in_sign and in_sign != 0)
        c["in_sample_cagr"] = MINE[mk]["cagr"] if mk in MINE else None
        c["clears_all"] = all(c[h] for h in ("H1", "H2", "H3", "H4", "H5"))
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:18s} {c['move_bp']:+7.2f}b {c['move_vs_cost']:5.2f}x "
              f"{c['cagr']:+7.2%} {a_s:+7.3f} {y(c['H1']):>3s} {y(c['H2']):>3s} "
              f"{y(c['H3']):>3s} {y(c['H4']):>3s} {y(c['H5']):>3s}  "
              f"{'** YES **' if c['clears_all'] else 'no'}")
    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    json.dump({"floor": floor, "cells": cells, "survivors": surv},
              open(OUT_HOLD, "w"), indent=1)
    print(f"\nwrote {OUT_HOLD.relative_to(REPO)}")
    return 0


def _hold_volume(panel):
    saved = V.FIXTURE
    try:
        V.FIXTURE = HOLD_PANEL
        return V.load_volume(panel)
    finally:
        V.FIXTURE = saved


if __name__ == "__main__":
    raise SystemExit(main())
