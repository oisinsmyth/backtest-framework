"""D348 -- control A on the slot books: each name's score rotated in time, re-ranked, re-simulated.

    uv run python scripts/run_d348_score_rotation_null.py --selftest
    uv run python scripts/run_d348_score_rotation_null.py --cell rsi:40 --draws 100 --part 0     (one process per part)
    uv run python scripts/run_d348_score_rotation_null.py --report

The three candidate cells (rsi k=40, hist_L k=40, retrace_leg k=20) rebuilt exactly as
D346's `run_cell` does, then faced with the null they have never met: every name's
finite score values circularly shifted in time by an independent uniform offset, the NaN
pattern untouched, the rotated score pushed through the unchanged pipeline
(`rank_single` -> `gate_from` -> both `simulate` lenses -> costing). The 24-shift rank
rotation is run beside it in `--report` so the record shows both nulls on one table.

Cell construction and every alias are D346's. `W.BASE_HOLD` is a module global: it is set
once per process for the cell, and no two k values are ever run in threads. Parallelism is
processes via `--part`.

ASSERTIONS [K][F0][R][ID][A][5][N][L][S][6][P] -- pre-reg section 6.
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


PR = _load("d348p", "d348_prep.py")                    # the cached prep shared with D349 / D350
ALIASES = ("W", "D", "Y", "R", "M", "X", "G22", "UF", "FL", "BR", "V9", "V38", "V31", "CEN", "SP", "EB")
if all(hasattr(PR, a) for a in ALIASES):
    W, D, Y, R, M, X, G22, UF, FL, BR, V9, V38, V31, CEN, SP, EB = (getattr(PR, a) for a in ALIASES)
else:
    V47 = _load("d347r", "run_d347_long_signal_controls.py")   # main guarded; every alias
    W, D, Y, R, M, X = V47.W, V47.D, V47.Y, V47.R, V47.M, V47.X
    G22, UF, FL, BR, V9, V38 = V47.G22, V47.UF, V47.FL, V47.BR, V47.V9, V47.V38
    V31, CEN, SP, EB = V47.V31, V47.CEN, V47.SP, V47.EB

DEPTH = 2
CONVS = ("PB", "PUB")
CELLS = (("rsi", 40), ("hist_L", 40), ("retrace_leg", 20))
STUDY = 348
N_BASE = W.N_BASE
N_LAG_BARS, N_NAME_SAMPLE = 200, 50
OUT = REPO / "data" / "d348_score_rotation_null.json"
CTRL = "d348_ctrl_{sig}_{k}_p{part}.json"
D346_JSON = REPO / "data" / "d346_legs_floor_open.json"
D343_JSON = REPO / "data" / "d343_relisting_clause.json"
PUBLISHED = {("hist_L", 40): (12.42, 0.401), ("rsi", 40): (5.14, 0.268), ("retrace_leg", 20): (2.68, 0.142)}
PREP_KEYS = ("A2", "r1T", "mkt", "finT", "ocT", "mkt_oc", "CLOSE", "VOL", "DV", "HALF", "G4", "excl", "keep", "RAW",
             "base", "T", "n", "score")

# the statistics recorded per draw (section 3), flat
STATS_V = ("gross_bp", "net_bp_PUB", "net_bp_PB", "sharpe_gross", "sharpe_net_PUB", "sharpe_net_PB", "net_bp_borrow_PUB",
           "net_bp_borrow_PB", "vol_bp", "maxdd_bp", "turnover", "bars", "entries", "trades_v")
STATS_I = ("leg_long_bp", "leg_short_bp", "leg_long_n", "leg_short_n", "leg_long_net_PUB", "leg_short_net_PUB",
           "inv_net_per_trade_PUB", "inv_net_per_trade_PB", "inv_trades")
STATS = STATS_V + STATS_I
TABLE_ROWS = (("gross bp/bar", "gross_bp"), ("PUB net bp/bar", "net_bp_PUB"), ("PB net bp/bar", "net_bp_PB"),
              ("PUB net + GC/HTB", "net_bp_borrow_PUB"), ("gross Sharpe", "sharpe_gross"), ("PUB net Sharpe", "sharpe_net_PUB"),
              ("bars", "bars"), ("entries", "entries"),
              ("long leg bp/trade", "leg_long_bp"), ("short leg bp/trade", "leg_short_bp"),
              ("long leg trades", "leg_long_n"), ("short leg trades", "leg_short_n"))


# ------------------------------------------------------------------ the rotation (D291's, on the finite mask)
def rotate_plan(fin):
    """Everything a per-name rotation needs that does NOT depend on the draw. `fin` is
    np.isfinite(sc), (n, T): the rotation is WITHIN each name's finite bars, so the NaN
    pattern -- floor, deal filter, warm-up, delisting -- is untouched."""
    ats = [np.flatnonzero(fin[i]) for i in range(fin.shape[0])]
    at_flat = np.concatenate(ats) if ats else np.empty(0, np.int64)
    lens = np.array([a.size for a in ats])
    start = np.concatenate([[0], np.cumsum(lens)[:-1]])
    rows = np.repeat(np.arange(fin.shape[0]), lens)
    jpos = np.arange(at_flat.size) - start[rows]
    return dict(at=at_flat.astype(np.int64), rows=rows, jpos=jpos, L=lens[rows], start=start[rows], ats=ats, lens=lens)


def rotate(score, rp, off):
    """out[i, at_i[j]] = score[i, at_i[(j - off_i) % L_i]]: four gathers, no loop, no arithmetic on values."""
    out = np.full(score.shape, np.nan)
    src = rp["at"][rp["start"] + (rp["jpos"] - off[rp["rows"]]) % rp["L"]]
    out[rp["rows"], rp["at"]] = score[rp["rows"], src]
    return out


def rotate_loop(score, ats, off):
    """The obvious per-name np.roll. KEPT, and used only by guard [5]."""
    out = np.full(score.shape, np.nan)
    for i, at in enumerate(ats):
        if at.size:
            out[i, at] = np.roll(score[i, at], int(off[i]))
    return out


def draw_offsets(rng, lens):
    """Uniform on [0, L_i); 0 when L_i < 2. One integer per name."""
    return rng.integers(0, np.maximum(lens, 1))


def check_rotation(rot, sc, fin, names):
    """[A]: per-name finite count, per-bar finite count, per-name sorted values -- exact."""
    rf = np.isfinite(rot)
    assert np.array_equal(rf.sum(axis=1), fin.sum(axis=1)), "[A] per-name finite count moved"
    assert np.array_equal(rf.sum(axis=0), fin.sum(axis=0)), "[A] per-bar finite count moved"
    for i in names:
        assert np.array_equal(np.sort(rot[i, rf[i]]), np.sort(sc[i, fin[i]])), f"[A] multiset of name {i} moved"


# ------------------------------------------------------------------ the cell (D346's run_cell, exactly)
def cell_score(P, sig):
    return UF.apply_floor_replace(np.where(P["excl"], np.nan, P["score"](sig)), P["keep"])


def build_gate(P, sig, sc):
    rankT = Y.rank_single({sig: sc}, P["base"], sig, P["n"], P["T"])
    return Y.gate_from(rankT, P["finT"])


def simulate_both(P, gate, shift=0):
    res_v = W.simulate(P["A2"], gate, DEPTH, True, slots=True, shift=shift, fill="open")
    res_i = W.simulate(P["A2"], gate, DEPTH, True, slots=False, shift=shift, fill="open")
    return res_v, res_i


def cell_stats(P, res_v, res_i, want_full=False):
    """Every section-3 statistic of one (variant, invariant) pair, flat. Costing via G22.costed
    per convention, per-leg via V9, borrow via V38.borrow_block as D344 does."""
    HALF, CLOSE, r1T, mkt = P["HALF"], P["CLOSE"], P["r1T"], P["mkt"]
    C, degenerate = {}, False
    for cv in CONVS:
        try:
            C[cv] = G22.costed(res_v, P["G4"][cv])
        except ZeroDivisionError:
            C[cv] = None
            degenerate = True
    LEGS = {cv: V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt) for cv in CONVS}
    both = all(LEGS[cv][s] for cv in CONVS for s in (0, 1))
    INV = {cv: (V9.invariant_legcost(res_i, LEGS[cv]) if both else None) for cv in CONVS}
    BV = None
    if not degenerate:
        BV, _ = V38.borrow_block(res_v, C, None, P["excl"], CLOSE, P["T"])
    nan = float("nan")
    s = {}
    c = C["PUB"]
    s["gross_bp"] = c["gross_bp"] if c else nan
    s["vol_bp"] = c["vol_bp"] if c else nan
    s["sharpe_gross"] = c["sharpe_gross"] if c else nan
    s["maxdd_bp"] = c["maxdd_bp"] if c else nan
    s["turnover"] = c["turnover"] if c else nan
    for cv in CONVS:
        s[f"net_bp_{cv}"] = C[cv]["net_bp"] if C[cv] else nan
        s[f"sharpe_net_{cv}"] = C[cv]["sharpe_net"] if C[cv] else nan
        s[f"net_bp_borrow_{cv}"] = BV["gc_htb"][cv]["net_bp_borrow"] if BV else nan
        s[f"inv_net_per_trade_{cv}"] = INV[cv]["net_per_trade"] if INV[cv] else nan
    ok = res_v["mask"]
    s["bars"] = int(ok.sum())
    s["entries"] = int(res_v["ent"][ok].sum())
    s["trades_v"] = len(res_v["trades"])
    for side, nm in ((0, "long"), (1, "short")):
        L = LEGS["PUB"][side]
        s[f"leg_{nm}_bp"] = L["gross"] if L else nan
        s[f"leg_{nm}_n"] = L["trades"] if L else 0
        s[f"leg_{nm}_net_PUB"] = L["net"] if L else nan
    s["inv_trades"] = len(res_i["trades"])
    s["degenerate"] = bool(degenerate)
    if want_full:
        return s, dict(C=C, LEGS=LEGS, INV=INV, borrow_variant=BV)
    return s


def observed_cell(P, sig, k, pub, verbose=True):
    """The zero-offset cell, asserted equal to the published cell to 0.0 ([ID])."""
    W.BASE_HOLD = k
    sc = cell_score(P, sig)
    gate = build_gate(P, sig, sc)
    res_v, res_i = simulate_both(P, gate)
    stats, full = cell_stats(P, res_v, res_i, want_full=True)
    worst = identity_worst(sig, k, stats, full, pub)
    assert worst < 1e-9, f"[ID] {sig} k={k}: worst {worst:.2e}"
    if verbose:
        hp, hs = PUBLISHED[(sig, k)]
        print(f"    [ID] {sig} k={k}: zero-offset cell == {'D346' if k == 40 else 'D343'} to {worst:.1e} -- PUB net {stats['net_bp_PUB']:+.2f} "
              f"(published {hp:+.2f}), Sharpe {stats['sharpe_net_PUB']:+.3f} (published {hs:.3f}), PB net {stats['net_bp_PB']:+.2f}, "
              f"{stats['trades_v']:,} trades, {stats['bars']:,} bars; legs {stats['leg_long_bp']:+.1f} / {stats['leg_short_bp']:+.1f} bp")
    return dict(sc=sc, gate=gate, res_v=res_v, res_i=res_i, stats=stats, full=full, worst=worst)


def identity_worst(sig, k, stats, full, pub):
    """Published values to 0.0: PUB and PB net bp/bar, Sharpe, trades, bars (where published), both legs' per-trade means."""
    C, LEGS, INV = full["C"], full["LEGS"], full["INV"]
    worst = 0.0
    if k == 40:
        ref = pub["d346"]["table"]["40"][sig]
        for cv in CONVS:
            worst = max(worst, abs(C[cv]["net_bp"] - ref["variant"][cv]["net_bp_bar"]),
                        abs(C[cv]["sharpe_net"] - ref["variant"][cv]["sharpe_net"]),
                        abs(C[cv]["gross_bp"] - ref["variant"][cv]["gross_bp_bar"]),
                        abs(INV[cv]["net_per_trade"] - ref["invariant"][cv]["net_per_trade"]),
                        abs(INV[cv]["trades"] - ref["invariant"][cv]["trades"]))
            for s in (0, 1):
                L, Lr = LEGS[cv][s], ref["legs"][cv][str(s)]
                worst = max(worst, abs(L["gross"] - Lr["gross"]), abs(L["net"] - Lr["net"]), abs(L["trades"] - Lr["trades"]))
    else:
        ref = pub["d343"]["cells"]["RL/v2"]
        for cv in CONVS:
            worst = max(worst, abs(C[cv]["net_bp"] - ref["costed"][cv]["net_bp"]),
                        abs(C[cv]["sharpe_net"] - ref["costed"][cv]["sharpe_net"]),
                        abs(C[cv]["gross_bp"] - ref["costed"][cv]["gross_bp"]),
                        abs(C[cv]["trades"] - ref["costed"][cv]["trades"]), abs(C[cv]["bars"] - ref["costed"][cv]["bars"]),
                        abs(C[cv]["entries"] - ref["costed"][cv]["entries"]),
                        abs(INV[cv]["net_per_trade"] - ref["invariant"][cv]["net_per_trade"]),
                        abs(INV[cv]["trades"] - ref["invariant"][cv]["trades"]))
            for s in (0, 1):
                L, Lr = LEGS[cv][s], ref["legs"][cv][str(s)]
                worst = max(worst, abs(L["gross"] - Lr["gross"]), abs(L["net"] - Lr["net"]), abs(L["trades"] - Lr["trades"]))
        worst = max(worst, abs(stats["trades_v"] - ref["trades"]))
    return worst


def one_draw(P, sig, sc, rp, rng, name_sample):
    """rotate -> rank_single -> gate_from -> both simulates -> stats. Asserts [N] and [A] on the draw."""
    off = draw_offsets(rng, rp["lens"])
    rot = rotate(sc, rp, off)
    big = rp["lens"] >= 100
    frac_nz = float((off[big] != 0).mean()) if big.any() else 1.0
    assert frac_nz > 0.99, f"[N] offsets non-zero on only {100 * frac_nz:.2f}% of names with L >= 100"
    check_rotation(rot, sc, rp["fin"], name_sample)
    gate = build_gate(P, sig, rot)
    res_v, res_i = simulate_both(P, gate)
    return dict(off=off, rot=rot, gate=gate, res_v=res_v, res_i=res_i, stats=cell_stats(P, res_v, res_i), frac_nz=frac_nz)


def plan_for(sc):
    fin = np.isfinite(sc)
    rp = rotate_plan(fin)
    rp["fin"] = fin
    return rp


def cell_rng(cell_index, part):
    return np.random.default_rng([W.SEED, STUDY, cell_index, part])


def load_published():
    return dict(d346=json.loads(D346_JSON.read_text()), d343=json.loads(D343_JSON.read_text()))


# ------------------------------------------------------------------ the audits
def lag_audit(P, gate, sc, bars):
    """[L]: the held long set at every sampled bar, rebuilt from score[:, t-1] by V38.rebuild_long_set,
    which never calls rank_single / rank_columns / gate_from. Returns how many bars the UNLAGGED
    rebuild differs on. Raises AssertionError on any mismatch."""
    base, finT = P["base"], P["finT"]
    n_unl = 0
    for t in bars:
        t = int(t)
        got = set(int(r) for r in V38.gate_rows(gate, 0, t))
        assert got == V38.rebuild_long_set(sc, base, finT, t, 1), f"[L] bar {t}: gate != rebuild from score[:, t-1]"
        n_unl += V38.rebuild_long_set(sc, base, finT, t, 0) != got
    return n_unl


def sign_audit(P, res, label):
    """[S] on a ledger: every trade equals the open-fill recomputation; favourable paths pay positively;
    a synthetic +50 bp on one held bar (the cash a holder of the prior close receives) lifts a long
    trade's P&L by exactly 50 bp and cuts a short trade's by exactly 50 bp."""
    r1T, mkt, ocT, mkt_oc = P["r1T"], P["mkt"], P["ocT"], P["mkt_oc"]
    tr = res["trades"]
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
    worst = float(np.abs(rec - pnl).max())
    assert worst < 1e-12, f"[S] {label}: recomputation differs by {worst:.2e}"
    ex = np.array([float((ocT[e0, row] - mkt_oc[e0]) + (r1T[e0 + 1:e0 + age, row] - mkt[e0 + 1:e0 + age]).sum())
                   for row, e0, age, _p, _s in tr])
    longs = np.array([t[4] == 0 for t in tr])
    assert (pnl[longs & (ex > 0)] > 0).all() and (pnl[~longs & (ex < 0)] > 0).all(), f"[S] {label}: a favourable path does not pay"
    # synthetic dividend: one long trade and one short trade on different names, each held >= 2 bars
    iL = next(i for i, t in enumerate(tr) if t[4] == 0 and t[2] >= 2)
    iS = next(i for i, t in enumerate(tr) if t[4] == 1 and t[2] >= 2 and t[0] != tr[iL][0])
    r1p = r1T.copy()
    for i in (iL, iS):
        row, e0 = tr[i][0], tr[i][1]
        r1p[e0 + 1, row] += 50e-4
    rec2 = FL.pnl_recomputed_fill([tr[iL], tr[iS]], r1p, mkt, ocT, mkt_oc)
    dL, dS = float(rec2[0] - pnl[iL]), float(rec2[1] - pnl[iS])
    assert abs(dL - 50e-4) < 1e-12 and abs(dS + 50e-4) < 1e-12 and dL * dS < 0, f"[S] {label}: dividend moved long {dL:+.2e}, short {dS:+.2e}"
    return worst, dL * 1e4, dS * 1e4, len(tr)


# ------------------------------------------------------------------ stages
def stage_selftest(P, draws=3):
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    pub = load_published()
    print("\nASSERTIONS")
    OBS, DRAWS = {}, {}
    for ci, (sig, k) in enumerate(CELLS):
        OBS[sig, k] = observed_cell(P, sig, k, pub)
        sc = OBS[sig, k]["sc"]
        rp = plan_for(sc)
        n_all = np.arange(P["n"])
        rng = cell_rng(ci, 0)
        DRAWS[sig, k] = []
        for d in range(draws):
            r = one_draw(P, sig, sc, rp, rng, n_all)         # [A] on ALL names in the selftest
            DRAWS[sig, k].append(r)
        fr = [r["frac_nz"] for r in DRAWS[sig, k]]
        print(f"    [A] {sig} k={k}: {draws} draws keep every name's finite count, every bar's finite count and every name's multiset exactly; "
              f"[N] offsets non-zero on {100 * min(fr):.2f}-{100 * max(fr):.2f}% of names with L >= 100 ({el()})")
        # the draws move the book
        g = [r["stats"]["gross_bp"] for r in DRAWS[sig, k]]
        print(f"        draws: gross bp/bar " + ", ".join(f"{v:+.2f}" for v in g) + f"; PUB net " +
              ", ".join(f"{r['stats']['net_bp_PUB']:+.2f}" for r in DRAWS[sig, k]) + f"; long leg " +
              ", ".join(f"{r['stats']['leg_long_bp']:+.1f}" for r in DRAWS[sig, k]) + f" vs observed {OBS[sig, k]['stats']['leg_long_bp']:+.1f}")
    # [5] vectorised == np.roll loop, real score 3 draws per cell, tie-heavy synthetic 20 draws
    rng5 = np.random.default_rng([W.SEED, STUDY, 5])
    for sig, k in CELLS:
        sc = OBS[sig, k]["sc"]
        rp = plan_for(sc)
        for _ in range(3):
            off = draw_offsets(rng5, rp["lens"])
            assert np.array_equal(rotate(sc, rp, off), rotate_loop(sc, rp["ats"], off), equal_nan=True), f"[5] real score {sig}"
    syn = rng5.integers(0, 4, size=(200, 500)).astype(float)
    syn[rng5.random(syn.shape) < 0.30] = np.nan
    rps = plan_for(syn)
    for _ in range(20):
        off = draw_offsets(rng5, rps["lens"])
        a, b = rotate(syn, rps, off), rotate_loop(syn, rps["ats"], off)
        assert np.array_equal(a, b, equal_nan=True), "[5] synthetic"
        check_rotation(a, syn, rps["fin"], range(200))
    print(f"    [5] the vectorised rotation equals the np.roll loop bit-identically: 3 draws on each cell's real score, 20 on a tie-heavy "
          f"synthetic (200 x 500, integers 0-3, {100 * np.isnan(syn).mean():.0f}% NaN)")
    # [L] lag audit on the observed rsi book and one rotated book
    sig, k = CELLS[0]
    O, R1 = OBS[sig, k], DRAWS[sig, k][0]
    lag_rng = np.random.default_rng([W.SEED, STUDY, 7])
    for lab, gate, sc in (("observed", O["gate"], O["sc"]), ("rotated", R1["gate"], R1["rot"])):
        nonempty = np.array([t for t in range(1, P["T"]) if V38.gate_rows(gate, 0, t).size > 0])
        bars = lag_rng.choice(nonempty, size=N_LAG_BARS, replace=False)
        n_unl = lag_audit(P, gate, sc, bars)
        assert n_unl > N_LAG_BARS // 2, f"[L] {lab}: unlagged rebuild differs on only {n_unl}"
        print(f"    [L] LAG AUDIT ({lab} {sig} k={k}): the long gate equals the rebuild from score[:, t-1] on all {N_LAG_BARS} sampled bars; "
              f"the unlagged rebuild differs on {n_unl}")
    # [S] sign in money on the rotated ledgers, both lenses
    for lens in ("res_i", "res_v"):
        worst, dL, dS, ntr = sign_audit(P, R1[lens], f"rotated {lens}")
        print(f"    [S] SIGN IN MONEY (rotated {sig} k={k}, {'invariant' if lens == 'res_i' else 'variant'}): {ntr:,} trades equal the open-fill "
              f"recomputation to {worst:.1e}; favourable paths pay positively; a +50 bp held-bar move lifts a long {dL:+.1f} bp and a short {dS:+.1f} bp")
    # [6] the audits raise
    broke = False
    try:
        sc_unl = np.full_like(O["sc"], np.nan)
        sc_unl[:, :-1] = O["sc"][:, 1:]                 # lag1 of this is the score AT t: an unlagged gate
        gate_unl = build_gate(P, sig, sc_unl)
        lag_audit(P, gate_unl, O["sc"], bars)
    except AssertionError:
        broke = True
    assert broke, "[6] [L] did not raise on the unlagged gate"
    broke = False
    try:
        check_rotation(np.roll(O["sc"], 7, axis=1), O["sc"], np.isfinite(O["sc"]), range(P["n"]))
    except AssertionError:
        broke = True
    assert broke, "[6] [A] did not raise on a whole-panel roll"
    print("    [6] and [L] raises on a gate fed the unlagged score; [A] raises on a whole-panel np.roll")
    # [P] the report identity, on this process's own record
    rec = json.loads(json.dumps(clean(OBS[sig, k]["stats"])))
    worst_p = stats_worst(rec, OBS[sig, k]["stats"])
    assert worst_p < 1e-9, f"[P] {worst_p:.2e}"
    print(f"    [P] a stored observed statistics dict round-trips through JSON and equals the live one to {worst_p:.1e}")
    print(f"\nOK  assertions pass  ({el()})")


def stats_worst(a, b):
    worst = 0.0
    for k in STATS:
        x, y = a.get(k), b.get(k)
        x = float("nan") if x is None else float(x)
        y = float("nan") if y is None else float(y)
        if np.isnan(x) and np.isnan(y):
            continue
        worst = max(worst, abs(x - y))
    return worst


def stage_cell(P, sig, k, draws, part):
    t0 = time.time()
    pub = load_published()
    ci = CELLS.index((sig, k))
    print("\nASSERTIONS")
    O = observed_cell(P, sig, k, pub)
    sc = O["sc"]
    rp = plan_for(sc)
    rng = cell_rng(ci, part)
    name_rng = np.random.default_rng([W.SEED, STUDY, 99, ci, part])
    REC = {s: [] for s in STATS}
    n_deg = 0
    ts = time.time()
    print(f"\n  {sig} k={k} part {part}: {draws} control-A draws, RNG [{W.SEED}, {STUDY}, {ci}, {part}]")
    for d in range(draws):
        names = name_rng.choice(P["n"], size=N_NAME_SAMPLE, replace=False)
        r = one_draw(P, sig, sc, rp, rng, names)
        s = r["stats"]
        n_deg += int(s["degenerate"])
        for key in STATS:
            REC[key].append(s[key])
        if (d + 1) % 10 == 0:
            print(f"    {d + 1}/{draws} ({time.time() - ts:.0f}s, {(time.time() - ts) / (d + 1):.2f} s/draw)", flush=True)
    out = dict(cell=f"{sig}:{k}", sig=sig, k=k, cell_index=ci, part=part, draws=draws, seed=[W.SEED, STUDY, ci, part],
               observed=O["stats"], identity_worst=O["worst"], degenerate_draws=n_deg, elapsed_s=time.time() - ts, per_draw=REC)
    f = REPO / "data" / CTRL.format(sig=sig, k=k, part=part)
    f.write_text(json.dumps(clean(out)))
    A = np.array(REC["net_bp_PUB"], float)
    print(f"  wrote {f.name}: PUB net observed {O['stats']['net_bp_PUB']:+.2f} vs control A p50 {np.nanmedian(A):+.2f} p95 {np.nanquantile(A, .95):+.2f} "
          f"max {np.nanmax(A):+.2f}; long leg observed {O['stats']['leg_long_bp']:+.1f} vs A p50 {np.nanmedian(REC['leg_long_bp']):+.1f}; "
          f"{n_deg} degenerate draws ({time.time() - t0:.0f}s)")


def dist_of(arr, obs):
    a = np.asarray(arr, float)
    fin = a[np.isfinite(a)]
    if fin.size == 0:
        return dict(p50=None, p95=None, max=None, draws=0, below=None)
    return dict(p50=float(np.median(fin)), p95=float(np.quantile(fin, .95)), max=float(fin.max()), draws=int(fin.size),
                below=(float((fin < obs).mean()) if obs is not None and np.isfinite(obs) else None),
                p=float((fin >= obs).sum() + 1) / (fin.size + 1) if obs is not None and np.isfinite(obs) else None)


def stage_report(P):
    t0 = time.time()
    pub = load_published()
    print("\nASSERTIONS")
    REPORT = {}
    for ci, (sig, k) in enumerate(CELLS):
        parts = sorted((REPO / "data").glob(CTRL.format(sig=sig, k=k, part="*")))
        O = observed_cell(P, sig, k, pub)
        obs = O["stats"]
        if not parts:
            print(f"    [P] {sig} k={k}: no control-A parts on disk -- the cell is reported without control A")
            A = None
        else:
            worst = 0.0
            recs = {s: [] for s in STATS}
            n_draws, n_deg = 0, 0
            for pth in parts:
                pj = json.loads(pth.read_text())
                worst = max(worst, stats_worst(pj["observed"], obs))
                for s in STATS:
                    recs[s].extend(pj["per_draw"][s])
                n_draws += pj["draws"]
                n_deg += pj.get("degenerate_draws", 0)
            assert worst < 1e-9, f"[P] {sig} k={k}: a stored observed statistic differs from the re-simulated one by {worst:.2e}"
            print(f"    [P] {sig} k={k}: {len(parts)} part(s), {n_draws} draws; every stored observed statistic equals the re-simulated one to {worst:.1e}")
            A = {s: np.array([np.nan if v is None else v for v in recs[s]], float) for s in STATS}
            A["_n"] = n_draws
            A["_deg"] = n_deg
            A["_parts"] = [p.name for p in parts]
        # the 24-shift rank rotation beside it, memoised over distinct shifts (every shift once)
        ts = time.time()
        W.BASE_HOLD = k
        by_shift = {}
        for s_ in range(1, N_BASE):
            rv, ri = simulate_both(P, O["gate"], shift=s_)
            by_shift[s_] = cell_stats(P, rv, ri)
        RR = {s: np.array([by_shift[s_][s] for s_ in sorted(by_shift)], float) for s in STATS}
        print(f"    rank rotation {sig} k={k}: {len(by_shift)} distinct shifts ({time.time() - ts:.0f}s)")
        REPORT[sig, k] = dict(observed=obs, A=A, RR=RR, identity_worst=O["worst"])

    # ---- the tables ---------------------------------------------------------------------------------------
    for sig, k in CELLS:
        Rp = REPORT[sig, k]
        obs, A, RR = Rp["observed"], Rp["A"], Rp["RR"]
        hp, hs = PUBLISHED[(sig, k)]
        print("\n" + "=" * 132)
        print(f"{sig} k={k}  (published PUB net {hp:+.2f}, Sharpe {hs:.3f}; control A {A['_n'] if A else 0} draws, "
              f"{A['_deg'] if A else 0} degenerate; rank rotation {RR['gross_bp'].size} shifts)")
        print("=" * 132)
        print("  %-20s %10s | %10s %10s %10s %8s | %10s %10s %10s %10s" % ("statistic", "observed", "A p50", "A p95", "A max", "A below",
                                                                            "rank p50", "rank p95", "rank max", "above k/24"))
        Rp["table"] = {}
        for lab, key in TABLE_ROWS:
            o = obs[key]
            dA = dist_of(A[key], o) if A else None
            dR = dist_of(RR[key], o)
            above_r = int((RR[key][np.isfinite(RR[key])] < o).sum())
            Rp["table"][key] = dict(observed=o, control_A=dA, rank_rotation=dict(dR, above_k=above_r, of=int(np.isfinite(RR[key]).sum())))
            fmt = "%10.3f" if key in ("sharpe_gross", "sharpe_net_PUB", "sharpe_net_PB") else ("%10d" if key in ("bars", "entries", "leg_long_n", "leg_short_n") else "%10.2f")
            f_ = lambda v: (fmt % v) if v is not None and np.isfinite(v) else "%10s" % "--"
            print("  %-20s %s | %s %s %s %8s | %s %s %s %10s" % (
                lab, f_(o), f_(dA["p50"]) if dA else "%10s" % "--", f_(dA["p95"]) if dA else "%10s" % "--", f_(dA["max"]) if dA else "%10s" % "--",
                (f"{100 * dA['below']:.1f}%" if dA and dA["below"] is not None else "--"),
                f_(dR["p50"]), f_(dR["p95"]), f_(dR["max"]), f"{above_r} of {int(np.isfinite(RR[key]).sum())}"))

    # ---- predictions --------------------------------------------------------------------------------------
    def A_of(sig, k, key):
        A = REPORT[sig, k]["A"]
        return dist_of(A[key], REPORT[sig, k]["observed"][key]) if A else None

    def above_A(sig, k, key):
        d = A_of(sig, k, key)
        return bool(d and d["p95"] is not None and REPORT[sig, k]["observed"][key] > d["p95"])

    def R_p95(sig, k, key):
        return dist_of(REPORT[sig, k]["RR"][key], None)["p95"]

    q = {}
    q["Q1"] = above_A("rsi", 40, "net_bp_PUB")
    q["Q2"] = above_A("hist_L", 40, "net_bp_PUB")
    aL = {c: A_of(*c, "leg_long_bp") for c in CELLS[:2]}
    aS = {c: A_of(*c, "leg_short_bp") for c in CELLS[:2]}
    q["Q3"] = bool(all(aL[c] and aL[c]["p50"] is not None and aL[c]["p50"] > 0 for c in CELLS[:2])
                   and aL[("hist_L", 40)] and REPORT["hist_L", 40]["observed"]["leg_long_bp"] < aL[("hist_L", 40)]["p50"])
    q["Q4"] = bool(all(aS[c] and aS[c]["p50"] is not None and aS[c]["p50"] < 0 for c in CELLS[:2]))
    q["Q5"] = bool(all(A_of(*c, "gross_bp") and A_of(*c, "gross_bp")["p95"] is not None and A_of(*c, "gross_bp")["p95"] > R_p95(*c, "gross_bp")
                       for c in CELLS))
    q["Q6"] = above_A("retrace_leg", 20, "net_bp_PUB")
    q["Q7"] = bool(any(above_A(*c, "sharpe_gross") for c in CELLS[:2]))
    check = bool(all(REPORT[c]["identity_worst"] < 1e-9 for c in CELLS))
    CF = lambda b: "CONFIRMED" if b else "FALSIFIED"

    def line(c, key):
        d = A_of(*c, key)
        o = REPORT[c]["observed"][key]
        return f"{c[0]} k={c[1]} {o:+.2f} vs A p95 {d['p95']:+.2f} (below {100 * d['below']:.1f}%)" if d and d["p95"] is not None else f"{c[0]} k={c[1]} {o:+.2f} vs A --"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) rsi k=40 PUB net above control A p95: {CF(q['Q1'])} -- {line(('rsi', 40), 'net_bp_PUB')}")
    print(f"  Q2 hist_L k=40 PUB net above control A p95: {CF(q['Q2'])} -- {line(('hist_L', 40), 'net_bp_PUB')}")
    print(f"  Q3 A's long leg centred > 0 on both k=40 cells and hist_L's observed long leg below A's median: {CF(q['Q3'])} -- " +
          ", ".join(f"{c[0]} A p50 {aL[c]['p50']:+.1f} (observed {REPORT[c]['observed']['leg_long_bp']:+.1f})" for c in CELLS[:2] if aL[c] and aL[c]["p50"] is not None))
    print(f"  Q4 A's short leg centred < 0 on both k=40 cells: {CF(q['Q4'])} -- " +
          ", ".join(f"{c[0]} A p50 {aS[c]['p50']:+.1f} (observed {REPORT[c]['observed']['leg_short_bp']:+.1f})" for c in CELLS[:2] if aS[c] and aS[c]["p50"] is not None))
    print(f"  Q5 A's gross p95 above the rank rotation's on every cell: {CF(q['Q5'])} -- " +
          ", ".join(f"{c[0]} k={c[1]} A {A_of(*c, 'gross_bp')['p95']:+.2f} vs rank {R_p95(*c, 'gross_bp'):+.2f}" for c in CELLS if A_of(*c, "gross_bp") and A_of(*c, "gross_bp")["p95"] is not None))
    print(f"  Q6 (against) retrace_leg k=20 PUB net above control A p95: {CF(q['Q6'])} -- {line(('retrace_leg', 20), 'net_bp_PUB')}")
    print(f"  Q7 gross Sharpe above A p95 on at least one k=40 cell: {CF(q['Q7'])} -- " +
          ", ".join(f"{c[0]} {REPORT[c]['observed']['sharpe_gross']:+.3f} vs A p95 {A_of(*c, 'sharpe_gross')['p95']:+.3f}" for c in CELLS[:2] if A_of(*c, "sharpe_gross") and A_of(*c, "sharpe_gross")["p95"] is not None))
    print(f"  check: zero-offset draws reproduce D346 / D343 to 0.0: {CF(check)} -- worst " +
          ", ".join(f"{c[0]} {REPORT[c]['identity_worst']:.1e}" for c in CELLS))

    out = dict(note="D348: control A (each name's score rotated in time within its finite bars, re-ranked, re-simulated) on the three "
                    "candidate slot-book cells, the 24-shift rank rotation beside it. Variant bp/bar and invariant per trade never compared. "
                    "Nothing promoted; the book is empty.",
               cells={f"{sig}:{k}": dict(observed=REPORT[sig, k]["observed"], identity_worst=REPORT[sig, k]["identity_worst"],
                                         published=dict(net_bp_PUB=PUBLISHED[(sig, k)][0], sharpe_net_PUB=PUBLISHED[(sig, k)][1]),
                                         control_A=(dict(draws=REPORT[sig, k]["A"]["_n"], degenerate=REPORT[sig, k]["A"]["_deg"],
                                                         parts=REPORT[sig, k]["A"]["_parts"],
                                                         dist={s: dist_of(REPORT[sig, k]["A"][s], REPORT[sig, k]["observed"][s]) for s in STATS})
                                                    if REPORT[sig, k]["A"] else None),
                                         rank_rotation=dict(shifts=int(REPORT[sig, k]["RR"]["gross_bp"].size),
                                                            dist={s: dist_of(REPORT[sig, k]["RR"][s], REPORT[sig, k]["observed"][s]) for s in STATS},
                                                            per_shift={s: REPORT[sig, k]["RR"][s] for s in STATS}),
                                         table=REPORT[sig, k]["table"])
                      for sig, k in CELLS},
               statistics=STATS, predictions=q, identity_check=check)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")


def clean(o):
    if isinstance(o, dict):
        return {("/".join(map(str, k)) if isinstance(k, tuple) else str(k)): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return [clean(v) for v in o.tolist()]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cell", help="SIG:K, one of " + ", ".join(f"{s}:{k}" for s, k in CELLS))
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    print("D348  control A on the slot books -- each name's score rotated in time, re-ranked, re-simulated")
    P = PR.prep(need_grids=False)
    missing = [k for k in PREP_KEYS if k not in P]
    if missing:
        print(f"prep() is missing keys the runner needs: {missing}")
        return 2
    print(f"  prep ready: panel {P['finT'].shape} ({time.time() - t0:.0f}s)")
    if a.selftest:
        stage_selftest(P, draws=3)
    elif a.cell:
        sig, k = a.cell.split(":")
        k = int(k)
        if (sig, k) not in CELLS:
            ap.error(f"--cell must be one of {CELLS}")
        stage_cell(P, sig, k, a.draws, a.part)
    elif a.report:
        stage_report(P)
    else:
        ap.error("one of --selftest, --cell SIG:K, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
