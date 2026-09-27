"""The 09:45 and 15:59 one-minute bars of EVERY listed ES and NQ outright (not only the front), per calendar ET day.
The LETF close-flow model computes returns within one contract (deposit s.4.1: r = P(t, tau) / P(t-1, 16:00) - 1;
H5: close(t) -> 09:45 open(t+1)). On a roll day D462's fixture holds only the front, so the new contract's prior 16:00
price, and the old contract's next 09:45 price, are not in it. CME's settlement is NOT a substitute: on 2,285 NQ
sessions 2016-2025 it equals the 15:59 bar close on 2.4% of days (median gap about 10 ticks, p99 181), in every year.

    python scripts/build_fut_index_anchor_bars.py [--workers 6]     # SYSTEM interpreter (databento lives there)

-> data/fixtures/fut_index_anchor_bars.csv.gz: root, day, contract, hhmm, open, close, volume.
Same pass, labelling and ET day as build_fut_index_1m.py (D462; windowed ids, D520). The bar labelled 15:59 closes at
16:00; the bar labelled 09:45 opens at 09:45. The archive spans 2010 -> 2026-09-10; readers cut at their own seal.
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
OUT = REPO / "data" / "fixtures" / "fut_index_anchor_bars.csv.gz"
META = REPO / "data" / "fixtures" / "fut_index_anchor_bars.meta.json"
_s = importlib.util.spec_from_file_location("build_fut_index_1m", REPO / "scripts" / "build_fut_index_1m.py")
assert _s is not None and _s.loader is not None
BI = importlib.util.module_from_spec(_s)
sys.modules["build_fut_index_1m"] = BI
_s.loader.exec_module(BI)
BI.OUTRIGHT = re.compile(r"^(ES|NQ)([FGHJKMNQUVXZ])(\d{1,2})$")  # module level: every spawned worker re-applies it
KEEP = ("09:45", "15:59")


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
            hhmm = np.asarray(ts.strftime("%H:%M"))
            k = np.isin(hhmm, KEEP)
            if not k.any():
                continue
            B.append(pd.DataFrame({"root": j["root"].to_numpy()[k], "day": np.asarray(ts.strftime("%Y-%m-%d"))[k],
                                   "contract": j["contract"].to_numpy()[k], "hhmm": hhmm[k],
                                   "open": a["open"][k] * BI.PX, "close": a["close"][k] * BI.PX,
                                   "volume": a["volume"][k].astype(np.int64)}))
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
    if dup.any():  # the same rule as D462's assemble: archive order, first kept
        print(f"  {int(dup.sum())} duplicate (contract, day, bar) rows across files; first kept")
        b = b[~dup]
    b = b.sort_values(["root", "day", "contract", "hhmm"]).reset_index(drop=True)
    b.to_csv(OUT, index=False, compression="gzip", float_format="%.2f")
    META.write_text(json.dumps({"builder": "scripts/build_fut_index_anchor_bars.py", "rows": int(len(b)), "bars": list(KEEP),
                                "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                "span": [b["day"].min(), b["day"].max()], "holdout": "every archive session; readers cut"},
                               indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.name}: {len(b):,} rows {b['day'].min()} .. {b['day'].max()} in {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
