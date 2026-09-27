"""Daily full-day volume of the MNQ and MES outrights, front month by full-day volume per calendar ET day: the micro
half of the LETF close-flow model's V = NQ + MNQ/10 (deposit s.4.4). The principal, 2026-09-27: "start NQ Phase 2".

    python scripts/build_fut_micro_day_volume.py [--workers 6]     # SYSTEM interpreter (databento lives there)

-> data/fixtures/fut_micro_day_volume.csv.gz: root, day, front, day_volume (the front's), total_volume (all outrights).

It is `build_fut_index_1m.py`'s own pass with the outright pattern swapped for the micros: the same windowed id
labelling (D520: never a flat id map), the same calendar-ET day, the same front rule (highest full-day volume), so
the micro column is built exactly as the NQ/ES `day_volume` in fut_index_sessions is. RTH bars are not kept. The
archive spans 2010 -> 2026-09-10 and this fixture carries every session in it; a study reads it through its own seal.
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
OUT = REPO / "data" / "fixtures" / "fut_micro_day_volume.csv.gz"
META = REPO / "data" / "fixtures" / "fut_micro_day_volume.meta.json"
_s = importlib.util.spec_from_file_location("build_fut_index_1m", REPO / "scripts" / "build_fut_index_1m.py")
assert _s is not None and _s.loader is not None
BI = importlib.util.module_from_spec(_s)
sys.modules["build_fut_index_1m"] = BI
_s.loader.exec_module(BI)
# module level, so every spawned worker re-applies it on import: ids_of reads BI.OUTRIGHT
BI.OUTRIGHT = re.compile(r"^(MNQ|MES)([FGHJKMNQUVXZ])(\d{1,2})$")


def worker(path: str) -> dict:
    import databento as db

    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = BI.ids_of(store)
    D = []
    n = 0
    if w is not None:
        for arr in store.to_ndarray(count=BI.CHUNK):
            n += len(arr)
            j = BI.label_rows(arr, w).sort_values("_i")
            if len(j) == 0:
                continue
            a = arr[j["_i"].to_numpy()]
            ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
            D.append(pd.DataFrame({"root": j["root"].to_numpy(), "day": ts.strftime("%Y-%m-%d"),
                                   "contract": j["contract"].to_numpy(), "volume": a["volume"].astype(np.int64)})
                     .groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index())
    return {"file": Path(path).name, "rows_in": n, "secs": round(time.time() - t0, 1),
            "dv": pd.concat(D, ignore_index=True) if D else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    t0 = time.time()
    files = sorted(BI.RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
    assert files, "no ohlcv-1m files"
    order = {f.name: i for i, f in enumerate(files)}
    from multiprocessing import Pool

    with Pool(a.workers) as pool:
        res = pool.map(worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: order[r["file"]])
    sec = sum(r["secs"] for r in res)
    wall = time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec / wall:.2f}x on {a.workers} workers ({100 * sec / wall / a.workers:.0f}%)")
    dv = pd.concat([r["dv"] for r in res if r["dv"] is not None], ignore_index=True)
    dv = dv.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    tot = dv.groupby(["root", "day"])["volume"].sum().rename("total_volume")
    front = (dv.sort_values(["root", "day", "volume", "contract"]).groupby(["root", "day"], sort=True).tail(1)
             .rename(columns={"contract": "front", "volume": "day_volume"}).set_index(["root", "day"]))
    out = front.join(tot).reset_index()
    out.to_csv(OUT, index=False, compression="gzip", encoding="utf-8")
    META.write_text(json.dumps({"builder": "scripts/build_fut_micro_day_volume.py", "built_utc": time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "front_rule": "highest full-day volume per calendar ET day (as D462)",
        "roots": sorted(out["root"].unique().tolist()), "rows": int(len(out)),
        "span": {r: [g["day"].min(), g["day"].max()] for r, g in out.groupby("root")},
        "files": [{k: v for k, v in r.items() if k != "dv"} for r in res],
        "holdout": "carries every archive session; readers cut at their own seal"}, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    for r, g in out.groupby("root"):
        print(f"  {r}: {len(g):,} sessions {g['day'].min()} .. {g['day'].max()}")
    print(f"wrote {OUT.name} in {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
