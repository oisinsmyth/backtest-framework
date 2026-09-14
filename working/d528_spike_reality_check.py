"""ARE THE SPIKE ENTRIES REAL PRICES, OR QUOTE ARTEFACTS?

    python working/d528_spike_reality_check.py --self-test
    python working/d528_spike_reality_check.py --run

Nothing admitted (R15). In sample only; reserved slice UNREAD. **No holdout is spent** -- this
reads the 5-minute TRADE fixture, which is a different fixture from the 1-minute quoted mid the
detector runs on, over the same days.

THE QUESTION. `d528_detector_diagnosis.py` found that the detector's best cell is a SINGLE-BAR
SPIKE out of a quiet window -- quiet + sudden + jump cleared its matched control at every rung
(gross +$3.66 on n=130 against a p95 of +$2.65). That is also the textbook signature of a
MOMENTARY WIDE OR STALE QUOTE: the mid jumps because one side of the book vanished for a few
seconds, and no tradeable price ever existed there. D523 has already burned this programme on
bid-ask effects, so the cell must be verified before it is believed.

THE TEST. The detector runs on `fut_day1m_mid` -- the quoted MID. `fut_day5m` carries true OHLC
built from TRADES over the same sessions. So for every entry:

    find the 5-minute TRADE bar containing the entry minute
    ask whether the entry's mid price lies inside that bar's [low, high]

A real price prints. **If the mid sat outside the range of every trade in its own 5-minute window,
no trade happened there and the price was never available.** Reported as `outside_rate`, and the
distance outside is reported in ticks so a marginal miss is not confused with a wild one.

TWO CONTROLS, because an outside-rate means nothing on its own:

  1. THE POOL. Every candidate, not just the spike cell. If the spike cell is no more often
     outside than the pool, suddenness is not buying artefacts.
  2. A RANDOM MINUTE in the same session. The mid and the trade range are different objects --
     the mid can sit outside a thin bar's range legitimately -- so the base rate must be measured
     on minutes the detector never chose.

AND THE SPREAD REGIME, from `fut_crossing_tbbo` (root x day x hour): the volume-weighted spread in
the hour containing each entry. If spike entries land in hours whose spread is much wider than
the session norm, the mid is less trustworthy there regardless of the range test.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_detector_diagnosis as D             # noqa: E402

FIVE = "data/fixtures/fut_day5m.parquet"
TBBO = "data/fixtures/fut_crossing_tbbo.csv.gz"
SEED = 528787


def P(*a):
    print(*a, flush=True)


def load_five(roots, days):
    f = pd.read_parquet(FIVE, columns=["root", "day", "bar", "high", "low", "volume",
                                       "n", "present"])
    f = f[f["root"].isin(roots) & f["day"].isin(days)]
    return {(r, d, b): (hi, lo, v, nn)
            for r, d, b, hi, lo, v, nn in zip(f["root"], f["day"], f["bar"], f["high"],
                                              f["low"], f["volume"], f["n"])}


def load_spread(roots, days):
    t = pd.read_csv(TBBO)
    t = t[t["root"].isin(roots) & t["day"].isin(days)]
    # volume-weighted mean spread per (root, day, hour)
    t["wsum"] = t["spread_tk"] * t["vol"]
    g = t.groupby(["root", "day", "hour"], as_index=False).agg(
        wsum=("wsum", "sum"), vol=("vol", "sum"))
    g["sp"] = g["wsum"] / g["vol"].replace(0, np.nan)
    return {(r, d, h): s for r, d, h, s in zip(g["root"], g["day"], g["hour"], g["sp"])}


def outside(entry_min, root, day, mid, tick, five):
    """(is_outside, distance_in_ticks, bar_volume). The 5-min bar covering this minute.

    The 1-minute fixture's `bar` is 0..419 from DAY_LO; the 5-minute fixture's is 0..83 over the
    same band, so bar5 = bar1 // 5.
    """
    b5 = entry_min // 5
    rec = five.get((root, day, b5))
    if rec is None:
        return None
    hi, lo, vol, nn = rec
    if not np.isfinite(hi) or not np.isfinite(lo):
        return None
    if mid > hi:
        return (True, (mid - hi) / tick, vol)
    if mid < lo:
        return (True, (lo - mid) / tick, vol)
    return (False, 0.0, vol)


def self_test():
    # 1. THE BAR MAPPING. minute 0..4 -> 5-min bar 0; 5..9 -> 1; 419 -> 83.
    for m, want in ((0, 0), (4, 0), (5, 1), (9, 1), (100, 20), (419, 83)):
        assert m // 5 == want, f"minute {m} -> bar {m//5}, wanted {want}"
    P("   [1] minute -> 5-minute bar mapping: 0->0, 4->0, 5->1, 419->83               OK")

    # 2. THE OUTSIDE TEST must fire in BOTH directions and stay silent inside the range.
    five = {("T", "d", 2): (101.0, 99.0, 500, 20)}
    hi = outside(10, "T", "d", 102.0, 0.25, five)
    lo = outside(10, "T", "d", 98.0, 0.25, five)
    inn = outside(10, "T", "d", 100.0, 0.25, five)
    assert hi[0] and abs(hi[1] - 4.0) < 1e-9, hi
    assert lo[0] and abs(lo[1] - 4.0) < 1e-9, lo
    assert not inn[0] and inn[1] == 0.0, inn
    P(f"   [2] outside test: above -> {hi[1]:.1f} tk, below -> {lo[1]:.1f} tk, "
      f"inside -> {inn[1]:.1f} tk   OK")

    # 3. AND IT MUST RETURN None WHERE THERE IS NO TRADE BAR, rather than silently scoring it as
    #    inside -- a missing bar is not evidence the price was available.
    assert outside(10, "T", "d", 100.0, 0.25, {}) is None
    P("   [3] a missing 5-minute bar returns None, not a false 'inside'                OK")
    P("\n   all self-tests pass\n")


def run():
    rng = np.random.default_rng(SEED)
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    rev_day = {i: u for u, i in day_index.items()}

    P("ARE THE SPIKE ENTRIES REAL PRICES, OR QUOTE ARTEFACTS?")
    P(f"  detector runs on the 1-minute quoted MID; this checks it against 5-minute TRADE OHLC")
    P(f"  {len(roots)} roots, {len(udays)} sessions, in sample only\n")

    pool = D.collect(d, sp, roots, day_index)
    five = load_five(roots, udays)
    spread = load_spread(roots, udays)
    P(f"  pool {len(pool):,} candidates; 5-minute trade bars loaded {len(five):,}")

    # attach the entry's own mid price and minute
    mid_lookup = {}
    for r in roots:
        gg = d[d["root"] == r]
        for day, pth, b0 in __import__("d528_book_and_sides").sessions_with_bars(gg, 1):
            mid_lookup[(r, day)] = (pth, b0)

    def entry_info(z):
        bar = z["t_in"] - z["day"] * 2000
        rec = mid_lookup.get((z["root"], rev_day[z["day"]]))
        if rec is None:
            return None
        pth, b0 = rec
        i = bar - b0
        if not (0 <= i < len(pth)):
            return None
        return bar, float(pth[i])

    def score(rows, label):
        n_out = n_tot = 0
        dists, vols, sps = [], [], []
        for z in rows:
            ei = entry_info(z)
            if ei is None:
                continue
            bar, mid = ei
            tick = sp[z["root"]]["tick_price_units"]
            o = outside(bar, z["root"], rev_day[z["day"]], mid, tick, five)
            if o is None:
                continue
            n_tot += 1
            n_out += int(o[0])
            if o[0]:
                dists.append(o[1])
            vols.append(o[2])
            hh = (Q.DAY_LO + bar) // 60
            s = spread.get((z["root"], rev_day[z["day"]], hh))
            if s is not None and np.isfinite(s):
                sps.append(s)
        if n_tot == 0:
            return None
        return {"label": label, "n": n_tot, "rate": n_out / n_tot,
                "med_dist": float(np.median(dists)) if dists else 0.0,
                "p90_dist": float(np.percentile(dists, 90)) if dists else 0.0,
                "med_vol": float(np.median(vols)) if vols else np.nan,
                "med_spread": float(np.median(sps)) if sps else np.nan}

    def f_quiet(z):
        return np.isfinite(z["vol_ratio"]) and z["vol_ratio"] < 0.913

    def f_sudden(z):
        return np.isfinite(z["frac_last"]) and z["frac_last"] > 0.8

    def f_jump(z):
        return np.isfinite(z["jump"]) and z["jump"] > 3

    CELLS = (
        ("the whole pool", lambda z: True),
        ("traverse (causal)", lambda z: z["trav"]),
        ("sudden only", f_sudden),
        ("quiet + sudden", lambda z: f_quiet(z) and f_sudden(z)),
        ("quiet + sudden + jump", lambda z: f_quiet(z) and f_sudden(z) and f_jump(z)),
        ("GRADUAL (the opposite)", lambda z: np.isfinite(z["frac_last"]) and z["frac_last"] <= 0.5),
    )

    P("")
    P("=" * 104)
    P("1  DID A TRADE EVER PRINT THERE? mid vs the [low, high] of its own 5-minute trade bar")
    P("")
    P("    cell                        n   OUTSIDE the trade range   median tk   p90 tk"
      "   5m volume   spread tk")
    base = None
    for label, fn in CELLS:
        rows = [z for z in pool if fn(z)]
        s = score(rows, label)
        if s is None or s["n"] < 20:
            continue
        if label == "the whole pool":
            base = s
        P(f"    {label:<24} {s['n']:>5,} {s['rate']:>22.1%} {s['med_dist']:>11.2f} "
          f"{s['p90_dist']:>8.2f} {s['med_vol']:>11,.0f} {s['med_spread']:>11.2f}")

    # the random-minute control: minutes the detector never chose
    P("")
    P("=" * 104)
    P("2  THE BASE RATE on minutes the detector never chose (same sessions, random bars)")
    P("")
    ctrl = []
    for _ in range(4000):
        r = roots[rng.integers(0, len(roots))]
        dy = udays[rng.integers(0, len(udays))]
        rec = mid_lookup.get((r, dy))
        if rec is None:
            continue
        pth, b0 = rec
        i = int(rng.integers(0, len(pth)))
        ctrl.append({"root": r, "day": day_index[dy], "t_in": day_index[dy] * 2000 + b0 + i})
    cs = score(ctrl, "random minutes")
    if cs:
        P(f"    random minutes           {cs['n']:>5,} {cs['rate']:>22.1%} "
          f"{cs['med_dist']:>11.2f} {cs['p90_dist']:>8.2f} {cs['med_vol']:>11,.0f} "
          f"{cs['med_spread']:>11.2f}")
    if base:
        P("")
        P(f"    the pool is {base['rate']:.1%} outside against a base rate of "
          f"{cs['rate']:.1%} on unchosen minutes." if cs else "")
    P("")
    P("  READING IT. A mid can legitimately sit outside a thin 5-minute trade range, so the")
    P("  LEVEL of `outside` means little -- the CONTRASTS do. If the spike cells are outside far")
    P("  more often than the pool and than unchosen minutes, the cell is quote artefact and its")
    P("  apparent edge is unfillable. If they are not, suddenness is buying real prices.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.run:
        run()
    if not (a.self_test or a.run):
        ap.error("choose --self-test or --run")
