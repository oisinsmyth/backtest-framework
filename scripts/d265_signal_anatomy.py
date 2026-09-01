"""D265 ANATOMY -- is the short signal EARLY, or does it carry no timing at all?

    uv run python scripts/d265_signal_anatomy.py

POST-HOC. This is a search on data D264 already scored, run at the principal's
request. It is labelled as such, it scores no book, and anything built on it
needs its own pre-registration carrying these looks in its ledger.

THE QUESTION, AND WHY HIT RATE ALONE CANNOT ANSWER IT
------------------------------------------------------
The decay profile showed CUMULATIVE short P&L rising with bars held. Two very
different things produce that shape:

  EARLY SIGNAL     the move has not started yet at entry, so the MARGINAL return
                   per bar RISES with time since entry. Fixable -- delay entry.
  NO TIMING        the signal selects names that drift down at a constant rate,
                   so the MARGINAL return is FLAT. Nothing to fix; you are being
                   paid for exposure, not for timing, and the entry instant is
                   irrelevant.

**Cumulative rising is consistent with both.** The marginal profile separates
them, and a hit rate separates neither -- a coin flip with a fat left tail and a
70% win rate with a fatter right tail can produce identical means.

SO THREE THINGS ARE MEASURED, NOT ONE
--------------------------------------
  1. MARGINAL mean return per bar since entry -- the shape that answers the
     actual question.
  2. HIT RATE, AVERAGE WIN, AVERAGE LOSS, PAYOFF RATIO. The mean is
     `p*W - (1-p)*L`; reporting `p` without `W/L` is how a 48% hit rate gets
     mistaken for a broken signal when it is merely a skewed one.
  3. A MATCHED RANDOM-ENTRY CONTROL AT THE SAME BAR-OF-DAY.

THE CONTROL IS THE LOAD-BEARING PART, for two separate reasons
---------------------------------------------------------------
D244's lesson is that a null can be beaten or lost by DRIFT STRUCTURE ALONE, and
D264 measured intraday drift at -8.97%/yr on the high-vol stratum. A short held
25 bars collects roughly 3.4 bp of that for free, with no signal in it at all.

And it settles the confound flagged when the decay profile was read: the later
columns only contain trades that HAD that many bars left before the close, which
selects early-session entries. **Drawing the control at the SAME BAR-OF-DAY makes
that selection identical in both arms**, so it cancels in the difference instead
of contaminating it.

The null draws, per actual entry: the same symbol, the same bar-of-day, a
different session chosen at random. Same clock, same instrument, wrong day.
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


R = _load("d264", "run_single_name_intraday.py")
D, M = R.D, R.M

OUT = REPO / "data" / "d265_signal_anatomy.json"
MAX_H = 26
SEED = 0
N_DRAWS = 20          # null entries drawn per real entry, to steady the control
CHECKPOINTS = (1, 2, 4, 8, 12, 16, 20, 24)


def session_index(first, T):
    """(session id, bar-of-day) for every bar."""
    sid = np.cumsum(first) - 1
    bod = np.empty(T, dtype=int)
    k = 0
    for t in range(T):
        k = 0 if first[t] else k + 1
        bod[t] = k
    return sid, bod


def paths(pos, rets, first, start, rng):
    """Forward SHORT P&L after each entry, and a bar-of-day-matched control."""
    n_sym, T = pos.shape
    sid, bod = session_index(first, T)
    starts = list(np.flatnonzero(first)) + [T]
    sess_end = np.empty(T, dtype=int)
    for a, b in zip(starts[:-1], starts[1:]):
        sess_end[a:b] = b
    # every bar index that opens each bar-of-day, so the control can be matched
    by_bod: dict[int, np.ndarray] = {}
    for d in range(MAX_H):
        by_bod[d] = np.flatnonzero((bod == d) & (np.arange(T) >= start))

    real = [[] for _ in range(MAX_H)]
    null = [[] for _ in range(MAX_H)]
    for i in range(n_sym):
        p = pos[i]
        entries = np.flatnonzero((p[start:] != 0.0) & (p[start - 1:-1] == 0.0)) + start
        for t in entries:
            end = min(sess_end[t], t + MAX_H)
            run = np.cumsum(rets[i, t:end])
            for h in range(len(run)):
                real[h].append(-run[h])
            pool = by_bod[bod[t]]
            if pool.size < 2:
                continue
            for u in rng.choice(pool, size=min(N_DRAWS, pool.size), replace=False):
                if sid[u] == sid[t]:
                    continue
                e2 = min(sess_end[u], u + MAX_H)
                r2 = np.cumsum(rets[i, u:e2])
                # match the horizon too: the control cannot use bars the real
                # trade did not have available
                for h in range(min(len(r2), len(run))):
                    null[h].append(-r2[h])
    return real, null


def main() -> int:
    rng = np.random.default_rng(SEED)
    raw_panel, raw_cleaned = R.load_full()
    panel_all, cleaned_all = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    first, _ = D.session_structure(panel_all.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    out = {}
    for st, arm in (("HIGH", "S1_short_intra"), ("LOW", "S2_short_intra"),
                    ("ALL", "S1_short_intra")):
        p, cl = ((panel_all, cleaned_all) if st == "ALL"
                 else R.subset(raw_panel, raw_cleaned, R.STRATA[st]))
        books = R.build_books(p, cl, start, first)
        c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
        real, null = paths(books[arm], p.total_log_returns, first, start, rng)

        print("=" * 96)
        print(f"{st}:{arm}   round-trip cost 2c = {c2:.2f} bp")
        print("=" * 96)
        print(f"  {'bars':>4s} {'n':>6s} | {'cum bp':>8s} {'MARGINAL':>9s} | "
              f"{'hit%':>6s} {'avg win':>8s} {'avg loss':>9s} {'payoff':>7s} | "
              f"{'null cum':>9s} {'SIGNAL':>8s}")
        rows = []
        prev = 0.0
        for h in range(MAX_H):
            v = np.array(real[h])
            if v.size == 0:
                continue
            nv = np.array(null[h])
            cum = float(v.mean()) * 1e4
            marg = cum - prev
            prev = cum
            wins, losses = v[v > 0], v[v < 0]
            aw = float(wins.mean()) * 1e4 if wins.size else 0.0
            al = float(-losses.mean()) * 1e4 if losses.size else 0.0
            ncum = float(nv.mean()) * 1e4 if nv.size else float("nan")
            row = {"bars": h + 1, "n": int(v.size), "cum_bp": cum, "marginal_bp": marg,
                   "hit_rate": float((v > 0).mean()), "avg_win_bp": aw,
                   "avg_loss_bp": al, "payoff": (aw / al) if al else None,
                   "null_cum_bp": ncum, "signal_bp": cum - ncum, "n_null": int(nv.size)}
            rows.append(row)
            if row["bars"] in CHECKPOINTS:
                print(f"  {row['bars']:4d} {v.size:6,d} | {cum:7.2f}b {marg:8.2f}b | "
                      f"{row['hit_rate'] * 100:5.1f}% {aw:7.2f}b {al:8.2f}b "
                      f"{(row['payoff'] or 0):6.2f} | {ncum:8.2f}b {cum - ncum:7.2f}b")

        early = [r["marginal_bp"] for r in rows[:8]]
        late = [r["marginal_bp"] for r in rows[8:20]]
        print(f"\n  mean MARGINAL bp/bar   bars 1-8: {np.mean(early):+.3f}   "
              f"bars 9-20: {np.mean(late):+.3f}")
        print("  -> " + ("SIGNAL IS EARLY: the move accelerates after entry"
                         if np.mean(late) > np.mean(early) * 1.25 else
                         "NOT an early signal: marginal return is flat or decaying, "
                         "so entry timing is not the lever"))
        pk = max(rows, key=lambda r: r["cum_bp"])
        pks = max(rows, key=lambda r: r["signal_bp"])
        print(f"  peak cumulative {pk['cum_bp']:.2f} bp @ bar {pk['bars']} "
              f"({pk['cum_bp'] / c2:.2f}x the bar)")
        print(f"  peak SIGNAL (over the bar-of-day control) {pks['signal_bp']:.2f} bp "
              f"@ bar {pks['bars']} ({pks['signal_bp'] / c2:.2f}x the bar)")
        out[f"{st}:{arm}"] = {"round_trip_cost_bp": c2, "rows": rows,
                              "marginal_early": float(np.mean(early)),
                              "marginal_late": float(np.mean(late))}
        print()

    OUT.write_text(json.dumps(out, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
