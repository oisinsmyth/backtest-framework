"""D354 -- the pair book: a trigger hedged with a basket of the ranking's opposite extreme.

    uv run python scripts/run_d354_pair_book.py --selftest
    uv run python scripts/run_d354_pair_book.py --arm long  --k 2 --exit cap --null N1 --draws 100 --part 0
    uv run python scripts/run_d354_pair_book.py --arm short --trigger SIG/SHAPE --k 2 --exit cap --null N2 --draws 100 --part 0
    uv run python scripts/run_d354_pair_book.py --report [--trigger-short SIG/SHAPE]

Long arm: rev_5/E1 (D350's member, D353's trigger) on name i at t -> long i, short the equal-weight
basket of the three highest-rsi eligible names in the lagged 25-name gate that day (skipping i and
any held name). Short arm: a D352 family member (SIG/S2|S5|S10 -- fresh entry into the top thr% of
the lagged floored percentile -- or rsi/turn) -> short j, long the three lowest-rsi. Exits: the
trigger's cap 40 or invalidation (percentile crosses 50). n_max_pairs in {2, 4}. No market term.

Nulls: N1 rotates each name's trigger events within its eligible bars (partner rule unchanged);
N2 keeps the trigger and draws the basket at random, without replacement, from the same-day
opposite-side gate; N3 randomises the pair ledger's signs (1,000, in --report). Seeds
[SEED, 354, arm, K, null, part]. Stage files data/d354_{arm}_k{K}_{exit}_{null}_p{part}.json;
the report writes data/d354_pair_book.json with Q1..Q7 on the long arm.

ASSERTIONS [K][F0][R] via the shared prep; [ID][L][S][HX][N1][N2][C][SB][V][6] -- pre-reg section 5.
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


PREP = _load("d348p", "d348_prep.py")        # executes D347's alias chain ONCE; take every alias from here
V50 = _load("d350r", "run_d350_long_timing_screen.py")
PB = _load("d354k", "d354_pair_book.py")
V47 = PREP.V47
Y, UF, EB, G22, BR, V9, W = PREP.Y, PREP.UF, PREP.EB, PREP.G22, PREP.BR, PREP.V9, PREP.W

SEED, CAP, N_BASE = V47.SEED, V47.CAP, Y.N_BASE
KS, EXITS, NULLS, ARMS = (2, 4), ("cap", "invalidation"), ("N1", "N2"), ("long", "short")
BASKET, U = 3, 4
LONG_TRIGGER = "rev_5/E1"
SHORT_THR = {"S2": 2.0, "S5": 5.0, "S10": 10.0}
CONVS = V47.CONVS
STAGE = REPO / "data" / "d354_{arm}_k{K}_{exit}_{null}_p{part}.json"
OUT = REPO / "data" / "d354_pair_book.json"
HAS_HEDGED = "hedged_series" in inspect.signature(EB.simulate_event).parameters


# ------------------------------------------------------------------ helpers
def peak_rss_mb():
    try:
        import psutil
        mi = psutil.Process().memory_info()
        return mi.rss / 2**20, (getattr(mi, "peak_wset", 0) or 0) / 2**20
    except ImportError:
        pass
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        h = ctypes.windll.kernel32.GetCurrentProcess()
        if ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb):
            return pmc.WorkingSetSize / 2**20, pmc.PeakWorkingSetSize / 2**20
    try:
        import resource
        return np.nan, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except ImportError:
        return np.nan, np.nan


def rss_line():
    cur, peak = peak_rss_mb()
    return f"rss {cur:,.0f} MB, peak working set {peak:,.0f} MB"


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return clean(o.tolist())
    if isinstance(o, Path):
        return str(o)
    return o


def n3_draws(rng, pnl, draws=1000):
    """N3: random direction on the pair ledger -- `draws` iid sign vectors, as pre-registered and as D347/D349/D350 drew
    it. [C] asserts the mean is within 2 SE of zero: a check that CAN fail (by seed luck on ~5% of cells, which the fixed
    seed makes deterministic and the record would report), not one made true by construction (an antithetic draw was
    tried and reverted: a self-test that cannot fail is worse than none, CLAUDE.md). The negative control below still
    checks that the flip is applied."""
    signs = rng.choice([-1.0, 1.0], size=(draws, pnl.size))
    c3 = (signs * pnl[None, :]).mean(axis=1)
    se = float(c3.std(ddof=1) / np.sqrt(c3.size))
    assert abs(float(c3.mean())) <= 2.0 * se, f"[C] N3 mean {c3.mean():+.3f} vs 2 SE {2 * se:.3f}"
    return c3, se


def q_of(x, obs=None):
    x = np.asarray(x, float)
    d = dict(draws=int(x.size), p50=float(np.median(x)), p95=float(np.quantile(x, .95)), max=float(x.max()), min=float(x.min()),
             mean=float(x.mean()), distinct=int(len(set(x.tolist()))))
    if obs is not None:
        d["observed"] = float(obs)
        d["above_p95"] = bool(obs > d["p95"])
        d["frac_below_observed"] = float((x < obs).mean())
    return d


# ------------------------------------------------------------------ the construction
def setup(P):
    """The arrays every stage reads: the rsi gate (lagged by construction), the eligibility, the kernel inputs."""
    n, T = P["n"], P["T"]
    elig = np.array(P["elig"])
    excl = np.asarray(P["excl"])
    sc_rsi = UF.apply_floor_replace(np.where(excl, np.nan, P["score"]("rsi")), P["keep"])      # (n, T), D346's run_cell
    rankT = Y.rank_single({"rsi": sc_rsi}, P["base"], "rsi", n, T)
    gate = Y.gate_from(rankT, P["finT"], keep=elig)
    r1T, finT, ocT = np.asarray(P["r1T"]), np.asarray(P["finT"]), np.asarray(P["ocT"])
    A2 = dict(P["A2"], r1T=r1T, finT=finT, ocT=ocT)                       # the pair kernel reads r1T, finT, ocT only
    zeros = np.zeros(T)
    A2_zero = dict(A2, mkt=zeros, mkt_oc=zeros)                          # [ID]: simulate_event with a zero market
    return dict(n=n, T=T, elig=elig, excl=excl, sc_rsi=sc_rsi, rankT=rankT, gate=gate, A2=A2, A2_zero=A2_zero, r1T=r1T, finT=finT, ocT=ocT,
                base=np.asarray(P["base"]), HALF=P["HALF"], CLOSE=np.asarray(P["CLOSE"]), DV=np.asarray(P["DV"]),
                RAW_CLOSE=np.asarray(P["RAW_CLOSE"]), m_f=np.asarray(P["m_f"]), m_f_oc=np.asarray(P["m_f_oc"]))


def long_trigger(P, elig):
    lo, hi, sc = V50.member_dense(P, LONG_TRIGGER, elig)
    return lo, hi, sc


def short_trigger(P, member, elig):
    """A D352 family member as a SHORT trigger: (hi, score). score is the raw lagged percentile (invalidation: <= 50,
    entry order: descending); rsi/turn reads the lagged rsi itself (D347's rsi_turn mirror event; invalidation rsi <= 50)."""
    sig, shape = member.split("/")
    if shape == "turn":
        assert sig == "rsi", member
        hi = np.ascontiguousarray(P["EVENTS"]["rsi_turn"][1])
        return hi, np.asarray(P["LAG"]["rsi"])
    thr = SHORT_THR[shape]
    pct = V47.percentile_grid(V50.lagged(P, sig))
    prev = np.full_like(pct, np.nan)
    prev[1:] = pct[:-1]
    edge = 100.0 - thr
    with np.errstate(invalid="ignore"):
        hi = (pct >= edge) & (prev < edge) & elig
    return np.ascontiguousarray(hi), pct


def trigger_of(P, S, arm, member=None):
    if arm == "long":
        lo, hi, sc = long_trigger(P, S["elig"])
        return lo, sc, 0, LONG_TRIGGER
    assert member, "--arm short needs --trigger SIG/SHAPE"
    hi, sc = short_trigger(P, member, S["elig"])
    return hi, sc, 1, member


def simulate(S, trig, sc, side, exit, K, **kw):
    return PB.simulate_pairs(S["A2"], trig, sc, S["gate"], side=side, exit=exit, cap=CAP, n_max_pairs=K, basket=BASKET, U=U, **kw)


def costed(S, res, cv, defined):
    return PB.costed_pairs(res, S["HALF"][cv], S["CLOSE"], S["DV"], S["excl"], S["RAW_CLOSE"], tot_mask=defined, BR=BR)


# ------------------------------------------------------------------ second implementations
def rebuild_basket(S, t, opp, trigger_row, held_rows, lag=1):
    """[L]: the basket at bar t from the raw floored rsi score at t-lag and the base at t, by one stable argsort --
    never rank_single, never gate_from. The gate is the first N_BASE finite (opp 0) or the last N_BASE finite
    reversed (opp 1: most extreme first, ties by row descending, the ranker's convention), filtered to finT & elig
    at t; the basket the first BASKET of those that are neither the trigger nor held."""
    if t - lag < 0:
        return ()
    v = np.where(S["base"][:, t], S["sc_rsi"][:, t - lag], np.nan)
    fin = np.isfinite(v)
    cnt = int(fin.sum())
    if cnt < 2 * N_BASE:
        return ()
    order = np.argsort(v, kind="stable")
    g = order[:N_BASE] if opp == 0 else order[cnt - N_BASE:cnt][::-1]
    out = []
    for r in g:
        r = int(r)
        if S["finT"][t, r] and S["elig"][t, r] and r != trigger_row and r not in held_rows:
            out.append(r)
            if len(out) == BASKET:
                break
    return tuple(out)


def ledger_arrays(res):
    """Closed and still-open pairs as arrays, with their open order."""
    allp = list(res["pairs"]) + list(res["open_pairs"])
    seq = np.concatenate([res["seq"], res["open_seq"]]) if allp else np.zeros(0, np.int64)
    e0 = np.array([p[1] for p in allp], np.int64)
    end = e0 + np.array([p[2] for p in allp], np.int64)
    return allp, seq, e0, end


def held_at_entry(L, j):
    """Names on any leg of a pair open when pair j was opened: pairs open at e0_j that opened earlier (an earlier bar,
    or the same bar in an earlier open order); a basket leg counts while its own partner_age is still running."""
    allp, seq, e0s, ends = L
    e0, sj = e0s[j], seq[j]
    m = (e0s <= e0) & (e0 < ends) & ((e0s < e0) | (seq < sj))
    m[j] = False
    held = set()
    for q in np.flatnonzero(m):
        row, e0q, _a, _p, _s, partners, pages = allp[q]
        held.add(int(row))
        for p, pa in zip(partners, pages):
            if e0 - e0q < pa:
                held.add(int(p))
    return held


def assert_identity(res_pair, res_event, tag):
    a = [(p[0], p[1], p[2], p[3]) for p in res_pair["pairs"]]
    b = [(t[0], t[1], t[2], t[3]) for t in res_event["trades"]]
    assert len(a) == len(b), f"[ID] {tag}: {len(a)} pairs vs {len(b)} trades"
    assert a == b, f"[ID] {tag}: ledgers differ (first at {next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)})"
    assert np.array_equal(res_pair["n_open"], res_event["cnt0"] + res_event["cnt1"]), f"[ID] {tag}: counts differ"
    assert np.array_equal(res_pair["ent"], res_event["ent"]) and np.array_equal(res_pair["skipped"], res_event["skipped"]), f"[ID] {tag}: entries/skipped"
    return len(a)


def assert_sign(delta_bp, want_bp, tag, tol=1e-9):
    assert abs(delta_bp - want_bp) < tol, f"[S] {tag}: pair moved {delta_bp:+.6f} bp, wanted {want_bp:+.6f}"


def check_N2(res, gate, opp, sample=None, rng=None):
    """[N2] every random partner is in the same-day opposite-side gate slice, is not the trigger, is not held on any
    leg of a pair open at entry; basket size preserved. On all pairs, or a sample."""
    L = ledger_arrays(res)
    allp = L[0]
    idx = np.arange(len(allp))
    if sample is not None and idx.size > sample:
        idx = np.sort(rng.choice(idx, size=sample, replace=False))
    gF, gO = gate["gateF"], gate["gateO"]
    for j in idx:
        row, e0, _a, _p, _s, partners, _pg = allp[j]
        assert len(partners) == BASKET, f"[N2] basket size {len(partners)} at ({row}, {e0})"
        assert len(set(partners)) == BASKET, f"[N2] duplicate partner at ({row}, {e0})"
        sl = set(int(x) for x in gF[gO[opp, e0]:gO[opp, e0 + 1]])
        held = held_at_entry(L, j)
        for p in partners:
            assert p in sl, f"[N2] partner {p} not in the day-{e0} side-{opp} gate"
            assert p != row, f"[N2] partner is the trigger at ({row}, {e0})"
            assert p not in held, f"[N2] partner {p} already held at ({row}, {e0})"
    return int(idx.size)


def sign_delta(S, trig, sc, side, exit, K, row, e0, bar, delta):
    """Re-run with r1T[bar, row] += delta and return the pair (row, e0)'s pnl change in bp; the ledger must be otherwise unchanged."""
    base = simulate(S, trig, sc, side, exit, K)
    r1p = np.array(S["r1T"])
    r1p[bar, row] += delta
    S2 = dict(S, A2=dict(S["A2"], r1T=r1p))
    pert = simulate(S2, trig, sc, side, exit, K)
    a = {(p[0], p[1]): p for p in base["pairs"]}
    b = {(p[0], p[1]): p for p in pert["pairs"]}
    assert set(a) == set(b) and all(a[k][2] == b[k][2] and a[k][5] == b[k][5] for k in a), "[S] the perturbation changed the ledger's shape"
    return (b[row, e0][3] - a[row, e0][3]) * 1e4, a[row, e0]


def hedged_trigger_series(S, res):
    """Q4: the pair book's OWN trigger legs, market-hedged as D353 hedges them (floored m_f / m_f_oc), per bar on the
    deployed base -- rebuilt from the ledger (closed + still-open pairs)."""
    allp = list(res["pairs"]) + list(res["open_pairs"])
    acc, cnt, pnl, acc_x = PB.per_bar_from_ledger(allp, S["r1T"], S["ocT"], res["side"], S["T"], mkt=S["m_f"], mkt_oc=S["m_f_oc"])
    m = cnt > 0
    return np.where(m, acc_x / np.maximum(cnt, 1), np.nan), acc, cnt, pnl


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    S = setup(P)
    T, n, elig, gate = S["T"], S["n"], S["elig"], S["gate"]
    lo, hi, sc = long_trigger(P, elig)
    defined = EB.defined_bars(sc)
    g_sz = np.diff(gate["gateO"], axis=1)
    print(f"    the rsi gate: {int((g_sz[0] > 0).sum()):,} bars with a long-side slice (median {int(np.median(g_sz[0][g_sz[0] > 0]))} names), "
          f"{int((g_sz[1] > 0).sum()):,} with a short-side slice; trigger {LONG_TRIGGER}: {int(lo.sum()):,} long events, {int(hi.sum()):,} mirror; "
          f"EB.simulate_event hedged_series option {'present' if HAS_HEDGED else 'ABSENT'}")
    # timing
    ts = time.time()
    res = simulate(S, lo, sc, 0, "cap", 4)
    t_sim = time.time() - ts
    print(f"    one simulation (long arm, K=4, cap, extreme partner): {t_sim:.2f}s -> {len(res['pairs']):,} pairs, {int(res['ent'].sum()):,} entries, "
          f"skipped {int(res['skipped'].sum()):,}, no_basket {int(res['no_basket'].sum()):,}, basket_delist {int(res['basket_delist'].sum()):,}, "
          f"basket_empty {int(res['basket_empty'].sum()):,}")
    # [ID] with the basket absent, the trigger ledger equals simulate_event's with a zero market, at the same n_max
    n_id = 0
    for side, trg in ((0, lo), (1, hi)):
        for exit in EXITS:
            for K in KS:
                rp = simulate(S, trg, sc, side, exit, K, zero_basket=True)
                re = EB.simulate_event(S["A2_zero"], trg if side == 0 else np.zeros_like(trg), trg if side == 1 else np.zeros_like(trg), sc,
                                       exit=exit, cap=CAP, n_max=K, U=U)
                n_id += assert_identity(rp, re, f"side {side} {exit} K={K}")
                worst_b = float(np.nanmax(np.abs(rp["book_dep"] - re["book_dep"]))) if rp["mask_dep"].any() else 0.0
                assert worst_b < 1e-15, f"[ID] deployed series differ by {worst_b:.2e}"
    print(f"    [ID] KERNEL: with the basket absent, the pair kernel's trigger ledger (row, e0, age, pnl) equals simulate_event's with a zero market "
          f"bit-identically on both sides x both exits x K in {KS} ({n_id:,} trades); counts, entries and skipped equal ({el()})")
    # [L] the basket re-derived from score[:, t-1] by a second implementation, observed and rotated; the unlagged rebuild differs
    rng = np.random.default_rng([SEED, 354, 0])
    rot_tr, rot_sc = PB.rotate_trigger_elig(lo, sc, elig, rng)
    res_rot = simulate(S, rot_tr, rot_sc, 0, "cap", 4)
    n_l, n_unl = 0, 0
    for label, r in (("observed", res), ("rotated", res_rot)):
        L = ledger_arrays(r)
        allp = L[0]
        pick = np.sort(rng.choice(len(allp), size=min(200, len(allp)), replace=False))
        for j in pick:
            row, e0, _a, _p, _s, partners, _pg = allp[j]
            held = held_at_entry(L, j)
            reb = rebuild_basket(S, e0, 1, row, held, lag=1)
            assert reb == partners, f"[L] {label} ({row}, {e0}): rebuilt {reb} vs kernel {partners}"
            n_l += 1
            n_unl += rebuild_basket(S, e0, 1, row, held, lag=0) != partners
    assert n_unl > n_l // 2, f"[L] the unlagged rebuild agrees on {n_l - n_unl} of {n_l}"
    print(f"    [L] LAG: the basket at {n_l} sampled entry bars (200 observed + 200 rotated) equals a rebuild from the raw floored rsi at t-1 by one stable "
          f"argsort (never rank_single / gate_from), with the same exclusions; the unlagged rebuild differs on {n_unl} of {n_l} ({el()})")
    # [S] sign in money
    res2 = simulate(S, lo, sc, 0, "cap", 2)
    pick = next(p for p in res2["pairs"] if p[2] >= 3 and min(p[6]) >= 3)
    row, e0 = pick[0], pick[1]
    d_t, _ = sign_delta(S, lo, sc, 0, "cap", 2, row, e0, e0 + 1, 50e-4)
    assert_sign(d_t, 50.0, "long trigger +50 bp")
    r1p = np.array(S["r1T"])
    r1p[e0 + 1, pick[5][0]] += 50e-4
    pert = simulate(dict(S, A2=dict(S["A2"], r1T=r1p)), lo, sc, 0, "cap", 2)
    d_b = (next(p for p in pert["pairs"] if p[0] == row and p[1] == e0)[3] - pick[3]) * 1e4
    assert_sign(d_b, -50.0 / 3.0, "long trigger's basket name +50 bp")
    res2s = simulate(S, hi, sc, 1, "cap", 2)
    pick_s = next(p for p in res2s["pairs"] if p[2] >= 3 and min(p[6]) >= 3)
    d_ts, _ = sign_delta(S, hi, sc, 1, "cap", 2, pick_s[0], pick_s[1], pick_s[1] + 1, 50e-4)
    assert_sign(d_ts, -50.0, "short trigger +50 bp")
    r1p = np.array(S["r1T"])
    r1p[pick_s[1] + 1, pick_s[5][0]] += 50e-4
    pert_s = simulate(dict(S, A2=dict(S["A2"], r1T=r1p)), hi, sc, 1, "cap", 2)
    d_bs = (next(p for p in pert_s["pairs"] if p[0] == pick_s[0] and p[1] == pick_s[1])[3] - pick_s[3]) * 1e4
    assert_sign(d_bs, 50.0 / 3.0, "short trigger's basket name +50 bp")
    print(f"    [S] SIGN in money: +50 bp on the trigger name for one held bar moves a long-trigger pair {d_t:+.3f} bp and a short-trigger pair {d_ts:+.3f}; "
          f"the same move on one basket name moves them {d_b:+.3f} / {d_bs:+.3f} (want -/+ 16.667) ({el()})")
    # [HX] the deployed and total series equal the ledger summed per bar
    worst_hx, worst_p, n_open_end = 0.0, 0.0, 0
    for r in (res, res2, res2s):
        allp = list(r["pairs"]) + list(r["open_pairs"])
        acc, cnt, pnl, _ = PB.per_bar_from_ledger(allp, S["r1T"], S["ocT"], r["side"], T)
        assert np.array_equal(cnt, r["n_open"]), "[HX] per-bar pair counts differ from the ledger"
        m = r["mask_dep"]
        worst_hx = max(worst_hx, float(np.abs(r["book_dep"][m] * r["n_open"][m] - acc[m]).max()),
                       float(np.abs(r["book_tot"][r["mask_tot"]] * U - acc[r["mask_tot"]]).max()))
        worst_p = max(worst_p, float(np.abs(pnl - np.array([p[3] for p in allp])).max()))
        n_open_end += len(r["open_pairs"])
    assert worst_hx < 1e-12 and worst_p < 1e-12, f"[HX] {worst_hx:.2e} / {worst_p:.2e}"
    print(f"    [HX] book_dep x n_open and book_tot x U equal the ledger's per-bar pr summed over pairs to {worst_hx:.1e} on every bar, "
          f"and every pair's pnl its own rebuild to {worst_p:.1e} (three books; {n_open_end} pairs still open at the last bar included in the rebuild) ({el()})")
    # [N1] the rotation
    rng1 = np.random.default_rng([SEED, 354, 0, 2, 1, 0])
    tr1, sc1 = PB.rotate_trigger_elig(lo, sc, elig, rng1)                      # asserts eligibility and counts inside
    sl_ref, _ss, sc_ref = EB.rotate_signals(lo, np.zeros_like(lo), sc, elig, np.random.default_rng([SEED, 354, 0, 2, 1, 0]))
    assert np.array_equal(tr1, sl_ref) and np.array_equal(sc1, sc_ref, equal_nan=True), "[N1] rotate_trigger_elig != EB.rotate_signals within elig"
    r1_ = simulate(S, tr1, sc1, 0, "cap", 2)
    p1 = np.array([p[3] for p in r1_["pairs"]])
    assert np.isfinite(p1).all() and np.isfinite(r1_["book_dep"][r1_["mask_dep"]]).all(), "[N1] NaN in a rotated draw"
    print(f"    [N1] every rotated trigger is eligible, every name keeps its count (== EB.rotate_signals within elig, same seed); "
          f"{int(tr1.sum()):,} events -> {len(r1_['pairs']):,} pairs, no NaN")
    # [N2] the random partner
    rng2 = np.random.default_rng([SEED, 354, 0, 2, 2, 0])
    r2_ = simulate(S, lo, sc, 0, "cap", 2, partner="random", rng=rng2)
    n2 = check_N2(r2_, gate, 1)
    n_diff = sum(1 for a, b in zip(res2["pairs"], r2_["pairs"]) if a[:2] == b[:2] and a[5] != b[5])
    print(f"    [N2] on a random-partner draw every partner of all {n2:,} pairs is in the same-day opposite-side gate, is not the trigger, is not held; "
          f"basket size {BASKET} preserved; the basket differs from the extreme's on {n_diff:,} pairs sharing (row, e0)")
    # [C] N3 centred
    rngC = np.random.default_rng([SEED, 354, 3])
    pnl2 = np.array([p[3] for p in res2["pairs"]]) * 1e4
    c3, se = n3_draws(rngC, pnl2)
    broke_c = False
    try:                                                     # the check must FAIL when the flip is not applied
        c_un = np.full(c3.size, float(pnl2.mean()))
        assert abs(float(c_un.mean())) <= 2.0 * se, "unflipped"
    except AssertionError:
        broke_c = True
    assert broke_c, "[C] the check passed an unflipped ledger"
    print(f"    [C] N3 (1,000 iid random-direction draws of the K=2 cap ledger) has mean {float(c3.mean()):+.2e} bp per pair, within 2 SE "
          f"({2 * se:.3f}); p95 {float(np.quantile(c3, .95)):+.2f}; the check fails on the unflipped ledger (mean {float(pnl2.mean()):+.1f})")
    # [SB] borrow on 200 short legs equals an independent recomputation
    rngS = np.random.default_rng([SEED, 354, 4])
    worst_sb = 0.0
    n_sb = 0
    for r in (res2, res2s):
        legs = r["legs"]
        short = [l for l in legs if l[3] == 1]
        pick = rngS.choice(len(short), size=min(100, len(short)), replace=False)
        tr5 = [(int(l[0]), int(l[1]), int(l[2]), 0.0, int(l[3])) for l in short]
        htb = BR.htb_flags(tr5, S["excl"], S["CLOSE"])
        per = BR.borrow_per_trade_bp(tr5, BR.rate_bps(tr5, htb, "gc_htb"))
        for j in pick:
            row, e0, age, _s, _k = short[j]
            hard = bool(S["excl"][row, max(e0 - 1, 0)]) or bool(S["CLOSE"][e0, row] < BR.PX_HTB)
            want = (BR.HTB_BPS if hard else BR.GC_BPS) * age / BR.ANN
            worst_sb = max(worst_sb, abs(per[j] - want))
            n_sb += 1
    assert worst_sb < 1e-12, f"[SB] {worst_sb:.2e}"
    c_pub = costed(S, res2, "PUB", defined)
    # the mean per-pair borrow in costed_pairs equals a direct recomputation: every pair's short legs at w x rate x age / 252, HTB rule direct
    tot = np.zeros(len(res2["pairs"]))
    for l, lp in zip(res2["legs"], res2["leg_pair"]):
        if l[3] == 1:
            hard = bool(S["excl"][l[0], max(l[1] - 1, 0)]) or bool(S["CLOSE"][l[1], l[0]] < BR.PX_HTB)
            tot[lp] += (BR.HTB_BPS if hard else BR.GC_BPS) * l[2] / BR.ANN * (1.0 if l[4] == 0 else 1.0 / BASKET)
    worst_pp = abs(float(tot.mean()) - c_pub["borrow_per_pair_bp"])
    # and the per-bar deployed charge reconciles to the per-pair total: sum_t borrow_bar[t] x n_open[t] == sum over pairs (D337's reconcile)
    acc_dep = c_pub["deployed"]["borrow_bp"] * float(res2["mask_dep"].sum())
    n_op = res2["n_open"].astype(float)
    # rebuild the per-bar charge directly and reconcile it to the ledger (pairs still open at the end carry their charge only to the ledger's horizon)
    acc = np.zeros(T)
    for l in res2["legs"]:
        if l[3] == 1:
            hard = bool(S["excl"][l[0], max(l[1] - 1, 0)]) or bool(S["CLOSE"][l[1], l[0]] < BR.PX_HTB)
            acc[l[1]:l[1] + l[2]] += (BR.HTB_BPS if hard else BR.GC_BPS) / BR.ANN * (1.0 if l[4] == 0 else 1.0 / BASKET)
    rec = abs(float((np.where(n_op > 0, acc / np.maximum(n_op, 1.0), 0.0)[res2["mask_dep"]]).sum()) - acc_dep)
    assert worst_pp < 1e-9 and rec < 1e-6, f"[SB] per pair {worst_pp:.2e}, per bar {rec:.2e}"
    print(f"    [SB] borrow on {n_sb} sampled short legs (long arm's baskets, short arm's triggers) equals rate x age / 252 with the HTB rule recomputed "
          f"directly, to {worst_sb:.1e}; the mean per-pair borrow ({c_pub['borrow_per_pair_bp']:.3f} bp) and the deployed per-bar charge "
          f"({c_pub['deployed']['borrow_bp']:.4f} bp/bar) equal direct rebuilds to {worst_pp:.1e} / {rec:.1e}; long arm K=2 cap: {c_pub['short_legs']:,} short legs, "
          f"HTB share {100 * c_pub['htb_share_short_legs']:.1f}%")
    # [V] at most K open; skipped counted
    for r, K in ((res, 4), (res2, 2), (res2s, 2), (r1_, 2), (r2_, 2)):
        assert int(r["n_open"].max()) <= K, f"[V] {int(r['n_open'].max())} > {K}"
    print(f"    [V] at most n_max_pairs open on every bar of five books; skipped counted: K=4 {int(res['skipped'].sum()):,}, K=2 {int(res2['skipped'].sum()):,} "
          f"of {int(lo.sum()):,} events")
    # [6] the checks fail when they should
    broke = 0
    try:
        re_m = EB.simulate_event(S["A2"], lo, np.zeros_like(lo), sc, exit="cap", cap=CAP, n_max=2, U=U)     # the market term left in
        assert_identity(simulate(S, lo, sc, 0, "cap", 2, zero_basket=True), re_m, "market left in")
    except AssertionError:
        broke += 1
    try:
        assert_sign(d_t + 50.0, 50.0, "handed +50 bp")
    except AssertionError:
        broke += 1
    try:
        bad = dict(r2_, pairs=list(r2_["pairs"]))
        p0 = bad["pairs"][0]
        sl = set(int(x) for x in gate["gateF"][gate["gateO"][1, p0[1]]:gate["gateO"][1, p0[1] + 1]])
        outsider = next(r for r in range(n) if r not in sl and r != p0[0])
        bad["pairs"][0] = p0[:5] + ((outsider,) + p0[5][1:], p0[6])
        check_N2(bad, gate, 1)
    except AssertionError:
        broke += 1
    assert broke == 3, f"[6] {broke} of 3 raised"
    print("    [6] [ID] raises with the market term left in; [S] raises on a pair handed +50 bp; [N2] raises on a partner from outside the gate")
    # timing summary
    ts = time.time()
    simulate(S, lo, sc, 0, "cap", 4)
    t2 = time.time() - ts
    ts = time.time()
    simulate(S, lo, sc, 0, "cap", 4, partner="random", rng=np.random.default_rng(1))
    t3 = time.time() - ts
    ts = time.time()
    PB.rotate_trigger_elig(lo, sc, elig, np.random.default_rng(1))
    t4 = time.time() - ts
    print(f"\n  timing: simulate {t2:.2f}s (extreme) / {t3:.2f}s (random); rotation {t4:.2f}s; {rss_line()}")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)")


def stage_arm(P, arm, member, K, exit, null, draws, part):
    S = setup(P)
    trig, sc, side, name = trigger_of(P, S, arm, member)
    defined = EB.defined_bars(sc)
    arm_code = ARMS.index(arm)
    null_code = NULLS.index(null) + 1
    obs = simulate(S, trig, sc, side, exit, K)
    assert int(obs["n_open"].max()) <= K, "[V]"
    oc = {cv: costed(S, obs, cv, defined) for cv in CONVS}
    d, t_ = oc["PUB"]["deployed"], oc["PUB"]["total"]
    print(f"\n  {arm} arm ({name}) K={K} {exit} {null} part {part}: {int(trig.sum()):,} events -> {len(obs['pairs']):,} pairs "
          f"(skipped {oc['PUB']['skipped']:,}, no_basket {oc['PUB']['no_basket']:,}); PUB deployed gross {d['gross_bp']:+.2f} net {d['net_bp']:+.2f} bp/bar "
          f"Sharpe {d['sharpe_net']:+.2f}; total gross {t_['gross_bp']:+.2f} net {t_['net_bp']:+.2f}; mean per pair {oc['PUB']['pair_mean_bp']:+.1f} bp")
    rng = np.random.default_rng([SEED, 354, arm_code, K, null_code, part])
    G, N, SH, M, NP = [], [], [], [], []
    ts = time.time()
    for dd in range(draws):
        if null == "N1":
            tr, sc_r = PB.rotate_trigger_elig(trig, sc, S["elig"], rng)          # [N1] asserted inside
            r = simulate(S, tr, sc_r, side, exit, K)
        else:
            r = simulate(S, trig, sc, side, exit, K, partner="random", rng=rng)
            if dd == 0:
                check_N2(r, S["gate"], 1 - side, sample=300, rng=np.random.default_rng([SEED, 354, 9, part]))
            assert all(len(p[5]) == BASKET for p in r["pairs"]), "[N2] basket size"
        assert int(r["n_open"].max()) <= K, "[V]"
        pn = np.array([p[3] for p in r["pairs"]])
        assert np.isfinite(pn).all(), f"[{null}] NaN in a draw"
        c = costed(S, r, "PUB", defined)
        G.append(c["deployed"]["gross_bp"])
        N.append(c["deployed"]["net_bp"])
        SH.append(c["deployed"]["sharpe_net"])
        M.append(c["pair_mean_bp"])
        NP.append(len(r["pairs"]))
        if (dd + 1) % 10 == 0 or dd + 1 == draws:
            print(f"    {null}: {dd + 1}/{draws} ({time.time() - ts:.0f}s)", flush=True)
    out = dict(arm=arm, trigger=name, K=K, exit=exit, null=null, draws=draws, part=part, seed=[SEED, 354, arm_code, K, null_code, part],
               events=int(trig.sum()), observed=oc, gross_bp=G, net_pub=N, sharpe_net_pub=SH, mean_per_pair=M, pairs=NP)
    f = Path(str(STAGE).format(arm=arm, K=K, exit=exit, null=null, part=part))
    f.write_text(json.dumps(clean(out)))
    print(f"  wrote {f.name}: net PUB p50 {np.median(N):+.2f} p95 {np.quantile(N, .95):+.2f} (observed {d['net_bp']:+.2f}); gross p50 {np.median(G):+.2f} "
          f"p95 {np.quantile(G, .95):+.2f}; per pair p50 {np.median(M):+.1f} p95 {np.quantile(M, .95):+.1f}; {rss_line()} ({time.time() - P['t0']:.0f}s)")


def stage_report(P, trigger_short=None):
    S = setup(P)
    T = S["T"]
    arms = [("long", None)]
    files_short = sorted(REPO.glob("data/d354_short_k*_p*.json"))
    if trigger_short is None and files_short:
        trigger_short = json.loads(files_short[0].read_text())["trigger"]
    if trigger_short:
        arms.append(("short", trigger_short))
    REPORT, rngC = {}, np.random.default_rng([SEED, 354, 3])
    for arm, member in arms:
        trig, sc, side, name = trigger_of(P, S, arm, member)
        defined = EB.defined_bars(sc)
        R_ = dict(trigger=name, events=int(trig.sum()), cells={})
        for K in KS:
            for exit in EXITS:
                res = simulate(S, trig, sc, side, exit, K)
                oc = {cv: costed(S, res, cv, defined) for cv in CONVS}
                pnl = np.array([p[3] for p in res["pairs"]]) * 1e4
                c3, se = n3_draws(rngC, pnl)                                    # [C] asserted inside
                ages = np.array([p[2] for p in res["pairs"]])
                k = max(1, int(np.floor(0.01 * pnl.size)))
                srt = np.sort(pnl)
                cell = dict(costed=oc, pairs=int(pnl.size), entries=int(res["ent"].sum()), skipped=int(res["skipped"].sum()),
                            skipped_share=float(res["skipped"].sum() / max(1, trig.sum())), no_basket=int(res["no_basket"].sum()),
                            basket_delist=int(res["basket_delist"].sum()), basket_empty=int(res["basket_empty"].sum()),
                            open_at_end=len(res["open_pairs"]), max_open=int(res["n_open"].max()),
                            pair_mean_bp=float(pnl.mean()), pair_median_bp=float(np.median(pnl)), win_rate=float((pnl > 0).mean()),
                            hold_mean=float(ages.mean()), hold_median=float(np.median(ages)),
                            mean_ex_top_bp=float(srt[:-k].mean()), mean_ex_bottom_bp=float(srt[k:].mean()), mean_trimmed_bp=float(srt[k:-k].mean()),
                            trigger_leg_mean_bp=float(res["pnl_trig"].mean()) * 1e4, basket_leg_mean_bp=float(res["pnl_basket"].mean()) * 1e4,
                            N3=dict(q_of(c3, pnl.mean()), se=se, mean_within_2se=True))
                for null in NULLS:
                    parts = sorted(REPO.glob(f"data/d354_{arm}_k{K}_{exit}_{null}_p*.json"))
                    if not parts:
                        continue
                    ds = [json.loads(p.read_text()) for p in parts]
                    for dd in ds:
                        assert dd["trigger"] == name, f"{parts} trigger {dd['trigger']} != {name}"
                        assert abs(dd["observed"]["PUB"]["deployed"]["net_bp"] - oc["PUB"]["deployed"]["net_bp"]) < 1e-9, f"observed differs between stages: {parts}"
                    cat = lambda key: np.concatenate([np.array(dd[key], float) for dd in ds])
                    cell[null] = dict(parts=[p.name for p in parts], draws=int(sum(dd["draws"] for dd in ds)),
                                      net_pub=q_of(cat("net_pub"), oc["PUB"]["deployed"]["net_bp"]),
                                      sharpe_net_pub=q_of(cat("sharpe_net_pub"), oc["PUB"]["deployed"]["sharpe_net"]),
                                      gross_bp=q_of(cat("gross_bp"), oc["PUB"]["deployed"]["gross_bp"]),
                                      mean_per_pair=q_of(cat("mean_per_pair"), pnl.mean()))
                if arm == "long" and K == 2 and exit == "cap":
                    # Q4: the pair's own trigger legs hedged against the floored market, per bar on the deployed base (ledger rebuild);
                    # beside it the K-capped trigger book without any basket, hedged, from the event kernel's hedged_series option
                    hx, acc, cnt, _ = hedged_trigger_series(S, res)
                    m = cnt > 0
                    vol_pair = float(res["book_dep"][res["mask_dep"]].std(ddof=1)) * 1e4
                    vol_hedged = float(hx[m].std(ddof=1)) * 1e4
                    cell["Q4"] = dict(vol_pair_bp=vol_pair, vol_hedged_trigger_same_trades_bp=vol_hedged,
                                      hedged_trigger_same_trades_gross_bp=float(hx[m].mean()) * 1e4,
                                      basis="the pair book's own trigger legs, market-hedged (floored m_f / m_f_oc), rebuilt from the ledger")
                    if HAS_HEDGED:
                        re = EB.simulate_event(P["A3"], trig, np.zeros_like(trig), sc, exit="cap", cap=CAP, n_max=K, U=U, hedged_series=True)
                        cell["Q4"]["vol_hedged_trigger_book_K_bp"] = float(re["book_dep_x"][re["mask_dep"]].std(ddof=1)) * 1e4
                        cell["Q4"]["hedged_trigger_book_K_gross_bp"] = float(re["book_dep_x"][re["mask_dep"]].mean()) * 1e4
                        cell["Q4"]["hedged_trigger_book_K_trades"] = len(re["trades"])
                    # Q7: the trigger's market-hedged mean per trade, every event taken (D353's lens)
                    rt = V47.run_events(P, trig, np.zeros_like(trig), sc, "cap")
                    cell["Q7"] = dict(trigger_hedged_mean_per_trade_bp=float(V47.pnl_bp(rt).mean()), trigger_trades=len(rt["trades"]),
                                      pair_mean_per_pair_bp=float(pnl.mean()))
                R_["cells"][f"K{K}/{exit}"] = cell
                print(f"  {arm} K={K} {exit:12s}: {pnl.size:,} pairs, PUB dep gross {oc['PUB']['deployed']['gross_bp']:+.2f} net {oc['PUB']['deployed']['net_bp']:+.2f} | "
                      f"PB net {oc['PB']['deployed']['net_bp']:+.2f} | per pair {pnl.mean():+.1f} (trigger {cell['trigger_leg_mean_bp']:+.1f}, basket {cell['basket_leg_mean_bp']:+.1f}) "
                      f"({time.time() - P['t0']:.0f}s)", flush=True)
        REPORT[arm] = R_

    # ---- print ----
    print("\n" + "=" * 140)
    print("THE PAIR BOOK -- trigger hedged with the equal-weight basket of the three most extreme opposite-rsi names; bp per bar, DEPLOYED base (TOTAL beside)")
    print("=" * 140)
    hdr = "  %-5s %-3s %-12s %6s %7s | %7s %7s %7s %7s %6s | %7s %7s | %7s %7s %6s | %7s %7s %7s %6s" % (
        "arm", "K", "exit", "pairs", "skip%", "gross", "netPUB", "netPB", "vol", "ShPUB", "maxDD", "hold", "totG", "totNet", "expo", "per pr", "trig", "bask", "2c")
    print(hdr)
    for arm, R_ in REPORT.items():
        for key, c in R_["cells"].items():
            K, exit = key.split("/")
            pu, pb = c["costed"]["PUB"], c["costed"]["PB"]
            d, t_ = pu["deployed"], pu["total"]
            print("  %-5s %-3s %-12s %6d %6.1f%% | %+7.2f %+7.2f %+7.2f %7.1f %+6.2f | %7.0f %7.1f | %+7.2f %+7.2f %5.1f%% | %+7.1f %+7.1f %+7.1f %6.1f" % (
                arm, K[1:], exit, c["pairs"], 100 * c["skipped_share"], d["gross_bp"], d["net_bp"], pb["deployed"]["net_bp"], d["vol_bp"], d["sharpe_net"],
                d["maxdd_bp"], c["hold_mean"], t_["gross_bp"], t_["net_bp"], 100 * t_["exposure"], c["pair_mean_bp"], c["trigger_leg_mean_bp"],
                c["basket_leg_mean_bp"], pu["round_trip"]))
    print("\n  COST PIECES (PUB | PB): trigger 2c, basket 2c, commission, borrow bp/bar deployed, breakeven half-spread bp/side (deployed), turnover")
    for arm, R_ in REPORT.items():
        for key, c in R_["cells"].items():
            s = []
            for cv in CONVS:
                x = c["costed"][cv]
                s.append(f"{cv} {x['trigger_2c']:.1f}/{x['basket_2c']:.1f}/{x['commission_rt']:.1f}/{x['deployed']['borrow_bp']:.3f}/"
                         f"{x['deployed']['breakeven_half_spread_bp_side']:.1f}/{x['deployed']['turnover']:.4f}")
            print(f"    {arm} {key:16s} " + " | ".join(s) + f"  (no_basket {c['no_basket']}, basket_delist {c['basket_delist']}, basket_empty {c['basket_empty']})")
    print("\n  NULLS on the DEPLOYED PUB net bp/bar (p50 / p95 / max / frac below observed) and per pair:")
    for arm, R_ in REPORT.items():
        for key, c in R_["cells"].items():
            line = f"    {arm} {key:16s} obs net {c['costed']['PUB']['deployed']['net_bp']:+.2f} per pair {c['pair_mean_bp']:+.1f} |"
            for null in NULLS:
                if null in c:
                    q = c[null]["net_pub"]
                    qp = c[null]["mean_per_pair"]
                    line += (f" {null}[{c[null]['draws']}] net {q['p50']:+.2f}/{q['p95']:+.2f}/{q['max']:+.2f} below {q['frac_below_observed']:.2f} "
                             f"{'above' if q['above_p95'] else 'NOT above'}; per pair {qp['p50']:+.1f}/{qp['p95']:+.1f} |")
                else:
                    line += f" {null} not run |"
            q3 = c["N3"]
            line += f" N3 per pair p95 {q3['p95']:+.2f} {'above' if q3['above_p95'] else 'NOT above'}"
            print(line)
            print(f"      trims: mean {c['pair_mean_bp']:+.1f} median {c['pair_median_bp']:+.1f} ex-top {c['mean_ex_top_bp']:+.1f} ex-bottom {c['mean_ex_bottom_bp']:+.1f} "
                  f"trimmed {c['mean_trimmed_bp']:+.1f}; win {100 * c['win_rate']:.1f}%; hold {c['hold_mean']:.1f}/{c['hold_median']:.0f}")

    # ---- predictions, long arm ----
    L = REPORT["long"]["cells"]
    c2, c2i = L["K2/cap"], L["K2/invalidation"]
    n1, n2 = c2.get("N1"), c2.get("N2")
    q = {}
    q["Q1"] = bool(n1 and n2 and n1["net_pub"]["above_p95"] and n2["net_pub"]["above_p95"])
    q["Q2"] = bool(c2["basket_leg_mean_bp"] > 0)
    q["Q3"] = bool(n2 and n2["net_pub"]["p50"] > c2["costed"]["PUB"]["deployed"]["net_bp"])
    q["Q4"] = bool(c2["Q4"]["vol_pair_bp"] < c2["Q4"]["vol_hedged_trigger_same_trades_bp"])
    q["Q5"] = bool(c2["costed"]["PUB"]["deployed"]["net_bp"] < 0 and c2["costed"]["PB"]["deployed"]["net_bp"] > 0)
    q["Q6"] = bool(c2i["costed"]["PUB"]["deployed"]["net_bp"] < c2["costed"]["PUB"]["deployed"]["net_bp"])
    q["Q7"] = bool(c2["pair_mean_bp"] < c2["Q7"]["trigger_hedged_mean_per_trade_bp"] - 10.0)
    v = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS (long arm, K=2, cap exit, PUB, deployed base)")
    print(f"  Q1 (LOAD-BEARING) above the p95 of BOTH N1 and N2 on PUB net bp/bar: {v(q['Q1'])} -- observed {c2['costed']['PUB']['deployed']['net_bp']:+.2f}; "
          + (f"N1 p95 {n1['net_pub']['p95']:+.2f} ({n1['draws']} draws)" if n1 else "N1 not run") + "; "
          + (f"N2 p95 {n2['net_pub']['p95']:+.2f} ({n2['draws']} draws)" if n2 else "N2 not run"))
    print(f"  Q2 (against) the basket leg's own P&L (short the three highest-rsi) is positive: {v(q['Q2'])} -- {c2['basket_leg_mean_bp']:+.1f} bp per pair "
          f"(trigger leg {c2['trigger_leg_mean_bp']:+.1f})")
    print(f"  Q3 N2 is centred above the observed (a random gate partner hedges better than the extreme): {v(q['Q3'])} -- "
          + (f"N2 p50 {n2['net_pub']['p50']:+.2f} vs observed {c2['costed']['PUB']['deployed']['net_bp']:+.2f}" if n2 else "N2 not run"))
    print(f"  Q4 the pair's per-bar vol is below the market-hedged trigger's on the same trades: {v(q['Q4'])} -- pair {c2['Q4']['vol_pair_bp']:.1f} vs "
          f"hedged trigger {c2['Q4']['vol_hedged_trigger_same_trades_bp']:.1f} bp/bar"
          + (f" (K-capped trigger book without basket, hedged: {c2['Q4']['vol_hedged_trigger_book_K_bp']:.1f})" if "vol_hedged_trigger_book_K_bp" in c2["Q4"] else ""))
    print(f"  Q5 nets negative under PUB and positive under PB: {v(q['Q5'])} -- PUB {c2['costed']['PUB']['deployed']['net_bp']:+.2f}, PB {c2['costed']['PB']['deployed']['net_bp']:+.2f}")
    print(f"  Q6 the invalidation exit is worse than the cap on net bp/bar: {v(q['Q6'])} -- invalidation {c2i['costed']['PUB']['deployed']['net_bp']:+.2f} vs cap "
          f"{c2['costed']['PUB']['deployed']['net_bp']:+.2f}")
    print(f"  Q7 the pair's mean per pair is more than 10 bp below the trigger's market-hedged mean per trade: {v(q['Q7'])} -- pair {c2['pair_mean_bp']:+.1f} vs "
          f"trigger {c2['Q7']['trigger_hedged_mean_per_trade_bp']:+.1f} on {c2['Q7']['trigger_trades']:,} trades")
    print(f"  check: [ID] the pair kernel with the basket absent equals the event kernel with a zero market (asserted in --selftest)")
    out = dict(note="D354: the pair book. Long trigger rev_5/E1 hedged with the three highest-rsi gate names; short arm on a D352 member hedged with "
                    "the three lowest. No market term. Deployed = mean over open pairs; total = sum / 4. Costs: each leg its own round trip at its held "
                    "median half-spread (basket legs at 1/3), commission per crossing, GC/HTB borrow on every short leg. Nothing is a book; nothing promoted.",
               cap=CAP, basket=BASKET, U=U, n_base=N_BASE, ks=KS, exits=EXITS, long_trigger=LONG_TRIGGER, short_trigger=trigger_short,
               hedged_series_option_present=HAS_HEDGED, report=REPORT, predictions=q)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s; {rss_line()})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--trigger", help="short arm: a D352 member SIG/S2|S5|S10 or rsi/turn")
    ap.add_argument("--k", type=int, choices=KS, default=2)
    ap.add_argument("--exit", choices=EXITS, default="cap")
    ap.add_argument("--null", choices=NULLS)
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--trigger-short", help="--report: the short arm's trigger (default: read from its stage files)")
    a = ap.parse_args()
    print("D354  the pair book -- a trigger hedged with a basket of the ranking's opposite extreme")
    P = PREP.prep(need_grids=False)
    if a.selftest:
        stage_selftest(P)
    elif a.arm:
        if not a.null:
            ap.error("--arm needs --null N1|N2")
        if a.arm == "short" and not a.trigger:
            ap.error("--arm short needs --trigger SIG/SHAPE")
        stage_arm(P, a.arm, a.trigger, a.k, a.exit, a.null, a.draws, a.part)
    elif a.report:
        stage_report(P, a.trigger_short)
    else:
        ap.error("one of --selftest, --arm ARM --null N, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
