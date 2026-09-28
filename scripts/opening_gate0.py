"""Gate O0 of the opening agent-state model (OPENING_AGENT_STATE_PREREG.md s.9, s.13 phase 1; OA-A1, OA-A6).

    python scripts/opening_gate0.py [--data-root DIR]     # SYSTEM interpreter; -> data/opening/gate0.json + labels.csv

The gate (s.9): bars cover >= 99% of expected minutes 08:00-16:00 ET; the calendar is sourced; SPY alignment is
verified; label frequencies are reported. O0-H (for S-H only): options OI and settlements on >= 90% of days.

Read under OA-A6 (ruled 2026-09-28):
- usable sessions (A6.9): NYSE trading days (SPY's daily bars) that are not half days (D589's ES early closes),
  2016-01-04 -> 2025-02-28;
- G1: minutes 08:00-15:59 with a bar, per market, against 480 a session;
- exclusions (A6.8, logged): a missing 09:30 bar, or fewer than 90% of the 09:30 -> t0 bars;
- labels per (session, t0), t0 in {09:45, 10:00} (A6.6), from `backtest_framework.opening.labels`;
- the 8% merge (A6.7): classes pooled over the in-sample per market, at each t0;
- G3 (A6.10): SPY's/QQQ's 09:30 and 15:59 bars on >= 99% of usable sessions, and the median day's correlation of
  1-minute returns with ES/NQ, 09:31-15:59, >= 0.9 at lag 0 and above lags +-1.
- O0-H: ES from `fut_es_options_eod` (D581/D616); NQ has no fixture yet and is reported PENDING.
Nothing on or after 2025-03-01 is read (A10): every frame passes `filter_before` and `assert_none_at_or_after`.

`--data-root` (default this checkout's `data/`) is where the gitignored inputs live: the SPY daily file, D589's
calendar, the ES options fixture and the Alpha Vantage 1-minute cache. The bar fixture is this checkout's.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.opening.labels import LABELS, atr_prior, classify, merge_rare  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402

BARS = REPO / "data" / "fixtures" / "fut_opening_globex_1m.csv.gz"
OUTDIR = REPO / "data" / "opening"
START, RESERVED_FROM = "2016-01-04", "2025-03-01"
ROOTS = ("ES", "NQ")
ETF = {"ES": "SPY", "NQ": "QQQ"}
T0S = ("09:45", "10:00")
COVER_MIN = list(pd.date_range("2000-01-01 08:00", "2000-01-01 15:59", freq="min").strftime("%H:%M"))
RTH_LO, RTH_HI, IB_HI = "09:30", "15:59", "10:29"


def minus_one(hhmm: str) -> str:
    return (pd.Timestamp(f"2000-01-01 {hhmm}") - pd.Timedelta(minutes=1)).strftime("%H:%M")


def usable_sessions(data_root: Path) -> tuple[list[str], dict[str, Any]]:
    spy = json.load(gzip.open(data_root / "raw" / "alphavantage" / "daily" / "SPY.json.gz", "rt", encoding="utf-8"))
    days = {d for d in (spy.keys() if isinstance(spy, dict) else []) if START <= d < RESERVED_FROM}
    if not days:
        raise SystemExit("no NYSE days read from SPY's daily file")
    cal = pd.read_csv(data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    half = set(cal.loc[(cal["root"] == "ES") & cal["is_early_close"].astype(bool), "day"])
    use = sorted(days - half)
    return use, {"nyse_days": len(days), "half_days_removed": sorted(days & half)}


def load_bars() -> pd.DataFrame:
    b = pd.read_csv(BARS, encoding="utf-8", dtype={"session": str, "hhmm": str})
    b = filter_before(b, "session", RESERVED_FROM)
    assert_none_at_or_after(b, "session", RESERVED_FROM)
    return b


def coverage(b: pd.DataFrame, use: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    cov = set(COVER_MIN)
    for r in ROOTS:
        x = b[(b["root"] == r) & b["session"].isin(use) & b["hhmm"].isin(cov)]
        per = x.groupby("session")["hhmm"].nunique().reindex(use, fill_value=0)
        share = float(per.sum() / (len(COVER_MIN) * len(use)))
        by_year = (per.groupby(per.index.str[:4]).sum() / per.groupby(per.index.str[:4]).size() / len(COVER_MIN))
        out[r] = {"share": share, "pass": share >= 0.99, "sessions_with_no_bar": int((per == 0).sum()),
                  "sessions_below_99pct": int((per < 0.99 * len(COVER_MIN)).sum()),
                  "by_year": {k: round(float(v), 5) for k, v in by_year.items()}}
    return out


def daily_frame(b: pd.DataFrame, r: str) -> pd.DataFrame:
    """Per session (every fixture session, in order): the RTH summary OA-A6 reads."""
    x = b[(b["root"] == r) & (b["hhmm"] >= RTH_LO) & (b["hhmm"] <= RTH_HI)]
    g = x.groupby("session", sort=True)
    d = pd.DataFrame({"high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "last_hhmm": g["hhmm"].last()})
    o = x[x["hhmm"] == RTH_LO].set_index("session")["open"]
    d["open"] = o.reindex(d.index)
    ib = x[x["hhmm"] <= IB_HI].groupby("session")
    d["ib_high"], d["ib_low"] = ib["high"].max(), ib["low"].min()
    for t0 in T0S:
        last = minus_one(t0)
        w = x[x["hhmm"] <= last]
        d[f"n_to_{t0}"] = w.groupby("session").size().reindex(d.index, fill_value=0)
        d[f"px_{t0}"] = w.groupby("session")["close"].last().reindex(d.index)
    d["prior_close"] = d["close"].shift(1)
    d["atr20"] = atr_prior(d["high"].to_numpy(), d["low"].to_numpy(), d["close"].to_numpy())
    return d


def labels(b: pd.DataFrame, use: list[str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows, excl = [], {}
    for r in ROOTS:
        d = daily_frame(b, r)
        d = d[d.index.isin(use)]
        for t0 in T0S:
            need = 0.9 * len(pd.date_range(f"2000-01-01 {RTH_LO}", f"2000-01-01 {minus_one(t0)}", freq="min"))
            bad = d["open"].isna() | (d[f"n_to_{t0}"] < need)
            excl[f"{r}_{t0}"] = sorted(d.index[bad])
            k = d[~bad]
            d0 = np.sign(k[f"px_{t0}"] - k["open"]).to_numpy()
            lab = classify(d0, k["open"], k["close"], k["high"], k["low"], k["ib_high"], k["ib_low"],
                           k["prior_close"], k["atr20"])
            rows.append(pd.DataFrame({"root": r, "session": k.index, "t0": t0, "d0": d0.astype(int), "label": lab,
                                      "gap_atr": ((k["open"] - k["prior_close"]) / k["atr20"]).round(4)}))
    L = pd.concat(rows, ignore_index=True)
    return L, excl


def freq_report(L: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for t0 in T0S:
        x = L[(L["t0"] == t0) & L["label"].notna()]
        pooled = {r: {k: round(float(v), 4) for k, v in x[x["root"] == r]["label"].value_counts(normalize=True)
                      .reindex(list(LABELS), fill_value=0).items()} for r in ROOTS}
        by_year = {r: {y: {k: round(float(v), 4) for k, v in g["label"].value_counts(normalize=True)
                           .reindex(list(LABELS), fill_value=0).items()}
                       for y, g in x[x["root"] == r].groupby(x["session"].str[:4])} for r in ROOTS}
        out[t0] = {"pooled": pooled, "by_year": by_year, "n": {r: int((x["root"] == r).sum()) for r in ROOTS},
                   "unclassified_d0_zero": {r: int(((L["t0"] == t0) & (L["root"] == r) & L["label"].isna()).sum())
                                            for r in ROOTS},
                   "merge_into_RANGE": merge_rare(pooled)}
    return out


def spy_alignment(b: pd.DataFrame, use: list[str], data_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    months = sorted({d[:7] for d in use})
    for r in ROOTS:
        sym = ETF[r]
        recs = []
        for m in months:
            p = data_root / "raw" / "alphavantage" / "1min" / sym / f"{m}.json.gz"
            payload = json.load(gzip.open(p, "rt", encoding="utf-8"))
            s = next(v for k, v in payload.items() if k.lower().startswith("time series"))
            recs.extend((k, float(v["4. close"])) for k, v in s.items())
        e = pd.DataFrame(recs, columns=["ts", "close"])
        e["day"], e["hhmm"] = e["ts"].str[:10], e["ts"].str[11:16]
        e = filter_before(e, "day", RESERVED_FROM)
        assert_none_at_or_after(e, "day", RESERVED_FROM)
        e = e[e["day"].isin(use)]
        present = {h: float(e[e["hhmm"] == h]["day"].nunique() / len(use)) for h in (RTH_LO, RTH_HI)}
        f = b[(b["root"] == r) & b["session"].isin(use) & (b["hhmm"] >= RTH_LO) & (b["hhmm"] <= RTH_HI)]
        cors = {-1: [], 0: [], 1: []}
        mins = pd.date_range("2000-01-01 09:30", "2000-01-01 15:59", freq="min").strftime("%H:%M")
        fp = f.pivot_table(index="session", columns="hhmm", values="close", aggfunc="first").reindex(columns=mins)
        ep = e.pivot_table(index="day", columns="hhmm", values="close", aggfunc="first").reindex(columns=mins)
        common = fp.index.intersection(ep.index)
        rf = np.diff(np.log(fp.loc[common].to_numpy(float)), axis=1)
        re_ = np.diff(np.log(ep.loc[common].to_numpy(float)), axis=1)
        for i in range(len(common)):
            a, c = rf[i], re_[i]
            for lag in (-1, 0, 1):
                x, y = (a[lag:], c[:len(c) - lag]) if lag > 0 else ((a[:len(a) + lag], c[-lag:]) if lag < 0 else (a, c))
                ok = np.isfinite(x) & np.isfinite(y)
                if ok.sum() > 200 and x[ok].std() > 0 and y[ok].std() > 0:
                    cors[lag].append(float(np.corrcoef(x[ok], y[ok])[0, 1]))
        med = {lag: float(np.median(v)) for lag, v in cors.items()}
        out[r] = {"etf": sym, "bar_present": present, "median_corr_by_lag": med, "days": len(cors[0]),
                  "pass": bool(min(present.values()) >= 0.99 and med[0] >= 0.9 and med[0] > max(med[-1], med[1]))}
    return out


def options_o0h(use: list[str], data_root: Path) -> dict[str, Any]:
    p = data_root / "fixtures" / "fut_es_options_eod.csv.gz"
    o = pd.read_csv(p, encoding="utf-8", usecols=["session", "oi", "settle"], dtype={"session": str})
    o = filter_before(o, "session", RESERVED_FROM)
    assert_none_at_or_after(o, "session", RESERVED_FROM)
    ok = o[(o["oi"] > 0) & o["settle"].notna()].groupby("session").size()
    share = float(pd.Index(use).isin(ok.index).mean())
    return {"ES": {"share_of_usable_sessions": share, "pass": share >= 0.9},
            "NQ": {"status": "PENDING: the NQ options fixture is not built (raw pull landed 2026-09-28)"}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    t0 = time.time()
    use, cal_note = usable_sessions(a.data_root)
    b = load_bars()
    g1 = coverage(b, use)
    L, excl = labels(b, use)
    freq = freq_report(L)
    g3 = spy_alignment(b, use, a.data_root)
    oh = options_o0h(use, a.data_root)
    g2 = {"events": (REPO / "data" / "calendar" / "events.csv").exists(),
          "session_calendar": (REPO / "data" / "fixtures" / "cme_session_calendar.meta.json").exists()}
    doc = {"spec": "OPENING_AGENT_STATE_PREREG.md s.9 Gate O0; OA-A1, OA-A6", "usable_sessions": len(use),
           "span": [use[0], use[-1]], "calendar": cal_note, "G1_coverage_0800_1559": g1,
           "G2_calendar_sourced": g2, "G3_spy_alignment": g3, "G4_label_frequencies": freq,
           "exclusions": {k: {"n": len(v), "sessions": v} for k, v in excl.items()}, "O0_H": oh,
           "windows": {"reserved_from": RESERVED_FROM, "last_session_read": str(b["session"].max())}}
    doc["gate_O0"] = bool(all(v["pass"] for v in g1.values()) and all(g2.values())
                          and all(v["pass"] for v in g3.values()))
    doc["runtime_min"] = round((time.time() - t0) / 60, 1)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "gate0.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8",
                                       newline="\n")
    L.to_csv(OUTDIR / "labels.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(json.dumps({k: doc[k] for k in ("usable_sessions", "gate_O0", "O0_H", "runtime_min")}, indent=1))
    for r in ROOTS:
        print(r, "coverage", round(g1[r]["share"], 5), "| SPY/QQQ", g3[r]["bar_present"], g3[r]["median_corr_by_lag"])
    for t in T0S:
        print(t, freq[t]["pooled"], "merge:", freq[t]["merge_into_RANGE"], "n", freq[t]["n"])
    return 0 if doc["gate_O0"] else 1


if __name__ == "__main__":
    sys.exit(main())
