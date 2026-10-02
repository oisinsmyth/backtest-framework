"""D762 fixture: ES, NQ, YM, RTY one-minute bars around the cash close, 15:30-16:14 ET (bar starts), 2016-01-04 ->
2023-12-29, from the CME ohlcv-1m archive. A variant of D462's `build_fut_index_1m.py` (its mapping-window labelling,
`ids_of` and `label_rows`, imported unchanged); the front contract per (root, day) is taken from D462's
`fut_index_sessions`, never re-derived, so a session's post-close bars belong to its day-session contract.

    python scripts/build_fut_index_close_1m.py --build [--workers 6]   # SYSTEM interpreter (databento lives there)
    python scripts/build_fut_index_close_1m.py --selftest

THE SEAL: only archive files whose own date range lies within 2016-01-01 .. 2023-12-31 are decoded; any decoded row
dated 2024-01-01 or later raises. VALIDATION (declared in D762 s.1, before this builder): V1, on the 15:30-15:59 overlap,
bars present here and in fut_{root}_rth_1m agree on open/high/low/close/volume on >= 99.9 %; V2, >= 95 % of sessions
with a 15:59 bar have a bar in 16:05-16:09. Output: data/fixtures/fut_index_close_1m.csv.gz (gitignored) and its meta.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fut_index_1m as M  # noqa: E402  (D462; importing defines, never runs)

REPO = Path(__file__).resolve().parents[1]
RAW, FIX = M.RAW, M.FIX
OUT = FIX / "fut_index_close_1m.csv.gz"
META = FIX / "fut_index_close_1m.meta.json"
LO, HI = "15:30", "16:14"
FIRST, CUTOFF = "2016-01-01", "2024-01-01"
NAME = re.compile(r"glbx-mdp3-(\d{8})-(\d{8})\.ohlcv-1m\.dbn\.zst$")


class BuildError(RuntimeError):
    pass


def select_files(paths) -> list[Path]:
    """Archive files whose whole date range lies in [2016-01-01, 2023-12-31]."""
    out = []
    for p in paths:
        m = NAME.search(Path(p).name)
        if not m:
            continue
        a, b = m.group(1), m.group(2)
        if a >= FIRST.replace("-", "") and b < CUTOFF.replace("-", ""):
            out.append(Path(p))
    return sorted(out, key=lambda p: p.name)


def seal(df: pd.DataFrame) -> None:
    if len(df) and (df["day"] >= CUTOFF).any():
        raise BuildError("the seal: a row dated 2024-01-01 or later")


def window_rows(arr, w) -> pd.DataFrame | None:
    """The four roots' outright bars in 15:30-16:14 ET, labelled by the mapping window containing each bar."""
    if w is None or len(w) == 0:
        return None
    j = M.label_rows(arr, w).sort_values("_i")
    if len(j) == 0:
        return None
    a = arr[j["_i"].to_numpy()]
    ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
    hhmm = np.asarray(ts.strftime("%H:%M"))
    keep = (hhmm >= LO) & (hhmm <= HI)
    if not keep.any():
        return None
    return pd.DataFrame({"root": j["root"].to_numpy()[keep], "day": np.asarray(ts.strftime("%Y-%m-%d"))[keep],
                         "hhmm": hhmm[keep], "contract": j["contract"].to_numpy()[keep],
                         "open": a["open"][keep] * M.PX, "high": a["high"][keep] * M.PX, "low": a["low"][keep] * M.PX,
                         "close": a["close"][keep] * M.PX, "volume": a["volume"][keep].astype(np.int64)})


def worker(path: str) -> dict:
    import databento as db
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = M.ids_of(store)
    parts, n_in = [], 0
    for arr in store.to_ndarray(count=M.CHUNK):
        n_in += len(arr)
        r = window_rows(arr, w)
        if r is not None:
            parts.append(r)
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    seal(df)
    return dict(file=Path(path).name, rows_in=n_in, rows_kept=int(len(df)), secs=round(time.time() - t0, 1), bars=df)


def front_only(bars: pd.DataFrame, sess: pd.DataFrame) -> pd.DataFrame:
    f = sess[["root", "day", "contract"]].rename(columns={"contract": "front"})
    b = bars.merge(f, on=["root", "day"], how="inner")
    b = b[b["contract"] == b["front"]].drop(columns="front")
    b = b.sort_values(["root", "day", "hhmm"]).reset_index(drop=True)
    if b.duplicated(["root", "day", "hhmm"]).any():
        raise BuildError("a (root, day, minute) appears twice for the front contract")
    return b


def validate(b: pd.DataFrame) -> dict:
    out = {}
    for root in M.ROOTS:
        x = b[b["root"] == root]
        r = pd.read_csv(M.fixture_path(root), dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
        r = r[(r["day"] >= FIRST) & (r["day"] < CUTOFF) & (r["hhmm"] >= LO)]
        j = x.merge(r, on=["day", "hhmm", "contract"], how="inner", suffixes=("", "_r"))
        eq = np.ones(len(j), bool)
        for c in ("open", "high", "low", "close"):
            eq &= np.isclose(j[c].to_numpy(float), j[c + "_r"].to_numpy(float), rtol=0, atol=1e-6)
        eq &= j["volume"].to_numpy() == j["volume_r"].to_numpy()
        has1559 = set(x.loc[x["hhmm"] == "15:59", "day"])
        post = set(x.loc[(x["hhmm"] >= "16:05") & (x["hhmm"] <= "16:09"), "day"])
        v1 = float(eq.mean()) if len(j) else 0.0
        v2 = len(has1559 & post) / max(1, len(has1559))
        out[root] = {"V1_overlap_bars": int(len(j)), "V1_identical_share": v1, "V2_sessions_with_1559": len(has1559),
                     "V2_post_close_share": v2, "sessions": int(x["day"].nunique()), "span": [x["day"].min(), x["day"].max()],
                     "pass": bool(v1 >= 0.999 and v2 >= 0.95)}
    return out


def cmd_build(workers: int) -> int:
    t0 = time.time()
    files = select_files(RAW.glob("*/*.ohlcv-1m.dbn.zst"))
    if not files:
        raise BuildError("no archive files in range")
    print(f"D762 build: {len(files)} files ({sum(f.stat().st_size for f in files) / 1e9:.1f} GB), {workers} workers", flush=True)
    for f in files:
        print(f"  {f.name}", flush=True)
    order = {f.name: i for i, f in enumerate(files)}
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: order[r["file"]])
    sec = sum(r["secs"] for r in res)
    wall = time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec / wall:.2f}x on {workers} workers ({100 * sec / wall / max(workers, 1):.0f}%)", flush=True)
    bars = pd.concat([r["bars"] for r in res if len(r["bars"])], ignore_index=True)
    seal(bars)
    sess = pd.read_csv(FIX / "fut_index_sessions.csv.gz", usecols=["root", "day", "contract"], dtype=str, encoding="utf-8")
    sess = sess[(sess["day"] >= FIRST) & (sess["day"] < CUTOFF)]
    b = front_only(bars, sess)
    b = b[(b["day"] >= "2016-01-04")]
    seal(b)
    b.to_csv(OUT, index=False, compression="gzip", float_format="%.2f", encoding="utf-8")
    b2 = pd.read_csv(OUT, dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")   # validate what was written
    val = validate(b2)
    meta = {"record": "D762", "builder": "scripts/build_fut_index_close_1m.py", "reuses": "scripts/build_fut_index_1m.py (D462)",
            "window_et": [LO, HI], "span_rule": [FIRST, CUTOFF], "front_rule": "fut_index_sessions (D462), not re-derived",
            "files": [{k: v for k, v in r.items() if k != "bars"} for r in res], "rows": int(len(b2)),
            "validation": val, "all_pass": bool(all(v["pass"] for v in val.values())),
            "built_seconds": round(time.time() - t0, 1)}
    META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print("VALIDATION " + json.dumps(val, indent=1), flush=True)
    print(f"wrote {OUT.name}: {len(b2):,} rows in {time.time() - t0:.0f} s; all pass {meta['all_pass']}", flush=True)
    return 0 if meta["all_pass"] else 2


def cmd_selftest() -> int:
    fails = []
    names = ["glbx-mdp3-20150101-20151231.ohlcv-1m.dbn.zst", "glbx-mdp3-20160101-20161231.ohlcv-1m.dbn.zst",
             "glbx-mdp3-20230823-20231231.ohlcv-1m.dbn.zst", "glbx-mdp3-20240101-20240828.ohlcv-1m.dbn.zst",
             "glbx-mdp3-20231201-20240115.ohlcv-1m.dbn.zst"]
    got = [p.name for p in select_files([Path("x") / n for n in names])]
    if got != [names[1], names[2]]:
        fails.append(f"select_files {got}")
    try:
        seal(pd.DataFrame({"day": ["2023-12-29", "2024-01-02"]}))
        fails.append("the seal did not raise")
    except BuildError:
        pass
    sess = pd.DataFrame({"root": ["ES", "ES"], "day": ["2020-01-02", "2020-01-03"], "contract": ["ESH0", "ESH0"]})
    bars = pd.DataFrame({"root": ["ES"] * 3, "day": ["2020-01-02", "2020-01-02", "2020-01-03"], "hhmm": ["16:00", "16:00", "16:01"],
                         "contract": ["ESH0", "ESM0", "ESH0"], "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1})
    fb = front_only(bars, sess)
    if len(fb) != 2 or (fb["contract"] != "ESH0").any():
        fails.append("front_only")
    try:
        front_only(pd.concat([bars, bars.iloc[:1]]), sess)
        fails.append("a duplicated front minute did not raise")
    except BuildError:
        pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D762 builder] selftest: {'FAIL' if fails else 'all passed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true")
    g.add_argument("--selftest", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    sys.exit(cmd_build(a.workers) if a.build else cmd_selftest())
