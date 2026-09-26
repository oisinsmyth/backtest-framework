"""Aggressor-signed volume per NG contract and session from 13:30 ET to each decision time τ, and the placebo's
10:52 → 11:30, from Sierra Chart's 1-tick files: Stage B's measurement z (settlement ledger deposit §5.2; AITODO
2026-09-26).

It builds a panel and computes no statistic: no regression, no Q, no price.

SPANS, ET, half-open [from, to), by record time:
  pre_1350 13:30–13:50 · pre_1400 13:30–14:00 · pre_1410 13:30–14:10 · (for the identity) mid_1428 14:10–14:28 ·
  plcpre_1130 10:52–11:30 (the placebo's pre-window, 58 minutes before 11:50, as the 13:30 start is 58 before 14:28).
Per span: `v_`, `net_` (Ask − Bid, + = buyers), `sided_`, `n_`.

It IMPORTS the frozen builder's record layout and vault guards (`build_signed_window_panel`: REC, ORIGIN, CUT_US,
FROM_US, the symbol list), and does not edit it: that file is frozen with Stage A (amendment A10). The vault is never
decoded: the same binary search on the timestamps, with the same assertions.

KNOWN ANSWER (raises): per (contract, day), pre_1410 + mid_1428 equals the frozen panel's `pre` (13:30–14:28) exactly,
in volume and in net, on every row of both.

Output: `data/ledger_signed_pretau_daily.csv.gz` (gitignored by suffix) and `data/ledger_signed_pretau_summary.json`.

    uv run python scripts/build_signed_pre_tau_panel.py [--check]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_signed_window_panel as B  # noqa: E402  (frozen: imported, never edited)

OUT_ROWS = REPO / "data" / "ledger_signed_pretau_daily.csv.gz"
OUT_SUM = REPO / "data" / "ledger_signed_pretau_summary.json"
SPANS = {"pre_1350": ("13:30:00", "13:50:00"), "pre_1400": ("13:30:00", "14:00:00"),
         "pre_1410": ("13:30:00", "14:10:00"), "mid_1428": ("14:10:00", "14:28:00"),
         "plcpre_1130": ("10:52:00", "11:30:00")}


class PreTauError(RuntimeError):
    pass


def one(sym: str) -> tuple[str, pd.DataFrame]:
    path = B.SC_DATA / f"{sym}-NYMEX.scid"
    with open(path, "rb") as fh:
        head = fh.read(12)
    hdr = int.from_bytes(head[4:8], "little")
    if head[:4] != b"SCID" or int.from_bytes(head[8:12], "little") != B.REC.itemsize:
        raise PreTauError(f"{sym}: not a 40-byte-record SCID file")
    mm = np.memmap(path, dtype=B.REC, mode="r", offset=hdr)
    dt_all = mm["dt"]
    cut = int(np.searchsorted(dt_all, B.CUT_US, side="left"))
    lo = int(np.searchsorted(dt_all[:cut], B.FROM_US, side="left"))
    dt = np.array(dt_all[lo:cut])
    if len(dt) and (dt.max() >= B.CUT_US or (np.diff(dt) < -1_000_000).any()):
        raise PreTauError(f"{sym}: the decoded prefix reaches the cut or has an inversion of 1 s or more")
    if cut < len(dt_all) and int(np.min(dt_all[cut:cut + 100])) < B.CUT_US:
        raise PreTauError(f"{sym}: a record after the cut index is before the cut")
    if not len(dt):
        return sym, pd.DataFrame()
    tod_utc = (dt % 86_400_000_000) // 1_000_000
    keep = (tod_utc >= 14 * 3600) & (tod_utc < 20 * 3600)  # ET 10:52-14:28 lies inside UTC 14:00-20:00
    sub = mm[lo:cut][keep]
    et = (B.ORIGIN + pd.to_timedelta(np.asarray(sub["dt"]), unit="us")).tz_convert(B.ET)
    wall = np.asarray(et.tz_localize(None).as_unit("ns").asi8)
    day_ns = 86_400 * 10**9
    tod, day = (wall % day_ns) // 10**9, wall // day_ns
    frames = []
    for span, (a, b) in SPANS.items():
        m = (tod >= B._sec(a)) & (tod < B._sec(b))
        if not m.any():
            continue
        av = np.asarray(sub["av"][m], dtype=np.int64)
        bv = np.asarray(sub["bv"][m], dtype=np.int64)
        g = pd.DataFrame({"day": day[m], "v": np.asarray(sub["v"][m], dtype=np.int64), "net": av - bv,
                          "sided": av + bv, "n": 1}).groupby("day").sum()
        frames.append(g.add_suffix(f"_{span}"))
    if not frames:
        return sym, pd.DataFrame()
    out = pd.concat(frames, axis=1).fillna(0).astype("int64").reset_index()
    out["day"] = pd.to_datetime(out["day"], unit="D").dt.strftime("%Y-%m-%d")
    out.insert(0, "symbol", sym)
    return sym, out


def build() -> tuple[bytes, str]:
    syms = [s for s in B.symbols() if s.startswith("NG")]
    with cf.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as ex:
        res = dict(ex.map(one, syms))
    df = pd.concat([res[s] for s in syms if len(res[s])], ignore_index=True)
    df.insert(0, "root", "NG")
    df.insert(3, "ym", df["symbol"].map(B.ym_of))
    df.insert(4, "sample", np.where(df["day"] < B.FIRST_IN, "pre", "in"))
    cols = ["root", "symbol", "day", "ym", "sample"] + [f"{k}_{s}" for s in SPANS for k in ("v", "net", "sided", "n")]
    for c in cols[5:]:
        if c not in df:
            df[c] = 0
    df[cols[5:]] = df[cols[5:]].fillna(0).astype("int64")
    df = df[cols].sort_values(["day", "symbol"]).reset_index(drop=True)
    if (df["day"] >= B.CUT).any():
        raise PreTauError("a row on or after the cut survived")
    # the known answer: 13:30-14:10 + 14:10-14:28 = the frozen panel's 13:30-14:28, in volume and in net
    fz = pd.read_csv(B.OUT_ROWS, encoding="utf-8", usecols=["root", "symbol", "day", "v_pre", "net_pre"])
    fz = fz[fz["root"] == "NG"].set_index(["symbol", "day"])
    mine = df.set_index(["symbol", "day"])
    j = fz.join(mine[["v_pre_1410", "v_mid_1428", "net_pre_1410", "net_mid_1428"]], how="outer").fillna(0)
    bad_v = int((j["v_pre"] != j["v_pre_1410"] + j["v_mid_1428"]).sum())
    bad_n = int((j["net_pre"] != j["net_pre_1410"] + j["net_mid_1428"]).sum())
    if bad_v or bad_n:
        raise PreTauError(f"the identity with the frozen panel fails: {bad_v} volume and {bad_n} net mismatches")
    summ: dict[str, Any] = {"spans_et": SPANS, "cut": B.CUT, "rows": int(len(df)),
                            "rows_by_sample": {k: int(v) for k, v in df["sample"].value_counts().items()},
                            "known_answer": {"pairs": int(len(j)), "volume_mismatches": bad_v, "net_mismatches": bad_n}}
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", encoding="utf-8")
    return gzip.compress(buf.getvalue().encode("utf-8"), mtime=0), json.dumps(summ, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    gz, summ = build()
    if a.check:
        if OUT_ROWS.read_bytes() != gz or OUT_SUM.read_text(encoding="utf-8") != summ:
            raise PreTauError("the panel does not reproduce")
        print("reproduces byte for byte")
        return 0
    OUT_ROWS.write_bytes(gz)
    OUT_SUM.write_text(summ, encoding="utf-8", newline="\n")
    print(summ)
    return 0


if __name__ == "__main__":
    sys.exit(main())
