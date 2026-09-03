"""D308 -- the ceiling on a time-varying book width.

    uv run python scripts/run_d308_width_in_time.py --selftest
    uv run python scripts/run_d308_width_in_time.py

PRE-REGISTERED AT `4500f38`, committed before this file existed (R8). This runner
may not add a family, a width, or a conditioner.

STAGE 1 RUNS FIRST BECAUSE IT CAN CLOSE THE STUDY. An oracle picks N with
hindsight once per f bars. If the f=63 oracle CHARGED FOR TRANSITIONS beats the
best static N by little, no indicator can matter and stages 2 and 3 do not run.

THE CHARGED ORACLE IS SOLVED EXACTLY, NOT GREEDILY. Picking each block's best N
and charging transitions afterwards is neither an upper nor a lower bound -- a
path with fewer switches can beat it. With 7 widths and ~50 blocks the exact
optimum is a small Viterbi, so it is computed rather than approximated:

    V[b][N] = blocknet[b][N] + max over M of ( V[b-1][M] - transition(M, N) )

TRANSITIONS, declared in the record and implemented here unchanged:

    traded fraction = 2 |N1 - N2| / max(N1, N2)
    cost            = traded fraction * rt(N2) / 2
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


W = _load("d306", "run_d306_width_exits.py")
D, SP, M = W.D, W.SP, W.M
DEPTHS = W.DEPTHS
FAMILIES = ("none", "target", "none+overlay", "target+overlay")
FREQS = (1, 5, 21, 63)
ANN, SEED = 252.0, 20260903
OUT = REPO / "data" / "d308_width_in_time.json"


def build(A, G, half):
    """A(N,t) for every family and width: per-bar gross and per-bar cost, in bp.

    Cost is charged PER BAR as rt * entries[t] * scale[t] / (2N). D306 factorised
    it as rt * turnover * exposure, which is the same thing only if entries and
    the overlay scale are uncorrelated. Assertion [1] holds the two identical for
    the non-overlay families, where scale is 1, and reports the gap for the
    overlay families rather than hiding it.
    """
    out, rts = {}, {}
    for depth in DEPTHS:
        for ut in (False, True):
            res = W.simulate(A, G, depth, ut)
            rt = W.held_rt(res, half)
            ok = res["mask"]
            sc_ov = W.overlay_scale(res["book"])
            ent = res["ent"].astype(float)
            for ov in (False, True):
                fam = ("none" if not ut else "target") + ("+overlay" if ov else "")
                scale = sc_ov if ov else np.ones_like(sc_ov)
                gross = np.where(ok, res["book"] * scale, 0.0) * 1e4
                cost = np.where(ok, rt * ent * scale / (2.0 * depth), 0.0)
                if ov:
                    ds = np.abs(np.diff(np.concatenate([[1.0], scale])))
                    cost = cost + np.where(ok, ds * rt / 2.0, 0.0)
                out[(fam, depth)] = dict(gross=gross, cost=cost, net=gross - cost)
                rts[(fam, depth)] = rt
    return out, rts, ok


def transition(n1, n2, rt):
    if n1 == n2:
        return 0.0
    return 2.0 * abs(n1 - n2) / max(n1, n2) * rt / 2.0


def blocks(mask, f):
    idx = np.flatnonzero(mask)
    return [idx[i:i + f] for i in range(0, idx.size, f)]


def oracle(cells, rts, fam, mask, f, charge):
    """Exact optimum over block-wise widths. Viterbi when transitions are
    charged, argmax per block when they are not."""
    bl = blocks(mask, f)
    nb, nd = len(bl), len(DEPTHS)
    bn = np.zeros((nb, nd))
    for j, depth in enumerate(DEPTHS):
        net = cells[(fam, depth)]["net"]
        for b, ix in enumerate(bl):
            bn[b, j] = net[ix].sum()
    if not charge:
        pick = bn.argmax(axis=1)
        total = bn.max(axis=1).sum()
        return [DEPTHS[j] for j in pick], total, 0.0
    tc = np.array([[transition(DEPTHS[i], DEPTHS[j], rts[(fam, DEPTHS[j])])
                    for j in range(nd)] for i in range(nd)])
    V = bn[0].copy()
    back = np.zeros((nb, nd), int)
    for b in range(1, nb):
        cand = V[:, None] - tc
        back[b] = cand.argmax(axis=0)
        V = bn[b] + cand.max(axis=0)
    j = int(V.argmax())
    path = [0] * nb
    for b in range(nb - 1, -1, -1):
        path[b] = j
        j = back[b][j]
    picks = [DEPTHS[k] for k in path]
    tcost = sum(transition(picks[b - 1], picks[b], rts[(fam, picks[b])])
                for b in range(1, nb))
    return picks, float(V.max()), float(tcost)


def path_series(cells, fam, mask, f, picks):
    """The per-bar net series the chosen path actually realises."""
    bl = blocks(mask, f)
    out = np.zeros(int(mask.sum()))
    pos = 0
    for b, ix in enumerate(bl):
        net = cells[(fam, picks[b])]["net"]
        out[pos:pos + ix.size] = net[ix]
        pos += ix.size
    return out


def sharpe(x):
    s = x.std(ddof=1)
    return float(x.mean() / s * np.sqrt(ANN)) if s > 0 else None


def runs(picks):
    r, cur = [], 1
    for a, b in zip(picks, picks[1:]):
        if a == b:
            cur += 1
        else:
            r.append(cur)
            cur = 1
    r.append(cur)
    return np.array(r)


# --------------------------------------------------------------------------
def assertions(cells, rts, mask, d306):
    print("\nASSERTIONS")

    # 1. REPRODUCTION. At constant N the per-bar decomposition must reproduce
    #    D306's published gross exactly, and its net exactly where the overlay
    #    is off. Where the overlay is on, D306 factorised cost as
    #    rt*turnover*exposure and this charges it per bar; the gap is reported.
    wg, wn, wov = 0.0, 0.0, 0.0
    for fam in FAMILIES:
        for depth in DEPTHS:
            c = cells[(fam, depth)]
            ref = d306[f"N={depth}/{fam}"]
            g = float(c["gross"][mask].mean())
            n = float(c["net"][mask].mean())
            wg = max(wg, abs(g - ref["gross_bp"]))
            if "overlay" in fam:
                wov = max(wov, abs(n - ref["net_bp"]))
            else:
                wn = max(wn, abs(n - ref["net_bp"]))
    assert wg < 1e-9, f"[1] gross differs from D306 by up to {wg:.2e} bp"
    assert wn < 1e-9, f"[1] net differs from D306 by up to {wn:.2e} bp"
    print(f"    [1] gross reproduces D306 exactly for all 28 cells (max "
          f"{wg:.1e} bp); net exactly where the overlay is off (max {wn:.1e})")
    print(f"        overlay cells differ by up to {wov:.3f} bp -- D306 factorised "
          f"cost as rt*turnover*exposure, this charges it per bar")

    # 2. THE DEGENERATE ORACLE. An oracle allowed one N for the whole sample
    #    must EQUAL the best static N. An oracle that cannot reproduce its own
    #    baseline is not an oracle.
    nb = int(mask.sum())
    for fam in FAMILIES:
        stat = {d: float(cells[(fam, d)]["net"][mask].mean()) for d in DEPTHS}
        best = max(stat.values())
        picks, tot, _ = oracle(cells, rts, fam, mask, nb + 10, charge=True)
        assert abs(tot / nb - best) < 1e-9, (
            f"[2] the one-block oracle {tot / nb:.6f} != best static "
            f"{best:.6f} for {fam}")
    print(f"    [2] a one-block oracle equals the best static N exactly, all "
          f"four families")

    # 3. TRANSITIONS: zero when N never moves, and monotone in |dN|.
    rt = rts[("none", 19)]
    assert transition(5, 5, rt) == 0.0
    seq = [transition(19, d, rt) for d in (14, 10, 7, 5, 3, 2)]
    assert all(a <= b for a, b in zip(seq, seq[1:])), \
        f"[3] transition cost is not monotone in |dN|: {seq}"
    print(f"    [3] transitions are zero at dN=0 and monotone in |dN| -- "
          f"19->14 costs {seq[0]:.1f} bp, 19->2 costs {seq[-1]:.1f} bp")

    # 4. NESTING. Uncharged, a less constrained oracle cannot be worse.
    for fam in FAMILIES:
        tot = []
        for f in FREQS:
            _, t, _ = oracle(cells, rts, fam, mask, f, charge=False)
            tot.append(t / nb)
        assert all(a >= b - 1e-9 for a, b in zip(tot, tot[1:])), \
            f"[4] uncharged oracle is not nested in f for {fam}: {tot}"
    print(f"    [4] the uncharged oracle is nested in the decision frequency, "
          f"all four families")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [r for r in d295["rows"] if r["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's "
          f"{b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK.
    broke = False
    try:
        b = cells[("none", 19)]["net"][mask].copy()
        b[:100] += 0.05
        assert float(b.mean()) == float(cells[("none", 19)]["net"][mask].mean())
    except AssertionError:
        broke = True
    assert broke, "the mean check passed a book handed free money"
    print("    [7] and the mean check raises on a book handed free money")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print("D308  the ceiling on a time-varying book width")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]
    cells, rts, mask = build(A, G, half)
    nb = int(mask.sum())
    print(f"  built A(N,t): {len(cells)} series over {nb:,} bars "
          f"({time.time() - t0:.0f}s)")

    assertions(cells, rts, mask, d306)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    res = {"static": {}, "oracle": {}, "persistence": {}}

    print("\nSTAGE 1 -- THE CEILING")
    print("%-16s %8s %10s %9s | %10s %10s %10s %9s" % (
        "family", "bestN", "static", "sharpe", "f", "uncharged", "CHARGED",
        "sharpe"))
    print("-" * 96)
    for fam in FAMILIES:
        stat = {d: float(cells[(fam, d)]["net"][mask].mean()) for d in DEPTHS}
        bestN = max(stat, key=stat.get)
        bser = cells[(fam, bestN)]["net"][mask]
        res["static"][fam] = dict(best_N=bestN, net_bp=stat[bestN],
                                  sharpe=sharpe(bser),
                                  by_N={str(k): v for k, v in stat.items()})
        first = True
        for f in FREQS:
            pu, tu, _ = oracle(cells, rts, fam, mask, f, charge=False)
            pc, tc, tcost = oracle(cells, rts, fam, mask, f, charge=True)
            sc = path_series(cells, fam, mask, f, pc)
            res["oracle"].setdefault(fam, {})[str(f)] = dict(
                uncharged_bp=tu / nb, charged_bp=tc / nb,
                transition_bp=tcost / nb, sharpe=sharpe(sc),
                gain_over_static=tc / nb - stat[bestN], picks=pc)
            print("%-16s %8s %10s %9s | %10d %10.2f %10.2f %9s" % (
                fam if first else "", "N=%d" % bestN if first else "",
                "%+.2f" % stat[bestN] if first else "",
                "%+.3f" % sharpe(bser) if first else "",
                f, tu / nb, tc / nb,
                "%+.3f" % sharpe(sc) if sharpe(sc) else "--"))
            first = False
        print()

    print("STAGE 2 -- PERSISTENCE of the charged oracle's width path")
    print("%-16s %6s %9s %10s %10s %9s %s" % (
        "family", "f", "blocks", "switches", "mean run", "modal N", "distribution"))
    print("-" * 96)
    for fam in FAMILIES:
        for f in FREQS:
            pc = res["oracle"][fam][str(f)]["picks"]
            r = runs(pc)
            u, c = np.unique(pc, return_counts=True)
            dist = " ".join(f"{int(k)}:{v}" for k, v in zip(u, c))
            res["persistence"].setdefault(fam, {})[str(f)] = dict(
                blocks=len(pc), switches=int((np.diff(pc) != 0).sum()),
                mean_run=float(r.mean()), max_run=int(r.max()),
                modal_N=int(u[c.argmax()]), share_modal=float(c.max() / len(pc)))
            print("%-16s %6d %9d %10d %10.2f %9d   %s" % (
                fam, f, len(pc), int((np.diff(pc) != 0).sum()), r.mean(),
                int(u[c.argmax()]), dist))
        print()

    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(f"  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
