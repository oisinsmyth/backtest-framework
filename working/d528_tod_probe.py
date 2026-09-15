"""WAS THE EDGE A TIME-OF-DAY EFFECT THE OLD ROOM MASK ACCIDENTALLY SELECTED?

    python working/d528_tod_probe.py --run

Nothing admitted (R15). Reads temp/d528_dec_shards (the ADDENDUM 14 build, whose room mask kept
the session's FIRST 24 candidate bars) and temp/d528_dec_retrace_shards (the corrected mask,
bars 20-34).

WHY THIS IS BEING RUN. The corrected R2 mask moved the eligible signal bars from [0, 24) to
[20, 34) and micro gross fell from -$1.11 to -$3.23 on a comparable cell. Two explanations:

    (a) TIME OF DAY -- the reversion is concentrated near the open, so the old mask was
        accidentally selecting the good window and every published D528 per-trade figure is
        flattered by it. This would be the single largest thing found in the study.
    (b) something else about the two runs differs and the comparison is invalid.

(b) is checked FIRST and it is checked by construction: this probe reads ONE cell from the
ADDENDUM 14 shards and splits it by the signal bar index alone. The comparison is then internal
to a single arm on a single build, so nothing but the bar position can move it -- no mask, no
cost line, no universe, no stop convention.

T1  THE SPLIT is on `i`, the classify2 index, which equals the session bar minus 2H (= 20). So
    i = 0 is bar 20 of the session, roughly 11:10 ET on a 09:30 open with 5-minute bars, and
    i = 23 is bar 43, roughly 13:05. The old mask's window was NOT the opening bars -- it was
    late morning to early afternoon -- and that is worth knowing before any story is told about
    the open.
T2  THE ARM is fresh_q25_w0_relative and noforecast_relative: the coupled arm and the
    unconditional one, both at the relative stop, so the split is on the two most-populated
    cells available.
T3  BOTH UNIVERSES, and the per-bucket n is printed, because a 24-bar window split four ways on
    micro leaves a few hundred trades a bucket.
T4  THE STATISTIC is mean GROSS dollars with a block bootstrap over (root, day) for the
    early-vs-late difference, plus median and trimmed mean. Gross, because cost does not vary
    with bar position within a root.
T5  THE OVERLAP CELL is reported separately: bars [20, 24) are in BOTH masks, so if the two
    builds agree there, the builds are comparable and the difference really is bar position.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_wide as W                           # noqa: E402

SPLIT = "2020-01-01"
MICRO = list(W.MICRO)
OLD = Path("temp/d528_dec_shards")
NEW = Path("temp/d528_dec_retrace_shards")
N_BOOT = 2000
SEED = 5281409
H2 = 20                                          # 2H: i = 0 is session bar 20


def P(*a):
    print(*a, flush=True)


def rd(p, cols=None):
    sh = sorted(p.glob("*.parquet"))
    if not sh:
        raise SystemExit(f"no shards in {p}")
    d = pd.concat([pd.read_parquet(x, columns=cols) for x in sh], ignore_index=True)
    return d[d["day"] >= SPLIT]


def boot_diff(a, b):
    """Block bootstrap over (root, day) of mean(b) - mean(a), resampling sessions ONCE and
    recomputing both means on the same draw so the difference keeps its correlation."""
    ga = a.groupby(["root", "day"])["gross"].apply(np.array)
    gb = b.groupby(["root", "day"])["gross"].apply(np.array)
    sess = sorted(set(ga.index) | set(gb.index))
    la = [ga.get(s, np.empty(0)) for s in sess]
    lb = [gb.get(s, np.empty(0)) for s in sess]
    rng = np.random.default_rng(SEED)
    out = np.empty(N_BOOT)
    for k in range(N_BOOT):
        p = rng.integers(0, len(sess), len(sess))
        va = np.concatenate([la[j] for j in p])
        vb = np.concatenate([lb[j] for j in p])
        out[k] = (vb.mean() if len(vb) else np.nan) - (va.mean() if len(va) else np.nan)
    out = out[np.isfinite(out)]
    return out.std(ddof=1), np.percentile(out, 5), np.percentile(out, 95)


def run():
    # the two builds do not carry the same columns -- the ADDENDUM 14 build emits only fills,
    # so it has no `filled` flag at all. Read each with its own list rather than a shared one.
    old = rd(OLD, ["cell", "day", "root", "i", "gross", "cost", "kind"])
    new = rd(NEW, ["cell", "day", "root", "i", "gross", "cost", "kind", "filled"])
    P("WAS THE EDGE A TIME-OF-DAY EFFECT THE OLD ROOM MASK SELECTED?")
    P("")
    P("  T1 the split is on i (classify2 index); session bar = i + 20, so i=0 is the 21st bar")
    P("     of the session -- about 11:10 ET. The OLD mask's window [0,24) was LATE MORNING to")
    P("     EARLY AFTERNOON, not the open. The corrected window [20,34) is ~13:00-14:10.")
    P("  T4 block bootstrap over (root, day), 2000 draws, on mean GROSS dollars")
    P("")
    for cell in ("noforecast_relative", "fresh_q25_w0_relative"):
        g0 = old[(old["cell"] == cell)]
        if len(g0) < 400:
            continue
        P("=" * 108)
        P(f"OLD BUILD, cell {cell} -- split by session bar position")
        P("")
        P("      universe   bars        n   gross$   median  trimmed   P(tgt)")
        for uni, ul in ((None, "ALL"), (MICRO, "MICRO")):
            g = g0 if uni is None else g0[g0["root"].isin(uni)]
            buckets = [(0, 6), (6, 12), (12, 18), (18, 24)]
            for (a, b) in buckets:
                m = g[(g["i"] >= a) & (g["i"] < b)]
                if len(m) < 50:
                    continue
                gr = m["gross"].to_numpy(float)
                lo, hi = np.percentile(gr, [1, 99])
                tm = gr[(gr >= lo) & (gr <= hi)]
                P(f"      {ul:<9} {a+H2:>2}-{b+H2:<3} {len(m):>8,} {gr.mean():>+8.2f} "
                  f"{np.median(gr):>+8.1f} {tm.mean():>+8.2f} "
                  f"{(m['kind'] == 0).mean():>8.1%}")
            e = g[(g["i"] >= 0) & (g["i"] < 12)]
            l = g[(g["i"] >= 12) & (g["i"] < 24)]
            if len(e) > 100 and len(l) > 100:
                se, p5, p95 = boot_diff(e, l)
                P(f"      {ul:<9} LATE - EARLY  "
                  f"{l['gross'].mean() - e['gross'].mean():>+8.2f}  SE {se:>5.2f}  "
                  f"boot p5 {p5:>+6.2f}  p95 {p95:>+6.2f}"
                  f"   n {len(e):,} / {len(l):,}")
            P("")
    # T5: the overlap. Bars [20,24) of the session are i in [0,4) OLD and i in [20,24) NEW.
    P("=" * 108)
    P("T5 -- THE OVERLAP CHECK. Session bars 40-44 are i in [20,24) of BOTH builds, so if the")
    P("   two builds disagree THERE, the builds are not comparable and nothing above holds.")
    P("")
    P("      universe        build        n   gross$   median   P(tgt)")
    for uni, ul in ((None, "ALL"), (MICRO, "MICRO")):
        for lab, src, cell in (("ADDENDUM 14", old, "fresh_q25_w0_relative"),
                               ("corrected  ", new, "market0.00_x2.0_q25_w0")):
            g = src[src["cell"] == cell]
            if uni is not None:
                g = g[g["root"].isin(uni)]
            if "filled" in g:
                g = g[g["filled"].fillna(1.0) > 0.5]
            m = g[(g["i"] >= 20) & (g["i"] < 24)]
            if len(m) < 30:
                P(f"      {ul:<9} {lab}  {len(m):>7,}   too few")
                continue
            gr = m["gross"].to_numpy(float)
            P(f"      {ul:<9} {lab}  {len(m):>7,} {gr.mean():>+8.2f} {np.median(gr):>+8.1f} "
              f"{(m['kind'] == 0).mean():>8.1%}")
        P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    else:
        ap.error("choose --run")
