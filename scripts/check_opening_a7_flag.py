"""A7's admission check (D645 s.2; OA-A3): does Sierra Chart's signed flow agree with the exchange's aggressor flag on
ES and NQ? Written before it runs.

    python scripts/check_opening_a7_flag.py      # SYSTEM interpreter (databento) -> data/opening/a7_flag_check.json

THE TRUTH: Databento `trades` (exchange side: B = buyer aggressor, A = seller aggressor, N = none) for the front
outrights ESZ6 and NQZ6, on the post-vault sessions 2026-09-21 -> 2026-09-25, on ts_event (job record
`data/opening/trades_check_jobs.json`). SIERRA: `ESZ26-CME.scid` and `NQZ26-CME.scid` (downloaded --live), the same
sessions only. No vault day (before 2026-09-19) is parsed from either.

PER (market, session), over 09:30 -> 10:00 ET (A7's primary window, t0 = 10:00):
- total volume, each side;
- the large-lot signed volume at the cut K = ceil(the market's last in-sample A7 threshold, from data/opening/a7.csv);
- the all-trade signed volume.
PASS (D645 s.2, fixed before the run): the day-level Pearson r of the large-lot signed volume, Sierra against the
exchange, over the session-markets is >= 0.8.

REPORTED BESIDE IT (the day-level sample is small, 2 markets x 5 sessions):
- the same r for all-trade signed volume;
- the minute-level r and sign agreement of all-trade signed volume, 09:30 -> 16:00, over every minute of both markets;
- the Sierra/exchange total-volume ratio per session-market;
- the share of Sierra volume carrying a side.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SC_DATA = Path(r"C:\SierraChart\Data")
JOBS = REPO / "data" / "opening" / "trades_check_jobs.json"
A7 = REPO / "data" / "opening" / "a7.csv"
OUT = REPO / "data" / "opening" / "a7_flag_check.json"
ET = "America/New_York"
DAYS = ["2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25"]
FRONT = {"ES": ("ESZ6", "ESZ26"), "NQ": ("NQZ6", "NQZ26")}
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
EPOCH = pd.Timestamp("1899-12-30")


def truth() -> pd.DataFrame:
    import databento as db  # type: ignore[import-not-found]
    rec = json.loads(JOBS.read_text(encoding="utf-8"))
    files = sorted((REPO / "data" / "raw" / "databento" / rec["job"]["id"]).glob("*.dbn.zst"))
    want = {v[0]: k for k, v in FRONT.items()}
    parts = []
    for f in files:
        df = db.DBNStore.from_file(f).to_df(map_symbols=True)
        df = df[df["symbol"].astype(str).isin(want)]
        if df.empty:
            continue
        et = pd.DatetimeIndex(df["ts_event"]).tz_convert(ET)
        parts.append(pd.DataFrame({"root": df["symbol"].astype(str).map(want).to_numpy(), "et": et,
                                   "size": df["size"].astype("int64").to_numpy(), "side": df["side"].astype(str).to_numpy()}))
    t = pd.concat(parts, ignore_index=True)
    t["signed"] = np.where(t["side"] == "B", t["size"], np.where(t["side"] == "A", -t["size"], 0))
    return t


def sierra() -> pd.DataFrame:
    parts = []
    for root, (_, sym) in FRONT.items():
        m = np.memmap(SC_DATA / f"{sym}-CME.scid", dtype=REC, mode="r", offset=56)
        for day in DAYS:
            a = pd.Timestamp(f"{day} 09:30", tz=ET).tz_convert("UTC").tz_localize(None)
            b = pd.Timestamp(f"{day} 16:00", tz=ET).tz_convert("UTC").tz_localize(None)
            ua, ub = int((a - EPOCH) / pd.Timedelta(microseconds=1)), int((b - EPOCH) / pd.Timedelta(microseconds=1))
            i0, i1 = max(int(np.searchsorted(m["dt"], ua)) - 5000, 0), min(int(np.searchsorted(m["dt"], ub)) + 5000, len(m))
            r = np.asarray(m[i0:i1])
            r = r[(r["dt"] >= ua) & (r["dt"] < ub)]
            et = pd.to_datetime(r["dt"], unit="us", origin=EPOCH).tz_localize("UTC").tz_convert(ET)
            parts.append(pd.DataFrame({"root": root, "et": et, "size": r["v"].astype("int64"),
                                       "signed": r["av"].astype("int64") - r["bv"].astype("int64"),
                                       "sided": (r["av"].astype("int64") + r["bv"].astype("int64"))}))
    return pd.concat(parts, ignore_index=True)


def per_window(x: pd.DataFrame, cut: dict[str, int]) -> pd.DataFrame:
    x = x[x["et"].dt.strftime("%Y-%m-%d").isin(DAYS)]
    hm = x["et"].dt.strftime("%H:%M")
    w = x[(hm >= "09:30") & (hm < "10:00")].assign(day=lambda d: d["et"].dt.strftime("%Y-%m-%d"))
    w = w.assign(large=np.where(w["size"] >= w["root"].map(cut), w["signed"], 0))
    return w.groupby(["root", "day"]).agg(vol=("size", "sum"), net_all=("signed", "sum"), net_large=("large", "sum"))


def per_minute(x: pd.DataFrame) -> pd.Series:
    x = x[x["et"].dt.strftime("%Y-%m-%d").isin(DAYS)]
    hm = x["et"].dt.strftime("%H:%M")
    x = x[(hm >= "09:30") & (hm < "16:00")]
    return x.groupby([x["root"], x["et"].dt.floor("min")])["signed"].sum()


def main() -> int:
    a7 = pd.read_csv(A7, encoding="utf-8", dtype={"session": str})
    cut = {r: int(np.ceil(a7[a7["root"] == r].sort_values("session")["thr"].dropna().iloc[-1])) for r in FRONT}
    tr, sc = truth(), sierra()
    wt, ws = per_window(tr, cut), per_window(sc, cut)
    j = wt.join(ws, lsuffix="_ex", rsuffix="_sc", how="inner")
    r_large = float(np.corrcoef(j["net_large_ex"], j["net_large_sc"])[0, 1])
    r_all = float(np.corrcoef(j["net_all_ex"], j["net_all_sc"])[0, 1])
    mt, ms = per_minute(tr), per_minute(sc)
    mm = pd.concat([mt.rename("ex"), ms.rename("sc")], axis=1).fillna(0)
    out = {"spec": "D645 s.2; OA-A3", "days": DAYS, "cut": cut, "session_markets": int(len(j)),
           "day_level_r_large": r_large, "day_level_r_all": r_all,
           "minute_level_r_all": float(np.corrcoef(mm["ex"], mm["sc"])[0, 1]),
           "minute_sign_agreement": float((np.sign(mm["ex"]) == np.sign(mm["sc"])).mean()), "minutes": int(len(mm)),
           "volume_ratio_sc_over_ex": (j["vol_sc"] / j["vol_ex"]).round(4).to_dict(),
           "sierra_side_share": float(sc["sided"].sum() / sc["size"].sum()),
           "table": j.reset_index().to_dict("records"), "pass": bool(r_large >= 0.8)}
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("cut", "session_markets", "day_level_r_large", "day_level_r_all",
                                          "minute_level_r_all", "minute_sign_agreement", "sierra_side_share", "pass")},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
