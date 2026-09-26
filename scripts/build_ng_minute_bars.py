"""NG one-minute bars around the settlement and the placebo window, per outright contract and session, from
Databento's one-second bars (settlement ledger, H2's price input; AITODO 2026-09-26).

It builds a panel and computes no statistic: no return, no direction, no signal. H2's signed return and its
controls are later functions of these bars.

BARS, ET, start-stamped, [HH:MM, HH:MM+1):
  * 11:30 → 12:20: the time placebo (the ledger at 11:30, fill at the 11:31 bar's close, exit at the 12:19 bar's close);
  * 13:50 → 15:00: the decision times 13:50 / 14:00 / 14:10, the fills at t0+1, the window's bars 14:28 and 14:29
    (W_start → W_end) and 30 minutes after it (H4's event curve and §7.5's post-window fade).
Per bar: `open`, `high`, `low`, `close` (the one-second bars' first open, max high, min low, last close) and
`volume`. A minute with no trade has no row. The as-of price before a block is the volume panel's `px_1130` /
`px_1350` (the last close from 09:30, `build_window_volume_panel.py`).

FILES READ, so no vault byte is decoded (A6: the in-sample ends 2025-02-28): the main free pull's NG year files for
2017–2024 (job ohlcv1s-NG; its 2025 and 2026 files are never opened) and the separate 2025-01-01 → 2025-02-28 pull
(job a6-tail-ohlcv1s). A guard raises if a row dated on or after 2025-03-01 reaches the output.

KNOWN ANSWER (raises): the bars' volume summed over 14:28 and 14:29 equals the volume panel's `vol_win`, and over
11:50 → 12:19 its `vol_plc`, on every (contract, day) of both; the 13:50 bar's open-to-close prices are consistent with
the panel's `px_1350` (the 13:49 bar's close, where one exists, is the as-of price).

PARALLEL: one process per file (GIL-bound decoding). One worker is timed before the fan-out (CLAUDE.md).

Output: `data/ng_minute_bars.csv.gz` (gitignored by suffix) and `data/ng_minute_bars_summary.json`.

    python scripts/build_ng_minute_bars.py [--check] [--probe FILE]   # SYSTEM interpreter (databento)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import hashlib
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
FREE_JOBS = REPO / "data" / "ledger_free_pull_jobs.json"
TAIL_JOBS = REPO / "data" / "ledger_a6_tail_pull_jobs.json"
PANEL = REPO / "data" / "ledger_window_volume_daily.csv.gz"
OUT_ROWS = REPO / "data" / "ng_minute_bars.csv.gz"
OUT_SUM = REPO / "data" / "ng_minute_bars_summary.json"
FIRST, CUT = "2017-05-22", "2025-03-01"
ET = "America/New_York"
BLOCKS = (("11:30:00", "12:20:00"), ("13:49:00", "15:00:00"))
RE_OUT = re.compile(r"^NG[FGHJKMNQUVXZ]\d{1,2}$")


class MinuteBarError(RuntimeError):
    pass


def files() -> list[Path]:
    rec = json.loads(FREE_JOBS.read_text(encoding="utf-8"))
    ids = {j["label"]: j["job"]["id"] for j in rec["jobs"]}
    out = [f for f in sorted((RAW / ids["ohlcv1s-NG"]).glob("*.ohlcv-1s.dbn.zst"))
           if int(f.name.split("-")[2][:4]) <= 2024]
    tail = json.loads(TAIL_JOBS.read_text(encoding="utf-8"))
    tid = next(j["job"]["id"] for j in tail["jobs"] if j["label"] == "a6-tail-ohlcv1s")
    out += sorted((RAW / tid).glob("*.ohlcv-1s.dbn.zst"))
    if not out:
        raise MinuteBarError("no input files")
    return out


def work(path: str) -> pd.DataFrame:
    import databento as db  # type: ignore[import-not-found]
    parts = []
    for chunk in db.DBNStore.from_file(path).to_df(map_symbols=True, count=2_000_000):
        sym = chunk["symbol"].astype(str)
        chunk = chunk[sym.str.match(RE_OUT)]
        if chunk.empty:
            continue
        ts = pd.DatetimeIndex(chunk.index).tz_convert(ET)
        clock = np.asarray(ts.strftime("%H:%M:%S"))
        k = np.zeros(len(chunk), dtype=bool)
        for a, b in BLOCKS:
            k |= (clock >= a) & (clock < b)
        if not k.any():
            continue
        c = chunk[k]
        parts.append(pd.DataFrame({
            "day": ts[k].strftime("%Y-%m-%d"), "symbol": c["symbol"].astype(str).to_numpy(),
            "minute": ts[k].strftime("%H:%M"), "sec": clock[k],
            "open": c["open"].astype("float64").to_numpy(), "high": c["high"].astype("float64").to_numpy(),
            "low": c["low"].astype("float64").to_numpy(), "close": c["close"].astype("float64").to_numpy(),
            "volume": c["volume"].astype("int64").to_numpy()}))
    if not parts:
        return pd.DataFrame(columns=["day", "symbol", "minute", "open", "high", "low", "close", "volume"])
    s = pd.concat(parts).sort_values(["day", "symbol", "sec"], kind="mergesort")
    g = s.groupby(["day", "symbol", "minute"], sort=True)
    return pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                         "close": g["close"].last(), "volume": g["volume"].sum()}).reset_index()


def _ym(sym: str, day: str) -> str:
    """The volume panel's own dating rule (D526), loaded by path so that its databento import stays unchecked."""
    import importlib.util
    if "build_window_volume_panel" not in sys.modules:
        spec = importlib.util.spec_from_file_location("build_window_volume_panel",
                                                      REPO / "scripts" / "build_window_volume_panel.py")
        assert spec is not None and spec.loader is not None
        m = importlib.util.module_from_spec(spec)
        sys.modules["build_window_volume_panel"] = m
        spec.loader.exec_module(m)
    return str(sys.modules["build_window_volume_panel"]._ym(sym, day))


def known_answer(df: pd.DataFrame) -> dict[str, Any]:
    p = pd.read_csv(PANEL, encoding="utf-8", usecols=["root", "kind", "day", "symbol", "vol_win", "vol_plc", "px_1350"])
    p = p[(p["root"] == "NG") & (p["kind"] == "outright")].set_index(["day", "symbol"])
    win = df[df["minute"].isin(["14:28", "14:29"])].groupby(["day", "symbol"])["volume"].sum()
    plc = df[(df["minute"] >= "11:50") & (df["minute"] < "12:20")].groupby(["day", "symbol"])["volume"].sum()
    j = p[["vol_win", "vol_plc"]].join(win.rename("bars_win"), how="outer").join(plc.rename("bars_plc"), how="outer")
    j = j.fillna(0)
    bad_win = int((j["vol_win"] != j["bars_win"]).sum())
    bad_plc = int((j["vol_plc"] != j["bars_plc"]).sum())
    last49 = df[df["minute"] == "13:49"].set_index(["day", "symbol"])["close"]
    both = p["px_1350"].dropna().to_frame().join(last49.rename("c49"), how="inner")
    bad_px = int((both["px_1350"] != both["c49"]).sum())
    out = {"pairs": int(len(j)), "window_volume_mismatches": bad_win, "placebo_volume_mismatches": bad_plc,
           "px_1350_vs_1349_close_pairs": int(len(both)), "px_1350_mismatches": bad_px}
    if bad_win or bad_plc or bad_px:
        raise MinuteBarError(f"known answer fails: {out}")
    return out


def build(workers: int) -> tuple[bytes, str]:
    sys.path.insert(0, str(REPO / "scripts"))
    fl = files()
    t0 = time.time()
    first = work(str(fl[0]))
    print(f"one worker: {fl[0].name} -> {len(first):,} bars in {time.time() - t0:.0f}s", flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        frames = [first] + list(ex.map(work, [str(f) for f in fl[1:]]))
    df = pd.concat(frames, ignore_index=True)
    df = df[df["day"] >= FIRST]
    if (df["day"] >= CUT).any():
        raise MinuteBarError("a row on or after the cut reached the panel")
    if df.duplicated(["day", "symbol", "minute"]).any():
        raise MinuteBarError("a (day, symbol, minute) appears twice: a day split across files")
    df["ym"] = [_ym(s, d) for s, d in zip(df["symbol"], df["day"])]
    df = df[["day", "symbol", "ym", "minute", "open", "high", "low", "close", "volume"]]
    df = df.sort_values(["day", "symbol", "minute"]).reset_index(drop=True)
    ka = known_answer(df)
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", float_format="%.6g", encoding="utf-8")
    text = buf.getvalue()
    summ = {"first": FIRST, "cut": CUT, "blocks_et": BLOCKS, "rows": int(len(df)),
            "sessions": int(df["day"].nunique()), "contracts": int(df["symbol"].nunique()),
            "files": [{"name": f.name, "bytes": f.stat().st_size} for f in fl],
            "known_answer": ka, "rows_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    return gzip.compress(text.encode("utf-8"), mtime=0), json.dumps(summ, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--probe", metavar="FILE")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    a = ap.parse_args(argv)
    if a.probe:
        t0 = time.time()
        print(f"[probe] {len(work(a.probe)):,} bars in {time.time() - t0:.1f}s")
        return 0
    gz, summ = build(a.workers)
    if a.check:
        if OUT_ROWS.read_bytes() != gz or OUT_SUM.read_text(encoding="utf-8") != summ:
            raise MinuteBarError("the panel does not reproduce")
        print("[check] both outputs reproduce byte for byte")
        return 0
    OUT_ROWS.write_bytes(gz)
    OUT_SUM.write_text(summ, encoding="utf-8", newline="\n")
    print(summ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
