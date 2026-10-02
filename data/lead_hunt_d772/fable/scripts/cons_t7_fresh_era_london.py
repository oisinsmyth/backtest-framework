"""T7: FRESH-ERA check (2010-06 .. 2015-08, never read by my earlier tests) of two post hoc London-morning cells:
  SI: x = 12:30->13:00 London, fade y = 13:00->14:00 London (the +$14.83/60m, t 2.7 cell of cons_t3b, 2016-23);
  HG: x = 10:30->11:00 London, fade y = 11:00->12:00 London (+$3.00/60m, t 3.2, 2016-23).
Also SI 12:15->13:00 as x (the auction-publication variant) and placebos at 11:00 and 15:00 London.
Decodes SI and HG minutes 05:00-11:00 ET from the raw ohlcv-1m archive (files 2010-2015 only; 4 processes); front =
the day's modal contract by volume. System interpreter (databento).
"""
import sys, os, json, time, re
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(__file__))
from cons_lib import *
WT_SCRIPTS = os.path.join(WT, "scripts")
RAWDIR = os.path.join(MAIN, "data", "raw", "databento", "GLBX-20260911-HSEKYEBHQ4")
TMP = os.path.join(OUT, "cons_t7_cache.parquet")
ROOTS = ("SI", "HG")

def decode(path):
    import databento as db
    sys.path.insert(0, WT_SCRIPTS)
    import build_fut_breadth_hourly as BH
    store = db.DBNStore.from_file(path)
    w = BH.ids_of(store)
    w = w[w["root"].isin(ROOTS)]
    parts = []
    for arr in store.to_ndarray(count=BH.CHUNK):
        a = arr[np.isin(arr["instrument_id"], w["iid"].to_numpy(np.uint32))]
        if a.size == 0:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.int64),
                            "close": a["close"] * BH.PX, "volume": a["volume"].astype(np.int64)})
        j = raw.merge(w, on="iid", how="inner")
        j = j[(j["ts"].astype(np.uint64) >= j["w0"]) & (j["ts"].astype(np.uint64) < j["w1"])]
        if len(j):
            parts.append(j[["root", "contract", "ts", "close", "volume"]])
    return pd.concat(parts, ignore_index=True) if parts else None

if __name__ == "__main__":
    if not os.path.exists(TMP):
        import glob
        files = sorted(p for p in glob.glob(os.path.join(MAIN, "data", "raw", "databento", "GLBX-*", "*.ohlcv-1m.dbn.zst"))
                       if os.path.basename(p)[10:14] <= "2015")
        print(len(files), "files", flush=True); t0 = time.time()
        with ProcessPoolExecutor(4) as ex:
            got = list(ex.map(decode, files))
        d = pd.concat([g for g in got if g is not None], ignore_index=True)
        d["utc"] = pd.to_datetime(d.ts, utc=True)
        d["trade_day"] = (d.utc.dt.tz_convert("America/New_York") + pd.Timedelta(hours=7)).dt.strftime("%Y-%m-%d")
        d = d[d.trade_day < "2015-09-01"]
        # front = modal contract by volume per (root, trade_day)
        v = d.groupby(["root", "trade_day", "contract"]).volume.sum().reset_index()
        front = v.sort_values("volume").groupby(["root", "trade_day"]).tail(1)[["root", "trade_day", "contract"]]
        d = d.merge(front, on=["root", "trade_day", "contract"], how="inner")
        d[["root", "contract", "ts", "close", "volume", "trade_day"]].to_parquet(TMP, index=False)
        print(f"decoded {len(d)} front minutes in {(time.time()-t0)/60:.1f} min", flush=True)
    d = pd.read_parquet(TMP)
    d["utc"] = pd.to_datetime(d.ts, utc=True)
    LON = ZoneInfo("Europe/London")
    res = {}
    for root, mult, cells in [("SI", 1000.0, {"si_1300": ("12:30", "13:00", 60), "si_1300_x45": ("12:15", "13:00", 60), "si_1300_y30": ("12:30", "13:00", 30),
                                                 "si_placebo_1100": ("10:30", "11:00", 60), "si_placebo_1500": ("14:30", "15:00", 60), "si_1200_auction": ("11:30", "12:00", 60)}),
                              ("HG", 2500.0, {"hg_1100": ("10:30", "11:00", 60), "hg_1100_y30": ("10:30", "11:00", 30), "hg_1235_ring": ("12:05", "12:35", 30), "hg_placebo_1500": ("14:30", "15:00", 60)})]:
        x = d[d.root == root]
        ser = pd.Series(x.close.to_numpy(), index=x.utc + pd.Timedelta(minutes=1)); ser = ser[~ser.index.duplicated(keep="last")].sort_index()
        ser = ser.reindex(pd.date_range(ser.index.min(), ser.index.max(), freq="1min", tz="UTC")).ffill(limit=3)
        days = sorted(set(x.trade_day)); days = [s for s in days if pd.Timestamp(s).dayofweek < 5 and s >= "2010-07-01"]
        yrs = np.array([s[:4] for s in days])
        def pa(hhmm):
            t = pd.DatetimeIndex([pd.Timestamp(f"{s} {hhmm}", tz=LON) for s in days]).tz_convert("UTC")
            return ser.reindex(t).to_numpy()
        for name, (c0, c1, h) in cells.items():
            hh, mm = map(int, c1.split(":")); t2 = hh * 60 + mm + h; c2 = f"{t2 // 60:02d}:{t2 % 60:02d}"
            p0, p1, p2 = pa(c0), pa(c1), pa(c2)
            f = pd.DataFrame({"x": (p1 - p0) * mult, "y": (p2 - p1) * mult, "year": yrs}).dropna()
            r = {"n": int(len(f)), "mean_abs_x": round(float(f.x.abs().mean()), 1), "sd_y": round(float(f.y.std()), 1), "rho_x_y": round(spearman(f.x, f.y), 4),
                 "rho_by_year": {y_: round(spearman(z.x, z.y), 3) for y_, z in f.groupby("year")}}
            s = f.x.abs().to_numpy(); thr = np.full(len(f), np.nan)
            for i in range(250, len(f)):
                thr[i] = np.quantile(s[i - 250:i], 2 / 3)
            sel = f[np.isfinite(thr) & (s > thr)]
            r["fade_top3rd"] = four_groups((-np.sign(sel.x) * sel.y).to_numpy(), sel.year.to_numpy(), micro_cost(root), name)
            r["fade_all"] = four_groups((-np.sign(f.x) * f.y).to_numpy(), f.year.to_numpy(), micro_cost(root), name + " all")
            # in-sample top third too (no burn-in, since the era is short)
            thr2 = np.quantile(s, 2 / 3); sel2 = f[s > thr2]
            r["fade_top3rd_insample_thr"] = four_groups((-np.sign(sel2.x) * sel2.y).to_numpy(), sel2.year.to_numpy(), micro_cost(root), name + " is")
            obs, p50, p95, p05, pv = rotation_p(f.x.to_numpy(), f.y.to_numpy(), spearman)
            r["rotation"] = {"obs": round(obs, 4), "p05": round(p05, 4), "p95": round(p95, 4), "p": pv}
            res[name] = r
            g = lambda q: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in q.items() if k in ("n", "gross_mean", "gross_median", "t", "net_mean", "win", "trimmed", "pos_years", "n_years", "by_year_mean", "top_trade")}
            print(name, {k: v for k, v in r.items() if not k.startswith("fade")}, flush=True)
            print("   top3rd wf", g(r["fade_top3rd"])); print("   top3rd is", g(r["fade_top3rd_insample_thr"])); print("   all", g(r["fade_all"]), flush=True)
    json.dump(res, open(os.path.join(OUT, "cons_t7_fresh_era_london.json"), "w", encoding="utf-8"), indent=1, default=str)
    print("done")
