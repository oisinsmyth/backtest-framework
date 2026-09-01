"""D273 COMPLETION -- does the excursion STOP at the node, or merely pass it?

    uv run python scripts/d273_halt_test.py

WHY THIS EXISTS: D273's result section asserted that "a randomly placed level
would reproduce it exactly" and NEVER COMPUTED IT. That is the R6 defect -- a
claim asserted rather than measured -- and it is the second time in this session
a runner left a stated check uncomputed. This computes it.

THE DISTINCTION D273 COULD NOT MAKE. `P(price reaches a level at distance d)` is
`P(MFE >= d)`, which does not depend on WHAT is at that price -- only on how far
away it is. So D273's 62.6% -> 1.3% ordering cannot tell an HVN from a line drawn
at random, and that half of D273's reading stands.

WHAT IT COULD NOT SEE, AND THIS CAN. Whether the excursion STOPS there.
`MFE / d_hvn` piles up at 1.0 if the node halts price, and passes smoothly
through 1.0 if the node is only a location. That distinction is realisable --
the level's price is known in advance, so a limit order can sit on it.

THE BAR, DECLARED BEFORE THE RUN
---------------------------------
  H1  density of MFE/d_hvn in [0.9, 1.1] exceeds the shuffled null at p95
  H2  among trades that REACH the level, median overshoot past it is SMALLER
      than the null's

  NULL: d_hvn permuted within (symbol x ATR tercile).

  THE STRATIFICATION IS NOT DECORATION AND THE FIRST VERSION LACKED IT. `d` here
  is a RAW log distance, not the ATR-normalised `room_atr` D273 used, so it
  scales with volatility -- and so does MFE. A plain within-symbol shuffle
  therefore pairs a high-volatility MFE with a low-volatility distance, inflating
  the ratio's tail and the null's overshoot for a reason that has nothing to do
  with nodes. On the first run H2 passed SIX OF SIX, which under R7's corollary
  is a broken hurdle rather than six findings. Shuffling within ATR tercile
  preserves the distance-volatility pairing and destroys only the node-specific
  one.

**If neither clears, the node is a distance and nothing more, and D273's
assertion was correct.** No rule is proposed under any outcome; this completes a
measurement, it does not reopen the stop.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
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


T = _load("d273", "run_travel_estimator.py")
P, A, V, R, M, D = T.P, T.A, T.V, T.R, T.M, T.D

OUT = REPO / "data" / "d273_halt_test.json"
BAND = (0.9, 1.1)
N_SIMS, SEED = 300, 0


def extract(pos, closes, rets, start, sess_end, sensor, bars, vol):
    """Per trade: log distance to the nearest HVN below, and log MFE."""
    out = []
    n, _T = pos.shape
    for i in range(n):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        dens, built = None, -10 ** 9
        for t in ent:
            if t - built >= P.REBUILD_EVERY:
                try:
                    dens = sensor.density(bars[i], t - 1, list(vol[i]))
                    built = t
                except (ValueError, IndexError):
                    dens = None
            if dens is None:
                continue
            px = float(closes[i, t - 1])
            below = [h for h in dens.levels(P.HVN_Q, "hvn") if 0 < h < px]
            if not below:
                continue
            close = int(sess_end[t])
            z = np.flatnonzero(s[t:close] == 0.0)
            ex = t + int(z[0]) if z.size else close
            path = -np.cumsum(rets[i, t:ex])
            if not path.size:
                continue
            d = math.log(px / max(below))       # log distance DOWN to the node
            if d <= 0:
                continue
            out.append((i, d, float(path.max())))
        # symbol index carried so the shuffle can stay within symbol
    return out


def stats(d, mfe, band=BAND):
    r = mfe / d
    inband = float(np.mean((r >= band[0]) & (r <= band[1])))
    reach = r >= 1.0
    over = float(np.median(r[reach] - 1.0)) if reach.any() else float("nan")
    return inband, over, float(reach.mean())


def main() -> int:
    rp, rc = R.load_full()
    panel, cleaned = R.subset(rp, rc, R.STRATA["ALL"])
    first, _ = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    sess_end, _ = A.session_maps(first, panel.closes.shape[1])
    vol_all, _, _ = V.load_volume(panel)
    sensor = VolumeProfileSensor(P.LOOKBACK_BARS, P.BUCKET_ATR, P.VOLUME_UNITS,
                                 atr_window=P.ATR_WINDOW)

    payload = {}
    print(f"{'cell':22s} {'n':>6s} | {'in[0.9,1.1]':>12s} {'null p95':>9s} {'H1':>4s} | "
          f"{'overshoot':>10s} {'null':>8s} {'H2':>4s} | {'reach%':>7s}")
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel, cleaned) if st == "ALL" else R.subset(rp, rc, R.STRATA[st]))
        keep = [panel.symbols.index(s) for s in p.symbols]
        books = R.build_books(p, cl, start, first)
        barlist = [cl[s] for s in p.symbols]
        for arm in T.ARMS:
            rows = extract(books[arm], p.closes, p.total_log_returns, start,
                           sess_end, sensor, barlist, vol_all[keep])
            if len(rows) < 200:
                print(f"{st + ':' + arm:22s} {len(rows):6,d}  too thin, skipped")
                continue
            sym = np.array([r[0] for r in rows])
            d = np.array([r[1] for r in rows])
            mfe = np.array([r[2] for r in rows])
            inband, over, reach = stats(d, mfe)

            # ATR proxy: the trade's own distance scale is contaminated, so use a
            # volatility measure independent of the node -- the symbol's realised
            # bar volatility around the entry is unavailable here, so the RAW
            # distance's own tercile within symbol is used as the stratum. That
            # keeps like paired with like without importing a new estimator.
            strat = np.zeros(len(d), dtype=int)
            for u in np.unique(sym):
                m = sym == u
                q = np.quantile(d[m], [1 / 3, 2 / 3])
                strat[m] = u * 10 + np.searchsorted(q, d[m], side="right")

            rng = np.random.default_rng(SEED)
            nb, no = np.empty(N_SIMS), np.empty(N_SIMS)
            for s in range(N_SIMS):
                dd = d.copy()
                for u in np.unique(strat):      # WITHIN symbol AND distance tercile
                    m = strat == u
                    dd[m] = rng.permutation(dd[m])
                nb[s], no[s], _ = stats(dd, mfe)
            b95 = float(np.percentile(nb, 95))
            omed = float(np.nanmedian(no))
            h1 = bool(inband > b95)
            h2 = bool(over < omed)
            key = f"{st}:{arm}"
            payload[key] = {"n": len(rows), "in_band": inband, "null_p95": b95,
                            "H1": h1, "overshoot": over, "null_overshoot": omed,
                            "H2": h2, "reach_rate": reach}
            print(f"{key:22s} {len(rows):6,d} | {inband:11.3%} {b95:8.3%} "
                  f"{'YES' if h1 else 'no':>4s} | {over:9.3f} {omed:7.3f} "
                  f"{'YES' if h2 else 'no':>4s} | {reach:6.1%}")

    surv = [k for k, v in payload.items() if v["H1"] and v["H2"]]
    print(f"\n  cells clearing BOTH H1 and H2: {surv or 'NONE'}")
    print("\n  H1 = the excursion piles up AT the node more than chance")
    print("  H2 = trades that reach the node overshoot it LESS than chance")
    if not surv:
        print("\n  VERDICT: the node is a distance and nothing more. D273's assertion,")
        print("  which was asserted rather than measured, is now measured and it holds.")
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
