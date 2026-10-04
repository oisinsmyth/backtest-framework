"""D794 DIAG: what the CPI/jobs-report fade (D776) and base L4 (D781) pay to trade -- the quoted spread at each line's
own fill moments against the crossing its cost line assumes. Spec:
docs/decisions/D794-DIAG-PRE-REG-what-the-cpi-fade-and-l4-pay-to-trade.md (f14b71f8), committed before this file.

    python scripts/diag_d794_fill_cost.py --selftest
    python scripts/diag_d794_fill_cost.py --run          # in-sample quotes only; writes data/diag_d794_fill_cost.json

The fills (the fixtures label a bar by its START, D644): D776 enters at the close of the 08:34 bar (the book just
before 08:35:00 ET) and exits at the close of the 11:00 bar (before 11:01:00); L4 enters at the close of the 18:04 bar
(before 18:05:00) on the evening its exit session opens and exits at the close of the 09:59 bar (before 10:00:00).
- Spread (measure 1): bbo-1s, the last record stamped at or before the fill moment, at most 5 s old.
- Crossing (measure 2): (entry spread + exit spread) / 2 ticks, round trip.
- Realised half-spread (measure 3): tbbo trades in the 5 s after the fill moment on the side a marketable order takes
  (a buy: buyer-initiated prints, price - prior mid; a sell: seller-initiated, prior mid - price), median per fill.
The trades and their sides are D775's and D778's own frames (the frozen runners' sealed loaders). System python
(databento). The quotes are the purchase of data/fill_cost_quotes_manifest.csv; every record is asserted < 2024.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

SPEC_REL = "docs/decisions/D794-DIAG-PRE-REG-what-the-cpi-fade-and-l4-pay-to-trade.md"
OUT = REPO / "data" / "diag_d794_fill_cost.json"
MANIFEST = REPO / "data" / "fill_cost_quotes_manifest.csv"
DEST = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento/fill_cost_2016_2023")
NY = ZoneInfo("America/New_York")
SEAL_NS = pd.Timestamp("2024-01-01", tz="UTC").value
MAX_AGE_S, TBBO_AFTER_S = 5, 5
FEE = 3.0
TICK = {"NQ": 0.25, "MNQ": 0.25, "RTY": 0.1, "M2K": 0.1}
TICK_USD_MICRO = 0.50                                   # MNQ 0.25 x $2; M2K 0.1 x $5
ASSUMED = {"D776": 2.1342422122227602, "L4": 1.5141420888834805}   # D694 cost_lines: NQ and RTY crossing ticks
COST = {"D776": 4.06712110611138, "L4": 3.7570710444417403}
SYMS = {"D776": ("MNQ", "NQ"), "L4": ("M2K", "RTY")}
MICRO_FROM = "2019-05-06"


class D794Error(AssertionError):
    pass


def need(c: bool, msg: str) -> None:
    if not c:
        raise D794Error(msg)


def at(day: str, hh: int, mm: int) -> pd.Timestamp:
    return pd.Timestamp(dt.datetime.combine(dt.date.fromisoformat(day), dt.time(hh, mm), tzinfo=NY)).tz_convert("UTC")


# ================================================================================ the fills
def d776_fills() -> pd.DataFrame:
    import vault_d776_cpi_nfp_fade as Rv
    U, _ = Rv.trades(Rv.in_sample_bars(), Rv.S.release_days())
    R = U[U["is_rel"]]
    need(len(R) == 186 and math.isclose(float(R["gross"].mean()), 34.87903225806452, abs_tol=1e-9), "D775's 186 trades")
    days = [str(d)[:10] for d in R.index]
    return pd.DataFrame({"line": "D776", "day": days, "event": R["event"].to_numpy(), "side": R["side"].to_numpy(float),
                         "gross_usd": R["gross"].to_numpy(float),
                         "entry_t": [at(d, 8, 35) for d in days], "exit_t": [at(d, 11, 1) for d in days],
                         "entry_leg": "D776_entry", "exit_leg": "D776_exit", "entry_day": days, "exit_day": days})


def l4_fills() -> pd.DataFrame:
    import vault_d781_l4_auction_fade as Lv
    D = Lv.frame(Lv.in_sample_bars())
    B = D[D["cvalid"] & D["base"] & (D["s1"] <= "2023-12-31")]
    need(len(B) == 280 and math.isclose(float(B["gross"].mean()), 15.844642857142867, abs_tol=1e-9), "D778's 280 trades")
    s1 = [str(x)[:10] for x in B["s1"]]
    ev = [(dt.date.fromisoformat(s) - dt.timedelta(days=3 if dt.date.fromisoformat(s).weekday() == 0 else 1)).isoformat() for s in s1]
    return pd.DataFrame({"line": "L4", "day": s1, "event": "", "side": B["side"].to_numpy(float), "gross_usd": B["gross"].to_numpy(float),
                         "entry_t": [at(e, 18, 5) for e in ev], "exit_t": [at(s, 10, 0) for s in s1],
                         "entry_leg": "L4_entry", "exit_leg": "L4_exit", "entry_day": ev, "exit_day": s1})


# ================================================================================ the quotes
def manifest() -> dict[tuple[str, str, str, str], Path]:
    with open(MANIFEST, encoding="utf-8", newline="") as fh:
        return {(r["symbol"].split(".")[0], r["schema"], r["leg"], r["day"]): DEST / r["path"] for r in csv.DictReader(fh)}


def load(p: Path | None) -> pd.DataFrame | None:
    if p is None or not p.exists():
        return None
    import databento as db
    df = db.DBNStore.from_file(str(p)).to_df(price_type="float")
    if len(df):
        ts = df.index.view("int64") if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df["ts_recv"]).view("int64")
        need(bool((np.asarray(ts) < SEAL_NS).all()), f"seal: {p.name} holds a record on or after 2024-01-01")
    return df


def spread_at(bbo: pd.DataFrame | None, t: pd.Timestamp, tick: float) -> dict:
    """Measure 1: the last bbo-1s record stamped at or before t, at most MAX_AGE_S old."""
    if bbo is None or not len(bbo):
        return {"spread_ticks": np.nan, "why": "no file or empty"}
    x = bbo[bbo.index <= t]
    if not len(x):
        return {"spread_ticks": np.nan, "why": "no record before the fill"}
    r = x.iloc[-1]
    age = (t - x.index[-1]).total_seconds()
    bid, ask = float(r["bid_px_00"]), float(r["ask_px_00"])
    if age > MAX_AGE_S or not (np.isfinite(bid) and np.isfinite(ask)) or ask <= bid:
        return {"spread_ticks": np.nan, "why": f"stale ({age:.0f} s) or crossed/empty book"}
    return {"spread_ticks": round((ask - bid) / tick, 6), "bid_sz": int(r["bid_sz_00"]), "ask_sz": int(r["ask_sz_00"]), "age_s": age}


def realised(tb: pd.DataFrame | None, t: pd.Timestamp, buy: bool, tick: float) -> float:
    """Measure 3: the median distance of the taking side's prints from the prior mid, in ticks, in (t, t + 5 s]."""
    if tb is None or not len(tb):
        return np.nan
    x = tb[(tb.index > t) & (tb.index <= t + pd.Timedelta(seconds=TBBO_AFTER_S))]
    x = x[x["side"] == ("B" if buy else "A")]
    if not len(x):
        return np.nan
    mid = (x["bid_px_00"].astype(float) + x["ask_px_00"].astype(float)) / 2
    d = (x["price"].astype(float) - mid) if buy else (mid - x["price"].astype(float))
    return float(np.median(d / tick))


def measure(F: pd.DataFrame, sym: str, man: dict) -> pd.DataFrame:
    tick = TICK[sym]
    rows = []
    for _, f in F.iterrows():
        r = {"day": f["day"], "event": f["event"], "gross_usd": f["gross_usd"], "side": f["side"]}
        for leg, t, d, buy in (("entry", f["entry_t"], f["entry_day"], f["side"] > 0), ("exit", f["exit_t"], f["exit_day"], f["side"] < 0)):
            lg = f[f"{leg}_leg"]
            bbo = load(man.get((sym, "bbo-1s", lg, d)))
            tb = load(man.get((sym, "tbbo", lg, d)))
            s = spread_at(bbo, t, tick)
            r[f"{leg}_spread"] = s["spread_ticks"]
            r[f"{leg}_why"] = s.get("why", "")
            r[f"{leg}_touch_min"] = min(s.get("bid_sz", np.nan), s.get("ask_sz", np.nan)) if "bid_sz" in s else np.nan
            r[f"{leg}_realised_half"] = realised(tb, t, bool(buy), tick)
        r["crossing"] = (r["entry_spread"] + r["exit_spread"]) / 2
        rows.append(r)
    return pd.DataFrame(rows)


# ================================================================================ the summary
def q(x: pd.Series) -> dict:
    x = pd.Series(x, dtype=float).dropna()
    if not len(x):
        return {"n": 0}
    return {"n": int(len(x)), "mean": float(x.mean()), "p50": float(x.median()), "p90": float(x.quantile(0.9)),
            "max": float(x.max()), "share_at_1_tick": float((x <= 1.0 + 1e-9).mean())}


def summarise(line: str, M: pd.DataFrame, micro: bool) -> dict:
    out = {"fills": int(len(M)), "entry_spread": q(M["entry_spread"]), "exit_spread": q(M["exit_spread"]),
           "crossing_round_trip": q(M["crossing"]), "entry_realised_half": q(M["entry_realised_half"]),
           "exit_realised_half": q(M["exit_realised_half"]),
           "touch_min_lots": {"entry_p10": float(M["entry_touch_min"].quantile(0.1)) if M["entry_touch_min"].notna().any() else None,
                              "exit_p10": float(M["exit_touch_min"].quantile(0.1)) if M["exit_touch_min"].notna().any() else None},
           "missing": {"entry": M.loc[M["entry_spread"].isna(), "entry_why"].value_counts().to_dict(),
                       "exit": M.loc[M["exit_spread"].isna(), "exit_why"].value_counts().to_dict()},
           "by_year_crossing_mean": {y: round(float(g["crossing"].mean()), 3) for y, g in M.groupby(M["day"].str[:4])}}
    if line == "D776":
        out["by_event_crossing_mean"] = {k: round(float(g["crossing"].mean()), 3) for k, g in M.groupby("event")}
    if micro:
        c = float(M["crossing"].mean())
        cost = FEE + c * TICK_USD_MICRO
        g = float(M["gross_usd"].mean())
        out["cost_line"] = {"assumed_crossing_ticks": ASSUMED[line], "assumed_cost_usd": COST[line],
                            "measured_crossing_ticks_mean": c, "measured_cost_usd": cost,
                            "measured_cost_usd_p50": FEE + float(M["crossing"].median()) * TICK_USD_MICRO,
                            "measured_cost_usd_p90": FEE + float(M["crossing"].quantile(0.9)) * TICK_USD_MICRO,
                            "mean_gross_usd_these_trades": g, "mean_net_at_assumed": g - COST[line], "mean_net_at_measured": g - cost,
                            "breakeven_crossing_ticks": (g - FEE) / TICK_USD_MICRO}
        out["reading"] = ("THE LINE DOES NOT BOOK" if g - cost <= 0 else
                          "COST LINE UNDERSTATES" if c > ASSUMED[line] else "COST LINE HOLDS")
    return out


def run() -> int:
    man = manifest()
    need(len(man) > 0, "the manifest is empty: buy the quotes first")
    res = {"spec": SPEC_REL, "fill_moments_et": {"D776": ["08:35:00", "11:01:00"], "L4": ["18:05:00", "10:00:00"]},
           "deviation": "the pre-registered clock control (the same clock on non-trade days) was not bought: the purchase "
                        "covered trade days only; not computed", "lines": {}}
    for line, F in (("D776", d776_fills()), ("L4", l4_fills())):
        micro, full = SYMS[line]
        Mm = measure(F[F["day"] >= MICRO_FROM].reset_index(drop=True), micro, man)
        Mf = measure(F, full, man)
        ov = Mf[Mf["day"] >= MICRO_FROM].set_index("day")["crossing"]
        both = pd.concat([Mm.set_index("day")["crossing"].rename("micro"), ov.rename("full")], axis=1).dropna()
        res["lines"][line] = {"micro": {"symbol": micro, **summarise(line, Mm, True)},
                              "full_size_reference": {"symbol": full, **summarise(line, Mf, False)},
                              "overlap_micro_vs_full": {"n": int(len(both)), "micro_mean": float(both["micro"].mean()) if len(both) else None,
                                                        "full_mean": float(both["full"].mean()) if len(both) else None,
                                                        "corr": float(both.corr().iloc[0, 1]) if len(both) > 2 else None}}
        cl = res["lines"][line]["micro"]["cost_line"]
        print(f"[{line}] {micro}: entry spread {q(Mm['entry_spread'])}  exit {q(Mm['exit_spread'])}")
        print(f"    crossing RT mean {cl['measured_crossing_ticks_mean']:.3f} ticks vs assumed {cl['assumed_crossing_ticks']:.3f}; "
              f"cost ${cl['measured_cost_usd']:.3f} vs ${cl['assumed_cost_usd']:.3f}; mean net ${cl['mean_net_at_measured']:.2f} "
              f"(at assumed ${cl['mean_net_at_assumed']:.2f}); breakeven {cl['breakeven_crossing_ticks']:.1f} ticks "
              f"-> {res['lines'][line]['micro']['reading']}")
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: None if isinstance(o, float) and not math.isfinite(o) else str(o)) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


# ================================================================================ self-test (synthetic)
def selftest() -> int:
    fired = 0
    t = pd.Timestamp("2023-03-10 13:35:00", tz="UTC")
    idx = pd.DatetimeIndex([t - pd.Timedelta(seconds=s) for s in (3, 1)] + [t + pd.Timedelta(seconds=1)])
    bbo = pd.DataFrame({"bid_px_00": [100.0, 100.0, 90.0], "ask_px_00": [100.5, 100.75, 99.0], "bid_sz_00": [3, 2, 1], "ask_sz_00": [4, 5, 1]}, index=idx)
    s = spread_at(bbo, t, 0.25)
    need(s["spread_ticks"] == 3.0 and s["bid_sz"] == 2, "spread_at must take the last record at or before t")
    need(math.isnan(spread_at(bbo.iloc[:1].set_axis([t - pd.Timedelta(seconds=9)]), t, 0.25)["spread_ticks"]), "a 9 s old record must be stale")
    need(math.isnan(spread_at(bbo.iloc[2:], t, 0.25)["spread_ticks"]), "a record after t must not be used")
    print("  PASS    spread_at: the last record at or before the fill; stale and future records refused")
    tidx = pd.DatetimeIndex([t + pd.Timedelta(seconds=s) for s in (0, 1, 2, 7)])
    tb = pd.DataFrame({"price": [101.0, 100.75, 100.0, 105.0], "side": ["B", "B", "A", "B"], "bid_px_00": [100.0] * 4,
                       "ask_px_00": [100.5] * 4}, index=tidx)
    need(realised(tb, t, True, 0.25) == 2.0, "realised: buy prints in (t, t+5] only (the print AT t and after 5 s excluded)")
    need(realised(tb, t, False, 0.25) == 1.0, "realised: a sell takes seller-initiated prints, mid - price")
    print("  PASS    realised: the taking side's prints in (t, t + 5 s], signed from the prior mid")
    try:
        need(spread_at(bbo, t, 0.25)["spread_ticks"] == 2.0, "canary")
    except D794Error:
        fired += 1
        print("  RAISES  a wrong spread is caught")
    M = pd.DataFrame({"day": ["2020-01-10", "2021-02-05"], "event": ["CPI", "EMPSIT"], "gross_usd": [40.0, 20.0], "side": [1.0, -1.0],
                      "entry_spread": [4.0, 2.0], "exit_spread": [2.0, 2.0], "entry_why": "", "exit_why": "", "entry_touch_min": [1, 2],
                      "exit_touch_min": [3, 4], "entry_realised_half": [1.0, 1.0], "exit_realised_half": [1.0, 1.0]})
    M["crossing"] = (M["entry_spread"] + M["exit_spread"]) / 2
    sm = summarise("D776", M, True)
    need(math.isclose(sm["cost_line"]["measured_crossing_ticks_mean"], 2.5) and math.isclose(sm["cost_line"]["measured_cost_usd"], 4.25)
         and sm["reading"] == "COST LINE UNDERSTATES", "summarise: crossing 2.5 > 2.134 must read UNDERSTATES at $4.25")
    M2 = M.assign(gross_usd=[4.0, 4.0])
    need(summarise("D776", M2, True)["reading"] == "THE LINE DOES NOT BOOK", "a gross below the measured cost must not book")
    M3 = M.assign(entry_spread=[1.0, 1.0], exit_spread=[1.0, 1.0], crossing=[1.0, 1.0])
    need(summarise("D776", M3, True)["reading"] == "COST LINE HOLDS", "crossing 1.0 must hold")
    print("  PASS    the three readings")
    need(at("2023-03-10", 8, 35) == pd.Timestamp("2023-03-10 13:35", tz="UTC") and at("2023-03-13", 8, 35) == pd.Timestamp("2023-03-13 12:35", tz="UTC"),
         "ET -> UTC across the DST change")
    print("  PASS    ET fill moments across the DST change")
    print(f"SELFTEST PASS ({fired} canary raised)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
