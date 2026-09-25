"""Stage A's volume panel: per NYMEX session and CL/NG outright contract, the one-second-bar volume in the settlement
window and its control spans, 2017-05-22 → 2025-02-28 (settlement ledger, amendment A8's H1a).

It builds a panel and computes no statistic: no regression, no prediction, no price. H1a's dependent variable
(abnormal window volume) and its controls are later functions of these counts. The source is Databento
`ohlcv-1s` under the CME Standard subscription, whose bar volume D624's K1 matched to the trades contract for
contract.

SPANS, in ET, half-open [from, to), by bar stamp:
  * win       14:28:00–14:30:00  the settlement window (W_start → W_end)
  * pre       13:30:00–14:28:00  the pre-window activity control
  * plc       11:50:00–12:20:00  H5's time-placebo window (ledger at 11:30 → 11:50–12:20)
  * plc_pre   10:52:00–11:50:00  the placebo's own pre-window control, the same 58 minutes before it
  * rth       09:30:00–14:30:00  the day session to W_end
For each span: `vol_<span>` (contracts) and `n_<span>` (seconds with at least one trade).
`vol_ses`, `n_ses`: the whole CME session per outright, 18:00 ET the evening before → 17:00 ET, dated to its trade
date. This is the daily volume behind §5.3's V_d (added 2026-09-25). Screen volume is a floor on the cleared volume,
which also counts block trades and EFPs; the 2017–2023 cleared-volume fixture is its cross-check.
TAS (CLT, NGT): `tas_vol` and `tas_n` from the session open (18:00 ET the evening before, dated to the session)
to 14:30:00, per TAS contract month.

FILES READ, so no vault byte is ever decoded (A6: the in-sample ends 2025-02-28):
  * the main free pull's year files for 2017–2024 (jobs ohlcv1s-CL, ohlcv1s-NG, ohlcv1s-TAS). Their 2025 and
    2026 files are never opened;
  * the separate free pull for 2025-01-01 → 2025-02-28 (job a6-tail-ohlcv1s).
A guard raises if any row dated on or after 2025-03-01 reaches the output.

PARALLEL: one process per file (GIL-bound decoding). One worker is timed and its RSS printed before the fan-out
(CLAUDE.md).

OUTPUT: `data/ledger_window_volume_daily.csv.gz` (rows, gitignored by suffix) and
`data/ledger_window_volume_summary.json` (tracked). `--check` rebuilds both and compares byte for byte.

    python scripts/build_window_volume_panel.py [--check] [--probe FILE]   # SYSTEM interpreter (databento)
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

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
OUT_ROWS = REPO / "data" / "ledger_window_volume_daily.csv.gz"
OUT_SUM = REPO / "data" / "ledger_window_volume_summary.json"
FREE_JOBS = REPO / "data" / "ledger_free_pull_jobs.json"
TAIL_JOBS = REPO / "data" / "ledger_a6_tail_pull_jobs.json"
FIRST, CUT = "2017-05-22", "2025-03-01"
ET = "America/New_York"
SPANS = {"win": ("14:28:00", "14:30:00"), "pre": ("13:30:00", "14:28:00"), "plc": ("11:50:00", "12:20:00"),
         "plc_pre": ("10:52:00", "11:50:00"), "rth": ("09:30:00", "14:30:00")}
TAS_TO = "14:30:00"
SES_OPEN, SES_CLOSE = "18:00:00", "17:00:00"  # the CME energy session: 18:00 ET the evening before -> 17:00 ET
#: the as-of prices: the close of the last one-second bar stamped at or after 09:30 and strictly before each time
#: (the decision times 13:50/14:00/14:10, the placebo ledger's 11:30, and W_start 14:28). They feed P1's index
#: return from the prior settlement to tau; no return is computed here.
PX_AT = ("11:30:00", "13:50:00", "14:00:00", "14:10:00", "14:28:00")
PX_FROM = "09:30:00"
RE_OUT = re.compile(r"^(CL|NG)[FGHJKMNQUVXZ]\d{1,2}$")
RE_TAS = re.compile(r"^(CLT|NGT)[FGHJKMNQUVXZ]\d{1,2}$")
LETTER = "FGHJKMNQUVXZ"


class PanelError(RuntimeError):
    pass


def files() -> list[Path]:
    rec = json.loads(FREE_JOBS.read_text(encoding="utf-8"))
    ids = {j["label"]: j["job"]["id"] for j in rec["jobs"]}
    out: list[Path] = []
    for label in ("ohlcv1s-CL", "ohlcv1s-NG", "ohlcv1s-TAS"):
        for f in sorted((RAW / ids[label]).glob("*.ohlcv-1s.dbn.zst")):
            year = int(f.name.split("-")[2][:4])  # glbx-mdp3-YYYYMMDD-YYYYMMDD
            if year <= 2024:
                out.append(f)
    tail = json.loads(TAIL_JOBS.read_text(encoding="utf-8"))
    tid = next(j["job"]["id"] for j in tail["jobs"] if j["label"] == "a6-tail-ohlcv1s")
    out += sorted((RAW / tid).glob("*.ohlcv-1s.dbn.zst"))
    if not out:
        raise PanelError("no input files")
    return out


def _ym(sym: str, day: str) -> str:
    """D526's rule: two-digit years are explicit; a one-digit year is the nearest delivery not more than a month
    behind the session."""
    m = re.match(r"^(?:CLT|NGT|CL|NG)([FGHJKMNQUVXZ])(\d{1,2})$", sym)
    if m is None:
        raise PanelError(f"not a CL/NG outright or TAS symbol: {sym}")
    code, y = m.group(1), m.group(2)
    mon = LETTER.index(code) + 1
    if len(y) == 2:
        return f"{2000 + int(y)}-{mon:02d}"
    sy, sm = int(day[:4]), int(day[5:7])
    for cand in range(sy - 1, sy + 12):
        if cand % 10 == int(y) and cand * 12 + mon >= sy * 12 + sm - 1:
            return f"{cand}-{mon:02d}"
    raise PanelError(f"cannot date {sym} on {day}")


def work(path: str) -> pd.DataFrame:
    """One DBN file -> per (kind, root, date, symbol) span volumes and second counts."""
    import databento as db
    parts = []
    px: list[pd.DataFrame] = []
    store = db.DBNStore.from_file(path)
    for chunk in store.to_df(map_symbols=True, count=2_000_000):
        sym = chunk["symbol"].astype(str)
        is_out, is_tas = sym.str.match(RE_OUT), sym.str.match(RE_TAS)
        chunk = chunk[is_out | is_tas]
        if chunk.empty:
            continue
        ts = pd.DatetimeIndex(chunk.index).tz_convert(ET)
        clock = ts.strftime("%H:%M:%S")
        day = ts.strftime("%Y-%m-%d")
        c = pd.DataFrame({"symbol": chunk["symbol"].astype(str).to_numpy(), "clock": clock, "day": day,
                          "volume": chunk["volume"].astype("int64").to_numpy(),
                          "close": chunk["close"].astype("float64").to_numpy()})
        tas = c["symbol"].str.match(RE_TAS)
        o = c[~tas]
        for at in PX_AT:
            s = o[(o["clock"] >= PX_FROM) & (o["clock"] < at)]
            if len(s):
                last = s.sort_values("clock").groupby(["day", "symbol"]).tail(1)
                px.append(last.assign(at=at)[["day", "symbol", "at", "clock", "close"]])
        for name, (a, b) in SPANS.items():
            s = o[(o["clock"] >= a) & (o["clock"] < b)]
            if len(s):
                parts.append(s.groupby(["day", "symbol"])["volume"].agg(["sum", "count"])
                             .rename(columns={"sum": f"vol_{name}", "count": f"n_{name}"}).reset_index())
        # the whole CME session, 18:00 ET the evening before -> 17:00 ET, dated to its trade date: §5.3's V_d
        s = o.copy()
        eve = s["clock"] >= SES_OPEN
        s.loc[eve, "day"] = (pd.to_datetime(s.loc[eve, "day"]) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
        s = s[eve | (s["clock"] < SES_CLOSE)]
        if len(s):
            parts.append(s.groupby(["day", "symbol"])["volume"].agg(["sum", "count"])
                         .rename(columns={"sum": "vol_ses", "count": "n_ses"}).reset_index())
        t = c[tas].copy()
        eve = t["clock"] >= SES_OPEN
        t.loc[eve, "day"] = (pd.to_datetime(t.loc[eve, "day"]) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
        t = t[eve | (t["clock"] < TAS_TO)]
        if len(t):
            parts.append(t.groupby(["day", "symbol"])["volume"].agg(["sum", "count"])
                         .rename(columns={"sum": "tas_vol", "count": "tas_n"}).reset_index())
    if not parts:
        return pd.DataFrame(columns=["day", "symbol"])
    # chunks can split one day: sum the partial aggregates, and keep the latest as-of price across chunks
    vol = pd.concat(parts).groupby(["day", "symbol"]).sum(min_count=1).reset_index()
    if px:
        p = pd.concat(px).sort_values(["day", "symbol", "at", "clock"]).groupby(["day", "symbol", "at"]).tail(1)
        wide = p.pivot(index=["day", "symbol"], columns="at", values="close")
        wide.columns = [f"px_{a[:2]}{a[3:5]}" for a in wide.columns]
        vol = vol.merge(wide.reset_index(), on=["day", "symbol"], how="outer")
    return vol


def probe(path: str) -> None:
    t0 = time.time()
    df = work(path)
    try:
        import psutil
        rss = psutil.Process(os.getpid()).memory_info().rss / 1e9
    except ImportError:
        rss = float("nan")
    print(f"[probe] {Path(path).name}: {len(df):,} rows in {time.time() - t0:.1f} s; RSS {rss:.2f} GB")


def build(workers: int) -> tuple[str, dict[str, Any]]:
    fl = files()
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        frames = list(ex.map(work, [str(f) for f in fl]))
    df = pd.concat(frames).groupby(["day", "symbol"]).sum(min_count=1).reset_index()
    df = df[(df["day"] >= FIRST)]
    if (df["day"] >= CUT).any():
        raise PanelError(f"rows dated on or after {CUT} reached the panel: {sorted(df.loc[df['day'] >= CUT, 'day'].unique())[:5]}")
    df["kind"] = df["symbol"].map(lambda s: "tas" if RE_TAS.match(s) else "outright")
    df["root"] = df["symbol"].str[:2]
    df["ym"] = [_ym(s, d) for s, d in zip(df["symbol"], df["day"])]
    counts = [f"{p}_{n}" for n in SPANS for p in ("vol", "n")] + ["vol_ses", "n_ses", "tas_vol", "tas_n"]
    prices = [f"px_{a[:2]}{a[3:5]}" for a in PX_AT]
    cols = ["root", "kind", "day", "symbol", "ym"] + counts + prices
    for c in counts:
        if c not in df.columns:
            df[c] = 0
        df[c] = df[c].fillna(0).astype("int64")
    for c in prices:
        if c not in df.columns:
            df[c] = float("nan")
    df = df[cols].sort_values(["root", "kind", "day", "symbol"]).reset_index(drop=True)
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", encoding="utf-8")
    text = buf.getvalue()
    summary: dict[str, Any] = {
        "spec": "settlement-ledger A8 H1a: Stage A's volume panel; see the script docstring",
        "span_first": FIRST, "cut": CUT, "rows": int(len(df)),
        "files": [{"name": f.name, "bytes": f.stat().st_size} for f in fl],
        "per_root": {}, "rows_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    for (root, kind), g in df.groupby(["root", "kind"]):
        summary["per_root"][f"{root}_{kind}"] = {
            "sessions": int(g["day"].nunique()), "first": str(g["day"].min()), "last": str(g["day"].max()),
            "contracts": int(g["symbol"].nunique()),
            "total_window_volume": int(g["vol_win"].sum()) if kind == "outright" else None,
            "total_tas_volume": int(g["tas_vol"].sum()) if kind == "tas" else None}
    return text, summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--probe", metavar="FILE")
    ap.add_argument("--workers", type=int, default=min(8, os.cpu_count() or 1))
    a = ap.parse_args(argv)
    if a.probe:
        probe(a.probe)
        return 0
    text, summary = build(a.workers)
    stext = json.dumps(summary, indent=1, sort_keys=True) + "\n"
    if a.check:
        with gzip.open(OUT_ROWS, "rt", encoding="utf-8", newline="") as fh:
            if fh.read() != text:
                raise PanelError(f"{OUT_ROWS.name} does not reproduce")
        if OUT_SUM.read_text(encoding="utf-8") != stext:
            raise PanelError(f"{OUT_SUM.name} does not reproduce")
        print("[check] both outputs reproduce byte for byte")
        return 0
    b = io.BytesIO()
    with gzip.GzipFile(fileobj=b, mode="wb", mtime=0) as gz:
        gz.write(text.encode("utf-8"))
    OUT_ROWS.write_bytes(b.getvalue())
    OUT_SUM.write_text(stext, encoding="utf-8", newline="\n")
    for k, v in summary["per_root"].items():
        print(k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())
