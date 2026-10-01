"""The pre-lapse gap pulls: the four $0.00 pulls the 2026-10-09 top-up does not carry, approved by the principal on
2026-10-01 (all of A, B, C and D; quotes in data/prelapse_gap_quote.json). The CME Standard subscription lapses
around 2026-10-11, after which every one of them is billed.

    python scripts/fetch_prelapse_gaps.py --submit                       # SYSTEM interpreter; batch jobs, recorded
    python scripts/fetch_prelapse_gaps.py --download --only A,B,C [--wait]
    python scripts/fetch_prelapse_gaps.py --download --only D [--wait]   # AFTER the 2026-10-09 top-up has downloaded
    python scripts/fetch_prelapse_gaps.py --submit-c2                    # 2026-10-10: C again, 10-01 -> the lapse
    python scripts/fetch_prelapse_gaps.py --download --only C2 [--wait]

A  ohlcv-1s, NQ ES YM RTY MNQ MES MYM M2K (parents), 2010-06-06 -> end
B  statistics + definition, MGC MCL SIL MHG M6E (parents), 2010-06-06 -> end
C  continuity top-ups from where each on-disk archive ends: status and bbo-1m on the 41 roots (2026-09-11 ->), NQ and
   CL/NG options statistics + definition (2026-09-27 ->)
D  mbo, MNQ MES MYM M2K (parents), 2026-09-01 -> end (the last free month)

D is submitted with the rest, so it is created at USD 0.00 while the subscription holds, but downloaded only after
the 10-09 top-up: that job refuses to start below 90 GB free, and D is ~25-30 GB on disk. A completed job stays
downloadable for about 30 days. Every job is re-quoted immediately before submission and refused unless USD 0.00.
Downloading is not reading: every seal (the joint vault 2025-03-01 -> 2026-09-18; NQ/ES/YM 2024+ for D716 and D737;
CL/NG/HO/RB from 2026-09-19 until D626's read on 2026-10-10) binds whoever builds from these files. Raw goes to
data/raw/databento/<job id>/; the record is data/prelapse_gap_jobs.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import databento_download as DL  # noqa: E402
import fetch_prelapse_topup as TU  # noqa: E402  (api_key, ROOTS_41; importing defines, never runs)

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
JOBS = REPO / "data" / "prelapse_gap_jobs.json"
DATASET = "GLBX.MDP3"
IDX = ["NQ", "ES", "YM", "RTY", "MNQ", "MES", "MYM", "M2K"]
MICROS_OUT = ["MGC", "MCL", "SIL", "MHG", "M6E"]
NQ_OPT = ([f"{p}.OPT" for p in ["NQ", "QN1", "QN2", "QN3", "QN4", "QNE", "Q2A", "Q3A"]]
          + [f"Q{i}{d}.OPT" for d in "BCD" for i in range(1, 5)])
CLNG_OPT = ["LO.OPT"] + [f"LO{i}.OPT" for i in range(1, 6)] + ["ON.OPT"] + [f"ON{i}.OPT" for i in range(1, 6)] + \
           ["LN1.OPT", "LN2.OPT", "LN3.OPT"]
PLAN = [  # (group, label, symbols, schema, start, split)
    ("A", "ohlcv-1s index + micro parents", [f"{r}.FUT" for r in IDX], "ohlcv-1s", "2010-06-06", "month"),
    ("B", "statistics micros outside the 41", [f"{r}.FUT" for r in MICROS_OUT], "statistics", "2010-06-06", "month"),
    ("B", "definition micros outside the 41", [f"{r}.FUT" for r in MICROS_OUT], "definition", "2010-06-06", "month"),
    ("C", "status 41 roots top-up", [f"{r}.FUT" for r in TU.ROOTS_41], "status", "2026-09-11", "day"),
    ("C", "bbo-1m 41 roots top-up", [f"{r}.FUT" for r in TU.ROOTS_41], "bbo-1m", "2026-09-11", "day"),
    ("C", "statistics NQ options top-up", NQ_OPT, "statistics", "2026-09-27", "day"),
    ("C", "definition NQ options top-up", NQ_OPT, "definition", "2026-09-27", "day"),
    ("C", "statistics CL/NG options top-up", CLNG_OPT, "statistics", "2026-09-27", "day"),
    ("C", "definition CL/NG options top-up", CLNG_OPT, "definition", "2026-09-27", "day"),
    ("D", "mbo micro index parents, last free month", [f"{r}.FUT" for r in ["MNQ", "MES", "MYM", "M2K"]], "mbo",
     "2026-09-01", "day"),
]


C2_START = "2026-10-01"  # C's first jobs end where the dataset ended on 2026-10-01; C2 carries them to the lapse


def submit_c2() -> int:
    """C's continuity top-ups again, from 2026-10-01 to the dataset's end, appended to the record as group C2.
    Run once, on 2026-10-10 (before the lapse); re-quoted and refused unless USD 0.00."""
    import databento as db
    rec = json.loads(JOBS.read_text(encoding="utf-8"))
    if any(j.get("group") == "C2" for j in rec["jobs"]):
        raise SystemExit("C2 already submitted; use --download --only C2")
    c = db.Historical(TU.api_key())
    rng = c.metadata.get_dataset_range(dataset=DATASET)
    end = str(rng["end"])[:10] if isinstance(rng, dict) else str(rng.end)[:10]
    for group, label, syms, schema, _start, _split in PLAN:
        if group != "C":
            continue
        kw = dict(dataset=DATASET, symbols=syms, schema=schema, start=C2_START, end=end, stype_in="parent")
        usd = float(c.metadata.get_cost(**kw))
        if usd != 0.0:
            print(f"  REFUSED C2 {label}: now quotes USD {usd:.2f}; not submitted", flush=True)
            rec["jobs"].append({"group": "C2", "label": label, "refused_usd": usd})
            write(rec)
            continue
        job = c.batch.submit_job(**kw, encoding="dbn", compression="zstd", split_duration="day",
                                 stype_out="instrument_id", delivery="download")
        rec["jobs"].append({"group": "C2", "label": label, "schema": schema, "start": C2_START, "split": "day",
                            "requoted_usd": usd, "submitted_utc": now(),
                            "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
                                    for k, v in job.items()}})
        print(f"  submitted [C2] {label} {C2_START}..{end}, job {job.get('id')}", flush=True)
        write(rec)
    return 0


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write(rec: dict) -> None:
    JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")


def submit() -> int:
    import databento as db
    if JOBS.exists():
        raise SystemExit(f"{JOBS.name} exists; do NOT resubmit. Use --download.")
    c = db.Historical(TU.api_key())
    rng = c.metadata.get_dataset_range(dataset=DATASET)
    end = str(rng["end"])[:10] if isinstance(rng, dict) else str(rng.end)[:10]
    rec: dict = {"instruction": 'the principal, 2026-10-01: pre-lapse gap pulls A, B, C and D approved',
                 "end": end, "submitted_utc": now(), "jobs": []}
    for group, label, syms, schema, start, split in PLAN:
        kw = dict(dataset=DATASET, symbols=syms, schema=schema, start=start, end=end, stype_in="parent")
        usd = float(c.metadata.get_cost(**kw))
        gb = c.metadata.get_billable_size(**kw) / 1e9
        if usd != 0.0:
            print(f"  REFUSED {label}: now quotes USD {usd:.2f}; not submitted", flush=True)
            rec["jobs"].append({"group": group, "label": label, "refused_usd": usd})
            write(rec)
            continue
        job = c.batch.submit_job(**kw, encoding="dbn", compression="zstd", split_duration=split,
                                 stype_out="instrument_id", delivery="download")
        rec["jobs"].append({"group": group, "label": label, "schema": schema, "start": start, "split": split,
                            "billable_gb": round(gb, 2), "requoted_usd": usd,
                            "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
                                    for k, v in job.items()}})
        print(f"  submitted [{group}] {label} {start}..{end}: {gb:.2f} GB billable, job {job.get('id')}", flush=True)
        write(rec)
    return 0


def download(only: set[str], wait: bool) -> int:
    import databento as db
    c = db.Historical(TU.api_key())
    rec = json.loads(JOBS.read_text(encoding="utf-8"))
    while True:
        live = {j["id"]: j for j in c.batch.list_jobs(states="queued,processing,done,expired")}
        pending = 0
        for j in rec["jobs"]:
            if j.get("group") not in only or "job" not in j or "downloaded_utc" in j:
                continue
            jid = j["job"]["id"]
            state = live.get(jid, {}).get("state", "unknown")
            j["job"]["state"] = state
            if state != "done":
                print(f"  [{j['group']}] {j['label']} job {jid}: {state}", flush=True)
                pending += 1
                continue
            summ = DL.download_job(c, TU.api_key(), jid, RAW)
            j["download"] = summ
            if summ["verified"] == summ["files"]:
                j["downloaded_utc"] = now()
                j["files"], j["bytes"] = summ["files"], summ["bytes"]
            else:
                pending += 1
            print(f"  [{j['group']}] {j['label']} job {jid}: {summ['verified']}/{summ['files']} files verified, "
                  f"{summ['bytes'] / 1e9:.2f} GB", flush=True)
            write(rec)
        write(rec)
        if not pending or not wait:
            return 3 if pending else 0
        time.sleep(120)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--submit-c2", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--only", default="A,B,C")
    ap.add_argument("--wait", action="store_true")
    a = ap.parse_args()
    sys.exit(submit() if a.submit else submit_c2() if a.submit_c2 else
             download(set(a.only.split(",")), a.wait) if a.download else 1)
