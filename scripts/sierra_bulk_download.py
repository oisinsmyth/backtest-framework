"""Bulk-download 1-tick Sierra Chart history for every CL and NG contract the funds' indices held in the ledger's
in-sample, 2017-05-22 -> 2025-02-28 (settlement ledger, the signed-flow route; AITODO 2026-09-26).

THE LIST is every contract in the `held` column of `data/ledger_predicted_flow_daily.csv.gz` (Gate 0b's holdings):
77 CL and 48 NG. Sierra Chart symbols are ROOT + month letter + two-digit year + "-NYMEX".

HOW. Sierra Chart serves CME data to no external API, so the driver:
  * opens charts through its UDP port (22903), in batches of BATCH. A first-time symbol queues its own download;
  * tracks progress by file size. Downloads are serial, so a batch is done when every file has stopped growing for
    STABLE_S seconds, or when BATCH_TIMEOUT_S passes;
  * reads the Message Log once per batch (`sierra_ui.read_log`, which overwrites the clipboard) to confirm each
    "Received N ... records for SYMBOL" line and catch "Symbol not allowed" and similar errors;
  * closes the batch's charts (`sierra_ui.cmd_close`), so the chartbook stays small.

WHAT IT READS. For each file: its size, its record count from the header arithmetic, and the timestamps of the first
and last records. No price, volume or side is read. Several contracts expire after 2025-02-28, so their files hold
vault days (2025-03-01 onward); those are downloaded and never parsed here.

KNOWN LIMIT. Sierra Chart downloads each contract from about five months before its expiry, and no setting moves
that earlier. CL era B's June/December components are held up to 456 days ahead, so their early holding months are
absent. The record lists, per contract, how many of its held days fall before the file's first record.

Output: `data/sierra_ledger_download_record.json`. Rerunning skips contracts whose file is already complete.

    uv run python scripts/sierra_bulk_download.py [--only CLM22,NGF18] [--batch 8]
"""
from __future__ import annotations

import argparse
import json
import re
import socket
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
FLOW = REPO / "data" / "ledger_predicted_flow_daily.csv.gz"
OUT = REPO / "data" / "sierra_ledger_download_record.json"
UDP = ("127.0.0.1", 22903)
LETTER = "FGHJKMNQUVXZ"
BATCH, STABLE_S, POLL_S, BATCH_TIMEOUT_S = 8, 12, 3, 900
REC_SIZE, HDR = 40, 56


def contract_list() -> dict[str, list[str]]:
    """symbol -> the in-sample days it was held."""
    d = pd.read_csv(FLOW, encoding="utf-8", usecols=["root", "day", "held"])
    d = d[d["day"] <= "2025-02-28"].drop_duplicates(["root", "day"])
    out: dict[str, list[str]] = {}
    for root, day, held in zip(d["root"], d["day"], d["held"]):
        for ym in held.split(";"):
            sym = f"{root}{LETTER[int(ym[5:7]) - 1]}{ym[2:4]}"
            out.setdefault(sym, []).append(day)
    return out


def size(sym: str) -> int:
    p = SC_DATA / f"{sym}-NYMEX.scid"
    return p.stat().st_size if p.exists() else 0


def file_span(sym: str) -> dict[str, Any]:
    """Record count and the first/last timestamps only: no price, volume or side is read."""
    p = SC_DATA / f"{sym}-NYMEX.scid"
    n = (p.stat().st_size - HDR) // REC_SIZE
    if n <= 0:
        return {"records": 0}
    with open(p, "rb") as fh:
        fh.seek(HDR)
        first = int(np.frombuffer(fh.read(8), "<i8")[0])
        fh.seek(HDR + (n - 1) * REC_SIZE)
        last = int(np.frombuffer(fh.read(8), "<i8")[0])
    t = pd.to_datetime([first, last], unit="us", origin=pd.Timestamp("1899-12-30"))
    return {"records": int(n), "first_utc": str(t[0]), "last_utc": str(t[1])}


def expected_last_day(sym: str) -> pd.Timestamp:
    """The contract's last trading day by the exchange rule, with weekends but no holiday calendar:
    CL, 3 business days before the 25th of the month before delivery (the business day before the 25th when the
    25th is not one); NG, 3 business days before the first day of the delivery month. A holiday moves the true day
    earlier, never later, so a file ending on or after this minus CUT_TOL_BDAYS is whole."""
    root, month, yy = sym[:2], LETTER.index(sym[2]) + 1, 2000 + int(sym[3:5])
    delivery = pd.Timestamp(year=yy, month=month, day=1)
    bd = pd.offsets.BDay()
    if root == "CL":
        d25 = delivery - pd.DateOffset(months=1) + pd.DateOffset(days=24)
        anchor = d25 if d25.weekday() < 5 else d25 - bd
        return anchor - 3 * bd
    if root == "NG":
        return delivery - 3 * bd
    raise ValueError(f"no last-day rule for {sym}")


CUT_TOL_BDAYS = 2


def run_batch(syms: list[str], log_mark: str) -> dict[str, Any]:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for sym in syms:
        s.sendto(f"{sym}-NYMEX.scid".encode(), UDP)
        time.sleep(0.3)
    t0 = time.time()
    last_sizes = {x: size(x) for x in syms}
    last_change = {x: time.time() for x in syms}
    while time.time() - t0 < BATCH_TIMEOUT_S:
        time.sleep(POLL_S)
        now = time.time()
        for x in syms:
            sz = size(x)
            if sz != last_sizes[x]:
                last_sizes[x], last_change[x] = sz, now
        done = [x for x in syms if last_sizes[x] > HDR and now - last_change[x] >= STABLE_S]
        if len(done) == len(syms):
            break
        # an empty file that has not moved while all others are done: stop waiting for it after STABLE_S * 5
        idle = all(now - last_change[x] >= STABLE_S * 5 for x in syms)
        if idle:
            break
    log = U.read_log()
    res: dict[str, Any] = {}
    for x in syms:
        received = [ln for ln in log.splitlines() if f"records for {x}-NYMEX" in ln and ln > log_mark]
        errors = [ln[26:160] for ln in log.splitlines() if x in ln and ln > log_mark
                  and re.search(r"not allowed|not enabled|error|failed|no data", ln, re.I)]
        res[x] = {"bytes": size(x), **file_span(x), "log_received": received[-1][26:260] if received else None,
                  "log_errors": errors[-3:]}
    U.cmd_close("^(" + "|".join(re.escape(x) for x in syms) + r")-NYMEX")
    return res


def queue_all(syms: list[str], force: tuple[str, ...] = ()) -> int:
    """Open each contract whose file is empty and close its chart straight away. Sierra Chart keeps the queued
    download after the chart closes (seen: CLK21 downloaded after its chart was closed), and a duplicate request is
    discarded ("a matching download is already pending"). `force` re-opens contracts whose file stopped short (a
    network drop at 13:26 UTC on 2026-09-26 cut CLQ24 at 2024-07-08); Sierra Chart resumes from the file's last
    record."""
    todo = [x for x in syms if size(x) <= HDR or x in force]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(0, len(todo), BATCH):
        part = todo[i:i + BATCH]
        for x in part:
            s.sendto(f"{x}-NYMEX.scid".encode(), UDP)
            time.sleep(0.4)
        time.sleep(3)  # let each chart register its request before the chart closes
        U.cmd_close("^(" + "|".join(re.escape(x) for x in part) + r")-NYMEX")
    print(f"queued {len(todo)} contracts", flush=True)
    return len(todo)


def wait_drained(syms: list[str], quiet_s: int = 300, cap_s: int = 3 * 3600) -> None:
    """Wait until no contract file has grown for `quiet_s` seconds (file sizes only; the clipboard is untouched)."""
    t0 = time.time()
    last = {x: size(x) for x in syms}
    changed = time.time()
    while time.time() - t0 < cap_s:
        time.sleep(15)
        cur = {x: size(x) for x in syms}
        if cur != last:
            changed, last = time.time(), cur
            n_done = sum(1 for v in cur.values() if v > HDR)
            print(f"{time.strftime('%H:%M:%S')} {n_done}/{len(syms)} contracts have data", flush=True)
        if time.time() - changed >= quiet_s:
            return


def record_all(held: dict[str, list[str]], syms: list[str]) -> dict[str, Any]:
    log = U.read_log().splitlines()
    rec: dict[str, Any] = {"contracts": {}}
    for x in syms:
        r = {"bytes": size(x), **file_span(x)}
        got = [ln for ln in log if f"records for {x}-NYMEX" in ln]
        r["log_received"] = got[-1][26:260] if got else None
        days = held.get(x, [])
        first_day = r.get("first_utc", "9999")[:10]
        r["held_days"] = len(days)
        r["held_days_before_file_start"] = sum(1 for d in days if d < first_day)
        exp = expected_last_day(x)
        r["expected_last_day"] = str(exp.date())
        # a network drop ends a download early and Sierra Chart logs it as complete (CLQ24, CLU22 on 2026-09-26)
        r["cut_short"] = bool(r.get("records", 0) > 0
                              and pd.Timestamp(r["last_utc"][:10]) < exp - CUT_TOL_BDAYS * pd.offsets.BDay())
        rec["contracts"][x] = r
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--batch", type=int, default=BATCH)
    ap.add_argument("--queue", action="store_true", help="queue every contract whose file is empty, then exit")
    ap.add_argument("--wait", action="store_true", help="wait until the files stop growing (sizes only)")
    ap.add_argument("--record", action="store_true", help="record every file's span and coverage")
    ap.add_argument("--force", default="", help="comma list re-queued even though its file has data (a cut file)")
    a = ap.parse_args(argv)
    held = contract_list()
    allsyms = sorted(held) if a.only is None else a.only.split(",")
    if a.queue or a.wait or a.record:
        if a.queue:
            queue_all(allsyms, tuple(x for x in a.force.split(",") if x))
        if a.wait:
            wait_drained(allsyms)
        if a.record:
            done = record_all(held, allsyms)
            miss = [x for x in allsyms if done["contracts"][x].get("records", 0) == 0]
            cut = [x for x in allsyms if done["contracts"][x]["cut_short"]]
            print(f"recorded {len(allsyms)}; without data: {miss}; cut short: {cut}", flush=True)
        return 0
    todo = sorted(held) if a.only is None else a.only.split(",")
    rec: dict[str, Any] = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"contracts": {}}
    pending = [x for x in todo if not (x in rec["contracts"] and rec["contracts"][x].get("records", 0) > 0)]
    print(f"{len(todo)} contracts, {len(pending)} to download, batch {a.batch}", flush=True)
    for i in range(0, len(pending), a.batch):
        batch = pending[i:i + a.batch]
        mark = time.strftime("%Y-%m-%d  %H:%M:%S", time.gmtime())
        res = run_batch(batch, mark)
        for x, r in res.items():
            days = held.get(x, [])
            first_day = r.get("first_utc", "9999")[:10]
            r["held_days"] = len(days)
            r["held_days_before_file_start"] = sum(1 for d in days if d < first_day)
            rec["contracts"][x] = r
        OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        ok = sum(1 for x in batch if res[x].get("records", 0) > 0)
        print(f"batch {i // a.batch + 1}: {ok}/{len(batch)} with data | {', '.join(batch)}", flush=True)
    miss = [x for x in todo if rec["contracts"].get(x, {}).get("records", 0) == 0]
    print("done; without data:", miss, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
