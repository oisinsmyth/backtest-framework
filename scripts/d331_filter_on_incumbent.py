"""D331 addendum -- the declared deal filter (F0, target-specific forms) applied to
the cells D331 did not run: the incumbent C0 at its operating point, hist_L
symmetric, and retrace_leg. A measurement, no predictions; same filter, same
window, same conventions as run_d331_deal_filter.py."""
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
Q, G22 = V6.Q, V6.G22
t0 = time.time()
D.build_cache(verbose=False)
A = D.load_cache(mmap=True)
r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
g = M.P1.build_grids(panel, cleaned)
HALF_PB = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
CLOSE = np.ascontiguousarray(panel.closes.T)
VOL = np.full(CLOSE.shape, np.nan)
sym = {s: i for i, s in enumerate(panel.symbols)}; pos = {d: i for i, d in enumerate(panel.dates)}
for s, bars in cleaned.items():
    i = sym.get(s)
    if i is None:
        continue
    for st in bars:
        t = pos.get(st.timestamp[:10])
        if t is not None:
            VOL[t, i] = st.bar.volume
DV = X.roll_mean_T(CLOSE * VOL)
z = np.load(R.BC.CACHE, allow_pickle=False)
base = z["warm"] & panel.live
n, T = panel.live.shape
cs = z["cs_spread"]; HALF_PUB = np.full((T, n), np.nan); HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
last_live = PA.last_live_bar(finT)
first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
dj = json.loads(D31.DEALS.read_text())
fb, drops, nok = D31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                 lambda f: f["form"] in D31.F0_FORMS)
excl = D31.exclusion_mask(fb, n, T, last_live)
print(f"loaded; F0 excludes {100 * (excl & finT.T).sum() / finT.sum():.2f}% of live name-bars ({time.time() - t0:.0f}s)")

zf = {k: np.where(excl, np.nan, z[k]) for k in ("hist_L", "macd_hist", "rsi", "retrace_leg")}
zd = {k: z[k] for k in ("hist_L", "macd_hist", "rsi", "retrace_leg")}
prim, pair = Q.COMPOSITES["C0_incumbent"]
RK = {"C0": (Q.rank_composite(zd, base, prim, pair, n, T), 5),
      "C0_F0": (Q.rank_composite(zf, base, prim, pair, n, T), 5),
      "hist_L": (Y.rank_single(zd, base, "hist_L", n, T), 20),
      "hist_L_F0": (Y.rank_single(zf, base, "hist_L", n, T), 20),
      "retrace_leg": (Y.rank_single(zd, base, "retrace_leg", n, T), 20),
      "retrace_leg_F0": (Y.rank_single(zf, base, "retrace_leg", n, T), 20)}


def run_cell(rankT, k, H):
    W.BASE_HOLD = k
    gate = Y.gate_from(rankT, finT)
    res_v = W.simulate(A, gate, 2, True, slots=True)
    c = G22.costed(res_v, (H, CLOSE, DV, finT))
    g1 = G22.group1(res_v, c, G22.contributions(res_v, r1T), r1T)
    res_i = W.simulate(A, gate, 2, True, slots=False)
    legs = V9.per_leg(res_i, H, CLOSE, r1T, mkt)
    inv = V9.invariant_legcost(res_i, legs)
    removed = float(np.mean([excl[t[0], max(t[1] - 1, 0)] for t in res_i["trades"]]))
    return dict(net_bp_bar=g1["net_bp_bar"], sharpe_net=g1["sharpe_net"], held_half=c["held_half_spread"],
                net_per_trade=inv["net_per_trade"], legL=legs[0]["net"], legS=legs[1]["net"],
                trades=inv["trades"], removed_at_entry=removed)


out = {}
print("\n%-16s %3s | %8s %8s %7s | %8s %8s %8s | %6s" % ("cell", "k", "bp/bar", "Sharpe", "half", "net/trd", "L leg", "S leg", "excl%"))
for cv in ("PB", "PUB"):
    print(f"  --- {cv} ---")
    for nm, (rk, k) in RK.items():
        r = run_cell(rk, k, HALF[cv]); out[f"{nm}/{cv}"] = r
        print("%-16s %3d | %+8.2f %+8.3f %7.1f | %+8.2f %+8.1f %+8.1f | %5.1f%%"
              % (nm, k, r["net_bp_bar"], r["sharpe_net"], r["held_half"], r["net_per_trade"],
                 r["legL"], r["legS"], 100 * r["removed_at_entry"]))
(REPO / "data" / "d331_filter_on_incumbent.json").write_text(json.dumps(out, indent=1, default=float))
print(f"\nwrote data/d331_filter_on_incumbent.json ({time.time() - t0:.0f}s)")
