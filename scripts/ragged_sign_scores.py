"""Axis I -- SIGN-SEQUENCE scores: the order of returns, with the magnitudes thrown away.

    uv run python scripts/ragged_sign_scores.py --selftest

THE ONE THING NO SCORE IN THE CATALOGUE READS. All 49 existing scores are magnitude summaries of a
window -- a return, a range, a volatility, a distance. **Not one reads the ORDER or the SIGN
PATTERN of the returns inside it.** `docs/research/the-signal-hunt-part2.md` section 3a.1 is the
statement of that gap.

WHY THIS FAMILY AND NOT ANOTHER, and the argument is D392's, not a preference. The atlas measured
what a purely random long earns, conditioned on the pool it draws from:

    price tercile      spread  36.8 bp   <- the widest
    momentum tercile   spread  32.2 bp
    volatility tercile spread  12.2 bp

A candidate that tilts on price or momentum inherits a large floor before it has done anything.
**Sign statistics are unit-free, price-free and magnitude-free by construction** -- they are the
one family that structurally cannot tilt on either of the two widest base rates. That is also
FINDINGS section 14's problem (a cross-sectional rank on a quantity carrying units ranks those
units) answered by construction rather than by a normalisation that failed.

THE THREE SCORES, over 21 of the name's OWN bars:

    up_run_21      the longest run of consecutive up days
    sign_flips_21  how many times the sign of the return changed
    up_frac_21     the share of days that were up

"Up" is `log(c/prev) > 0` STRICTLY. A flat day is not an up day and it breaks a run -- which
matters on a coarse tick, and is reported by the self-test rather than assumed away.

WARM-UP FOLLOWS THE E/G REGIME, NOT A'S, AND THE REASON IS SURVIVORSHIP. `ragged_vol_scores.py`
lines 111-127 records it: a `if at.size < W: continue` guard is a test on a symbol's TOTAL bar
count, so whether bar t gets a score depends on how many bars the name has in the FUTURE. On a
35.7%-dead fixture the names with few total bars are the ones that DELIST, so such a guard
silently withholds scores from exactly the cohort the panel exists to include -- survivorship
arriving through a warm-up check, caught as 851 moved cells. So: `V._trail` decides per bar from
bars already seen, and the only symbol-level guard is `at.size < 2`.

CAUSALITY IS PROVED, NOT ASSERTED. The self-test's `[2]` is the shared truncation audit
(`ragged_vol_scores.truncation_audit`): build on the full panel and on one truncated at T0, and
require the finite mask AND the values to be identical on the overlap. Run-length and flip counts
are causal by construction -- but that is exactly the kind of claim this programme has been wrong
about, so it is measured.

**This proves the SCORE does not read the future. It does not prove a POSITION built from it is
lagged** -- that is `scripts/lag_audit.py`, and D391 shipped a defect that passed the first and
failed the second.
"""

from __future__ import annotations

import argparse
import importlib.util
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


V = _load("ragged_vol_scores", "ragged_vol_scores.py")     # _trail, _windows, truncation_audit

SIGN_SCORES = ("up_run_21", "sign_flips_21", "up_frac_21")

SIGN_BARS = 21          # one trading month, the unit the rest of the programme uses


def _max_run(win):
    """Longest run of 1.0 along each row of a trailing window.

    A NaN column breaks a run, which is correct: a day the name did not trade is not an up day.
    During warm-up every column is NaN and the whole row scores 0 -- `_trail`'s count test is what
    turns that into NaN, not this function."""
    best = np.zeros(win.shape[0])
    cur = np.zeros(win.shape[0])
    for j in range(win.shape[1]):
        up = win[:, j] == 1.0
        cur = np.where(up, cur + 1.0, 0.0)
        best = np.maximum(best, cur)
    return best


def sign_scores(g, live, w=SIGN_BARS):
    """I1-I3 on the panel's own grid, NaN outside each symbol's window. UNLAGGED.

    Like every other family here the value at column t is computed from bars up to and INCLUDING
    t; the consumer lags (`run_d350.lagged`, `d348_prep`'s closure, or `lag_audit.lag1_mask` for
    an event book). Lagging here as well would silently double-lag every study built on it."""
    C = g["close"]
    n, T = C.shape
    out = {k: np.full((n, T), np.nan) for k in SIGN_SCORES}

    for i in range(n):
        at = np.flatnonzero(live[i])
        if at.size < 2:
            continue
        c = C[i, at]
        prev = np.concatenate([[np.nan], c[:-1]])
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.log(np.where((c > 0) & (prev > 0), c / prev, np.nan))

        up = np.where(np.isfinite(r), (r > 0.0).astype(float), np.nan)
        out["up_frac_21"][i, at] = V._trail(up, w, lambda x: np.nanmean(x, axis=1))
        out["up_run_21"][i, at] = V._trail(up, w, _max_run)

        # A FLIP is a change of sign between consecutive returns, counted PER RETURN: `flip[k]`
        # asks whether return k differs in sign from k-1. A w-bar window therefore holds w
        # indicators, one of which reaches back to the return immediately before the window --
        # so the maximum is w, not w-1.
        #
        # The alternative -- counting only flips strictly INSIDE the window -- differs by that one
        # boundary term. The per-return form is chosen because every return contributes exactly
        # one indicator, which keeps the statistic a clean trailing mean-like reduction and lets
        # `_trail`'s MIN_FRAC warm-up rule apply unchanged. Stated because it is a real choice,
        # and the self-test pins it (a perfect alternation over w=10 scores 10, not 9).
        s = np.sign(r)
        sp = np.concatenate([[np.nan], s[:-1]])
        with np.errstate(invalid="ignore"):
            flip = np.where(np.isfinite(s) & np.isfinite(sp), (s != sp).astype(float), np.nan)
        out["sign_flips_21"][i, at] = V._trail(flip, w, lambda x: np.nansum(x, axis=1))

    for k in out:                                    # the closing hygiene block, as every family
        out[k][~live] = np.nan
        out[k] = np.where(np.isfinite(out[k]), out[k], np.nan)
    return out


# ------------------------------------------------------------------------ self-test
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()
    t0 = time.time()

    print("AXIS I -- SIGN-SEQUENCE SCORES\n")
    print("  [0] hand cases, before any fixture\n")
    # a name that rises every day: run = w-1 returns, no flips, up_frac 1
    live1 = np.ones((1, 30), dtype=bool)
    g1 = {"close": np.linspace(100.0, 130.0, 30)[None, :]}
    h = sign_scores(g1, live1, w=10)
    assert h["up_frac_21"][0, 29] == 1.0, h["up_frac_21"][0, 29]
    assert h["up_run_21"][0, 29] == 10.0, h["up_run_21"][0, 29]
    assert h["sign_flips_21"][0, 29] == 0.0, h["sign_flips_21"][0, 29]
    print(f"      monotone riser: up_frac 1.000, longest run 10, flips 0")

    # a perfect alternation: up_frac ~0.5, run 1, flips = w-1
    alt = 100.0 + np.tile([0.0, 2.0], 15)
    g2 = {"close": alt[None, :]}
    h2 = sign_scores(g2, live1, w=10)
    assert h2["up_run_21"][0, 29] == 1.0, h2["up_run_21"][0, 29]
    # 10, not 9: flips are counted PER RETURN, so a w-bar window holds w indicators and the
    # first of them reaches back to the return before the window. See sign_scores' comment.
    assert h2["sign_flips_21"][0, 29] == 10.0, h2["sign_flips_21"][0, 29]
    print(f"      perfect alternation: longest run 1, flips 10 of 10 (per-RETURN convention)")

    # a FLAT day is not an up day and BREAKS a run -- stated, then checked
    flat = np.array([100.0, 101, 102, 102, 103, 104, 105, 106, 107, 108, 109, 110])
    g3 = {"close": flat[None, :]}
    h3 = sign_scores(g3, np.ones((1, 12), dtype=bool), w=6)
    assert h3["up_run_21"][0, 11] == 6.0
    # the window at bar 6 covers own-bars 1..6, whose returns are [+, +, 0, +, +, +]:
    # runs of 2 and then 3, so 3. WITHOUT the flat day every one would be up and it would be 6.
    assert h3["up_run_21"][0, 6] == 3.0, h3["up_run_21"][0, 6]
    print(f"      a flat day breaks the run: the window spanning it scores "
          f"{h3['up_run_21'][0, 6]:.0f}, against 6 for an unbroken one")

    # a holed name: the window must be counted in the name's OWN bars
    holed = np.ones((1, 40), dtype=bool)
    holed[0, 8:20] = False
    cc = np.full((1, 40), np.nan)
    at = np.flatnonzero(holed[0])
    cc[0, at] = np.linspace(50.0, 90.0, at.size)
    h4 = sign_scores({"close": cc}, holed, w=10)
    assert np.isnan(h4["up_frac_21"][0, at[:9]]).all() and np.isfinite(h4["up_frac_21"][0, at[10]])
    assert np.isnan(h4["up_frac_21"][0, 9]), "a column inside the hole must stay NaN"
    print(f"      holed name: first defined bar is its OWN 11th (column {at[10]}), "
          f"and the hole stays NaN")

    # ---- the fixture ---------------------------------------------------
    B = _load("d256", "run_book_single_names.py")
    P1 = _load("d280p1", "d280_forecast_precheck.py")
    panel, cleaned = B.RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    print(f"\n  loaded {live.shape[0]} x {live.shape[1]} in {time.time() - t0:.0f}s")

    def build(T0):
        if T0 is None:
            return sign_scores(g, live)
        gg = {k: v[:, :T0] for k, v in g.items()}
        return sign_scores(gg, live[:, :T0])

    sc = build(None)
    print(f"\n  [1] coverage and bounds\n")
    for k in SIGN_SCORES:
        a = sc[k]
        fin = np.isfinite(a)
        assert not np.isinf(a[fin]).any(), f"{k} has infinities"
        assert not (fin & ~live).any(), f"{k} is finite off a live bar"
        assert fin.sum() > 0, f"{k} produced nothing"
        print(f"      {k:<14s} finite {int(fin.sum()):>10,} ({100 * fin.sum() / live.sum():5.1f}% "
              f"of live)  range [{a[fin].min():.3f}, {a[fin].max():.3f}]")
    assert sc["up_run_21"][np.isfinite(sc["up_run_21"])].max() <= SIGN_BARS
    assert sc["up_frac_21"][np.isfinite(sc["up_frac_21"])].max() <= 1.0
    fl = sc["sign_flips_21"][np.isfinite(sc["sign_flips_21"])]
    assert fl.min() >= 0.0 and fl.max() <= SIGN_BARS, (fl.min(), fl.max())
    print(f"      bounds hold: run <= {SIGN_BARS}, frac <= 1, 0 <= flips <= {SIGN_BARS}")

    T0 = int(live.shape[1] * 0.7)
    print(f"\n  [2] truncation audit at column {T0} of {live.shape[1]}")
    bad = V.truncation_audit(build, live, T0, SIGN_SCORES, "I")
    assert bad == 0, f"{bad} I score(s) READ THE FUTURE"

    print(f"\nOK  {len(SIGN_SCORES)} I scores, all causal  ({time.time() - t0:.0f}s)")
    print("\nNOTE: this proves the SCORE is causal. It does NOT prove a position built from it is "
          "lagged -- that is scripts/lag_audit.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
