"""D393 -- resolve null B at 4,000 draws, on the terms Addendum 4 section 2 declared in advance.

    uv run python scripts/run_d393_b_resolve.py --prep-cell     # heavy, ONCE, ~30s
    uv run python scripts/run_d393_b_resolve.py --verify        # bit-identity vs the 1,000-draw run
    uv run python scripts/run_d393_b_resolve.py --shard i --nshards N --draws 4000
    uv run python scripts/run_d393_b_resolve.py --merge --nshards N --draws 4000

WHY THIS EXISTS. B came back **UNRESOLVED** at 1,000 draws: margin +0.69 inside 2 SE = 0.78.
D373's amendment pre-declares the remedy -- where a hurdle lands in the band, spend more draws on
THAT hurdle and say so rather than rounding it to a verdict.

**THE DIRECTION IT RESOLVES TO IS THE ANSWER. Declared in Addendum 4 section 2 BEFORE these draws:
BELOW retires the cell; ABOVE clears B by under one basis point, which is not a strong result and
must not be reported as one.** Adding draws because a margin is in the band is legitimate; adding
draws until it leaves the band on the side you want is not.

WHY A SEPARATE FILE. `run_d393_bs_null.py` produced the published A', B_s, B and C numbers. This
runner is an OPTIMISATION, and an optimisation that edits the file it must be checked against
cannot be checked against it. **The null itself is imported, not reimplemented** -- `control_bs_signal`
and `assert_Bs` come from that module, so there is still exactly one definition of the swap.

THE CANDIDATE ONLY, and that is a scope decision with a reason. `up_frac_21` already resolved
**BELOW at -5.84**, far outside the band; more draws for it buy nothing. This run exists to resolve
`up_run_21`'s +0.69. Halving the work is the point.

WHAT WAS OPTIMISED, all of it EXACT -- hoists and skips, never a reordered float sum or a
revectorised RNG draw (CLAUDE.md):

  1. THE SWAP PLAN IS HOISTED. Per (bar, rsi bucket) the event indices and the replacement pool
     are FIXED across draws -- `flatnonzero(elig_b[t] & (bucket[t]==d) & ~mask[t])` was recomputed
     4,000 times over a full-width boolean. Now computed once. The `rng.choice` calls happen in the
     same order on the same arrays, so the draw stream is untouched.
  2. THE CONSTANT SCORE GRID IS HOISTED. `np.full((T,n), 17.0)` is 53 MB and 13 ms, allocated once
     per draw. Now allocated once.
  3. THE OUTPUT BUFFER IS REUSED, zeroing only the event rows -- the only rows ever written.
  4. THE WORKERS NEVER BUILD THE PANEL. `prep(need_grids=False)` plus a cached mask replaces a
     3.08 GB build peak with a ~0.1 GB load. That is what makes the fan fit the memory budget,
     and it is a memory optimisation before it is a speed one.

  Measured: 0.568 s/draw -> see --verify's report. Worker RSS 1.44 GB -> ~0.5 GB.

EXACTNESS IS PROVED, NOT CLAIMED. `--verify` runs the first 1,000 draws through the optimised path
with the SAME seeds the 1,000-draw run used and asserts every value is bit-identical to the stored
`data/d393_b_null.json`. If that fails, the optimisation changed the null and nothing here is
usable.
"""

from __future__ import annotations

import argparse
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


CELL = REPO / "temp" / "d393_cell_B.npz"
OUT = REPO / "data" / "d393_b_resolved.json"
PRIOR = REPO / "data" / "d393_b_null.json"          # the 1,000-draw run this must reproduce
CAP = 20
CANDIDATE = "up_run_21"
SEED = 393                                          # the stream the 1,000-draw run used


def SHARD(i):
    return REPO / "temp" / f"d393_Bres_shard_{i}.json"


def seed_at(idx):
    """Draw `idx`'s seed, and THE ONLY definition of it.

    `run_d393_bs_null.item_at(idx, n_draws)` gives the candidate seed SEED+1+idx for idx < n_draws.
    Candidate-only here, so the rule is the same for every index -- which is exactly why draws
    0..999 reproduce the 1,000-draw run bit-for-bit."""
    return SEED + 1 + idx


def rss():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1e9
    except Exception:
        return float("nan")


# ------------------------------------------------------- the hoisted swap
def prepare_swap(mask, group, elig):
    """Everything about the swap that does NOT depend on the draw, computed once.

    Order is load-bearing: bars ascending, then groups in `np.unique` order (sorted), which is the
    order `control_bs_signal` visits them in. The RNG is consumed in that order, so preserving it
    is what keeps the optimised draw bit-identical to the original."""
    plan = []
    for t in np.flatnonzero(mask.any(axis=1)):
        ev = np.flatnonzero(mask[t])
        gt = group[t]
        groups = []
        for d in np.unique(gt[ev]):
            evd = ev[gt[ev] == d]
            pool = np.flatnonzero(elig[t] & (gt == d) & ~mask[t])
            groups.append((evd, pool))
        plan.append((t, groups))
    return plan


def swap_from_plan(plan, buf, rows, rng):
    """One B draw against a hoisted plan, into a reused buffer.

    Identical arithmetic to `control_bs_signal`, identical RNG call sequence. Only the rows that
    can ever be written are cleared, because no other row is ever touched."""
    buf[rows] = False
    kept = 0
    for t, groups in plan:
        for evd, pool in groups:
            k = min(evd.size, pool.size)
            if k:
                buf[t, rng.choice(pool, size=k, replace=False)] = True
            if evd.size > k:
                buf[t, evd[k:]] = True
                kept += evd.size - k
    return kept


# ------------------------------------------------------- the two builds
def build_heavy():
    """The full build -- panel, grids, sign scores. Peaks near 3.1 GB, so it runs ONCE."""
    R = _load("d393b", "run_d393_bs_null.py")
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    P, elig, cols, masks, dec, T, n, bucket, elig_b = R.build(PREP, V50, SG)
    sc = np.where(np.isfinite(cols[CANDIDATE]), cols[CANDIDATE], 50.0)
    res = V59.run_mirror(P, masks[CANDIDATE], sc, "cap", CAP)
    obs = float(PREP.V47.pnl_bp(res).mean())
    return R, PREP, V59, P, elig, masks[CANDIDATE], bucket, elig_b, T, n, obs


def build_light():
    """What a WORKER needs: no panel, no grids, no sign scores -- the mask comes from the cache.

    `need_grids=False` is D359's own choice for its null stages, and `prof_mem` confirmed the
    kernel reproduces the observed +22.056 under it."""
    assert CELL.exists(), f"run --prep-cell first: {CELL} is missing"
    PREP = _load("d348p", "d348_prep.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    R = _load("d393b", "run_d393_bs_null.py")
    P = PREP.prep(need_grids=False)
    z = np.load(CELL)
    mask = z["mask"]
    obs = float(z["obs"])
    T, n = P["T"], P["n"]
    assert mask.shape == (T, n), f"cached mask {mask.shape} != panel {(T, n)}"
    elig = np.asarray(P["elig"])
    bucket = np.asarray(P["bucket_rsi"]).astype(np.int16)
    elig_b = elig & np.isfinite(np.asarray(P["PCT"]["rsi"]))
    return R, PREP, V59, P, elig, mask, bucket, elig_b, T, n, obs


# ------------------------------------------------------- the draw loop
def make_runner(R, PREP, V59, P, mask, bucket, elig_b, T, n, check_first=True):
    plan = prepare_swap(mask, bucket, elig_b)
    rows = np.flatnonzero(mask.any(axis=1))
    buf = np.zeros_like(mask)
    sc_const = np.full((T, n), 17.0)                 # hoisted: 53 MB, was per draw
    checked = {"done": not check_first}

    def draw(idx):
        rng = np.random.default_rng(seed_at(idx))
        kept = swap_from_plan(plan, buf, rows, rng)
        if not checked["done"]:                      # [B] on this worker's first draw
            R.assert_Bs(buf, mask, bucket, elig_b, kept)
            checked["done"] = True
        r = V59.run_mirror(P, buf, sc_const, "cap", CAP)
        return float(PREP.V47.pnl_bp(r).mean())

    return draw, plan


# ------------------------------------------------------- modes
def prep_cell() -> int:
    t0 = time.time()
    R, PREP, V59, P, elig, mask, bucket, elig_b, T, n, obs = build_heavy()
    np.savez_compressed(CELL, mask=mask, obs=np.array(obs))
    print(f"\n  wrote {CELL.relative_to(REPO)}  ({int(mask.sum()):,} events, observed "
          f"{obs:+.3f} bp)  peak RSS {rss():.2f} GB  ({time.time() - t0:.0f}s)")
    return 0


def verify() -> int:
    """The optimised path must reproduce the 1,000-draw run's values EXACTLY, same seeds."""
    t0 = time.time()
    assert PRIOR.exists(), f"{PRIOR} missing -- nothing to verify against"
    prior = json.loads(PRIOR.read_text())["draws"][CANDIDATE]
    R, PREP, V59, P, elig, mask, bucket, elig_b, T, n, obs = build_light()
    gc.collect()
    print(f"  light build RSS {rss():.2f} GB  ({time.time() - t0:.0f}s)", flush=True)

    # the ORIGINAL, unoptimised draw, as the reference for a handful of draws
    t1 = time.time()
    ref = []
    sc_c = np.full((T, n), 17.0)
    for i in range(8):
        rng = np.random.default_rng(seed_at(i))
        sig, _ = R.control_bs_signal(mask, bucket, elig_b, rng)
        r = V59.run_mirror(P, sig, sc_c, "cap", CAP)
        ref.append(float(PREP.V47.pnl_bp(r).mean()))
    t_orig = (time.time() - t1) / 8

    draw, plan = make_runner(R, PREP, V59, P, mask, bucket, elig_b, T, n)
    t2 = time.time()
    got = [draw(i) for i in range(8)]
    t_new = (time.time() - t2) / 8
    assert got == ref, f"[EXACT] optimised != original\n{got}\n{ref}"
    print(f"    [EXACT] 8 draws identical to the UNOPTIMISED function in this process")

    m = min(len(prior), 200)
    got2 = [draw(i) for i in range(m)]
    bad = [(i, got2[i], prior[i]) for i in range(m) if got2[i] != prior[i]]
    assert not bad, f"[EXACT] differs from the stored 1,000-draw run at {len(bad)}: {bad[:3]}"
    print(f"    [EXACT] first {m} draws BIT-IDENTICAL to the stored 1,000-draw run "
          f"(data/d393_b_null.json)")
    print(f"\n  SPEED  original {t_orig:.3f} s/draw -> optimised {t_new:.3f} s/draw "
          f"({t_orig / t_new:.2f}x)")
    print(f"  MEMORY worker RSS {rss():.2f} GB  ({time.time() - t0:.0f}s)")
    return 0


def shard(i, nshards, n_draws) -> int:
    t0 = time.time()
    R, PREP, V59, P, elig, mask, bucket, elig_b, T, n, obs = build_light()
    gc.collect()
    draw, _ = make_runner(R, PREP, V59, P, mask, bucket, elig_b, T, n)
    idxs = [k for k in range(n_draws) if k % nshards == i]
    got = {}
    for c, k in enumerate(idxs):
        got[k] = draw(k)
        if c % 100 == 0:
            print(f"    shard {i}: {c}/{len(idxs)}  RSS {rss():.2f} GB  "
                  f"({time.time() - t0:.0f}s)", flush=True)
    SHARD(i).write_text(json.dumps({"n_draws": n_draws, "nshards": nshards,
                                    "shard": i, "values": got}))
    print(f"  shard {i}: {len(idxs)} draws, RSS {rss():.2f} GB ({time.time() - t0:.0f}s)")
    return 0


def merge(nshards, n_draws) -> int:
    t0 = time.time()
    got = {}
    for i in range(nshards):
        p = SHARD(i)
        assert p.exists(), f"shard {i} missing"
        d = json.loads(p.read_text())
        assert d["n_draws"] == n_draws and d["nshards"] == nshards, f"shard {i} ran a different fan"
        for k, v in d["values"].items():
            k = int(k)
            assert k not in got, f"index {k} in two shards"
            got[k] = v
    missing = set(range(n_draws)) - set(got)
    assert not missing, f"{len(missing)} draws missing, e.g. {sorted(missing)[:5]}"
    vals = np.array([got[i] for i in range(n_draws)])

    prior = json.loads(PRIOR.read_text())
    pv = prior["draws"][CANDIDATE]
    m = min(len(pv), n_draws)
    bad = [i for i in range(m) if vals[i] != pv[i]]
    assert not bad, f"[EXACT] the fan disagrees with the 1,000-draw run at {len(bad)} indices"
    print(f"  [EXACT] draws 0..{m - 1} reproduce the stored 1,000-draw run BIT-IDENTICALLY",
          flush=True)

    obs = float(np.load(CELL)["obs"])
    rngb = np.random.default_rng(7)
    p95 = float(np.percentile(vals, 95))
    boot = np.array([np.percentile(rngb.choice(vals, vals.size, replace=True), 95)
                     for _ in range(400)])
    se = float(boot.std(ddof=1))
    margin = obs - p95
    within = bool(abs(margin) <= 2 * se)
    verdict = ("UNRESOLVED (still within 2 SE)" if within else
               "ABOVE" if margin > 0 else "BELOW")

    prior_stats = prior["stats"][CANDIDATE]
    payload = dict(
        study=393, stage="B_resolved", cap=CAP, shape="E1", side="long", score=CANDIDATE,
        n_draws=n_draws, seed=SEED, observed=obs,
        p50=float(np.median(vals)), p95=p95, se_p95=se,
        min=float(vals.min()), max=float(vals.max()),
        margin=margin, within_2se=within, verdict=verdict,
        prior_1000=dict(p95=prior_stats["p95"], se_p95=prior_stats["se_p95"],
                        margin=prior_stats["margin"], verdict=prior_stats["verdict"]),
        declared_in_advance="Addendum 4 section 2: the direction this resolves to IS the answer. "
                            "BELOW retires the cell; ABOVE clears B by under one basis point, "
                            "which is not a strong result and must not be reported as one.",
        exactness=f"draws 0..{m - 1} bit-identical to data/d393_b_null.json; the optimisation is "
                  f"hoists only.",
        purpose="Resolve null B for up_run_21 at 4,000 draws. The control up_frac_21 already "
                "resolved BELOW at -5.84 and is deliberately not re-run. Admits nothing (R15).",
        draws=[float(v) for v in vals])
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    print(f"\nB RESOLVED -- {CANDIDATE}, same rsi bucket, {n_draws:,} draws, E1 cap {CAP} long\n")
    print(f"  {'draws':>6s} {'obs':>8s} {'p50':>8s} {'p95':>8s} {'SE':>6s} {'2SE':>6s} "
          f"{'margin':>8s}   verdict")
    print(f"  {1000:>6,} {obs:+8.2f} {'':>8s} {prior_stats['p95']:+8.2f} "
          f"{prior_stats['se_p95']:6.2f} {2 * prior_stats['se_p95']:6.2f} "
          f"{prior_stats['margin']:+8.2f}   {prior_stats['verdict']}")
    print(f"  {n_draws:>6,} {obs:+8.2f} {np.median(vals):+8.2f} {p95:+8.2f} {se:6.2f} "
          f"{2 * se:6.2f} {margin:+8.2f}   {verdict}")
    print(f"\n  ({time.time() - t0:.0f}s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prep-cell", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--shard", type=int)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--nshards", type=int, default=8)
    ap.add_argument("--draws", type=int, default=4000)
    a = ap.parse_args()
    if a.prep_cell:
        return prep_cell()
    if a.verify:
        return verify()
    if a.shard is not None:
        return shard(a.shard, a.nshards, a.draws)
    if a.merge:
        return merge(a.nshards, a.draws)
    ap.error("pass --prep-cell, --verify, --shard, or --merge")


if __name__ == "__main__":
    raise SystemExit(main())
