"""The skip-a-bar test across ALL 51 candidates.

    uv run python scripts/d290_skip_all.py [--workers 6]

WHY IT IS WORTH RUNNING ON EVERYTHING. The five-candidate probe found that
`close_in_range` kept 2% of its k=1 edge after waiting one bar, `lower_wick` kept
NOTHING at any horizon, and `body_frac` kept 79% at k=20. Those three sat 1st,
2nd and 4th on D290's headline. The ranking inverted once the bounce came out, so
the test has to be applied to the whole list rather than to the three that looked
suspicious.

AND IT EXPOSES A LIMIT OF THE RANKING STATISTIC. Name-split CV -- D290's "honest"
column -- CANNOT SEE MICROSTRUCTURE. Bid-ask bounce generalises across names
perfectly well, which is how `lower_wick` posted CV +6.19 on an effect that is
entirely artifact. CV answers "does this hold on names I have not seen". The skip
test answers "is any of this real", and they are different questions.

THE OPTIMISATION, and it is the only kind CLAUDE.md permits -- HOISTING, not
reordering any float. The probe called `rank_columns` inside the per-(N, k) loop:
5 N x 12 horizons x 4 skips = 240 column sorts per candidate, when the ranking
depends only on the score and the skip. Hoisted, it is 4. `legs_from_order`
depends on N but not the horizon, so it moves out of the horizon loop too. The
arithmetic is identical; it just stops being recomputed.

    per candidate   before: 240 sorts + 240 leg builds
                     after:   4 sorts +  20 leg builds

Threads rather than processes: `argsort` and `bincount` release the GIL, and 6
threads share one 2.69 GB cache where 6 processes would need six copies.

REGRESSION-CHECKED against the committed five-candidate result. If the hoist
changed any number the run stops.
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


M = _load("run_mine_neutral", "run_mine_neutral.py")
BC = _load("d290_build_cache", "d290_build_cache.py")
B, C, FN = M.B, M.C, M.FN

OUT = REPO / "data" / "d290_skip_all.json"
PRIOR = REPO / "data" / "d290_skip_bar.json"
D290 = json.loads((REPO / "data" / "d290_stage1.json").read_text())
SKIPS = (0, 1, 2, 3)
# D290's OWN N SWEEP, not run_mine_neutral's. The first run used M.N_LEVELS =
# (10, 25, 50) and 20 of 51 candidates came back "no peak" -- every one whose
# D290 peak sat at N=3 or N=5 was silently unevaluated at its own best cell.
NS = tuple(D290["n_levels"])
KS = tuple(D290["horizons"])
MIN_RETAIN = 0.50           # "survives": half the effect left after one skip
MAX_BOUNCE = 0.25           # "bounce": a quarter or less


def skipped(score, n):
    for _ in range(n):
        score = C.lag1(score)
    return score


def full_grid(score, base, fwd, T):
    """{skip: {(N, k): (spread_bp, t)}} -- one sort per skip, one leg build per N."""
    out = {}
    for s in SKIPS:
        order, cnt = M.rank_columns(skipped(score, s), base)   # HOISTED
        g = {}
        for N in NS:
            ev_lo, ev_hi, _ = M.legs_from_order(order, cnt, N, base.shape)
            lr, lc = np.nonzero(ev_lo)
            hr, hc = np.nonzero(ev_hi)
            for k in KS:
                f = fwd[k]
                slo, clo = M.bar_sums(f, lr, lc, T)
                shi, chi = M.bar_sums(f, hr, hc, T)
                m = (clo > 0) & (chi > 0)
                if int(m.sum()) < M.MIN_BARS:
                    continue
                d = slo[m] / clo[m] - shi[m] / chi[m]
                sd = d.std(ddof=1)
                g[(N, k)] = (float(d.mean() * 1e4),
                             float(d.mean() / (sd / np.sqrt(d.size)))
                             if sd > 0 else 0.0)
        out[s] = g
    return out


def summarise(c, g):
    peak = D290["results"][c]["observed"]["spread"]
    cell = (peak[0], peak[1])
    a0 = g[0].get(cell)
    a1 = g[1].get(cell)
    ret = (a1[0] / a0[0]) if (a0 and a1 and a0[0] != 0) else None
    # where does it still work AFTER a skip? best cell by skip-1 t.
    best = max((v[1], k) for k, v in g[1].items()) if g[1] else None
    verdict = ("no peak" if ret is None else
               "BOUNCE" if ret <= MAX_BOUNCE else
               "survives" if ret >= MIN_RETAIN else "partial")
    return dict(c=c, ax=D290["axes"][c], N=cell[0], k=cell[1],
                s0=a0[0] if a0 else None, t0=a0[1] if a0 else None,
                s1=a1[0] if a1 else None, t1=a1[1] if a1 else None,
                ret=ret, verdict=verdict,
                best_t=best[0] if best else None,
                best_cell=list(best[1]) if best else None,
                best_bp=g[1][best[1]][0] if best else None,
                s2=(g[2].get(cell) or [None])[0],
                s3=(g[3].get(cell) or [None])[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()

    t0 = time.time()
    z = np.load(BC.CACHE, allow_pickle=False)
    assert str(z["key"]) == BC.cache_key(B.FIXTURE), "CACHE IS STALE -- rebuild"
    panel, _ = M.RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    base = z["warm"] & live
    T = live.shape[1]
    fwd = M.forward_returns(panel, live)
    cands = list(BC.CANDIDATES)
    print(f"loaded in {time.time() - t0:.0f}s | {len(cands)} candidates x "
          f"{len(SKIPS)} skips x {len(NS)} N x {len(KS)} k | {a.workers} threads",
          flush=True)

    grids = FN.parallel_map(lambda c, s: full_grid(s, base, fwd, T),
                            [(c, z[c]) for c in cands],
                            workers=a.workers, progress=True)

    # REGRESSION CHECK. The hoist must not have moved a number.
    if PRIOR.exists():
        prior = json.loads(PRIOR.read_text())["results"]
        checked = 0
        for c, byN in prior.items():
            if c not in grids:
                continue
            for N, byK in byN.items():
                for k, bySkip in byK.items():
                    for s, v in bySkip.items():
                        if v is None or int(s) not in grids[c]:
                            continue
                        got = grids[c][int(s)].get((int(N), int(k)))
                        if got is None:
                            continue
                        assert abs(got[0] - v[0]) < 1e-9, (
                            f"HOIST CHANGED A NUMBER: {c} N={N} k={k} skip={s} "
                            f"{v[0]:.6f} -> {got[0]:.6f}")
                        checked += 1
        print(f"  regression: {checked:,} cells match the 5-candidate probe "
              f"exactly", flush=True)

    rows = [summarise(c, grids[c]) for c in cands]
    rows.sort(key=lambda r: -(r["t1"] if r["t1"] is not None else -9e9))

    print(f"\n{'=' * 104}")
    print("  ALL 51 AT THEIR OWN D290 SPREAD PEAK -- what survives one skipped bar")
    print(f"{'=' * 104}")
    print(f"  {'ax':2s} {'candidate':16s} {'N':>3s} {'k':>3s} | "
          f"{'skip0':>8s} {'t':>6s} | {'skip1':>8s} {'t':>6s} | "
          f"{'skip2':>8s} {'skip3':>8s} | {'kept':>6s}  verdict")
    for r in rows:
        if r["s0"] is None:
            continue
        print(f"  {r['ax']:2s} {r['c']:16s} {r['N']:3d} {r['k']:3d} | "
              f"{r['s0']:+8.1f} {r['t0']:+6.2f} | "
              f"{r['s1']:+8.1f} {r['t1']:+6.2f} | "
              f"{(r['s2'] if r['s2'] is not None else float('nan')):+8.1f} "
              f"{(r['s3'] if r['s3'] is not None else float('nan')):+8.1f} | "
              f"{r['ret']:+6.0%}  {r['verdict']}")

    tally = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print(f"\n  {tally}")

    surv = [r for r in rows if r["verdict"] == "survives" and r["t1"] and r["t1"] > 2]
    print(f"\n  SURVIVES ONE SKIP WITH t > 2 AT ITS OWN PEAK: {len(surv)}")
    for r in surv:
        print(f"    {r['ax']} {r['c']:16s} N={r['N']:2d} k={r['k']:2d}  "
              f"{r['s1']:+7.1f} bp  t {r['t1']:+.2f}  kept {r['ret']:.0%}")

    print(f"\n  BEST SURVIVING CELL PER CANDIDATE (top 12 by skip-1 t)")
    for r in rows[:12]:
        if r["best_cell"] is None:
            continue
        print(f"    {r['ax']} {r['c']:16s} best after skip: N={r['best_cell'][0]:2d} "
              f"k={r['best_cell'][1]:2d}  {r['best_bp']:+7.1f} bp  t {r['best_t']:+.2f}")

    OUT.write_text(json.dumps(
        {"purpose": "skip-a-bar test on all 51. Separates bid-ask bounce from a "
                    "real effect. Name-split CV cannot do this -- bounce "
                    "generalises across names.",
         "skips": list(SKIPS), "min_retain": MIN_RETAIN, "max_bounce": MAX_BOUNCE,
         "rows": rows, "elapsed_s": round(time.time() - t0, 1)}, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
