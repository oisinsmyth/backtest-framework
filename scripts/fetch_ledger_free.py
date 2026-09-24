"""The settlement ledger's FREE data (AITODO 4 and 6, the principal's word 2026-09-24: "go for the free data pulls").

Two sources, neither of which costs anything beyond subscriptions already paid:

  * Databento GLBX.MDP3 under the CME Standard subscription (full history for L0 schemas, the last 12 months for
    L1). Jobs:
      - `ohlcv-1s` for CL and NG, 2017-05-21 → 2026-09-19. Signed window flow is ESTIMATED from these one-second
        bars, because aggressor-marked trades before 2025-09 are billed.
      - `ohlcv-1s` for the TAS roots CLT and NGT, over the same span.
      - `trades` for CL, NG, CLT and NGT from 2026-09-19. This is the free last-12-months window AFTER the vault,
        so it is outside both the in-sample and the vault. It is the ground truth that the one-second estimate is
        validated against.
    Every job is re-quoted at submit time, and the script REFUSES unless the total is exactly USD 0.00.
  * Alpha Vantage `TIME_SERIES_INTRADAY` 1-minute bars for BOIL, KOLD, UCO, SCO, UNG and USO, 2017-05 → 2026-09, on
    the principal's paid key. The repo's `fetch_etf_intraday.py` supplies the slice fetcher, the structural error
    check and the rate limiter, with its interval set to 1min. Slices are cached under
    `data/raw/alphavantage/1min/<SYM>/<YYYY-MM>.json.gz` and never re-fetched.

The vault months (2025-03 → 2026-09-18) are downloaded but not read. The seal is the loader's, `reserved_from=
"2025-03-01"` (amendment A6). Raw data goes to data/raw/ (a gitignored cache). The job record is
data/ledger_free_pull_jobs.json. The keys are never printed.

    python scripts/fetch_ledger_free.py --plan                          # quote only, nothing sent
    python scripts/fetch_ledger_free.py --submit --i-accept-the-cost 0.00
    python scripts/fetch_ledger_free.py --download --wait               # one downloader; lock-guarded
    uv run python scripts/fetch_ledger_free.py --alphavantage           # the ETF 1-minute slices, resumable
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
import urllib.error
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
JOBS = REPO / "data" / "ledger_free_pull_jobs.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
DATASET = "GLBX.MDP3"
SPAN = ("2017-05-21", "2026-09-19")
POST_VAULT = ("2026-09-19", "2026-09-24")
PLAN: list[tuple[str, str, list[str], tuple[str, str]]] = [
    ("ohlcv1s-CL", "ohlcv-1s", ["CL.FUT"], SPAN),
    ("ohlcv1s-NG", "ohlcv-1s", ["NG.FUT"], SPAN),
    ("ohlcv1s-TAS", "ohlcv-1s", ["CLT.FUT", "NGT.FUT"], SPAN),
    ("trades-post-vault", "trades", ["CL.FUT", "NG.FUT", "CLT.FUT", "NGT.FUT"], POST_VAULT),
]
ETFS = ("BOIL", "KOLD", "UCO", "SCO", "UNG", "USO")
AV_MONTHS = ("2017-05", "2026-09")


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def quotes(c: Any) -> list[dict[str, Any]]:
    out = []
    for label, schema, syms, (a, b) in PLAN:
        kw = {"dataset": DATASET, "symbols": syms, "schema": schema, "start": a, "end": b, "stype_in": "parent"}
        out.append({"label": label, "schema": schema, "symbols": syms, "start": a, "end": b,
                    "billable_gb": round(c.metadata.get_billable_size(**kw) / 1e9, 3),
                    "usd": float(c.metadata.get_cost(**kw))})
    return out


def plan() -> int:
    import databento as db
    for q in quotes(db.Historical(api_key())):
        print(f"  {q['label']:18s} {q['schema']:9s} {q['start']} -> {q['end']}  {q['billable_gb']:9.3f} GB  USD {q['usd']:.2f}")
    return 0


def submit(accepted: float | None) -> int:
    import databento as db
    c = db.Historical(api_key())
    qs = quotes(c)
    total = sum(q["usd"] for q in qs)
    if total != 0.0:
        raise SystemExit(f"REFUSING TO SPEND: the jobs quote USD {total:.4f} now; this script submits only free data")
    if accepted is None or abs(accepted - total) > 0.005:
        raise SystemExit("REFUSING: pass --i-accept-the-cost 0.00 (the quoted figure)")
    if JOBS.exists():
        raise SystemExit(f"{JOBS.name} exists; do NOT resubmit. Use --download.")
    rec: dict[str, Any] = {"submitted_utc": now(), "quotes": qs, "paid_schemas_submitted": [], "jobs": []}
    for q in qs:
        job = c.batch.submit_job(dataset=DATASET, symbols=q["symbols"], schema=q["schema"], start=q["start"],
                                 end=q["end"], encoding="dbn", compression="zstd", split_duration="year",
                                 stype_in="parent", stype_out="instrument_id", delivery="download")
        rec["jobs"].append({"label": q["label"], "schema": q["schema"], "accepted_usd": q["usd"],
                            "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
                                    for k, v in job.items()}})
        print(f"  submitted {q['label']} {q['schema']}: job {job.get('id')} state {job.get('state')} USD {q['usd']:.2f}",
              flush=True)
    JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


LOCK = RAW / ".fetch_ledger_free.download.lock"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def download(wait: bool) -> int:
    """One downloader at a time (two pollers on one batch zip corrupted a 13 GB download on 2026-09-22)."""
    import databento as db
    RAW.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        holder = LOCK.read_text(encoding="utf-8").strip()
        if holder.isdigit() and _pid_alive(int(holder)):
            raise SystemExit(f"REFUSING: another --download is running (pid {holder}). Stop it first.")
    LOCK.write_text(str(os.getpid()), encoding="utf-8")
    c = db.Historical(api_key())
    rec = json.loads(JOBS.read_text(encoding="utf-8"))
    while True:
        live = {j["id"]: j for j in c.batch.list_jobs(states="queued,processing,done,expired")}
        pending = 0
        for j in rec["jobs"]:
            jid = j["job"]["id"]
            state = live.get(jid, {}).get("state", "unknown")
            j["job"]["state"] = state
            out = RAW / jid
            if state != "done":
                print(f"  {now()} {j['label']} job {jid}: {state}", flush=True)
                pending += 1
                continue
            if "bytes" in j and out.exists():
                continue
            t0 = time.time()
            paths = c.batch.download(job_id=jid, output_dir=RAW)
            j["downloaded_utc"] = now()
            j["files"] = len(paths)
            j["bytes"] = int(sum(Path(p).stat().st_size for p in paths))
            print(f"  {now()} {j['label']} job {jid}: {len(paths)} files, {j['bytes'] / 1e9:.2f} GB in "
                  f"{(time.time() - t0) / 60:.1f} min", flush=True)
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
        if not pending or not wait:
            LOCK.unlink(missing_ok=True)
            print("  all jobs on disk" if not pending else f"  {pending} job(s) still pending", flush=True)
            return 3 if pending else 0
        time.sleep(60)


def alphavantage() -> int:
    spec = importlib.util.spec_from_file_location("fetch_etf_intraday", REPO / "scripts" / "fetch_etf_intraday.py")
    assert spec is not None and spec.loader is not None
    av = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(av)
    setattr(av, "INTERVAL", "1min")  # noqa: B010 -- fetch_slice and slice_path read it at call time
    key = av.api_key()
    limiter = av.RateLimiter(av.MIN_INTERVAL)
    todo = [(s, m) for s in ETFS for m in av.months(*AV_MONTHS) if not av.slice_path(s, m).exists()]
    print(f"{len(todo)} slices to fetch at {av.REQUESTS_PER_MIN}/min, ETA {len(todo) * av.MIN_INTERVAL / 60:.1f} min",
          flush=True)
    import gzip
    fails = 0
    for i, (sym, month) in enumerate(todo, 1):
        path = av.slice_path(sym, month)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload = av.fetch_slice(sym, month, key, limiter)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            fails += 1
            print(f"  [{i}/{len(todo)}] {sym} {month}: FAILED {str(exc)[:120]}", flush=True)
            if fails >= av.MAX_CONSECUTIVE_FAILURES:
                raise SystemExit("stopping: consecutive failures") from exc
            time.sleep(min(60.0 * fails, 300.0))
            continue
        fails = 0
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(payload, fh)
        if i % 50 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] {sym} {month}: {len(av.series_of(payload)):,} bars", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--alphavantage", action="store_true")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    a = ap.parse_args(argv)
    if a.plan:
        return plan()
    if a.submit:
        return submit(a.i_accept_the_cost)
    if a.download:
        return download(a.wait)
    if a.alphavantage:
        return alphavantage()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
