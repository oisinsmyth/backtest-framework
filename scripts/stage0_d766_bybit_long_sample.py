"""D766 supplement (written after the one run, disclosed in the result): the pre-registered "longer sample".

D766 §3 reports "the same gates on Bybit's inverse BTCUSD funding, from 2018-11". The runner
(`stage0_d766_crowded_leverage.py`, 3f7c331f) read BTC prices only from 2019-09-01, and its 250-session burn-in counts
eligible price days, so its Bybit inverse line began on 2020-09-02, no longer than the main sample. This script
calls the runner's own functions unchanged and widens only the price window to the Bybit inverse series' start
(2018-11-15), so the line is scored as the pre-registration described. It is reported, never gating.

Run: uv run --no-sync python scripts/stage0_d766_bybit_long_sample.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d766_crowded_leverage as R  # noqa: E402

OUT = REPO / "data" / "stage0_d766_bybit_long_sample.json"
FIRST = "2018-11-15"


def load_btc_from(first: str) -> pd.DataFrame:
    parts = []
    for ch in pd.read_csv(R.BTC, usecols=["root", "day", "ts_utc", "close"], dtype={"day": str, "ts_utc": str}, chunksize=500_000, encoding="utf-8"):
        ch = ch[(ch["root"] == "BTC") & (ch["day"] < R.SEAL) & (ch["day"] >= first)]
        if len(ch):
            parts.append(ch)
    b = pd.concat(parts, ignore_index=True)
    R.seal(b["day"], "btc")
    b["tm"] = R.D4.to_minutes(b["ts_utc"])
    return b.sort_values(["day", "tm"]).reset_index(drop=True)


def main() -> int:
    R.need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    fraw = pd.read_csv(R.FUND, usecols=["venue", "symbol", "settlement_utc", "funding_rate"], dtype={"settlement_utc": str}, encoding="utf-8")
    fraw = fraw[fraw["settlement_utc"] < R.SEAL]
    cc = json.loads(R.COSTS.read_text(encoding="utf-8"))["roots"]["BTC"]["micro"]
    cost = float(cc["commission_rt_usd"]["value"] + cc["crossing_ticks_rt"][cc["default_line"]]["value"] * cc["tick_usd"])
    upp = float(cc["usd_per_point"])
    mv = R.day_moves(load_btc_from(FIRST))
    fund_b = R.load_funding("bybit_inverse", "BTCUSD", fraw)
    ev = R.evaluate(fund_b, mv, upp, cost)
    rot, gd, c, tr = ev["rot"], ev["gross"], ev["c"], ev["tr"]
    res = {"record": "D766 supplement", "venue": "bybit_inverse BTCUSD", "prices_from": FIRST,
           "sessions": {"n": ev["n"], "L": ev["n_L"], "S": ev["n_S"], "first": str(ev["days"][0]), "last": str(ev["days"][-1])},
           "G1": dict(rot, **{"pass": bool(rot["A"] > 0 and rot["A"] > rot["p95"])}),
           "G2": {"gross": gd, "t_nw": ev["t_nw"], "cost": cost, "pass": bool(gd["mean"] >= cost and ev["t_nw"] >= R.T_MIN)},
           "G3": {"episodes": len(ev["episodes"]), "pass": ev["g3"]},
           "sides": {"L_short": R.D3.dist(-ev["r"][c == -1]), "S_long": R.D3.dist(ev["r"][c == 1])},
           "by_year": {k: {"n": int(len(v)), "net": float(v["net"].sum())} for k, v in tr.groupby("year")},
           "size": ev["size"], "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
    print(f"[D766 supplement] bybit inverse from {res['sessions']['first']}: n {ev['n']} (L {ev['n_L']}, S {ev['n_S']}); "
          f"A {rot['A']:+.2f} (p95 {rot['p95']:+.2f}, p {rot['p_one_sided']:.3f}); NW t {ev['t_nw']:.2f}; episodes {len(ev['episodes'])}")
    print("  sides", json.dumps(res["sides"]["L_short"]["mean"]), json.dumps(res["sides"]["S_long"]["mean"]), "years", json.dumps(res["by_year"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
