"""D331 addendum 3 -- the single trade that is 15% of the incumbent's P&L.
Name it, date it, show the price path and the filings around it, and say
whether the fixture's OHLC is consistent with a real move or a data artefact."""
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
r1T, finT = np.asarray(A["r1T"]), np.asarray(A["finT"])
panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
g = M.P1.build_grids(panel, cleaned)
z = np.load(R.BC.CACHE, allow_pickle=False)
base = z["warm"] & panel.live
n, T = panel.live.shape
dj = json.loads(D31.DEALS.read_text())
ev = json.loads(Path(M.B.EVENTS).read_text())
prim, pair = Q.COMPOSITES["C0_incumbent"]
rk = Q.rank_composite({k: z[k] for k in ("hist_L", "macd_hist", "rsi")}, base, prim, pair, n, T)
W.BASE_HOLD = 5
res = W.simulate(A, Y.gate_from(rk, finT), 2, True, slots=False)
tr = sorted(res["trades"], key=lambda t: -t[3])
tot = sum(t[3] for t in res["trades"]) * 1e4
print(f"C0 invariant k=5: {len(res['trades'])} trades, total P&L {tot:+.0f} bp ({time.time() - t0:.0f}s)\n")
print("TOP 10 TRADES by P&L (both legs), with the largest one-day |r1| in the hold and any dividend on file that day")
for row, e0, age, pnl, side in tr[:10]:
    s = panel.symbols[row]
    seg = r1T[e0:e0 + age, row]
    j = int(np.nanargmax(np.abs(seg))); tj = e0 + j
    dv = [d for d in ev["dividends"].get(s, []) if d[0][:10] == panel.dates[tj]]
    pc = g["close"][row, tj - 1] if tj > 0 else np.nan
    print(f"  {s:6s} {'LONG ' if side == 0 else 'SHORT'} entry {panel.dates[e0]} hold {age}  P&L {pnl * 1e4:+8.0f} bp "
          f"= {100 * pnl * 1e4 / tot:4.1f}%  | biggest day {panel.dates[tj]} r1 {100 * seg[j]:+7.1f}%  "
          f"close {pc:.2f}->{g['close'][row, tj]:.2f} ({100 * (g['close'][row, tj] / pc - 1):+.1f}%)  dividend {dv[0][1] if dv else '-'}")
cum = np.cumsum([t[3] for t in tr]) * 1e4
print(f"\n  top 1 / 5 / 10 trades = {100 * cum[0] / tot:.1f}% / {100 * cum[4] / tot:.1f}% / {100 * cum[9] / tot:.1f}% of the book's P&L")
row, e0, age, pnl, side = tr[0]
s = panel.symbols[row]
print(f"\nTHE TOP TRADE: {s}, {'long' if side == 0 else 'short'}, entered {panel.dates[e0]}")
lo, hi = max(e0 - 8, 0), min(e0 + age + 3, T)
print("  %-12s %10s %10s %10s %10s %12s %8s" % ("date", "open", "high", "low", "close", "volume", "r1 %"))
for t in range(lo, hi):
    vol = np.nan
    for st in cleaned.get(s, []):
        if st.timestamp[:10] == panel.dates[t]:
            vol = st.bar.volume; break
    mark = " <- entry" if t == e0 else (" <- exit" if t == e0 + age else "")
    print("  %-12s %10.3f %10.3f %10.3f %10.3f %12.0f %+8.1f%s"
          % (panel.dates[t], g["open"][row, t], g["high"][row, t], g["low"][row, t], g["close"][row, t],
             vol, 100 * r1T[t, row] if np.isfinite(r1T[t, row]) else np.nan, mark))
print(f"\n  splits on file for {s}: {ev['splits'].get(s, [])}")
print(f"  dividends around entry: {[d for d in ev['dividends'].get(s, []) if abs((np.datetime64(d[0][:10]) - np.datetime64(panel.dates[e0])).astype(int)) < 40]}")
fl = [f for f in dj["deals"].get(s, []) if abs((np.datetime64(f['date']) - np.datetime64(panel.dates[e0])).astype(int)) < 400]
print(f"  deal filings within 400 days: {len(fl)}")
for f in sorted(fl, key=lambda f: f["date"])[:12]:
    print(f"    {f['date']}  {f['form']:8s} {f.get('items', '')} {f.get('matched_queries', '')}  {f['url']}")
print(f"  resolution: {dj['resolution'].get(s, {}).get('entity')}  ({dj['resolution'].get(s, {}).get('confidence')})")
print(f"  first/last live bar: {panel.dates[int(np.flatnonzero(finT[:, row])[0])]} .. {panel.dates[int(np.flatnonzero(finT[:, row])[-1])]}")
print(f"\ndone ({time.time() - t0:.0f}s)")
