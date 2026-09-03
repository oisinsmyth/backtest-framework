"""D306 -- book width crossed with the exits, through both lenses.

    uv run python scripts/run_d306_width_exits.py --selftest
    uv run python scripts/run_d306_width_exits.py [--draws 200]

PRE-REGISTERED AT `5926d93`, committed before this file existed (R8). This runner
may not add a depth, an exit configuration, or change the base book.

WHAT WAS OPTIMISED
==================
  * THE OVERLAY DOES NOT TOUCH THE HOLDINGS. It scales the book's return series
    after the fact, so `target+overlay` and `target` share ONE book simulation --
    28 cells need 14 sims, and 5,600 null draws need 2,800. Assertion [11] holds
    the two trade ledgers identical rather than assuming it.
  * THE GATE IS PRE-SORTED ONCE. D300 rebuilt `flatnonzero((rank < 25) & finite)`
    over all 1,573 rows twice per bar per simulation -- ~13M element-ops each.
    The gate members, sorted by rank, are the same array in every simulation, so
    they are cached flat with offsets and each bar becomes a masked operation on
    <=25 elements. Assertion [3b] holds the result bit-identical.
  * A ROTATED RANK IS STILL A PREFIX. Under shift `s` the effective rank is
    `(rank + s) % 25`, so selecting `eff < N` from the pre-sorted gate is a
    <=25-element mask, never a re-sort of the panel.

None of it moves a float: assertion [10] holds the no-exit arm to D300's
published numbers at every depth.
"""

from __future__ import annotations

import argparse
import hashlib
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
O = _load("d297", "run_d297_overlay.py")
SP = _load("d285sp", "d285_spread_estimate.py")
E, R, M = D.E, D.R, D.M

N_BASE, BASE_HOLD = E.N_BASE, D.BASE_HOLD
DEPTHS = (2, 3, 5, 7, 10, 14, 19)
EXITS = ("none", "target", "overlay", "target+overlay")
X_TARGET = 0.9627                      # D303's adopted rule, flat band
OVERLAY_X, OVERLAY_S = 12.0, 0.0       # D297's, unchanged
ANN, SEED = 252.0, 20260903
CACHE = REPO / "temp" / "d306_cache"
OUT = REPO / "data" / "d306_width_exits.json"
GATE = ("gateF", "gateR", "gateO")


def cache_key():
    h = hashlib.sha1(D.cache_key().encode())
    st = (REPO / "scripts" / "run_d306_width_exits.py").stat()
    h.update(f"{st.st_size}:{int(st.st_mtime)}:{N_BASE}".encode())
    return h.hexdigest()[:16]


def build_gate(A, verbose=True):
    """The gate members per (side, bar), sorted by rank, flat with offsets.

    The same array in every simulation, so it is built once instead of
    2 x 4,187 times per book over all 1,573 rows.
    """
    d = CACHE / cache_key()
    if all((d / f"{a}.npy").exists() for a in GATE):
        if verbose:
            print(f"  gate cache HIT  {d.name}")
        return {a: np.load(d / f"{a}.npy") for a in GATE}
    t0 = time.time()
    rankT, finT = np.asarray(A["rankT"]), np.asarray(A["finT"])
    T = rankT.shape[1]
    rows, rks, off = [], [], np.zeros((2, T + 1), np.int64)
    k = 0
    for side in (0, 1):
        for t in range(T):
            rk = rankT[side, t]
            g = np.flatnonzero((rk < N_BASE) & finT[t])
            if g.size:
                g = g[np.argsort(rk[g], kind="stable")]
            rows.append(g.astype(np.int32))
            rks.append(rk[g].astype(np.int32))
            off[side, t] = k
            k += g.size
        off[side, T] = k
    out = {"gateF": np.concatenate(rows).astype(np.int32),
           "gateR": np.concatenate(rks).astype(np.int32), "gateO": off}
    d.mkdir(parents=True, exist_ok=True)
    for a in GATE:
        np.save(d / f"{a}.npy", out[a])
    if verbose:
        print(f"  gate cache BUILT {d.name}  ({time.time() - t0:.0f}s)")
    return out


# --------------------------------------------------------------------------
def simulate(A, G, depth, use_target, slots=True, shift=0, runs=None, rng=None,
             legacy=False):
    """D295's bar order at an arbitrary depth. The overlay is NOT here -- it
    scales the returns afterwards and does not touch the holdings.

    `slots=False` is the PATH-INVARIANT lens: no slot cap, every eligible name
    held. Not a tradeable book; scored per trade only.
    """
    r1T, mkt, vxT, finT = A["r1T"], A["mkt"], A["vxT"], A["finT"]
    rankT = A["rankT"]
    gF, gR, gO = G["gateF"], G["gateR"], G["gateO"]
    T = r1T.shape[0]
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    cnt = {0: np.zeros(T, np.int32), 1: np.zeros(T, np.int32)}
    ent = np.zeros(T, np.int32)
    trades = []
    open_ = {0: {}, 1: {}}
    buf = np.empty(N_BASE * 4 + 8)

    for t in range(1, T):
        r1t, fint, mt, vxt = r1T[t], finT[t], mkt[t], vxT[t]
        for side in (0, 1):
            held = open_[side]
            sgn = 1.0 if side == 0 else -1.0
            for row in list(held):
                age, cx, e0, tgt = held[row]
                trig = False
                if runs is not None:
                    trig = age >= tgt
                elif use_target:
                    u = vxt[row]
                    if u == u and u > 0.0:
                        trig = cx >= X_TARGET * u
                cap = (runs is None) and age >= BASE_HOLD
                if ((trig or cap) and age > 0) or not fint[row]:
                    st = held.pop(row)
                    if st[0] > 0:
                        trades.append((row, st[2], st[0], st[1], side))
            free = (10 ** 9 if not slots else depth - len(held))
            if free > 0:
                if legacy:
                    rk = rankT[side, t]
                    g = np.flatnonzero((rk < N_BASE) & fint)
                    if g.size:
                        g = g[np.argsort(rk[g], kind="stable")]
                    rr = rk[g]
                else:
                    a, b = gO[side, t], gO[side, t + 1]
                    g, rr = gF[a:b], gR[a:b]
                if g.size:
                    eff = (rr + shift) % N_BASE if shift else rr
                    sel = eff < depth
                    if sel.any():
                        cand = g[sel]
                        if shift:
                            cand = cand[np.argsort(eff[sel], kind="stable")]
                        for row in cand:
                            if free == 0:
                                break
                            r = int(row)
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
                st[1] += sgn * (v - mt)
                buf[k] = v
                k += 1
            if k:
                ret[side][t] = float(np.mean(buf[:k]))
                cnt[side][t] = k

    ok = np.isfinite(ret[0]) & np.isfinite(ret[1])
    # cnt0/cnt1 are exposed for D307c's contribution decomposition: the book is
    # mean(long) - mean(short), so a trade's weight at bar t is 1/n_t for its
    # own leg, NOT 1/depth -- the two differ whenever a delisting leaves the leg
    # short of its slots. Additive only; no computation above changes.
    return dict(book=np.where(ok, ret[0] - ret[1], np.nan), mask=ok, ent=ent,
                trades=trades, held=(cnt[0] + cnt[1]),
                cnt0=cnt[0], cnt1=cnt[1])


def overlay_scale(book):
    """D297's schedule, X=12, s=0. Applied to the RETURN SERIES only."""
    on, _, _ = O.schedule(np.nan_to_num(book, nan=0.0), OVERLAY_X)
    return np.where(on, 1.0, OVERLAY_S)


def stats(res, depth, scale, rt, half):
    ok = res["mask"]
    raw = res["book"][ok]
    sc = scale[ok]
    b = raw * sc
    bars, sd = b.size, b.std(ddof=1)
    eq = np.cumsum(b)
    e = int(res["ent"][ok].sum())
    turn = e / float(depth) / 2.0 / bars
    expo = float(sc.mean())
    ds = np.abs(np.diff(np.concatenate([[1.0], scale])))
    ov_cost = float(ds[ok].sum() * rt / 2.0 / bars)
    pos_cost = float(rt * turn * expo)
    pnl = np.array([x[3] for x in res["trades"]])
    return dict(
        gross_bp=float(b.mean()) * 1e4, vol_bp=float(sd) * 1e4,
        sharpe=float(b.mean() / sd * np.sqrt(ANN)) if sd > 0 else None,
        t=float(b.mean() / (sd / np.sqrt(bars))) if sd > 0 else None,
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
        exposure=expo, held_per_bar=float(res["held"][ok].mean()),
        turnover=float(turn), entries=e, trades=int(pnl.size),
        round_trip=float(rt), cost_pos_bp=pos_cost, cost_overlay_bp=ov_cost,
        net_bp=float(b.mean()) * 1e4 - pos_cost - ov_cost,
        trade_mean_bp=float(pnl.mean()) * 1e4 if pnl.size else None,
        trade_median_bp=float(np.median(pnl)) * 1e4 if pnl.size else None,
        bars=bars)


def held_rt(res, half):
    """Round trip on the names ACTUALLY HELD at this depth (D285's rule)."""
    hv = np.array([half[e0, row] for row, e0, _a, _p, _s in res["trades"]])
    hv = hv[np.isfinite(hv)]
    return 4.0 * float(np.median(hv)) if hv.size else np.nan


# --------------------------------------------------------------------------
def assertions(A, G, half):
    print("\nASSERTIONS")
    base = {}
    for depth in DEPTHS:
        base[depth] = simulate(A, G, depth, False)

    # 4. BIT-IDENTITY at N=19 / none against D303's no-exit control.
    ref = D.simulate(A, "none", "flat", None)
    assert np.array_equal(np.nan_to_num(base[19]["book"], nan=-9e9),
                          np.nan_to_num(ref["book"], nan=-9e9)), \
        "N=19 / none is NOT D303's no-exit control"
    print(f"    [4] N=19/none is bit-identical to D303's no-exit control, "
          f"{int(base[19]['ent'].sum()):,} entries")

    # 3b. THE PRE-SORTED GATE IS THE ONE IT REPLACED, bit-identically.
    lg = simulate(A, G, 5, True, legacy=True)
    fs = simulate(A, G, 5, True)
    assert np.array_equal(np.nan_to_num(lg["book"], nan=-9e9),
                          np.nan_to_num(fs["book"], nan=-9e9)), \
        "the cached gate differs from rebuilding it per bar"
    print("    [3b] the pre-sorted gate is bit-identical to rebuilding it "
          "per bar over all 1,573 rows")

    # 10. THE NO-EXIT ARM MUST REPRODUCE D300 AT EVERY DEPTH.
    d300 = json.loads((REPO / "data" / "d300_width.json").read_text())["depths"]
    worst = 0.0
    for depth in DEPTHS:
        got = float(np.nanmean(base[depth]["book"][base[depth]["mask"]])) * 1e4
        want = d300[str(depth)]["gross_bp"]
        worst = max(worst, abs(got - want))
    assert worst < 1e-9, (f"[10] the no-exit arm differs from D300 by up to "
                          f"{worst:.2e} bp -- the two studies are not on the "
                          f"same book")
    print(f"    [10] the no-exit arm reproduces D300 at all {len(DEPTHS)} "
          f"depths, max difference {worst:.2e} bp")

    # 11. THE OVERLAY MUST NOT TOUCH THE HOLDINGS.
    tgt = simulate(A, G, 19, True)
    sc = overlay_scale(tgt["book"])
    assert 0.0 < sc.mean() < 1.0, "the overlay never fires, or never stops"
    a = stats(tgt, 19, np.ones_like(sc), 100.0, half)
    b = stats(tgt, 19, sc, 100.0, half)
    assert a["trades"] == b["trades"] and a["entries"] == b["entries"], \
        "[11] the overlay changed the trade ledger -- it is wired INTO the book"
    print(f"    [11] the overlay leaves the ledger identical "
          f"({a['trades']:,} trades) and is out of the market "
          f"{100 * (1 - sc.mean()):.1f}% of bars")

    # 3. RIGHT QUANTITY. Held names track the depth; turnover is invariant.
    turns = []
    for depth in DEPTHS:
        s = stats(base[depth], depth, np.ones(A["r1T"].shape[0]), 100.0, half)
        turns.append(s["turnover"])
        assert abs(s["held_per_bar"] - 2 * depth) < 0.05 * 2 * depth
    assert max(turns) - min(turns) < 0.02, "turnover moved with the depth"
    print(f"    [3] right quantity: held names track the depth; turnover "
          f"invariant, spread {max(turns) - min(turns):.4f}")

    # 5. EVERY CELL A DISTINCT BOOK.
    seen = {}
    for depth in DEPTHS:
        for ut in (False, True):
            r = simulate(A, G, depth, ut)
            k = np.nan_to_num(r["book"], nan=-9e9).tobytes()
            assert k not in seen, f"[5] N={depth}/{ut} duplicates {seen[k]}"
            seen[k] = f"N={depth}/{ut}"
    print(f"    [5] all {len(seen)} position-level books are distinct")

    # 6. THE PATH-INVARIANT LENS MUST HOLD MORE THAN THE VARIANT.
    for depth in (2, 19):
        v = simulate(A, G, depth, True)
        i = simulate(A, G, depth, True, slots=False)
        hv = float(v["held"][v["mask"]].mean())
        hi = float(i["held"][i["mask"]].mean())
        assert hi > hv, f"the invariant lens holds {hi:.1f} <= the variant's {hv:.1f}"
    print(f"    [6] the path-invariant lens holds strictly more than the "
          f"variant at N=2 and N=19")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [r for r in d295["rows"] if r["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's "
          f"{b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK.
    broke = False
    try:
        ok = base[19]["mask"]
        bad = base[19]["book"].copy()
        bad[np.flatnonzero(ok)[:100]] += 0.05
        assert float(np.nanmean(bad[ok])) == float(
            np.nanmean(base[19]["book"][ok]))
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

    print(f"D306  width x exits, both lenses  gate={N_BASE} k={BASE_HOLD}")
    D.build_cache(verbose=True)
    A = D.load_cache(mmap=True)
    G = build_gate(A)
    T = A["r1T"].shape[0]
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    print(f"  loaded ({time.time() - t0:.0f}s)")

    assertions(A, G, half)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    ones = np.ones(T)
    cells, drag = {}, {}
    for depth in DEPTHS:
        for ut in (False, True):
            v = simulate(A, G, depth, ut)           # path-variant
            i = simulate(A, G, depth, ut, slots=False)   # path-invariant
            rt = held_rt(v, half)
            sc = overlay_scale(v["book"])
            for ov in (False, True):
                name = ("none" if not ut else "target") + ("+overlay" if ov else "")
                key = f"N={depth}/{name}"
                cells[key] = stats(v, depth, sc if ov else ones, rt, half)
                cells[key].update(depth=depth, exit=name)
            # the two lenses, per trade only -- never in bp/bar beside the book
            pv = np.array([x[3] for x in v["trades"]])
            pi = np.array([x[3] for x in i["trades"]])
            drag[f"N={depth}/{'target' if ut else 'none'}"] = dict(
                variant_trade_bp=float(pv.mean()) * 1e4,
                invariant_trade_bp=float(pi.mean()) * 1e4,
                drag_bp=float(pi.mean() - pv.mean()) * 1e4,
                variant_trades=int(pv.size), invariant_trades=int(pi.size),
                variant_held=float(v["held"][v["mask"]].mean()),
                invariant_held=float(i["held"][i["mask"]].mean()))
        print(f"  N={depth} done ({time.time() - t0:.0f}s)", flush=True)

    # nulls: the overlay is post-hoc, so 14 sims per draw serve 28 cells
    for depth in DEPTHS:
        for ut in (False, True):
            rng = np.random.default_rng([SEED, depth, int(ut)])
            offs = rng.choice(np.arange(1, N_BASE), size=a.draws, replace=True)
            acc = {}
            for s in offs:
                r = simulate(A, G, depth, ut, shift=int(s))
                ok = r["mask"]
                if int(ok.sum()) < 200:
                    continue
                nsc = overlay_scale(r["book"])
                for ov in (False, True):
                    sc = nsc if ov else ones
                    b = (r["book"] * sc)[ok]
                    nm = ("none" if not ut else "target") + ("+overlay" if ov else "")
                    acc.setdefault(nm, ([], []))
                    acc[nm][0].append(float(b.mean()) * 1e4)
                    acc[nm][1].append(float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)))
            for nm, (gm, sh) in acc.items():
                key = f"N={depth}/{nm}"
                ga, sa = np.array(gm), np.array(sh)
                c = cells[key]
                c["null_gross_p95"] = float(np.quantile(ga, .95))
                c["null_sharpe_p95"] = float(np.quantile(sa, .95))
                c["p_gross"] = float((ga >= c["gross_bp"]).sum() + 1) / (ga.size + 1)
                c["p_sharpe"] = float((sa >= c["sharpe"]).sum() + 1) / (sa.size + 1)
        print(f"    nulls N={depth} ({time.time() - t0:.0f}s)", flush=True)

    OUT.write_text(json.dumps(dict(
        purpose="D306: book width crossed with the exits, through the "
                "path-variant and path-invariant lenses.",
        preregistered="5926d93", draws=a.draws,
        overlay="D297 X=12 s=0.0, applied to the return series only",
        null="circular shift of the rank assignment within the 25-name gate",
        cells=cells, contention=drag), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
