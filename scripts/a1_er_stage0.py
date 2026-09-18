"""A1 STAGE 0 -- is path efficiency (Kaufman ER) a NEW input, or a volatility/momentum proxy?

    uv run python scripts/a1_er_stage0.py --selftest
    uv run python scripts/a1_er_stage0.py

DESCRIPTIVE. No cell is scored, no book is built, NO FORWARD RETURN IS READ. This
measures the correlation structure of the SCORES ONLY, in the universe the
strategy would trade, and it exists to kill a candidate cheaply if its premise is
false -- `d268_score_independence.py`'s charter, on the daily fixture and against
the six scores the candidate would have to be distinct from.

IT CARRIES NO DECISION NUMBER because it records nothing: it gates a candidate
rather than proposing one. Only the principal opens or closes an avenue (R15).

THE BAR WAS COMMITTED BEFORE THIS FILE EXISTED (R8). K1/K2/K3 below are quoted
verbatim from docs/research/the-signal-hunt-part2.md section 7, commit ed967bd,
which was committed before any line of this runner was written.

  K1  |rho| > 0.5 against rvol21, atr_norm or vol_ratio  -> ER is a VOLATILITY
      PROXY. Drop it; the programme already owns five volatility levels.
  K2  |rho| > 0.5 against mom_252_21 or trailing_return  -> ER is MOMENTUM
      re-expressed, D268's finding for the sixth time. Drop it.
  K3  ER_21/63/252 carry < 2.0 effective inputs among themselves -> one window,
      not three. Pick one and say which, rather than screening all three.

THE QUANTITY, over a window of w of the name's OWN bars:

    ER_w(t)  =  |c_t - c_{t-w}|  /  sum_{j=t-w+1..t} |c_j - c_{j-1}|

Every momentum score in the catalogue IS the numerator. ER divides it out by
construction, which is the entire reason to measure it before designing anything.

WHERE IT IS MEASURED, and this is D351's correction, not a detail. The
correlations are taken WITHIN EACH BAR over the ELIGIBLE names -- finT & keep_v2
after the hedge is defined -- because that is the set a cross-sectional selector
ranks. A correlation pooled over every priced bar would include the sub-$5,
sub-floor tail that D339 found to be every book's top trade and none of their
edge, and D347's control A was broken for exactly that reason.

TWO LENSES, never mixed (CLAUDE.md section 10, and D268's convention alongside
the operative one):
  * WITHIN-BAR, averaged over bars -- the OPERATIVE reading. Selection ranks
    names against each other on one day, so this is the correlation that decides
    whether ER picks different names than mom_252_21 does.
  * POOLED WITHIN-NAME -- D268's convention, reported so the number is
    comparable to its 2.87 effective inputs, and NOT used for the verdicts.

ONE CORRECTION TO THE PRE-REGISTERED GUARD, made here and not hidden. Section 7
demanded "a denominator floor ... a score whose tail is denominator noise selects
on denominator noise", by analogy with retrace_leg's [-2295, +1207] and fvg_dist's
829 ATRs. THAT ANALOGY IS WRONG AND ER CANNOT EXPLODE: the triangle inequality
gives |c_t - c_{t-w}| <= sum|c_j - c_{j-1}|, so ER is bounded in [0, 1] by
construction and is asserted to be. The real degenerate case is the OPPOSITE one
-- a frozen or halted tape where numerator and denominator are both a tick, so
0/0 or a ratio of two rounding errors. The guard implemented is therefore a
MINIMUM-TRAVEL floor (the window's total travel must exceed MIN_TRAVEL of price),
its cost is reported, and ER's extreme tail is named by symbol and bar rather
than described (`name-the-top-trade`, D322).

ASSERTIONS
  [B]  ER in [0, 1] on every finite cell -- the triangle inequality, checked not
       assumed.
  [W]  ER_w is finite only from the name's own (w+1)-th bar, counted in ITS OWN
       bars and never in grid columns (a name with an internal hole spans more
       columns than it has bars; gating on columns lets it act early).
  [E]  every cell entering a correlation satisfies the SAME eligibility mask
       (D351), and the share of finite ER cells that are ineligible is reported.
  [P]  the JSON is persisted BEFORE it is rendered (D371 computed its evidence
       and lost it to a KeyError in the print loop).
  [X]  the self-test RAISES on a deliberately broken ER. A self-test that cannot
       fail is worse than none.
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


def _repo_relative(path) -> str:
    """A path as the repository sees it, so provenance survives leaving this machine."""
    try:
        return Path(path).resolve().relative_to(REPO).as_posix()
    except ValueError:
        return Path(path).as_posix()
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "a1_er_stage0.json"

WINDOWS = (21, 63, 252)
ER_NAMES = tuple(f"ER_{w}" for w in WINDOWS)
VOL_REF = ("rvol21", "atr_norm", "vol_ratio")          # K1
MOM_REF = ("mom_252_21", "trailing_return")            # K2
OTHER_REF = ("max_ret_21",)
REFS = VOL_REF + MOM_REF + OTHER_REF

K_RHO = 0.50                    # K1 and K2's bar, committed in section 7
K3_MIN_EFFECTIVE = 2.0          # K3's bar, committed in section 7
MIN_NAMES = 50                  # a bar with fewer eligible names is not ranked (D373's `pct` convention)
MIN_TRAVEL = 1e-4               # the window's total travel must exceed 1 bp of price -- see the docstring


# ---------------------------------------------------------------- the quantity
def er_grid(closes_nT, live_nT, w):
    """ER_w as (n, T), NaN off the name's live bars and before its own (w+1)-th bar.

    Computed on each symbol's OWN bars via `np.flatnonzero(live[i])` and scattered
    back to those column indices -- `signals_ragged`'s rule. A contiguous slice
    would misalign every value after an internal hole by the hole's width.

    THE DENOMINATOR IS SUMMED DIRECTLY, NOT AS A DIFFERENCE OF CUMULATIVE SUMS.
    The first implementation used `cd[w:] - cd[:-w]`, which is FASTER and is a
    REORDERING OF A FLOAT SUM -- the thing CLAUDE.md forbids by name -- and [B]
    caught it on the fixture within one run: 329 of 11.86M cells scored above 1,
    breaking the triangle inequality by up to 3.2e-12. The mechanism is
    catastrophic cancellation, and it is worst exactly where the score is most
    interesting: LKM on 2019-01-29 travelled $0.0039 over 21 bars against an
    accumulated `cd` of $414.67, so the window was 0.0009% of the number it was
    differenced out of. Summed directly the same cell gives ER == 1.00000000000
    exactly. The fix is exactness, not a tolerance."""
    n, T = closes_nT.shape
    out = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live_nT[i])
        if at.size <= w:
            continue                                    # [W] not enough of ITS OWN bars
        c = closes_nT[i, at]
        if not np.isfinite(c).all():
            raise AssertionError(f"row {i}: non-finite close on a live bar")
        d = np.abs(np.diff(c))
        den = np.lib.stride_tricks.sliding_window_view(d, w).sum(axis=-1)
        num = np.abs(c[w:] - c[:-w])
        with np.errstate(invalid="ignore", divide="ignore"):
            er = np.where(den > np.maximum(MIN_TRAVEL * np.abs(c[w:]), 0.0), num / den, np.nan)
        out[i, at[w:]] = er
    return out


# ------------------------------------------------------------------ estimators
def rank01(v):
    """Ranks of a 1-D finite vector, scaled to [0, 1]. D268's `rankify`, same ties policy."""
    order = np.argsort(np.argsort(v))
    return order / (len(v) - 1) if len(v) > 1 else np.zeros_like(v, dtype=float)


def effective_inputs(Rm):
    """Three published estimators on one correlation matrix.

    participation ratio  (sum l)^2 / sum l^2      -- D268's
    Cheverud-Nyholt      1 + (M-1)(1 - Var(l)/M)  -- D321b's
    Li-Ji                sum over l of I(l>=1) + (l - floor(l))
    """
    lam = np.maximum(np.linalg.eigvalsh(Rm), 0.0)
    M = Rm.shape[0]
    pr = float(lam.sum() ** 2 / (lam ** 2).sum())
    cn = float(1.0 + (M - 1) * (1.0 - np.var(lam) / M))
    lj = float(np.sum((lam >= 1.0).astype(float) + (lam - np.floor(lam))))
    return {"participation_ratio": pr, "cheverud_nyholt": cn, "li_ji": lj,
            "eigenvalues": [float(v) for v in sorted(lam)[::-1]],
            "first_component_share": float(lam.max() / lam.sum())}


# ------------------------------------------------------------------- self-test
def selftest() -> int:
    print("A1 STAGE 0 SELF-TEST -- the quantity, its bound, and a break that must be caught\n")
    live = np.ones((3, 40), dtype=bool)
    c = np.empty((3, 40))
    c[0] = np.linspace(100.0, 140.0, 40)                              # straight line up  -> ER == 1
    c[1] = 100.0 + 2.0 * (np.arange(40) % 2)                          # pure zigzag, zero net -> ER == 0
    c[2] = 100.0                                                      # frozen tape -> guarded to NaN
    g = er_grid(c, live, 10)

    a = g[0, 10:]
    assert np.allclose(a, 1.0), f"[X] a monotone series must score ER == 1, got {a[:3]}"
    print(f"    monotone series      ER == 1.000  on all {a.size} defined bars")
    b = g[1, 10:]
    assert np.allclose(b, 0.0, atol=1e-12), f"[X] a zero-net zigzag must score ER == 0, got {b[:3]}"
    print(f"    zero-net zigzag      ER == 0.000  on all {b.size} defined bars")
    assert np.isnan(g[2, 10:]).all(), "[X] a frozen tape must be guarded to NaN, not divided"
    print(f"    frozen tape          NaN on all {g[2, 10:].size} bars -- MIN_TRAVEL floor holds")

    fin = np.isfinite(g)
    assert ((g[fin] >= 0.0) & (g[fin] <= 1.0)).all(), "[B] ER outside [0, 1]"
    print("    [B] every finite cell within [0, 1] -- the triangle inequality holds")

    # [D] THE VECTORISED DENOMINATOR EQUALS THE LOOP IT REPLACED, BIT FOR BIT, ON A
    #     TIE-HEAVY INPUT -- CLAUDE.md's guard, and the reason this function no longer
    #     differences cumulative sums. Ties (repeated closes, zero steps) are where a
    #     rewrite disagrees, and a penny name on a coarse tick is nothing but ties.
    rng = np.random.default_rng(20260907)
    tick = 0.01
    ties = np.round(100.0 + np.cumsum(rng.integers(-1, 2, 600)) * tick, 2)   # many zero steps
    ties[200:260] = ties[200]                                                # a frozen run
    lv = np.ones((1, ties.size), dtype=bool)
    for w_ in (5, 21, 63):
        got = er_grid(ties[None, :], lv, w_)[0]
        want = np.full(ties.size, np.nan)
        for j in range(w_, ties.size):
            den_ = np.abs(np.diff(ties[j - w_:j + 1])).sum()                 # the loop, term by term
            if den_ > max(MIN_TRAVEL * abs(ties[j]), 0.0):
                want[j] = abs(ties[j] - ties[j - w_]) / den_
        f_ = np.isfinite(got) | np.isfinite(want)
        assert np.array_equal(np.isfinite(got), np.isfinite(want)), f"[D] w={w_} finite masks differ"
        assert (got[np.isfinite(got)] == want[np.isfinite(want)]).all(), \
            f"[D] w={w_} vectorised denominator != the per-window loop"
        print(f"    [D] w={w_:<3d} vectorised == per-window loop EXACTLY on {int(f_.sum())} "
              f"tie-heavy bars ({int((np.diff(ties) == 0).sum())} zero steps in the input)")

    # [W] warm-up is counted in the name's OWN bars, not in grid columns
    holed = np.ones((1, 40), dtype=bool)
    holed[0, 5:15] = False                                            # a ten-column internal hole
    cc = np.full((1, 40), np.nan)
    cc[0, holed[0]] = np.linspace(100.0, 130.0, int(holed[0].sum()))
    gh = er_grid(cc, holed, 10)
    at = np.flatnonzero(holed[0])
    assert np.isnan(gh[0, at[:10]]).all() and np.isfinite(gh[0, at[10]]), \
        "[W] warm-up is being counted in columns, not in the name's own bars"
    print(f"    [W] holed name: first defined bar is its OWN 11th (column {at[10]}, not column 10)")

    # [X] THE BREAK THAT MUST BE CAUGHT -- a denominator one step too long understates
    #     travel's opposite: it OVERSTATES it, so a monotone series no longer scores 1.
    def broken(c1, live1, w):
        n, T = c1.shape
        out = np.full((n, T), np.nan)
        for i in range(n):
            at_ = np.flatnonzero(live1[i])
            if at_.size <= w + 1:
                continue
            cx = c1[i, at_]
            cd = np.concatenate([[0.0], np.cumsum(np.abs(np.diff(cx)))])
            den = cd[w + 1:] - cd[:-(w + 1)]                          # w+1 steps of travel
            num = np.abs(cx[w + 1:] - cx[1:-w])                       # w steps of displacement
            out[i, at_[w + 1:]] = np.where(den > 0, num / den, np.nan)
        return out

    gb = broken(c, live, 10)
    raised = False
    try:
        ab = gb[0, 11:]
        assert np.allclose(ab, 1.0), "mis-windowed ER must not score 1 on a monotone series"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- a mis-windowed ER passed the monotone check"
    print(f"    [X] mis-windowed ER scores {gb[0, 11]:.4f} on the monotone series and IS CAUGHT")
    print("\nSELF-TEST PASSED\n")
    return 0


# ------------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    selftest()
    t0 = time.time()
    PREP = _load("d348p", "d348_prep.py")
    P = PREP.prep(need_grids=False)
    print(f"  prep in {time.time() - t0:.0f}s (cache_hit={P.get('cache_hit')})", flush=True)

    n, T = P["n"], P["T"]
    live = P["live"]                       # (n, T)
    base = P["base"]                       # (n, T)  warm & live -- each score's own clock
    elig = P["elig"]                       # (T, n)  finT & keep_v2, after the hedge is defined
    CLOSE_Tn = np.asarray(P["CLOSE"])      # (T, n)
    closes = np.ascontiguousarray(CLOSE_Tn.T)
    symbols, dates = P["symbols"], P["dates"]
    print(f"  panel {n} names x {T} bars | eligible name-bars {int(elig.sum()):,} "
          f"({100 * elig.sum() / max(1, np.isfinite(CLOSE_Tn).sum()):.1f}% of priced)", flush=True)

    # ---- the ER grids ------------------------------------------------------
    ER, guard_rep = {}, {}
    for w in WINDOWS:
        t = time.time()
        g = er_grid(closes, live, w)
        fin = np.isfinite(g)
        assert ((g[fin] >= 0.0) & (g[fin] <= 1.0)).all(), "[B] ER outside [0, 1] on the fixture"
        ER[f"ER_{w}"] = g
        guard_rep[f"ER_{w}"] = {"finite_cells": int(fin.sum()),
                                "finite_share_of_live": float(fin.sum() / live.sum())}
        print(f"    ER_{w:<3d} built in {time.time() - t:.0f}s | finite on {int(fin.sum()):,} cells "
              f"({100 * fin.sum() / live.sum():.1f}% of live) | [B] within [0,1]", flush=True)

    # ---- the reference scores, on their own warm clocks ---------------------
    SC = {}
    for k in REFS:
        SC[k] = np.where(base, P["score"](k), np.nan)
    for k, g in ER.items():
        SC[k] = np.where(live, g, np.nan)
    names = list(ER_NAMES) + list(REFS)

    # ---- [E] eligibility: how much of ER lives OUTSIDE the traded universe ---
    eligT = elig.T                                                     # (n, T)
    e_rep = {}
    for k in ER_NAMES:
        fin = np.isfinite(SC[k])
        e_rep[k] = {"finite": int(fin.sum()), "finite_and_eligible": int((fin & eligT).sum()),
                    "share_ineligible": float(1.0 - (fin & eligT).sum() / max(1, fin.sum()))}
        print(f"    [E] {k}: {100 * e_rep[k]['share_ineligible']:.1f}% of its finite cells are "
              f"INELIGIBLE and are excluded from every correlation below", flush=True)

    # ---- the extreme tail, NAMED (D322) ------------------------------------
    tail = {}
    for k in ER_NAMES:
        v = np.where(eligT, SC[k], np.nan)
        fin = np.isfinite(v)
        idx = np.argsort(np.where(fin, v, -np.inf), axis=None)[::-1][:3]
        rows, cols = np.unravel_index(idx, v.shape)
        tail[k] = [{"symbol": symbols[int(r)], "date": dates[int(c)], "ER": float(v[r, c]),
                    "close": float(CLOSE_Tn[int(c), int(r)])} for r, c in zip(rows, cols)]
        top = tail[k][0]
        print(f"    top {k}: {top['symbol']} on {top['date']} at ER {top['ER']:.4f}, "
              f"close ${top['close']:.2f}", flush=True)

    # ---- LENS 1: within-bar Spearman, the operative one --------------------
    m = len(names)
    acc = np.zeros((m, m))
    per_bar = {f"{names[i]}|{names[j]}": [] for i in range(m) for j in range(i + 1, m)}
    bars = 0
    for t in range(T):
        sel = elig[t].copy()
        if sel.sum() < MIN_NAMES:
            continue
        cols = []
        ok = sel
        for k in names:
            ok = ok & np.isfinite(SC[k][:, t])
        if ok.sum() < MIN_NAMES:
            continue
        for k in names:
            cols.append(rank01(SC[k][ok, t]))
        Xb = np.vstack(cols)
        Rb = np.corrcoef(Xb)
        if not np.isfinite(Rb).all():
            continue
        acc += Rb
        bars += 1
        for i in range(m):
            for j in range(i + 1, m):
                per_bar[f"{names[i]}|{names[j]}"].append(Rb[i, j])
    assert bars > 0, "no bar carried MIN_NAMES eligible names with every score finite"
    Rm = acc / bars                       # a convex combination of correlation matrices: still PSD
    print(f"\n  LENS 1 -- within-bar Spearman over {bars:,} bars "
          f"(of {T:,}; a bar needs {MIN_NAMES} eligible names with all {m} scores finite)", flush=True)

    # ---- LENS 2: pooled within-name, D268's convention ---------------------
    cols = []
    for k in names:
        per = []
        for i in range(n):
            v = np.where(eligT[i], SC[k][i], np.nan)
            f = np.isfinite(v)
            r = np.full(v.shape, np.nan)
            if f.sum() > 1:
                r[f] = rank01(v[f])
            per.append(r)
        cols.append(np.concatenate(per))
    Xp = np.vstack(cols)
    okp = np.all(np.isfinite(Xp), axis=0)
    Rp = np.corrcoef(Xp[:, okp])
    print(f"  LENS 2 -- pooled within-name over {int(okp.sum()):,} eligible cells "
          f"(D268's convention; reported, not used for the verdicts)", flush=True)

    # ---- the verdicts ------------------------------------------------------
    idx = {k: i for i, k in enumerate(names)}
    rho = lambda a_, b_: float(Rm[idx[a_], idx[b_]])                  # noqa: E731

    k1 = [{"er": e, "ref": r, "rho": rho(e, r)} for e in ER_NAMES for r in VOL_REF
          if abs(rho(e, r)) > K_RHO]
    k2 = [{"er": e, "ref": r, "rho": rho(e, r)} for e in ER_NAMES for r in MOM_REF
          if abs(rho(e, r)) > K_RHO]
    sub = Rm[np.ix_([idx[e] for e in ER_NAMES], [idx[e] for e in ER_NAMES])]
    eff_er = effective_inputs(sub)
    eff_all = effective_inputs(Rm)
    k3_fail = eff_er["participation_ratio"] < K3_MIN_EFFECTIVE

    verdict = ("K1 FIRES -- ER is a volatility proxy" if k1 else
               "K2 FIRES -- ER is momentum re-expressed" if k2 else
               "ER CLEARS K1 AND K2 -- it is a new input on this universe")

    # ---- [P] PERSIST BEFORE RENDERING (D371) -------------------------------
    payload = {
        "purpose": "Stage 0 for candidate A1 (path efficiency). Descriptive; scores nothing; "
                   "reads no forward return. Gates a candidate, records none.",
        "bar_committed_in": "docs/research/the-signal-hunt-part2.md section 7, commit ed967bd, "
                            "before this runner existed (R8)",
        # REPO-RELATIVE (D544). The committed `data/a1_er_stage0.json` records this fixture
        # inside `.claude/worktrees/signal-hunt-part2/`, a git worktree that exists on no clone
        # and no longer on this machine -- provenance nobody can re-resolve, including its
        # author. That artifact is not rewritten: the unresolvable path is the only evidence
        # that the provenance is unresolvable. This stops the next run adding another.
        "fixture": _repo_relative(PREP.M.B.FIXTURE), "n": n, "T": T, "windows": list(WINDOWS),
        "min_travel_floor": MIN_TRAVEL, "min_names_per_bar": MIN_NAMES,
        "eligible_name_bars": int(elig.sum()),
        "er_guard": guard_rep, "eligibility": e_rep, "extreme_tail_named": tail,
        "names": names,
        "lens1_within_bar": {"bars": bars, "spearman_mean": Rm.tolist(),
                             "pair_p5_p95": {k: [float(np.percentile(v, 5)), float(np.percentile(v, 95))]
                                             for k, v in per_bar.items() if v}},
        "lens2_pooled_within_name": {"cells": int(okp.sum()), "spearman": Rp.tolist()},
        "effective_inputs_ER_only": eff_er, "effective_inputs_all": eff_all,
        "K_RHO": K_RHO, "K3_MIN_EFFECTIVE": K3_MIN_EFFECTIVE,
        "K1_volatility_violations": k1, "K2_momentum_violations": k2,
        "K3_fails": bool(k3_fail), "verdict": verdict,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render ------------------------------------------------------------
    print("\nWITHIN-BAR SPEARMAN, mean over bars (the operative lens)")
    print("           " + " ".join(f"{k[:9]:>10s}" for k in names))
    for i, k in enumerate(names):
        print(f"{k[:10]:>10s} " + " ".join(f"{Rm[i, j]:10.3f}" for j in range(m)))

    print("\nPOOLED WITHIN-NAME SPEARMAN (D268's convention)")
    print("           " + " ".join(f"{k[:9]:>10s}" for k in names))
    for i, k in enumerate(names):
        print(f"{k[:10]:>10s} " + " ".join(f"{Rp[i, j]:10.3f}" for j in range(m)))

    print(f"\nK1  volatility (|rho| > {K_RHO} vs {', '.join(VOL_REF)}):")
    for e in ER_NAMES:
        print("      " + f"{e:8s} " + "  ".join(f"{r} {rho(e, r):+.3f}" for r in VOL_REF))
    print(f"    -> {'FIRES: ' + str(k1) if k1 else 'CLEARS'}")
    print(f"\nK2  momentum (|rho| > {K_RHO} vs {', '.join(MOM_REF)}):")
    for e in ER_NAMES:
        print("      " + f"{e:8s} " + "  ".join(f"{r} {rho(e, r):+.3f}" for r in MOM_REF))
    print(f"    -> {'FIRES: ' + str(k2) if k2 else 'CLEARS'}")
    print(f"\nK3  effective inputs among ER_21/63/252 (bar {K3_MIN_EFFECTIVE}): "
          f"participation ratio {eff_er['participation_ratio']:.2f}, "
          f"Li-Ji {eff_er['li_ji']:.2f}, Cheverud-Nyholt {eff_er['cheverud_nyholt']:.2f}")
    print(f"    -> {'FAILS -- one window, not three' if k3_fail else 'CLEARS -- the windows are distinct'}")
    print(f"\n  all {m} scores together: {eff_all['participation_ratio']:.2f} effective inputs "
          f"(Li-Ji {eff_all['li_ji']:.2f}); first component {eff_all['first_component_share']:.1%}")
    print(f"\nVERDICT: {verdict}")
    print("\nThis measurement admits nothing. It reads no forward return, and clearing K1-K3 "
          "makes ER a distinct INPUT, not a signal (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
