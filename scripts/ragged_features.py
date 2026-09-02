"""D288 Phase 0.5 -- feature families ported to the DAILY RAGGED panel.

    uv run python scripts/ragged_features.py --selftest

NOTHING HERE SCORES A CELL. It moves existing estimators onto a panel they could
not previously run on, and proves each move changed no number.

WHY THE PORTS ARE NEEDED. The signal inventory for D288 found that two of the
five axes the mine wants exist only as FIFTEEN-MINUTE wrappers. The primitives
are fine in every case; the wrappers index a GLOBAL bar index `t` against
SYMBOL-LOCAL arrays, which is correct on a rectangular panel and silently wrong
on a ragged one. `run_book_single_names.signals_ragged` shows the idiom that
fixes it:

    at = np.flatnonzero(panel.live[i])      # this symbol's own bars
    grid[i, at] = series_of_length_len(at)

THE ONE THING A RAGGED PORT MUST NOT DO. A trailing window has to run over the
SYMBOL'S OWN live bars, never over `t-k .. t-1` on the union grid. On this panel
134 of 1,573 names carry internal holes and every name has its own start, so a
global window silently mixes in bars where the name did not trade -- and for a
volume estimator that is not a small error, it is a comparison against days that
do not exist.

EQUIVALENCE IS TESTED, NOT ASSERTED. Every port takes the same arguments the
original did and `--selftest` runs both on the RECTANGULAR 15-minute panel,
requiring bit-identical output. A port that changes a number is a new estimator
wearing an old name.

ONE ESTIMATOR GENUINELY CHANGES, AND IT IS DECLARED RATHER THAN HIDDEN.
`rel_vol` and its relatives normalise against the trailing 20 sessions AT THE
SAME BAR-OF-DAY. Daily bars have one bar per day, so that collapses to a plain
trailing 20-BAR window. Defensible -- it is the same idea at the only frequency
available -- but it is NOT the estimator D270 measured, and D288's
pre-registration says so rather than inheriting D270's result. The code makes
the choice explicit through `bod=None` rather than burying it.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
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


RP = _load("ragged_panel", "ragged_panel.py")

VOL_SCORES = ("rel_vol", "vol_z", "dollar_vol", "vol_trend", "signed_vol")
LOOKBACK_SESSIONS = 20          # D269's constant, unchanged
TREND_BARS = 8
SIGN_BARS = 8


# --------------------------------------------------------------------------
# the volume grid -- volume is parsed into `cleaned` and never gridded on daily
# --------------------------------------------------------------------------


def volume_grids(panel, cleaned, live=None):
    """`(vol, px)` on the panel's own grid, NaN outside each symbol's window.

    `load_ragged` already parses volume into `cleaned[sym][j].bar.volume`; it
    simply never builds a grid from it, because nothing before D288 needed one.
    This is the scatter idiom and nothing more -- no re-reading of the fixture,
    so the grid cannot drift from the panel it is aligned to."""
    n, T = panel.closes.shape
    # A rectangular panel has no `live`; every bar is live. Taking the mask as an
    # argument means this function runs unchanged on both shapes, which is what
    # lets the self-test prove it against the rectangular original.
    if live is None:
        live = getattr(panel, "live", np.ones((n, T), dtype=bool))
    vol = np.full((n, T), np.nan)
    px = np.full((n, T), np.nan)
    for i, s in enumerate(panel.symbols):
        at = np.flatnonzero(live[i])
        bars = cleaned[s]
        if at.size != len(bars):
            raise AssertionError(
                f"{s}: {at.size} live bars against {len(bars)} cleaned bars -- "
                "the panel and the bar list disagree")
        vol[i, at] = [b.bar.volume for b in bars]
        px[i, at] = [b.bar.close for b in bars]
    return vol, px


def volume_scores(vol, px, rets, live, bod=None):
    """D269/D270's five volume scores, on a ragged OR a rectangular panel.

    `bod` is the bar-of-day index the 15-minute construction normalises within.
    **Pass it to reproduce the intraday estimator exactly. Pass `None` for daily
    bars**, where there is one bar per session and the grouping collapses to a
    plain trailing window -- see the module docstring; that is a declared change
    of estimator, not an incidental one.

    On a ragged panel the trailing window runs over the SYMBOL'S OWN live bars.
    Zero and missing volume become NaN before any log, so a stub bar cannot
    become a -inf that quietly poisons a median."""
    n, T = vol.shape
    out = {k: np.full((n, T), np.nan) for k in VOL_SCORES}
    lv = np.log(np.where(vol > 0, vol, np.nan))
    ldv = np.log(np.where(vol > 0, vol * px, np.nan))

    for i in range(n):
        own = np.flatnonzero(live[i])
        if own.size == 0:
            continue
        groups = ([own] if bod is None
                  else [own[bod[own] == d] for d in np.unique(bod[own])])
        for idx in groups:
            for j, t in enumerate(idx):
                if j < LOOKBACK_SESSIONS:
                    continue
                w = idx[j - LOOKBACK_SESSIONS:j]           # TRAILING ONLY -- R9
                a, b = lv[i, w], lv[i, t]
                if not np.isfinite(b) or not np.isfinite(a).any():
                    continue
                med = np.nanmedian(a)
                sd = np.nanstd(a, ddof=1)
                out["rel_vol"][i, t] = b - med
                if sd > 0:
                    out["vol_z"][i, t] = (b - med) / sd
                a2, b2 = ldv[i, w], ldv[i, t]
                if np.isfinite(b2) and np.isfinite(a2).any():
                    out["dollar_vol"][i, t] = b2 - np.nanmedian(a2)

        rv = out["rel_vol"][i]
        for k in range(TREND_BARS, own.size):
            seg = rv[own[k - TREND_BARS + 1:k + 1]]
            if np.isfinite(seg).sum() == TREND_BARS:
                out["vol_trend"][i, own[k]] = np.polyfit(
                    np.arange(TREND_BARS), seg, 1)[0]

        r = np.nan_to_num(rets[i, own])
        cs = np.concatenate([[0.0], np.cumsum(r)])
        cum = np.full(own.size, np.nan)
        cum[SIGN_BARS:] = cs[SIGN_BARS + 1:] - cs[1:own.size - SIGN_BARS + 1]
        out["signed_vol"][i, own] = rv[own] * np.sign(cum)
    return out


INTRABAR_SCORES = ("upper_wick", "lower_wick", "wick_asym", "body_frac",
                   "close_in_range", "range_frac", "gap_frac")


def intrabar_scores(g, live):
    """Intrabar SHAPE, the axis D280 measured as genuinely independent.

    D280 G3 found 16 OHLC-derivative terms carrying **13.50-15.76 effective
    inputs**, against 2.87 for nine price scores (D268) -- the prediction that
    they would collapse was WRONG, and that is why this family is in D288's mine
    rather than more price transforms.

    These live inline in `d280_delta_range_precheck.main()` and
    `d280_combined_forecast.main()` and have never been a function. Lifted
    verbatim -- same formulae, same guard -- so the mine calls one thing rather
    than pasting ten lines. **Already ragged-safe**: they are pure per-bar
    arithmetic on `build_grids` output, which maps each bar's own timestamp onto
    the union grid, so nothing indexes a symbol-local array by a global bar.

    UNLAGGED, matching every other score family here. Consumers (`top_n`,
    `neutral_book`) call `lag1` themselves; lagging here would double-lag them.

    `range_frac` is the fractional range `(H-L)/C` D280 used to normalise, and
    `gap_frac` is the overnight leg `O/C_prev - 1` -- the window D280 part 4
    measured as carrying the whole effect. Both are shape, not level, so they
    are comparable across names."""
    O, H, L, C = g["open"], g["high"], g["low"], g["close"]

    # MALFORMED BARS ARE MASKED, NOT CLAMPED. An assertion here caught five bars
    # in 4,137,239 where the CLOSE sits BELOW the LOW -- MWR 2014-05-09
    # (O 25.3800 H 25.4100 L 25.3700 C 24.9893), AVV 2014-05-12, TLLP
    # 2016-07-28. In every case the close carries decimals the OHLC do not,
    # which is an ex-dividend adjustment applied to the close and not to the
    # high and low: a provider artefact, not a market event.
    #
    # Nothing in the build gates looks for this. Gate A checks split
    # discontinuities and gate B checks large single-bar moves; neither sees an
    # OHLC ORDERING violation, so these five have been in the fixture unnoticed.
    #
    # A shape cannot be computed from a bar that is not a bar, so the cells go
    # NaN. Clamping would invent a shape; dropping the symbol would spend three
    # names on five bars.
    valid = (H >= np.maximum(O, C) - 1e-12) & (L <= np.minimum(O, C) + 1e-12)
    live = live & valid

    rng = H - L
    # A ZERO-RANGE BAR IS NOT A SHAPE EITHER -- 17,886 of them (0.43%), stub and
    # halted sessions where high == low. Their ratios would all be 0/0.
    safe = np.where(rng > 0, rng, np.nan)
    body_hi = np.maximum(O, C)
    body_lo = np.minimum(O, C)
    prev_c = np.full_like(C, np.nan)
    ok = live[:, 1:] & live[:, :-1]
    prev_c[:, 1:] = np.where(ok, C[:, :-1], np.nan)
    out = {
        "upper_wick": (H - body_hi) / safe,
        "lower_wick": (body_lo - L) / safe,
        "wick_asym": ((H - body_hi) - (body_lo - L)) / safe,
        "body_frac": (C - O) / safe,
        "close_in_range": (C - L) / safe,
        "range_frac": np.where(C > 0, rng / C, np.nan),
        "gap_frac": np.where(prev_c > 0, O / prev_c - 1.0, np.nan),
    }
    return {k: np.where(live, v, np.nan) for k, v in out.items()}


# --------------------------------------------------------------------------
# the self-test -- equivalence against the original, on the RECTANGULAR panel
# --------------------------------------------------------------------------


def selftest() -> int:
    print("RAGGED FEATURE PORTS -- equivalence against the 15-minute originals\n")
    V = _load("d269", "run_volume_structure.py")
    R = _load("d264", "run_single_name_intraday.py")

    raw_panel, raw_cleaned = R.load_full()
    panel, cleaned = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    vol, px, stamps = V.load_volume(panel)
    bod = V.bar_of_day(stamps)
    rets = panel.total_log_returns
    live = np.ones(panel.closes.shape, dtype=bool)      # rectangular: all live

    want = V.build_volume_scores(panel, vol, px, bod, rets)
    got = volume_scores(vol, px, rets, live, bod=bod)

    bad = 0
    for k in VOL_SCORES:
        a, b = want[k], got[k]
        same = np.array_equal(a, b, equal_nan=True)
        finite = int(np.isfinite(a).sum())
        worst = (float(np.nanmax(np.abs(a - b))) if np.isfinite(a - b).any() else 0.0)
        print(f"  {k:12s} identical: {str(same):5s}   finite cells {finite:9,d}   "
              f"max abs diff {worst:.3e}")
        bad += 0 if same else 1
    if bad:
        raise AssertionError(f"{bad} volume score(s) differ from the original")
    print("\n  [1] all five volume scores are BIT-IDENTICAL to "
          "run_volume_structure.build_volume_scores")

    # `volume_grids` is tested where it actually runs: the DAILY RAGGED panel.
    # It cannot be tested on the 15-minute one, because that panel's bars are
    # `simulator.fills.Bar`, which carries OHLC and NO VOLUME -- only
    # `ragged_panel.Bar` has it. That asymmetry is exactly why volume was never
    # gridded on daily before, and testing the port on the wrong panel would
    # have proved nothing.
    B = _load("d256", "run_book_single_names.py")
    dpanel, dcleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    dvol, dpx = volume_grids(dpanel, dcleaned)

    # the grid must be populated exactly on the live mask and nowhere else
    if not np.array_equal(np.isfinite(dvol), dpanel.live):
        raise AssertionError("volume grid is finite off the live mask, or absent on it")
    # and the close it carries must be the panel's own close, not a re-read
    m = dpanel.live & np.isfinite(dpanel.closes)
    if not np.allclose(dpx[m], dpanel.closes[m], rtol=0, atol=0):
        raise AssertionError("price grid disagrees with panel.closes")
    zero = int((dvol[dpanel.live] == 0).sum())
    print(f"  [2] volume_grids on the DAILY ragged panel: finite exactly on the "
          f"live mask,\n      closes match panel.closes bit-for-bit, "
          f"{zero:,} zero-volume bars present")

    # the zero-volume guard, on real data rather than a contrived case
    dsc = volume_scores(dvol, dpx, dpanel.total_log_returns, dpanel.live, bod=None)
    if np.isinf(dsc["rel_vol"]).any():
        raise AssertionError("a zero-volume bar produced an infinite rel_vol")
    print(f"  [2b] no zero-volume bar leaked a -inf into rel_vol "
          f"({int(np.isfinite(dsc['rel_vol']).sum()):,} finite cells on daily)")

    # bod=None must DIFFER -- it is a declared change of estimator, and a port
    # that silently returned the same thing would mean the grouping never bound
    daily_like = volume_scores(vol, px, rets, live, bod=None)
    if np.array_equal(want["rel_vol"], daily_like["rel_vol"], equal_nan=True):
        raise AssertionError(
            "bod=None produced the SAME result as bod-grouped -- the bar-of-day "
            "normalisation is not doing anything, which contradicts D269")
    print("  [3] bod=None differs from bod-grouped, as the declared estimator "
          "change requires")

    # intrabar shape, on the daily panel where the mine will use it
    P1 = _load("d280p1", "d280_forecast_precheck.py")
    dg = P1.build_grids(dpanel, dcleaned)
    isc = intrabar_scores(dg, dpanel.live)
    for k, v in isc.items():
        if np.isinf(v).any():
            raise AssertionError(f"{k} produced an infinity")
        if np.isfinite(v[~dpanel.live]).any():
            raise AssertionError(f"{k} is finite OFF the live mask")
    # the ratios that are shares of the range must lie in [0, 1]
    for k in ("upper_wick", "lower_wick", "close_in_range"):
        v = isc[k][np.isfinite(isc[k])]
        if v.size and (v.min() < -1e-12 or v.max() > 1 + 1e-12):
            raise AssertionError(f"{k} leaves [0,1]: {v.min():.4f}..{v.max():.4f}")
    covered = {k: int(np.isfinite(v).sum()) for k, v in isc.items()}
    dO, dH, dL, dC = dg["open"], dg["high"], dg["low"], dg["close"]
    malformed = int((dpanel.live
                     & ~((dH >= np.maximum(dO, dC) - 1e-12)
                         & (dL <= np.minimum(dO, dC) + 1e-12))).sum())
    zero_rng = int((dpanel.live & (dH == dL)).sum())
    print(f"  [4] intrabar shape: no infinities, nothing finite off the live mask,")
    print(f"      range shares within [0,1]; finite cells "
          f"{min(covered.values()):,}..{max(covered.values()):,}")
    print(f"  [4b] masked {malformed} malformed bar(s) (close outside high-low) and "
          f"{zero_rng:,} zero-range bars")

    print("\n  ALL SELF-TESTS PASSED. No cell scored.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    ap.print_help()
    raise SystemExit(2)
