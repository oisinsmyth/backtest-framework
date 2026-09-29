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

CL AND NG (D629 §6, added 2026-09-29, the principal's rulings): after D626's one read, the same comparison on CL and
NG, run once on the sessions D626 reads (2026-09-21 -> 2026-10-09):
    python scripts/check_sierra_aggressor.py --root NG --run      # refuses before 2026-10-11 and before D626's marker
    python scripts/check_sierra_aggressor.py --root NG --check    # reproduces the written file byte for byte
    python scripts/check_sierra_aggressor.py --selftest           # synthetic only; reads no market data
Truth is exactly D626's CL/NG `trades` (validate_tas_sign.py:63): the free post-vault job plus the 10-10 top-up.
Sierra: only CLX26, CLF27, NGX26, NGF27 (the principal: "The four on disk"), memory-mapped and decoded only inside
[2026-09-21, 2026-10-10) ET, never through `read_scid`. The window, the >= 20-contract floor and the ts_recv clock are
the sibling check's. VERDICT (D629 §6 with the principal's floor, "≥ 10 sessions, r ≥ 0.8"): UNRESOLVED if fewer
than 10 sessions have a qualifying pair; otherwise KEEP if r(ts_recv) >= 0.8, else VOID. ts_event and the HO/RB
`pass` / `usable_r_ge_0.8` keys are reported beside and never gate it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import tempfile
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

# ---- CL/NG (D629 §6)
CLNG = ("CL", "NG")
D626_SESSIONS = ("2026-09-21", "2026-10-09")  # D626 §3: 15 NYMEX sessions
D626_END_EXCL = "2026-10-10"
D626_MARKER = REPO / "data" / "ledger_tas_sign_validation.json"  # written once by validate_tas_sign.py --gate
ENERGY_FROM = dt.date(2026, 10, 11)  # as check_c0_sierra_sign.py:40 (frozen, so copied rather than imported)
CLNG_CONTRACTS = {"CL": ("CLX26", "CLF27"), "NG": ("NGX26", "NGF27")}  # the principal: "The four on disk"
D629_R_BAR, D629_MIN_SESSIONS = 0.8, 10  # D629 §6; the floor is the principal's (2026-09-29)
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")


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


def truth_windows(contracts: list[str], files: list[Path] | None = None,
                  cache_name: str = "sierra_check_truth_windows") -> pd.DataFrame:
    """Databento window nets per (clock, contract, day). By default the HO/RB sibling job, as first written; the
    CL/NG check passes D626's own files and its own cache name."""
    import databento as db  # type: ignore[import-not-found]
    if files is None:
        rec = json.loads(JOBS.read_text(encoding="utf-8"))
        job = next(j for j in rec["jobs"] if j["label"] == "siblings-trades")
        files = sorted((RAW / job["job"]["id"]).glob("*.dbn.zst"))
    cache = REPO / "temp" / f"{cache_name}.csv.gz"
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


# ================================================================================ CL/NG (D629 §6)
def _us(ts: pd.Timestamp) -> int:
    """Microseconds since Sierra Chart's epoch (1899-12-30 UTC)."""
    return int((ts.tz_convert("UTC") - ORIGIN) // pd.Timedelta(microseconds=1))


def sierra_slice(path: Path, lo_us: int, hi_us: int) -> np.ndarray:
    """The records with lo_us <= dt < hi_us, memory-mapped and decoded only inside that range. Sierra Chart files
    are sorted up to millisecond inversions, so the binary search is exact unless one straddles a bound: the slice
    must have no inversion of 1 s or more and lie inside the bounds, the 100 records before it must all be before
    lo_us and the 100 after it at or past hi_us (their timestamps only)."""
    with open(path, "rb") as fh:
        head = fh.read(12)
    if head[:4] != b"SCID":
        raise CheckError(f"{path.name}: not an SCID file")
    hdr, rs = int.from_bytes(head[4:8], "little"), int.from_bytes(head[8:12], "little")
    if rs != REC.itemsize:
        raise CheckError(f"{path.name}: record size {rs} != {REC.itemsize}")
    mm = np.memmap(path, dtype=REC, mode="r", offset=hdr)
    dt_all = mm["dt"]
    lo = int(np.searchsorted(dt_all, lo_us, side="left"))
    hi = int(np.searchsorted(dt_all, hi_us, side="left"))
    rec = np.array(mm[lo:hi])
    d = rec["dt"]
    if len(d) and (int(d.min()) < lo_us or int(d.max()) >= hi_us or bool((np.diff(d) < -1_000_000).any())):
        raise CheckError(f"{path.name}: the decoded slice leaves its bounds or has an inversion of 1 s or more")
    if lo > 0 and int(np.max(dt_all[max(0, lo - 100):lo])) >= lo_us:
        raise CheckError(f"{path.name}: a record before the slice index is inside the slice's range")
    if hi < len(dt_all) and int(np.min(dt_all[hi:hi + 100])) < hi_us:
        raise CheckError(f"{path.name}: a record after the slice index is before its upper bound")
    del dt_all, mm
    return rec


def slice_windows(contract: str, rec: np.ndarray) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Per ET day, the 14:28:00-14:30:00 window's Sierra total and net (AskVolume - BidVolume), and the slice's
    metadata (computed on the slice only)."""
    if not len(rec):
        return [], {"records": 0}
    et = (ORIGIN + pd.to_timedelta(rec["dt"], unit="us")).tz_convert(ET)
    v, bv, av = (rec[k].astype("int64") for k in ("v", "bv", "av"))
    meta = {"records": int(len(rec)), "first": str(et.min()), "last": str(et.max()),
            "share_volume_with_side": round(float((bv + av).sum() / v.sum()), 6) if v.sum() else None}
    clock = et.strftime("%H:%M:%S")
    keep = np.asarray((clock >= W0) & (clock < W1))
    g = pd.DataFrame({"day": et[keep].strftime("%Y-%m-%d"), "v": v[keep], "net": (av - bv)[keep]}).groupby("day").sum()
    return [{"contract": contract, "day": day, "sc_total": int(x["v"]), "sc_net": int(x["net"])} for day, x in g.iterrows()], meta


def d629_guard(root: str, *, today: dt.date, marker: Path, topup_jobs: Path) -> None:
    """Refuse before any CL/NG file is opened unless D626's read has happened: the date, D626's own written gate,
    and the 10-10 top-up job downloaded."""
    if root not in CLNG:
        raise CheckError(f"root {root!r}: the D629 §6 check is for CL and NG")
    if today < ENERGY_FROM:
        raise CheckError(f"REFUSING: {today} is before {ENERGY_FROM}; CL/NG post-vault data is D626's sample until its read")
    if not marker.exists():
        raise CheckError(f"REFUSING: {marker.name} is absent, so D626's read has not happened")
    doc = json.loads(marker.read_text(encoding="utf-8"))
    if not (doc.get("gate") or {}).get("verdict"):
        raise CheckError(f"REFUSING: {marker.name} carries no gate verdict")
    if not topup_jobs.exists():
        raise CheckError(f"REFUSING: {topup_jobs.name} is absent (the 10-10 top-up has not run)")
    rec = json.loads(topup_jobs.read_text(encoding="utf-8"))
    job = next((j for j in rec.get("jobs", []) if j.get("label") == "topup-trades"), None)
    if not job or not job.get("downloaded_utc"):
        raise CheckError("REFUSING: the topup-trades job is not downloaded")


def truth_seal(tr: pd.DataFrame, root: str) -> None:
    """No vault row may be in memory, and every truth day must be one of D626's sessions."""
    import validate_flow_estimate as V
    V.vault_guard(tr.assign(symbol=tr["contract"]), (root,))
    bad = tr[(tr["day"] < D626_SESSIONS[0]) | (tr["day"] > D626_SESSIONS[1])]
    if len(bad):
        raise CheckError(f"{len(bad)} truth rows fall outside D626's sessions {D626_SESSIONS}: {sorted(set(bad['day']))[:5]}")


def d629_verdict(sc: pd.DataFrame, tr: pd.DataFrame) -> dict[str, Any]:
    """r of the (contract, day) window nets on ts_recv, the pairs with >= MIN_GROSS true contracts; UNRESOLVED below
    D629_MIN_SESSIONS distinct sessions; KEEP at r >= D629_R_BAR, else VOID. A Fisher-z 95% interval is reported."""
    g = tr[tr["clock"] == "ts_recv"]
    m = sc.merge(g, on=["contract", "day"], how="inner")
    m = m[m["tr_total"] >= MIN_GROSS]
    out: dict[str, Any] = {"clock": "ts_recv", "pairs": int(len(m)), "sessions": int(m["day"].nunique()),
                           "r_bar": D629_R_BAR, "min_sessions": D629_MIN_SESSIONS}
    r = float(np.corrcoef(m["sc_net"], m["tr_net"])[0, 1]) if len(m) >= 3 else float("nan")
    out["r_net"] = None if not math.isfinite(r) else round(r, 4)
    if math.isfinite(r) and len(m) > 3 and abs(r) < 1:
        z, se = math.atanh(r), 1 / math.sqrt(len(m) - 3)
        out["ci95"] = [round(math.tanh(z - 1.96 * se), 4), round(math.tanh(z + 1.96 * se), 4)]
    if out["sessions"] < D629_MIN_SESSIONS:
        out["verdict"] = f"UNRESOLVED (fewer than {D629_MIN_SESSIONS} sessions)"
    elif not math.isfinite(r):
        out["verdict"] = "UNRESOLVED (r undefined)"
    else:
        out["verdict"] = "KEEP" if r >= D629_R_BAR else "VOID"
    return out


def run_clng(root: str, check: bool) -> int:
    out = OUT.with_name(f"sierra_aggressor_check_{root.lower()}.json")
    if not check and out.exists():
        raise CheckError(f"{out.name} exists: D629 §6 runs once (use --check to reproduce it)")
    sys.path.insert(0, str(REPO / "scripts"))
    import validate_flow_estimate as V
    d629_guard(root, today=dt.date.today(), marker=D626_MARKER, topup_jobs=V.TOPUP_JOBS)
    contracts = list(CLNG_CONTRACTS[root])
    missing = [c for c in contracts if not (SC_DATA / f"{c}-NYMEX.scid").exists()]
    if missing:
        raise CheckError(f"Sierra files missing: {missing}")
    files = V._files(V.FREE_JOBS, "trades-post-vault") + V._files(V.TOPUP_JOBS, "topup-trades")
    lo_us, hi_us = _us(pd.Timestamp(D626_SESSIONS[0], tz=ET)), _us(pd.Timestamp(D626_END_EXCL, tz=ET))
    rows: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    for c in contracts:
        r_, meta[c] = slice_windows(c, sierra_slice(SC_DATA / f"{c}-NYMEX.scid", lo_us, hi_us))
        rows += r_
    sc = pd.DataFrame(rows, columns=["contract", "day", "sc_total", "sc_net"])
    tr = truth_windows(contracts, files=files, cache_name=f"sierra_check_truth_{root.lower()}")
    truth_seal(tr, root)
    res = {"spec": "D629 §6 (the principal's rulings 2026-09-29: >= 10 sessions, r >= 0.8; the four contracts on disk)",
           "root": root, "sessions": list(D626_SESSIONS), "truth_files": [f.name for f in files],
           "contracts": contracts, "sierra_files": meta, "window_et": [W0, W1], "min_gross": MIN_GROSS,
           "d629": d629_verdict(sc, tr), "comparison_reported_beside": compare(sc, tr),
           "note": "only d629.verdict gates; comparison's pass / usable_r_ge_0.8 are the HO/RB sibling check's bars",
           "deviations": []}
    text = json.dumps(res, indent=1, sort_keys=True, default=str) + "\n"
    if check:
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            raise CheckError(f"--check: {out.name} does not reproduce")
        print(f"--check: {out.name} reproduces byte for byte")
        return 0
    out.write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps(res["d629"], indent=1))
    return 0


def selftest() -> int:
    """Synthetic only: no market file is opened. Every guard is shown to fire."""
    fired: list[str] = []

    def must_raise(name: str, fn: Any) -> None:
        try:
            fn()
        except CheckError:
            fired.append(name)
            return
        except Exception as e:  # validate_flow_estimate raises its own error class
            if type(e).__name__.endswith("Error"):
                fired.append(name)
                return
            raise
        raise SystemExit(f"selftest: the {name} guard did not fire")

    lo_us, hi_us = _us(pd.Timestamp(D626_SESSIONS[0], tz=ET)), _us(pd.Timestamp(D626_END_EXCL, tz=ET))

    def at(s: str) -> int:
        return _us(pd.Timestamp(s, tz=ET))

    def write_scid(p: Path, stamps: list[int], bv: int = 2, av: int = 5) -> None:
        r = np.zeros(len(stamps), REC)
        r["dt"], r["v"], r["bv"], r["av"], r["n"] = stamps, 10, bv, av, 1
        hdr = bytearray(56)
        hdr[:4], hdr[4:8], hdr[8:12] = b"SCID", (56).to_bytes(4, "little"), REC.itemsize.to_bytes(4, "little")
        p.write_bytes(bytes(hdr) + r.tobytes())

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # 1. the slice decodes only [lo, hi)
        good = tdp / "g.scid"
        write_scid(good, [at("2026-09-18 14:28:30"), at("2026-09-21 14:27:59"), at("2026-09-21 14:28:00"),
                          at("2026-09-21 14:29:59"), at("2026-09-21 14:30:00"), at("2026-10-10 14:28:30")])
        rec = sierra_slice(good, lo_us, hi_us)
        if len(rec) != 4 or int(rec["dt"].min()) < lo_us or int(rec["dt"].max()) >= hi_us:
            raise SystemExit("selftest: the slice is not [lo, hi)")
        # 2. the window keeps 14:28:00 <= t < 14:30:00 and nets av - bv
        rows, _ = slice_windows("NGX26", rec)
        if rows != [{"contract": "NGX26", "day": "2026-09-21", "sc_total": 20, "sc_net": 6}]:
            raise SystemExit(f"selftest: window rows {rows}")
        # 3. a record out of order just inside the slice must raise
        bad = tdp / "b.scid"
        write_scid(bad, [at("2026-09-18 10:00"), at("2026-09-21 10:00"), at("2026-09-17 10:00"), at("2026-09-22 10:00")])
        must_raise("an inverted record inside the slice", lambda: sierra_slice(bad, lo_us, hi_us))
    # 4. the verdict
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-09-21", "2026-10-09")][:12]
    rng = np.random.default_rng(5)
    net = rng.integers(-200, 200, len(days))
    sc = pd.DataFrame({"contract": "NGX26", "day": days, "sc_total": 500, "sc_net": net})
    tr = pd.DataFrame({"clock": "ts_recv", "contract": "NGX26", "day": days, "tr_total": 500, "tr_net": net})
    if d629_verdict(sc, tr)["verdict"] != "KEEP":
        raise SystemExit("selftest: identical nets did not KEEP")
    tr_half = tr.assign(tr_net=(0.5 * net + rng.normal(0, 1, len(days)) * np.std(net) * 0.9).round().astype(int))
    v_half = d629_verdict(sc, tr_half)
    if not (v_half["r_net"] is not None and v_half["r_net"] < 0.8 and v_half["verdict"] == "VOID"):
        raise SystemExit(f"selftest: a weak match did not VOID ({v_half})")
    if not d629_verdict(sc.head(5), tr.head(5))["verdict"].startswith("UNRESOLVED"):
        raise SystemExit("selftest: five sessions did not read UNRESOLVED")
    if d629_verdict(sc, tr.assign(tr_total=10))["pairs"] != 0:
        raise SystemExit("selftest: pairs below 20 true contracts were counted")
    # 5. the guards
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        mk, tj = tdp / "marker.json", tdp / "topup.json"
        late = dt.date(2026, 10, 11)
        must_raise("a run before 2026-10-11", lambda: d629_guard("NG", today=dt.date(2026, 10, 10), marker=mk, topup_jobs=tj))
        must_raise("a missing D626 marker", lambda: d629_guard("NG", today=late, marker=mk, topup_jobs=tj))
        mk.write_text(json.dumps({"gate": {}}), encoding="utf-8")
        must_raise("a marker without a verdict", lambda: d629_guard("NG", today=late, marker=mk, topup_jobs=tj))
        mk.write_text(json.dumps({"gate": {"verdict": "PASS"}}), encoding="utf-8")
        must_raise("a missing top-up record", lambda: d629_guard("NG", today=late, marker=mk, topup_jobs=tj))
        tj.write_text(json.dumps({"jobs": [{"label": "topup-trades"}]}), encoding="utf-8")
        must_raise("an undownloaded top-up job", lambda: d629_guard("NG", today=late, marker=mk, topup_jobs=tj))
        tj.write_text(json.dumps({"jobs": [{"label": "topup-trades", "downloaded_utc": "2026-10-10T08:00:00Z"}]}), encoding="utf-8")
        d629_guard("NG", today=late, marker=mk, topup_jobs=tj)
        must_raise("a non-CL/NG root", lambda: d629_guard("HO", today=late, marker=mk, topup_jobs=tj))
    sys.path.insert(0, str(REPO / "scripts"))
    must_raise("a vault day in the truth", lambda: truth_seal(pd.DataFrame({"contract": ["NGX26"], "day": ["2026-09-18"]}), "NG"))
    must_raise("a truth day after D626's sample", lambda: truth_seal(pd.DataFrame({"contract": ["NGX26"], "day": ["2026-10-12"]}), "NG"))
    truth_seal(pd.DataFrame({"contract": ["NGX26"], "day": ["2026-09-21"]}), "NG")
    # 6. CL/NG needs --run or --check; HO/RB keep their positional call
    if main(["--root", "NG"]) != 2:
        raise SystemExit("selftest: a CL/NG call without --run or --check was not refused")
    print(f"selftest: {len(fired)} guards fired: {fired}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root_pos", nargs="?", default=None, help="HO or RB (the original positional call)")
    ap.add_argument("--root", default=None, choices=("HO", "RB", "CL", "NG"))
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.selftest:
        return selftest()
    root = a.root or a.root_pos or "HO"
    if root in CLNG:
        if not (a.run or a.check):
            print("refused: the CL/NG check runs only with --run (once) or --check")
            return 2
        return run_clng(root, check=a.check)
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
