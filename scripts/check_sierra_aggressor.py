"""Known-answer check: does Sierra Chart's historical tick data carry the true aggressor side? (2026-09-26)

If it does, Sierra Chart's historical data service, from $26 a month, holds the aggressor-signed flow
that the settlement ledger's deposit H1 needs (AITODO G1, D624). This check must pass before any signed-flow
pre-registration relies on it.

THE TRUTH: Databento `trades` for HO (the free sibling pull, `data/ledger_sibling_pull_jobs.json`, label
siblings-trades), with its side flag: B = buyer aggressor, A = seller aggressor, N = none. Size is cast to int64
(D624). The sibling year is SEEN data. It is used here only as a data-quality reference, never as a test sample. HO
is not CL or NG, so no ledger vault byte is touched.

SIERRA: `C:\\SierraChart\\Data\\HO*-NYMEX.scid`, downloaded as 1-tick records. The documented record layout is:
SCDateTimeMS int64 (microseconds since 1899-12-30, UTC); Open, High, Low, Close float32; NumTrades, TotalVolume,
BidVolume, AskVolume uint32. Sierra Chart assigns BidVolume/AskVolume from the exchange's aggressor field:
AskVolume = buyer-initiated, BidVolume = seller-initiated.

PER (contract, ET date), over 14:28:00–14:30:00 ET:
    net_sierra = Σ AskVolume − Σ BidVolume;  net_truth = Σ size[B] − Σ size[A]
The truth is computed on Databento's ts_recv (D624's clock) and on ts_event (the exchange's).
REPORTED: sessions compared; Pearson r of the nets; the share of sessions whose nets match exactly and within 1%
of gross; sign agreement; the Sierra/truth total-volume ratio; and, over whole sessions, the share of Sierra tick
volume carrying a side.
PASS (declared before the first run): r ≥ 0.99, sign agreement ≥ 0.98, and the median total ratio within
[0.99, 1.01], on ≥ 50 sessions.

    python scripts/check_sierra_aggressor.py      # SYSTEM interpreter (databento)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SC_DATA = Path(r"C:\SierraChart\Data")
RAW = REPO / "data" / "raw" / "databento"
JOBS = REPO / "data" / "ledger_sibling_pull_jobs.json"
OUT = REPO / "data" / "sierra_aggressor_check.json"
ET = "America/New_York"
W0, W1 = "14:28:00", "14:30:00"
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
MIN_GROSS = 20
LAST_DAY_EXCL = "2026-09-19"  # the sibling year ends 2026-09-18; D626's HO sessions (from 09-21) stay unread


class CheckError(RuntimeError):
    pass


def read_scid(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    if raw[:4] != b"SCID":
        raise CheckError(f"{path.name}: not an SCID file")
    hdr = int.from_bytes(raw[4:8], "little")
    rs = int.from_bytes(raw[8:12], "little")
    if rs != REC.itemsize:
        raise CheckError(f"{path.name}: record size {rs} != {REC.itemsize}")
    r = np.frombuffer(raw[hdr:], REC)
    t = pd.to_datetime(r["dt"], unit="us", origin=pd.Timestamp("1899-12-30")).tz_localize("UTC").tz_convert(ET)
    return pd.DataFrame({"et": t, "n": r["n"].astype("int64"), "v": r["v"].astype("int64"),
                         "bv": r["bv"].astype("int64"), "av": r["av"].astype("int64")})


def sierra_windows(contracts: list[str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    meta: dict[str, dict[str, Any]] = {}
    for c in contracts:
        df = read_scid(SC_DATA / f"{c}-NYMEX.scid")
        # D626 reads HO and RB sessions from 2026-09-21 ONCE, on 2026-10-10: no HO row after the sibling year may be read
        df = df[df["et"] < pd.Timestamp(LAST_DAY_EXCL, tz=ET)]
        if (df["et"] >= pd.Timestamp(LAST_DAY_EXCL, tz=ET)).any():
            raise CheckError("a row after 2026-09-18 survived the guard")
        if df.empty:
            meta[c] = {"records": 0}
            continue
        clock = df["et"].dt.strftime("%H:%M:%S")
        meta[c] = {"records": int(len(df)), "first": str(df["et"].min()), "last": str(df["et"].max()),
                   "share_records_one_trade": round(float((df["n"] == 1).mean()), 4),
                   "share_volume_with_side": round(float((df["bv"] + df["av"]).sum() / df["v"].sum()), 6)}
        w = df[(clock >= W0) & (clock < W1)]
        g = w.groupby(w["et"].dt.strftime("%Y-%m-%d")).agg(v=("v", "sum"), bv=("bv", "sum"), av=("av", "sum"))
        for day, x in g.iterrows():
            rows.append({"contract": c, "day": day, "sc_total": int(x["v"]), "sc_net": int(x["av"] - x["bv"])})
    return pd.DataFrame(rows), meta


def truth_windows(contracts: list[str]) -> pd.DataFrame:
    import databento as db  # type: ignore[import-not-found]
    rec = json.loads(JOBS.read_text(encoding="utf-8"))
    job = next(j for j in rec["jobs"] if j["label"] == "siblings-trades")
    files = sorted((RAW / job["job"]["id"]).glob("*.dbn.zst"))
    cache = REPO / "temp" / "sierra_check_truth_windows.csv.gz"
    key = ";".join(f"{f.name}:{f.stat().st_size}" for f in files) + "|" + ",".join(contracts)
    if cache.exists() and cache.with_suffix(".key").exists() and cache.with_suffix(".key").read_text(encoding="utf-8") == key:
        return pd.read_csv(cache, encoding="utf-8")
    # Databento writes one-digit years (HOK6); Sierra Chart two (HOK26)
    to_sc = {c[:3] + c[-1]: c for c in contracts}
    want = set(to_sc)
    parts = []
    for f in files:
        for chunk in db.DBNStore.from_file(f).to_df(map_symbols=True, count=2_000_000):
            chunk = chunk[chunk["symbol"].astype(str).isin(want)]
            if chunk.empty:
                continue
            for clock_col in ("ts_recv", "ts_event"):
                ts = chunk[clock_col] if clock_col in chunk.columns else chunk.index.to_series()
                et = pd.DatetimeIndex(ts).tz_convert(ET)
                clock = et.strftime("%H:%M:%S")
                keep = (clock >= W0) & (clock < W1)
                if not keep.any():
                    continue
                c = chunk.loc[keep]
                parts.append(pd.DataFrame({"clock": clock_col,
                                           "contract": c["symbol"].astype(str).map(to_sc).to_numpy(),
                                           "day": et[keep].strftime("%Y-%m-%d"), "side": c["side"].astype(str).to_numpy(),
                                           "size": c["size"].astype("int64").to_numpy()}))
    if not parts:
        raise CheckError(f"no Databento window trades for {sorted(want)}")
    t = pd.concat(parts)
    t["signed"] = np.where(t["side"] == "B", t["size"], np.where(t["side"] == "A", -t["size"], 0))
    out = t.groupby(["clock", "contract", "day"]).agg(tr_total=("size", "sum"), tr_net=("signed", "sum")).reset_index()
    cache.parent.mkdir(exist_ok=True)
    out.to_csv(cache, index=False, encoding="utf-8")
    cache.with_suffix(".key").write_text(key, encoding="utf-8", newline="\n")
    return out


def compare(sc: pd.DataFrame, tr: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for clock, g in tr.groupby("clock"):
        m = sc.merge(g, on=["contract", "day"], how="inner")
        m = m[m["tr_total"] >= MIN_GROSS]
        if len(m) < 3:
            out[clock] = {"sessions": int(len(m))}
            continue
        ratio = m["sc_total"] / m["tr_total"]
        out[clock] = {
            "sessions": int(len(m)),
            "r_net": round(float(np.corrcoef(m["sc_net"], m["tr_net"])[0, 1]), 4),
            "exact_net_share": round(float((m["sc_net"] == m["tr_net"]).mean()), 4),
            "within_1pct_gross_share": round(float(((m["sc_net"] - m["tr_net"]).abs() <= 0.01 * m["tr_total"]).mean()), 4),
            "sign_agreement": round(float((np.sign(m["sc_net"]) == np.sign(m["tr_net"])).mean()), 4),
            "total_ratio_median": round(float(ratio.median()), 4),
            "total_ratio_p10_p90": [round(float(ratio.quantile(0.1)), 4), round(float(ratio.quantile(0.9)), 4)],
            "worst": m.assign(err=(m["sc_net"] - m["tr_net"]).abs()).sort_values("err").tail(3)[
                ["contract", "day", "sc_total", "tr_total", "sc_net", "tr_net"]].to_dict("records"),
        }
        out[clock]["pass"] = bool(out[clock]["sessions"] >= 50 and out[clock]["r_net"] >= 0.99
                                  and out[clock]["sign_agreement"] >= 0.98
                                  and 0.99 <= out[clock]["total_ratio_median"] <= 1.01)
        # the principal's usability bar for a signed-flow stand-in (AITODO item 5, decided 2026-09-24): r >= 0.8
        out[clock]["usable_r_ge_0.8"] = bool(out[clock]["sessions"] >= 50 and out[clock]["r_net"] >= 0.8)
    return out


def main(argv: list[str] | None = None) -> int:
    root = (argv or sys.argv[1:] or ["HO"])[0]
    if root not in ("HO", "RB"):
        raise CheckError(f"root {root!r}: only the sibling roots HO and RB are checked (CL/NG truth is vault or D626)")
    contracts = sorted(p.name.split("-")[0] for p in SC_DATA.glob(f"{root}???-NYMEX.scid") if p.stat().st_size > 56)
    if not contracts or not all(re.fullmatch(rf"{root}[FGHJKMNQUVXZ]\d\d", c) for c in contracts):
        raise CheckError(f"unexpected contract list {contracts}")
    sc, meta = sierra_windows(contracts)
    tr = truth_windows(contracts)
    res = {"root": root, "contracts": contracts, "sierra_files": meta, "window_et": [W0, W1], "min_gross": MIN_GROSS,
           "comparison": compare(sc, tr)}
    out = OUT.with_name(f"sierra_aggressor_check_{root.lower()}.json")
    out.write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, indent=1, default=str)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
