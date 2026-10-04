"""Buy the quote history at D776's and L4's own fill timestamps, in-sample only (the principal, 2026-10-04: "Yes buy
the $24 set").

PAID DATA. DO NOT DELETE. Re-buying it costs about USD 24 (the quote of 2026-10-04, data/fill_cost_probe.json), and
after the Standard plan lapses (about 2026-10-11) quote schemas older than 12 months cannot be bought at all.

What it buys (Databento GLBX.MDP3, continuous front `.v.0`, `tbbo` and `bbo-1s`), one request per window, the windows
of scripts/probe_fill_cost_quotes.py (imported, so the purchase is exactly what was priced):
- D776, its 186 in-sample trade days: entry 08:33 -> 08:36 ET, exit 10:58 -> 11:02 ET; NQ (all), MNQ (from 2019-05-06);
- L4, D778's 280 base-book trades: entry 18:03 -> 18:07 ET on the evening the exit session opens, exit 09:58 -> 10:02
  ET; RTY (all), M2K (from 2019-05-06).
Nothing reaches 2024-01-01 (asserted per window).

Every window is priced (`metadata.get_cost`) immediately before it is fetched. The run REFUSES to start without
`--i-accept-the-cost 24` and stops before the running total would pass CAP_USD (30). Files go to
`<main checkout>/data/raw/databento/fill_cost_2016_2023/<SYM>_<schema>/<YYYY>/<YYYY-MM-DD>_<leg>.dbn.zst` (gitignored;
CME's terms forbid committing them), a DO_NOT_DELETE.md sits in that directory, and every finished file is set
read-only. The committed manifest is `data/fill_cost_quotes_manifest.csv`. One downloader at a time (a lock file); it
resumes by skipping files already in the manifest. The key is never printed. Helpers (retry, count_records, sha256)
are fetch_china_window_tbbo's, imported.

    python scripts/fetch_fill_cost_quotes.py --plan
    python scripts/fetch_fill_cost_quotes.py --fetch --i-accept-the-cost 24
    python scripts/fetch_fill_cost_quotes.py --verify
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import stat
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import fetch_china_window_tbbo as CW  # noqa: E402
import probe_fill_cost_quotes as PR  # noqa: E402

MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
DEST = MAIN_DATA / "raw" / "databento" / "fill_cost_2016_2023"
MANIFEST = REPO / "data" / "fill_cost_quotes_manifest.csv"
LOCK = DEST / ".download.lock"
DATASET = "GLBX.MDP3"
SCHEMAS = ("tbbo", "bbo-1s")
APPROVED_USD = 24.0
CAP_USD = 30.0
THREADS = 8
MAX_ERRORS = 20
FIELDS = ["path", "symbol", "schema", "leg", "day", "start_utc", "end_utc", "bytes", "usd", "records", "sha256", "fetched_at"]
DO_NOT_DELETE = """# DO NOT DELETE — PAID DATA (about USD 24, bought 2026-10-04)

Quote history (tbbo, bbo-1s) at the CPI/jobs-report fade's (D776) and base L4's (D781) own entry and exit windows,
2016-2023, bought on the principal's word ("Yes buy the $24 set") to measure what the two frozen lines pay to trade.

Re-buying it costs money, and after the Standard plan lapses (about 2026-10-11) these L1 schemas older than 12 months
cannot be bought at all. The files are read-only on purpose. The manifest with every file's size, cost and sha256 is
committed at `data/fill_cost_quotes_manifest.csv`; the fetcher is `scripts/fetch_fill_cost_quotes.py`. CME's terms
forbid committing or redistributing the files themselves.
"""


def plan_rows() -> list[tuple[str, str, str, str, str]]:
    """(symbol, schema, leg, start_utc, end_utc), one per window and schema."""
    rows = []
    seal = PR.utc(PR.SEAL, 0, 0)
    for sym, leg, v in PR.jobs(PR.windows()):
        for s, e in v:
            if not e < seal:
                raise SystemExit(f"seal: {sym} {leg} {s} reaches 2024")
            for sch in SCHEMAS:
                rows.append((sym, sch, leg, s, e))
    return rows


def et_day(s: str) -> str:
    return pd.Timestamp(s).tz_convert("America/New_York").strftime("%Y-%m-%d")


def rel_path(sym: str, sch: str, leg: str, s: str) -> Path:
    d = et_day(s)
    return Path(f"{sym.split('.')[0]}_{sch}") / d[:4] / f"{d}_{leg}.dbn.zst"


def load_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST.exists():
        return {}
    with open(MANIFEST, encoding="utf-8", newline="") as fh:
        return {r["path"]: r for r in csv.DictReader(fh)}


def write_manifest(done: dict[str, dict[str, str]], new_rows: list[dict[str, str]]) -> None:
    allr = dict(done)
    for r in new_rows:
        allr[r["path"]] = r
    tmp = MANIFEST.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for k in sorted(allr):
            w.writerow(allr[k])
    os.replace(tmp, MANIFEST)


def plan() -> int:
    rows = plan_rows()
    paths = [rel_path(r[0], r[1], r[2], r[3]).as_posix() for r in rows]
    assert len(set(paths)) == len(paths), "two windows share a file path"
    done = load_manifest()
    print(f"{len(rows)} windows planned; {len(done)} already in the manifest; approved USD {APPROVED_USD}, cap USD {CAP_USD}")
    print(pd.DataFrame(rows, columns=["symbol", "schema", "leg", "s", "e"]).groupby(["symbol", "leg", "schema"]).size().to_string())
    return 0


def fetch(accepted: float | None, threads: int = THREADS) -> int:
    import databento as db
    if accepted is None or abs(accepted - APPROVED_USD) > 0.5:
        raise SystemExit(f"refused: pass --i-accept-the-cost {APPROVED_USD:g} (the principal's approval)")
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "DO_NOT_DELETE.md").write_text(DO_NOT_DELETE, encoding="utf-8")
    if LOCK.exists():
        raise SystemExit(f"another downloader holds {LOCK} (pid {LOCK.read_text(encoding='utf-8').strip()}); refusing")
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    try:
        c = db.Historical(PR.api_key())
        done = load_manifest()
        spent = sum(float(r["usd"]) for r in done.values())
        todo = [r for r in plan_rows() if rel_path(r[0], r[1], r[2], r[3]).as_posix() not in done]
        print(f"{len(todo)} windows to fetch; spent so far USD {spent:.2f}", flush=True)
        lock = threading.Lock()
        state = {"spent": spent, "stop": False, "n": 0, "empty": 0}
        new_rows: list[dict[str, str]] = []
        errors: list[str] = []

        def one(r: tuple[str, str, str, str, str]) -> None:
            try:
                _one(r)
            except Exception as ex:  # noqa: BLE001  (printed at once; MAX_ERRORS stops the run so it cannot keep spending)
                msg = f"{r[:3]} {r[3]}: {type(ex).__name__}: {str(ex)[:200]}"
                with lock:
                    errors.append(msg)
                    print("ERROR", msg, flush=True)
                    if len(errors) >= MAX_ERRORS:
                        state["stop"] = True
                        print(f"STOP: {MAX_ERRORS} errors", flush=True)

        def _one(r: tuple[str, str, str, str, str]) -> None:
            sym, sch, leg, s, e = r
            if state["stop"]:
                return
            kw = dict(dataset=DATASET, symbols=[sym], schema=sch, start=s, end=e, stype_in="continuous")
            try:
                usd = float(CW.retry(c.metadata.get_cost, **kw))
            except Exception as ex:  # noqa: BLE001
                if "symbology_invalid_request" in str(ex):
                    with lock:
                        state["empty"] += 1
                    return
                raise
            with lock:
                if state["spent"] + usd > CAP_USD:
                    state["stop"] = True
                    print(f"CAP: {sym} {sch} {leg} {s} would bring the total to USD {state['spent'] + usd:.2f}; stopping", flush=True)
                    return
                state["spent"] += usd                        # reserve before fetching
            rel = rel_path(sym, sch, leg, s)
            out = DEST / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".part")
            if not out.exists():
                store = CW.retry(c.timeseries.get_range, **kw)     # in memory: no open handle on Windows
                tmp.unlink(missing_ok=True)
                store.to_file(str(tmp))
                del store
                CW.count_records(tmp, s, e)
                os.replace(tmp, out)
                os.chmod(out, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
            recs = CW.count_records(out, s, e)
            row = {"path": rel.as_posix(), "symbol": sym, "schema": sch, "leg": leg, "day": et_day(s), "start_utc": s,
                   "end_utc": e, "bytes": str(out.stat().st_size), "usd": f"{usd:.6f}", "records": str(recs),
                   "sha256": CW.sha256(out), "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
            with lock:
                new_rows.append(row)
                state["n"] += 1
                if state["n"] % 200 == 0:
                    print(f"  {state['n']} fetched, USD {state['spent']:.2f}", flush=True)
                    write_manifest(done, new_rows)

        with ThreadPoolExecutor(threads) as ex:
            list(ex.map(one, todo))
        write_manifest(done, new_rows)
        print(f"done: {state['n']} files, {state['empty']} windows with no session, {len(errors)} errors, total USD "
              f"{state['spent']:.2f} (reserved, including any failed windows){' (STOPPED)' if state['stop'] else ''}", flush=True)
        return 2 if (state["stop"] or errors) else 0
    finally:
        LOCK.unlink(missing_ok=True)


def verify() -> int:
    done = load_manifest()
    bad = 0
    for k, r in done.items():
        p = DEST / k
        if not p.exists() or str(p.stat().st_size) != r["bytes"] or CW.sha256(p) != r["sha256"]:
            bad += 1
            print(f"MISMATCH {k}")
        elif os.access(p, os.W_OK):
            print(f"not read-only: {k}")
    df = pd.DataFrame(done.values())
    if len(df):
        df["usd"] = df["usd"].astype(float)
        print(df.groupby(["symbol", "leg", "schema"]).agg(files=("path", "size"), usd=("usd", "sum")).to_string())
    print(f"{len(done)} files, USD {df['usd'].sum() if len(df) else 0:.2f}, {bad} mismatches")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true")
    g.add_argument("--fetch", action="store_true")
    g.add_argument("--verify", action="store_true")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    ap.add_argument("--threads", type=int, default=THREADS)
    a = ap.parse_args()
    if a.plan:
        return plan()
    if a.fetch:
        return fetch(a.i_accept_the_cost, a.threads)
    return verify()


if __name__ == "__main__":
    sys.exit(main())
