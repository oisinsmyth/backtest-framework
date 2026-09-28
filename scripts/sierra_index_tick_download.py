"""Sierra Chart 1-tick history for every ES and NQ quarterly contract whose front life falls in the opening model's
in-sample (OA-A3: the principal, 2026-09-28, "Sierra Chart, one contract at a time"; A7 / stage S-B needs the
exchange aggressor side, which Databento serves in-sample only at a price).

    python scripts/sierra_index_tick_download.py [--only ESH19,NQM20] [--dry-run]

ONE CONTRACT AT A TIME, because the disk decides it: one ES contract is ~1.8 GB of ticks (ESH19: 45.9 M records) and
the pull is ~150 GB raw against ~137 GB free. Each file is therefore, in turn:
  1. requested through Sierra Chart's UDP port (22903) and waited on until its size has been still for STABLE_S
     (Sierra's queue has long quiet gaps, so a short idle rule misreads it), then its chart is closed;
  2. checked for a cut-short download: a network drop ends a download early and Sierra logs it as complete
     (memory: sierra-chart-download-quirks). Its last record must fall on or after the contract's last trading day
     (the third Friday of the expiry month) minus CUT_TOL_BDAYS. A cut file is re-requested, which resumes it from
     its last record, up to RETRIES times;
  3. hashed (SHA-256), then COMPRESSED IN PLACE by NTFS (`compact /c /exe:lzx`), which is lossless and transparent:
     nothing is deleted, the file keeps its name and location, and Sierra Chart and every reader see the same bytes.
     The hash is re-taken and must be unchanged. ESH19 measured 3.8 : 1 (1.83 GB stored in 0.48 GB);
  4. recorded in `data/opening/sierra_index_tick_record.json`: bytes, bytes stored, records, first/last timestamp,
     the expected last day, cut_short, the SHA-256.
It stops before a contract if free space is below MIN_FREE_GB, which protects the 90 GB the 2026-10-09 top-up
(`prelapse-databento-topup`) checks for.

WHAT IT READS: each file's size, record count (header arithmetic) and first and last timestamps. No price, volume or
side. ESH25 and NQH25 expire 2025-03-21, so they hold vault days (2025-03-01 onward); those are downloaded and never
parsed here (OA-A1).

THE LIST: H, M, U, Z of 2016 → H 2025 for ES and NQ, 37 each. ESH16 is the front from mid-December 2015, which gives
the 20-session warm-up A7's large-lot threshold needs before 2016-01-04. Sierra Chart symbols: ROOT + month letter +
two-digit year + "-CME".
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import sierra_ui as U  # noqa: E402

SC_DATA = Path(r"C:\SierraChart\Data")
OUT = REPO / "data" / "opening" / "sierra_index_tick_record.json"
UDP = ("127.0.0.1", 22903)
ROOTS = ("ES", "NQ")
QUARTERS = "HMUZ"
LETTER = "FGHJKMNQUVXZ"
REC_SIZE, HDR = 40, 56
STABLE_S, POLL_S, CAP_S = 90, 10, 90 * 60  # a quiet gap that ends a wait early is caught by the cut-short check
LIVE_LAG_MIN = 20  # a live contract is complete once its last tick is this close to now (the feed is 10 min delayed)
RETRIES, CUT_TOL_BDAYS = 2, 1
MIN_FREE_GB = 95.0


def contracts() -> list[str]:
    out = []
    for yy in range(16, 26):
        for q in QUARTERS:
            if yy == 25 and q != "H":
                continue
            for r in ROOTS:
                out.append(f"{r}{q}{yy:02d}")
    return sorted(out, key=lambda s: (s[3:5], QUARTERS.index(s[2]), s[:2]))


def path(sym: str) -> Path:
    return SC_DATA / f"{sym}-CME.scid"


def size(sym: str) -> int:
    p = path(sym)
    return p.stat().st_size if p.exists() else 0


def stored_bytes(p: Path) -> int:
    """Bytes the file occupies on disk (after NTFS compression), GetCompressedFileSizeW."""
    hi = ctypes.c_ulong(0)
    lo = ctypes.windll.kernel32.GetCompressedFileSizeW(str(p), ctypes.byref(hi))
    return int((hi.value << 32) + lo)


def file_span(sym: str) -> dict[str, Any]:
    """Record count and the first/last timestamps only: no price, volume or side is read."""
    p = path(sym)
    n = (p.stat().st_size - HDR) // REC_SIZE if p.exists() else 0
    if n <= 0:
        return {"records": 0}
    with open(p, mode="rb") as fh:
        fh.seek(HDR)
        first = int(np.frombuffer(fh.read(8), "<i8")[0])
        fh.seek(HDR + (n - 1) * REC_SIZE)
        last = int(np.frombuffer(fh.read(8), "<i8")[0])
    t = pd.to_datetime([first, last], unit="us", origin=pd.Timestamp("1899-12-30"))
    return {"records": int(n), "first_utc": str(t[0]), "last_utc": str(t[1])}


def expected_last_day(sym: str) -> pd.Timestamp:
    """The equity index quarterly's last trading day: the third Friday of the expiry month (trading ends 09:30 ET).
    A holiday moves it earlier, never later."""
    month, yy = LETTER.index(sym[2]) + 1, 2000 + int(sym[3:5])
    first = pd.Timestamp(year=yy, month=month, day=1)
    first_friday = first + pd.Timedelta(days=(4 - first.weekday()) % 7)
    return first_friday + pd.Timedelta(days=14)


def is_cut_short(span: dict[str, Any], sym: str) -> bool:
    if span.get("records", 0) <= 0:
        return True
    return bool(pd.Timestamp(span["last_utc"][:10]) < expected_last_day(sym) - CUT_TOL_BDAYS * pd.offsets.BDay())


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, mode="rb") as fh:
        while b := fh.read(64 * 1024 * 1024):
            h.update(b)
    return h.hexdigest()


def free_gb() -> float:
    return shutil.disk_usage("C:\\").free / 1e9


def caught_up(sym: str) -> bool:
    """A live contract's file never goes still while the market is open (the delayed feed keeps appending), so the
    stillness rule would run it to CAP_S. It is complete once its last tick is within LIVE_LAG_MIN of now."""
    last = file_span(sym).get("last_utc")
    return last is not None and pd.Timestamp(last, tz="UTC") >= pd.Timestamp.now("UTC") - pd.Timedelta(
        minutes=LIVE_LAG_MIN)


def request_and_wait(sym: str, live: bool = False) -> None:
    """Open the chart (queues or resumes the download), wait until the file has been still for STABLE_S (or, for a
    live contract, until it has caught up to now), close it."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(f"{sym}-CME.scid".encode(), UDP)
    t0, last, changed = time.time(), size(sym), time.time()
    while time.time() - t0 < CAP_S:
        time.sleep(POLL_S)
        cur = size(sym)
        if cur != last:
            last, changed = cur, time.time()
        if cur > HDR and time.time() - changed >= STABLE_S:
            break
        if live and cur > HDR and time.time() - t0 >= STABLE_S and caught_up(sym):
            break
    U.cmd_close("^" + re.escape(sym) + "-CME")


def compress(p: Path) -> None:
    subprocess.run(["compact", "/c", "/exe:lzx", str(p)], capture_output=True, text=True, check=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--dry-run", action="store_true", help="print the plan and the file states; request nothing")
    ap.add_argument("--live", action="store_true",
                    help="unexpired contracts (ESZ26, NQZ26 for A7's exchange-flag check): no cut-short retry, "
                         "recorded as live; the check reads their post-vault sessions only")
    a = ap.parse_args(argv)
    syms = contracts() if a.only is None else a.only.split(",")
    rec: dict[str, Any] = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"contracts": {}}
    done = {x for x, r in rec["contracts"].items() if r.get("compressed") and not r.get("cut_short")}
    todo = [x for x in syms if x not in done]
    print(f"{len(syms)} contracts, {len(todo)} to do; {free_gb():.1f} GB free", flush=True)
    if a.dry_run:
        for x in todo:
            print(f"  {x}: {size(x):,} bytes on disk now; last day {expected_last_day(x).date()}", flush=True)
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for i, x in enumerate(todo, 1):
        if free_gb() < MIN_FREE_GB:
            print(f"STOP: {free_gb():.1f} GB free, below {MIN_FREE_GB} GB; {len(todo) - i + 1} contracts left",
                  flush=True)
            return 2
        t0 = time.time()
        span: dict[str, Any] = {}
        for attempt in range(1 + RETRIES):
            request_and_wait(x, live=a.live)
            span = file_span(x)
            if a.live or not is_cut_short(span, x):
                break
            print(f"  {x}: cut short at {span.get('last_utc')} (attempt {attempt + 1}); re-requesting", flush=True)
        p = path(x)
        r: dict[str, Any] = {"bytes": size(x), **span, "expected_last_day": str(expected_last_day(x).date()),
                             "cut_short": (None if a.live else is_cut_short(span, x)), "live": a.live,
                             "minutes": round((time.time() - t0) / 60, 1)}
        if a.live:  # Sierra keeps an unexpired contract's file open and appending: no stable hash, and compact fails
            r.update({"compressed": False, "note": "live: neither hashed nor compressed; the flag check reads the span"})
        elif span.get("records", 0) > 0:
            h1 = sha256(p)
            compress(p)
            h2 = sha256(p)
            if h1 != h2:
                raise SystemExit(f"{x}: the hash changed under compression ({h1} -> {h2})")
            r.update({"sha256": h1, "compressed": True, "bytes_stored": stored_bytes(p)})
        rec["contracts"][x] = r
        OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"[{i}/{len(todo)}] {x}: {r.get('records', 0):,} records, {r['bytes'] / 1e9:.2f} GB -> "
              f"{r.get('bytes_stored', 0) / 1e9:.2f} GB stored, {r.get('first_utc', '')[:10]} -> "
              f"{r.get('last_utc', '')[:10]}, cut_short={r['cut_short']}, {r['minutes']} min; "
              f"{free_gb():.1f} GB free", flush=True)
    bad = [x for x in syms if rec["contracts"].get(x, {}).get("cut_short", True)]
    print(f"ALL DONE; cut short or empty: {bad}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
