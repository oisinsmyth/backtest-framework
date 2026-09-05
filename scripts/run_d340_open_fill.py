"""D340 -- execution lag: a next-open fill for the D300 family.

    uv run python scripts/run_d340_open_fill.py --selftest
    uv run python scripts/run_d340_open_fill.py [--draws 200]

PRE-REGISTERED in docs/decisions/D340-execution-lag-a-next-open-fill.md, committed
before the simulator flag, d340_fill.py and this runner existed (R8).

TWO CELLS, TWO FILLS. D338's retrace_leg cell (symmetric, depth 2, k=20, D303
target, F0) and the incumbent C0 (N=2/target, k=5, unfiltered), each under
`fill="close"` (the family's convention: the entry bar earns close[t-1]->close[t],
the very close the signal was computed at) and `fill="open"` (the entry bar earns
open[t]->close[t], price only, against the open-to-close market). Both lenses,
PB and PUB, GC+HTB borrow. The implementation-lag premium per leg is
mean(sgn * (r1T - ocT)[e0, row]) over the close-fill ledger's entries. The null
is the family's rank rotation on the OPEN-fill retrace_leg cell, 200 draws,
seeded [W.SEED, 340], teeth on the GROSS null.

ASSERTIONS -- properties of code (pre-registration section 5)
  [ID] (a) D303's no-exit control bit-identical at W.BASE_HOLD = D.BASE_HOLD
       (b) the retrace_leg close-fill cell reproduces data/d338 to 1e-9
       (c) simulate(A2) == simulate(A) bitwise on the close fill, both lenses
       (d) the open fill differs on > 0 bars
  [V]  fill="x" -> ValueError; fill="open" on the plain cache -> KeyError; a
       shape mismatch -> ValueError
  [E1] use_target=False: identical (row, e0, age, side), ent, cnt0, cnt1 across
       fills; P&L differs by exactly sgn*((ocT-r1T)[e0,row] - (mkt_oc-mkt)[e0])
  [E2] with the target: t* = first bar the exit-event sets differ; every trade
       closed before t* identical; ent first differs at >= t*
  [G]  the synthetic gap fixture (d340_fill.synthetic_gap_case) on THIS W
  [F]  fallback < 1% of priced cells; its share of entries and of P&L printed
  [P]  every trade in every ledger recomputed to 1e-12, both fills; the close-fill
       self-check with (r1T, mkt); the open-fill ledger is NOT reproduced by the
       close arrays
  [2]  contributions_fill - d322.contributions == sgn*w*(ocT-r1T)[e0,row];
       gross reconstructs to < 1 bp up to the open tail
  [L2] ocT on 3,000 sampled cells rebuilt from the raw Bar objects; r1T != ocT on
       sampled ex-date cells
  [6]  [ID](b) raises on a book handed +5 bp on 200 masked bars
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


V38 = _load("d338", "run_d338_retrace_leg_candidate.py")      # main is guarded
V35, V31, PA, V9 = V38.V35, V38.V31, V38.PA, V38.V9
V6, Y, W, D, M, SP, R, X = V38.V6, V38.Y, V38.W, V38.D, V38.M, V38.SP, V38.R, V38.X
G22, BR = V38.G22, V38.BR
Q = V6.Q
FL = _load("d340f", "d340_fill.py")

SIG, K_RL, K_C0, DEPTH = "retrace_leg", 20, 5, 2
N_BASE = W.N_BASE
NULL_SEED = [W.SEED, 340]
FILLS = ("close", "open")
CONVS = ("PB", "PUB")
ANN = 252.0
N_L2, L2_SEED = 3000, 340
OUT = REPO / "data" / "d340_open_fill.json"
D338_JSON = REPO / "data" / "d338_retrace_leg_candidate.json"
D333_JSON = REPO / "data" / "d333_dividend_bound.json"
VSA_ENTRY = ("VSA", "2025-01-31")


def bookkey(res):
    return np.nan_to_num(res["book"], nan=-9e9)


def keys(trades):
    return [(t[0], t[1], t[2], t[4]) for t in trades]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    print("D340  execution lag -- a next-open fill for the D300 family")

    # ---- data (D338's preparation) ------------------------------------------------
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF_PB = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
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
    cs = z["cs_spread"]
    HALF_PUB = np.full((T, n), np.nan)
    HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    G4 = {cv: (HALF[cv], CLOSE, DV, finT) for cv in CONVS}
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    years = np.array([int(d[:4]) for d in panel.dates])
    meta = json.loads(G22.META.read_text())["symbols"]
    dead = np.array([bool(meta.get(s, {}).get("delistingDate")) for s in panel.symbols])
    ev = json.loads(Path(M.B.EVENTS).read_text())
    d338 = json.loads(D338_JSON.read_text())
    d333 = json.loads(D333_JSON.read_text())["cells"]
    print(f"  panel {finT.shape}, {int(dead.sum())} delisted names ({time.time() - t0:.0f}s)")

    # the F0 mask (D338 [F])
    dj = json.loads(V31.DEALS.read_text())
    fbars, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                         lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fbars, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == V35.EXPECT_APPLIED and abs(pct - V35.EXPECT_PCT) < 0.02, f"[F0] {n_ok} / {pct:.3f}%"

    # the open-fill arrays
    A2, fb, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]
    print(f"  ocT / mkt_oc built: {FBREP['cells_with_open']:,} cells with an open, fallback "
          f"{FBREP['fallback_cells']:,} of {FBREP['priced_cells']:,} priced ({100 * FBREP['fallback_frac']:.4f}%), "
          f"mkt_oc on {FBREP['mkt_oc_bars']:,} bars ({time.time() - t0:.0f}s)")

    # ---- the two rank arrays and gates ------------------------------------------------
    score_f0 = np.where(excl, np.nan, z[SIG])
    rank_rl = Y.rank_single({SIG: score_f0}, base, SIG, n, T)
    prim, pair = Q.COMPOSITES["C0_incumbent"]
    rank_c0 = Q.rank_composite({k: z[k] for k in ("hist_L", "macd_hist", "rsi")}, base, prim, pair, n, T)
    SPEC = {"RL": dict(rankT=rank_rl, k=K_RL, label=f"{SIG} F0, depth {DEPTH}, k={K_RL}, D303 target"),
            "C0": dict(rankT=rank_c0, k=K_C0, label=f"C0 incumbent, depth {DEPTH}, k={K_C0}, D303 target, unfiltered")}
    GATE = {nm: Y.gate_from(sp["rankT"], finT) for nm, sp in SPEC.items()}

    def run_cell(nm, fill):
        W.BASE_HOLD = SPEC[nm]["k"]
        gate = GATE[nm]
        res_v = W.simulate(A2, gate, DEPTH, True, slots=True, fill=fill)
        res_i = W.simulate(A2, gate, DEPTH, True, slots=False, fill=fill)
        contrib = (G22.contributions(res_v, r1T) if fill == "close"
                   else FL.contributions_fill(res_v, r1T, ocT))
        C = {cv: G22.costed(res_v, G4[cv]) for cv in CONVS}
        G1 = {cv: G22.group1(res_v, C[cv], contrib, r1T) for cv in CONVS}
        G2 = G22.group2(res_v)
        G3 = {cv: G22.group3(res_v, contrib, C[cv], years, dead, CLOSE, HALF[cv]) for cv in CONVS}
        LEGS = {cv: V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt) for cv in CONVS}
        INV = {cv: V9.invariant_legcost(res_i, LEGS[cv]) for cv in CONVS}
        BV, _ = V38.borrow_block(res_v, C, INV, excl, CLOSE, T)
        BI, _ = V38.borrow_block(res_i, C, INV, excl, CLOSE, T)
        return dict(res_v=res_v, res_i=res_i, contrib=contrib, C=C, G1=G1, G2=G2, G3=G3,
                    LEGS=LEGS, INV=INV, BORROW_V=BV, BORROW_I=BI)

    CELLS = {nm: {fill: run_cell(nm, fill) for fill in FILLS} for nm in SPEC}
    print(f"  {len(SPEC) * len(FILLS)} cells simulated, both lenses ({time.time() - t0:.0f}s)")

    # ---- assertions -----------------------------------------------------------------------
    print("\nASSERTIONS")
    saved = W.BASE_HOLD

    # [ID](a) D303's no-exit control at the import default
    W.BASE_HOLD = D.BASE_HOLD
    try:
        G0 = W.build_gate(A, verbose=False)
        b19 = W.simulate(A, G0, 19, False)
        ref = D.simulate(A, "none", "flat", None)
        assert np.array_equal(bookkey(b19), np.nan_to_num(ref["book"], nan=-9e9)), "[ID](a) N=19/none != D303"
    finally:
        W.BASE_HOLD = saved
    print(f"    [ID](a) N=19/none at W.BASE_HOLD={D.BASE_HOLD} is bit-identical to D303's no-exit control, "
          f"{int(b19['ent'].sum()):,} entries")

    # [ID](b) the D338 cell on the close fill
    rl_c = CELLS["RL"]["close"]
    worst_b = 0.0
    for cv in CONVS:
        worst_b = max(worst_b,
                      abs(rl_c["G1"][cv]["gross_bp_bar"] - d338["group1"][cv]["gross_bp_bar"]),
                      abs(rl_c["G1"][cv]["net_bp_bar"] - d338["group1"][cv]["net_bp_bar"]),
                      abs(rl_c["G1"][cv]["sharpe_net"] - d338["group1"][cv]["sharpe_net"]),
                      abs(rl_c["INV"][cv]["net_per_trade"] - d338["invariant"][cv]["net_per_trade"]),
                      abs(rl_c["LEGS"][cv][0]["net"] - d338["legs"][cv]["0"]["net"]),
                      abs(rl_c["LEGS"][cv][1]["net"] - d338["legs"][cv]["1"]["net"]))
    assert worst_b < 1e-9, f"[ID](b) {worst_b:.2e}"
    print(f"    [ID](b) the retrace_leg close-fill cell reproduces data/d338 to {worst_b:.1e} -- gross, net, "
          f"net Sharpe, invariant per trade, both legs, PB and PUB")
    # C0 against D333's new-panel cell (reported; the pre-registration's identity is [ID](b))
    c0_c = CELLS["C0"]["close"]
    worst_c0 = 0.0
    for cv in CONVS:
        ref3 = d333[f"C0 N=2/{cv}/new"]
        worst_c0 = max(worst_c0,
                       abs(c0_c["G1"][cv]["gross_bp_bar"] - ref3["variant"]["gross_bp_bar"]),
                       abs(c0_c["G1"][cv]["net_bp_bar"] - ref3["variant"]["net_bp_bar"]),
                       abs(c0_c["G1"][cv]["sharpe_net"] - ref3["variant"]["sharpe_net"]),
                       abs(c0_c["INV"][cv]["net_per_trade"] - ref3["invariant"]["net_per_trade"]),
                       abs(c0_c["LEGS"][cv][0]["net"] - ref3["legs"]["0"]["net"]),
                       abs(c0_c["LEGS"][cv][1]["net"] - ref3["legs"]["1"]["net"]))
    c0_identity = bool(worst_c0 < 1e-9)
    print(f"    [ID](b') the C0 close-fill cell {'reproduces' if c0_identity else 'DOES NOT reproduce'} "
          f"D333's 'C0 N=2/*/new' cells: worst {worst_c0:.1e}"
          + ("" if c0_identity else " -- C0 has no published identity on the current cache; its numbers here stand alone"))

    # [ID](c) the extra keys are inert on the close fill, both lenses
    W.BASE_HOLD = K_RL
    for slots, key in ((True, "res_v"), (False, "res_i")):
        rA = W.simulate(A, GATE["RL"], DEPTH, True, slots=slots)
        assert np.array_equal(bookkey(rA), bookkey(rl_c[key])), f"[ID](c) book differs slots={slots}"
        assert rA["trades"] == rl_c[key]["trades"], f"[ID](c) ledger differs slots={slots}"
        assert np.array_equal(rA["ent"], rl_c[key]["ent"])
    print(f"    [ID](c) simulate(A2) == simulate(A) bitwise on the close fill: book, ent and the full ledger, both lenses")

    # [ID](d) the open fill moves the book
    rl_o = CELLS["RL"]["open"]
    nd = int((bookkey(rl_o["res_v"]) != bookkey(rl_c["res_v"])).sum())
    assert nd > 0, "[ID](d) the open fill is inert"
    print(f"    [ID](d) the open fill differs from the close fill on {nd:,} of {T:,} bars")

    # [V] three raises
    raised = []
    try:
        W.simulate(A2, GATE["RL"], DEPTH, True, fill="x")
    except ValueError:
        raised.append("ValueError fill='x'")
    try:
        W.simulate(A, GATE["RL"], DEPTH, True, fill="open")
    except KeyError:
        raised.append("KeyError fill='open' on the plain cache")
    try:
        W.simulate(dict(A2, ocT=np.ascontiguousarray(ocT[:, :-1])), GATE["RL"], DEPTH, True, fill="open")
    except ValueError:
        raised.append("ValueError ocT shape")
    try:
        W.simulate(dict(A2, mkt_oc=mkt_oc[:-1]), GATE["RL"], DEPTH, True, fill="open")
    except ValueError:
        raised.append("ValueError mkt_oc shape")
    assert len(raised) == 4, f"[V] only {raised}"
    print(f"    [V] raises: " + "; ".join(raised))

    # [E1] no target: identical decisions, P&L differs by the entry-bar splice only
    e1c = W.simulate(A2, GATE["RL"], DEPTH, False, slots=True)
    e1o = W.simulate(A2, GATE["RL"], DEPTH, False, slots=True, fill="open")
    assert keys(e1c["trades"]) == keys(e1o["trades"]), "[E1] ledger keys differ"
    assert np.array_equal(e1c["ent"], e1o["ent"]) and np.array_equal(e1c["cnt0"], e1o["cnt0"]) \
        and np.array_equal(e1c["cnt1"], e1o["cnt1"]), "[E1] ent / cnt differ"
    pnl_e1c, pnl_e1o = np.array([t[3] for t in e1c["trades"]]), np.array([t[3] for t in e1o["trades"]])
    sg = np.array([1.0 if t[4] == 0 else -1.0 for t in e1c["trades"]])
    rows_e = np.array([t[0] for t in e1c["trades"]])
    e0s = np.array([t[1] for t in e1c["trades"]])
    splice = sg * ((ocT[e0s, rows_e] - r1T[e0s, rows_e]) - (mkt_oc[e0s] - mkt[e0s]))
    d_pnl = pnl_e1o - pnl_e1c
    worst_e1 = float(np.abs(d_pnl - splice).max())
    assert worst_e1 < 1e-12, f"[E1] {worst_e1:.2e}"
    assert (d_pnl[splice == 0.0] == 0.0).all(), "[E1] P&L moved on a trade whose entry cell did not"
    n_cell_diff = int((ocT[e0s, rows_e] != r1T[e0s, rows_e]).sum())
    n_pnl_diff = int((d_pnl != 0.0).sum())
    print(f"    [E1] use_target=False: identical (row, e0, age, side), ent, cnt0, cnt1 on {len(pnl_e1c):,} trades across "
          f"fills; P&L differs by exactly\n         sgn*((ocT-r1T)[e0,row] - (mkt_oc-mkt)[e0]) to {worst_e1:.1e}; "
          f"ocT != r1T at {n_cell_diff:,} entry cells, P&L differs on {n_pnl_diff:,} trades")

    # [E2] with the target: the first bar the exits diverge
    def exit_events(res):
        ev_ = {}
        for row, e0, age, _p, side in res["trades"]:
            ev_.setdefault(e0 + age, set()).add((row, side))
        return ev_
    xc, xo = exit_events(rl_c["res_v"]), exit_events(rl_o["res_v"])
    t_star = T
    for t in range(T + 1):
        if xc.get(t, set()) != xo.get(t, set()):
            t_star = t
            break
    before_c = sorted(k for k in keys(rl_c["res_v"]["trades"]) if k[1] + k[2] < t_star)
    before_o = sorted(k for k in keys(rl_o["res_v"]["trades"]) if k[1] + k[2] < t_star)
    assert before_c == before_o, "[E2] a trade closed before t* differs"
    ent_diff = np.flatnonzero(rl_c["res_v"]["ent"] != rl_o["res_v"]["ent"])
    first_ent = int(ent_diff[0]) if ent_diff.size else T
    assert first_ent >= t_star, f"[E2] ent differs at {first_ent} < t* {t_star}"
    kc, ko = set(keys(rl_c["res_v"]["trades"])), set(keys(rl_o["res_v"]["trades"]))
    share_diff = 1.0 - len(kc & ko) / float(len(kc))
    first_exit = min(min(xc), min(xo))
    E2 = dict(t_star=int(t_star), t_star_date=panel.dates[min(t_star, T - 1)], trades_before_t_star=len(before_c),
              first_exit_bar=int(first_exit), first_ent_diff=first_ent, trades_close=len(kc), trades_open=len(ko),
              common=len(kc & ko), share_close_trades_not_recurring=float(share_diff))
    print(f"    [E2] target: exit sets first differ at bar t*={t_star} ({E2['t_star_date']}; the first exit of any kind is "
          f"at bar {first_exit}); all {len(before_c)} trades\n         closed before t* identical; ent first differs at bar "
          f"{first_ent} >= t*; {len(kc & ko):,} of {len(kc):,} close-fill trades recur under the open fill "
          f"({100 * share_diff:.1f}% do not; the open ledger has {len(ko):,})")

    # [G] synthetic gap on THIS W
    Gs = FL.synthetic_gap_case(W_=W, Y_=Y)
    FL.check_gap_case(Gs)
    assert W.BASE_HOLD == K_RL, "[G] BASE_HOLD not restored"
    print(f"    [G] synthetic +50%/-50% gap, market +1%: close fill books long {Gs['close'][0]:+.2f} / short "
          f"{Gs['close'][1]:+.2f}; open fill books {Gs['open'][0]:+.1f} / {Gs['open'][1]:+.1f} -- mkt_oc pinned")

    # [F] fallback
    assert FBREP["fallback_frac"] < 0.01, f"[F] {FBREP['fallback_frac']:.4f}"
    F = {}
    for nm in SPEC:
        tr = CELLS[nm]["open"]["res_v"]["trades"]
        on_fb = np.array([bool(fb[t[1], t[0]]) for t in tr]) if tr else np.zeros(0, bool)
        pn = np.array([t[3] for t in tr])
        F[nm] = dict(entry_share=float(on_fb.mean()) if on_fb.size else 0.0,
                     pnl_share=float(pn[on_fb].sum() / pn.sum()) if on_fb.any() else 0.0,
                     entries_on_fallback=int(on_fb.sum()))
    print(f"    [F] fallback covers {FBREP['fallback_cells']:,} of {FBREP['priced_cells']:,} priced cells "
          f"({100 * FBREP['fallback_frac']:.4f}%); share of entries RL {100 * F['RL']['entry_share']:.3f}% "
          f"C0 {100 * F['C0']['entry_share']:.3f}%; share of ledger P&L RL {100 * F['RL']['pnl_share']:.3f}% "
          f"C0 {100 * F['C0']['pnl_share']:.3f}%")

    # [P] every ledger recomputed
    worst_p = 0.0
    n_led = 0
    for nm in SPEC:
        for fill in FILLS:
            for key in ("res_v", "res_i"):
                tr = CELLS[nm][fill][key]["trades"]
                pn = np.array([t[3] for t in tr])
                if fill == "close":
                    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, r1T, mkt)
                else:
                    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
                worst_p = max(worst_p, float(np.abs(rec - pn).max()))
                n_led += 1
    assert worst_p < 1e-12, f"[P] {worst_p:.2e}"
    tr_o = rl_o["res_v"]["trades"]
    wrong = FL.pnl_recomputed_fill(tr_o, r1T, mkt, r1T, mkt)
    miss = float(np.abs(wrong - np.array([t[3] for t in tr_o])).max())
    assert miss > 1e-6, "[P] the close arrays reproduce the open-fill ledger -- the check cannot fail"
    print(f"    [P] all {n_led} ledgers (2 cells x 2 fills x 2 lenses) recomputed from (row, e0, age, side) to "
          f"{worst_p:.1e}; the close arrays miss the open-fill ledger by up to {miss:.3f}")

    # [2] contributions reconcile
    cf = rl_o["contrib"]
    cc = G22.contributions(rl_o["res_v"], r1T)
    res_o = rl_o["res_v"]
    ncnt = {0: np.asarray(res_o["cnt0"], float), 1: np.asarray(res_o["cnt1"], float)}
    mm = res_o["mask"].astype(float)
    ww = {s: np.where(ncnt[s] > 0, 1.0 / np.maximum(ncnt[s], 1), 0.0) * mm for s in (0, 1)}
    exp2 = np.array([(1.0 if s == 0 else -1.0) * ww[s][e0] * (ocT[e0, row] - r1T[e0, row])
                     for row, e0, _a, _p, s in tr_o])
    worst_2 = float(np.abs((cf - cc) - exp2).max())
    assert worst_2 < 1e-15, f"[2] {worst_2:.2e}"
    attributed = float(cf.sum()) / rl_o["C"]["PUB"]["bars"] * 1e4
    resid = rl_o["C"]["PUB"]["gross_bp"] - attributed
    n_open = int(res_o["ent"].sum()) - len(tr_o)
    gap_bars, first, TT = G22.unattributed(res_o)
    assert 0 <= n_open <= 2 * DEPTH and first >= TT - K_RL and abs(resid) < 1.0, f"[2] {resid:.4f} / {n_open} / {first}"
    print(f"    [2] contributions_fill - d322.contributions == sgn*w*(ocT-r1T)[e0,row] to {worst_2:.1e} on "
          f"{len(tr_o):,} trades; open-fill gross reconstructs to {resid:+.4f} bp\n         ({n_open} positions open at T, "
          f"{gap_bars:.0f} position-bars, none before bar {first} of {TT})")

    # [L2] ocT rebuilt from the raw Bar objects; r1T != ocT on ex-date cells
    rng = np.random.default_rng(L2_SEED)
    real = finT & ~fb
    cand = np.flatnonzero(real.ravel())
    pick = rng.choice(cand, size=N_L2, replace=False)
    ts, is_ = np.unravel_index(pick, real.shape)
    bar_of = {}
    worst_l2, n_exact = 0.0, 0
    for t, i in zip(ts, is_):
        s = panel.symbols[i]
        if s not in bar_of:
            bar_of[s] = {st.timestamp[:10]: st.bar for st in cleaned[s]}
        b = bar_of[s][panel.dates[t]]
        want = b.close / b.open - 1.0
        got = float(ocT[t, i])
        n_exact += int(got == want)
        worst_l2 = max(worst_l2, abs(got - want))
    assert n_exact == N_L2, f"[L2] only {n_exact} of {N_L2} exact, worst {worst_l2:.2e}"
    ex_cells = []
    for s, lst in ev["dividends"].items():
        i = sym.get(s)
        if i is None:
            continue
        for d_ in lst:
            t = pos.get(d_[0][:10])
            if t is not None and real[t, i] and float(d_[1]) > 0:
                ex_cells.append((t, i))
    ex_cells = np.array(ex_cells)
    if ex_cells.shape[0] > N_L2:
        ex_cells = ex_cells[rng.choice(ex_cells.shape[0], size=N_L2, replace=False)]
    neq = r1T[ex_cells[:, 0], ex_cells[:, 1]] != ocT[ex_cells[:, 0], ex_cells[:, 1]]
    assert neq.all(), f"[L2] r1T == ocT on {int((~neq).sum())} ex-date cells"
    print(f"    [L2] ocT equals close/open - 1 rebuilt from the raw Bar objects on all {N_L2:,} sampled cells "
          f"({len(bar_of)} names); r1T != ocT on all {ex_cells.shape[0]:,} sampled ex-date cells")

    # [6] [ID](b) raises
    broke = False
    try:
        bk = rl_c["res_v"]["book"].copy()
        bk[np.flatnonzero(rl_c["res_v"]["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(rl_c["res_v"], book=bk), G4["PUB"])
        assert abs(bad["net_bp"] - d338["group1"]["PUB"]["net_bp_bar"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] [ID](b) passed a book handed free money"
    print("    [6] and [ID](b) raises on a book handed +5 bp on 200 masked bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the implementation-lag premium per leg ----------------------------------------
    def premium(trades):
        out = {}
        for side in (0, 1):
            sgn = 1.0 if side == 0 else -1.0
            tr = [t for t in trades if t[4] == side]
            rows_ = np.array([t[0] for t in tr])
            e0_ = np.array([t[1] for t in tr])
            name = sgn * (r1T[e0_, rows_] - ocT[e0_, rows_])
            hedge = sgn * (mkt[e0_] - mkt_oc[e0_])
            out[str(side)] = dict(
                n=int(name.size), name_mean_bp=float(name.mean()) * 1e4, name_median_bp=float(np.median(name)) * 1e4,
                name_t=float(name.mean() / (name.std(ddof=1) / np.sqrt(name.size))),
                share_positive=float((name > 0).mean()), hedge_mean_bp=float(hedge.mean()) * 1e4,
                excess_mean_bp=float((name - hedge).mean()) * 1e4)
        return out
    PREM = {nm: dict(variant=premium(CELLS[nm]["close"]["res_v"]["trades"]),
                     invariant=premium(CELLS[nm]["close"]["res_i"]["trades"])) for nm in SPEC}

    # ---- top five under both fills, VSA's entry-bar credit ---------------------------------
    def top5(res):
        tr = res["trades"]
        pn = np.array([t[3] for t in tr])
        tot = float(pn.sum())
        order = np.argsort(-pn)[:5]
        rows_ = []
        for i in order:
            row, e0, age, p, side = tr[i]
            rows_.append(dict(symbol=panel.symbols[row], side="long" if side == 0 else "short", entry=panel.dates[e0],
                              hold=int(age), pnl_bp=float(p) * 1e4, share=float(p / tot),
                              entry_bar_r1=float(r1T[e0, row]), entry_bar_oc=float(ocT[e0, row])))
        return rows_, float(pn[order].sum() / tot)

    def find_vsa(res):
        for row, e0, age, p, side in res["trades"]:
            if panel.symbols[row] == VSA_ENTRY[0] and panel.dates[e0] == VSA_ENTRY[1] and side == 0:
                return dict(entry=panel.dates[e0], hold=int(age), pnl_bp=float(p) * 1e4,
                            entry_bar_r1=float(r1T[e0, row]), entry_bar_oc=float(ocT[e0, row]),
                            open=float(g["open"][row, e0]), close=float(g["close"][row, e0]),
                            prev_close=float(g["close"][row, e0 - 1]))
        return None
    TOP = {fill: top5(CELLS["RL"][fill]["res_v"]) for fill in FILLS}
    VSA = {fill: find_vsa(CELLS["RL"][fill]["res_v"]) for fill in FILLS}
    # the cell's credit under each convention, read off the arrays -- independent of
    # whether the slot-limited path holds VSA on that bar
    vrow, vbar = sym[VSA_ENTRY[0]], pos[VSA_ENTRY[1]]
    VSA["cell"] = dict(row=int(vrow), bar=int(vbar), r1=float(r1T[vbar, vrow]), oc=float(ocT[vbar, vrow]),
                       prev_close=float(g["close"][vrow, vbar - 1]), open=float(g["open"][vrow, vbar]),
                       close=float(g["close"][vrow, vbar]), long_rank=int(rank_rl[0, vbar, vrow]),
                       long_leg_open_fill=[(panel.symbols[r_], panel.dates[e0], int(ag)) for r_, e0, ag, _p, s_
                                           in rl_o["res_v"]["trades"] if s_ == 0 and e0 <= vbar < e0 + ag])

    # ---- the null on the OPEN-fill retrace_leg cell ------------------------------------------
    ts_ = time.time()
    W.BASE_HOLD = K_RL
    rng = np.random.default_rng(NULL_SEED)
    offs = rng.choice(np.arange(1, N_BASE), size=a.draws, replace=True)
    NG, NSG, NSN = [], [], {cv: [] for cv in CONVS}
    for s_ in offs:
        r = W.simulate(A2, GATE["RL"], DEPTH, True, shift=int(s_), fill="open")
        okm = r["mask"]
        if int(okm.sum()) < 200:
            continue
        b = r["book"][okm]
        NG.append(float(b.mean()) * 1e4)
        NSG.append(float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)))
        for cv in CONVS:
            NSN[cv].append(G22.costed(r, G4[cv])["sharpe_net"])
    NG, NSG = np.array(NG), np.array(NSG)
    NSN = {cv: np.array(NSN[cv]) for cv in CONVS}
    assert NG.size >= min(195, a.draws - 5), f"[N] only {NG.size} valid draws"
    Co = rl_o["C"]
    NULL = dict(construction="rank rotation inside the 25-name gate, simulated under fill='open'", seed=NULL_SEED,
                draws=int(NG.size), gross_bp=G22.dist(NG, Co["PUB"]["gross_bp"]),
                sharpe_gross=G22.dist(NSG, Co["PUB"]["sharpe_gross"]),
                sharpe_net={cv: G22.dist(NSN[cv], Co[cv]["sharpe_net"]) for cv in CONVS})
    teeth = bool(NULL["gross_bp"]["p95"] > 0)
    print(f"\n    [N] {NG.size} of {a.draws} open-fill null draws valid ({time.time() - ts_:.0f}s)")

    # ---- report ---------------------------------------------------------------------------
    f2 = lambda v: "%+.2f" % v
    f3 = lambda v: "%+.3f" % v
    pc_ = lambda v: "%.1f%%" % (100 * v)
    G1SPEC = (("gross bp/bar", "gross_bp_bar", f2), ("cost bp/bar", "cost_bp_bar", lambda v: "%.2f" % v),
              ("NET bp/bar", "net_bp_bar", f2), ("vol bp/bar", "vol_bp_bar", lambda v: "%.1f" % v),
              ("gross Sharpe", "sharpe_gross", f3), ("NET Sharpe", "sharpe_net", f3), ("gross t", "t_gross", f2),
              ("maxDD bp", "maxdd_bp", lambda v: "%.0f" % v), ("exposure (bars / panel)", "exposure_bars", pc_),
              ("names held per bar", "held_per_bar", lambda v: "%.2f" % v),
              ("turnover/bar (names HELD)", "turnover_held", lambda v: "%.4f" % v),
              ("held half-spread bp/side", "held_half_spread", lambda v: "%.2f" % v),
              ("held median price", "held_price", lambda v: "$%.2f" % v),
              ("2c = rt_total / 2", "two_c_bp", lambda v: "%.2f" % v),
              ("mean move per TRADE bp", "trade_mean_bp", f2),
              ("mean move / 2c", "trade_mean_over_2c", lambda v: "%.2fx" % v),
              ("BREAKEVEN half-spread /side", "breakeven_half_spread_bp_side", lambda v: "%.2f" % v),
              ("breakeven / measured", "breakeven_multiple", lambda v: "%.2fx" % v))
    G2SPEC = (("trades", "n", lambda v: "%d" % v), ("mean bp", "mean_bp", lambda v: "%+.1f" % v),
              ("MEDIAN bp", "median_bp", lambda v: "%+.1f" % v),
              ("mean BELOW median?", "mean_below_median", lambda v: "YES" if v else "no"),
              ("win rate", "win_rate", pc_), ("payoff", "payoff", lambda v: "%.2f" % v),
              ("holding run mean", "holding_run_mean", lambda v: "%.2f" % v), ("skew", "skew", f2),
              ("kurtosis (raw)", "kurtosis_raw", lambda v: "%.1f" % v),
              ("mean EX-TOP 1%", "mean_ex_top_bp", lambda v: "%+.1f" % v),
              ("mean EX-BOTTOM 1%", "mean_ex_bottom_bp", lambda v: "%+.1f" % v),
              ("mean TRIMMED both", "mean_trimmed_bp", lambda v: "%+.1f" % v),
              ("top 1% share of P&L", "top1_share", lambda v: "%+.0f%%" % (100 * v)),
              ("bottom 1% share of P&L", "bottom1_share", lambda v: "%+.0f%%" % (100 * v)))
    for nm in SPEC:
        print("\n" + "=" * 96)
        print(f"{nm}: {SPEC[nm]['label']}")
        print("=" * 96)
        print("GROUP 1 -- PERFORMANCE, NET AND GROSS, the same gate under both fills (variant book)")
        print("  %-30s %14s %14s %14s %14s" % ("", "close PB", "close PUB", "OPEN PB", "OPEN PUB"))
        for label, key, fn in G1SPEC:
            print("  %-30s %14s %14s %14s %14s" % (
                label, fn(CELLS[nm]["close"]["G1"]["PB"][key]), fn(CELLS[nm]["close"]["G1"]["PUB"][key]),
                fn(CELLS[nm]["open"]["G1"]["PB"][key]), fn(CELLS[nm]["open"]["G1"]["PUB"][key])))
        print("  %-30s %14s %14s %14s %14s" % ("NET after GC+HTB borrow",
              *[f2(CELLS[nm][fl]["BORROW_V"]["gc_htb"][cv]["net_bp_borrow"]) for fl in FILLS for cv in CONVS]))
        print("  %-30s %14s %14s %14s %14s" % ("invariant NET per trade",
              *[f2(CELLS[nm][fl]["INV"][cv]["net_per_trade"]) for fl in FILLS for cv in CONVS]))
        print("  %-30s %14s %14s %14s %14s" % ("  long leg net / trade",
              *[f2(CELLS[nm][fl]["LEGS"][cv][0]["net"]) for fl in FILLS for cv in CONVS]))
        print("  %-30s %14s %14s %14s %14s" % ("  short leg net / trade",
              *[f2(CELLS[nm][fl]["LEGS"][cv][1]["net"]) for fl in FILLS for cv in CONVS]))
        print("\nGROUP 2 -- TRADE DISTRIBUTION, BOTH TAILS TRIMMED (variant ledger)")
        print("  %-30s %14s %14s" % ("", "close", "OPEN"))
        for label, key, fn in G2SPEC:
            print("  %-30s %14s %14s" % (label, fn(CELLS[nm]["close"]["G2"][key]), fn(CELLS[nm]["open"]["G2"][key])))
        print("\nGROUP 3 -- WHAT THE WINNERS DEPEND ON (PUB)")
        for fl in FILLS:
            g3 = CELLS[nm][fl]["G3"]["PUB"]
            print(f"  {fl:5s}: names {g3['names']}, to half the P&L {g3['names_to_half_pnl']}, top 1/5/10 name share "
                  f"{100 * g3['top1_name_share']:.1f}/{100 * g3['top5_name_share']:.1f}/{100 * g3['top10_name_share']:.1f}%; "
                  f"years net-positive {g3['years_profitable_net']}/{g3['years']} (gross {g3['years_profitable_gross']}); "
                  f"dead {100 * g3['dead']['share_pnl']:.1f}%, price LOW {100 * g3['price_low']['share_pnl']:.1f}% "
                  f"(net/trade {g3['price_low']['net_per_trade_bp']:+.1f})")
        pr = PREM[nm]["variant"]
        print(f"\nIMPLEMENTATION-LAG PREMIUM, mean sgn*(r1T - ocT) at entry over the close-fill ledger (variant):")
        for s in ("0", "1"):
            p_ = pr[s]
            print(f"  {'long ' if s == '0' else 'short'} n={p_['n']:5d}  name {p_['name_mean_bp']:+8.1f} bp (median "
                  f"{p_['name_median_bp']:+.1f}, t {p_['name_t']:+.2f}, {100 * p_['share_positive']:.0f}% positive); "
                  f"hedge {p_['hedge_mean_bp']:+.1f}; excess {p_['excess_mean_bp']:+.1f}")
        pi_ = PREM[nm]["invariant"]
        print(f"  invariant ledger: long {pi_['0']['name_mean_bp']:+.1f} (n={pi_['0']['n']}), short "
              f"{pi_['1']['name_mean_bp']:+.1f} (n={pi_['1']['n']})")

    print("\n" + "=" * 96)
    print("RL TOP FIVE TRADES under each fill (variant ledger), with the entry-bar credit")
    print("=" * 96)
    for fl in FILLS:
        rows_, sh5 = TOP[fl]
        print(f"  {fl.upper()} fill  (top-5 share {100 * sh5:.1f}%)")
        for r_ in rows_:
            cred = r_["entry_bar_r1"] if fl == "close" else r_["entry_bar_oc"]
            print(f"    {r_['symbol']:6s} {r_['side']:5s} entry {r_['entry']} hold {r_['hold']:2d}  P&L {r_['pnl_bp']:+9.0f} bp "
                  f"({100 * r_['share']:5.1f}%)  entry bar earns {100 * cred:+7.1f}%  [r1 {100 * r_['entry_bar_r1']:+.1f}% / "
                  f"oc {100 * r_['entry_bar_oc']:+.1f}%]")
    vc = VSA["cell"]
    print(f"  VSA {VSA_ENTRY[1]} (long rank {vc['long_rank']} in the gate): prev close {vc['prev_close']:.2f}, open {vc['open']:.2f}, "
          f"close {vc['close']:.2f}; the entry bar is credited {100 * vc['r1']:+.1f}% on the close fill and "
          f"{100 * vc['oc']:+.1f}% on the open fill")
    for fl in FILLS:
        v = VSA[fl]
        if v is None:
            print(f"    {fl}-fill ledger: VSA NOT held -- the long leg on that bar was {vc['long_leg_open_fill']} "
                  f"(both slots taken; a path effect, not a marking effect)")
        else:
            print(f"    {fl}-fill ledger: VSA long held {v['hold']} bar(s), P&L {v['pnl_bp']:+.0f} bp")

    print("\n" + "=" * 96)
    print("GROUP 4 -- THE NULL on the OPEN-fill retrace_leg cell: p50 AND p95 (teeth on GROSS)")
    print("=" * 96)
    print("  %-18s %10s %10s %10s %10s %10s" % ("statistic", "score", "null p50", "null p95", "null max", "p"))
    for nm_, d_ in (("gross bp/bar", NULL["gross_bp"]), ("gross Sharpe", NULL["sharpe_gross"]),
                    ("net Sharpe PB", NULL["sharpe_net"]["PB"]), ("net Sharpe PUB", NULL["sharpe_net"]["PUB"])):
        print("  %-18s %10.3f %10.3f %10.3f %10.3f %10.4f" % (nm_, d_["score"], d_["p50"], d_["p95"], d_["max"], d_["p"]))
    print(f"  the gross null has teeth (p95 > 0): {'yes' if teeth else 'NO -- R7 flag'}; "
          f"D338's close-fill null: gross p50 {d338['null']['gross_bp']['p50']:.3f} p95 {d338['null']['gross_bp']['p95']:.3f}")

    # ---- predictions ------------------------------------------------------------------------
    rl_net = {fl: CELLS["RL"][fl]["G1"]["PUB"]["net_bp_bar"] for fl in FILLS}
    c0_net = {fl: CELLS["C0"][fl]["G1"]["PUB"]["net_bp_bar"] for fl in FILLS}
    prem_rl = PREM["RL"]["variant"]
    q = {}
    q["Q1"] = bool(rl_net["close"] - rl_net["open"] > 5.0)
    q["Q2"] = bool(prem_rl["0"]["name_mean_bp"] > 0 and abs(prem_rl["0"]["name_mean_bp"]) > abs(prem_rl["1"]["name_mean_bp"]))
    q["Q3"] = bool(TOP["open"][1] < 0.35)
    q["Q4"] = bool(abs(c0_net["open"] - c0_net["close"]) < 2.0)
    q["Q5"] = bool(FBREP["fallback_frac"] < 0.01 and F["RL"]["entry_share"] < 0.02 and F["C0"]["entry_share"] < 0.02)
    q["Q6"] = bool(NULL["gross_bp"]["score"] > NULL["gross_bp"]["p95"])
    vsa_ok = bool(abs(vc["r1"] - 3.298) < 0.01 and abs(vc["oc"] - (389.20 / 195.05 - 1.0)) < 1e-3)
    tag = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    print(f"  Q1 RL PUB net falls > 5 bp/bar under the open fill: {tag(q['Q1'])} -- {rl_net['close']:+.2f} -> "
          f"{rl_net['open']:+.2f} ({rl_net['open'] - rl_net['close']:+.2f}); PB {CELLS['RL']['close']['G1']['PB']['net_bp_bar']:+.2f} -> "
          f"{CELLS['RL']['open']['G1']['PB']['net_bp_bar']:+.2f}")
    print(f"  Q2 long-leg premium positive and larger than the short's: {tag(q['Q2'])} -- long "
          f"{prem_rl['0']['name_mean_bp']:+.1f} bp (t {prem_rl['0']['name_t']:+.2f}), short {prem_rl['1']['name_mean_bp']:+.1f} bp "
          f"(t {prem_rl['1']['name_t']:+.2f})")
    print(f"  Q3 top-5 trade share < 35% under the open fill: {tag(q['Q3'])} -- {100 * TOP['close'][1]:.1f}% -> {100 * TOP['open'][1]:.1f}%")
    print(f"  Q4 C0 moves < 2 bp/bar on PUB net: {tag(q['Q4'])} -- {c0_net['close']:+.2f} -> {c0_net['open']:+.2f} "
          f"({c0_net['open'] - c0_net['close']:+.2f})")
    print(f"  Q5 fallback < 1% of priced cells and < 2% of entries: {tag(q['Q5'])} -- {100 * FBREP['fallback_frac']:.4f}% of cells, "
          f"{100 * F['RL']['entry_share']:.3f}% / {100 * F['C0']['entry_share']:.3f}% of entries")
    print(f"  Q6 open-fill RL above its gross null p95: {tag(q['Q6'])} -- {NULL['gross_bp']['score']:+.3f} vs p95 "
          f"{NULL['gross_bp']['p95']:+.3f} (p50 {NULL['gross_bp']['p50']:+.3f}, p {NULL['gross_bp']['p']:.4f}), teeth {'yes' if teeth else 'no'}")
    print(f"  check VSA entry-bar credit +329.8% -> +99.5%: {'REPRODUCED' if vsa_ok else 'NOT reproduced'} -- "
          f"{100 * vc['r1']:+.1f}% -> {100 * vc['oc']:+.1f}% (389.20/195.05-1 = {100 * (389.20 / 195.05 - 1):+.1f}%); "
          f"held on that bar: close ledger {VSA['close'] is not None}, open ledger {VSA['open'] is not None}")

    # ---- write ------------------------------------------------------------------------------
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    def cell_out(c):
        return dict(group1=c["G1"], group2=c["G2"], group3=c["G3"],
                    legs={cv: {str(s): c["LEGS"][cv][s] for s in (0, 1)} for cv in CONVS},
                    invariant=c["INV"], borrow=dict(variant=c["BORROW_V"], invariant=c["BORROW_I"]),
                    trades_variant=len(c["res_v"]["trades"]), trades_invariant=len(c["res_i"]["trades"]))
    out = dict(
        note="D340: the D300 family's entry bar earns close[t-1]->close[t], the close the signal was computed at. "
             "fill='open' earns open[t]->close[t] (price only) against the open-to-close market on the entry bar. "
             "Two cells under both fills, both lenses, PB and PUB, GC+HTB borrow; the rank-rotation null on the "
             "open-fill retrace_leg cell. Variant bp/bar and invariant per trade are never compared. Nothing is promoted. "
             "per_leg's premium_bp and the borrow schemes read r1T on the entry bar under both fills (diagnostics only).",
        cells={nm: dict(label=SPEC[nm]["label"], k=SPEC[nm]["k"], depth=DEPTH, **{fl: cell_out(CELLS[nm][fl]) for fl in FILLS})
               for nm in SPEC},
        identity=dict(d338_worst=worst_b, c0_vs_d333_worst=worst_c0, c0_identity=c0_identity,
                      open_fill_bars_differ=nd, bars=int(T)),
        e1=dict(trades=int(pnl_e1c.size), entry_cells_differ=n_cell_diff, pnl_differ=n_pnl_diff, worst=worst_e1),
        e2=E2, fallback=dict(FBREP, per_cell=F), premiums=PREM,
        top_trades={fl: dict(rows=TOP[fl][0], top5_share=TOP[fl][1]) for fl in FILLS}, vsa=VSA,
        null=NULL, teeth_gross=teeth, predictions=q, vsa_check=bool(vsa_ok), draws=a.draws, seed=NULL_SEED,
        reconciliation=dict(residual_bp=resid, open_positions=n_open, worst_contrib_splice=worst_2))
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
