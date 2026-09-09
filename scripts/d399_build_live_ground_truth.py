"""Rebuild the CAUSAL ground truth from the replay's append-only event log, and analyse it.

    uv run python scripts/d399_build_live_ground_truth.py

WHY IT IS REBUILT RATHER THAN READ. The replay page kept two records: an append-only `events` log
and a per-bar `snapshots` array. THE SNAPSHOT ARRAY IS DEFECTIVE -- it stopped at bar 48 while the
principal stepped to 259, so the page's own `g_support`/`g_resistance` cover 6 of 260 bars. That
is a bug in the page, not in his work.

The event log is intact: 273 events, every draw with full geometry, every end, every step, each
stamped with the bar it happened on. So the per-bar state is RECONSTRUCTED from it here. That is
precisely what an append-only log is for, and it is why the state was not stored only as a
derived array.

    draw   at bar b -- the line becomes live at b with the geometry carried in the event
    end    at bar b -- the line's last live bar is b
    step   the cursor moving; the bars it passes are bars he saw and drew nothing new on

UNDO IS NOT IN THE LOG, and that is a second defect worth naming: `undo` popped a line without
logging an event. Draws that appear in the log but not in the surviving `lines` were undone, and
the bar at which that happened is unrecoverable. They are excluded, and counted, rather than
silently dropped.

Writes data/d399_live_ground_truth.json. Scores nothing, admits nothing (R15).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "temp" / "live_pull" / "drawn" / "gme_live.json"
OUT = REPO / "data" / "d399_live_ground_truth.json"
HIND = REPO / "data" / "d399_drawn_ground_truth.json"


def main() -> int:
    raw = json.loads(SRC.read_text())
    D = raw.get("data", raw)
    n = int(D["n"])
    events = D["events"]
    surviving = {L.get("id") for L in D.get("lines", []) if L.get("id")}

    draws = [e for e in events if e["action"] == "draw"]
    ends = {e["line_id"]: int(e["at_bar"]) for e in events if e["action"] == "end"}
    steps = [e for e in events if e["action"] == "step"]
    seen_through = int(D["seen_through"])

    undone = [e for e in draws if e["line_id"] not in surviving and e["line_id"] not in ends]
    used = [e for e in draws if e["line_id"] in surviving or e["line_id"] in ends]

    print(f"\n  EVENT LOG: {len(events)} events -- "
          + ", ".join(f"{k} {v}" for k, v in Counter(e['action'] for e in events).items()))
    print(f"  stepped from bar {draws[0]['at_bar'] if draws else '?'} through {seen_through} "
          f"of {n - 1}")
    if undone:
        print(f"  {len(undone)} drawn line(s) undone and NOT in the log -- excluded: "
              + ", ".join(e["line_id"] for e in undone))

    # --- reconstruct ---------------------------------------------------------
    lines = []
    for e in used:
        lid = e["line_id"]
        lines.append(dict(id=lid, kind=e["kind"], drawn_at=int(e["at_bar"]),
                          drawn_at_date=e["at_date"], ended_at=ends.get(lid),
                          g_per_bar=float(e["g_per_bar"]),
                          annualised=float(np.expm1(252 * e["g_per_bar"])),
                          segment=e["segment"],
                          live_bars=(ends.get(lid, seen_through) - int(e["at_bar"]) + 1)))
    lines.sort(key=lambda L: (L["drawn_at"], L["kind"]))

    g = {"support": [None] * n, "resistance": [None] * n}
    cnt = {"support": [0] * n, "resistance": [0] * n}
    for L in lines:
        last = L["ended_at"] if L["ended_at"] is not None else seen_through
        for t in range(L["drawn_at"], min(last, n - 1) + 1):
            g[L["kind"]][t] = L["g_per_bar"]      # last writer wins if two are live
            cnt[L["kind"]][t] += 1

    on = {k: sum(1 for v in g[k] if v is not None) for k in g}
    print(f"\n  RECONSTRUCTED: {len(lines)} lines")
    print(f"    support    live on {on['support']:>3d}/{seen_through + 1} bars seen "
          f"({100 * on['support'] / (seen_through + 1):.0f}%)")
    print(f"    resistance live on {on['resistance']:>3d}/{seen_through + 1} bars seen "
          f"({100 * on['resistance'] / (seen_through + 1):.0f}%)")
    both = sum(1 for t in range(seen_through + 1)
               if g["support"][t] is not None and g["resistance"][t] is not None)
    neither = sum(1 for t in range(seen_through + 1)
                  if g["support"][t] is None and g["resistance"][t] is None)
    print(f"    BOTH sides live on {both} bars; NEITHER on {neither} "
          f"({100 * neither / (seen_through + 1):.0f}% of the replay was 'no trend')")

    # --- how long does a trend live? ----------------------------------------
    lv = [L["live_bars"] for L in lines]
    print(f"\n  HOW LONG A TREND LIVES, drawn live:")
    print(f"    n {len(lv)}  min {min(lv)}  p25 {np.percentile(lv, 25):.0f}  "
          f"MEDIAN {np.median(lv):.0f}  p75 {np.percentile(lv, 75):.0f}  max {max(lv)} bars")

    hind = json.loads(HIND.read_text())
    hs = [L["i1"] - L["i0"] + 1 for L in hind["lines"]]
    print(f"    against the HINDSIGHT set's spans: n {len(hs)}, median {np.median(hs):.0f} bars")
    print(f"    -> drawn live he holds a trend about "
          f"{np.median(hs) / np.median(lv):.1f}x LESS long than he drew it with hindsight")

    # --- pairing -------------------------------------------------------------
    bybar = {}
    for L in lines:
        bybar.setdefault(L["drawn_at"], []).append(L["kind"])
    paired = sum(1 for b, ks in bybar.items() if "support" in ks and "resistance" in ks)
    print(f"\n  PAIRING: {len(bybar)} bars carry a new line; {paired} of them carry BOTH a "
          f"support and a resistance drawn together ({100 * paired / len(bybar):.0f}%)")

    ann = [100 * L["annualised"] for L in lines]
    print(f"\n  SLOPES: median |annualised| {np.median(np.abs(ann)):.0f}%/yr, "
          f"range {min(ann):.0f}% to {max(ann):.0f}%")
    delta_ann = 100 * float(np.expm1(252 * 1e-3))
    over = sum(1 for L in lines if abs(L["g_per_bar"]) > 1e-3)
    print(f"    {over}/{len(lines)} clear the delta filter of 1e-3 ({delta_ann:.0f}%/yr)")

    res = dict(
        what="CAUSAL ground truth: trendlines drawn by the principal on a forward-only replay.",
        symbol=D["symbol"], start_bar=D["start_bar"], n=n, seen_through=seen_through,
        first_date=D["first_date"], last_date=D["last_date"],
        provenance="Reconstructed from the replay's append-only event log "
                   "(artifact 22e7b47f-0b40-483f-80a0-120092822b8b, doc drawn/gme_live). "
                   "The page's own per-bar snapshot array is DEFECTIVE -- it stopped at bar 48 -- "
                   "so it is not used. The event log is intact and is the source.",
        LIMIT="Undo did not log an event, so drawn lines that were undone cannot be placed in "
              "time. They are excluded and counted in undone_line_ids.",
        causal=True,
        note="Unlike data/d399_drawn_ground_truth.json these lines never saw the future: each is "
             "stamped with the bar showing when it was drawn. A causal construction may be scored "
             "against g_support/g_resistance directly, with no oracle caveat.",
        n_events=len(events), undone_line_ids=[e["line_id"] for e in undone],
        lines=lines, g_support=g["support"], g_resistance=g["resistance"],
        n_live_support=cnt["support"], n_live_resistance=cnt["resistance"],
        bars_support_live=on["support"], bars_resistance_live=on["resistance"],
        bars_both_live=both, bars_no_trend=neither,
        median_live_bars=float(np.median(lv)), live_bars=lv,
        pairs_drawn_together=paired, bars_with_a_new_line=len(bybar))
    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  [P] {OUT.relative_to(REPO)} written")
    print("\nGROUND TRUTH. Nothing scored, nothing admitted (R15).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
