"""D393 STAGE 0 -- is a sign statistic a new input, or trailing return with the magnitude removed?

    uv run python scripts/run_d393_sign_sequences.py --selftest
    uv run python scripts/run_d393_sign_sequences.py --stage0

Pre-registration: docs/decisions/D393-the-sign-sequence-family.md (committed BEFORE this file, R8).

DESCRIPTIVE. Stage 0 scores no book and admits nothing (R15). It answers K1/K2/K3 from the
pre-registration's section 2, and reports the exposure arithmetic and the atlas floor beside them.

**K1 IS EXPECTED TO FIRE.** Q1 is declared against the candidate: fifteen up days out of
twenty-one is mechanically a positive trailing return, so the claim that magnitude-free buys
independence is exactly what K1 measures. If it fires the record stops here.

THE SCORES ARE COMPUTED IN-PROCESS AND THE CACHE IS NOT TOUCHED, and that is a deliberate choice
with a cost. `run_d350_long_timing_screen.py:97-102` asserts its pool is exactly 46 names AND
set-equal to the npz's members; adding a family to `temp/d290_scores.npz` makes that raise for
D350 and D352, whose 46-name pool and 138-member count are load-bearing in two published records.
The write would also cost 2.7 GB, invalidate `d348_prep`'s cache through `cache_key`, and -- with
`temp/d290_chunk_*.npz` absent from this worktree -- trigger the full C/D/G/H fan.

**So this is a PROBE, not a repeatable artifact.** The grids live only in this process. If Stage 0
clears, promoting the family into the cache properly (new `AXES["I"]`, `"ABCDEFGH"` -> `"...I"` in
two places, the `cache_key` file tuple, a D371-style merge-rewrite) is its own piece of work.

ASSERTIONS
  [T]  the scores are causal -- `ragged_sign_scores`' truncation audit re-run HERE rather than
       trusted from the module's own self-test.
  [L]  from `scripts/lag_audit.py`, with `raises_on_broken` on a deliberately unlagged input.
       D391 listed this requirement and did not implement it.
  [E]  every event sits on an eligible bar (D351).
  [C]  the cache is untouched: `temp/d290_scores.npz` size and mtime unchanged across the run.
  [P]  the JSON is persisted BEFORE it is rendered (D371; D391 reproduced that defect).
  [X]  the self-test RAISES on a flipped direction and on an unlagged mask.
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
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "d393_stage0.json"
NPZ = REPO / "temp" / "d290_scores.npz"
ATLAS = REPO / "data" / "d392_atlas.json"

SIGN = ("up_run_21", "sign_flips_21", "up_frac_21")
K1_REF = ("rev_5", "rev_21", "trailing_return", "mom_252_21")
K2_REF = ("rvol21", "atr_norm")
K_RHO = 0.50
K3_MIN_EFF = 2.0
MIN_NAMES = 50
CAPS = (5, 10, 20, 40, 60)
PRIMARY_CAP = 20
POOL = "ALL"                    # declared in the pre-registration section 3, before any number


def rank01(v):
    return np.argsort(np.argsort(v)) / (len(v) - 1) if len(v) > 1 else np.zeros_like(v, float)


def effective_inputs(Rm):
    lam = np.maximum(np.linalg.eigvalsh(Rm), 0.0)
    M = Rm.shape[0]
    return dict(participation_ratio=float(lam.sum() ** 2 / (lam ** 2).sum()),
                li_ji=float(np.sum((lam >= 1.0) + (lam - np.floor(lam)))),
                cheverud_nyholt=float(1.0 + (M - 1) * (1.0 - np.var(lam) / M)))


PROBE_OUT = REPO / "data" / "d393_probe.json"
SURVIVORS = ("up_run_21", "sign_flips_21")      # cleared K1 on 2026-09-08; the principal's ruling
REFERENCE = "up_frac_21"                        # K1 killed it; carried as a POSITIVE CONTROL only

# An axis counts as TILTED when its dominant tercile holds more than this share of the events
# (uniform is 1/3). Set here, before any number was seen, so "which floor is operative" is a rule
# and not a choice made after looking. 0.45 is one third plus a third of a third.
TILT_SHARE = 0.45


# ---------------------------------------------------------------------- the probe
def probe(LA) -> int:
    """ONE CELL, in money: E1, cap 20, long, the declared direction. NOT Stage 1.

    WHAT THIS IS. Stage 0 read no forward returns. Before spending ~2.5 hours of nulls (section 4's
    7,000 draws over a 10-cell best-of floor) on a score with no measured edge, this asks the cheap
    question: does the cell the pre-registration ALREADY declared primary earn anything gross, and
    how does that sit against the D392 atlas floor?

    WHY THIS IS NOT CELL-PICKING. Section 3 froze `PRIMARY_CAP = 20` and E1 before the runner
    existed, and section 3's atlas pool was declared there too. Nothing here is chosen after
    looking. What IS true, and is recorded rather than hidden: seeing this number before the other
    nine cells means the full grid, if it is ever run, is no longer being read blind.

    THE POOL QUESTION, which section 3 anticipated. It declared pool ALL, `if Stage 0's
    correlations say otherwise the conditional pool is used instead and the record says the pool
    changed and why`. K1 put `up_run_21` at rho +0.370 to `rev_21`, so its floor may be a momentum
    floor rather than the unconditional one. This does not guess: it MEASURES where the events sit
    on the three tercile axes the atlas conditions on, and reports every floor that applies.

    THE DIRECTION DEFECT, found here and reported rather than worked around. Section 1 declared one
    mechanism for all three scores -- `a low value is a name under sustained one-sided selling`.
    That is true of `up_run_21` and `up_frac_21`. **It is false of `sign_flips_21`**, which is
    blind to direction by construction: a low flip count is a name that TRENDED, up or down. So E1
    on it does not isolate sustained selling, and the diagnostic split by trailing-return sign is
    reported beside it -- as a diagnostic, never as a candidate cell."""
    t0 = time.time()
    npz_before = (NPZ.stat().st_size, int(NPZ.stat().st_mtime)) if NPZ.exists() else None
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    ATL = _load("d392a", "run_d392_base_rate_atlas.py")
    P = PREP.prep(need_grids=True)
    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    live = panel.live
    T, n = P["T"], P["n"]
    elig = np.asarray(P["elig"])
    print(f"  prep in {time.time() - t0:.0f}s | {n} names x {T} bars", flush=True)

    raw = SG.sign_scores(g, live)
    print(f"    sign scores built in-process ({time.time() - t0:.0f}s); the cache is not touched",
          flush=True)

    def lagged_from(arr):
        """`run_d350.lagged` with the array passed in -- identical to the Stage 0 path."""
        sc = np.where(P["excl"], np.nan, arr)
        sc = PREP.UF.apply_floor_replace(sc, P["keep"])
        sc = np.where(P["base"], sc, np.nan)
        out = np.full((T, n), np.nan)
        out[1:] = sc[:, :-1].T
        return out, sc

    cols, proc = {}, {}
    for k in SIGN:
        cols[k], proc[k] = lagged_from(raw[k])
    rev21, _ = lagged_from(np.asarray(P["score"]("rev_21")))

    # ---- [L] the lag, in a SECOND implementation that never calls percentile_grid ----------
    #      Two separate claims, because they can fail separately:
    #        L1  the grid the mask is built from carries NO bar-t information
    #        L2  the percentile the decile test reads agrees with direct counting
    rng = np.random.default_rng(393)
    for k in SIGN:
        assert np.isnan(cols[k][0]).all(), f"[L1] {k} row 0 is not empty"
        assert np.array_equal(cols[k][1:], proc[k][:, :-1].T, equal_nan=True), \
            f"[L1] {k} column t is not the processed score at t-1"
    # the negative control: hand the SAME grid in as its own unshifted source, which is what a
    # missing lag looks like, and require the check to raise
    LA.raises_on_broken(_assert_no_bar_t, cols["up_run_21"], cols["up_run_21"])
    print(f"    [L1] all three grids are the processed score at t-1, row 0 empty; and the check "
          f"RAISES on an unshifted grid", flush=True)

    pct = {k: PREP.V47.percentile_grid(cols[k]) for k in SIGN}
    masks = {k: V50.shape_masks(pct[k], elig)["E1"][0] for k in SIGN}
    checked = 0
    for k in SIGN:
        ts, iis = LA.sample_events(masks[k], 400, rng)
        for t, i in zip(ts, iis):
            assert LA.pct_direct(cols[k][t], i) <= V50.DECILE + 1e-9, f"[L2] {k} event not in decile"
            assert elig[t, i], f"[E] {k} event on an ineligible bar"
            checked += 1
    print(f"    [L2] {checked:,} sampled events re-derived by DIRECT COUNTING from the lagged "
          f"column, and every one sits on an eligible bar [E]", flush=True)

    # ---- where the events actually sit, on the atlas's own three axes ----------------------
    tp = time.time()
    pools = ATL.tercile_pools(P, elig)
    print(f"    tercile pools built in {time.time() - tp:.0f}s (the atlas's OWN construction, so "
          f"the comparison is like-for-like)", flush=True)
    placement = {}
    for k in SIGN:
        m_ = masks[k]
        tot = int(m_.sum())
        placement[k] = {ax: {b: float((m_ & pools[f"{ax}_{b}"]).sum()) / max(1, tot)
                             for b in ("lo", "mid", "hi")} for ax in ("price", "vol", "mom")}

    # ---- the cell, in money ----------------------------------------------------------------
    atlas = json.loads(ATLAS.read_text())
    out = {}
    for k in SIGN:
        m_ = masks[k]
        sc = np.where(np.isfinite(cols[k]), cols[k], 50.0)
        res = V59.run_mirror(P, m_, sc, "cap", PRIMARY_CAP)
        # [SC] with exit="cap" and n_max=None the score is inert; a constant must give the same ledger
        res2 = V59.run_mirror(P, m_, np.full((T, n), 17.0), "cap", PRIMARY_CAP)
        assert len(res["trades"]) == len(res2["trades"]), f"[SC] the score moved {k}'s cap ledger"
        pnl = PREP.V47.pnl_bp(res)
        trd = V59.trade_block(P, res, elig, 0, True)
        dep = V59.deployed_block(res, P)
        tr = res["trades"]
        j = int(np.argmax(pnl))
        top = dict(symbol=P["symbols"][tr[j][0]], entry_bar=int(tr[j][1]),
                   entry_date=str(P["dates"][tr[j][1]]), held=int(tr[j][2]),
                   pnl_bp=float(pnl[j]),
                   share_of_total=float(pnl[j] / pnl.sum()) if pnl.sum() != 0 else None)

        floors = {"ALL": _floor(ATL, atlas, len(tr), "ALL")}
        tilted = []
        for ax in ("price", "vol", "mom"):
            b = max(placement[k][ax], key=placement[k][ax].get)
            if placement[k][ax][b] > TILT_SHARE:
                tilted.append(f"{ax}_{b}")
                floors[f"{ax}_{b}"] = _floor(ATL, atlas, len(tr), f"{ax}_{b}")
        ok = [v["p95"] for v in floors.values() if "p95" in v]
        operative = max(ok) if ok else None

        out[k] = dict(role=("candidate" if k in SURVIVORS else "REFERENCE ONLY -- K1 killed it"),
                      events=int(m_.sum()), trades=len(tr), groups=group_stats_local(pnl),
                      per_trade=trd, deployed=dep, top_trade=top, placement=placement[k],
                      floors=floors, tilted_axes=tilted, operative_floor=operative,
                      margin=(float(pnl.mean()) - operative) if operative is not None else None)
        print(f"    {k:<14s} {len(tr):>7,} trades, gross {pnl.mean():+8.2f} bp/trade "
              f"({time.time() - t0:.0f}s)", flush=True)

    # ---- the direction diagnostic sign_flips_21 needs and the other two do not -------------
    k = "sign_flips_21"
    m_ = masks[k]
    with np.errstate(invalid="ignore"):
        dn = m_ & (rev21 < 0)
        up = m_ & (rev21 > 0)
    diag = {}
    for nm, mm in (("trailing_down", dn), ("trailing_up", up)):
        r_ = V59.run_mirror(P, mm, np.where(np.isfinite(cols[k]), cols[k], 50.0), "cap", PRIMARY_CAP)
        p_ = PREP.V47.pnl_bp(r_)
        diag[nm] = dict(trades=len(r_["trades"]), mean_bp=float(p_.mean()),
                        median_bp=float(np.median(p_)))

    npz_after = (NPZ.stat().st_size, int(NPZ.stat().st_mtime)) if NPZ.exists() else None
    assert npz_before == npz_after, f"[C] the score cache CHANGED: {npz_before} -> {npz_after}"

    payload = dict(
        study=393, stage="probe", cap=PRIMARY_CAP, shape="E1", side="long",
        purpose="D393 cheap single-cell probe: the pre-registered PRIMARY cell in money, against "
                "the D392 atlas floor. NOT Stage 1: no null was run. Admits nothing (R15).",
        prereg="docs/decisions/D393-the-sign-sequence-family.md",
        ruling="Per-score reading of the split K1, given by the principal 2026-09-08: up_frac_21 "
               "is dropped as a candidate and carried as a positive control only.",
        tilt_share_rule=TILT_SHARE, survivors=list(SURVIVORS), reference=REFERENCE,
        cells=out, sign_flips_direction_diagnostic=diag,
        caveat="Seeing this cell before the other nine means the full 10-cell grid is no longer "
               "being read blind, and any later Stage 1 must say so.")
    PROBE_OUT.write_text(json.dumps(_clean(payload), indent=1))
    print(f"\n  [P] wrote {PROBE_OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    _render(out, diag)
    print(f"\n  ({time.time() - t0:.0f}s)  NO NULL WAS RUN. This is not Stage 1 and admits nothing.")
    return 0


def _assert_no_bar_t(col, unshifted):
    """The negative control for [L1]: an UNSHIFTED grid must fail the same test the real one passes."""
    assert np.isnan(col[0]).all() and not np.array_equal(col, unshifted, equal_nan=True), \
        "[L1] the grid carries bar-t information"


def _floor(ATL, atlas, n_trades, pool):
    try:
        return ATL.lookup(atlas, n_trades, PRIMARY_CAP, "long", pool)
    except (ValueError, KeyError) as e:
        return {"error": str(e)[:90]}


def group_stats_local(pnl):
    p = np.asarray(pnl, float)
    lo, hi = np.percentile(p, 1), np.percentile(p, 99)
    return dict(n=int(p.size), mean_bp=float(p.mean()), median_bp=float(np.median(p)),
                win_rate=float((p > 0).mean()),
                t=float(p.mean() / (p.std(ddof=1) / np.sqrt(p.size))) if p.size > 1 else None,
                trim_ex_top_bp=float(p[p <= hi].mean()), trim_ex_bottom_bp=float(p[p >= lo].mean()),
                trim_both_bp=float(p[(p >= lo) & (p <= hi)].mean()))


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def _render(out, diag):
    print(f"\nTHE PRE-REGISTERED PRIMARY CELL IN MONEY -- E1, cap {PRIMARY_CAP}, LONG, "
          f"every event taken\n")
    for k, d in out.items():
        g = d["groups"]
        t_ = d["per_trade"]
        print(f"  {k}   [{d['role']}]")
        print(f"      {d['trades']:,} trades from {d['events']:,} events | "
              f"GROSS {g['mean_bp']:+.2f} bp/trade, median {g['median_bp']:+.2f}, "
              f"win {100 * g['win_rate']:.1f}%, t {g['t']:+.2f}")
        print(f"      trim: ex-top {g['trim_ex_top_bp']:+.2f} | ex-bottom "
              f"{g['trim_ex_bottom_bp']:+.2f} | BOTH {g['trim_both_bp']:+.2f}")
        rt = t_["two_c"]["PUB"]
        print(f"      round trip (PUB, MEASURED Corwin-Schultz) {rt:.2f} bp -> "
              f"NET {t_['net_per_trade']['PUB']:+.2f}, gross/2c {t_['mean_over_2c']['PUB']:.2f}x, "
              f"breakeven half-spread {t_['breakeven_half_spread_bp_side']:+.2f} bp/side")
        print(f"      hold {t_['hold_mean']:.1f} bars, held price ${t_['held_price']:.2f}, "
              f"era1 {t_['era1_mean_bp']:+.1f} / era2 {t_['era2_mean_bp']:+.1f}")
        print(f"      TOP TRADE: {d['top_trade']['symbol']} entered {d['top_trade']['entry_date']} "
              f"(bar {d['top_trade']['entry_bar']}), held {d['top_trade']['held']}, "
              f"{d['top_trade']['pnl_bp']:+,.0f} bp = "
              f"{100 * (d['top_trade']['share_of_total'] or 0):.2f}% of the ledger")
        pl = d["placement"]
        print("      where the events sit: " + " | ".join(
            f"{ax} " + "/".join(f"{100 * pl[ax][b]:.0f}" for b in ("lo", "mid", "hi"))
            for ax in ("price", "vol", "mom")) + "   (lo/mid/hi %, uniform = 33/33/33)")
        fl = " ".join(f"{p} {v['p95']:+.2f}+/-{v['se_p95']:.2f}" if "p95" in v else f"{p} n/a"
                      for p, v in d["floors"].items())
        print(f"      atlas floors: {fl}")
        if d["operative_floor"] is not None:
            verdict = "ABOVE" if d["margin"] > 0 else "BELOW"
            print(f"      OPERATIVE FLOOR {d['operative_floor']:+.2f} "
                  f"(tilted axes: {d['tilted_axes'] or 'none'}) -> margin "
                  f"{d['margin']:+.2f} bp, {verdict}")
        print()
    print("SIGN_FLIPS_21 DIRECTION DIAGNOSTIC -- not a candidate cell, and not pre-registered.\n"
          "  A low flip count is a name that TRENDED; the score cannot say which way, so section\n"
          "  1's 'sustained one-sided selling' does not describe this score's E1 set.\n")
    for nm, d in diag.items():
        print(f"      {nm:<14s} {d['trades']:>7,} trades, mean {d['mean_bp']:+8.2f} bp, "
              f"median {d['median_bp']:+8.2f}")


# ---------------------------------------------------------------------- self-test
def selftest(LA) -> int:
    print("D393 STAGE 0 SELF-TEST -- the direction, the lag, and two breaks that must be caught\n")
    T, N = 60, 30
    rng = np.random.default_rng(393)

    # the declared direction: LONG on the LOW end of the sign statistic
    p = rng.uniform(0, 100, size=(T, N))
    prev = np.full_like(p, np.nan)
    prev[1:] = p[:-1]
    with np.errstate(invalid="ignore"):
        e1 = (p <= 10.0) & (prev > 10.0)
    lo_end = e1.sum()
    with np.errstate(invalid="ignore"):
        wrong = (p >= 90.0) & (prev < 90.0)
    assert lo_end > 0 and wrong.sum() > 0
    print(f"    E1 on the LOW end fires {lo_end} times; the high-end mirror {wrong.sum()} "
          f"-- the declared long is the low end")

    raised = False
    try:
        assert np.array_equal(e1, wrong), "the declared direction must not equal its mirror"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- the flipped direction passed"
    print("    [X] the direction flipped IS CAUGHT")

    pos = LA.lag1_mask(e1)
    LA.assert_mask_is_lagged(pos, e1)
    LA.raises_on_broken(LA.assert_mask_is_lagged, e1, e1)
    print("    [L] positions open one bar after the signal, and handing the RAW mask over "
          "IS CAUGHT (D391's defect)")
    print("\nSELF-TEST PASSED\n")
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--probe", action="store_true",
                    help="the pre-registered PRIMARY cell in money; no null, not stage 1")
    a = ap.parse_args()
    LA = _load("lag_audit", "lag_audit.py")
    if a.selftest:
        return selftest(LA)
    if a.probe:
        selftest(LA)
        return probe(LA)
    if not a.stage0:
        ap.error("pass --stage0 or --probe (stage 1 is not authorised; K1 may stop the record)")
    selftest(LA)

    t0 = time.time()
    npz_before = (NPZ.stat().st_size, int(NPZ.stat().st_mtime)) if NPZ.exists() else None
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    P = PREP.prep(need_grids=True)
    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    live = panel.live
    T, N = P["T"], P["n"]
    elig = np.asarray(P["elig"])
    print(f"  prep in {time.time() - t0:.0f}s | {N} names x {T} bars", flush=True)

    # ---- the scores, in-process ------------------------------------------
    t1 = time.time()
    raw = SG.sign_scores(g, live)
    print(f"    sign scores built in {time.time() - t1:.0f}s (IN-PROCESS; the cache is not "
          f"touched)", flush=True)

    # ---- [T] causal, re-checked here rather than trusted -----------------
    T0 = int(T * 0.7)

    def build(cut):
        if cut is None:
            return raw
        gg = {k: v[:, :cut] for k, v in g.items()}
        return SG.sign_scores(gg, live[:, :cut])

    bad = SG.V.truncation_audit(build, live, T0, SIGN, "I")
    assert bad == 0, f"[T] {bad} sign score(s) read the future"
    print(f"    [T] all three scores causal at the truncation audit (column {T0})", flush=True)

    # ---- the comparison grids, through the SAME pipeline ------------------
    def lagged_from(arr):
        """`run_d350.lagged` with the array passed in instead of a cache name -- floored,
        deal-filtered, warm-based, then shifted one bar. Four lines, and the only npz-dependent
        input was the raw grid."""
        sc = np.where(P["excl"], np.nan, arr)
        sc = PREP.UF.apply_floor_replace(sc, P["keep"])
        sc = np.where(P["base"], sc, np.nan)
        out = np.full((T, N), np.nan)
        out[1:] = sc[:, :-1].T
        return out

    cols = {}
    for k in SIGN:
        cols[k] = lagged_from(raw[k])
    for k in K1_REF + K2_REF:
        cols[k] = lagged_from(np.asarray(P["score"](k)))
    names = list(SIGN) + list(K1_REF) + list(K2_REF)
    print(f"    comparison grids built through run_d350.lagged's pipeline "
          f"({len(names)} scores)", flush=True)

    # ---- K1 / K2 / K3: the within-bar correlation, the operative lens -----
    m = len(names)
    acc = np.zeros((m, m))
    bars = 0
    for t in range(T):
        ok = elig[t].copy()
        for k in names:
            ok = ok & np.isfinite(cols[k][t])
        if ok.sum() < MIN_NAMES:
            continue
        X = np.vstack([rank01(cols[k][t][ok]) for k in names])
        R = np.corrcoef(X)
        if np.isfinite(R).all():
            acc += R
            bars += 1
    assert bars > 0, "no bar carried enough eligible names with every score finite"
    Rm = acc / bars
    idx = {k: i for i, k in enumerate(names)}
    rho = lambda a_, b_: float(Rm[idx[a_], idx[b_]])                     # noqa: E731

    k1 = [{"sign": s, "ref": r, "rho": rho(s, r)} for s in SIGN for r in K1_REF
          if abs(rho(s, r)) > K_RHO]
    k2 = [{"sign": s, "ref": r, "rho": rho(s, r)} for s in SIGN for r in K2_REF
          if abs(rho(s, r)) > K_RHO]
    sub = Rm[np.ix_([idx[s] for s in SIGN], [idx[s] for s in SIGN])]
    eff = effective_inputs(sub)
    k3_fail = eff["participation_ratio"] < K3_MIN_EFF

    # ---- the exposure arithmetic, computed before it is predicted --------
    p_sign = {}
    for s in SIGN:
        p_sign[s] = PREP.V47.percentile_grid(cols[s])
    ev = {}
    for s in SIGN:
        p = p_sign[s]
        prev = np.full_like(p, np.nan)
        prev[1:] = p[:-1]
        with np.errstate(invalid="ignore"):
            e1 = (p <= 10.0) & (prev > 10.0) & elig
        ev[s] = int(e1.sum())
    bars_def = int(elig.any(axis=1).sum())

    # ---- the atlas floor for the DECLARED pool ---------------------------
    atlas = json.loads(ATLAS.read_text())
    ATL = _load("d392a", "run_d392_base_rate_atlas.py")
    floors = {}
    for s in SIGN:
        approx_trades = ev[s]           # cap 20 collapses this; reported as the EVENT count
        try:
            floors[s] = ATL.lookup(atlas, approx_trades, PRIMARY_CAP, "long", POOL)
        except (ValueError, KeyError) as e:
            floors[s] = {"error": str(e)}

    # ---- [C] the cache is untouched --------------------------------------
    npz_after = (NPZ.stat().st_size, int(NPZ.stat().st_mtime)) if NPZ.exists() else None
    assert npz_before == npz_after, f"[C] the score cache CHANGED: {npz_before} -> {npz_after}"
    print(f"    [C] temp/d290_scores.npz unchanged ({npz_after[0] / 1e9:.2f} GB)", flush=True)

    verdict = ("K1 FIRES -- a sign statistic is trailing return with the magnitude removed"
               if k1 else "K2 FIRES -- a volatility proxy" if k2 else
               "SIGN STATISTICS CLEAR K1 AND K2 -- a new input on this universe")

    payload = dict(
        study=393, stage=0, purpose="D393 Stage 0: K1/K2/K3 on the sign-sequence family. "
                                    "Descriptive; scores nothing, admits nothing (R15).",
        prereg="docs/decisions/D393-the-sign-sequence-family.md",
        note="Scores computed IN-PROCESS; temp/d290_scores.npz deliberately not written, because "
             "run_d350.load_pool asserts a 46-name pool set-equal to the npz members and two "
             "published records depend on it. This is a probe, not a repeatable artifact.",
        bars=bars, names=names, spearman_within_bar=Rm.tolist(),
        K_RHO=K_RHO, K1_violations=k1, K2_violations=k2,
        effective_inputs_sign_only=eff, K3_fails=bool(k3_fail),
        events_E1=ev, bars_defined=bars_def,
        exposure_arithmetic={s: {str(c): ev[s] / max(1, bars_def) * c for c in CAPS} for s in SIGN},
        atlas_pool=POOL, atlas_floor=floors, verdict=verdict)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render ------------------------------------------------------------
    print(f"\nWITHIN-BAR SPEARMAN, mean over {bars:,} bars (the operative lens)\n")
    print("            " + " ".join(f"{k[:11]:>12s}" for k in names))
    for i, k in enumerate(names):
        print(f"{k[:11]:>11s} " + " ".join(f"{Rm[i, j]:12.3f}" for j in range(m)))

    print(f"\nK1  trailing-return proxy? (|rho| > {K_RHO} vs {', '.join(K1_REF)})\n")
    for s in SIGN:
        print(f"      {s:<14s} " + "  ".join(f"{r} {rho(s, r):+.3f}" for r in K1_REF))
    print(f"    -> {'FIRES' if k1 else 'CLEARS'}")
    print(f"\nK2  volatility proxy? (|rho| > {K_RHO} vs {', '.join(K2_REF)})\n")
    for s in SIGN:
        print(f"      {s:<14s} " + "  ".join(f"{r} {rho(s, r):+.3f}" for r in K2_REF))
    print(f"    -> {'FIRES' if k2 else 'CLEARS'}")
    print(f"\nK3  effective inputs among the three (bar {K3_MIN_EFF}): "
          f"participation ratio {eff['participation_ratio']:.2f}, Li-Ji {eff['li_ji']:.2f}")
    print(f"    -> {'FAILS' if k3_fail else 'CLEARS'}")

    print(f"\nEXPOSURE ARITHMETIC (section 38 rule 2), E1 events over {bars_def:,} bars\n")
    for s in SIGN:
        print(f"      {s:<14s} {ev[s]:>8,} events = {ev[s] / max(1, bars_def):6.2f}/bar "
              f"-> {ev[s] / max(1, bars_def) * PRIMARY_CAP:8.1f} open at cap {PRIMARY_CAP}")

    print(f"\nATLAS FLOOR, pool {POOL} declared in advance (cap {PRIMARY_CAP}, long)\n")
    for s in SIGN:
        f = floors[s]
        print(f"      {s:<14s} " + (f"p95 {f['p95']:+.2f} +/- {f['se_p95']:.2f}"
                                    if "p95" in f else f"-- {f['error'][:64]}"))

    print(f"\nVERDICT: {verdict}")
    print(f"\n  ({time.time() - t0:.0f}s)  No null was run. Stage 1 is not authorised by this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
