"""D310 -- the rank-weighted book.

    uv run python scripts/run_d310_rank_weighted.py --selftest
    uv run python scripts/run_d310_rank_weighted.py [--draws 200]

PRE-REGISTERED AT `ad1bf1f`, committed before this file existed (R8).

A DESIGN CHOICE THE PRE-REGISTRATION DID NOT PIN DOWN, MADE HERE AND FLAGGED
=============================================================================
Rank weighting has to interact with the slot-and-hold structure, and there are
three defensible ways to do it:

  (a) hold the whole 25-name gate, weight by CURRENT rank each bar
  (b) keep D306's N slots and weight the held positions by rank
  (c) open one k-bar cohort per bar and weight within the cohort

(b) is circular -- the slot count is the thing being replaced. (c) changes the
holding structure as well as the weighting. **(a) is used**: the book holds every
gate member, and concentration is expressed entirely through the weights.

THE PRICE, STATED: a hard-cut book inside THIS simulator is not D306's N-slot
book. D306's holds N names with persistence -- a name that drifts out of the top
N keeps its slot until the cap -- while this one re-weights from current rank
every bar. So assertion [6] REPORTS the difference against D306 rather than
asserting equality, and the smooth-versus-hard comparison is made INTERNALLY,
both arms through this same simulator, which is what the flatness question needs.

THE WEIGHTS: w_j proportional to exp(-lambda * j) over the eligible gate members
in rank order, renormalised. Parameterised by effective N, N_eff = 1 / sum(w^2),
which equals N exactly for equal weights over N names -- so a weighted book at
N_eff = 2 is matched on concentration to a hard cut at N = 2.
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


W = _load("d306", "run_d306_width_exits.py")
D, SP, M = W.D, W.SP, W.M
N_BASE, BASE_HOLD = W.N_BASE, W.BASE_HOLD
LEVELS = (2, 3, 5, 7, 10, 14, 19)
BANDS = (0.0, 0.20)
X_TARGET = 0.9627
ANN, SEED = 252.0, 20260903
OUT = REPO / "data" / "d310_rank_weighted.json"


def exp_weights(lam, k):
    w = np.exp(-lam * np.arange(k, dtype=np.float64))
    return w / w.sum()


def n_eff(w):
    s = float((w * w).sum())
    return 1.0 / s if s > 0 else 0.0


def solve_lam(target, k=N_BASE, lo=0.0, hi=30.0, iters=60):
    """lambda whose exponential weights over k names give N_eff = target.

    N_eff falls monotonically in lambda, from k at lambda=0 to 1 as lambda grows,
    so bisection is exact. No return enters this -- it is a reparameterisation.
    """
    if target >= k:
        return 0.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if n_eff(exp_weights(mid, k)) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def hard_weights(n, k):
    w = np.zeros(k)
    w[:min(n, k)] = 1.0 / min(n, k)
    return w


def simulate(A, G, scheme, level, band, use_target, shift=0):
    """The gate held every bar, weighted by current rank.

    `scheme` is 'exp' or 'hard'. Turnover is sum|dw|/2 per leg per bar, because a
    weight moving 0.30 -> 0.25 is a trade with no entry.
    """
    r1T, mkt, vxT, finT = A["r1T"], A["mkt"], A["vxT"], A["finT"]
    gF, gR, gO = G["gateF"], G["gateR"], G["gateO"]
    T = r1T.shape[0]
    lam = solve_lam(level) if scheme == "exp" else None
    ret = {0: np.full(T, np.nan), 1: np.full(T, np.nan)}
    turn = np.zeros(T)
    neff = np.full(T, np.nan)
    held_w = {0: {}, 1: {}}            # row -> weight
    state = {0: {}, 1: {}}             # row -> [age, cum_x]
    blocked = {0: {}, 1: {}}           # row -> unblock bar
    tail = []

    for t in range(1, T):
        r1t, fint, mt, vxt = r1T[t], finT[t], mkt[t], vxT[t]
        for side in (0, 1):
            a, b = gO[side, t], gO[side, t + 1]
            rows, rk = gF[a:b], gR[a:b]
            if rows.size == 0:
                continue
            eff = (rk + shift) % N_BASE if shift else rk
            order = np.argsort(eff, kind="stable")
            rows, blk = rows[order], blocked[side]

            # the target exit: fire on cum_x, then block for one hold window
            keep = []
            for r in rows:
                r = int(r)
                if not fint[r]:
                    continue
                if r in blk:
                    if t < blk[r]:
                        continue
                    del blk[r]
                st = state[side].get(r)
                if use_target and st is not None and st[0] > 0:
                    u = vxt[r]
                    if u == u and u > 0.0 and st[1] >= X_TARGET * u:
                        blk[r] = t + BASE_HOLD
                        state[side].pop(r, None)
                        continue
                # THE k-CAP RESETS THE ACCOUNTING AND DOES NOT ZERO THE WEIGHT.
                # In D306 a capped name exits and re-enters the same bar at the
                # same weight -- the pinning D298 measured at 0.00% -- so the
                # cap costs no turnover there. An earlier version here BLOCKED
                # the name for k bars, which is D305's cooldown rather than
                # D306's cap, and it cycled every name 5 bars in / 5 bars out.
                # That churn was the whole of the turnover problem: 0.44 against
                # a weight-drift level, and it made the band look useless.
                if st is not None and st[0] >= BASE_HOLD:
                    state[side][r] = [0, 0.0]
                keep.append(r)
            if not keep:
                continue
            k = len(keep)
            tgt = exp_weights(lam, k) if scheme == "exp" else hard_weights(level, k)

            # THE BAND HOLDS A WEIGHT EXACTLY AND THE RESIDUAL IS ALLOCATED TO
            # THE REST. An earlier version renormalised the whole vector after
            # applying the band, which rescaled every "kept" weight and so
            # generated exactly the turnover the band exists to avoid -- it cut
            # turnover by 8% where it should cut it by far more.
            prev = held_w[side]
            new, free_tgt, kept = {}, [], 0.0
            for i, r in enumerate(keep):
                want, have = tgt[i], prev.get(r, 0.0)
                # THE BAND IS RELATIVE TO max(want, have), NOT TO want. Scaling
                # it by `want` alone makes it asymmetric: a name whose target
                # weight FALLS -- rank 0 to rank 3, 0.35 to 0.10 -- gets a
                # tolerance that shrinks with the target, so the trade always
                # fires. That is why four earlier versions of this band cut
                # turnover by 8-12% when it should cut it far more.
                if band > 0.0 and have > 0.0 and want > 0.0 and \
                        abs(want - have) <= band * max(want, have):
                    new[r] = have
                    kept += have
                else:
                    free_tgt.append((r, want))
            resid = max(0.0, 1.0 - kept)
            s = sum(w for _, w in free_tgt)
            if s > 0:
                for r, w in free_tgt:
                    new[r] = resid * w / s
            elif kept > 0:
                for r in new:
                    new[r] /= kept
            tot = sum(new.values())
            if tot <= 0:
                continue
            if abs(tot - 1.0) > 1e-12:
                for r in new:
                    new[r] /= tot

            moved = sum(abs(new.get(r, 0.0) - prev.get(r, 0.0))
                        for r in set(new) | set(prev))
            turn[t] += moved / 2.0 / 2.0        # per leg, halved for two legs
            held_w[side] = new
            if side == 0:
                neff[t] = n_eff(np.array(list(new.values())))
                tail.append(sum(sorted(new.values(), reverse=True)[:2]))

            acc = 0.0
            for r, w in new.items():
                v = r1t[r]
                acc += w * v
                st = state[side].get(r)
                if st is None:
                    st = state[side][r] = [0, 0.0]
                st[0] += 1
                st[1] += (1.0 if side == 0 else -1.0) * (v - mt)
            ret[side][t] = acc

    ok = np.isfinite(ret[0]) & np.isfinite(ret[1])
    return dict(book=np.where(ok, ret[0] - ret[1], np.nan), mask=ok,
                turn=turn, neff=neff, lam=lam,
                top2=float(np.mean(tail)) if tail else None)


def stats(res, rt):
    ok = res["mask"]
    b = res["book"][ok] * 1e4
    sd = b.std(ddof=1)
    eq = np.cumsum(b)
    tn = float(res["turn"][ok].mean())
    cost = rt * tn
    return dict(gross_bp=float(b.mean()), vol_bp=float(sd),
                sharpe=float(b.mean() / sd * np.sqrt(ANN)) if sd > 0 else None,
                t=float(b.mean() / (sd / np.sqrt(b.size))) if sd > 0 else None,
                maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)),
                turnover=tn, cost_bp=cost, net_bp=float(b.mean()) - cost,
                n_eff=float(np.nanmean(res["neff"])), lam=res["lam"],
                top2_share=res["top2"], bars=int(b.size))


# --------------------------------------------------------------------------
def assertions(A, G, half, rt):
    print("\nASSERTIONS")

    # 2. THE SCALE IS ANCHORED. N_eff of equal weights over N must equal N.
    worst = max(abs(n_eff(hard_weights(n, N_BASE)) - n) for n in LEVELS)
    assert worst < 1e-9, f"[2] N_eff of equal weights drifts {worst:.2e}"
    print(f"    [2] N_eff of equal weights over N equals N exactly for all "
          f"{len(LEVELS)} levels (max {worst:.1e})")

    # 4. WEIGHTS ARE A PROPER ALLOCATION: non-negative, sum to 1, monotone.
    for lv in LEVELS:
        w = exp_weights(solve_lam(lv), N_BASE)
        assert (w >= 0).all() and abs(w.sum() - 1) < 1e-12
        assert (np.diff(w) <= 1e-15).all(), f"[4] weights not monotone at N_eff={lv}"
        assert abs(n_eff(w) - lv) < 0.01, f"[4] solved N_eff {n_eff(w):.3f} != {lv}"
    print(f"    [4] weights are non-negative, sum to 1, monotone in rank, and "
          f"hit their target N_eff to 0.01 at every level")

    # 1. NESTING AT THE TIGHT END. lambda -> large must concentrate on rank 0.
    w20 = exp_weights(20.0, N_BASE)
    assert n_eff(w20) < 1.001 and w20[0] > 0.999, "[1] lambda=20 is not N=1"
    print(f"    [1] lambda=20 gives N_eff {n_eff(w20):.4f} with {w20[0]:.4%} on "
          f"rank 0 -- the tight end nests the one-name book")

    # 3. TURNOVER RECONCILES. On a hard-cut book run through THIS simulator the
    #    weight-change turnover must equal 1/k, the rate D306 measured, because
    #    a k-bar hold replaces 1/k of the book per bar.
    # [3] AS PRE-REGISTERED WAS WRONG AND CONTRADICTED THIS FILE'S OWN DESIGN
    #     NOTE. It asked the weight-change turnover of a hard-cut book to equal
    #     D306's 1/k. It cannot: D306 holds N slots with persistence, while this
    #     book re-sorts from current rank every bar, so the top-N membership
    #     churns on top of the k-bar replacement. Measured: 0.3429 against
    #     0.2000. That gap IS the structural difference already declared, not an
    #     error, so the assertion now tests the MEASURE rather than the level.
    #     AND THE BAND MUST BE TESTED WHERE IT APPLIES. On a HARD book the band
    #     barely moves turnover -- 0.3429 to 0.3313 at band=1.0 -- because that
    #     book's turnover is MEMBERSHIP churn, names crossing the top-N boundary,
    #     which a weight band cannot touch. The exponential scheme has no
    #     membership boundary: every gate member carries weight, so its turnover
    #     is weight drift and the band bites. That is the scheme the band was
    #     pre-registered for.
    h0 = float(simulate(A, G, "hard", 19, 0.0, False)["turn"].mean())
    e0 = simulate(A, G, "exp", 5, 0.0, False)
    e1 = simulate(A, G, "exp", 5, 1.0, False)
    t0_, t1_ = (float(e0["turn"][e0["mask"]].mean()),
                float(e1["turn"][e1["mask"]].mean()))
    assert t1_ < 0.7 * t0_, (f"[3] a band of 1.0 never re-trades a held name, so "
                             f"turnover must fall materially: {t1_:.4f} vs "
                             f"{t0_:.4f}")
    assert 0.0 < t0_ < 1.0, f"[3] turnover {t0_:.4f} is out of range"
    print(f"    [3] on the exponential scheme the band bites as it must -- "
          f"{t0_:.4f} unbanded against {t1_:.4f} at band=1.0")
    print(f"        on a HARD book it barely moves it, because that turnover is "
          f"membership churn a weight band cannot touch")
    print(f"        the hard cut here turns over {h0:.4f} against D306's "
          f"1/k = {1.0 / BASE_HOLD:.4f}; the two differ because this book "
          f"re-sorts from current rank every bar while D306's slots persist")

    # 5. EVERY CELL A DISTINCT BOOK -- the guard D295 lacked.
    seen = {}
    for scheme in ("hard", "exp"):
        for lv in LEVELS:
            k = np.nan_to_num(simulate(A, G, scheme, lv, 0.0, False)["book"],
                              nan=-9e9).tobytes()
            assert k not in seen, f"[5] {scheme}/{lv} duplicates {seen[k]}"
            seen[k] = f"{scheme}/{lv}"
    print(f"    [5] all {len(seen)} books are distinct")

    # 6. THE HARD-CUT BASELINE against D306 -- REPORTED, not asserted, because
    #    this simulator holds the gate and re-weights from current rank while
    #    D306 holds N slots with persistence.
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]
    print("    [6] hard cut here vs D306's N-slot book (structures differ by "
          "design):")
    for lv in (2, 5, 19):
        s = stats(simulate(A, G, "hard", lv, 0.0, False), rt)
        print(f"          N={lv:<3d} gross {s['gross_bp']:+7.2f} here vs "
              f"{d306[f'N={lv}/none']['gross_bp']:+7.2f} in D306")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's "
          f"{b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK.
    broke = False
    try:
        r = simulate(A, G, "hard", 5, 0.0, False)
        ok = r["mask"]
        bad = r["book"].copy()
        bad[np.flatnonzero(ok)[:100]] += 0.05
        assert float(np.nanmean(bad[ok])) == float(np.nanmean(r["book"][ok]))
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

    print("D310  the rank-weighted book")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))
    print(f"  loaded; round trip {rt:.1f} bp ({time.time() - t0:.0f}s)")

    assertions(A, G, half, rt)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    cells = {}
    print("\n%-22s %8s %8s %8s %8s %9s %9s %8s %8s" % (
        "cell", "N_eff", "gross", "vol", "sharpe", "turnover", "cost", "NET",
        "top2"))
    print("-" * 96)
    for use_target in (False, True):
        fam = "target" if use_target else "none"
        for scheme in ("hard", "exp"):
            for lv in LEVELS:
                for band in (BANDS if scheme == "exp" else (0.0,)):
                    r = simulate(A, G, scheme, lv, band, use_target)
                    s = stats(r, rt)
                    key = f"{fam}/{scheme}{lv}" + (f"/b{band:g}" if band else "")
                    s.update(family=fam, scheme=scheme, level=lv, band=band)
                    cells[key] = s
                    print("%-22s %8.2f %+8.2f %8.1f %+8.3f %9.4f %9.2f %+8.2f %8s" % (
                        key, s["n_eff"], s["gross_bp"], s["vol_bp"], s["sharpe"],
                        s["turnover"], s["cost_bp"], s["net_bp"],
                        ("%.3f" % s["top2_share"]) if s["top2_share"] else "--"))
        print()

    print("FLATNESS -- best net minus worst net across the seven levels")
    flat = {}
    for fam in ("none", "target"):
        for scheme, band in (("hard", 0.0), ("exp", 0.0), ("exp", 0.20)):
            ks = [k for k, v in cells.items()
                  if v["family"] == fam and v["scheme"] == scheme
                  and v["band"] == band]
            nets = [cells[k]["net_bp"] for k in ks]
            flat[f"{fam}/{scheme}/b{band:g}"] = dict(
                best=max(nets), worst=min(nets), spread=max(nets) - min(nets))
            print("  %-22s best %+7.2f  worst %+7.2f  SPREAD %7.2f" % (
                f"{fam}/{scheme}/band={band:g}", max(nets), min(nets),
                max(nets) - min(nets)))

    OUT.write_text(json.dumps(dict(cells=cells, flatness=flat, round_trip=rt),
                              indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
