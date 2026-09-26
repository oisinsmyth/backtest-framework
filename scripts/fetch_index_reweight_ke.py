"""KE (KC HRW wheat) settlements and definitions for the index-reweight model (the principal, 2026-09-27: "Yes,
download"). KE is the one BCOM CME component never bought (it is not in ROOTS_41), and its L0 schemas are $0 only
while the CME Standard subscription lasts (the refetch clock runs to about 2026-10-11).

It reuses `fetch_ledger_free.py`'s quote, spend guard, submit and one-downloader logic, with its own plan and job
record. The script REFUSES unless the jobs quote exactly USD 0.00. Data dated 2025-03-01 or later is downloaded and
never read before the joint vault run (A10). Raw data goes to data/raw/databento/; the job record is
data/index_reweight_ke_jobs.json. The key is never printed.

    python scripts/fetch_index_reweight_ke.py --plan
    python scripts/fetch_index_reweight_ke.py --submit --i-accept-the-cost 0.00
    python scripts/fetch_index_reweight_ke.py --download --wait
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("fetch_ledger_free", REPO / "scripts" / "fetch_ledger_free.py")
assert _s is not None and _s.loader is not None
F = importlib.util.module_from_spec(_s)
sys.modules["fetch_ledger_free"] = F
_s.loader.exec_module(F)

SPAN = ("2010-06-06", "2026-09-26")
F.PLAN = [("statistics-KE", "statistics", ["KE.FUT"], SPAN), ("definition-KE", "definition", ["KE.FUT"], SPAN)]
F.JOBS = REPO / "data" / "index_reweight_ke_jobs.json"
F.LOCK = F.RAW / ".fetch_index_reweight_ke.download.lock"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--wait", action="store_true")
    a = ap.parse_args(argv)
    if a.plan:
        return int(F.plan())
    if a.submit:
        return int(F.submit(a.i_accept_the_cost))
    if a.download:
        return int(F.download(a.wait))
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
