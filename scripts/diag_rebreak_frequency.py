"""How often does the principal's re-break setup trigger (2026-09-29)? Reads the price path only UP TO each entry --
never a price after it -- in-sample 2016-01-04 -> 2025-02-28 through the sealed loader. Per root (ES, NQ), day session.

    uv run python scripts/diag_rebreak_frequency.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

The setup, long side (short mirrored): L = the prior session's RTH high. ARM: a 1-min bar trades above L. PULLBACK: a
later bar's low touches L (<= L). ENTRY: a later bar's high reaches L + 1 x ATR20 (the daily ATR, D644's atr20) -- a
buy stop. The first entry of the day, either side, is counted. Reported: sessions, setups per year, entries per side,
the entry's clock time, and D661's bar at the vault count this frequency implies.
Writes data/opening/rebreak_frequency.json (counts only).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d662_gamma_product as S  # noqa: E402

OUT = REPO / "data" / "opening" / "rebreak_frequency.json"
Z = 1.959964 + 0.841621


def first_entry(bb: dict, L_hi: float, L_lo: float, atr: float, window: int | None = None) -> tuple[int, int] | None:
    """(side, minute) of the first entry of the day, reading bars only up to that bar. `window`: the re-break must
    fill within this many minutes of the pullback's touch, else that side resets to idle (it may set up again)."""
    m, h, l = bb["m"], bb["h"], bb["l"]
    state = {1: 0, -1: 0}  # 0 idle, 1 armed, 2 pulled back
    touched = {1: -1, -1: -1}
    for i in range(len(m)):
        for side, lvl in ((1, L_hi), (-1, L_lo)):
            beyond = h[i] > lvl if side > 0 else l[i] < lvl
            touch = l[i] <= lvl if side > 0 else h[i] >= lvl
            trig = h[i] >= lvl + atr if side > 0 else l[i] <= lvl - atr
            if state[side] == 2 and window is not None and m[i] - touched[side] > window:
                state[side] = 0  # expired: the setup must form again
            if state[side] == 2 and trig:
                return side, int(m[i])
            if state[side] == 1 and touch:
                state[side], touched[side] = 2, int(m[i])
            if state[side] == 0 and beyond:
                state[side] = 1
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    V = S.load_v2()
    R = V.R
    b, use, _ = V.load_inputs(a.data_root, False)
    tabs = R.session_table(b, use)
    bars = R.bar_arrays(b)
    bar = json.loads((REPO / "data" / "opening" / "prize_bar.json").read_text(encoding="utf-8"))["bar"]
    out: dict = {"spec": "the principal's re-break setup, 2026-09-29; counts only, no price after an entry read", "roots": {}}
    for r, window in [(r, w) for r in ("ES", "NQ") for w in (None, 30, 45, 60)]:
        d = tabs[r]
        d = d[d["usable"] & (d.index >= "2016-01-04") & (d.index < "2025-03-01")]
        ents, by_year, sides, clocks = 0, {}, {1: 0, -1: 0}, []
        n = 0
        for s in d.index:
            bb = bars.get((r, s))
            ph, pl, atr = d.at[s, "prior_high"], d.at[s, "prior_low"], d.at[s, "atr20"]
            if bb is None or not (np.isfinite(ph) and np.isfinite(pl) and np.isfinite(atr)):
                continue
            n += 1
            e = first_entry(bb, float(ph), float(pl), float(atr), window)
            if e:
                ents += 1
                by_year[s[:4]] = by_year.get(s[:4], 0) + 1
                sides[e[0]] += 1
                clocks.append(e[1])
        per_year = ents / (n / 252)
        n_vault = per_year * 390 / 252
        sig60 = bar[r]["daily_60min"]["sigma_hold_bp"]
        c = bar[r]["break_even_s_bp"] * 0.8
        need = (Z * sig60 / math.sqrt(max(n_vault, 1e-9)) + c) / 0.8
        cl = np.array(clocks)
        out["roots"][f"{r}_window_{window or 'none'}"] = {"sessions": n, "entries": ents, "share_of_sessions": ents / n, "per_year": per_year,
                           "by_year": by_year, "long": sides[1], "short": sides[-1],
                           "entry_clock_median": f"{int(np.median(cl)) // 60:02d}:{int(np.median(cl)) % 60:02d}" if len(cl) else None,
                           "entries_after_1500": int((cl >= 15 * 60).sum()) if len(cl) else 0,
                           "vault_events_expected": n_vault, "push_needed_bp_60min_hold": need}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
