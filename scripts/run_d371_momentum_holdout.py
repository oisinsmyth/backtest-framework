"""D371 -- the momentum book's out-of-sample protocol. BUILT AND REHEARSED; the read is NOT spent here.

    uv run python scripts/run_d371_momentum_holdout.py --selftest
    uv run python scripts/run_d371_momentum_holdout.py --pipe
    uv run python scripts/run_d371_momentum_holdout.py --dry
    uv run python scripts/run_d371_momentum_holdout.py --rehearse
    uv run python scripts/run_d371_momentum_holdout.py --read --spend-the-holdout      # NOT RUN

BOTH GATES ON ONE READ IS TWO TESTS. Each arm must clear the p97.5 of its nulls, not the p95 -- a Bonferroni
split of alpha across the two arms, fixed in the pre-registration so it cannot be chosen afterwards to suit
whichever passes. The unadjusted p95 is reported beside and labelled.

THE READ IS GUARDED TWICE. `--read` refuses without `--spend-the-holdout`, and refuses without the committed
construction file naming the two arms. `--rehearse` runs the read's exact code path on the MINING fixture with
tiny draw counts and writes only to temp/ -- so the one execution that matters is not the first execution.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_d357_holdout_read as V57           # noqa: E402  -- repoint(), FIXTURES, the re-pointing machinery
import d369_fast_kernel as FK                 # noqa: E402
import run_d369_null_precision as V69         # noqa: E402  -- summarise(), bootstrap SE
import run_d367_gate_deconstruction as V67    # noqa: E402
import run_d366_gated_buffer as V66           # noqa: E402
import run_d365_momentum_buffer as V65        # noqa: E402

PREP, V58, V50 = FK.PREP, FK.V58, V66.V50
STUDY, SEED = 371, V66.SEED
EXIT_ONE, ALPHA_Q = 90, 0.975                 # p97.5: alpha = 0.05 split across two arms
ARMS = ("S6", "C9")
CONSTRUCTION = REPO / "data" / "d371_construction.json"
OUT = REPO / "data"

# The holdout universe's own construction constants, taken from the counts-only --dry stage (which reads no
# return). Used as a REGRESSION LOCK inside prep, not as an independent check -- there is no prior record for
# this fixture to cross-check against. See d348_prep.EXPECT.
HOLDOUT_EXPECT = dict(tag="holdout", f0_applied=951, f0_pct=2.70, floor_share=0.310516)


def el(t0):
    return f"{time.time() - t0:.0f}s"


# ================================================================== the construction
def build(P):
    pct = V58.pct_of(P, V65.SCORE)
    elig = np.asarray(P["elig"], bool)
    cond, C, vq = V67.conditions(P)
    G = V67.gate_set(cond)
    cc, oc = V66.dvw_market(P)
    return pct, elig, G, cc, oc


def kernel(P, pct, elig, cc, oc):
    K = FK.Kernel(P, pct, elig, cc, oc)
    K.keep_open = K.keep_shut                 # the single exit rank; D367 measured the 80/90 split at 0.02 bp/bar
    return K


def run_primary(P, gate, pct, elig, cc, oc, zeros):
    """The frozen construction under the single exit rank, with the full stats the hurdles need."""
    hold = V66.hold_of(pct, elig, gate, P["m_start"], cap=V66.CAP, lo_open=EXIT_ONE, lo_shut=V66.LO_SHUT)
    v, mask, ent, cn = V66.book_of(P, hold, cc, oc)
    c = V66.costs(P, hold, zeros)
    s = V66.stats(P, v, mask, c["total"])
    s.update(cost_parts=c, hold=hold, ent=ent, v=v, mask=mask,
             members=float(hold.sum(axis=1)[mask].mean()))
    return s


def hurdles(P, s, gate, elig, cc, oc, nulls):
    """H1-H6 exactly as pre-registered. H4 is retained although the in-sample book fails it at 11.7%."""
    ret = np.where(s["ent"], np.asarray(P["ocT"], float), np.asarray(P["r1T"], float)) - \
        np.where(s["ent"], oc[:, None], cc[:, None])
    tr, open_end, _nb = V65.trades_of(s["hold"], ret)
    pnl = np.array([p * 1e4 for _r, _e, _a, p, _s in tr])
    g4 = V50.four_groups(tr, pnl, P, elig)
    two_c, tc = V65.per_trade_two_c(P, tr, "PUB")
    H = {}
    H["H1"] = dict(ok=bool(s["net"] > 0), value=s["net"], text="net PUB bp/bar > 0 after hedge costs")
    both = [nulls[a] for a in ("GATEROT", "APRIME")]
    H["H2"] = dict(ok=all(d["verdict"] == "CLEARS" for d in both),
                   value=min(d["margin"] for d in both),
                   text=f"net above the p{100*ALPHA_Q:g} of BOTH nulls",
                   detail={a: dict(p_adj=nulls[a]["p_adj"], se=nulls[a]["p95_se"], margin=nulls[a]["margin"],
                                   in_se=nulls[a]["margin_in_se"], verdict=nulls[a]["verdict"])
                           for a in ("GATEROT", "APRIME")})
    H["H3"] = dict(ok=bool(g4["mean_trimmed_bp"] > float(two_c.mean())),
                   value=g4["mean_trimmed_bp"] - float(two_c.mean()),
                   text=f"trimmed mean/trade {g4['mean_trimmed_bp']:+.1f} > round trip {two_c.mean():.1f}")
    top = g4["top_trade"]
    H["H4"] = dict(ok=bool(abs(top["share_of_pnl"]) <= 0.10), value=100 * top["share_of_pnl"],
                   text=f"top trade {top['symbol']} {top['entry_date']} is {100*top['share_of_pnl']:.1f}% of P&L "
                        f"(ceiling 10%)")
    H["H5"] = dict(ok=bool(g4["names_to_half_pnl"] >= 10), value=g4["names_to_half_pnl"],
                   text=f"{g4['names_to_half_pnl']} names to half the P&L (floor 10)")
    H["H6"] = dict(ok=bool(s["sharpe"] > 0), value=s["sharpe"], text="net PUB Sharpe > 0")
    return H, g4, dict(n=len(tr), round_trip=float(two_c.mean()), open_at_end=open_end)


def null_arm(P, K, gate, pct, elig, cc, oc, obs, draws, which, seed):
    m0 = P["m_start"]
    vals = []
    for i in range(draws):
        rng = np.random.default_rng([SEED, STUDY, seed, i])
        if which == "GATEROT":
            vals.append(K.net(V67.rotate(gate, m0, int(rng.integers(1, P["T"] - m0)))))
        else:
            vals.append(kernel(P, V65.aprime_draw(pct, elig, rng), elig, cc, oc).net(gate))
    d = V69.summarise(vals, obs, seed=seed)
    x = np.asarray(vals, float)
    d["p_adj"] = float(np.quantile(x, ALPHA_Q))               # the Bonferroni-adjusted bar
    d["p95_unadjusted"] = d["p95"]
    d["margin"] = float(obs - d["p_adj"])
    d["margin_in_se"] = d["margin"] / d["p95_se"] if d["p95_se"] > 0 else None
    d["verdict"] = ("UNRESOLVED" if abs(d["margin"]) < 2 * d["p95_se"]
                    else ("CLEARS" if d["margin"] > 0 else "FAILS"))
    return d


def evaluate(P, label, draws, t0):
    """Both arms on one fixture segment: observed, both nulls, all six hurdles."""
    pct, elig, G, cc, oc = build(P)
    zeros = np.zeros((P["T"], P["n"]), float)
    K = kernel(P, pct, elig, cc, oc)
    res = {}
    for j, arm in enumerate(ARMS):
        gate = G[arm]
        s = run_primary(P, gate, pct, elig, cc, oc, zeros)
        N = {w: null_arm(P, K, gate, pct, elig, cc, oc, s["net"], draws, w, 10 + j * 2 + k)
             for k, w in enumerate(("GATEROT", "APRIME"))}
        H, g4, led = hurdles(P, s, gate, elig, cc, oc, N)
        res[arm] = dict(net=s["net"], gross=s["gross"], cost=s["cost"], sharpe=s["sharpe"],
                        maxdd=s["maxdd"], members=s["members"], trades=led["n"], era1=s["era1"],
                        era2=s["era2"], vol=s["vol"], bars=s["bars"],
                        open_share=float(gate[P["m_start"]:].mean()), nulls=N, hurdles=H,
                        four_groups=g4, ledger=led,
                        passed=all(h["ok"] for h in H.values()),
                        # the per-bar net series and its dates, so the COMBINED arm is computable afterwards
                        series=dict(dates=[P["dates"][t] for t in range(P["T"]) if s["mask"][t]],
                                    net=[float(x - s["cost"]) for x in s["v"][s["mask"]]]))
        print(f"    {label}/{arm}: net {s['net']:+.3f} sharpe {s['sharpe']:+.3f} trades {led['n']} -- "
              f"{sum(h['ok'] for h in H.values())}/6 hurdles ({el(t0)})", flush=True)
    return res


def print_table(label, R):
    print(f"\n  {label}")
    print(f"  {'arm':<5}{'open%':>7}{'gross':>8}{'net':>8}{'Sharpe':>8}{'maxDD':>8}{'trades':>8}   hurdles")
    for arm in ARMS:
        r = R[arm]
        hs = " ".join(f"{k}{'OK' if v['ok'] else 'X'}" for k, v in r["hurdles"].items())
        print(f"  {arm:<5}{100*r['open_share']:6.1f}%{r['gross']:+8.2f}{r['net']:+8.2f}{r['sharpe']:+8.3f}"
              f"{r['maxdd']:8.0f}{r['trades']:8d}   {hs}   {'PASS' if r['passed'] else 'FAIL'}")
    for arm in ARMS:
        for k, v in R[arm]["hurdles"].items():
            if not v["ok"]:
                print(f"    {arm} {k} FAILED: {v['text']}")


# ================================================================== stages
def stage_selftest(t0):
    print("D371  selftest -- the holdout is NOT read")
    V57.repoint("mining")
    P = PREP.prep(need_grids=False, verbose=False)
    pct, elig, G, cc, oc = build(P)

    # [NOREAD] -- the audit hook installed by the D365 chain refuses ANY path containing 'holdout', including
    # metadata that carries only symbol names. Discovered by trying it: the first version of this self-test read
    # the holdout's meta file to assert disjointness and was refused. That refusal IS the assertion worth having,
    # so [DISJOINT] moves to the stages that legitimately re-point at the fixture (--dry, --pipe, --read).
    ma = set(json.loads(V57.FIXTURES["mining"]["meta"].read_text())["symbols"])
    blocked = None
    try:
        json.loads(V57.FIXTURES["holdout"]["meta"].read_text())
    except RuntimeError as e:
        blocked = str(e)
    assert blocked and "HOLDOUT-GUARD" in blocked, "[NOREAD] the audit hook did NOT refuse the holdout metadata"
    print(f"    [NOREAD] the audit hook refuses even the holdout's METADATA from a mining-mode process "
          f"({V57.FIXTURES['holdout']['meta'].name}); mining carries {len(ma):,} names. [DISJOINT] is asserted "
          f"in --dry, which is the stage entitled to look.")

    for arm in ARMS:
        assert FK.Kernel(P, pct, elig, cc, oc).net(G[arm]) == \
            V66.run_cell(P, G[arm], pct, elig, cc, oc, np.zeros((P["T"], P["n"]), float))["net"], f"[FAST] {arm}"
    print(f"    [FAST] the kernel is bit-identical to D366's functions on both arms")

    m0 = P["m_start"]
    k = int(np.random.default_rng([SEED, STUDY, 1]).integers(1, P["T"] - m0))
    for arm in ARMS:
        r = V67.rotate(G[arm], m0, k)
        assert r[m0:].sum() == G[arm][m0:].sum() and V67.circ_runs(r[m0:]) == V67.circ_runs(G[arm][m0:]), \
            f"[SHARE] {arm}"
    print(f"    [SHARE] rotations preserve on-share and the circular run-length multiset on both arms")

    # [GUARD] -- both refusals, exercised
    refused = []
    for args, why in ((["--read"], "without --spend-the-holdout"),
                      (["--read", "--spend-the-holdout"], "without the committed construction")):
        try:
            guard(argparse.Namespace(read=True, spend_the_holdout=("--spend-the-holdout" in args)))
        except SystemExit:
            refused.append(why)
    assert len(refused) == 2 or (CONSTRUCTION.exists() and len(refused) == 1), f"[GUARD] only refused {refused}"
    print(f"    [GUARD] --read refuses {', '.join(refused)}"
          + ("" if not CONSTRUCTION.exists() else "  (the construction file exists, so only the flag guard fires)"))

    broke = []
    try:
        assert blocked is None
    except AssertionError:
        broke.append("NOREAD/the hook fired")
    try:
        # [2,2] vs [1,1,1,1]. (The first version compared [1,1,0] with [1,0,0], which BOTH give [1,2] --
        # a broken-input check that could not fail, which is worse than none.)
        assert V67.circ_runs(np.array([1, 1, 0, 0], bool)) == V67.circ_runs(np.array([1, 0, 1, 0], bool))
    except AssertionError:
        broke.append("SHARE/runs")
    try:
        guard(argparse.Namespace(read=True, spend_the_holdout=False))
    except SystemExit:
        broke.append("GUARD")
    try:
        assert PREP.prep(need_grids=False, verbose=False)["n"] == 1
    except AssertionError:
        broke.append("PIPE/name count")
    assert len(broke) == 4, f"[6] only {broke} raised"
    print(f"    [6] each of {', '.join(broke)} raises on a deliberately broken input")
    print(f"\nOK  selftest passes  ({el(t0)})  {PREP.rss_line()}   HOLDOUT READS SPENT: 0")


def stage_rehearse(draws, t0):
    """The read's exact code path on the MINING fixture. NOT A RESULT."""
    print(f"D371  REHEARSAL on the MINING fixture -- NOT A RESULT; draws {draws}")
    V57.repoint("mining")
    P = PREP.prep(need_grids=False, verbose=False)
    R = evaluate(P, "rehearsal", draws, t0)
    print_table("REHEARSAL (mining fixture, tiny draws) -- NOT A RESULT", R)
    f = REPO / "temp" / "d371_rehearsal_mining.json"
    f.write_text(json.dumps(V65.clean(dict(study=STUDY, rehearsal=True, draws=draws, arms=R,
                                           note="D371 REHEARSAL on the MINING fixture: exercises the read "
                                                "stage end to end. Nothing here is a result.")), indent=1))
    print(f"\n  wrote {f.relative_to(REPO)}  ({el(t0)})  {PREP.rss_line()}   HOLDOUT READS SPENT: 0")


def combined(R, mining):
    """The COMBINED arm, per D367 section 5 -- and a stated deviation from the literal wording.

    'Combined data' cannot mean one merged universe here: ranking across the union of 2,376 names is a DIFFERENT
    strategy from the one being read, with a different top 5% on every bar. What is combined is the P&L.

    AND IT IS COMBINED DATE BY DATE, NOT CONCATENATED. Both fixtures span the same 2010-2026 calendar, so
    appending one series to the other would count every trading day twice and treat the two as independent
    observations of different periods. They are not: they are two disjoint universes over the SAME days. The
    combined book is therefore the 50/50 portfolio held simultaneously -- the mean of the two books' returns on
    each shared date -- which is what actually holding both would have earned, and which can beat either on
    Sharpe through diversification even when one book's mean is lower. The correlation between the two is
    reported so that effect is visible rather than implied.

    It is CONTEXT, never evidence: the mining half is the fixture the construction was selected on."""
    out = {}
    for arm in ARMS:
        md = dict(zip(mining[arm]["dates"], mining[arm]["net"]))
        hd = dict(zip(R[arm]["series"]["dates"], R[arm]["series"]["net"]))
        both = sorted(set(md) & set(hd))
        a = np.array([md[d] for d in both], float)          # mining book, on the shared dates
        b = np.array([hd[d] for d in both], float)          # holdout book, same dates
        x = 0.5 * (a + b)                                   # the 50/50 portfolio, held simultaneously
        sh = lambda y: (float(np.mean(y) / np.std(y, ddof=1) * np.sqrt(252.0))
                        if np.std(y, ddof=1) > 0 else None)
        out[arm] = dict(shared_bars=len(both), mining_only_bars=len(md), holdout_only_bars=len(hd),
                        net=float(np.mean(x)), vol=float(np.std(x, ddof=1)), sharpe=sh(x),
                        ann_pct=float(np.mean(x) * 252.0 / 100.0),
                        mining_net=float(np.mean(a)), mining_sharpe=sh(a),
                        holdout_net=float(np.mean(b)), holdout_sharpe=sh(b),
                        correlation=float(np.corrcoef(a, b)[0, 1]) if len(both) > 2 else None)
    return out


def stage_mining_series(t0):
    """Store the MINING per-bar series for both arms, so the combined arm is computable after the read
    without re-running anything. Reads no holdout data."""
    V57.repoint("mining")
    P = PREP.prep(need_grids=False, verbose=False)
    pct, elig, G, cc, oc = build(P)
    zeros = np.zeros((P["T"], P["n"]), float)
    out = {}
    for arm in ARMS:
        s = run_primary(P, G[arm], pct, elig, cc, oc, zeros)
        out[arm] = dict(dates=[P["dates"][t] for t in range(P["T"]) if s["mask"][t]],
                        net=[float(x - s["cost"]) for x in s["v"][s["mask"]]], mean=s["net"])
        print(f"    mining/{arm}: {len(out[arm]['net']):,} bars, mean {s['net']:+.4f}")
    f = REPO / "temp" / "d371_mining_series.json"
    f.write_text(json.dumps(out, indent=1))
    print(f"  wrote {f.relative_to(REPO)}  ({el(t0)})")


def guard(a):
    if getattr(a, "read", False) and not getattr(a, "spend_the_holdout", False):
        print("REFUSED: --read requires --spend-the-holdout. The holdout is one clean read (RULES.md R8).")
        raise SystemExit(2)
    if getattr(a, "read", False) and not CONSTRUCTION.exists():
        print(f"REFUSED: {CONSTRUCTION.relative_to(REPO)} does not exist. The read runs only against a "
              f"COMMITTED construction, named before the fixture is touched.")
        raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pipe", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--rehearse", action="store_true")
    ap.add_argument("--mining-series", action="store_true")
    ap.add_argument("--read", action="store_true")
    ap.add_argument("--spend-the-holdout", action="store_true")
    ap.add_argument("--draws", type=int, default=2000)
    a = ap.parse_args()
    t0 = time.time()
    guard(a)
    if a.selftest:
        stage_selftest(t0)
    elif a.rehearse:
        stage_rehearse(min(a.draws, 50), t0)
    elif a.mining_series:
        stage_mining_series(t0)
    elif a.pipe:
        V57.stage_pipe()
    elif a.dry:
        V65.allow_holdout("D371 --dry: counts only, no return becomes a statistic")
        V57.repoint("holdout")
        PREP.EXPECT = HOLDOUT_EXPECT
        V57.stage_dry("holdout")
    elif a.read:
        print("D371 READ -- this spends the programme's one clean holdout read.")
        mine = json.loads((REPO / "temp" / "d371_mining_series.json").read_text()) \
            if (REPO / "temp" / "d371_mining_series.json").exists() else None
        V65.allow_holdout("D371 --read --spend-the-holdout: the principal's explicit authorisation, 2026-09-07")
        V57.repoint("holdout")
        PREP.EXPECT = HOLDOUT_EXPECT
        P = PREP.prep(need_grids=False, verbose=True)
        V65.assert_HOLDOUT_GUARD()
        R = evaluate(P, "holdout", a.draws, t0)
        print_table("HOLDOUT ALONE -- THE EVIDENCE", R)
        comb = combined(R, mine) if mine else None
        if comb:
            print(f"\n  COMBINED -- context, not evidence. The two books are ranked WITHIN their own universes "
                  f"and their per-bar series pooled; merging the universes would rank across 2,376 names and be "
                  f"a different strategy.")
            print(f"  {'arm':<5}{'bars':>8}{'net':>9}{'Sharpe':>9}   (mining bars are contaminated: the "
                  f"construction was selected on them)")
            for arm in ARMS:
                c = comb[arm]
                print(f"  {arm:<5}{c['bars']:8,}{c['net']:+9.3f}{c['sharpe']:+9.3f}")
        (OUT / "d371_read.json").write_text(json.dumps(V65.clean(
            dict(study=STUDY, arms=R, combined=comb, holdout_reads_spent=1)), indent=1))
        print(f"\n  HOLDOUT READS SPENT: 1.  Programme total: 1.")
    else:
        ap.error("one of --selftest, --pipe, --dry, --rehearse, --read")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
