"""D304 -- the two lenses, and the opportunity cost nothing here has measured.

    uv run python scripts/d304_two_lenses.py

A DIAGNOSTIC, not a study. Every construction is already decided; nothing is
searched and nothing is promoted. See `docs/FINDINGS.md` section 10.

THE TWO LENSES
  path-variant   the slot-limited book we actually run -- what was earned
  path-invariant every candidate name held, no slot cap -- whether the rule is
                 good, free of contention. NOT a tradeable book: unbounded
                 capital and uncontrolled exposure, so it is scored per TRADE and
                 never quoted in bp/bar beside a real book.

Three pools, so contention and bench depth are separated rather than confounded:
  B19   19 slots, pool = the selected top 19          <- the incumbent
  A19   no cap,   pool = the selected top 19          <- B19 minus contention
  A25   no cap,   pool = the whole 25-name gate       <- what a bench would add

THE REPLACEMENT PREMIUM is the sharpest of the three quantities and the one that
prices an exit directly: when a slot turns over, what the arriving name earned
over the next k bars minus what the departing name would have earned had it
stayed. Split by whether the departing name was STILL SELECTED -- if it was, the
slot refills with that same name and the premium is structurally zero.
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


D = _load("d303", "run_d303_reference.py")
N_SLOTS, N_BASE, HOLD = D.N_SLOTS, D.E.N_BASE, D.BASE_HOLD
X_MATCHED = 0.9627                      # D303's adopted rule, flat band
OUT = REPO / "data" / "d304_two_lenses.json"


def run(A, slots, pool, X=X_MATCHED):
    """One book. `slots=None` removes the cap; `pool` is 19 or 25.

    D295's bar order, unchanged: exit on information through t-1, drop delisted,
    refill from what was knowable at t-1, then mark once.
    """
    r1T, mkt, vxT = A["r1T"], A["mkt"], A["vxT"]
    selT, rankT, finT = A["selT"], A["rankT"], A["finT"]
    T, n = r1T.shape
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    cnt = {0: np.zeros(T, np.int32), 1: np.zeros(T, np.int32)}
    exits, entries, trades = [], [], []
    open_ = {0: {}, 1: {}}

    for t in range(1, T):
        r1t, fint, mt, vxt = r1T[t], finT[t], mkt[t], vxT[t]
        for side in (0, 1):
            rankt = rankT[side, t]
            held = open_[side]
            sgn = 1.0 if side == 0 else -1.0
            for row in list(held):
                age, cx, e0 = held[row]
                trig = False
                u = vxt[row]
                if u == u and u > 0.0:
                    trig = cx >= X * u
                if (trig or age >= HOLD) and age > 0:
                    held.pop(row)
                    still = bool(rankt[row] < N_SLOTS)
                    exits.append((row, t, side, still, trig))
                    trades.append((row, e0, age, cx, side))
                elif not fint[row]:
                    st = held.pop(row)
                    if st[0] > 0:
                        trades.append((row, st[2], st[0], st[1], side))
            cand = np.flatnonzero((rankt < pool) & fint)
            if cand.size:
                cand = cand[np.argsort(rankt[cand], kind="stable")]
                free = (len(cand) if slots is None else slots - len(held))
                for row in cand:
                    if free <= 0:
                        break
                    r = int(row)
                    if r in held:
                        continue
                    held[r] = [0, 0.0, t]
                    entries.append((r, t, side))
                    free -= 1
            vals = []
            for row, st in held.items():
                v = r1t[row]
                st[0] += 1
                st[1] += sgn * (v - mt)
                vals.append(v)
            if vals:
                ret[side][t] = float(np.mean(vals))
                cnt[side][t] = len(vals)

    ok = np.isfinite(ret[0]) & np.isfinite(ret[1])
    return dict(book=np.where(ok, ret[0] - ret[1], np.nan), mask=ok,
                exits=exits, entries=entries, trades=trades,
                held_per_bar=float(np.mean(cnt[0][ok] + cnt[1][ok])))


def fwd(r1T, h):
    """Forward sum of the next `h` bars, NaN-safe. fwd[t, i] covers t..t+h-1."""
    v = np.nan_to_num(np.asarray(r1T), nan=0.0)
    c = np.cumsum(np.vstack([np.zeros((1, v.shape[1])), v]), axis=0)
    out = np.full_like(v, np.nan)
    out[:-h] = c[h:-1] - c[:-h - 1] if h < v.shape[0] else np.nan
    return out


def main() -> int:
    t0 = time.time()
    A = D.load_cache(mmap=False)
    r1T = np.asarray(A["r1T"])
    T = r1T.shape[0]
    f5 = fwd(r1T, HOLD)
    res = {}

    print("D304  the two lenses  (adopted rule: excess @ 0.9627, flat band)\n")
    books = {}
    for tag, slots, pool in (("B19 constrained, pool 19", N_SLOTS, N_SLOTS),
                             ("B25 constrained, pool 25", N_SLOTS, N_BASE),
                             ("A19 unconstrained, pool 19", None, N_SLOTS),
                             ("A25 unconstrained, pool 25", None, N_BASE)):
        b = run(A, slots, pool)
        books[tag] = b
        pnl = np.array([x[3] for x in b["trades"]])
        print(f"  {tag:28s} trades {len(b['trades']):>7,}  "
              f"mean trade {pnl.mean() * 1e4:+8.1f} bp  "
              f"median {np.median(pnl) * 1e4:+7.1f}  "
              f"held/bar {b['held_per_bar']:5.1f}  "
              f"({time.time() - t0:.0f}s)")
        res[tag] = dict(trades=len(b["trades"]),
                        mean_trade_bp=float(pnl.mean()) * 1e4,
                        median_trade_bp=float(np.median(pnl)) * 1e4,
                        held_per_bar=b["held_per_bar"])

    B, A19, A25 = (books["B19 constrained, pool 19"],
                   books["A19 unconstrained, pool 19"],
                   books["A25 unconstrained, pool 25"])

    # 1. CONTENTION DRAG -- the same pool, with and without the slot cap
    pb = np.array([x[3] for x in B["trades"]])
    pa = np.array([x[3] for x in A19["trades"]])
    drag = (pa.mean() - pb.mean()) * 1e4
    print(f"\n1. CONTENTION DRAG (A19 minus B19, same pool, cap removed)")
    print(f"   unconstrained mean trade {pa.mean() * 1e4:+.1f} bp on "
          f"{len(pa):,} trades")
    print(f"   constrained   mean trade {pb.mean() * 1e4:+.1f} bp on "
          f"{len(pb):,} trades")
    print(f"   drag {drag:+.2f} bp/trade -- positive means the cap makes the "
          f"book hold the WORSE names")
    res["contention_drag_bp"] = float(drag)

    # 2. THE BENCH. The uncapped comparison only says the 6 extra names are
    #    worse, which the rank profile already implies -- uncapped, a wider pool
    #    just holds MORE names and dilutes. The question a bench actually poses
    #    is whether, AT 19 SLOTS, having somewhere to swap to is worth anything.
    B25 = books["B25 constrained, pool 25"]
    pb25 = np.array([x[3] for x in B25["trades"]])
    p25 = np.array([x[3] for x in A25["trades"]])
    bk = lambda b: float(np.nanmean(b["book"][b["mask"]])) * 1e4
    print(f"\n2. THE BENCH")
    print(f"   uncapped, pool 25 vs 19: {p25.mean() * 1e4:+.1f} vs "
          f"{pa.mean() * 1e4:+.1f} bp/trade -- a wider pool with no cap just "
          f"holds MORE names and dilutes")
    print(f"   AT 19 SLOTS, pool 25 vs 19: {pb25.mean() * 1e4:+.1f} vs "
          f"{pb.mean() * 1e4:+.1f} bp/trade, book "
          f"{bk(B25):+.2f} vs {bk(B):+.2f} bp/bar   <- the real bench test")
    res["bench_uncapped_bp"] = float((p25.mean() - pa.mean()) * 1e4)
    res["bench_capped_bp"] = float((pb25.mean() - pb.mean()) * 1e4)
    res["book_B19_bp"], res["book_B25_bp"] = bk(B), bk(B25)

    # 3. THE REPLACEMENT PREMIUM -- what each slot turnover actually paid
    ent_by = {}
    for r, t, s in B["entries"]:
        ent_by.setdefault((t, s), []).append(r)
    prem = {True: [], False: []}
    for row, t, side, still, trig in B["exits"]:
        arrivals = [r for r in ent_by.get((t, side), []) if r != row]
        if not arrivals:
            continue
        sgn = 1.0 if side == 0 else -1.0
        out_r = f5[t, row]
        in_r = np.nanmean([f5[t, r] for r in arrivals])
        if np.isfinite(out_r) and np.isfinite(in_r):
            prem[still].append(sgn * (in_r - out_r))
    print(f"\n3. THE REPLACEMENT PREMIUM (arriving minus departing, next "
          f"{HOLD} bars)")
    for still, label in ((True, "departing name STILL SELECTED"),
                         (False, "departing name DRIFTED OUT")):
        v = np.array(prem[still])
        if v.size:
            se = v.std(ddof=1) / np.sqrt(v.size)
            print(f"   {label:32s} {v.size:>7,} swaps  "
                  f"premium {v.mean() * 1e4:+8.2f} bp  t {v.mean() / se:+5.2f}")
            res[f"premium_{'still' if still else 'drifted'}"] = dict(
                n=int(v.size), bp=float(v.mean()) * 1e4,
                t=float(v.mean() / se))
        else:
            print(f"   {label:32s}       0 swaps")
            res[f"premium_{'still' if still else 'drifted'}"] = None

    tot = len(B["exits"])
    still_n = sum(1 for e in B["exits"] if e[3])
    # THE DIRECT CHURN MEASURE. "Was the departing name still selected" is a
    # proxy; whether it RE-ENTERED on the same bar is the thing itself, and it
    # is what makes an exit worthless -- the slot turns over, the cost is paid,
    # and the holding does not change.
    ent_set = {(t, s, r) for r, t, s in B["entries"]}
    churn = sum(1 for row, t, side, _st, _tg in B["exits"]
                if (t, side, row) in ent_set)
    print(f"\n   of {tot:,} exits, {still_n:,} ({100 * still_n / tot:.1f}%) were "
          f"on a name still in the top {N_SLOTS}")
    print(f"   and {churn:,} ({100 * churn / tot:.1f}%) re-entered THE SAME NAME "
          f"on the SAME BAR -- pure churn: cost paid, holding unchanged")
    res["exits_total"] = tot
    res["exits_still_selected_share"] = float(still_n / tot)
    res["exits_same_name_reentry_share"] = float(churn / tot)

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
