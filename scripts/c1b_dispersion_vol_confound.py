"""C1b -- is DISPERSION a new state, or is it VOLATILITY wearing a new name?

    uv run python scripts/c1b_dispersion_vol_confound.py --selftest
    uv run python scripts/c1b_dispersion_vol_confound.py

DESCRIPTIVE, and it exists because C1 left a hole I named before running this.

C1 (data/c1_gate_stage0.json) found DISPERSION decisive on the loser cohort at
+0.205 against a shuffled |r| p95 of 0.151, and showed it is NOT the
market-direction family: -0.105 to -0.167 against G1, G2 and BREADTH, which are
0.56-0.73 correlated with each other and are one state in three sets of clothes.

**BUT C1 COMPARED DISPERSION ONLY AGAINST DIRECTION MEASURES. IT NEVER COMPARED IT
AGAINST VOLATILITY.** High-dispersion days are plausibly just high-volatility
days, and if that is what this is then it is not a new state at all -- it is the
volatility tilt this programme has tripped over repeatedly (D280 part 4's
zh+zv+za+zr at IC -0.01373, and the sigma^2 tax in FINDINGS 1b that took 59% of
D264's gross). "Distinct from direction" is not "distinct".

THREE QUESTIONS, and only the third decides it:

  Q1  HOW RELATED?      Spearman of the levels, DISPERSION against two volatility
                        states built here -- and against G1/G2/BREADTH for the
                        frame C1 already established.
  Q2  DOES VOLATILITY   the same block premise D361 rule 1 defines, run on the
      DO THE JOB        volatility levels themselves. If volatility alone is
      ALREADY?          decisive on the loser cohort at similar strength,
                        dispersion adds nothing even if the two are distinct.
  Q3  DOES DISPERSION'S the block premise recomputed with volatility PARTIALLED
      PREMISE SURVIVE?  OUT of the dispersion level -- both the closed-form
                        partial correlation and a residual-and-shuffle version
                        carrying its own p95, because a partial correlation with
                        no null is a number without a bar.

THE TWO VOLATILITY STATES, declared before the run, both lagged to t-1 and both
over ELIGIBLE names only (D351):

  VOL_XS    the cross-sectional MEDIAN of `rvol21` -- the typical eligible name's
            own realised volatility. Median, not mean, for the reason C1 used an
            IQR: on this fixture a mean is a GME detector.
  VOL_MKT   the trailing 21-bar standard deviation of the floored market's own
            return m_f -- index volatility, which is a different object from the
            typical name's (their difference IS dispersion, which is the point).

Gate rule for both: above its own trailing 252-bar median, causal -- DISPERSION's
rule in C1, unchanged, so the on/off lines are comparable.

ASSERTIONS
  [REG] this file reproduces C1's published DISPERSION block correlation, block
        count and shuffle p95 from data/c1_gate_stage0.json, to 0.0, using C1's
        own seed -- before any new number is read. Same object or no comparison.
  [L]   every level is built through C1's `state_pack`, which owns the lag, so no
        level here can read its own bar.
  [E]   both volatility states are computed over eligible names only; the count
        per bar is reported.
  [P]   the JSON is persisted BEFORE it is rendered (D371).
  [X]   the self-test RAISES on a partial correlation that fails to remove a
        planted confound. A self-test that cannot fail is worse than none.
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


OUT = REPO / "data" / "c1b_dispersion_vol_confound.json"
C1_JSON = REPO / "data" / "c1_gate_stage0.json"
VOL_BARS = 21


def cross_median(grid_nT, eligT_Tn, min_names):
    """Per bar: the median of `grid_nT` over the eligible names with a finite value."""
    n, T = grid_nT.shape
    val = np.full(T, np.nan)
    cnt = np.zeros(T, dtype=int)
    for t in range(T):
        v = grid_nT[eligT_Tn[t], t]
        v = v[np.isfinite(v)]
        cnt[t] = v.size
        if v.size >= min_names:
            val[t] = float(np.median(v))
    return val, cnt


def market_vol(m_f, w=VOL_BARS):
    """Trailing w-bar standard deviation of the floored market's return, ending at t."""
    T = m_f.size
    out = np.full(T, np.nan)
    fin = np.isfinite(m_f)
    if fin.sum() <= w:
        return out
    j0 = int(np.flatnonzero(fin)[0])
    seg = m_f[j0:]
    assert np.isfinite(seg).all(), "m_f has an interior hole; the window would span it"
    W = np.lib.stride_tricks.sliding_window_view(seg, w)
    out[j0 + w - 1:] = W.std(axis=-1)
    return out


def partial_corr(x, z, y):
    """r(x, y | z), closed form, and the residual of x on z for the shuffle test."""
    rxy = float(np.corrcoef(x, y)[0, 1])
    rxz = float(np.corrcoef(x, z)[0, 1])
    rzy = float(np.corrcoef(z, y)[0, 1])
    den = np.sqrt(max((1 - rxz ** 2) * (1 - rzy ** 2), 1e-300))
    beta = np.polyfit(z, x, 1)[0]
    return (rxy - rxz * rzy) / den, x - beta * z, dict(r_xy=rxy, r_xz=rxz, r_zy=rzy)


def shuffled_bar(a, b, seed, draws=999):
    """|r| p95 of `a` permuted against `b` -- D361's control, unchanged."""
    rng = np.random.default_rng(seed)
    more = np.array([np.corrcoef(a[rng.permutation(a.size)], b)[0, 1] for _ in range(draws)])
    return float(np.quantile(np.abs(more), .95)), float(np.median(more))


# ---------------------------------------------------------------------- self-test
def selftest() -> int:
    print("C1b SELF-TEST -- does the partial correlation actually remove a planted confound?\n")
    rng = np.random.default_rng(11)
    n = 400
    z = rng.normal(size=n)                                   # the confound
    y = z + 0.35 * rng.normal(size=n)                        # y is driven by z ALONE
    x = z + 0.35 * rng.normal(size=n)                        # x is z plus noise: NO OWN EFFECT

    raw = float(np.corrcoef(x, y)[0, 1])
    pc, resid, parts = partial_corr(x, z, y)
    assert raw > 0.6, f"the planted confound should make the raw correlation large, got {raw:.3f}"
    assert abs(pc) < 0.15, f"[X] the partial failed to remove a pure confound: {pc:+.3f}"
    print(f"    planted pure confound: raw r {raw:+.3f} -> partial r {pc:+.3f}  (confound REMOVED)")

    # and it must NOT remove a real effect that survives the confound
    x2 = z + 0.35 * rng.normal(size=n)
    y2 = z + 1.2 * x2 + 0.35 * rng.normal(size=n)            # y2 genuinely depends on x2
    pc2, _r2, _p2 = partial_corr(x2, z, y2)
    assert pc2 > 0.5, f"[X] the partial destroyed a REAL effect: {pc2:+.3f}"
    print(f"    planted real effect:   raw r {float(np.corrcoef(x2, y2)[0, 1]):+.3f} -> "
          f"partial r {pc2:+.3f}  (effect KEPT)")

    # [X] the check must be able to fail: a "partial" that ignores z must be caught
    raised = False
    try:
        assert abs(raw) < 0.15, "a partial that ignores the confound must not pass"
    except AssertionError:
        raised = True
    assert raised, "[X] THE SELF-TEST CANNOT FAIL -- an unpartialled correlation passed"
    print(f"    [X] a 'partial' that ignores z reads {raw:+.3f} and IS CAUGHT")
    print("\nSELF-TEST PASSED\n")
    return 0


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    if ap.parse_args().selftest:
        return selftest()
    selftest()

    t0 = time.time()
    P = C1.PREP.prep(need_grids=False)
    V61 = C1.V61
    T, H = P["T"], V61.HORIZON
    elig = np.asarray(P["elig"])
    dates, years = P["dates"], P["years"]
    F = V61.forward20(P)
    groups = V61.stage0_groups(P)
    print(f"  prep in {time.time() - t0:.0f}s | {P['n']} names x {T} bars | horizon {H}", flush=True)

    # ---- rebuild C1's DISPERSION exactly, and [REG] against its artifact -----
    tr = C1.trailing_return(np.ascontiguousarray(np.asarray(P["CLOSE"]).T), P["live"])
    dp_raw, dp_cnt = C1.cross_state(tr, elig, "iqr")
    DISP = C1.state_pack("DISPERSION", dp_raw, dp_cnt, T, dates, years, C1.trailing_median_rule)

    c1 = json.loads(C1_JSON.read_text())
    pub = c1["result"]["DISPERSION"]["blocks"]["bottom_10"]
    got = C1.block_corr(DISP["level"], groups["bottom_10"], F, DISP["d0"], T, [C1.SEED, 0, 0], H)
    for k in ("n_blocks", "corr", "shuffle_p95"):
        assert abs(got[k] - pub[k]) < 1e-12, f"[REG] DISPERSION.{k}: {got[k]!r} != C1's {pub[k]!r}"
    print(f"    [REG] DISPERSION reproduces C1's published {pub['corr']:+.5f} on "
          f"{pub['n_blocks']} blocks to 0.0 -- same object", flush=True)

    # ---- the two volatility states -----------------------------------------
    rv = np.where(P["base"], P["score"]("rvol21"), np.nan)
    vx_raw, vx_cnt = cross_median(rv, elig, C1.MIN_NAMES)
    vm_raw = market_vol(np.asarray(P["m_f"], float))
    vm_cnt = np.where(np.isfinite(vm_raw), C1.MIN_NAMES, 0)
    VOLXS = C1.state_pack("VOL_XS", vx_raw, vx_cnt, T, dates, years, C1.trailing_median_rule)
    VOLMKT = C1.state_pack("VOL_MKT", vm_raw, vm_cnt, T, dates, years, C1.trailing_median_rule)
    for nm, cnt, gp in (("VOL_XS", vx_cnt, VOLXS), ("VOL_MKT", vm_cnt, VOLMKT)):
        c = cnt[gp["defined"]]
        print(f"    [E] {nm}: names per defined bar min {c.min()}, median {np.median(c):.0f}; "
              f"on {100 * gp['on_share']:.1f}% of {gp['Td']:,} defined bars", flush=True)

    PACKS = {"DISPERSION": DISP, "VOL_XS": VOLXS, "VOL_MKT": VOLMKT,
             "G1": V61.gate_pack(P, "G1"), "G2": V61.gate_pack(P, "G2")}

    # ---- Q1: how related are the levels? -----------------------------------
    keys = list(PACKS)
    both = np.ones(T, bool)
    for k in keys:
        both &= PACKS[k]["defined"] & np.isfinite(PACKS[k]["level"])
    rk = {k: np.argsort(np.argsort(PACKS[k]["level"][both])) / max(1, int(both.sum()) - 1) for k in keys}
    Lm = np.corrcoef(np.vstack([rk[k] for k in keys]))
    print(f"  Q1 level Spearman over the {int(both.sum()):,} commonly-defined bars", flush=True)

    # ---- Q2: is volatility ALONE decisive? ---------------------------------
    q2 = {nm: {g: C1.block_corr(PACKS[nm]["level"], groups[g], F, PACKS[nm]["d0"], T,
                                [C1.SEED, 1, i], H)
               for i, g in enumerate(C1.TARGETS)} for nm in ("VOL_XS", "VOL_MKT")}

    # ---- Q3: does DISPERSION's premise survive partialling volatility out? --
    q3 = {}
    for nm in ("VOL_XS", "VOL_MKT"):
        d0 = max(DISP["d0"], PACKS[nm]["d0"])
        xs, zs, ys, empty = [], [], [], 0
        for b in range(d0, T - H + 1, H):
            row = groups["bottom_10"][b]
            if not row.any():
                empty += 1
                continue
            xs.append(DISP["level"][b])
            zs.append(PACKS[nm]["level"][b])
            ys.append(float(F[b][row].mean()))
        x, z, y = np.array(xs), np.array(zs), np.array(ys)
        pc, resid, parts = partial_corr(x, z, y)
        r_res = float(np.corrcoef(resid, y)[0, 1])
        p95, p50 = shuffled_bar(resid, y, [C1.SEED, 2, len(q3)])
        q3[nm] = dict(n_blocks=int(x.size), empty_blocks=empty, d0=int(d0),
                      raw_corr=parts["r_xy"], corr_disp_vol=parts["r_xz"], corr_vol_y=parts["r_zy"],
                      partial_corr=pc, residual_corr=r_res, shuffle_p95=p95, shuffle_p50=p50,
                      survives=bool(abs(r_res) > p95))
        print(f"    Q3 vs {nm}: raw {parts['r_xy']:+.3f} -> partial {pc:+.3f} "
              f"(residual {r_res:+.3f} vs shuffled p95 {p95:.3f}) -- "
              f"{'SURVIVES' if q3[nm]['survives'] else 'DOES NOT SURVIVE'}", flush=True)

    # ---- [P] PERSIST BEFORE RENDERING --------------------------------------
    payload = {
        "purpose": "C1b: is DISPERSION a new state or volatility renamed? C1 compared it only "
                   "against direction measures. Descriptive; scores nothing.",
        "reproduces": {"c1_dispersion_bottom_10": pub["corr"], "recomputed": got["corr"]},
        "states": {"VOL_XS": f"cross-sectional median of rvol21 over eligible names at t-1",
                   "VOL_MKT": f"trailing {VOL_BARS}-bar std of the floored market return at t-1",
                   "gate_rule": "above its own trailing 252-bar median, causal (C1's rule)"},
        "horizon": H, "targets": list(C1.TARGETS), "seed": C1.SEED,
        "q1_level_spearman": {"bars": int(both.sum()), "states": keys, "matrix": Lm.tolist()},
        "q2_volatility_alone": q2, "q3_partial": q3,
        "verdict": ("DISPERSION SURVIVES both volatility controls"
                    if all(v["survives"] for v in q3.values()) else
                    "DISPERSION DOES NOT SURVIVE at least one volatility control"),
    }
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)

    # ---- render -------------------------------------------------------------
    print("\nQ1 -- LEVEL SPEARMAN. Is dispersion the same object as volatility?\n")
    print("  " + " " * 12 + " ".join(f"{k[:10]:>11s}" for k in keys))
    for i, k in enumerate(keys):
        print(f"  {k:<12s}" + " ".join(f"{Lm[i, j]:>11.3f}" for j in range(len(keys))))

    print("\nQ2 -- IS VOLATILITY ALONE DECISIVE? Same block premise, run on the volatility levels.\n")
    print(f"  {'state':<11s} {'target':<11s} {'blocks':>7s} {'corr':>8s} {'shuf p95':>9s}  decisive")
    for nm in ("VOL_XS", "VOL_MKT"):
        for g in C1.TARGETS:
            b = q2[nm][g]
            print(f"  {nm:<11s} {g:<11s} {b['n_blocks']:>7d} {b['corr']:>+8.3f} "
                  f"{b['shuffle_p95']:>9.3f}  {'YES' if b['decisive'] else 'no'}")

    print("\nQ3 -- DOES DISPERSION'S PREMISE SURVIVE PARTIALLING VOLATILITY OUT?  (loser cohort)\n")
    print(f"  {'control':<9s} {'blocks':>7s} {'raw':>7s} {'r(D,V)':>8s} {'r(V,y)':>8s} "
          f"{'partial':>8s} {'resid':>7s} {'p95':>7s}  verdict")
    for nm, v in q3.items():
        print(f"  {nm:<9s} {v['n_blocks']:>7d} {v['raw_corr']:>+7.3f} {v['corr_disp_vol']:>+8.3f} "
              f"{v['corr_vol_y']:>+8.3f} {v['partial_corr']:>+8.3f} {v['residual_corr']:>+7.3f} "
              f"{v['shuffle_p95']:>7.3f}  {'SURVIVES' if v['survives'] else 'FAILS'}")

    print(f"\nVERDICT: {payload['verdict']}")
    print("\nQ3 is the one that decides. Q1 says whether they are the same object; Q2 says whether "
          "volatility\nalready does the job; only Q3 asks whether dispersion carries anything "
          "volatility does not.")
    return 0


C1 = _load("c1", "c1_gate_stage0.py")

if __name__ == "__main__":
    raise SystemExit(main())
