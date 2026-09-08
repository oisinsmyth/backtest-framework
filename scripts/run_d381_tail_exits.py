"""D381 -- stops and targets at thresholds that actually select a tail.

    uv run python scripts/run_d381_tail_exits.py --selftest
    uv run python scripts/run_d381_tail_exits.py --run --draws 2000
    --out-dir DIR   (default data/)

Pre-registration: docs/decisions/D381-stops-and-targets-at-thresholds-that-actually-select-a-tail.md (committed 6c2d6b5, BEFORE this
file -- R8)

WHAT D380 GOT WRONG AND THIS FIXES. D380's +/-200 bp thresholds fired on ~80% of trades, because the fire rate is set by the PATH's
excursion distribution and not by the terminal mean: the median trade swings +839 up and -773 down at some point in its life. So
+/-200 never selected a tail, it fired on the first meaningful move. Here the FIRE RATE is declared and the basis points follow.

BOTH BENCHMARKS. D380 section 2 found R7's matched-count control INHERITS whichever trades the rule selects -- p50 +11.95 when the
rule fires on winners, +181.11 when it fires on losers, the latter HARDER THAN DOING NOTHING. A control-only verdict is therefore
uninterpretable, and D380's own pre-registration omitted the baseline. V1 requires BOTH legs: beat the control's p95 AND beat the
un-overlaid +160.55.

That mechanism also gives a DIRECTIONAL VALIDITY CHECK (pre-reg s3): stop controls should centre ABOVE the baseline and target
controls below it. If not, the arms are reported as UNINTERPRETABLE rather than as verdicts.

[CAL] is the assertion this record exists for: each arm's REALISED fire rate within 2 points of its declared rate.

ASSERTIONS [MIR][CUT][OVL][R7][CAL][MONO][FIRE][DIR][X] -- pre-reg s5.
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


V80 = _load("d380r", "run_d380_exit_rules.py")                 # the re-cut machinery, the R7 control, the assertions
V77, V73, PREP, V59, V47 = V80.V77, V80.V73, V80.PREP, V80.V59, V80.V47
clean = V80.clean
STUDY = 381
DATA = REPO / "data"
CELL_NAME = V80.CELL_NAME
D373_LEDGER = V80.D373_LEDGER
CAP = V80.CAP

# pre-reg s2. Declared as FIRE RATES; the basis points follow from the baseline's own excursion distribution and are written out
# because they were already computed and published in D380 section 6a -- more honest than implying they are unseen.
ARMS = {"T05": ("target", 0.05, 3798.8), "T10": ("target", 0.10, 2837.6), "T20": ("target", 0.20, 1881.2),
        "S05": ("stop", 0.05, -3229.4), "S10": ("stop", 0.10, -2510.8), "S20": ("stop", 0.20, -1743.0)}
CAL_TOL = 0.02                                                 # [CAL] 2 percentage points
BEST_OF_SE = 4.0                                               # best-of-6 pricing (pre-reg s4)
UNRESOLVED_SE = 2.0


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, report=d / "d381_tail_exits.json")


# ------------------------------------------------------------------ the arms
def excursions(C, holds0):
    """Each trade's best and worst point along its OWN path, within its own hold. The quantity that sets a fire rate."""
    mask = np.arange(C.shape[1])[None, :] < holds0[:, None]
    return np.where(mask, C, -np.inf).max(axis=1), np.where(mask, C, np.inf).min(axis=1)


def arm_holds(C, holds0, kind, thr):
    """First bar the cumulative path reaches the threshold, else the baseline hold. Never lengthens -- [OVL] proves it."""
    with np.errstate(invalid="ignore"):
        hit = (C >= thr) if kind == "target" else (C <= thr)
    hit &= np.arange(C.shape[1])[None, :] < holds0[:, None]
    first = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, holds0)
    return np.minimum(first, holds0).astype(np.int64)


def assert_CAL(realised, declared, name):
    """[CAL] the arm fires where it was calibrated to fire. The whole point of this record."""
    d = abs(realised - declared)
    assert d <= CAL_TOL, f"[CAL] {name} fires on {realised:.1%}, declared {declared:.0%} -- off by {d:.1%}, above {CAL_TOL:.0%}"
    return True


def assert_MONO(fired):
    """[MONO] fire rates monotone in threshold within each direction; a non-monotone grid means the excursion maths is wrong."""
    for pre in ("T", "S"):
        r = [fired[f"{pre}{s}"] for s in ("05", "10", "20")]
        assert r[0] <= r[1] <= r[2], f"[MONO] {pre} fire rates are not monotone: {r}"
    return True


# ------------------------------------------------------------------ stages
def prep():
    return V80.prep()


def stage_run(P, draws, paths):
    print(f"\nRUN -- {CELL_NAME}, {len(ARMS)} arms x {draws} draws, BOTH benchmarks (pre-reg s3)")
    t0 = time.time()
    res0 = V80.baseline(P)
    mir = V80.assert_MIR(P, res0)
    pnl0 = np.asarray(V47.pnl_bp(res0), float)
    C, holds0 = V80.trade_paths(P, res0)
    cut = V80.assert_CUT(C, holds0, pnl0)
    base_mean, base_med = float(pnl0.mean()), float(np.median(pnl0))
    print(f"  [MIR] {mir['trades']:,} trades  mean {base_mean:+.2f}  median {base_med:+.2f}")
    print(f"  [CUT] {cut['max_abs_dev']:.3e}")
    up, dn = excursions(C, holds0)
    print(f"  excursions: favourable p50 {np.median(up):+.1f} p90 {np.percentile(up, 90):+.1f} | "
          f"adverse p50 {np.median(dn):+.1f} p10 {np.percentile(dn, 10):+.1f}")

    top = int(np.argmax(pnl0))
    keep = np.ones(pnl0.size, bool)
    keep[top] = False
    pool = np.flatnonzero(holds0 > 1)
    out, fired_share = {}, {}
    for i, (name, (kind, rate, thr)) in enumerate(ARMS.items()):
        hk = arm_holds(C, holds0, kind, thr)
        n_fired = V80.assert_OVL(hk, holds0, name)
        share = n_fired / hk.size
        fired_share[name] = share
        assert_CAL(share, rate, name)
        r = V80.assert_FIRE(n_fired, hk.size, name)
        assert r is None, f"[FIRE] {r}"
        sel = np.flatnonzero(hk < holds0)
        p = V80.pnl_at(C, hk)
        strict = V80.control_block(C, holds0, sel, draws, seed_arm=i + 1, strict=True)
        loose = V80.control_block(C, holds0, sel, draws, seed_arm=i + 21, strict=False, pool=pool)
        vs_ctrl = V80.verdict(float(p.mean()), strict["mean"])
        beats_base = bool(p.mean() > base_mean)
        lo1 = V80.verdict(float(p[keep].mean()), strict["leave_one_out"])
        out[name] = dict(
            kind=kind, declared_rate=rate, threshold_bp=thr, fired=n_fired, fired_share=share,
            hold_mean=float(hk.mean()), mean_bp=float(p.mean()), median_bp=float(np.median(p)),
            bp_per_bar=float(p.mean() / hk.mean()),
            vs_control=vs_ctrl, beats_baseline=beats_base,
            V1=("PASS" if (vs_ctrl["verdict"] == "PASS" and vs_ctrl.get("margin_in_se", 0) >= BEST_OF_SE and beats_base)
                else "FAIL"),
            V2=("PASS" if (lo1["verdict"] == "PASS" and float(p[keep].mean()) > float(pnl0[keep].mean())) else "FAIL"),
            leave_one_out=lo1, vs_loose=V80.verdict(float(p.mean()), loose["mean"]),
            control_p50=strict["mean"]["p50"], control_p95=strict["mean"]["p95"],
            control_above_baseline=bool(strict["mean"]["p50"] > base_mean),
            loose_p50=loose["mean"]["p50"])
        v = out[name]
        print(f"  {name}  {kind:<6} fire {share:>5.1%} (declared {rate:.0%})  thr {thr:>+9.1f}  hold {hk.mean():5.1f}  "
              f"mean {p.mean():+8.2f}  ctrl p50 {v['control_p50']:+8.2f}  V1 {v['V1']}  V2 {v['V2']}")
    assert_MONO(fired_share)

    # pre-reg s3's directional validity check
    tgt_below = all(out[k]["control_p50"] < base_mean for k in ("T05", "T10", "T20"))
    stp_above = all(out[k]["control_p50"] > base_mean for k in ("S05", "S10", "S20"))
    valid = bool(tgt_below and stp_above)
    report = dict(study=STUDY, kind="SIGNAL TEST on an OVERLAY (R15, governed by R7)", cell=CELL_NAME,
                  baseline=dict(**mir, hold_mean=float(holds0.mean()), bp_per_bar=float(base_mean / holds0.mean()),
                                mean_ex_top1=float(np.sort(pnl0)[:-max(1, int(0.01 * pnl0.size))].mean())),
                  cut=cut, draws=draws, arms=out,
                  directional_check=dict(target_controls_below_baseline=tgt_below,
                                         stop_controls_above_baseline=stp_above, valid=valid,
                                         note="pre-reg s3/s8: if this fails the arms are UNINTERPRETABLE, not verdicts"),
                  excursions=dict(fav_p50=float(np.median(up)), fav_p90=float(np.percentile(up, 90)),
                                  adv_p50=float(np.median(dn)), adv_p10=float(np.percentile(dn, 10))),
                  predictions=score_predictions(out, base_mean, fired_share), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(report)))       # [P] PERSIST BEFORE RENDERING
    print(f"  wrote {paths['report']}")
    print_report(report)
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return report


def score_predictions(A, base_mean, fired):
    tgts = [A[k]["mean_bp"] for k in ("T05", "T10", "T20")]
    stops = {k: A[k]["mean_bp"] for k in ("S05", "S10", "S20")}
    best_stop = max(stops, key=stops.get)
    return {
        "Q1": dict(claim="all three TARGET arms reduce the mean below the baseline",
                   values=tgts, held=bool(all(t < base_mean for t in tgts))),
        "Q2": dict(claim="at least one STOP arm beats the baseline's mean", values=stops,
                   held=bool(any(v > base_mean for v in stops.values()))),
        "Q3": dict(claim="stop controls centre ABOVE the baseline and target controls below",
                   held=bool(all(A[k]["control_above_baseline"] for k in ("S05", "S10", "S20"))
                             and not any(A[k]["control_above_baseline"] for k in ("T05", "T10", "T20")))),
        "Q4": dict(claim="AGAINST myself: NO arm clears V1 on both legs",
                   held=bool(all(v["V1"] != "PASS" for v in A.values()))),
        "Q5": dict(claim="[CAL] holds on all six -- realised fire rates within 2 points of declared",
                   values={k: round(v, 4) for k, v in fired.items()}, held=True),
        "Q6": dict(claim="the best stop arm is S10 or S20, not S05", value=best_stop,
                   held=bool(best_stop in ("S10", "S20"))),
        "Q7": dict(claim="the stops barely change the holding run -- cost is not what decides this",
                   values={k: round(A[k]["hold_mean"], 2) for k in ("S05", "S10", "S20")},
                   held=bool(all(A[k]["hold_mean"] > 0.8 * 39.94 for k in ("S05", "S10", "S20")))),
    }


def print_report(o):
    b = o["baseline"]
    print(f"\n  baseline {b['trades']:,} trades  mean {b['mean_bp']:+.2f}  median {b['median_bp']:+.2f}  "
          f"hold {b['hold_mean']:.1f}  mean ex-top-1% {b['mean_ex_top1']:+.2f}")
    print(f"\n  {'arm':<5} {'kind':<7} {'fire':>6} {'threshold':>11} {'hold':>6} {'mean':>9} {'median':>10} "
          f"{'ctrl p50':>9} {'ctrl p95':>9} {'in SE':>7} {'>base':>6} {'V1':<6} {'V2':<6}")
    for k, v in o["arms"].items():
        se = v["vs_control"].get("margin_in_se")
        print(f"  {k:<5} {v['kind']:<7} {v['fired_share']:>6.1%} {v['threshold_bp']:>+11.1f} {v['hold_mean']:>6.1f} "
              f"{v['mean_bp']:>+9.2f} {v['median_bp']:>+10.2f} {v['control_p50']:>+9.2f} {v['control_p95']:>+9.2f} "
              f"{(se if se is not None else 0):>+7.1f} {str(v['beats_baseline']):>6} {v['V1']:<6} {v['V2']:<6}")
    d = o["directional_check"]
    print(f"\n  DIRECTIONAL VALIDITY (pre-reg s3): target controls below baseline {d['target_controls_below_baseline']}, "
          f"stop controls above {d['stop_controls_above_baseline']} -> {'VALID' if d['valid'] else 'UNINTERPRETABLE'}")
    print("\n  PREDICTIONS")
    for k, v in o["predictions"].items():
        print(f"    {k}  {'HELD' if v['held'] else 'FALSIFIED'}   {v['claim']}")


def stage_selftest(P):
    print("\nSELFTEST")
    t0 = time.time()
    res0 = V80.baseline(P)
    pnl0 = np.asarray(V47.pnl_bp(res0), float)
    C, holds0 = V80.trade_paths(P, res0)
    print("  [MIR] the baseline reproduces D373's committed ledger")
    mir = V80.assert_MIR(P, res0)
    print(f"       {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}")
    print(f"  [CUT] {V80.assert_CUT(C, holds0, pnl0)['max_abs_dev']:.3e}")
    fired = {}
    print("  [OVL][CAL] every arm shortens, and fires where it was calibrated to")
    for name, (kind, rate, thr) in ARMS.items():
        hk = arm_holds(C, holds0, kind, thr)
        n = V80.assert_OVL(hk, holds0, name)
        fired[name] = n / hk.size
        assert_CAL(fired[name], rate, name)
        print(f"       {name} {kind:<6} thr {thr:>+9.1f}  fires {fired[name]:>6.2%} (declared {rate:.0%})  hold {hk.mean():5.1f}")
    print("  [MONO] fire rates monotone in threshold")
    assert_MONO(fired)

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

    must_raise("cal_threshold_off_scale",
               lambda: assert_CAL(float((arm_holds(C, holds0, "target", 200.0) < holds0).mean()), 0.10, "toy"))
    must_raise("mono_reversed", lambda: assert_MONO({**fired, "T05": 0.9}))
    must_raise("ovl_lengthens", lambda: V80.assert_OVL(holds0 + 1, holds0, "toy"))
    bad = C.copy()
    bad[0, holds0[0] - 1] += 1.0
    must_raise("cut_perturbed_endpoint", lambda: V80.assert_CUT(bad, holds0, pnl0))
    for k, v in broken.items():
        print(f"       {k}: {v}")
    print(f"\n  selftest OK ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D381  stops and targets at thresholds that actually select a tail")
    paths = out_paths(a.out_dir)
    P = prep()
    if a.selftest:
        stage_selftest(P)
    elif a.run:
        stage_run(P, a.draws, paths)
    else:
        ap.error("one of --selftest, --run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
