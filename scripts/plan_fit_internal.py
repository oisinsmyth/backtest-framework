"""Fit the plan to the internal drive, bars first, keeping a stated amount free.

    uv run python scripts/plan_fit_internal.py [--free-gb 64] [--json]

Reads the VENDOR figures in data/plan_cost_probe.json -- no estimates -- and walks the
plan in priority order, reporting cumulative disk under three compression scenarios.

THE DISTINCTION THAT DECIDES THIS. Databento METERS the uncompressed size and DELIVERS
zstd-compressed files. The 441 GiB total is the metered figure; what lands on the drive
is that divided by the compression ratio. Reading the metered number as a disk number
overstates the footprint by roughly 2.6x.

THE RATIO IS THE ONE REAL UNKNOWN. 2.60x was MEASURED on OHLCV records carrying real
prices (data/decode_pipeline_bench.json). It was NOT measured on tbbo, mbo, definition
or statistics, and those are most of the volume here. So three scenarios are carried:

    1.5x  pessimistic -- if these schemas compress far worse than bars
    2.0x  conservative
    2.6x  measured, on OHLCV only

A plan that fits at 1.5x fits at any plausible ratio. That is the line to plan against,
and one small job settles it for real before the large ones are submitted.

PRIORITY ORDER, as instructed: bars first, then whatever is most useful per byte.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROBE = REPO / "data" / "plan_cost_probe.json"
OUT = REPO / "data" / "plan_fit_internal.json"

GIB = 1024 ** 3
GB = 10 ** 9
FREE_NOW_GB = 414.2          # measured on C: 2026-09-11
DRIVE_GB = 930.5
SCENARIOS = (1.5, 2.0, 2.6)

# (substring matching the probe's item label, rank, why it sits here)
PRIORITY = [
    ("ohlcv-1m",   "1  THE BARS. Every instrument, every contract month, 16 years. The core "
                   "panel and the thing every study reads first."),
    ("definition", "2  Roll calendar, expiries, tick sizes. The bars are NOT usable without "
                   "it -- a continuous series cannot be stitched or a contract priced."),
    ("statistics", "3  Open interest and settlements, 16 years. Daily, cheap, and the only "
                   "positioning series in the plan."),
    ("status",     "4  Halts and auction states. Tiny, and it is what a breach looks like "
                   "when the position cannot be exited."),
    ("tbbo",       "5  Every trade with the quote before it, 12 months. With 1-second bars "
                   "excluded this is the ONLY intrabar path in the plan, plus the spread."),
    ("bbo-1m",     "6  Quoted spread per minute including the overnight, 12 months. Answers "
                   "cost where no trade prints, which tbbo cannot."),
    ("mbo",        "7  Full order book, 8 roots. Unrepeatable -- the free L3 window trails "
                   "the current date -- but the repo has no order-book engine, so it is "
                   "insurance, not a study input. Last in, first cut."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--free-gb", type=float, default=64.0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    items = {r["item"]: r for r in probe["items"] if "billable_gib" in r}
    budget_gb = FREE_NOW_GB - a.free_gb

    print(f"C: {DRIVE_GB:.0f} GB total, {FREE_NOW_GB:.1f} GB free now")
    print(f"keeping {a.free_gb:.0f} GB free -> {budget_gb:.0f} GB of budget for data")
    print(f"(that leaves the drive {100*a.free_gb/DRIVE_GB:.1f}% free; under ~10% an SSD "
          f"loses room for wear levelling)\n")

    ordered = []
    for key, why in PRIORITY:
        match = next((k for k in items if k.strip().startswith(key)), None)
        if match:
            ordered.append((match, items[match], why))

    print(f"  {'#':<3}{'item':30}{'metered':>9}" +
          "".join(f"{'disk@'+str(s)+'x':>12}" for s in SCENARIOS) + "   verdict")
    cum = {s: 0.0 for s in SCENARIOS}
    rows, cut_at = [], None
    for i, (name, r, why) in enumerate(ordered, 1):
        g = r["billable_gib"]
        for s in SCENARIOS:
            cum[s] += g / s * GIB / GB
        worst = cum[1.5]
        fits = worst <= budget_gb
        if not fits and cut_at is None:
            cut_at = i
        rows.append({"rank": i, "item": name, "metered_gib": g,
                     "cum_disk_gb": {str(s): cum[s] for s in SCENARIOS},
                     "fits_at_worst_case": fits, "why": why})
        print(f"  {i:<3}{name.strip():30}{g:9.1f}" +
              "".join(f"{cum[s]:12.0f}" for s in SCENARIOS) +
              f"   {'ok' if fits else 'OVER BUDGET'}")

    total_metered = sum(r["billable_gib"] for _n, r, _w in ordered)
    print(f"\n  metered total {total_metered:,.1f} GiB")
    for s in SCENARIOS:
        disk = total_metered / s * GIB / GB
        print(f"  at {s}x compression -> {disk:6.0f} GB on disk, "
              f"{FREE_NOW_GB - disk:6.0f} GB free afterwards"
              f"   {'FITS' if disk <= budget_gb else 'DOES NOT FIT'}")

    print()
    if cut_at is None:
        print("  THE WHOLE PLAN FITS, even at the pessimistic 1.5x. Nothing needs cutting.")
        spare = budget_gb - total_metered / 1.5 * GIB / GB
        print(f"  Spare budget at the pessimistic ratio: {spare:.0f} GB.")
    else:
        print(f"  CUT AFTER RANK {cut_at - 1}. Items {cut_at} and below do not fit at 1.5x.")

    if a.json:
        OUT.write_text(json.dumps({
            "source": "data/plan_cost_probe.json (vendor figures, free metadata calls)",
            "drive_gb": DRIVE_GB, "free_now_gb": FREE_NOW_GB,
            "keep_free_gb": a.free_gb, "budget_gb": budget_gb,
            "compression_scenarios": list(SCENARIOS),
            "compression_note": "2.60x was measured on OHLCV only; tbbo/mbo/definition/statistics were NOT measured. Plan against 1.5x until one small job settles it.",
            "priority": rows, "total_metered_gib": total_metered,
            "cut_after_rank": cut_at,
        }, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
