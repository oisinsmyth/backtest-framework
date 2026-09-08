"""D394 -- do distress, one-sided events or PATH EFFICIENCY separate the left tail from the right?

    uv run python scripts/run_d394_asymmetry_candidates.py

DESCRIPTIVE. No null, no hurdle, nothing selected, fitted or admitted (R15).

THE CRITERION, set by Addendum 2 before these candidates were chosen: a filter must be scored on
**ASYMMETRY** -- `spread_left - spread_right` -- not on how well it predicts losses. Predicting
losses is easy: `rvol21` does it at 10.6 pp and is useless, because it predicts gains at 10.1 pp.
Five observables failed that test (the score, `rsi`, `rev_21`, `rvol21`, price).

THE CANDIDATES, and why each could plausibly be one-sided:

  ER_SIGNED_21   PATH EFFICIENCY WITH A SIGN -- net move / total travel over 21 of the name's own
                 bars. The mechanism: a name falling in a STRAIGHT LINE is being sold with
                 conviction and may keep falling; a name falling CHOPPILY is noise and reverts.
                 Unsigned ER cannot express that -- it scores a straight-line riser and a
                 straight-line faller identically -- which is why A1's version is not the one
                 tested here. **This is the strongest a-priori candidate.**

  ER_21          A1's UNSIGNED efficiency ratio, carried as the contrast. If signed ER shows
                 asymmetry and unsigned does not, the sign is doing the work rather than the
                 efficiency.

  DD_252         DRAWDOWN from the trailing 252-bar max. The distress proxy: a name 80% off its
                 own high is a different object from one 5% off, and distress is genuinely
                 one-sided -- a bankruptcy has no mirror.

  DV_SPIKE       DOLLAR VOLUME at t-1 over its own trailing mean. The event proxy: capitulation
                 and forced selling arrive on volume, and a volume spike marks an event the tape
                 has already priced.

  BARS_TO_DELIST **A LOOK-AHEAD DIAGNOSTIC, NOT A FILTER, AND IT MUST NEVER BE USED AS ONE.**
                 Bars from entry to the name's last live bar. Nobody knows this at entry. It is
                 computed ONLY to answer whether the left tail is delisting-driven, because that
                 would say what a legitimate proxy should be hunting. It is reported in its own
                 section, labelled, and excluded from every filter comparison.

WHAT IS ACTUALLY DECISION-RELEVANT is not the asymmetry alone but what dropping a band does to the
MEAN, against the measured round trip. Both are reported: a band can have a low P(left) and a low
mean, and dropping it would then cost more than it saves -- which is exactly what `rvol21` did.

EXACTNESS. `signed_er_grid` follows A1's structure including the DIRECT denominator sum; A1's
docstring records that a cumulative-sum difference is a reordered float sum and broke the triangle
inequality on 329 of 11.86M cells. [ER] asserts `|signed| == a1_er_stage0.er_grid` exactly.
"""

from __future__ import annotations

import gc
import importlib.util
import json
import os
import sys
import time
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


def _rss():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1e9
    except Exception:
        return float("nan")


OUT = REPO / "data" / "d394_asymmetry_candidates.json"
CAPS = (5, 20)
SHAPE = "E1"
CANDIDATE = "up_run_21"
W = 21
DD_W = 252
DV_W = 63


def signed_er_grid(closes_nT, live_nT, w, MIN_TRAVEL):
    """SIGNED path efficiency: (c[t] - c[t-w]) / sum|dc| over the name's OWN bars, in [-1, +1].

    A1's `er_grid` with the numerator's absolute value removed, and its denominator convention kept
    EXACTLY -- summed directly, never as a difference of cumulative sums, which A1 records as a
    reordered float sum that broke the triangle inequality on 329 cells."""
    n, T = closes_nT.shape
    out = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live_nT[i])
        if at.size <= w:
            continue
        c = closes_nT[i, at]
        d = np.abs(np.diff(c))
        den = np.lib.stride_tricks.sliding_window_view(d, w).sum(axis=-1)
        num = c[w:] - c[:-w]                                  # SIGNED
        with np.errstate(invalid="ignore", divide="ignore"):
            out[i, at[w:]] = np.where(den > np.maximum(MIN_TRAVEL * np.abs(c[w:]), 0.0),
                                      num / den, np.nan)
    return out


def trailing_drawdown(closes_nT, live_nT, w):
    """close / trailing max(close, w) - 1, on the name's own bars. 0 at a high, negative below."""
    n, T = closes_nT.shape
    out = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live_nT[i])
        if at.size < 2:
            continue
        c = closes_nT[i, at]
        k = min(w, c.size)
        pad = np.concatenate([np.full(k - 1, c[0]), c])
        mx = np.lib.stride_tricks.sliding_window_view(pad, k).max(axis=-1)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[i, at] = np.where(mx > 0, c / mx - 1.0, np.nan)
    return out


def dv_spike(dv_Tn, w):
    """DV over its own trailing mean, per name, on the (T, n) grid prep already provides."""
    x = np.asarray(dv_Tn, float)
    T = x.shape[0]
    out = np.full_like(x, np.nan)
    csum = np.nancumsum(np.nan_to_num(x), axis=0)
    cnt = np.cumsum(np.isfinite(x), axis=0)
    for t in range(w, T):
        s = csum[t - 1] - csum[t - w - 1] if t - w - 1 >= 0 else csum[t - 1]
        k = cnt[t - 1] - (cnt[t - w - 1] if t - w - 1 >= 0 else 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            m = np.where(k > 0, s / np.maximum(k, 1), np.nan)
            out[t] = np.where((m > 0) & np.isfinite(x[t]), x[t] / m, np.nan)
    return out


def bands_of(v, ok, q=(33.333, 66.667)):
    a, b = np.percentile(v[ok], q)
    return np.where(v <= a, 0, np.where(v >= b, 2, 1))


def main() -> int:
    t0 = time.time()
    R = _load("d393b", "run_d393_bs_null.py")
    A1 = _load("a1er", "a1_er_stage0.py")
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    V47 = PREP.V47

    P, elig, cols, masks, dec, T, n, bucket, elig_b = R.build(PREP, V50, SG)
    col = cols[CANDIDATE]
    pctg = V47.percentile_grid(col)
    mask = V50.shape_masks(pctg, elig)[SHAPE][0]
    sc = np.where(np.isfinite(col), col, 50.0)

    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    g = M.P1.build_grids(panel, cleaned)
    closes = np.asarray(g["close"], float)
    print(f"  build {time.time() - t0:.0f}s, RSS {_rss():.2f} GB", flush=True)

    t1 = time.time()
    er_s = signed_er_grid(closes, live, W, A1.MIN_TRAVEL)
    er_u = A1.er_grid(closes, live, W)
    fin = np.isfinite(er_s) & np.isfinite(er_u)
    bad = int((np.abs(er_s[fin]) != er_u[fin]).sum())
    assert bad == 0, f"[ER] signed and unsigned disagree on {bad} cells"
    assert np.nanmax(np.abs(er_s)) <= 1.0 + 1e-12, "[ER] signed efficiency outside [-1, 1]"
    print(f"    [ER] |signed| == A1's unsigned on {int(fin.sum()):,} cells, exactly; "
          f"range [{np.nanmin(er_s):.3f}, {np.nanmax(er_s):.3f}]  ({time.time() - t1:.0f}s)",
          flush=True)

    dd = trailing_drawdown(closes, live, DD_W)
    dvs = dv_spike(np.asarray(P["DV"], float), DV_W)

    def lag_nT(a_nT):
        """(n, T) built on own bars -> (T, n) shifted one bar, the book's own convention."""
        s_ = np.where(P["excl"], np.nan, a_nT)
        s_ = PREP.UF.apply_floor_replace(s_, P["keep"])
        s_ = np.where(P["base"], s_, np.nan)
        o = np.full((T, n), np.nan)
        o[1:] = s_[:, :-1].T
        return o

    def lag_Tn(a_Tn):
        o = np.full((T, n), np.nan)
        o[1:] = a_Tn[:-1]
        return o

    obs = {"ER_signed_21": lag_nT(er_s), "ER_21": lag_nT(er_u),
           "DD_252": lag_nT(dd), "DV_spike": lag_Tn(dvs)}
    last_live = np.asarray(P["last_live"])          # LOOK-AHEAD -- diagnostic only

    del cols, masks, dec, bucket, elig_b, g, panel, cleaned, closes, er_s, er_u, dd, dvs
    gc.collect()
    print(f"    candidates built, RSS {_rss():.2f} GB ({time.time() - t0:.0f}s)", flush=True)

    out = {}
    for cap in CAPS:
        res = V59.run_mirror(P, mask, sc, "cap", cap)
        p = np.asarray(V47.pnl_bp(res), float)
        tr = res["trades"]
        rt = V59.trade_block(P, res, elig, 0, False)["two_c"]["PUB"]
        lo_cut, hi_cut = np.percentile(p, 10), np.percentile(p, 90)
        is_lo, is_hi = p <= lo_cut, p >= hi_cut
        rows_i = np.array([t_[0] for t_ in tr])
        bars_i = np.array([t_[1] for t_ in tr])

        cand = {}
        for nm, gr in obs.items():
            v = gr[bars_i, rows_i]
            ok = np.isfinite(v)
            if ok.sum() < 500:
                continue
            band = bands_of(v, ok)
            rows = []
            for j, lab in enumerate(("lo", "mid", "hi")):
                sel = ok & (band == j)
                if not sel.any():
                    continue
                keep = ~sel                      # what the book becomes if this band is DROPPED
                rows.append(dict(band=lab, n=int(sel.sum()),
                                 p_left=float(is_lo[sel].mean()),
                                 p_right=float(is_hi[sel].mean()),
                                 mean_bp=float(p[sel].mean()),
                                 mean_if_dropped=float(p[keep].mean()),
                                 kept_if_dropped=int(keep.sum())))
            sl = max(r["p_left"] for r in rows) - min(r["p_left"] for r in rows)
            sr = max(r["p_right"] for r in rows) - min(r["p_right"] for r in rows)
            best_drop = max(rows, key=lambda r: r["mean_if_dropped"])
            cand[nm] = dict(bands=rows, spread_left=sl, spread_right=sr, asymmetry=sl - sr,
                            best_drop_band=best_drop["band"],
                            best_mean_if_dropped=best_drop["mean_if_dropped"],
                            covers_cost=bool(best_drop["mean_if_dropped"] >= rt))

        # ---- the LOOK-AHEAD diagnostic, quarantined -----------------------
        btl = last_live[rows_i] - bars_i
        okb = np.isfinite(btl.astype(float))
        bandb = bands_of(btl.astype(float), okb)
        dl = []
        for j, lab in enumerate(("soon", "mid", "far")):
            sel = okb & (bandb == j)
            if sel.any():
                dl.append(dict(band=lab, n=int(sel.sum()),
                               median_bars_to_delist=float(np.median(btl[sel])),
                               p_left=float(is_lo[sel].mean()), p_right=float(is_hi[sel].mean()),
                               mean_bp=float(p[sel].mean())))

        out[cap] = dict(trades=int(p.size), mean_bp=float(p.mean()), round_trip=float(rt),
                        candidates=cand, delisting_diagnostic=dl)
        print(f"    cap {cap}: {p.size:,} trades, mean {p.mean():+.2f}, "
              f"round trip {rt:.2f}  ({time.time() - t0:.0f}s)", flush=True)

    payload = dict(study=394, stage="asymmetry_candidates", score=CANDIDATE, shape=SHAPE,
                   window=W, purpose="Do distress, one-sided events or SIGNED path efficiency "
                                     "separate the left tail from the right? Descriptive; nothing "
                                     "selected, fitted or admitted (R15).",
                   criterion="asymmetry = spread_left - spread_right (Addendum 2)",
                   look_ahead_warning="delisting_diagnostic uses last_live and is NOT usable as a "
                                      "filter. Diagnostic only.",
                   results=out)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    for cap, d in out.items():
        print(f"\n{'=' * 78}\nCAP {cap} -- {d['trades']:,} trades, mean {d['mean_bp']:+.2f}, "
              f"round trip {d['round_trip']:.2f} bp\n")
        print(f"  {'candidate':<14s} {'band':<5s} {'n':>7s} {'P(left)':>8s} {'P(right)':>9s} "
              f"{'mean':>9s} {'mean if dropped':>16s}")
        for nm, c in d["candidates"].items():
            for r in c["bands"]:
                print(f"  {nm:<14s} {r['band']:<5s} {r['n']:>7,} {100 * r['p_left']:7.1f}% "
                      f"{100 * r['p_right']:8.1f}% {r['mean_bp']:+9.2f} "
                      f"{r['mean_if_dropped']:+16.2f}")
            print(f"  {'':14s} left {100 * c['spread_left']:5.1f} pp | right "
                  f"{100 * c['spread_right']:5.1f} pp | ASYMMETRY {100 * c['asymmetry']:+5.1f} pp"
                  f"   best: drop '{c['best_drop_band']}' -> {c['best_mean_if_dropped']:+.2f} "
                  f"({'COVERS COST' if c['covers_cost'] else 'below cost'})\n")

        print(f"  LOOK-AHEAD DIAGNOSTIC -- bars from entry to the name's LAST LIVE BAR.")
        print(f"  NOT A FILTER: nobody knows this at entry. It only asks whether the left tail is "
              f"delisting-driven.\n")
        print(f"  {'band':<6s} {'n':>7s} {'median bars':>12s} {'P(left)':>8s} {'P(right)':>9s} "
              f"{'mean':>9s}")
        for r in d["delisting_diagnostic"]:
            print(f"  {r['band']:<6s} {r['n']:>7,} {r['median_bars_to_delist']:>12,.0f} "
                  f"{100 * r['p_left']:7.1f}% {100 * r['p_right']:8.1f}% {r['mean_bp']:+9.2f}")

    print(f"\n  ({time.time() - t0:.0f}s)  Descriptive. Nothing selected, fitted or admitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
