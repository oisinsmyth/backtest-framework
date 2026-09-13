"""STAGE 0, step 2: are the micro gas / copper / silver contracts actually TRADEABLE, and what is
their tick?

Step 1 found MNG (27 contract months), MHG (42) and SIL (11) in the archive, plus the E-minis QG,
QC, QI, QO, QM. Listing is not liquidity: a contract can be listed and trade three lots a day, and
a C-d pass is worthless if the book is empty.

Measures, per root, over ONE recent archive slice:
  * sessions with any day-session trade, and median DAY-SESSION volume of the busiest month
  * the tick, measured as the smallest positive price increment actually printed
  * the price level, so usd_per_point can be checked against the parent later

NO RETURN IS READ AS A P&L. This is a liquidity and instrument census (R15).

    python working/stage0_micro_liquidity.py            # SYSTEM python (databento)
"""
from __future__ import annotations
import re
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import databento as db

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_fut_breadth_hourly as B  # noqa: E402

PX = 1e-9
CHUNK = 10_000_000
# candidates, and the parents / already-traded micros they must be judged against
ROOTS = ["MNG", "MHG", "SIL", "QG", "QC", "QI", "QO", "QM",
         "NG", "HG", "SI", "GC", "CL", "MGC", "MCL", "MNQ", "MES"]
RE_ROOT = re.compile(r"^(" + "|".join(sorted(ROOTS, key=len, reverse=True)) + r")([FGHJKMNQUVXZ])(\d{1,2})$")
DAY_LO, DAY_HI = 540, 959          # 09:00 .. 15:59 ET in minutes, the day session the screen uses


def windows(store):
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = RE_ROOT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
            e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), m.group(1), str(sym),
                         np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    w = pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"])
    assert not w.duplicated(["iid", "w0"]).any(), "[IDS] repeated (instrument_id, window start)"
    return w


def main():
    files = B.ohlcv_files()
    f = [x for x in files if x.name[10:14] >= "2026"][-1]
    print(f"decoding {f.name}\n", flush=True)
    t0 = time.time()
    store = db.DBNStore.from_file(f)
    w = windows(store)
    print(f"{w['root'].nunique()} roots, {len(w):,} mapping windows\n", flush=True)

    parts = []
    for arr in store.to_ndarray(count=CHUNK):
        raw = pd.DataFrame({"iid": arr["instrument_id"].astype(np.uint32),
                            "ts": arr["ts_event"].astype(np.uint64),
                            "_i": np.arange(len(arr), dtype=np.int64)})
        j = raw.merge(w, on="iid", how="inner")
        j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
        if not len(j):
            continue
        assert not j["_i"].duplicated().any(), "[IDS] a bar claimed by more than one window"
        k = j["_i"].to_numpy()
        a = arr[k]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        minute = ts.hour * 60 + ts.minute
        keep = (minute >= DAY_LO) & (minute <= DAY_HI)
        if not keep.any():
            continue
        parts.append(pd.DataFrame({
            "root": j["root"].to_numpy()[keep], "contract": j["contract"].to_numpy()[keep],
            "day": ts.strftime("%Y-%m-%d")[keep],
            "close_i": a["close"][keep].astype("int64"), "volume": a["volume"][keep].astype("int64")}))
    G = pd.concat(parts, ignore_index=True)
    print(f"{len(G):,} day-session bars in {(time.time()-t0)/60:.1f} min\n")

    rows = []
    for root, g in G.groupby("root", sort=True):
        # the busiest contract month carries the root's liquidity
        top = g.groupby("contract")["volume"].sum().idxmax()
        gt = g[g["contract"] == top].sort_values("day")
        per_day = gt.groupby("day")["volume"].sum()
        d = np.diff(np.sort(gt["close_i"].unique()))
        tick_pts = float(d[d > 0].min()) * PX if (d > 0).any() else np.nan
        rows.append(dict(root=root, months=g["contract"].nunique(), busiest=top,
                         sessions=int(per_day.size), vol_p50=float(per_day.median()),
                         vol_p10=float(per_day.quantile(0.10)), bars_per_session=len(gt) / max(per_day.size, 1),
                         tick_pts=tick_pts, px=float(gt["close_i"].median() * PX)))
    d = pd.DataFrame(rows).sort_values("vol_p50", ascending=False)
    print(f"{'root':<6}{'months':>7}{'busiest':>9}{'sess':>6}{'vol p50':>11}{'vol p10':>10}{'bars/sess':>11}{'tick pts':>11}{'price':>10}")
    for r in d.itertuples():
        star = "  <-- candidate" if r.root in ("MNG", "MHG", "SIL", "QG", "QC", "QI") else ""
        print(f"{r.root:<6}{r.months:>7}{r.busiest:>9}{r.sessions:>6}{r.vol_p50:>11,.0f}{r.vol_p10:>10,.0f}"
              f"{r.bars_per_session:>11.0f}{r.tick_pts:>11.6f}{r.px:>10.3f}{star}")
    d.to_csv(REPO / "working" / "stage0_micro_liquidity.csv", index=False)
    print(f"\nfor scale: one MNQ session is {int(d.loc[d.root=='MNQ','vol_p50'].iloc[0]):,} lots "
          f"and the admitted arm trades 1 lot 1.01 times a session.")


if __name__ == "__main__":
    main()
