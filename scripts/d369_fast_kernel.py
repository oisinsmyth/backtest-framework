"""D369 -- an EXACT fast kernel for the gated-buffer null draws.

    uv run python scripts/d369_fast_kernel.py --verify

WHY. Deciding a verdict at 10,000 draws instead of 200 costs 50x the compute, and D366's kernel spends its time
where a null does not need it. Profiled (never guessed): of 0.181s per draw, hold_of is 36%, book_of 37%, costs
26%, and stats 0.6% -- so the drawdown code I assumed was the problem is irrelevant, and book_of's cost is
allocating six (T, n) float arrays per call to read the 1% of entries that are actually held.

EXACTNESS, NOT TOLERANCE (CLAUDE.md). Every rewrite here either hoists an invariant, skips what nothing reads, or
indexes sparsely into a PRE-ZEROED buffer of the same shape -- so the dense sum runs over the same values at the
same positions in the same order and is bit-identical, not merely close. Two places where that took care:

  1  book_of's per-bar mean is `np.where(h, x, 0.0).sum(axis=1)`. Summing only the held entries would reorder a
     float sum: numpy's pairwise summation groups by index block, and interspersed zeros change the grouping of
     the non-zeros ((a+b)+c vs a+(b+c)). So the buffer stays (T, n), is memset to zero, and is filled by masked
     copy -- same tree, same result.
  2  the per-trade cost sums a ledger that `trades_of` emits sorted by (entry bar, row). The vectorised ledger
     comes out column-major, so it is re-sorted into that exact order before summing.

`--verify` asserts bit-identity against D366's own functions across many gates including rotations, on the real
percentile grid (which is tie-heavy by construction: percentile_grid gives tied scores a shared percentile).
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_d366_gated_buffer as V66            # noqa: E402
import run_d365_momentum_buffer as V65         # noqa: E402

PREP, V58 = V66.PREP, V66.V58
ANN, GC_BPS, HEDGE_HS = 252.0, V66.GC_BPS, V66.HEDGE_HS


class Kernel:
    """Everything invariant to the gate, hoisted once. A gate rotation changes only `gate`."""

    def __init__(self, P, pct, elig, mkt_cc, mkt_oc, cv="PUB"):
        self.P, self.T, self.n, self.m0 = P, P["T"], P["n"], P["m_start"]
        self.pct, self.elig = pct, np.asarray(elig, bool)
        r1T, ocT = np.asarray(P["r1T"], float), np.asarray(P["ocT"], float)

        # --- the two hedged return grids, and the PRE-ZEROED values the book sums -------------------
        X_cc = r1T - mkt_cc[:, None]
        X_oc = ocT - mkt_oc[:, None]
        ok_cc = self.elig & np.isfinite(X_cc)
        ok_oc = self.elig & np.isfinite(X_oc)
        self.ZCC = np.where(ok_cc, X_cc, 0.0)     # what a held NON-entry bar contributes
        self.ZOC = np.where(ok_oc, X_oc, 0.0)     # what a held ENTRY bar contributes
        self.OKCC, self.OKOC = ok_cc, ok_oc

        # --- the hold loop's per-bar masks, hoisted out of the loop ---------------------------------
        al = self.elig & np.isfinite(pct)
        self.enter = al & (pct > V66.HI)
        self.keep_open = al & (pct > V66.LO_OPEN)
        self.keep_shut = al & (pct > V66.LO_SHUT)

        # --- costing inputs -------------------------------------------------------------------------
        self.HALF = np.asarray(P["HALF"][cv], float)
        self.RAWC = np.asarray(P["RAW_CLOSE"], float)
        self.med_half = float(np.nanmedian(self.HALF))

        # --- reusable buffers: allocated ONCE, not once per draw -------------------------------------
        self._buf = np.empty((self.T, self.n), float)
        self._hold = np.zeros((self.T, self.n), bool)
        self._st = np.empty((self.T, self.n), bool)
        self._en = np.empty((self.T, self.n), bool)
        self._prev = np.zeros(self.n, bool)
        self._cur = np.zeros(self.n, bool)
        self._keep = np.zeros(self.n, bool)
        self._tmp = np.zeros(self.n, bool)
        self._age = np.zeros(self.n, np.int64)

    # ------------------------------------------------------------------ the hold loop
    def hold(self, gate, cap=V66.CAP):
        """Bit-identical to V66.hold_of: the same boolean recursion, with its invariants hoisted, every
        temporary preallocated, and the age update turned into two unmasked ops.

        `age = (age + 1) * cur` is exactly `where(cur, where(prev, age+1, 1), 0)` here, because age is already
        0 for anything not held at t-1 -- so the three masked writes the original needed become two."""
        hold = self._hold
        hold[:] = False
        prev, cur, keep, tmp = self._prev, self._cur, self._keep, self._tmp
        prev[:] = False
        age = self._age
        age[:] = 0
        ko, ks, en = self.keep_open, self.keep_shut, self.enter
        for t in range(self.m0, self.T):
            g = gate[t]
            np.logical_and(prev, ko[t] if g else ks[t], out=keep)
            if cap is not None:
                np.less(age, cap, out=tmp)
                np.logical_and(keep, tmp, out=keep)
            if g:
                np.logical_not(prev, out=tmp)
                np.logical_and(tmp, en[t], out=tmp)
                np.logical_or(keep, tmp, out=cur)
            else:
                np.copyto(cur, keep)
            np.add(age, 1, out=age)
            np.multiply(age, cur, out=age)
            hold[t] = cur
            prev, cur = cur, prev
        return hold

    # ------------------------------------------------------------------ the ledger, vectorised
    def ledger(self, hold):
        """(row, e0, exit) per trade, emitted sorted by (e0, row) -- `trades_of`'s own sort key, so the cost
        sum below reduces in the same sequence and is bit-identical.

        The first version transposed `hold` and cast it to int8, which copies 6.6M elements against the cache
        and cost more than the hold loop. This works in the natural (T, n) orientation: run starts and ends are
        two boolean row-shifts, and C-order `nonzero` already yields (t, col) -- the required order, no final
        sort. Only the START-to-END pairing needs column-major, and that is two lexsorts over ~1,000 trades."""
        st, en = self._st, self._en
        st[0] = hold[0]
        np.logical_and(hold[1:], ~hold[:-1], out=st[1:])
        en[-1] = hold[-1]
        np.logical_and(hold[:-1], ~hold[1:], out=en[:-1])
        st_t, st_c = np.nonzero(st)                        # C-order: sorted by (t, col) == (e0, row)
        en_t, en_c = np.nonzero(en)
        assert st_t.size == en_t.size, "ledger: starts and ends do not pair"
        os_ = np.lexsort((st_t, st_c))                     # by column, then time -- pairs 1:1 with ends
        oe_ = np.lexsort((en_t, en_c))
        ex = np.empty_like(st_t)
        ex[os_] = en_t[oe_]
        return st_c, st_t, ex

    # ------------------------------------------------------------------ one draw -> net bp/bar
    def net(self, gate, cap=V66.CAP, want=None):
        hold = self.hold(gate, cap=cap)
        rows, e0, ex = self.ledger(hold)

        # the book's per-bar mean, summed over a (T, n) buffer so the float order is unchanged
        buf = self._buf
        buf[:] = 0.0
        np.copyto(buf, self.ZCC, where=hold)
        buf[e0, rows] = self.ZOC[e0, rows]                 # entry bars fill open-to-close, both legs
        cn = np.count_nonzero(hold & self.OKCC, axis=1)
        cn_e = np.zeros(self.T, np.int64)
        np.add.at(cn_e, e0, self.OKOC[e0, rows].astype(np.int64) - self.OKCC[e0, rows].astype(np.int64))
        cn = cn + cn_e
        mask = cn > 0
        v = np.zeros(self.T)
        v[mask] = buf.sum(axis=1)[mask] / cn[mask] * 1e4

        # the cost, in trades_of's own order
        h1 = self.HALF[e0, rows]
        h1 = np.where(np.isfinite(h1), h1, np.nanmedian(h1) if np.isfinite(h1).any() else self.med_half)
        h2 = self.HALF[ex, rows]
        h2 = np.where(np.isfinite(h2), h2, h1)
        px = self.RAWC[e0, rows]
        two_c = h1 + h2 + V65.CROSSINGS_ONE_LEG * V65.PER_SHARE / px * 1e4
        pos = int(np.count_nonzero(hold))
        mem = np.count_nonzero(hold, axis=1).astype(float)
        mm = mem > 0
        reb = float(np.mean(np.abs(np.diff(mem, prepend=mem[0]))[mm] / np.maximum(mem[mm], 1)))
        cost = float(two_c.sum()) / pos + GC_BPS / ANN + reb * HEDGE_HS

        # `mean(v - cost)`, NOT `mean(v) - cost`: V66.stats subtracts the cost from the SERIES before averaging,
        # and the two differ in the last bits. That one transposition was the whole of a 3.6e-15 mismatch.
        net = float(np.mean(v[mask] - cost))
        if want is None:
            return net
        out = dict(net=net, gross=float(np.mean(v[mask])), cost=cost, trades=int(rows.size),
                   members=float(mem[mask].mean()), bars=int(mask.sum()))
        if "v" in want:
            out["v"], out["mask"], out["hold"] = v.copy(), mask, hold
        return out


# ================================================================== verification
def stage_verify(t0):
    P = PREP.prep(need_grids=False)
    import run_d367_gate_deconstruction as V67
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    cond, C, vq = V67.conditions(P)
    G = V67.gate_set(cond)
    cc, oc = V66.dvw_market(P)
    zeros = np.zeros((P["T"], P["n"]), float)
    K = Kernel(P, pct, elig, cc, oc)
    m0 = P["m_start"]

    ties = int((np.sort(pct[m0 + 1500])[1:] == np.sort(pct[m0 + 1500])[:-1]).sum())
    print(f"\n  the probe grid is TIE-HEAVY by construction: {ties} tied adjacent scores on one sampled bar "
          f"(percentile_grid gives tied scores a shared percentile)")

    rng = np.random.default_rng([V66.SEED, 369, 0])
    names = ["S6", "C9", "C4", "C2+C9", "C1"]
    probes = [(nm, G[nm]) for nm in names]
    for i in range(8):                                     # rotations, where a rewrite is most likely to disagree
        k = int(rng.integers(1, P["T"] - m0))
        probes.append((f"rot(S6,{k})", V67.rotate(G["S6"], m0, k)))
    for i in range(4):
        k = int(rng.integers(1, P["T"] - m0))
        probes.append((f"rot(C9,{k})", V67.rotate(G["C9"], m0, k)))

    print(f"  {'gate':<16}{'slow net':>12}{'fast net':>12}{'delta':>12}   hold identical?")
    worst = 0.0
    for nm, g in probes:
        s = V66.run_cell(P, g, pct, elig, cc, oc, zeros)
        f = K.net(g, want=("v",))
        same_hold = np.array_equal(s["hold"], f["hold"])
        d = abs(s["net"] - f["net"])
        worst = max(worst, d)
        assert same_hold, f"[FAST] {nm}: hold grid differs"
        assert s["cost_parts"]["trades"] == f["trades"], f"[FAST] {nm}: trade count"
        assert d == 0.0, f"[FAST] {nm}: net differs by {d:.3e} -- NOT bit-identical"
        print(f"  {nm:<16}{s['net']:+12.6f}{f['net']:+12.6f}{d:12.1e}   {'YES' if same_hold else 'NO'}")
    print(f"  [FAST] bit-identical on all {len(probes)} probes (worst |delta| {worst:.1e}), including "
          f"12 rotations")

    # speed
    g = G["S6"]
    t = time.time()
    for _ in range(10):
        V66.run_cell(P, g, pct, elig, cc, oc, zeros)
    slow = (time.time() - t) / 10
    t = time.time()
    for _ in range(10):
        K.net(g)
    fast = (time.time() - t) / 10
    print(f"\n  SPEED  slow {slow*1000:.0f} ms/draw   fast {fast*1000:.0f} ms/draw   {slow/fast:.1f}x")
    print(f"  10,000 draws: {slow*10000/60:.0f} min -> {fast*10000/60:.1f} min serial, "
          f"{fast*10000/60/8:.1f} min on 8 processes")
    print(f"\nOK  verify passes  ({time.time()-t0:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    if a.verify:
        stage_verify(t0)
    else:
        ap.error("--verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
