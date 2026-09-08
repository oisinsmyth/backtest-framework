"""D393 -- (a) the ten pre-registered cells, observed; (b) the price-tercile split of the primary.

    uv run python scripts/run_d393_cells_and_price.py --cells --price

BOTH ARE DESCRIPTIVE. No null is drawn, nothing is scored against a hurdle, nothing is admitted
(R15). They exist to answer two questions cheaply before anything expensive is run.

(a) THE TEN CELLS. Section 3 froze 2 shapes x 5 caps and said they are "reported in full and NOT
    picked" (R14's fourth amendment). Only E1/cap-20 has ever been run. Reporting the other nine
    observed values costs ~20 s and settles two things at once:

      - what the cap profile looks like, which section 7's best-of-10 floor will need anyway;
      - whether a LONGER HOLD closes the cost gap, because COST PER TRADE IS ONE ROUND TRIP
        REGARDLESS OF HOLD (~61 bp here) while gross per trade grows with it.

    **THE TRAP IS NAMED BEFORE THE NUMBERS ARE SEEN.** CLAUDE.md: a longer hold lifts breakeven by
    amortising one round trip while per-bar edge usually falls. D289's SEVENTH AMENDMENT makes a
    ratio that clears while the per-bar edge falls versus a shorter cap **HOLD-DRIVEN, not
    clearing**. So every cell carries its per-bar edge beside its ratio, and the renderer flags
    HOLD-DRIVEN itself rather than leaving it to the reader.

    **Reporting all ten is NOT picking one.** If a later record quotes a cell other than the
    pre-registered primary, that is a selection and it owes section 7's best-of-10 floor.

(b) THE PRICE SPLIT. The gap is gross +22.06 against a measured 61.19 bp round trip. Cost in bp
    scales inversely with price (D284), so a price filter is the obvious lever -- and D392 measured
    a **36.8 bp spread** in what a purely RANDOM long earns across price terciles, the widest of
    the three axes. **So the cheap tercile is cheap to earn in and expensive to trade, and the
    honest comparator for a filtered book is the PRICE-CONDITIONAL atlas floor, never the
    unconditional one.** Both are reported per tercile.

    The terciles are built by `run_d392_base_rate_atlas.tercile_pools`, the atlas's OWN
    construction, so the floor and the split are measured on the same partition.

    **This is a diagnostic split of an existing ledger, not a filtered construction.** It says
    whether any price band pays for itself. It does NOT license trading one -- that would be a new
    construction, changing the sample and re-opening all four nulls at a +0.91 bp binding margin.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np


def _rss():
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1e9
    except Exception:
        return float("nan")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "d393_cells_and_price.json"
ATLAS = REPO / "data" / "d392_atlas.json"
CANDIDATE = "up_run_21"
SHAPES = ("E1", "E3")
CAPS = (5, 10, 20, 40, 60)
PRIMARY = ("E1", 20)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", action="store_true")
    ap.add_argument("--price", action="store_true")
    a = ap.parse_args()
    if not (a.cells or a.price):
        ap.error("pass --cells and/or --price")
    t0 = time.time()

    R = _load("d393b", "run_d393_bs_null.py")
    PREP = _load("d348p", "d348_prep.py")
    SG = _load("ragged_sign_scores", "ragged_sign_scores.py")
    V50 = _load("d350r", "run_d350_long_timing_screen.py")
    V59 = _load("d359r", "run_d359_loser_rally_short.py")
    ATL = _load("d392a", "run_d392_base_rate_atlas.py")
    V47 = PREP.V47

    P, elig, cols, masks, dec, T, n, bucket, elig_b = R.build(PREP, V50, SG)
    col = cols[CANDIDATE]
    pct = V47.percentile_grid(col)
    sh = V50.shape_masks(pct, elig)
    sc = np.where(np.isfinite(col), col, 50.0)
    atlas = json.loads(ATLAS.read_text())

    # RAM: the build peaks near 3.1 GB, and everything below needs only P, elig, sh and sc.
    # Dropping the rest takes the steady state to ~0.5 GB while other processes are at work.
    del cols, masks, dec, bucket, elig_b, col, pct
    gc.collect()
    print(f"  build {time.time() - t0:.0f}s, intermediates freed, RSS {_rss():.2f} GB", flush=True)

    primary_res = None                       # the primary cell is simulated ONCE and reused by (b)

    payload = dict(study=393, stage="cells_and_price", score=CANDIDATE,
                   purpose="Descriptive. (a) the ten pre-registered cells observed; (b) the "
                           "price-tercile split of the primary ledger. No null, no hurdle, "
                           "nothing admitted (R15).",
                   primary=list(PRIMARY))

    # ---------------------------------------------------------------- (a)
    if a.cells:
        cells = {}
        for shape in SHAPES:
            mask = sh[shape][0]
            for cap in CAPS:
                res = V59.run_mirror(P, mask, sc, "cap", cap)
                if (shape, cap) == PRIMARY:
                    primary_res = res
                tb = V59.trade_block(P, res, elig, 0, False)
                dep = V59.deployed_block(res, P)["PUB"]["hedged"]
                cells[f"{shape}/cap{cap}"] = dict(
                    shape=shape, cap=cap, events=int(mask.sum()), trades=tb["trades"],
                    gross_bp=tb["mean_bp"], median_bp=tb["median_bp"], t=tb["t"],
                    hold=tb["hold_mean"], per_bar_bp=tb["mean_per_bar_held_bp"],
                    round_trip=tb["two_c"]["PUB"], net_bp=tb["net_per_trade"]["PUB"],
                    ratio=tb["mean_over_2c"]["PUB"],
                    breakeven_hs=tb["breakeven_half_spread_bp_side"],
                    deployed_gross_bp_bar=dep["gross_bp"], deployed_net_bp_bar=dep["net_bp"],
                    exposure=dep.get("exposure"))
                print(f"    {shape}/cap{cap:<3d} {tb['trades']:>7,} trades  "
                      f"gross {tb['mean_bp']:+7.2f}  ratio {tb['mean_over_2c']['PUB']:.2f}x  "
                      f"({time.time() - t0:.0f}s)", flush=True)
        payload["cells"] = cells

    # ---------------------------------------------------------------- (b)
    if a.price:
        pools = ATL.tercile_pools(P, elig)
        # reuse (a)'s primary simulation when it ran; only simulate if --price is used alone
        res = primary_res if primary_res is not None else \
            V59.run_mirror(P, sh[PRIMARY[0]][0], sc, "cap", PRIMARY[1])
        pnl = V47.pnl_bp(res)
        tr = res["trades"]
        band = np.full(len(tr), "none", object)
        for b in ("lo", "mid", "hi"):
            g = pools[f"price_{b}"]
            hit = np.array([bool(g[t[1], t[0]]) for t in tr])
            band[hit] = b
        split = {}
        for b in ("lo", "mid", "hi", "none"):
            sel = band == b
            if not sel.any():
                continue
            sub = [tr[i] for i in np.flatnonzero(sel)]
            cost, half, px = V47.two_c(sub, P["HALF"]["PUB"], P["CLOSE"])
            p_ = pnl[sel]
            comm = 2.0 * V59.PER_SHARE / px * 1e4
            try:
                fl = ATL.lookup(atlas, len(sub), PRIMARY[1], "long", f"price_{b}") if b != "none" \
                    else {"error": "no pool"}
            except (ValueError, KeyError) as e:
                fl = {"error": str(e)[:70]}
            split[b] = dict(trades=int(sel.sum()), gross_bp=float(p_.mean()),
                            median_bp=float(np.median(p_)),
                            t=float(p_.mean() / (p_.std(ddof=1) / np.sqrt(p_.size))),
                            round_trip=float(cost), held_half_spread=float(half),
                            held_price=float(px), net_bp=float(p_.mean() - cost),
                            ratio=float(p_.mean() / cost) if cost else None,
                            breakeven_hs=float((p_.mean() - comm) / 2.0),
                            atlas_floor=fl)
        payload["price_split"] = split

    OUT.write_text(json.dumps(_clean(payload), indent=1))
    print(f"\n  [P] wrote {OUT.relative_to(REPO)} BEFORE rendering", flush=True)
    _render(payload)
    print(f"\n  ({time.time() - t0:.0f}s)  No null was run. Descriptive only; nothing admitted.")
    return 0


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def _render(pl):
    if "cells" in pl:
        print("\n(a) THE TEN PRE-REGISTERED CELLS, OBSERVED -- reported in full, NOT picked\n")
        print(f"  {'cell':<12s} {'trades':>7s} {'gross':>8s} {'median':>8s} {'t':>6s} "
              f"{'hold':>6s} {'per-bar':>8s} {'2c':>7s} {'net':>8s} {'ratio':>7s}")
        prev = {}
        for k, c in pl["cells"].items():
            print(f"  {k:<12s} {c['trades']:>7,} {c['gross_bp']:+8.2f} {c['median_bp']:+8.2f} "
                  f"{c['t']:+6.2f} {c['hold']:6.1f} {c['per_bar_bp']:+8.3f} "
                  f"{c['round_trip']:7.2f} {c['net_bp']:+8.2f} {c['ratio']:7.2f}x")
            prev[k] = c
        print("\n  HOLD-DRIVEN CHECK (D289 seventh amendment): a ratio that rises while the "
              "PER-BAR edge\n  falls versus a shorter cap is HOLD-DRIVEN, not clearing.\n")
        for shape in SHAPES:
            row = [(c, pl["cells"].get(f"{shape}/cap{c}")) for c in CAPS]
            row = [(c, x) for c, x in row if x]
            for i in range(1, len(row)):
                c0, a0 = row[i - 1]
                c1, a1 = row[i]
                dr = a1["ratio"] - a0["ratio"]
                dp = a1["per_bar_bp"] - a0["per_bar_bp"]
                tag = ("HOLD-DRIVEN" if dr > 0 and dp < 0 else
                       "both up" if dr > 0 and dp >= 0 else "ratio down")
                print(f"      {shape} cap {c0:>2d} -> {c1:<2d}  ratio {dr:+.3f}  "
                      f"per-bar {dp:+.4f}   {tag}")
    if "price_split" in pl:
        print("\n(b) PRICE-TERCILE SPLIT of the primary ledger (E1, cap 20) -- DIAGNOSTIC\n")
        print(f"  {'band':<6s} {'trades':>7s} {'price':>8s} {'gross':>8s} {'half-sp':>8s} "
              f"{'2c':>7s} {'net':>8s} {'ratio':>7s} {'bkeven':>8s}  atlas floor")
        for b, d in pl["price_split"].items():
            fl = d["atlas_floor"]
            fs = (f"{fl['p95']:+.2f}+/-{fl['se_p95']:.2f}" if "p95" in fl
                  else f"n/a ({fl.get('error', '')[:28]})")
            print(f"  {b:<6s} {d['trades']:>7,} {d['held_price']:8.2f} {d['gross_bp']:+8.2f} "
                  f"{d['held_half_spread']:8.2f} {d['round_trip']:7.2f} {d['net_bp']:+8.2f} "
                  f"{d['ratio']:7.2f}x {d['breakeven_hs']:+8.2f}  {fs}")
        print("\n  A band's gross must beat its OWN price-conditional floor, never the "
              "unconditional one:\n  D392 measured a 36.8 bp spread across these terciles for a "
              "purely RANDOM long.")


if __name__ == "__main__":
    raise SystemExit(main())
