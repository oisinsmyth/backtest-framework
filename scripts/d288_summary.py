"""D288 -- the full 31-candidate table, both legs, against both floors.

    uv run python scripts/d288_summary.py

Reads `data/d288_mine.json` and `data/d288_gateA_floor.json`. Computes nothing
and gates nothing; it is the reporting view the decision record quotes.

BOTH LEGS, ALWAYS, and the peak cell they came from. A spread alone hides
whether a candidate sorts winners from losers or merely "rises less" from "rises
more" -- which is the distinction D286 established and the whole reason D288
exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MINE = json.loads((REPO / "data" / "d288_mine.json").read_text())
FLOOR = json.loads((REPO / "data" / "d288_gateA_floor.json").read_text())

AXIS = MINE["axes"]
RES = MINE["results"]
COVER = MINE["coverage"]
BASE = MINE["base_cells"]

WHAT = {
    "hist_L": "Impulse log-band histogram: signed acceleration of price vs its own band",
    "md": "Impulse log-band LEVEL: where price sits inside its band",
    "macd_hist": "MACD histogram: MACD line minus its signal line",
    "macd_line": "MACD line: fast EMA minus slow EMA",
    "trailing_return": "plain trailing return over the lookback",
    "upper_wick": "(high - max(open,close)) / range: rejection of higher prices",
    "lower_wick": "(min(open,close) - low) / range: rejection of lower prices",
    "wick_asym": "upper wick minus lower wick: which side did the rejecting",
    "body_frac": "|close - open| / range: how much of the range the body took",
    "close_in_range": "(close - low) / range: where the session settled",
    "range_frac": "(high - low) / close: realised intrabar volatility, scale-free",
    "gap_frac": "open / prev close - 1: the overnight leg alone",
    "rel_vol": "log volume minus its trailing 20-bar median",
    "vol_z": "the same, divided by its trailing dispersion",
    "dollar_vol": "the same in money rather than shares",
    "vol_trend": "OLS slope of rel_vol over 8 bars: participation building or fading",
    "signed_vol": "rel_vol signed by the direction of the trailing 8-bar move",
    "dist_hvn": "distance to the nearest high-volume node, in ATR/2",
    "dist_lvn": "distance to the nearest low-volume node",
    "mass_here": "traded volume in the bucket at the current price",
    "mass_imbalance": "traded mass above the price minus below it",
    "atr_norm": "14-bar mean true range over price: volatility LEVEL",
    "cs_spread": "trailing 21-bar Corwin-Schultz half-spread: liquidity",
    "rvol21": "21-bar standard deviation of log returns",
    "vol_ratio": "5-bar vol over 63-bar vol: volatility REGIME, not level",
    "range_over_atr": "today's range against the name's own 14-bar norm",
    "on_mean": "trailing 21-bar mean OVERNIGHT return (open/prev close)",
    "id_mean": "trailing 21-bar mean INTRADAY return (close/open)",
    "on_share": "overnight share of the name's total absolute move",
    "on_minus_id": "on_mean minus id_mean: divergence between the two sessions",
    "on_persist": "mean sign(gap_t) * sign(gap_t-1): does the gap direction repeat",
}


def peak_cell(rec, key):
    """The (N, k, row) maximising `key` across the reported grid."""
    best = None
    for N, r in rec.items():
        for k, h in r["horizons"].items():
            if best is None or h[key] > best[2][key]:
                best = (int(N), int(k), h)
    return best


def main() -> int:
    fs, ft = FLOOR["floor_p95"], FLOOR["floor_p95_t"]
    ot = FLOOR["observed_t"]

    print(f"D288 -- 31 pre-registered candidates, dead-inclusive daily panel")
    print(f"  base {BASE:,} warm live cells | floors: spread {fs:+.1f} bp, "
          f"t {ft:+.2f} (p95 of 200 shared-offset draws)")
    print(f"  PEAK-t CELL shown: the grid position with the most evidence, which "
          f"is NOT always the biggest number\n")

    hdr = (f"{'ax':2s} {'candidate':16s} {'N':>3s} {'k':>3s} {'long':>8s} "
           f"{'short':>8s} {'spread':>8s} {'t':>7s} {'cov':>6s}  what it is")
    print(hdr)
    print("-" * len(hdr))

    order = sorted(MINE["results"], key=lambda c: -ot[c])
    for c in order:
        N, k, h = peak_cell(RES[c], "t")
        flag = ""
        if ot[c] > ft:
            flag = " <= CLEARS t FLOOR"
        print(f"{AXIS[c]:2s} {c:16s} {N:3d} {k:3d} {h['long_bp']:+8.1f} "
              f"{h['short_bp']:+8.1f} {h['spread_bp']:+8.1f} {h['t']:+7.2f} "
              f"{COVER[c] / BASE:5.1%}  {WHAT[c]}{flag}")

    neg = [(c, N, k, h) for c in RES
           for N, r in RES[c].items()
           for k, h in r["horizons"].items()
           if h["short_bp"] < 0 and int(k) >= 5]
    print(f"\nSHORT LEG NEGATIVE at k>=5 -- the pre-registered falsifier for M4: "
          f"{len(neg)} cell(s)")
    for c, N, k, h in sorted(neg, key=lambda x: x[3]["short_bp"])[:10]:
        print(f"  {AXIS[c]:2s} {c:16s} N={N:>2s} k={k:>2s}  short {h['short_bp']:+7.1f} bp"
              f"  spread {h['spread_bp']:+7.1f}  t {h['t']:+.2f}")

    print(f"\nCLEARS THE t FLOOR: {FLOOR['clears_t_floor']}")
    print(f"CLEARS THE SPREAD FLOOR: {FLOOR['clears_spread_floor'] or 'none'}")
    print(f"GATE A SURVIVORS (must clear BOTH): {FLOOR['survivors'] or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
