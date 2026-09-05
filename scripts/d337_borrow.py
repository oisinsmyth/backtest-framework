"""D337 -- constant-shares P&L kernel and the declared borrow stress charge.

Pure numpy; imported by run_d337_constant_shares_borrow.py. Nothing here edits
any downstream key: `net_bp` and `mean_over_2c` are copied through untouched
and the borrow lands under NEW keys only (docs/decisions/D337 section 2).

Schemes (bp per year, charged on SHORT position-bars only, / 252):
    none    0
    gc_htb  GC_BPS general collateral; HTB_BPS if the name is hard-to-borrow --
            inside an F0 deal window at e0 - 1 (D331's one-bar lag) or with a
            close at entry below PX_HTB
    house   HOUSE_BPS flat (the fixture's previously declared assumption)
"""

from __future__ import annotations

import math

import numpy as np

GC_BPS = 50.0
HTB_BPS = 500.0
HOUSE_BPS = 300.0
PX_HTB = 5.0
ANN = 252.0
SCHEMES = ("none", "gc_htb", "house")


# ------------------------------------------------------------------ kernel
def compound_pnl(v, mt, sgn) -> float:
    """Constant shares on the name, daily-rebalanced market hedge, signed."""
    v = np.asarray(v, float)
    mt = np.asarray(mt, float)
    return float(sgn * (math.expm1(float(np.log1p(v).sum())) - float(mt.sum())))


def compound_from_ledger(trades, r1T, mkt) -> np.ndarray:
    """Per trade, recomputed from (row, e0, age, side) on r1T and mkt."""
    out = np.empty(len(trades))
    for i, (row, e0, age, _p, side) in enumerate(trades):
        sgn = 1.0 if side == 0 else -1.0
        out[i] = compound_pnl(r1T[e0:e0 + age, row], mkt[e0:e0 + age], sgn)
    return out


# ------------------------------------------------------------------ borrow
def htb_flags(trades, excl_nT, CLOSE_Tn) -> np.ndarray:
    """True for SHORT trades in an F0 window at e0-1 or priced below PX_HTB at
    entry; False for every long. excl is (n, T); CLOSE is (T, n)."""
    out = np.zeros(len(trades), bool)
    for i, (row, e0, _age, _p, side) in enumerate(trades):
        if side != 1:
            continue
        px = CLOSE_Tn[e0, row]
        out[i] = bool(excl_nT[row, max(e0 - 1, 0)]) or bool(px < PX_HTB)
    return out


def rate_bps(trades, htb, scheme) -> np.ndarray:
    """Annual borrow rate per trade in bp; zero on every long."""
    if scheme not in SCHEMES:
        raise ValueError(f"unknown borrow scheme {scheme!r}")
    short = np.array([t[4] == 1 for t in trades], bool)
    htb = np.asarray(htb, bool)
    if scheme == "none":
        return np.zeros(len(trades))
    if scheme == "gc_htb":
        return np.where(short, GC_BPS + (HTB_BPS - GC_BPS) * htb, 0.0)
    return np.where(short, HOUSE_BPS, 0.0)


def borrow_per_trade_bp(trades, rate) -> np.ndarray:
    age = np.array([t[2] for t in trades], float)
    return np.asarray(rate, float) * age / ANN


def borrow_per_bar_bp(res, trades, rate, T) -> np.ndarray:
    """bp per bar on the BOOK: each short position's rate / (252 * cnt1[t])
    over its held bars, the short leg's weight being 1/cnt1[t] on bar t.
    Bars still open at T are covered only up to the ledger, as per trade."""
    cnt1 = np.asarray(res["cnt1"], float)
    acc = np.zeros(T)
    for (row, e0, age, _p, side), r in zip(trades, rate):
        if side != 1 or r == 0.0:
            continue
        acc[e0:e0 + age] += r / ANN
    return np.where(cnt1 > 0, acc / np.maximum(cnt1, 1.0), 0.0)


def reconcile(bar_bp, res, per_trade) -> float:
    cnt1 = np.asarray(res["cnt1"], float)
    return float(abs((np.asarray(bar_bp) * cnt1).sum() - np.asarray(per_trade).sum()))


def costed_with_borrow(c: dict, bar_bp, mask) -> dict:
    """G22.costed's dict plus borrow_bp and net_bp_borrow; net_bp untouched."""
    out = dict(c)
    b = float(np.asarray(bar_bp)[np.asarray(mask, bool)].mean())
    out["borrow_bp"] = b
    out["net_bp_borrow"] = c["net_bp"] - b
    return out


def legcost_with_borrow(inv: dict, per_trade) -> dict:
    """V9.invariant_legcost's dict plus borrow_per_trade and
    net_per_trade_borrow; mean_over_2c untouched."""
    out = dict(inv)
    b = float(np.asarray(per_trade, float).mean())
    out["borrow_per_trade"] = b
    out["net_per_trade_borrow"] = inv["net_per_trade"] - b
    return out


# ------------------------------------------------------------------ [S]
def selftest() -> None:
    """Kernel sign audit on synthetic paths, mt = 0 (D337 section 6 [S])."""
    mt = np.zeros(2)
    cases = [  # path, sgn, summed, compound
        ([-0.5, 1.0], +1.0, +0.5, 0.0),
        ([-0.5, 1.0], -1.0, -0.5, 0.0),
        ([-0.5, -0.5], +1.0, -1.0, -0.75),
        ([-0.5, -0.5], -1.0, +1.0, +0.75),
    ]
    for path, sgn, want_sum, want_cmp in cases:
        v = np.array(path)
        got_sum = float(sgn * (v - mt).sum())
        got_cmp = compound_pnl(v, mt, sgn)
        assert abs(got_sum - want_sum) < 1e-12, (path, sgn, got_sum, want_sum)
        assert abs(got_cmp - want_cmp) < 1e-12, (path, sgn, got_cmp, want_cmp)
        # the simulator's form: summed minus the signed premium
        prem = sgn * (v.sum() - math.expm1(float(np.log1p(v).sum())))
        assert abs((got_sum - prem) - want_cmp) < 1e-12
    # the kernel must RAISE on a wrong expectation
    broke = False
    try:
        assert abs(compound_pnl(np.array([-0.5, 1.0]), mt, 1.0) - 0.5) < 1e-12
    except AssertionError:
        broke = True
    assert broke, "[S] the kernel test passed a wrong expectation"


if __name__ == "__main__":
    selftest()
    print("OK  d337_borrow kernel self-test")
