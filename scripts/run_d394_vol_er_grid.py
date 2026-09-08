"""D394 -- the volatility x path-efficiency taxonomy, at three windows, with its own noise floor.

    uv run python scripts/run_d394_vol_er_grid.py

DESCRIPTIVE AND EXPLORATORY. No null, no hurdle, nothing selected, fitted or admitted (R15).
**This is hypothesis GENERATION on the training ledger.** Anything interesting found here would be
a new construction needing its own pre-registration and its own nulls (D289's fourth amendment)
before it could be believed, and would change the sample -- re-opening all four of D393's nulls.

THE TAXONOMY, from the principal, corrected on one axis. ER is scale-free -- it measures the SHAPE
of a path, not its size -- and volatility measures the size. So the four corners are:

                    low ER (wanders)          high ER (direct)
    low vol         DEAD -- small, nowhere    GRIND -- small, one way
    high vol        CHOP -- big, nowhere      TREND -- big, one way

(The principal's note had low-vol/high-ER as "flat" and low-vol/low-ER as "slow trending"; it is
the other way round. Flat is low-vol/LOW-ER; a slow trend is low-vol/HIGH-ER.)

THE PRIOR, declared before the numbers, because a 27-cell search with no prior is a fishing trip.
This is a REVERSAL book -- it buys names whose up-run has collapsed. So:

    CHOP  should revert hardest  -- thrashing is noise, and noise is what mean-reverts
    DEAD  should do least        -- nothing has moved, so nothing has to come back
    TREND should do worst        -- a big efficient move is repricing, and repricing continues

**If the ordering comes out CHOP > DEAD > TREND the taxonomy has content. Any other ordering, and a
"best cell" is a number from a 27-cell search.**

THE WINDOW QUESTION IS THE POINT, not a nuisance. ER over 5, 21 and 63 bars measures different
objects, and the hold here is 5 bars. Both are run. **ER_5/ER_63 is also crossed with volatility**
-- a name efficient over a week but inefficient over a quarter is making a FRESH directional move
inside a range, which no single window can express.

THE NOISE FLOOR IS COMPUTED BEFORE THE CELLS ARE READ. With ~2,750 trades a cell and a per-trade
std near 498 bp, a cell mean carries an SE near 9.5 bp -- so cells scatter tens of bp on noise
alone, against a bar of 61.48. The expected MAXIMUM of 9 independent cell means under a
no-difference null is reported beside the observed maximum. **A best cell that does not clear its
own noise floor is not a finding.**
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


OUT = REPO / "data" / "d394_vol_er_grid.json"
CAPS = (5, 20)
SHAPE = "E1"
CANDIDATE = "up_run_21"
ER_WINDOWS = (5, 21, 63)
CORNER = {(0, 0): "DEAD", (0, 2): "GRIND", (2, 0): "CHOP", (2, 2): "TREND"}
NOISE_DRAWS = 2000


def terciles(v, ok):
    a, b = np.percentile(v[ok], [33.333, 66.667])
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
    mask = V50.shape_masks(V47.percentile_grid(col), elig)[SHAPE][0]
    sc = np.where(np.isfinite(col), col, 50.0)

    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    g = M.P1.build_grids(panel, cleaned)
    closes = np.asarray(g["close"], float)
    print(f"  build {time.time() - t0:.0f}s, RSS {_rss():.2f} GB", flush=True)

    def lag_nT(a):
        s_ = np.where(P["excl"], np.nan, a)
        s_ = PREP.UF.apply_floor_replace(s_, P["keep"])
        s_ = np.where(P["base"], s_, np.nan)
        o = np.full((T, n), np.nan)
        o[1:] = s_[:, :-1].T
        return o

    er = {}
    for w in ER_WINDOWS:
        t1 = time.time()
        er[w] = lag_nT(A1.er_grid(closes, live, w))
        print(f"    ER_{w} built ({time.time() - t1:.0f}s)", flush=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        er["5/63"] = np.where(np.isfinite(er[5]) & np.isfinite(er[63]) & (er[63] > 0),
                              er[5] / er[63], np.nan)
    vol = V47.percentile_grid(lag_nT(np.asarray(P["score"]("rvol21"))))

    del cols, masks, dec, bucket, elig_b, g, panel, cleaned, closes
    gc.collect()
    print(f"    grids ready, RSS {_rss():.2f} GB ({time.time() - t0:.0f}s)", flush=True)

    rng = np.random.default_rng(394)
    out = {}
    for cap in CAPS:
        res = V59.run_mirror(P, mask, sc, "cap", cap)
        p = np.asarray(V47.pnl_bp(res), float)
        tr = res["trades"]
        rt = V59.trade_block(P, res, elig, 0, False)["two_c"]["PUB"]
        rows_i = np.array([t_[0] for t_ in tr])
        bars_i = np.array([t_[1] for t_ in tr])
        lo_c, hi_c = np.percentile(p, 10), np.percentile(p, 90)
        is_lo, is_hi = p <= lo_c, p >= hi_c
        vv = vol[bars_i, rows_i]

        # ---- the noise floor, computed BEFORE the cells are read ----------
        N = p.size
        per_cell = N // 9
        se_cell = float(p.std(ddof=1) / np.sqrt(per_cell))
        maxes = np.array([np.max([p[rng.choice(N, per_cell, replace=False)].mean()
                                  for _ in range(9)]) for _ in range(NOISE_DRAWS // 100)])
        noise = dict(per_cell_n=int(per_cell), se_cell=se_cell,
                     expected_max_of_9=float(maxes.mean()),
                     p95_max_of_9=float(np.percentile(maxes, 95)))

        grids = {}
        for key in list(ER_WINDOWS) + ["5/63"]:
            ee = er[key][bars_i, rows_i]
            ok = np.isfinite(ee) & np.isfinite(vv)
            if ok.sum() < 900:
                continue
            eb, vb = terciles(ee, ok), terciles(vv, ok)
            cells = []
            for iv, vl in enumerate(("lovol", "midvol", "hivol")):
                for ie, el in enumerate(("loER", "midER", "hiER")):
                    sel = ok & (vb == iv) & (eb == ie)
                    if sel.sum() < 50:
                        continue
                    m = float(p[sel].mean())
                    cells.append(dict(vol=vl, er=el, corner=CORNER.get((iv, ie), ""),
                                      n=int(sel.sum()), mean_bp=m,
                                      se=float(p[sel].std(ddof=1) / np.sqrt(sel.sum())),
                                      z_vs_book=float((m - p.mean()) /
                                                      (p[sel].std(ddof=1) / np.sqrt(sel.sum()))),
                                      p_left=float(is_lo[sel].mean()),
                                      p_right=float(is_hi[sel].mean()),
                                      covers=bool(m >= rt)))
            best = max(cells, key=lambda c: c["mean_bp"])
            corners = {c["corner"]: c["mean_bp"] for c in cells if c["corner"]}
            ordered = (corners.get("CHOP", -1e9) > corners.get("DEAD", -1e9) >
                       corners.get("TREND", -1e9))
            grids[str(key)] = dict(cells=cells, best=best,
                                   corners=corners, prior_ordering_holds=bool(ordered),
                                   best_beats_noise=bool(best["mean_bp"] > noise["p95_max_of_9"]))
        out[cap] = dict(trades=N, mean_bp=float(p.mean()), round_trip=float(rt),
                        noise=noise, grids=grids)
        print(f"    cap {cap}: {N:,} trades, noise p95 max-of-9 "
              f"{noise['p95_max_of_9']:+.2f} ({time.time() - t0:.0f}s)", flush=True)

    payload = dict(study=394, stage="vol_er_grid", score=CANDIDATE, shape=SHAPE,
                   purpose="Volatility x path-efficiency taxonomy at three windows plus the "
                           "short/long ratio, against a pre-computed noise floor. EXPLORATORY; "
                           "nothing selected, fitted or admitted (R15).",
                   prior="CHOP > DEAD > TREND, declared before the numbers",
                   er_windows=list(ER_WINDOWS), results=out)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    for cap, d in out.items():
        nz = d["noise"]
        print(f"\n{'=' * 80}\nCAP {cap} -- {d['trades']:,} trades, book mean {d['mean_bp']:+.2f}, "
              f"round trip {d['round_trip']:.2f}")
        print(f"  NOISE FLOOR: {nz['per_cell_n']:,} trades/cell, SE {nz['se_cell']:.2f} bp. "
              f"A random 9-cell split has max {nz['expected_max_of_9']:+.2f} on average, "
              f"p95 {nz['p95_max_of_9']:+.2f}.")
        for key, gr in d["grids"].items():
            print(f"\n  ER window {key}\n")
            print(f"    {'vol':<7s} {'ER':<7s} {'corner':<6s} {'n':>6s} {'mean':>9s} {'SE':>6s} "
                  f"{'z':>6s} {'P(left)':>8s} {'P(right)':>9s}")
            for c in gr["cells"]:
                print(f"    {c['vol']:<7s} {c['er']:<7s} {c['corner']:<6s} {c['n']:>6,} "
                      f"{c['mean_bp']:+9.2f} {c['se']:6.2f} {c['z_vs_book']:+6.2f} "
                      f"{100 * c['p_left']:7.1f}% {100 * c['p_right']:8.1f}%")
            b = gr["best"]
            print(f"    -> best {b['vol']}/{b['er']} {b['mean_bp']:+.2f}  |  "
                  f"beats noise p95? {'YES' if gr['best_beats_noise'] else 'no'}  |  "
                  f"covers cost? {'YES' if b['covers'] else 'no'}")
            if gr["corners"]:
                cs = "  ".join(f"{k} {v:+.2f}" for k, v in gr["corners"].items())
                print(f"    -> corners: {cs}   prior CHOP>DEAD>TREND "
                      f"{'HOLDS' if gr['prior_ordering_holds'] else 'FAILS'}")

    print(f"\n  ({time.time() - t0:.0f}s)  Exploratory. Nothing selected, fitted or admitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
