"""CL one-minute bars around the settlement and the placebo window, per outright contract and session, from
Databento's one-second bars (settlement ledger, H2's price input). A mirror of `build_ng_minute_bars.py` for CL.

It builds a panel and computes no statistic: no return, no direction, no signal. H2's signed return and its
controls are later functions of these bars.

BARS, ET, start-stamped, [HH:MM, HH:MM+1):
  * 11:30 → 12:20: the time placebo (the ledger at 11:30, fill at the 11:31 bar's close, exit at the 12:19 bar's close);
  * 13:49 → 15:00: the as-of 13:49 bar, the decision times 13:50 / 14:00 / 14:10, the fills at t0+1, the window's bars
    14:28 and 14:29 (W_start → W_end) and 30 minutes after it (H4's event curve and §7.5's post-window fade).
Per bar: `open`, `high`, `low`, `close` (the one-second bars' first open, max high, min low, last close) and
`volume`. A minute with no trade has no row. The as-of price before a block is the volume panel's `px_1130` /
`px_1350` (the last close from 09:30, `build_window_volume_panel.py`). Every CL outright is covered, not only the
held contracts (CL's era B holds three a day; selection is a later function).

FILES READ, so no vault byte is decoded (A6: the in-sample ends 2025-02-28): the main free pull's CL year files for
2017–2024 (job ohlcv1s-CL; its 2025 and 2026 files are never opened, and `_vault_guard` raises if one is ever
selected) and the separate 2025-01-01 → 2025-02-28 pull (job a6-tail-ohlcv1s, which also holds NG; CL outrights
only are kept). A guard raises if a row dated on or after 2025-03-01 reaches the output.

The raw pulls and the volume panel are gitignored and live in the MAIN checkout; run from a worktree they are read
from there (`_main_checkout`, as in `build_fut_nq_options_eod.py`). The outputs are written to this checkout.

KNOWN ANSWER (raises): the bars' volume summed over 14:28 and 14:29 equals the volume panel's `vol_win`, and over
11:50 → 12:19 its `vol_plc`, on every CL outright (contract, day) of both; the 13:49 bar's close, where one exists,
equals the panel's `px_1350` (the as-of price).

PARALLEL: one process per file (GIL-bound decoding). One worker is timed and the wall time projected before the
fan-out (CLAUDE.md).

Output: `data/cl_minute_bars.csv.gz` (gitignored by suffix) and `data/cl_minute_bars_summary.json`.

    python scripts/build_cl_minute_bars.py [--check] [--selftest] [--probe FILE]   # SYSTEM interpreter (databento)
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


def _main_checkout(repo: Path) -> Path:
    """This builder may run in a worktree; the gitignored raw pulls and the volume panel live in the MAIN checkout."""
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


MAIN = _main_checkout(REPO)


def _resolve(rel: str) -> Path:
    """This checkout's copy if it exists, else the main checkout's."""
    p = REPO / rel
    return p if p.exists() else MAIN / rel


RAW = MAIN / "data" / "raw" / "databento"          # the raw cache lives in the main checkout (a worktree's is partial)
FREE_JOBS = REPO / "data" / "ledger_free_pull_jobs.json"
TAIL_JOBS = REPO / "data" / "ledger_a6_tail_pull_jobs.json"
PANEL = _resolve("data/ledger_window_volume_daily.csv.gz")
OUT_ROWS = REPO / "data" / "cl_minute_bars.csv.gz"
OUT_SUM = REPO / "data" / "cl_minute_bars_summary.json"
FIRST, CUT = "2017-05-22", "2025-03-01"
LAST_MAIN_YEAR = 2024                                   # the main job's 2025 and 2026 files are never opened
MAIN_LABEL, TAIL_LABEL = "ohlcv1s-CL", "a6-tail-ohlcv1s"
ET = "America/New_York"
BLOCKS = (("11:30:00", "12:20:00"), ("13:49:00", "15:00:00"))
RE_OUT = re.compile(r"^CL[FGHJKMNQUVXZ]\d{1,2}$")
COLS = ["day", "symbol", "ym", "minute", "open", "high", "low", "close", "volume"]


class MinuteBarError(RuntimeError):
    pass


def _year(f: Path) -> int:
    return int(f.name.split("-")[2][:4])  # glbx-mdp3-YYYYMMDD-YYYYMMDD


def _vault_guard(paths: list[Path], main_id: str) -> None:
    """Raises if any main-job file whose span starts in 2025 or later is selected."""
    bad = [f.name for f in paths if f.parent.name == main_id and _year(f) > LAST_MAIN_YEAR]
    if bad:
        raise MinuteBarError(f"vault: main-job files from {LAST_MAIN_YEAR + 1} on were selected: {bad}")


def files() -> list[Path]:
    rec = json.loads(FREE_JOBS.read_text(encoding="utf-8"))
    ids = {j["label"]: j["job"]["id"] for j in rec["jobs"]}
    main_id = ids[MAIN_LABEL]
    out = [f for f in sorted((RAW / main_id).glob("*.ohlcv-1s.dbn.zst")) if _year(f) <= LAST_MAIN_YEAR]
    tail = json.loads(TAIL_JOBS.read_text(encoding="utf-8"))
    tid = next(j["job"]["id"] for j in tail["jobs"] if j["label"] == TAIL_LABEL)
    out += sorted((RAW / tid).glob("*.ohlcv-1s.dbn.zst"))
    if not out:
        raise MinuteBarError("no input files")
    _vault_guard(out, main_id)
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


def _finalise(df: pd.DataFrame) -> pd.DataFrame:
    """The span and vault guards: sessions from FIRST, nothing on or after CUT, one row per (day, symbol, minute)."""
    df = df[df["day"] >= FIRST]
    if (df["day"] >= CUT).any():
        raise MinuteBarError(f"a row on or after the cut reached the panel: "
                             f"{sorted(df.loc[df['day'] >= CUT, 'day'].unique())[:5]}")
    if df.duplicated(["day", "symbol", "minute"]).any():
        raise MinuteBarError("a (day, symbol, minute) appears twice: a day split across files")
    if not df["symbol"].map(lambda s: bool(RE_OUT.match(str(s)))).all():
        raise MinuteBarError("a non-CL-outright symbol reached the panel")
    return df


def _panel() -> pd.DataFrame:
    p = pd.read_csv(PANEL, encoding="utf-8", usecols=["root", "kind", "day", "symbol", "vol_win", "vol_plc", "px_1350"])
    return p[(p["root"] == "CL") & (p["kind"] == "outright")]


def known_answer(df: pd.DataFrame, panel: pd.DataFrame | None = None) -> dict[str, Any]:
    p = (_panel() if panel is None else panel).set_index(["day", "symbol"])
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
        ex = j[(j["vol_win"] != j["bars_win"]) | (j["vol_plc"] != j["bars_plc"])].head(10)
        raise MinuteBarError(f"known answer fails: {out}\nfirst volume mismatches:\n{ex}\n"
                             f"first price mismatches:\n{both[both['px_1350'] != both['c49']].head(10)}")
    return out


def build(workers: int) -> tuple[bytes, str]:
    sys.path.insert(0, str(REPO / "scripts"))
    fl = files()
    t0 = time.time()
    first = work(str(fl[0]))
    t1 = time.time() - t0
    rest = fl[1:]
    rounds = -(-len(rest) // max(workers, 1))
    per_byte = t1 / fl[0].stat().st_size
    proj = t1 + rounds * per_byte * max(f.stat().st_size for f in rest) if rest else t1
    print(f"one worker: {fl[0].name} -> {len(first):,} bars in {t1:.0f}s; projected wall {proj / 60:.1f} min "
          f"({len(rest)} files on {workers} processes, largest {max(f.stat().st_size for f in rest) / 1e6:.0f} MB)",
          flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        frames = [first] + list(ex.map(work, [str(f) for f in rest]))
    print(f"decoded in {time.time() - t0:.0f}s", flush=True)
    df = _finalise(pd.concat(frames, ignore_index=True))
    df["ym"] = [_ym(s, d) for s, d in zip(df["symbol"], df["day"])]
    df = df[COLS]
    df = df.sort_values(["day", "symbol", "minute"]).reset_index(drop=True)
    ka = known_answer(df)
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", float_format="%.6g", encoding="utf-8")
    text = buf.getvalue()
    summ = {"first": FIRST, "cut": CUT, "blocks_et": BLOCKS, "rows": int(len(df)),
            "sessions": int(df["day"].nunique()), "contracts": int(df["symbol"].nunique()),
            "files": [{"job": f.parent.name, "name": f.name, "bytes": f.stat().st_size} for f in fl],
            "known_answer": ka, "rows_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    return gzip.compress(text.encode("utf-8"), mtime=0), json.dumps(summ, indent=1, sort_keys=True) + "\n"


def selftest() -> int:
    """A clean synthetic case passes; each guard RAISES when the scalar it compares is broken."""
    days, syms = ["2019-03-04", "2019-03-05"], ["CLJ9", "CLK9"]
    rows, prow = [], []
    for d in days:
        for i, s in enumerate(syms):
            for m, v in (("11:49", 5), ("11:50", 3 + i), ("12:19", 2), ("13:49", 7), ("14:28", 11 + i), ("14:29", 4),
                         ("14:30", 9)):
                rows.append({"day": d, "symbol": s, "minute": m, "open": 50.0, "high": 50.5, "low": 49.5,
                             "close": 50.0 + i / 100 if m == "13:49" else 50.25, "volume": v})
            prow.append({"root": "CL", "kind": "outright", "day": d, "symbol": s, "vol_win": 15 + i,
                         "vol_plc": 5 + i, "px_1350": 50.0 + i / 100})
    bars = pd.DataFrame(rows)
    panel = pd.DataFrame(prow)
    panel = pd.concat([panel, pd.DataFrame([{"root": "CL", "kind": "outright", "day": "2019-03-06",
                                             "symbol": "CLJ9", "vol_win": 0, "vol_plc": 0, "px_1350": np.nan}])])
    ok = known_answer(bars, panel)
    assert ok["pairs"] == 5 and ok["px_1350_vs_1349_close_pairs"] == 4, ok
    _finalise(bars)
    main_id = "GLBX-TEST"
    good = [Path(main_id) / "glbx-mdp3-20240101-20241231.ohlcv-1s.dbn.zst",
            Path("GLBX-TAIL") / "glbx-mdp3-20250101-20250228.ohlcv-1s.dbn.zst"]
    _vault_guard(good, main_id)

    def must_raise(name: str, fn: Any) -> None:
        try:
            fn()
        except MinuteBarError:
            print(f"[selftest] {name}: raises, as it must")
            return
        raise AssertionError(f"[selftest] {name}: did NOT raise on a broken input")

    b = bars.copy(); b.loc[(b["minute"] == "14:28") & (b["symbol"] == "CLK9"), "volume"] += 1
    must_raise("window volume (14:28 bar +1)", lambda: known_answer(b, panel))
    b = bars.copy(); b.loc[b.index[b["minute"] == "14:29"][0], "minute"] = "14:30"
    must_raise("window volume (a 14:29 bar moved out)", lambda: known_answer(b, panel))
    b = bars.copy(); b.loc[(b["minute"] == "11:50") & (b["day"] == days[1]), "volume"] -= 1
    must_raise("placebo volume (11:50 bar -1)", lambda: known_answer(b, panel))
    p2 = panel.copy(); p2.loc[p2["day"] == "2019-03-06", "vol_plc"] = 1
    must_raise("placebo volume (a panel row the bars lack)", lambda: known_answer(bars, p2))
    b = bars.copy(); b.loc[b.index[b["minute"] == "13:49"][0], "close"] += 0.01
    must_raise("px_1350 (13:49 close +0.01)", lambda: known_answer(b, panel))
    b = pd.concat([bars, bars.iloc[[0]].assign(day="2025-03-03")])
    must_raise("vault cut (a row dated 2025-03-03)", lambda: _finalise(b))
    b = pd.concat([bars, bars.iloc[[0]].assign(day="2025-03-01")])
    must_raise("vault cut (a row dated 2025-03-01, the cut itself)", lambda: _finalise(b))
    must_raise("vault files (main-job 2025 file selected)",
               lambda: _vault_guard(good + [Path(main_id) / "glbx-mdp3-20250101-20251231.ohlcv-1s.dbn.zst"], main_id))
    must_raise("vault files (main-job 2026 file selected)",
               lambda: _vault_guard(good + [Path(main_id) / "glbx-mdp3-20260101-20260918.ohlcv-1s.dbn.zst"], main_id))
    must_raise("duplicate (day, symbol, minute)", lambda: _finalise(pd.concat([bars, bars.iloc[[0]]])))
    must_raise("non-CL-outright symbol", lambda: _finalise(pd.concat([bars, bars.iloc[[0]].assign(symbol="NGJ9")])))
    print("[selftest] clean case passes; every guard raises on its break")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--probe", metavar="FILE")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
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
