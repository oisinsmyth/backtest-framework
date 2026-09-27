"""The pre-lapse options pulls: NQ options and CL/NG options, `definition` + `statistics`, 2016-01-01 to the sweep's
available end, on the principal's word of 2026-09-27 (the pre-lapse sweep: "NQ options (~48 GB), CL/NG options
(~25 GB)"). Quoted by scripts/quote_prelapse_sweep.py at USD 0.00 under the CME Standard subscription.

    python scripts/fetch_prelapse_options.py --set nq|energy --submit      # SYSTEM interpreter; batch jobs, recorded
    python scripts/fetch_prelapse_options.py --set nq|energy --download [--wait]

The symbols are the sweep's RESOLVED parents (never written by hand: D581). Every job is RE-QUOTED immediately before
submission and refused unless it is still USD 0.00. Batch jobs, never streaming. The key is never printed. Raw goes to
data/raw/databento/<job id>/ (gitignored cache, D191); the job record is tracked at
data/prelapse_options_pull_jobs_<set>.json.
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
QUOTE = REPO / "data" / "prelapse_sweep_quote.json"
DATASET = "GLBX.MDP3"
START = "2016-01-01"
SCHEMAS = ("statistics", "definition")
BLOCK = {"nq": "nq_options", "energy": "energy_options"}


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def groups(which: str, syms: list[str]) -> list[list[str]]:
    """Statistics is the big schema: split it so Databento processes the parts in parallel."""
    if which == "nq":
        return [[s for s in syms if s.startswith(("NQ", "QN"))], [s for s in syms if s[:1] == "Q" and s[2:3] in "AB"],
                [s for s in syms if s[:1] == "Q" and s[2:3] in "CD"]]
    return [[s for s in syms if s.startswith("LO")], [s for s in syms if not s.startswith("LO")]]


def submit(which: str) -> int:
    import databento as db

    jobs_path = REPO / "data" / f"prelapse_options_pull_jobs_{which}.json"
    if jobs_path.exists():
        raise SystemExit(f"{jobs_path.name} exists; do NOT resubmit. Use --download.")
    q = json.loads(QUOTE.read_text(encoding="utf-8"))
    syms, end = list(q[BLOCK[which]]["resolved"]), q["available_end"]
    parts = {"statistics": [g for g in groups(which, syms) if g], "definition": [syms]}
    assert sorted(s for g in parts["statistics"] for s in g) == sorted(syms), "the statistics groups must tile the set"
    c = db.Historical(api_key())
    rec: dict = {"instruction": "the principal, 2026-09-27: pre-lapse sweep downloads approved", "set": which,
                 "symbols": syms, "start": START, "end": end, "submitted_utc": now(), "jobs": []}
    for schema in SCHEMAS:
        for g in parts[schema]:
            kw = dict(dataset=DATASET, symbols=g, schema=schema, start=START, end=end, stype_in="parent")
            usd = float(c.metadata.get_cost(**kw))
            if usd != 0.0:
                raise SystemExit(f"REFUSING: {schema} {g[:3]} now quotes USD {usd:.2f}, not 0.00")
            job = c.batch.submit_job(**kw, encoding="dbn", compression="zstd", split_duration="year",
                                     stype_out="instrument_id", delivery="download")
            rec["jobs"].append({"schema": schema, "symbols": g, "requoted_usd": usd,
                                "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
                                        for k, v in job.items()}})
            print(f"  submitted {schema} {g[:3]}{'...' if len(g) > 3 else ''}: job {job.get('id')} "
                  f"state {job.get('state')} (re-quoted USD {usd:.2f})", flush=True)
            jobs_path.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def download(which: str, wait: bool) -> int:
    import databento as db

    jobs_path = REPO / "data" / f"prelapse_options_pull_jobs_{which}.json"
    c = db.Historical(api_key())
    rec = json.loads(jobs_path.read_text(encoding="utf-8"))
    while True:
        live = {j["id"]: j for j in c.batch.list_jobs(states="queued,processing,done,expired")}
        pending = 0
        for j in rec["jobs"]:
            jid = j["job"]["id"]
            state = live.get(jid, {}).get("state", "unknown")
            j["job"]["state"] = state
            out = RAW / jid
            if state != "done":
                print(f"  {j['schema']} job {jid}: {state}", flush=True)
                pending += 1
                continue
            if "downloaded_utc" in j:
                continue
            out.mkdir(parents=True, exist_ok=True)
            t0 = time.time()
            paths = c.batch.download(job_id=jid, output_dir=RAW)
            j["downloaded_utc"] = now()
            j["files"] = len(paths)
            j["bytes"] = int(sum(Path(p).stat().st_size for p in paths))
            print(f"  {j['schema']} job {jid}: downloaded {len(paths)} files, {j['bytes'] / 1e9:.2f} GB in "
                  f"{(time.time() - t0) / 60:.1f} min", flush=True)
        jobs_path.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
        if not pending or not wait:
            return 3 if pending else 0
        time.sleep(120)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=sorted(BLOCK), required=True)
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--wait", action="store_true")
    a = ap.parse_args()
    sys.exit(submit(a.set) if a.submit else download(a.set, a.wait) if a.download else 1)
