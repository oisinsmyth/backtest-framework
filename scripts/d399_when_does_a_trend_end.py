"""What ENDED the principal's drawn trendlines? A diagnostic, not a construction.

    uv run python scripts/d399_when_does_a_trend_end.py

THE QUESTION. Every construction tried so far ends a trend when the FITTED GRADIENT MOVES -- the
window closes as soon as a refit drifts past `h`. The principal's objection: the gradient wobbling
as data arrives is normal and should not end a trend. So what should?

This asks his own seven lines. For each drawn line it extends the line FORWARD past the bar he
stopped at and finds the first bar whose wick breaks it, and it also looks BACKWARD for breaks
inside the span he drew.

    if the first forward break lands ON or NEAR his end bar
        -> PRICE BREAKING THE LINE is what ends a trend, and the rule is obvious
    if the line survives far past his end bar unbroken
        -> he stopped for some other reason, and a break rule would run trends too long
    if the line was already broken INSIDE his span
        -> he tolerates breaks, and any zero-tolerance break rule is wrong

It also measures how long a line would live under a pure break rule against the ~46-bar median he
actually drew, so the fragmentation problem can be checked against the proposed cure before
anything is built.

Scores nothing. Admits nothing (R15).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
GT = REPO / "data" / "d399_drawn_ground_truth.json"
OUT = REPO / "data" / "d399_trend_end_diagnostic.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


TOLS = (0.0, 0.01, 0.03)          # a break must exceed the line by this much in log price


def main() -> int:
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("ragged_panel", "ragged_panel.py")

    gt = json.loads(GT.read_text())
    start, n = int(gt["start_bar"]), int(gt["n"])
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[gt["symbol"]]
    hi = np.array([b.bar.high for b in bars], float)[start:start + n]
    lo = np.array([b.bar.low for b in bars], float)[start:start + n]
    cl = np.array([b.bar.close for b in bars], float)[start:start + n]
    dates = [str(b.timestamp)[:10] for b in bars][start:start + n]

    res = dict(symbol=gt["symbol"], start_bar=start, n=n, tolerances=list(TOLS),
               note="DIAGNOSTIC. Asks the principal's own lines what ended them. Nothing scored.",
               lines=[])

    print(f"\n  {gt['symbol']} bars {start}-{start + n}, the principal's {len(gt['lines'])} lines")
    print(f"  Does PRICE BREAKING THE LINE explain where he stopped drawing?\n")
    print(f"  {'line':>22s} {'drew':>10s} {'span':>5s} "
          + " ".join(f"{'brk@' + f'{100*t:g}%':>9s}" for t in TOLS) + f" {'inside?':>8s}")

    for L in gt["lines"]:
        kind = L["kind"]
        i0, i1, g = int(L["i0"]), int(L["i1"]), float(L["g_per_bar"])
        p0 = float(L["p0"])
        idx = np.arange(n)
        line = np.exp(np.log(p0) + g * (idx - i0))          # extended across the whole window
        wick = lo if kind == "support" else hi
        with np.errstate(invalid="ignore", divide="ignore"):
            excess = (np.log(line) - np.log(wick)) if kind == "support" \
                else (np.log(wick) - np.log(line))          # >0 means the line is BROKEN

        row = dict(kind=kind, i0=i0, i1=i1, span=i1 - i0 + 1,
                   date0=L["date0"], date1=L["date1"], g_per_bar=g, breaks={})
        cells = []
        for tol in TOLS:
            brk = excess > tol
            after = np.flatnonzero(brk[i1 + 1:]) + i1 + 1
            first_after = int(after[0]) if after.size else None
            inside = np.flatnonzero(brk[i0:i1 + 1]) + i0
            row["breaks"][f"{tol:g}"] = dict(
                first_break_after_end=first_after,
                bars_past_end=(first_after - i1) if first_after is not None else None,
                breaks_inside_span=int(inside.size),
                first_break_inside=int(inside[0]) if inside.size else None,
                life_under_break_rule=(first_after - i0 + 1) if first_after is not None
                else int(n - i0))
            cells.append(f"{(first_after - i1) if first_after is not None else 999:>9d}")
        res["lines"].append(row)
        ins = row["breaks"][f"{TOLS[0]:g}"]["breaks_inside_span"]
        print(f"  {kind[:3] + ' ' + L['date0']:>22s} {L['date1']:>10s} {i1 - i0 + 1:>5d} "
              + " ".join(cells) + f" {ins:>8d}")

    print("\n  'brk@x%' = bars PAST his end bar before the extended line is first broken by x%.")
    print("  'inside?' = how many bars inside the span he drew already broke the line (tol 0%).\n")

    for tol in TOLS:
        past = [L["breaks"][f"{tol:g}"]["bars_past_end"] for L in res["lines"]
                if L["breaks"][f"{tol:g}"]["bars_past_end"] is not None]
        lives = [L["breaks"][f"{tol:g}"]["life_under_break_rule"] for L in res["lines"]]
        ins = [L["breaks"][f"{tol:g}"]["breaks_inside_span"] for L in res["lines"]]
        res.setdefault("summary", {})[f"{tol:g}"] = dict(
            median_bars_past_end=float(np.median(past)) if past else None,
            n_broken_at_or_within_5=int(sum(1 for p in past if p <= 5)),
            median_life_under_break_rule=float(np.median(lives)),
            lines_with_a_break_inside=int(sum(1 for i in ins if i > 0)),
            median_breaks_inside=float(np.median(ins)))
        s = res["summary"][f"{tol:g}"]
        print(f"  tolerance {100 * tol:>4.1f}%:  median {s['median_bars_past_end']:.0f} bars past "
              f"his end before a break | {s['n_broken_at_or_within_5']}/7 broke within 5 bars of it")
        print(f"                  a pure break rule would give lines of median "
              f"{s['median_life_under_break_rule']:.0f} bars against his 46 | "
              f"{s['lines_with_a_break_inside']}/7 of his lines were ALREADY broken inside "
              f"(median {s['median_breaks_inside']:.0f} bars)")

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written")
    print("\nDIAGNOSTIC. Nothing was scored and nothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
