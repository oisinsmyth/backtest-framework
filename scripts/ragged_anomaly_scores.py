"""Axis G -- DOCUMENTED CROSS-SECTIONAL ANOMALIES, on the daily ragged panel.

    uv run python scripts/ragged_anomaly_scores.py --selftest

NOTHING HERE SCORES A CELL. It computes ten candidates and proves they are
causal.

WHY THIS AXIS EXISTS. D288 mined CONSTRUCTION features -- candle geometry,
volume profile, band levels -- because those were what the codebase already
computed. Almost none of the best-documented cross-sectional equity predictors
were in its 31, and several of the missing ones are specifically SHORT-side
effects, which is the personal track's actual objective. That was a candidate
list chosen by code availability rather than by hypothesis quality.

THE SCOPED CLOSURE THIS COLLIDES WITH, QUOTED RATHER THAN GLOSSED.
`docs/FINDINGS.md` section 8 closes "classic short anomalies for liquid names":

    "the premium is absent, not merely expensive, in value-weighted liquid
     names"

That closure is scoped to VALUE-WEIGHTED LIQUID names. This fixture is
EQUAL-WEIGHTED, DEAD-INCLUSIVE, 1,573 names, 35.7% dead, and carries the small
and illiquid tail that scope excludes -- which is precisely where MAX, IVOL and
Amihud are documented to live. The closure therefore does not bind here, and
saying so in the module rather than in a footnote is the point: a revisit
wearing a new universe is still a revisit unless the scope difference is stated.

THE MARKET RETURN IS BUILT FROM THE PANEL'S OWN CROSS-SECTION, equal-weighted
over the names live at that bar. It uses bar t's returns to form bar t's score,
which is known at the close of t and is lagged once by the book -- the same
convention every other family here uses. There is no external index, so the
fixture stays self-contained and no survivorship enters through a benchmark.

UNLAGGED, matching every other family. `top_n` and `neutral_book` lag themselves.

Causality is proven by the TRUNCATION AUDIT from `ragged_vol_scores` -- delete
every bar after T0, recompute, require bit-identity before T0. That audit caught
a real defect in E and F: a symbol-level warm-up guard made bar t's score depend
on the name's TOTAL bar count, which on a 35.7%-dead panel is survivorship
entering through a warm-up check.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import warnings
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


V = _load("ragged_vol_scores", "ragged_vol_scores.py")

ANOMALY_SCORES = ("max_ret_21", "ivol_21", "beta_63", "rev_5", "rev_21",
                  "mom_252_21", "skew_63", "amihud_21", "price_log",
                  "dist_52w_high")

MAX_BARS = 21
IVOL_BARS = 21
BETA_BARS = 63
REV_FAST = 5
REV_SLOW = 21
MOM_LONG = 252
MOM_SKIP = 21
SKEW_BARS = 63
AMIHUD_BARS = 21
HIGH_BARS = 252


def market_return(log_returns, live):
    """Equal-weight cross-sectional mean log return per bar.

    From the PANEL'S OWN live cross-section, not an external index. A benchmark
    fetched from elsewhere would carry its own survivorship and its own calendar;
    this one is definitionally aligned with the names being scored.
    """
    r = np.where(live, log_returns, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN bars are real
        m = np.nanmean(r, axis=0)
    return np.where(np.isfinite(m), m, np.nan)


def as_traded_factor(panel, events_path):
    """Undo the fixture's back-adjustment, per bar. adjusted -> AS TRADED.

    THE PRICE LEVEL IN A BACK-ADJUSTED SERIES IS LOOK-AHEAD, and `price_log` is
    the only candidate that reads a level rather than a ratio. The fixture's meta
    states the convention: "prices DIVIDED by the product of ratios effective
    after the bar, volumes MULTIPLIED". So `adjusted[t]` CHANGES whenever a
    future split happens, and the number a trader saw at t is
    `adjusted[t] * prod(ratios dated after t)`.

    THE TRUNCATION AUDIT CANNOT CATCH THIS. The contamination is baked into the
    FIXTURE at build time, not into the score code, so recomputing from the same
    adjusted grid reproduces it exactly. It was found by a bounds check instead:
    DRYS closes at $79,615,200 in 2010, which is correct cumulative adjustment
    for DryShips' reverse-split sequence and is not a price anyone could trade.

    Returns and ratios are IMMUNE -- the factor cancels -- which is why every
    other candidate here is unaffected. Dollar volume is immune too, because
    volumes are multiplied by exactly what prices are divided by.

    Reconstructing uses future split dates, but the RESULT is the price that
    actually traded at t, which is knowable at t. Undoing hindsight is not
    borrowing it.
    """
    import json
    splits = json.loads(Path(events_path).read_text()).get("splits", {})
    n, T = panel.closes.shape
    dates = [str(d) for d in panel.dates]
    factor = np.ones((n, T))
    for i, sym in enumerate(panel.symbols):
        ev = splits.get(sym) or []
        if not ev:
            continue
        pairs = sorted((str(d), float(f)) for d, f in ev)
        run = 1.0
        k = len(pairs) - 1
        for t in range(T - 1, -1, -1):
            while k >= 0 and pairs[k][0] > dates[t]:
                run *= pairs[k][1]
                k -= 1
            factor[i, t] = run
    return factor


def _beta_ivol(r, m, w):
    """Trailing beta of r on m, and the residual sigma, over w own bars.

    Both from the SAME window and the same pairs, so `ivol` is the dispersion
    left after `beta` has taken what the market explains -- not an independently
    windowed quantity that happens to share a name.
    """
    R = V._windows(r, w)
    M = V._windows(m, w)
    ok = np.isfinite(R) & np.isfinite(M)
    n = ok.sum(axis=1)
    good = n >= int(np.ceil(V.MIN_FRAC * w))
    R = np.where(ok, R, np.nan)
    M = np.where(ok, M, np.nan)
    with warnings.catch_warnings(), np.errstate(invalid="ignore", divide="ignore"):
        warnings.simplefilter("ignore", RuntimeWarning)
        mr = np.nanmean(R, axis=1, keepdims=True)
        mm = np.nanmean(M, axis=1, keepdims=True)
        cov = np.nanmean((R - mr) * (M - mm), axis=1)
        var = np.nanmean((M - mm) ** 2, axis=1)
        beta = np.where(var > 0, cov / var, np.nan)
        resid = R - mr - beta[:, None] * (M - mm)
        ivol = np.sqrt(np.nanmean(resid ** 2, axis=1))
    return np.where(good, beta, np.nan), np.where(good, ivol, np.nan)


def _skew(x, w):
    def fn(win):
        mu = np.nanmean(win, axis=1, keepdims=True)
        sd = np.nanstd(win, axis=1)
        c = np.nanmean((win - mu) ** 3, axis=1)
        return np.where(sd > 0, c / sd ** 3, np.nan)
    return V._trail(x, w, fn)


def anomaly_scores(g, panel, live, vol=None, mkt=None, px_factor=None):
    """G1-G10. `vol` is the share-volume grid; only `amihud_21` needs it.

    `mkt` MUST BE PASSED WHEN SCORING A SYMBOL SUBSET. The market return is a
    CROSS-SECTIONAL aggregate over every live name, so a worker handling 197 of
    1,573 symbols that recomputed it from its own rows would regress each name
    on a 197-name "market" -- silently changing `beta_63` and `ivol_21` into
    different estimators, with no error and no NaN to notice. This is the one
    quantity in the build that is not row-local, and process chunking is exactly
    what would have broken it.
    """
    C = g["close"]
    H = g["high"]
    n, T = C.shape
    out = {k: np.full((n, T), np.nan) for k in ANOMALY_SCORES}
    if mkt is None:
        mkt = market_return(panel.total_log_returns, live)
    assert mkt.shape[0] == C.shape[1], (
        f"market return has {mkt.shape[0]} bars against {C.shape[1]} columns")

    mean = lambda w: np.nanmean(w, axis=1)                          # noqa: E731
    for i in range(n):
        at = np.flatnonzero(live[i])
        # THE GUARD IS 2 BARS, NOT A WARM-UP LENGTH. A symbol-level test on a
        # TOTAL bar count makes bar t's score depend on how many bars the name
        # has in FUTURE, and on a 35.7%-dead panel the short-history names are
        # the ones that delist. The truncation audit caught exactly this in the
        # E and F families. Warm-up belongs to `_trail`, per score, per bar.
        if at.size < 2:
            continue
        c, h = C[i, at], H[i, at]
        prev = np.concatenate([[np.nan], c[:-1]])
        with np.errstate(invalid="ignore", divide="ignore"):
            r = np.log(c / prev)
            simple = c / prev - 1.0

        out["max_ret_21"][i, at] = V._trail(
            simple, MAX_BARS, lambda w: np.nanmax(w, axis=1))
        out["rev_5"][i, at] = V._trail(r, REV_FAST, lambda w: np.nansum(w, axis=1))
        out["rev_21"][i, at] = V._trail(r, REV_SLOW, lambda w: np.nansum(w, axis=1))
        out["skew_63"][i, at] = _skew(r, SKEW_BARS)
        # G9 ON THE AS-TRADED PRICE, not the back-adjusted one -- see
        # `as_traded_factor`. Without this, G9 ranks DRYS as the most expensive
        # name in the universe at $79.6m a share and is really measuring
        # cumulative reverse-split history.
        traded = c if px_factor is None else c * px_factor[i, at]
        out["price_log"][i, at] = np.where(traded > 0, np.log(traded), np.nan)

        beta, ivol_b = _beta_ivol(r, mkt[at], BETA_BARS)
        out["beta_63"][i, at] = beta
        _, ivol = _beta_ivol(r, mkt[at], IVOL_BARS)
        out["ivol_21"][i, at] = ivol

        # G6. 12-1 momentum: the long window with the most recent month SKIPPED,
        # because the last month is short-term REVERSAL (G5) and folding the two
        # together is how a momentum score ends up measuring its own opposite.
        cum = V._trail(r, MOM_LONG, lambda w: np.nansum(w, axis=1))
        recent = V._trail(r, MOM_SKIP, lambda w: np.nansum(w, axis=1))
        out["mom_252_21"][i, at] = cum - recent

        if vol is not None:
            dv = vol[i, at] * c
            with np.errstate(invalid="ignore", divide="ignore"):
                il = np.where(dv > 0, np.abs(simple) / dv, np.nan)
            out["amihud_21"][i, at] = V._trail(il, AMIHUD_BARS, mean)

        hi = V._trail(h, HIGH_BARS, lambda w: np.nanmax(w, axis=1))
        with np.errstate(invalid="ignore", divide="ignore"):
            out["dist_52w_high"][i, at] = np.where(
                (hi > 0) & (c > 0), np.log(c / hi), np.nan)

    for k in out:
        out[k][~live] = np.nan
        out[k] = np.where(np.isfinite(out[k]), out[k], np.nan)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not a.selftest:
        print(__doc__)
        return 0

    B = _load("d256", "run_book_single_names.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    P1 = _load("d280p1", "d280_forecast_precheck.py")
    RF = _load("ragged_features", "ragged_features.py")

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=0.0)
    g = P1.build_grids(panel, cleaned)
    live = panel.live
    vol, _ = RF.volume_grids(panel, cleaned, live=live)
    print(f"loaded {live.shape[0]} names x {live.shape[1]} bars in "
          f"{time.time() - t0:.0f}s", flush=True)

    mkt = market_return(panel.total_log_returns, live)
    fin = np.isfinite(mkt)
    print(f"\n  [1] equal-weight market return: {int(fin.sum()):,} bars, "
          f"mean {np.nanmean(mkt) * 1e4:+.2f} bp/bar, "
          f"sd {np.nanstd(mkt) * 1e4:.1f} bp")

    pxf = as_traded_factor(panel, B.EVENTS)
    aff = int((pxf != 1.0).any(axis=1).sum())
    print(f"  as-traded reconstruction: {aff} of {live.shape[0]} names carry a "
          f"split adjustment; max factor {pxf.max():,.1f}, min {pxf.min():.2e}")

    def build(T0):
        if T0 is None:
            return anomaly_scores(g, panel, live, vol=vol, px_factor=pxf)
        # A TRUNCATED PANEL SHIM. The market return must be RECOMPUTED from the
        # truncated cross-section, not sliced -- slicing would be fine here since
        # it is causal, but recomputing is what proves it.
        class _P:
            total_log_returns = panel.total_log_returns[:, :T0]
        return anomaly_scores({k: v[:, :T0] for k, v in g.items()}, _P(),
                              live[:, :T0], vol=vol[:, :T0],
                              px_factor=pxf[:, :T0])

    scores = build(None)
    print("\n  [2] coverage and bounds")
    for k in ANOMALY_SCORES:
        v = scores[k]
        assert not np.isinf(v).any(), f"{k}: infinities"
        assert not np.isfinite(v[~live]).any(), f"{k}: finite off the live mask"
        assert np.isfinite(v).sum() > 0, f"{k}: produced nothing"
        print(f"      {k:16s} {int(np.isfinite(v).sum()):>9,} cells   "
              f"[{np.nanmin(v):+.4f}, {np.nanmax(v):+.4f}]")
    assert np.nanmin(scores["ivol_21"]) >= 0.0, "ivol went negative"
    hi_px = float(np.nanmax(scores["price_log"]))
    assert hi_px < 14.0, (
        f"price_log reaches {hi_px:.2f} (${np.exp(hi_px):,.0f}/share) -- the "
        "as-traded reconstruction has regressed and G9 is reading back-adjusted "
        "prices again")
    print(f"      highest as-traded close: ${np.exp(hi_px):,.2f}")
    assert np.nanmax(scores["dist_52w_high"]) <= 1e-9, (
        "dist_52w_high above 0 means the close exceeded its own trailing high")

    T0 = int(live.shape[1] * 0.7)
    print(f"\n  [3] truncation audit at column {T0} of {live.shape[1]}")
    bad = V.truncation_audit(build, live, T0, ANOMALY_SCORES, "G")
    assert bad == 0, f"{bad} G score(s) READ THE FUTURE"

    print(f"\nOK  {len(ANOMALY_SCORES)} G scores, all causal  "
          f"({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
