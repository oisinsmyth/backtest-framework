"""C26 build: open interest by strike for CL (LO, LO1-5) and NG (ON, ON1-5) options in the days before each expiry, 2016-2023
only (the 2024+ yearly files are never opened). System python. Adapted read-only from the repo's build_fut_es_options_eod.py
(windowed definitions per D520; stat_type 9 = OI in quantity; UNDEF filtered). Output in scratch out/:
  crea_pin_defs_<year>.pkl  (iid, raw_symbol, family, right, strike, expiry_date, expiry_hhmm, underlying, ts_recv_first, ts_recv)
  crea_pin_oi.pkl           (raw_symbol, family, right, strike, expiry_date, expiry_hhmm, underlying, oi, ts_event) for publications
                             made in the 6 calendar days before each option's expiry.
Usage: python crea_pin_build.py defs | stats"""
import pickle, re, sys, time
from pathlib import Path
import numpy as np, pandas as pd

RAW = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento")
OUT = Path(__file__).resolve().parents[1] / "out"
DEF_DIR = RAW / "GLBX-20260922-YWCPR3SEQT"
STAT_DIRS = [RAW / "GLBX-20260922-N4TYWYXL96", RAW / "GLBX-20260922-WXKGD8B66A"]  # LO family stats, ON family stats
OPTION = re.compile(r"^(LO[1-5]?|ON[1-5]?)([FGHJKMNQUVXZ])(\d{1,2}) ([CP])(\d+)$")
YEARS = range(2016, 2024)
ST_OI = 9; UNDEF = np.iinfo(np.int64).max; PX = 1e-9; CHUNK = 800_000


def year_of(p):
    return int(re.search(r"glbx-mdp3-(\d{4})", Path(p).name).group(1))


def defs_worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); rows = []
    for arr in store.to_ndarray(count=CHUNK):
        cls = arr["instrument_class"]; m = (cls == b"C") | (cls == b"P")
        if not m.any():
            continue
        a = arr[["instrument_id", "raw_symbol", "instrument_class", "strike_price", "expiration", "underlying", "ts_recv"]][m].copy(); sym = np.char.decode(a["raw_symbol"].astype("S"), "ascii"); keep = np.array([bool(OPTION.match(s)) for s in sym])
        if not keep.any():
            continue
        a = a[keep]; sym = sym[keep]
        rows.append(pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "raw_symbol": sym, "right": np.char.decode(a["instrument_class"].astype("S"), "ascii"),
                                  "strike": a["strike_price"].astype(np.int64) * PX, "expiration_ns": a["expiration"].astype(np.int64),
                                  "underlying": np.char.decode(a["underlying"].astype("S"), "ascii").astype(str), "ts_recv": a["ts_recv"].astype(np.int64)}))
    d = pd.concat(rows, ignore_index=True)
    d = d.sort_values(["iid", "ts_recv"]); first = d.groupby(["iid", "raw_symbol"])["ts_recv"].min().rename("ts_recv_first")
    d = d.drop_duplicates(["iid", "raw_symbol"], keep="last").merge(first, on=["iid", "raw_symbol"], how="left")
    d["family"] = d["raw_symbol"].str.extract(OPTION.pattern)[0]
    exp = pd.to_datetime(d["expiration_ns"].astype("int64"), utc=True).dt.tz_convert("US/Eastern")
    d["expiry_date"] = exp.dt.strftime("%Y-%m-%d"); d["expiry_hhmm"] = exp.dt.strftime("%H:%M")
    y = year_of(path)
    (OUT / f"crea_pin_defs_{y}.pkl").write_bytes(pickle.dumps(d))
    return (Path(path).name, len(d), round(time.time() - t0, 1))


def stats_worker(path):
    import databento as db
    t0 = time.time(); y = year_of(path)
    defs = pickle.loads((OUT / f"crea_pin_defs_{y}.pkl").read_bytes())
    keys = np.unique(defs["iid"].to_numpy(np.uint32))
    store = db.DBNStore.from_file(path); parts = []
    for arr in store.to_ndarray(count=CHUNK):
        a = arr[["instrument_id", "ts_event", "quantity"]][(arr["stat_type"] == ST_OI) & np.isin(arr["instrument_id"], keys)].copy()
        a = a[(a["quantity"] != UNDEF) & (a["quantity"] >= 0)]
        if a.size:
            parts.append(pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts_event": a["ts_event"].astype(np.int64), "oi": a["quantity"].astype(np.int64)}))
    s = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["iid", "ts_event", "oi"])
    # windowed labelling: each publication takes the definition of its id in force at the publication time
    w = defs.copy(); w["w0"] = w["ts_recv_first"].astype("int64"); w = w.sort_values(["iid", "w0"])
    firstw = w.groupby("iid")["w0"].transform("min"); w.loc[w["w0"] == firstw, "w0"] = 0
    s = pd.merge_asof(s.sort_values("ts_event"), w[["iid", "w0", "raw_symbol", "family", "right", "strike", "expiry_date", "expiry_hhmm", "expiration_ns", "underlying"]].sort_values("w0"),
                      left_on="ts_event", right_on="w0", by="iid", direction="backward")
    s = s[s["raw_symbol"].notna()]
    dt = (s["expiration_ns"].astype("int64") - s["ts_event"]) / 86400e9
    s = s[(dt > 0) & (dt <= 6)]
    return (Path(path).name, s.drop(columns=["w0"]), round(time.time() - t0, 1))


if __name__ == "__main__":
    from multiprocessing import Pool
    stage = sys.argv[1]
    if stage == "defs":
        files = [f for f in sorted(DEF_DIR.glob("*.definition.dbn.zst")) if year_of(f) in YEARS]
        with Pool(4) as p:
            for r in p.imap_unordered(defs_worker, [str(f) for f in files]):
                print(r, flush=True)
    else:
        files = [f for d in STAT_DIRS for f in sorted(d.glob("*.statistics.dbn.zst")) if year_of(f) in YEARS]
        files = sorted(files, key=lambda f: -f.stat().st_size)
        res = []
        with Pool(4) as p:
            for r in p.imap_unordered(stats_worker, [str(f) for f in files]):
                print(r[0], len(r[1]), r[2], flush=True); res.append(r[1])
        s = pd.concat(res, ignore_index=True)
        assert s["expiry_date"].max() < "2024-01-08"
        (OUT / "crea_pin_oi.pkl").write_bytes(pickle.dumps(s))
        print("oi rows", len(s), s.family.value_counts().to_dict())
