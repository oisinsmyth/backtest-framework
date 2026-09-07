"""D367 -- the gate deconstructed, and the book without its ten best names.

    uv run python scripts/run_d367_gate_deconstruction.py --selftest
    uv run python scripts/run_d367_gate_deconstruction.py --gates --draws 200
    uv run python scripts/run_d367_gate_deconstruction.py --reduced --draws 200
    uv run python scripts/run_d367_gate_deconstruction.py --report

THE STATISTIC IS NOT RAW NET. Every gate has a different on-share, and a gate does two things at once: it chooses
WHEN to hold and it chooses HOW MUCH to hold at all. Only the first is a forecast. Each gate is scored on

    timing premium = its net  -  the MEDIAN of its OWN time rotation

which holds on-share and circular run structure fixed and leaves only timing, so a condition open 60% of bars and
one open 9% are comparable. Raw net, gross and on-share are reported beside it and are never the ranking.

THE RECORD'S OWN SEARCH IS PRICED. The SHARED-OFFSET arm applies ONE shift to ALL 46 gates per draw and scores the
maximum timing premium across them, so Q4 tests S6 against the best of forty-six rather than against any one gate.

THE TEN-NAME REMOVAL IS LOOK-AHEAD. The set was chosen by knowing which names turned out best. The reduced book is
NOT a strategy and no version of it is proposable; it answers only whether what remains beats its own controls.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_d366_gated_buffer as V66            # noqa: E402  -- the frozen construction, verbatim
import run_d365_momentum_buffer as V65         # noqa: E402
import d365_export_trades as EX                # noqa: E402

PREP, V58, V50 = V66.PREP, V66.V58, V66.V50
STUDY, SEED, ANN = 367, V66.SEED, 252.0
COND = ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9")
COND_TEXT = {
    "C1": "NOT the crash state (20-bar vol below its EXPANDING 80th pct, or the 63-bar return not negative)",
    "C2": "index above its 200-bar mean", "C3": "index 63-bar return > 0",
    "C4": "the index's own 252-21 momentum > 0", "C5": "50-bar mean above the 200-bar mean",
    "C6": "index above its 50-bar mean", "C7": "index 21-bar return > 0",
    "C8": "breadth: more than half of eligible names above their own 200-bar mean",
    "C9": "index at a 252-bar high"}
MIN_OPEN = 50                                  # fewer open bars than this after warm-up == degenerate [DEGEN]
D366_JK = REPO / "data" / "d366_jackknife.json"
D366_OUT = REPO / "data" / "d366_gated_buffer.json"


def el(t0):
    return f"{time.time() - t0:.0f}s"


# ================================================================== the nine conditions
def conditions(P):
    """The nine lagged conditions of D366's gate, each on its own. Built from V66's own conditioners (R9)."""
    C = V66.conditioners(P)
    vq = V66.expanding_q(C["vol"], 80)
    Z = lambda a, c: np.where(np.isfinite(a), c, True)      # an undefined conditioner never shuts the gate
    fin = np.isfinite(C["vol"]) & np.isfinite(C["l63"]) & np.isfinite(C["l200"])
    return {
        "C1": np.where(fin & np.isfinite(vq), ~((C["vol"] >= vq) & (C["l63"] < 0)), True),
        "C2": Z(C["l200"], C["l200"] > 0), "C3": Z(C["l63"], C["l63"] > 0),
        "C4": Z(C["mom"], C["mom"] > 0), "C5": Z(C["cross"], C["cross"] > 0),
        "C6": Z(C["l50"], C["l50"] > 0), "C7": Z(C["r21"], C["r21"] > 0),
        "C8": Z(C["breadth"], C["breadth"] > 0.5), "C9": C["hi252"].astype(bool),
    }, C, vq


def gate_set(cond):
    """The 46 gates: 9 singles, all 36 pairs, and the combined S6. Order is fixed and is the report's order."""
    G = {c: cond[c].copy() for c in COND}
    for a, b in itertools.combinations(COND, 2):
        G[f"{a}+{b}"] = cond[a] & cond[b]
    s6 = cond["C1"].copy()
    for c in COND[1:]:
        s6 &= cond[c]
    G["S6"] = s6
    return G


# ================================================================== scoring
def open_share(g, m0):
    return float(g[m0:].mean())


def run_gate(P, g, pct, elig, mkt_cc, mkt_oc, zeros):
    return V66.run_cell(P, g, pct, elig, mkt_cc, mkt_oc, zeros)


def circ_runs(v):
    """The CIRCULAR run-length multiset of a boolean sequence -- the invariant a circular roll must preserve.
    (An earlier version doubled the array and grouped it, which merges across the seam and is not the circular
    statistic at all; it failed on a rotation that was in fact correct.)"""
    v = np.asarray(v, bool)
    if v.size == 0 or v.all() or (~v).all():
        return [int(v.size)]
    idx = np.flatnonzero(np.diff(v.astype(np.int8)) != 0) + 1
    lens = [int(len(p)) for p in np.split(v, idx)]
    if v[0] == v[-1] and len(lens) > 1:                 # the ring closes: first and last run are one run
        lens[0] += lens.pop()
    return sorted(lens)


def rotate(g, m0, k):
    """Circularly shift a gate within its defined range by a GIVEN k, so one k can be shared across all gates."""
    out = g.copy()
    seg = g[m0:]
    if seg.size < 10:
        return out
    out[m0:] = np.roll(seg, int(k) % seg.size)
    return out


def summarise(vals, obs):
    x = np.asarray([v for v in vals if v is not None and np.isfinite(v)], float)
    if x.size == 0:
        return None
    return dict(p50=float(np.median(x)), p95=float(np.quantile(x, 0.95)), max=float(np.max(x)),
                min=float(np.min(x)), draws=int(x.size), distinct=int(np.unique(x).size),
                above_p95=bool(obs > np.quantile(x, 0.95)),
                draws_beating_observed=int((x >= obs).sum()), pct_rank=float(100.0 * (x < obs).mean()))


# ================================================================== the reduced universe
def removed_names(P):
    """The ten names read from COMMITTED EVIDENCE (D366's jackknife), never retyped. [LOOK]"""
    assert D366_JK.exists(), "run D366 --jackknife first: data/d366_jackknife.json is the evidence for the set"
    top = json.loads(D366_JK.read_text())["top10"]
    syms = [d["symbol"] for d in top]
    idx = {s: i for i, s in enumerate(P["symbols"])}
    missing = [s for s in syms if s not in idx]
    assert not missing, f"[LOOK] {missing} not in the universe"
    return syms, [idx[s] for s in syms]


def reduced_elig(P, elig, cols):
    e = elig.copy()
    e[:, cols] = False
    return e


def reduced_pct(P, cols):
    """Removing names from the UNIVERSE must RE-RANK everyone else, or it is not a universe change at all -- it is
    merely a decision not to trade those names, with every other name's percentile unmoved.

    `percentile_grid` ranks among names with a FINITE score, so the removal is done by NaN-ing the removed columns
    of the lagged score before the grid is built. Other names' percentiles then rise (the removed names were the
    high-momentum ones) and some cross rank 95 that previously did not -- which is what makes the freed capital
    reappear. D366's jackknife did NOT do this: it kept the full-universe ranking and only suppressed those names
    from the book, and its comment claiming slots refilled was wrong. Its numbers are still valid, read as
    'do not trade these ten', which is the weaker of the two questions."""
    raw = np.asarray(V50.lagged(P, V65.SCORE), float).copy()
    raw[:, cols] = np.nan
    return V66.V47.percentile_grid(raw)


# ================================================================== stages
def prepare(P):
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    cond, C, vq = conditions(P)
    G = gate_set(cond)
    mkt_cc, mkt_oc = V66.dvw_market(P)
    zeros = np.zeros((P["T"], P["n"]), float)
    return pct, elig, cond, C, vq, G, mkt_cc, mkt_oc, zeros


def stage_selftest(P, t0):
    pct, elig, cond, C, vq, G, mkt_cc, mkt_oc, zeros = prepare(P)
    m0 = P["m_start"]
    V65.assert_HOLDOUT_GUARD()

    # [ID] -- against D366's STORED result, not a number retyped here
    assert D366_OUT.exists(), "run D366 --report first"
    d66 = json.loads(D366_OUT.read_text())["observed"]
    s6 = run_gate(P, G["S6"], pct, elig, mkt_cc, mkt_oc, zeros)
    for k, got in (("net", s6["net"]), ("sharpe", s6["sharpe"]), ("maxdd", s6["maxdd"]), ("gross", s6["gross"])):
        assert abs(float(got) - float(d66[k])) < 1e-9, f"[ID] {k}: {got} vs D366's stored {d66[k]}"
    assert s6["cost_parts"]["trades"] == d66["cost_parts"]["trades"], "[ID] trade count"
    print(f"    [ID] S6 here reproduces D366's STORED result to <1e-9: net {s6['net']:+.4f} sharpe "
          f"{s6['sharpe']:.4f} maxDD {s6['maxdd']:.1f} trades {s6['cost_parts']['trades']}")

    # [COND] -- each condition independently, and the conjunction
    man = cond["C1"].copy()
    for c in COND[1:]:
        man &= cond[c]
    assert np.array_equal(man, G["S6"]), "[COND] the nine conditions do not conjoin to S6"
    assert np.array_equal(man, V66.gate_ladder(C)[0]["S6"]), "[COND] disagrees with D366's own ladder"
    for a, b in itertools.combinations(COND, 2):
        assert np.array_equal(G[f"{a}+{b}"], cond[a] & cond[b]), f"[COND] pair {a}+{b}"
    shares = {c: open_share(cond[c], m0) for c in COND}
    assert len(G) == 46, f"[COND] {len(G)} gates, expected 46"
    print(f"    [COND] 9 conditions conjoin to S6 bit-for-bit and match D366's ladder; all 36 pairs equal the "
          f"intersection of their members; 46 gates in total")
    print("    on-share of each condition alone: " + ", ".join(f"{c} {100*shares[c]:.1f}%" for c in COND)
          + f", S6 {100*open_share(G['S6'], m0):.1f}%")

    # [SHARE] -- a rotation preserves the on-share exactly and the circular run-length multiset
    rng = np.random.default_rng([SEED, STUDY, 1])
    k = int(rng.integers(1, (P["T"] - m0)))
    for nm in ("S6", "C9", "C2+C9"):
        r = rotate(G[nm], m0, k)
        assert r[m0:].sum() == G[nm][m0:].sum(), f"[SHARE] {nm} on-share changed"
        assert not np.array_equal(r, G[nm]), f"[SHARE] {nm} rotation returned the observed gate"
        assert circ_runs(G[nm][m0:]) == circ_runs(r[m0:]), f"[SHARE] {nm} circular run-length multiset changed"
    print(f"    [SHARE] a shift of {k} preserves on-share and the circular run-length multiset exactly on S6, C9 "
          f"and C2+C9, and never returns the observed gate")

    # [SHARED] -- one draw's gates are all recomputable from the single recorded shift
    ks = int(np.random.default_rng([SEED, STUDY, 2, 0]).integers(1, P["T"] - m0))
    rot_all = {nm: rotate(g, m0, ks) for nm, g in G.items()}
    for nm in list(G)[:5] + ["S6"]:
        assert np.array_equal(rot_all[nm], rotate(G[nm], m0, ks)), f"[SHARED] {nm}"
    assert len({int(np.flatnonzero(rot_all[nm][m0:] != G[nm][m0:]).size) for nm in G}) > 1, \
        "[SHARED] every gate changed identically -- the shift is not being applied per gate"
    print(f"    [SHARED] all 46 gates in one draw are recomputable from the single recorded shift {ks}")

    # [UNIV] and [LOOK]
    syms, cols = removed_names(P)
    e2 = reduced_elig(P, elig, cols)
    pct2 = reduced_pct(P, cols)
    diff_cols = np.flatnonzero((e2 != elig).any(axis=0))
    assert len(diff_cols) == 10 and set(diff_cols) == set(cols), f"[UNIV] {len(diff_cols)} columns differ"
    assert np.all(np.isnan(pct2[:, cols])), "[UNIV] a removed name still carries a percentile"
    moved = int((np.nan_to_num(pct2, nan=-1) != np.nan_to_num(pct, nan=-1)).any(axis=0).sum())
    assert moved > 10, f"[UNIV] only {moved} names' ranks moved -- the universe was not re-ranked"
    red = run_gate(P, G["S6"], pct2, e2, mkt_cc, mkt_oc, zeros)
    tr_full, _o, _n = V65.trades_of(s6["hold"], zeros)
    tr_red, _o2, _n2 = V65.trades_of(red["hold"], zeros)
    assert not any(r in cols for r, _e, _a, _p, _s in tr_red), "[UNIV] a removed name traded in the reduced book"
    n_removed_trades = sum(1 for r, _e, _a, _p, _s in tr_full if r in cols)
    kept_full = {(r, e0) for r, e0, _a, _p, _s in tr_full if r not in cols}
    kept_red = {(r, e0) for r, e0, _a, _p, _s in tr_red}
    new_trades = len(kept_red - kept_full)
    assert new_trades > 0, "[UNIV] no name entered that did not enter before -- the universe was not re-ranked"
    print(f"    [UNIV] exactly 10 columns differ and {moved} names' percentiles moved, so the universe is genuinely "
          f"re-ranked rather than merely un-traded; the removed names never trade in the reduced book; their "
          f"{n_removed_trades} trades are replaced by {new_trades} entries that did not exist before "
          f"({len(tr_full)} -> {len(tr_red)} trades)")
    print(f"    [LOOK] the removed set is READ from data/d366_jackknife.json, not retyped: {', '.join(syms)}. "
          f"It was chosen by knowing which names turned out best -- a look-ahead diagnostic, not a strategy.")

    # [DEGEN]
    degen = [nm for nm, g in G.items() if int(g[m0:].sum()) < MIN_OPEN]
    print(f"    [DEGEN] {len(degen)} of 46 gates open on fewer than {MIN_OPEN} bars"
          + (f": {', '.join(degen)}" if degen else " -- none"))

    # [S]
    rng2 = np.random.default_rng([SEED, STUDY, 9])
    hold = s6["hold"]
    cand = np.flatnonzero(hold.sum(axis=1) > 3)
    tb = int(rng2.choice(cand[cand > m0 + 1200]))
    ib = int(rng2.choice(np.flatnonzero(hold[tb] & ~s6["ent"][tb])))
    r1p = np.asarray(P["r1T"], float).copy()
    r1p[tb, ib] += 50e-4
    v2, _m, _e, _c = V66.book_of(dict(P, r1T=r1p), hold, mkt_cc, mkt_oc)
    nh = int(s6["cn"][tb])
    d = v2[tb] - s6["v"][tb]
    other = np.ones(P["T"], bool)
    other[tb] = False
    assert abs(d - 50.0 / nh) < 1e-6, f"[S] moved {d:.4f}, expected {50.0/nh:.4f}"
    assert np.array_equal(np.nan_to_num(v2[other]), np.nan_to_num(s6["v"][other])), "[S] leaked"
    print(f"    [S] +50 bp on {P['symbols'][ib]} {P['dates'][tb]} moves the bar by {d:.4f} = 50 / {nh} held, "
          f"and no other bar")

    # [6]
    broke = []
    try:
        bad = cond["C1"] & cond["C2"]
        assert np.array_equal(bad, G["S6"])
    except AssertionError:
        broke.append("COND/conjunction")
    try:
        r = rotate(G["S6"], m0, k)
        r[m0] = ~r[m0]
        assert r[m0:].sum() == G["S6"][m0:].sum()
    except AssertionError:
        broke.append("SHARE/on-share")
    try:
        assert np.array_equal(rotate(G["S6"], m0, k), rotate(G["S6"], m0, k + 1))
    except AssertionError:
        broke.append("SHARED/one shift")
    try:
        assert np.array_equal(np.nan_to_num(reduced_pct(P, cols[:9]), nan=-1), np.nan_to_num(pct2, nan=-1))
    except AssertionError:
        broke.append("UNIV/ten columns")
    try:
        assert abs((v2[tb] - s6["v"][tb]) - 50.0 / (nh + 1)) < 1e-6
    except AssertionError:
        broke.append("S")
    assert len(broke) == 5, f"[6] only {broke} raised"
    print(f"    [6] each of {', '.join(broke)} raises on a deliberately broken input")
    print(f"\nOK  selftest passes  ({el(t0)})  {PREP.rss_line()}")


def stage_gates(P, draws, t0):
    """All 46 gates, each against its OWN rotation, plus the SHARED-OFFSET maximum over them."""
    pct, elig, cond, C, vq, G, mkt_cc, mkt_oc, zeros = prepare(P)
    m0 = P["m_start"]
    names = list(G)
    obs = {}
    for i, nm in enumerate(names):
        s = run_gate(P, G[nm], pct, elig, mkt_cc, mkt_oc, zeros)
        obs[nm] = dict(net=s["net"], gross=s["gross"], sharpe=s["sharpe"], maxdd=s["maxdd"],
                       trades=s["cost_parts"]["trades"], members=s["members"], era1=s["era1"], era2=s["era2"],
                       open_share=open_share(G[nm], m0), open_bars=int(G[nm][m0:].sum()),
                       degenerate=bool(int(G[nm][m0:].sum()) < MIN_OPEN))
        if (i + 1) % 10 == 0:
            print(f"    observed {i+1}/{len(names)} ({el(t0)})")

    per = {nm: [] for nm in names}
    shared_max, shared_ks = [], []
    rng = np.random.default_rng([SEED, STUDY, 3])
    live = [nm for nm in names if not obs[nm]["degenerate"]]
    for d in range(draws):
        k = int(rng.integers(1, P["T"] - m0))
        shared_ks.append(k)
        row = {}
        for nm in names:
            s = run_gate(P, rotate(G[nm], m0, k), pct, elig, mkt_cc, mkt_oc, zeros)
            per[nm].append(s["net"])
            row[nm] = s["net"]
        # the shared-offset draw's score is the best TIMING PREMIUM available under this one shift, over the
        # non-degenerate gates -- computed against each gate's own running rotation median at the end
        shared_max.append(row)
        if (d + 1) % 10 == 0:
            print(f"    draws {d+1}/{draws} ({el(t0)})  {PREP.rss_line()}")

    p50 = {nm: float(np.median(per[nm])) for nm in names}
    out_gates = {}
    for nm in names:
        dd = summarise(per[nm], obs[nm]["net"])
        out_gates[nm] = dict(observed=obs[nm], rotation=dd, rot_p50=p50[nm],
                             timing_premium=obs[nm]["net"] - p50[nm])
    # each draw's max timing premium across the live gates, using each gate's own p50 as its centre
    smax = [max(row[nm] - p50[nm] for nm in live) for row in shared_max]
    s6_tp = out_gates["S6"]["timing_premium"]

    out = dict(study=STUDY, draws=draws, gates=out_gates,
               shared_offset_max=summarise(smax, s6_tp), shared_shifts_distinct=int(len(set(shared_ks))),
               live_gates=len(live), degenerate=[nm for nm in names if obs[nm]["degenerate"]],
               cond_text=COND_TEXT,
               note="D367: timing premium = net - the median of that gate's OWN time rotation. The shared-offset "
                    "arm applies ONE shift to all gates per draw and scores the best premium, pricing the search.")
    p = REPO / "data" / "d367_gates.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\n  wrote {p.name}: S6 premium {s6_tp:+.2f}, shared-offset max p95 "
          f"{out['shared_offset_max']['p95']:+.2f}  ({el(t0)})  {PREP.rss_line()}")


def stage_reduced(P, draws, t0):
    """The book without its ten best names, against its OWN controls."""
    pct, elig, cond, C, vq, G, mkt_cc, mkt_oc, zeros = prepare(P)
    m0 = P["m_start"]
    syms, cols = removed_names(P)
    e2 = reduced_elig(P, elig, cols)
    pct2 = reduced_pct(P, cols)
    S6 = G["S6"]
    obs = run_gate(P, S6, pct2, e2, mkt_cc, mkt_oc, zeros)
    full = run_gate(P, S6, pct, elig, mkt_cc, mkt_oc, zeros)

    res = {}
    rng = np.random.default_rng([SEED, STUDY, 4])
    vals = []
    for sh in range(1, V65.N_BASE):
        vals.append(run_gate(P, S6, V65.rank_rotate(pct2, e2, sh), e2, mkt_cc, mkt_oc, zeros)["net"])
    res["ROT"] = summarise(vals, obs["net"])
    print(f"    ROT done ({el(t0)})")

    vals = []
    for d in range(draws):
        vals.append(run_gate(P, S6, V65.aprime_draw(pct2, e2, rng), e2, mkt_cc, mkt_oc, zeros)["net"])
        if (d + 1) % 25 == 0:
            print(f"    APRIME {d+1}/{draws} ({el(t0)})")
    res["APRIME"] = summarise(vals, obs["net"])

    vals = []
    for d in range(draws):
        k = int(rng.integers(1, P["T"] - m0))
        vals.append(run_gate(P, rotate(S6, m0, k), pct2, e2, mkt_cc, mkt_oc, zeros)["net"])
        if (d + 1) % 25 == 0:
            print(f"    GATEROT {d+1}/{draws} ({el(t0)})")
    res["GATEROT"] = summarise(vals, obs["net"])

    b = obs["v"][obs["mask"]] - obs["cost_parts"]["total"]
    vals = []
    for _ in range(10):
        sg = rng.choice([-1.0, 1.0], size=(100, b.size))
        vals.extend((sg * b[None, :]).mean(axis=1).tolist())
    res["C"] = summarise(vals, obs["net"])

    # the reduced universe's OWN new top ten
    ret = np.where(obs["ent"], np.asarray(P["ocT"], float), np.asarray(P["r1T"], float)) - \
        np.where(obs["ent"], mkt_oc[:, None], mkt_cc[:, None])
    tr, open_end, _nb = V65.trades_of(obs["hold"], ret)
    pnl = np.array([p * 1e4 for _r, _e, _a, p, _s in tr])
    g4 = V50.four_groups(tr, pnl, P, e2)
    per = {}
    for r, _e, _a, p, _s in tr:
        per[r] = per.get(r, 0.0) + p * 1e4
    tot = sum(per.values())
    top = sorted(per.items(), key=lambda kv: -kv[1])[:10]

    out = dict(study=STUDY, removed=syms, look_ahead=True,
               observed={k: v for k, v in obs.items() if k not in ("hold", "v", "mask", "ent", "cn")},
               full_universe={k: v for k, v in full.items() if k not in ("hold", "v", "mask", "ent", "cn")},
               nulls=res, four_groups=g4, open_at_end=open_end,
               new_top10=[dict(symbol=P["symbols"][r], pnl_bp=v, share=v / tot) for r, v in top],
               new_top10_share=float(sum(v for _r, v in top) / tot),
               note="D367: the ten names were chosen by knowing which turned out best. LOOK-AHEAD DIAGNOSTIC, "
                    "not a strategy; no version of this book is proposable.")
    p = REPO / "data" / "d367_reduced.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\n  wrote {p.name}: reduced net {obs['net']:+.2f} vs full {full['net']:+.2f}; "
          + ", ".join(f"{a} p95 {res[a]['p95']:+.2f}" for a in ("ROT", "APRIME", "GATEROT", "C"))
          + f"  ({el(t0)})  {PREP.rss_line()}")


def stage_report(P, t0):
    gp, rp = REPO / "data" / "d367_gates.json", REPO / "data" / "d367_reduced.json"
    Gj = json.loads(gp.read_text()) if gp.exists() else None
    Rj = json.loads(rp.read_text()) if rp.exists() else None
    print("\n" + "=" * 150)
    print("D367 -- the gate deconstructed, and the book without its ten best names")
    print("=" * 150)
    q = {}
    if Gj:
        gs = Gj["gates"]
        order = sorted(gs, key=lambda k: -gs[k]["timing_premium"])
        singles = [c for c in COND]
        pairs = [k for k in gs if "+" in k]
        print(f"\n  THE NINE CONDITIONS ALONE -- ranked by TIMING PREMIUM (net less its own rotation's median)")
        print(f"  {'gate':<8} {'open%':>6} {'gross':>7} {'net':>7} {'rot p50':>8} {'PREMIUM':>8} {'rot p95':>8} "
              f"{'rank%':>6} {'beat':>5} {'trades':>7}  condition")
        for c in sorted(singles, key=lambda k: -gs[k]["timing_premium"]):
            o, r = gs[c]["observed"], gs[c]["rotation"]
            print(f"  {c:<8} {100*o['open_share']:5.1f}% {o['gross']:+7.2f} {o['net']:+7.2f} "
                  f"{gs[c]['rot_p50']:+8.2f} {gs[c]['timing_premium']:+8.2f} {r['p95']:+8.2f} "
                  f"{r['pct_rank']:5.1f}% {r['draws_beating_observed']:5d} {o['trades']:7d}  {COND_TEXT[c][:52]}")
        s6 = gs["S6"]
        print(f"  {'S6':<8} {100*s6['observed']['open_share']:5.1f}% {s6['observed']['gross']:+7.2f} "
              f"{s6['observed']['net']:+7.2f} {s6['rot_p50']:+8.2f} {s6['timing_premium']:+8.2f} "
              f"{s6['rotation']['p95']:+8.2f} {s6['rotation']['pct_rank']:5.1f}% "
              f"{s6['rotation']['draws_beating_observed']:5d} {s6['observed']['trades']:7d}  ALL NINE")

        bp = sorted(pairs, key=lambda k: -gs[k]["timing_premium"])
        print(f"\n  THE TEN BEST PAIRS of 36, by timing premium")
        print(f"  {'gate':<10} {'open%':>6} {'net':>7} {'rot p50':>8} {'PREMIUM':>8} {'rot p95':>8} {'rank%':>6} "
              f"{'beat':>5} {'trades':>7}")
        for k in bp[:10]:
            o, r = gs[k]["observed"], gs[k]["rotation"]
            print(f"  {k:<10} {100*o['open_share']:5.1f}% {o['net']:+7.2f} {gs[k]['rot_p50']:+8.2f} "
                  f"{gs[k]['timing_premium']:+8.2f} {r['p95']:+8.2f} {r['pct_rank']:5.1f}% "
                  f"{r['draws_beating_observed']:5d} {o['trades']:7d}")
        sm = Gj["shared_offset_max"]
        n_sing = sum(1 for c in singles if gs[c]["rotation"]["above_p95"])
        n_pair = sum(1 for k in pairs if gs[k]["rotation"]["above_p95"])
        print(f"\n  MULTIPLICITY -- the SHARED-OFFSET maximum over {Gj['live_gates']} non-degenerate gates: "
              f"p50 {sm['p50']:+.2f} p95 {sm['p95']:+.2f} max {sm['max']:+.2f}; S6's premium "
              f"{s6['timing_premium']:+.2f} ranks {sm['pct_rank']:.1f}%, {sm['draws_beating_observed']} draws beat it")
        print(f"  degenerate gates (fewer than {MIN_OPEN} open bars): {len(Gj['degenerate'])}"
              + (f" -- {', '.join(Gj['degenerate'])}" if Gj["degenerate"] else ""))
        best_single = max(singles, key=lambda k: gs[k]["timing_premium"])
        best_pair = max(pairs, key=lambda k: gs[k]["timing_premium"])
        q["Q1"] = any(gs[c]["rotation"]["above_p95"] for c in singles)
        q["Q2"] = best_single == "C9"
        q["Q3"] = all(s6["timing_premium"] > gs[c]["timing_premium"] for c in singles)
        q["Q4"] = bool(s6["timing_premium"] > sm["p95"])
        q["Q5"] = bool(gs[best_pair]["timing_premium"] > s6["timing_premium"])
        q["Q6"] = bool(n_pair < 18)

    if Rj:
        o, f, N = Rj["observed"], Rj["full_universe"], Rj["nulls"]
        print(f"\n  THE BOOK WITHOUT ITS TEN BEST NAMES -- LOOK-AHEAD DIAGNOSTIC, NOT A STRATEGY")
        print(f"  removed: {', '.join(Rj['removed'])}")
        print(f"  {'':<20} {'gross':>7} {'net':>7} {'Sharpe':>7} {'ann':>8} {'maxDD':>6} {'trades':>7} {'era2':>7}")
        for lbl, s in (("full universe", f), ("minus the ten", o)):
            print(f"  {lbl:<20} {s['gross']:+7.2f} {s['net']:+7.2f} {s['sharpe']:+7.3f} {s['ann_bp']/100:+7.1f}% "
                  f"{s['maxdd']:6.0f} {s['cost_parts']['trades']:7d} {s['era2']:+7.2f}")
        print(f"  {'arm':<10} {'draws':>6} {'p50':>8} {'p95':>8} {'max':>8} {'rank%':>7} {'beat':>5}  above p95?")
        for a in ("ROT", "APRIME", "GATEROT", "C"):
            d = N[a]
            print(f"  {a:<10} {d['draws']:>6} {d['p50']:+8.2f} {d['p95']:+8.2f} {d['max']:+8.2f} "
                  f"{d['pct_rank']:6.1f}% {d['draws_beating_observed']:5d}  {'YES' if d['above_p95'] else 'no'}")
        g4 = Rj["four_groups"]
        print(f"  the reduced universe's OWN new top ten take {100*Rj['new_top10_share']:.0f}% of its P&L "
              f"(the full universe's took 45%): "
              + ", ".join(f"{d['symbol']} {100*d['share']:.1f}%" for d in Rj["new_top10"][:5]) + ", ...")
        print(f"  names to half the P&L {g4['names_to_half_pnl']} of {g4['n_names']}; top trade "
              f"{g4['top_trade']['symbol']} {g4['top_trade']['entry_date']} {g4['top_trade']['pnl_bp']:+,.0f} bp "
              f"= {100*g4['top_trade']['share_of_pnl']:.1f}%")
        q["Q7"] = bool(o["net"] > 0 and all(N[a]["above_p95"] for a in ("ROT", "APRIME", "GATEROT")))
        q["Q8"] = bool(abs(100 * Rj["new_top10_share"] - 45.0) <= 10.0)

    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    print("\nPREDICTIONS")
    if Gj:
        gs = Gj["gates"]
        bs = max(COND, key=lambda k: gs[k]["timing_premium"])
        bpr = max([k for k in gs if "+" in k], key=lambda k: gs[k]["timing_premium"])
        print(f"  Q1 (LOAD-BEARING) at least one SINGLE condition is above the p95 of its own rotation: "
              f"{v_(q['Q1'])} -- {sum(1 for c in COND if gs[c]['rotation']['above_p95'])} of 9 are")
        print(f"  Q2 C9 has the largest timing premium of the nine singles: {v_(q['Q2'])} -- largest is {bs} at "
              f"{gs[bs]['timing_premium']:+.2f} (C9 {gs['C9']['timing_premium']:+.2f})")
        print(f"  Q3 S6's timing premium exceeds every single condition's: {v_(q['Q3'])} -- S6 "
              f"{gs['S6']['timing_premium']:+.2f} vs best single {bs} {gs[bs]['timing_premium']:+.2f}")
        print(f"  Q4 S6's premium is above the p95 of the SHARED-OFFSET MAX: {v_(q['Q4'])} -- "
              f"{gs['S6']['timing_premium']:+.2f} vs {Gj['shared_offset_max']['p95']:+.2f}")
        print(f"  Q5 (AGAINST) the best PAIR's premium exceeds S6's: {v_(q['Q5'])} -- {bpr} "
              f"{gs[bpr]['timing_premium']:+.2f} vs S6 {gs['S6']['timing_premium']:+.2f}")
        print(f"  Q6 fewer than half the 36 pairs clear their own p95: {v_(q['Q6'])} -- "
              f"{sum(1 for k in gs if '+' in k and gs[k]['rotation']['above_p95'])} of 36")
    if Rj:
        N = Rj["nulls"]
        print(f"  Q7 (LOAD-BEARING) reduced universe net > 0 and above the p95 of ROT, A' and GATE-ROT: "
              f"{v_(q['Q7'])} -- net {Rj['observed']['net']:+.2f}; "
              + ", ".join(f"{a} p95 {N[a]['p95']:+.2f}" for a in ("ROT", "APRIME", "GATEROT")))
        print(f"  Q8 the reduced universe's own top-10 share is within 10 points of 45%: {v_(q['Q8'])} -- "
              f"{100*Rj['new_top10_share']:.0f}%")

    out = dict(study=STUDY, predictions=q, gates=(Gj if Gj else None), reduced=(Rj if Rj else None))
    p = REPO / "data" / "d367_report.json"
    p.write_text(json.dumps(V65.clean(out), indent=1))
    print(f"\nwrote {p.name}  ({el(t0)})  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--reduced", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    print("D367  the gate deconstructed, and the book without its ten best names")
    P = PREP.prep(need_grids=False)
    if a.selftest:
        stage_selftest(P, t0)
    elif a.gates:
        stage_gates(P, a.draws, t0)
    elif a.reduced:
        stage_reduced(P, a.draws, t0)
    elif a.report:
        stage_report(P, t0)
    else:
        ap.error("one of --selftest, --gates, --reduced, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
