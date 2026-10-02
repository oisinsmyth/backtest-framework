"""Premise test A, step 1: census of CME Stop Logic / Velocity Logic 'reserved state' events from the status schema, 2016-2023.

A reserved-state event appears as action=1 (PreOpen) with reason=3 (MarketEvent) [or reason=2 SurveillanceIntervention]
on an instrument, followed by action=6 (NewPriceIndication) and action=7 (Trading). Scheduled pre-opens (reason=1) are
not events. Output: ../out/crea_04_status_events.csv with one row per (root, contract, event start, resume time).
Read-only on data/raw; files whose span reaches 2024 are never opened (SEAL).

    python crea_04_stop_logic_census.py
"""
import os, re, time
from pathlib import Path
import numpy as np
import pandas as pd
import databento as db

RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento/GLBX-20260911-HSEKYEBHQ4")
OUT = Path(__file__).resolve().parents[1] / "out"
OUTRIGHT = re.compile(r"^(ES|NQ|YM|RTY|CL|NG|GC|SI|HG|6E|6A|6J|BTC|ZN|ZB|MES|MNQ|MGC|MCL)([FGHJKMNQUVXZ])(\d{1,2})$")
CHUNK = 5_000_000


def ids_of(store):
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = OUTRIGHT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
            e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), m.group(1), str(sym), np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    return pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"])


def main():
    OUT.mkdir(exist_ok=True)
    recs = []
    for f in sorted(os.listdir(RAW)):
        span = f.split(".")[0].replace("glbx-mdp3-", "")
        a, b = span.split("-")
        if b >= "20240101" or a < "20160101":
            continue
        t0 = time.time(); store = db.DBNStore.from_file(RAW / f); w = ids_of(store); n = 0
        for arr in store.to_ndarray(count=CHUNK):
            n += len(arr)
            keep = (np.isin(arr["action"], [1, 6, 7, 8, 9, 10]) & np.isin(arr["reason"], [2, 3, 6])) | np.isin(arr["action"], [8, 9, 10])
            a2 = arr[keep]
            if len(a2) == 0:
                continue
            raw = pd.DataFrame({"iid": a2["instrument_id"].astype(np.uint32), "ts": a2["ts_event"].astype(np.uint64),
                                "action": a2["action"], "reason": a2["reason"], "tev": a2["trading_event"], "_i": np.arange(len(a2))})
            j = raw.merge(w, on="iid", how="inner")
            j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
            recs.append(j[["root", "contract", "ts", "action", "reason", "tev"]])
        print(f, n, round(time.time() - t0, 1), flush=True)
    ev = pd.concat(recs, ignore_index=True)
    ev["ts"] = pd.to_datetime(ev["ts"].astype(np.int64), utc=True)
    ev["et"] = ev["ts"].dt.tz_convert("US/Eastern").dt.tz_localize(None)
    ev = ev.sort_values(["root", "contract", "ts"]).reset_index(drop=True)
    ev.to_csv(OUT / "crea_04_status_raw.csv", index=False)
    print("raw rows", len(ev))
    print(ev.groupby(["action", "reason"]).size().to_string())
    # pair each PreOpen(1)/Halt(8)/Pause(9) event with the next Trading(7) on the same contract
    rows = []
    for (root, con), g in ev.groupby(["root", "contract"], sort=False):
        g = g.sort_values("ts"); start = None
        for r in g.itertuples():
            if r.action in (1, 8, 9, 10) and start is None:
                start = r
            elif r.action == 7 and start is not None:
                rows.append(dict(root=root, contract=con, start_et=start.et, resume_et=r.et, secs=(r.ts - start.ts).total_seconds(),
                                 start_action=start.action, start_reason=start.reason))
                start = None
    E = pd.DataFrame(rows)
    E.to_csv(OUT / "crea_04_status_events.csv", index=False)
    print("events", len(E))
    E["year"] = E["start_et"].dt.year
    E["hh"] = E["start_et"].dt.hour
    print(E.groupby(["root", "year"]).size().unstack(fill_value=0).to_string())
    print(E["secs"].describe().to_string())
    print(E.groupby("start_reason").size().to_string())
    print(E.groupby("hh").size().to_string())


if __name__ == "__main__":
    main()
