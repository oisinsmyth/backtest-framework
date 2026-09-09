"""D399 -- WARM-STARTED DYNAMIC WINDOWS. Branch E's blind head, removed.

    uv run python scripts/d399_alt_warmstart.py                  the full sweep
    uv run python scripts/d399_alt_warmstart.py --verify          equality vs branch E only

WHAT BRANCH E DOES AND WHY IT COSTS RECALL. `segment_windows` opens each new window AT THE BREAK
BAR with its pivot accumulator emptied (`ptr = searchsorted(pidx, at)`). The window therefore has
no gradient until it has earned `min_piv` fresh pivots inside itself, which the scorer measures at
a median ~29 bars. Those bars are silent, and silence is what RECALL charges for.

THE FIX, two variants, both strictly causal:

  carry   : the window still opens at the break bar j, but the last `c` pivots that are ALREADY
            CONFIRMED at j (index p usable at p + k) are pre-loaded into the accumulator. The
            gradient can exist at j itself when c >= min_piv, and needs only min_piv - c new
            pivots otherwise. The offset still minimises over [j, j] onward -- the line's POSITION
            is measured from the new trend's own beginning, as in E.
  pivot   : the window opens AT THE c-th LAST CONFIRMED PIVOT, s = pidx[last - c + 1], so those c
            pivots are inside the window by construction AND the offset minimises over [s, j].
            The line's position therefore also sees the run-up to the break.

  c = 0 in either variant IS branch E, exactly -- asserted below, bit-identically, which is what
  makes the comparison a measurement of the warm start rather than of a rewrite.

CAUSALITY. Everything a bar j reads is dated <= j: the carried pivots are drawn from
`pidx <= j - k` (the same confirmation lag rolling_fit uses), and the offset reads px_respect over
bars [s, j] with s <= j. The pointer past the carried block is set to `searchsorted(pidx, j)`,
exactly as E does, so pivots sitting in the unconfirmed gap (j-k, j) are discarded by BOTH -- the
warm start adds pivots, it never changes which pivots the forward scan will pick up.

NOT A RESULT. This scores one hand-drawn window on one symbol. The best cell of a 2 x 3 x 4 x 4
sweep is a best-of-N and means nothing without a floor; the grid is printed whole for that reason.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "temp" / "d399_warmstart_grid.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def warm_windows(piv_idx, piv_logpx, px_respect, n_bars, k, h, widen,
                 min_piv, max_window=None, carry=0, variant="carry"):
    """`segment_windows` with a WARM START at every window boundary.

    Identical to branch E in every other respect: sticky gradient (fixed at the window's first
    admissible fit), window closes when its own refit drifts more than `h` from that gradient,
    line = tightest offset at slope G over the window's own bars.

    `carry` = how many already-confirmed pivots the new window opens with. `variant`:
      "carry" -- window start stays at the break bar, the pivots are pre-loaded
      "pivot" -- window start moves back to the oldest carried pivot's bar

    Returns (G, L, anc, win) with branch E's meanings.
    """
    assert variant in ("carry", "pivot")
    assert carry >= 0
    G = np.full(n_bars, np.nan)
    L = np.full(n_bars, np.nan)
    anc = np.zeros(n_bars, bool)
    win = np.full(n_bars, -1, int)
    order = np.argsort(piv_idx, kind="stable")
    pidx, ppx = piv_idx[order], piv_logpx[order]
    ptr = 0
    s = 0
    n_p = sx = sy = sxx = sxy = 0.0
    Gh = np.nan
    anc[0] = True

    def fit():
        den = n_p * sxx - sx * sx
        if n_p < min_piv or den <= 0:
            return np.nan
        return (n_p * sxy - sx * sy) / den

    def add(i):
        nonlocal n_p, sx, sy, sxx, sxy
        x, y = float(pidx[i]), float(ppx[i])
        n_p += 1.0; sx += x; sy += y; sxx += x * x; sxy += x * y

    def reopen(at):
        """Close the window and open a new one at bar `at`, warm-started."""
        nonlocal s, n_p, sx, sy, sxx, sxy, Gh, ptr
        Gh = np.nan
        n_p = sx = sy = sxx = sxy = 0.0
        # pivots CONFIRMED at bar `at`: index p is knowable at p + k, so p <= at - k.
        n_conf = int(np.searchsorted(pidx, at - k, "right"))
        c = min(carry, n_conf)
        if variant == "pivot" and c > 0:
            s = int(pidx[n_conf - c])          # window opens at the oldest carried pivot's bar
        else:
            s = at
        # branch E's forward pointer, unchanged: pivots in the unconfirmed gap are discarded
        ptr = int(np.searchsorted(pidx, at, "left"))
        for i in range(n_conf - c, n_conf):
            add(i)

    for j in range(n_bars):
        did_reopen = False
        for attempt in (0, 1):                     # a warm start gets ONE re-fit on its own bar
            while ptr < pidx.size and pidx[ptr] <= j - k:
                add(ptr)
                ptr += 1
            g_now = fit()
            broke = False
            if np.isfinite(g_now):
                if not np.isfinite(Gh):
                    Gh = g_now                     # the window's gradient, fixed once
                elif abs(g_now - Gh) > h:
                    broke = True                   # THE TREND CHANGED
            if not broke and max_window is not None and j - s + 1 > max_window:
                broke = True
            if broke and attempt == 0:
                reopen(j)
                anc[j] = True
                did_reopen = True
                continue
            break
        if did_reopen and not np.isfinite(Gh):
            continue                               # E's `continue` at a boundary: nothing to draw.
                                                   # With carry = 0 this is EVERY boundary, which
                                                   # is exactly the blind head being removed here.
        win[j] = s
        if not np.isfinite(Gh):
            continue
        idx = np.arange(s, j + 1)
        det = px_respect[idx] - Gh * (idx - j)
        fin = np.isfinite(det)
        if not fin.any():
            continue
        det = det[fin]
        G[j] = Gh
        L[j] = det.min() if widen < 0 else det.max()
    return G, L, anc, win


# --------------------------------------------------------------------------------------------


def prepare():
    DR = _load("d399draw", "d399_draw_construction.py")
    SC = _load("d399score", "d399_score_against_drawn.py")
    UO = _load("d240_uptrend", "run_uptrend_onset.py")
    RP = _load("ragged_panel", "ragged_panel.py")
    from backtest_framework.research.structure import pivots as PV

    gt = json.loads((REPO / "data" / "d399_drawn_ground_truth.json").read_text())
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    bars = cleaned[gt["symbol"]]
    m = len(bars)
    px = {"support": np.array([b.bar.low for b in bars], float),
          "resistance": np.array([b.bar.high for b in bars], float)}
    ps = PV(bars, UO.K)
    piv = {}
    for kind, sign in (("support", -1), ("resistance", +1)):
        pidx = np.array([p.index for p in ps if p.sign == sign], dtype=int)
        assert pidx.size == 0 or np.all(np.diff(pidx) > 0), "pivot indices not ascending"
        piv[kind] = (pidx, np.log([p.price for p in ps if p.sign == sign]))
    return DR, SC, UO, gt, m, px, piv


def verify(DR, UO, m, px, piv):
    """carry = 0 must be branch E, bit-identically, in BOTH variants."""
    n_checked = 0
    for kind, widen in (("support", -1), ("resistance", +1)):
        pidx, ppx = piv[kind]
        r = np.log(px[kind])
        for mp in (2, 3, 4, 5):
            for pct in (1, 2, 4, 8):
                h = DR.h_of_annual(pct)
                Ge, Le, ae, we = DR.segment_windows(pidx, ppx, r, m, UO.K, h, widen,
                                                    min_piv=mp, max_window=UO.WINDOW)
                for var in ("carry", "pivot"):
                    Gw, Lw, aw, ww = warm_windows(pidx, ppx, r, m, UO.K, h, widen, mp,
                                                  max_window=UO.WINDOW, carry=0, variant=var)
                    for nm, a, b in (("G", Ge, Gw), ("L", Le, Lw)):
                        assert np.array_equal(a, b, equal_nan=True), \
                            f"[VERIFY] {nm} differs from branch E at {kind}/{var}/mp{mp}/h{pct}"
                    assert np.array_equal(ae, aw) and np.array_equal(we, ww), \
                        f"[VERIFY] anchors/windows differ from branch E at {kind}/{var}/mp{mp}/h{pct}"
                    n_checked += 1
    # a self-test that cannot fail is worse than none: the check must RAISE on a real difference.
    pidx, ppx = piv["support"]
    r = np.log(px["support"])
    h = DR.h_of_annual(4)
    Ge, _, _, _ = DR.segment_windows(pidx, ppx, r, m, UO.K, h, -1, min_piv=3,
                                     max_window=UO.WINDOW)
    Gb, _, _, _ = warm_windows(pidx, ppx, r, m, UO.K, h, -1, 3, max_window=UO.WINDOW,
                               carry=2, variant="carry")
    assert not np.array_equal(Ge, Gb, equal_nan=True), \
        "[VERIFY] the equality check cannot fail -- carry=2 produced branch E's own array"
    print(f"  [VERIFY] carry=0 == branch E on {n_checked} (side, variant, min_piv, h) cells, "
          f"bit-identical; and the check does fire on carry=2.")


def score_one(DR, SC, UO, gt, m, px, piv, variant, carry, min_piv, pct):
    start, n = int(gt["start_bar"]), int(gt["n"])
    h = DR.h_of_annual(pct)
    out = {}
    for kind, widen in (("support", -1), ("resistance", +1)):
        pidx, ppx = piv[kind]
        G, L, anc, win = warm_windows(pidx, ppx, np.log(px[kind]), m, UO.K, h, widen, min_piv,
                                      max_window=UO.WINDOW, carry=carry, variant=variant)
        sl = slice(start, start + n)
        Gw = G[sl]
        hon, hg, _lvl = SC.human_mask(gt["lines"], n, kind)
        mon = np.isfinite(Gw)
        both = hon & mon
        cell = SC.score_side(Gw, hg, both, int(hon.sum()), DR.DELTA)
        # median blind head: bars from a window opening to its first drawn point
        opens = np.flatnonzero(anc)
        lags = []
        for oi, o0 in enumerate(opens):
            o1 = opens[oi + 1] if oi + 1 < opens.size else m
            seg = np.flatnonzero(np.isfinite(G[o0:o1]))
            lags.append(int(seg[0]) if seg.size else int(o1 - o0))
        cell["lag_median"] = float(np.median(lags)) if lags else None
        cell["machine_bars_on"] = int(mon.sum())
        cell["precision"] = round(float(both.sum() / max(mon.sum(), 1)), 4)
        cell["machine_segments"] = int(anc[sl].sum())
        out[kind] = cell
    total = float(np.mean([out[k]["score"] for k in ("support", "resistance")]))
    return round(total, 4), out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="equality vs branch E, then stop")
    a = ap.parse_args()

    t0 = time.time()
    DR, SC, UO, gt, m, px, piv = prepare()
    print(f"  {gt['symbol']}: {m} bars loaded in {time.time() - t0:.0f}s; "
          f"scoring window {gt['start_bar']}-{gt['start_bar'] + gt['n']}\n")

    verify(DR, UO, m, px, piv)
    if a.verify:
        return 0
    print()

    MPS = (2, 3, 4, 5)
    HS = (1, 2, 4, 8)
    rows = []
    for variant in ("carry", "pivot"):
        for carry in (0, 1, 2, 3):
            print(f"  variant {variant:>5s}, carry {carry}   " +
                  "".join(f"{'h=' + str(p) + '%':>10s}" for p in HS))
            for mp in MPS:
                cells = []
                for pct in HS:
                    tot, sides = score_one(DR, SC, UO, gt, m, px, piv, variant, carry, mp, pct)
                    rows.append(dict(variant=variant, carry=carry, min_piv=mp, h_annual_pct=pct,
                                     SCORE=tot, sides=sides))
                    cells.append(tot)
                print(f"    min_piv {mp}          " + "".join(f"{c:>10.3f}" for c in cells))
            print()

    rows.sort(key=lambda r: -r["SCORE"])
    best = rows[0]
    print(f"  BEST OF {len(rows)}: variant {best['variant']}, carry {best['carry']}, "
          f"min_piv {best['min_piv']}, h {best['h_annual_pct']}%/yr  ->  SCORE {best['SCORE']:.4f}")
    for k in ("support", "resistance"):
        c = best["sides"][k]
        print(f"    {k:>11s}  agreement {c['agreement']:.4f}  recall {c['recall']:.4f}  "
              f"overlap {c['overlap_bars']:>3d} bars  precision {c['precision']:.3f}  "
              f"machine on {c['machine_bars_on']:>3d}  blind head (median) {c['lag_median']}")
    print("\n  Runners-up:")
    for r in rows[1:6]:
        print(f"    {r['SCORE']:.4f}  {r['variant']:>5s} carry {r['carry']} "
              f"min_piv {r['min_piv']} h {r['h_annual_pct']}%")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(
        what="D399 warm-started dynamic windows, full sweep grid",
        caveat="BEST-OF-N. 2 variants x 4 carries x 4 min_piv x 4 h = 128 cells scored on ONE "
               "hand-drawn window on ONE symbol. The maximum of a sweep needs a floor before it "
               "means anything; no floor is computed here.",
        n_cells=len(rows), rows=rows), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}   ({time.time() - t0:.0f}s total)")
    print("  DIAGNOSTIC / best-of-N. Nothing scored here is admitted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
