"""Databento `trades` (with the exchange's aggressor flag) for the 15 CME BCOM roots on post-vault sessions, for
D635 §7's per-root check of Sierra Chart's signing (IR-A7; the principal, 2026-09-27: "approve both downloads").

Reuses `fetch_ledger_free.py`'s quote, spend guard (REFUSES unless the jobs quote exactly USD 0.00), submit and
one-downloader logic. Each call is one span; `--start/--end` let later top-ups add sessions (at least 10 per root are
needed). The job record is data/index_reweight/signcheck_jobs_<start>_<end>.json.

CL, NG, HO and RB sessions from 2026-09-19 are D626's sample: downloaded now, never read before its one read on
2026-10-10.

    python scripts/fetch_index_reweight_signcheck.py --plan --start 2026-09-19 --end 2026-09-26
    python scripts/fetch_index_reweight_signcheck.py --submit --i-accept-the-cost 0.00 --start ... --end ...
    python scripts/fetch_index_reweight_signcheck.py --download --wait --start ... --end ...
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

GROUPS = {"energy": ["CL.FUT", "NG.FUT", "HO.FUT", "RB.FUT"], "metals": ["GC.FUT", "SI.FUT", "HG.FUT"],
          "grains": ["ZC.FUT", "ZS.FUT", "ZW.FUT", "KE.FUT", "ZL.FUT", "ZM.FUT"], "livestock": ["LE.FUT", "HE.FUT"]}


def setup(start: str, end: str) -> None:
    if start < "2026-09-19":
        raise SystemExit("the sign check reads post-vault sessions only (from 2026-09-19)")
    F.PLAN = [(f"trades-{g}", "trades", syms, (start, end)) for g, syms in GROUPS.items()]
    F.JOBS = REPO / "data" / "index_reweight" / f"signcheck_jobs_{start}_{end}.json"
    F.LOCK = F.RAW / ".fetch_index_reweight_signcheck.download.lock"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--i-accept-the-cost", type=float, default=None)
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    a = ap.parse_args(argv)
    setup(a.start, a.end)
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
