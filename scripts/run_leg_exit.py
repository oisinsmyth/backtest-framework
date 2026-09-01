"""D276 -- the leg-relative exit. Pre-registered in
`docs/decisions/D276-the-leg-relative-exit.md`, commit 07bf541, BEFORE this file
was written.

    uv run python scripts/run_leg_exit.py

Entry is D275's CHOCH_DOWN at k=2, unchanged. Only the EXIT differs: hold until
the state machine emits a NEW Leg -- the bar the leg's end pivot confirms -- or
the session close, whichever is first. Causal and parameter-free.

L2 IS THE HURDLE THAT DECIDES ANYTHING. D274 found a RANDOM exit bar beats a
fixed one on S1 and S2, which is R7's finding reproduced. So the leg exit must
beat a matched random exit drawn from the SAME hold-length distribution -- beating
D275's state rule only shows that less churn costs less, which is arithmetic.
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

from backtest_framework.research.structure import Event, market_structure  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


S = _load("d275", "run_choch_short.py")
A, R, M, D, X, J = S.A, S.R, S.M, S.D, S.X, S.J

OUT = REPO / "data" / "d276_leg_exit_summary.json"
K = S.K
N_SIMS, N_BOOT, SEED = 1000, 1000, 0


def leg_books(panel, cleaned, first, start, sess_end):
    """Enter on CHoCH, exit when a NEW leg confirms or at the session close."""
    n, T = panel.closes.shape
    books = {"leg_short": np.zeros((n, T)), "leg_long": np.zeros((n, T))}
    holds = {"leg_short": [], "leg_long": []}
    for i, sym in enumerate(panel.symbols):
        states = market_structure(cleaned[sym], K)
        for ev, key, sign in ((Event.CHOCH_DOWN, "leg_short", -1.0),
                              (Event.CHOCH_UP, "leg_long", 1.0)):
            for t in range(start, T - 1):
                if states[t].event is not ev:
                    continue
                leg0 = states[t].leg
                close = int(sess_end[t])
                ex = close
                for u in range(t + 1, close):
                    if states[u].leg is not None and states[u].leg != leg0:
                        ex = u + 1          # act on the bar AFTER it becomes knowable
                        break
                ex = min(ex, close)
                if ex > t + 1:
                    books[key][i, t + 1:ex] = sign      # lag 1
                    holds[key].append(ex - (t + 1))
    for b in books.values():
        b[:, :start] = 0.0
        b[:, first] = 0.0
    return books, {k: np.array(v) for k, v in holds.items()}


def per_trade(pos, rets, start, sess_end):
    out, lens = [], []
    for i in range(pos.shape[0]):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        for t in ent:
            close = int(sess_end[t])
            z = np.flatnonzero(s[t:close] == 0.0)
            ex = t + int(z[0]) if z.size else close
            if ex > t:
                out.append(float(np.sign(s[t]) * rets[i, t:ex].sum()) * 1e4)
                lens.append(ex - t)
    return np.array(out), np.array(lens)


def random_exit_null(pos, rets, start, sess_end, rng, n_draws=300):
    """R7's control: the SAME entries, exits at a random bar drawn from the same
    hold-length distribution. Not a rotation -- rotation tests the entry."""
    trades = []
    for i in range(pos.shape[0]):
        s = pos[i]
        ent = np.flatnonzero((s[start:] != 0.0) & (s[start - 1:-1] == 0.0)) + start
        for t in ent:
            close = int(sess_end[t])
            z = np.flatnonzero(s[t:close] == 0.0)
            ex = t + int(z[0]) if z.size else close
            if ex > t:
                trades.append((i, t, close, np.sign(s[t])))
    lens = np.array([min(c, t + 40) - t for _, t, c, _ in trades])
    out = np.empty(n_draws)
    for d in range(n_draws):
        tot = 0.0
        for (i, t, close, sg), L in zip(trades, rng.permutation(lens)):
            e = min(t + max(1, int(L)), close)
            tot += float(sg * rets[i, t:e].sum())
        out[d] = tot / len(trades) * 1e4
    return out


def main() -> int:
    rp, rc = R.load_full()
    panel, cleaned = R.subset(rp, rc, R.STRATA["ALL"])
    first, gap = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    T = panel.closes.shape[1]
    ppy = (T / int(first.sum())) * 252.0
    sess_end, _ = A.session_maps(first, T)
    rng = np.random.default_rng(SEED)

    payload, per_cell = {}, {}
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel, cleaned) if st == "ALL" else R.subset(rp, rc, R.STRATA[st]))
        books, holds = leg_books(p, cl, first, start, sess_end)
        borrow = R.borrow_vector(p.symbols)
        c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
        print("=" * 96)
        print(f"{st}   cost bar 2c = {c2:.2f} bp")
        print("=" * 96)
        for k in ("leg_short", "leg_long"):
            sc = R.score(p, books[k], start, first, gap, ppy, borrow)
            tr, lens = per_trade(books[k], p.total_log_returns, start, sess_end)
            if tr.size < 200:
                print(f"  {k:11s} only {tr.size} trades, skipped")
                continue
            mv = float(tr.mean())
            null = random_exit_null(books[k], p.total_log_returns, start, sess_end, rng)
            nmed, n95 = float(np.median(null)), float(np.percentile(null, 95))
            key = f"{st}:{k}"
            per_cell[key] = (p, books[k], borrow)
            payload[key] = {**sc, "cost_bar_bp": c2, "n_trades": int(tr.size),
                            "mean_move_bp": mv, "mean_hold_bars": float(lens.mean()),
                            "r7_null_median_bp": nmed, "r7_null_p95_bp": n95,
                            "L1": bool(mv >= c2), "L2": bool(mv > n95),
                            "L4": bool(sc["cagr"] > 0)}
            print(f"  {k:11s} exposure {sc['exposure']:5.1%}  CAGR {sc['cagr']:+7.2%}  "
                  f"turn {sc['turnover_per_year']:4.0f}  {tr.size:6,d} trades  "
                  f"hold {lens.mean():4.1f}b")
            print(f"              move {mv:+6.2f}b vs bar {c2:5.2f}b  L1 "
                  f"{'YES' if mv >= c2 else 'no':>3s}   |   R7 null median {nmed:+6.2f}b "
                  f"p95 {n95:+6.2f}b  L2 {'YES' if mv > n95 else 'no':>3s}")
        print()

    print("rotation nulls (both legs, shared offsets) ...", flush=True)
    keys = list(per_cell)
    rg = np.random.default_rng(SEED)
    ps = {k: np.empty(N_SIMS) for k in keys}
    pm = {k: np.empty(N_SIMS) for k in keys}
    for s in range(N_SIMS):
        off = rg.integers(1, T - start, size=len(panel.symbols))
        for k in keys:
            p, book, borrow = per_cell[k]
            idx = [panel.symbols.index(x) for x in p.symbols]
            rot = np.zeros_like(book)
            for i, j in enumerate(idx):
                rot[i, start:] = np.roll(book[i, start:], int(off[j]))
            tot = X.signed_log_returns(p, rot, total_return=True)[start:]
            ex, _ = R.excess_vec(tot, rot, start, first, gap, ppy, borrow)
            ps[k][s] = R._sharpe(ex, ppy)
            pm[k][s] = float(np.sum(tot))
        if (s + 1) % 250 == 0:
            print(f"  {s + 1}/{N_SIMS}", flush=True)

    rb = np.random.default_rng(SEED)
    nlen, blk = T - start, J.BLOCK
    idxs = [(rb.integers(0, nlen - blk + 1, size=math.ceil(nlen / blk))[:, None]
             + np.arange(blk)[None, :]).ravel()[:nlen] for _ in range(N_BOOT)]

    print(f"\n  {'cell':20s} {'move':>8s} {'L1':>4s} {'L2':>4s} {'SR pct':>7s} {'$ pct':>7s} "
          f"{'L3':>4s} {'L4':>4s} {'L5':>4s}  ALL FIVE")
    surv = []
    for k in keys:
        p, book, borrow = per_cell[k]
        a_s = payload[k]["excess_sharpe"]
        tot = X.signed_log_returns(p, book, total_return=True)[start:]
        a_m = float(np.sum(tot))
        ex, _ = R.excess_vec(tot, book, start, first, gap, ppy, borrow)
        boot = np.array([R._sharpe(ex[i], ppy) for i in idxs])
        l3 = bool(a_s > np.percentile(ps[k], 95) and a_m > np.percentile(pm[k], 95))
        l5 = bool(np.percentile(boot, 5) > 0.0)
        payload[k].update(sharpe_pct=float((ps[k] < a_s).mean() * 100),
                          money_pct=float((pm[k] < a_m).mean() * 100),
                          L3=l3, L5=l5, boot_p05=float(np.percentile(boot, 5)))
        allz = all(payload[k][x] for x in ("L1", "L2", "L3", "L4", "L5"))
        payload[k]["clears_all"] = allz
        if allz and "short" in k:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:20s} {payload[k]['mean_move_bp']:+7.2f}b {y(payload[k]['L1']):>4s} "
              f"{y(payload[k]['L2']):>4s} {payload[k]['sharpe_pct']:6.1f}th "
              f"{payload[k]['money_pct']:6.1f}th {y(l3):>4s} {y(payload[k]['L4']):>4s} "
              f"{y(l5):>4s}  {'** YES **' if allz else 'no'}")

    payload["survivors"] = surv
    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
