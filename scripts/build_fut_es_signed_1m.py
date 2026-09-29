"""D695 fixture: ES aggressor-signed volume per regular-session minute, 2016-01-04 -> 2023-12-29, from Sierra Chart's
tick files (the principal: "A, B and C, continuous ranking, 2016-2023 only").

    uv run python scripts/build_fut_es_signed_1m.py --data-root "<main checkout>/data"

Source: C:\\SierraChart\\Data\\ES{H,M,U,Z}{16..24}-CME.scid, one record per trade: SCDateTimeMS int64 (microseconds since
1899-12-30, UTC); Open/High/Low/Close float32; NumTrades, TotalVolume, BidVolume, AskVolume uint32
(check_sierra_aggressor.py's layout). AskVolume = buyer-initiated, BidVolume = seller-initiated.

For each session in `fut_index_sessions` (root ES), read ONLY that session's front contract (its `contract`), ONLY
between 09:30 and 16:00 ET, by a memory-mapped binary search on the timestamps (the check_sierra_aggressor slice rule:
bounded, inversions under 1 s tolerated). The minute label is the minute the trade falls in (the D462 convention: the
bar labelled 09:30 holds 09:30:00-09:30:59). Nothing on or after 2024-01-01 is decoded: every slice is bounded at the
session's 16:00, and the session list stops at 2023-12-29.

Output (gitignored, the data root's fixtures): fut_ES_signed_1m.csv.gz, one row per (day, hhmm): contract, trades,
volume, buy (AskVolume), sell (BidVolume); plus fut_ES_signed_1m.meta.json.

VALIDATION (declared before the build; written into the meta; D695 uses order flow only if it passes). Against the
Databento 1-minute bars (`fut_ES_rth_1m`, same contract), per minute:
  V1  the median ratio of Sierra volume to Databento volume lies in [0.98, 1.02]
  V2  the Pearson correlation of per-minute volume is >= 0.98
  V3  the share of Sierra volume carrying a side, (buy + sell) / volume, is >= 0.99
  V4  the minute's last trade equals the Databento minute close on >= 95 % of minutes
Databento's bars are stamped on ts_recv and Sierra on the exchange's time, so minute boundaries can differ by
milliseconds; exact agreement is not expected. The TRUE aggressor side cannot be checked for ES here: Databento's
side-flagged ES trades exist only in the sealed 2025-26 vault. The HO/RB check (Sierra against Databento truth, 2-minute
windows) gave r 0.88 and 80 % sign agreement.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SC_DATA = Path(r"C:\SierraChart\Data")
FIRST, CUTOFF = "2016-01-04", "2024-01-01"
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")
N_WORKERS = 8
MINUTES = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(390)]


class BuildError(RuntimeError):
    pass


def sierra_code(c: str, day: str) -> str:
    """ESH0 on a 2019/2020 session -> ESH20: the one-digit year resolved to the first year >= the session's year."""
    y = int(c[-1])
    sy = int(day[:4])
    year = next(yy for yy in range(sy, sy + 10) if yy % 10 == y)
    return f"{c[:-1]}{year % 100:02d}"


def _us(ts: pd.Timestamp) -> int:
    return int((ts.tz_convert("UTC") - ORIGIN) / pd.Timedelta(microseconds=1))


def slice_session(mm, dt_all, day: str) -> np.ndarray:
    lo_ts = pd.Timestamp(f"{day} 09:30", tz="America/New_York")
    hi_ts = pd.Timestamp(f"{day} 16:00", tz="America/New_York")
    if hi_ts.tz_convert("UTC") > pd.Timestamp(CUTOFF, tz="America/New_York").tz_convert("UTC"):
        raise BuildError(f"{day}: a slice would reach past the cutoff")
    lo_us, hi_us = _us(lo_ts), _us(hi_ts)
    lo = int(np.searchsorted(dt_all, lo_us, side="left"))
    hi = int(np.searchsorted(dt_all, hi_us, side="left"))
    rec = np.array(mm[lo:hi])
    d = rec["dt"]
    if len(d) and (int(d.min()) < lo_us or int(d.max()) >= hi_us or bool((np.diff(d) < -1_000_000).any())):
        raise BuildError(f"{day}: the decoded slice leaves its bounds or has an inversion of 1 s or more")
    return rec


def build_contract(args):
    contract, days = args
    path = SC_DATA / f"{contract}-CME.scid"
    with open(path, "rb") as fh:
        head = fh.read(12)
    if head[:4] != b"SCID":
        raise BuildError(f"{path.name}: not an SCID file")
    hdr, rs = int.from_bytes(head[4:8], "little"), int.from_bytes(head[8:12], "little")
    if rs != REC.itemsize:
        raise BuildError(f"{path.name}: record size {rs} != {REC.itemsize}")
    mm = np.memmap(path, dtype=REC, mode="r", offset=hdr)
    dt_all = mm["dt"]
    out = []
    for day in days:
        rec = slice_session(mm, dt_all, day)
        if len(rec) == 0:
            continue
        # integer minute buckets from 09:30 ET (the slice is bounded to [09:30, 16:00), so 0 .. 389)
        k = ((rec["dt"] - _us(pd.Timestamp(f"{day} 09:30", tz="America/New_York"))) // 60_000_000).astype(np.int64)
        if k.min() < 0 or k.max() > 389:
            raise BuildError(f"{contract} {day}: a trade falls outside 09:30-16:00")
        n = np.bincount(k, weights=rec["n"].astype(np.float64), minlength=390)
        v = np.bincount(k, weights=rec["v"].astype(np.float64), minlength=390)
        sell = np.bincount(k, weights=rec["bv"].astype(np.float64), minlength=390)
        buy = np.bincount(k, weights=rec["av"].astype(np.float64), minlength=390)
        lastpos = np.full(390, -1, dtype=np.int64)
        np.maximum.at(lastpos, k, np.arange(len(k)))
        live = v > 0
        mins = np.flatnonzero(live)
        out.append(pd.DataFrame({"day": day, "hhmm": [MINUTES[x] for x in mins], "contract": contract,
                                 "trades": n[live].astype(np.int64), "volume": v[live].astype(np.int64),
                                 "buy": buy[live].astype(np.int64), "sell": sell[live].astype(np.int64),
                                 "last": rec["c"][lastpos[live]].astype(np.float64)}))
    del dt_all, mm
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def main(data_root: Path) -> int:
    t0 = time.time()
    fx = data_root / "fixtures"
    sess = pd.read_csv(fx / "fut_index_sessions.csv.gz", usecols=["root", "day", "contract"], dtype=str, encoding="utf-8")
    sess = sess[(sess["root"] == "ES") & (sess["day"] >= FIRST) & (sess["day"] < CUTOFF)]
    if (sess["day"] >= CUTOFF).any():
        raise BuildError("a session on or after the cutoff reached the builder")
    sess = sess.assign(sc=[sierra_code(c, d) for c, d in zip(sess["contract"], sess["day"])])
    jobs = [(c, sorted(g["day"])) for c, g in sess.groupby("sc")]
    for c, _ in jobs:
        if not (SC_DATA / f"{c}-CME.scid").exists():
            raise BuildError(f"no Sierra file for {c}")
    print(f"  {len(sess)} sessions over {len(jobs)} contracts; decoding 09:30-16:00 ET of each front session", flush=True)
    parts = []
    with ProcessPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(build_contract, jb): jb[0] for jb in jobs}
        for f in as_completed(futs):
            parts.append(f.result())
            print(f"    {futs[f]} done ({len(parts)}/{len(jobs)}, {time.time() - t0:.0f} s)", flush=True)
    t = pd.concat(parts, ignore_index=True).sort_values(["day", "hhmm"]).reset_index(drop=True)
    if (t["day"] >= CUTOFF).any():
        raise BuildError("a row on or after the cutoff survived")
    print(f"  decoded {len(t):,} minutes in {time.time() - t0:.0f} s", flush=True)
    # ---- validation against the Databento 1-minute bars ----
    b = pd.read_csv(fx / "fut_ES_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "close", "volume"], dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")
    b = b[(b["day"] >= FIRST) & (b["day"] < CUTOFF)]
    b = b.assign(contract=[sierra_code(c, d) for c, d in zip(b["contract"], b["day"])])
    j = t.merge(b, on=["day", "hhmm", "contract"], how="inner")
    ratio = j["volume_x"] / j["volume_y"].where(j["volume_y"] > 0)
    val = {"minutes_sierra": int(len(t)), "minutes_databento": int(len(b)), "minutes_matched": int(len(j)),
           "V1_median_volume_ratio": float(ratio.median()), "V1_ratio_p10_p90": [float(ratio.quantile(0.1)), float(ratio.quantile(0.9))],
           "V2_volume_correlation": float(np.corrcoef(j["volume_x"], j["volume_y"])[0, 1]),
           "V3_signed_share": float((t["buy"] + t["sell"]).sum() / t["volume"].sum()),
           "V4_last_equals_close_share": float((np.abs(j["last"] - j["close"]) < 1e-6).mean()),
           "V4_within_one_tick_share": float((np.abs(j["last"] - j["close"]) <= 0.25 + 1e-9).mean())}
    val["pass"] = bool(0.98 <= val["V1_median_volume_ratio"] <= 1.02 and val["V2_volume_correlation"] >= 0.98 and val["V3_signed_share"] >= 0.99 and val["V4_last_equals_close_share"] >= 0.95)
    print("  VALIDATION: " + json.dumps(val), flush=True)
    t.drop(columns=["last"]).to_csv(fx / "fut_ES_signed_1m.csv.gz", index=False, compression="gzip", encoding="utf-8")
    meta = {"record": "D695", "builder": "scripts/build_fut_es_signed_1m.py", "source": str(SC_DATA), "sessions": int(sess["day"].nunique()),
            "span": [t["day"].min(), t["day"].max()], "cutoff": CUTOFF, "contracts": [c for c, _ in jobs], "validation": val,
            "columns": {"trades": "Sierra NumTrades", "volume": "TotalVolume", "buy": "AskVolume (buyer-initiated)", "sell": "BidVolume (seller-initiated)"},
            "built_seconds": round(time.time() - t0, 1)}
    (fx / "fut_ES_signed_1m.meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"  wrote {fx / 'fut_ES_signed_1m.csv.gz'} in {time.time() - t0:.0f} s; validation pass {val['pass']}", flush=True)
    return 0 if val["pass"] else 2


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(main(a.data_root))
