"""D361 -- the regime-gated short: the record's two short triggers (D359's loser-rally spike, D360's gap-up fade) switched on by a
market-level gate computed on the floored market's own return series, with the gate's own null (a circular time rotation).

    uv run python scripts/run_d361_regime_gated_short.py --selftest
    uv run python scripts/run_d361_regime_gated_short.py --stage0                                    the premise: does the gate forecast the cohort's drift?
    uv run python scripts/run_d361_regime_gated_short.py --cell G1:T1 --draws 100 --draws-rot 200 --part 0    the controls for one cell (one process per cell)
    uv run python scripts/run_d361_regime_gated_short.py --report
    --out-dir DIR   (every stage; default data/ -- the smoke runs pass temp/... so that nothing under data/ is touched)
    --draws N       the A'-within-gate and B draws; --draws-rot R the gate-rotation draws (default: N). The pre-registration is 200 / 100 / 100.

Pre-registration: docs/decisions/D361-the-regime-gated-short-the-triggers-the-record-has-behind-a-market-level-gate.md

The gate, on m_f (P["m_f"]: the floored market's per-bar equal-weight SIMPLE return -- r1T is a simple total return, d340_fill compounds it
with log1p; m_f = V47.floored_market's mean of r1T over the floored priced names), lagged one bar (the value at t uses m_f to t-1):
    index[t]  = prod_{j = m_start..t} (1 + m_f[j])                     (the cumulative index; index[m_start - 1] := 1; the base is immaterial)
    G1[t]     = prod_{j = t-63..t-1} (1 + m_f[j]) - 1  <  0            (the trailing 63-bar COMPOUNDED return of the floored market)
    G2[t]     = index[t-1]  <  mean(index[t-200 .. t-1])              (the index below its trailing 200-bar mean)
    defined[t] = t >= m_start + window; the gate is False (off) where undefined. The record's yr_ret sums m_f additively; the gate compounds.
    The sign of G1 under the plain sum of m_f is counted beside ([GT] prints the bars where it would differ).

The triggers, each exactly the parent's construction (imported, never copied), entered SHORT via run_d359's run_short (D345's kernel,
every event taken, no slot cap, hedged by the floored market):
    T1 = run_d359.cell_signal(P, 10, 90):  pct_mom <= 10 & pct_rev >= 90 & pct_rev[t-1] < 90 & elig      score pct_rev
    T2 = run_d360.mirror_signal(P, 2, 10): pct_gap >= 98 & pct_rv >= 90 & elig[g+1], event at t = g+1,
                                           D360's exclusions [XD] [V0] applied                             score 100 - pct_gap lagged (D360's kernel score)
Arms per (gate, trigger): gated = trigger & gate[t]; gate-off = trigger & ~gate[t]; ungated = trigger. gated u off == ungated, disjoint ([G]).
A position opened while the gate is on is held to its exit whatever the gate does after (the exit is the cap). Exits cap 10 (PRIMARY), cap 20.
Cells G1:T1 (PRIMARY, index 0), G1:T2 (1), G2:T1 (2), G2:T2 (3).

Stage 0 (the premise), per gate: (1) the loser cohort's (pct_mom <= 10, eligible name-bars) hedged forward-20 drift, F20[t, i] =
sum_{j = t..t+19} (r1T - m_f)[t+j, i] (non-priced bars count 0, as V47.forward_excess_grid; the window must fit), averaged over name-bars
with the gate on vs off; (2) the correlation between the gate's LEVEL at the start of each NON-OVERLAPPING 20-bar block (blocks from the
gate's first defined bar) and the cohort's mean F20 over the names in the cohort at that block start; (3) the on-share, episodes and run
lengths; (4) beside, the floored market's own forward-20 return (the additive sum the hedge pays, and compounded) with the gate on and off.

Nulls on the primary exit per cell: gate ROTATION (load-bearing: the gate boolean circularly shifted over its DEFINED bars by an offset
drawn without replacement from [1, Td-1], re-ANDed with the trigger, re-simulated), A' WITHIN THE GATE (EB.rotate_signals on the mask
elig & gate), B (same day, same rsi bucket, random eligible name with a defined rsi percentile; shortfall counted), C (1,000 sign flips).
Cost per trade (deciding nothing, R15): 2c (V47.two_c) PUB and PB on the ledger's own held names, D337's gc_htb borrow, HTB share, net after
both, the breakeven half-spread; the deployed base with the 4- and 2-crossing lines; exposure on the kernel's defined bars (D358's
convention) and on the gate's defined bars beside.

Everything shared is imported: d348_prep (FIRST), run_d360 (its mirror, exclusions and cached open grid), run_d359 (cell_signal, grids,
cohort, run_short, simulate, trade_block with borrow and the four groups, deployed_block with the 2-crossing line, assert_S_short,
perturb_test, bucket_interaction, assert_partition), and through it run_d358 (assert_HX, control_C, null_stats, observed_stats, assert_B,
deployed_subsets), run_d353 (b_pool_P, assert_series_defs, _dist), run_d349 (borrow_of, check_borrow, event_accounting), run_d350 (clean).

ASSERTIONS [K][F0][R][GT][G][ID][D][ROT][A'][B][C][SB][S][HX][6] -- pre-reg section 8.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from collections import Counter
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


PREP = _load("d348p", "d348_prep.py")                       # installs memo_load; the alias chain executes once
V60 = _load("d360r", "run_d360_news_gap_short.py")          # T2's construction (its own _loads are memoised through memo_load)
V59 = _load("d359r", "run_d359_loser_rally_short.py")       # T1's construction and the short conventions
assert V59 is V60.V59, "run_d359 loaded twice (memo_load not installed?)"
V58, V53, V49, V50 = V59.V58, V59.V53, V59.V49, V59.V50
V47 = PREP.V47
EB, G22, BR = PREP.EB, PREP.G22, PREP.BR
SEED, X_TARGET = V47.SEED, V47.X_TARGET
CONVS = V47.CONVS
STUDY = 361
GATES = ("G1", "G2")
TRIGGERS = ("T1", "T2")
CELLS = [("G1", "T1"), ("G1", "T2"), ("G2", "T1"), ("G2", "T2")]     # index 0..3 fixes the RNG keys
PRIMARY = ("G1", "T1")
WIN = {"G1": 63, "G2": 200}
HORIZON = 20
EXITS = (("cap", 10), ("cap", 20))
EXIT_NAME = {("cap", 10): "cap10", ("cap", 20): "cap20"}
PRIMARY_EXIT = "cap10"
ARMS = ("gated", "off", "ungated")
ARM = dict(A=1, B=2, C=4, ROT=5)                            # seed arms: A' 1, B 2, C 4 (as D359/D360), the gate rotation 5
T1_PARENT, T2_PARENT = (10, 90), (2, 10)
PREREG = dict(T1=dict(trades=8_085, mean_bp=8.9095), T2=dict(trades=20_621, mean_bp=14.76))     # the pre-reg's rounded figures (section 6 check)
DATA = REPO / "data"
D359_REPORT, D360_REPORT = DATA / "d359_loser_rally_short.json", DATA / "d360_news_gap_short.json"
SELFTEST_TMP = REPO / "temp" / "d361_selftest"
PER_SHARE, BORROW_SCHEME = V49.PER_SHARE, V49.BORROW_SCHEME
run_short, simulate = V59.run_short, V59.simulate
deployed_block, trade_block = V59.deployed_block, V59.trade_block
assert_S_short, perturb_test, bucket_interaction = V59.assert_S_short, V59.perturb_test, V59.bucket_interaction
deployed_subsets, assert_HX, control_C, null_stats, observed_stats, assert_B = (V58.deployed_subsets, V58.assert_HX, V58.control_C,
                                                                                V58.null_stats, V58.observed_stats, V58.assert_B)
assert_C = V60.assert_C
clean = V50.clean


def cell_name(g, tr):
    return f"{g}:{tr}"


def fq(x, nd=2):
    return "-" if x is None else f"{x:+.{nd}f}"


def zeros(x):
    return np.zeros_like(x)


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, stage0=d / "d361_stage0.json", ctrl=str(d / "d361_ctrl_{g}_{tr}_p{part}.json"), report=d / "d361_regime_gated_short.json")


# ------------------------------------------------------------------ the gates
_GATE = {}


def gate_pack(P, name):
    """The gate, vectorised: dict(gate, defined, level, index, d0, Td, on_share, episodes, runs, years). Memoised.
    level: G1 the trailing 63-bar compounded return; G2 index[t-1] / mean(index[t-200..t-1]) - 1 (NaN where undefined)."""
    if name in _GATE:
        return _GATE[name]
    m_f = np.asarray(P["m_f"], float)
    T, m0, w = P["T"], P["m_start"], WIN[name]
    assert np.isfinite(m_f[m0:]).all(), "[GT] m_f undefined after m_start"
    g1 = 1.0 + m_f[m0:]
    index = np.full(T, np.nan)
    index[m0:] = np.cumprod(g1)
    level = np.full(T, np.nan)
    gate = np.zeros(T, bool)
    d0 = m0 + w
    k = T - d0                                                        # windows ending at t-1 for t = d0 .. T-1
    assert k >= 2, "[GT] no defined bars"
    if name == "G1":
        W = np.lib.stride_tricks.sliding_window_view(g1, w)           # W[j] covers bars m0+j .. m0+j+w-1 -> the value at t = m0+j+w
        prod = W.prod(axis=1)[:k]
        level[d0:] = prod - 1.0
        gate[d0:] = prod < 1.0
    else:
        W = np.lib.stride_tricks.sliding_window_view(index[m0:], w)
        mean = W.mean(axis=1)[:k]
        prev = index[d0 - 1:T - 1]
        level[d0:] = prev / mean - 1.0
        gate[d0:] = prev < mean
    defined = np.zeros(T, bool)
    defined[d0:] = True
    eps = episodes_of(gate)
    years = np.asarray(P["years"])
    out = dict(name=name, w=w, d0=d0, Td=int(k), gate=gate, defined=defined, level=level, index=index, on=int(gate.sum()),
               on_share=float(gate[defined].mean()), episodes=eps, runs=[e - s + 1 for s, e in eps],
               years=[sorted(set(int(y) for y in years[s:e + 1])) for s, e in eps],
               dates=[(P["dates"][s], P["dates"][e]) for s, e in eps])
    _GATE[name] = out
    return out


def episodes_of(b):
    """[(start, end)] inclusive of the runs of True in a boolean series."""
    b = np.asarray(b, bool)
    if not b.any():
        return []
    d = np.diff(np.concatenate([[0], b.astype(np.int8), [0]]))
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1
    return [(int(s), int(e)) for s, e in zip(starts, ends)]


def runs_linear(seg):
    return [e - s + 1 for s, e in episodes_of(seg)]


def runs_circular(seg):
    """Run lengths of the boolean series read on a circle (a run straddling the ends is one run): the invariant of a circular shift."""
    seg = np.asarray(seg, bool)
    if seg.all():
        return [int(seg.size)]
    if not seg.any():
        return []
    j = int(np.flatnonzero(~seg)[0])
    return runs_linear(np.roll(seg, -j))


def gate_loop(P, name):
    """[GT]'s second implementation: a plain Python loop over bars, no numpy window, no cumprod."""
    m_f = [float(x) for x in np.asarray(P["m_f"])]
    T, m0, w = P["T"], P["m_start"], WIN[name]
    index = [float("nan")] * T
    cum = 1.0
    for t in range(m0, T):
        cum *= 1.0 + m_f[t]
        index[t] = cum
    level, gate = [float("nan")] * T, [False] * T
    for t in range(m0 + w, T):
        if name == "G1":
            p = 1.0
            for j in range(t - w, t):
                p *= 1.0 + m_f[j]
            level[t], gate[t] = p - 1.0, p < 1.0
        else:
            s = 0.0
            for j in range(t - w, t):
                s += index[j]
            mean = s / w
            level[t], gate[t] = index[t - 1] / mean - 1.0, index[t - 1] < mean
    return np.array(level), np.array(gate, bool)


def assert_GT(P, gp, gate=None, level=None, tol=1e-12, tag="[GT]"):
    """The vectorised gate equals the loop to tol on the level (over the defined bars) and EXACTLY on the boolean; the gate is False
    off its defined range; lagged one bar (the level at t is a function of m_f to t-1: moving m_f[t] leaves level[t] unchanged and moves
    level[t+1]). `gate`/`level` may be perturbed copies ([6])."""
    gate = gp["gate"] if gate is None else gate
    level = gp["level"] if level is None else level
    lv, gl = gate_loop(P, gp["name"])
    d = gp["defined"]
    assert not gate[~d].any(), f"{tag} {gp['name']} on outside its defined range"
    assert np.isfinite(level[d]).all() and not np.isfinite(level[~d]).any(), f"{tag} {gp['name']} level defined on the wrong bars"
    worst = float(np.abs(level[d] - lv[d]).max())
    assert worst < tol, f"{tag} {gp['name']} level differs from the loop ({worst:.2e})"
    assert np.array_equal(gate, gl), f"{tag} {gp['name']} boolean differs from the loop on {int((gate != gl).sum())} bars"
    # the lag: perturb m_f at one defined bar t; the level at t is unchanged, at t+1 it moves
    t = gp["d0"] + gp["Td"] // 2
    m_f = np.array(P["m_f"], float)
    m_f[t] += 1e-3
    gpp = _pack_from(m_f, P, gp["name"])
    assert gpp["level"][t] == level[t] and gpp["level"][t + 1] != level[t + 1], f"{tag} {gp['name']} is not lagged one bar"
    return worst


def _pack_from(m_f, P, name):
    """gate_pack on a substituted m_f, unmemoised (the lag check)."""
    saved = _GATE.pop(name, None)
    try:
        return gate_pack(dict(P, m_f=m_f), name)
    finally:
        _GATE.pop(name, None)
        if saved is not None:
            _GATE[name] = saved


def gate_line(P, gp):
    m_f = np.asarray(P["m_f"])
    d = gp["defined"]
    extra = ""
    if gp["name"] == "G1":
        W = np.lib.stride_tricks.sliding_window_view(m_f[P["m_start"]:], gp["w"]).sum(axis=1)[:gp["Td"]]
        n_diff = int(((W < 0) != gp["gate"][d]).sum())
        extra = f"; the plain (additive) sum of m_f would flip the sign on {n_diff} of {gp['Td']:,} defined bars"
    r = gp["runs"]
    return (f"{gp['name']} (window {gp['w']}): defined from bar {gp['d0']} ({P['dates'][gp['d0']]}), {gp['Td']:,} defined bars; on {gp['on']:,} "
            f"({100 * gp['on_share']:.1f}%); {len(r)} distinct on-episodes, run length min {min(r) if r else 0} median {np.median(r) if r else 0:.0f} "
            f"max {max(r) if r else 0}{extra}")


def episode_lines(P, gp):
    return [f"{i + 1:2d}. {a} .. {b} ({n} bars; {'/'.join(str(y) for y in ys)})" for i, ((a, b), n, ys) in enumerate(zip(gp["dates"], gp["runs"], gp["years"]))]


# ------------------------------------------------------------------ the triggers (the parents' constructions, imported)
_SIG = {}


def triggers(P):
    """{'T1': (sig, score, elig, counts), 'T2': (...)}: T1 from run_d359 (cell (10, 90)), T2 from run_d360's mirror (2, 10) with its exclusions.
    D360's grid memo (~1 GB) is released once T2's mask and kernel score are out."""
    if "T1" in _SIG:
        return _SIG
    _pm, pct_rev, _pv, elig = V59.grids(P)
    sh1 = V59.cell_signal(P, *T1_PARENT)
    _SIG["T1"] = (sh1, pct_rev, elig, dict(events=int(sh1.sum())))
    sh2, c2 = V60.mirror_signal(P, *T2_PARENT)
    G = V60.signal_grids(P)
    V60.assert_XD(sh2, G["XD"])
    V60.assert_V0(sh2, G["V0"], G["NF"])
    sc2 = np.array(G["sc"])
    assert np.array_equal(G["elig"], elig)
    V60._G.clear()                                                    # OPEN, gap, rv, the percentile grids and the exclusion grids: released
    del G
    _SIG["T2"] = (np.ascontiguousarray(sh2), sc2, elig, dict(c2))
    return _SIG


def arms_of(P, g, tr):
    """(gated, off, ungated) event grids for one cell; [G] asserts the partition."""
    sig, sc, elig, _c = triggers(P)[tr]
    gate = gate_pack(P, g)["gate"]
    gated = np.ascontiguousarray(sig & gate[:, None])
    off = np.ascontiguousarray(sig & ~gate[:, None])
    V59.assert_partition(gated, off, sig, tag="[G]")
    return gated, off, sig, sc


def assert_G(P, verbose=True):
    """[G]: with the gate removed the triggers ARE the parents' event matrices (the same imported functions; the counts equal the parents'
    stored event counts read from their report files); every cell's gated and gate-off arms partition the ungated trigger."""
    S = triggers(P)
    d359 = json.loads(D359_REPORT.read_text())
    d360 = json.loads(D360_REPORT.read_text())
    n1 = int(S["T1"][0].sum())
    n2 = int(S["T2"][0].sum())
    e1 = d359["results"][V59.cell_name(*T1_PARENT)]["events"]
    e2 = d360["results"][V60.cell_name(*T2_PARENT)]["mirror"]["events"]
    c2 = d360["G"][V60.cell_name(*T2_PARENT)]["mirror"]
    assert n1 == e1, f"[G] T1 events {n1:,} != D359's stored {e1:,}"
    assert n2 == e2 == c2["events"] and S["T2"][3]["excluded"] == c2["excluded"] and S["T2"][3]["raw"] == c2["raw"], \
        f"[G] T2 events {n2:,} ({S['T2'][3]}) != D360's stored mirror {c2}"
    out = dict(T1=dict(events=n1, stored=e1), T2=dict(events=n2, stored=e2, counts=dict(S["T2"][3])), cells={})
    for g, tr in CELLS:
        gated, off, ung, _sc = arms_of(P, g, tr)
        out["cells"][cell_name(g, tr)] = dict(gated=int(gated.sum()), off=int(off.sum()), ungated=int(ung.sum()))
    if verbose:
        print(f"    [G] with the gate removed T1 is D359's cell (10, 90) event matrix ({n1:,} events == its stored {e1:,}) and T2 is D360's mirror (2, 10) "
              f"({n2:,} events == its stored {e2:,}; raw {c2['raw']:,}, {c2['excluded']} excluded on ex-distribution / zero-volume / no-prior-close days, "
              f"[XD] [V0] re-asserted); gated u gate-off == ungated and disjoint in every cell: "
              + ", ".join(f"{k} {v['gated']:,} + {v['off']:,} = {v['ungated']:,}" for k, v in out["cells"].items()))
    return out


# ------------------------------------------------------------------ [ID] against the parents' stored ledgers
def assert_ID(P, res1, res2, res2_long=None, res1_20=None, res2_20=None, verbose=True):
    """The ungated T1 ledger on cap 10 equals D359's primary (data/d359_loser_rally_short.json results['10:90'].cap10.per_trade: trades,
    mean, median, held half-spread, and observed gross / net) to 1e-9; the ungated T2 SHORT ledger equals D360's mirror LONG ledger
    (results['2:10'].mirror.cap10.per_trade) with the side reversed: the same trade count, the mean and the median NEGATED to 1e-9 (the
    kernel accumulates sgn (v - m): as a long sgn = +1, as a short -1, so every trade's P&L flips sign exactly -- asserted trade for
    trade against a LONG re-run when res2_long is given). Cap 20 beside when given."""
    d359 = json.loads(D359_REPORT.read_text())["results"][V59.cell_name(*T1_PARENT)]
    d360 = json.loads(D360_REPORT.read_text())["results"][V60.cell_name(*T2_PARENT)]["mirror"]
    p1, o1 = d359["cap10"]["per_trade"], d359["observed"]
    pnl1 = V47.pnl_bp(res1)
    m1 = float(pnl1.mean())
    assert len(res1["trades"]) == p1["trades"] == PREREG["T1"]["trades"], f"[ID] T1 {len(res1['trades']):,} trades != D359's {p1['trades']:,}"
    assert abs(m1 - p1["mean_bp"]) < 1e-9, f"[ID] T1 mean {m1:.10f} != D359's stored {p1['mean_bp']:.10f}"
    assert abs(float(np.median(pnl1)) - p1["median_bp"]) < 1e-9, "[ID] T1 median"
    ob1 = observed_stats(res1, P)
    for k in ("gross_bp", "net_bp_PUB", "net_bp_PB", "trades", "entries"):
        assert abs(ob1[k] - o1[k]) < 1e-9, f"[ID] T1 observed {k} {ob1[k]} != D359's {o1[k]}"
    hs1 = V47.two_c(res1["trades"], P["HALF"]["PUB"], P["CLOSE"])[1]
    assert abs(hs1 - p1["held_half"]["PUB"]) < 1e-9, "[ID] T1 held half-spread PUB"
    p2 = d360["cap10"]["per_trade"]
    assert p2["side"] == "long", "[ID] D360's mirror was stored as a long"
    pnl2 = V47.pnl_bp(res2)
    m2 = float(pnl2.mean())
    assert all(t[4] == 1 for t in res2["trades"]), "[ID] a long in the T2 short ledger"
    assert len(res2["trades"]) == p2["trades"] == PREREG["T2"]["trades"], f"[ID] T2 {len(res2['trades']):,} trades != D360's mirror {p2['trades']:,}"
    assert abs(m2 + p2["mean_bp"]) < 1e-9, f"[ID] T2 short mean {m2:.10f} != -(D360's mirror long mean {p2['mean_bp']:.10f})"
    assert abs(float(np.median(pnl2)) + p2["median_bp"]) < 1e-9, "[ID] T2 median"
    hs2 = V47.two_c(res2["trades"], P["HALF"]["PUB"], P["CLOSE"])[1]
    assert abs(hs2 - p2["held_half"]["PUB"]) < 1e-9, "[ID] T2 held half-spread PUB (the same names at the same entries)"
    flip = None
    if res2_long is not None:
        a = sorted((r, e, g, p) for r, e, g, p, _s in res2["trades"])
        b = sorted((r, e, g, -p) for r, e, g, p, _s in res2_long["trades"])
        assert all(t[4] == 0 for t in res2_long["trades"]) and len(a) == len(b), "[ID] the long re-run differs in shape"
        flip = max(abs(x[3] - y[3]) for x, y in zip(a, b)) if a else 0.0
        assert all(x[:3] == y[:3] for x, y in zip(a, b)) and flip == 0.0, f"[ID] the short is not the long with the sign reversed ({flip:.2e})"
    out = dict(T1=dict(trades=len(res1["trades"]), mean_bp=m1, stored_mean_bp=p1["mean_bp"], prereg_mean_bp=PREREG["T1"]["mean_bp"], held_half_PUB=hs1),
               T2=dict(trades=len(res2["trades"]), mean_bp=m2, stored_long_mean_bp=p2["mean_bp"], prereg_mean_bp=PREREG["T2"]["mean_bp"], held_half_PUB=hs2,
                       sign_flip_worst=flip))
    # beside: the parents' OTHER stored cap exits (D359 stored cap10 / inv10 / cap40, D360 cap10 / cap20 / rec20): T1 at cap 40, T2 at cap 20
    for nm, r_, key in (("T1", res1_20, "cap40"), ("T2", res2_20, "cap20")):
        if r_ is None:
            continue
        s_ = (d359 if nm == "T1" else d360)[key]["per_trade"]
        m_ = float(V47.pnl_bp(r_).mean())
        sg = 1.0 if nm == "T1" else -1.0
        assert all(t[2] <= int(key[3:]) for t in r_["trades"]), f"[ID] {nm} {key}: a hold past the cap"
        assert len(r_["trades"]) == s_["trades"] and abs(m_ - sg * s_["mean_bp"]) < 1e-9, f"[ID] {nm} {key}: {len(r_['trades']):,} {m_:.6f} vs stored {s_['trades']:,} {s_['mean_bp']:.6f}"
        out[nm][key] = dict(trades=len(r_["trades"]), mean_bp=m_, stored_mean_bp=s_["mean_bp"])
    if verbose:
        print(f"    [ID] the ungated T1 cap-10 ledger == D359's primary: {len(res1['trades']):,} trades, mean {m1:+.6f} bp == stored {p1['mean_bp']:+.6f} to 1e-9 "
              f"(median, held half-spread PUB {hs1:.3f}, deployed gross {ob1['gross_bp']:+.4f} and net PUB {ob1['net_bp_PUB']:+.4f} bp/bar also to 1e-9); the "
              f"pre-registration's rounded +{PREREG['T1']['mean_bp']} differs from the stored value by {abs(m1 - PREREG['T1']['mean_bp']):.4f} bp (a transcription "
              f"in the pre-reg; the stored file is the reference). The ungated T2 SHORT cap-10 ledger == D360's mirror LONG with the side reversed: "
              f"{len(res2['trades']):,} trades, mean {m2:+.6f} == -({p2['mean_bp']:+.6f}) to 1e-9 (median and held half-spread PUB {hs2:.3f} too"
              + (f"; trade for trade the short's P&L is the long's negated to {flip:.1f}" if flip is not None else "") + ")"
              + (f"; beside, the parents' other stored cap exits: T1 cap 40 {out['T1']['cap40']['trades']:,} trades {out['T1']['cap40']['mean_bp']:+.4f} == D359's "
                 f"stored {d359['cap40']['per_trade']['mean_bp']:+.4f}, T2 cap 20 {out['T2']['cap20']['trades']:,} {out['T2']['cap20']['mean_bp']:+.4f} == "
                 f"-({d360['cap20']['per_trade']['mean_bp']:+.4f}), each to 1e-9" if res1_20 is not None and res2_20 is not None else ""))
    return out


# ------------------------------------------------------------------ Stage 0: the premise
_F20 = {}


def forward20(P):
    """F20[t, i] = sum_{j = 0..19} (r1T - m_f)[t + j, i], non-priced / undefined bars counting 0 (V47.forward_excess_grid's convention
    without the open fill: the cohort's drift is not a trade), NaN where the window does not fit. Memoised."""
    if "F" in _F20:
        return _F20["F"]
    r1T, m_f, finT = np.asarray(P["r1T"]), np.asarray(P["m_f"]), np.asarray(P["finT"])
    T, n = r1T.shape
    ex = np.where(finT & np.isfinite(r1T) & np.isfinite(m_f)[:, None], r1T - m_f[:, None], 0.0)
    C = np.concatenate([np.zeros((1, n)), np.cumsum(ex, axis=0)])
    del ex
    F = np.full((T, n), np.nan)
    t = np.arange(0, T - HORIZON + 1)
    F[t] = C[t + HORIZON] - C[t]
    del C
    _F20["F"] = F
    return F


def f20_direct(P, t, i):
    r1T, m_f, finT = P["r1T"], P["m_f"], P["finT"]
    s = 0.0
    for j in range(t, t + HORIZON):
        if finT[j, i] and np.isfinite(r1T[j, i]) and np.isfinite(m_f[j]):
            s += float(r1T[j, i]) - float(m_f[j])
    return s


def stage0_groups(P):
    """Name-bar groups on eligible bars whose forward window fits: the loser cohort (bottom_10), all eligible, the top decile."""
    pct_mom, _pr, _pv, elig = V59.grids(P)
    T = P["T"]
    fits = np.zeros(T, bool)
    fits[:T - HORIZON + 1] = True
    ok = elig & fits[:, None]
    with np.errstate(invalid="ignore"):
        return {"bottom_10": ok & (pct_mom <= 10.0), "elig_all": ok, "top_10": ok & (pct_mom >= V59.TOP_DECILE)}


def cond_drift(F, mask):
    k = int(mask.sum())
    return dict(n=k, bp=float(F[mask].sum() / k) * 1e4 if k else None)


def drift_independent(F, mask):
    return float(np.nanmean(np.where(mask, F, np.nan))) * 1e4


def blocks_of(P, gp):
    """Non-overlapping 20-bar blocks from the gate's first defined bar; the block start must have a defined level and a fitting window."""
    T = P["T"]
    return [b for b in range(gp["d0"], T - HORIZON + 1, HORIZON)]


def stage0_gate(P, gp, rng_seed):
    """The two numbers per gate (and the beside lines): conditional forward-20 drifts on/off, the block correlation with its shuffle."""
    F = forward20(P)
    groups = stage0_groups(P)
    gate, d = gp["gate"], gp["defined"]
    on, off = (gate & d)[:, None], (~gate & d)[:, None]
    drift, worst = {}, 0.0
    for g, m in groups.items():
        drift[g] = {}
        for lab, cm in (("on", on), ("off", off), ("all", d[:, None])):
            mm = m & cm
            drift[g][lab] = cond_drift(F, mm)
            if drift[g][lab]["bp"] is not None:
                worst = max(worst, abs(drift_independent(F, mm) - drift[g][lab]["bp"]))
    # the blocks
    bl = blocks_of(P, gp)
    coh = groups["bottom_10"]
    xs, ys, empty = [], [], 0
    for b in bl:
        row = coh[b]
        if not row.any():
            empty += 1
            continue
        xs.append(gp["level"][b])
        ys.append(float(F[b][row].mean()))
    x, y = np.array(xs), np.array(ys)
    nb = x.size
    assert nb >= 10 and np.isfinite(x).all() and np.isfinite(y).all(), "[D] too few blocks or an undefined block level"
    r = float(np.corrcoef(x, y)[0, 1])
    rng = np.random.default_rng(rng_seed)
    r_sh = float(np.corrcoef(x[rng.permutation(nb)], y)[0, 1])
    se = 1.0 / np.sqrt(nb - 1.0)
    more = np.array([np.corrcoef(x[rng.permutation(nb)], y)[0, 1] for _ in range(999)])
    # the market's own forward-20 return, on/off
    m_f = np.asarray(P["m_f"], float)
    T = P["T"]
    Wsum = np.lib.stride_tricks.sliding_window_view(m_f, HORIZON).sum(axis=1)           # index t: bars t .. t+19
    Wcmp = np.lib.stride_tricks.sliding_window_view(1.0 + m_f, HORIZON).prod(axis=1) - 1.0
    fits = np.zeros(T, bool)
    fits[:T - HORIZON + 1] = True
    mk = {}
    for lab, cm in (("on", gate & d & fits), ("off", ~gate & d & fits)):
        idx = np.flatnonzero(cm)
        mk[lab] = dict(n=int(idx.size), sum_bp=float(Wsum[idx].mean()) * 1e4 if idx.size else None, compounded_bp=float(Wcmp[idx].mean()) * 1e4 if idx.size else None)
    return dict(drift=drift, D_worst=worst,
                block=dict(n_blocks=nb, empty_blocks=empty, horizon=HORIZON, corr=r, corr_shuffled=r_sh, se=se, z_shuffled=r_sh / se, shuffle_seed=list(rng_seed),
                           shuffle_p50=float(np.median(more)), shuffle_p95=float(np.quantile(np.abs(more), .95)), x_mean=float(x.mean()), y_mean_bp=float(y.mean()) * 1e4,
                           level="63-bar trailing compounded return" if gp["name"] == "G1" else "index[t-1] / mean(index[t-200..t-1]) - 1"),
                market_fwd20=mk, on_share=gp["on_share"], on=gp["on"], Td=gp["Td"], d0=gp["d0"], d0_date=P["dates"][gp["d0"]], episodes=len(gp["runs"]),
                runs=gp["runs"], run_min=min(gp["runs"]) if gp["runs"] else None, run_median=float(np.median(gp["runs"])) if gp["runs"] else None,
                run_max=max(gp["runs"]) if gp["runs"] else None, episode_dates=gp["dates"], episode_years=gp["years"], _xy=(x, y))


def assert_D(P, S, gp, rng, tol=1e-12, k=300, tag="[D]"):
    """The conditional drifts equal the independent masked mean (recomputed here on the masks) to tol; F20 equals a direct per-name-bar
    loop on k sampled cohort name-bars to 1e-12; the block correlation on shuffled levels is within 3 SE of zero."""
    F = forward20(P)
    groups = stage0_groups(P)
    gate, d = gp["gate"], gp["defined"]
    worst = 0.0
    for g, m in groups.items():
        for lab, cm in (("on", gate & d), ("off", ~gate & d), ("all", d)):
            if S["drift"][g][lab]["bp"] is None:
                continue
            worst = max(worst, abs(drift_independent(F, m & cm[:, None]) - S["drift"][g][lab]["bp"]))
    assert worst < tol, f"{tag} conditional drift differs from the independent masked mean ({worst:.2e})"
    ev = np.argwhere(groups["bottom_10"] & d[:, None])
    pick = ev[rng.choice(len(ev), size=min(k, len(ev)), replace=False)]
    wf = max(abs(F[t, i] - f20_direct(P, t, i)) for t, i in pick)
    assert wf < tol, f"{tag} F20 differs from the direct loop ({wf:.2e})"
    b = S["block"]
    assert abs(b["z_shuffled"]) < 3.0, f"{tag} the block correlation on shuffled levels is {b['z_shuffled']:+.2f} SE from zero"
    return worst, wf, len(pick)


def stage0_compute(P):
    out = {}
    for g in GATES:
        gp = gate_pack(P, g)
        out[g] = stage0_gate(P, gp, [SEED, STUDY, 0, 0])
    return out


def print_stage0(P, S0):
    print("\n  STAGE 0 -- the premise. Per gate: the loser cohort's (pct_mom <= 10, eligible name-bars) hedged forward-20 drift sum_{t..t+19} (r1T - m_f), bp per "
          "name-bar [name-bars], with the gate ON / OFF (lagged: gate[t] uses m_f to t-1; the drift starts at bar t);")
    print("  the correlation between the gate's level at the start of each non-overlapping 20-bar block and the cohort's mean drift over that block; the on-share, "
          "episodes and run lengths; beside, the floored market's own forward-20 return (the additive sum the hedge pays / compounded) ON vs OFF.")
    print("  %-4s | %-38s | %-38s | %-38s" % ("gate", "bottom_10 on / off / all", "elig_all on / off / all", "top_10 on / off / all"))
    for g, S in S0.items():
        cells = []
        for grp in ("bottom_10", "elig_all", "top_10"):
            d = S["drift"][grp]
            cells.append(" / ".join(f"{d[l]['bp']:+.1f}[{d[l]['n']:,}]" if d[l]["bp"] is not None else "-" for l in ("on", "off", "all")))
        print("  %-4s | %-38s | %-38s | %-38s" % (g, *cells))
    for g, S in S0.items():
        b, mk = S["block"], S["market_fwd20"]
        print(f"  {g}: blocks {b['n_blocks']} ({b['empty_blocks']} without a cohort name), level = {b['level']}: corr {b['corr']:+.3f}; on shuffled levels {b['corr_shuffled']:+.3f} "
              f"(SE {b['se']:.3f}, z {b['z_shuffled']:+.2f}; 999 more shuffles: |r| p95 {b['shuffle_p95']:.3f}); on-share {100 * S['on_share']:.1f}% of {S['Td']:,} defined bars "
              f"from {S['d0_date']}; {S['episodes']} episodes, runs min {S['run_min']} median {S['run_median']:.0f} max {S['run_max']}; market forward-20 ON "
              f"{fq(mk['on']['sum_bp'], 1)} sum / {fq(mk['on']['compounded_bp'], 1)} compounded bp [{mk['on']['n']:,}], OFF {fq(mk['off']['sum_bp'], 1)} / "
              f"{fq(mk['off']['compounded_bp'], 1)} [{mk['off']['n']:,}]")


def stage_stage0(P, paths):
    S0 = stage0_compute(P)
    lines = []
    for g in GATES:
        gp = gate_pack(P, g)
        w = assert_GT(P, gp)
        lines.append(f"{gate_line(P, gp)} (loop to {w:.1e})")
        wd, wf, k = assert_D(P, S0[g], gp, np.random.default_rng([SEED, STUDY, 0, 1]))
        lines.append(f"[D] {g}: conditional drifts == the independent masked mean to {wd:.1e}; F20 == the direct loop on {k} sampled cohort name-bars to {wf:.1e}; "
                     f"block correlation on shuffled levels {S0[g]['block']['corr_shuffled']:+.3f} (z {S0[g]['block']['z_shuffled']:+.2f}) within 3 SE of zero")
    for l in lines:
        print(f"    [GT] {l}" if not l.startswith("[D]") else f"    {l}")
    print_stage0(P, S0)
    for g in GATES:
        print(f"  {g} episodes: " + "; ".join(episode_lines(P, gate_pack(P, g))))
    out = dict(study=STUDY, note="D361 Stage 0: the gate's premise. F20 = the 20-bar hedged forward drift from bar t (non-priced bars 0); groups on eligible "
                                  "name-bars whose window fits, restricted to the gate's defined bars; blocks of 20 bars from the gate's first defined bar, the "
                                  "level at the block start vs the mean F20 of the cohort at that start.",
               gates={g: {k: v for k, v in S0[g].items() if not k.startswith("_")} for g in GATES}, windows=WIN, horizon=HORIZON, m_start=P["m_start"],
               down_years=P["down_years"], floored_market_by_year=P["yr_ret"], index="cumprod(1 + m_f) from m_start (m_f a simple equal-weight return)")
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["stage0"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['stage0']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


# ------------------------------------------------------------------ the gate rotation: [ROT]
def rotate_gate(gp, k):
    """The gate boolean circularly shifted by k over its defined bars (undefined bars stay False)."""
    out = np.zeros_like(gp["gate"])
    out[gp["d0"]:] = np.roll(gp["gate"][gp["d0"]:], int(k))
    return out


def assert_ROT(gp, rot, k, tag="[ROT]"):
    """The rotated gate keeps the on-share EXACTLY and the CIRCULAR run-length multiset exactly (the invariant of a circular shift); it is
    False off the defined range; it is never the observed gate; the offset is in [1, Td-1]. The wrap: the rotated series read linearly
    equals the circular multiset, or the circular multiset with exactly ONE run split in two at the wrap (asserted to be one of the two;
    the split is reported per draw, never silently accepted as 'kept'). The LINEAR multiset of the observed is kept iff no split."""
    Td = gp["Td"]
    assert 1 <= k <= Td - 1, f"{tag} offset {k} outside [1, {Td - 1}]"
    obs_seg, rot_seg = gp["gate"][gp["d0"]:], rot[gp["d0"]:]
    assert not rot[:gp["d0"]].any(), f"{tag} on outside the defined range"
    assert int(rot_seg.sum()) == int(obs_seg.sum()), f"{tag} on-share changed: {int(rot_seg.sum())} vs {int(obs_seg.sum())}"
    assert not np.array_equal(rot, gp["gate"]), f"{tag} the rotated gate is the observed gate"
    circ_o, circ_r = Counter(runs_circular(obs_seg)), Counter(runs_circular(rot_seg))
    assert circ_o == circ_r, f"{tag} the circular run-length multiset changed"
    lin_o, lin_r = Counter(runs_linear(obs_seg)), Counter(runs_linear(rot_seg))
    split = lin_r != circ_o
    if split:
        diff = lin_r - circ_o                                          # the two wrap pieces
        gone = circ_o - lin_r                                          # the one run they came from
        assert sum(diff.values()) == 2 and sum(gone.values()) == 1 and sum(l * c for l, c in diff.items()) == next(iter(gone)), \
            f"{tag} the linear runs are not the circular runs with one run split at the wrap"
        assert bool(rot_seg[0]) and bool(rot_seg[-1]), f"{tag} a split without the wrap on an on-run"
    return dict(offset=int(k), wrap_split=bool(split), linear_kept=bool(lin_r == lin_o), n_runs=len(runs_linear(rot_seg)))


def rot_offsets(gp, draws, rng):
    """`draws` DISTINCT offsets in [1, Td-1], uniformly without replacement (a with-replacement draw of 200 in ~5,000 collides with
    probability ~98%; the pre-reg wants 200 distinct)."""
    assert draws <= gp["Td"] - 1, f"[ROT] {draws} draws exceed the {gp['Td'] - 1} admissible offsets"
    return rng.choice(np.arange(1, gp["Td"]), size=draws, replace=False)


# ------------------------------------------------------------------ [A'] within the gate
def aprime_gate_draw(sh, sc, elig, gate, rng):
    """A' within the gate: EB.rotate_signals on the mask elig & gate (every rotated event lands on an eligible bar on which the gate is
    on), the score rotated with the signal; D351's assertions on that mask."""
    mask = np.ascontiguousarray(elig & gate[:, None])
    assert not (sh & ~mask).any(), "[A'] an observed gated event off the mask"
    sl, ss, sc_ = EB.rotate_signals(zeros(sh), sh, sc, mask, rng)
    assert not sl.any(), "[A'] a long appeared in the rotation"
    assert not (ss & ~mask).any(), "[A'] a rotated event landed off elig & gate"
    assert not (ss & ~elig).any() and not (ss & ~gate[:, None]).any(), "[A'] a rotated event off the floor or off the gate"
    assert np.array_equal(ss.sum(axis=0), sh.sum(axis=0)), "[A'] per-name event count changed"
    return ss, sc_


# ------------------------------------------------------------------ the arms in the report
def gate_exposure(res, gp):
    d = gp["defined"]
    return dict(bars_gate_defined=int(d.sum()), bars_with_position=int((res["held"] > 0)[d].sum()), exposure_gate_defined=float((res["held"] > 0)[d].mean()),
                gate_on_share=gp["on_share"])


def arm_report(P, sig, sc, elig, gp, with_groups, exits=EXITS):
    out = dict(events=int(sig.sum()))
    for e, cap in exits:
        nm = EXIT_NAME[(e, cap)]
        res = run_short(P, sig, sc, e, cap)
        V53.assert_series_defs(res)
        hx = dict(hedged=assert_HX(res, P, "book_dep_x", hedged=True), unhedged=assert_HX(res, P, "book_dep", hedged=False))
        dep = deployed_block(res, P)
        dep["splits_hedged"] = deployed_subsets(res, P, res["book_dep_x"])
        dep["gate"] = gate_exposure(res, gp)
        trd = trade_block(P, res, elig, 1, with_groups and nm == PRIMARY_EXIT)
        out[nm] = dict(deployed=dep, per_trade=trd, hx=hx, accounting=V49.event_accounting(P, sig, res, cap=cap), res=res)
    return out


def drop_res(d):
    for k in list(d):
        if isinstance(d[k], dict) and "res" in d[k]:
            d[k].pop("res")


def by_episode(P, gp, res):
    """The gated ledger split by on-episode: a trade belongs to the episode containing its entry bar e0 (the signal bar, gate on)."""
    tr = res["trades"]
    pnl = V47.pnl_bp(res)
    e0 = np.array([t[1] for t in tr])
    out = []
    covered = 0
    for (s, e), (da, db), ys in zip(gp["episodes"], gp["dates"], gp["years"]):
        m = (e0 >= s) & (e0 <= e)
        covered += int(m.sum())
        out.append(dict(start=da, end=db, bars=e - s + 1, years=ys, trades=int(m.sum()), mean_bp=float(pnl[m].mean()) if m.any() else None,
                        median_bp=float(np.median(pnl[m])) if m.any() else None, sum_bp=float(pnl[m].sum())))
    assert covered == len(tr), f"by_episode: {covered} of {len(tr)} trades fall in an on-episode"
    return out


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    print(f"    [K] [F0] [R] via d348_prep (cache {'HIT' if P['cache_hit'] else 'BUILD'} {P['cache_key']}); the kernel is D345's (EB.simulate_event), the fill the next open")
    g0, t0n = PRIMARY
    ci0 = CELLS.index(PRIMARY)
    # [GT]
    worst_gt = {}
    for g in GATES:
        gp = gate_pack(P, g)
        worst_gt[g] = assert_GT(P, gp)
        print(f"    [GT] {gate_line(P, gp)}; equals a plain Python loop over bars to {worst_gt[g]:.1e} on the level and exactly on the boolean; lagged one bar "
              f"(moving m_f[t] leaves the level at t unchanged and moves t+1)")
        print("         episodes: " + "; ".join(episode_lines(P, gp)))
    print(f"        ({el()})")
    # [G]
    g = assert_G(P)
    S = triggers(P)
    elig = S["T1"][2]
    print(f"        ({el()})")
    # [ID]
    sh1, sc1 = S["T1"][0], S["T1"][1]
    sh2, sc2 = S["T2"][0], S["T2"][1]
    r1 = run_short(P, sh1, sc1, "cap", 10)
    r2 = run_short(P, sh2, sc2, "cap", 10)
    r2L = simulate(P, sh2, sc2, "cap", 10, 0)
    r1_40 = run_short(P, sh1, sc1, "cap", 40)                        # D359 stored cap 40 (not cap 20); D360 stored cap 20
    r2_20 = run_short(P, sh2, sc2, "cap", 20)
    idd = assert_ID(P, r1, r2, res2_long=r2L, res1_20=r1_40, res2_20=r2_20)
    del r2L, r1_40, r2_20
    print(f"        ({el()})")
    # [D] Stage 0
    S0 = stage0_compute(P)
    for gname in GATES:
        wd, wf, k = assert_D(P, S0[gname], gate_pack(P, gname), np.random.default_rng([SEED, STUDY, 0, 1]))
        print(f"    [D] {gname}: Stage 0's conditional drifts (masked sum / count) equal an independent np.where + nanmean to {wd:.1e}; F20 equals a direct per-name-bar "
              f"loop on {k} sampled cohort name-bars to {wf:.1e}; the block correlation recomputed on block-shuffled levels (seed {S0[gname]['block']['shuffle_seed']}) "
              f"is {S0[gname]['block']['corr_shuffled']:+.3f} = {S0[gname]['block']['z_shuffled']:+.2f} SE, within 3 SE of zero (observed {S0[gname]['block']['corr']:+.3f} "
              f"on {S0[gname]['block']['n_blocks']} blocks)")
    print_stage0(P, S0)
    print(f"        ({el()})")
    # the primary cell on both exits
    gp0 = gate_pack(P, g0)
    gated, off, ung, sc = arms_of(P, g0, t0n)
    RES = {EXIT_NAME[(e, cap)]: run_short(P, gated, sc, e, cap) for e, cap in EXITS}
    res = RES[PRIMARY_EXIT]
    tr = res["trades"]
    assert tr and all(t[4] == 1 for t in tr) and all(t[2] <= 10 for t in tr), "[K] a long or an over-cap hold in the primary ledger"
    assert all(t[2] <= 20 for t in RES["cap20"]["trades"]), "[K] cap-20 held past the cap"
    assert all(gp0["gate"][t[1]] for t in tr), "[K] a gated trade entered on a gate-off bar"
    acc = V49.event_accounting(P, gated, res, cap=10)
    obs = observed_stats(res, P)
    ge = gate_exposure(res, gp0)
    print(f"    check: primary {cell_name(*PRIMARY)} cap 10: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + "
          f"{acc['unpriced']:,} unpriced; trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end; every entry bar is gate-on; per trade "
          f"{obs['trade_mean_bp']:+.2f} bp; exposure {100 * obs['exposure']:.1f}% of the kernel's defined bars, {100 * ge['exposure_gate_defined']:.1f}% of the gate's "
          f"{ge['bars_gate_defined']:,} defined bars (gate on {100 * ge['gate_on_share']:.1f}%)")
    # [SB]
    rng = np.random.default_rng([SEED, STUDY, 5])
    pt, htb, rate = V49.borrow_of(P, tr)
    idx_sb, worst_b = V49.check_borrow(P, tr, pt, htb, rng, k=200)
    assert (rate[htb] == BR.HTB_BPS).all() and (rate[~htb] == BR.GC_BPS).all(), "[SB] rates"
    print(f"    [SB] BORROW: on {len(idx_sb)} sampled short trades the per-trade borrow equals the rule x bars held / 252 to {worst_b:.1e}, and every HTB flag agrees "
          f"with the F0-window / ${BR.PX_HTB:.0f} rule; HTB on {int(htb.sum())} of {len(tr):,} ({100 * htb.mean():.2f}%); mean borrow {pt.mean():.2f} bp per trade")
    # [HX]
    lines = []
    for nm, r in RES.items():
        V53.assert_series_defs(r)
        hx = assert_HX(r, P, "book_dep_x", hedged=True)
        hu = assert_HX(r, P, "book_dep", hedged=False)
        lines.append(f"{nm} {hx['worst']:.0e}/{hu['worst']:.0e} ({hx['uncovered']} tail)")
    print(f"    [HX] hedged deployed x held == the ledger's sgn(v - m) per bar and unhedged x held == sgn v per bar, to 1e-12 on every covered bar (open tail "
          f"excluded, contiguous), the hedged rebuild sums to the ledger to 1e-9; primary x both exits: " + "; ".join(lines) + f" ({el()})")
    # [ROT] on 5 draws
    rngR = np.random.default_rng([SEED, STUDY, ci0, ARM["ROT"], 0])
    offs = rot_offsets(gp0, 5, rngR)
    rot_info, R_ = [], []
    for k in offs:
        rot = rotate_gate(gp0, k)
        rot_info.append(assert_ROT(gp0, rot, k))
        R_.append(null_stats(run_short(P, np.ascontiguousarray(ung & rot[:, None]), sc, "cap", 10), P))
    lin_obs = Counter(runs_linear(gp0["gate"][gp0["d0"]:])) == Counter(runs_circular(gp0["gate"][gp0["d0"]:]))
    print(f"    [ROT] 5 rotations of {g0} (offsets {[int(k) for k in offs]}, distinct, in [1, {gp0['Td'] - 1}]): the on-share kept exactly ({gp0['on']:,} on), the CIRCULAR "
          f"run-length multiset kept exactly, never the observed gate, off outside the defined range; the wrap split one run in {sum(r['wrap_split'] for r in rot_info)} "
          f"of 5 draws (the linear multiset kept in {sum(r['linear_kept'] for r in rot_info)}; the observed gate's own linear runs {'equal' if lin_obs else 'do NOT equal'} "
          f"its circular runs); per trade " + ", ".join(f"{r['trade_mean_bp']:+.2f}" for r in R_) + f" bp ({', '.join(f'{r['trades']:,}' for r in R_)} trades) vs observed "
          f"{obs['trade_mean_bp']:+.2f} ({el()})")
    # [A'] [B] on 2 draws of the primary
    PB = V53.b_pool_P(P, elig)
    rngA = np.random.default_rng([SEED, STUDY, ci0, ARM["A"], 0])
    rngB = np.random.default_rng([SEED, STUDY, ci0, ARM["B"], 0])
    A_, B_ = [], []
    rA_keep = None
    for d in range(2):
        ss, sc_ = aprime_gate_draw(gated, sc, elig, gp0["gate"], rngA)
        rA = run_short(P, ss, sc_, "cap", 10)
        A_.append(null_stats(rA, P))
        sB = V47.control_b_signal(PB, gated, rngB)
        keptB, shortB = assert_B(P, PB, gated, sB, elig)
        assert all(gp0["gate"][t] for t in np.flatnonzero(sB.any(axis=1))), "[B] a replacement on a gate-off day"
        B_.append(null_stats(run_short(P, sB, sc, "cap", 10), P))
        if d == 0:
            rA_keep = rA
    fm = lambda xs, key, f: ", ".join(format(x[key], f) for x in xs)
    print(f"    [A'] 2 draws within the gate: every rotated event on an eligible bar with the gate ON (mask elig & gate), every name's event count kept, no long, the "
          f"score rotated with the signal, deployed series NaN-free; per trade {fm(A_, 'trade_mean_bp', '+.2f')} bp ({fm(A_, 'trades', ',')} trades) vs observed "
          f"{obs['trade_mean_bp']:+.2f} ({el()})")
    print(f"    [B] every event keeps its date (a gate-on day) and rsi bucket; replacements are eligible names with a DEFINED rsi percentile, never an event name; "
          f"kept == the pool shortfall ({keptB} of {int(gated.sum()):,}); per trade {fm(B_, 'trade_mean_bp', '+.2f')} bp")
    # [S]
    worst_s, n_s, n_fell, n_rose, worst_m = assert_S_short(P, rA_keep["trades"], np.random.default_rng([SEED, STUDY, 2]))
    pert = perturb_test(P, gated, sc, 1, res, -1.0)
    print(f"    [S] SIGN IN MONEY on the SHORT: {n_s} sampled A' trades equal the open-fill recomputation against the floored market to {worst_s:.1f} (bit-identical); "
          f"a short on a name that fell pays positively ({n_fell} fell, {n_rose} rose, of {n_s}); the LONG of the same path pays the opposite amount to {worst_m:.1f}; "
          f"+50 bp on r1T[{pert['bar']}, {pert['row']}] ({pert['symbol']} {pert['date']}, bar 2 of a {pert['age']}-bar short) re-simulated on a perturbed A3 moves that "
          f"trade by {pert['dpnl']:+.3f} bp and no other, and the deployed series by {pert['delta']:.4f} = -50 / {pert['n_open']} open, no other bar ({el()})")
    # [C]
    pnl = V47.pnl_bp(res)
    cC = control_C(pnl, np.random.default_rng([SEED, STUDY, ci0, ARM["C"]]))
    z = assert_C(cC)
    print(f"    [C] control C (1,000 random directions on the primary cap-10 ledger): mean {cC['mean']:+.3f} bp (se {cC['se']:.3f}, z {z:+.2f}) within 3 SE of zero; "
          f"p50 {cC['p50']:+.2f} p95 {cC['p95']:+.2f} max {cC['max']:+.2f}; observed {pnl.mean():+.2f} {'above' if cC['above'] else 'NOT above'} p95")
    # [6]
    broke = []
    try:                                                              # [GT] on a perturbed gate (one defined bar flipped)
        g6 = gp0["gate"].copy()
        g6[gp0["d0"] + 10] = not g6[gp0["d0"] + 10]
        assert_GT(P, gp0, gate=g6)
    except AssertionError as e:
        assert "[GT]" in str(e)
        broke.append("GT")
    try:                                                              # [ROT] on a rotation that changes the on-share
        r6 = rotate_gate(gp0, int(offs[0]))
        j = int(np.flatnonzero(~r6[gp0["d0"]:])[0]) + gp0["d0"]
        r6[j] = True
        assert_ROT(gp0, r6, int(offs[0]))
    except AssertionError as e:
        assert "[ROT]" in str(e)
        broke.append("ROT")
    try:                                                              # [ID] on a perturbed ledger (+1 bp on one trade)
        r6 = dict(r1, trades=[(r, e, a, p + (1e-4 if j == 0 else 0.0), sd) for j, (r, e, a, p, sd) in enumerate(r1["trades"])])
        assert_ID(P, r6, r2, verbose=False)
    except AssertionError as e:
        assert "[ID]" in str(e)
        broke.append("ID")
    try:                                                              # [S] on a sign-flipped ledger
        assert_S_short(P, [(r, e, a, -p, sd) for r, e, a, p, sd in rA_keep["trades"]], np.random.default_rng(6))
    except AssertionError as e:
        assert "[S]" in str(e)
        broke.append("S")
    try:                                                              # [D] with a perturbed drift table
        S6 = dict(S0[g0], drift={k: {l: dict(v) for l, v in d.items()} for k, d in S0[g0]["drift"].items()})
        S6["drift"]["bottom_10"]["on"]["bp"] += 1e-6
        assert_D(P, S6, gp0, np.random.default_rng(6))
    except AssertionError as e:
        assert "[D]" in str(e)
        broke.append("D")
    assert broke == ["GT", "ROT", "ID", "S", "D"], f"[6] raised: {broke}"
    print("    [6] [GT] raises on a perturbed gate (one defined bar flipped); [ROT] raises on a rotation that changes the on-share (one bar switched on); [ID] raises "
          "on a perturbed ledger (+1 bp on one trade); [S] raises on a sign-flipped ledger; [D] raises on a perturbed drift table (+1e-6 bp)")
    (SELFTEST_TMP / "selftest_summary.json").write_text(json.dumps(clean(dict(G=g, ID=idd, C=cC, observed=obs, gate_exposure=ge, rot=rot_info,
                                                                                stage0={k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in S0.items()})), indent=1))
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_cell(P, g, tr, draws, draws_rot, part, paths):
    ci = CELLS.index((g, tr))
    gp = gate_pack(P, g)
    assert_GT(P, gp)
    gated, off, ung, sc = arms_of(P, g, tr)
    elig = triggers(P)[tr][2]
    res = run_short(P, gated, sc, "cap", 10)
    obs = observed_stats(res, P)
    ge = gate_exposure(res, gp)
    print(f"\n  {cell_name(g, tr)} part {part}: {int(gated.sum()):,} gated events (of {int(ung.sum()):,}) -> {obs['trades']:,} trades, {obs['entries']:,} entries; per trade "
          f"{obs['trade_mean_bp']:+.2f} bp; deployed gross {obs['gross_bp']:+.2f} net PUB {obs['net_bp_PUB']:+.2f} bp/bar (Sharpe {obs['sharpe_net_PUB']:+.3f}), exposure "
          f"{100 * obs['exposure']:.1f}% (gate-defined {100 * ge['exposure_gate_defined']:.1f}%); gate on {100 * gp['on_share']:.1f}%, {len(gp['runs'])} episodes")
    PB = V53.b_pool_P(P, elig)
    seeds = dict(ROT=[SEED, STUDY, ci, ARM["ROT"], part], A=[SEED, STUDY, ci, ARM["A"], part], B=[SEED, STUDY, ci, ARM["B"], part])
    rngR, rngA, rngB = (np.random.default_rng(seeds[k]) for k in ("ROT", "A", "B"))
    keys = ("gross_bp", "net_bp_PUB", "sharpe_net_PUB", "net_bp_PB", "trade_mean_bp", "trades", "exposure")
    # the gate rotation (load-bearing)
    offs = rot_offsets(gp, draws_rot, rngR)
    R_, rot_info = [], []
    tR = 0.0
    ts = time.time()
    for d, k in enumerate(offs):
        t1 = time.time()
        rot = rotate_gate(gp, k)
        rot_info.append(assert_ROT(gp, rot, k))
        R_.append(null_stats(run_short(P, np.ascontiguousarray(ung & rot[:, None]), sc, "cap", 10), P))
        tR += time.time() - t1
        if (d + 1) % 20 == 0 or d + 1 == draws_rot:
            print(f"    {cell_name(g, tr)}: rotation {d + 1}/{draws_rot} ({time.time() - ts:.0f}s; {tR / (d + 1):.2f} s/draw)", flush=True)
    A_, B_, keptB = [], [], []
    tA = tB = 0.0
    ts = time.time()
    for d in range(draws):
        t1 = time.time()
        ss, sc_ = aprime_gate_draw(gated, sc, elig, gp["gate"], rngA)
        A_.append(null_stats(run_short(P, ss, sc_, "cap", 10), P))
        t2 = time.time()
        sB = V47.control_b_signal(PB, gated, rngB)
        kb, _ = assert_B(P, PB, gated, sB, elig)
        keptB.append(kb)
        B_.append(null_stats(run_short(P, sB, sc, "cap", 10), P))
        tA += t2 - t1
        tB += time.time() - t2
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {cell_name(g, tr)}: A'/B {d + 1}/{draws} ({time.time() - ts:.0f}s; A' {tA / (d + 1):.2f} s/draw, B {tB / (d + 1):.2f})", flush=True)
    out = dict(study=STUDY, gate=g, trigger=tr, cell=cell_name(g, tr), cell_index=ci, exit=PRIMARY_EXIT, draws=draws, draws_rot=draws_rot, part=part, seeds=seeds,
               events=int(gated.sum()), events_ungated=int(ung.sum()), observed=obs, gate_exposure=ge,
               gate_info=dict(Td=gp["Td"], d0=gp["d0"], on=gp["on"], on_share=gp["on_share"], episodes=len(gp["runs"]), runs=gp["runs"]),
               control_rot={k: [x[k] for x in R_] for k in keys}, rot_offsets=[int(k) for k in offs], rot_wrap_split=[r["wrap_split"] for r in rot_info],
               rot_linear_kept=[r["linear_kept"] for r in rot_info],
               control_A_prime={k: [x[k] for x in A_] for k in keys}, control_B={k: [x[k] for x in B_] for k in keys}, B_kept=keptB,
               A_mask="elig & gate (per-name rotation within the gate-on eligible bars)", B_pool="elig & isfinite(PCT rsi), same day, same rsi bucket",
               seconds_per_draw=dict(ROT=tR / max(draws_rot, 1), A=tA / max(draws, 1), B=tB / max(draws, 1)), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["ctrl"].format(g=g, tr=tr, part=part))
    f.write_text(json.dumps(clean(out)))
    msg = f"  wrote {f}:"
    if draws_rot:
        r = np.array(out["control_rot"]["trade_mean_bp"])
        msg += f" per trade ROT p50 {np.median(r):+.2f} p95 {np.quantile(r, .95):+.2f} ({sum(out['rot_wrap_split'])} wrap splits of {draws_rot});"
    if draws:
        a, b = (np.array(out[k]["trade_mean_bp"]) for k in ("control_A_prime", "control_B"))
        msg += f" A' p50 {np.median(a):+.2f} p95 {np.quantile(a, .95):+.2f}; B p50 {np.median(b):+.2f} p95 {np.quantile(b, .95):+.2f};"
    print(msg + f" vs observed {obs['trade_mean_bp']:+.2f} ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def load_controls(paths, g, tr, obs):
    fs = sorted(paths["dir"].glob(f"d361_ctrl_{g}_{tr}_p*.json"))
    if not fs:
        return None
    R, A, B, parts, offs, splits, lin = {}, {}, {}, [], [], [], []
    for f in fs:
        d = json.loads(f.read_text())
        assert d["gate"] == g and d["trigger"] == tr and d["draws"] == len(d["control_A_prime"]["trade_mean_bp"]) and d["draws_rot"] == len(d["control_rot"]["trade_mean_bp"]), f"[P] {f.name}"
        for k in ("net_bp_PUB", "gross_bp", "trade_mean_bp", "trades"):
            assert abs(d["observed"][k] - obs[k]) < 1e-9, f"[P] {f.name}: observed {k} {d['observed'][k]} differs from the re-simulated {obs[k]}"
        for k in d["control_rot"]:
            R.setdefault(k, []).extend(d["control_rot"][k])
            A.setdefault(k, []).extend(d["control_A_prime"][k])
            B.setdefault(k, []).extend(d["control_B"][k])
        offs.extend(d["rot_offsets"])
        splits.extend(d["rot_wrap_split"])
        lin.extend(d["rot_linear_kept"])
        parts.append(dict(file=f.name, part=d["part"], draws=d["draws"], draws_rot=d["draws_rot"], seconds_per_draw=d.get("seconds_per_draw"), B_kept=d.get("B_kept")))
    assert len(set(offs)) == len(offs), f"[ROT] {len(offs) - len(set(offs))} repeated offsets across parts {[p['part'] for p in parts]}"
    stats = ("trade_mean_bp", "net_bp_PUB", "sharpe_net_PUB", "gross_bp", "net_bp_PB")
    tdist = lambda x: dict(p50=float(np.median(x)), min=int(min(x)), max=int(max(x)))
    return dict(draws=len(A["trade_mean_bp"]), draws_rot=len(R["trade_mean_bp"]), parts=parts,
                rot={k: V53._dist(R[k], obs[k]) for k in stats}, A_prime={k: V53._dist(A[k], obs[k]) for k in stats}, B={k: V53._dist(B[k], obs[k]) for k in stats},
                rot_trades=tdist(R["trades"]), A_prime_trades=tdist(A["trades"]), B_trades=tdist(B["trades"]),
                rot_offsets_distinct=len(set(offs)), rot_wrap_splits=int(sum(splits)), rot_linear_kept=int(sum(lin)))


def stage_report(P, paths):
    R = {}
    t0 = time.time()
    assert paths["stage0"].exists(), f"run --stage0 first ({paths['stage0']})"
    S0 = json.loads(paths["stage0"].read_text())["gates"]
    GP = {g: gate_pack(P, g) for g in GATES}
    for g in GATES:
        w = assert_GT(P, GP[g])
        print(f"    [GT] {gate_line(P, GP[g])} (loop to {w:.1e})")
    g_ = assert_G(P, verbose=False)
    S = triggers(P)
    elig = S["T1"][2]
    UNG = {}
    for tr in TRIGGERS:
        sig, sc = S[tr][0], S[tr][1]
        UNG[tr] = arm_report(P, sig, sc, elig, GP["G1"], with_groups=False)
    idd = assert_ID(P, UNG["T1"][PRIMARY_EXIT]["res"], UNG["T2"][PRIMARY_EXIT]["res"], res2_20=UNG["T2"]["cap20"]["res"], verbose=False)
    print(f"    [G] T1 == D359's event matrix ({g_['T1']['events']:,}), T2 == D360's mirror ({g_['T2']['events']:,}); [ID] ungated T1 {idd['T1']['trades']:,} trades "
          f"{idd['T1']['mean_bp']:+.4f} == D359's stored to 1e-9; ungated T2 short {idd['T2']['trades']:,} {idd['T2']['mean_bp']:+.4f} == -(D360's mirror long) to 1e-9 "
          f"({time.time() - t0:.0f}s)")
    elig_b = elig & np.isfinite(np.asarray(P["PCT"]["rsi"]))
    F10 = V47.forward_excess_grid(P["r1T"], P["ocT"], P["m_f"], P["m_f_oc"], P["finT"], h=10)
    for g, tr in CELLS:
        nm = cell_name(g, tr)
        prim = (g, tr) == PRIMARY
        gated, off, ung, sc = arms_of(P, g, tr)
        cell = dict(events=dict(gated=int(gated.sum()), off=int(off.sum()), ungated=int(ung.sum())))
        cell["gated"] = arm_report(P, gated, sc, elig, GP[g], with_groups=True)
        cell["off"] = arm_report(P, off, sc, elig, GP[g], with_groups=prim)
        res = cell["gated"][PRIMARY_EXIT]["res"]
        cell["observed"] = observed_stats(res, P)
        cell["controls"] = load_controls(paths, g, tr, cell["observed"])
        cell["control_C"] = control_C(V47.pnl_bp(res), np.random.default_rng([SEED, STUDY, CELLS.index((g, tr)), ARM["C"]]))
        cell["interaction"] = bucket_interaction(P, res["trades"], V47.pnl_bp(res), F10, elig_b)
        cell["by_episode"] = by_episode(P, GP[g], res)
        drop_res(cell["gated"])
        drop_res(cell["off"])
        R[nm] = cell
        print(f"    {nm}: [HX] " + ", ".join(f"{a} {e} {cell[a][e]['hx']['hedged']['worst']:.0e}/{cell[a][e]['hx']['unhedged']['worst']:.0e}" for a in ("gated", "off") for e in EXIT_NAME.values())
              + f"; gated {cell['events']['gated']:,} events, off {cell['events']['off']:,}; controls {'loaded' if cell['controls'] else 'NOT RUN'} ({time.time() - t0:.0f}s)", flush=True)
    for tr in TRIGGERS:
        drop_res(UNG[tr])
    del F10

    # ---- print ----
    print("\n" + "=" * 170)
    print("THE REGIME-GATED SHORT -- each trigger taken short at the next open on the bars its gate is on, every event, no slot cap, hedged by the floored market; "
          "bp per TRADE (gated = trigger & gate; off = trigger & ~gate; ungated = the parent's own ledger)")
    print("=" * 170)
    print("  %-14s %-8s %-6s %7s %6s %7s %7s %6s %5s | %6s %6s %6s %6s %5s | %7s %7s | %7s | %7s %7s %6s" % (
        "cell", "arm", "exit", "events", "n", "mean", "median", "t", "hold", "2c PUB", "2c PB", "hs PUB", "borrow", "HTB%", "netPUB", "netPB", "be hs/s",
        "era1", "era2", "down"))

    def row(label, arm, ex, ev, d):
        b = d["borrow"]
        nb = d["net_per_trade_borrow"]
        print("  %-14s %-8s %-6s %7s %6d %+7.1f %+7.1f %+6.2f %5.1f | %6.1f %6.1f %6.1f %6.1f %5.2f | %+7.1f %+7.1f | %7.1f | %+7.1f %+7.1f %6s" % (
            label, arm, ex, f"{ev:,}", d["trades"], d["mean_bp"], d["median_bp"], d["t"] or 0, d["hold_mean"], d["two_c"]["PUB"], d["two_c"]["PB"], d["held_half"]["PUB"],
            b["mean_bp"], 100 * b["htb_share"], nb["PUB"], nb["PB"], d["breakeven_half_spread_bp_side"], d["era1_mean_bp"] or 0, d["era2_mean_bp"] or 0,
            ("%+.0f" % d["down_years_mean_bp"]) if d["down_years_mean_bp"] is not None else "-"))
    for nm in R:
        for e in EXIT_NAME.values():
            row(nm + (" *" if nm == cell_name(*PRIMARY) and e == PRIMARY_EXIT else ""), "gated", e, R[nm]["events"]["gated"], R[nm]["gated"][e]["per_trade"])
        for e in EXIT_NAME.values():
            row(nm, "off", e, R[nm]["events"]["off"], R[nm]["off"][e]["per_trade"])
        tr_ = nm.split(":")[1]
        for e in EXIT_NAME.values():
            row(nm, "ungated", e, UNG[tr_]["events"], UNG[tr_][e]["per_trade"])
    print("  hs PUB = the held names' median PUB half-spread at entry on THIS ledger (bp/side); netPUB/netPB = mean - 2c - borrow; be hs/s = the held half-spread at "
          "which the net after commission and borrow is zero; era1/era2/down = mean per trade in the era halves and the down-years")
    print("\n  DEPLOYED BASE (hedged, bp per BAR), 4-crossing line (G22.costed) and the 2-crossing line beside (cost / 2); exp% = share of the kernel's defined bars with "
          "a position (D358's convention; Q4), expG% = share of the GATE's defined bars, on% = the gate's on-share:")
    print("  %-14s %-8s %-6s %5s %5s %5s %5s %6s | %7s %6s %7s %7s %7s | %6s %7s %7s | %7s %6s" % ("cell", "arm", "exit", "exp%", "expG%", "on%", "pos", "ent/yr", "gross",
                                                                                                 "cost4", "net4PUB", "net4PB", "Sh4PUB", "cost2", "net2PUB", "net2PB", "Sh2PUB", "be4 hs"))

    def drow(label, arm, e, d):
        h, hb, h2, hb2 = d["PUB"]["hedged"], d["PB"]["hedged"], d["PUB"]["hedged_2x"], d["PB"]["hedged_2x"]
        print("  %-14s %-8s %-6s %5.1f %5.1f %5.1f %5.1f %6.0f | %+7.2f %6.2f %+7.2f %+7.2f %+7.3f | %6.2f %+7.2f %+7.2f | %+7.3f %6.1f" % (
            label, arm, e, 100 * d["exposure"], 100 * d["gate"]["exposure_gate_defined"], 100 * d["gate"]["gate_on_share"], d["mean_positions_deployed"], d["entries_per_year"],
            h["gross_bp"], h["cost_bp"], h["net_bp"], hb["net_bp"], h["sharpe_net"], h2["cost_bp"], h2["net_bp"], hb2["net_bp"], h2["sharpe_net"], h["breakeven_half_spread_bp_side"] or 0))
    for nm in R:
        for arm in ("gated", "off"):
            for e in EXIT_NAME.values():
                drow(nm, arm, e, R[nm][arm][e]["deployed"])
        for e in EXIT_NAME.values():
            drow(nm, "ungated", e, UNG[nm.split(":")[1]][e]["deployed"])
    print("\n  CONTROLS on the gated arm, primary exit (cap 10), per trade bp: ROT = the gate circularly shifted in time (load-bearing); A' = per-name rotation within "
          "elig & gate; B = same day / same rsi bucket / defined-percentile pool; C = random direction")
    print("  %-8s %5s %5s %8s | %8s %8s %5s | %8s %8s %5s | %8s %8s %5s | %8s %8s %5s | %s" % ("cell", "rot", "A'/B", "observed", "ROT p50", "ROT p95", "above", "A' p50", "A' p95",
                                                                                           "above", "B p50", "B p95", "above", "C p50", "C p95", "above", "deployed net PUB: obs / ROT p95 / A' p95"))
    for nm in R:
        o, k, C = R[nm]["observed"], R[nm]["controls"], R[nm]["control_C"]
        if k is None:
            print("  %-8s %5s %5s %+8.2f | %-70s | %+8.2f %+8.2f %5s |" % (nm, "-", "-", o["trade_mean_bp"], "ROT / A' / B NOT RUN", C["p50"], C["p95"], "yes" if C["above"] else "NO"))
            continue
        r, a, b = k["rot"]["trade_mean_bp"], k["A_prime"]["trade_mean_bp"], k["B"]["trade_mean_bp"]
        print("  %-8s %5d %5d %+8.2f | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+8.2f %+8.2f %5s | %+.2f / %+.2f / %+.2f" % (
            nm, k["draws_rot"], k["draws"], o["trade_mean_bp"], r["p50"], r["p95"], "yes" if r["above"] else "NO", a["p50"], a["p95"], "yes" if a["above"] else "NO",
            b["p50"], b["p95"], "yes" if b["above"] else "NO", C["p50"], C["p95"], "yes" if C["above"] else "NO", o["net_bp_PUB"], k["rot"]["net_bp_PUB"]["p95"], k["A_prime"]["net_bp_PUB"]["p95"]))
        print(f"           ROT: {k['rot_offsets_distinct']} distinct offsets of {k['draws_rot']}; the wrap split one run in {k['rot_wrap_splits']} draws (linear run multiset kept in "
              f"{k['rot_linear_kept']}); trades p50 {k['rot_trades']['p50']:.0f} [{k['rot_trades']['min']}, {k['rot_trades']['max']}] vs observed {o['trades']:,}; A' trades p50 "
              f"{k['A_prime_trades']['p50']:.0f}, B p50 {k['B_trades']['p50']:.0f}")
    pn = cell_name(*PRIMARY)
    g4 = R[pn]["gated"][PRIMARY_EXIT]["per_trade"]["four_groups"]
    tt = g4["top_trade"]
    print(f"\n  FOUR GROUPS per trade (primary {pn} gated, cap 10, short): n {g4['count']:,} mean {g4['mean_bp']:+.1f} median {g4['median_bp']:+.1f} win {100 * g4['win_rate']:.1f}% "
          f"payoff {round(g4['payoff'], 2) if g4['payoff'] is not None else '-'} hold {g4['hold_mean']:.1f} skew {g4['skew']:+.2f} kurt {g4['kurtosis_excess']:+.1f}; "
          f"trims (k={g4['trim_k']}): ex-top {g4['mean_ex_top_bp']:+.1f} ex-bottom {g4['mean_ex_bottom_bp']:+.1f} trimmed {g4['mean_trimmed_bp']:+.1f}")
    print(f"      names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top-1/5/10 name share "
          + "/".join(("%.0f%%" % (100 * v)) if v is not None else "-" for v in g4["top_name_share"].values())
          + f"; profitable years {100 * g4['profitable_years_share']:.0f}% of {g4['years']}; TOP TRADE {tt['symbol']} entered {tt['entry_date']} at ${tt['as_traded_price']:.2f} "
          f"(DV pct {round(tt['dv_percentile_at_entry'], 1) if tt['dv_percentile_at_entry'] is not None else '-'}), held {tt['hold']} bars, {tt['pnl_bp']:+.0f} bp = "
          f"{('%.1f%%' % (100 * tt['share_of_pnl'])) if tt['share_of_pnl'] is not None else '-'} of P&L")
    sd_, sp_ = g4["split_dead_alive"], g4["split_price"]
    r_ = lambda x: "-" if x is None else round(x, 1)
    print(f"      splits: dead {sd_['dead_n']} {r_(sd_['dead_mean_bp'])} / alive {sd_['alive_n']} {r_(sd_['alive_mean_bp'])}; price <= ${sp_['median_price']:.2f} "
          f"{sp_['low_n']} {r_(sp_['low_mean_bp'])} / above {sp_['high_n']} {r_(sp_['high_mean_bp'])}")
    acc = R[pn]["gated"][PRIMARY_EXIT]["accounting"]
    print(f"      check: {acc['events']:,} events = {acc['entries']:,} entries + {acc['already_held']:,} on names already held + {acc['unpriced']:,} unpriced; "
          f"trades {acc['trades']:,} = entries - {acc['open_at_end']} open at the end")
    for e in EXIT_NAME.values():
        d = R[pn]["gated"][e]["per_trade"]
        b = d["borrow"]
        print(f"      primary gated {e}: n {d['trades']:,} mean {d['mean_bp']:+.2f} median {d['median_bp']:+.2f} t {d['t']:+.2f} hold {d['hold_mean']:.2f}; 2c PUB {d['two_c']['PUB']:.2f} "
              f"PB {d['two_c']['PB']:.2f}; held hs PUB {d['held_half']['PUB']:.2f} PB {d['held_half']['PB']:.2f} (price ${d['held_price']:.2f}); borrow {b['mean_bp']:.2f} bp "
              f"(HTB {100 * b['htb_share']:.2f}%, {b['htb_n']}); net after borrow PUB {d['net_per_trade_borrow']['PUB']:+.2f} PB {d['net_per_trade_borrow']['PB']:+.2f}; "
              f"be hs/s {d['breakeven_half_spread_bp_side']:.1f}")
    print(f"\n  SPLITS of the gated arm (cap 10): per trade era1 / era2 / down-years [n], and the deployed hedged net PUB bp/bar [bars]; down-years {P['down_years']}")
    for nm in R:
        tr_ = R[nm]["gated"][PRIMARY_EXIT]["per_trade"]
        s_ = R[nm]["gated"][PRIMARY_EXIT]["deployed"]["splits_hedged"]
        fmt = lambda x: (f"{x['PUB']['net_bp']:+.2f}[{x['bars']}]" if "PUB" in x else f"-[{x['bars']}]")
        print(f"  {nm:8s} per trade era1 {tr_['era1_mean_bp'] or 0:+.1f} [{tr_['era1_n']}] era2 {tr_['era2_mean_bp'] or 0:+.1f} [{tr_['era2_n']}] down {tr_['down_years_mean_bp'] or 0:+.1f} "
              f"[{tr_['down_years_n']}] | deployed era1 {fmt(s_['era1'])} era2 {fmt(s_['era2'])} down {fmt(s_['down_years'])}")
        print("      by year (per trade mean [n]): " + " ".join(f"{y}:{v['mean_bp']:+.0f}[{v['n']}]" for y, v in sorted(tr_["by_year"].items())))
    eps = R[pn]["by_episode"]
    empty = [e for e in eps if e["trades"] == 0]
    print(f"\n  BY EPISODE (primary {pn} gated, cap 10; a trade belongs to the on-episode containing its entry bar; every cell's split is in the JSON): "
          f"{len(eps)} episodes, {len(empty)} without a trade" + (f" (all before {max(e['end'] for e in empty)})" if empty else "") + "; the rest, one per line:")
    print("  %-12s %-12s %5s %6s %8s %8s %9s" % ("start", "end", "bars", "trades", "mean", "median", "sum bp"))
    for e in eps:
        if e["trades"]:
            print("  %-12s %-12s %5d %6d %+8.1f %+8.1f %+9.0f" % (e["start"], e["end"], e["bars"], e["trades"], e["mean_bp"], e["median_bp"], e["sum_bp"]))
    pos = [e for e in eps if e["trades"] and e["mean_bp"] > 0]
    print(f"  episodes with trades: {len(eps) - len(empty)}, of which {len(pos)} with a positive mean; trades in the ten longest episodes "
          f"{sum(e['trades'] for e in sorted(eps, key=lambda e: -e['bars'])[:10]):,} of {sum(e['trades'] for e in eps):,}")
    print("\n  INTERACTION with the rsi bucket of the trigger name at entry (gated, cap 10): b[n] mean per trade / short forward-10 base rate / interaction "
          "(E_sb - E_b - E_s + E_all)")
    for nm in R:
        it = R[nm]["interaction"]
        print(f"  {nm:8s} E_all {it['E_all']:+.1f}: " + " ".join(f"b{b}[{v['n']}] {v['mean_bp']:+.0f}/{v['E_b']:+.0f}/{v['interaction']:+.0f}" for b, v in sorted(it["buckets"].items()))
              + f"; undefined {it['undefined_n']}")
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1")
    print_stage0(P, S0)

    # ---- predictions ----
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    q = {}
    s1 = S0["G1"]
    b10 = s1["drift"]["bottom_10"]
    q["Q0"] = bool(b10["on"]["bp"] < 0 and b10["off"]["bp"] > 0 and s1["block"]["corr"] > 0 and s1["episodes"] >= 4)
    pr = R[pn]["gated"][PRIMARY_EXIT]["per_trade"]
    k = R[pn]["controls"]
    C = R[pn]["control_C"]
    q["Q1"] = bool(pr["mean_bp"] > 0 and k is not None and k["rot"]["trade_mean_bp"]["above"] and k["A_prime"]["trade_mean_bp"]["above"] and C["above"])
    off1 = R[pn]["off"][PRIMARY_EXIT]["per_trade"]
    q["Q2"] = bool(pr["mean_bp"] - off1["mean_bp"] >= 20.0)
    t2g = R[cell_name("G1", "T2")]["gated"][PRIMARY_EXIT]["per_trade"]
    t2u = UNG["T2"][PRIMARY_EXIT]["per_trade"]
    q["Q3"] = bool(t2g["mean_bp"] >= t2u["mean_bp"] + 10.0)
    dep = R[pn]["gated"][PRIMARY_EXIT]["deployed"]
    q["Q4"] = bool(dep["exposure"] < 0.5)
    q["Q5"] = bool(pr["net_per_trade_borrow"]["PUB"] > 0)
    t1u = UNG["T1"][PRIMARY_EXIT]["per_trade"]
    q["Q6"] = bool(pr["held_half"]["PUB"] >= t1u["held_half"]["PUB"] + 3.0)
    m_ = lambda g, tr: R[cell_name(g, tr)]["gated"][PRIMARY_EXIT]["per_trade"]["mean_bp"]
    q["Q7"] = bool(all(m_("G2", tr) < m_("G1", tr) for tr in TRIGGERS))
    rot_ok = k is not None and k["rot_offsets_distinct"] == k["draws_rot"]
    q["check"] = bool(idd["T1"]["trades"] == PREREG["T1"]["trades"] and idd["T2"]["trades"] == PREREG["T2"]["trades"] and rot_ok)
    q["check_rot_linear_multiset_kept_every_draw"] = bool(k is not None and k["rot_linear_kept"] == k["draws_rot"])
    print(f"\nPREDICTIONS (primary cell {pn}, gated, cap 10, short, bp per trade unless stated; the signal criterion is GROSS, R15)")
    print(f"  Q0 (premise, G1) cohort forward-20 hedged drift < 0 with the gate on and > 0 off, block correlation > 0, at least four episodes: {v_(q['Q0'])} -- "
          f"on {b10['on']['bp']:+.2f} [{b10['on']['n']:,}] off {b10['off']['bp']:+.2f} [{b10['off']['n']:,}] bp per name-bar; corr {s1['block']['corr']:+.3f} on "
          f"{s1['block']['n_blocks']} blocks (shuffled {s1['block']['corr_shuffled']:+.3f}); {s1['episodes']} episodes")
    print(f"  Q1 (LOAD-BEARING) gross mean per trade > 0 and above the p95 of the gate rotation, A'-within-gate and C: {v_(q['Q1'])} -- observed {pr['mean_bp']:+.2f} "
          f"({pr['trades']:,} trades)"
          + (f"; ROT p95 {k['rot']['trade_mean_bp']['p95']:+.2f} (p50 {k['rot']['trade_mean_bp']['p50']:+.2f}) at {k['draws_rot']} draws, A' p95 {k['A_prime']['trade_mean_bp']['p95']:+.2f} "
             f"(p50 {k['A_prime']['trade_mean_bp']['p50']:+.2f}), B p95 {k['B']['trade_mean_bp']['p95']:+.2f} at {k['draws']} draws" if k else "; ROT/A'/B NOT RUN (falsified by absence)")
          + f"; C p95 {C['p95']:+.2f} (p50 {C['p50']:+.2f})")
    print(f"  Q2 T1's gated mean exceeds its gate-off mean by at least 20 bp: {v_(q['Q2'])} -- gated {pr['mean_bp']:+.2f} ({pr['trades']:,}) vs off {off1['mean_bp']:+.2f} "
          f"({off1['trades']:,}), gap {pr['mean_bp'] - off1['mean_bp']:+.2f}")
    print(f"  Q3 T2's gated gross mean exceeds its ungated mean by at least 10 bp: {v_(q['Q3'])} -- gated {t2g['mean_bp']:+.2f} ({t2g['trades']:,}) vs ungated "
          f"{t2u['mean_bp']:+.2f} ({t2u['trades']:,}; the pre-reg's +{PREREG['T2']['mean_bp']}), gap {t2g['mean_bp'] - t2u['mean_bp']:+.2f}")
    print(f"  Q4 the primary cell is deployed on fewer than half the defined bars: {v_(q['Q4'])} -- {100 * dep['exposure']:.1f}% of the kernel's {dep['bars_defined']:,} defined bars "
          f"({100 * dep['gate']['exposure_gate_defined']:.1f}% of the gate's {dep['gate']['bars_gate_defined']:,}; gate on {100 * dep['gate']['gate_on_share']:.1f}%)")
    print(f"  Q5 (against) nets > 0 per trade after the PUB 2c and borrow: {v_(q['Q5'])} -- mean {pr['mean_bp']:+.2f} - 2c PUB {pr['two_c']['PUB']:.2f} - borrow "
          f"{pr['borrow']['mean_bp']:.2f} = {pr['net_per_trade_borrow']['PUB']:+.2f} (PB {pr['net_per_trade_borrow']['PB']:+.2f}); be hs/s {pr['breakeven_half_spread_bp_side']:.1f}")
    print(f"  Q6 the gated ledger's held half-spread PUB at least 3 bp a side wider than the ungated T1's: {v_(q['Q6'])} -- gated {pr['held_half']['PUB']:.2f} vs ungated "
          f"{t1u['held_half']['PUB']:.2f} bp/side (PB {pr['held_half']['PB']:.2f} vs {t1u['held_half']['PB']:.2f}; held price ${pr['held_price']:.2f} vs ${t1u['held_price']:.2f})")
    print(f"  Q7 G2 gives a lower gated mean than G1 for both triggers: {v_(q['Q7'])} -- " + "; ".join(f"{tr}: G2 {m_('G2', tr):+.2f} vs G1 {m_('G1', tr):+.2f}" for tr in TRIGGERS))
    print(f"  check: with the gate removed T1 reproduces D359's primary ({idd['T1']['trades']:,} trades, {idd['T1']['mean_bp']:+.4f}; the pre-reg wrote +{PREREG['T1']['mean_bp']}, the "
          f"stored file says {idd['T1']['stored_mean_bp']:+.4f}) and T2 reproduces D360's mirror with the side reversed ({idd['T2']['trades']:,} trades, {idd['T2']['mean_bp']:+.4f}), "
          f"each to 1e-9; the gate rotation keeps the on-share and the CIRCULAR run-length multiset exactly in every draw with "
          + (f"{k['rot_offsets_distinct']} distinct offsets of {k['draws_rot']}; the LINEAR multiset is kept in {k['rot_linear_kept']} of {k['draws_rot']} draws (the wrap splits one "
             f"run in the others: reported, not relaxed)" if k else "the rotation NOT RUN") + f": {v_(q['check'])}")
    out = dict(note="D361: the regime-gated short -- D359's loser-rally spike and D360's gap-up fade entered short only on bars where a market-level gate is on; "
                    "four cells gate x trigger, gated / gate-off / ungated arms, cap 10 and cap 20; the gate rotation (load-bearing), A' within the gate, B and C "
                    "on the gated primary exit; cost beside, deciding nothing (R15). Per-trade numbers are bp per TRADE and never compared to per-bar numbers. "
                    "Nothing is a book; nothing promoted.",
               study=STUDY, cells=[cell_name(g, tr) for g, tr in CELLS], primary=pn, primary_exit=PRIMARY_EXIT, exits=list(EXIT_NAME.values()), arms=list(ARMS),
               gates={g: dict(window=WIN[g], d0=GP[g]["d0"], d0_date=P["dates"][GP[g]["d0"]], Td=GP[g]["Td"], on=GP[g]["on"], on_share=GP[g]["on_share"], episodes=len(GP[g]["runs"]),
                              runs=GP[g]["runs"], episode_dates=GP[g]["dates"], episode_years=GP[g]["years"]) for g in GATES},
               gate_definition=dict(index="cumprod(1 + m_f) from m_start; m_f the floored market's simple equal-weight return", G1="63-bar trailing compounded return < 0",
                                    G2="index[t-1] < mean(index[t-200..t-1])", lag="the value at t uses m_f to t-1", undefined="False where the window is incomplete"),
               triggers=dict(T1=f"run_d359.cell_signal{T1_PARENT} (score pct_rev)", T2=f"run_d360.mirror_signal{T2_PARENT} entered SHORT (score 100 - pct_gap lagged)"),
               exposure="exposure = deployed bars / the kernel's defined bars (D358); exposure_gate_defined beside",
               U=V59.U_SLOTS, x_target=X_TARGET, down_years=P["down_years"], floored_market_by_year=P["yr_ret"], m_start=P["m_start"],
               seeds=dict(ROT=[SEED, STUDY, "cell_index", ARM["ROT"], "part"], A=[SEED, STUDY, "cell_index", ARM["A"], "part"], B=[SEED, STUDY, "cell_index", ARM["B"], "part"],
                          C=[SEED, STUDY, "cell_index", ARM["C"]], stage0_shuffle=[SEED, STUDY, 0, 0]),
               borrow=dict(scheme=BORROW_SCHEME, gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB), G=g_, ID=idd, stage0=S0, ungated=UNG, results=R, predictions=q)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {paths['report']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--stage0", action="store_true")
    ap.add_argument("--cell", metavar="GATE:TRIGGER", help="e.g. G1:T1 -- the gate rotation, A'-within-gate and B controls for one cell on the primary exit")
    ap.add_argument("--draws", type=int, default=100, help="A'-within-gate and B draws")
    ap.add_argument("--draws-rot", type=int, default=None, help="gate-rotation draws (default: --draws; the pre-registration is 200)")
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA), help="where the stage files go (default data/; the smoke runs pass a temp/ directory)")
    a = ap.parse_args()
    print("D361  the regime-gated short -- the record's two short triggers behind a market-level gate, with the gate's own null")
    paths = out_paths(a.out_dir)
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))                # what V49.event_buckets reads
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    if a.selftest:
        stage_selftest(P)
    elif a.stage0:
        stage_stage0(P, paths)
    elif a.cell:
        g, tr = a.cell.split(":")
        assert (g, tr) in CELLS, f"cell must be one of {[cell_name(g_, t_) for g_, t_ in CELLS]}"
        stage_cell(P, g, tr, a.draws, a.draws if a.draws_rot is None else a.draws_rot, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --stage0, --cell GATE:TRIGGER, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
