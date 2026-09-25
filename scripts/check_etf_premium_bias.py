"""The ETF-premium trade-price bias check (settlement ledger A8's C2 clause, decided 2026-09-24): how far the Alpha
Vantage 1-minute CLOSE, a last TRADE, sits from the quote MID. C2's premium is priced off that close. IEX's free
historical TOPS quotes measure it on ten sample days, all in-sample (2018-06-13 → 2024-07-17, before the cut
2025-03-01).

It is a measurement, not a hypothesis test. Nothing here reads a NAV, a premium, a futures price or a flow.

STEP 1, THE BAR LABEL (a known-answer check first). Is an Alpha Vantage bar stamped T the minute [T, T+60 s) or
[T-60 s, T)? For every bar, the close is compared with IEX's last trade in each candidate minute. The label is the
one with the larger share of exact price matches. It must win by at least 10 points on the pooled sample, or the
script raises.

STEP 2, THE BIAS. At each bar's end instant, IEX's standing quote is rebuilt from every Quote Update since the open.
It is used only if two-sided with ask > bid, and not older than 60 s (the deposit's staleness rule, line 200).
    bias_bp = (AV close - IEX mid) / IEX mid x 1e4
PRIMARY: only minutes where IEX's spread is ONE TICK. There, IEX's best bid and offer equals the national best
(the NBBO cannot be tighter than a tick), barring a locked market, so the mid is the NBBO mid. A ≤ 3-tick cap is
reported beside it. Added after the first two days showed IEX half-spreads of 190–320 bp on UCO and SCO: a
one-venue quote that is not at the inside, whose mid is not a fair value.
reported per ETF over regular hours (09:30–16:00 ET) and over 13:30–14:28, the window C2's features are built in.
Each is reported with n, mean, median, sd, the mean IEX half-spread in bp, and the share of minutes with a usable
quote. The mean bias is what a time-averaged close-based premium carries. The sd is per-minute noise, which
averaging over n minutes shrinks.

THE LIMIT, stated so the number is not over-read. IEX's quote is ONE venue's best bid and offer, not the national
best. It is at least as wide as the NBBO, so the half-spread here is an UPPER bound on the NBBO's. A thin ETF
(BOIL, KOLD) may have no two-sided IEX quote much of the day, and its coverage says so.

Inputs: `data/raw/iex/tops_filtered/<day>.csv.gz` (`fetch_iex_tops_sample.py`) and
`data/raw/alphavantage/1min/<SYM>/<YYYY-MM>.json.gz`. Output: `data/ledger_etf_premium_bias_check.json`.
`--check` rebuilds it and compares byte for byte.

    uv run python scripts/check_etf_premium_bias.py [--check] [--days D1,D2,...]
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IEX = REPO / "data" / "raw" / "iex" / "tops_filtered"
AV = REPO / "data" / "raw" / "alphavantage" / "1min"
OUT = REPO / "data" / "ledger_etf_premium_bias_check.json"
SYMS = ("BOIL", "KOLD", "UCO", "SCO", "UNG", "USO")
CUT = "2025-03-01"
ET = "America/New_York"
STALE_S = 60
LABEL_MARGIN = 0.10
MIN_NS = 60 * 10**9
#: IEX spread caps, in 1/10,000 dollar. At ONE TICK, IEX's best bid and offer IS the national best (the NBBO can
#: only be as tight or tighter, and one tick is the floor), barring a locked market: primary. Three ticks: reported.
CAPS = {"one_tick": 100, "three_ticks": 300}
WINDOWS = {"rth": ("09:30", "16:00"), "c2": ("13:30", "14:28")}


class BiasError(RuntimeError):
    pass


def _ns(t: pd.Series) -> pd.Series:
    """UTC nanoseconds since the epoch, computed explicitly (a view or astype of datetime64 need not be ns)."""
    return (t.dt.tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(1, "ns")


def av_bars(sym: str, day: str) -> pd.DataFrame:
    path = AV / sym / f"{day[:7]}.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        js = json.load(fh)
    ts = js.get("Time Series (1min)")
    if not ts:
        raise BiasError(f"{path.name} for {sym}: no time series")
    if js["Meta Data"].get("6. Time Zone") != "US/Eastern":
        raise BiasError(f"{sym} {day[:7]}: time zone {js['Meta Data'].get('6. Time Zone')!r}")
    rows = [(k, float(v["4. close"]), int(v["5. volume"])) for k, v in ts.items() if k.startswith(day)]
    df = pd.DataFrame(rows, columns=["stamp", "close", "volume"]).sort_values("stamp").reset_index(drop=True)
    df["t"] = pd.to_datetime(df["stamp"]).dt.tz_localize(ET)
    df["ns"] = _ns(df["t"])
    return df


def iex_day(day: str) -> pd.DataFrame:
    if day >= CUT:
        raise BiasError(f"{day} is on or after the cut {CUT}")
    df = pd.read_csv(IEX / f"{day}.csv.gz", encoding="utf-8")
    df["t"] = pd.to_datetime(df["ts_ns"], unit="ns", utc=True).dt.tz_convert(ET)
    df["ns"] = df["ts_ns"].astype("int64")
    return df


def label_test(av: pd.DataFrame, trades: pd.DataFrame) -> dict[str, int]:
    """Exact matches of the AV close with IEX's last trade in [T, T+60) ('start') and in [T-60, T) ('end')."""
    out = {"start": 0, "end": 0, "bars_with_iex_trade_start": 0, "bars_with_iex_trade_end": 0}
    if trades.empty:
        return out
    tt = trades["ns"].to_numpy()
    px = trades["b"].to_numpy() / 1e4  # T rows: b = price in 1/10,000 dollar
    for t, c in zip(av["ns"].to_numpy(), av["close"].to_numpy()):
        for name, lo, hi in (("start", t, t + MIN_NS), ("end", t - MIN_NS, t)):
            i = np.searchsorted(tt, hi, side="left") - 1
            if i >= 0 and tt[i] >= lo:
                out[f"bars_with_iex_trade_{name}"] += 1
                if abs(px[i] - c) < 5e-5:
                    out[name] += 1
    return out


def quotes_at(q: pd.DataFrame, instants: np.ndarray) -> pd.DataFrame:
    """IEX's standing top of book at each instant: the latest Quote Update at or before it."""
    qt = q["ns"].to_numpy()
    idx = np.searchsorted(qt, instants, side="right") - 1
    ok = idx >= 0
    idx = np.where(ok, idx, 0)
    bid_sz, bid, ask, ask_sz = (q[c].to_numpy()[idx] for c in ("a", "b", "c", "d"))
    age = (instants - qt[idx]) / 1e9
    usable = ok & (bid_sz > 0) & (ask_sz > 0) & (ask > bid) & (bid > 0) & (age <= STALE_S)
    mid = np.where(usable, (bid + ask) / 2e4, np.nan)
    half = np.where(usable, (ask - bid) / 2e4, np.nan)
    spread_e4 = np.where(usable, ask - bid, np.iinfo(np.int64).max)
    return pd.DataFrame({"mid": mid, "half": half, "usable": usable, "spread_e4": spread_e4})


def _stats(x: np.ndarray, half_bp: np.ndarray, n_bars: int) -> dict[str, Any]:
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {"n": 0, "bars": n_bars}
    return {"n": int(len(x)), "bars": n_bars, "usable_share": round(len(x) / n_bars, 4),
            "mean_bp": round(float(x.mean()), 3), "median_bp": round(float(np.median(x)), 3),
            "sd_bp": round(float(x.std(ddof=1)), 3) if len(x) > 1 else None,
            "se_mean_bp": round(float(x.std(ddof=1) / np.sqrt(len(x))), 3) if len(x) > 1 else None,
            "mean_abs_bp": round(float(np.abs(x).mean()), 3),
            "mean_iex_half_spread_bp": round(float(np.nanmean(half_bp)), 3)}


def build(days: list[str]) -> dict[str, Any]:
    lab_tot = {"start": 0, "end": 0, "bars_with_iex_trade_start": 0, "bars_with_iex_trade_end": 0}
    keys = [(w, c) for w in WINDOWS for c in CAPS]
    per: dict[str, dict[tuple[str, str], list[np.ndarray]]] = {s: {k: [] for k in keys} for s in SYMS}
    halves: dict[str, dict[tuple[str, str], list[np.ndarray]]] = {s: {k: [] for k in keys} for s in SYMS}
    bars: dict[str, dict[str, int]] = {s: {w: 0 for w in WINDOWS} for s in SYMS}
    per_day: dict[str, Any] = {}
    cache: dict[str, tuple[pd.DataFrame, dict[str, pd.DataFrame]]] = {}
    for day in days:
        ix = iex_day(day)
        avs = {s: av_bars(s, day) for s in SYMS}
        cache[day] = (ix, avs)
        for s in SYMS:
            tr = ix[(ix["symbol"] == s) & (ix["type"] == "T")].sort_values("t")
            lt = label_test(avs[s], tr)
            for k in lab_tot:
                lab_tot[k] += lt[k]
    rate = {k: lab_tot[k] / max(lab_tot[f"bars_with_iex_trade_{k}"], 1) for k in ("start", "end")}
    label = max(rate, key=lambda k: rate[k])
    if abs(rate["start"] - rate["end"]) < LABEL_MARGIN:
        raise BiasError(f"the bar label is not identified: exact-match rates {rate}")
    shift = MIN_NS if label == "start" else 0
    for day in days:
        ix, avs = cache[day]
        per_day[day] = {}
        for s in SYMS:
            av = avs[s]
            q = ix[(ix["symbol"] == s) & (ix["type"] == "Q")].sort_values("t")
            clock = av["t"].dt.strftime("%H:%M")
            ends = av["ns"].to_numpy() + shift
            qa = quotes_at(q, ends) if len(q) else pd.DataFrame({"mid": np.nan, "half": np.nan, "usable": False},
                                                                  index=range(len(av)))
            bias = (av["close"].to_numpy() - qa["mid"].to_numpy()) / qa["mid"].to_numpy() * 1e4
            half_bp = qa["half"].to_numpy() / qa["mid"].to_numpy() * 1e4
            d_rec: dict[str, Any] = {}
            for w, (a, b) in WINDOWS.items():
                m = ((clock >= a) & (clock < b)).to_numpy()
                bars[s][w] += int(m.sum())
                for cname, cap in CAPS.items():
                    mc = m & (qa["spread_e4"].to_numpy() <= cap)
                    per[s][(w, cname)].append(bias[mc])
                    halves[s][(w, cname)].append(half_bp[mc])
                    d_rec[f"{w}_{cname}"] = _stats(bias[mc], half_bp[mc], int(m.sum()))
            per_day[day][s] = d_rec
    res: dict[str, Any] = {
        "days": days, "cut": CUT, "stale_s": STALE_S,
        "bar_label": {"chosen": label, "exact_match_rate": {k: round(v, 4) for k, v in rate.items()}, **lab_tot,
                      "rule": f"the label with more exact close-vs-IEX-last-trade matches; margin >= {LABEL_MARGIN}"},
        "pooled": {s: {f"{w}_{c}": _stats(np.concatenate(per[s][(w, c)]), np.concatenate(halves[s][(w, c)]),
                                          bars[s][w])
                       for w, c in keys} for s in SYMS},
        "caps_e4": CAPS,
        "per_day": per_day,
        "limit": "IEX's own top of book, not the NBBO: its half-spread is an upper bound on the NBBO's",
    }
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--days", default=None, help="comma-separated; default: every filtered IEX day on disk")
    a = ap.parse_args(argv)
    days = a.days.split(",") if a.days else sorted(p.name[:10] for p in IEX.glob("*.csv.gz"))
    text = json.dumps(build(days), indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise BiasError(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    if a.days is None:
        OUT.write_text(text, encoding="utf-8", newline="\n")
    res = json.loads(text)
    print("bar label:", res["bar_label"]["chosen"], res["bar_label"]["exact_match_rate"])
    for s, v in res["pooled"].items():
        for k, st in v.items():
            print(f"  {s:5s} {k:17s} " + " ".join(f"{x}={st[x]}" for x in ("bars", "n", "usable_share", "mean_bp",
                                                                               "se_mean_bp", "median_bp", "sd_bp",
                                                                               "mean_iex_half_spread_bp") if x in st))
    return 0


if __name__ == "__main__":
    sys.exit(main())
