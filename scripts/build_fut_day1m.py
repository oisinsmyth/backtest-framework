"""The 1-MINUTE day-session fixture: 420 bars a session, from the same archive as the 5-minute one.

    python scripts/build_fut_day1m.py --self-test
    python scripts/build_fut_day1m.py --decode     # re-decodes all 26 ohlcv-1m files
    python scripts/build_fut_day1m.py --build
    python scripts/build_fut_day1m.py --status

**Data layer only. No study, no signal, no label.** If a function here computes a return, it is a
bug -- this produces bars and nothing else.

WHY A SEPARATE FIXTURE RATHER THAN A DEEPER READ OF THE 5-MINUTE ONE
--------------------------------------------------------------------
`fut_day5m`'s decode step AGGREGATES to 5-minute bars before caching, so the minute detail is
already gone from `temp/day5m_decode`. The 1-minute bars have to come from the raw
`ohlcv-1m.dbn.zst` archive again -- 26 files, 11.38 GiB.

WHAT THIS IS FOR, AND THE HONEST SIZE OF THE PRIZE
--------------------------------------------------
D528 ADDENDUM 15 found the grace-window axis DEGENERATE on 5-minute bars: an 84-bar session
minus a 20-bar warm-up, a 20-bar leading exclusion and a 30-bar trailing reservation leaves
FOURTEEN eligible signal bars, at which W=15 and W=20 select identical bars and produce
identical numbers. That is arithmetic, not sampling, so no quantity of 5-minute data fixes it.

**ADDENDUM 15 quoted "23x" for this fixture and that number is the RAW ELIGIBLE BAR COUNT, which
overstates the statistical gain. It is corrected here before anything is run.** Adjacent
candidate bars share almost all of their window, so the count is not n_eff:

    bar-matched   (H=10, TAU=20, W in bars)   14 -> ~320 eligible bars   raw 23x
                  but a 10-minute window tiles a 390-minute session ~39 times against ~7.8 for
                  the 5-minute version's 50-minute window, so INDEPENDENT windows rise ~5x.
                  And sigma per 10-minute window is ~sqrt(5) SMALLER than per 50-minute window,
                  so the target shrinks ~2.24x against a FIXED $4.58 round trip: cost/payoff
                  gets 2.24x WORSE. This tests the same construction at a different SCALE.
    clock-matched (H=50, TAU=100, W scaled)   14 -> ~40 eligible bars    raw 2.9x
                  same 50-minute window, so the same sigma and the same economics; the gain is
                  purely denser sampling of the SAME trade, and the overlap is 49/50 so n_eff
                  rises by much less than 2.9x.

Both legs are worth running and they answer different questions, so this fixture serves both.
The prediction on record, before the study runs: the bar-matched leg RESOLVES the grace question
and resolves it NEGATIVE, because a 2.24x worse cost ratio swamps a $0.3-0.6 edge.

WHAT IS INHERITED RATHER THAN RE-DERIVED
----------------------------------------
Everything. `build_fut_day5m.set_bar_minutes(1)` rebinds the bar width, the bars-per-session
count, the decode cache directory AND filename tag, and both output paths together, so this file
cannot half-retarget the builder and write 1-minute bars into the committed 5-minute fixture.
The id validity windows (D520), the front month taken from `fut_breadth_hourly` rather than
re-derived, the `present`/`same_front` flags (D506), the duplicate-minute guard and the coverage
report all come from that module unchanged.

ONE PROPERTY THAT IS GENUINELY DIFFERENT AT ONE MINUTE, and it is the reason `--status` matters
more here: `reaggregate` is a no-op in expectation at this width (one archive bar per
instrument-minute maps to one fixture bar), so `n` should be exactly 1 on every row. That is
asserted -- if any row carries n > 1 the archive holds duplicate instrument-minutes and the
duplicate guard upstream is not doing what its name says.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_fut_day5m as B                        # noqa: E402
from build_fut_breadth_hourly import GateError     # noqa: E402

BAR_MIN = 1


def P(*a, **k):
    print(*a, **k, flush=True)


def retarget():
    B.set_bar_minutes(BAR_MIN)
    if B.BAR_MIN != 1 or B.N_BARS != 420 or B.SUFFIX != "1m":
        raise GateError(f"[RETARGET] {B.BAR_MIN}m, {B.N_BARS} bars, suffix {B.SUFFIX}")
    if "day5m" in str(B.CACHE) or "day5m" in str(B.OUT) or "day5m" in str(B.META):
        raise GateError(f"[RETARGET] still pointed at the 5-minute paths: {B.CACHE}, {B.OUT}")
    return B


def self_test() -> int:
    ok = True

    # [1] the retarget must move ALL of it -- width, count, suffix and both paths.
    retarget()
    P(f"  [1] retarget -> {B.BAR_MIN}m, {B.N_BARS} bars/session, cache {B.CACHE.name}, "
      f"out {B.OUT.name}                      OK")

    # [2] bar_of must be the identity on the session offset at this width, and -1 outside.
    got = [int(B.bar_of(B.DAY_LO)), int(B.bar_of(B.DAY_LO + 1)), int(B.bar_of(B.DAY_HI)),
           int(B.bar_of(B.DAY_LO - 1)), int(B.bar_of(B.DAY_HI + 1))]
    want = [0, 1, 419, -1, -1]
    P(f"  [2] bar_of at 09:00/09:01/15:59/08:59/16:00 = {got} (want {want})"
      f"                {'OK' if got == want else 'FAIL'}")
    ok &= got == want

    # [3] AND THE 5-MINUTE MAPPING MUST BREAK UNDER THIS RETARGET -- a check that passes under
    #     both widths would not be testing the retarget at all.
    five = int(B.bar_of(B.DAY_LO + 7))
    P(f"  [3] minute 09:07 -> bar {five} at 1m (it is bar 1 at 5m, so the retarget took)"
      f"       {'OK' if five == 7 else 'FAIL'}")
    ok &= five == 7

    # [4] the width guard must refuse a width that does not divide the session.
    try:
        B.set_bar_minutes(11)
        P("  [4] set_bar_minutes(11) did NOT raise                                           FAIL")
        ok = False
    except GateError:
        P("  [4] set_bar_minutes(11) raises: 11 does not divide 420                            OK")
    retarget()

    # [5] reaggregate at width 1 must be the identity, and must still catch a duplicate minute.
    df = pd.DataFrame({"root": ["ES"] * 3, "contract": ["ESZ0"] * 3, "day": ["2020-01-02"] * 3,
                       "bar": [0, 1, 2], "minute": [540, 541, 542],
                       "open": [1.0, 2.0, 3.0], "high": [1.5, 2.5, 3.5],
                       "low": [0.5, 1.5, 2.5], "close": [1.2, 2.2, 3.2],
                       "volume": [10, 20, 30]})
    g = B.reaggregate(df)
    idn = (len(g) == 3 and g["n"].eq(1).all()
           and np.allclose(sorted(g["close"]), [1.2, 2.2, 3.2]))
    P(f"  [5] reaggregate is the identity at 1m ({len(g)} rows, n all 1)"
      f"                            {'OK' if idn else 'FAIL'}")
    ok &= idn
    try:
        B.reaggregate(pd.concat([df, df.iloc[[0]]], ignore_index=True))
        P("  [6] the duplicate-minute guard did NOT fire                                     FAIL")
        ok = False
    except GateError:
        P("  [6] the duplicate-minute guard still fires on a repeated minute                   OK")

    # [7] it must also equal the slow reference, on a TIE-HEAVY input (CLAUDE.md: ties are where
    #     a rewrite and its reference disagree).
    tie = df.copy()
    tie["close"] = 1.0
    tie["open"] = 1.0
    a = B.reaggregate(tie).sort_values(B.KEY).reset_index(drop=True)
    b = B.reaggregate_ref(tie).sort_values(B.KEY).reset_index(drop=True)
    eq = a[["high", "low", "volume", "n", "open", "close"]].equals(
        b[["high", "low", "volume", "n", "open", "close"]])
    P(f"  [7] reaggregate == reaggregate_ref on a tie-heavy input"
      f"                                  {'OK' if eq else 'FAIL'}")
    ok &= eq

    P(f"\n  {'ALL SELF-TESTS PASS' if ok else 'SELF-TESTS FAILED'}")
    return 0 if ok else 1


def status() -> int:
    retarget()
    files = B.ohlcv_files()
    have = sorted(B.CACHE.glob(f"*.{B.SUFFIX}.parquet"))
    gb = sum(p.stat().st_size for p in have) / 2 ** 30 if have else 0.0
    P(f"  raw        {len(files)} ohlcv-1m files, "
      f"{sum(f.stat().st_size for f in files) / 2**30:.2f} GiB")
    P(f"  decoded    {len(have)} of {len(files)} slices, {gb:.2f} GiB in {B.CACHE}")
    if B.OUT.exists():
        d = pd.read_parquet(B.OUT, columns=["root", "day", "bar", "n"])
        P(f"  fixture    {len(d):,} bars, {d['root'].nunique()} roots, "
          f"{d.groupby(['root', 'day']).ngroups:,} root-sessions, "
          f"{B.OUT.stat().st_size / 2**30:.2f} GiB")
        bad = int((d["n"] != 1).sum())
        P(f"  n == 1     {len(d) - bad:,} of {len(d):,} rows"
          + ("" if not bad else f"   *** {bad:,} rows carry n > 1 ***"))
    else:
        P(f"  fixture    not built ({B.OUT})")
    return 0


def build() -> int:
    retarget()
    rc = B.do_build()
    # THE WIDTH-SPECIFIC GATE: at one minute the reaggregation is a no-op in expectation, so a
    # row with n > 1 means the archive holds duplicate instrument-minutes. Checked on the OUTPUT
    # rather than trusted from the guard upstream.
    d = pd.read_parquet(B.OUT, columns=["root", "day", "bar", "n"])
    bad = int((d["n"] != 1).sum())
    if bad:
        raise GateError(f"[N] {bad:,} of {len(d):,} fixture rows carry n != 1, but at 1-minute "
                        f"width one archive bar maps to one fixture bar")
    P(f"\n  [N] all {len(d):,} rows carry n == 1, as 1-minute width requires")
    per = d.groupby(["root"]).agg(bars=("bar", "size"), sessions=("day", "nunique"))
    per["bars_per_session"] = per["bars"] / per["sessions"]
    P(f"  [BARS/SESSION] median {per['bars_per_session'].median():.1f} of {B.N_BARS} possible; "
      f"max {per['bars_per_session'].max():.1f}")
    if per["bars_per_session"].max() > B.N_BARS:
        raise GateError("[BARS/SESSION] a root exceeds the bars a session can hold")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--decode", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if not (a.self_test or a.decode or a.build or a.status):
        ap.error("choose --self-test / --decode / --build / --status")
    if a.self_test:
        rc = self_test()
        if rc:
            return rc
    if a.decode:
        retarget()
        P(f"  decoding at {B.BAR_MIN}-minute width into {B.CACHE}")
        rc = B.do_decode(a.limit)
        if rc:
            return rc
    if a.build:
        rc = build()
        if rc:
            return rc
    if a.status:
        return status()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
