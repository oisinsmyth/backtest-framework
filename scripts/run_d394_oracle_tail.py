"""D394 -- the CLAIRVOYANT bound on chopping the left tail, and whether the tail is predictable.

    uv run python scripts/run_d394_oracle_tail.py

DESCRIPTIVE. No null, no hurdle, nothing admitted (R15).

THE QUESTION. D394 showed no stop, target or trail closes the gap. The follow-up is whether an
ENTRY FILTER could -- not cutting a trade after it goes wrong, but never taking the trades that
become the left tail. Before hunting for such a filter, this measures the bound no filter can beat.

(1) THE ORACLE CURVE. Remove the worst k% of trades WITH PERFECT FORESIGHT and report the mean of
    what remains. **No real filter can beat this**, because a real one must decide at entry with a
    fraction of the information. If the oracle does not reach the round trip at a plausible k, the
    entire left-tail direction is closed by ARITHMETIC rather than by search.

    The bar is the measured round trip: cost per trade does not change when trades are removed --
    each surviving trade still pays one round trip -- so the target is a MEAN of ~61 bp.

(2) IS THE LEFT TAIL EVEN PREDICTABLE, and asymmetrically? A filter is only useful if it separates
    the left tail from the right one. Filtering out "fat-tailed names" removes BOTH tails, and at a
    payoff of 1.024 that removes roughly equal amounts and moves the mean very little.

    So for each entry-time observable this reports P(left tail) and P(right tail) by tercile, and
    the ASYMMETRY between them. A tercile that is 2x as likely to produce a bottom-decile trade AND
    2x as likely to produce a top-decile trade is useless, however striking the first number looks.

    Observables are all known at t-1 -- the score itself, the rsi percentile, the trailing return,
    realised vol, and price -- and are read from the SAME lagged grids the book was built on.

WHY THIS IS NOT A SEARCH. Nothing here is selected, fitted or proposed as a construction. It is a
bound and a diagnostic on an existing ledger. If (2) finds an asymmetric observable, THAT would
need its own pre-registration before anything is built on it (D289's fourth amendment).
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


OUT = REPO / "data" / "d394_oracle_tail.json"
CAPS = (5, 20)
SHAPE = "E1"
CANDIDATE = "up_run_21"
KS = (1, 2, 5, 10, 15, 20, 25, 33, 50)
OBS = ("up_run_21", "rsi", "rev_21", "rvol21", "price")


def main() -> int:
    t0 = time.time()
    R = _load("d393b", "run_d393_bs_null.py")
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

    # entry-time observables, all LAGGED exactly as the book's own score is
    def lagged_from(arr):
        s_ = np.where(P["excl"], np.nan, arr)
        s_ = PREP.UF.apply_floor_replace(s_, P["keep"])
        s_ = np.where(P["base"], s_, np.nan)
        o = np.full((T, n), np.nan)
        o[1:] = s_[:, :-1].T
        return o

    obs = {"up_run_21": pctg,
           "rsi": np.asarray(P["PCT"]["rsi"]),
           "rev_21": V47.percentile_grid(lagged_from(np.asarray(P["score"]("rev_21")))),
           "rvol21": V47.percentile_grid(lagged_from(np.asarray(P["score"]("rvol21")))),
           "price": np.asarray(P["CLOSE"])}
    del cols, masks, dec, bucket, elig_b
    gc.collect()
    print(f"  build {time.time() - t0:.0f}s, RSS {_rss():.2f} GB", flush=True)

    out = {}
    for cap in CAPS:
        res = V59.run_mirror(P, mask, sc, "cap", cap)
        p = np.asarray(V47.pnl_bp(res), float)
        tr = res["trades"]
        tb = V59.trade_block(P, res, elig, 0, False)
        rt = tb["two_c"]["PUB"]
        N = p.size
        srt = np.sort(p)

        # ---- (1) the oracle curve -------------------------------------
        curve = []
        for k in KS:
            m = int(round(N * k / 100.0))
            kept = srt[m:]
            curve.append(dict(drop_pct=k, dropped=m, kept=int(kept.size),
                              mean_bp=float(kept.mean()),
                              covers=bool(kept.mean() >= rt)))
        # and the symmetric version, for contrast
        sym = []
        for k in KS:
            m = int(round(N * k / 200.0))
            kept = srt[m:N - m] if m else srt
            sym.append(dict(drop_pct=k, mean_bp=float(kept.mean())))

        # ---- (2) is the tail predictable, and asymmetrically? ----------
        lo_cut, hi_cut = np.percentile(p, 10), np.percentile(p, 90)
        is_lo, is_hi = p <= lo_cut, p >= hi_cut
        pred = {}
        for nm in OBS:
            g = obs[nm]
            v = np.array([g[t_[1], t_[0]] for t_ in tr], float)
            ok = np.isfinite(v)
            if ok.sum() < 100:
                continue
            a, b = np.percentile(v[ok], [33.333, 66.667])
            band = np.where(v <= a, 0, np.where(v >= b, 2, 1))
            rows = []
            for j, lab in enumerate(("lo", "mid", "hi")):
                sel = ok & (band == j)
                if not sel.any():
                    continue
                rows.append(dict(band=lab, n=int(sel.sum()),
                                 p_left=float(is_lo[sel].mean()),
                                 p_right=float(is_hi[sel].mean()),
                                 mean_bp=float(p[sel].mean())))
            spread_l = max(r["p_left"] for r in rows) - min(r["p_left"] for r in rows)
            spread_r = max(r["p_right"] for r in rows) - min(r["p_right"] for r in rows)
            pred[nm] = dict(bands=rows, spread_left=spread_l, spread_right=spread_r,
                            asymmetry=spread_l - spread_r)

        out[cap] = dict(trades=N, mean_bp=float(p.mean()), round_trip=float(rt),
                        oracle=curve, symmetric=sym, predictability=pred)
        print(f"    cap {cap}: {N:,} trades, mean {p.mean():+.2f}, round trip {rt:.2f} "
              f"({time.time() - t0:.0f}s)", flush=True)

    payload = dict(study=394, stage="oracle_tail", score=CANDIDATE, shape=SHAPE,
                   purpose="A clairvoyant upper bound on removing the left tail, and whether that "
                           "tail is predictably separable from the right one. Descriptive; "
                           "nothing selected, fitted or admitted (R15).",
                   caps=list(CAPS), results=out)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    for cap, d in out.items():
        print(f"\n(1) ORACLE -- drop the worst k% of cap-{cap} trades WITH PERFECT FORESIGHT.")
        print(f"    Bar to cover cost: mean >= {d['round_trip']:.2f} bp   "
              f"(baseline mean {d['mean_bp']:+.2f} on {d['trades']:,} trades)\n")
        print(f"    {'drop':>5s} {'kept':>8s} {'ORACLE mean':>12s} {'covers cost?':>13s}   "
              f"{'symmetric trim':>15s}")
        for c, s in zip(d["oracle"], d["symmetric"]):
            print(f"    {c['drop_pct']:>4d}% {c['kept']:>8,} {c['mean_bp']:>+12.2f} "
                  f"{'YES' if c['covers'] else 'no':>13s}   {s['mean_bp']:>+15.2f}")

        print(f"\n(2) IS THE LEFT TAIL PREDICTABLE at entry, and ASYMMETRICALLY? (cap {cap})")
        print(f"    P(bottom decile) and P(top decile) by tercile of each entry-time observable.")
        print(f"    A useful filter needs a LEFT spread much larger than its RIGHT spread.\n")
        print(f"    {'observable':<12s} {'band':<5s} {'n':>7s} {'P(left)':>8s} {'P(right)':>9s} "
              f"{'mean':>8s}")
        for nm, pd_ in d["predictability"].items():
            for r in pd_["bands"]:
                print(f"    {nm:<12s} {r['band']:<5s} {r['n']:>7,} {100 * r['p_left']:7.1f}% "
                      f"{100 * r['p_right']:8.1f}% {r['mean_bp']:+8.2f}")
            print(f"    {'':12s} {'-> spread left':<22s} {100 * pd_['spread_left']:5.1f} pp   "
                  f"right {100 * pd_['spread_right']:5.1f} pp   "
                  f"ASYMMETRY {100 * pd_['asymmetry']:+5.1f} pp\n")

    print(f"  ({time.time() - t0:.0f}s)  Descriptive. Nothing selected, fitted or admitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
