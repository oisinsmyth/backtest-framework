"""D378 -- does the entry DAY matter inside the cohort? A'_c, the cohort-conditioned time rotation.

    uv run python scripts/run_d378_entry_day.py --selftest
    uv run python scripts/run_d378_entry_day.py --observed
    uv run python scripts/run_d378_entry_day.py --cells --draws 400 --part 0
    uv run python scripts/run_d378_entry_day.py --report
    --out-dir DIR   (default data/ -- smoke runs pass temp/... so nothing under data/ is touched)

Pre-registration: docs/decisions/D378-does-the-entry-day-matter-inside-the-cohort.md (committed b59776e, BEFORE this file -- R8)
Authorised by the principal's NARROW reopening of the winners'-dip avenue, 2026-09-08. This is the one test it permits.

THE CONTROL. A'_c: for each observed signal bar, draw a replacement bar uniformly from the bars on which THAT SAME NAME was eligible
AND in the mom_252_21 top decile. Name fixed, cohort fixed, per-name count fixed, ONLY THE DAY MOVES.

IT IS A SIGNAL-LEVEL CONTROL, deliberately: the drawn signal grid is fed to the SAME kernel, so the fill convention, the exits, the
slot mechanics and the hedge are identical to the observed book by construction rather than by re-derivation.

WHY NEITHER EXISTING CONTROL ANSWERS IT. A' rotates to any eligible bar, most of them OUTSIDE the top decile, so it prices cohort
membership and timing together -- its centre is +59.42. B_c holds the day fixed by construction. And rho = 0.923 between cohort books
(D376) bounds CO-MOVEMENT, not means: two books can correlate that highly and earn very differently.

EXITS ARE EXCLUDED and R7 made that call: a rule that modifies an existing book needs a MATCHED-COUNT RANDOM-EXIT control, not a
rotation. D235 cleared a rotation null at p95 -0.284 and then landed at the 63rd percentile against the right one. What IS reported,
free, is the horizon profile per BAR HELD for the observed book AND for A'_c -- which settles whether the front-loading belongs to the
dip or to the cohort, without testing any exit RULE.

T3 IS A GATE THIS TIME. D373's H1 passed and then died on one trade (GME 2021-01-04, 6.34% of the ledger). That failure mode is known,
so leave-one-out is pre-registered as a hurdle rather than discovered as a post-hoc.

ASSERTIONS [MIR][POOL][CNT][LAG][DIST][DIR][DEG][X] -- pre-reg s5. [POOL] is the one this study exists on (D351).
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


V77 = _load("d377r", "run_d377_hedge.py")                      # and through it d376, d373, d359, the prep chain
V76, V73, PREP, V59, V58, V50, V47, V53 = V77.V76, V77.V73, V77.PREP, V77.V59, V77.V58, V77.V50, V77.V47, V77.V53
clean = V50.clean
STUDY = 378
DATA = REPO / "data"

(C_MOM, S_REV), (EXIT_, CAP) = V73.CELLS[V73.PRIMARY_IX]       # (10, 90), ("cap", 40)
CELL_NAME = V73.CELL_NAME[V73.PRIMARY_IX]
D373_LEDGER = dict(trades=3932, mean_bp=160.55, median_bp=51.55)
A_PRIME_CENTRE = 59.42                                          # D373 H1's A' p50 -- Q7's lower validity rail
CAPS = (5, 10, 20, 40, 60)                                      # T4: reported, never picked (R14 2026-09-03)
ARM = 1
UNRESOLVED_SE = 2.0
DEGENERATE_MAX = 0.20


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, observed=d / "d378_observed.json", ctrl=str(d / "d378_ctrl_p{part}.json"),
                report=d / "d378_entry_day.json")


# ------------------------------------------------------------------ the pool, and the control built on it
def cohort_pool(P, c=C_MOM):
    """[POOL] the bars a name COULD have been entered on: eligible AND in the mom_252_21 top decile.

    Exactly the cohort leg of V59.mirror_signal -- `(pct_mom >= 100 - c) & elig` -- so the observed signal is a SUBSET of it by
    construction, which assert_POOL checks rather than assumes. grids() documents that pct_mom[t] uses information to t-1.
    """
    pct_mom, _pr, _prev, elig = V59.grids(P)
    with np.errstate(invalid="ignore"):
        return np.ascontiguousarray((pct_mom >= 100.0 - c) & elig)


def aprimec_draw(lo, pool, rng):
    """A'_c: each name's signal bars re-drawn WITHOUT REPLACEMENT from its own cohort pool. Count preserved name by name."""
    out = np.zeros_like(lo)
    cnt = lo.sum(axis=0)
    for j in np.flatnonzero(cnt):
        k = int(cnt[j])
        bars = np.flatnonzero(pool[:, j])
        if bars.size < k:                                       # [DEG] -- counted by pool_stats, never silently patched
            out[bars, j] = True
            continue
        out[rng.choice(bars, size=k, replace=False), j] = True
    return out


def pool_stats(lo, pool):
    """[DIST][DEG] the pool-size distribution per name, and the trades on names that cannot be meaningfully rotated."""
    cnt = lo.sum(axis=0)
    names = np.flatnonzero(cnt)
    sizes = pool[:, names].sum(axis=0)
    tight = sizes < cnt[names]
    return dict(names=int(names.size), trades=int(cnt.sum()),
                pool_min=int(sizes.min()), pool_p50=float(np.median(sizes)), pool_max=int(sizes.max()),
                pool_over_count_p50=float(np.median(sizes / np.maximum(cnt[names], 1))),
                degenerate_names=int(tight.sum()), degenerate_trades=int(cnt[names][tight].sum()),
                degenerate_trade_share=float(cnt[names][tight].sum() / max(1, cnt.sum())))


# ------------------------------------------------------------------ audits
def assert_MIR(P, res):
    pnl = np.asarray(V47.pnl_bp(res), float)
    got = dict(trades=len(res["trades"]), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)))
    assert got["trades"] == D373_LEDGER["trades"], f"[MIR] {got['trades']:,} trades != D373's {D373_LEDGER['trades']:,}"
    for k in ("mean_bp", "median_bp"):
        assert abs(got[k] - D373_LEDGER[k]) < 0.01, f"[MIR] {k} {got[k]:+.4f} != D373's {D373_LEDGER[k]:+.2f}"
    return got


def assert_POOL(sig, pool, tag="[POOL]"):
    """[POOL] THE ASSERTION THIS STUDY EXISTS ON (D351). No drawn event may sit outside the cohort pool.

    D347's rotation traded the sub-$5 tail and its headline INVERTED when the null was confined to the observed universe (D351).
    """
    bad = int((sig & ~pool).sum())
    assert bad == 0, f"{tag} {bad:,} drawn events landed outside the cohort pool"
    return True


def assert_CNT(sig, lo):
    """[CNT] per-name counts preserved NAME BY NAME, not merely in total -- a total-only check passes a book that moved trades
    between names, which would make the control a name swap rather than a time rotation."""
    a, b = sig.sum(axis=0), lo.sum(axis=0)
    assert np.array_equal(a, b), f"[CNT] per-name counts differ on {int((a != b).sum())} names"
    return True


def assert_LAG(P, pool, n_probe=400):
    """[LAG] the pool re-derived from the lagged grid by a SECOND implementation that never calls cohort_pool."""
    pct_mom, _pr, _prev, elig = V59.grids(P)
    pct_mom, elig = np.asarray(pct_mom, float), np.asarray(elig, bool)
    rng = np.random.default_rng([V47.SEED, STUDY, 3])
    T, n = pool.shape
    checked = 0
    for _ in range(n_probe):
        t, j = int(rng.integers(0, T)), int(rng.integers(0, n))
        g = pct_mom[t, j]
        want = bool(np.isfinite(g) and g >= 100.0 - C_MOM and elig[t, j])
        assert bool(pool[t, j]) == want, f"[LAG] pool({t},{j}) = {bool(pool[t, j])}, second implementation says {want}"
        checked += 1
    return dict(checked=checked)


def assert_DIR(pnl):
    """[DIR] the comparison uses the HIGH tail: a duplicated ledger must outrank a zeroed one on the mean."""
    dup, zero = float(pnl.mean()), float(np.zeros_like(pnl).mean())
    assert dup > zero, "[DIR] a zeroed ledger did not fall below the observed -- the test is inverted"
    return dict(observed=dup, zeroed=zero)


def assert_DEG(ps):
    if ps["degenerate_trade_share"] > DEGENERATE_MAX:
        return (f"REFUSED: {ps['degenerate_trades']:,} of {ps['trades']:,} trades sit on names whose pool is smaller than their "
                f"entry count ({ps['degenerate_trade_share']:.1%} > {DEGENERATE_MAX:.0%})")
    return None


# ------------------------------------------------------------------ stages
def prep():
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    return P


def observed_signal(P):
    return V73.mirror(P, C_MOM, S_REV)


def run_cap(P, sig, cap):
    return V73.run_long(P, sig, V59.grids(P)[1], EXIT_, cap)


def profile(P, sig):
    """The horizon profile, per trade AND per bar held, at every cap. T4 -- reported, never picked."""
    out = {}
    for cap in CAPS:
        r = run_cap(P, sig, cap)
        pnl = np.asarray(V47.pnl_bp(r), float)
        hold = float(np.mean([t[2] for t in r["trades"]])) if r["trades"] else float("nan")
        out[cap] = dict(trades=int(pnl.size), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)),
                        hold_mean=hold, bp_per_bar=float(pnl.mean() / hold) if hold else float("nan"))
    return out


def stage_observed(P, paths):
    print("\nOBSERVED -- the ledger and the pool, before any draw. This adjudicates nothing.")
    t0 = time.time()
    lo = observed_signal(P)
    pool = cohort_pool(P)
    res = run_cap(P, lo, CAP)
    mir = assert_MIR(P, res)
    print(f"  [MIR] {CELL_NAME} {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}")
    assert_POOL(lo, pool, "[POOL] the OBSERVED signal must itself lie inside the pool:")
    lag = assert_LAG(P, pool)
    ps = pool_stats(lo, pool)
    print(f"  [POOL] the observed signal is a subset of the cohort pool; [LAG] {lag['checked']} cells re-derived from the lagged grid")
    print(f"  [DIST] {ps['names']} names, pool size min {ps['pool_min']} / median {ps['pool_p50']:.0f} / max {ps['pool_max']}; "
          f"median pool per entry {ps['pool_over_count_p50']:.1f}x")
    print(f"  [DEG] {ps['degenerate_names']} names ({ps['degenerate_trades']:,} trades, {ps['degenerate_trade_share']:.2%}) "
          f"have a pool smaller than their entry count")
    prof = profile(P, lo)
    HH = V77.build_hedges(P)
    h1_mean, h1_med = V77.hedged_trade_stats(P, res, HH, "H1")
    out = dict(study=STUDY, kind="SIGNAL TEST (R15)", cell=CELL_NAME, ledger=mir, pool=ps, lag=lag,
               horizon=prof, under_H1_hedge=dict(mean_bp=h1_mean, median_bp=h1_med), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["observed"].write_text(json.dumps(clean(out)))        # [P] persist before rendering
    print(f"  wrote {paths['observed']}")
    print(f"\n  horizon profile (T4, REPORTED not picked):  {'cap':>5} {'trades':>7} {'mean':>9} {'hold':>6} {'bp/bar':>8}")
    for cap, v in prof.items():
        print(f"                                              {cap:>5} {v['trades']:>7,} {v['mean_bp']:>+9.2f} "
              f"{v['hold_mean']:>6.1f} {v['bp_per_bar']:>8.2f}")
    print(f"\n  under D377's H1 hedge (pre-reg s1, reported beside H0): mean {h1_mean:+.2f}  median {h1_med:+.2f}")
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def stage_cells(P, draws, part, paths):
    print(f"\nCONTROL A'_c -- {draws} draws x {len(CAPS)} caps, part {part}. Name fixed, cohort fixed, count fixed; only the day moves.")
    lo, pool = observed_signal(P), cohort_pool(P)
    res = run_cap(P, lo, CAP)
    assert_MIR(P, res)
    assert_POOL(lo, pool, "[POOL] the OBSERVED signal must itself lie inside the pool:")
    ps = pool_stats(lo, pool)
    r = assert_DEG(ps)
    assert r is None, f"[DEG] {r}"
    print(f"  [MIR][POOL][DEG] observed reproduced; pool median {ps['pool_p50']:.0f} bars, "
          f"degenerate trades {ps['degenerate_trade_share']:.2%}")
    rows, overlap = [], []
    t0 = time.time()
    for d in range(part * draws, (part + 1) * draws):
        rng = np.random.default_rng([V47.SEED, STUDY, ARM, d])
        sig = aprimec_draw(lo, pool, rng)
        assert_POOL(sig, pool)                                  # every draw, not a sample
        assert_CNT(sig, lo)
        overlap.append(float((sig & lo).sum() / max(1, lo.sum())))
        rows.append({str(cap): v for cap, v in profile(P, sig).items()})
        n = d - part * draws + 1
        if n % 20 == 0 or n == draws:
            print(f"    {n}/{draws} ({time.time() - t0:.0f}s, {(time.time() - t0) / n:.2f} s/draw)  {PREP.rss_line()}", flush=True)
    out = dict(study=STUDY, draws=draws, part=part, cell=CELL_NAME, caps=list(CAPS), pool=ps,
               draws_rows=rows, overlap_with_observed=overlap,
               rng="default_rng([SEED, 378, 1, draw])", seconds_per_draw=(time.time() - t0) / max(draws, 1),
               rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["ctrl"].format(part=part))
    f.write_text(json.dumps(clean(out)))                        # [P] persist before rendering
    print(f"  wrote {f} ({time.time() - t0:.0f}s)")
    return out


def load_controls(paths):
    fs = sorted(paths["dir"].glob("d378_ctrl_p*.json"))
    if not fs:
        return None
    parts = [json.loads(f.read_text()) for f in fs]
    assert len({p["part"] for p in parts}) == len(parts), "[CTRL] duplicate parts"
    return dict(parts=[dict(file=f.name, part=p["part"], draws=p["draws"], seconds_per_draw=p["seconds_per_draw"])
                       for f, p in zip(fs, parts)],
                rows=[r for p in parts for r in p["draws_rows"]],
                overlap=[o for p in parts for o in p["overlap_with_observed"]],
                pool=parts[0]["pool"])


def pct_block(vals):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], float)
    if v.size == 0:
        return dict(n=0)
    rng = np.random.default_rng([V47.SEED, STUDY, 99])
    bs = v[rng.integers(0, v.size, size=(400, v.size))]
    return dict(n=int(v.size), p05=float(np.percentile(v, 5)), p50=float(np.percentile(v, 50)),
                p95=float(np.percentile(v, 95)), mean=float(v.mean()), max=float(v.max()),
                se_p95=float(np.percentile(bs, 95, axis=1).std(ddof=1)),
                se_p50=float(np.percentile(bs, 50, axis=1).std(ddof=1)))


def verdict(obs, blk):
    if not blk.get("n"):
        return dict(verdict="UNRESOLVED")
    margin = obs - blk["p95"]
    se = blk["se_p95"]
    v = ("FAIL" if margin <= 0 else ("UNRESOLVED" if se and margin / se < UNRESOLVED_SE else "PASS"))
    return dict(observed=obs, p50=blk["p50"], p95=blk["p95"], se_p95=se, margin=margin,
                margin_in_se=(margin / se if se else None), verdict=v)


def stage_report(P, paths):
    print("\nREPORT")
    t0 = time.time()
    ctrl = load_controls(paths)
    assert ctrl, "[CTRL] no d378_ctrl_p*.json -- run --cells first"
    lo, pool = observed_signal(P), cohort_pool(P)
    res = run_cap(P, lo, CAP)
    mir = assert_MIR(P, res)
    assert_POOL(lo, pool, "[POOL] observed:")
    pnl = np.asarray(V47.pnl_bp(res), float)
    dirc = assert_DIR(pnl)

    K = str(CAP)
    means = [r[K]["mean_bp"] for r in ctrl["rows"]]
    medians = [r[K]["median_bp"] for r in ctrl["rows"]]
    Bm, Bmed = pct_block(means), pct_block(medians)

    T1 = verdict(float(pnl.mean()), Bm)
    T2 = verdict(float(np.median(pnl)), Bmed)
    top = int(np.argmax(pnl))
    keep = np.ones(pnl.size, bool)
    keep[top] = False
    T3 = verdict(float(pnl[keep].mean()), Bm)
    T3.update(dropped_trade=dict(symbol=P["symbols"][res["trades"][top][0]],
                                 entry_date=str(P["dates"][res["trades"][top][1]]),
                                 pnl_bp=float(pnl[top]), share_of_pnl=float(pnl[top] / pnl.sum())))
    obs_prof = profile(P, lo)
    T4 = {}
    for cap in CAPS:
        b = pct_block([r[str(cap)]["bp_per_bar"] for r in ctrl["rows"]])
        T4[cap] = dict(observed=obs_prof[cap]["bp_per_bar"], **{k: b.get(k) for k in ("p50", "p95", "se_p95")},
                       excess=obs_prof[cap]["bp_per_bar"] - (b.get("p50") or 0.0))

    ov = pct_block(ctrl["overlap"])
    gate = "PASS" if (T1["verdict"] == "PASS" and T3["verdict"] == "PASS") else (
        "FAIL" if "FAIL" in (T1["verdict"], T3["verdict"]) else "UNRESOLVED")
    out = dict(study=STUDY, kind="SIGNAL TEST (R15)", cell=CELL_NAME, ledger=mir, dir_check=dirc,
               controls=dict(parts=ctrl["parts"], draws=len(ctrl["rows"]), arm="A'_c cohort-conditioned time rotation"),
               pool=ctrl["pool"], overlap_with_observed=ov,
               T1=T1, T2=T2, T3=T3, T4=T4, gate=gate,
               predictions=score_predictions(T1, T3, T4, Bm, ctrl, ov), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out)))          # [P] PERSIST BEFORE RENDERING
    print(f"  wrote {paths['report']}")
    print_report(out)
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def score_predictions(T1, T3, T4, Bm, ctrl, ov):
    p50 = Bm.get("p50")
    steep_obs = T4[CAPS[0]]["observed"] - T4[CAPS[-1]]["observed"]
    steep_null = (T4[CAPS[0]]["p50"] or 0.0) - (T4[CAPS[-1]]["p50"] or 0.0)
    return {
        "Q1": dict(claim="A'_c p50 lands in +100 to +140 bp", value=p50,
                   held=(None if p50 is None else bool(100.0 <= p50 <= 140.0))),
        "Q2": dict(claim="T1 PASSES and narrowly -- the margin over p95 is under 20 bp",
                   margin=T1.get("margin"), held=bool(T1["verdict"] == "PASS" and (T1.get("margin") or 0) < 20.0)),
        "Q3": dict(claim="AGAINST myself: T3 FAILS -- dropping the largest trade takes it below p95",
                   verdict=T3["verdict"], held=bool(T3["verdict"] != "PASS")),
        "Q4": dict(claim="the observed decays faster across the horizon than A'_c",
                   observed_decay=steep_obs, null_decay=steep_null, held=bool(steep_obs > steep_null)),
        "Q5": dict(claim="median pool size per name exceeds 100 bars", value=ctrl["pool"]["pool_p50"],
                   held=bool(ctrl["pool"]["pool_p50"] > 100)),
        "Q6": dict(claim="fewer than 5% of drawn bars coincide with an observed entry bar",
                   value=ov.get("p50"), held=bool((ov.get("p50") or 1.0) < 0.05)),
        "Q7": dict(claim="A'_c's centre sits between A''s +59.42 and the observed +160.55 -- a validity rail, not a hope",
                   value=p50, held=(None if p50 is None else bool(A_PRIME_CENTRE < p50 < D373_LEDGER["mean_bp"]))),
    }


def print_report(out):
    print(f"\n  {out['cell']}  {out['ledger']['trades']:,} trades  mean {out['ledger']['mean_bp']:+.2f}  "
          f"median {out['ledger']['median_bp']:+.2f}")
    print(f"  A'_c: {out['controls']['draws']} draws.  pool median {out['pool']['pool_p50']:.0f} bars, "
          f"{out['pool']['pool_over_count_p50']:.1f}x the entry count; degenerate trades {out['pool']['degenerate_trade_share']:.2%}")
    o = out["overlap_with_observed"]
    print(f"  drawn bars coinciding with an observed entry: p50 {o['p50']:.2%}  p95 {o['p95']:.2%}")
    print("\n  HURDLES  (judged on the HIGH tail)")
    for k, lbl in (("T1", "gross mean per trade"), ("T2", "gross median per trade (reported)"),
                   ("T3", "T1 with the largest trade removed  [GATE]")):
        d = out[k]
        if "observed" not in d:
            print(f"    {k}  UNRESOLVED  {lbl}")
            continue
        print(f"    {k}  {d['verdict']:<11} {lbl}: obs {d['observed']:+8.2f}  p50 {d['p50']:+8.2f}  p95 {d['p95']:+8.2f}  "
              f"margin {d['margin']:+7.2f} ({(d['margin_in_se'] or 0):+.1f} SE)")
    t = out["T3"].get("dropped_trade")
    if t:
        print(f"         dropped: {t['symbol']} {t['entry_date']}  {t['pnl_bp']:+,.0f} bp = {t['share_of_pnl']:.2%} of the ledger")
    print("\n  T4  HORIZON PROFILE, bp PER BAR HELD -- reported, never picked")
    print(f"    {'cap':>5} {'observed':>10} {'A_c p50':>10} {'A_c p95':>10} {'excess':>9}")
    for cap in CAPS:
        d = out["T4"][cap]
        print(f"    {cap:>5} {d['observed']:>10.2f} {(d['p50'] or 0):>10.2f} {(d['p95'] or 0):>10.2f} {d['excess']:>+9.2f}")
    print(f"\n  GATE (T1 and T3 must both hold): {out['gate']}")
    print("\n  PREDICTIONS")
    for k, v in out["predictions"].items():
        print(f"    {k}  {'HELD' if v['held'] else ('FALSIFIED' if v['held'] is not None else 'UNRESOLVED')}   {v['claim']}")


# ------------------------------------------------------------------ [X]
def stage_selftest(P):
    print("\nSELFTEST")
    t0 = time.time()
    lo, pool = observed_signal(P), cohort_pool(P)
    res = run_cap(P, lo, CAP)
    print("  [MIR] the inherited cell reproduces D373's committed ledger")
    mir = assert_MIR(P, res)
    print(f"       {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}")
    print("  [POOL] the observed signal lies inside the cohort pool")
    assert_POOL(lo, pool)
    print("  [LAG] the pool re-derived from the lagged grid by a second implementation")
    print(f"       {assert_LAG(P, pool)['checked']} cells")
    rng = np.random.default_rng([V47.SEED, STUDY, ARM, 0])
    sig = aprimec_draw(lo, pool, rng)
    print("  [POOL][CNT] a drawn control stays inside the pool and preserves per-name counts")
    assert_POOL(sig, pool)
    assert_CNT(sig, lo)
    ps = pool_stats(lo, pool)
    print(f"       {ps['names']} names; pool median {ps['pool_p50']:.0f} bars = {ps['pool_over_count_p50']:.1f}x the entry count; "
          f"overlap with observed {(sig & lo).sum() / lo.sum():.2%}")
    print("  [DIR] the comparison uses the HIGH tail")
    print(f"       {assert_DIR(np.asarray(V47.pnl_bp(res), float))}")

    print("\n  [X] the audits RAISE on a deliberately broken book")
    broken = {}

    def must_raise(name, fn):
        try:
            fn()
        except AssertionError:
            broken[name] = "RAISED"
            return
        broken[name] = "*** DID NOT RAISE ***"
        raise AssertionError(f"[X] {name} did not raise -- a self-test that cannot fail is worse than none")

    must_raise("mir_truncated", lambda: assert_MIR(P, {**res, "trades": res["trades"][:10]}))
    must_raise("pool_event_outside_cohort", lambda: assert_POOL(np.ones_like(pool), pool))
    # a draw from the FULL eligible set -- i.e. plain A', the control this study exists to replace -- must fail [POOL]
    elig = np.asarray(P["elig"], bool)
    must_raise("pool_drawn_from_elig_not_cohort",
               lambda: assert_POOL(aprimec_draw(lo, elig, np.random.default_rng([V47.SEED, STUDY, 77])), pool))
    must_raise("cnt_trades_moved_between_names",
               lambda: assert_CNT(np.roll(sig, 1, axis=1), lo))
    must_raise("lag_pool_unlagged",
               lambda: assert_LAG(P, np.roll(pool, -1, axis=0)))
    for k, v in broken.items():
        print(f"       {k}: {v}")

    print("\n  [DEG] the guard refuses rather than reporting")
    bad = dict(ps, degenerate_trades=1000, trades=3932, degenerate_trade_share=0.25)
    assert "REFUSED" in (assert_DEG(bad) or ""), "[DEG] a 25% degenerate book was not refused"
    print(f"       {assert_DEG(bad)}")
    assert assert_DEG(ps) is None, "[DEG] the real book was wrongly refused"
    print(f"       the real book: {ps['degenerate_trade_share']:.2%} degenerate, reported not refused")
    print(f"\n  selftest OK ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--observed", action="store_true")
    ap.add_argument("--cells", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=400)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D378  does the entry DAY matter inside the cohort? A'_c, the cohort-conditioned time rotation")
    paths = out_paths(a.out_dir)
    P = prep()
    if a.selftest:
        stage_selftest(P)
    elif a.observed:
        stage_observed(P, paths)
    elif a.cells:
        stage_cells(P, a.draws, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --observed, --cells, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
