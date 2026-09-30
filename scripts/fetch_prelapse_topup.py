"""The pre-lapse forward top-up: every on-disk Databento archive extended from its end (2026-09-11) to the latest
available date, while the CME Standard subscription still makes it USD 0.00 (lapse ~2026-10-11). On the principal's
word of 2026-09-27 (the pre-lapse sweep: "Top-ups, no MBO (~3 GB)" and "MBO top-up (~28 GB+)"). Scheduled to run on
2026-10-09 so it reaches as close to the lapse as possible.

    python scripts/fetch_prelapse_topup.py --submit                 # SYSTEM interpreter; batch jobs, recorded
    python scripts/fetch_prelapse_topup.py --download [--wait]

Every job is RE-QUOTED immediately before submission and refused unless USD 0.00. Downloading is not reading: the
CL/NG/HO/RB sessions from 2026-09-19 stay unread until D626's read (2026-10-10), and every vault rule still applies to
whoever builds from these files. Raw goes to data/raw/databento/<job id>/; the record is
data/prelapse_topup_jobs.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
import databento_download as DL  # noqa: E402  (the hang-proof per-file downloader, 2026-09-28)

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
JOBS = REPO / "data" / "prelapse_topup_jobs.json"
DATASET = "GLBX.MDP3"
START = "2026-09-11"
# ohlcv-1m's archive ends 2026-09-10T00:00Z (last file 20260609-20260909), so its top-up starts a day earlier to
# cover session 2026-09-10 (docs/internal/JOINT_RUN_CHECKLIST.md s.1). Every other job starts at START.
JOB_START = {"ohlcv-1m all symbols": "2026-09-10"}
ROOTS_41 = ["ES", "NQ", "RTY", "YM", "MES", "MNQ", "M2K", "MYM", "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
            "SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA", "6E", "6J", "6B", "6A", "6C", "6S",
            "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT"]
ROOTS_8 = ["ES", "NQ", "RTY", "YM", "CL", "GC", "ZN", "ZB"]
ES_OPT = [f"{p}.OPT" for p in ["ES", "EW", "EW1", "EW2", "EW3", "EW4"]
          + [f"E{i}{d}" for d in "ABCD" for i in range(1, 6) if f"E{i}{d}" != "E5A"]]
PLAN = [  # (label, symbols, stype_in, schema)
    ("ohlcv-1m all symbols", "ALL_SYMBOLS", "raw_symbol", "ohlcv-1m"),
    ("tbbo all symbols", "ALL_SYMBOLS", "raw_symbol", "tbbo"),
    ("statistics 41 roots", [f"{r}.FUT" for r in ROOTS_41], "parent", "statistics"),
    ("definition 41 roots", [f"{r}.FUT" for r in ROOTS_41], "parent", "definition"),
    ("statistics ES options", ES_OPT, "parent", "statistics"),
    ("definition ES options", ES_OPT, "parent", "definition"),
    ("mbo 8 roots", [f"{r}.FUT" for r in ROOTS_8], "parent", "mbo"),
]


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def submit() -> int:
    import databento as db

    if JOBS.exists():
        raise SystemExit(f"{JOBS.name} exists; do NOT resubmit. Use --download.")
    c = db.Historical(api_key())
    rng = c.metadata.get_dataset_range(dataset=DATASET)
    end = str(rng["end"])[:10] if isinstance(rng, dict) else str(rng.end)[:10]
    rec: dict = {"instruction": "the principal, 2026-09-27: pre-lapse top-ups approved, MBO included",
                 "start": START, "end": end, "submitted_utc": now(), "jobs": []}
    for label, syms, stype, schema in PLAN:
        start = JOB_START.get(label, START)
        kw = dict(dataset=DATASET, symbols=syms, schema=schema, start=start, end=end, stype_in=stype)
        usd = float(c.metadata.get_cost(**kw))
        gb = c.metadata.get_billable_size(**kw) / 1e9
        if usd != 0.0:
            print(f"  REFUSED {label}: now quotes USD {usd:.2f} (the subscription may have lapsed); not submitted",
                  flush=True)
            rec["jobs"].append({"label": label, "refused_usd": usd})
            continue
        job = c.batch.submit_job(**kw, encoding="dbn", compression="zstd", split_duration="day",
                                 stype_out="instrument_id", delivery="download")
        rec["jobs"].append({"label": label, "schema": schema, "start": start, "billable_gb": round(gb, 2), "requoted_usd": usd,
                            "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
                                    for k, v in job.items()}})
        print(f"  submitted {label} {start}..{end}: {gb:.2f} GB billable, job {job.get('id')}", flush=True)
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
    JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def download(wait: bool) -> int:
    import databento as db

    c = db.Historical(api_key())
    rec = json.loads(JOBS.read_text(encoding="utf-8"))
    while True:
        live = {j["id"]: j for j in c.batch.list_jobs(states="queued,processing,done,expired")}
        pending = 0
        for j in rec["jobs"]:
            if "job" not in j or "downloaded_utc" in j:
                continue
            jid = j["job"]["id"]
            state = live.get(jid, {}).get("state", "unknown")
            j["job"]["state"] = state
            if state != "done":
                print(f"  {j['label']} job {jid}: {state}", flush=True)
                pending += 1
                continue
            summ = DL.download_job(c, api_key(), jid, RAW)
            j["download"] = summ
            if summ["verified"] == summ["files"]:
                j["downloaded_utc"] = now()
                j["files"], j["bytes"] = summ["files"], summ["bytes"]
            else:
                pending += 1  # an abandoned file: the next pass resumes it
            print(f"  {j['label']} job {jid}: {summ['verified']}/{summ['files']} files verified, "
                  f"{summ['bytes'] / 1e9:.2f} GB", flush=True)
            JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
        if not pending or not wait:
            return 3 if pending else 0
        time.sleep(120)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--wait", action="store_true")
    a = ap.parse_args()
    sys.exit(submit() if a.submit else download(a.wait) if a.download else 1)
