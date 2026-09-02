"""D288 axis F -- OVERNIGHT VERSUS INTRADAY, on the daily ragged panel.

    uv run python scripts/ragged_session_scores.py --selftest

NOTHING HERE SCORES A CELL. It builds the five F candidates D288 pre-registered
at `fa098a2`.

WHY THE AXIS EXISTS. D280 part 4 found the whole `hist_L` effect sat OVERNIGHT,
and D286 found the intraday session reversing it. Every study since has treated
that as a property of one score. F asks whether the SPLIT ITSELF ranks names:
`gap_frac` (B7) is one night, F is where a name habitually gets repriced.

    r_on[k] = open[k]  / close[k-1] - 1      while the market was shut
    r_id[k] = close[k] / open[k]    - 1      while it was open

A GAP ACROSS A HOLE IS NOT AN OVERNIGHT RETURN, and this is the one place the
distinction bites. 134 of 1,573 names carry internal gaps -- halts, provider
holes -- and for those the previous OWN bar can be weeks earlier. `open[k] /
close[k-1]` across such a hole is a multi-session move being counted as one
night, which would load F1 with exactly the delisting-adjacent names the fixture
was built to include. Those cells are DROPPED, and the count is reported.

The same masking is why F does not simply reuse `gap_frac`: B7 divides by the
previous GRID column, which is the right thing for a shape statistic and the
wrong thing for a session decomposition.

UNLAGGED, matching every other family. `top_n` and `neutral_book` lag themselves.

Causality is proven by the same TRUNCATION AUDIT the E family uses -- delete
every bar after T0, recompute, require bit-identity before T0 -- reusing
`ragged_vol_scores.truncation_audit` rather than a second copy of it.
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


V = _load("ragged_vol_scores", "ragged_vol_scores.py")

SESSION_SCORES = ("on_mean", "id_mean", "on_share", "on_minus_id", "on_persist")

WINDOW = 21             # one trading month, the unit D280 part 4 measured in


def session_scores(g, live, report=None):
    """F1-F5. `report` is an optional dict that collects the masked-gap count."""
    O, C = g["open"], g["close"]
    n, T = C.shape
    out = {k: np.full((n, T), np.nan) for k in SESSION_SCORES}
    dropped = kept = 0

    for i in range(n):
        at = np.flatnonzero(live[i])
        # 2 BARS, NOT 23. Same defect the truncation audit found in the E family:
        # a symbol-level test on a TOTAL bar count makes bar t's score depend on
        # how many bars the name has in future, and on a 35.7%-dead panel the
        # short-history names are the ones that delist. `V._trail` decides
        # warm-up per bar from bars already seen.
        if at.size < 2:
            continue
        o, c = O[i, at], C[i, at]
        prev = np.concatenate([[np.nan], c[:-1]])

        # ONLY CONSECUTIVE OWN BARS CARRY AN OVERNIGHT. See the docstring.
        adjacent = np.zeros(at.size, dtype=bool)
        adjacent[1:] = np.diff(at) == 1
        dropped += int((~adjacent).sum()) - 1        # bar 0 has no night at all
        kept += int(adjacent.sum())

        with np.errstate(invalid="ignore", divide="ignore"):
            r_on = np.where(adjacent & (prev > 0), o / prev - 1.0, np.nan)
            r_id = np.where(o > 0, c / o - 1.0, np.nan)
        # an intraday leg whose night was dropped is still a valid intraday leg,
        # but pairing them per bar is what F3 and F4 compare -- so F3/F4 use the
        # nights that survived and F2 uses every session.
        mean = lambda w: np.nanmean(w, axis=1)                        # noqa: E731
        on = V._trail(r_on, WINDOW, mean)
        idr = V._trail(r_id, WINDOW, mean)
        out["on_mean"][i, at] = on
        out["id_mean"][i, at] = idr
        out["on_minus_id"][i, at] = on - idr

        a_on = V._trail(np.abs(r_on), WINDOW, mean)
        a_id = V._trail(np.abs(r_id), WINDOW, mean)
        with np.errstate(invalid="ignore", divide="ignore"):
            tot = a_on + a_id
            out["on_share"][i, at] = np.where(tot > 0, a_on / tot, np.nan)

        # F5. sign(t) * sign(t-1) averaged: +1 if the gap direction always
        # repeats, -1 if it always alternates, 0 if it is a coin. A night whose
        # predecessor was dropped has no pair, so it contributes nothing.
        s = np.sign(r_on)
        pair = np.full(at.size, np.nan)
        both = adjacent[1:] & adjacent[:-1]
        pair[1:] = np.where(both, s[1:] * s[:-1], np.nan)
        out["on_persist"][i, at] = V._trail(pair, WINDOW, mean)

    for k in out:
        out[k][~live] = np.nan
        out[k] = np.where(np.isfinite(out[k]), out[k], np.nan)
    if report is not None:
        report["nights_kept"] = kept
        report["nights_dropped"] = dropped
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

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=0.0)
    g = P1.build_grids(panel, cleaned)
    live = panel.live
    print(f"loaded {panel.closes.shape[0]} names x {panel.closes.shape[1]} bars "
          f"in {time.time() - t0:.0f}s", flush=True)

    def build(T0):
        if T0 is None:
            return session_scores(g, live)
        return session_scores({k: v[:, :T0] for k, v in g.items()}, live[:, :T0])

    rep = {}
    scores = session_scores(g, live, report=rep)
    tot = rep["nights_kept"] + rep["nights_dropped"]
    print(f"\n  [1] session split: {rep['nights_kept']:,} overnights usable, "
          f"{rep['nights_dropped']:,} dropped across internal holes "
          f"({rep['nights_dropped'] / tot:.2%})")

    print("\n  [2] coverage and bounds")
    for k in SESSION_SCORES:
        v = scores[k]
        assert not np.isinf(v).any(), f"{k}: infinities"
        assert not np.isfinite(v[~live]).any(), f"{k}: finite off the live mask"
        fin = np.isfinite(v)
        assert fin.sum() > 0, f"{k}: produced nothing"
        print(f"      {k:16s} {int(fin.sum()):>9,} cells   "
              f"[{np.nanmin(v):+.4f}, {np.nanmax(v):+.4f}]")
    lo, hi = np.nanmin(scores["on_share"]), np.nanmax(scores["on_share"])
    assert -1e-12 <= lo and hi <= 1 + 1e-12, f"on_share left [0,1]: {lo}, {hi}"
    lo, hi = np.nanmin(scores["on_persist"]), np.nanmax(scores["on_persist"])
    assert -1 - 1e-12 <= lo and hi <= 1 + 1e-12, f"on_persist left [-1,1]"

    T0 = int(live.shape[1] * 0.7)
    print(f"\n  [3] truncation audit at column {T0} of {live.shape[1]}")
    bad = V.truncation_audit(build, live, T0, SESSION_SCORES, "F")
    assert bad == 0, f"{bad} F score(s) READ THE FUTURE"

    print(f"\nOK  {len(SESSION_SCORES)} F scores, all causal  "
          f"({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
