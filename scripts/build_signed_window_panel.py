"""Aggressor-signed volume per CL/NG contract and NYMEX session in the settlement window and its control spans, from
Sierra Chart's 1-tick files (settlement ledger, the signed-H1 route; AITODO 2026-09-26).

It builds a panel and computes no statistic against any predictor: no regression, no Q, no price. The signed-H1
dependent and its controls are later functions of these sums.

SOURCE: `C:\\SierraChart\\Data\\<SYM>-NYMEX.scid`, downloaded by `sierra_bulk_download.py`. 40-byte records:
int64 microseconds since 1899-12-30 UTC; o/h/l/c float32; NumTrades, TotalVolume, BidVolume, AskVolume uint32.
AskVolume is buyer-initiated and BidVolume seller-initiated. `net = AskVolume - BidVolume` (+ = buyers). On the
sibling year (HO/RB, `check_sierra_aggressor.py`) Sierra's window net flow had r 0.877 and 0.875 with the exchange's
aggressor flow, and window total volume matched exactly: the error is the ~29% of volume the exchange marks with no
aggressor (spread legs), which Sierra Chart signs by its own rule.

SPANS, ET, half-open [from, to), by record time (the volume panel's, `build_window_volume_panel.SPANS`):
  win 14:28:00-14:30:00 · pre 13:30:00-14:28:00 · plc 11:50:00-12:20:00 · plc_pre 10:52:00-11:50:00.
Per span: `v_<span>` (TotalVolume), `net_<span>` (Ask - Bid), `sided_<span>` (Ask + Bid) and `n_<span>` (records).

CONTRACTS: the 125 the ledger's funds held in the in-sample (`sierra_bulk_download.contract_list`) and the 26
pre-sample holdings (BCOM lead and next, 2015-06-01 -> 2017-05-19) for the power study's noise. `sample` is `pre`
before 2017-05-22 and `in` from it.

THE VAULT IS NEVER DECODED (A6: the in-sample ends 2025-02-28). Each file is memory-mapped and the first record at
or after 2025-03-01 00:00 ET is found by binary search on the timestamps; nothing from that record on is decoded.
The prefix is asserted sorted and wholly before the cut, and the output is asserted to hold no day on or after it.

KNOWN ANSWER (raises below the bar; `known_answer` says how the bar was set): each in-sample (contract, day) window
volume `v_win` against Databento's `vol_win` (`data/ledger_window_volume_daily.csv.gz`, already read by D627), on
the days the Sierra file covers. Per root, >= 95% of contract-days within 1% and the total ratio within 1%; the
exact-equality share is reported, and the same for `pre` and `plc`.

Output: `data/ledger_signed_window_daily.csv.gz` (gitignored by suffix) and `data/ledger_signed_window_summary.json`.

    uv run python scripts/build_signed_window_panel.py [--check]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
SC_DATA = Path(r"C:\SierraChart\Data")
DBN_WIN = REPO / "data" / "ledger_window_volume_daily.csv.gz"
OUT_ROWS = REPO / "data" / "ledger_signed_window_daily.csv.gz"
OUT_SUM = REPO / "data" / "ledger_signed_window_summary.json"
ET = "America/New_York"
FIRST_IN, CUT = "2017-05-22", "2025-03-01"
PRE_FROM = "2015-06-01"
SPANS = {"win": ("14:28:00", "14:30:00"), "pre": ("13:30:00", "14:28:00"), "plc": ("11:50:00", "12:20:00"),
         "plc_pre": ("10:52:00", "11:50:00")}
PRESAMPLE = ("CLF16,CLF17,CLH16,CLH17,CLK16,CLK17,CLN15,CLN16,CLN17,CLU15,CLU16,CLX15,CLX16,"
             "NGF16,NGF17,NGH16,NGH17,NGK16,NGK17,NGN15,NGN16,NGN17,NGU15,NGU16,NGX15,NGX16").split(",")
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")
LETTER = "FGHJKMNQUVXZ"
KNOWN_ANSWER_BAR = 0.95


class SignedPanelError(RuntimeError):
    pass


def _us(ts: pd.Timestamp) -> int:
    return int((ts - ORIGIN) // pd.Timedelta(microseconds=1))


CUT_US = _us(pd.Timestamp(CUT, tz=ET).tz_convert("UTC"))
FROM_US = _us(pd.Timestamp(PRE_FROM, tz=ET).tz_convert("UTC"))


def _sec(hms: str) -> int:
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 3600 + m * 60 + s


def one(sym: str) -> tuple[str, pd.DataFrame, dict[str, Any]]:
    path = SC_DATA / f"{sym}-NYMEX.scid"
    with open(path, "rb") as fh:
        head = fh.read(12)
    if head[:4] != b"SCID":
        raise SignedPanelError(f"{sym}: not an SCID file")
    hdr, rs = int.from_bytes(head[4:8], "little"), int.from_bytes(head[8:12], "little")
    if rs != REC.itemsize:
        raise SignedPanelError(f"{sym}: record size {rs}")
    mm = np.memmap(path, dtype=REC, mode="r", offset=hdr)
    dt_all = mm["dt"]
    cut = int(np.searchsorted(dt_all, CUT_US, side="left"))
    lo = int(np.searchsorted(dt_all[:cut], FROM_US, side="left"))
    dt = np.array(dt_all[lo:cut])
    # Sierra Chart files are sorted up to millisecond inversions (NGH17: one of 2 ms). The binary search is exact
    # unless an inversion straddles the cut, so: no inversion of 1 s or more before it, nothing at or past it in the
    # prefix, and the 100 records after it all at or past it (their timestamps only).
    inv = np.diff(dt)
    if len(dt) and (dt.max() >= CUT_US or (inv < -1_000_000).any()):
        raise SignedPanelError(f"{sym}: the decoded prefix reaches the cut or has an inversion of 1 s or more")
    if cut < len(dt_all) and int(np.min(dt_all[cut:cut + 100])) < CUT_US:
        raise SignedPanelError(f"{sym}: a record after the cut index is before the cut")
    meta: dict[str, Any] = {"records_decoded": int(len(dt)), "inversions_below_1s": int((inv < 0).sum()),
                            "records_after_cut_not_decoded": int(len(dt_all) - cut)}
    if not len(dt):
        return sym, pd.DataFrame(), meta
    # coarse UTC pre-filter (ET 10:52-14:30 lies inside UTC 14:00-20:00 in both EST and EDT), then exact ET spans
    tod_utc = (dt % 86_400_000_000) // 1_000_000
    keep = (tod_utc >= 14 * 3600) & (tod_utc < 20 * 3600)
    sub = mm[lo:cut][keep]
    et = (ORIGIN + pd.to_timedelta(np.asarray(sub["dt"]), unit="us")).tz_convert(ET)
    wall = np.asarray(et.tz_localize(None).as_unit("ns").asi8)  # ET wall-clock ns since 1970 (unit pinned: asi8 is
    # in the index's own unit, microseconds here)
    day_ns = 86_400 * 10**9
    tod = (wall % day_ns) // 10**9
    day = wall // day_ns  # ET calendar day number; turned into a date string once per group below
    first_et = (ORIGIN + pd.Timedelta(microseconds=int(dt[0]))).tz_convert(ET)
    meta["first_et"] = str(first_et)
    frames = []
    for span, (a, b) in SPANS.items():
        m = (tod >= _sec(a)) & (tod < _sec(b))
        if not m.any():
            continue
        v = np.asarray(sub["v"][m], dtype=np.int64)
        bv = np.asarray(sub["bv"][m], dtype=np.int64)
        av = np.asarray(sub["av"][m], dtype=np.int64)
        g = pd.DataFrame({"day": day[m], "v": v, "net": av - bv, "sided": av + bv, "n": 1}).groupby("day").sum()
        frames.append(g.add_suffix(f"_{span}"))
    if not frames:
        return sym, pd.DataFrame(), meta
    out = pd.concat(frames, axis=1).fillna(0).astype("int64").reset_index()
    out["day"] = pd.to_datetime(out["day"], unit="D").dt.strftime("%Y-%m-%d")
    out.insert(0, "symbol", sym)
    return sym, out, meta


def symbols() -> list[str]:
    import sierra_bulk_download as S
    return sorted(set(S.contract_list()) | set(PRESAMPLE))


def ym_of(sym: str) -> str:
    return f"20{sym[3:5]}-{LETTER.index(sym[2]) + 1:02d}"


def known_answer(df: pd.DataFrame, first_day: dict[str, str]) -> dict[str, Any]:
    """Sierra's window volume against Databento's, on the days each Sierra file covers (after its first record's ET
    date; a day before the file starts is not a comparison). The first version compared every Databento day and
    required exact equality on 95%: it fired at 0.33, almost all from uncovered days. On covered days the two agree
    exactly on ~90-98% of contract-days, and the rest differ by a few contracts at the window's edges (Databento's
    one-second bars are stamped on its receive clock). The bar, set after seeing that: within 1% of the window's
    volume on >= 95% of contract-days, and the total ratio within 1%. The exact share is reported beside it."""
    dbn = pd.read_csv(DBN_WIN, encoding="utf-8", usecols=["root", "kind", "day", "ym", "vol_win", "vol_pre", "vol_plc"])
    dbn = dbn[dbn["kind"] == "outright"].drop(columns="kind")
    ins = df[df["sample"] == "in"]
    held = set(zip(ins["root"], ins["ym"]))
    dbn = dbn[[k in held for k in zip(dbn["root"], dbn["ym"])]]
    m = ins.merge(dbn, on=["root", "day", "ym"], how="outer")
    first = m["root"] + ":" + m["ym"]
    m = m[m["day"].to_numpy() > first.map(first_day).to_numpy()]
    out: dict[str, Any] = {}
    for span in ("win", "pre", "plc"):
        a, b = m[f"v_{span}"].fillna(0), m[f"vol_{span}"].fillna(0)
        live = (a > 0) | (b > 0)
        eq = (a == b) & live
        near = ((a - b).abs() <= 0.01 * b.clip(lower=1)) & live
        out[span] = {"pairs_with_volume": int(live.sum()), "equal_share": round(float(eq.sum() / live.sum()), 6),
                     "within_1pct_share": round(float(near.sum() / live.sum()), 6),
                     "sierra_over_databento_total": round(float(a[live].sum() / b[live].sum()), 6)}
    out["win"]["by_root"] = {}
    for r, g in m.groupby("root"):
        a, b = g["v_win"].fillna(0), g["vol_win"].fillna(0)
        live = (a > 0) | (b > 0)
        out["win"]["by_root"][r] = {
            "equal_share": round(float(((a == b) & live).sum() / live.sum()), 6),
            "within_1pct_share": round(float((((a - b).abs() <= 0.01 * b.clip(lower=1)) & live).sum() / live.sum()), 6),
            "sierra_over_databento_total": round(float(a[live].sum() / b[live].sum()), 6)}
    for r, v in out["win"]["by_root"].items():
        if v["within_1pct_share"] < KNOWN_ANSWER_BAR or abs(v["sierra_over_databento_total"] - 1) > 0.01:
            raise SignedPanelError(f"{r}: window volume against Databento fails the known answer: {out}")
    return out


def build() -> tuple[bytes, str]:
    syms = symbols()
    missing = [s for s in syms if not (SC_DATA / f"{s}-NYMEX.scid").exists()]
    if missing:
        raise SignedPanelError(f"no Sierra Chart file for {missing}")
    t0 = time.time()
    first = one(syms[0])
    print(f"one worker: {syms[0]} {first[2]['records_decoded']:,} records in {time.time() - t0:.1f}s", flush=True)
    res = {first[0]: first}
    with cf.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as ex:
        for sym, frame, meta in ex.map(one, syms[1:]):
            res[sym] = (sym, frame, meta)
    print(f"all {len(syms)} files in {time.time() - t0:.0f}s", flush=True)
    frames = [res[s][1] for s in syms if len(res[s][1])]
    df = pd.concat(frames, ignore_index=True)
    df.insert(0, "root", df["symbol"].str[:2])
    df.insert(3, "ym", df["symbol"].map(ym_of))
    df.insert(4, "sample", np.where(df["day"] < FIRST_IN, "pre", "in"))
    cols = ["root", "symbol", "day", "ym", "sample"] + [f"{k}_{s}" for s in SPANS for k in ("v", "net", "sided", "n")]
    for c in cols[5:]:
        if c not in df:
            df[c] = 0
    df[cols[5:]] = df[cols[5:]].fillna(0).astype("int64")
    df = df[cols].sort_values(["root", "day", "symbol"]).reset_index(drop=True)
    if (df["day"] >= CUT).any() or (df["day"] < PRE_FROM).any():
        raise SignedPanelError("a row outside 2015-06-01 .. 2025-02-28 survived")
    first_day = {f"{s[:2]}:{ym_of(s)}": res[s][2]["first_et"][:10] for s in syms if "first_et" in res[s][2]}
    ka = known_answer(df, first_day)
    summ: dict[str, Any] = {
        "cut": CUT, "first_in": FIRST_IN, "pre_from": PRE_FROM, "spans_et": SPANS,
        "files": {s: res[s][2] for s in syms},
        "rows": {f"{r}_{smp}": int(len(g)) for (r, smp), g in df.groupby(["root", "sample"])},
        "sided_share_of_volume": {span: round(float(df[f"sided_{span}"].sum() / df[f"v_{span}"].sum()), 6)
                                  for span in SPANS},
        "known_answer_vs_databento": ka,
    }
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", encoding="utf-8")
    gz = gzip.compress(buf.getvalue().encode("utf-8"), mtime=0)
    return gz, json.dumps(summ, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="rebuild and compare byte for byte")
    a = ap.parse_args(argv)
    gz, summ = build()
    if a.check:
        if OUT_ROWS.read_bytes() != gz or OUT_SUM.read_text(encoding="utf-8") != summ:
            raise SignedPanelError("the panel does not reproduce")
        print("reproduces byte for byte")
        return 0
    OUT_ROWS.write_bytes(gz)
    OUT_SUM.write_text(summ, encoding="utf-8", newline="\n")
    s = json.loads(summ)
    print(json.dumps({k: s[k] for k in ("rows", "sided_share_of_volume", "known_answer_vs_databento")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
