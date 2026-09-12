"""Wait for the futures acquisition to stop moving, then re-run D448, D449 and D450.

    python scripts/rerun_es_studies_on_completion.py             # wait, then run
    python scripts/rerun_es_studies_on_completion.py --now       # skip the wait
    python scripts/rerun_es_studies_on_completion.py --check     # report state and exit

WHY THIS EXISTS. D450 section 6 records that `temp/databento/` is a LIVE directory: between
D449's build and D450's re-run the acquisition landed a further chunk and the ES panel extended
from 2022-08-16 to 2024-08-28 mid-study. Every ES number in D448, D449 and D450 is therefore a
snapshot of an incomplete acquisition, and the T+1 settlement era -- the one D447 found most
anomalous and the one D448 could not test at all -- is only reachable once the remaining chunks
land.

THE COMPLETION CONDITION, and it deliberately covers FAILURE as well as success:

    no ohlcv-1m item in the manifest is still in state 'submitted'

A job that errors, is cancelled, or is re-split leaves 'submitted' as surely as one that
succeeds, so this fires on every terminal state rather than on the happy path only. What it
cannot distinguish is COMPLETE from ABANDONED -- so the runner reports the final state table and
the date coverage it actually achieved, and says plainly if the range still stops short of
2026-09-11. Silence is not success; the report is.

WHAT IT RUNS, in order, each the committed runner unchanged:

    d448_es_front_month.py --build --test      the direct settlement test, ES vs SPY
    d449_es_holds.py       --build --test      C1's hold on ES, against the proxy
    d450_entry_prints.py                       the entry-print decomposition

NOTHING IS COMMITTED AUTOMATICALLY. The runners write their fixtures and JSON; the records are
amended by hand, because a result that lands without anyone reading it is not a result.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "data" / "futures_acquisition_manifest.json"
LOG = REPO / "temp" / "es_rerun.log"
POLL_S = 180
MAX_WAIT_H = 12.0

STEPS = [
    ("D448 build", [sys.executable, "scripts/d448_es_front_month.py", "--build"]),
    ("D448 test", [sys.executable, "scripts/d448_es_front_month.py", "--test"]),
    ("D449 build", [sys.executable, "scripts/d449_es_holds.py", "--build"]),
    ("D449 test", [sys.executable, "scripts/d449_es_holds.py", "--test"]),
    ("D450", [sys.executable, "scripts/d450_entry_prints.py"]),
]


def state() -> tuple[list, bool]:
    """(ohlcv items, still_moving). A malformed read means the writer is mid-flush, which is
    NOT completion -- treated as still moving rather than as an error."""
    try:
        m = json.loads(MANIFEST.read_text())
    except Exception:
        return [], True
    items = [i for i in m.get("items", []) if i.get("schema") == "ohlcv-1m"]
    return items, any(i.get("state") == "submitted" for i in items)


def coverage() -> str:
    fs = sorted((REPO / "data" / "raw" / "databento").glob("*/*.ohlcv-1m.dbn.zst"))
    if not fs:
        return "no ohlcv-1m files on disk"
    span = sorted(f.name.split("glbx-mdp3-")[1].split(".")[0] for f in fs)
    return f"{len(fs)} files, {span[0][:8]} .. {span[-1][-8:]}"


def report(items) -> None:
    print(f"  acquisition state at {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    for i in items:
        print(f"    {str(i.get('window')):<28} {i.get('state'):<12} "
              f"{i.get('bytes_on_disk', 0):>14,}")
    print(f"  on disk: {coverage()}")
    short = not any("2026" in str(i.get("window")) and i.get("state") == "downloaded"
                    for i in items)
    if short:
        print("  NOTE: the range still stops short of 2026-09-11. The re-run below uses what "
              "is on disk,\n        and the T+1 era may still be only partly covered. Say so "
              "in any record that quotes it.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    items, moving = state()
    if a.check:
        report(items)
        print(f"  still moving: {moving}")
        return 0

    t0 = time.time()
    while moving and not a.now:
        if (time.time() - t0) / 3600 > MAX_WAIT_H:
            print(f"TIMED OUT after {MAX_WAIT_H}h with chunks still submitted. Nothing re-run.")
            report(items)
            return 2
        time.sleep(POLL_S)
        items, moving = state()

    print("ACQUISITION HAS STOPPED MOVING -- re-running the three ES studies\n")
    report(items)
    print()

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("w", encoding="utf-8") as fh:
        for name, cmd in STEPS:
            print(f"  --- {name} ---", flush=True)
            fh.write(f"\n{'=' * 70}\n{name}\n{'=' * 70}\n")
            fh.flush()
            r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
            fh.write(r.stdout or "")
            fh.write(r.stderr or "")
            fh.flush()
            if r.returncode != 0:
                print(f"  {name} FAILED (exit {r.returncode}) -- see {LOG}")
                print((r.stderr or "")[-1200:])
                return 1
            for line in (r.stdout or "").splitlines():
                if any(k in line for k in ("GATE", "holds", "matched", "ES-SPY", "ratio",
                                           "corr", "regime", "T+", "V ", "ann%", "breach")):
                    print("   ", line)
    print(f"\nall three re-ran. full output: {LOG.relative_to(REPO)}")
    print("RECORDS ARE NOT AMENDED AUTOMATICALLY -- read the log and write them by hand.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
