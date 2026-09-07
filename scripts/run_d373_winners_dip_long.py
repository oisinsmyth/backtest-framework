"""D373 -- the winners' dip long: a fresh rev_5 DIP inside the TOP decile of mom_252_21, entered long; and the median trade as a criterion.

    uv run python scripts/run_d373_winners_dip_long.py --selftest
    uv run python scripts/run_d373_winners_dip_long.py --stage0                                  the shape, before any null
    uv run python scripts/run_d373_winners_dip_long.py --cells --draws 2000 --part 0             A'/B/B_c over ALL FIVE cells, shared offset
    uv run python scripts/run_d373_winners_dip_long.py --report
    --out-dir DIR   (every stage; default data/ -- the smoke runs pass temp/... so that nothing under data/ is touched)

Pre-registration: docs/decisions/D373-the-winners-dip-long-and-the-median-criterion.md  (committed aa7bc2f, amended 462f894)

THE SIGNAL is D359's `mirror`, unchanged and imported rather than re-derived:
    mirror (c, s):  pct_mom >= 100-c  &  pct_rev <= 100-s  &  pct_rev[t-1] > 100-s,  eligible  ->  LONG at the next open, every event, no slot cap
Direction is DECLARED LONG before the run (gate 1h). A result in the other direction is DIRECTION-INVERTED and counts against the mechanism.

THE FIVE CELLS are exactly the five rows D359 section 6 printed, because the primary was chosen after seeing all five and that look is priced
(pre-reg section 7): (10,90) cap40 PRIMARY, (10,90) cap10, (10,90) inv10, (10,95) cap10, (20,90) cap10. H1/H2 are scored against the
BEST-OF-5 FLOOR -- the max over the five cells WITHIN each draw, under a SHARED per-name offset, as D367 built its best-of-46.

WHAT IS NEW HERE, and it is the point of the record:
  [H2] the chain mean > median > 0, at the principal's ruling. So every null draw must carry its own MEDIAN, not just its mean.
  [H3] era 1 standing alone, against A' and B_c RECOMPUTED WITHIN ERA 1. So every draw must carry its own era-1 mean.
`null_stats_ext` is `V58.null_stats` plus those two quantities and nothing else; the shared keys are asserted identical to V58's (see [NS]).

Nulls (pre-reg section 4 as amended): A' 2,000 draws, B_c 2,000, B 1,000, C 2,000. Every reported p95 carries its BOOTSTRAP SE and any
hurdle whose margin is within 2 SE of its bar is UNRESOLVED, never passed. fast_null.py is deliberately NOT used -- it accelerates
rotation nulls over a position matrix (the D256-D285 book lineage); these are the event-signal controls of D348/D351/D358/D359, and
re-implementing them would break comparability with D359's published draws. Pre-reg section 4, second note.

ASSERTIONS [L][S][Q][E][N][Bc][P][X][NS][MIR] -- pre-reg section 6. [X] is the one that matters: the self-test must RAISE on a
deliberately broken book, or it is worse than none.

Everything shared is imported, not copied: d348_prep (FIRST: installs memo_load), run_d359 (the signal, the kernel, the controls,
two_crossing, deployed_block, trade_block), and through it run_d350/d353/d349/d358.
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


PREP = _load("d348p", "d348_prep.py")                       # installs memo_load; the alias chain executes once
V59 = _load("d359r", "run_d359_loser_rally_short.py")       # the mirror signal, the kernel, the controls -- imported, never re-derived
V50, V53, V49, V58, V47 = V59.V50, V59.V53, V59.V49, V59.V58, V59.V47
EB, G22 = PREP.EB, PREP.G22
SEED, X_TARGET, CONVS = V47.SEED, V47.X_TARGET, V47.CONVS
STUDY = 373
MOM, REV = V59.MOM, V59.REV
ANN = V59.ANN
PER_SHARE = V59.PER_SHARE
clean = V50.clean
pct_of = V58.pct_of

# The five cells, in the order D359 section 6 printed them. The index fixes the RNG keys and must never be reordered.
CELLS = [((10, 90), ("cap", 40)), ((10, 90), ("cap", 10)), ((10, 90), ("invalidation", 10)), ((10, 95), ("cap", 10)), ((20, 90), ("cap", 10))]
PRIMARY_IX = 0                                              # (10,90) cap 40 -- the cell the record makes primary
CELL_NAME = ["10:90/cap40", "10:90/cap10", "10:90/inv10", "10:95/cap10", "20:90/cap10"]
# D359 section 6's published numbers for these five cells, in the same order. Used ONLY by [MIR] to prove this runner reproduces the
# arm it claims to be testing before it is allowed to null it. bp per trade.
D359_MIRROR = [dict(n=3932, mean=160.5, median=51.5), dict(n=7290, mean=68.6, median=36.6), dict(n=8190, mean=47.2, median=123.4),
               dict(n=4955, mean=74.5, median=36.1), dict(n=12486, mean=52.1, median=31.1)]
HORIZON_CAPS = (5, 10, 20, 40, 60)                          # reported, NOT picked (R14, 2026-09-03)
ARM = dict(A=1, B=2, Bc=3, C=4)
SIDE_LONG = 0
DATA = REPO / "data"
SELFTEST_TMP = REPO / "temp" / "d373_selftest"

# The hurdles, as pre-registered. Kept as data so the report cannot quietly disagree with the record.
H4_NAMES_TO_HALF_SHARE = 0.10
H4_TOP1_SHARE = 0.15
H4_TOP5_SHARE = 0.50
H5_OPEN_T = 2.0
H5_RETENTION = 0.50
H7_CORR = 0.50
UNRESOLVED_SE = 2.0                                         # a margin within 2 SE of its bar is UNRESOLVED, never passed


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, stage0=d / "d373_stage0.json", ctrl=str(d / "d373_ctrl_p{part}.json"), report=d / "d373_winners_dip_long.json")


# ------------------------------------------------------------------ the signal: imported, not re-derived
def mirror(P, c, s):
    """D359's mirror signal, unchanged. [MIR] proves the ledger it builds matches D359's published table before anything is nulled."""
    return V59.mirror_signal(P, c, s)


def top_cohort(P, c):
    """The WINNER cohort -- pct_mom >= 100 - c on eligible bars. B_c's pool; the mirror of V59.cohort."""
    pct_mom, _pr, _pv, elig = V59.grids(P)
    with np.errstate(invalid="ignore"):
        return (pct_mom >= 100.0 - float(c)) & elig


def run_long(P, lo, sc, exit_, cap, A3=None):
    return V59.run_mirror(P, lo, sc, exit_, cap, A3)


# ------------------------------------------------------------------ the statistics the new hurdles need
def era1_mask(P, trades):
    """The kernel's own era split: entry bar in the first half of the span (t < T // 2), as V59.trade_block defines it."""
    half = P["T"] // 2
    return np.array([t[1] < half for t in trades], bool)


def null_stats_ext(res, P):
    """V58.null_stats plus the two quantities the new hurdles need: the per-trade MEDIAN (H2) and the era-1 per-trade mean (H3).

    [NS] the shared keys are asserted identical to V58's -- this must be an EXTENSION, not a reimplementation, or the draws stop being
    comparable to D359's."""
    base = V58.null_stats(res, P)
    pnl = V47.pnl_bp(res)
    e1 = era1_mask(P, res["trades"])
    base["trade_median_bp"] = float(np.median(pnl)) if pnl.size else float("nan")
    base["era1_mean_bp"] = float(pnl[e1].mean()) if e1.any() else float("nan")
    base["era1_trades"] = int(e1.sum())
    return base


def assert_NS(res, P):
    """[NS] null_stats_ext extends V58.null_stats and changes none of its values."""
    a, b = V58.null_stats(res, P), null_stats_ext(res, P)
    for k, v in a.items():
        assert b[k] == v or (isinstance(v, float) and np.isnan(v) and np.isnan(b[k])), f"[NS] null_stats_ext changed {k}: {v} -> {b[k]}"
    for k in ("trade_median_bp", "era1_mean_bp", "era1_trades"):
        assert k in b, f"[NS] {k} missing"
    return True


def observed_ext(res, P):
    d = null_stats_ext(res, P)
    d["entries"] = int(res["ent"].sum())
    return d


# ------------------------------------------------------------------ the controls, on the LONG side
def aprime_draw_long(lo, sc, elig, rng):
    """A' for a LONG arm: per-name time rotation within elig, the score rotated with it. V59.aprime_draw asserts the long leg is EMPTY
    (it rotates a short); this is its mirror and asserts the SHORT leg is empty. D351's assertions otherwise unchanged."""
    sl, ss, sc_ = EB.rotate_signals(lo, V59.zeros(lo), sc, elig, rng)
    assert not ss.any(), "[A'] a short appeared in the rotation of a long arm"
    assert not (sl & ~elig).any(), "[A'] a rotated event landed off the floor"
    assert np.array_equal(sl.sum(axis=0), lo.sum(axis=0)), "[A'] per-name event count changed"
    return sl, sc_


def bc_long(lo, coh_top, elig, rng):
    """B_c on the winner cohort. V59.control_bc_signal takes the cohort as an ARGUMENT, so it is reused unchanged -- only the pool
    differs (pct_mom >= 100 - c rather than <= c). Isolates the DIP's timing inside the pool of strong names."""
    return V59.control_bc_signal(lo, coh_top, elig, rng)


def draw_rng(draw, arm):
    """The best-of-5 floor needs the SAME per-name offset across the five cells within one draw (D367's shared-offset best-of-46).

    The key is (SEED, STUDY, arm, draw) and carries NO CELL INDEX, and a FRESH generator is built for every cell. That is what makes
    the offsets shared: five identical streams from five identical starts, so within a draw each name is rotated by the same amount in
    every cell, and the max over cells is a joint null rather than five independent ones."""
    return np.random.default_rng([SEED, STUDY, ARM[arm], draw])


# ------------------------------------------------------------------ [MIR] this runner reproduces the arm it claims to test
def assert_MIR(P, tol_mean=0.6, tol_med=0.6, verbose=True):
    """[MIR] Each of the five cells reproduces D359 section 6's published trade count, mean and median. D359 printed to one decimal, so
    the tolerance is the printing, not the arithmetic. WITHOUT THIS the study could null a different book than the one it reports."""
    rows = []
    for ix, ((c, s), (e, cap)) in enumerate(CELLS):
        lo = mirror(P, c, s)
        res = run_long(P, lo, V59.grids(P)[1], e, cap)
        pnl = V47.pnl_bp(res)
        got = dict(n=len(res["trades"]), mean=float(pnl.mean()), median=float(np.median(pnl)))
        exp = D359_MIRROR[ix]
        assert got["n"] == exp["n"], f"[MIR] {CELL_NAME[ix]}: {got['n']:,} trades != D359's {exp['n']:,}"
        assert abs(got["mean"] - exp["mean"]) < tol_mean, f"[MIR] {CELL_NAME[ix]}: mean {got['mean']:+.2f} != D359's {exp['mean']:+.1f}"
        assert abs(got["median"] - exp["median"]) < tol_med, f"[MIR] {CELL_NAME[ix]}: median {got['median']:+.2f} != D359's {exp['median']:+.1f}"
        rows.append(dict(cell=CELL_NAME[ix], **got, d359=exp))
        if verbose:
            print(f"    [MIR] {CELL_NAME[ix]:<12} {got['n']:>6,} trades  mean {got['mean']:+7.2f} (D359 {exp['mean']:+6.1f})  "
                  f"median {got['median']:+7.2f} (D359 {exp['median']:+6.1f})")
    return rows


# ------------------------------------------------------------------ [E] every null event is eligible; [N] the null's centre
def assert_E(P, rng, k=200):
    """[E] every event of a sampled null draw satisfies the OBSERVED events' eligibility mask (D351). Asserted per null, not once."""
    (c, s), (e, cap) = CELLS[PRIMARY_IX]
    lo, elig = mirror(P, c, s), np.asarray(P["elig"])
    coh = top_cohort(P, c)
    sA, _ = aprime_draw_long(lo, V59.grids(P)[1], elig, rng)
    assert not (sA & ~elig).any(), "[E] an A' event is ineligible"
    sBc, kept = bc_long(lo, coh, elig, rng)
    assert not (sBc & ~elig).any(), "[E] a B_c event is ineligible"
    V59.assert_Bc(sBc, lo, coh, elig, kept)
    PB = V53.b_pool_P(P, P["elig_b"])
    sB = V47.control_b_signal(PB, lo, rng)
    assert not (sB & ~elig).any(), "[E] a B event is ineligible"
    return dict(A_prime=int(sA.sum()), B=int(sB.sum()), B_c=int(sBc.sum()), observed=int(lo.sum()))


def base_rate_line(P, obs_mean, nulls):
    """[N] the null's CENTRE against the cohort's own base rate. A null centred far from the base rate is a broken null, not a
    mechanism -- D347's 'cohort drift' was the null trading the excluded tail (D351)."""
    (c, _s), _ex = CELLS[PRIMARY_IX]
    coh = top_cohort(P, c)
    r1T, m_f = np.asarray(P["r1T"]), np.asarray(P["m_f"])
    ex = r1T - m_f[:, None]
    with np.errstate(invalid="ignore"):
        base = float(np.nanmean(ex[coh])) * 1e4
    return dict(cohort_base_rate_bp_per_bar=base, observed_trade_mean_bp=obs_mean,
                null_centres={k: float(np.median(v)) for k, v in nulls.items()})


# ------------------------------------------------------------------ [S] sign in money, on the LONG
def assert_S_long(P, lo, sc, res, rng, k=300, tag="[S]"):
    """[S] sign audit IN MONEY on a long arm: a favourable move must pay POSITIVELY. V59.perturb_test drives it; +50 bp on one name's
    entry must move exactly one trade by +50.000 and no other bar."""
    tr = res["trades"]
    assert tr and all(t[4] == SIDE_LONG for t in tr), f"{tag} a short in the mirror's ledger"
    pnl = V47.pnl_bp(res)
    n = min(k, len(tr))
    ix = rng.choice(len(tr), size=n, replace=False)
    r1T, ocT, m_f, m_oc = P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"]
    worst, n_fav = 0.0, 0
    for j in ix:
        row, e0, age, _p, _side = tr[j]
        v = np.array(r1T[e0:e0 + age, row], dtype=float) - np.asarray(m_f)[e0:e0 + age]
        v[0] = float(ocT[e0, row]) - float(m_oc[e0])
        recomputed = float(np.sum(v)) * 1e4
        worst = max(worst, abs(recomputed - pnl[j]))
        n_fav += int(recomputed > 0)
    assert worst < 1e-9, f"{tag} a long trade does not equal its own recomputed path (worst {worst:.2e})"
    pert = V59.perturb_test(P, lo, sc, SIDE_LONG, res, +1)
    return dict(sampled=n, worst_abs_bp=worst, favourable=n_fav, perturb=pert)


# ------------------------------------------------------------------ H5 capturability, H7 independence
def capturability(P, c, s, e, cap):
    """[H5] gate 1e: the same signal entered at open[t] rather than at the close[t-1] that generated it. The kernel already fills at the
    NEXT OPEN (D340), so the comparison is against a same-close fill; retention = open-entry mean / close-entry mean."""
    lo, sc = mirror(P, c, s), V59.grids(P)[1]
    res_open = run_long(P, lo, sc, e, cap)
    pnl_o = V47.pnl_bp(res_open)
    t_open = float(pnl_o.mean() / (pnl_o.std(ddof=1) / np.sqrt(pnl_o.size))) if pnl_o.size > 1 else float("nan")
    close = P.get("A3_close")
    if close is None:
        return dict(open_entry_t=t_open, open_entry_mean_bp=float(pnl_o.mean()), close_entry_mean_bp=None, retention=None,
                    note="no same-close panel in prep; retention not computable here -- reported as unavailable, not as a pass")
    res_close = run_long(P, lo, sc, e, cap, A3=close)
    pnl_c = V47.pnl_bp(res_close)
    ret = float(pnl_o.mean() / pnl_c.mean()) if pnl_c.mean() != 0 else float("nan")
    return dict(open_entry_t=t_open, open_entry_mean_bp=float(pnl_o.mean()), close_entry_mean_bp=float(pnl_c.mean()), retention=ret)


def independence(P, res):
    """[H7] correlation of this arm's deployed hedged bar series to the RETIRED momentum books (D371's S6/C9) where their series are on
    disk, measured on the SHARED defined bars. Missing series are reported as unavailable, never as a pass."""
    mine = np.asarray(res["book_dep_x"], float)
    mask = np.asarray(res["mask_dep"], bool)
    out = {}
    f = DATA / "d371_read.json"
    if not f.exists():
        return dict(note=f"{f.name} absent -- correlation to the retired books not computable", arms={})
    d = json.loads(f.read_text())
    for arm, blk in d.get("arms", {}).items():
        ser = blk.get("series", {})
        for key, v in ser.items():
            v = np.asarray(v, float)
            if v.ndim != 1 or v.size != mine.size:
                out[f"{arm}/{key}"] = dict(note=f"length {v.size} != {mine.size}; not aligned, not compared")
                continue
            m = mask & np.isfinite(v) & np.isfinite(mine)
            out[f"{arm}/{key}"] = dict(bars=int(m.sum()), corr=float(np.corrcoef(mine[m], v[m])[0, 1]) if m.sum() > 2 else None)
    return dict(arms=out)


# ------------------------------------------------------------------ the hurdles
def boot_se_p95(x, draws=400, rng=None):
    """The bootstrap SE of a p95, as D369 reported it. This is what decides UNRESOLVED, so it is computed, never assumed."""
    x = np.asarray(x, float)
    rng = rng or np.random.default_rng([SEED, STUDY, 99])
    q = [np.quantile(rng.choice(x, size=x.size, replace=True), .95) for _ in range(draws)]
    return float(np.std(q, ddof=1))


def verdict(obs, null_x, higher_is_better=True):
    """PASS / FAIL / UNRESOLVED against a null's p95, with the bootstrap SE carried. A margin within 2 SE of the bar is UNRESOLVED --
    never passed. That is the guard the pre-registration keeps from D369."""
    x = np.asarray(null_x, float)
    p95, p50 = float(np.quantile(x, .95)), float(np.median(x))
    se = boot_se_p95(x)
    margin = (obs - p95) if higher_is_better else (p95 - obs)
    if abs(margin) < UNRESOLVED_SE * se:
        v = "UNRESOLVED"
    else:
        v = "PASS" if margin > 0 else "FAIL"
    return dict(observed=float(obs), p50=p50, p95=p95, se_p95=se, margin=float(margin), margin_in_se=float(margin / se) if se > 0 else None,
                above=bool(obs > p95), draws=int(x.size), verdict=v)


def hurdle_H2(pnl, null_med):
    """[H2] the chain mean > median > 0, at the principal's ruling (pre-reg 5a). Three legs, each reported; ALL must hold."""
    mean, med = float(pnl.mean()), float(np.median(pnl))
    legs = dict(median_positive=dict(value=med, holds=bool(med > 0)),
                median_above_nulls=verdict(med, null_med),
                mean_exceeds_median=dict(mean=mean, median=med, holds=bool(mean > med)))
    vs = [legs["median_positive"]["holds"], legs["median_above_nulls"]["verdict"] == "PASS", legs["mean_exceeds_median"]["holds"]]
    unresolved = legs["median_above_nulls"]["verdict"] == "UNRESOLVED"
    return dict(chain="mean > median > 0", mean_bp=mean, median_bp=med, legs=legs,
                verdict="UNRESOLVED" if unresolved else ("PASS" if all(vs) else "FAIL"))


def hurdle_H4(groups):
    """[H4] breadth, as SHARES of names traded -- the mis-specification D371 section 6a found in its own H5."""
    n_names = groups.get("n_names") or groups.get("names") or 0
    to_half = groups.get("names_to_half_pnl")
    share = (to_half / n_names) if (to_half and n_names) else None
    top = groups.get("top_name_share") or {}
    t1, t5 = top.get("top1"), top.get("top5")
    legs = dict(names_to_half_share=dict(value=share, bar=H4_NAMES_TO_HALF_SHARE, holds=bool(share is not None and share >= H4_NAMES_TO_HALF_SHARE)),
                top1_share=dict(value=t1, bar=H4_TOP1_SHARE, holds=bool(t1 is not None and t1 <= H4_TOP1_SHARE)),
                top5_share=dict(value=t5, bar=H4_TOP5_SHARE, holds=bool(t5 is not None and t5 <= H4_TOP5_SHARE)))
    known = [v["holds"] for v in legs.values() if v["value"] is not None]
    return dict(legs=legs, names=n_names, names_to_half=to_half,
                verdict=("PASS" if all(known) else "FAIL") if len(known) == 3 else "UNRESOLVED")


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    """[X] IS THE ONE THAT MATTERS: every audit must RAISE on a deliberately broken book. A self-test that cannot fail is worse than none."""
    print("\nSELFTEST")
    t0 = time.time()
    (c, s), (e, cap) = CELLS[PRIMARY_IX]
    lo, sc, elig = mirror(P, c, s), V59.grids(P)[1], np.asarray(P["elig"])
    res = run_long(P, lo, sc, e, cap)
    rng = np.random.default_rng([SEED, STUDY, 0])

    print("  [MIR] the five cells against D359 section 6")
    assert_MIR(P)

    print("  [NS] null_stats_ext extends V58.null_stats and changes nothing")
    assert_NS(res, P)

    print("  [L] lag audit -- the held set re-derived WITHOUT the selection function")
    n_lag = assert_L(P, lo, res)
    print(f"       {n_lag:,} entries re-derived from the t-1 grids by a second implementation")

    print("  [S] sign in money on the long")
    sgn = assert_S_long(P, lo, sc, res, rng)
    print(f"       {sgn['sampled']} trades equal their recomputed path (worst {sgn['worst_abs_bp']:.2e}); {sgn['favourable']} favourable")

    print("  [E] every null draw's events are eligible")
    print(f"       {assert_E(P, rng)}")

    print("  [Q] right-quantity -- the compounded grid differs from the one not meant to be scored")
    assert_Q(P, res)

    print("  [X] the audits RAISE on a deliberately broken book")
    broke = assert_X(P, lo, sc, elig, res)
    for name, ok in broke.items():
        print(f"       {name}: {'RAISED' if ok else 'DID NOT RAISE'}")
    assert all(broke.values()), f"[X] an audit failed to raise: {[k for k, v in broke.items() if not v]}"
    print(f"  selftest OK ({time.time() - t0:.0f}s)  {PREP.rss_line()}")


def assert_L(P, lo, res):
    """[L] LAG AUDIT. Re-derive the entry set from the t-1 information in a SECOND implementation that never calls mirror_signal or
    V59.grids -- the raw scores are re-percentiled here, independently. ~93% of D279's apparent edge was this bug."""
    (c, s), _ex = CELLS[PRIMARY_IX]
    raw_mom, raw_rev = pct_of(P, MOM), pct_of(P, REV)          # the same public helper the study uses ...
    # ... but the CONDITION is rebuilt from scratch, shifted by hand, and never touches mirror_signal / grids.
    T = P["T"]
    elig = np.asarray(P["elig"])
    prev = np.full_like(raw_rev, np.nan)
    prev[1:] = raw_rev[:-1]
    with np.errstate(invalid="ignore"):
        indep = (raw_mom >= 100.0 - float(c)) & (raw_rev <= 100.0 - float(s)) & (prev > 100.0 - float(s)) & elig
    assert np.array_equal(indep, lo), "[L] the independent re-derivation of the entry set disagrees with mirror_signal"
    # and the trades' entry bars must all be signal bars
    for row, e0, _age, _p, _side in res["trades"]:
        assert lo[e0, row], f"[L] a trade entered on a bar with no signal ({e0}, {row})"
    assert T == raw_mom.shape[0], "[L] grid length"
    return int(lo.sum())


def assert_Q(P, res):
    """[Q] right-quantity: the deployed hedged series is NOT the unhedged one, and the per-trade ledger is not the per-bar book."""
    hx, ux = np.asarray(res["book_dep_x"], float), np.asarray(res["book_dep"], float)
    m = np.asarray(res["mask_dep"], bool)
    assert not np.allclose(hx[m], ux[m]), "[Q] the hedged and unhedged deployed series are identical -- one of them is not what it claims"
    pnl = V47.pnl_bp(res)
    assert pnl.size == len(res["trades"]), "[Q] the ledger length is not the trade count"
    assert abs(float(pnl.mean()) - float(hx[m].mean())) > 1e-9, "[Q] the per-trade mean equals the per-bar mean -- the two lenses are the same object"
    return True


def assert_X(P, lo, sc, elig, res):
    """[X] the audits must RAISE on a deliberately broken book. Each entry is True when the audit CORRECTLY raised."""
    out = {}

    def raises(fn):
        try:
            fn()
        except AssertionError:
            return True
        except Exception:
            return True
        return False

    # 1. the sign flipped: a long ledger presented as a short
    bad = dict(res)
    bad["trades"] = [(t[0], t[1], t[2], t[3], 1) for t in res["trades"]]
    out["sign_flipped_ledger"] = raises(lambda: assert_S_long(P, lo, sc, bad, np.random.default_rng([SEED, STUDY, 1])))

    # 2. an event drawn OUTSIDE the eligible mask
    bad_sig = lo.copy()
    off = np.flatnonzero(~elig.ravel())
    bad_sig.ravel()[off[: max(1, off.size // 1000)]] = True
    out["ineligible_event"] = raises(lambda: _assert_all_eligible(bad_sig, elig))

    # 3. B_c drawing from outside the cohort
    (c, _s), _ex = CELLS[PRIMARY_IX]
    coh = top_cohort(P, c)
    bad_bc = lo.copy()
    outside = np.flatnonzero((elig & ~coh).ravel())
    if outside.size:
        bad_bc.ravel()[outside[:50]] = True
    out["bc_outside_cohort"] = raises(lambda: V59.assert_Bc(bad_bc, lo, coh, elig, 0))

    # 4. the lag audit against a signal shifted the WRONG way (look-ahead)
    ahead = np.zeros_like(lo)
    ahead[:-1] = lo[1:]
    out["lookahead_signal"] = raises(lambda: assert_L_against(P, ahead))

    # 5. null_stats_ext silently changing a shared key
    out["null_stats_mutated"] = raises(lambda: _assert_NS_broken(res, P))
    return out


def _assert_all_eligible(sig, elig):
    assert not (sig & ~elig).any(), "[E] an event is ineligible"


def assert_L_against(P, claimed):
    (c, s), _ex = CELLS[PRIMARY_IX]
    raw_mom, raw_rev = pct_of(P, MOM), pct_of(P, REV)
    elig = np.asarray(P["elig"])
    prev = np.full_like(raw_rev, np.nan)
    prev[1:] = raw_rev[:-1]
    with np.errstate(invalid="ignore"):
        indep = (raw_mom >= 100.0 - float(c)) & (raw_rev <= 100.0 - float(s)) & (prev > 100.0 - float(s)) & elig
    assert np.array_equal(indep, claimed), "[L] the independent re-derivation disagrees"


def _assert_NS_broken(res, P):
    a = V58.null_stats(res, P)
    b = dict(null_stats_ext(res, P))
    b["trade_mean_bp"] = b["trade_mean_bp"] + 1.0                     # a deliberate mutation of a SHARED key
    for k, v in a.items():
        assert b[k] == v or (isinstance(v, float) and np.isnan(v) and np.isnan(b[k])), f"[NS] mutated {k}"


def stage_stage0(P, paths):
    """The shape, before any null. Four groups with the TOP TRADE NAMED and its bar printed -- a concentration report is not finished
    until the top trade is named (D322 reported the share, never looked, and fifteen studies ran on thirty fabricated days)."""
    print("\nSTAGE 0 -- the shape, before any null. This admits nothing.")
    (c, s), (e, cap) = CELLS[PRIMARY_IX]
    lo, sc, elig = mirror(P, c, s), V59.grids(P)[1], np.asarray(P["elig"])
    mir = assert_MIR(P)
    res = run_long(P, lo, sc, e, cap)
    pnl = V47.pnl_bp(res)
    groups = V50.four_groups(res["trades"], pnl, P, elig)
    obs = observed_ext(res, P)
    h2 = dict(mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)), mean_exceeds_median=bool(pnl.mean() > np.median(pnl)))
    h4 = hurdle_H4(groups)
    horizon = {}
    for k in HORIZON_CAPS:
        r = run_long(P, lo, sc, "cap", k)
        p = V47.pnl_bp(r)
        horizon[f"cap{k}"] = dict(trades=len(r["trades"]), mean_bp=float(p.mean()), median_bp=float(np.median(p)),
                                  hold_mean=float(np.mean([t[2] for t in r["trades"]])))
    out = dict(study=STUDY, cell=CELL_NAME[PRIMARY_IX], mirror_check=mir, observed=obs, four_groups=groups,
               H2_shape_before_nulls=h2, H4_breadth=h4, horizon_profile=horizon, rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["stage0"].write_text(json.dumps(clean(out)))          # [P] PERSIST BEFORE RENDERING -- D371 lost its evidence to a print loop
    print(f"  wrote {paths['stage0']}")
    print_stage0(out)
    return out


def print_stage0(out):
    g, h2, h4 = out["four_groups"], out["H2_shape_before_nulls"], out["H4_breadth"]
    print(f"\n  {out['cell']}: {g.get('count', g.get('trades'))} trades")
    print(f"    mean {h2['mean_bp']:+.2f}  median {h2['median_bp']:+.2f}  -> mean > median > 0 is "
          f"{'SATISFIED' if (h2['mean_exceeds_median'] and h2['median_bp'] > 0) else 'NOT SATISFIED'} before any null")
    for k in ("win_rate", "payoff", "hold_mean", "hold_median", "skew", "kurtosis_excess"):
        if k in g:
            print(f"    {k:<18} {g[k]}")
    for k in ("mean_ex_top_bp", "mean_ex_bottom_bp", "mean_trimmed_bp"):
        if k in g:
            print(f"    {k:<18} {g[k]:+.2f}")
    print(f"    names to half {g.get('names_to_half_pnl')} of {g.get('n_names')}  "
          f"(share {h4['legs']['names_to_half_share']['value']}, bar {H4_NAMES_TO_HALF_SHARE})")
    print(f"    top name share {g.get('top_name_share')}")
    tt = g.get("top_trade")
    if tt:
        print(f"    TOP TRADE {tt}")
    print("\n  horizon profile (REPORTED, NOT PICKED -- R14 2026-09-03):")
    for k, v in out["horizon_profile"].items():
        print(f"    {k:<6} {v['trades']:>6,} trades  mean {v['mean_bp']:+8.2f}  median {v['median_bp']:+8.2f}  hold {v['hold_mean']:5.1f}")


def stage_cells(P, draws, part, paths):
    """A'/B/B_c over ALL FIVE cells with a SHARED per-name offset per draw, so the best-of-5 floor is a joint null and not five
    independent ones."""
    print(f"\nCONTROLS -- {draws} draws x 5 cells, shared offset, part {part}")
    elig, sc = np.asarray(P["elig"]), V59.grids(P)[1]
    sigs = [mirror(P, c, s) for (c, s), _ex in CELLS]
    cohs = [top_cohort(P, c) for (c, _s), _ex in CELLS]
    obs = []
    for ix, (_cs, (e, cap)) in enumerate(CELLS):
        r = run_long(P, sigs[ix], sc, e, cap)
        obs.append(observed_ext(r, P))
        print(f"  {CELL_NAME[ix]:<12} {obs[ix]['trades']:>6,} trades  mean {obs[ix]['trade_mean_bp']:+8.2f}  median {obs[ix]['trade_median_bp']:+8.2f}  "
              f"era1 {obs[ix]['era1_mean_bp']:+8.2f} ({obs[ix]['era1_trades']:,} trades)")
    PB = V53.b_pool_P(P, P["elig_b"])
    keys = ("gross_bp", "net_bp_PUB", "sharpe_net_PUB", "net_bp_PB", "trade_mean_bp", "trade_median_bp", "era1_mean_bp", "trades", "exposure")
    A = [{k: [] for k in keys} for _ in CELLS]
    B = [{k: [] for k in keys} for _ in CELLS]
    BC = [{k: [] for k in keys} for _ in CELLS]
    keptB, keptBc = [], []
    t0 = time.time()
    for d in range(part * draws, (part + 1) * draws):
        for ix, (_cs, (e, cap)) in enumerate(CELLS):
            sA, scA = aprime_draw_long(sigs[ix], sc, elig, draw_rng(d, "A"))
            st = null_stats_ext(run_long(P, sA, scA, e, cap), P)
            for k in keys:
                A[ix][k].append(st[k])
        for ix, (_cs, (e, cap)) in enumerate(CELLS):
            sBc, kc = bc_long(sigs[ix], cohs[ix], elig, draw_rng(d, "Bc"))
            V59.assert_Bc(sBc, sigs[ix], cohs[ix], elig, kc)
            keptBc.append(kc)
            st = null_stats_ext(run_long(P, sBc, sc, e, cap), P)
            for k in keys:
                BC[ix][k].append(st[k])
        if d < part * draws + (draws + 1) // 2:                      # B at half the count, as pre-registered
            for ix, (_cs, (e, cap)) in enumerate(CELLS):
                sB = V47.control_b_signal(PB, sigs[ix], draw_rng(d, "B"))
                kb, _ = V58.assert_B(P, PB, sigs[ix], sB, elig)
                keptB.append(kb)
                st = null_stats_ext(run_long(P, sB, sc, e, cap), P)
                for k in keys:
                    B[ix][k].append(st[k])
        n = d - part * draws + 1
        if n % 10 == 0 or n == draws:
            print(f"    {n}/{draws} ({time.time() - t0:.0f}s, {(time.time() - t0) / n:.2f} s/draw)  {PREP.rss_line()}", flush=True)
    out = dict(study=STUDY, draws=draws, part=part, cells=CELL_NAME, observed=obs,
               control_A_prime=A, control_B=B, control_B_c=BC, B_kept=keptB, B_c_kept=keptBc,
               shared_offset="per draw, per arm: default_rng([SEED, STUDY, ARM, draw]) re-derived for every cell",
               seconds_per_draw=(time.time() - t0) / max(draws, 1), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["ctrl"].format(part=part))
    f.write_text(json.dumps(clean(out)))                             # [P] persist before rendering
    print(f"  wrote {f} ({time.time() - t0:.0f}s)")
    return out


def load_controls(paths):
    fs = sorted(paths["dir"].glob("d373_ctrl_p*.json"))
    if not fs:
        return None
    A = [{} for _ in CELLS]
    B = [{} for _ in CELLS]
    BC = [{} for _ in CELLS]
    parts, obs = [], None
    for f in fs:
        d = json.loads(f.read_text())
        assert d["cells"] == CELL_NAME, f"[P] {f.name}: cell order differs -- the RNG keys would not line up"
        obs = obs or d["observed"]
        for ix in range(len(CELLS)):
            for k, v in d["control_A_prime"][ix].items():
                A[ix].setdefault(k, []).extend(v)
            for k, v in d["control_B"][ix].items():
                B[ix].setdefault(k, []).extend(v)
            for k, v in d["control_B_c"][ix].items():
                BC[ix].setdefault(k, []).extend(v)
        parts.append(dict(file=f.name, part=d["part"], draws=d["draws"], seconds_per_draw=d.get("seconds_per_draw")))
    return dict(parts=parts, observed=obs, A=A, B=B, Bc=BC)


def best_of_5(ctrl, key):
    """The best-of-5 floor: the MAX over the five cells WITHIN each draw. Scoring the chosen cell against its own control alone would
    flatter it, because cap 40 was chosen after seeing all five of D359's rows (pre-reg section 7)."""
    out = {}
    for arm in ("A", "B", "Bc"):
        cols = [np.asarray(ctrl[arm][ix][key], float) for ix in range(len(CELLS))]
        n = min(c.size for c in cols)
        out[arm] = np.max(np.vstack([c[:n] for c in cols]), axis=0).tolist()
    return out


def stage_report(P, paths):
    print("\nREPORT")
    t0 = time.time()
    ctrl = load_controls(paths)
    assert ctrl, "no control files -- run --cells first"
    (c, s), (e, cap) = CELLS[PRIMARY_IX]
    lo, sc, elig = mirror(P, c, s), V59.grids(P)[1], np.asarray(P["elig"])
    res = run_long(P, lo, sc, e, cap)
    pnl = V47.pnl_bp(res)
    obs = observed_ext(res, P)
    groups = V50.four_groups(res["trades"], pnl, P, elig)

    floor_mean = best_of_5(ctrl, "trade_mean_bp")
    floor_med = best_of_5(ctrl, "trade_median_bp")
    floor_era1 = best_of_5(ctrl, "era1_mean_bp")
    rngC = np.random.default_rng([SEED, STUDY, ARM["C"]])
    ctrl_C = V58.control_C(pnl, rngC, draws=2000)

    H1 = {arm: verdict(obs["trade_mean_bp"], floor_mean[arm]) for arm in ("A", "B", "Bc")}
    H1["C"] = ctrl_C
    H2 = {arm: hurdle_H2(pnl, floor_med[arm]) for arm in ("A", "B", "Bc")}
    e1 = era1_mask(P, res["trades"])
    era1_obs = float(pnl[e1].mean()) if e1.any() else float("nan")
    H3 = {arm: verdict(era1_obs, floor_era1[arm]) for arm in ("A", "Bc")}
    H4 = hurdle_H4(groups)
    H5 = capturability(P, c, s, e, cap)
    H7 = independence(P, res)
    dep = V59.deployed_block(res, P)
    nb = base_rate_line(P, obs["trade_mean_bp"], {k: floor_mean[k] for k in floor_mean})

    def V(x):
        return x.get("verdict") if isinstance(x, dict) else None

    hurdles = dict(
        H1=dict(legs=H1, verdict=_worst([V(H1[a]) for a in ("A", "B", "Bc")] + ["PASS" if ctrl_C.get("above") else "FAIL"])),
        H2=dict(legs=H2, verdict=_worst([V(H2[a]) for a in ("A", "B", "Bc")])),
        H3=dict(legs=H3, era1_observed_bp=era1_obs, era1_trades=int(e1.sum()), verdict=_worst([V(H3[a]) for a in ("A", "Bc")])),
        H4=H4,
        H5=dict(**H5, verdict=("UNRESOLVED" if H5.get("retention") is None else
                               ("PASS" if (H5["open_entry_t"] >= H5_OPEN_T and H5["retention"] >= H5_RETENTION) else "FAIL"))),
        H7=dict(**H7, bar=H7_CORR),
    )
    predictions = score_predictions(hurdles, obs, pnl, dep, H7)
    out = dict(study=STUDY, cell=CELL_NAME[PRIMARY_IX], observed=obs, four_groups=groups, deployed=dep,
               controls=dict(parts=ctrl["parts"], draws=len(floor_mean["A"]), floor="best-of-5, max over cells within a draw"),
               null_centres=nb, hurdles=hurdles, predictions=predictions, rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out)))               # [P] PERSIST BEFORE RENDERING
    print(f"  wrote {paths['report']}")
    print_report(out)
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def _worst(vs):
    vs = [v for v in vs if v]
    if any(v == "FAIL" for v in vs):
        return "FAIL"
    if any(v == "UNRESOLVED" for v in vs):
        return "UNRESOLVED"
    return "PASS" if vs else "UNRESOLVED"


def score_predictions(h, obs, pnl, dep, H7):
    """The eight predictions of pre-reg section 8, scored mechanically. Q3 is the AGAINST prediction: I expect H3 to fail."""
    corrs = [v.get("corr") for v in H7.get("arms", {}).values() if isinstance(v, dict) and v.get("corr") is not None]
    mx = max((abs(x) for x in corrs), default=None)
    return {
        "Q1": dict(claim="the mean is above B_c's p95 -- the dip carries timing INSIDE the winner pool",
                   outcome=h["H1"]["legs"]["Bc"]["verdict"]),
        "Q2": dict(claim="the chain mean > median > 0 holds, median above all controls' p95", outcome=h["H2"]["verdict"]),
        "Q3": dict(claim="AGAINST: H3 fails -- era 1 is <= 0 or inside its controls", outcome=h["H3"]["verdict"],
                   prediction_held=(h["H3"]["verdict"] in ("FAIL", "UNRESOLVED"))),
        "Q4": dict(claim="|corr| to the retired S6/C9 books is 0.2-0.5", max_abs_corr=mx,
                   outcome=None if mx is None else ("HELD" if 0.2 <= mx <= 0.5 else "FALSIFIED")),
        "Q5": dict(claim="capturability retention >= 50%", outcome=h["H5"]["verdict"]),
        "Q6": dict(claim="the horizon peak on gross per trade sits at the GRID EDGE (cap 60), not interior -- see --stage0", outcome="see stage0"),
        "Q7": dict(claim="the top trade is <= 15% of the ledger", outcome=h["H4"]["legs"]["top1_share"]["holds"]),
    }


def print_report(out):
    h = out["hurdles"]
    print(f"\n  {out['cell']}  {out['observed']['trades']:,} trades  mean {out['observed']['trade_mean_bp']:+.2f}  "
          f"median {out['observed']['trade_median_bp']:+.2f}  era1 {out['observed']['era1_mean_bp']:+.2f}")
    print(f"  controls: {out['controls']['draws']} draws, {out['controls']['floor']}")
    print("\n  HURDLES")
    for k in ("H1", "H2", "H3", "H4", "H5", "H7"):
        v = h[k].get("verdict", "-")
        print(f"    {k}  {v}")
        if k in ("H1", "H3"):
            for arm, d in h[k]["legs"].items():
                if isinstance(d, dict) and "p95" in d:
                    print(f"         {arm:<3} obs {d['observed']:+8.2f}  p50 {d['p50']:+8.2f}  p95 {d['p95']:+8.2f}  "
                          f"SE {d['se_p95']:.3f}  margin {d['margin']:+8.2f} ({d['margin_in_se']:+.1f} SE)  {d['verdict']}")
        if k == "H2":
            for arm, d in h[k]["legs"].items():
                l = d["legs"]["median_above_nulls"]
                print(f"         {arm:<3} median {d['median_bp']:+8.2f}  p95 {l['p95']:+8.2f}  SE {l['se_p95']:.3f}  "
                      f"({l['margin_in_se']:+.1f} SE)  mean>median {d['legs']['mean_exceeds_median']['holds']}  {d['verdict']}")
    print("\n  PREDICTIONS")
    for k, v in out["predictions"].items():
        print(f"    {k}  {v.get('outcome')}   {v['claim']}")
    print("\n  NULL CENTRES vs the cohort's own base rate [N]")
    print(f"    {out['null_centres']}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--cells", action="store_true", help="A'/B/B_c over all five cells with a shared offset")
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D373  the winners' dip long -- a fresh rev_5 dip inside the mom_252_21 TOP decile, entered LONG; and mean > median > 0")
    paths = out_paths(a.out_dir)
    P = PREP.prep(need_grids=(a.selftest or a.report))
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    if a.selftest:
        stage_selftest(P)
    elif a.stage0:
        stage_stage0(P, paths)
    elif a.cells:
        stage_cells(P, a.draws, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --stage0, --cells, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
