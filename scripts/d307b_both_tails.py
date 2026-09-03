"""D307b -- the ex-top-1% test, done symmetrically. A correction to D307.

    uv run python scripts/d307b_both_tails.py

CLAUDE.md's rule is "drop the best 1% and re-report the mean", and it exists
because D285's top 1% was 196.9% of P&L. But the test is ASYMMETRIC, and using
it alone to call a book a lottery is only fair if the left tail is thin. If both
tails are fat, dropping only winners manufactures the conclusion.

The tell was already in D307's own table and was not read: at N=2/target the mean
is +68.1 and the MEDIAN is +94.4. A mean below its median is LEFT-skewed -- the
opposite of a book carried by a few big winners.

Reported here: both one-sided trims, the symmetric trim, and what each tail
actually contributes.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


W = _load("d306", "run_d306_width_exits.py")
D = W.D
OUT = REPO / "data" / "d307b_both_tails.json"

CELLS = (("N=2/target", 2, True), ("N=3/target", 3, True),
         ("N=5/none", 5, False), ("N=7/none", 7, False),
         ("N=19/target", 19, True), ("N=19/none", 19, False))


def tails(pnl):
    p = np.sort(pnl)
    n = p.size
    k = max(1, n // 100)
    tot = p.sum()
    top, bot, mid = p[-k:], p[:k], p[k:-k]
    return dict(
        n=int(n), k=int(k),
        mean=float(p.mean()) * 1e4, median=float(np.median(p)) * 1e4,
        mean_ex_top=float(p[:-k].mean()) * 1e4,
        mean_ex_bottom=float(p[k:].mean()) * 1e4,
        mean_trimmed=float(mid.mean()) * 1e4,
        top_sum_share=float(top.sum() / tot) if tot else None,
        bottom_sum_share=float(bot.sum() / tot) if tot else None,
        top_mean=float(top.mean()) * 1e4, bottom_mean=float(bot.mean()) * 1e4,
        skew=float(((p - p.mean()) ** 3).mean() / p.std() ** 3),
        win_rate=float((p > 0).mean()))


def main() -> int:
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    out = {}
    for name, depth, ut in CELLS:
        r = W.simulate(A, G, depth, ut)
        out[name] = tails(np.array([x[3] for x in r["trades"]]))

    print("BOTH TAILS -- trade P&L in bp\n")
    h = "%-14s %7s %8s %9s %11s %12s %11s"
    print(h % ("cell", "n", "mean", "median", "ex-top-1%", "ex-bottom-1%",
               "trimmed 1%"))
    print("-" * 78)
    for k, v in out.items():
        print(h % (k, "%d" % v["n"], "%+.1f" % v["mean"], "%+.1f" % v["median"],
                   "%+.1f" % v["mean_ex_top"], "%+.1f" % v["mean_ex_bottom"],
                   "%+.1f" % v["mean_trimmed"]))

    print("\nWHAT EACH TAIL CONTRIBUTES")
    h2 = "%-14s %12s %14s %12s %13s %8s %8s"
    print(h2 % ("cell", "top1% share", "bottom1% share", "top1% mean",
                "bottom1% mean", "skew", "win%"))
    print("-" * 88)
    for k, v in out.items():
        print(h2 % (k, "%+.0f%%" % (100 * v["top_sum_share"]),
                    "%+.0f%%" % (100 * v["bottom_sum_share"]),
                    "%+.0f" % v["top_mean"], "%+.0f" % v["bottom_mean"],
                    "%+.2f" % v["skew"], "%.1f%%" % (100 * v["win_rate"])))

    print("\nNET EFFECT OF THE TWO TAILS ON THE MEAN")
    for k, v in out.items():
        dt = v["mean_ex_top"] - v["mean"]
        db = v["mean_ex_bottom"] - v["mean"]
        print("  %-14s dropping winners %+8.1f   dropping losers %+8.1f   "
              "net of the two %+8.1f" % (k, dt, db, dt + db))

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
