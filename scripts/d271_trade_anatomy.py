"""D271 -- trade-level anatomy of the three null-surviving constructions.

    uv run python scripts/d271_trade_anatomy.py

DESCRIPTIVE. No hurdle is run, no cell scored, no rule proposed. This takes
constructions ALREADY measured and reports the distribution of their individual
trades, because every number reported so far has been a mean and a mean cannot
distinguish a broad edge from one that lives in a handful of trades.

THE THREE, and why these three:

  LOW:S2_short_intra    D264 hurdle H, BOTH legs: 97.2th / 97.9th
  HIGH:S1_short_intra   D264 hurdle H, BOTH legs: 96.9th / 99.7th
  LOW:rel_vol Q5        D270 M1 (monotone 5/5) and M3 (3.68 bp vs a 2.56 floor)

Nothing else in the programme survives a properly-constructed null.

**THE rel_vol ARM IS AN ANATOMY OF AN ALREADY-MEASURED BUCKET, NOT A NEW BOOK.**
D270 measured the mean forward move of the Q5 bucket; this shows the
distribution behind that mean. No new cell is scored and D270's stop is not
reopened.

WHAT IS COMPUTED, and why each earns its place:

  P&L DISTRIBUTION      the ask. Reported GROSS, with the round-trip cost drawn
                        on it, because gross-vs-cost is the whole question
  SKEW and KURTOSIS     a short should be negatively skewed -- small wins, rare
                        large losses. Positive skew in a short book means the
                        edge lives in the tail and is fragile
  TAIL CONCENTRATION    share of total P&L from the top 5% of trades. If the
                        answer is most of it, the mean is not describing a
                        repeatable process
  P&L BY YEAR           FINDINGS 6: measured effects in this programme are
                        frequently one era, and this sample contains 2020
  PER SYMBOL            four names is not four independent bets; R10 applies
  BY ENTRY BUCKET       D265 found EARLY entries carry S2 entirely
"""

from __future__ import annotations

import importlib.util
import json
import math
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


V = _load("d270", "run_volume_structure.py")
C, I, R, M, D = V.C, V.I, V.R, V.M, V.D

OUT = REPO / "data" / "d271_trade_anatomy.json"
H_VOL = 8


def session_maps(first, T):
    starts = list(np.flatnonzero(first)) + [T]
    sess_end = np.empty(T, dtype=int)
    for a, b in zip(starts[:-1], starts[1:]):
        sess_end[a:b] = b
    bod = np.empty(T, dtype=int)
    k = 0
    for t in range(T):
        k = 0 if first[t] else k + 1
        bod[t] = k
    return sess_end, bod


def book_trades(pos, rets, dates, syms, start, sess_end, bod):
    """One record per trade, using the BOOK'S OWN exit. Short P&L = -(returns)."""
    out = []
    for i in range(pos.shape[0]):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        for t in ent:
            close = int(sess_end[t])
            z = np.flatnonzero(s[t:close] == 0.0)
            ex = t + int(z[0]) if z.size else close
            out.append({"symbol": syms[i], "date": dates[t][:10], "year": dates[t][:4],
                        "bod": int(bod[t]), "bars": int(ex - t),
                        "pnl_bp": float(-rets[i, t:ex].sum()) * 1e4})
    return out


def score_trades(score, rets, dates, syms, start, sess_end, bod, q=4, n_q=5):
    """Entries where the LAGGED score sits in its top quintile, held H bars."""
    out = []
    n, T = score.shape
    for i in range(n):
        s = score[i, start - 1:T - 1]
        ok = np.isfinite(s)
        if ok.sum() < 100:
            continue
        edges = np.quantile(s[ok], np.linspace(0, 1, n_q + 1)[1:-1])
        for j in np.flatnonzero(ok):
            if np.searchsorted(edges, s[j], side="right") != q:
                continue
            t = start + j
            e = min(int(sess_end[t]), t + H_VOL)
            if e <= t:
                continue
            out.append({"symbol": syms[i], "date": dates[t][:10], "year": dates[t][:4],
                        "bod": int(bod[t]), "bars": int(e - t),
                        "pnl_bp": float(-rets[i, t:e].sum()) * 1e4})
    return out


def describe(tr, cost_bp):
    p = np.array([x["pnl_bp"] for x in tr])
    w, l = p[p > 0], p[p < 0]
    srt = np.sort(p)[::-1]
    top5 = max(1, int(round(0.05 * len(p))))
    tot = p.sum()
    mu, sd = float(p.mean()), float(p.std(ddof=1))
    z = (p - mu) / sd if sd > 0 else p * 0
    by_year, by_sym, by_bod = {}, {}, {}
    for x in tr:
        by_year.setdefault(x["year"], []).append(x["pnl_bp"])
        by_sym.setdefault(x["symbol"], []).append(x["pnl_bp"])
        b = "EARLY" if x["bod"] <= 8 else ("MID" if x["bod"] <= 17 else "LATE")
        by_bod.setdefault(b, []).append(x["pnl_bp"])
    return {
        "n": len(p), "cost_bp": cost_bp,
        "mean_bp": mu, "median_bp": float(np.median(p)), "sd_bp": sd,
        "mean_vs_cost": mu / cost_bp,
        "hit_rate": float((p > 0).mean()),
        "avg_win_bp": float(w.mean()) if w.size else 0.0,
        "avg_loss_bp": float(-l.mean()) if l.size else 0.0,
        "payoff": float(w.mean() / -l.mean()) if l.size and w.size else None,
        "skew": float((z ** 3).mean()), "kurtosis": float((z ** 4).mean()),
        "percentiles": {str(q): float(np.percentile(p, q))
                        for q in (1, 5, 25, 50, 75, 95, 99)},
        "top5pct_share_of_total": float(srt[:top5].sum() / tot) if tot != 0 else None,
        "share_of_trades_above_cost": float((p > cost_bp).mean()),
        "mean_bars": float(np.mean([x["bars"] for x in tr])),
        "by_year": {k: {"n": len(v), "mean_bp": float(np.mean(v)),
                        "total_bp": float(np.sum(v))} for k, v in sorted(by_year.items())},
        "by_symbol": {k: {"n": len(v), "mean_bp": float(np.mean(v))}
                      for k, v in sorted(by_sym.items())},
        "by_entry_bucket": {k: {"n": len(v), "mean_bp": float(np.mean(v))}
                            for k, v in sorted(by_bod.items())},
        "cum_pnl_bp": np.cumsum([x["pnl_bp"] for x in
                                 sorted(tr, key=lambda y: y["date"])]).tolist(),
        "cum_dates": [x["date"] for x in sorted(tr, key=lambda y: y["date"])],
        "pnl_bp": p.tolist(),
    }


def main() -> int:
    rp, rc = R.load_full()
    panel_all, cleaned_all = R.subset(rp, rc, R.STRATA["ALL"])
    first, _ = D.session_structure(panel_all.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    T = panel_all.closes.shape[1]
    sess_end, bod = session_maps(first, T)
    vol, px, stamps = V.load_volume(panel_all)
    vol_all = V.build_volume_scores(panel_all, vol, px, V.bar_of_day(stamps),
                                    panel_all.total_log_returns)

    arms = {}
    for st, arm in (("LOW", "S2_short_intra"), ("HIGH", "S1_short_intra")):
        p, cl = R.subset(rp, rc, R.STRATA[st])
        books = R.build_books(p, cl, start, first)
        c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
        arms[f"{st}:{arm}"] = (book_trades(books[arm], p.total_log_returns,
                                           panel_all.dates, p.symbols, start,
                                           sess_end, bod), c2)
    p, _ = R.subset(rp, rc, R.STRATA["LOW"])
    keep = [panel_all.symbols.index(s) for s in p.symbols]
    c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
    arms["LOW:rel_vol Q5"] = (score_trades(vol_all["rel_vol"][keep], p.total_log_returns,
                                           panel_all.dates, p.symbols, start,
                                           sess_end, bod), c2)

    payload = {}
    for k, (tr, c2) in arms.items():
        d = describe(tr, c2)
        payload[k] = d
        print(f"\n{'=' * 78}\n{k}   ({d['n']:,} trades, cost bar {c2:.2f} bp)\n{'=' * 78}")
        print(f"  mean {d['mean_bp']:+.2f} bp ({d['mean_vs_cost']:.2f}x cost)   "
              f"median {d['median_bp']:+.2f}   sd {d['sd_bp']:.1f}")
        print(f"  hit {d['hit_rate']:.1%}   avg win {d['avg_win_bp']:.1f}   "
              f"avg loss {d['avg_loss_bp']:.1f}   payoff {d['payoff']:.2f}")
        print(f"  skew {d['skew']:+.2f}   kurtosis {d['kurtosis']:.1f}   "
              f"mean hold {d['mean_bars']:.1f} bars")
        print(f"  top 5% of trades = {d['top5pct_share_of_total']:.0%} of total P&L")
        print(f"  trades beating the cost bar: {d['share_of_trades_above_cost']:.1%}")
        print("  percentiles: " + "  ".join(
            f"p{q}={d['percentiles'][q]:+.0f}" for q in ("1", "5", "25", "50", "75", "95", "99")))
        print("  by year: " + "  ".join(
            f"{y}:{v['mean_bp']:+.1f}" for y, v in d["by_year"].items()))
        print("  by symbol: " + "  ".join(
            f"{s}:{v['mean_bp']:+.1f}" for s, v in d["by_symbol"].items()))

    OUT.write_text(json.dumps(payload))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
