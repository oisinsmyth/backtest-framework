"""D771 Stage 0: the queue imbalance at the touch on gold's China-open fade. PHASE P only (amendment A1).
Spec: docs/decisions/D771-STAGE-0-PRE-REG-queue-imbalance-at-the-china-open.md (section 9, amendment A1).

    python scripts/stage0_d771_china_open_queue_imbalance.py --selftest     # SYSTEM interpreter (databento)
    python scripts/stage0_d771_china_open_queue_imbalance.py --premise

Phase P reads the book alone: the GC and MGC `bbo-1m` records of the PAID China window (read-only; never modified),
each file cut at 09:31 Beijing before any field is used. It reads no `tbbo`, none of D765's bars, no fade side, fill,
exit or P&L. I(t) = (bid size - ask size) / (bid size + ask size) at the touch. Every clock is a UTC nanosecond.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import stage0_d765_china_open as C  # noqa: E402
import stage0_d770_china_open_flow_passive as D  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D771-STAGE-0-PRE-REG-queue-imbalance-at-the-china-open.md"
OUT_P = REPO / "data" / "stage0_d771_china_open_queue_imbalance_premise.json"
MANIFEST = REPO / "data" / "china_window_tbbo_manifest.csv"
RAW_TICK = 10**8                # 0.1 in Databento's fixed 1e-9 prices: GC and MGC tick
QUOTE_STALE_NS = D.QUOTE_STALE_NS
SNAPS = [f"09:{m:02d}" for m in range(21, 31)]   # the ten snapshots of Q
MIN_SNAPS = 8
P_T_MIN = 3.0
WORKERS = 8
SAMPLE_AUDIT = 40


class D771Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D771Error(msg)


# ================================================================================ the book at a minute
def snap(q: np.ndarray, t: int) -> tuple[int, int, int, int, int, int] | None:
    """The latest bbo-1m record stamped at or before t, no older than 3 minutes, valid: finite prices, ask > bid, both
    sizes > 0. Returns raw (bid, ask, bid size, ask size, bid count, ask count) or None."""
    ts = q["ts_recv"].astype(np.int64)
    i = int(np.searchsorted(ts, t, side="right")) - 1
    if i < 0 or ts[i] < t - QUOTE_STALE_NS:
        return None
    b, a = int(q["bid_px_00"][i]), int(q["ask_px_00"][i])
    bs, as_ = int(q["bid_sz_00"][i]), int(q["ask_sz_00"][i])
    if b in (D.UNDEF, -D.UNDEF - 1) or a in (D.UNDEF, -D.UNDEF - 1) or b <= 0 or a <= b or bs <= 0 or as_ <= 0:
        return None
    return b, a, bs, as_, int(q["bid_ct_00"][i]), int(q["ask_ct_00"][i])


def imb(x: int, y: int) -> float:
    return (x - y) / (x + y) if x + y > 0 else float("nan")


def session_from_array(a: np.ndarray, day: str) -> dict[str, Any]:
    """Phase P's per-session quantities from a decoded bbo-1m array. The array is cut at 09:31 first."""
    t20, t31 = D.bj_ns(day, "09:20"), D.bj_ns(day, "09:31")
    need(bool((np.diff(a["ts_recv"].astype(np.int64)) >= 0).all()), f"the records are not in time order ({day})")
    a = a[a["ts_recv"].astype(np.int64) <= t31]
    need(bool((a["ts_recv"].astype(np.int64) <= t31).all()), f"cut: a record after 09:31 reached the reader ({day})")
    rec: dict[str, Any] = {"day": day}
    w = a[a["ts_recv"].astype(np.int64) >= t20]
    if len(np.unique(w["instrument_id"])) > 1:
        rec["why"] = "two_instruments"
        return rec
    s30, s31 = snap(a, D.bj_ns(day, "09:30")), snap(a, D.bj_ns(day, "09:31"))
    if s30 is None or s31 is None:
        rec["why"] = "no_quote"
        return rec
    rec["why"] = "used"
    rec["I30"] = imb(s30[2], s30[3])
    rec["Ict30"] = imb(s30[4], s30[5])
    rec["dm"] = ((s31[0] + s31[1]) - (s30[0] + s30[1])) / (2 * RAW_TICK)   # mid change in ticks (half-tick exact)
    rec["spread30"] = (s30[1] - s30[0]) / RAW_TICK
    rec["sz30"] = s30[2] + s30[3]
    vals = []
    for hm in SNAPS:
        s = snap(a, D.bj_ns(day, hm))
        vals.append(imb(s[2], s[3]) if s is not None else float("nan"))
    rec["I29"], rec["I21"] = vals[-2], vals[0]
    nv = int(np.isfinite(vals).sum())
    rec["nvalid"] = nv
    rec["Iavg"] = float(np.nanmean(vals)) if nv >= MIN_SNAPS else float("nan")
    return rec


def session_p(args: tuple[str, str]) -> dict[str, Any]:
    root, day = args
    a = D.read(root, "bbo-1m", day)
    if a is None:
        return {"day": day, "root": root, "why": "no_file"}
    rec = session_from_array(a, day)
    rec["root"] = root
    return rec


def _chunk(items: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return [session_p(it) for it in items]


def sessions(items: list[tuple[str, str]], workers: int = WORKERS) -> list[dict[str, Any]]:
    """Every session, fanned out over processes by stride; returned in input order."""
    if workers == 1:
        return _chunk(items)
    parts = [items[i::workers] for i in range(workers)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        outs = list(ex.map(_chunk, parts))
    res: list[dict[str, Any] | None] = [None] * len(items)
    for i, out in enumerate(outs):
        for j, r in enumerate(out):
            res[i + j * workers] = r
    need(all(r is not None for r in res), "fan-out: a session was lost")
    return res  # type: ignore[return-value]


# ================================================================================ the second implementation
def audit_session(a: np.ndarray, day: str, rec: dict[str, Any]) -> None:
    """Explicit loops over the raw records, never calling snap(): I(09:30), the 09:31 mid change and Q's mean."""
    def at(t: int) -> tuple[int, ...] | None:
        best = None
        for r in a:
            tr = int(r["ts_recv"])
            if tr <= t:
                best = r
            else:
                break
        if best is None or int(best["ts_recv"]) < t - QUOTE_STALE_NS:
            return None
        b, k = int(best["bid_px_00"]), int(best["ask_px_00"])
        bs, ks = int(best["bid_sz_00"]), int(best["ask_sz_00"])
        if b <= 0 or k <= b or bs <= 0 or ks <= 0 or b == D.UNDEF or k == D.UNDEF:
            return None
        return b, k, bs, ks
    t31 = D.bj_ns(day, "09:31")
    a = a[[k for k in range(len(a)) if int(a["ts_recv"][k]) <= t31]]
    s30, s31 = at(D.bj_ns(day, "09:30")), at(t31)
    need(s30 is not None and s31 is not None, f"lag audit: the second implementation finds no quote ({day})")
    i30 = (s30[2] - s30[3]) / (s30[2] + s30[3])
    dm = ((s31[0] + s31[1]) - (s30[0] + s30[1])) / (2 * RAW_TICK)
    vals = []
    for hm in SNAPS:
        s = at(D.bj_ns(day, hm))
        vals.append((s[2] - s[3]) / (s[2] + s[3]) if s is not None else float("nan"))
    nv = sum(1 for v in vals if v == v)
    avg = sum(v for v in vals if v == v) / nv if nv >= MIN_SNAPS else float("nan")
    need(i30 == rec["I30"], f"lag audit: I(09:30) differs ({day}: {i30} vs {rec['I30']})")
    need(dm == rec["dm"], f"lag audit: the 09:31 mid change differs ({day})")
    need(nv == rec["nvalid"], f"lag audit: the valid snapshot count differs ({day})")
    need((avg != avg and rec["Iavg"] != rec["Iavg"]) or abs(avg - rec["Iavg"]) < 1e-12,
         f"lag audit: Q's mean differs ({day})")


# ================================================================================ statistics
def tstat(rho: float, n: int) -> float:
    return float(math.sqrt(n - 2) * rho / math.sqrt(1 - rho * rho)) if n > 2 and abs(rho) < 1 else float("nan")


def corr(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    m = np.isfinite(a) & np.isfinite(b)
    rho = C.spearman(a[m], b[m])
    n = int(m.sum())
    return {"n": n, "rho": round(rho, 4), "t": round(tstat(rho, n), 2)}


def premise_stats(df: pd.DataFrame) -> dict[str, Any]:
    i30, dm = df["I30"].to_numpy(float), df["dm"].to_numpy(float)
    out: dict[str, Any] = {"P": corr(i30, dm)}
    mv = (dm != 0) & (i30 != 0)
    out["hit_rate"] = round(float((np.sign(i30[mv]) == np.sign(dm[mv])).mean()), 4)
    out["n_moved"] = int(mv.sum())
    out["share_no_mid_change"] = round(float((dm == 0).mean()), 4)
    lo, hi = np.quantile(i30, [1 / 3, 2 / 3])
    out["mean_dm_ticks_top_third"] = round(float(dm[i30 > hi].mean()), 4)
    out["mean_dm_ticks_bottom_third"] = round(float(dm[i30 < lo].mean()), 4)
    out["mean_dm_ticks_all"] = round(float(dm.mean()), 4)
    out["by_year"] = {y: corr(g["I30"].to_numpy(float), g["dm"].to_numpy(float))
                      for y, g in df.groupby(df["day"].str[:4])}
    edt = np.array([C.edt_by_zoneinfo(C.bj(d, "09:30")) for d in df["day"]])
    out["EDT"] = corr(i30[edt], dm[edt])
    out["EST"] = corr(i30[~edt], dm[~edt])
    out["order_counts"] = corr(df["Ict30"].to_numpy(float), dm)
    out["ten_snapshot_mean"] = corr(df["Iavg"].to_numpy(float), dm)
    out["persistence_I29_I30"] = corr(df["I29"].to_numpy(float), i30)
    out["persistence_I21_I30"] = corr(df["I21"].to_numpy(float), i30)
    out["spread30_ticks_mean_median"] = [round(float(df["spread30"].mean()), 3), float(df["spread30"].median())]
    out["touch_size30_median"] = float(df["sz30"].median())
    return out


# ================================================================================ the sample
def days_of(root: str) -> list[str]:
    hol = C.load_holidays()
    out = []
    with open(MANIFEST, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["schema"] != "bbo-1m" or not r["path"].startswith(f"{root}_bbo-1m/"):
                continue
            d = r["day"]
            if d < "2024-01-01" and dt.date.fromisoformat(d).weekday() < 5 and d not in hol:
                out.append(d)
    return sorted(set(out))


def run_root(root: str) -> tuple[pd.DataFrame, dict[str, int]]:
    days = days_of(root)
    recs = sessions([(root, d) for d in days])
    counts = {"read": len(recs)}
    for r in recs:
        counts[r["why"]] = counts.get(r["why"], 0) + 1
    need(counts["read"] == sum(v for k, v in counts.items() if k != "read"), "right quantity: read != used + exclusions")
    df = pd.DataFrame([r for r in recs if r["why"] == "used"])
    return df, counts


def premise() -> int:
    t0 = time.time()
    out: dict[str, Any] = {"spec": SPEC.name, "phase": "P (amendment A1): the book alone, cut at 09:31 Beijing"}
    frames = {}
    for root in ("GC", "MGC"):
        df, counts = run_root(root)
        frames[root] = df
        need(not df["I30"].equals(df["I29"]), "right quantity: I(09:30) equals I(09:29)")
        need(not df["I30"].equals(df["Ict30"]), "right quantity: the size imbalance equals the count imbalance")
        rng = np.random.default_rng(771)
        for i in sorted(rng.choice(len(df), size=min(SAMPLE_AUDIT, len(df)), replace=False)):
            day = df["day"].iloc[i]
            audit_session(D.read(root, "bbo-1m", day), day, df.iloc[i].to_dict())
        out[root] = {"counts": counts, **premise_stats(df)}
        print(root, json.dumps(out[root]["counts"]), json.dumps(out[root]["P"]), flush=True)
    g, m = frames["GC"], frames["MGC"]
    j = g.merge(m, on="day", suffixes=("_gc", "_mgc"))
    out["GC_vs_MGC_I30"] = corr(j["I30_gc"].to_numpy(float), j["I30_mgc"].to_numpy(float))
    p = out["GC"]["P"]
    out["P_holds"] = bool(p["rho"] > 0 and p["t"] >= P_T_MIN)
    out["reading"] = "P HOLDS" if out["P_holds"] else "PREMISE FAILS"
    out["wall_s"] = round(time.time() - t0, 1)
    OUT_P.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(out["reading"], f"{out['wall_s']}s ->", OUT_P.relative_to(REPO))
    return 0


# ================================================================================ self-test
def _rec_array(rows: list[tuple[int, int, int, int, int, int, int, int]]) -> np.ndarray:
    dtp = [("ts_recv", "u8"), ("bid_px_00", "i8"), ("ask_px_00", "i8"), ("bid_sz_00", "u4"), ("ask_sz_00", "u4"),
           ("bid_ct_00", "u4"), ("ask_ct_00", "u4"), ("instrument_id", "u4")]
    return np.array(rows, dtype=dtp)


def _synthetic(day: str, i_sign: int, up: int) -> np.ndarray:
    """Ten minutes of a book leaning to the bid (i_sign +1) or the ask (-1), then a mid move of `up` ticks at 09:31."""
    rows = []
    for m in range(20, 32):
        t = D.bj_ns(day, f"09:{m:02d}")
        b = 2000 * 10**9 + (up * RAW_TICK if m == 31 else 0)
        bs, ks = (30, 10) if i_sign > 0 else (10, 30)
        rows.append((t, b, b + RAW_TICK, bs, ks, 5, 3, 1))
    return _rec_array(rows)


def sign_audit(mirror: int = 1) -> None:
    """In money: a bid-heavy book followed by a rise is a positive P contribution; an ask-heavy book followed by a
    fall too. A mirrored reader (sizes swapped) must raise."""
    day = "2019-03-12"
    for i_sign, up in ((1, 1), (-1, -1)):
        a = _synthetic(day, i_sign, up)
        if mirror < 0:
            a["bid_sz_00"], a["ask_sz_00"] = a["ask_sz_00"].copy(), a["bid_sz_00"].copy()
        r = session_from_array(a, day)
        need(r["I30"] * r["dm"] > 0, f"sign audit: a {'bid' if i_sign > 0 else 'ask'}-heavy book before a "
             f"{'rise' if up > 0 else 'fall'} gives I*dm = {r['I30'] * r['dm']}")


def selftest() -> int:
    day = "2019-03-12"
    # the imbalance on hand-built records, including a zero side (invalid) and a stale quote (refused)
    a = _synthetic(day, 1, 1)
    r = session_from_array(a, day)
    need(r["I30"] == 0.5 and r["dm"] == 1.0 and r["Ict30"] == 0.25 and r["nvalid"] == 10, f"imbalance: {r}")
    z = a.copy()
    z["ask_sz_00"][z["ts_recv"] == D.bj_ns(day, "09:30")] = 0
    need(snap(z, D.bj_ns(day, "09:30")) is None, "a zero ask size must be invalid")
    st = a[a["ts_recv"].astype(np.int64) <= D.bj_ns(day, "09:25")]
    need(snap(st, D.bj_ns(day, "09:30")) is None, "a 5-minute-old quote must be refused")
    need(snap(st, D.bj_ns(day, "09:27")) is not None, "a 2-minute-old quote must be accepted")
    # a record after 09:31 never reaches the statistics: a wild 09:32 quote changes nothing
    late = _rec_array(list(a.tolist()) + [(D.bj_ns(day, "09:32"), 1, 10**12, 1, 999, 1, 1, 2)])
    need(session_from_array(late, day) == r, "cut: a 09:32 record changed phase P's quantities")
    # two instruments in the window are dropped
    two = a.copy()
    two["instrument_id"][3] = 2
    need(session_from_array(two, day)["why"] == "two_instruments", "two instruments must be dropped")
    # the sign audit passes, and raises on a mirrored reader
    sign_audit(1)
    try:
        sign_audit(-1)
    except D771Error:
        pass
    else:
        raise D771Error("the sign audit did not raise on a mirrored reader")
    # the second implementation agrees on the synthetic, and raises on a broken size
    audit_session(a, day, r)
    broken = dict(r)
    broken["I30"] = 0.4
    try:
        audit_session(a, day, broken)
    except D771Error:
        pass
    else:
        raise D771Error("the second implementation did not raise on a broken I(09:30)")
    # a real paid session parses, and chunk == whole on processes
    days = days_of("GC")
    probe = [("GC", d) for d in days[::max(1, len(days) // 40)][:40]]
    whole = sessions(probe, workers=1)
    chunk = sessions(probe, workers=4)
    need(json.dumps(whole, sort_keys=True, default=str) == json.dumps(chunk, sort_keys=True, default=str),
         "chunk != whole")
    used = [w for w in whole if w["why"] == "used"]
    need(len(used) >= 30, f"too few real sessions parse: {len(used)}")
    for w in used[:5]:
        audit_session(D.read("GC", "bbo-1m", w["day"]), w["day"], w)
    print("selftest OK:", len(used), "of", len(probe), "real GC sessions used; I30 sample",
          [round(w["I30"], 3) for w in used[:5]])
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--premise", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else premise()


if __name__ == "__main__":
    sys.exit(main())
