"""Rebuild the PIVOT ground truth from the replay's append-only event log, and compare it to the
k=3 detector.

    uv run python scripts/d399_build_pivot_ground_truth.py

THE LOG IS THE RECORD. Every action wrote its own document as it happened -- `place`, `remove`,
`step`, `setting` -- so the final pivot set is REPLAYED from the events rather than read from a
derived array. The previous replay stored a per-bar snapshot array that stopped at bar 48 while
the principal stepped to 259; there is no such array here to break, and removals are logged, so a
misclick and its correction are both in the record.

WHAT IS COMPARED, and it is deliberately three numbers rather than one:

  MATCHED       he and the detector name the same bar, same sign
  HIS ONLY      he marked a turn the detector did not -- a DETECTOR MISS
  DETECTOR ONLY the detector marked a turn he did not -- a DETECTOR FALSE POSITIVE
  NEAR          same sign, within TOL bars: the same turn, disagreeing about which bar

A single "agreement %" would hide which of those is happening, and they have different fixes: a
miss points at the tie rule or the window width, a false positive points at the missing size
filter, and a near-match is a tolerance question rather than a disagreement at all.

Writes data/d399_pivot_ground_truth.json. Scores nothing, admits nothing (R15).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
EV = REPO / "temp" / "pivot_pull" / "events"
OUT = REPO / "data" / "d399_pivot_ground_truth.json"
CHART = REPO / "temp" / "d399_recalc_chart.json"
TOL = 2          # bars, for the NEAR bucket


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def replay(events):
    """Re-run the log in sequence order. The surviving set is what a `place` left un-`remove`d."""
    live, first_seen, seen_through = {}, None, 0
    for e in events:
        a = e.get("action")
        if a == "place":
            live[(int(e["bar"]), int(e["sign"]))] = float(e["price"])
            if first_seen is None:
                first_seen = int(e["at_bar"])
        elif a == "remove":
            live.pop((int(e["bar"]), int(e["sign"])), None)
        seen_through = max(seen_through, int(e.get("at_bar", 0)))
    return live, first_seen, seen_through


def main() -> int:
    files = sorted(EV.glob("*.json"))
    assert files, f"no events under {EV}"
    raw = []
    for f in files:
        d = json.loads(f.read_text())
        raw.append(d.get("data", d))
    raw.sort(key=lambda e: int(e.get("seq", 0)))
    assert [int(e["seq"]) for e in raw] == list(range(1, len(raw) + 1)), (
        "[E] the sequence has a hole -- an event was lost and the replay would be wrong")

    kinds = Counter(e.get("action") for e in raw)
    live, first_seen, seen_through = replay(raw)
    print(f"\n  EVENT LOG: {len(raw)} events -- " + ", ".join(f"{k} {v}" for k, v in kinds.items()))
    print(f"  first pivot placed at bar {first_seen}; stepped through bar {seen_through}")
    n_place, n_remove = kinds.get("place", 0), kinds.get("remove", 0)
    print(f"  {n_place} placed, {n_remove} removed -> {len(live)} surviving "
          f"({100 * n_remove / max(1, n_place):.0f}% of placements were corrected)")

    # ---- his pivots
    his = {+1: sorted(b for (b, s) in live if s > 0), -1: sorted(b for (b, s) in live if s < 0)}
    print(f"  his pivots: {len(his[+1])} highs, {len(his[-1])} lows")

    # ---- the detector's, on the same window, never shown to him
    DR = _load("d399draw", "d399_draw_construction.py")
    UO = _load("d240", "run_uptrend_onset.py")
    RP = _load("rp", "ragged_panel.py")
    from backtest_framework.research.structure import pivots as PV

    ch = json.loads(CHART.read_text())
    start, n = int(ch["start_bar"]), int(ch["n"])
    _panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[ch["symbol"]]

    res = dict(symbol=ch["symbol"], start_bar=start, n=n, tol_bars=TOL,
               first_seen=first_seen, seen_through=seen_through,
               n_events=len(raw), n_placed=n_place, n_removed=n_remove,
               his={str(s): his[s] for s in (+1, -1)}, compare={})
    for k in (2, 3):
        ps = PV(bars, k)
        det = {+1: sorted(p.index - start for p in ps
                          if p.sign > 0 and start <= p.index < start + n),
               -1: sorted(p.index - start for p in ps
                          if p.sign < 0 and start <= p.index < start + n)}
        print(f"\n  k={k}: detector has {len(det[+1])} highs, {len(det[-1])} lows in the window")
        cell = {}
        for sg, nm in ((+1, "high"), (-1, "low")):
            H = [b for b in his[sg] if first_seen is not None and b <= seen_through]
            Dd = [b for b in det[sg] if first_seen is not None and b <= seen_through]
            hs, ds = set(H), set(Dd)
            exact = sorted(hs & ds)
            h_only, d_only = sorted(hs - ds), sorted(ds - hs)
            near = []
            for b in list(h_only):
                cand = [x for x in d_only if abs(x - b) <= TOL]
                if cand:
                    x = min(cand, key=lambda y: (abs(y - b), y))
                    near.append((b, x))
                    h_only.remove(b)
                    d_only.remove(x)
            tot = len(exact) + len(near) + len(h_only) + len(d_only)
            agree = 100 * (len(exact) + len(near)) / max(1, tot)
            print(f"    {nm:<5s} his {len(H):>3d}  detector {len(Dd):>3d}  ->  "
                  f"exact {len(exact):>3d}, near(<={TOL}b) {len(near):>3d}, "
                  f"HIS ONLY {len(h_only):>3d}, DETECTOR ONLY {len(d_only):>3d}   "
                  f"agreement {agree:.0f}%")
            cell[nm] = dict(his=H, detector=Dd, exact=exact,
                            near=[list(x) for x in near], his_only=h_only,
                            detector_only=d_only, agreement_pct=round(agree, 1))
        res["compare"][f"k{k}"] = cell

    # ---- what the DETECTOR-ONLY pivots look like: are they small?
    hi = np.array([b.bar.high for b in bars], float)[start:start + n]
    lo = np.array([b.bar.low for b in bars], float)[start:start + n]
    print(f"\n  ARE THE DETECTOR'S EXTRA PIVOTS JUST SMALL WIGGLES?")
    print(f"  swing size = the move from the previous opposite extreme, in per cent\n")
    for k in (2, 3):
        for sg, nm in ((+1, "high"), (-1, "low")):
            c = res["compare"][f"k{k}"][nm]
            px = hi if sg > 0 else lo
            other = lo if sg > 0 else hi

            def size(b):
                a = max(0, b - 10)
                ref = (other[a:b + 1].min() if sg > 0 else other[a:b + 1].max())
                return abs(px[b] / ref - 1.0) * 100 if ref > 0 else np.nan

            for lab, arr in (("matched", c["exact"]), ("DETECTOR ONLY", c["detector_only"]),
                             ("HIS ONLY", c["his_only"])):
                if not arr:
                    continue
                v = np.array([size(b) for b in arr], float)
                v = v[np.isfinite(v)]
                if v.size:
                    print(f"    k={k} {nm:<5s} {lab:<14s} n={v.size:>3d}  median swing "
                          f"{np.median(v):>5.1f}%   p25 {np.percentile(v, 25):>5.1f}%  "
                          f"p75 {np.percentile(v, 75):>5.1f}%")
        print()

    OUT.write_text(json.dumps(res, indent=1))
    print(f"  [P] {OUT.relative_to(REPO)} written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
