"""D356 -- the `rsi` and `hist_L` k=40 slot books as a 50/50 capital portfolio: one blend, two arms, the covariance measured.

    uv run python scripts/run_d356_blend.py --selftest [--arm target|invalidation]
    uv run python scripts/run_d356_blend.py --null --arm target --draws 100 --part 0        (one process per part)
    uv run python scripts/run_d356_blend.py --report [--arm target|invalidation|both-arms]

Both parents are rebuilt exactly as D346's `run_cell` does, via D348's `observed_cell` ([ID] to 0.0 against
`data/d346_legs_floor_open.json`). The blend is `0.5 * (book_rsi + book_histL)` on the bars both books report
([M]: the two masks coincide); gross is the mean of that series; cost per bar is the mean of the two books' OWN
`G22.costed` cost per bar (each parent priced on its own ledger -- a merged ledger is never re-priced); net =
gross - cost; vol = std(ddof=1); net Sharpe = net / vol * sqrt(252). Beside it the arithmetic prediction
`Sharpe_pred = 0.5 (net_a + net_b) / sqrt(0.25 (v_a^2 + v_b^2 + 2 rho v_a v_b)) * sqrt(252)`.

MAX DRAWDOWN -- one definition for parents and blend alike: the cumulative sum of the NET per-bar series in bp
(`book * 1e4 - cost_bp` per convention), peak-to-trough. `G22.costed` reports the GROSS cumsum drawdown; that
number is also carried (`maxdd_gross_bp`) for every book, but Q3 reads the net one, PUB.

Arms: `target` (the published exit; the primary arm; depends on nothing but `W.simulate`'s published signature)
and `invalidation` (D355's construction: `use_target=False, invalidation=PCT[sig]`, both parents; it needs the
`invalidation=` keyword on `run_d306_width_exits.simulate` and raises a clear message when the keyword is absent).
Under the invalidation arm's null the percentile grid is recomputed from the ROTATED score (D355 section 3).

Nulls: 100 paired time-rotation draws in two parts -- parent 0 (`rsi`) rotated with rng `[SEED, 356, 0, part]`,
parent 1 (`hist_L`) with `[SEED, 356, 1, part]`, each rotation D348's (`rotate`, `check_rotation` [A]), each gate
and book rebuilt, the pair blended the same way; and the 24 rank rotations paired shift-for-shift in `--report`.

ASSERTIONS [K][F0][R][ID][M][LIN][V][T][A][6] -- pre-reg section 5; [P] the stored observed record equals the live one.
"""

from __future__ import annotations

import argparse
import importlib.util
import inspect
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


PREP = _load("d348p", "d348_prep.py")                       # the alias chain executes once (memo_load)
V48 = _load("d348r", "run_d348_score_rotation_null.py")     # memoised: binds the same module objects
W, Y, G22, V47 = PREP.W, PREP.Y, PREP.G22, PREP.V47

STUDY = 356
K = 40
PARENTS = (("rsi", K), ("hist_L", K))                       # parent index 0, 1 -- the seed's third element
CONVS = ("PB", "PUB")
ARMS = ("target", "invalidation")
DEPTH = V48.DEPTH
N_BASE = W.N_BASE
N_NAME_SAMPLE = V48.N_NAME_SAMPLE
ANN = 252.0
WORST_FRAC = 0.01
NULL_FILE = "d356_null_{arm}_p{part}.json"
OUT = REPO / "data" / "d356_blend.json"
PUBLISHED = V48.PUBLISHED
# per-draw record, flat
STATS_DRAW = ("net_sharpe_PUB", "net_bp_PUB", "gross_bp", "rho", "vol_bp", "net_sharpe_PB", "net_bp_PB", "maxdd_net_PUB_bp",
              "bars", "a_net_bp_PUB", "b_net_bp_PUB", "a_gross_bp", "b_gross_bp", "a_sharpe_net_PUB", "b_sharpe_net_PUB",
              "a_entries", "b_entries")
NULL_ROWS = (("PUB net Sharpe", "net_sharpe_PUB"), ("PUB net bp/bar", "net_bp_PUB"), ("gross bp/bar", "gross_bp"), ("rho", "rho"),
             ("vol bp/bar", "vol_bp"), ("PB net Sharpe", "net_sharpe_PB"), ("PB net bp/bar", "net_bp_PB"),
             ("PUB maxdd net bp", "maxdd_net_PUB_bp"), ("rsi PUB net bp/bar", "a_net_bp_PUB"), ("hist_L PUB net bp/bar", "b_net_bp_PUB"))


# ------------------------------------------------------------------ the simulator, per arm
def has_invalidation() -> bool:
    return "invalidation" in inspect.signature(W.simulate).parameters


def simulate_slots(P, gate, arm, pct=None, shift=0):
    """The slot-limited (path-variant) book. `target` is D348's `simulate_both` first line, verbatim."""
    if arm == "target":
        return W.simulate(P["A2"], gate, DEPTH, True, slots=True, shift=shift, fill="open")
    if arm != "invalidation":
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    if not has_invalidation():
        raise RuntimeError("--arm invalidation needs the keyword-only `invalidation=` on run_d306_width_exits.simulate (D355); "
                           "this checkout's simulate() has no such parameter. The target arm does not depend on it.")
    if pct is None:
        raise ValueError("the invalidation arm needs the percentile grid")
    return W.simulate(P["A2"], gate, DEPTH, False, slots=True, shift=shift, fill="open", invalidation=pct)


def pct_of(P, sc):
    """d348_prep's `lagged(sig)` -> V47.percentile_grid, on an (n, T) score already floored and excluded (cell_score's
    output). On the observed score this must equal the prep's cached PCT[sig] bit-identically ([PC], selftest)."""
    sc = np.where(P["base"], sc, np.nan)
    out = np.full((P["T"], P["n"]), np.nan)
    out[1:] = sc[:, :-1].T
    return V47.percentile_grid(out)


# ------------------------------------------------------------------ one book's statistics, and the blend
def maxdd_of(x):
    eq = np.cumsum(x)
    return float(np.max(np.maximum.accumulate(eq) - eq))


def parent_stats(P, res_v):
    """G22.costed per convention on the book's own ledger, plus the per-bar series and the one-definition drawdowns.
    None when the draw is degenerate (costed divides by zero on an empty book), as D348 records it."""
    try:
        C = {cv: G22.costed(res_v, P["G4"][cv]) for cv in CONVS}
    except ZeroDivisionError:
        return None
    ok = res_v["mask"]
    bp = res_v["book"][ok] * 1e4
    S = dict(book=res_v["book"], mask=ok, trades=res_v["trades"], cnt0=res_v["cnt0"], cnt1=res_v["cnt1"], C=C, bars=int(ok.sum()),
             entries=int(res_v["ent"][ok].sum()), gross_bp=C["PUB"]["gross_bp"], vol_bp=C["PUB"]["vol_bp"], maxdd_gross_bp=maxdd_of(bp))
    for cv in CONVS:
        c = C[cv]
        S[cv] = dict(gross_bp=c["gross_bp"], cost_bp=c["cost_bp"], net_bp=c["net_bp"], vol_bp=c["vol_bp"], sharpe_net=c["sharpe_net"],
                     maxdd_net_bp=maxdd_of(bp - c["cost_bp"]), maxdd_gross_bp=S["maxdd_gross_bp"], maxdd_gross_G22_bp=c["maxdd_bp"],
                     turnover=c["turnover"], entries=c["entries"], bars=c["bars"], trades=c["trades"])
    return S


def blend(A, B, w=0.5):
    """w * A + (1 - w) * B in capital, on the common mask ([M]). Cost per bar: the same weights over the two books' own
    cost per bar. Scalars only, plus the per-bar net series under '_net' (stripped before writing)."""
    assert np.array_equal(A["mask"], B["mask"]), "[M] the two masks differ"
    m = A["mask"]
    a, b = A["book"][m], B["book"][m]
    bl = (w * a + (1.0 - w) * b)                       # return units, as G22 keeps its book
    blp = bl * 1e4
    rho = float(np.corrcoef(a, b)[0, 1])
    va, vb = A["C"]["PUB"]["vol_bp"], B["C"]["PUB"]["vol_bp"]
    out = dict(w=w, rho=rho, bars=int(m.sum()), gross_bp=float(bl.mean()) * 1e4, vol_bp=float(bl.std(ddof=1)) * 1e4,
               vol_a_bp=va, vol_b_bp=vb, maxdd_gross_bp=maxdd_of(blp), _net={})
    vol_pred = np.sqrt(w * w * va * va + (1.0 - w) ** 2 * vb * vb + 2.0 * w * (1.0 - w) * rho * va * vb)
    out["vol_pred_bp"] = float(vol_pred)
    for cv in CONVS:
        ca, cb = A["C"][cv], B["C"][cv]
        cost = w * ca["cost_bp"] + (1.0 - w) * cb["cost_bp"]
        net = out["gross_bp"] - cost
        net_series = blp - cost
        net_pred = w * ca["net_bp"] + (1.0 - w) * cb["net_bp"]
        out[cv] = dict(gross_bp=out["gross_bp"], cost_bp=cost, net_bp=net, vol_bp=out["vol_bp"],
                       sharpe_net=(net / out["vol_bp"] * np.sqrt(ANN)) if out["vol_bp"] > 0 else 0.0,
                       maxdd_net_bp=maxdd_of(net_series), maxdd_gross_bp=out["maxdd_gross_bp"],
                       net_pred_bp=net_pred, sharpe_pred=(net_pred / vol_pred * np.sqrt(ANN)) if vol_pred > 0 else 0.0)
        out["_net"][cv] = net_series
    return out


def check_lin_v(A, B, BL, rho=None):
    """[LIN]: the blend's net (both conventions) and gross equal the 50/50 arithmetic of the parents' to 1e-12.
    [V]: vol_blend^2 == 0.25 (v_a^2 + v_b^2 + 2 rho v_a v_b) to 1e-9. `rho` overrides the measured one (guard [6])."""
    rho = BL["rho"] if rho is None else rho
    worst_lin = abs(BL["gross_bp"] - 0.5 * (A["C"]["PUB"]["gross_bp"] + B["C"]["PUB"]["gross_bp"]))
    for cv in CONVS:
        worst_lin = max(worst_lin, abs(BL[cv]["net_bp"] - 0.5 * (A["C"][cv]["net_bp"] + B["C"][cv]["net_bp"])))
    assert worst_lin < 1e-12, f"[LIN] blend net/gross differs from the 50/50 arithmetic by {worst_lin:.2e}"
    va, vb = A["C"]["PUB"]["vol_bp"], B["C"]["PUB"]["vol_bp"]
    worst_v = abs(BL["vol_bp"] ** 2 - 0.25 * (va * va + vb * vb + 2.0 * rho * va * vb))
    assert worst_v < 1e-9, f"[V] blend variance differs from the covariance arithmetic by {worst_v:.2e}"
    return worst_lin, worst_v


def summary(BL):
    return {k: v for k, v in BL.items() if not k.startswith("_")}


def parent_summary(S):
    return {k: S[k] for k in ("bars", "entries", "gross_bp", "vol_bp", "maxdd_gross_bp") + CONVS}


# ------------------------------------------------------------------ overlap
def worst_set(v, frac=WORST_FRAC):
    """The worst ceil(frac * N) positions of `v`. Method 1: a stable argsort. Method 2 ([T]): the partition threshold --
    everything strictly below it must be in the set, nothing above it may be, and the size must be exact.
    Returns (indices, n, boundary ties): ties > 0 means the threshold value is shared beyond the cut."""
    v = np.asarray(v, float)
    n = max(1, int(np.ceil(frac * v.size)))
    idx = np.argsort(v, kind="stable")[:n]
    thr = np.partition(v, n - 1)[n - 1]
    s = set(idx.tolist())
    strict = set(np.flatnonzero(v < thr).tolist())
    loose = set(np.flatnonzero(v <= thr).tolist())
    assert len(s) == n and strict <= s <= loose, "[T] the worst set disagrees with the partition threshold"
    assert float(v[idx].max()) == float(thr), "[T] the worst set's largest value is not the threshold"
    return idx, n, len(loose) - n


def occupancy(res, T, n, tag):
    """(2, T, n) bool: name held on side at bar t, rebuilt from the closed-trade ledger (a trade covers [e0, e0 + age)).
    Checked against the simulator's own cnt0/cnt1: the rebuild never exceeds them and falls short only in the tail of
    positions still open at the last bar (D322's `unattributed`)."""
    occ = np.zeros((2, T, n), bool)
    for row, e0, age, _p, side in res["trades"]:
        occ[side, e0:e0 + age, row] = True
    cnt = occ.sum(axis=2)
    first_gap = T
    for side in (0, 1):
        gap = np.asarray(res[f"cnt{side}"], np.int64) - cnt[side]
        assert (gap >= 0).all(), f"[T] {tag}: the ledger claims a position the book never held"
        nz = np.flatnonzero(gap > 0)
        if nz.size:
            first_gap = min(first_gap, int(nz.min()))
    assert first_gap >= T - W.BASE_HOLD - 1, f"[T] {tag}: the occupancy rebuild has a hole at bar {first_gap}, not only the open tail"
    return occ, first_gap


def overlap(P, A, B, labels=("rsi", "hist_L")):
    m = A["mask"]
    assert np.array_equal(m, B["mask"]), "[M]"
    bars = np.flatnonzero(m)
    out = {}
    # worst 1% of bars by gross book value, per parent
    wa, na, ta = worst_set(A["book"][m])
    wb, nb, tb = worst_set(B["book"][m])
    sa, sb = set(wa.tolist()), set(wb.tolist())
    both = sa & sb
    out["bars"] = dict(n_a=na, n_b=nb, shared=len(both), share_a_in_b=len(both) / na, share_b_in_a=len(both) / nb, ties_a=ta, ties_b=tb,
                       worst_a_value_bp=float(A["book"][m][wa].min()) * 1e4, worst_b_value_bp=float(B["book"][m][wb].min()) * 1e4,
                       shared_dates=[P["dates"][int(bars[i])] for i in sorted(both)])
    # worst 1% of trades by pnl, per parent: the names
    TR = {}
    for lab, S in zip(labels, (A, B)):
        pnl = np.array([t[3] for t in S["trades"]], float)
        w, n, ties = worst_set(pnl)
        names = sorted({int(S["trades"][i][0]) for i in w})
        TR[lab] = dict(n=n, ties=ties, names=names, symbols=[P["symbols"][r] for r in names], worst_pnl_bp=float(pnl[w].min()) * 1e4,
                       cut_pnl_bp=float(pnl[w].max()) * 1e4)
    shared = sorted(set(TR[labels[0]]["names"]) & set(TR[labels[1]]["names"]))
    out["trades"] = dict(a=TR[labels[0]], b=TR[labels[1]], shared_names=shared, shared_symbols=[P["symbols"][r] for r in shared],
                         n_shared=len(shared))
    # same name, same side, same bar
    oa, ga = occupancy(A, P["T"], P["n"], labels[0])
    ob, gb = occupancy(B, P["T"], P["n"], labels[1])
    same = oa & ob
    same_bar = same.any(axis=(0, 2))
    opp = (oa[0] & ob[1]) | (oa[1] & ob[0])              # (T, n)
    opp_bar = opp.any(axis=1)
    out["holdings"] = dict(share_bars_same_name_same_side=float(same_bar[m].mean()), share_bars_same_name_opposite_side=float(opp_bar[m].mean()),
                           name_bars_a=int(oa[:, m].sum()), name_bars_b=int(ob[:, m].sum()), name_bars_shared=int(same[:, m].sum()),
                           share_name_bars_a=float(same[:, m].sum() / max(1, oa[:, m].sum())),
                           share_name_bars_b=float(same[:, m].sum() / max(1, ob[:, m].sum())),
                           open_tail_from_bar=dict(a=ga, b=gb))
    return out


def print_overlap(O, labels=("rsi", "hist_L")):
    b, t, h = O["bars"], O["trades"], O["holdings"]
    la, lb = labels
    print(f"  worst {100 * WORST_FRAC:.0f}% of bars (gross): {la} n={b['n_a']} (cut {b['worst_a_value_bp']:+.0f} bp), {lb} n={b['n_b']} "
          f"(cut {b['worst_b_value_bp']:+.0f} bp); shared {b['shared']} -- {la}'s in {lb}'s {100 * b['share_a_in_b']:.1f}%, "
          f"{lb}'s in {la}'s {100 * b['share_b_in_a']:.1f}%; boundary ties {b['ties_a']}/{b['ties_b']}")
    if b["shared_dates"]:
        print(f"      shared dates: " + ", ".join(b["shared_dates"][:12]) + (" ..." if len(b["shared_dates"]) > 12 else ""))
    print(f"  worst {100 * WORST_FRAC:.0f}% of trades (pnl): {la} n={t['a']['n']} over {len(t['a']['names'])} names, {lb} n={t['b']['n']} over "
          f"{len(t['b']['names'])} names; names shared {t['n_shared']}" + (f" [{', '.join(t['shared_symbols'])}]" if t["shared_symbols"] else ""))
    print(f"  same name, same side, same bar: {100 * h['share_bars_same_name_same_side']:.2f}% of bars; name-bars shared {h['name_bars_shared']:,} "
          f"of {h['name_bars_a']:,} ({la}) / {h['name_bars_b']:,} ({lb}); same name OPPOSITE side on {100 * h['share_bars_same_name_opposite_side']:.2f}% of bars")


# ------------------------------------------------------------------ the observed parents and the paired draw
def observed_parents(P, arm, pub, verbose=True):
    """Both parents via D348's observed_cell ([ID] to 0.0 on the target construction), then, for the invalidation arm,
    re-simulated with `use_target=False, invalidation=PCT[sig]` on the same gate."""
    W.BASE_HOLD = K
    OBS = {}
    for sig, k in PARENTS:
        O = V48.observed_cell(P, sig, k, pub, verbose=verbose)
        assert W.BASE_HOLD == K
        if arm == "target":
            res_v = O["res_v"]
        else:
            res_v = simulate_slots(P, O["gate"], arm, P["PCT"][sig])
        S = parent_stats(P, res_v)
        assert S is not None, f"{sig}: the observed {arm} book is degenerate"
        OBS[sig] = dict(sc=O["sc"], gate=O["gate"], res_v=res_v, res_v_target=O["res_v"], S=S, worst=O["worst"], d348_stats=O["stats"])
    return OBS


def observed_blend(P, OBS, verbose=True):
    A, B = OBS["rsi"]["S"], OBS["hist_L"]["S"]
    BL = blend(A, B)
    wl, wv = check_lin_v(A, B, BL)
    if verbose:
        print(f"    [M] the two masks coincide: {BL['bars']:,} bars each, equal element-wise")
        print(f"    [LIN] blend net (PB, PUB) and gross equal 0.5 (a + b) to {wl:.1e}")
        print(f"    [V] blend variance equals 0.25 (v_a^2 + v_b^2 + 2 rho v_a v_b) to {wv:.1e}  (rho {BL['rho']:+.4f}, "
              f"vol {BL['vol_bp']:.3f} vs predicted {BL['vol_pred_bp']:.3f} bp)")
    return BL, wl, wv


def one_paired_draw(P, arm, OBS, rps, rngs, names):
    """Both parents rotated independently, each rebuilt (gate, book; percentile grid from the ROTATED score under the
    invalidation arm), blended the same way. [A] per parent on `names`. None on a degenerate draw."""
    R, fr = {}, []
    for j, (sig, k) in enumerate(PARENTS):
        sc, rp = OBS[sig]["sc"], rps[j]
        off = V48.draw_offsets(rngs[j], rp["lens"])
        rot = V48.rotate(sc, rp, off)
        big = rp["lens"] >= 100
        frac_nz = float((off[big] != 0).mean()) if big.any() else 1.0
        assert frac_nz > 0.99, f"[N] {sig}: offsets non-zero on only {100 * frac_nz:.2f}% of names with L >= 100"
        fr.append(frac_nz)
        V48.check_rotation(rot, sc, rp["fin"], names)                                   # [A]
        gate = V48.build_gate(P, sig, rot)
        pct = pct_of(P, rot) if arm == "invalidation" else None
        S = parent_stats(P, simulate_slots(P, gate, arm, pct))
        if S is None:
            return None
        R[sig] = S
    A, B = R["rsi"], R["hist_L"]
    BL = blend(A, B)
    check_lin_v(A, B, BL)
    rec = dict(net_sharpe_PUB=BL["PUB"]["sharpe_net"], net_bp_PUB=BL["PUB"]["net_bp"], gross_bp=BL["gross_bp"], rho=BL["rho"], vol_bp=BL["vol_bp"],
               net_sharpe_PB=BL["PB"]["sharpe_net"], net_bp_PB=BL["PB"]["net_bp"], maxdd_net_PUB_bp=BL["PUB"]["maxdd_net_bp"], bars=BL["bars"],
               a_net_bp_PUB=A["PUB"]["net_bp"], b_net_bp_PUB=B["PUB"]["net_bp"], a_gross_bp=A["gross_bp"], b_gross_bp=B["gross_bp"],
               a_sharpe_net_PUB=A["PUB"]["sharpe_net"], b_sharpe_net_PUB=B["PUB"]["sharpe_net"], a_entries=A["entries"], b_entries=B["entries"])
    return dict(rec=rec, frac_nz=fr, BL=BL, R=R)


def draw_rngs(part):
    return [np.random.default_rng([W.SEED, STUDY, j, part]) for j in range(len(PARENTS))]


def observed_record(OBS, BL):
    return dict(blend=summary(BL), parents={sig: parent_summary(OBS[sig]["S"]) for sig, _ in PARENTS},
                identity_worst={sig: OBS[sig]["worst"] for sig, _ in PARENTS})


def record_worst(a, b):
    """Largest absolute difference over every numeric leaf shared by two nested records (NaN == NaN)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return max([0.0] + [record_worst(a[k], b[k]) for k in a if k in b])
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return max([0.0] + [record_worst(x, y) for x, y in zip(a, b)])
    if isinstance(a, (int, float, np.floating, np.integer)) and isinstance(b, (int, float, np.floating, np.integer)) \
            and not isinstance(a, bool) and not isinstance(b, bool):
        x, y = float(a), float(b)
        if np.isnan(x) and np.isnan(y):
            return 0.0
        return abs(x - y)
    return 0.0


# ------------------------------------------------------------------ stages
def stage_selftest(P, arm, draws=2):
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    pub = V48.load_published()
    print(f"\nASSERTIONS  (arm {arm})")
    OBS = observed_parents(P, arm, pub)
    # the null path's simulator call reproduces observed_cell's book bit-identically (so [ID] covers the draws' kernel)
    for sig, k in PARENTS:
        rv = simulate_slots(P, OBS[sig]["gate"], "target")
        ref = OBS[sig]["res_v_target"]
        assert np.array_equal(rv["book"], ref["book"], equal_nan=True) and rv["trades"] == ref["trades"] and np.array_equal(rv["mask"], ref["mask"]), \
            f"[ID] {sig}: simulate_slots(target) != observed_cell's res_v"
    print(f"    [ID] simulate_slots('target') reproduces observed_cell's book, mask and ledger bit-identically on both parents ({el()})")
    if arm == "invalidation":
        for sig, k in PARENTS:
            pc = pct_of(P, OBS[sig]["sc"])
            assert np.array_equal(pc, P["PCT"][sig], equal_nan=True), f"[PC] pct_of({sig}) != prep's PCT"
        print(f"    [PC] the percentile grid rebuilt from each parent's observed score equals the prep's cached PCT bit-identically ({el()})")
    BL, wl, wv = observed_blend(P, OBS)
    A, B = OBS["rsi"]["S"], OBS["hist_L"]["S"]
    for sig in ("rsi", "hist_L"):
        S = OBS[sig]["S"]
        for cv in CONVS:
            d = abs(S[cv]["maxdd_gross_bp"] - S[cv]["maxdd_gross_G22_bp"])
            assert d < 1e-6, f"{sig} {cv}: gross maxdd (bp cumsum) vs G22's (return cumsum) differ by {d:.2e}"
    # [T]
    O = overlap(P, A, B)
    print(f"    [T] worst-{100 * WORST_FRAC:.0f}% bar and trade sets agree with an independent partition-threshold construction on both parents "
          f"(boundary ties bars {O['bars']['ties_a']}/{O['bars']['ties_b']}, trades {O['trades']['a']['ties']}/{O['trades']['b']['ties']}); "
          f"the occupancy rebuild from each ledger matches the simulator's cnt0/cnt1 except in the open tail (from bar "
          f"{O['holdings']['open_tail_from_bar']['a']} / {O['holdings']['open_tail_from_bar']['b']} of {P['T']}) ({el()})")
    # [A] paired draws, every name checked
    rps = [V48.plan_for(OBS[sig]["sc"]) for sig, _ in PARENTS]
    rngs = draw_rngs(0)
    n_all = np.arange(P["n"])
    D = []
    for d in range(draws):
        r = one_paired_draw(P, arm, OBS, rps, rngs, n_all)
        assert r is not None, "degenerate selftest draw"
        D.append(r)
    fr = [f for r in D for f in r["frac_nz"]]
    print(f"    [A] {draws} paired draws, RNG [{W.SEED}, {STUDY}, 0|1, 0]: each parent's rotation keeps every name's finite count, every bar's finite "
          f"count and every name's multiset exactly; [N] offsets non-zero on {100 * min(fr):.2f}-{100 * max(fr):.2f}% of names with L >= 100 ({el()})")
    for i, r in enumerate(D):
        print(f"        draw {i}: blend PUB net Sharpe {r['rec']['net_sharpe_PUB']:+.3f}, PUB net {r['rec']['net_bp_PUB']:+.2f} bp/bar, rho {r['rec']['rho']:+.3f}; "
              f"parents PUB net {r['rec']['a_net_bp_PUB']:+.2f} / {r['rec']['b_net_bp_PUB']:+.2f}  (observed blend {BL['PUB']['sharpe_net']:+.3f}, "
              f"{BL['PUB']['net_bp']:+.2f}, rho {BL['rho']:+.3f})")
    # [6] the arithmetic guards raise
    broke = ""
    try:
        check_lin_v(A, B, blend(A, B, w=0.6))
    except AssertionError as e:
        broke = str(e)
    assert broke.startswith("[LIN]"), f"[6] [LIN] did not raise on a 60/40 blend ({broke!r})"
    broke2 = ""
    try:
        check_lin_v(A, B, BL, rho=0.0)
    except AssertionError as e:
        broke2 = str(e)
    assert broke2.startswith("[V]"), f"[6] [V] did not raise with rho replaced by 0 ({broke2!r})"
    print(f"    [6] [LIN] raises on a 60/40 blend ({broke.split(' by ')[-1]}); [V] raises with rho replaced by 0 ({broke2.split(' by ')[-1]})")
    # [P] the stored observed record round-trips
    rec = observed_record(OBS, BL)
    wp = record_worst(json.loads(json.dumps(V48.clean(rec))), rec)
    assert wp < 1e-9, f"[P] {wp:.2e}"
    print(f"    [P] the observed record round-trips through JSON to {wp:.1e}")
    print(f"\nOK  assertions pass  ({el()})")
    print_tables(arm, OBS, BL)
    print("\nOVERLAP")
    print_overlap(O)
    print(f"\n  {PREP.rss_line()}")


def stage_null(P, arm, draws, part):
    t0 = time.time()
    pub = V48.load_published()
    print(f"\nASSERTIONS  (arm {arm})")
    OBS = observed_parents(P, arm, pub)
    BL, wl, wv = observed_blend(P, OBS)
    rps = [V48.plan_for(OBS[sig]["sc"]) for sig, _ in PARENTS]
    rngs = draw_rngs(part)
    name_rng = np.random.default_rng([W.SEED, STUDY, 99, part])
    REC = {s: [] for s in STATS_DRAW}
    n_deg = 0
    ts = time.time()
    print(f"\n  paired time rotation, arm {arm}, part {part}: {draws} draws; rsi RNG [{W.SEED}, {STUDY}, 0, {part}], hist_L RNG [{W.SEED}, {STUDY}, 1, {part}]")
    for d in range(draws):
        names = name_rng.choice(P["n"], size=N_NAME_SAMPLE, replace=False)
        r = one_paired_draw(P, arm, OBS, rps, rngs, names)
        if r is None:
            n_deg += 1
            for key in STATS_DRAW:
                REC[key].append(float("nan"))
        else:
            for key in STATS_DRAW:
                REC[key].append(r["rec"][key])
        if (d + 1) % 5 == 0 or d + 1 == draws:
            print(f"    {d + 1}/{draws} ({time.time() - ts:.0f}s, {(time.time() - ts) / (d + 1):.2f} s/draw)", flush=True)
    out = dict(study=STUDY, arm=arm, part=part, draws=draws, seeds={sig: [W.SEED, STUDY, j, part] for j, (sig, _) in enumerate(PARENTS)},
               observed=observed_record(OBS, BL), lin_worst=wl, v_worst=wv, degenerate_draws=n_deg, elapsed_s=time.time() - ts,
               s_per_draw=(time.time() - ts) / max(1, draws), per_draw=REC)
    f = REPO / "data" / NULL_FILE.format(arm=arm, part=part)
    f.write_text(json.dumps(V48.clean(out)))
    S_ = np.array(REC["net_sharpe_PUB"], float)
    print(f"  wrote {f.name}: blend PUB net Sharpe observed {BL['PUB']['sharpe_net']:+.3f} vs paired null p50 {np.nanmedian(S_):+.3f} "
          f"p95 {np.nanquantile(S_, .95):+.3f} max {np.nanmax(S_):+.3f}; rho observed {BL['rho']:+.3f} vs null p50 {np.nanmedian(REC['rho']):+.3f}; "
          f"{n_deg} degenerate draws ({time.time() - t0:.0f}s)")
    print(f"  {PREP.rss_line()}")


def print_tables(arm, OBS, BL):
    A, B = OBS["rsi"]["S"], OBS["hist_L"]["S"]
    print("\n" + "=" * 128)
    print(f"arm {arm}: the parents and the 50/50 capital blend  (max drawdown: peak-to-trough of the cumulative NET per-bar series, bp; "
          f"'gross dd' is G22's gross cumsum)")
    print("=" * 128)
    print("  %-4s %-14s %9s %9s %9s %9s %11s %11s %11s %7s %8s %7s" % ("conv", "book", "gross", "cost", "net", "vol", "net Sharpe", "maxdd net", "gross dd", "bars", "entries", "trades"))
    for cv in CONVS:
        for lab, S in (("rsi k=40", A), ("hist_L k=40", B)):
            c = S[cv]
            print("  %-4s %-14s %9.3f %9.3f %9.3f %9.3f %11.3f %11.0f %11.0f %7d %8d %7d" % (
                cv, lab, c["gross_bp"], c["cost_bp"], c["net_bp"], c["vol_bp"], c["sharpe_net"], c["maxdd_net_bp"], c["maxdd_gross_bp"], c["bars"], c["entries"], c["trades"]))
        c = BL[cv]
        print("  %-4s %-14s %9.3f %9.3f %9.3f %9.3f %11.3f %11.0f %11.0f %7d %8s %7s" % (
            cv, "blend 50/50", c["gross_bp"], c["cost_bp"], c["net_bp"], c["vol_bp"], c["sharpe_net"], c["maxdd_net_bp"], c["maxdd_gross_bp"], BL["bars"], "--", "--"))
        print("  %-4s %-14s predicted: net %+.3f, vol %.3f (rho %+.4f), net Sharpe %+.3f -> realised minus predicted %+.4f" % (
            cv, "", c["net_pred_bp"], BL["vol_pred_bp"], BL["rho"], c["sharpe_pred"], c["sharpe_net"] - c["sharpe_pred"]))
    print(f"  rho of the gross series: {BL['rho']:+.4f}; vol ratio hist_L / rsi {BL['vol_b_bp'] / BL['vol_a_bp']:.2f}")


def load_null(arm, OBS, BL):
    parts = sorted((REPO / "data").glob(NULL_FILE.format(arm=arm, part="*")))
    if not parts:
        print(f"    [P] arm {arm}: no paired-null parts on disk -- reported without the time-rotation null")
        return None
    live = observed_record(OBS, BL)
    recs = {s: [] for s in STATS_DRAW}
    worst, n, n_deg = 0.0, 0, 0
    for pth in parts:
        pj = json.loads(pth.read_text())
        worst = max(worst, record_worst(pj["observed"], live))
        for s in STATS_DRAW:
            recs[s].extend(pj["per_draw"].get(s, [np.nan] * pj["draws"]))
        n += pj["draws"]
        n_deg += pj.get("degenerate_draws", 0)
    assert worst < 1e-9, f"[P] arm {arm}: a stored observed value differs from the re-simulated one by {worst:.2e}"
    print(f"    [P] arm {arm}: {len(parts)} part(s), {n} paired draws, {n_deg} degenerate; every stored observed value equals the re-simulated one to {worst:.1e}")
    N = {s: np.array([np.nan if v is None else v for v in recs[s]], float) for s in STATS_DRAW}
    N["_n"], N["_deg"], N["_parts"] = n, n_deg, [p.name for p in parts]
    return N


def rank_rotations(P, arm, OBS):
    """The 24 rank rotations paired shift-for-shift: both parents at `shift`, blended."""
    ts = time.time()
    W.BASE_HOLD = K
    rows = {s: [] for s in STATS_DRAW}
    shifts = list(range(1, N_BASE))
    for s_ in shifts:
        R = {}
        for sig, k in PARENTS:
            pct = P["PCT"][sig] if arm == "invalidation" else None
            R[sig] = parent_stats(P, simulate_slots(P, OBS[sig]["gate"], arm, pct, shift=s_))
        if any(R[sig] is None for sig, _ in PARENTS):
            for key in STATS_DRAW:
                rows[key].append(np.nan)
            continue
        A, B = R["rsi"], R["hist_L"]
        BLs = blend(A, B)
        check_lin_v(A, B, BLs)
        rec = dict(net_sharpe_PUB=BLs["PUB"]["sharpe_net"], net_bp_PUB=BLs["PUB"]["net_bp"], gross_bp=BLs["gross_bp"], rho=BLs["rho"], vol_bp=BLs["vol_bp"],
                   net_sharpe_PB=BLs["PB"]["sharpe_net"], net_bp_PB=BLs["PB"]["net_bp"], maxdd_net_PUB_bp=BLs["PUB"]["maxdd_net_bp"], bars=BLs["bars"],
                   a_net_bp_PUB=A["PUB"]["net_bp"], b_net_bp_PUB=B["PUB"]["net_bp"], a_gross_bp=A["gross_bp"], b_gross_bp=B["gross_bp"],
                   a_sharpe_net_PUB=A["PUB"]["sharpe_net"], b_sharpe_net_PUB=B["PUB"]["sharpe_net"], a_entries=A["entries"], b_entries=B["entries"])
        for key in STATS_DRAW:
            rows[key].append(rec[key])
    RR = {s: np.array(rows[s], float) for s in STATS_DRAW}
    RR["_shifts"] = shifts
    print(f"    rank rotation arm {arm}: {len(shifts)} shifts, both parents paired shift-for-shift ({time.time() - ts:.0f}s)")
    return RR


def report_arm(P, arm, pub):
    print(f"\nASSERTIONS  (arm {arm})")
    OBS = observed_parents(P, arm, pub)
    BL, wl, wv = observed_blend(P, OBS)
    A, B = OBS["rsi"]["S"], OBS["hist_L"]["S"]
    O = overlap(P, A, B)
    print(f"    [T] worst-{100 * WORST_FRAC:.0f}% sets agree with the partition-threshold construction (ties bars {O['bars']['ties_a']}/{O['bars']['ties_b']}, "
          f"trades {O['trades']['a']['ties']}/{O['trades']['b']['ties']}); occupancy rebuilt from both ledgers, open tail only")
    N = load_null(arm, OBS, BL)
    RR = rank_rotations(P, arm, OBS)
    obs = dict(net_sharpe_PUB=BL["PUB"]["sharpe_net"], net_bp_PUB=BL["PUB"]["net_bp"], gross_bp=BL["gross_bp"], rho=BL["rho"], vol_bp=BL["vol_bp"],
               net_sharpe_PB=BL["PB"]["sharpe_net"], net_bp_PB=BL["PB"]["net_bp"], maxdd_net_PUB_bp=BL["PUB"]["maxdd_net_bp"], bars=BL["bars"],
               a_net_bp_PUB=A["PUB"]["net_bp"], b_net_bp_PUB=B["PUB"]["net_bp"], a_gross_bp=A["gross_bp"], b_gross_bp=B["gross_bp"],
               a_sharpe_net_PUB=A["PUB"]["sharpe_net"], b_sharpe_net_PUB=B["PUB"]["sharpe_net"], a_entries=A["entries"], b_entries=B["entries"])
    print_tables(arm, OBS, BL)
    print("\nOVERLAP")
    print_overlap(O)
    # nulls table
    print(f"\nNULLS  (paired time rotation {N['_n'] if N else 0} draws, {N['_deg'] if N else 0} degenerate; paired rank rotation {len(RR['_shifts'])} shifts)")
    print("  %-22s %10s | %10s %10s %10s %8s | %10s %10s %10s %10s" % ("statistic", "observed", "time p50", "time p95", "time max", "below", "rank p50", "rank p95", "rank max", "above k/24"))
    table = {}
    for lab, key in NULL_ROWS:
        o = obs[key]
        dN = V48.dist_of(N[key], o) if N else None
        dR = V48.dist_of(RR[key], o)
        above_r = int((RR[key][np.isfinite(RR[key])] < o).sum())
        of_r = int(np.isfinite(RR[key]).sum())
        table[key] = dict(observed=o, time_rotation=dN, rank_rotation=dict(dR, above_k=above_r, of=of_r))
        fmt = "%10.3f" if ("sharpe" in key or key == "rho") else "%10.2f"
        f_ = lambda v: (fmt % v) if v is not None and np.isfinite(v) else "%10s" % "--"
        print("  %-22s %s | %s %s %s %8s | %s %s %s %10s" % (
            lab, f_(o), f_(dN["p50"]) if dN else f_(None), f_(dN["p95"]) if dN else f_(None), f_(dN["max"]) if dN else f_(None),
            (f"{100 * dN['below']:.1f}%" if dN and dN["below"] is not None else "--"), f_(dR["p50"]), f_(dR["p95"]), f_(dR["max"]), f"{above_r} of {of_r}"))
    # predictions (pre-reg section 3)
    better = max(A["PUB"]["sharpe_net"], B["PUB"]["sharpe_net"])
    dN_s = V48.dist_of(N["net_sharpe_PUB"], obs["net_sharpe_PUB"]) if N else None
    q = {}
    q["Q1"] = bool(BL["rho"] < 0.4)
    q["Q2"] = bool(BL["PUB"]["sharpe_net"] > better)
    q["Q3"] = bool(BL["PUB"]["maxdd_net_bp"] < min(A["PUB"]["maxdd_net_bp"], B["PUB"]["maxdd_net_bp"]))
    q["Q4"] = bool(O["bars"]["share_a_in_b"] < 0.25 and O["bars"]["share_b_in_a"] < 0.25 and O["trades"]["n_shared"] <= 3)
    q["Q5"] = bool(dN_s is not None and dN_s["p95"] is not None and BL["PUB"]["sharpe_net"] > dN_s["p95"])
    q["Q6"] = bool(BL["PUB"]["sharpe_net"] - BL["PUB"]["sharpe_pred"] > 0.05)
    check = bool(all(OBS[sig]["worst"] < 1e-9 for sig, _ in PARENTS) and wl < 1e-12 and wv < 1e-9)
    CF = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print(f"\nPREDICTIONS  (arm {arm}{'; the pre-registered predictions are stated for the primary arm' if arm != 'target' else ''})")
    print(f"  Q1 rho of the gross series < 0.4: {CF(q['Q1'])} -- rho {BL['rho']:+.4f}")
    print(f"  Q2 (LOAD-BEARING) blend PUB net Sharpe above the better parent's: {CF(q['Q2'])} -- blend {BL['PUB']['sharpe_net']:+.3f} vs rsi "
          f"{A['PUB']['sharpe_net']:+.3f} / hist_L {B['PUB']['sharpe_net']:+.3f} (published {PUBLISHED[('rsi', K)][1]:.3f} / {PUBLISHED[('hist_L', K)][1]:.3f})")
    print(f"  Q3 blend max drawdown (net PUB) below the smaller parent's: {CF(q['Q3'])} -- blend {BL['PUB']['maxdd_net_bp']:,.0f} vs rsi "
          f"{A['PUB']['maxdd_net_bp']:,.0f} / hist_L {B['PUB']['maxdd_net_bp']:,.0f} bp (gross: {BL['maxdd_gross_bp']:,.0f} vs {A['maxdd_gross_bp']:,.0f} / {B['maxdd_gross_bp']:,.0f})")
    print(f"  Q4 worst-1% bars overlap < 25% and worst-1% trades share <= 3 names: {CF(q['Q4'])} -- bars {100 * O['bars']['share_a_in_b']:.1f}% / "
          f"{100 * O['bars']['share_b_in_a']:.1f}%, names shared {O['trades']['n_shared']}")
    print(f"  Q5 blend PUB net Sharpe above the paired time-rotation null's p95: {CF(q['Q5'])} -- " +
          (f"{BL['PUB']['sharpe_net']:+.3f} vs p95 {dN_s['p95']:+.3f} (p50 {dN_s['p50']:+.3f}, max {dN_s['max']:+.3f}, below {100 * dN_s['below']:.1f}%, {dN_s['draws']} draws)"
           if dN_s and dN_s["p95"] is not None else "no null on disk"))
    print(f"  Q6 (against) blend net Sharpe exceeds the arithmetic prediction by > 0.05: {CF(q['Q6'])} -- realised {BL['PUB']['sharpe_net']:+.3f} vs predicted "
          f"{BL['PUB']['sharpe_pred']:+.3f} (diff {BL['PUB']['sharpe_net'] - BL['PUB']['sharpe_pred']:+.4f})")
    print(f"  check: parents reproduce D346 to 0.0, [LIN] to 1e-12, [V] to 1e-9: {CF(check)} -- worst " +
          ", ".join(f"{sig} {OBS[sig]['worst']:.1e}" for sig, _ in PARENTS) + f"; LIN {wl:.1e}; V {wv:.1e}")
    return dict(arm=arm, observed=observed_record(OBS, BL), published=dict(rsi=PUBLISHED[("rsi", K)], hist_L=PUBLISHED[("hist_L", K)]),
                blend=summary(BL), overlap=O, lin_worst=wl, v_worst=wv,
                time_rotation=(dict(draws=N["_n"], degenerate=N["_deg"], parts=N["_parts"], seeds_note=f"parent j rotated with [{W.SEED}, {STUDY}, j, part]",
                                    dist={s: V48.dist_of(N[s], obs[s]) for s in STATS_DRAW}) if N else None),
                rank_rotation=dict(shifts=RR["_shifts"], dist={s: V48.dist_of(RR[s], obs[s]) for s in STATS_DRAW}, per_shift={s: RR[s] for s in STATS_DRAW}),
                table=table, predictions=q, identity_check=check,
                maxdd_definition="peak-to-trough of the cumulative sum of the NET per-bar series in bp (book*1e4 - cost_bp per convention), the same for parents and blend; "
                                 "maxdd_gross_bp is the gross cumsum (G22's)")


def stage_report(P, arms):
    t0 = time.time()
    pub = V48.load_published()
    R = {arm: report_arm(P, arm, pub) for arm in arms}
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    arms_out = dict(prev.get("arms", {}))
    for arm in arms:
        arms_out[arm] = R[arm]
    out = dict(note="D356: rsi k=40 and hist_L k=40 (D346's cells) as a 50/50 capital blend on the common mask; cost the mean of the two "
                    "books' own G22 cost per bar; drawdown on the net per-bar cumsum for parents and blend alike; overlap of the worst 1% bars, "
                    "worst 1% trades and same-name-same-side holdings; paired time-rotation and paired rank-rotation nulls. Nothing promoted; "
                    "the book is empty.",
               study=STUDY, parents=[f"{s}:{k}" for s, k in PARENTS], primary_arm="target", arms=arms_out, statistics=STATS_DRAW)
    OUT.write_text(json.dumps(V48.clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  (arms {sorted(arms_out)}; {time.time() - t0:.0f}s)")
    print(f"  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--null", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--arm", default="target", help="target (primary) | invalidation | both-arms (--report only)")
    ap.add_argument("--draws", type=int, default=50)
    ap.add_argument("--part", type=int, default=0)
    a = ap.parse_args()
    t0 = time.time()
    print("D356  the rsi and hist_L k=40 books as a 50/50 capital portfolio -- one blend, two arms, the covariance measured")
    if a.arm not in ARMS + ("both-arms",):
        ap.error(f"--arm must be one of {ARMS + ('both-arms',)}")
    if a.arm == "both-arms" and not a.report:
        ap.error("--arm both-arms is for --report only")
    if a.arm in ("invalidation", "both-arms") and not has_invalidation():
        print("run_d306_width_exits.simulate has no `invalidation=` keyword in this checkout (D355 adds it); the invalidation arm cannot run. "
              "The target arm does not depend on it.")
        return 2
    P = PREP.prep(need_grids=False)
    missing = [k for k in V48.PREP_KEYS + ("PCT", "symbols", "dates") if k not in P]
    if missing:
        print(f"prep() is missing keys the runner needs: {missing}")
        return 2
    print(f"  prep ready: panel {P['finT'].shape} ({time.time() - t0:.0f}s); simulate() {'has' if has_invalidation() else 'lacks'} the invalidation keyword")
    if a.selftest:
        stage_selftest(P, a.arm, draws=2)
    elif a.null:
        stage_null(P, a.arm, a.draws, a.part)
    elif a.report:
        stage_report(P, list(ARMS) if a.arm == "both-arms" else [a.arm])
    else:
        ap.error("one of --selftest, --null, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
