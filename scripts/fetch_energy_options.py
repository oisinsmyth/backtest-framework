"""D619's census, acted on -- the CL/NG option families' `definition` and `statistics` history and the
TAS roots' free `definition` and `statistics` from Databento GLBX.MDP3, on the principal's word of
2026-09-22 ("delay the paid data, do the other free download now"). Quoted first by
scripts/quote_energy_options_pull.py: options 178.21 GB at USD 0.00 across fifteen resolved parents
(LO, LO1-LO5, ON, ON1-ON5, LN1-LN3; CL.OPT and NG.OPT do not exist), TAS definition + statistics
0.56 GB at USD 0.00. **The TAS `trades` schema (USD 3.17) is NOT submitted here** -- it is the one
paid line and the principal deferred it; `--tas-trades` is deliberately absent.

    python scripts/fetch_energy_options.py --submit --i-accept-the-cost 0.00    # SYSTEM interpreter; five batch jobs, recorded
    python scripts/fetch_energy_options.py --download [--wait]                  # poll; download into data/raw/databento/<job id>/

Batch jobs, never streaming (billed once, re-downloadable free for 30 days). The key is the
principal's and is never printed. Raw goes to data/raw/ (gitignored cache, D191); the job record is
tracked at data/energy_options_pull_jobs.json. The spend guard is `fetch_es_options.py`'s: the
accepted figure must equal the quoted total of the schemas submitted, to the cent, and here that
total is asserted to be exactly zero before anything is sent.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
QUOTE = REPO / "data" / "energy_options_pull_quote.json"
JOBS = REPO / "data" / "energy_options_pull_jobs.json"
DATASET = "GLBX.MDP3"
STYPE_IN = "parent"
START = "2016-01-01"
END = "2026-09-11"
FREE_SCHEMAS = ("definition", "statistics")  # `trades` is the paid TAS line and is not here


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sections() -> tuple[dict, dict]:
    q = json.loads(QUOTE.read_text(encoding="utf-8"))
    opt = next(v for v in q.values() if isinstance(v, dict) and "LO.OPT" in v.get("symbols", []))
    tas = q["tas"]
    assert "CLT.FUT" in tas["symbols"] and "NGT.FUT" in tas["symbols"], tas["symbols"]
    return opt, tas


def planned() -> list[tuple[str, str, list[str], float]]:
    """(label, schema, symbols, quoted usd) for every job this script may submit. Nothing paid."""
    opt, tas = sections()
    by_family = {
        "LO": [s for s in opt["symbols"] if s.startswith("LO")],
        "ON": [s for s in opt["symbols"] if s.startswith("ON")],
        "LN": [s for s in opt["symbols"] if s.startswith("LN")],
    }
    assert sorted(sum(by_family.values(), [])) == sorted(opt["symbols"]), "a parent fell outside the three families"
    plan: list[tuple[str, str, list[str], float]] = []
    # statistics is 117.76 GB billable: one job per family so Databento processes them in parallel
    for fam, syms in by_family.items():
        plan.append((f"options-{fam}", "statistics", syms, opt["schemas"]["statistics"]["usd"] / 3))
    plan.append(("options", "definition", list(opt["symbols"]), opt["schemas"]["definition"]["usd"]))
    for schema in FREE_SCHEMAS:
        plan.append(("tas", schema, list(tas["symbols"]), tas["schemas"][schema]["usd"]))
    return plan


def submit(accepted: float | None) -> int:
    import databento as db

    plan = planned()
    total = sum(p[3] for p in plan)
    if total != 0.0:
        raise SystemExit(f"REFUSING TO SPEND: the planned jobs quote USD {total:.4f}, and this script submits only free schemas")
    if accepted is None or abs(accepted - total) > 0.005:
        raise SystemExit(f"REFUSING TO SPEND: pass --i-accept-the-cost {total:.2f} (the quoted figure)")
    if JOBS.exists():
        raise SystemExit(f"{JOBS.name} exists; do NOT resubmit. Use --download.")
    c = db.Historical(api_key())
    rec = {"quote_file": QUOTE.name, "submitted_utc": now(), "start": START, "end": END, "paid_schemas_submitted": [], "jobs": []}
    for label, schema, syms, usd in plan:
        job = c.batch.submit_job(
            dataset=DATASET, symbols=syms, schema=schema, start=START, end=END, encoding="dbn",
            compression="zstd", split_duration="year", stype_in=STYPE_IN, stype_out="instrument_id",
            delivery="download",
        )
        rec["jobs"].append({
            "label": label, "schema": schema, "symbols": syms, "accepted_usd": usd,
            "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v)) for k, v in job.items()},
        })
        print(f"  submitted {label} {schema} ({len(syms)} symbols): job {job.get('id')} state {job.get('state')} quoted USD {usd:.2f}", flush=True)
    JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    return 0


LOCK = RAW / ".fetch_energy_options.download.lock"


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _take_lock() -> None:
    """One downloader at a time. Two pollers writing the same batch zip corrupted a 13 GB
    download on 2026-09-22 (BadZipFile at unpack, hours lost); the lock names the PID that holds
    it and refuses while that PID is alive. A dead PID's lock is stale and is taken over."""
    RAW.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        holder = LOCK.read_text(encoding="utf-8").strip()
        if holder.isdigit() and _pid_alive(int(holder)):
            raise SystemExit(f"REFUSING: another --download is running (pid {holder}, {LOCK}). "
                             "Two writers on one batch zip corrupt it. Stop that process first.")
    LOCK.write_text(str(os.getpid()), encoding="utf-8")


def download(wait: bool) -> int:
    import databento as db

    _take_lock()
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
                print(f"  {j['label']} {j['schema']} job {jid}: {state}", flush=True)
                pending += 1
                continue
            if out.exists() and any(out.glob("*.dbn.zst")):
                print(f"  {j['label']} {j['schema']} job {jid}: on disk ({len(list(out.glob('*.dbn.zst')))} files)")
                continue
            out.mkdir(parents=True, exist_ok=True)
            t0 = time.time()
            paths = c.batch.download(job_id=jid, output_dir=RAW)
            j["downloaded_utc"] = now()
            j["files"] = len(paths)
            j["bytes"] = int(sum(Path(p).stat().st_size for p in paths))
            print(f"  {j['label']} {j['schema']} job {jid}: downloaded {len(paths)} files, {j['bytes'] / 1e9:.2f} GB in {(time.time() - t0) / 60:.1f} min -> {out}", flush=True)
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        if not pending or not wait:
            LOCK.unlink(missing_ok=True)
            return 3 if pending else 0
        time.sleep(60)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--plan", action="store_true", help="print the jobs and their quoted cost; sends nothing")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    a = ap.parse_args(argv)
    if a.plan:
        for label, schema, syms, usd in planned():
            print(f"  {label:12s} {schema:11s} {len(syms):2d} symbols  USD {usd:.2f}")
        print(f"  total USD {sum(p[3] for p in planned()):.2f}; paid schemas submitted: none")
        return 0
    if a.submit:
        return submit(a.i_accept_the_cost)
    if a.download:
        return download(a.wait)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
