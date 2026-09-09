"""Pair the drawn support and resistance into CHANNELS, and ask when each channel breaks.

    uv run python scripts/d399_channel_end.py

THE PRINCIPAL'S POINT, 2026-09-09. Asking a single line when it ends gives 'never' four times in
seven -- a support line price simply walks away from is never touched again. A CHANNEL cannot do
that: price is between two lines, so it must eventually leave through one side or the other.
Pairing is therefore the better object to ask.

    pair each drawn support with the drawn resistance it overlaps in time
    extend BOTH lines forward past the span he drew
    the channel BREAKS at the first bar whose wick leaves it -- low below support,
        or high above resistance -- by more than a tolerance

Reported per pair: which side broke, how many bars past the end of his drawing, the channel's
width at the start and at the break, and whether the two gradients converge (a wedge) or run
parallel.

Scores nothing. Admits nothing (R15). A diagnostic that asks the ground truth a question.
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
OUT = REPO / "data" / "d399_channel_end_diagnostic.json"
TOLS = (0.0, 0.01, 0.03)


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def level(L, n):
    """The drawn line's price at every bar of the window, extended both ways."""
    idx = np.arange(n)
    return np.exp(np.log(float(L["p0"])) + float(L["g_per_bar"]) * (idx - int(L["i0"])))


def main() -> int:
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("ragged_panel", "ragged_panel.py")

    gt = json.loads(GT.read_text())
    start, n = int(gt["start_bar"]), int(gt["n"])
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[gt["symbol"]]
    hi = np.array([b.bar.high for b in bars], float)[start:start + n]
    lo = np.array([b.bar.low for b in bars], float)[start:start + n]
    dates = [str(b.timestamp)[:10] for b in bars][start:start + n]

    sup = [L for L in gt["lines"] if L["kind"] == "support"]
    res = [L for L in gt["lines"] if L["kind"] == "resistance"]

    # pair each support with the resistance it overlaps most in time
    pairs = []
    for s in sup:
        best, bov = None, 0
        for r in res:
            ov = min(int(s["i1"]), int(r["i1"])) - max(int(s["i0"]), int(r["i0"])) + 1
            if ov > bov:
                best, bov = r, ov
        pairs.append((s, best, bov))

    out = dict(symbol=gt["symbol"], start_bar=start, n=n, tolerances=list(TOLS),
               note="DIAGNOSTIC. Channels from the principal's own drawn lines. Nothing scored.",
               pairs=[])

    print(f"\n  {gt['symbol']} bars {start}-{start + n}")
    print(f"  Pairing each drawn support with the resistance it overlaps -- when does the "
          f"CHANNEL break?\n")

    for s, r, ov in pairs:
        if r is None:
            print(f"  sup {s['date0']} -> {s['date1']}:  NO overlapping resistance drawn; "
                  f"no channel")
            out["pairs"].append(dict(support=s["date0"], resistance=None, overlap=0))
            continue
        Ls, Lr = level(s, n), level(r, n)
        a = max(int(s["i0"]), int(r["i0"]))
        b_end = max(int(s["i1"]), int(r["i1"]))          # the later of the two second clicks
        gs, gr = float(s["g_per_bar"]), float(r["g_per_bar"])
        with np.errstate(invalid="ignore", divide="ignore"):
            below = np.log(Ls) - np.log(lo)              # >0: low is under support
            above = np.log(hi) - np.log(Lr)              # >0: high is over resistance

        row = dict(support=s["date0"], resistance=r["date0"], overlap_bars=int(ov),
                   i_open=int(a), i_last_click=int(b_end),
                   g_support=gs, g_resistance=gr,
                   width_open_pct=float(100 * (np.log(Lr[a]) - np.log(Ls[a]))),
                   converging=bool((gr - gs) < 0), breaks={})
        cells = []
        for tol in TOLS:
            brk = (below > tol) | (above > tol)
            after = np.flatnonzero(brk[b_end + 1:]) + b_end + 1
            first = int(after[0]) if after.size else None
            side = None
            if first is not None:
                side = "support" if below[first] > tol else "resistance"
            inside = int(np.flatnonzero(brk[a:b_end + 1]).size)
            row["breaks"][f"{tol:g}"] = dict(
                first_break=first, bars_past_last_click=(first - b_end) if first is not None else None,
                side=side, date=dates[first] if first is not None else None,
                width_at_break_pct=(float(100 * (np.log(Lr[first]) - np.log(Ls[first])))
                                    if first is not None else None),
                breaks_inside=inside,
                channel_life=(first - a + 1) if first is not None else int(n - a))
            cells.append(f"{(first - b_end) if first is not None else 999:>7d}")
        out["pairs"].append(row)
        w = row["width_open_pct"]
        print(f"  sup {s['date0']} + res {r['date0']}  overlap {ov:>3d} bars, "
              f"width {w:>5.1f}%, {'converging' if row['converging'] else 'diverging'}")
        print(f"      bars past the last click before the CHANNEL breaks: "
              + " ".join(f"{t*100:g}%:{c.strip()}" for t, c in zip(TOLS, cells))
              + f"   side: {row['breaks']['0']['side'] or '-'}")

    print()
    for tol in TOLS:
        rows = [p for p in out["pairs"] if p.get("breaks")]
        past = [p["breaks"][f"{tol:g}"]["bars_past_last_click"] for p in rows
                if p["breaks"][f"{tol:g}"]["bars_past_last_click"] is not None]
        lives = [p["breaks"][f"{tol:g}"]["channel_life"] for p in rows]
        never = sum(1 for p in rows if p["breaks"][f"{tol:g}"]["first_break"] is None)
        out.setdefault("summary", {})[f"{tol:g}"] = dict(
            channels=len(rows), never_broken=never,
            median_bars_past_last_click=float(np.median(past)) if past else None,
            median_channel_life=float(np.median(lives)))
        s_ = out["summary"][f"{tol:g}"]
        print(f"  tolerance {100 * tol:>4.1f}%:  {len(rows) - never}/{len(rows)} channels break | "
              f"median {s_['median_bars_past_last_click'] if past else float('nan'):.0f} bars past "
              f"the last click | median channel life {s_['median_channel_life']:.0f} bars")

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written")
    print("\nDIAGNOSTIC. Nothing was scored and nothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
