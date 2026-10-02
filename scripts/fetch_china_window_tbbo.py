"""Buy gold's China-open trade-and-quote history (the principal, 2026-10-02: "Ok go for the $98 one, make sure to
mark it as do not delete/expensive data").

PAID DATA. DO NOT DELETE. Re-buying it costs about USD 98 (the quote of 2026-10-02, 40 sampled windows scaled).

What it buys (Databento GLBX.MDP3, continuous front `GC.v.0` / `MGC.v.0`, one request per trade date D, window
18:30 ET on the evening before -> 03:15 ET on D: the China open under EDT and EST, the Tokyo placebo, a 30-minute
look-back, and the SHFE close):
- GC  `tbbo` and `bbo-1m`, trade dates 2016-01-04 -> 2023-12-29 (in-sample only; nothing reaches 2024);
- MGC `tbbo` and `bbo-1m`, trade dates 2022-01-03 -> 2023-12-29 (the micro calibration sample).

Every window is priced (`metadata.get_cost`) immediately before it is fetched. The run REFUSES to start without
`--i-accept-the-cost 98` and stops before the running total would pass CAP_USD. Files go to
`<main checkout>/data/raw/databento/china_window_2016_2023/<SYM>_<schema>/<YYYY>/<YYYY-MM-DD>.dbn.zst` (gitignored,
CME terms forbid committing them), a DO_NOT_DELETE.md sits in that directory, and every finished file is set read-only.
The committed manifest is `data/china_window_tbbo_manifest.csv` (path, bytes, USD, sha256, records). A lock file
keeps it to one downloader; it resumes by skipping files already in the manifest. The key is never printed.

    python scripts/fetch_china_window_tbbo.py --plan
    python scripts/fetch_china_window_tbbo.py --fetch --i-accept-the-cost 98
    python scripts/fetch_china_window_tbbo.py --verify
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import os
import stat
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
DEST = MAIN_DATA / "raw" / "databento" / "china_window_2016_2023"
MANIFEST = REPO / "data" / "china_window_tbbo_manifest.csv"
LOCK = DEST / ".download.lock"
DATASET = "GLBX.MDP3"
NY = ZoneInfo("America/New_York")
SEAL_UTC = dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc)
APPROVED_USD = 98.0
CAP_USD = 120.0                     # raised from 110 by the principal, 2026-10-02 ("Keep going raise the cap")
THREADS = 8
MAX_ERRORS = 20
JOBS = [("GC.v.0", "tbbo", "2016-01-04"), ("GC.v.0", "bbo-1m", "2016-01-04"),
        ("MGC.v.0", "tbbo", "2022-01-03"), ("MGC.v.0", "bbo-1m", "2022-01-03")]
LAST_DAY = "2023-12-29"
FIELDS = ["path", "symbol", "schema", "day", "start_utc", "end_utc", "bytes", "usd", "records", "sha256", "fetched_at"]
DO_NOT_DELETE = """# DO NOT DELETE — PAID DATA (about USD 98, bought 2026-10-02)

Gold's China-open trade-and-quote history, bought on the principal's word ("Ok go for the $98 one, make sure to mark
it as do not delete/expensive data").

- GC `tbbo` + `bbo-1m`, every trade date 2016-01-04 -> 2023-12-29, window 18:30 ET (evening before) -> 03:15 ET;
- MGC `tbbo` + `bbo-1m`, 2022-01-03 -> 2023-12-29, same window (the micro calibration sample).

Re-buying it costs money: these are L1 schemas older than the subscription's 12-month window. The files are set
read-only on purpose. The manifest with every file's size, cost and sha256 is committed at
`data/china_window_tbbo_manifest.csv`; the fetcher is `scripts/fetch_china_window_tbbo.py`. CME's terms forbid
committing or redistributing the files themselves.
"""


def api_key() -> str:
    import fetch_futures_1m as F
    return F.api_key()


def window(day: str) -> tuple[str, str]:
    d = dt.date.fromisoformat(day)
    a = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(18, 30), tzinfo=NY).astimezone(dt.timezone.utc)
    b = dt.datetime.combine(d, dt.time(3, 15), tzinfo=NY).astimezone(dt.timezone.utc)
    if not b < SEAL_UTC:
        raise SystemExit(f"seal: the window for {day} reaches 2024")
    return a.isoformat(), b.isoformat()


def plan_rows() -> list[tuple[str, str, str]]:
    rows = []
    for sym, sch, first in JOBS:
        for d in pd.bdate_range(first, LAST_DAY):
            rows.append((sym, sch, d.strftime("%Y-%m-%d")))
    return rows


def rel_path(sym: str, sch: str, day: str) -> Path:
    return Path(f"{sym.split('.')[0]}_{sch}") / day[:4] / f"{day}.dbn.zst"


def load_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST.exists():
        return {}
    with open(MANIFEST, encoding="utf-8", newline="") as fh:
        return {r["path"]: r for r in csv.DictReader(fh)}


def retry(f, **kw):
    for k in range(7):
        try:
            return f(**kw)
        except Exception as ex:  # noqa: BLE001
            msg = str(ex)
            if "symbology_invalid_request" in msg:
                raise
            if k == 6 or not any(s in msg for s in ("504", "502", "503", "500", "timed out", "Timeout", "Connection", "ended prematurely")):
                raise
            time.sleep(2 * 2 ** k)


def count_records(p: Path, s: str, e: str) -> int:
    """Decode the whole file; every record's ts_event inside the window, or raise."""
    import databento as db
    st = db.DBNStore.from_bytes(p.read_bytes())
    lo, hi = pd.Timestamp(s).value, pd.Timestamp(e).value
    n = 0
    for a in st.to_ndarray(count=1 << 20):
        if len(a):
            # ts_recv: the record's own stamp (bbo-1m: the interval; tbbo: the trade's receipt). bbo-1m's ts_event is
            # the last quote change, which in a quiet minute can precede the window (the first run's false alarm).
            ts = a["ts_recv"].astype("int64") if "ts_recv" in a.dtype.names else a["ts_event"].astype("int64")
            if not ((ts >= lo - 60_000_000_000) & (ts < hi + 60_000_000_000)).all():
                raise ValueError(f"{p.name}: a record outside its window")
        n += len(a)
    return n


def salvage(p: Path, s: str, e: str) -> int | None:
    """A .part left by the first run (paid, downloaded, never renamed): keep it if it decodes cleanly."""
    try:
        import databento as db
        n = count_records(p, s, e)
        idx = db.DBNStore.from_bytes(p.read_bytes()).to_df().index
        if n == 0 or idx.max() < pd.Timestamp(e) - pd.Timedelta(minutes=30):
            raise ValueError("it does not reach the window's end (a truncated stream?)")
        return n
    except Exception as ex:  # noqa: BLE001
        print(f"  salvage refused {p.name}: {type(ex).__name__}: {str(ex)[:120]}; re-fetching", flush=True)
        p.unlink(missing_ok=True)
        return None


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def plan() -> int:
    rows = plan_rows()
    done = load_manifest()
    print(f"{len(rows)} windows planned; {len(done)} already in the manifest; approved USD {APPROVED_USD}, cap USD {CAP_USD}")
    for sym, sch, first in JOBS:
        n = sum(1 for r in rows if r[0] == sym and r[1] == sch)
        print(f"  {sym} {sch}: {n} windows from {first}")
    return 0


def fetch(accepted: float | None) -> int:
    import databento as db
    if accepted is None or abs(accepted - APPROVED_USD) > 0.5:
        raise SystemExit(f"refused: pass --i-accept-the-cost {APPROVED_USD:g} (the principal's approval)")
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "DO_NOT_DELETE.md").write_text(DO_NOT_DELETE, encoding="utf-8")
    if LOCK.exists():
        raise SystemExit(f"another downloader holds {LOCK} (pid {LOCK.read_text(encoding='utf-8').strip()}); refusing")
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    try:
        c = db.Historical(api_key())
        done = load_manifest()
        spent = sum(float(r["usd"]) for r in done.values())
        todo = [r for r in plan_rows() if rel_path(*r).as_posix() not in done]
        print(f"{len(todo)} windows to fetch; spent so far USD {spent:.2f}", flush=True)
        lock = threading.Lock()
        state = {"spent": spent, "stop": False, "n": 0, "empty": 0}
        new_rows: list[dict[str, str]] = []

        errors: list[str] = []

        def one(r: tuple[str, str, str]) -> None:
            try:
                _one(r)
            except Exception as ex:  # noqa: BLE001  (printed at once; MAX_ERRORS stops the run so it cannot keep spending)
                msg = f"{r}: {type(ex).__name__}: {str(ex)[:200]}"
                with lock:
                    errors.append(msg)
                    print("ERROR", msg, flush=True)
                    if len(errors) >= MAX_ERRORS:
                        state["stop"] = True
                        print(f"STOP: {MAX_ERRORS} errors", flush=True)

        def _one(r: tuple[str, str, str]) -> None:
            sym, sch, day = r
            if state["stop"]:
                return
            s, e = window(day)
            kw = dict(dataset=DATASET, symbols=[sym], schema=sch, start=s, end=e, stype_in="continuous")
            try:
                usd = float(retry(c.metadata.get_cost, **kw))
            except Exception as ex:  # noqa: BLE001
                if "symbology_invalid_request" in str(ex):
                    with lock:
                        state["empty"] += 1
                    return                                   # no session that day: nothing to buy
                raise
            with lock:
                if state["spent"] + usd > CAP_USD:
                    state["stop"] = True
                    print(f"CAP: {day} {sym} {sch} would bring the total to USD {state['spent'] + usd:.2f}; stopping", flush=True)
                    return
                state["spent"] += usd                        # reserve before fetching
            out = DEST / rel_path(sym, sch, day)
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".part")
            if out.exists():                                        # finished by an earlier run but not yet in its
                recs = count_records(out, s, e)                     # manifest: adopt it, never buy it again
                row = {"path": rel_path(sym, sch, day).as_posix(), "symbol": sym, "schema": sch, "day": day,
                       "start_utc": s, "end_utc": e, "bytes": str(out.stat().st_size), "usd": f"{usd:.6f}",
                       "records": str(recs), "sha256": sha256(out),
                       "fetched_at": dt.datetime.fromtimestamp(out.stat().st_mtime, dt.timezone.utc).isoformat(timespec="seconds")}
                with lock:
                    new_rows.append(row)
                    state["n"] += 1
                return
            recs = salvage(tmp, s, e) if tmp.exists() else None    # a window already paid for (the first run)
            if recs is None:
                store = retry(c.timeseries.get_range, **kw)        # in memory: no open handle on Windows
                tmp.unlink(missing_ok=True)
                store.to_file(str(tmp))
                recs = count_records(tmp, s, e)
                del store
            os.replace(tmp, out)
            os.chmod(out, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
            row = {"path": rel_path(sym, sch, day).as_posix(), "symbol": sym, "schema": sch, "day": day,
                   "start_utc": s, "end_utc": e, "bytes": str(out.stat().st_size), "usd": f"{usd:.6f}", "records": str(recs),
                   "sha256": sha256(out), "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
            with lock:
                new_rows.append(row)
                state["n"] += 1
                if state["n"] % 25 == 0:
                    print(f"  {state['n']} fetched, USD {state['spent']:.2f}, last {day} {sym} {sch}", flush=True)
                if state["n"] % 200 == 0:
                    print(f"  {state['n']} fetched, USD {state['spent']:.2f}", flush=True)
                    _write_manifest(done, new_rows)

        with ThreadPoolExecutor(THREADS) as ex:
            list(ex.map(one, todo))
        _write_manifest(done, new_rows)
        for m in errors[:20]:
            print("ERROR", m, flush=True)
        print(f"done: {state['n']} files fetched, {state['empty']} windows with no session, {len(errors)} errors, "
              f"total USD {state['spent']:.2f} (reserved, including any failed windows)"
              f"{' (STOPPED AT THE CAP)' if state['stop'] else ''}", flush=True)
        return 2 if (state["stop"] or errors) else 0
    finally:
        LOCK.unlink(missing_ok=True)


def _write_manifest(done: dict[str, dict[str, str]], new_rows: list[dict[str, str]]) -> None:
    allr = dict(done)
    for r in new_rows:
        allr[r["path"]] = r
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for k in sorted(allr):
            w.writerow(allr[k])
    os.replace(tmp, MANIFEST)


def verify() -> int:
    done = load_manifest()
    bad = 0
    for k, r in done.items():
        p = DEST / k
        if not p.exists() or str(p.stat().st_size) != r["bytes"] or sha256(p) != r["sha256"]:
            bad += 1
            print(f"MISMATCH {k}")
        elif os.access(p, os.W_OK):
            print(f"not read-only: {k}")
    usd = sum(float(r["usd"]) for r in done.values())
    by = pd.DataFrame(done.values()).groupby(["symbol", "schema"]).agg(files=("path", "size"),
                                                                     usd=("usd", lambda v: sum(map(float, v))))
    print(by.to_string())
    print(f"{len(done)} files, USD {usd:.2f}, {bad} mismatches")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    a = ap.parse_args(argv)
    if a.plan:
        return plan()
    if a.fetch:
        return fetch(a.i_accept_the_cost)
    if a.verify:
        return verify()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
