"""D380 -- does the exit rule beat a RANDOM CUT of the same trades? R7's control, which D235 needed and did not have.

    uv run python scripts/run_d380_exit_rules.py --selftest
    uv run python scripts/run_d380_exit_rules.py --run --draws 2000
    --out-dir DIR   (default data/ -- smoke runs pass temp/... so nothing under data/ is touched)

Pre-registration: docs/decisions/D380-does-the-exit-rule-beat-a-random-cut.md (committed e6365fb, BEFORE this file -- R8)

R7 GOVERNS. An overlay -- a stop, a target, a partial exit -- must be nulled against a control that KEEPS THE BASE BOOK and
randomises only the overlay's decisions, MATCHED ON HOW MANY IT MAKES. D235 cleared a rotation null at p95 -0.284 (a bar anything not
actively harmful would clear) and then landed at the 63rd PERCENTILE against the correct control. D378 excluded exits for exactly this
reason; this is the study that does them properly.

THE CONTROL, and it is the harder version deliberately: take exactly the trades a rule shortens, keep that SET and that COUNT fixed,
and cut each at a bar drawn uniformly from its OWN window [1, hold_E0). That grants the rule its trade selection for free and asks only
whether it cut at the right BAR -- which isolates exit TIMING. A LOOSE control that also re-draws WHICH trades are cut is reported
beside it: beating the loose one while failing the strict one means the rule picks trades, not bars (U3).

EACH RULE GETS ITS OWN CONTROL WITH ITS OWN N. A target fires on a different number of trades than an invalidation does, and a control
matched on the wrong count is not matched.

WHY THIS RUNS IN SECONDS. Per-trade P&L is the sum of a trade's OWN per-bar path, so every rule and every control draw is a re-cut of
one stored cumulative-sum matrix -- no kernel re-run per draw. [CUT] proves the re-cut reproduces the kernel's own per-trade P&L before
any rule is applied; D377's analogue [REC] fired at 1e-3 and found a real specification error.

AND THE ONE PLACE IT IS NOT EXACT, scoped in the pre-registration rather than discovered here: the per-BAR DEPLOYED book cannot be
re-cut, because an earlier exit frees a slot and changes what is held next. The deployed series is therefore reported only for E0 and
E1 from GENUINE KERNEL RUNS and is never compared to a control draw.

ASSERTIONS [MIR][CUT][OVL][R7][FIRE][DIR][X] -- pre-reg s6. [X] is the one that matters.
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


V78 = _load("d378r", "run_d378_entry_day.py")                  # and through it d377/d376/d373/d359 and the prep chain
V77, V73, PREP, V59, V58, V50, V47, V53 = V78.V77, V78.V73, V78.PREP, V78.V59, V78.V58, V78.V50, V78.V47, V78.V53
clean = V50.clean
STUDY = 380
DATA = REPO / "data"

(C_MOM, S_REV), (EXIT0, CAP) = V73.CELLS[V73.PRIMARY_IX]       # (10, 90), ("cap", 40)
CELL_NAME = V73.CELL_NAME[V73.PRIMARY_IX]
D373_LEDGER = dict(trades=3932, mean_bp=160.55, median_bp=51.55)
TARGET_BP, STOP_BP = 200.0, -200.0                             # pre-reg s2: DECLARED here, round, symmetric, NOT swept
RULES = ("E1", "E2", "E3")
RULE_NAME = {"E0": "40-bar cap (incumbent)", "E1": "signal invalidation, capped 40",
             "E2": f"profit target {TARGET_BP:+.0f} bp", "E3": f"stop {STOP_BP:+.0f} bp"}
FIRE_MIN = 0.01                                                # [FIRE] pre-reg s6
UNRESOLVED_SE = 2.0
CUT_TOL = 1e-9                                                 # pre-reg s4


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, report=d / "d380_exit_rules.json")


# ------------------------------------------------------------------ the paths, and the re-cut built on them
def trade_paths(P, res):
    """Each trade's per-bar HEDGED return in bp, as a padded cumulative-sum matrix C[i, k] = sum of bars 0..k.

    The kernel's own arithmetic for a long: bar 0 uses the OPEN-to-close pair (ocT, m_f_oc) because the fill is at the next open
    (D340); every later bar uses (r1T, m_f). [CUT] is what proves this reproduces the kernel rather than merely resembling it.
    """
    r1T, ocT = np.asarray(P["r1T"], float), np.asarray(P["ocT"], float)
    m_f, m_f_oc = np.asarray(P["m_f"], float), np.asarray(P["m_f_oc"], float)
    tr = res["trades"]
    holds = np.array([t[2] for t in tr], np.int64)
    H = int(holds.max())
    C = np.full((len(tr), H), np.nan)
    for i, (row, e0, age, _p, side) in enumerate(tr):
        sgn = 1.0 if side == 0 else -1.0
        v = r1T[e0:e0 + age, row].copy()
        mm = m_f[e0:e0 + age].copy()
        v[0], mm[0] = ocT[e0, row], m_f_oc[e0]
        C[i, :age] = np.cumsum(sgn * np.nan_to_num(v - mm)) * 1e4
    return C, holds


def pnl_at(C, holds):
    """P&L of each trade held `holds[i]` bars -- the cumulative sum at index holds-1."""
    return C[np.arange(C.shape[0]), np.asarray(holds, np.int64) - 1]


def invalidation_holds(P, res0, holds0):
    """E1 AS AN OVERLAY: the kernel's invalidation condition applied to the BASELINE's own trades, with NO re-entry.

    Amendment 571b9d3. The kernel's ("invalidation", 40) run is NOT an overlay -- exiting at a mean 6.32 bars frees each name to take
    signals the 40-bar cap suppressed, so it holds 7,945 trades against the baseline's 3,932 from the same 10,270 events. That is a
    different BOOK, not a modified one, and R7's matched-count control would be meaningless for it.

    So the condition is re-applied here to the baseline's trade set. For a LONG the kernel exits when the score reverts to >= 50
    (V59.simulate's docstring; EB.simulate_event step 1). `assert_INV` proves this reproduces the kernel's own holds on every entry the
    two runs share -- 3,810 of them, zero mismatches -- so this is the kernel's rule re-applied, not a re-derivation of it.
    """
    sc = np.asarray(V59.grids(P)[1], float)
    out = np.empty_like(holds0)
    for i, (row, e0, age, _p, _side) in enumerate(res0["trades"]):
        s = sc[e0 + 1:e0 + age, row]
        hit = np.flatnonzero(np.isfinite(s) & (s >= 50.0))
        out[i] = (hit[0] + 1) if hit.size else age
    return out


def assert_INV(P, res0, holds0, h_recut):
    """[INV] the re-cut invalidation equals the KERNEL's own hold on every entry the two runs share (amendment 571b9d3)."""
    r1 = V73.run_long(P, V73.mirror(P, C_MOM, S_REV), V59.grids(P)[1], "invalidation", CAP)
    k1 = {(t[0], t[1]): t[2] for t in r1["trades"]}
    shared = bad = 0
    for i, (row, e0, _a, _p, _s) in enumerate(res0["trades"]):
        kh = k1.get((row, e0))
        if kh is None:
            continue
        shared += 1
        if min(int(kh), int(holds0[i])) != int(h_recut[i]):
            bad += 1
    assert shared > 1000, f"[INV] only {shared} shared entries -- the check proved nothing"
    assert bad == 0, f"[INV] the re-cut differs from the kernel on {bad:,} of {shared:,} shared entries"
    return dict(shared=shared, mismatches=bad, kernel_book_trades=len(r1["trades"]), baseline_trades=len(res0["trades"]),
                kernel_book_mean_bp=float(np.asarray(V47.pnl_bp(r1), float).mean()),
                kernel_book_hold_mean=float(np.mean([t[2] for t in r1["trades"]])), _res=r1)


def rule_holds(P, res0, C, holds0):
    """Each rule's per-trade hold, all as OVERLAYS on the baseline's trade set (amendment 571b9d3)."""
    out = {"E1": invalidation_holds(P, res0, holds0)}
    with np.errstate(invalid="ignore"):
        hit_t = C >= TARGET_BP
        hit_s = C <= STOP_BP
    for key, hit in (("E2", hit_t), ("E3", hit_s)):
        first = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, holds0)
        out[key] = np.minimum(first, holds0).astype(np.int64)
    return out


# ------------------------------------------------------------------ audits
def assert_MIR(P, res):
    pnl = np.asarray(V47.pnl_bp(res), float)
    got = dict(trades=len(res["trades"]), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)))
    assert got["trades"] == D373_LEDGER["trades"], f"[MIR] {got['trades']:,} trades != D373's {D373_LEDGER['trades']:,}"
    for k in ("mean_bp", "median_bp"):
        assert abs(got[k] - D373_LEDGER[k]) < 0.01, f"[MIR] {k} {got[k]:+.4f} != D373's {D373_LEDGER[k]:+.2f}"
    return got


def assert_CUT(C, holds0, pnl0):
    """[CUT] the re-cut baseline reproduces the KERNEL's own per-trade P&L. D377's analogue fired at 1e-3 on a real defect."""
    d = float(np.abs(pnl_at(C, holds0) - pnl0).max())
    assert d < CUT_TOL, f"[CUT] the re-cut misses the kernel by {d:.3e}, above {CUT_TOL:.0e} -- the paths are not the kernel's"
    return dict(max_abs_dev=d, tol=CUT_TOL)


def assert_OVL(hk, holds0, name):
    """[OVL] an overlay SHORTENS. Same trade count, and every hold at or below the baseline's. A rule that lengthens is not one."""
    assert hk.shape == holds0.shape, f"[OVL] {name} changed the trade count"
    bad = int((hk > holds0).sum())
    assert bad == 0, f"[OVL] {name} LENGTHENED {bad:,} trades -- that is not an overlay"
    assert (hk >= 1).all(), f"[OVL] {name} produced a hold below 1 bar"
    return int((hk < holds0).sum())


def assert_R7(cut_idx, draw_holds, sel, holds0, name):
    """[R7] the control cuts THE SAME TRADES, at the SAME COUNT, at bars inside each trade's OWN window."""
    assert np.array_equal(np.sort(cut_idx), np.sort(sel)), f"[R7] {name}'s control cut a different set of trades than the rule did"
    assert cut_idx.size == sel.size, f"[R7] {name}'s control cut {cut_idx.size} trades against the rule's {sel.size}"
    h = draw_holds[cut_idx]
    assert (h >= 1).all() and (h < holds0[cut_idx]).all(), f"[R7] {name}'s control cut outside a trade's own window"
    return True


def assert_FIRE(n_fired, n_trades, name):
    share = n_fired / max(1, n_trades)
    if share < FIRE_MIN:
        return f"REFUSED: {name} shortens {n_fired:,} of {n_trades:,} trades ({share:.2%} < {FIRE_MIN:.0%}) -- its control is matched on almost nothing"
    return None


def assert_DIR(pnl):
    assert float(pnl.mean()) > float(np.zeros_like(pnl).mean()), "[DIR] a zeroed ledger did not fall below the observed"
    return dict(observed=float(pnl.mean()), zeroed=0.0)


# ------------------------------------------------------------------ the controls
def draw_control(C, holds0, sel, rng, strict=True, pool=None):
    """One control draw. strict: cut exactly `sel`. loose: cut a fresh random subset of the same SIZE from `pool`."""
    idx = sel if strict else rng.choice(pool, size=sel.size, replace=False)
    h = holds0.copy()
    h[idx] = rng.integers(1, holds0[idx])                       # uniform on [1, hold0) -- each trade's own window
    return idx, h


def control_block(C, holds0, sel, draws, seed_arm, strict, pool=None):
    rng = np.random.default_rng([V47.SEED, STUDY, seed_arm, int(strict)])
    means, medians, lo1 = [], [], []
    top = int(np.argmax(pnl_at(C, holds0)))
    keep = np.ones(C.shape[0], bool)
    keep[top] = False
    for _ in range(draws):
        idx, h = draw_control(C, holds0, sel, rng, strict, pool)
        assert_R7(idx if strict else np.sort(idx), h, idx if strict else np.sort(idx), holds0, "control")
        p = pnl_at(C, h)
        means.append(float(p.mean()))
        medians.append(float(np.median(p)))
        lo1.append(float(p[keep].mean()))
    return dict(mean=pct_block(means), median=pct_block(medians), leave_one_out=pct_block(lo1), draws=draws)


def pct_block(vals):
    v = np.asarray(vals, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return dict(n=0)
    rng = np.random.default_rng([V47.SEED, STUDY, 99])
    bs = v[rng.integers(0, v.size, size=(400, v.size))]
    return dict(n=int(v.size), p05=float(np.percentile(v, 5)), p50=float(np.percentile(v, 50)),
                p95=float(np.percentile(v, 95)), mean=float(v.mean()), max=float(v.max()),
                se_p95=float(np.percentile(bs, 95, axis=1).std(ddof=1)))


def verdict(obs, blk):
    if not blk.get("n"):
        return dict(verdict="UNRESOLVED")
    margin, se = obs - blk["p95"], blk["se_p95"]
    v = "FAIL" if margin <= 0 else ("UNRESOLVED" if se and margin / se < UNRESOLVED_SE else "PASS")
    return dict(observed=obs, p50=blk["p50"], p95=blk["p95"], se_p95=se, margin=margin,
                margin_in_se=(margin / se if se else None), verdict=v)


# ------------------------------------------------------------------ stages
def prep():
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    return P


def baseline(P):
    return V73.run_long(P, V73.mirror(P, C_MOM, S_REV), V59.grids(P)[1], EXIT0, CAP)


def stage_run(P, draws, paths):
    print(f"\nRUN -- {CELL_NAME}, {draws} draws per control, R7-matched")
    t0 = time.time()
    res0 = baseline(P)
    mir = assert_MIR(P, res0)
    pnl0 = np.asarray(V47.pnl_bp(res0), float)
    C, holds0 = trade_paths(P, res0)
    cut = assert_CUT(C, holds0, pnl0)
    print(f"  [MIR] {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}")
    print(f"  [CUT] the re-cut reproduces the kernel to {cut['max_abs_dev']:.3e} (tol {CUT_TOL:.0e})")
    dirc = assert_DIR(pnl0)

    RH = rule_holds(P, res0, C, holds0)
    inv = assert_INV(P, res0, holds0, RH["E1"])
    kernel_book = inv.pop("_res")
    print(f"  [INV] the re-cut invalidation equals the kernel's hold on all {inv['shared']:,} shared entries, "
          f"{inv['mismatches']} mismatches")
    print(f"        the kernel's own invalidation BOOK holds {inv['kernel_book_trades']:,} trades (mean hold "
          f"{inv['kernel_book_hold_mean']:.2f}) against the baseline's {inv['baseline_trades']:,} -- a DIFFERENT book, "
          f"reported with NO control (amendment 571b9d3)")

    top = int(np.argmax(pnl0))
    keep = np.ones(pnl0.size, bool)
    keep[top] = False
    pool = np.flatnonzero(holds0 > 1)
    out_rules, refusals = {}, {}
    for k in RULES:
        hk = RH[k]
        n_fired = assert_OVL(hk, holds0, k)
        r = assert_FIRE(n_fired, hk.size, k)
        if r:
            refusals[k] = r
            print(f"  [FIRE] {r}")
            continue
        sel = np.flatnonzero(hk < holds0)
        p = pnl_at(C, hk)
        strict = control_block(C, holds0, sel, draws, seed_arm=RULES.index(k) + 1, strict=True)
        loose = control_block(C, holds0, sel, draws, seed_arm=RULES.index(k) + 11, strict=False, pool=pool)
        out_rules[k] = dict(
            name=RULE_NAME[k], fired=n_fired, fired_share=n_fired / hk.size,
            hold_mean=float(hk.mean()), hold_median=float(np.median(hk)),
            mean_bp=float(p.mean()), median_bp=float(np.median(p)), bp_per_bar=float(p.mean() / hk.mean()),
            U1=verdict(float(p.mean()), strict["mean"]),
            U2=verdict(float(p[keep].mean()), strict["leave_one_out"]),
            U3=dict(median=verdict(float(np.median(p)), strict["median"]),
                    vs_loose=verdict(float(p.mean()), loose["mean"])),
            strict=strict, loose=loose)
        v = out_rules[k]
        print(f"  {k} {RULE_NAME[k]:<32} fires {n_fired:>5,} ({n_fired / hk.size:>5.1%})  hold {hk.mean():5.1f}  "
              f"mean {p.mean():+8.2f}  U1 {v['U1']['verdict']:<11} U2 {v['U2']['verdict']}")

    # U4 -- what the exit keys on (CLAUDE.md's D285 lesson), and the deployed book for E0 and E1 only (pre-reg s4)
    h1 = RH["E1"]
    U4 = dict(E1=dict(trigger_fired=int((h1 < holds0).sum()), cap_bound=int(((h1 == holds0) & (holds0 == CAP)).sum()),
                      natural_end=int(((h1 == holds0) & (holds0 < CAP)).sum()),
                      hold_hist={str(b): int(v) for b, v in zip(*np.histogram(h1, bins=[1, 5, 10, 20, 30, 40, 41])[::-1])}))
    dep = dict(E0=V59.deployed_block(res0, P), invalidation_book_UNCONTROLLED=V59.deployed_block(kernel_book, P))
    HH = V77.build_hedges(P)
    h1_hedge = dict(zip(("mean_bp", "median_bp"), V77.hedged_trade_stats(P, res0, HH, "H1")))

    gate = {k: ("PASS" if (v["U1"]["verdict"] == "PASS" and v["U2"]["verdict"] == "PASS") else
                ("FAIL" if "FAIL" in (v["U1"]["verdict"], v["U2"]["verdict"]) else "UNRESOLVED"))
            for k, v in out_rules.items()}
    out = dict(study=STUDY, kind="SIGNAL TEST on an OVERLAY (R15, governed by R7)", cell=CELL_NAME,
               baseline=dict(**mir, hold_mean=float(holds0.mean()), bp_per_bar=float(pnl0.mean() / holds0.mean())),
               cut=cut, inv=inv, dir_check=dirc, draws=draws, target_bp=TARGET_BP, stop_bp=STOP_BP,
               rules=out_rules, refusals=refusals, gate=gate, U4=U4, deployed=dep, baseline_under_H1_hedge=h1_hedge,
               predictions=score_predictions(out_rules, gate, U4, holds0, pnl0, cut), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out)))          # [P] PERSIST BEFORE RENDERING
    print(f"  wrote {paths['report']}")
    print_report(out)
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def score_predictions(R, gate, U4, holds0, pnl0, cut):
    e1 = R.get("E1")
    return {
        "Q1": dict(claim="AGAINST my own proposal: U1 FAILS -- E1 does not beat a random cut of the same trades",
                   verdict=(e1 or {}).get("U1", {}).get("verdict"),
                   held=bool(e1 and e1["U1"]["verdict"] != "PASS")),
        "Q2": dict(claim="E1's mean holding run is under 25 bars -- a real overlay, not a rule that never fires",
                   value=(e1 or {}).get("hold_mean"), held=bool(e1 and e1["hold_mean"] < 25.0)),
        "Q3": dict(claim="E1 beats the LOOSE control while failing the STRICT one -- it picks trades, not bars",
                   held=bool(e1 and e1["U3"]["vs_loose"]["verdict"] == "PASS" and e1["U1"]["verdict"] != "PASS")),
        "Q4": dict(claim="E1's mean per trade falls below E0's +160.55 while its bp per bar rises above +4.02",
                   mean_bp=(e1 or {}).get("mean_bp"), bp_per_bar=(e1 or {}).get("bp_per_bar"),
                   held=bool(e1 and e1["mean_bp"] < float(pnl0.mean()) and e1["bp_per_bar"] > float(pnl0.mean() / holds0.mean()))),
        "Q5": dict(claim="the trigger fires on more than half of trades",
                   value=(e1 or {}).get("fired_share"), held=bool(e1 and e1["fired_share"] > 0.50)),
        "Q6": dict(claim="E2 and E3 both fail their own controls",
                   held=bool(all(gate.get(k) != "PASS" for k in ("E2", "E3")))),
        "Q7": dict(claim="[CUT]'s max deviation is below 1e-12 -- same addends, same order, unlike D377's [REC]",
                   value=cut["max_abs_dev"], held=bool(cut["max_abs_dev"] < 1e-12)),
    }


def print_report(out):
    b = out["baseline"]
    print(f"\n  {out['cell']}  baseline {b['trades']:,} trades  mean {b['mean_bp']:+.2f}  hold {b['hold_mean']:.1f}  "
          f"bp/bar {b['bp_per_bar']:.2f}")
    i = out["inv"]
    print(f"  [CUT] baseline {out['cut']['max_abs_dev']:.3e}   [INV] {i['mismatches']} mismatches on {i['shared']:,} shared entries")
    print("  UNCONTROLLED OBSERVATION (amendment 571b9d3): the kernel's invalidation BOOK is a different construction --")
    print(f"      {i['kernel_book_trades']:,} trades vs the baseline's {i['baseline_trades']:,}, mean hold "
          f"{i['kernel_book_hold_mean']:.2f}, mean per trade {i['kernel_book_mean_bp']:+.2f}. NO CONTROL, NO VERDICT.")
    print(f"\n  {'rule':<4} {'what it is':<32} {'fires':>7} {'hold':>6} {'mean':>9} {'bp/bar':>8} "
          f"{'strict p95':>11} {'U1':<11} {'U2':<11} GATE")
    for k, v in out["rules"].items():
        print(f"  {k:<4} {v['name']:<32} {v['fired_share']:>6.1%} {v['hold_mean']:>6.1f} {v['mean_bp']:>+9.2f} "
              f"{v['bp_per_bar']:>8.2f} {v['U1']['p95']:>+11.2f} {v['U1']['verdict']:<11} {v['U2']['verdict']:<11} {out['gate'][k]}")
    for k, r in out["refusals"].items():
        print(f"  {k}  {r}")
    print("\n  U3  where the gain lives")
    for k, v in out["rules"].items():
        m, l = v["U3"]["median"], v["U3"]["vs_loose"]
        print(f"    {k}  median {m['observed']:+8.2f} vs p95 {m['p95']:+8.2f} -> {m['verdict']:<11} | "
              f"vs LOOSE control p95 {l['p95']:+8.2f} -> {l['verdict']}")
    u = out["U4"]["E1"]
    print(f"\n  U4  what E1 keys on: trigger fired {u['trigger_fired']:,}, cap bound {u['cap_bound']:,}, "
          f"natural end {u['natural_end']:,}")
    print(f"      hold histogram {u['hold_hist']}")
    d = out["deployed"]
    for k in ("E0", "invalidation_book_UNCONTROLLED"):
        pb = d[k]["PB"]["hedged"]
        print(f"  {k} deployed (genuine kernel run): gross {pb['gross_bp']:+.3f} bp/bar  net PB {pb['net_bp']:+.3f}  "
              f"turnover {pb['turnover']:.4f}  held {pb['held_per_bar']:.1f}")
    print("\n  PREDICTIONS")
    for k, v in out["predictions"].items():
        print(f"    {k}  {'HELD' if v['held'] else 'FALSIFIED'}   {v['claim']}")


# ------------------------------------------------------------------ [X]
def stage_selftest(P):
    print("\nSELFTEST")
    t0 = time.time()
    res0 = baseline(P)
    pnl0 = np.asarray(V47.pnl_bp(res0), float)
    C, holds0 = trade_paths(P, res0)
    print("  [MIR] the baseline reproduces D373's committed ledger")
    mir = assert_MIR(P, res0)
    print(f"       {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}")
    print("  [CUT] the re-cut reproduces the kernel's own per-trade P&L")
    cut = assert_CUT(C, holds0, pnl0)
    print(f"       max |dev| {cut['max_abs_dev']:.3e}, tol {CUT_TOL:.0e}")
    RH = rule_holds(P, res0, C, holds0)
    print("  [OVL] every rule shortens, never lengthens")
    for k in RULES:
        n = assert_OVL(RH[k], holds0, k)
        print(f"       {k} shortens {n:,} of {holds0.size:,} ({n / holds0.size:.1%}), hold {RH[k].mean():.1f} vs {holds0.mean():.1f}")
    print("  [DIR] the HIGH tail")
    print(f"       {assert_DIR(pnl0)}")

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

    must_raise("mir_truncated", lambda: assert_MIR(P, {**res0, "trades": res0["trades"][:10]}))
    # NOT bad[0, 0]: C is a stored CUMULATIVE SUM, so perturbing an early entry leaves the endpoint [CUT] reads untouched and the
    # break is a no-op. [X] caught that -- the second time this session a deliberate break of mine could not fire (D376's was a
    # rescale against a scale-invariant correlation). Perturb the endpoint the assertion actually reads.
    bad = C.copy()
    bad[0, holds0[0] - 1] += 1.0
    must_raise("cut_perturbed_endpoint", lambda: assert_CUT(bad, holds0, pnl0))
    shifted = C.copy()
    shifted[:, :] += 1e-6
    must_raise("cut_shifted_paths", lambda: assert_CUT(shifted, holds0, pnl0))
    must_raise("ovl_rule_that_lengthens", lambda: assert_OVL(holds0 + 1, holds0, "toy"))
    must_raise("ovl_changed_trade_count", lambda: assert_OVL(holds0[:10], holds0, "toy"))
    sel = np.flatnonzero(RH["E1"] < holds0)
    other = np.setdiff1d(np.flatnonzero(holds0 > 1), sel)[:sel.size]
    must_raise("r7_control_cut_a_different_set",
               lambda: assert_R7(other, holds0.copy(), sel, holds0, "toy"))
    hbad = holds0.copy()
    hbad[sel] = holds0[sel]                                     # a "cut" that does not actually shorten
    must_raise("r7_cut_outside_the_window", lambda: assert_R7(sel, hbad, sel, holds0, "toy"))
    for k, v in broken.items():
        print(f"       {k}: {v}")

    print("\n  [FIRE] the guard refuses a rule that barely fires")
    r = assert_FIRE(5, 3932, "toy")
    assert r and "REFUSED" in r, "[FIRE] a 0.1% rule was not refused"
    print(f"       {r}")
    assert assert_FIRE(2000, 3932, "toy") is None, "[FIRE] a 51% rule was wrongly refused"
    print(f"\n  selftest OK ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D380  does the exit rule beat a RANDOM CUT of the same trades? R7's control")
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
