"""D288 Phase 0.5 -- the VOLUME-PROFILE score family ported to the DAILY RAGGED panel.

    uv run python scripts/ragged_profile.py --selftest

NOTHING HERE SCORES A CELL. No strategy runs, no rule is proposed, no forward
return is touched. This moves an existing estimator onto a panel it could not
previously run on, and proves the move changed no number.

WHAT WAS BROKEN, AND WHAT WAS NOT. `terrain.VolumeProfileSensor` is daily-native
-- D189 built it on daily bars and its docstring says so. The sensor is fine.
The PANEL WRAPPER, `run_volume_profile.build_profile_scores`, is what does not
survive a ragged panel: it pairs `panel.closes[i, t - 1]`, a GLOBAL bar index,
with `cleaned[sym][t - 1]` and `vol[i][t - 1]`, which are SYMBOL-LOCAL. Those
two index spaces coincide only on a rectangular panel. On this one 134 of 1,573
names carry internal holes and every name starts on its own date, so a global
`t` reads some other date's bar out of the name's own bar list -- and for a
volume-at-price map, that is not a small misalignment: it is a profile built
from a window that includes days the name did not trade.

THE IDIOM THAT FIXES IT, from `run_book_single_names.signals_ragged`:

    at = np.flatnonzero(panel.live[i])      # this symbol's own bars
    grid[i, at] = series_of_length_len(at)

So the walk runs over LOCAL indices `j` into the symbol's own bar list, and the
result is scattered back to `at[j]`. The sensor is handed `j - 1`, never `t - 1`.

R9 IS PRESERVED EXACTLY. The original builds the profile at `index = t - 1` and
reads the price at `t - 1`, writing the value at `t`. Here the profile is built
at the symbol's own previous bar `j - 1`, the price is read at that same bar
(`panel.closes[i, at[j - 1]]`), and the value is written at `at[j]`. On a
rectangular panel `at[j] == j == t`, so this is the identical statement; on a
ragged one it is the one that means what the original meant -- "the profile as
of the last bar THIS NAME actually traded".

THE REBUILD CADENCE IS A DECLARED CHANGE, NOT AN INHERITED CONSTANT.
`run_volume_profile.REBUILD_EVERY = 26` is documented there as "once per
session; a 7-session map needs no intra-session rebuild". A daily bar IS a
session, so that justification has no daily referent at all -- the constant
cannot be carried over, it can only be re-chosen. **This port rebuilds the
profile on EVERY bar (`REBUILD_EVERY_DAILY = 1`).** Three reasons, in order:

  1. It removes a free parameter rather than replacing one arbitrary value with
     another. Phase 0.5 exists to move estimators without introducing search,
     and any cadence other than 1 would be a number nobody has registered.
  2. Staleness on daily is not the same object it was at 15m. Carrying 26 over
     would mean the map -- and `bucket_width`, which is the unit `dist_hvn` and
     `dist_lvn` are quoted in -- is up to 26 TRADING DAYS old. Price moves
     several ATR in five weeks, so the distance would be measured in a stale
     unit against a stale node. At 15m the same 26 bars was one session.
  3. The cost is measured, not guessed. On the 1,573-name daily panel:
     `density()` costs 208 us a call and the per-bar consumer work (`levels`
     twice, the mass rank, the imbalance sums) 15 us, over 3,564,667 post-warm-up
     bars -- 13.2 min at cadence 1 against 1.5 min at a monthly cadence. Nine
     times dearer and still a one-off feature build. The `--selftest` prints the
     wall-clock it actually took.

`rebuild_every` is a parameter with a daily default, exactly as
`ragged_features.volume_scores` takes `bod=None`: the self-test reproduces the
15-minute original by PASSING 26, not by branching on the panel shape. There is
no special case for the test anywhere in this file.

EQUIVALENCE IS TESTED, NOT ASSERTED. `--selftest` runs this port and the
untouched original on the RECTANGULAR 15-minute panel and requires
`np.array_equal(..., equal_nan=True)` on all four scores -- bit-identical, not
within a tolerance. Then it runs the port on the real daily ragged panel and
reports the finite-cell census.
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

from backtest_framework.research.terrain import VolumeProfileSensor  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


RP = _load("ragged_panel", "ragged_panel.py")
RF = _load("ragged_features", "ragged_features.py")

PROFILE_SCORES = ("dist_hvn", "dist_lvn", "mass_here", "mass_imbalance")

# Every one of these is D272's value, unchanged, and every one is from the
# sensor's own sanctioned set -- it raises on anything else.
LOOKBACK_BARS = 180        # in `terrain.DAILY_LOOKBACKS`; this is the daily value
BUCKET_ATR = 0.5           # sanctioned set: 0.25 / 0.5
ATR_WINDOW = 182           # calendar-matched to the lookback, as D272 matched it
VOLUME_UNITS = "shares"    # the daily fixture's column IS share count (D187)
HVN_Q, LVN_Q = 0.7, 0.3    # terrain_nulls.HVN_QUANTILE = 0.7; LVN is its mirror

REBUILD_EVERY_DAILY = 1    # DECLARED, not inherited -- see the module docstring
REBUILD_EVERY_15M = 26     # what the original used; the self-test passes this in


# --------------------------------------------------------------------------
# the port
# --------------------------------------------------------------------------


def build_profile_scores(panel, cleaned, vol, start, live=None,
                         rebuild_every=REBUILD_EVERY_DAILY):
    """The four positional scores, on a ragged OR a rectangular panel.

    `live` is the per-symbol bar mask. Omitted, it is taken from the panel and
    falls back to all-live, so a rectangular panel needs no special handling.

    `rebuild_every` is the profile rebuild cadence IN THE SYMBOL'S OWN BARS.
    **It defaults to the daily choice of 1 (rebuild every bar).** Pass 26 to
    reproduce the 15-minute original's once-per-session cadence; the module
    docstring records why 26 is not carried over to daily.

    R9: the profile at the symbol's bar `j` is built with `index = j - 1`, and
    `density()` slices everything after `index` away before any arithmetic
    touches it -- so the no-look-ahead property belongs to the sensor's code
    path, not to this calling convention. The price read is also `j - 1`.

    Returns `(scores, census)`; `census` counts what could not be built and is
    what the caller reports instead of inferring it from NaNs."""
    if rebuild_every < 1:
        raise ValueError(f"rebuild_every must be at least 1 bar, got {rebuild_every}")
    sensor = VolumeProfileSensor(LOOKBACK_BARS, BUCKET_ATR, VOLUME_UNITS,
                                 atr_window=ATR_WINDOW)
    n, T = panel.closes.shape
    if live is None:
        live = getattr(panel, "live", np.ones((n, T), dtype=bool))
    out = {k: np.full((n, T), np.nan) for k in PROFILE_SCORES}
    warm = max(start, sensor.warm_up_bars() + 1)
    census = {"too_short": 0, "no_density": 0, "with_profile": 0, "symbols": n}

    for i, sym in enumerate(panel.symbols):
        bars = cleaned[sym]
        # SCATTER TO ACTUAL BAR INDICES, NOT A CONTIGUOUS SLICE -- a holed
        # symbol's `index_of` span is longer than its bar count, so a slice
        # would misalign the whole series by the width of the gap.
        at = np.flatnonzero(live[i])
        if at.size != len(bars):
            raise AssertionError(
                f"{sym}: {at.size} live bars against {len(bars)} cleaned bars -- "
                "the panel and the bar list disagree")
        m = at.size
        if m <= warm:
            census["too_short"] += 1
            continue
        vols = list(vol[i, at])
        dens = None
        built = False
        for j in range(warm, m):
            if dens is None or (j - warm) % rebuild_every == 0:
                try:
                    dens = sensor.density(bars, j - 1, vols)
                except (ValueError, IndexError):
                    dens = None
            if dens is None:
                continue
            built = True
            t, prev = at[j], at[j - 1]
            px = float(panel.closes[i, prev])
            bw = dens.bucket_width
            if bw <= 0:
                continue
            hvn = dens.levels(HVN_Q, "hvn")
            lvn = dens.levels(LVN_Q, "lvn")
            if hvn:
                near = min(hvn, key=lambda x: abs(px - x))
                out["dist_hvn"][i, t] = (px - near) / bw
            if lvn:
                near = min(lvn, key=lambda x: abs(px - x))
                out["dist_lvn"][i, t] = (px - near) / bw
            occ = [mm for mm in dens.mass if mm > 0.0]
            here = dens.mass_at(px)
            if here is not None and occ:
                out["mass_here"][i, t] = float(sum(1 for mm in occ if mm <= here) / len(occ))
            b = dens.bucket_of(px)
            if b is not None:
                lo = float(sum(dens.mass[:b]))
                hi = float(sum(dens.mass[b + 1:]))
                tot = lo + hi + float(dens.mass[b])
                if tot > 0:
                    out["mass_imbalance"][i, t] = (hi - lo) / tot
        census["with_profile" if built else "no_density"] += 1
    return out, census


# --------------------------------------------------------------------------
# the self-test -- equivalence against the original, on the RECTANGULAR panel
# --------------------------------------------------------------------------


def selftest() -> int:
    print("RAGGED VOLUME-PROFILE PORT -- equivalence against the 15-minute original\n")
    # The original module, and the loaders IT uses -- taken off it rather than
    # re-loaded, so the port cannot be compared against a second instance of the
    # fixture loader that has drifted from the one the original reads.
    P = _load("d272", "run_volume_profile.py")
    V, R = P.V, P.R

    raw_panel, raw_cleaned = R.load_full()
    panel, cleaned = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    vol, _px, _stamps = V.load_volume(panel)
    start = max(P.M.impulse_warm_up_bars(), P.M.warm_up_bars(),
                P.M.MATCHED_MOMENTUM_LOOKBACK)
    print(f"  rectangular 15m panel: {len(panel.symbols)} names x "
          f"{panel.closes.shape[1]:,} bars, start={start}")

    # Every constant this port declares must be the one the original used, or the
    # comparison below is between two different estimators and proves nothing.
    for nm, mine, theirs in (("LOOKBACK_BARS", LOOKBACK_BARS, P.LOOKBACK_BARS),
                             ("BUCKET_ATR", BUCKET_ATR, P.BUCKET_ATR),
                             ("ATR_WINDOW", ATR_WINDOW, P.ATR_WINDOW),
                             ("VOLUME_UNITS", VOLUME_UNITS, P.VOLUME_UNITS),
                             ("HVN_Q", HVN_Q, P.HVN_Q), ("LVN_Q", LVN_Q, P.LVN_Q),
                             ("REBUILD_EVERY_15M", REBUILD_EVERY_15M, P.REBUILD_EVERY),
                             ("PROFILE_SCORES", PROFILE_SCORES, P.PROFILE_SCORES)):
        if mine != theirs:
            raise AssertionError(f"{nm}: this port has {mine!r}, the original {theirs!r}")
    print("  [0] all sensor constants match run_volume_profile bit-for-bit")

    t0 = time.time()
    want = P.build_profile_scores(panel, cleaned, vol, start)
    t1 = time.time()
    # The SAME code path the daily panel uses. `live` is left to the panel (the
    # rectangular Panel has no `live`, so it falls back to all-live) and the only
    # argument that differs from the daily call is the cadence, which is the
    # declared parameter -- there is no branch on panel shape anywhere above.
    got, census = build_profile_scores(panel, cleaned, vol, start,
                                       rebuild_every=REBUILD_EVERY_15M)
    t2 = time.time()
    print(f"      original {t1 - t0:.1f}s, port {t2 - t1:.1f}s, "
          f"census {census}\n")

    bad = 0
    for k in PROFILE_SCORES:
        a, b = want[k], got[k]
        same = np.array_equal(a, b, equal_nan=True)
        d = a - b
        worst = float(np.nanmax(np.abs(d))) if np.isfinite(d).any() else 0.0
        print(f"  {k:16s} identical: {str(same):5s}   finite cells {int(np.isfinite(a).sum()):9,d}"
              f"   max abs diff {worst:.3e}")
        bad += 0 if same else 1
    if bad:
        raise AssertionError(f"{bad} profile score(s) differ from the original")
    print("\n  [1] all four profile scores are BIT-IDENTICAL to "
          "run_volume_profile.build_profile_scores")

    # A self-test that cannot fail is worse than none. Break the panel the way a
    # ragged panel is DIFFERENT -- punch a hole in the live mask -- and the port
    # must refuse rather than quietly index past the end of the bar list.
    holed = np.ones(panel.closes.shape, dtype=bool)
    holed[0, holed.shape[1] // 2] = False
    try:
        build_profile_scores(panel, cleaned, vol, start, live=holed,
                             rebuild_every=REBUILD_EVERY_15M)
    except AssertionError:
        print("  [1b] the live/bar-count guard RAISES on a deliberately holed mask")
    else:
        raise AssertionError("the port accepted a live mask that disagrees with the bars")

    # The cadence must actually bind, or [1] proved only that two identical walks
    # agree and the declared daily change would be an empty gesture. Run on ONE
    # name -- the claim is about the parameter, not about the panel, and 55,004
    # bars x 8 names of every-bar rebuild is 85s to say the same thing.
    one, one_cl = R.subset(raw_panel, raw_cleaned, (R.STRATA["ALL"][0],))
    ov, _, _ = V.load_volume(one)
    slow, _ = build_profile_scores(one, one_cl, ov, start,
                                   rebuild_every=REBUILD_EVERY_15M)
    fast, _ = build_profile_scores(one, one_cl, ov, start,
                                   rebuild_every=REBUILD_EVERY_DAILY)
    if np.array_equal(slow["dist_hvn"], fast["dist_hvn"], equal_nan=True):
        raise AssertionError(
            "rebuild_every=1 produced the SAME result as rebuild_every=26 -- the "
            "cadence is not doing anything, so the declared daily change is empty")
    n_moved = int((~np.isclose(slow["dist_hvn"], fast["dist_hvn"],
                               rtol=0, atol=0, equal_nan=True)).sum())
    tot = int(np.isfinite(slow["dist_hvn"]).sum())
    print(f"  [2] rebuild_every=1 differs from 26 as the declared change requires "
          f"({n_moved:,} of {tot:,} dist_hvn cells move on {one.symbols[0]})")

    # --------------------------------------------------------------------
    # the real daily ragged panel
    # --------------------------------------------------------------------
    print("\nDAILY RAGGED PANEL -- the port on the panel it exists for\n")
    B = _load("d256", "run_book_single_names.py")
    t0 = time.time()
    dpanel, dcleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
    dvol, _dpx = RF.volume_grids(dpanel, dcleaned)
    n, T = dpanel.closes.shape
    holes = sum(1 for s in dpanel.symbols
                if (dpanel.index_of[s][1] - dpanel.index_of[s][0] + 1) != len(dcleaned[s]))
    print(f"  {n:,} names x {T:,} bars, {holes} with internal holes, "
          f"loaded in {time.time() - t0:.0f}s")
    print(f"  rebuilding the profile on EVERY bar (REBUILD_EVERY_DAILY="
          f"{REBUILD_EVERY_DAILY}) ...", flush=True)

    t0 = time.time()
    dsc, dcensus = build_profile_scores(dpanel, dcleaned, dvol, 0)
    wall = time.time() - t0
    print(f"  built in {wall:.0f}s ({wall / 60:.1f} min)\n")

    cells = int(dpanel.live.sum())
    for k in PROFILE_SCORES:
        g = dsc[k]
        if np.isinf(g).any():
            raise AssertionError(f"{k} carries {int(np.isinf(g).sum())} infinities")
        if np.isfinite(g[~dpanel.live]).any():
            raise AssertionError(f"{k} is finite off the live mask")
        fin = int(np.isfinite(g).sum())
        rows = int((np.isfinite(g).sum(axis=1) > 0).sum())
        print(f"  {k:16s} {fin:11,d} finite cells "
              f"({100.0 * fin / cells:5.2f}% of {cells:,} live)   {rows:,} names")
    need = VolumeProfileSensor(LOOKBACK_BARS, BUCKET_ATR, VOLUME_UNITS,
                               atr_window=ATR_WINDOW).warm_up_bars() + 2
    print("\n  no score carries an infinity, and none is finite off the live mask")
    print(f"  names with a profile: {dcensus['with_profile']:,}   "
          f"too short (< {need} bars): {dcensus['too_short']:,}   "
          f"long enough but no density ever built: {dcensus['no_density']:,}")

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
