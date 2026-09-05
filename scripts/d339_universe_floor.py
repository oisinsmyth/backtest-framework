"""D339 -- the universe floor: raw price >= $5 at t-1 AND the dv28 keep mask.

The floor is a DEFINITION, declared in docs/decisions/D339-a-universe-floor-
price-and-dollar-volume.md section 2:

    keep[t, i] = (RAW_CLOSE[t-1, i] >= 5) & keep_mask(DV, finT, 28, bad_low=True)[t, i]

Two semantics share the one `keep` array and are never averaged:

  replace  -- `apply_floor_replace` puts NaN into the SCORE where ~keep, before
              ranking, exactly as the F0 deal filter does. The ranker lags the
              score one bar, so the floor effective at bar t is keep[t-1]: the
              as-traded price at t-2 and dollar volume through t-2. Pre-reg [A]
              says "the floor at t-1"; this is that.
  starve   -- `gate_starved` is dv28's construction: keep[t] applied INSIDE the
              rank cut, so the excluded name leaves a hole in the gate.

Bar 0 has no prior close inside the panel: the price floor is not applied
there (see `price_floor_pass`); the census's arithmetic makes the same choice.

NaN raw close at t-1. A name that is live at t (finT[t]) has a finite r1 at t,
which needs a finite close at t-1, so a NaN prior close on a live name-bar
should not happen; where it does, the CHOICE is: NaN at t-1 fails the price
floor only if the name was live at t-1 (a name that was not trading cannot pass
a price test it never took; a name that was not live at t-1 is not floored on
price -- the dv mask still applies). `price_floor_detail` counts both cases so
the runner prints them. The census (scripts/d339_census.py) treats NaN as NOT
failing; the two agree whenever the count of "live at t-1 with NaN close" is
zero, and [G] holds the share to the census's number to 1e-9.

`bind(X, Y)` hands this module the d320 (keep_mask) and d323 (gate_from)
modules; nothing here loads the runner chain.
"""

from __future__ import annotations

import numpy as np

PX_MIN, DV_PCT = 5.0, 28.0
_X = _Y = None


def bind(X, Y):
    """Give the module its two collaborators: X.keep_mask and Y.gate_from."""
    global _X, _Y
    _X, _Y = X, Y


def raw_price_factor(panel, events):
    """(T, n): product of split ratios in events["splits"][sym] dated strictly
    AFTER panel.dates[t]; 1.0 where none. The census's `raw_factor` logic --
    the runner asserts the two agree on the full grid. Entries are
    [date_str, ratio]; the fixture divides prices by that product on the way
    in, so multiplying undoes it: CLOSE * factor is the price that traded."""
    dates, symbols = list(panel.dates), list(panel.symbols)
    T, n = len(dates), len(symbols)
    F = np.ones((T, n))
    darr = np.array(dates)
    for i, s in enumerate(symbols):
        for d, ratio in events["splits"].get(s, []):
            k = int(np.searchsorted(darr, d[:10], side="left"))  # dates[t] < d  <=>  t < k
            if k > 0:
                F[:k, i] *= float(ratio)
    return F


def price_floor_pass(RAW_CLOSE, finT, px_min=PX_MIN):
    """(T, n) bool: RAW_CLOSE[t-1] >= px_min. NaN at t-1 fails only if live at
    t-1 (see module docstring).

    ROW 0 PASSES. Bar 0 has no prior close inside the panel, so the price floor
    is not applied there (the dv mask still is -- and keeps everything at bar 0,
    DV[0] being NaN). 826 names are live at bar 0; failing them would (i) break
    the census reproduction [G] by exactly those name-bars and (ii) under
    replace semantics mask score[:, 0], which the lagged ranker reads at bar 1,
    emptying bar 1's gate for a reason unrelated to liquidity."""
    T, n = RAW_CLOSE.shape
    ok = np.ones((T, n), bool)
    prev = RAW_CLOSE[:-1]
    fin = np.isfinite(prev)
    with np.errstate(invalid="ignore"):
        ge = prev >= px_min
    # finite: the comparison decides; NaN: pass iff NOT live at t-1
    ok[1:] = np.where(fin, ge, ~finT[:-1])
    return ok


def price_floor_detail(RAW_CLOSE, finT):
    """Counts behind the NaN choice, over name-bars live at t; and the names
    live at bar 0, where the price floor is not applied (no prior close)."""
    prev_nan = ~np.isfinite(RAW_CLOSE[:-1])
    live_t = finT[1:]
    return dict(live_at_bar0=int(finT[0].sum()),
                nan_prev_live_now=int((prev_nan & live_t).sum()),
                nan_prev_live_now_and_live_prev=int((prev_nan & live_t & finT[:-1]).sum()),
                nan_prev_live_now_not_live_prev=int((prev_nan & live_t & ~finT[:-1]).sum()))


def floor_mask(RAW_CLOSE, DV, finT, px_min=PX_MIN, dv_pct=DV_PCT):
    """keep (T, n) bool = price floor at t-1 AND the dv28 keep mask (DV is
    roll_mean_T's already-lagged mean, so keep_mask(DV)[t] reads through t-1)."""
    assert _X is not None, "call bind(X, Y) first"
    return price_floor_pass(RAW_CLOSE, finT, px_min) & _X.keep_mask(DV, finT, dv_pct, True)


def apply_floor_replace(score_nT, keep_Tn):
    """Replacement semantics: NaN into the (n, T) score where ~keep. The masked
    score then goes through rank_single / rank_composite as the F0 filter does."""
    assert score_nT.shape == keep_Tn.T.shape, (score_nT.shape, keep_Tn.shape)
    return np.where(keep_Tn.T, score_nT, np.nan)


def gate_starved(rankT, finT, keep):
    """Starve semantics: dv28's gate_from(rankT, finT, keep) -- the floor inside
    the rank cut, the excluded name a hole."""
    assert _Y is not None, "call bind(X, Y) first"
    return _Y.gate_from(rankT, finT, keep)


def floor_share(keep, finT):
    """Share of LIVE name-bars failing the floor."""
    return float((~keep & finT).sum() / finT.sum())


def keep_independent(CLOSE, VOL, RAW, finT, w, px_min=PX_MIN, dv_pct=DV_PCT):
    """SECOND IMPLEMENTATION of the floor for assertion [C]. Never calls
    roll_mean_T or keep_mask: a plain loop over names builds each name's
    trailing-w mean of close x volume (finite count >= w/3, else NaN), lagged
    one bar; a plain loop over bars takes the 28th percentile of the live
    finite cross-section (skipped below 20 names) and drops x <= q; the price
    floor reads RAW_CLOSE[t-1] with the module's NaN choice."""
    T, n = CLOSE.shape
    DVi = np.full((T, n), np.nan)
    X_ = CLOSE * VOL
    for i in range(n):
        x = X_[:, i]
        ok = np.isfinite(x)
        cs = np.concatenate([[0.0], np.cumsum(np.where(ok, x, 0.0))])
        cn = np.concatenate([[0], np.cumsum(ok)])
        j = np.arange(w, T + 1)
        cnt = cn[j] - cn[j - w]
        out = np.full(T, np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[j - 1] = np.where(cnt >= w / 3, (cs[j] - cs[j - w]) / np.maximum(cnt, 1), np.nan)
        DVi[1:, i] = out[:-1]
    keep_dv = np.ones((T, n), bool)
    for t in range(T):
        m = finT[t] & np.isfinite(DVi[t])
        if m.sum() < 20:
            continue
        x = DVi[t][m]
        q = np.percentile(x, dv_pct)
        keep_dv[t, np.flatnonzero(m)[x <= q]] = False
    return price_floor_pass(CLOSE * RAW, finT, px_min) & keep_dv
