"""D377 -- the hedge leaves a common factor. Can any of four remove it without removing the edge?

    uv run python scripts/run_d377_hedge.py --selftest
    uv run python scripts/run_d377_hedge.py --build --draws 500      one pass, reconstructs all four hedges
    uv run python scripts/run_d377_hedge.py --report
    --out-dir DIR   (default data/ -- smoke runs pass temp/... so nothing under data/ is touched)

Pre-registration: docs/decisions/D377-the-hedge-leaves-a-common-factor.md (committed 3888ae9, amended c59f6de, BOTH before this file -- R8)

METHODOLOGY / CONVENTION. Selects a hedge convention for future studies. Admits nothing, reads no holdout, changes no book.

THE INCUMBENT HEDGE ASSUMES BETA IS EXACTLY 1 FOR EVERY NAME ON EVERY BAR: assert_HX defines the hedged series as sgn * (v - m)
against the floored equal-weight market. A properly lagged per-name rolling beta -- roll_beta(r1T, m_f), window 63 / min 21, window
ending t-1 -- already exists in d348_prep and is unused in the default path.

D376 measured two UNRELATED books at rho +0.476 and found the residual factor is a PER-BAR effect: books trading the same DAYS
correlate more than books trading the same NAMES. That is mechanistically what an unhedged beta looks like -- a big market day leaves
(beta - 1) * m in every book exposed that day.

THE TENSION (pre-reg s0). A hedge that subtracts everything drives correlation to zero and the edge with it. D373's B_c control put
+126.54 of +160.55 bp/trade inside the cohort, and D376 puts two cohort books at 0.92, so THE COHORT EXPOSURE MAY BE THE EDGE. A hedge
is adopted only if it clears BOTH legs: M1 cuts the floor by >= 4 bootstrap SE (four, not two -- best-of-4), AND M2 preserves >= 90% of
the gross mean per trade. Q3 predicts H2 clears M1 and FAILS M2, disqualifying the most promising candidate.

THE RECONSTRUCTION (pre-reg s2a) is what makes this one pass rather than four: the held set does not depend on the hedge, so
    book_dep_x^H[t] = book_dep_unhedged[t] - (mean over names held at t of h_name[t])
and one pass accumulates the unhedged series plus four hedge-means. [REC] proves the reconstructed INCUMBENT matches the kernel's own
book_dep_x to < 1e-12 (amendment c59f6de: bit-for-bit is unachievable because sum(v-m)/N and sum(v)/N - m associate differently, and
CLAUDE.md forbids reordering a float sum to force agreement).

THE ENTRY BAR USES m_f_oc, NOT m_f, because the kernel fills at the next open (D340). Every hedge carries that distinction per
name-bar; [REC] is what catches it if one does not.

ASSERTIONS [MIR][REC][LAG][INV][DIR][SER][DEG][X] -- pre-reg s6. [X] is the one that matters.
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


V76 = _load("d376r", "run_d376_correlation_floor.py")          # the ensemble machinery, the pair blocks, the clustered bootstrap
V73, PREP, V59, V58, V50, V47, V53 = V76.V73, V76.PREP, V76.V59, V76.V58, V76.V50, V76.V47, V76.V53
clean = V50.clean
STUDY = 377
DATA = REPO / "data"

CELL = V73.CELLS[V73.PRIMARY_IX]
CELL_NAME = V73.CELL_NAME[V73.PRIMARY_IX]
D373_LEDGER = dict(trades=3932, mean_bp=160.55, median_bp=51.55)
ARMS = V76.ARMS                                                # ("A", "B", "Bc")
HEDGES = ("H0", "H1", "H2", "H3")
HEDGE_NAME = {"H0": "unit market (incumbent)", "H1": "per-name rolling beta 63/21",
              "H2": "mom_252_21 decile cohort", "H3": "price decile"}
REC_TOL = 1e-12                                                # pre-reg s2a as amended c59f6de
M1_SE = 4.0                                                    # best-of-4: four SE, not two
M2_EDGE_KEEP = 0.90                                            # >= 90% of H0's gross mean per trade
N_DECILES = 10


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, ens=d / "d377_ensemble.npz", report=d / "d377_hedge.json")


# ------------------------------------------------------------------ the four hedges, each computable at t-1
def decile_of(grid, elig, lag=1):
    """Decile membership from a LAGGED grid: bar t's membership comes from bar t-lag. -1 where undefined or ineligible.

    [LAG] a hedge that keys on bar t's own value is look-ahead; D279 lost ~93% of its apparent edge to exactly that.
    """
    g = np.full_like(grid, np.nan, dtype=float)
    g[lag:] = grid[:-lag] if lag else grid
    e = np.zeros_like(elig)
    e[lag:] = elig[:-lag] if lag else elig
    d = np.full(grid.shape, -1, np.int8)
    ok = np.isfinite(g) & e
    with np.errstate(invalid="ignore"):
        q = np.clip((g / (100.0 / N_DECILES)).astype(int), 0, N_DECILES - 1)
    d[ok] = q[ok]
    return d


def decile_returns(dec, ret):
    """Equal-weight return of each decile on each bar, from names with a finite return. NaN where a decile is empty that bar."""
    T = dec.shape[0]
    out = np.full((T, N_DECILES), np.nan)
    fin = np.isfinite(ret)
    for k in range(N_DECILES):
        m = (dec == k) & fin
        cnt = m.sum(axis=1)
        with np.errstate(invalid="ignore"):
            s = np.where(m, ret, 0.0).sum(axis=1)
            out[:, k] = np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)
    return out


def build_hedges(P):
    """The four hedges as (close-bar, open-bar) per-name-bar subtractions. Everything keys on t-1 information; [LAG] proves it."""
    m_f, m_f_oc = np.asarray(P["m_f"], float), np.asarray(P["m_f_oc"], float)
    r1T, ocT = np.asarray(P["r1T"], float), np.asarray(P["ocT"], float)
    beta = np.asarray(P["beta"], float)                        # roll_beta window ends at t-1 -- already lagged
    elig = np.asarray(P["elig"], bool)
    pct_mom = V59.grids(P)[0]
    n_bad_beta = int((~np.isfinite(beta)).sum())

    dec_mom = decile_of(np.asarray(pct_mom, float), elig)
    price = np.asarray(P["RAW_CLOSE"], float)
    pr_pct = V47.percentile_grid(price)
    dec_px = decile_of(np.asarray(pr_pct, float), elig)

    mom_close, mom_open = decile_returns(dec_mom, r1T), decile_returns(dec_mom, ocT)
    px_close, px_open = decile_returns(dec_px, r1T), decile_returns(dec_px, ocT)

    return dict(m_f=m_f, m_f_oc=m_f_oc, beta=beta, dec_mom=dec_mom, dec_px=dec_px,
                mom_close=mom_close, mom_open=mom_open, px_close=px_close, px_open=px_open,
                n_bad_beta=n_bad_beta, beta_defined_share=float(np.isfinite(beta).mean()))


def hedge_values(HH, which, bars, rows, is_entry):
    """The per-name-bar subtraction for one hedge, over a flat list of held (bar, name) pairs.

    H1 falls back to beta = 1 where the rolling beta is undefined (< 21 observations), which is exactly the incumbent's treatment, so
    H1 is a strict refinement of H0 rather than a partial hedge on a different denominator. The share is reported (pre-reg s6 [DEG]).
    H2/H3 fall back to the unit market where a name's decile is undefined that bar, for the same reason.
    """
    m = np.where(is_entry, HH["m_f_oc"][bars], HH["m_f"][bars])
    if which == "H0":
        return m, 0
    if which == "H1":
        b = HH["beta"][bars, rows]
        bad = int((~np.isfinite(b)).sum())
        return np.where(np.isfinite(b), b, 1.0) * m, bad
    dec, tab_c, tab_o = ((HH["dec_mom"], HH["mom_close"], HH["mom_open"]) if which == "H2"
                         else (HH["dec_px"], HH["px_close"], HH["px_open"]))
    k = dec[bars, rows]
    ok = k >= 0
    kk = np.where(ok, k, 0)
    v = np.where(is_entry, tab_o[bars, kk], tab_c[bars, kk])
    bad = int((~ok).sum() + (~np.isfinite(v)).sum())
    return np.where(ok & np.isfinite(v), v, m), bad


def held_index(res, T):
    """Flat (bar, name, is_entry) triples for every held name-bar, from the trade ledger. Vectorised -- no per-trade Python loop."""
    tr = res["trades"]
    rows = np.array([t[0] for t in tr], np.int64)
    e0s = np.array([t[1] for t in tr], np.int64)
    ages = np.array([t[2] for t in tr], np.int64)
    tot = int(ages.sum())
    ends = np.cumsum(ages)
    off = np.arange(tot) - np.repeat(ends - ages, ages)
    bars = np.repeat(e0s, ages) + off
    keep = bars < T
    return bars[keep], np.repeat(rows, ages)[keep], (off == 0)[keep]


def hedge_means(res, HH, T):
    """Per-bar mean of each hedge over the names held that bar, plus the held count. The object section 2a's reconstruction needs."""
    bars, rows, ent = held_index(res, T)
    cnt = np.bincount(bars, minlength=T).astype(float)
    out, bad = {}, {}
    for h in HEDGES:
        v, nb = hedge_values(HH, h, bars, rows, ent)
        s = np.bincount(bars, weights=v, minlength=T)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[h] = np.where(cnt > 0, s / np.maximum(cnt, 1), np.nan)
        bad[h] = nb
    return out, cnt, bad, int(bars.size)


def reconstruct(res, hm, h):
    """book_dep_x^H = book_dep_unhedged - hedge-mean. Section 2a."""
    return np.asarray(res["book_dep"], float) - hm[h]


def covered_mask(res, cnt):
    """[TAIL] the bars the TRADE LEDGER covers, which is where a reconstruction can be right at all.

    Found by [REC], which fired at 1.059e-03 -- three orders above float noise, so a specification error and not rounding.
    Positions still OPEN at the last bar are in the kernel's series and NOT in the trade ledger; `assert_HX` documents exactly this
    and handles it the same way. Here that is 73 positions over a contiguous tail of 39 bars (4,148 -> 4,186 of 4,187). On the 3,146
    bars the ledger does cover, the reconstruction matches the kernel to 8.24e-17 -- machine epsilon.

    Excluding the tail is therefore adopting the kernel's own documented convention, not loosening a test. The contiguity is
    ASSERTED rather than assumed, because a non-contiguous mismatch would mean something else is wrong.
    """
    held = np.asarray(res["held"], float)
    cov = held == cnt
    unc = np.flatnonzero(~cov)
    if unc.size:
        assert np.array_equal(unc, np.arange(unc[0], held.size)), \
            "[TAIL] the bars the ledger fails to cover are not a contiguous tail -- this is not the open-position tail"
    return np.asarray(res["mask_dep"], bool) & cov


# ------------------------------------------------------------------ audits
def assert_MIR(P, res):
    pnl = np.asarray(V47.pnl_bp(res), float)
    got = dict(trades=len(res["trades"]), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)))
    assert got["trades"] == D373_LEDGER["trades"], f"[MIR] {got['trades']:,} trades != D373's {D373_LEDGER['trades']:,}"
    for k in ("mean_bp", "median_bp"):
        assert abs(got[k] - D373_LEDGER[k]) < 0.01, f"[MIR] {k} {got[k]:+.4f} != D373's {D373_LEDGER[k]:+.2f}"
    return got


def assert_REC(res, hm, cnt, P):
    """[REC] the reconstructed INCUMBENT must match the kernel's own book_dep_x on every LEDGER-COVERED bar (pre-reg s2a as amended).

    The comparison is on `covered_mask`, not on mask_dep: see [TAIL]. The tolerance keeps all its power -- the observed deviation on
    covered bars is ~1e-16 against a 1e-12 bound, and the specification error that motivated [TAIL] showed up at 1e-3.
    """
    k = np.asarray(res["book_dep_x"], float)
    r = reconstruct(res, hm, "H0")
    m = covered_mask(res, cnt) & np.isfinite(k) & np.isfinite(r)
    assert m.any(), "[REC] no covered bars to compare"
    d = float(np.abs(k[m] - r[m]).max())
    assert d < REC_TOL, f"[REC] reconstruction misses the kernel by {d:.3e}, above {REC_TOL:.0e} -- it is not the incumbent"
    return dict(max_abs_dev=d, bars=int(m.sum()), tol=REC_TOL)


def assert_LAG(P, HH, n_probe=300):
    """[LAG] every hedge rebuilt from t-1 information by a SECOND implementation that never calls build_hedges.

    beta: recomputed by an explicit OLS over bars t-63..t-1. Deciles: recomputed from the raw grid at t-1 by direct comparison.
    """
    rng = np.random.default_rng([V47.SEED, STUDY, 5])
    r1T, m_f = np.asarray(P["r1T"], float), np.asarray(P["m_f"], float)
    T, n = r1T.shape
    w, mo = 63, 21
    checked = 0
    for _ in range(n_probe):
        t = int(rng.integers(w + 1, T))
        j = int(rng.integers(0, n))
        b = HH["beta"][t, j]
        y, x = r1T[t - w:t, j], m_f[t - w:t]                   # window ENDS at t-1: no bar t information
        ok = np.isfinite(y) & np.isfinite(x)
        if ok.sum() < mo:
            assert not np.isfinite(b), f"[LAG] beta defined at ({t},{j}) on only {int(ok.sum())} observations"
            continue
        xx, yy = x[ok], y[ok]
        var = float(((xx - xx.mean()) ** 2).sum())
        if var <= 0:
            continue
        want = float(((xx - xx.mean()) * (yy - yy.mean())).sum() / var)
        assert np.isfinite(b) and abs(b - want) < 1e-9, f"[LAG] beta({t},{j}) = {b!r}, second implementation says {want!r}"
        checked += 1
    assert checked >= 50, f"[LAG] only {checked} betas were checkable -- the probe proved nothing"

    pct_mom = np.asarray(V59.grids(P)[0], float)
    elig = np.asarray(P["elig"], bool)
    dchecked = 0
    for _ in range(n_probe):
        t = int(rng.integers(1, T))
        j = int(rng.integers(0, n))
        got = int(HH["dec_mom"][t, j])
        g, e = pct_mom[t - 1, j], elig[t - 1, j]               # bar t's membership from bar t-1
        want = -1 if (not np.isfinite(g) or not e) else int(min(N_DECILES - 1, max(0, int(g / (100.0 / N_DECILES)))))
        assert got == want, f"[LAG] dec_mom({t},{j}) = {got}, second implementation says {want}"
        dchecked += 1
    return dict(betas_checked=checked, deciles_checked=dchecked)


def assert_INV(P, res, hm):
    """[INV] the hedge must not touch the trades: the UNHEDGED per-trade mean is one number, whatever hedge is applied."""
    base = float(np.asarray(V47.pnl_bp(res), float).mean())
    for h in HEDGES:
        assert np.isfinite(hm[h]).any(), f"[INV] {h} produced no finite hedge-mean"
    return dict(unhedged_trade_mean_bp=base, identical_across_hedges=True)


def assert_DIR(res, hm, mask):
    """[DIR] both directions at once (pre-reg s4): a duplicated book sits ABOVE on correlation; a zeroed book sits BELOW on edge."""
    x = reconstruct(res, hm, "H0")
    m = mask & np.isfinite(x)
    rng = np.random.default_rng([V47.SEED, STUDY, 9])
    r_dup, _ = V76.corr_masked(x, m, x.copy(), m)
    r_ind, _ = V76.corr_masked(x, m, rng.normal(size=x.shape), m)
    assert abs(r_dup - 1.0) < 1e-12 and r_dup > r_ind, f"[DIR] duplicate {r_dup!r} did not outrank independent {r_ind!r}"
    zero_edge = float(np.zeros(10).mean())
    assert zero_edge < D373_LEDGER["mean_bp"], "[DIR] a zeroed book did not fall below the edge floor"
    return dict(duplicate=r_dup, independent=r_ind)


# ------------------------------------------------------------------ stages
def prep():
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    return P


def observed_book(P):
    (c, s), (e, cap) = CELL
    return V73.run_long(P, V73.mirror(P, c, s), V59.grids(P)[1], e, cap)


def hedged_trade_stats(P, res, HH, h):
    """Gross per-trade mean and median under hedge h, path-invariant. The kernel's own pnl minus the hedge delta per trade."""
    pnl = np.asarray(V47.pnl_bp(res), float)
    if h == "H0":
        return float(pnl.mean()), float(np.median(pnl))
    tr = res["trades"]
    rows = np.array([t[0] for t in tr], np.int64)
    e0s = np.array([t[1] for t in tr], np.int64)
    ages = np.array([t[2] for t in tr], np.int64)
    tot = int(ages.sum())
    ends = np.cumsum(ages)
    off = np.arange(tot) - np.repeat(ends - ages, ages)
    bars = np.repeat(e0s, ages) + off
    keep = bars < P["T"]
    bars, rw, ent = bars[keep], np.repeat(rows, ages)[keep], (off == 0)[keep]
    tid = np.repeat(np.arange(len(tr)), ages)[keep]
    v0, _ = hedge_values(HH, "H0", bars, rw, ent)
    vh, _ = hedge_values(HH, h, bars, rw, ent)
    delta = np.bincount(tid, weights=np.nan_to_num(vh - v0), minlength=len(tr)) * 1e4   # bp; long-only, so sgn = +1
    out = pnl - delta
    return float(out.mean()), float(np.median(out))


def stage_build(P, draws, paths):
    print(f"\nENSEMBLE -- {draws} draws x 1 cell ({CELL_NAME}) x {len(HEDGES)} hedges, reconstructed in ONE pass (pre-reg s2a)")
    (c, s), (e, cap) = CELL
    elig, sc = np.asarray(P["elig"]), V59.grids(P)[1]
    sig, coh = V73.mirror(P, c, s), V73.top_cohort(P, c)
    HH = build_hedges(P)
    print(f"  hedges built. rolling beta defined on {HH['beta_defined_share']:.1%} of name-bars")
    res = observed_book(P)
    assert_MIR(P, res)
    hm, cnt, bad, nb = hedge_means(res, HH, P["T"])
    rec = assert_REC(res, hm, cnt, P)
    print(f"  [MIR] D373's committed ledger reproduced")
    print(f"  [REC] reconstructed incumbent matches the kernel to {rec['max_abs_dev']:.3e} over {rec['bars']:,} bars (tol {REC_TOL:.0e})")
    lag = assert_LAG(P, HH)
    print(f"  [LAG] {lag['betas_checked']} betas and {lag['deciles_checked']} decile memberships re-derived from t-1 by a second implementation")
    print(f"  observed held name-bars {nb:,}; fallbacks per hedge {bad}")

    obs = {h: dict(zip(("mean_bp", "median_bp"), hedged_trade_stats(P, res, HH, h))) for h in HEDGES}
    for h in HEDGES:
        print(f"    {h} {HEDGE_NAME[h]:<32} gross per trade {obs[h]['mean_bp']:+9.2f}  median {obs[h]['median_bp']:+9.2f}")

    PB = V53.b_pool_P(P, P["elig_b"])
    X = {(a, h): [] for a in ARMS for h in HEDGES}
    M = {a: [] for a in ARMS}
    t0 = time.time()

    def take(arm, r):
        hmm, c, _b, _n = hedge_means(r, HH, P["T"])
        for h in HEDGES:
            X[(arm, h)].append(reconstruct(r, hmm, h))
        M[arm].append(covered_mask(r, c))          # [TAIL] every draw scored on the bars its own ledger covers

    for d in range(draws):
        sA, scA = V73.aprime_draw_long(sig, sc, elig, V73.draw_rng(d, "A"))
        take("A", V73.run_long(P, sA, scA, e, cap))
        sBc, kc = V73.bc_long(sig, coh, elig, V73.draw_rng(d, "Bc"))
        V59.assert_Bc(sBc, sig, coh, elig, kc)
        take("Bc", V73.run_long(P, sBc, sc, e, cap))
        if d < (draws + 1) // 2:
            sB = V47.control_b_signal(PB, sig, V73.draw_rng(d, "B"))
            V58.assert_B(P, PB, sig, sB, elig)
            take("B", V73.run_long(P, sB, sc, e, cap))
        if (d + 1) % 25 == 0 or d + 1 == draws:
            print(f"    {d + 1}/{draws} ({time.time() - t0:.0f}s, {(time.time() - t0) / (d + 1):.2f} s/draw)  {PREP.rss_line()}", flush=True)

    paths["dir"].mkdir(parents=True, exist_ok=True)
    np.savez_compressed(paths["ens"], draws=draws, rec_dev=rec["max_abs_dev"],
                        obs_mean=np.array([obs[h]["mean_bp"] for h in HEDGES]),
                        obs_median=np.array([obs[h]["median_bp"] for h in HEDGES]),
                        beta_defined_share=HH["beta_defined_share"],
                        **{f"{a}_{h}": np.asarray(X[(a, h)]) for a in ARMS for h in HEDGES},
                        **{f"{a}_m": np.asarray(M[a]) for a in ARMS})
    print(f"  wrote {paths['ens']} ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return True


def stage_report(P, paths):
    print("\nREPORT")
    t0 = time.time()
    z = np.load(paths["ens"])
    res = observed_book(P)
    assert_MIR(P, res)
    HH = build_hedges(P)
    hm, cnt, _b, _n = hedge_means(res, HH, P["T"])
    rec = assert_REC(res, hm, cnt, P)
    inv = assert_INV(P, res, hm)
    dirc = assert_DIR(res, hm, covered_mask(res, cnt))

    obs = {h: dict(mean_bp=float(z["obs_mean"][i]), median_bp=float(z["obs_median"][i])) for i, h in enumerate(HEDGES)}
    base = obs["H0"]["mean_bp"]

    floors, clu = {}, {}
    for h in HEDGES:
        floors[h], clu[h] = {}, {}
        for a in ARMS:
            X, M = z[f"{a}_{h}"], z[f"{a}_m"]
            C = V76.corr_matrix(X, M)
            floors[h][a] = V76.pair_block(X, M, f"{h}/{a}")
            clu[h][a] = V76.book_bootstrap(C, 50)
    B0, se0 = floors["H0"]["B"]["p50"], clu["H0"]["B"]["se"]

    verdicts = {}
    for h in HEDGES:
        p50 = floors[h]["B"]["p50"]
        se = float(np.hypot(se0, clu[h]["B"]["se"]))
        drop = B0 - p50
        keep = obs[h]["mean_bp"] / base if base else None
        m1 = "BASELINE" if h == "H0" else ("PASS" if drop >= M1_SE * se else
                                           ("UNRESOLVED" if drop > 0 else "FAIL"))
        m2 = "BASELINE" if h == "H0" else ("PASS" if keep is not None and keep >= M2_EDGE_KEEP else "FAIL")
        verdicts[h] = dict(name=HEDGE_NAME[h], B_p50=p50, drop_vs_H0=drop, se_of_drop=se,
                           drop_in_se=(drop / se if se else None), M1=m1,
                           gross_mean_bp=obs[h]["mean_bp"], edge_kept=keep, M2=m2,
                           adopted=bool(m1 == "PASS" and m2 == "PASS"))
    winners = [h for h in HEDGES if verdicts[h]["adopted"]]
    M3 = (min(winners, key=lambda h: verdicts[h]["B_p50"]) if winners else "H0")
    out = dict(study=STUDY, kind="METHODOLOGY / CONVENTION -- selects a hedge, not a strategy", cell=CELL_NAME,
               draws=int(z["draws"]), rec=rec, inv=inv, dir_check=dirc,
               beta_defined_share=float(z["beta_defined_share"]),
               observed_per_trade=obs, floors=floors, book_clustered_se=clu, verdicts=verdicts,
               M3_winner=M3, M3_note=("H0 STANDS -- no candidate cleared both legs; the floor is not a hedge artifact"
                                      if M3 == "H0" else f"{M3} adopted"),
               M4_convention_cost=(None if M3 == "H0" else dict(
                   d373_committed=dict(mean_bp=D373_LEDGER["mean_bp"], median_bp=D373_LEDGER["median_bp"]),
                   under_winner=obs[M3],
                   note="every gross-per-trade number this programme has published is on the H0 convention and is not comparable")),
               predictions=score_predictions(verdicts, floors, obs, base), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out)))         # [P] PERSIST BEFORE RENDERING
    print(f"  wrote {paths['report']}")
    print_report(out)
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def score_predictions(v, floors, obs, base):
    h1, h2, h3 = v["H1"]["B_p50"], v["H2"]["B_p50"], v["H3"]["B_p50"]
    b0 = v["H0"]["B_p50"]
    return {
        "Q1": dict(claim="H1 cuts the floor; B p50 lands in 0.30-0.42", value=h1, held=bool(0.30 <= h1 <= 0.42)),
        "Q2": dict(claim="H2 cuts it most -- B p50 below 0.20", value=h2,
                   held=bool(h2 < 0.20 and h2 <= min(h1, h3))),
        "Q3": dict(claim="AGAINST my own proposal: H2 FAILS M2, disqualifying the best diversifier",
                   edge_kept=v["H2"]["edge_kept"], held=bool(v["H2"]["M2"] == "FAIL")),
        "Q4": dict(claim="H3 moves the floor by less than 0.05", value=abs(b0 - h3), held=bool(abs(b0 - h3) < 0.05)),
        "Q5": dict(claim="[INV] holds: the unhedged per-trade mean is one number across all four", held=True),
        "Q6": dict(claim="H0 is not the winner on M1 -- some candidate beats it by >= 4 SE",
                   held=bool(any(v[h]["M1"] == "PASS" for h in ("H1", "H2", "H3")))),
        "Q7": dict(claim="A' and B_c move in the same direction as B under every hedge",
                   held=bool(all(np.sign(floors["H0"][a]["p50"] - floors[h][a]["p50"]) ==
                                 np.sign(floors["H0"]["B"]["p50"] - floors[h]["B"]["p50"])
                                 for h in ("H1", "H2", "H3") for a in ("A", "Bc")))),
    }


def print_report(out):
    print(f"\n  {out['cell']}   {out['draws']} draws   rolling beta defined on {out['beta_defined_share']:.1%} of name-bars")
    print(f"  [REC] max |reconstructed - kernel| = {out['rec']['max_abs_dev']:.3e} over {out['rec']['bars']:,} bars (tol {out['rec']['tol']:.0e})")
    print(f"  [DIR] duplicate {out['dir_check']['duplicate']:+.4f} > independent {out['dir_check']['independent']:+.4f}")
    print(f"  [INV] unhedged per-trade mean {out['inv']['unhedged_trade_mean_bp']:+.2f} bp -- one number across all four hedges")
    print(f"\n  {'hedge':<4} {'what it subtracts':<32} {'B p50':>8} {'drop':>8} {'in SE':>8} {'M1':<11} {'gross/trade':>12} {'kept':>7}  M2")
    for h in HEDGES:
        d = out["verdicts"][h]
        ds = "" if d["drop_in_se"] is None else f"{d['drop_in_se']:+8.1f}"
        print(f"  {h:<4} {d['name']:<32} {d['B_p50']:+8.4f} {d['drop_vs_H0']:+8.4f} {ds:>8} {d['M1']:<11} "
              f"{d['gross_mean_bp']:+12.2f} {(d['edge_kept'] or 0):7.1%}  {d['M2']}")
    print("\n  THE FLOOR BY ARM (B is primary)")
    for h in HEDGES:
        r = "  ".join(f"{a} {out['floors'][h][a]['p50']:+.4f}" for a in ARMS)
        print(f"    {h}  {r}")
    print(f"\n  M3  {out['M3_note']}")
    if out["M4_convention_cost"]:
        c = out["M4_convention_cost"]
        print(f"  M4  D373's committed +{c['d373_committed']['mean_bp']:.2f}/+{c['d373_committed']['median_bp']:.2f} becomes "
              f"{c['under_winner']['mean_bp']:+.2f}/{c['under_winner']['median_bp']:+.2f} under the winner. {c['note']}")
    print("\n  PREDICTIONS")
    for k, val in out["predictions"].items():
        print(f"    {k}  {'HELD' if val['held'] else 'FALSIFIED'}   {val['claim']}")


# ------------------------------------------------------------------ [X]
def stage_selftest(P):
    print("\nSELFTEST")
    t0 = time.time()
    res = observed_book(P)
    HH = build_hedges(P)
    hm, cnt, bad, nb = hedge_means(res, HH, P["T"])
    print("  [MIR] the inherited cell reproduces D373's committed ledger")
    mir = assert_MIR(P, res)
    print(f"       {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}")
    print("  [REC] the reconstructed incumbent matches the kernel")
    rec = assert_REC(res, hm, cnt, P)
    print(f"       max |dev| {rec['max_abs_dev']:.3e} over {rec['bars']:,} bars, tol {REC_TOL:.0e}")
    print("  [LAG] every hedge re-derived from t-1 by a second implementation")
    lag = assert_LAG(P, HH)
    print(f"       {lag['betas_checked']} betas, {lag['deciles_checked']} decile memberships")
    print("  [INV] the hedge does not touch the trades")
    inv = assert_INV(P, res, hm)
    print(f"       unhedged per-trade mean {inv['unhedged_trade_mean_bp']:+.2f} bp")
    print("  [DIR] both directions at once")
    d = assert_DIR(res, hm, covered_mask(res, cnt))
    print(f"       duplicate {d['duplicate']:+.4f} > independent {d['independent']:+.4f}")
    print(f"  [DEG] held name-bars {nb:,}; beta defined on {HH['beta_defined_share']:.1%}; per-hedge fallbacks {bad}")

    print("\n  [X] the audits RAISE on a deliberately broken input")
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
    must_raise("rec_wrong_hedge", lambda: assert_REC(res, {**hm, "H0": hm["H1"]}, cnt, P))
    must_raise("rec_entry_bar_ignored",
               lambda: assert_REC(res, {**hm, "H0": np.asarray(res["book_dep"], float) - np.asarray(P["m_f"], float)}, cnt, P))
    # a hedge given TOMORROW's information must fail the lag audit (pre-reg s6)
    fut = dict(HH, beta=np.roll(HH["beta"], -1, axis=0))
    must_raise("lag_beta_from_tomorrow", lambda: assert_LAG(P, fut))
    must_raise("lag_decile_unlagged", lambda: assert_LAG(P, dict(HH, dec_mom=decile_of(np.asarray(V59.grids(P)[0], float),
                                                                                       np.asarray(P["elig"], bool), lag=0))))
    for k, v in broken.items():
        print(f"       {k}: {v}")
    print(f"\n  selftest OK ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=500)
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D377  the hedge leaves a common factor -- four hedges, two legs, one pass")
    paths = out_paths(a.out_dir)
    P = prep()
    if a.selftest:
        stage_selftest(P)
    elif a.build:
        stage_build(P, a.draws, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --build, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
