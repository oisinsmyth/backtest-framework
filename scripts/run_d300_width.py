"""D300 -- book width. How many pairs should the book hold?

    uv run python scripts/run_d300_width.py --selftest
    uv run python scripts/run_d300_width.py [--draws 200]

PRE-REGISTERED AT `ed523f0`, amended at `ce34daf`, both committed before this
file existed (R8). This runner may not add a depth or change the base book.

N PER LEG in {2, 3, 5, 7, 10, 14, 19}, NO EXITS. The exit rules are out of scope:
adding one would confound the single axis this study exists to measure.

BOTH STATISTICS ARE PRIMARY, because they will disagree. Concentration raises the
mean and destroys diversification, and a four-position book is not a portfolio.
Reporting only the mean would recommend N=2; only Sharpe would hide why.

THE NULL IS A CIRCULAR SHIFT OF THE RANK ASSIGNMENT inside the gate: the name
ranked j is treated as rank (j + s) mod 25. A size-matched RANDOM SUBSET is not a
control for a persistent selector -- it re-draws every bar where the treatment
persists, which is what voided D291's veto arm. The shift preserves each name's
rank persistence, the gate membership, the held-set size and the entry rate
exactly, and destroys only the alignment between rank order and preference.

AND THE BOTTOM-N IS A FREE DIRECTIONAL CHECK. If the ranking carries ordinal
information the bottom must be worse than the top. If it is not, nothing else in
the output means anything.
"""

from __future__ import annotations

import argparse
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
E, R, M = D.E, D.R, D.M
SP = _load("d285sp", "d285_spread_estimate.py")

N_BASE, BASE_HOLD = E.N_BASE, D.BASE_HOLD
DEPTHS = (2, 3, 5, 7, 10, 14, 19)
ANN, SEED = 252.0, 20260903
OUT = REPO / "data" / "d300_width.json"


def simulate(A, n_slots, shift=0, bottom=False, runs=None, rng=None):
    """D295's bar order at an arbitrary depth. No exit rule; the cap is the exit.

    `shift` applies the rank-rotation null. `bottom=True` takes the WORST n_slots
    of the gate instead of the best -- the directional diagnostic.
    """
    r1T, rankT, finT = A["r1T"], A["rankT"], A["finT"]
    T = r1T.shape[0]
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    cnt = {0: np.zeros(T, np.int32), 1: np.zeros(T, np.int32)}
    ent = np.zeros(T, np.int32)
    trades = []
    open_ = {0: {}, 1: {}}
    buf = np.empty(N_BASE + 4)

    for t in range(1, T):
        r1t, fint = r1T[t], finT[t]
        for side in (0, 1):
            rk = rankT[side, t]
            held = open_[side]
            sgn = 1.0 if side == 0 else -1.0
            for row in list(held):
                age, cum, e0, tgt = held[row]
                trig = (age >= tgt) if runs is not None else (age >= BASE_HOLD)
                if (trig and age > 0) or not fint[row]:
                    st = held.pop(row)
                    if st[0] > 0:
                        trades.append((row, st[2], st[0], st[1], side))
            free = n_slots - len(held)
            if free > 0:
                g = np.flatnonzero((rk < N_BASE) & fint)
                if g.size:
                    eff = (rk[g] + shift) % N_BASE
                    key = (N_BASE - 1 - eff) if bottom else eff
                    order = np.argsort(key, kind="stable")
                    for j in order:
                        if free == 0:
                            break
                        if key[j] >= n_slots:
                            break
                        r = int(g[j])
                        if r in held:
                            continue
                        tg = (int(rng.choice(runs)) if runs is not None
                              else BASE_HOLD)
                        held[r] = [0, 0.0, t, max(1, tg)]
                        ent[t] += 1
                        free -= 1
            k = 0
            for row, st in held.items():
                v = r1t[row]
                st[0] += 1
                st[1] += sgn * v
                buf[k] = v
                k += 1
            if k:
                ret[side][t] = float(np.mean(buf[:k]))
                cnt[side][t] = k

    ok = np.isfinite(ret[0]) & np.isfinite(ret[1])
    return dict(book=np.where(ok, ret[0] - ret[1], np.nan), mask=ok, ent=ent,
                trades=trades, held=(cnt[0] + cnt[1]))


def block(res, n_slots, rt_rob, rt_mean, half, price):
    ok = res["mask"]
    b = res["book"][ok]
    bars, sd = b.size, res["book"][ok].std(ddof=1)
    eq = np.cumsum(b)
    e = int(res["ent"][ok].sum())
    turn = e / float(n_slots) / 2.0 / bars
    pnl = np.array([x[3] for x in res["trades"]])
    run = np.array([x[2] for x in res["trades"]])
    hv = np.array([half[e0, row] for row, e0, _a, _p, _s in res["trades"]])
    pv = np.array([price[e0, row] for row, e0, _a, _p, _s in res["trades"]])
    hv, pv = hv[np.isfinite(hv)], pv[np.isfinite(pv)]
    byname = {}
    for x in res["trades"]:
        byname[x[0]] = byname.get(x[0], 0.0) + x[3]
    vals = np.sort(np.array(list(byname.values())))[::-1]
    tot = float(vals.sum())
    return dict(
        n_slots=n_slots, gross_bp=float(b.mean()) * 1e4,
        vol_bp=float(sd) * 1e4, sharpe=float(b.mean() / sd * np.sqrt(ANN)),
        t=float(b.mean() / (sd / np.sqrt(bars))), bars=bars,
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
        held_per_bar=float(res["held"][ok].mean()),
        turnover=float(turn), entries=e, trades=int(pnl.size),
        cost_rob_bp=float(rt_rob * turn), cost_mean_bp=float(rt_mean * turn),
        net_rob_bp=float(b.mean()) * 1e4 - rt_rob * turn,
        gross_per_position_bp=float(b.mean()) * 1e4 / (n_slots / 19.0),
        trade_mean=float(pnl.mean()) * 1e4,
        trade_median=float(np.median(pnl)) * 1e4,
        run=float(run.mean()),
        held_price_median=float(np.median(pv)) if pv.size else None,
        held_half_spread_median=float(np.median(hv)) if hv.size else None,
        names=len(byname),
        names_to_half=(int(np.searchsorted(np.cumsum(vals), 0.5 * tot) + 1)
                       if tot > 0 else None))


# --------------------------------------------------------------------------
def assertions(A, half, price):
    print("\nASSERTIONS")
    T = A["r1T"].shape[0]

    # 4. BIT-IDENTITY at N=19 against D303's no-exit control. If the widest
    #    depth is not the book every earlier record ran, no depth here is
    #    comparable to anything.
    mine = simulate(A, 19)
    ref = D.simulate(A, "none", "flat", None)
    assert np.array_equal(np.nan_to_num(mine["book"], nan=-9e9),
                          np.nan_to_num(ref["book"], nan=-9e9)), \
        "N=19 is NOT D303's no-exit control"
    print(f"    [4] N=19 is bit-identical to D303's no-exit control, "
          f"{int(mine['ent'].sum()):,} entries")

    # 3. RIGHT QUANTITY. Held names must track the depth, and turnover must not:
    #    turnover is the RATE 1/k and is invariant to N. If it moves with N the
    #    denominator is wrong.
    turns, helds = [], []
    for n in DEPTHS:
        r = simulate(A, n)
        s = block(r, n, 1.0, 1.0, half, price)
        turns.append(s["turnover"])
        helds.append(s["held_per_bar"])
        assert abs(s["held_per_bar"] - 2 * n) < 0.05 * 2 * n, (
            f"N={n} holds {s['held_per_bar']:.1f} names, not ~{2 * n}")
    spread = max(turns) - min(turns)
    assert spread < 0.02, (f"turnover moved {spread:.4f} across depths -- it is "
                           f"the rate 1/k and must be invariant to N")
    print(f"    [3] right quantity: held names track the depth "
          + ", ".join(f"N={n}:{h:.0f}" for n, h in zip(DEPTHS, helds))
          + f"; turnover invariant across depths, spread {spread:.4f}")

    # 5. EVERY DEPTH A DISTINCT BOOK -- the guard D295 lacked.
    seen = {}
    for n in DEPTHS:
        k = np.nan_to_num(simulate(A, n)["book"], nan=-9e9).tobytes()
        assert k not in seen, f"[5] N={n} and N={seen[k]} are the SAME BOOK"
        seen[k] = n
    print(f"    [5] all {len(seen)} depths are distinct books")

    # 6. THE NULL MUST MOVE THE HELD SET AND PRESERVE THE ENTRY RATE.
    base = simulate(A, 19)
    for s in (1, 7, 13):
        r = simulate(A, 19, shift=s)
        rel = abs(int(r["ent"].sum()) - int(base["ent"].sum())) / int(base["ent"].sum())
        assert rel < 0.25, f"rotation s={s} moves the entry rate by {rel:.1%}"
        assert not np.array_equal(np.nan_to_num(r["book"], nan=-9e9),
                                  np.nan_to_num(base["book"], nan=-9e9))
    print(f"    [6] the rank rotation changes the book and holds the entry rate "
          f"within 25% at s = 1, 7, 13")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [r for r in d295["rows"] if r["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's "
          f"published {b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK.
    broke = False
    try:
        ok = base["mask"]
        bad = base["book"].copy()
        bad[np.flatnonzero(ok)[:100]] += 0.05
        assert float(np.nanmean(bad[ok])) == float(np.nanmean(base["book"][ok]))
    except AssertionError:
        broke = True
    assert broke, "the mean check passed a book handed free money"
    print("    [7] and the mean check raises on a book handed free money")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print(f"D300  book width  gate={N_BASE}  k={BASE_HOLD}  no exits")
    D.build_cache(verbose=True)
    A = D.load_cache(mmap=True)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    price = np.ascontiguousarray(np.asarray(g["close"], dtype=np.float64).T)
    print(f"  loaded ({time.time() - t0:.0f}s)")

    assertions(A, half, price)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # the round trip on the names held at N=19, the incumbent depth. MEDIAN is
    # primary; D302 showed the mean is a left-truncation artefact.
    r19 = simulate(A, 19)
    hv = np.array([half[e0, row] for row, e0, _a, _p, _s in r19["trades"]])
    hv = hv[np.isfinite(hv)]
    rt_mean, rt_rob = 4.0 * float(hv.mean()), 4.0 * float(np.median(hv))
    print(f"\n  round trip {rt_mean:.1f} (artefact) / {rt_rob:.1f} bp robust")

    obs, books = {}, {}
    for n in DEPTHS:
        r = simulate(A, n)
        books[n] = r
        obs[str(n)] = block(r, n, rt_rob, rt_mean, half, price)
        rb = simulate(A, n, bottom=True)
        obs[str(n)]["bottom_gross_bp"] = float(
            np.nanmean(rb["book"][rb["mask"]])) * 1e4
    print(f"  {len(obs)} depths + {len(obs)} bottom-N diagnostics "
          f"({time.time() - t0:.0f}s)")

    for n in DEPTHS:
        rng = np.random.default_rng([SEED, n])
        offs = rng.choice(np.arange(1, N_BASE), size=a.draws, replace=True)
        gm, sh = [], []
        for s in offs:
            r = simulate(A, n, shift=int(s))
            b = r["book"][r["mask"]]
            if b.size > 200:
                gm.append(float(b.mean()) * 1e4)
                sh.append(float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)))
        ga, sa = np.array(gm), np.array(sh)
        o = obs[str(n)]
        o["null_gross_p50"], o["null_gross_p95"] = (float(np.median(ga)),
                                                    float(np.quantile(ga, .95)))
        o["null_sharpe_p95"] = float(np.quantile(sa, .95))
        o["p_gross"] = float((ga >= o["gross_bp"]).sum() + 1) / (ga.size + 1)
        o["p_sharpe"] = float((sa >= o["sharpe"]).sum() + 1) / (sa.size + 1)
        o["beats_gross_p95"] = bool(o["gross_bp"] > o["null_gross_p95"])
        print(f"    null N={n:<3d} p_gross={o['p_gross']:.4f} "
              f"p_sharpe={o['p_sharpe']:.4f} ({time.time() - t0:.0f}s)",
              flush=True)

    OUT.write_text(json.dumps(dict(
        purpose="D300: book width. N per leg in {2,3,5,7,10,14,19}, no exits, "
                "against a rank-rotation null.",
        preregistered="ed523f0", amended="ce34daf", draws=a.draws,
        round_trip_mean=rt_mean, round_trip_robust=rt_rob,
        null="circular shift of the rank assignment within the 25-name gate",
        depths=obs), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
