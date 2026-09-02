"""D286 follow-up -- WHAT does the -5% cap actually fire on?

    uv run python scripts/d286_cap_mechanism.py

NOTHING HERE SCORES A CELL. It attributes trades D286 already scored.

THE CLAIM THIS EXISTS TO CHECK IS MINE, AND IT WAS UNSUPPORTED. Reporting D286
I wrote that the cap "cut the winners with it". What I had MEASURED was the
symptom -- mean 36.44 -> 15.86 bp, median +82.11 -> -14.69, breakeven 14.35 ->
3.03 -- not the mechanism. Whether the cap fires on trades that would have
RECOVERED is a different question and it is answerable directly.

THE TEST. Walk every `disp` trade -- the uncapped book -- and for each one record
its RUNNING CUMULATIVE return and its FINAL outcome. Then split:

    TOUCHED   the trade's running cumulative return reached -5% at some point
    CLEAN     it never did

For the touched set, report what those trades WENT ON TO EARN under `disp`. That
is exactly what the cap gave up, because the cap exits them at -5% and blocks
re-entry until the name leaves the extreme.

    if the touched set ends NEGATIVE on average   the cap cut losers, and the
                                                  damage is elsewhere
    if it ends POSITIVE                           the cap cut recoveries, and
                                                  "it cut winners" is earned

**Neither outcome generalises to other stops on other books.** A stop is
destructive exactly when the path of a typical winner passes through the
trigger, and that is a property of THIS book's path distribution, not of stops.
The report is therefore about this cap on this construction and says so.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
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


B = _load("d256", "run_book_single_names.py")
EX = _load("d286", "run_exit_rules.py")
RP = B.RP

OUT = REPO / "data" / "d286_cap_mechanism.json"
CAP = EX.LOSS_CAP
N = 10


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=EX.FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    simple = np.expm1(panel.total_log_returns)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm & panel.live
    base = np.where(ok, 1.0, 0.0)
    base[:, 0] = 0.0
    pos = RP.enforce_live(EX.walk_exits(base, hs, N, "disp", simple=simple), panel, 0)
    sgn_grid = np.sign(pos)
    print(f"loaded {time.time() - t0:.0f}s", flush=True)

    finals, touched, mins, runs, bars_to_touch = [], [], [], [], []
    n, T = pos.shape
    for i in range(n):
        row = sgn_grid[i]
        t = 0
        while t < T:
            if row[t] == 0.0:
                t += 1
                continue
            sgn, cum, lo, k, hit = row[t], 0.0, 0.0, 0, -1
            while t < T and row[t] == sgn:
                r = simple[i, t]
                if np.isfinite(r):
                    cum += sgn * r
                if cum < lo:
                    lo = cum
                if hit < 0 and cum <= CAP:
                    hit = k
                k += 1
                t += 1
            finals.append(cum)
            touched.append(hit >= 0)
            mins.append(lo)
            runs.append(k)
            bars_to_touch.append(hit)

    f = np.array(finals)
    tch = np.array(touched)
    print(f"  {f.size:,} `disp` trades walked\n", flush=True)

    print(f"  THE -5% CAP ON THIS BOOK. `disp` is the uncapped book; TOUCHED means")
    print(f"  the running loss reached {CAP:.0%} at some point during the trade.\n")
    print(f"  {'':22s} {'n':>8s} {'share':>7s} {'mean bp':>9s} {'median bp':>10s} "
          f"{'win rate':>9s} {'run':>6s}")
    rows = {}
    for label, m in (("ALL disp trades", np.ones_like(tch, dtype=bool)),
                     ("TOUCHED -5%", tch), ("never touched", ~tch)):
        if m.sum() == 0:
            continue
        v = f[m]
        rows[label] = {"n": int(m.sum()), "share": float(m.mean()),
                       "mean_bp": float(v.mean() * 1e4),
                       "median_bp": float(np.median(v) * 1e4),
                       "win_rate": float((v > 0).mean()),
                       "mean_run": float(np.mean(np.array(runs)[m]))}
        print(f"  {label:22s} {m.sum():8,d} {m.mean():6.1%} {v.mean() * 1e4:+9.2f} "
              f"{np.median(v) * 1e4:+10.2f} {(v > 0).mean():8.1%} "
              f"{np.mean(np.array(runs)[m]):6.2f}")

    t_final = f[tch]
    recovered = float((t_final > 0).mean()) if t_final.size else float("nan")
    give_up = float(t_final.mean() * 1e4) if t_final.size else float("nan")
    print(f"\n  WHAT THE CAP GIVES UP. It exits a TOUCHED trade at {CAP:.0%} and")
    print(f"  blocks re-entry, so it forgoes whatever that trade went on to do:")
    print(f"    touched trades that end PROFITABLE   {recovered:6.1%}")
    print(f"    mean final outcome of touched trades {give_up:+7.2f} bp")
    print(f"    capped exit books instead            {CAP * 1e4:+7.2f} bp")
    print(f"    difference per touched trade         {give_up - CAP * 1e4:+7.2f} bp")

    # ---------------- the distributions, side by side ----------------
    def moments(v):
        m, sd = float(v.mean()), float(v.std(ddof=1))
        z = (v - m) / sd if sd > 0 else v * 0.0
        return m, sd, float((z ** 3).mean()), float((z ** 4).mean())

    pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print(f"\n  THE DISTRIBUTIONS, in bp. This is what the cap removes against what")
    print(f"  the book is made of.\n")
    print(f"  {'percentile':>14s} " + " ".join(f"{q:>8d}" for q in pcts))
    dist = {}
    for label, m in (("ALL disp trades", np.ones_like(tch, dtype=bool)),
                     ("TOUCHED -5%", tch), ("never touched", ~tch)):
        v = f[m] * 1e4
        dist[label] = {f"p{q}": float(np.percentile(v, q)) for q in pcts}
        print(f"  {label:>14s} " + " ".join(f"{np.percentile(v, q):8.0f}" for q in pcts))

    print(f"\n  {'':>14s} {'mean':>9s} {'sd':>9s} {'skew':>8s} {'kurt':>8s} "
          f"{'P&L share':>10s}")
    tot = float(f.sum())
    for label, m in (("ALL disp trades", np.ones_like(tch, dtype=bool)),
                     ("TOUCHED -5%", tch), ("never touched", ~tch)):
        v = f[m] * 1e4
        mu, sd, sk, ku = moments(v)
        share = float(f[m].sum() / tot) if tot else float("nan")
        dist[label].update({"mean": mu, "sd": sd, "skew": sk, "kurtosis": ku,
                            "pnl_share": share})
        print(f"  {label:>14s} {mu:9.1f} {sd:9.1f} {sk:+8.2f} {ku:8.1f} "
              f"{share:9.1%}")

    # ---------------- where ANY threshold would bite ----------------
    mn = np.array(mins) * 1e4
    print(f"\n  RUNNING MINIMUM of every `disp` trade, bp -- where a cap of any")
    print(f"  level would fire. A DIAGNOSTIC on scored trades; acting on it needs")
    print(f"  its own pre-registration, because picking a level off this curve is")
    print(f"  fitting.\n")
    print(f"  {'cap level bp':>13s} {'touched':>9s} {'their mean':>11s} "
          f"{'cap books':>10s} {'gain/trade':>11s} {'book-wide':>10s}")
    sweep = {}
    for lvl in (-200, -300, -500, -750, -1000, -1500, -2000):
        hit = mn <= lvl
        if hit.sum() < 50:
            continue
        got = float(f[hit].mean() * 1e4)
        gain = lvl - got
        sweep[lvl] = {"share": float(hit.mean()), "their_mean_bp": got,
                      "gain_per_touched_bp": gain,
                      "book_wide_bp": float(gain * hit.mean())}
        print(f"  {lvl:13d} {hit.mean():8.1%} {got:11.1f} {lvl:10d} "
              f"{gain:+11.1f} {gain * hit.mean():+10.1f}")
    print(f"\n  `book-wide` is the gain per touched trade times the share touched --")
    print(f"  the mean bp a cap at that level adds BEFORE any turnover cost, which")
    print(f"  is the term that sank the -5% arm.")

    verdict = ("CUT RECOVERIES -- the touched set ends POSITIVE on average, so "
               "'it cut winners' is earned" if give_up > 0 else
               "CUT LOSERS -- the touched set ends NEGATIVE on average, so the "
               "damage is NOT truncated recoveries and my wording was wrong")
    print(f"\n  VERDICT: the cap {verdict}.")
    print(f"\n  THIS DOES NOT GENERALISE. A stop is destructive exactly when a")
    print(f"  typical winner's PATH passes through the trigger, which is a property")
    print(f"  of this book's path distribution, not of stops.")

    json.dump({"purpose": ("what the -5% cap fires on; attributes trades D286 "
                           "already scored, scores no cell"),
               "cap": CAP, "n_levels": N, "rows": rows,
               "touched_share": float(tch.mean()),
               "touched_recovered_share": recovered,
               "touched_mean_final_bp": give_up,
               "distributions": dist, "threshold_sweep": sweep,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
