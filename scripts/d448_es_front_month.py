"""D448 -- build an ES front-month price panel from the raw GLBX ohlcv-1m, and run the DIRECT
settlement test: ES (T+0) against SPY (T+3/T+2/T+1) over the SAME clock window, same days.

    python scripts/d448_es_front_month.py --build     # DBN -> data/fixtures/es_front_15m_raw.csv.gz
    python scripts/d448_es_front_month.py --test      # the direct test

RUN WITH THE SYSTEM INTERPRETER, NOT `uv run`. `databento` is installed there and is NOT a
project dependency; adding it to pyproject.toml belongs to the acquisition session, not to this
study. numpy and pandas are the same versions in both.

WHY THIS NEEDS NO ROLL ADJUSTMENT, WHICH IS THE WHOLE REASON IT IS SAFE TO RUN NOW
----------------------------------------------------------------------------------
The acquisition prompt names the roll as the gate that matters most: a synthetic gap in an
adjusted continuous series is scored as a price move that never happened. This study never
builds an adjusted series. Every return it computes takes BOTH endpoints from the SAME contract,
and any session pair whose front month differs between the two days is DROPPED. There is no
stitching, so there is no synthetic gap, so there is nothing for a roll adjustment to get wrong.

    overnight(b)  =  ES 09:30 open on b   /  ES 16:00 close on a   - 1     same contract
    rth(b)        =  ES 16:00 close on b  /  ES 09:30 open on b    - 1     same contract

Front month is the contract with the highest volume on the day -- measured, not a calendar rule.

MATCHING SPY EXACTLY. run_overnight_decomposition defines p0930 as the OPEN of the 09:30 bar and
p1600 as the CLOSE of the 15:45 bar, whose interval [15:45,16:00) makes its close the 16:00
print. On a one-minute grid the same two points are the open of the 09:30 bar and the close of
the 15:59 bar. Timestamps are converted US/Eastern with DST, which is the fixture's own zone.

THE CLAIM UNDER TEST. Prop-firm lane 19: "the overnight drift is a property of the SETTLEMENT
RULE, not of the passage of time", from China's T+1 cash against T+0 futures giving opposite
signs. D447 ran the US within-cash version and REJECTED the predicted direction. This is the
cross-instrument version -- the falsifier the leads doc actually named.

PREDICTIONS, WRITTEN BEFORE THE RUN:
  Y1  ES carries a POSITIVE overnight drift over the same window, not the zero-or-negative the
      settlement story needs. If ES's overnight is flat or negative while SPY's is strongly
      positive, the settlement mechanism survives and C1 is in serious trouble.
  Y2  ES and SPY overnight returns correlate ABOVE 0.90 -- they are the same underlying over the
      same hours. A low correlation means the extraction is wrong, not that the world is
      interesting, and it is the validation gate rather than a finding.
  Y3  ES's overnight drift is SMALLER than SPY's in magnitude, because SPY's overnight is an
      auction-to-auction gap that also carries the microstructure D402 measured, while ES's is a
      continuously traded return.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

RAW = REPO / "data" / "raw" / "databento"   # moved 2026-09-12 out of deletable temp/
FIX = REPO / "data" / "fixtures" / "es_front_1m_boundaries.csv.gz"
OUT = REPO / "data" / "d448_direct_settlement_test.json"

OUTRIGHT = re.compile(r"^ES[FGHJKMNQUVXZ]\d{1,2}$")
PX = 1e-9                      # databento fixed-point price scale
OPEN_HHMM, LAST_HHMM = "09:30", "15:59"


# ==============================================================================================
# Build
# ==============================================================================================

def es_ids(store) -> dict:
    """instrument_id -> raw symbol, for ES OUTRIGHTS only. 'ESM0' yes; 'ESF1 C0375' is an
    option and 'ESM0-ESU0' a calendar spread, and both are excluded by the regex."""
    out = {}
    for sym, ivs in store.metadata.mappings.items():
        if not OUTRIGHT.match(str(sym)):
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if sid:
                out[int(sid)] = str(sym)
    return out


def build() -> int:
    import databento as db

    files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"))
    if not files:
        raise SystemExit("no ohlcv-1m files under data/raw/databento/")
    print(f"D448 build -- {len(files)} ohlcv-1m files\n")

    frames = []
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f)
        ids = es_ids(store)
        arr = store.to_ndarray()
        sel = np.isin(arr["instrument_id"], np.fromiter(ids, dtype=np.uint32))
        a = arr[sel]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        d = pd.DataFrame({
            "day": ts.strftime("%Y-%m-%d"),
            "hhmm": ts.strftime("%H:%M"),
            "contract": [ids[int(x)] for x in a["instrument_id"]],
            "open": a["open"] * PX, "close": a["close"] * PX,
            "volume": a["volume"].astype(np.int64),
        })
        frames.append(d)
        print(f"  [{i:2d}/{len(files)}] {f.name[:38]:<38} {len(arr):>11,} rows "
              f"-> ES {len(a):>8,} ({100 * sel.mean():.2f}%)")

    df = pd.concat(frames, ignore_index=True)
    del frames
    print(f"\n  ES bars total: {len(df):,}  "
          f"{df['day'].min()} .. {df['day'].max()}  contracts {df['contract'].nunique()}")

    # front month = highest volume that day, MEASURED rather than a calendar rule
    vol = df.groupby(["day", "contract"], sort=False)["volume"].sum().reset_index()
    front = vol.sort_values("volume").groupby("day", sort=True).tail(1)
    front = front.set_index("day")["contract"].to_dict()
    df["is_front"] = [c == front.get(d) for d, c in zip(df["day"], df["contract"])]
    fr = df[df["is_front"]]

    o = fr[fr["hhmm"] == OPEN_HHMM].groupby("day", sort=True).first()
    c = fr[fr["hhmm"] == LAST_HHMM].groupby("day", sort=True).last()
    panel = pd.DataFrame({
        "contract": pd.Series(front),
        "p0930": o["open"], "p1600": c["close"],
        "vol": fr.groupby("day", sort=True)["volume"].sum(),
    }).dropna(subset=["p0930", "p1600"])
    panel.index.name = "day"

    FIX.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(FIX, compression="gzip")
    print(f"  wrote {FIX.relative_to(REPO)}  ({len(panel):,} sessions, "
          f"{panel.index.min()} .. {panel.index.max()})")
    return 0


# ==============================================================================================
# The direct test
# ==============================================================================================

def test() -> int:
    import run_overnight_decomposition as ODR

    panel = pd.read_csv(FIX, index_col="day")
    print(f"D448 -- the DIRECT settlement test: ES (T+0) against SPY, same clock, same days\n")
    print(f"  ES sessions {len(panel):,}  {panel.index.min()} .. {panel.index.max()}")

    df = ODR.load()
    df = df[df["suspect"] == 0]
    drop = ODR.half_days(df)
    sess = ODR.sessions_for(df, "SPY", drop)
    spy = ODR.decompose(sess, "SPY")
    spy = spy[spy["consecutive"]].set_index("day")
    print(f"  SPY pairs   {len(spy):,}")

    # ES over the same pairs, SAME CONTRACT on both days -- never stitched
    rows = []
    for b, r in spy.iterrows():
        a = r["prev_day"]
        if a not in panel.index or b not in panel.index:
            continue
        if panel.at[a, "contract"] != panel.at[b, "contract"]:
            continue                      # the roll: dropped, never adjusted
        rows.append({
            "day": b, "prev_day": a, "contract": panel.at[b, "contract"],
            "es_overnight": panel.at[b, "p0930"] / panel.at[a, "p1600"] - 1.0,
            "es_rth": panel.at[b, "p1600"] / panel.at[b, "p0930"] - 1.0,
            "spy_overnight": r["overnight"], "spy_rth": r["rth"],
        })
    d = pd.DataFrame(rows)
    n_roll = len(spy) - len(d) - sum(1 for b, r in spy.iterrows()
                                     if r["prev_day"] not in panel.index
                                     or b not in panel.index)
    print(f"  matched     {len(d):,} pairs   (roll pairs dropped: {n_roll:,})\n")

    def ann(x, days):
        span = (date.fromisoformat(days.max()) - date.fromisoformat(days.min())).days / 365.25
        lr = np.log1p(x)
        t = float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))
        return float(lr.sum() / span), float(1e4 * x.mean()), t

    print(f"  {'series':<18}{'ann%':>9}{'bp/day':>9}{'t':>8}{'n':>9}")
    res = {}
    for name in ("spy_overnight", "es_overnight", "spy_rth", "es_rth"):
        a, bp, t = ann(d[name].to_numpy(dtype=float), d["day"])
        res[name] = {"ann": a, "bp": bp, "t": t}
        print(f"  {name:<18}{100 * a:>8.2f}%{bp:>9.2f}{t:>8.2f}{len(d):>9,}")

    print(f"\n  [Y2 GATE] corr(ES, SPY) overnight "
          f"{np.corrcoef(d['es_overnight'], d['spy_overnight'])[0, 1]:.4f}"
          f"   rth {np.corrcoef(d['es_rth'], d['spy_rth'])[0, 1]:.4f}")

    diff = d["es_overnight"] - d["spy_overnight"]
    td = float(diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff))))
    print(f"  ES minus SPY, overnight: {1e4 * diff.mean():+.2f} bp/day, t {td:+.2f}")

    print("\n  BY SETTLEMENT REGIME -- SPY's rule changes, ES's never does")
    print(f"  {'regime':<8}{'n':>7}{'SPY on ann%':>13}{'ES on ann%':>12}{'ES-SPY bp':>11}")
    T2, T1 = date(2017, 9, 5), date(2024, 5, 28)
    for lab, lo, hi in (("T+3", date(2000, 1, 1), T2), ("T+2", T2, T1),
                        ("T+1", T1, date(2100, 1, 1))):
        s = d[[lo <= date.fromisoformat(x) < hi for x in d["prev_day"]]]
        if len(s) < 30:
            print(f"  {lab:<8}{len(s):>7}   too few pairs")
            continue
        sa = ann(s["spy_overnight"].to_numpy(dtype=float), s["day"])
        ea = ann(s["es_overnight"].to_numpy(dtype=float), s["day"])
        print(f"  {lab:<8}{len(s):>7,}{100 * sa[0]:>12.2f}%{100 * ea[0]:>11.2f}%"
              f"{ea[1] - sa[1]:>11.2f}")
        res[f"regime_{lab}"] = {"n": len(s), "spy_ann": sa[0], "es_ann": ea[0],
                               "spy_bp": sa[1], "es_bp": ea[1]}

    d.to_json(REPO / "data" / "d448_es_spy_pairs.json", orient="records")
    pd.Series(res).to_json(OUT, indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.build:
        return build()
    if a.test:
        return test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
