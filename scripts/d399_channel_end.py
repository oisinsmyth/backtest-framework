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

# WHAT COUNTS AS A BREAK. The first version of this file used the WICK, which is the loosest of
# the three conventions and not the principal's: "I only count the body as breaking it."
#
#   wick   the extreme -- low for support, high for resistance. A single spike breaks the line.
#   body   the body's far edge -- min(open, close) for support, max for resistance. A wick
#          through the line is NOT a break; part of the body must be through it.
#   close  the close alone. The strictest, and the usual "confirmed break" convention.
#
# Note the asymmetry this creates and it is deliberate, not an oversight: the principal DREW the
# lines snapped to the WICK, and breaks them on the BODY. Resting a line on the extremes while
# requiring a body to violate it is the standard chartist pairing, and it is what his own two
# choices together specify.
BREAK_ON = ("wick", "body", "close")


def break_series(kind, o, h, l, c, how):
    """The price series that must cross the line for a break, per convention."""
    if how == "wick":
        return l if kind == "support" else h
    if how == "close":
        return c
    return np.minimum(o, c) if kind == "support" else np.maximum(o, c)


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
    op = np.array([b.bar.open for b in bars], float)[start:start + n]
    hi = np.array([b.bar.high for b in bars], float)[start:start + n]
    lo = np.array([b.bar.low for b in bars], float)[start:start + n]
    cl = np.array([b.bar.close for b in bars], float)[start:start + n]
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

        row = dict(support=s["date0"], resistance=r["date0"], overlap_bars=int(ov),
                   i_open=int(a), i_last_click=int(b_end),
                   g_support=gs, g_resistance=gr,
                   width_open_pct=float(100 * (np.log(Lr[a]) - np.log(Ls[a]))),
                   converging=bool((gr - gs) < 0), breaks={})
        print(f"  sup {s['date0']} + res {r['date0']}  overlap {ov:>3d} bars, "
              f"width {row['width_open_pct']:>5.1f}%, "
              f"{'CONVERGING' if row['converging'] else 'diverging'}")
        for how in BREAK_ON:
            ps_ = break_series("support", op, hi, lo, cl, how)
            pr_ = break_series("resistance", op, hi, lo, cl, how)
            with np.errstate(invalid="ignore", divide="ignore"):
                below = np.log(Ls) - np.log(ps_)         # >0: price is under support
                above = np.log(pr_) - np.log(Lr)         # >0: price is over resistance
            cells = []
            for tol in TOLS:
                brk = (below > tol) | (above > tol)
                after = np.flatnonzero(brk[b_end + 1:]) + b_end + 1
                first = int(after[0]) if after.size else None
                side = ("support" if below[first] > tol else "resistance") if first is not None else None
                inside = int(np.flatnonzero(brk[a:b_end + 1]).size)
                row["breaks"][f"{how}|{tol:g}"] = dict(
                    first_break=first,
                    bars_past_last_click=(first - b_end) if first is not None else None,
                    side=side, date=dates[first] if first is not None else None,
                    breaks_inside=inside,
                    channel_life=(first - a + 1) if first is not None else int(n - a))
                cells.append(f"{(first - b_end) if first is not None else 999:>4d}")
            sd = row["breaks"][f"{how}|0"]["side"] or "-"
            ins = row["breaks"][f"{how}|0"]["breaks_inside"]
            print(f"      {how:>5s}:  bars past last click  "
                  + "  ".join(f"{t*100:g}%:{c.strip()}" for t, c in zip(TOLS, cells))
                  + f"   side {sd:>10s}   broken inside {ins}")
        out["pairs"].append(row)

    print()
    rows = [p for p in out["pairs"] if p.get("breaks")]
    print(f"  {'break on':>9s} {'tol':>6s} {'channels breaking':>18s} {'median past click':>18s} "
          f"{'median life':>12s}")
    for how in BREAK_ON:
        for tol in TOLS:
            key = f"{how}|{tol:g}"
            past = [p["breaks"][key]["bars_past_last_click"] for p in rows
                    if p["breaks"][key]["bars_past_last_click"] is not None]
            lives = [p["breaks"][key]["channel_life"] for p in rows]
            never = sum(1 for p in rows if p["breaks"][key]["first_break"] is None)
            out.setdefault("summary", {})[key] = dict(
                channels=len(rows), never_broken=never,
                median_bars_past_last_click=float(np.median(past)) if past else None,
                median_channel_life=float(np.median(lives)))
            print(f"  {how:>9s} {100*tol:>5.1f}% {f'{len(rows)-never}/{len(rows)}':>18s} "
                  f"{(np.median(past) if past else float('nan')):>18.0f} "
                  f"{np.median(lives):>12.0f}")

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written")
    print("\nDIAGNOSTIC. Nothing was scored and nothing is admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
