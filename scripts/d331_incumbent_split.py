"""D331 addendum 2 -- inside the incumbent's UNFILTERED ledger (C0, N=2/target,
k=5, invariant), split every trade by whether its name was inside an F0 deal
window at entry. What did the deal-window trades earn, how long were they
held, and what did they cost? A measurement; no book is re-run filtered."""
import sys, json, time, importlib.util
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


D31 = _load("d331", "run_d331_deal_filter.py")
PA, V9 = D31.PA, D31.V9
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X
Q = V6.Q
t0 = time.time()
D.build_cache(verbose=False)
A = D.load_cache(mmap=True)
r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
g = M.P1.build_grids(panel, cleaned)
HALF_PB = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
CLOSE = np.ascontiguousarray(panel.closes.T)
z = np.load(R.BC.CACHE, allow_pickle=False)
base = z["warm"] & panel.live
n, T = panel.live.shape
last_live = PA.last_live_bar(finT)
first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
dj = json.loads(D31.DEALS.read_text())
fb, _, _ = D31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                           lambda f: f["form"] in D31.F0_FORMS)
excl = D31.exclusion_mask(fb, n, T, last_live)
prim, pair = Q.COMPOSITES["C0_incumbent"]
rk = Q.rank_composite({k: z[k] for k in ("hist_L", "macd_hist", "rsi")}, base, prim, pair, n, T)
W.BASE_HOLD = 5
res = W.simulate(A, Y.gate_from(rk, finT), 2, True, slots=False)
print(f"loaded; C0 invariant k=5: {len(res['trades'])} trades ({time.time() - t0:.0f}s)")

for side, lbl in ((0, "LONG"), (1, "SHORT")):
    tr = [t for t in res["trades"] if t[4] == side]
    inwin = np.array([excl[t[0], max(t[1] - 1, 0)] for t in tr])
    pnl = np.array([t[3] for t in tr]) * 1e4
    age = np.array([t[2] for t in tr]); px = np.array([CLOSE[t[1], t[0]] for t in tr])
    hv = np.array([HALF_PB[t[1], t[0]] for t in tr])
    # bars since the most recent qualifying filing, for the in-window trades
    lead = []
    for t, w in zip(tr, inwin):
        if w:
            bs = fb.get(t[0], np.array([], int)); bs = bs[bs <= t[1]]
            lead.append(t[1] - bs.max() if bs.size else np.nan)
    tot = pnl.sum()
    print(f"\n{lbl} leg: {len(tr)} trades, {inwin.sum()} in an F0 deal window at entry ({100 * inwin.mean():.1f}%)")
    print("  %-14s %6s %9s %9s %8s %8s %8s %9s" % ("group", "n", "pnl/trd", "median", "hold", "price", "half", "share P&L"))
    for nm, m in (("in deal window", inwin), ("other", ~inwin)):
        if m.sum() == 0:
            continue
        print("  %-14s %6d %+9.1f %+9.1f %8.1f %8.1f %8.1f %8.0f%%"
              % (nm, m.sum(), pnl[m].mean(), np.median(pnl[m]), age[m].mean(), np.nanmedian(px[m]),
                 np.nanmedian(hv[m]), 100 * pnl[m].sum() / tot if tot else np.nan))
    if lead:
        print(f"  in-window trades enter a median {np.nanmedian(lead):.0f} bars after the filing")
        p = pnl[inwin]; s = np.sort(p); c1 = max(1, len(s) // 100)
        print(f"  in-window P&L: win {100 * (p > 0).mean():.0f}%  top-1% share of their P&L "
              f"{100 * s[-c1:].sum() / p.sum() if p.sum() else np.nan:.0f}%  trimmed-both {s[c1:-c1].mean():+.1f}")
print(f"\ndone ({time.time() - t0:.0f}s)")
