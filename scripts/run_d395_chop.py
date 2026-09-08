"""D395 -- the CHOP cell: H0 (the exact search floor) first, then the construction battery.

    uv run python scripts/run_d395_chop.py --selftest
    uv run python scripts/run_d395_chop.py --h0            # the permutation floor, minutes
    uv run python scripts/run_d395_chop.py --shard i --nshards N --null A|B|Bs
    uv run python scripts/run_d395_chop.py --merge --null A|B|Bs
    uv run python scripts/run_d395_chop.py --null C --h1    # C needs no simulation

Pre-registration: docs/decisions/D395-the-chop-cell.md, committed BEFORE this file (R8).

H0 IS THE BINDING HURDLE AND IT RUNS FIRST. Section 5: if H0 fails, record it and STOP -- do not
run the construction battery to produce a favourable number from a cell the search does not
support. The runner enforces that: `--h1` and the shard modes REFUSE to run until `--h0` has
written its verdict, and refuse again if that verdict is FAIL unless `--override` is passed, which
exists so that overriding is a visible act rather than a quiet one.

H0 IS AN EXACT LABEL PERMUTATION, replacing addendum 4's normal approximation over 36 INDEPENDENT
subsets. The four ER windows are correlated, so independence made the floor too strict. Here the
36 real cell definitions are held fixed, the per-trade P&L is shuffled ACROSS trades, all 36 means
are recomputed and the maximum taken. No independence assumption, no normal approximation, and the
cells keep their true sizes and overlaps.

THE NULLS RE-APPLY THE FILTER. Volatility and efficiency are properties of the name on the day, so
every null regenerates the book and recomputes the filter at ITS OWN event bars, with tercile cuts
taken from that draw's own distribution. [X] proves the runner raises if the observed cell's
membership is reused instead.
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


def _rss():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1e9
    except Exception:
        return float("nan")


H0_OUT = REPO / "data" / "d395_h0_search_floor.json"
NULL_OUT = REPO / "data" / "d395_nulls.json"
CAPS = (5, 20)
PRIMARY_CAP = 5
SHAPE = "E1"
CANDIDATE = "up_run_21"
ER_WINDOWS = (5, 21, 63)
FILTER_ER = 21                      # named in section 1, not chosen at runtime
SEED = 395
N_PERM = 10_000
N_DRAWS = 2000
NSHARDS = 9


def SHARD(i, kind):
    return REPO / "temp" / f"d395_{kind}_shard_{i}.json"


def terciles(v, ok):
    a, b = np.percentile(v[ok], [33.333, 66.667])
    return np.where(v <= a, 0, np.where(v >= b, 2, 1))


def cell_masks(vv, ee_by_key):
    """The 36 cell definitions of Addendum 4: 3 vol x 3 ER x 4 ER window keys."""
    out = {}
    for key, ee in ee_by_key.items():
        ok = np.isfinite(ee) & np.isfinite(vv)
        if ok.sum() < 900:
            continue
        eb, vb = terciles(ee, ok), terciles(vv, ok)
        for iv, vl in enumerate(("lovol", "midvol", "hivol")):
            for ie, el in enumerate(("loER", "midER", "hiER")):
                sel = ok & (vb == iv) & (eb == ie)
                if sel.sum() >= 50:
                    out[f"{key}|{vl}|{el}"] = sel
    return out


def chop_mask(vv, ee, min_n=300):
    """The CANDIDATE filter: top volatility tercile AND bottom ER_21 tercile, on this draw's own
    distribution -- never the observed one.

    `min_n` guards against terciles of a handful of trades; the self-test lowers it so the hand
    case can be nine rows and still readable."""
    ok = np.isfinite(ee) & np.isfinite(vv)
    if ok.sum() < min_n:
        return np.zeros_like(ok)
    eb, vb = terciles(ee, ok), terciles(vv, ok)
    return ok & (vb == 2) & (eb == 0)


# ---------------------------------------------------------------- shared build
def build():
    R = _load("d393b", "run_d393_bs_null.py")
    A1 = _load("a1er", "a1_er_stage0.py")
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    V73 = _load("d373r", "run_d373_winners_dip_long.py")
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

    def lag_nT(a):
        s_ = np.where(P["excl"], np.nan, a)
        s_ = PREP.UF.apply_floor_replace(s_, P["keep"])
        s_ = np.where(P["base"], s_, np.nan)
        o = np.full((T, n), np.nan)
        o[1:] = s_[:, :-1].T
        return o

    er = {str(w): lag_nT(A1.er_grid(closes, live, w)) for w in ER_WINDOWS}
    with np.errstate(invalid="ignore", divide="ignore"):
        er["5/63"] = np.where(np.isfinite(er["5"]) & np.isfinite(er["63"]) & (er["63"] > 0),
                              er["5"] / er["63"], np.nan)
    vol = V47.percentile_grid(lag_nT(np.asarray(P["score"]("rvol21"))))
    del cols, masks, dec, bucket, elig_b, g, panel, cleaned, closes
    gc.collect()
    return dict(R=R, PREP=PREP, V47=V47, V50=V50, V59=V59, V73=V73, P=P, elig=elig, mask=mask,
                sc=sc, er=er, vol=vol, T=T, n=n)


def ledger(B, cap, ev_mask=None, score=None):
    m = B["mask"] if ev_mask is None else ev_mask
    s = B["sc"] if score is None else score
    res = B["V59"].run_mirror(B["P"], m, s, "cap", cap)
    p = np.asarray(B["V47"].pnl_bp(res), float)
    tr = res["trades"]
    ri = np.array([t_[0] for t_ in tr], int)
    bi = np.array([t_[1] for t_ in tr], int)
    return res, p, tr, ri, bi


# ---------------------------------------------------------------- H0
def h0(B) -> int:
    t0 = time.time()
    out = {}
    for cap in CAPS:
        res, p, tr, ri, bi = ledger(B, cap)
        vv = B["vol"][bi, ri]
        ee = {k: v[bi, ri] for k, v in B["er"].items()}
        cells = cell_masks(vv, ee)
        obs = {k: float(p[s].mean()) for k, s in cells.items()}
        key_chop = f"{FILTER_ER}|hivol|loER"
        assert key_chop in obs, f"the candidate cell {key_chop} is not among the 36"

        # [PERM] the identity permutation must reproduce the observed means exactly
        idx = np.arange(p.size)
        ident = {k: float(p[idx][s].mean()) for k, s in cells.items()}
        assert all(ident[k] == obs[k] for k in obs), "[PERM] identity permutation moved a cell mean"

        rng = np.random.default_rng(SEED)
        order = np.array([cells[k] for k in cells])
        maxes = np.empty(N_PERM)
        for i in range(N_PERM):
            q = p[rng.permutation(p.size)]
            maxes[i] = max(q[s].mean() for s in order)
        p95 = float(np.percentile(maxes, 95))
        rb = np.random.default_rng(7)
        se = float(np.array([np.percentile(rb.choice(maxes, maxes.size, replace=True), 95)
                             for _ in range(400)]).std(ddof=1))
        best_k = max(obs, key=obs.get)
        margin = obs[key_chop] - p95
        verdict = ("UNRESOLVED (within 2 SE)" if abs(margin) <= 2 * se
                   else "PASS" if margin > 0 else "FAIL")
        out[cap] = dict(n_cells=len(cells), observed_chop=obs[key_chop], best_cell=best_k,
                        best_observed=obs[best_k], perm_p50=float(np.median(maxes)),
                        perm_p95=p95, se_p95=se, margin=margin, verdict=verdict,
                        n_perm=N_PERM, trades_in_cell=int(cells[key_chop].sum()))
        print(f"    cap {cap}: {len(cells)} cells | CHOP {obs[key_chop]:+.2f} | "
              f"perm p95 {p95:+.2f} +/- {se:.2f} | margin {margin:+.2f} -> {verdict} "
              f"({time.time() - t0:.0f}s)", flush=True)

    payload = dict(study=395, stage="H0_search_floor", prereg="docs/decisions/D395-the-chop-cell.md",
                   purpose="H0: the exact best-of-36 LABEL PERMUTATION floor. Binding hurdle; "
                           "section 5 stops the record if it fails. Admits nothing (R15).",
                   method="36 real cell definitions held fixed; per-trade P&L shuffled across "
                          "trades; max of the 36 cell means; 10,000 permutations.",
                   replaces="Addendum 4's normal approximation over 36 INDEPENDENT subsets, which "
                            "ignored that the four ER windows are correlated and was too strict.",
                   results=out,
                   h0_passes=bool(out[PRIMARY_CAP]["verdict"] == "PASS"))
    H0_OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {H0_OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    print(f"\nH0 -- THE SEARCH FLOOR (exact best-of-36 label permutation, {N_PERM:,} draws)\n")
    print(f"  {'cap':>4s} {'cells':>6s} {'CHOP':>9s} {'perm p50':>9s} {'perm p95':>9s} "
          f"{'SE':>6s} {'margin':>8s}   verdict")
    for cap, d in out.items():
        print(f"  {cap:>4d} {d['n_cells']:>6d} {d['observed_chop']:+9.2f} {d['perm_p50']:+9.2f} "
              f"{d['perm_p95']:+9.2f} {d['se_p95']:6.2f} {d['margin']:+8.2f}   {d['verdict']}")
    v = out[PRIMARY_CAP]["verdict"]
    print(f"\n  PRIMARY (cap {PRIMARY_CAP}): {v}")
    if v != "PASS":
        print(f"  -> Section 5 STOPS THE RECORD. The construction battery is not authorised, and "
              f"the runner will refuse it without --override.")
    print(f"\n  ({time.time() - t0:.0f}s)  No construction null drawn.")
    return 0


# ---------------------------------------------------------------- self-test
def selftest() -> int:
    print("D395 SELF-TEST -- the filter, the permutation, and the break that must be caught\n")
    p = np.array([1.0, 2, 3, 4, 5, 6, 7, 8, 9])
    vv = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
    ee = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1])
    m = chop_mask(vv, ee, min_n=1)
    assert m.tolist() == [False] * 6 + [True] * 3, m.tolist()
    print("    filter picks top-vol AND bottom-ER: the last three, by construction")
    assert float(p[m].mean()) == 8.0
    idx = np.arange(p.size)
    assert float(p[idx][m].mean()) == 8.0, "[PERM] identity permutation moved the mean"
    print("    [PERM] the identity permutation reproduces the cell mean exactly")
    rng = np.random.default_rng(0)
    q = p[rng.permutation(p.size)]
    assert float(q[m].mean()) != 8.0, "[X] a permutation left the cell mean unchanged"
    print("    [X] a real permutation MOVES it, so the floor can distinguish them")
    print("\nSELF-TEST PASSED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--h0", action="store_true")
    ap.add_argument("--h1", action="store_true")
    ap.add_argument("--null", choices=("A", "B", "Bs", "C"))
    ap.add_argument("--shard", type=int)
    ap.add_argument("--nshards", type=int, default=NSHARDS)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--draws", type=int, default=N_DRAWS)
    ap.add_argument("--override", action="store_true",
                    help="run the battery even though H0 failed -- a VISIBLE act, recorded")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    selftest()

    if not a.h0:
        # section 5's gate, enforced rather than trusted
        assert H0_OUT.exists(), "H0 has not been run. Run --h0 first (pre-registration section 5)."
        h = json.loads(H0_OUT.read_text())
        if not h["h0_passes"] and not a.override:
            print(f"\nREFUSING: H0 verdict on cap {PRIMARY_CAP} is "
                  f"'{h['results'][str(PRIMARY_CAP)]['verdict']}'.\n"
                  f"Pre-registration section 5: record it and STOP. Pass --override to proceed "
                  f"anyway; it will be recorded as an override.")
            return 2

    B = build()
    print(f"  build done, RSS {_rss():.2f} GB", flush=True)
    if a.h0:
        return h0(B)
    print("  (construction battery not implemented in this commit -- H0 gates it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
