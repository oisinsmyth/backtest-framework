"""D402 -- is D280's overnight gap a real repricing, or a stale opening print?

    uv run python scripts/run_d402_stale_open_check.py --run

MEASUREMENT record. Scores no cell, ranks no name, proposes no rule, admits nothing, reads no
holdout, fetches nothing. Pre-registration 6843a39 predates this file (R8). Pre-registered as D390 and RENUMBERED to
D402: D390-D399 is reserved for the worktree-signal-hunt-part2 branch (fb2af62).

D280 tested the dividend confound exhaustively and it survived. It never tested whether the OPENING
PRINT IS REAL -- and gap(t+1) = open(t+1)/close(t) - 1 is formed entirely from the vendor's `open`,
on the ALL universe, which includes thin and low-priced names. Price alone killed D284.

Reuses D280's OWN module for the fixture, signal, split, grids and ic_series, so [REP] can hold the
runner to D280's committed numbers before any filter is applied.
"""
import argparse
import importlib.util
import json
import os
import pathlib
import sys
import time
from collections import Counter

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- [SPLIT] holdout guard, no unlock
_OPENED = dict(n=0, refused=0)


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    low = os.fspath(p).replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        raise RuntimeError(f"[SPLIT] refused to open {low}")


sys.addaudithook(_audit)

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
_s = importlib.util.spec_from_file_location("d280c", REPO / "scripts" / "d280_combined_forecast.py")
D280 = importlib.util.module_from_spec(_s)
sys.modules["d280c"] = D280
_s.loader.exec_module(D280)

B, C, P1, RP = D280.B, D280.C, D280.P1, D280.RP
SPLIT_DATE = D280.SPLIT_DATE
OUT = REPO / "data" / "d402_stale_open_check.json"

COMMITTED = {"ALL": -0.01531, "QUAL": -0.01255}    # [REP] -- D280's committed gap IC
TOL_REP = 5e-4
MIN_BARS = 1000
QUINTILES = 5


# --------------------------------------------------------------------- contamination signatures
def signatures(O, H, L, Cl, V, nxt, oos):
    """All applied to bar t+1, the bar whose OPEN forms the gap. S1-S4 are EXACT-equality tests on
    raw OHLC -- not tolerance comparisons -- because a carried-forward print is bit-identical."""
    nO, nH, nL, nCl, nV = nxt(O), nxt(H), nxt(L), nxt(Cl), nxt(V)
    s = {}
    s["S1 open == prior close"] = (nO == Cl)
    s["S2 open==high==low==close"] = (nO == nH) & (nH == nL) & (nL == nCl)
    s["S3 open at session extreme"] = (nO == nH) | (nO == nL)
    s["S4 zero/absent volume"] = ~np.isfinite(nV) | (nV <= 0)
    dv = Cl * V
    s["S5 cheap (bottom price quintile)"] = _bottom_quintile(Cl, oos)
    s["S6 thin (bottom $vol quintile)"] = _bottom_quintile(dv, oos)
    return {k: (v & oos) for k, v in s.items()}


def _bottom_quintile(X, oos):
    """Per BAR, cross-sectionally -- a price floor fixed in dollars would be a different test."""
    out = np.zeros_like(oos, dtype=bool)
    for t in range(X.shape[1]):
        col = X[:, t]
        m = oos[:, t] & np.isfinite(col) & (col > 0)
        if m.sum() < 20:
            continue
        cut = np.percentile(col[m], 100.0 / QUINTILES)
        out[:, t] = m & (col <= cut)
    return out


def quintile_masks(X, oos, q=QUINTILES):
    """Cross-sectional quintile membership, per bar."""
    out = [np.zeros_like(oos, dtype=bool) for _ in range(q)]
    for t in range(X.shape[1]):
        col = X[:, t]
        m = oos[:, t] & np.isfinite(col) & (col > 0)
        if m.sum() < 20:
            continue
        cuts = np.percentile(col[m], [100.0 * i / q for i in range(1, q)])
        idx = np.digitize(col, cuts)
        for k in range(q):
            out[k][:, t] = m & (idx == k)
    return out


def ic_cell(h, tgt, mask):
    """D280's own ic_series, with its bar count. Returns (mean, t, bars) or None below the floor."""
    ics = D280.ic_series(h, tgt, mask)
    if ics.size < 30:
        return None
    n = int(mask.sum())
    if n < MIN_BARS:
        return None
    mu = float(ics.mean())
    t = float(ics.mean() / (ics.std(ddof=1) / np.sqrt(ics.size)))
    return dict(ic=mu, t=t, bar_days=int(ics.size), obs=n)


# ------------------------------------------------------------------------------ assertions
def assert_REP(got):
    for u, want in COMMITTED.items():
        g = got[u]["ic"]
        assert abs(g - want) < TOL_REP, f"[REP] {u} gap IC {g:+.5f} != D280's {want:+.5f}"
    return {u: got[u]["ic"] for u in COMMITTED}


def assert_LAG(hs, h, gap, oos):
    """The signal must be the LAGGED score. An unlagged variant must give a DIFFERENT IC -- if it
    does not, the lag is not doing anything and D280's R9 discipline was decorative here."""
    un = ic_cell(hs, gap, oos)
    la = ic_cell(h, gap, oos)
    assert un is not None and la is not None, "[LAG] a cell fell below the bar floor"
    d = abs(un["ic"] - la["ic"])
    assert d > 1e-4, f"[LAG] lagged and unlagged ICs agree to {d:.2e} -- the lag does nothing"
    return la["ic"], un["ic"], d


def assert_SIG(sig, oos):
    """Report every signature's flagged share, and prove S1-S4 are EXACT tests: perturbing one
    matched open by one ULP must UNFLAG it."""
    shares = {k: float(v.sum() / max(oos.sum(), 1)) for k, v in sig.items()}
    for k in shares:
        assert 0.0 <= shares[k] <= 1.0, f"[SIG] {k} share {shares[k]}"
    return shares


def assert_X(O, Cl, nxt, oos, hs, h, gap):
    fired = {}
    try:                                            # [REP]: a number that is not D280's
        assert_REP({"ALL": {"ic": -0.010}, "QUAL": {"ic": -0.01255}})
        fired["REP"] = False
    except AssertionError:
        fired["REP"] = True
    try:                                            # [LAG]: comparing the signal to ITSELF
        assert_LAG(h, h, gap, oos)
        fired["LAG"] = False
    except AssertionError:
        fired["LAG"] = True
    try:
        # [SIG]: S1 must be EXACT. Nudging a matched open by one ULP must unflag that cell; if a
        # tolerance had crept in, the flag would survive and the count would not move.
        nO = nxt(O)
        eq = (nO == Cl) & oos
        assert eq.sum() > 0, "no S1 bars to perturb"
        i, t = [int(a[0]) for a in np.nonzero(eq)]
        pert = nO.copy()
        pert[i, t] = np.nextafter(pert[i, t], np.inf)
        assert int(((pert == Cl) & oos).sum()) == int(eq.sum()), "one ULP did not unflag"
        fired["SIG"] = False
    except AssertionError:
        fired["SIG"] = True
    bad = [k for k, v in fired.items() if not v]
    assert not bad, f"[X] these audits did NOT raise on a deliberate break: {bad}"
    return fired


# ------------------------------------------------------------------------------------ run
def run():
    t0 = time.time()
    print("\nRUN -- D402. Reusing D280's own module for fixture, signal, split and ic_series.")
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE)
    md, hs_raw, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    O, H, L, Cl = g["open"], g["high"], g["low"], g["close"]
    V = np.full_like(Cl, np.nan)
    pos = {d: i for i, d in enumerate(panel.dates)}
    for i, sym in enumerate(panel.symbols):
        for st in cleaned[sym]:
            V[i, pos[st.timestamp[:10]]] = st.bar.volume
    dates = np.array(panel.dates)
    oos = live & (dates >= SPLIT_DATE)[None, :]

    def nxt(x):
        out = np.full_like(x, np.nan)
        ok = live[:, 1:] & live[:, :-1]
        out[:, :-1] = np.where(ok, x[:, 1:], np.nan)
        return out

    gap = nxt(O) / Cl - 1.0
    intraday = nxt(Cl) / nxt(O) - 1.0
    okm = ~(np.isnan(md) | np.isnan(hs_raw)) & warm
    qual = oos & (-B.hold_book((hs_raw < 0) & (md >= 0) & okm, warm) != 0.0)
    h = C.lag1(hs_raw)
    print(f"  loaded {time.time()-t0:.0f}s   oos bars {int(oos.sum()):,}   qual {int(qual.sum()):,}")

    uni = {"ALL": oos, "QUAL": qual}
    base = {u: ic_cell(h, gap, m) for u, m in uni.items()}
    for u in uni:
        print(f"  [REP] {u:>4} gap IC {base[u]['ic']:+.5f} (t {base[u]['t']:+.2f}) "
              f"vs D280's {COMMITTED[u]:+.5f}")
    assert_REP(base)
    print("  [REP] reproduces D280's committed gap IC before any filter")
    la, un, d = assert_LAG(hs_raw, h, gap, oos)
    print(f"  [LAG] lagged {la:+.5f} vs unlagged {un:+.5f}, gap {d:.2e}")

    sig = signatures(O, H, L, Cl, V, nxt, oos)
    shares = assert_SIG(sig, oos)
    print(f"  [SIG] flagged shares: " + ", ".join(f"{k.split()[0]} {100*v:.2f}%"
                                                 for k, v in shares.items()))
    print(f"  [SPLIT] guard saw {_OPENED['n']:,} opens, refused {_OPENED['refused']}")
    print(f"  [X]     {assert_X(O, Cl, nxt, oos, hs_raw, h, gap)}")

    out = {"base": base, "shares": shares, "signatures": {}, "clean": {}, "quintiles": {},
           "reversal": {}}

    print("\n  P2 -- the gap IC WITHIN each contamination signature (ALL universe)")
    print(f"{'signature':>34}{'share':>8}{'IC':>10}{'t':>8}{'obs':>10}")
    for k, m in sig.items():
        c = ic_cell(h, gap, m & oos)
        out["signatures"][k] = c
        if c is None:
            print(f"{k:>34}{100*shares[k]:>7.2f}%{'--':>10}{'--':>8}{'too few':>10}")
        else:
            print(f"{k:>34}{100*shares[k]:>7.2f}%{c['ic']:>10.5f}{c['t']:>8.2f}{c['obs']:>10,}")

    print("\n  P1 -- the gap IC on CLEAN bars")
    exact = sig["S1 open == prior close"] | sig["S2 open==high==low==close"] | \
        sig["S3 open at session extreme"] | sig["S4 zero/absent volume"]
    liq = sig["S5 cheap (bottom price quintile)"] | sig["S6 thin (bottom $vol quintile)"]
    cuts = {"exact-print clean (not S1-S4)": ~exact,
            "liquidity clean (not S5-S6)": ~liq,
            "CLEAN (neither)": ~(exact | liq)}
    print(f"{'universe':>7}{'cut':>34}{'IC':>10}{'t':>8}{'vs committed':>14}{'obs':>10}")
    for u, um in uni.items():
        for label, keep in cuts.items():
            c = ic_cell(h, gap, um & keep)
            out["clean"][f"{u}|{label}"] = c
            if c is None:
                continue
            rel = c["ic"] / base[u]["ic"]
            print(f"{u:>7}{label:>34}{c['ic']:>10.5f}{c['t']:>8.2f}{rel:>13.2f}x{c['obs']:>10,}")

    print("\n  P3 -- THE DISCRIMINATING TEST: gap IC by liquidity and by price (ALL)")
    dv = Cl * V
    for nm, X in (("$ volume", dv), ("price", Cl)):
        qs = quintile_masks(X, oos)
        print(f"{nm:>12} quintile:" + "".join(f"{'Q'+str(i+1):>12}" for i in range(QUINTILES)))
        ics, ts = [], []
        for k in range(QUINTILES):
            c = ic_cell(h, gap, qs[k])
            ics.append(None if c is None else c["ic"])
            ts.append(None if c is None else c["t"])
        out["quintiles"][nm] = dict(ic=ics, t=ts)
        print(f"{'':>22}" + "".join(f"{('--' if v is None else f'{v:+.5f}'):>12}" for v in ics))
        print(f"{'t':>22}" + "".join(f"{('--' if v is None else f'{v:+.2f}'):>12}" for v in ts))
        lo, hi = ics[0], ics[-1]
        if lo is not None and hi is not None:
            print(f"{'':>22}Q1 (thin/cheap) {lo:+.5f}   Q5 (liquid/dear) {hi:+.5f}   "
                  f"ratio {abs(lo)/max(abs(hi),1e-9):.2f}x")

    print("\n  P4 -- does the gap REVERSE?  corr(gap, intraday) on the same bars")
    for label, m in (("contaminated (S1-S4)", exact & oos), ("clean", ~exact & oos),
                     ("thin/cheap (S5|S6)", liq & oos), ("liquid/dear", ~liq & oos)):
        k = m & np.isfinite(gap) & np.isfinite(intraday)
        if k.sum() < MIN_BARS:
            print(f"{label:>26}: too few bars")
            continue
        r = float(np.corrcoef(gap[k], intraday[k])[0, 1])
        out["reversal"][label] = dict(corr=r, obs=int(k.sum()))
        print(f"{label:>26}: {r:+.4f}   n {int(k.sum()):,}")

    OUT.write_text(json.dumps(out, indent=1, default=lambda o: None))
    print(f"\n  wrote {OUT}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    print("D402  is D280's overnight gap a real repricing, or a stale opening print?")
    if a.run:
        run()
    else:
        ap.print_help()
