"""D355 -- the invalidation exit on the candidate books: a signal exit beside the target on the two cells that pay.

    uv run python scripts/run_d355_exit_swap.py --selftest
    uv run python scripts/run_d355_exit_swap.py --cell rsi:40 --arm invalidation --draws 100 --part 0     (one process per part)
    uv run python scripts/run_d355_exit_swap.py --report

PRE-REGISTERED in docs/decisions/D355-the-invalidation-exit-on-the-candidate-books.md, committed before this file
or the simulator keyword existed (R8).

The two k=40 cells (`rsi`, `hist_L`) rebuilt exactly as D346's `run_cell` / D348's `observed_cell` do, then run under
three exits (section 2):

    target        D303's target or the cap -- the published cell, the identity arm ([ID0])
    invalidation  the name's LAGGED floored cross-sectional percentile of the same score crossing 50, or the cap; no target
    both          target or invalidation, whichever first, or the cap

The invalidation exit is the additive `invalidation=` keyword on run_d306_width_exits.simulate, fed the shared prep's
cached `PCT[sig]` (D347's percentile_grid of exactly the lagged score the ranker ranks). [IDX] holds that keyword to
D345's kernel with exit="invalidation" bit-for-bit on the invariant lens.

Nulls per arm (section 3): the 24 rank rotations of the observed gate (the arm's exit reading the REAL percentile grid),
and control A' -- D348's per-name time rotation of the score within its finite bars, re-ranked, WITH THE PERCENTILE GRID
RECOMPUTED FROM THE ROTATED SCORE so the exit under the null reads the rotated signal. Seeds [SEED, 355, cell, arm, part].

Cell construction, costing, per-leg, borrow and every alias are D348's. `W.BASE_HOLD` is a module global set once per
process (both cells are k=40). Parallelism is processes via `--part`.

ASSERTIONS [K][F0][R][ID0][IDX][X0][PC][A][N][L][S][6][P] -- pre-reg section 6.
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


PR = _load("d348p", "d348_prep.py")                    # the cached prep shared with D348 / D349 / D350; every alias from here
V47 = PR.V47
W, D, Y, R, M, X = PR.W, PR.D, PR.Y, PR.R, PR.M, PR.X
G22, UF, FL, BR, V9, V38, V31, CEN, SP, EB = PR.G22, PR.UF, PR.FL, PR.BR, PR.V9, PR.V38, PR.V31, PR.CEN, PR.SP, PR.EB
V45 = V47.V45                                          # ledger_set

DEPTH = 2
CONVS = ("PB", "PUB")
CELLS = (("rsi", 40), ("hist_L", 40))
ARMS = ("target", "invalidation", "both")
STUDY = 355
N_BASE = W.N_BASE
X_TARGET, U_CAP = W.X_TARGET, 4
N_LAG_BARS, N_NAME_SAMPLE, N_EXIT_SAMPLE = 200, 50, 300
OUT = REPO / "data" / "d355_exit_swap.json"
CTRL = "d355_ctrl_{sig}_{k}_{arm}_p{part}.json"
D348_CTRL = "d348_ctrl_{sig}_{k}_p0.json"
D346_JSON = REPO / "data" / "d346_legs_floor_open.json"
PUBLISHED = {("hist_L", 40): (12.42, 0.401), ("rsi", 40): (5.14, 0.268)}
PREP_KEYS = ("A2", "r1T", "mkt", "finT", "ocT", "mkt_oc", "CLOSE", "VOL", "DV", "HALF", "G4", "excl", "keep", "RAW",
             "base", "T", "n", "score", "LAG", "PCT")

# the statistics recorded per draw: D348's 23, plus the cost term and the holding lengths the exit moves (additive)
STATS_V = ("gross_bp", "net_bp_PUB", "net_bp_PB", "sharpe_gross", "sharpe_net_PUB", "sharpe_net_PB", "net_bp_borrow_PUB",
           "net_bp_borrow_PB", "vol_bp", "maxdd_bp", "turnover", "bars", "entries", "trades_v", "cost_bp_PUB", "cost_bp_PB",
           "hold_v")
STATS_I = ("leg_long_bp", "leg_short_bp", "leg_long_n", "leg_short_n", "leg_long_net_PUB", "leg_short_net_PUB",
           "inv_net_per_trade_PUB", "inv_net_per_trade_PB", "inv_trades", "hold_i",
           "leg_long_age", "leg_short_age", "leg_long_bp_per_bar", "leg_short_bp_per_bar")
STATS = STATS_V + STATS_I
STATS_D348 = ("gross_bp", "net_bp_PUB", "net_bp_PB", "sharpe_gross", "sharpe_net_PUB", "sharpe_net_PB", "net_bp_borrow_PUB",
              "net_bp_borrow_PB", "vol_bp", "maxdd_bp", "turnover", "bars", "entries", "trades_v",
              "leg_long_bp", "leg_short_bp", "leg_long_n", "leg_short_n", "leg_long_net_PUB", "leg_short_net_PUB",
              "inv_net_per_trade_PUB", "inv_net_per_trade_PB", "inv_trades")
TABLE_ROWS = (("gross bp/bar", "gross_bp"), ("PUB net bp/bar", "net_bp_PUB"), ("PB net bp/bar", "net_bp_PB"),
              ("PUB cost bp/bar", "cost_bp_PUB"), ("PUB net + GC/HTB", "net_bp_borrow_PUB"),
              ("gross Sharpe", "sharpe_gross"), ("PUB net Sharpe", "sharpe_net_PUB"),
              ("bars", "bars"), ("entries", "entries"), ("hold bars (variant)", "hold_v"),
              ("long leg bp/trade", "leg_long_bp"), ("short leg bp/trade", "leg_short_bp"),
              ("long leg hold bars", "leg_long_age"), ("long leg bp/bar held", "leg_long_bp_per_bar"),
              ("long leg trades", "leg_long_n"), ("short leg trades", "leg_short_n"))
INT_KEYS = ("bars", "entries", "leg_long_n", "leg_short_n", "trades_v", "inv_trades")
SHARPE_KEYS = ("sharpe_gross", "sharpe_net_PUB", "sharpe_net_PB")


# ------------------------------------------------------------------ the rotation (D348's, on the finite mask)
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


def plan_for(sc):
    fin = np.isfinite(sc)
    rp = rotate_plan(fin)
    rp["fin"] = fin
    return rp


# ------------------------------------------------------------------ the cell (D346's run_cell, exactly) and the percentile grid
def cell_score(P, sig):
    return UF.apply_floor_replace(np.where(P["excl"], np.nan, P["score"](sig)), P["keep"])


def build_gate(P, sig, sc):
    rankT = Y.rank_single({sig: sc}, P["base"], sig, P["n"], P["T"])
    return Y.gate_from(rankT, P["finT"])


def lagged_of(P, sc):
    """d348_prep's `lagged`, on a supplied (n, T) score: base-masked, transposed, lagged one bar -> (T, n)."""
    s = np.where(P["base"], sc, np.nan)
    out = np.full((P["T"], P["n"]), np.nan)
    out[1:] = s[:, :-1].T
    return out


def pct_of(P, sc):
    """The percentile grid of the lagged score: D347's percentile_grid, exactly as the prep caches it."""
    return V47.percentile_grid(lagged_of(P, sc))


def percentile_rebuild(score_T, min_names=50):
    """[PC]'s INDEPENDENT rebuild of percentile_grid: np.unique with counts instead of two searchsorteds.
    below = names strictly smaller, eq = names equal; (below + 0.5 eq) / k * 100 in the same float order."""
    T, n = score_T.shape
    out = np.full((T, n), np.nan)
    for t in range(T):
        v = score_T[t]
        idx = np.flatnonzero(np.isfinite(v))
        k = idx.size
        if k < min_names:
            continue
        _u, inv, cnt = np.unique(v[idx], return_inverse=True, return_counts=True)
        below = np.cumsum(cnt) - cnt
        out[t, idx] = (below[inv] + 0.5 * cnt[inv]) / k * 100.0
    return out


def arm_flags(arm):
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    return arm in ("target", "both"), arm in ("invalidation", "both")


def simulate_both(P, gate, arm, pct, shift=0):
    """Both lenses under one arm's exit. target: D303's target, no grid; invalidation: the grid, no target; both: both."""
    use_target, use_inv = arm_flags(arm)
    inv = pct if use_inv else None
    if use_inv and inv is None:
        raise ValueError(f"arm {arm!r} needs a percentile grid")
    res_v = W.simulate(P["A2"], gate, DEPTH, use_target, slots=True, shift=shift, fill="open", invalidation=inv)
    res_i = W.simulate(P["A2"], gate, DEPTH, use_target, slots=False, shift=shift, fill="open", invalidation=inv)
    return res_v, res_i


def cell_stats(P, res_v, res_i, want_full=False):
    """Every section-3 statistic of one (variant, invariant) pair, flat -- D348's, plus the cost term and the holding
    lengths. Costing via G22.costed per convention, per-leg via V9, borrow via V38.borrow_block as D344 does."""
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
        s[f"cost_bp_{cv}"] = C[cv]["cost_bp"] if C[cv] else nan
        s[f"net_bp_borrow_{cv}"] = BV["gc_htb"][cv]["net_bp_borrow"] if BV else nan
        s[f"inv_net_per_trade_{cv}"] = INV[cv]["net_per_trade"] if INV[cv] else nan
    ok = res_v["mask"]
    s["bars"] = int(ok.sum())
    s["entries"] = int(res_v["ent"][ok].sum())
    s["trades_v"] = len(res_v["trades"])
    s["hold_v"] = float(np.mean([t[2] for t in res_v["trades"]])) if res_v["trades"] else nan
    s["hold_i"] = float(np.mean([t[2] for t in res_i["trades"]])) if res_i["trades"] else nan
    for side, nm in ((0, "long"), (1, "short")):
        L = LEGS["PUB"][side]
        s[f"leg_{nm}_bp"] = L["gross"] if L else nan
        s[f"leg_{nm}_n"] = L["trades"] if L else 0
        s[f"leg_{nm}_net_PUB"] = L["net"] if L else nan
        tr = [t for t in res_i["trades"] if t[4] == side]
        ages = np.array([t[2] for t in tr], float)
        pnl = np.array([t[3] for t in tr], float)
        s[f"leg_{nm}_age"] = float(ages.mean()) if tr else nan
        s[f"leg_{nm}_bp_per_bar"] = float(pnl.sum() / ages.sum()) * 1e4 if tr and ages.sum() > 0 else nan
    s["inv_trades"] = len(res_i["trades"])
    s["degenerate"] = bool(degenerate)
    if want_full:
        return s, dict(C=C, LEGS=LEGS, INV=INV, borrow_variant=BV)
    return s


def identity_worst(sig, k, stats, full, pub):
    """D348's: published D346 values to 0.0 -- PUB and PB net bp/bar, Sharpe, gross, invariant per trade and count,
    both legs' per-trade means, nets and counts."""
    C, LEGS, INV = full["C"], full["LEGS"], full["INV"]
    assert k == 40, "D355 runs k=40 only"
    ref = pub["d346"]["table"]["40"][sig]
    worst = 0.0
    for cv in CONVS:
        worst = max(worst, abs(C[cv]["net_bp"] - ref["variant"][cv]["net_bp_bar"]),
                    abs(C[cv]["sharpe_net"] - ref["variant"][cv]["sharpe_net"]),
                    abs(C[cv]["gross_bp"] - ref["variant"][cv]["gross_bp_bar"]),
                    abs(INV[cv]["net_per_trade"] - ref["invariant"][cv]["net_per_trade"]),
                    abs(INV[cv]["trades"] - ref["invariant"][cv]["trades"]))
        for s in (0, 1):
            L, Lr = LEGS[cv][s], ref["legs"][cv][str(s)]
            worst = max(worst, abs(L["gross"] - Lr["gross"]), abs(L["net"] - Lr["net"]), abs(L["trades"] - Lr["trades"]))
    return worst


def load_published():
    return dict(d346=json.loads(D346_JSON.read_text()))


def cell_rng(cell_index, arm_index, part):
    return np.random.default_rng([W.SEED, STUDY, cell_index, arm_index, part])


def stats_worst(a, b, keys=STATS):
    worst = 0.0
    for k in keys:
        x, y = a.get(k), b.get(k)
        x = float("nan") if x is None else float(x)
        y = float("nan") if y is None else float(y)
        if np.isnan(x) and np.isnan(y):
            continue
        worst = max(worst, abs(x - y))
    return worst


def book_eq(a, b):
    return np.array_equal(np.nan_to_num(np.asarray(a, float), nan=-9e9), np.nan_to_num(np.asarray(b, float), nan=-9e9))


# ------------------------------------------------------------------ the observed cell, all three arms
def observed_cell(P, sig, k, pub, verbose=True, arms=ARMS):
    """The zero-offset cell under every arm. The target arm is asserted equal to the published cell to 0.0 ([ID0]);
    the percentile grid is the prep's cached PCT, asserted equal to a live rebuild ([PC] observed)."""
    W.BASE_HOLD = k
    sc = cell_score(P, sig)
    gate = build_gate(P, sig, sc)
    pct = np.asarray(P["PCT"][sig])
    lag = lagged_of(P, sc)
    assert np.array_equal(lag, np.asarray(P["LAG"][sig]), equal_nan=True), f"[PC] {sig}: lagged score != prep's LAG"
    live = V47.percentile_grid(lag)
    assert np.array_equal(live, pct, equal_nan=True), f"[PC] {sig}: percentile_grid(LAG) != prep's cached PCT"
    out = dict(sc=sc, gate=gate, pct=pct, arms={})
    for arm in arms:
        res_v, res_i = simulate_both(P, gate, arm, pct)
        stats, full = cell_stats(P, res_v, res_i, want_full=True)
        rec = dict(res_v=res_v, res_i=res_i, stats=stats, full=full)
        if arm == "target":
            worst = identity_worst(sig, k, stats, full, pub)
            assert worst < 1e-9, f"[ID0] {sig} k={k}: worst {worst:.2e}"
            rec["worst"] = worst
            if verbose:
                hp, hs = PUBLISHED[(sig, k)]
                print(f"    [ID0] {sig} k={k} target arm: zero-offset cell == D346 to {worst:.1e} -- PUB net {stats['net_bp_PUB']:+.2f} "
                      f"(published {hp:+.2f}), Sharpe {stats['sharpe_net_PUB']:+.3f} (published {hs:.3f}), PB net {stats['net_bp_PB']:+.2f}, "
                      f"{stats['trades_v']:,} trades, {stats['bars']:,} bars; legs {stats['leg_long_bp']:+.1f} / {stats['leg_short_bp']:+.1f} bp")
        elif verbose:
            print(f"          {sig} k={k} {arm:12s}: PUB net {stats['net_bp_PUB']:+.2f}, gross {stats['gross_bp']:+.2f}, cost {stats['cost_bp_PUB']:.2f}, "
                  f"Sharpe {stats['sharpe_net_PUB']:+.3f}, entries {stats['entries']:,}, hold {stats['hold_v']:.1f} bars; "
                  f"legs {stats['leg_long_bp']:+.1f} / {stats['leg_short_bp']:+.1f} bp, long hold {stats['leg_long_age']:.1f}")
        out["arms"][arm] = rec
    return out


# ------------------------------------------------------------------ [IDX] the kernel identity
def gate_order_check(P, gate, pct):
    """Per (side, bar): the slot gate's rank<2 members in gate order vs the kernel's ordering of the same members by
    PCT (longs ascending, ties by row ascending; shorts descending, ties by row descending). Also counts gate members
    whose PCT is NaN, and bars where PCT is undefined (all NaN) yet the gate is non-empty."""
    T = P["T"]
    undefined = ~np.isfinite(pct).any(axis=1)
    n_diff, n_nan, n_und_nonempty, n_pairs = 0, 0, 0, 0
    first_diff = []
    for t in range(1, T):
        for side in (0, 1):
            o = gate["gateO"]
            rows = gate["gateF"][o[side, t]:o[side, t + 1]]
            rks = gate["gateR"][o[side, t]:o[side, t + 1]]
            if undefined[t] and rows.size:
                n_und_nonempty += 1
            top = rows[rks < DEPTH]
            if top.size == 0:
                continue
            n_pairs += 1
            pv = pct[t, top]
            n_nan += int((~np.isfinite(pv)).sum())
            cand = np.sort(top)                                # the kernel's flatnonzero order: row ascending
            keyc = np.where(np.isfinite(pct[t, cand]), pct[t, cand], np.inf if side == 0 else -np.inf)
            oc = np.argsort(keyc, kind="stable")
            kern = cand[oc] if side == 0 else cand[oc[::-1]]
            if not np.array_equal(kern, top):
                n_diff += 1
                if len(first_diff) < 5:
                    first_diff.append((t, side, top.tolist(), kern.tolist(), pct[t, top].tolist()))
    return dict(bars_undefined=int(undefined.sum()), undefined_nonempty=n_und_nonempty, members_nan=n_nan,
                order_diff=n_diff, pairs=n_pairs, first_diff=first_diff)


def repair_order(P, gate, pct):
    """The ordering keys of the rank<2 gate members whose PCT is NaN, repaired -- and NOTHING else.

    THE ONE PLACE THE RANKER AND THE GRID DISAGREE. `rank_columns` masks score[t-1] with base[t]; d348_prep's
    `lagged` masks score[t-1] with base[t-1]. Wherever base[row, t] is True and base[row, t-1] False the name is in
    the gate at t with PCT[t, row] = NaN: at bar 1000 (the first bar of the base, where the whole gate is defined
    and the grid is not) and for single names whose base switches on later. The exit never reads those cells
    (NaN fires nothing) but the kernel orders a NaN key LAST while the gate orders by rank, so two same-bar
    entrants can be inserted in the opposite order and a later per-side np.mean over >= 8 names can differ by an
    ULP. Each such member is asserted to be exactly that case, and given a key that reproduces the gate order and
    can fire no exit (longs stay < 50, shorts > 50). Returns (grid, swapped (t, side, rows), n NaN members)."""
    rep = np.array(pct, float, copy=True)
    base, T = P["base"], P["T"]
    swapped, n_nan = [], 0
    for t in range(1, T):
        for side in (0, 1):
            o = gate["gateO"]
            rows = gate["gateF"][o[side, t]:o[side, t + 1]]
            rks = gate["gateR"][o[side, t]:o[side, t + 1]]
            top = rows[rks < DEPTH]
            if top.size == 0:
                continue
            pv = pct[t, top]
            nanm = ~np.isfinite(pv)
            if not nanm.any():
                continue
            n_nan += int(nanm.sum())
            for r in top[nanm]:
                assert base[r, t] and not base[r, t - 1], f"[IDX] bar {t} side {side} row {r}: NaN PCT on a gate member NOT explained by base[t-1]"
            cand = np.sort(top)
            keyc = np.where(np.isfinite(pct[t, cand]), pct[t, cand], np.inf if side == 0 else -np.inf)
            oc = np.argsort(keyc, kind="stable")
            kern = cand[oc] if side == 0 else cand[oc[::-1]]
            if np.array_equal(kern, top):
                continue
            swapped.append((t, side, top.tolist()))
            assert top.size == 2
            if side == 0:                                          # ascending; keep < 50
                if nanm.all():
                    rep[t, top[0]], rep[t, top[1]] = -1.0, -0.5
                elif nanm[0]:
                    rep[t, top[0]] = pv[1] - 1.0
                else:
                    rep[t, top[1]] = np.nextafter(pv[0], np.inf)
            else:                                                  # descending; keep > 50
                if nanm.all():
                    rep[t, top[0]], rep[t, top[1]] = 101.0, 100.5
                elif nanm[0]:
                    rep[t, top[0]] = np.nextafter(pv[1], np.inf)
                else:
                    rep[t, top[1]] = np.nextafter(pv[0], -np.inf)
    return rep, swapped, n_nan


def kernel_identity(P, sig, sc, pct, use_target=False, verbose=True, label="[IDX]", diagnose=True):
    """With invalidation=PCT, use_target=False, slots=False, the slot simulator equals D345's kernel with
    exit="invalidation" fed rank<2 and PCT as its score:
      (1) ledger, cnt0, cnt1, ent bit-identical on the grid AS CACHED;
      (2) the bars where the gate is non-empty while the grid is undefined are exactly the bars where the prep's
          count (base[t-1]) is < 50 <= the ranker's (base[t]); every gate member with NaN PCT is a name whose base
          switches on at t (asserted inside repair_order);
      (3) with ONLY those members' ordering keys repaired, the slot ledger is unchanged and the kernel equals the
          slot simulator bit-for-bit on ledger, counts, entries AND the per-side book;
      (4) on the raw grid the book's residual bars all lie inside the hold window of a swapped pair; reported in ULPs.
    Raises with a diagnosis."""
    W.BASE_HOLD = 40
    rankT = Y.rank_single({sig: sc}, P["base"], sig, P["n"], P["T"])
    gate = Y.gate_from(rankT, P["finT"])
    sig_gl = np.ascontiguousarray(rankT[0] < DEPTH)
    sig_gs = np.ascontiguousarray(rankT[1] < DEPTH)
    res_ref = W.simulate(P["A2"], gate, DEPTH, use_target, slots=False, fill="open", invalidation=pct)
    res_id = EB.simulate_event(P["A2"], sig_gl, sig_gs, pct, exit="invalidation", cap=40, n_max=None, x_target=X_TARGET, U=U_CAP)
    oc = gate_order_check(P, gate, pct)
    ls_ref, ls_id = V45.ledger_set(res_ref["trades"]), V45.ledger_set(res_id["trades"])
    same1 = (ls_ref == ls_id and np.array_equal(res_id["cnt0"], res_ref["cnt0"]) and np.array_equal(res_id["cnt1"], res_ref["cnt1"])
             and np.array_equal(res_id["ent"], res_ref["ent"]))
    if not same1:
        if diagnose:
            sr, si = set(ls_ref), set(ls_id)
            only_ref, only_id = sorted(sr - si, key=lambda x: x[1]), sorted(si - sr, key=lambda x: x[1])
            ent_diff = np.flatnonzero(res_id["ent"] != res_ref["ent"])
            print(f"    {label} DIAGNOSIS {sig}: ledgers {len(ls_ref):,} (slot) vs {len(ls_id):,} (kernel); only-slot {len(only_ref)}, only-kernel {len(only_id)}; "
                  f"ent differs on {ent_diff.size} bars (first {ent_diff[:5].tolist()})")
            for tr in (only_ref[:3] + only_id[:3]):
                print(f"          trade {tr}: {'slot only' if tr in sr else 'kernel only'}")
        assert same1, f"{label} {sig}: the slot simulator's ledger / counts / entries are NOT identical to D345's kernel"
    # (2) the undefined-grid bars, explained exactly by the two base masks
    base = np.asarray(P["base"])
    n_rank = np.isfinite(np.where(base[:, 1:], sc[:, :-1], np.nan)).sum(axis=0)     # the ranker's count at t = 1..T-1
    n_prep = np.isfinite(np.where(base[:, :-1], sc[:, :-1], np.nan)).sum(axis=0)    # the prep's count at t = 1..T-1
    undefined = ~np.isfinite(pct).any(axis=1)
    nonempty = np.array([(gate["gateO"][0, t + 1] > gate["gateO"][0, t]) or (gate["gateO"][1, t + 1] > gate["gateO"][1, t]) for t in range(1, P["T"])])
    und_ne = np.flatnonzero(undefined[1:] & nonempty) + 1
    expl = np.flatnonzero((n_prep < 50) & (n_rank >= 2 * N_BASE)) + 1
    assert np.array_equal(und_ne, expl), f"{label} {sig}: gate non-empty while PCT undefined on bars {und_ne.tolist()}, base-lag explains {expl.tolist()}"
    # (3) the repaired ordering keys: no exit moves, and the identity is bit-for-bit
    rep, swapped, n_nan = repair_order(P, gate, pct)
    res_ref2 = W.simulate(P["A2"], gate, DEPTH, use_target, slots=False, fill="open", invalidation=rep)
    res_id2 = EB.simulate_event(P["A2"], sig_gl, sig_gs, rep, exit="invalidation", cap=40, n_max=None, x_target=X_TARGET, U=U_CAP)
    assert V45.ledger_set(res_ref2["trades"]) == ls_ref, f"{label} {sig}: repairing the ordering keys moved an exit"
    same3 = (V45.ledger_set(res_id2["trades"]) == ls_ref and np.array_equal(res_id2["cnt0"], res_ref2["cnt0"])
             and np.array_equal(res_id2["cnt1"], res_ref2["cnt1"]) and np.array_equal(res_id2["ent"], res_ref2["ent"])
             and book_eq(res_id2["book_slot"], res_ref2["book"]))
    assert same3, f"{label} {sig}: with the ordering keys repaired the kernel is STILL not bit-identical to the slot simulator"
    # (4) the raw grid's residual
    a, b = np.nan_to_num(res_id["book_slot"], nan=-9e9), np.nan_to_num(res_ref["book"], nan=-9e9)
    bd = np.flatnonzero(a != b)
    max_ulp = float(np.max(np.abs(a[bd] - b[bd]) / np.spacing(np.abs(b[bd])))) if bd.size else 0.0
    inside = all(any(t <= int(x) < t + W.BASE_HOLD for t, _s, _r in swapped) for x in bd)
    assert inside, f"{label} {sig}: the book differs on bars {bd.tolist()} outside every swapped pair's hold window"
    if verbose:
        print(f"    {label} KERNEL IDENTITY {sig}: with invalidation=PCT, use_target=False, slots=False the slot simulator equals D345's kernel "
              f"(exit='invalidation', rank<2, score=PCT) on the ledger ({len(ls_ref):,} trades), cnt0/cnt1 and ent bit-for-bit. "
              f"The grid is undefined on {int(undefined.sum())} bars; the gate is non-empty there on {und_ne.tolist()} -- exactly the bars where the "
              f"prep's base[t-1] count is < 50 <= the ranker's base[t] count. {n_nan} rank<2 gate members carry NaN PCT, every one a name whose base "
              f"switches on at t; the kernel orders {len(swapped)} of those (side, bar) pairs differently from the gate {[(t, s) for t, s, _ in swapped]}. "
              f"With only those ordering keys repaired (no exit moves: ledger unchanged) the kernel equals the slot simulator bit-for-bit, per-side book "
              f"included; on the raw grid the book differs on {bd.size} bars {bd.tolist()} by at most {max_ulp:.0f} ULP, all inside a swapped pair's hold window")
    return dict(res_ref=res_ref, res_id=res_id, order=oc, same=bool(same1 and same3), trades=len(ls_ref), undefined_nonempty=und_ne.tolist(),
                members_nan=n_nan, swapped=swapped, book_diff_bars=bd.tolist(), max_ulp=max_ulp)


# ------------------------------------------------------------------ [X0] exit ordering across arms
def match_ages(trades_by_arm):
    keyed = {arm: {(t[0], t[1], t[4]): t[2] for t in tr} for arm, tr in trades_by_arm.items()}
    common = set(keyed["target"]) & set(keyed["invalidation"]) & set(keyed["both"])
    tb = set(keyed["target"]) & set(keyed["both"])
    ib = set(keyed["invalidation"]) & set(keyed["both"])
    n_gt_t = sum(keyed["both"][k] > keyed["target"][k] for k in tb)
    n_gt_i = sum(keyed["both"][k] > keyed["invalidation"][k] for k in ib)
    n_min = sum(keyed["both"][k] == min(keyed["target"][k], keyed["invalidation"][k]) for k in common)
    n_lt_t = sum(keyed["both"][k] < keyed["target"][k] for k in tb)
    return dict(tb=len(tb), ib=len(ib), common=len(common), gt_t=n_gt_t, gt_i=n_gt_i, eq_min=n_min, lt_t=n_lt_t)


# ------------------------------------------------------------------ the audits
def lag_audit(P, gate, sc, bars):
    """[L] on the gate: the held long set at every sampled bar, rebuilt from score[:, t-1] by V38.rebuild_long_set,
    which never calls rank_single / rank_columns / gate_from. Returns how many bars the UNLAGGED rebuild differs on."""
    base, finT = P["base"], P["finT"]
    n_unl = 0
    for t in bars:
        t = int(t)
        got = set(int(r) for r in V38.gate_rows(gate, 0, t))
        assert got == V38.rebuild_long_set(sc, base, finT, t, 1), f"[L] bar {t}: gate != rebuild from score[:, t-1]"
        n_unl += V38.rebuild_long_set(sc, base, finT, t, 0) != got
    return n_unl


def exit_rebuild(P, pct, use_target, use_inv, trade, cap=40):
    """[L] on the exit: a trade's age re-derived from (row, e0, side) alone -- the summed hedged excess with the open
    fill on the entry bar against X_TARGET x vxT[t], the percentile grid at t (known at the close of t-1), the cap and
    the delisting -- by a loop that never touches the simulator. None if the position never closes."""
    row, e0, _age, _pnl, side = trade
    r1T, mkt, ocT, mkt_oc, vxT, finT, T = P["r1T"], P["mkt"], P["ocT"], P["mkt_oc"], P["A2"]["vxT"], P["finT"], P["T"]
    sgn = 1.0 if side == 0 else -1.0
    cx = sgn * (float(ocT[e0, row]) - float(mkt_oc[e0]))
    for t in range(e0 + 1, T):
        a = t - e0
        trig = False
        if use_target:
            u = float(vxT[t, row])
            if u == u and u > 0.0:
                trig = cx >= X_TARGET * u
        if use_inv:
            s = float(pct[t, row])
            if s == s:
                trig = trig or ((s >= 50.0) if side == 0 else (s <= 50.0))
        if ((trig or a >= cap) and a > 0) or not finT[t, row]:
            return a
        cx += sgn * (float(r1T[t, row]) - float(mkt[t]))
    return None


def exit_audit(P, trades, pct, arm, rng, n=N_EXIT_SAMPLE):
    """Every sampled closed trade's age equals exit_rebuild's; returns (n checked, n differing under the UNLAGGED grid)."""
    use_target, use_inv = arm_flags(arm)
    idx = rng.choice(len(trades), size=min(n, len(trades)), replace=False)
    pct_unl = None
    if use_inv:
        pct_unl = np.full_like(pct, np.nan)
        pct_unl[:-1] = pct[1:]                 # the percentile of the score AT t: an unlagged exit
    n_unl = 0
    for i in idx:
        tr = trades[int(i)]
        got = exit_rebuild(P, pct, use_target, use_inv, tr)
        assert got == tr[2], f"[L] {arm}: trade {tr} age {tr[2]} != re-derived {got}"
        if use_inv:
            n_unl += exit_rebuild(P, pct_unl, use_target, use_inv, tr) != tr[2]
    return int(idx.size), n_unl


def sign_audit(P, res, label):
    """[S] on a ledger: every trade equals the open-fill recomputation; favourable paths pay positively;
    a synthetic +50 bp on one held bar lifts a long trade's P&L by exactly 50 bp and cuts a short trade's by exactly 50 bp."""
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
    iL = next(i for i, t in enumerate(tr) if t[4] == 0 and t[2] >= 2)
    iS = next(i for i, t in enumerate(tr) if t[4] == 1 and t[2] >= 2 and t[0] != tr[iL][0])
    r1p = np.array(r1T, float, copy=True)
    for i in (iL, iS):
        row, e0 = tr[i][0], tr[i][1]
        r1p[e0 + 1, row] += 50e-4
    rec2 = FL.pnl_recomputed_fill([tr[iL], tr[iS]], r1p, mkt, ocT, mkt_oc)
    dL, dS = float(rec2[0] - pnl[iL]), float(rec2[1] - pnl[iS])
    assert abs(dL - 50e-4) < 1e-12 and abs(dS + 50e-4) < 1e-12 and dL * dS < 0, f"[S] {label}: dividend moved long {dL:+.2e}, short {dS:+.2e}"
    return worst, dL * 1e4, dS * 1e4, len(tr)


# ------------------------------------------------------------------ one control-A' draw
def one_draw(P, sig, arm, sc, rp, rng, name_sample, want_pct=False):
    """rotate -> rank_single -> gate_from -> (percentile grid of the ROTATED lagged score, if the arm reads it) ->
    both simulates -> stats. Asserts [N] and [A] on the draw."""
    use_target, use_inv = arm_flags(arm)
    off = draw_offsets(rng, rp["lens"])
    rot = rotate(sc, rp, off)
    big = rp["lens"] >= 100
    frac_nz = float((off[big] != 0).mean()) if big.any() else 1.0
    assert frac_nz > 0.99, f"[N] offsets non-zero on only {100 * frac_nz:.2f}% of names with L >= 100"
    check_rotation(rot, sc, rp["fin"], name_sample)
    gate = build_gate(P, sig, rot)
    t_p = time.time()
    pct = pct_of(P, rot) if use_inv else None
    t_p = time.time() - t_p
    res_v, res_i = simulate_both(P, gate, arm, pct)
    out = dict(off=off, rot=rot, gate=gate, res_v=res_v, res_i=res_i, stats=cell_stats(P, res_v, res_i), frac_nz=frac_nz, pct_s=t_p)
    if want_pct:
        out["pct"] = pct
    return out


# ------------------------------------------------------------------ stages
def stage_selftest(P, draws=3):
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    pub = load_published()
    print("\nASSERTIONS")
    OBS, DRAWS, KID = {}, {}, {}
    for ci, (sig, k) in enumerate(CELLS):
        O = observed_cell(P, sig, k, pub)
        OBS[sig, k] = O
        # [ID0] the keyword absent vs invalidation=None explicitly: identical (trivial); and D348's stored observed block
        tv = O["arms"]["target"]["res_v"]
        rv0 = W.simulate(P["A2"], O["gate"], DEPTH, True, slots=True, fill="open", invalidation=None)
        assert book_eq(rv0["book"], tv["book"]) and V45.ledger_set(rv0["trades"]) == V45.ledger_set(tv["trades"]), "[ID0] invalidation=None != keyword absent"
        f48 = REPO / "data" / D348_CTRL.format(sig=sig, k=k)
        if f48.exists():
            w48 = stats_worst(json.loads(f48.read_text())["observed"], O["arms"]["target"]["stats"], keys=STATS_D348)
            assert w48 < 1e-9, f"[ID0] {sig}: D348's stored observed block differs by {w48:.2e}"
            print(f"    [ID0] {sig} k={k}: invalidation=None == keyword absent (book and ledger); D348's stored observed block "
                  f"({f48.name}) equals the target arm on all {len(STATS_D348)} statistics to {w48:.1e}")
        else:
            print(f"    [ID0] {sig} k={k}: invalidation=None == keyword absent; {f48.name} not on disk, D348 block not compared")
        # [IDX] the kernel identity
        KID[sig, k] = kernel_identity(P, sig, O["sc"], O["pct"])
        # [PC] observed grid == cached (in observed_cell) and == the independent rebuild
        rb = percentile_rebuild(np.asarray(P["LAG"][sig]))
        assert np.array_equal(rb, O["pct"], equal_nan=True), f"[PC] {sig}: independent rebuild != cached PCT"
        # [X0] on the same entries, the both arm exits no later than either single exit
        for lens in ("res_i", "res_v"):
            m = match_ages({a: O["arms"][a][lens]["trades"] for a in ARMS})
            assert m["gt_t"] == 0 and m["gt_i"] == 0, f"[X0] {sig} {lens}: both arm held longer on {m['gt_t']} / {m['gt_i']} matched trades"
            assert m["eq_min"] == m["common"], f"[X0] {sig} {lens}: both != min on {m['common'] - m['eq_min']}"
            print(f"    [X0] {sig} k={k} {'invariant' if lens == 'res_i' else 'variant'}: on {m['tb']:,} entries matched to the target arm and {m['ib']:,} to the "
                  f"invalidation arm, the both arm's age is <= each ({m['lt_t']:,} strictly shorter than the target's); on the {m['common']:,} entries "
                  f"in all three it equals the minimum")
        # control-A' draws per arm
        sc = O["sc"]
        rp = plan_for(sc)
        n_all = np.arange(P["n"])
        for ai, arm in enumerate(ARMS):
            rng = cell_rng(ci, ai, 0)
            DRAWS[sig, k, arm] = []
            ts = time.time()
            for d in range(draws):
                r = one_draw(P, sig, arm, sc, rp, rng, n_all, want_pct=True)      # [A] on ALL names in the selftest
                DRAWS[sig, k, arm].append(r)
            per = (time.time() - ts) / draws
            fr = [r["frac_nz"] for r in DRAWS[sig, k, arm]]
            print(f"    [A] {sig} k={k} {arm}: {draws} draws keep every name's finite count, every bar's finite count and every name's multiset exactly; "
                  f"[N] offsets non-zero on {100 * min(fr):.2f}-{100 * max(fr):.2f}% of names with L >= 100 ({per:.1f} s/draw, "
                  f"grid {np.mean([r['pct_s'] for r in DRAWS[sig, k, arm]]):.1f} s; {el()})")
            st = O["arms"][arm]["stats"]
            print(f"        draws: PUB net " + ", ".join(f"{r['stats']['net_bp_PUB']:+.2f}" for r in DRAWS[sig, k, arm]) +
                  f" vs observed {st['net_bp_PUB']:+.2f}; entries " + ", ".join(f"{r['stats']['entries']}" for r in DRAWS[sig, k, arm]) +
                  f" vs {st['entries']}; long leg " + ", ".join(f"{r['stats']['leg_long_bp']:+.1f}" for r in DRAWS[sig, k, arm]) + f" vs {st['leg_long_bp']:+.1f}")
        # [PC] the rotated grid equals the independent rebuild on the 3 invalidation-arm draws
        for r in DRAWS[sig, k, "invalidation"]:
            rb = percentile_rebuild(lagged_of(P, r["rot"]))
            assert np.array_equal(rb, r["pct"], equal_nan=True), f"[PC] {sig}: rotated grid != independent rebuild"
            assert not np.array_equal(r["pct"], O["pct"], equal_nan=True), f"[PC] {sig}: the rotated grid equals the observed one"
        print(f"    [PC] {sig} k={k}: the observed grid equals the prep's cached PCT and an independent np.unique rebuild bit-for-bit; "
              f"the grid of the rotated score equals the independent rebuild on {draws} draws and differs from the observed grid")
    # [5] vectorised == np.roll loop
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
    print(f"    [5] the vectorised rotation equals the np.roll loop bit-identically: 3 draws on each cell's real score, 20 on a tie-heavy synthetic")
    # [L] lag audit: the gate on the observed and one rotated book; the exit re-derived on the target and invalidation arms
    sig, k = CELLS[0]
    O = OBS[sig, k]
    lag_rng = np.random.default_rng([W.SEED, STUDY, 7])
    R1 = DRAWS[sig, k, "invalidation"][0]
    for lab, gate, sc in (("observed", O["gate"], O["sc"]), ("rotated", R1["gate"], R1["rot"])):
        nonempty = np.array([t for t in range(1, P["T"]) if V38.gate_rows(gate, 0, t).size > 0])
        bars = lag_rng.choice(nonempty, size=N_LAG_BARS, replace=False)
        n_unl = lag_audit(P, gate, sc, bars)
        assert n_unl > N_LAG_BARS // 2, f"[L] {lab}: unlagged rebuild differs on only {n_unl}"
        print(f"    [L] LAG AUDIT gate ({lab} {sig} k={k}): the long gate equals the rebuild from score[:, t-1] on all {N_LAG_BARS} sampled bars; "
              f"the unlagged rebuild differs on {n_unl}")
    ex_rng = np.random.default_rng([W.SEED, STUDY, 8])
    n_unl_inv = None
    for arm in ("target", "invalidation"):
        for lab, rec, pct in (("observed", O["arms"][arm], O["pct"]), ("rotated", DRAWS[sig, k, arm][0], DRAWS[sig, k, arm][0].get("pct"))):
            for lens in ("res_i", "res_v"):
                n_chk, n_unl = exit_audit(P, rec[lens]["trades"], pct, arm, ex_rng)
                if arm == "invalidation":
                    assert n_unl > n_chk // 2, f"[L] {arm} {lab} {lens}: the unlagged grid re-derives the same exit on all but {n_unl}"
                    if lab == "observed" and lens == "res_i":
                        n_unl_inv = n_unl
                print(f"    [L] LAG AUDIT exit ({lab} {sig} {arm} {'invariant' if lens == 'res_i' else 'variant'}): {n_chk} sampled trades' ages equal the "
                      f"re-derivation from (row, e0, side) and the lagged inputs" + (f"; the UNLAGGED grid differs on {n_unl}" if arm == "invalidation" else ""))
    # [S] sign in money on the invalidation-arm ledgers, both lenses (observed and rotated)
    for lab, rec in (("observed", O["arms"]["invalidation"]), ("rotated", R1)):
        for lens in ("res_i", "res_v"):
            worst, dL, dS, ntr = sign_audit(P, rec[lens], f"{lab} invalidation {lens}")
            print(f"    [S] SIGN IN MONEY ({lab} {sig} invalidation, {'invariant' if lens == 'res_i' else 'variant'}): {ntr:,} trades equal the open-fill "
                  f"recomputation to {worst:.1e}; favourable paths pay positively; a +50 bp held-bar move lifts a long {dL:+.1f} bp and a short {dS:+.1f} bp")
    # [6] the audits raise
    broke = False
    try:
        rv, ri = simulate_both(P, O["gate"], "both", O["pct"] + 1.0)           # the target arm handed a perturbed grid
        st, full = cell_stats(P, rv, ri, want_full=True)
        assert identity_worst(sig, k, st, full, pub) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] [ID0] did not raise on a perturbed grid"
    broke = False
    try:
        kernel_identity(P, sig, O["sc"], O["pct"], use_target=True, verbose=False, label="[6/IDX]", diagnose=False)
    except AssertionError:
        broke = True
    assert broke, "[6] [IDX] did not raise with use_target=True left on"
    broke = False
    try:
        sc_unl = np.full_like(O["sc"], np.nan)
        sc_unl[:, :-1] = O["sc"][:, 1:]
        gate_unl = build_gate(P, sig, sc_unl)
        lag_audit(P, gate_unl, O["sc"], bars)
    except AssertionError:
        broke = True
    assert broke, "[6] [L] did not raise on the unlagged gate"
    broke = False
    try:
        pct_unl = np.full_like(O["pct"], np.nan)
        pct_unl[:-1] = O["pct"][1:]
        exit_audit(P, O["arms"]["invalidation"]["res_i"]["trades"], pct_unl, "invalidation", np.random.default_rng(1))
    except AssertionError:
        broke = True
    assert broke, "[6] [L] exit did not raise on the unlagged grid"
    broke = False
    try:
        check_rotation(np.roll(O["sc"], 7, axis=1), O["sc"], np.isfinite(O["sc"]), range(P["n"]))
    except AssertionError:
        broke = True
    assert broke, "[6] [A] did not raise on a whole-panel roll"
    print(f"    [6] [ID0] raises on a grid perturbed by +1; [IDX] raises with use_target=True left on (the ledger differs); "
          f"[L] raises on a gate fed the unlagged score and on an exit fed the unlagged grid ({n_unl_inv} of the sampled trades move); [A] raises on a whole-panel np.roll")
    # [P] the report identity, on this process's own record
    rec = json.loads(json.dumps(clean(O["arms"]["invalidation"]["stats"])))
    worst_p = stats_worst(rec, O["arms"]["invalidation"]["stats"])
    assert worst_p < 1e-9, f"[P] {worst_p:.2e}"
    print(f"    [P] a stored observed statistics dict round-trips through JSON and equals the live one to {worst_p:.1e}")
    print(f"\nOK  assertions pass  ({el()})  {PR.rss_line()}")


def stage_cell(P, sig, k, arm, draws, part):
    t0 = time.time()
    pub = load_published()
    ci, ai = CELLS.index((sig, k)), ARMS.index(arm)
    print("\nASSERTIONS")
    O = observed_cell(P, sig, k, pub, arms=("target", arm) if arm != "target" else ("target",))
    if arm != "target":
        kernel_identity(P, sig, O["sc"], O["pct"])
    sc = O["sc"]
    rp = plan_for(sc)
    rng = cell_rng(ci, ai, part)
    name_rng = np.random.default_rng([W.SEED, STUDY, 99, ci, ai, part])
    REC = {s: [] for s in STATS}
    n_deg = 0
    ts = time.time()
    print(f"\n  {sig} k={k} arm {arm} part {part}: {draws} control-A' draws, RNG [{W.SEED}, {STUDY}, {ci}, {ai}, {part}]")
    for d in range(draws):
        names = name_rng.choice(P["n"], size=N_NAME_SAMPLE, replace=False)
        r = one_draw(P, sig, arm, sc, rp, rng, names)
        s = r["stats"]
        n_deg += int(s["degenerate"])
        for key in STATS:
            REC[key].append(s[key])
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {d + 1}/{draws} ({time.time() - ts:.0f}s, {(time.time() - ts) / (d + 1):.2f} s/draw)", flush=True)
    OS = O["arms"][arm]["stats"]
    out = dict(cell=f"{sig}:{k}", sig=sig, k=k, arm=arm, cell_index=ci, arm_index=ai, part=part, draws=draws,
               seed=[W.SEED, STUDY, ci, ai, part], observed=OS, identity_worst=O["arms"]["target"]["worst"],
               degenerate_draws=n_deg, elapsed_s=time.time() - ts, per_draw=REC)
    f = REPO / "data" / CTRL.format(sig=sig, k=k, arm=arm, part=part)
    f.write_text(json.dumps(clean(out)))
    A = np.array(REC["net_bp_PUB"], float)
    print(f"  wrote {f.name}: PUB net observed {OS['net_bp_PUB']:+.2f} vs control A' p50 {np.nanmedian(A):+.2f} p95 {np.nanquantile(A, .95):+.2f} "
          f"max {np.nanmax(A):+.2f}; long leg observed {OS['leg_long_bp']:+.1f} vs A' p50 {np.nanmedian(REC['leg_long_bp']):+.1f}; "
          f"{n_deg} degenerate draws ({time.time() - t0:.0f}s)  {PR.rss_line()}")


def dist_of(arr, obs):
    a = np.asarray(arr, float)
    fin = a[np.isfinite(a)]
    if fin.size == 0:
        return dict(p50=None, p95=None, max=None, draws=0, below=None, p=None)
    return dict(p50=float(np.median(fin)), p95=float(np.quantile(fin, .95)), max=float(fin.max()), draws=int(fin.size),
                below=(float((fin < obs).mean()) if obs is not None and np.isfinite(obs) else None),
                p=float((fin >= obs).sum() + 1) / (fin.size + 1) if obs is not None and np.isfinite(obs) else None)


def stage_report(P):
    t0 = time.time()
    pub = load_published()
    print("\nASSERTIONS")
    REPORT, KID = {}, {}
    for ci, (sig, k) in enumerate(CELLS):
        O = observed_cell(P, sig, k, pub)
        KID[sig, k] = kernel_identity(P, sig, O["sc"], O["pct"])
        for arm in ARMS:
            obs = O["arms"][arm]["stats"]
            parts = sorted((REPO / "data").glob(CTRL.format(sig=sig, k=k, arm=arm, part="*")))
            if not parts:
                print(f"    [P] {sig} k={k} {arm}: no control-A' parts on disk -- the arm is reported without control A'")
                A = None
            else:
                worst = 0.0
                recs = {s: [] for s in STATS}
                n_draws, n_deg = 0, 0
                for pth in parts:
                    pj = json.loads(pth.read_text())
                    assert pj.get("arm") == arm, f"[P] {pth.name} is arm {pj.get('arm')!r}"
                    worst = max(worst, stats_worst(pj["observed"], obs))
                    for s in STATS:
                        recs[s].extend(pj["per_draw"][s])
                    n_draws += pj["draws"]
                    n_deg += pj.get("degenerate_draws", 0)
                assert worst < 1e-9, f"[P] {sig} k={k} {arm}: a stored observed statistic differs from the re-simulated one by {worst:.2e}"
                print(f"    [P] {sig} k={k} {arm}: {len(parts)} part(s), {n_draws} draws; every stored observed statistic equals the re-simulated one to {worst:.1e}")
                A = {s: np.array([np.nan if v is None else v for v in recs[s]], float) for s in STATS}
                A["_n"], A["_deg"], A["_parts"] = n_draws, n_deg, [p.name for p in parts]
            ts = time.time()
            W.BASE_HOLD = k
            by_shift = {}
            for s_ in range(1, N_BASE):
                rv, ri = simulate_both(P, O["gate"], arm, O["pct"], shift=s_)
                by_shift[s_] = cell_stats(P, rv, ri)
            RR = {s: np.array([by_shift[s_][s] for s_ in sorted(by_shift)], float) for s in STATS}
            print(f"    rank rotation {sig} k={k} {arm}: {len(by_shift)} distinct shifts ({time.time() - ts:.0f}s)")
            REPORT[sig, k, arm] = dict(observed=obs, A=A, RR=RR)
        REPORT[sig, k] = dict(identity_worst=O["arms"]["target"]["worst"], kernel=KID[sig, k]["same"], kernel_trades=KID[sig, k]["trades"],
                              kernel_detail={key: KID[sig, k][key] for key in ("undefined_nonempty", "members_nan", "swapped", "book_diff_bars", "max_ulp")})

    # ---- the tables ---------------------------------------------------------------------------------------
    def fmt_of(key):
        return "%10.3f" if key in SHARPE_KEYS else ("%10d" if key in INT_KEYS else "%10.2f")

    for sig, k in CELLS:
        hp, hs = PUBLISHED[(sig, k)]
        print("\n" + "=" * 132)
        print(f"{sig} k={k}  (published PUB net {hp:+.2f}, Sharpe {hs:.3f}; target arm == D346 to {REPORT[sig, k]['identity_worst']:.1e}; "
              f"kernel identity {'holds' if REPORT[sig, k]['kernel'] else 'FAILS'})")
        print("=" * 132)
        print("  %-22s %12s %12s %12s" % ("statistic", *ARMS))
        for lab, key in TABLE_ROWS:
            f_ = lambda v: (fmt_of(key) % v).strip() if v is not None and np.isfinite(v) else "--"
            print("  %-22s %12s %12s %12s" % (lab, *[f_(REPORT[sig, k, a]["observed"][key]) for a in ARMS]))
        for arm in ARMS:
            Rp = REPORT[sig, k, arm]
            obs, A, RR = Rp["observed"], Rp["A"], Rp["RR"]
            print(f"\n  -- {sig} k={k} arm {arm}: control A' {A['_n'] if A else 0} draws, {A['_deg'] if A else 0} degenerate; rank rotation {RR['gross_bp'].size} shifts")
            print("  %-22s %10s | %10s %10s %10s %8s | %10s %10s %10s %10s" % ("statistic", "observed", "A' p50", "A' p95", "A' max", "A' below",
                                                                                "rank p50", "rank p95", "rank max", "above k/24"))
            Rp["table"] = {}
            for lab, key in TABLE_ROWS:
                o = obs[key]
                dA = dist_of(A[key], o) if A else None
                dR = dist_of(RR[key], o)
                above_r = int((RR[key][np.isfinite(RR[key])] < o).sum())
                Rp["table"][key] = dict(observed=o, control_A=dA, rank_rotation=dict(dR, above_k=above_r, of=int(np.isfinite(RR[key]).sum())))
                fmt = fmt_of(key)
                f_ = lambda v: (fmt % v) if v is not None and np.isfinite(v) else "%10s" % "--"
                print("  %-22s %s | %s %s %s %8s | %s %s %s %10s" % (
                    lab, f_(o), f_(dA["p50"]) if dA else "%10s" % "--", f_(dA["p95"]) if dA else "%10s" % "--", f_(dA["max"]) if dA else "%10s" % "--",
                    (f"{100 * dA['below']:.1f}%" if dA and dA["below"] is not None else "--"),
                    f_(dR["p50"]), f_(dR["p95"]), f_(dR["max"]), f"{above_r} of {int(np.isfinite(RR[key]).sum())}"))

    # ---- predictions --------------------------------------------------------------------------------------
    def ob(c, arm, key):
        return REPORT[c[0], c[1], arm]["observed"][key]

    def A_p95(c, arm, key):
        A = REPORT[c[0], c[1], arm]["A"]
        d = dist_of(A[key], ob(c, arm, key)) if A else None
        return d["p95"] if d and d["p95"] is not None else None

    def R_p95(c, arm, key):
        return dist_of(REPORT[c[0], c[1], arm]["RR"][key], None)["p95"]

    def gt(a, b):
        return a is not None and b is not None and np.isfinite(a) and np.isfinite(b) and a > b

    q = {}
    q["Q1"] = bool(all(gt(ob(c, "invalidation", "net_bp_PUB"), ob(c, "target", "net_bp_PUB")) for c in CELLS))
    q["Q2"] = bool(all(gt(ob(c, "invalidation", "net_bp_PUB"), A_p95(c, "invalidation", "net_bp_PUB")) and
                       gt(ob(c, "invalidation", "net_bp_PUB"), R_p95(c, "invalidation", "net_bp_PUB")) for c in CELLS))
    q["Q3"] = bool(all(ob(c, "invalidation", "entries") >= 2 * ob(c, "target", "entries") for c in CELLS))
    dG = {c: ob(c, "invalidation", "gross_bp") - ob(c, "target", "gross_bp") for c in CELLS}
    dC = {c: ob(c, "invalidation", "cost_bp_PUB") - ob(c, "target", "cost_bp_PUB") for c in CELLS}
    q["Q4"] = bool(all(dG[c] > dC[c] for c in CELLS))
    q["Q5"] = bool(all(ob(c, "invalidation", "leg_long_bp") < ob(c, "target", "leg_long_bp") and
                       ob(c, "invalidation", "leg_long_bp_per_bar") > ob(c, "target", "leg_long_bp_per_bar") for c in CELLS))
    q["Q6"] = bool(all(gt(ob(c, "invalidation", "sharpe_net_PUB"), ob(c, "target", "sharpe_net_PUB")) for c in CELLS))
    q["Q7"] = bool(all(min(ob(c, "target", "net_bp_PUB"), ob(c, "invalidation", "net_bp_PUB")) < ob(c, "both", "net_bp_PUB")
                       < max(ob(c, "target", "net_bp_PUB"), ob(c, "invalidation", "net_bp_PUB")) for c in CELLS))
    check = bool(all(REPORT[c]["identity_worst"] < 1e-9 and REPORT[c]["kernel"] for c in CELLS))
    CF = lambda b: "CONFIRMED" if b else "FALSIFIED"
    fs = lambda v: f"{v:+.2f}" if v is not None and np.isfinite(v) else "--"
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) invalidation PUB net > target PUB net on both cells: {CF(q['Q1'])} -- " +
          ", ".join(f"{c[0]} {fs(ob(c, 'invalidation', 'net_bp_PUB'))} vs {fs(ob(c, 'target', 'net_bp_PUB'))}" for c in CELLS))
    print(f"  Q2 invalidation PUB net above p95 of BOTH nulls on both cells: {CF(q['Q2'])} -- " +
          ", ".join(f"{c[0]} {fs(ob(c, 'invalidation', 'net_bp_PUB'))} vs A' p95 {fs(A_p95(c, 'invalidation', 'net_bp_PUB'))} / rank p95 {fs(R_p95(c, 'invalidation', 'net_bp_PUB'))}" for c in CELLS))
    print(f"  Q3 entries at least double under invalidation on both cells: {CF(q['Q3'])} -- " +
          ", ".join(f"{c[0]} {ob(c, 'invalidation', 'entries'):,} vs {ob(c, 'target', 'entries'):,} ({ob(c, 'invalidation', 'entries') / max(ob(c, 'target', 'entries'), 1):.2f}x)" for c in CELLS))
    print(f"  Q4 edge-sharpening, not cost-cutting: gross rises by more than cost rises on both cells: {CF(q['Q4'])} -- " +
          ", ".join(f"{c[0]} d gross {dG[c]:+.2f} vs d cost {dC[c]:+.2f}" for c in CELLS) + "  (cost = gross - PUB net, so this is Q1's inequality restated in its two terms)")
    print(f"  Q5 long leg: mean per trade FALLS and mean per bar held RISES under invalidation on both cells: {CF(q['Q5'])} -- " +
          ", ".join(f"{c[0]} per trade {fs(ob(c, 'invalidation', 'leg_long_bp'))} vs {fs(ob(c, 'target', 'leg_long_bp'))}, per bar {fs(ob(c, 'invalidation', 'leg_long_bp_per_bar'))} vs {fs(ob(c, 'target', 'leg_long_bp_per_bar'))}" for c in CELLS))
    print(f"  Q6 (against) PUB net Sharpe rises on both cells: {CF(q['Q6'])} -- " +
          ", ".join(f"{c[0]} {ob(c, 'invalidation', 'sharpe_net_PUB'):+.3f} vs {ob(c, 'target', 'sharpe_net_PUB'):+.3f}" for c in CELLS))
    print(f"  Q7 the both arm's PUB net sits strictly between the other two on both cells: {CF(q['Q7'])} -- " +
          ", ".join(f"{c[0]} target {fs(ob(c, 'target', 'net_bp_PUB'))} / both {fs(ob(c, 'both', 'net_bp_PUB'))} / invalidation {fs(ob(c, 'invalidation', 'net_bp_PUB'))}" for c in CELLS))
    print(f"  check: target arm == D346 to 0.0 and the slot simulator's invalidation exit == D345's kernel bit-for-bit: {CF(check)} -- " +
          ", ".join(f"{c[0]} worst {REPORT[c]['identity_worst']:.1e}, kernel {'==' if REPORT[c]['kernel'] else '!='} ({REPORT[c]['kernel_trades']:,} trades)" for c in CELLS))
    stop = ("Q1 and Q2 hold: the invalidation construction is the candidate D357 reads, as a NEW candidate entry, and D356's secondary arm"
            if q["Q1"] and q["Q2"] else "Q1 fails: the target stays; D357 reads the declared cell" if not q["Q1"]
            else "Q1 held, Q2 failed: the invalidation arm earns more and is inside a null it must clear; the target stays")
    print(f"  stop condition (section 5): {stop}")

    def arm_block(sig, k, arm):
        Rp = REPORT[sig, k, arm]
        return dict(observed=Rp["observed"],
                    control_A=(dict(draws=Rp["A"]["_n"], degenerate=Rp["A"]["_deg"], parts=Rp["A"]["_parts"],
                                    dist={s: dist_of(Rp["A"][s], Rp["observed"][s]) for s in STATS}) if Rp["A"] else None),
                    rank_rotation=dict(shifts=int(Rp["RR"]["gross_bp"].size),
                                       dist={s: dist_of(Rp["RR"][s], Rp["observed"][s]) for s in STATS},
                                       per_shift={s: Rp["RR"][s] for s in STATS}),
                    table=Rp["table"])

    out = dict(note="D355: the invalidation exit (the lagged percentile of the ranked score crossing 50) beside D303's target on the two "
                    "k=40 candidate cells, three arms, both lenses; control A' (per-name time rotation with the grid recomputed from the "
                    "rotated score) and the 24-shift rank rotation per arm. Variant bp/bar and invariant per trade never compared. "
                    "Nothing promoted; the book is empty.",
               cells={f"{sig}:{k}": dict(identity_worst=REPORT[sig, k]["identity_worst"], kernel_identity=REPORT[sig, k]["kernel"],
                                         kernel_trades=REPORT[sig, k]["kernel_trades"], kernel_detail=REPORT[sig, k]["kernel_detail"],
                                         published=dict(net_bp_PUB=PUBLISHED[(sig, k)][0], sharpe_net_PUB=PUBLISHED[(sig, k)][1]),
                                         arms={arm: arm_block(sig, k, arm) for arm in ARMS})
                      for sig, k in CELLS},
               arms=list(ARMS), statistics=list(STATS), predictions=q, identity_check=check, stop_condition=stop,
               deltas={f"{sig}:{k}": dict(gross=dG[(sig, k)], cost_PUB=dC[(sig, k)]) for sig, k in CELLS})
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)  {PR.rss_line()}")


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
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    print("D355  the invalidation exit on the candidate books -- target / invalidation / both, control A' with the grid recomputed, rank rotation")
    P = PR.prep(need_grids=False)
    missing = [k for k in PREP_KEYS if k not in P]
    if missing:
        print(f"prep() is missing keys the runner needs: {missing}")
        return 2
    print(f"  prep ready: panel {P['finT'].shape} ({time.time() - t0:.0f}s)")
    if a.selftest:
        stage_selftest(P, draws=3)
    elif a.cell:
        if not a.arm:
            ap.error("--cell needs --arm")
        sig, k = a.cell.split(":")
        k = int(k)
        if (sig, k) not in CELLS:
            ap.error(f"--cell must be one of {CELLS}")
        stage_cell(P, sig, k, a.arm, a.draws, a.part)
    elif a.report:
        stage_report(P)
    else:
        ap.error("one of --selftest, --cell SIG:K --arm A, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
