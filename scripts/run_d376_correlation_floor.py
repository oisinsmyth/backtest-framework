"""D376 -- what do two books in this universe correlate at? Gate 1d's structural floor.

    uv run python scripts/run_d376_correlation_floor.py --selftest
    uv run python scripts/run_d376_correlation_floor.py --draws 500          builds the book ensemble, writes data/d376_series.npz
    uv run python scripts/run_d376_correlation_floor.py --report
    --out-dir DIR   (default data/ -- the smoke runs pass temp/... so nothing under data/ is touched)

Pre-registration: docs/decisions/D376-what-do-two-books-in-this-universe-correlate-at.md  (committed 6b6d905, BEFORE this file -- R8)

METHODOLOGY. Adjudicates a GATE, not a strategy. Nothing here can be passed by a book.

THE PROBLEM (D375 section 4). Gate 1d -- correlation to every existing book arm < 0.50 -- is defined in D289 and applied EXACTLY ONCE
in the programme's history: D373's H7, at rho 0.9346. Its only two passes on record are from the ETF universe. Nobody has measured what
two books in the SINGLE-NAME universe correlate at structurally, before any shared signal: same eligibility floor, same hedge against
the same floored market, same slot mechanics, same calendar, same 3,185 deployed bars.

THREE POPULATIONS, BRACKETING THE QUESTION rather than controlling each other (pre-reg s3). NO ARM IS LOAD-BEARING here -- D374 fixed
A' as load-bearing because it had one question; this has three, and each rule names the arm that settles it:
    B     two genuinely unrelated constructions       -- the floor gate 1d is actually about        -> L1
    A'    identical name set, independent timing      -- the CEILING of structural correlation
    B_c   two books both inside the winner cohort     -- the population D373 and D365 both live in  -> L2, L3

B_c is expected high on arithmetic: the daily top decile is ~100 names and each book holds ~50, so two independent draws should overlap
about half their held names by chance. If that alone carries a high correlation then D373's 0.935 is above the cohort's own baseline by
less than it appears, and L3 CORRECTS H7 the way D374 corrected H4. That possibility is pre-registered, not discovered.

DIRECTION: correlation is judged on the HIGH tail (p95). That is the OPPOSITE of D374's H4 and the same as H1-H3. [DIR] asserts it
against a duplicated book and an independent one, because D374 established that tail direction is the easiest thing here to invert.

[SER] IS THE ANCHOR: the observed series must reproduce H7's rho = 0.9346373668783634 to 1e-12 before any pair is computed. Without it
this study could correlate a different object than the gate is defined on and never know.

ASSERTIONS [MIR][SER][PAIR][MASK][DIR][DEG][X] -- pre-reg s5. [X] is the one that matters.
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


V73 = _load("d373r", "run_d373_winners_dip_long.py")
PREP, V59, V58, V50, V47, V53 = V73.PREP, V73.V59, V73.V58, V73.V50, V73.V47, V73.V53
clean = V50.clean
STUDY = 376
DATA = REPO / "data"

CELL_IX = V73.PRIMARY_IX
CELL = V73.CELLS[CELL_IX]
CELL_NAME = V73.CELL_NAME[CELL_IX]
D373_LEDGER = dict(trades=3932, mean_bp=160.55, median_bp=51.55)
H7_RHO = 0.9346373668783634                 # data/d373_winners_dip_long.json, committed 9162a64 -- the [SER] anchor
GATE_1D = 0.50                              # D289 section 92
MIN_COMMON_BARS = 500                       # pre-reg s5 [MASK]
UNRESOLVED_SE = 2.0                         # a margin within 2 SE of its bar is UNRESOLVED, never passed -- programme convention
DEGENERATE_MAX = 0.20                       # pre-reg s5 [DEG]
ARMS = ("A", "B", "Bc")


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, series=d / "d376_series.npz", report=d / "d376_correlation_floor.json")


# ------------------------------------------------------------------ the series, and it must be gate 1d's own
def book_series(res):
    """The deployed hedged bar series and its defined mask -- exactly the object D373's H7 correlated (`independence`)."""
    return np.asarray(res["book_dep_x"], float), np.asarray(res["mask_dep"], bool)


def observed_book(P):
    (c, s), (e, cap) = CELL
    return V73.run_long(P, V73.mirror(P, c, s), V59.grids(P)[1], e, cap)


def d365_aligned(P):
    """D365's mining series, aligned BY DATE as H7 aligns it. Returns (index into the panel, values)."""
    ix = {str(d): i for i, d in enumerate(P["dates"])}
    rows = [l.split(",") for l in (DATA / "d365_series_95_80.csv").read_text().strip().splitlines()]
    hdr = rows[0]
    cd, cn = hdr.index("date"), hdr.index("net_PUB_bp")
    pairs = [(ix[r[cd]], float(r[cn])) for r in rows[1:] if r[cd] in ix]
    return np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs], float)


def corr_masked(x, mx, y, my):
    """[MASK] correlate on the INTERSECTION of two defined masks. Returns (rho, common bars); rho is None when undefined."""
    k = mx & my & np.isfinite(x) & np.isfinite(y)
    n = int(k.sum())
    if n < 3:
        return None, n
    a, b = x[k], y[k]
    if a.std() == 0 or b.std() == 0:
        return None, n
    return float(np.corrcoef(a, b)[0, 1]), n


# ------------------------------------------------------------------ audits
def assert_MIR(P, res):
    pnl = np.asarray(V47.pnl_bp(res), float)
    got = dict(trades=len(res["trades"]), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)))
    assert got["trades"] == D373_LEDGER["trades"], f"[MIR] {got['trades']:,} trades != D373's {D373_LEDGER['trades']:,}"
    for k in ("mean_bp", "median_bp"):
        assert abs(got[k] - D373_LEDGER[k]) < 0.01, f"[MIR] {k} {got[k]:+.4f} != D373's {D373_LEDGER[k]:+.2f}"
    return got


def assert_SER(P, res):
    """[SER] THE ANCHOR. The observed series must reproduce H7's published rho, or this study is correlating the wrong object."""
    x, mx = book_series(res)
    idx, oth = d365_aligned(P)
    my = np.zeros_like(mx)
    my[idx] = True
    y = np.full_like(x, np.nan)
    y[idx] = oth
    rho, n = corr_masked(x, mx, y, my)
    assert rho is not None, "[SER] the observed series against D365 is undefined"
    assert abs(rho - H7_RHO) < 1e-12, f"[SER] rho {rho!r} != D373 H7's {H7_RHO!r} -- the series is not gate 1d's object"
    return dict(rho=rho, bars=n)


def assert_PAIR():
    """[PAIR] the routine returns +1 on a duplicate, -1 on a negation, ~0 on independent noise."""
    rng = np.random.default_rng([V47.SEED, STUDY, 7])
    x = rng.normal(size=4000)
    y = rng.normal(size=4000)
    m = np.ones(4000, bool)
    for want, b, tol in ((1.0, x, 1e-12), (-1.0, -x, 1e-12), (0.0, y, 0.05)):
        r, _n = corr_masked(x, m, b, m)
        assert r is not None and abs(r - want) < tol, f"[PAIR] expected {want}, got {r!r}"
    return True


def assert_MASK(x, mx, y, my):
    """[MASK] a pair below MIN_COMMON_BARS is refused rather than reported."""
    _r, n = corr_masked(x, mx, y, my)
    assert n >= MIN_COMMON_BARS, f"[MASK] a pair shares only {n} bars, below the {MIN_COMMON_BARS} floor"
    return n


def assert_DIR(P, res):
    """[DIR] correlation is judged on the HIGH tail. A duplicate of a book must score ABOVE an independent series against it.

    Checks the ORDER, which no p05-for-p95 typo can satisfy.
    """
    x, mx = book_series(res)
    rng = np.random.default_rng([V47.SEED, STUDY, 11])
    noise = rng.normal(size=x.shape)
    r_dup, _ = corr_masked(x, mx, x.copy(), mx)
    r_ind, _ = corr_masked(x, mx, noise, mx)
    assert abs(r_dup - 1.0) < 1e-12, f"[DIR] a duplicated book scored {r_dup!r}, not 1.0"
    assert abs(r_ind) < 0.10, f"[DIR] an independent series scored {r_ind!r} against the book"
    assert r_dup > r_ind, "[DIR] the duplicate did not outrank the independent series -- the test is inverted"
    return dict(duplicate=r_dup, independent=r_ind)


def assert_DEG(n_bad, n_all, what):
    if n_all and n_bad / n_all > DEGENERATE_MAX:
        return f"REFUSED: {n_bad:,} of {n_all:,} {what} degenerate ({n_bad / n_all:.1%} > {DEGENERATE_MAX:.0%})"
    return None


# ------------------------------------------------------------------ stages
def prep():
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    return P


def stage_build(P, draws, paths):
    """Build the book ensemble and persist every series. One process: at D374's ~0.7 s/draw this is under 10 minutes."""
    print(f"\nENSEMBLE -- {draws} draws x 1 cell ({CELL_NAME}). A' {draws}, B_c {draws}, B {(draws + 1) // 2}.")
    (c, s), (e, cap) = CELL
    elig, sc = np.asarray(P["elig"]), V59.grids(P)[1]
    sig, coh = V73.mirror(P, c, s), V73.top_cohort(P, c)
    res = observed_book(P)
    assert_MIR(P, res)
    ser = assert_SER(P, res)
    print(f"  [MIR] D373's committed ledger reproduced")
    print(f"  [SER] observed vs D365: rho {ser['rho']:.13f} over {ser['bars']:,} bars == H7's published value")
    ox, om = book_series(res)
    PB = V53.b_pool_P(P, P["elig_b"])
    X = {a: [] for a in ARMS}
    M = {a: [] for a in ARMS}
    t0 = time.time()
    for d in range(draws):
        sA, scA = V73.aprime_draw_long(sig, sc, elig, V73.draw_rng(d, "A"))
        x, m = book_series(V73.run_long(P, sA, scA, e, cap))
        X["A"].append(x)
        M["A"].append(m)
        sBc, kc = V73.bc_long(sig, coh, elig, V73.draw_rng(d, "Bc"))
        V59.assert_Bc(sBc, sig, coh, elig, kc)
        x, m = book_series(V73.run_long(P, sBc, sc, e, cap))
        X["Bc"].append(x)
        M["Bc"].append(m)
        if d < (draws + 1) // 2:
            sB = V47.control_b_signal(PB, sig, V73.draw_rng(d, "B"))
            V58.assert_B(P, PB, sig, sB, elig)
            x, m = book_series(V73.run_long(P, sB, sc, e, cap))
            X["B"].append(x)
            M["B"].append(m)
        if (d + 1) % 25 == 0 or d + 1 == draws:
            print(f"    {d + 1}/{draws} ({time.time() - t0:.0f}s, {(time.time() - t0) / (d + 1):.2f} s/draw)  {PREP.rss_line()}", flush=True)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    np.savez_compressed(paths["series"], obs_x=ox, obs_m=om, draws=draws,
                        **{f"{a}_x": np.asarray(X[a]) for a in ARMS}, **{f"{a}_m": np.asarray(M[a]) for a in ARMS})
    print(f"  wrote {paths['series']} ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return True


def pair_block(X, M, label, window=None):
    """Every unordered pair's correlation, on its own mask intersection. Degenerates counted, never absorbed.

    `window`, when given, intersects every pair with one COMMON mask. Added after the 12-draw smoke and BEFORE the full run, on a
    nuisance observation and not on any verdict: A' books deploy on ~4,122 bars while B and B_c books deploy on 3,185, so the three
    arms' primary blocks are measured over DIFFERENT windows and are not directly comparable to each other. The pre-registered
    primary (each pair on its own intersection, s2) is unchanged and still decides L1-L4; this is the matched-nuisance companion
    CLAUDE.md asks for -- a control must share the treatment's nuisance, not merely its count.
    """
    n = len(X)
    rs, bars, bad = [], [], 0
    for i in range(n):
        for j in range(i + 1, n):
            mi = M[i] if window is None else (M[i] & window)
            mj = M[j] if window is None else (M[j] & window)
            r, b = corr_masked(X[i], mi, X[j], mj)
            if r is None:
                bad += 1
                continue
            rs.append(r)
            bars.append(b)
    v = np.asarray(rs, float)
    npairs = n * (n - 1) // 2
    if v.size == 0:
        return dict(label=label, books=n, pairs=npairs, defined=0, degenerate=bad, degenerate_share=1.0)
    return dict(label=label, books=n, pairs=npairs, defined=int(v.size), degenerate=bad,
                degenerate_share=bad / max(1, npairs), judged_on="p95",
                p05=float(np.percentile(v, 5)), p50=float(np.percentile(v, 50)), p95=float(np.percentile(v, 95)),
                mean=float(v.mean()), min=float(v.min()), max=float(v.max()),
                common_bars_min=int(min(bars)), common_bars_median=float(np.median(bars)))


def corr_matrix(X, M):
    """The full book x book correlation matrix, each entry on its own mask intersection. NaN where undefined."""
    n = len(X)
    C = np.full((n, n), np.nan)
    for i in range(n):
        C[i, i] = 1.0
        for j in range(i + 1, n):
            r, _b = corr_masked(X[i], M[i], X[j], M[j])
            C[i, j] = C[j, i] = np.nan if r is None else r
    return C


def book_bootstrap(C, q=95, reps=400, seed_tag=31):
    """[CLU] the SE of a percentile, RESAMPLING BOOKS rather than pairs.

    124,750 pairs come from 500 independent books, so a bootstrap over pairs would treat one book's series as ~499 independent
    observations and understate the SE by roughly sqrt(n/2). This resamples BOOKS with replacement and recomputes the percentile
    over the pairs among them, dropping self-pairs (a book drawn twice would contribute rho = 1 and bias the tail upward).
    """
    n = C.shape[0]
    rng = np.random.default_rng([V47.SEED, STUDY, seed_tag, q])
    out = []
    for _ in range(reps):
        idx = rng.integers(0, n, size=n)
        sub = C[np.ix_(idx, idx)]
        iu = np.triu_indices(n, 1)
        same = idx[iu[0]] == idx[iu[1]]                       # self-pairs: the same book sampled twice
        v = sub[iu][~same]
        v = v[np.isfinite(v)]
        if v.size:
            out.append(np.percentile(v, q))
    a = np.asarray(out, float)
    return dict(reps=int(a.size), se=float(a.std(ddof=1)), p025=float(np.percentile(a, 2.5)), p975=float(np.percentile(a, 97.5)))


def vs_observed(ox, om, X, M):
    rs = [corr_masked(ox, om, X[i], M[i])[0] for i in range(len(X))]
    v = np.asarray([r for r in rs if r is not None], float)
    if v.size == 0:
        return dict(n=0)
    return dict(n=int(v.size), p05=float(np.percentile(v, 5)), p50=float(np.percentile(v, 50)),
                p95=float(np.percentile(v, 95)), mean=float(v.mean()), max=float(v.max()))


def stage_report(P, paths):
    print("\nREPORT")
    t0 = time.time()
    z = np.load(paths["series"])
    res = observed_book(P)
    assert_MIR(P, res)
    ser = assert_SER(P, res)
    assert_PAIR()
    dirc = assert_DIR(P, res)
    ox, om = z["obs_x"], z["obs_m"]

    pairs, pairs_cw, obs_vs, refusals, CM = {}, {}, {}, {}, {}
    for a in ARMS:
        X, M = z[f"{a}_x"], z[f"{a}_m"]
        assert_MASK(X[0], M[0], X[1], M[1])                       # [MASK] on a representative pair; pair_block carries the min
        CM[a] = corr_matrix(X, M)
        pairs[a] = pair_block(X, M, a)
        pairs_cw[a] = pair_block(X, M, a, window=om)              # secondary: all three arms on the OBSERVED book's window
        obs_vs[a] = vs_observed(ox, om, X, M)
        r = assert_DEG(pairs[a]["degenerate"], pairs[a]["pairs"], f"{a} pairs")
        if r:
            refusals[a] = r
        assert pairs[a]["common_bars_min"] >= MIN_COMMON_BARS, \
            f"[MASK] {a}'s thinnest pair shares {pairs[a]['common_bars_min']} bars, below {MIN_COMMON_BARS}"

    B, A, BC = pairs["B"], pairs["A"], pairs["Bc"]
    L1 = dict(question="is 0.50 reachable by two UNRELATED books here?", arm="B", bar=GATE_1D, p95=B.get("p95"),
              verdict=("UNRESOLVED" if "p95" not in B or "B" in refusals else
                       ("GATE SOUND -- two unrelated books sit under the bar" if B["p95"] < GATE_1D
                        else "GATE UNREACHABLE -- the bar is inside the structural noise; REPLACE")))
    L2 = dict(question="can anything inside the cohort ever pass?", arm="B_c", bar=GATE_1D, p05=BC.get("p05"),
              verdict=("UNRESOLVED" if "p05" not in BC else
                       ("COHORT-BLIND -- every pair inside this cohort fails 1d automatically; SCOPE the gate" if BC["p05"] > GATE_1D
                        else "the cohort does not force failure")))
    # [CLU] the SE of the percentiles that the verdicts turn on, clustered on BOOKS. L3's margin is small enough that a
    # pair-level bootstrap would be actively misleading, so this is computed before L3 is decided, not after.
    clu = {a: dict(p95=book_bootstrap(CM[a], 95), p50=book_bootstrap(CM[a], 50), p05=book_bootstrap(CM[a], 5)) for a in ARMS}
    m3 = H7_RHO - BC["p95"] if "p95" in BC else None
    se3 = clu["Bc"]["p95"]["se"]
    L3 = dict(question="does D373's H7 survive?", arm="B_c", h7=H7_RHO, p95=BC.get("p95"),
              margin=m3, se_p95_book_clustered=se3, margin_in_se=(None if m3 is None or not se3 else m3 / se3),
              verdict=("UNRESOLVED" if "p95" not in BC else
                       ("UNRESOLVED -- 0.935 is above the cohort p95 but within 2 book-clustered SE of it"
                        if (H7_RHO > BC["p95"] and se3 and m3 / se3 < UNRESOLVED_SE) else
                        ("H7 STANDS -- D373 is closer to D365 than two arbitrary cohort books are" if H7_RHO > BC["p95"]
                         else "H7 CORRECTED -- 0.935 is inside the cohort's own pair distribution"))))
    L4 = dict(replacement="1d': correlation at or below the p95 of the same-universe pair distribution on the study's own draws",
              applies=bool(L1["verdict"].startswith("GATE UNREACHABLE") or L2["verdict"].startswith("COHORT-BLIND")),
              thresholds_for_this_universe={a: pairs[a].get("p95") for a in ARMS})
    preds = score_predictions(pairs, obs_vs)
    out = dict(study=STUDY, kind="METHODOLOGY -- adjudicates a gate, not a strategy", cell=CELL_NAME,
               ser=ser, dir_check=dirc, gate_1d=GATE_1D, draws=int(z["draws"]),
               pairs=pairs, pairs_common_window=pairs_cw, observed_vs_arm=obs_vs, refusals=refusals,
               common_window_note=("SECONDARY, added after the 12-draw smoke on a NUISANCE observation and before the full run: A' "
                                   "books deploy on more bars than B/B_c books, so the primary blocks are measured over different "
                                   "windows and are not directly comparable arm-to-arm. The pre-registered primary still decides "
                                   "L1-L4; this block re-runs every pair on the observed book's own mask."),
               book_clustered_se=clu, L1=L1, L2=L2, L3=L3, L4=L4, predictions=preds, rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out)))            # [P] PERSIST BEFORE RENDERING
    print(f"  wrote {paths['report']}")
    print_report(out)
    print(f"  ({time.time() - t0:.0f}s)  {PREP.rss_line()}")
    return out


def score_predictions(pairs, obs_vs):
    A, B, BC = pairs["A"], pairs["B"], pairs["Bc"]
    a50, b50, bc50 = A.get("p50"), B.get("p50"), BC.get("p50")
    ov = obs_vs["A"].get("p50")
    return {
        "Q1": dict(claim="A' median pair correlation is 0.10-0.35", value=a50,
                   held=(None if a50 is None else bool(0.10 <= a50 <= 0.35))),
        "Q2": dict(claim="B_c median exceeds A' median; point estimate 0.45-0.75", values=dict(A=a50, Bc=bc50),
                   held=(None if (a50 is None or bc50 is None) else bool(bc50 > a50)),
                   point_estimate_held=(None if bc50 is None else bool(0.45 <= bc50 <= 0.75))),
        "Q3": dict(claim="B has the lowest median of the three", values=dict(A=a50, B=b50, Bc=bc50),
                   held=(None if any(v is None for v in (a50, b50, bc50)) else bool(b50 < a50 and b50 < bc50))),
        "Q4": dict(claim="gate 1d is SOUND under L1: B's p95 is below 0.50", value=B.get("p95"),
                   held=(None if "p95" not in B else bool(B["p95"] < GATE_1D))),
        "Q5": dict(claim="D373's H7 SURVIVES under L3: 0.9346 is above B_c's p95", value=BC.get("p95"),
                   held=(None if "p95" not in BC else bool(H7_RHO > BC["p95"]))),
        "Q6": dict(claim="every pair's mask intersection is >= 99% of 3,185 bars",
                   values={a: pairs[a].get("common_bars_min") for a in ARMS},
                   held=bool(all((pairs[a].get("common_bars_min") or 0) >= 0.99 * 3185 for a in ARMS))),
        "Q7": dict(claim="AGAINST myself: the observed book's median corr to A' draws is within 0.05 of A''s own pair median",
                   values=dict(observed_vs_A=ov, A_pair=a50),
                   held=(None if (ov is None or a50 is None) else bool(abs(ov - a50) <= 0.05))),
    }


def print_report(out):
    print(f"\n  {out['cell']}   {out['draws']} draws   gate 1d bar {out['gate_1d']:.2f}")
    print(f"  [SER] observed vs D365 rho {out['ser']['rho']:.13f} over {out['ser']['bars']:,} bars == D373 H7")
    print(f"  [DIR] duplicate {out['dir_check']['duplicate']:+.4f} > independent {out['dir_check']['independent']:+.4f}")
    if out["refusals"]:
        print(f"  [DEG] {out['refusals']}")
    print("\n  PAIRWISE CORRELATION BETWEEN TWO BOOKS  (judged on the HIGH tail -- p95)")
    for a in ARMS:
        b = out["pairs"][a]
        if not b.get("defined"):
            print(f"    {a:<3} no defined pairs")
            continue
        print(f"    {a:<3} {b['books']:>4} books, {b['defined']:>7,} pairs   p05 {b['p05']:+.4f}  p50 {b['p50']:+.4f}  "
              f"p95 {b['p95']:+.4f}  max {b['max']:+.4f}   common bars min {b['common_bars_min']:,}   degenerate {b['degenerate']}")
    print("\n  THE SAME PAIRS ON ONE COMMON WINDOW (the observed book's mask) -- SECONDARY, see note")
    for a in ARMS:
        b = out["pairs_common_window"][a]
        if b.get("defined"):
            print(f"    {a:<3} {b['defined']:>7,} pairs   p05 {b['p05']:+.4f}  p50 {b['p50']:+.4f}  p95 {b['p95']:+.4f}  "
                  f"max {b['max']:+.4f}   bars {b['common_bars_min']:,}")
    print("\n  THE OBSERVED BOOK vs each arm's draws")
    for a in ARMS:
        v = out["observed_vs_arm"][a]
        if v.get("n"):
            print(f"    {a:<3} n {v['n']:>4}  p50 {v['p50']:+.4f}  p95 {v['p95']:+.4f}  max {v['max']:+.4f}")
    print("\n  DECISIONS")
    for a in ARMS:
        c = out["book_clustered_se"][a]
        print(f"    [CLU] {a:<3} se(p05) {c['p05']['se']:.4f}   se(p50) {c['p50']['se']:.4f}   se(p95) {c['p95']['se']:.4f}"
              "   -- resampling BOOKS, not pairs")
    for k in ("L1", "L2", "L3"):
        print(f"    {k}  {out[k]['verdict']}")
    l3 = out["L3"]
    if l3.get("margin") is not None:
        print(f"         H7 {l3['h7']:.4f} vs B_c p95 {l3['p95']:.4f}   margin {l3['margin']:+.4f}  "
              f"({l3['margin_in_se']:+.2f} book-clustered SE)")
    print(f"    L4  replacement applies: {out['L4']['applies']}   p95 by arm {out['L4']['thresholds_for_this_universe']}")
    print("\n  PREDICTIONS")
    for k, v in out["predictions"].items():
        tag = "HELD" if v["held"] else ("FALSIFIED" if v["held"] is not None else "UNRESOLVED")
        sub = [f"{kk} {vv}" for kk, vv in v.items() if kk.endswith("_held") and kk != "held"]
        print(f"    {k}  {tag}   {v['claim']}" + (f"   [{'; '.join(sub)}]" if sub else ""))


# ------------------------------------------------------------------ [X]
def stage_selftest(P):
    print("\nSELFTEST")
    t0 = time.time()
    res = observed_book(P)
    print("  [MIR] the inherited cell reproduces D373's committed ledger")
    mir = assert_MIR(P, res)
    print(f"       {mir['trades']:,} trades  mean {mir['mean_bp']:+.2f}  median {mir['median_bp']:+.2f}")
    print("  [SER] the observed series reproduces D373 H7's published rho")
    ser = assert_SER(P, res)
    print(f"       rho {ser['rho']:.13f} over {ser['bars']:,} bars")
    print("  [PAIR] +1 on a duplicate, -1 on a negation, ~0 on independent noise")
    assert_PAIR()
    print("  [DIR] correlation is judged on the HIGH tail")
    d = assert_DIR(P, res)
    print(f"       duplicate {d['duplicate']:+.4f} > independent {d['independent']:+.4f}")

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

    x, mx = book_series(res)
    must_raise("mir_truncated_ledger",
               lambda: assert_MIR(P, {**res, "trades": res["trades"][:10]}))
    # NOT a rescale: correlation is scale- and location-invariant, so `* 1.5 + 1.0` legitimately leaves rho unchanged and [SER]
    # legitimately does not fire. The break worth guarding is MISALIGNMENT -- H7's own docstring stresses that alignment is by DATE
    # and never by index, and a one-bar slip is the way that goes wrong in practice.
    must_raise("ser_lag_one_misalignment",
               lambda: assert_SER(P, {**res, "book_dep_x": np.roll(np.asarray(res["book_dep_x"], float), 1)}))
    must_raise("ser_scrambled_series",
               lambda: assert_SER(P, {**res, "book_dep_x": np.random.default_rng([V47.SEED, STUDY, 23]).permutation(
                   np.asarray(res["book_dep_x"], float))}))
    must_raise("mask_too_few_common_bars",
               lambda: assert_MASK(x, mx, x, np.concatenate([np.ones(400, bool), np.zeros(mx.size - 400, bool)])))

    def dir_inverted():
        """The inversion worth catching is a routine that ranks an INDEPENDENT series above a DUPLICATE -- i.e. p05 read for p95."""
        rng = np.random.default_rng([V47.SEED, STUDY, 17])
        noise = rng.normal(size=x.shape)
        r_dup, _ = corr_masked(x, mx, x.copy(), mx)
        r_ind, _ = corr_masked(x, mx, noise, mx)
        assert r_ind > r_dup, "[DIR] inverted"
    must_raise("dir_inverted_ordering", dir_inverted)
    for k, v in broken.items():
        print(f"       {k}: {v}")

    print("\n  [DEG] the guard refuses rather than reporting")
    r = assert_DEG(30, 100, "pairs")
    assert r and "REFUSED" in r, f"[DEG] a 30% degenerate arm was not refused: {r!r}"
    print(f"       {r}")
    assert assert_DEG(5, 100, "pairs") is None, "[DEG] a 5% degenerate arm was wrongly refused"
    print("       5% degenerate: reported, not refused")
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
    print("D376  what do two books in this universe correlate at? gate 1d's structural floor")
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
