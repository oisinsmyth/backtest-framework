"""The per-contract daily cleared volume of the 17 commodity roots from the CME `statistics` archive (stat_type 6), for the
D600 capacity table (BASIS_MOMENTUM.md item 7). Data layer only: no returns, no signal, no trade.

    python scripts/build_fut_cleared_volume_cm.py --probe            # one file: rows, timing, RSS, projected wall
    python scripts/build_fut_cleared_volume_cm.py --build [--workers 8]
    python scripts/build_fut_cleared_volume_cm.py --selftest         # the gates raise on broken panels

System python (databento 0.86); the venv has no databento. Reuses the breadth builder's windowed id map (D520/D521: a symbol
label is valid only inside its (w0, w1) window, because CME recycles single-digit year codes) and the open-interest builder's
row labelling. Each publication is keyed on the CME trade date it describes: ts_ref is the session START (the evening before),
so the trade date is ts_ref + 1 day in US/Eastern, as `build_fut_open_interest.py` labels its reference session.
Output data/fixtures/fut_cleared_volume_cm_daily.csv.gz (gitignored by suffix; manifest-registered) + meta.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from build_fut_breadth_hourly import ids_of as _ids_windows  # noqa: E402
from build_fut_open_interest import label_rows, rss_mb  # noqa: E402

RAW = REPO / "data" / "raw" / "databento" / "GLBX-20260911-SDNLQ6M99S"
FIX = REPO / "data" / "fixtures"; OUT = FIX / "fut_cleared_volume_cm_daily.csv.gz"; META = FIX / "fut_cleared_volume_cm_daily.meta.json"
CM = sorted(["CL", "BZ", "HO", "RB", "NG", "GC", "SI", "HG", "PL", "PA", "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE"])
ST_CV = 6
UNDEF = np.iinfo(np.int64).max
SPAN = ("2010-06-07", "2023-12-29")


def worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = _ids_windows(store)
    if w is None or len(w) == 0:
        return dict(file=Path(path).name, rows_in=0, rows_kept=0, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=None)
    w = w[w["root"].isin(CM)].reset_index(drop=True); keys = w["iid"].to_numpy(np.uint32); parts = []; n_in = 0
    for arr in store.to_ndarray(count=5_000_000):
        n_in += len(arr)
        a = arr[np.isin(arr["instrument_id"], keys) & (arr["stat_type"] == ST_CV)]
        if a.size:
            j = label_rows(a, w)
            if len(j):
                k = j["_i"].to_numpy()
                parts.append(pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(), "ts_event": a["ts_event"][k].astype("int64"),
                                           "ts_ref": a["ts_ref"][k].astype("int64"), "value": a["quantity"][k].astype("int64")}))
    d = pd.concat(parts, ignore_index=True) if parts else None
    if d is not None:
        d = d[(d["value"] != UNDEF) & (d["value"] >= 0)]
    return dict(file=Path(path).name, rows_in=n_in, rows_kept=int(len(d)) if d is not None else 0, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=d)


def assemble(d):
    """One row per (root, contract, session): the LAST cleared-volume publication for that trade date."""
    ref = pd.to_datetime(d["ts_ref"], utc=True).dt.tz_convert("US/Eastern") + pd.Timedelta(days=1)
    d = d.assign(session=ref.dt.strftime("%Y-%m-%d")).sort_values("ts_event")
    out = d.groupby(["root", "contract", "session"], as_index=False).last()[["root", "contract", "session", "value", "ts_event"]]
    out = out[(out["session"] >= SPAN[0]) & (out["session"] <= SPAN[1])].rename(columns={"value": "cleared_volume"})
    pub = pd.to_datetime(out["ts_event"], utc=True).dt.tz_convert("US/Eastern"); out["published_et"] = pub.dt.strftime("%Y-%m-%d %H:%M")
    return out.drop(columns=["ts_event"]).sort_values(["root", "session", "contract"]).reset_index(drop=True)


def gates(out):
    assert not out.duplicated(["root", "contract", "session"]).any(), "V1: duplicate (root, contract, session)"
    assert (out["cleared_volume"] >= 0).all(), "V2: a negative cleared volume"
    assert set(out["root"]) == set(CM), f"V3: roots missing {set(CM) - set(out['root'])}"
    wd = pd.to_datetime(out["session"]).dt.dayofweek; sat = float((wd == 5).mean()); assert sat < 0.01, f"V4: {sat:.2%} of sessions dated Saturday"
    # the archive publishes cleared volume only from late 2015 (D497's fixture starts 2016 for the same reason): the gate is on the
    # density over each root's OWN covered span, and the first session is recorded, never assumed
    per = out.groupby("root")["session"].agg(["nunique", "min", "max"]); yrs = (pd.to_datetime(per["max"]) - pd.to_datetime(per["min"])).dt.days / 365.25
    dens = per["nunique"] / yrs; assert (dens >= 200).all(), f"V5: a root with fewer than 200 sessions a year over its own span: {dens[dens < 200].round(0).to_dict()}"
    assert (per["min"] <= "2016-01-04").all(), f"V6: a root whose coverage starts after 2016-01-04: {per['min'][per['min'] > '2016-01-04'].to_dict()}"
    return {"V1": "no duplicate (root, contract, session)", "V2": "cleared volume >= 0", "V3": "all 17 roots present", "V4": f"Saturday-dated sessions {sat:.3%} < 1 %",
            "V5": "every root >= 200 sessions a year over its own covered span", "V6": "every root covered from 2016-01-04", "sessions_by_root": per["nunique"].to_dict(), "first_session_by_root": per["min"].to_dict(), "rows": int(len(out))}


def build(workers):
    from multiprocessing import Pool
    files = sorted(RAW.glob("*.statistics.dbn.zst")); t0 = time.time()
    with Pool(workers) as pool:
        res = pool.map(worker, [str(f) for f in files])
    for r in res:
        print(f"  {r['file']}: {r['rows_in']:,} rows in, {r['rows_kept']:,} kept, {r['secs']} s, RSS {r['rss_mb']} MB", flush=True)
    d = pd.concat([r["table"] for r in res if r["table"] is not None], ignore_index=True)
    out = assemble(d); rep = gates(out)
    FIX.mkdir(parents=True, exist_ok=True)
    with __import__("gzip").open(OUT, "wt", encoding="utf-8", newline="\n") as fh:
        out.to_csv(fh, index=False, encoding="utf-8")
    import hashlib
    h = hashlib.sha256(OUT.read_bytes()).hexdigest()
    META.write_text(json.dumps({"built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "builder": "scripts/build_fut_cleared_volume_cm.py", "source": str(RAW.relative_to(REPO)),
                                "shape": "TIDY -- one row per (root, contract, session): the last cleared-volume publication for that CME trade date; session = ts_ref + 1 day US/Eastern",
                                "span": list(SPAN), "roots": CM, "rows": int(len(out)), "sha256": h, "gates": rep, "all_gates_pass": True, "wall_s": round(time.time() - t0, 1)}, indent=1), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}: {len(out):,} rows in {time.time() - t0:.0f} s; gates green", flush=True)


def probe():
    f = sorted(RAW.glob("*.statistics.dbn.zst"))[8]; r = worker(str(f)); print(f"  {r['file']}: {r['rows_in']:,} rows in, {r['rows_kept']:,} kept, {r['secs']} s, RSS {r['rss_mb']} MB; projected wall with 8 workers ~ {17 * r['secs'] / 8 / 60:.1f} min")
    if r["table"] is not None:
        print(assemble(r["table"]).head(5).to_string())


def selftest():
    def expect_raise(fn, what):
        try:
            fn()
        except AssertionError as e:
            print(f"    gate RAISES on {what}: {str(e)[:70]}"); return
        raise AssertionError(f"gate did not raise on {what}")
    days = pd.bdate_range(SPAN[0], SPAN[1]).strftime("%Y-%m-%d"); rows = []
    for r in CM:
        for s in days:
            rows.append({"root": r, "contract": r + "Z5", "session": s, "cleared_volume": 100, "published_et": s + " 20:00"})
    out = pd.DataFrame(rows); gates(out); print("  gates pass a clean synthetic panel")
    expect_raise(lambda: gates(pd.concat([out, out.iloc[[0]]])), "a duplicate row (V1)"); bad = out.copy(); bad.loc[0, "cleared_volume"] = -1; expect_raise(lambda: gates(bad), "a negative volume (V2)")
    expect_raise(lambda: gates(out[out["root"] != "HE"]), "a missing root (V3)")
    thin = out[~((out["root"] == "CL") & (np.arange(len(out)) % 3 != 0))]; expect_raise(lambda: gates(thin), "a root thinned to one session in three (V5)")
    late = out[~((out["root"] == "CL") & (out["session"] < "2017-01-01"))]; expect_raise(lambda: gates(late), "a root whose coverage starts in 2017 (V6)")
    # assemble: two publications for one trade date keep the last
    d = pd.DataFrame({"root": ["CL", "CL"], "contract": ["CLZ5", "CLZ5"], "ts_event": [2, 1], "ts_ref": [pd.Timestamp("2020-03-02 00:00", tz="UTC").value] * 2, "value": [7, 5]})
    a = assemble(d); assert len(a) == 1 and int(a["cleared_volume"].iloc[0]) == 7 and a["session"].iloc[0] == "2020-03-02", a.to_string()
    print("  assemble keeps the last publication per trade date and labels ts_ref + 1 day"); print("  selftest: every gate passes its clean panel and raises on its break"); return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--probe", action="store_true"); ap.add_argument("--build", action="store_true"); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.probe:
        probe()
    if a.build:
        build(a.workers)
