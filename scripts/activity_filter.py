"""The ACTIVITY FILTER -- a standing, reusable instrument. Kept by the principal on 2026-09-13 when D506 closed the construction it came from.

    from activity_filter import activity_score, causal_threshold, in_play, from_session_table

WHAT IT IS. A causal, root-agnostic measure of how active the session before the open was:

    score_d = sqrt( (night_range_d / median_20(night_range)) x (night_volume_d / median_20(night_volume)) )

with both medians taken over the trailing 20 sessions ENDING AT d-1, so the score is known before
09:30 and never reads the session it labels. "In play" is score_d >= the trailing 250-session 90th
percentile of the score, also ending at d-1. Both windows are arguments; the defaults are what D506
measured.

WHAT IT IS FOR -- the SURVIVAL layer. Trading only the in-play decile cuts R11's P3a (breaches of the
2%-of-account daily limit, per year) by three to five fold, because both prop death mechanisms are
counted in EXPOSURE-DAYS and a filter that removes 90% of the sessions removes 90% of the chances to
die -- even though each session it keeps is individually MORE dangerous:

    ZB   14.00 breaches/yr on all sessions  ->  2.71 on the in-play decile
    ZN    2.00                              ->  0.71
    NQ    0.57 (the long day drift)         ->  0.00

    Reach for it when a construction fails P3a and NOTHING ELSE. That is the whole indication.

WHAT IT IS NOT FOR -- direction. D506 scored it against two signals the repo owns (the day drift and
D484's log MACD) on eight roots, 2016-2023:

    the fee it saves       +0.85 points of (2p-1)  -- positive in 16 of 16 cells, ~ +0.10 of Sharpe
    the accuracy it costs  -2.09 points            -- negative in 11 of 16 cells
    net (the primary)      -0.0334 mean            -- negative in  9 of 16; family p95 +0.2192 vs an
                                                      observed maximum of +0.0620 (97.8% of offsets beat it)

    And the UNTRADEABLE bound -- conditioning on the day's REALISED range, which nobody can do in
    advance -- is -0.0018. There is no prize even with perfect foreknowledge of the day's size, so
    this is not a forecasting failure: the day session after a big night is simply harder to call
    (FINDINGS s70, s71, s72: by 09:30 the information is spent).

MEASURED PROPERTIES, for anyone sizing a study on it (D506, 2016-2023, eight roots):
    rho(score, |day move| it precedes)  0.09 to 0.20      -- it does predict size, weakly
    rho(score, its own next value)      0.19 to 0.41      -- volatility clustering; it persists
    E|day move|, decile 10 / decile 1   x1.15 to x1.94
    fee as a share of E|M|              ES 3.3->1.8%, NQ 2.1->1.2%, YM 4.4->2.3%, 6E 9.7->7.1%

    uv run python scripts/activity_filter.py --selftest
"""
from __future__ import annotations
import numpy as np
import pandas as pd

MED_N, THR_N, THR_Q = 20, 250, 0.90                      # the defaults D506 measured
NIGHT_SEGMENTS = ["h18", "h19", "h20", "h21", "h22", "h23", "h00", "h01", "h02", "h03", "h04", "h05", "h06", "h07", "h08"]


def activity_score(night_range, night_volume, med_n: int = MED_N) -> np.ndarray:
    """The causal activity score. Both inputs are per-session arrays in any units; the score is a ratio, so units cancel and the
    result is invariant to a constant rescaling of either input (asserted in --selftest)."""
    r = np.asarray(night_range, float); v = np.asarray(night_volume, float)
    assert r.shape == v.shape and r.ndim == 1, "night_range and night_volume must be one-dimensional and the same length"
    mr = pd.Series(r).rolling(med_n, min_periods=med_n).median().shift(1).to_numpy()
    mv = pd.Series(v).rolling(med_n, min_periods=med_n).median().shift(1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.sqrt(np.clip(r / mr, 0, None) * np.clip(v / mv, 0, None))


def causal_threshold(score, n: int = THR_N, q: float = THR_Q) -> np.ndarray:
    """The trailing quantile the score is compared against, ending at d-1. NaN over the warm-up, so no session before it can be in play."""
    return pd.Series(np.asarray(score, float)).rolling(n, min_periods=n).quantile(q).shift(1).to_numpy()


def in_play(score, thr=None, n: int = THR_N, q: float = THR_Q) -> np.ndarray:
    """Boolean mask: the session is in the top causal decile of activity. Sessions inside either warm-up are False, never True."""
    s = np.asarray(score, float); t = causal_threshold(s, n, q) if thr is None else np.asarray(thr, float)
    return np.isfinite(s) & np.isfinite(t) & (s >= t)


def from_session_table(t: pd.DataFrame, mult: float = 1.0, segments=NIGHT_SEGMENTS, med_n: int = MED_N, n: int = THR_N, q: float = THR_Q):
    """Convenience for a D467-style hourly session table (one root, sorted by day, one row per session).
    Returns (score, threshold, mask, night_range, night_volume). `mult` only scales the range into dollars for reporting; the score is unaffected."""
    hi = t[[f"{s}_h" for s in segments]].to_numpy(float); lo = t[[f"{s}_l" for s in segments]].to_numpy(float)
    vol = t[[f"{s}_v" for s in segments]].to_numpy(float)
    with np.errstate(invalid="ignore"):
        rng = (np.nanmax(hi, axis=1) - np.nanmin(lo, axis=1)) * mult
    v = np.nansum(vol, axis=1)
    s = activity_score(rng, v, med_n); thr = causal_threshold(s, n, q)
    return s, thr, in_play(s, thr), rng, v


def cmd_selftest():
    print("activity_filter selftest")
    rng = np.random.default_rng(11); n = 1400
    state = rng.random(n) < 0.12
    r = np.exp(rng.normal(0, .3, n)) * np.where(state, 2.2, 1.0) * 100
    v = np.exp(rng.normal(0, .3, n)) * np.where(state, 2.2, 1.0) * 1000
    s = activity_score(r, v); thr = causal_threshold(s); m = in_play(s, thr)
    # [A] causality: nothing at or before t0 moves when everything after t0 is replaced
    t0 = 800; r2, v2 = r.copy(), v.copy(); r2[t0:] *= 9.0; v2[t0:] *= 9.0
    s2 = activity_score(r2, v2); assert np.array_equal(np.nan_to_num(s[:t0]), np.nan_to_num(s2[:t0])), "the score read the future"
    assert not np.array_equal(np.nan_to_num(s[t0:]), np.nan_to_num(s2[t0:])), "the score must react to its own session"
    m2 = in_play(s2); assert np.array_equal(m[:t0], m2[:t0]), "the mask read the future"
    # [B] the warm-ups bind: no session before MED_N + THR_N can be in play
    assert not m[:MED_N + THR_N - 1].any(), int(np.flatnonzero(m)[0])
    # [C] it fires on about a decile of the sessions it can judge
    share = float(m[np.isfinite(thr)].mean()); assert 0.06 < share < 0.16, share
    # [D] scale invariance: the score is a ratio, so rescaling either input changes nothing
    assert np.allclose(np.nan_to_num(activity_score(r * 137.0, v * 0.004)), np.nan_to_num(s)), "the score must be scale-free"
    # [E] it recovers the planted state, and the check can fail: an unplanted series recovers nothing
    assert state[m].mean() > 0.8, state[m].mean()
    flat_r = np.exp(rng.normal(0, .3, n)) * 100; flat_v = np.exp(rng.normal(0, .3, n)) * 1000
    mf = in_play(activity_score(flat_r, flat_v)); assert state[mf].mean() < 0.35, state[mf].mean()
    # [F] the argument defaults are the measured ones, so a caller who passes nothing gets D506's instrument
    assert (MED_N, THR_N, THR_Q) == (20, 250, 0.90)
    print(f"  A causality (score and mask)  B warm-ups bind  C fires on {100*share:.1f}%  D scale-free  E recovers the planted state "
          f"({100*state[m].mean():.0f}%) and not an unplanted one ({100*state[mf].mean():.0f}%)  F defaults are D506's\n  all pass")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    else:
        ap.print_help()
