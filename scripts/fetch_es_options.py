"""D581 section 0 -- the ES option family's `statistics` (open interest, settlements) and `definition` (strike, expiry,
right) history from Databento GLBX.MDP3, on the principal's word of 2026-09-20. Quoted first by
scripts/quote_es_options_pull.py: 47.69 GB, USD 0.00 under the subscription.

    python scripts/fetch_es_options.py --submit --i-accept-the-cost 0.00    # SYSTEM interpreter; two batch jobs, recorded
    python scripts/fetch_es_options.py --download [--wait]                  # poll; download into data/raw/databento/<job id>/

Batch jobs, never streaming (billed once, re-downloadable free for 30 days). The key is the principal's and is never
printed. Raw goes to data/raw/ (gitignored cache, D191); the job record is tracked at data/es_options_pull_jobs.json.
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
DATASET = "GLBX.MDP3"; STYPE_IN = "parent"; START = "2016-01-01"; END = "2026-09-11"; SCHEMAS = ("statistics", "definition")
# Two symbol sets, two job records: `ES.OPT` is the quarterly family alone; the weeklies and dailies are their own parents (see quote_es_options_pull.py).
WEEKLY_FAMILIES = ["EW", "EW1", "EW2", "EW3", "EW4"] + [f"E{i}{l}" for l in "ABCD" for i in range(1, 6) if f"E{i}{l}" != "E5A"]
if "--weeklies" in sys.argv:
    SYMBOLS = [f"{f}.OPT" for f in WEEKLY_FAMILIES]; JOBS = REPO / "data" / "es_options_pull_jobs_weeklies.json"; QUOTE = REPO / "data" / "es_options_pull_quote_weeklies.json"
else:
    SYMBOLS = ["ES.OPT"]; JOBS = REPO / "data" / "es_options_pull_jobs.json"; QUOTE = REPO / "data" / "es_options_pull_quote.json"


def api_key():
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def submit(accepted):
    import databento as db
    q = json.loads(QUOTE.read_text(encoding="utf-8"))
    if accepted is None or abs(accepted - q["total_usd"]) > 0.005:
        raise SystemExit(f"REFUSING TO SPEND: pass --i-accept-the-cost {q['total_usd']:.2f} (the quoted figure)")
    if JOBS.exists():
        raise SystemExit(f"{JOBS.name} exists; do NOT resubmit. Use --download.")
    c = db.Historical(api_key()); rec = {"quote": q, "submitted_utc": now(), "jobs": []}
    # the weeklies' statistics are 268 GB billable: split into three family groups so Databento processes them in parallel and the download starts on the first
    groups = {"statistics": [SYMBOLS], "definition": [SYMBOLS]}
    if "--weeklies" in sys.argv:
        groups["statistics"] = [[s for s in SYMBOLS if s.startswith("EW")], [s for s in SYMBOLS if s[0] == "E" and s[2] in "AB"], [s for s in SYMBOLS if s[0] == "E" and s[2] in "CD"]]
    for schema in SCHEMAS:
        for syms in groups[schema]:
            job = c.batch.submit_job(dataset=DATASET, symbols=syms, schema=schema, start=START, end=END, encoding="dbn", compression="zstd",
                                     split_duration="year", stype_in=STYPE_IN, stype_out="instrument_id", delivery="download")
            rec["jobs"].append({"schema": schema, "symbols": syms, "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v)) for k, v in job.items()}, "accepted_usd": q["schemas"][schema]["usd"] / len(groups[schema])})
            print(f"  submitted {schema} {syms[:3]}{'...' if len(syms) > 3 else ''}: job {job.get('id')} state {job.get('state')} quoted USD {q['schemas'][schema]['usd']:.2f} for the schema")
    JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8"); return 0


def download(wait):
    import databento as db
    c = db.Historical(api_key()); rec = json.loads(JOBS.read_text(encoding="utf-8"))
    while True:
        live = {j["id"]: j for j in c.batch.list_jobs(states="queued,processing,done,expired")}; pending = 0
        for j in rec["jobs"]:
            jid = j["job"]["id"]; state = live.get(jid, {}).get("state", "unknown"); j["job"]["state"] = state; out = RAW / jid
            if state != "done":
                print(f"  {j['schema']} job {jid}: {state}", flush=True); pending += 1; continue
            if out.exists() and any(out.glob("*.dbn.zst")):
                print(f"  {j['schema']} job {jid}: on disk ({len(list(out.glob('*.dbn.zst')))} files)"); continue
            out.mkdir(parents=True, exist_ok=True); t0 = time.time(); paths = c.batch.download(job_id=jid, output_dir=RAW)
            j["downloaded_utc"] = now(); j["files"] = len(paths); j["bytes"] = int(sum(Path(p).stat().st_size for p in paths))
            print(f"  {j['schema']} job {jid}: downloaded {len(paths)} files, {j['bytes']/1e9:.2f} GB in {(time.time()-t0)/60:.1f} min -> {out}", flush=True)
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        if not pending or not wait:
            return 3 if pending else 0
        time.sleep(60)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--submit", action="store_true"); ap.add_argument("--download", action="store_true"); ap.add_argument("--wait", action="store_true"); ap.add_argument("--weeklies", action="store_true"); ap.add_argument("--i-accept-the-cost", type=float, default=None)
    a = ap.parse_args(); sys.exit(submit(a.i_accept_the_cost) if a.submit else download(a.wait) if a.download else 1)
