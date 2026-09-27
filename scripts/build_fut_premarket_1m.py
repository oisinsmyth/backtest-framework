"""The 08:00-08:59 ET one-minute bars of GC, SI, 6E and ZN, the hour `fut_day1m`'s 09:00-15:59 template does not hold:
the shock classifier's GC window opens at 08:25 (SHOCK_CLASSIFIER_PREREG.md s.3.3; SC-A4, the principal 2026-09-27).

    python scripts/build_fut_premarket_1m.py [--workers 6]     # SYSTEM interpreter (databento lives there)

-> data/fixtures/fut_premarket_1m.csv.gz: root, day, contract, hhmm, open, high, low, close, volume (all months kept),
   and the front flag `front` = the contract fut_day1m names for that (root, day), so the two fixtures agree on the
   front by construction (fut_day1m takes its front from fut_breadth_hourly).
Same pass, windowed-id labelling (D520) and calendar-ET day as build_fut_index_1m.py (D462). A bar is labelled by its
START. The archive spans 2010 -> 2026-09-10; readers cut at their own seal.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "fixtures" / "fut_premarket_1m.csv.gz"
META = REPO / "data" / "fixtures" / "fut_premarket_1m.meta.json"
DAY1M = REPO / "data" / "fixtures" / "fut_day1m.parquet"
ROOTS = ("GC", "SI", "6E", "ZN")
_s = importlib.util.spec_from_file_location("build_fut_index_1m", REPO / "scripts" / "build_fut_index_1m.py")
assert _s is not None and _s.loader is not None
BI = importlib.util.module_from_spec(_s)
sys.modules["build_fut_index_1m"] = BI
_s.loader.exec_module(BI)
BI.OUTRIGHT = re.compile(r"^(GC|SI|6E|ZN)([FGHJKMNQUVXZ])(\d{1,2})$")  # module level: every spawned worker re-applies it


def worker(path: str) -> dict:
    import databento as db

    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = BI.ids_of(store)
    B = []
    if w is not None:
        for arr in store.to_ndarray(count=BI.CHUNK):
            j = BI.label_rows(arr, w).sort_values("_i")
            if len(j) == 0:
                continue
            a = arr[j["_i"].to_numpy()]
            ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
            hh = np.asarray(ts.hour)
            k = hh == 8
            if not k.any():
                continue
            B.append(pd.DataFrame({"root": j["root"].to_numpy()[k], "day": np.asarray(ts.strftime("%Y-%m-%d"))[k],
                                   "contract": j["contract"].to_numpy()[k], "hhmm": np.asarray(ts.strftime("%H:%M"))[k],
                                   "open": a["open"][k] * BI.PX, "high": a["high"][k] * BI.PX, "low": a["low"][k] * BI.PX,
                                   "close": a["close"][k] * BI.PX, "volume": a["volume"][k].astype(np.int64)}))
    return {"file": Path(path).name, "secs": round(time.time() - t0, 1), "bars": pd.concat(B, ignore_index=True) if B else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    t0 = time.time()
    files = sorted(BI.RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
    order = {f.name: i for i, f in enumerate(files)}
    from multiprocessing import Pool

    with Pool(a.workers) as pool:
        res = pool.map(worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: order[r["file"]])
    sec, wall = sum(r["secs"] for r in res), time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec / wall:.2f}x on {a.workers} workers ({100 * sec / wall / a.workers:.0f}%)")
    b = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    dup = b.duplicated(["root", "day", "contract", "hhmm"])
    if dup.any():  # D462's rule: archive order, first kept
        print(f"  {int(dup.sum())} duplicate (contract, day, bar) rows across files; first kept")
        b = b[~dup]
    import pyarrow.dataset as ds

    fr = (ds.dataset(DAY1M).to_table(columns=["root", "day", "contract"], filter=ds.field("root").isin(list(ROOTS)))
          .to_pandas().drop_duplicates(["root", "day"]))
    b = b.merge(fr.rename(columns={"contract": "front_contract"}), on=["root", "day"], how="left")
    b["front"] = b["contract"] == b["front_contract"]
    b = b.drop(columns="front_contract").sort_values(["root", "day", "contract", "hhmm"]).reset_index(drop=True)
    b.to_csv(OUT, index=False, compression="gzip", float_format="%.6g", encoding="utf-8")
    f = b[b["front"]]
    per = f.groupby(["root", "day"]).size()
    META.write_text(json.dumps({
        "builder": "scripts/build_fut_premarket_1m.py", "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "roots": list(ROOTS), "rows": int(len(b)), "front_rows": int(len(f)), "span": [b["day"].min(), b["day"].max()],
        "front_rule": "fut_day1m's contract for the (root, day)",
        "front_bars_per_session": {r: {"mean": float(per[r].mean()), "p10": float(per[r].quantile(0.1))} for r in ROOTS},
        "holdout": "every archive session; readers cut at their own seal"}, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in ROOTS:
        print(f"  {r}: front bars per session mean {per[r].mean():.1f} of 60, p10 {per[r].quantile(0.1):.0f}")
    print(f"wrote {OUT.name}: {len(b):,} rows in {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
