"""D520 -- NAME the bars the flat dict was ingesting, on the worst file the build audit found.

    python scripts/d520_contaminant_anatomy.py            # SYSTEM interpreter (databento)
    python scripts/d520_contaminant_anatomy.py --file glbx-mdp3-20190101-20191231

Data layer only. `build_fut_sessions_hourly.py`'s per-file `flat_dict_audit` counts the bars the old
flat {instrument_id: (root, symbol)} dict accepted and the new window labelling rejects. A count is
not an object: this resolves those bars back to the symbol they actually belonged to, and prints the
price the old build was pooling into a front-month panel, because a contamination is only sized once
you have seen what it was (MEMORY: look at the object before reporting it).

One file at a time, deliberately: walking a 4.4M-entry mapping dict for the NON-outright symbols
costs about a minute, which is why the builder does not do it for all 26.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fut_sessions_hourly as B      # noqa: E402

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"


def main() -> int:
    import databento as db
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="glbx-mdp3-20220101-20220816")
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    hits = sorted(RAW.glob(f"*/{a.file}.ohlcv-1m.dbn.zst"))
    assert len(hits) == 1, f"{a.file}: {len(hits)} matches"
    f = hits[0]
    print(f"{f.name}  {f.stat().st_size / 2**20:.0f} MiB")
    store = db.DBNStore.from_file(f)
    w = B.ids_of(store)
    flat = B.flat_labels(w)
    ours = set(w["iid"].tolist())

    # every symbol each of OUR ids carries, outrights and not -- the reverse map, for these ids only
    rev: dict[int, list[tuple[str, str, str]]] = {}
    for sym, ivs in store.metadata.mappings.items():
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            try:
                sid = int(sid)
            except ValueError:
                continue
            if sid in ours:
                s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
                e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
                rev.setdefault(sid, []).append((str(sym), str(s), str(e)))
    print(f"  {len(w)} mapping windows on {len(ours)} ids; "
          f"{sum(1 for v in rev.values() if len(v) > 1)} of those ids carry more than one symbol")

    keep, drop = [], []
    for arr in store.to_ndarray(count=B.CHUNK):
        sel = np.isin(arr["instrument_id"], w["iid"].to_numpy(np.int64))
        x = arr[sel]
        if not x.size:
            continue
        raw = pd.DataFrame({"iid": x["instrument_id"].astype(np.int64),
                            "ts": x["ts_event"].astype(np.int64),
                            "open": x["open"] * B.PX, "close": x["close"] * B.PX,
                            "volume": x["volume"].astype(np.int64)})
        raw = raw.merge(flat, on="iid", how="left")
        j = raw.merge(w[["iid", "w0", "w1", "contract"]], on="iid", how="left")
        inwin = (j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])
        claimed = set(zip(j["iid"][inwin], j["ts"][inwin]))
        m = ~pd.Series(list(zip(raw["iid"], raw["ts"]))).isin(claimed).to_numpy()
        drop.append(raw[m])
        keep.append(raw[~m])
    D = pd.concat(drop, ignore_index=True) if drop else pd.DataFrame()
    K = pd.concat(keep, ignore_index=True) if keep else pd.DataFrame()
    print(f"\n  bars the OLD flat dict accepted: {len(K) + len(D):,}"
          f"   window-claimed {len(K):,}   NOT OURS {len(D):,} "
          f"({(len(D) / max(len(K) + len(D), 1)):.4%})")
    if not len(D):
        print("  nothing dropped on this file")
        return 0
    D["day"] = B.et_days(pd.to_datetime(D["ts"].to_numpy(), utc=True).tz_convert("US/Eastern"))
    D["hour"] = pd.to_datetime(D["ts"].to_numpy(), utc=True).tz_convert("US/Eastern").hour
    g = D.groupby(["flat_root", "flat_contract"]).agg(
        bars=("ts", "size"), volume=("volume", "sum"),
        px_lo=("close", "min"), px_hi=("close", "max"), px_med=("close", "median"),
        first_day=("day", "min"), last_day=("day", "max")).sort_values("bars", ascending=False)
    real = K.groupby(["flat_root", "flat_contract"])["close"].median().rename("real_px_med")
    g = g.join(real)
    print("\n  what the OLD build pooled, by the label it gave the bars "
          "(px_med vs real_px_med is the tell):")
    print(g.head(a.top).to_string())
    print("\n  and the symbol those bars REALLY belonged to:")
    seen = set()
    for r in D.drop_duplicates("iid").itertuples():
        if len(seen) >= a.top:
            break
        seen.add(r.iid)
        others = [t for t in rev.get(int(r.iid), []) if t[0] != r.flat_contract]
        nb = int((D["iid"] == r.iid).sum())
        print(f"    id {int(r.iid):>7}  flat label {r.flat_root}/{r.flat_contract:<7} "
              f"{nb:>7,} bars  really: {others[:3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
