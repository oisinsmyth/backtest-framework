"""THE PAIRED TEST: fresh vs hybrid on the IDENTICAL entries, and fixed vs relative stops.

    python working/d528_paired.py --run

Nothing admitted (R15). Reads temp/d528_dec_shards (d528_decouple.py --build).

WHY PAIRED IS THE RIGHT STATISTIC HERE, and it is stronger than the matched control.

`fresh` and `hybrid` share their TRIGGER exactly -- the same bar, the same root, the same day, the
same cost, the same count. The only difference is which bar the level, slope and sigma used for
the target and the stop are read from. So the two arms are the SAME TRADES under two exit
geometries, and the difference can be taken trade by trade. A paired difference removes all of
the between-trade variance that a count-matched control has to average over, which is why the
control in d528_decouple.py can only ever say "these two populations differ"; this says "this
change is worth X per trade, +/- SE".

D1  THE PAIRS are keyed on (root, day, entry bar index). Both arms are asserted to have the same
    number of rows and a perfect key match, or the run raises -- an unmatched key would mean the
    two arms are not the same trades and the whole premise is void.
D2  THE STATISTIC is the mean paired difference in GROSS dollars per trade. Gross, because cost
    is identical within a pair by construction, so net carries no extra information and would
    only invite a cost-driven reading of an exit change.
D3  THE ERROR is a BLOCK BOOTSTRAP over (root, day), 2000 draws, because trades inside a session
    overlap and are not independent. The per-trade SE would be optimistic by roughly the square
    root of the trades-per-session count.
D4  ALSO REPORTED: median and 1%-trimmed mean of the paired difference, because a mean on a
    tail-dominated difference is where a bootstrap is least informative (ADDENDUM 11), and the
    fraction of pairs where the change helps -- a mean carried by a handful of pairs is not a
    geometry improvement.
D5  THE SECOND PAIRING is the stop convention on the SAME arm: noforecast fixed vs relative.
    Same entries again, so the same paired machinery sizes the D11 defect exactly.
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
import d528_decouple as DC                      # noqa: E402

SPLIT = DC.SPLIT
MICRO = list(W.MICRO)
N_BOOT = 2000
SEED = 5281117
KEY = ["root", "day", "i"]


def P(*a):
    print(*a, flush=True)


def load():
    sh = sorted(DC.SHARD.glob("*.parquet"))
    if not sh:
        raise SystemExit(f"no shards in {DC.SHARD}")
    d = pd.concat([pd.read_parquet(x) for x in sh], ignore_index=True)
    return d[d["day"] >= SPLIT]


def paired(d, a, b, uni):
    """The paired difference b - a, on the trades both arms hold. Raises if they are not the
    same trades -- D1: an unmatched key voids the premise, so it must not be silently dropped."""
    x = d[(d["cell"] == a)]
    y = d[(d["cell"] == b)]
    if uni is not None:
        x, y = x[x["root"].isin(uni)], y[y["root"].isin(uni)]
    if len(x) == 0 or len(y) == 0:
        return None
    x = x.set_index(KEY).sort_index()
    y = y.set_index(KEY).sort_index()
    assert len(x) == len(y), f"{a} n={len(x)} vs {b} n={len(y)}: not the same trades"
    assert x.index.equals(y.index), f"{a} / {b}: keys differ, the pairing premise is void"
    dif = (y["gross"] - x["gross"]).to_numpy(float)
    blk = pd.Series(np.arange(len(dif)), index=x.index).groupby(level=[0, 1]).apply(
        lambda s: s.to_numpy())
    groups = [np.asarray(v, int) for v in blk.to_numpy()]
    rng = np.random.default_rng(SEED)
    bs = np.empty(N_BOOT)
    gi = np.arange(len(groups))
    for k in range(N_BOOT):
        pick = rng.integers(0, len(groups), len(groups))
        bs[k] = dif[np.concatenate([groups[j] for j in gi[pick]])].mean()
    lo, hi = np.percentile(dif, [1, 99])
    tm = dif[(dif >= lo) & (dif <= hi)]
    return {"n": len(dif), "blocks": len(groups), "mean": dif.mean(),
            "se": bs.std(ddof=1), "p5": np.percentile(bs, 5), "p95": np.percentile(bs, 95),
            "median": float(np.median(dif)), "trim": float(tm.mean()),
            "help": float((dif > 0).mean()), "za": x["gross"].mean(), "zb": y["gross"].mean()}


def show(title, rows):
    P(title)
    P("      cell pair                              uni      n  blocks    A$     B$    diff$"
      "      SE   boot p5  boot p95  median   trimmed  help%")
    for lab, uni_lab, r in rows:
        if r is None:
            P(f"      {lab:<36} {uni_lab:<6}  -- not present")
            continue
        P(f"      {lab:<36} {uni_lab:<6} {r['n']:>6,} {r['blocks']:>7,} "
          f"{r['za']:>+6.2f} {r['zb']:>+6.2f} {r['mean']:>+8.2f} {r['se']:>7.2f} "
          f"{r['p5']:>+9.2f} {r['p95']:>+9.2f} {r['median']:>+7.2f} {r['trim']:>+9.2f} "
          f"{r['help']:>6.1%}")
    P("")


def run():
    d = load()
    P("THE PAIRED TEST -- same trades, one thing changed")
    P(f"  out of time (>= {SPLIT}); GROSS dollars; block bootstrap over (root, day), "
      f"{N_BOOT} draws")
    P("  A paired difference is reported because both arms hold the SAME entries: cost, count,")
    P("  root mix and session mix are identical by construction, so nothing but the geometry")
    P("  can move the number. That is a stronger statement than the count-matched control.")
    P("")
    unis = ((None, "ALL"), (MICRO, "MICRO"))

    rows = []
    for q in DC.QS:
        for w in (10, 15, 20):
            for sm in DC.STOPS:
                for uni, ul in unis:
                    a = f"fresh_q{q}_w{w}_{sm}"
                    b = f"hybrid_q{q}_w{w}_{sm}"
                    rows.append((f"{a} -> hybrid", ul, paired(d, a, b, uni)))
    show("  (1) FROZEN EXPECTATIONS on identical triggers: fresh -> hybrid (B - A)", rows)

    rows = []
    for cell in ["noforecast"] + [f"fresh_q{q}_w{w}" for q in DC.QS for w in (0, 15)] \
            + [f"hybrid_q{q}_w15" for q in DC.QS]:
        for uni, ul in unis:
            a, b = f"{cell}_fixed", f"{cell}_relative"
            rows.append((f"{cell}: fixed -> relative", ul, paired(d, a, b, uni)))
    show("  (2) THE STOP CONVENTION on identical trades: fixed -> relative (B - A)", rows)

    P("  (3) THE GRACE WINDOW's MARGINAL trades vs the w=0 base they are added to.")
    P("      NOT pairable -- these are different trades -- so it is an unpaired block bootstrap")
    P("      over (root, day) of each mean and of the difference. This is the weaker statistic")
    P("      of the three and is labelled as such.")
    P("      cell                              uni    base n  marg n   base$   marg$    diff$"
      "      SE   boot p5  boot p95")
    rng = np.random.default_rng(SEED + 1)
    for sm in DC.STOPS:
        for q in DC.QS:
            for w in (10, 20):
                for uni, ul in unis:
                    b = d[d["cell"] == f"fresh_q{q}_w0_{sm}"]
                    g = d[d["cell"] == f"fresh_q{q}_w{w}_{sm}"]
                    if uni is not None:
                        b, g = b[b["root"].isin(uni)], g[g["root"].isin(uni)]
                    if len(b) < 100 or len(g) < 200:
                        continue
                    key = set(zip(b["root"], b["day"], b["i"]))
                    m = g[[k not in key for k in zip(g["root"], g["day"], g["i"])]]
                    if len(m) < 100:
                        continue
                    # one bootstrap over the UNION of sessions, resampling sessions and
                    # recomputing BOTH means on the same draw, so the difference keeps its
                    # correlation rather than being built from two independent draws
                    bb = b.groupby(["root", "day"])["gross"].apply(np.array)
                    mm = m.groupby(["root", "day"])["gross"].apply(np.array)
                    sess = sorted(set(bb.index) | set(mm.index))
                    bl = [bb.get(s, np.empty(0)) for s in sess]
                    ml = [mm.get(s, np.empty(0)) for s in sess]
                    dif = np.empty(N_BOOT)
                    for k in range(N_BOOT):
                        p = rng.integers(0, len(sess), len(sess))
                        bv = np.concatenate([bl[j] for j in p])
                        mv = np.concatenate([ml[j] for j in p])
                        dif[k] = (mv.mean() if len(mv) else np.nan) - \
                                 (bv.mean() if len(bv) else np.nan)
                    dif = dif[np.isfinite(dif)]
                    P(f"      fresh_q{q}_w{w}_{sm:<9} marginal      {ul:<6} "
                      f"{len(b):>6,} {len(m):>7,} {b['gross'].mean():>+7.2f} "
                      f"{m['gross'].mean():>+7.2f} "
                      f"{m['gross'].mean() - b['gross'].mean():>+8.2f} {dif.std(ddof=1):>7.2f} "
                      f"{np.percentile(dif, 5):>+9.2f} {np.percentile(dif, 95):>+9.2f}")
    P("")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    else:
        ap.error("choose --run")
