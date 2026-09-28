"""The exchange-flag check for the opening model's A7 (OA-A3; D645 s.2): Databento `trades` (the exchange's aggressor
side) for ES and NQ on post-vault sessions, 2026-09-19 onward. That is the free last-12-months window under the CME
Standard subscription, and the known answer that Sierra Chart's signed flow is checked against (r >= 0.8 at day
level, as D624 did on HO/RB).

    python scripts/fetch_opening_trades_check.py --quote                           # metadata only, nothing sent
    python scripts/fetch_opening_trades_check.py --submit --i-accept-the-cost 0.00
    python scripts/fetch_opening_trades_check.py --download

Parent symbols (ES.FUT, NQ.FUT): every month and spread, so the front outright is filtered at read time with D520's
windowed ids. It submits only free data (it refuses any non-zero quote). Downloads go through the hang-proof per-file
downloader (`databento_download.py`) into data/raw/databento/<job>/. Job record: data/opening/trades_check_jobs.json.
The key is never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import databento_download as DL  # noqa: E402

KEY_FILE = Path.home() / ".config" / "databento" / "key"
DATASET = "GLBX.MDP3"
SPAN = ("2026-09-19", "2026-09-28")  # end exclusive: the complete post-vault sessions available on 2026-09-28
SYMBOLS = ["ES.FUT", "NQ.FUT"]
JOBS = REPO / "data" / "opening" / "trades_check_jobs.json"


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def quote(c: Any) -> dict[str, Any]:
    kw = {"dataset": DATASET, "symbols": SYMBOLS, "schema": "trades", "start": SPAN[0], "end": SPAN[1],
          "stype_in": "parent"}
    return {"symbols": SYMBOLS, "schema": "trades", "start": SPAN[0], "end": SPAN[1],
            "billable_gb": round(c.metadata.get_billable_size(**kw) / 1e9, 3), "usd": float(c.metadata.get_cost(**kw))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quote", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    a = ap.parse_args()
    import databento as db
    c = db.Historical(api_key())
    if a.quote:
        q = quote(c)
        print(f"trades {SYMBOLS} {SPAN[0]} -> {SPAN[1]} (exclusive): {q['billable_gb']} GB billable, USD {q['usd']:.2f}")
        return 0
    if a.submit:
        q = quote(c)
        if q["usd"] != 0.0:
            raise SystemExit(f"REFUSING TO SPEND: USD {q['usd']:.4f}; this script submits only free data")
        if a.i_accept_the_cost is None or abs(a.i_accept_the_cost - q["usd"]) > 0.005:
            raise SystemExit("REFUSING: pass --i-accept-the-cost 0.00 (the quoted figure)")
        if JOBS.exists():
            raise SystemExit(f"{JOBS.name} exists; do NOT resubmit. Use --download.")
        job = c.batch.submit_job(dataset=DATASET, symbols=SYMBOLS, schema="trades", start=SPAN[0], end=SPAN[1],
                                 encoding="dbn", compression="zstd", split_duration="day", stype_in="parent",
                                 stype_out="instrument_id", delivery="download")
        rec = {"submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "quote": q,
               "job": {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v)) for k, v in job.items()}}
        JOBS.parent.mkdir(parents=True, exist_ok=True)
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"submitted job {job.get('id')} state {job.get('state')}")
        return 0
    if a.download:
        rec = json.loads(JOBS.read_text(encoding="utf-8"))
        jid = rec["job"]["id"]
        while True:
            st = {j["id"]: j["state"] for j in c.batch.list_jobs(states="queued,processing,done,expired")}.get(jid)
            if st == "done":
                break
            print(f"job {jid} state {st}; waiting", flush=True)
            time.sleep(30)
        summ = DL.download_job(c, api_key(), jid, REPO / "data" / "raw" / "databento")
        rec["download"] = summ
        JOBS.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"downloaded {summ['verified']}/{summ['files']} files, {summ['bytes'] / 1e9:.2f} GB")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
