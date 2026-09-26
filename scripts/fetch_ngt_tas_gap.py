"""Buy the one TAS span Sierra Chart lacks: Databento `trades` for NGT.FUT (NG trade-at-settlement, the exchange's
aggressor flag), 2017-05-21 → 2020-02-10 (the principal, 2026-09-26: "Approve the $0.29").

Sierra Chart holds NG TAS from 2020-02-10 on, and its sides equal the exchange flag (`check_sierra_tas_aggressor.py`:
r 0.9998–0.9999 on the HO/RB siblings). Before that date it has no file, and this job fills the gap. It is re-quoted
at submit, and the script REFUSES unless the quote equals the approved figure within half a cent and is below
USD 0.35. The job record is `data/ledger_ngt_tas_gap_job.json`; raw files go to `data/raw/databento/<job id>/`. The
key is never printed.

    python scripts/fetch_ngt_tas_gap.py --plan
    python scripts/fetch_ngt_tas_gap.py --submit --i-accept-the-cost 0.29
    python scripts/fetch_ngt_tas_gap.py --download --wait
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import fetch_ledger_free as F  # noqa: E402  (the key reader, the clock, the one-downloader lock pattern)

JOBS = REPO / "data" / "ledger_ngt_tas_gap_job.json"
SPEC = {"label": "ngt-tas-gap", "schema": "trades", "symbols": ["NGT.FUT"], "start": "2017-05-21",
        "end": "2020-02-11"}
CAP_USD = 0.35


def quote(c: Any) -> dict[str, Any]:
    kw = {"dataset": F.DATASET, "symbols": SPEC["symbols"], "schema": SPEC["schema"], "start": SPEC["start"],
          "end": SPEC["end"], "stype_in": "parent"}
    return {**SPEC, "billable_mb": round(c.metadata.get_billable_size(**kw) / 1e6, 2),
            "usd": float(c.metadata.get_cost(**kw))}


def main(argv: list[str] | None = None) -> int:
    import databento as db  # type: ignore[import-not-found]
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    a = ap.parse_args(argv)
    c = db.Historical(F.api_key())
    if a.plan:
        print(json.dumps(quote(c), indent=1))
        return 0
    if a.submit:
        q = quote(c)
        if q["usd"] >= CAP_USD:
            raise SystemExit(f"REFUSING: the quote is USD {q['usd']:.4f}, at or above the cap {CAP_USD}")
        if a.i_accept_the_cost is None or abs(a.i_accept_the_cost - q["usd"]) > 0.005:
            raise SystemExit(f"REFUSING: the quote is USD {q['usd']:.4f}; pass --i-accept-the-cost with that figure")
        if JOBS.exists():
            raise SystemExit(f"{JOBS.name} exists; do NOT resubmit. Use --download.")
        job = c.batch.submit_job(dataset=F.DATASET, symbols=SPEC["symbols"], schema=SPEC["schema"],
                                 start=SPEC["start"], end=SPEC["end"], encoding="dbn", compression="zstd",
                                 split_duration="year", stype_in="parent", stype_out="instrument_id",
                                 delivery="download")
        rec = {"submitted_utc": F.now(), "approved_by": "the principal, 2026-09-26: 'Approve the $0.29'",
               "quote": q, "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
                                   for k, v in job.items()}}
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"submitted job {job.get('id')} state {job.get('state')} USD {q['usd']:.2f}", flush=True)
        return 0
    if a.download:
        rec = json.loads(JOBS.read_text(encoding="utf-8"))
        jid = rec["job"]["id"]
        while True:
            state = next((j["state"] for j in c.batch.list_jobs(states="queued,processing,done,expired")
                          if j["id"] == jid), "unknown")
            print(f"  {F.now()} job {jid}: {state}", flush=True)
            if state == "done":
                paths = c.batch.download(job_id=jid, output_dir=F.RAW)
                rec["downloaded_utc"] = F.now()
                rec["files"] = [Path(p).name for p in paths]
                rec["bytes"] = int(sum(Path(p).stat().st_size for p in paths))
                JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
                print(f"  downloaded {len(paths)} files, {rec['bytes'] / 1e6:.1f} MB", flush=True)
                return 0
            if not a.wait:
                return 3
            time.sleep(30)
    return 0


if __name__ == "__main__":
    sys.exit(main())
