"""The opening model's A7 (large-lot signed flow, s.4; OA-A3; D645 s.2) from Sierra Chart's ES/NQ tick files.

    python scripts/build_opening_a7.py --selftest
    python scripts/build_opening_a7.py --build [--data-root DIR]     # -> data/opening/a7.csv + a7.meta.json

Per (market, session), on the session's D462 front contract, over RTH trades (09:30 -> 16:00 ET):
- every trade is one Sierra record (NumTrades = 1 on ES, measured 2026-09-28) carrying the exchange's aggressor side:
  AskVolume = buyer-initiated, BidVolume = seller-initiated;
- the large-lot threshold is the 90th percentile of trade size over the PRIOR 20 sessions' RTH trades (deposit test
  10). It is computed from per-session size histograms and equals `agents.large_lot_threshold` on the raw sizes
  exactly (--selftest proves it). A trade is large when its size is AT OR ABOVE the threshold;
- for each checkpoint t: the total volume 09:30 -> t, the large-lot signed volume (buys minus sells), and
  a7_t = large-lot signed volume / total volume. The model's feature is a7_t x d0 (D645 s.2).
Sessions 2015-11-02 -> 2025-02-28: a 20-session warm-up, then the in-sample. A contract file that runs into the vault
(the H25s) is sliced by in-sample session bounds only, so no vault trade is parsed (A10). Files are read through a
memory map, so NTFS compression (OA-A3) is transparent.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.opening.agents import large_lot_threshold  # noqa: E402

SC_DATA = Path(r"C:\SierraChart\Data")
OUT = REPO / "data" / "opening" / "a7.csv"
META = REPO / "data" / "opening" / "a7.meta.json"
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
HDR = 56
ROOTS = ("ES", "NQ")
FIRST, RESERVED_FROM = "2015-11-02", "2025-03-01"
CHECKPOINTS = ("09:45", "10:00", "10:30", "11:00")
SIZE_CAP = 512
Q, N_PRIOR = 0.90, 20
EPOCH = pd.Timestamp("1899-12-30")
LETTER = "FGHJKMNQUVXZ"


def to_us(ts: pd.Timestamp) -> int:
    return int((ts.tz_convert("UTC").tz_localize(None) - EPOCH) / pd.Timedelta(microseconds=1))


def sierra_symbol(d462_contract: str, day: str) -> str:
    """D462 writes one-digit years (ESH6); Sierra two (ESH16). The decade is the one that puts the expiry within a
    year after the session."""
    root, letter, digit = d462_contract[:2], d462_contract[2], int(d462_contract[3:])
    y = int(day[:4])
    for yy in (y, y + 1):
        if yy % 10 == digit:
            return f"{root}{letter}{yy % 100:02d}"
    raise ValueError(f"cannot place {d462_contract} on {day}")


def hist_quantile(hist: np.ndarray, q: float) -> float:
    """np.quantile(sizes, q) (linear interpolation) from a size histogram (index = size)."""
    n = int(hist.sum())
    if n == 0:
        return float("nan")
    cum = np.cumsum(hist)
    h = (n - 1) * q
    lo = int(np.floor(h))

    def kth(k: int) -> int:  # the k-th smallest size (0-based)
        return int(np.searchsorted(cum, k + 1))

    a = kth(lo)
    b = kth(min(lo + 1, n - 1))
    return float(a + (h - lo) * (b - a))


def session_rows(m: np.ndarray, day: str) -> dict:
    """One session's RTH trades from a contract's memory-mapped records."""
    t0 = pd.Timestamp(f"{day} 09:30", tz="America/New_York")
    t1 = pd.Timestamp(f"{day} 16:00", tz="America/New_York")
    a, b = to_us(t0), to_us(t1)
    i0 = max(int(np.searchsorted(m["dt"], a)) - 5000, 0)  # a margin for rare timestamp inversions
    i1 = min(int(np.searchsorted(m["dt"], b)) + 5000, len(m))
    r = np.asarray(m[i0:i1])
    keep = (r["dt"] >= a) & (r["dt"] < b)
    r = r[keep]
    mins = ((r["dt"] - a) // 60_000_000).astype(int)  # minutes after 09:30
    size = r["v"].astype(np.int64)
    signed = r["av"].astype(np.int64) - r["bv"].astype(np.int64)
    cs = np.minimum(size, SIZE_CAP)
    out = {"n": int(len(r)), "hist": np.bincount(cs, minlength=SIZE_CAP + 1), "side_share":
           float((r["av"].astype(np.int64) + r["bv"]).sum() / max(size.sum(), 1))}
    for t in CHECKPOINTS:
        w = mins < (int(t[:2]) * 60 + int(t[3:]) - (9 * 60 + 30))
        out[f"vol_{t}"] = int(size[w].sum())
        out[f"sbs_{t}"] = np.bincount(cs[w], weights=signed[w], minlength=SIZE_CAP + 1)  # signed volume by size
    return out


def finished_contracts() -> set[str]:
    """Contracts the Sierra downloader has recorded as complete and compressed: a --trial never opens a file Sierra
    may still be writing."""
    rec = json.loads((REPO / "data" / "opening" / "sierra_index_tick_record.json").read_text(encoding="utf-8"))
    return {k for k, v in rec["contracts"].items() if v.get("compressed") and v.get("cut_short") is False}


def build(data_root: Path, only: set[str] | None = None) -> pd.DataFrame:
    ses = pd.read_csv(data_root / "fixtures" / "fut_index_sessions.csv.gz", encoding="utf-8", dtype={"day": str})
    ses = ses[ses["root"].isin(ROOTS) & (ses["day"] >= FIRST) & (ses["day"] < RESERVED_FROM)]
    rows, meta = [], {"contracts": {}}
    for r in ROOTS:
        s = ses[ses["root"] == r].sort_values("day")
        s = s.assign(sym=[sierra_symbol(c, d) for c, d in zip(s["contract"], s["day"])])
        per = {}
        for sym, g in s.groupby("sym", sort=False):
            p = SC_DATA / f"{sym}-CME.scid"
            if only is not None and sym not in only:
                meta["contracts"][sym] = "NOT IN TRIAL"
                continue
            if not p.exists():
                meta["contracts"][sym] = "MISSING"
                continue
            m = np.memmap(p, dtype=REC, mode="r", offset=HDR)
            t = time.time()
            for day in g["day"]:
                per[day] = session_rows(m, day)
            meta["contracts"][sym] = {"sessions": int(len(g)), "secs": round(time.time() - t, 1)}
            del m
        days = [d for d in s["day"] if d in per]
        hists = [per[d]["hist"] for d in days]
        for i, d in enumerate(days):
            x = per[d]
            thr = hist_quantile(np.sum(hists[i - N_PRIOR:i], axis=0), Q) if i >= N_PRIOR else float("nan")
            row = {"root": r, "session": d, "n_trades": x["n"], "side_share": x["side_share"], "thr": thr}
            for t in CHECKPOINTS:
                sbs = x[f"sbs_{t}"]
                k = int(np.ceil(thr)) if np.isfinite(thr) else None
                ls = float(sbs[k:].sum()) if k is not None else float("nan")
                row[f"vol_{t}"] = x[f"vol_{t}"]
                row[f"lsigned_{t}"] = ls
                row[f"a7_{t}"] = ls / x[f"vol_{t}"] if x[f"vol_{t}"] > 0 else float("nan")
            rows.append(row)
    res = pd.DataFrame(rows)
    if (res["session"] >= RESERVED_FROM).any():
        raise SystemExit("a vault session reached A7")
    if only is None:
        META.write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return res


def selftest() -> int:
    rng = np.random.default_rng(10)
    sizes = [rng.geometric(0.4, rng.integers(50, 400)).astype(float) for _ in range(30)]
    ref = large_lot_threshold(sizes)
    hists = [np.bincount(np.minimum(s.astype(int), SIZE_CAP), minlength=SIZE_CAP + 1) for s in sizes]
    mine = [hist_quantile(np.sum(hists[i - N_PRIOR:i], axis=0), Q) if i >= N_PRIOR else float("nan")
            for i in range(len(sizes))]
    assert np.allclose(ref[N_PRIOR:], mine[N_PRIOR:], rtol=0, atol=1e-12), (ref[N_PRIOR:], mine[N_PRIOR:])
    assert sierra_symbol("ESH6", "2015-12-20") == "ESH16" and sierra_symbol("ESZ9", "2019-10-01") == "ESZ19"
    assert sierra_symbol("NQH0", "2019-12-15") == "NQH20"
    print("selftest: the histogram threshold equals agents.large_lot_threshold exactly; symbols map")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--trial", action="store_true", help="only the contracts the downloader has finished; writes to "
                    "temp/ (a runtime projection and a check on real files before the full build)")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.build or a.trial:
        t = time.time()
        res = build(a.data_root, finished_contracts() if a.trial else None)
        out = REPO / "temp" / "a7_trial.csv" if a.trial else OUT
        out.parent.mkdir(parents=True, exist_ok=True)
        res.to_csv(out, index=False, encoding="utf-8", lineterminator="\n", float_format="%.8g")
        print(f"wrote {out}: {len(res):,} rows in {(time.time() - t) / 60:.1f} min")
        print(res.groupby("root")[["n_trades", "side_share", "thr", "a7_10:00"]].describe().T.round(4).to_string())
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
