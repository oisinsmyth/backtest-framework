"""The opening prize-sizing bar (post hoc, after D660; in-sample only through the runners' sealed loader): what impact
a mechanism must be able to produce to be worth testing, measured on ES and NQ, and the ceiling for mechanisms that
predict the SIZE of the move rather than its direction.

    uv run python scripts/diag_opening_prize_bar.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

1. MARKET: per session, RTH dollar volume (close x volume x the full-size multiplier), the 09:30-10:00 and 10:00-11:00
   shares, sigma of the RTH close-to-close return, of 10:00 -> 11:00 and of 10:30 -> 16:00 (bp), and the micro round
   trip in bp at the 10:00 price. All sessions 2016-01-04 -> 2025-02-28, and the last two years separately.
2. THE BAR: trading the sign of a perfectly known push I (normal, sd s) earns E|I| = 0.8 s per trade gross. Break-even
   s = c / 0.8. Confirmable at 80% power (one-sided 0.025) on n vault trades: 0.8 s - c >= 2.80 x sigma_hold / sqrt(n).
   Designs: daily 60-minute hold (n 390), daily hold to close (n 390), a rare event (n 40, 60-minute hold).
   The square-root law then gives the one-way unanticipated flow that pushes s: Q / V = (s / (Y sigma_d))^2, Y 0.5 and 1.
3. THE SIZE-ONLY ORACLE: D645's B3 (the opening-range breakout: range 09:30-10:00, entry on the first close beyond it
   by 11:29, stop half the range, 60-minute hold, micro cost) on every session, bucketed by the EX-POST expansion
   (the 10:00-16:00 range over the opening range). A perfect size forecaster that trades only the top buckets earns
   what those buckets earn: the ceiling for every size mechanism.
Writes data/opening/prize_bar.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "opening" / "prize_bar.json"
MULT = {"ES": 50.0, "NQ": 20.0}  # full-size $ per point: the market's volume is counted in full-size contracts
Z = 1.959964 + 0.841621
RECENT = "2023-03-01"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.path.insert(0, str(REPO / "scripts"))
    import diag_opening_mechanics as M

    V = M.load_v2()
    R = V.R
    b, use, _ = V.load_inputs(a.data_root, False)
    tab = R.session_table(b, use)
    bars = R.bar_arrays(b)
    out: dict = {"spec": "post hoc, after D660; in-sample only", "hours_in_fixture": [str(b["hhmm"].min()), str(b["hhmm"].max())],
                 "market": {}, "bar": {}, "size_oracle": {}}
    rows = []
    for r in R.ROOTS:
        x = b[(b["root"] == r) & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59") & b["session"].isin(set(use))]
        dv = (x["close"] * x["volume"] * MULT[r])
        g = x.assign(dv=dv).groupby("session")
        tot = g["dv"].sum()
        first = x[x["hhmm"] < "10:00"].assign(dv=dv).groupby("session")["dv"].sum().reindex(tot.index)
        second = x[(x["hhmm"] >= "10:00") & (x["hhmm"] < "11:00")].assign(dv=dv).groupby("session")["dv"].sum().reindex(tot.index)
        c = x.pivot_table(index="session", columns="hhmm", values="close", aggfunc="first")
        close = g["close"].last()
        rd = np.log(close / close.shift(1)) * 1e4
        r60 = np.log(c["10:59"] / c["09:59"]) * 1e4
        rcl = np.log(close / c["10:29"]) * 1e4
        r30 = np.log(close / c["15:29"]) * 1e4
        px10 = c["09:59"]
        cost = R.COST_USD[r] / (R.USD_PER_POINT[r] * px10) * 1e4
        d = pd.DataFrame({"dv": tot, "share_0930": first / tot, "share_1000": second / tot, "rd": rd, "r60": r60,
                          "rcl": rcl, "r30": r30, "cost": cost})
        d = d[d.index >= "2016-01-04"]
        rows.append(d.assign(root=r))
        mk = {}
        for lab, dd in (("all", d), ("recent", d[d.index >= RECENT])):
            mk[lab] = {"sessions": int(len(dd)), "dollar_volume_median_bn": float(dd["dv"].median() / 1e9),
                       "share_0930_1000": float(dd["share_0930"].median()), "share_1000_1100": float(dd["share_1000"].median()),
                       "sigma_daily_bp": float(dd["rd"].std()), "sigma_1000_1100_bp": float(dd["r60"].std()),
                       "sigma_1030_close_bp": float(dd["rcl"].std()), "sigma_1530_close_bp": float(dd["r30"].std()), "cost_micro_rt_bp": float(dd["cost"].median())}
        out["market"][r] = mk
    # 2. the bar, per market on the recent window
    for r in R.ROOTS:
        m = out["market"][r]["recent"]
        c, sd = m["cost_micro_rt_bp"], m["sigma_daily_bp"]
        designs = {"daily_60min": (m["sigma_1000_1100_bp"], 390), "daily_to_close": (m["sigma_1030_close_bp"], 390),
                   "event_40_60min": (m["sigma_1000_1100_bp"], 40)}
        bar = {"break_even_s_bp": c / 0.8}
        for k, (sig, n) in designs.items():
            mde = Z * sig / math.sqrt(n)
            s = (mde + c) / 0.8
            bar[k] = {"sigma_hold_bp": sig, "n": n, "mde_net_bp": mde, "s_needed_bp": s,
                      **{f"flow_share_Y{y}": (s / (y * sd)) ** 2 for y in (0.5, 1.0)},
                      **{f"flow_bn_Y{y}": (s / (y * sd)) ** 2 * m["dollar_volume_median_bn"] for y in (0.5, 1.0)}}
        bar["flow_bn_for_break_even_Y1"] = (bar["break_even_s_bp"] / sd) ** 2 * m["dollar_volume_median_bn"]
        out["bar"][r] = bar
    # 3. the size-only oracle through D645's B3
    trades = []
    for r in R.ROOTS:
        d = tab[r]
        for s in d.index:
            if s < "2016-01-04" or not d.loc[s, "usable"] or (r, s) not in bars:
                continue
            hi, lo = float(d.loc[s, "hi_10:00"]), float(d.loc[s, "lo_10:00"])
            if not (np.isfinite(hi) and np.isfinite(lo) and hi > lo):
                continue
            bb = bars[(r, s)]
            after = bb["m"] >= R.hm("10:00")
            if not after.any():
                continue
            expansion = (bb["h"][after].max() - bb["l"][after].min()) / (hi - lo)
            t = R.b3_trade(bb, "10:00", hi, lo)
            net = gross = np.nan
            if t is not None:
                e, xx, _, D = t
                gross = R.pnl_bp(D, e, xx)
                net = gross - R.COST_USD[r] / R.USD_PER_POINT[r] / e * 1e4
            trades.append((r, s, expansion, gross, net))
    T = pd.DataFrame(trades, columns=["root", "session", "expansion", "gross", "net"])
    T["q"] = pd.qcut(T["expansion"].rank(method="first"), 10, labels=False)
    dec = T.groupby("q").agg(expansion=("expansion", "median"), traded=("net", lambda v: float(v.notna().mean())),
                             net_per_trade=("net", "mean"), gross_per_trade=("gross", "mean"), n=("expansion", "size"))
    dec["net_per_session_row"] = T.assign(n0=T["net"].fillna(0.0)).groupby("q")["n0"].mean()
    top = {}
    for k in (1, 2, 3, 5):
        sel = T[T["q"] >= 10 - k]
        v = sel["net"].dropna()
        n_v = len(v) * 390 / T["session"].nunique()  # the same share of trades over the vault's 390 sessions
        se_v = v.std(ddof=1) / math.sqrt(n_v)
        top[f"top_{k}0pct"] = {"rows": int(len(sel)), "trades": int(len(v)), "net_per_trade": float(v.mean()),
                               "sd_per_trade": float(v.std(ddof=1)),
                               "t": float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))),
                               "net_per_row_all_sessions": float(sel["net"].fillna(0.0).sum() / len(T)),
                               "vault_trades": float(n_v), "vault_mde80_per_trade": float(Z * se_v),
                               "vault_power_normal": float(1 - __import__("scipy.stats").stats.norm.cdf(1.959964 - v.mean() / se_v))}
    allv = T["net"].dropna()
    out["size_oracle"] = {"rows": int(len(T)), "orb_all": {"trades": int(len(allv)), "net_per_trade": float(allv.mean()),
                                                           "gross_per_trade": float(T["gross"].dropna().mean())},
                          "deciles": dec.round(4).reset_index().to_dict("records"), "top": top,
                          "note": "ex-post expansion = (10:00-16:00 high - low) / (09:30-10:00 range); an oracle, not a signal"}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"market": out["market"], "bar": out["bar"]}, indent=1, default=lambda v: round(v, 3)))
    print(dec.round(2).to_string())
    print(json.dumps(top, indent=1))
    print("ORB all:", out["size_oracle"]["orb_all"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
