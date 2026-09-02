"""D288 POST-CLOSURE probes -- overlay and confluence. NOT PART OF D288.

    uv run python scripts/d288_postclosure_probes.py

D288 CLOSED at `596b039` with zero gate-A survivors and a stop condition that
forbids a re-cut of its axes. This file does not reopen it and scores no cell
against it. It exists because the principal asked, after the closure, whether
combining the mined signals would be worth pursuing -- and the honest way to
answer is to measure it and DISCLOSE THE LOOKS, not to reason about it.

EVERY NUMBER HERE IS POST-HOC, ON THE MINING FIXTURE, AND SELECTED ON D288'S OWN
RESULTS. `close_in_range` is the primary only because D288's search crowned it.
Nothing here may promote anything. Its one legitimate use is to inform a
PRE-REGISTERED successor, and the successor must carry these looks (R13) --
which is the point of counting them.

TWO CONSTRUCTIONS, AND THEY ARE NOT THE SAME QUESTION.

  OVERLAY (weighted blend). Rank on w1*s1 + w2*s2. For equal IC the gain is
  sqrt(2/(1+rho)), MONOTONE in rho -- lower is strictly better, there is no
  interior optimum. Unequal IC changes the story completely: with optimal
  weights the gain runs through Sigma^-1, which at high rho puts a NEGATIVE
  weight on the weaker leg. That is residualisation, not confirmation.

  CONFLUENCE (AND gate). Hold a name only when BOTH signals put it in the same
  tail. Here rho DOES have an interior optimum: intersecting two N-of-M sets
  leaves ~N^2/M names under independence, so low rho empties the book, and high
  rho makes the filter a no-op.

THE CONTROL IS THE WHOLE TEST FOR CONFLUENCE. A filter SHRINKS the held set, so
it must be compared against simply taking a smaller N of the primary. Matched
count, not matched idea -- otherwise the filter is credited for concentration the
ranking already supplied. CLAUDE.md: a control must share the treatment's
nuisance, not just its count.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from math import comb
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


M = _load("run_mine_neutral", "run_mine_neutral.py")

OUT = REPO / "data" / "d288_postclosure_probes.json"
PRIMARY = "close_in_range"
N = 25
K = 20                      # the horizon at which the primary clears round-trip cost
TOP = 12                    # how many candidates the overlay arithmetic ranges over
COST_BP = 33.81 * 2         # D285's measured Corwin-Schultz on HELD names, round trip


def comb2(a, b, r):
    """Optimally-weighted two-signal IC: (a^2 + b^2 - 2*rho*a*b) / (1 - rho^2)."""
    if abs(r) >= 0.9999:
        return max(a, b)
    return float(np.sqrt(max((a * a + b * b - 2 * r * a * b) / (1 - r * r), 0.0)))


def main() -> int:
    g0 = json.loads((REPO / "data" / "d288_gate0_independence.json").read_text())
    fl = json.loads((REPO / "data" / "d288_gateA_floor.json").read_text())
    names, R = g0["names"], np.array(g0["spearman"])
    idx = {n: i for i, n in enumerate(names)}
    ot = fl["observed_t"]
    out = {"purpose": "POST-CLOSURE probes for D288. Score nothing, promote "
                      "nothing, and must be CARRIED as looks by any successor.",
           "primary": PRIMARY, "N": N, "k": K,
           "cost_bar_bp_round_trip": COST_BP}

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    g = M.P1.build_grids(panel, cleaned)
    scores, warm, _ = M.build_scores(panel, cleaned, g, live)
    base, T = warm & live, live.shape[1]
    fwd = M.forward_returns(panel, live)

    # ---- 1. the algebraic overlap the correlation alone does not show -----
    O, H, C_, Lo = g["open"], g["high"], g["close"], g["low"]
    ok = live & ((H - Lo) > 0) & np.isfinite(O) & np.isfinite(C_)
    down = ok & (C_ <= O)
    frac = float(down.sum() / ok.sum())
    out["algebraic_identity"] = {
        "pair": ["close_in_range", "lower_wick"],
        "note": "close_in_range=(C-L)/range, lower_wick=(min(O,C)-L)/range. When "
                "C<=O these are the SAME NUMBER, which a correlation of +0.368 "
                "does not reveal.",
        "identical_fraction": frac, "bars": int(ok.sum())}
    print(f"close_in_range == lower_wick on {frac:.1%} of "
          f"{int(ok.sum()):,} usable bars (every bar with C <= O)")

    # ---- 2. overlay arithmetic -------------------------------------------
    top = sorted(ot, key=ot.get, reverse=True)[:TOP]
    pairs = []
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            a, b = ot[top[i]], ot[top[j]]
            r = float(R[idx[top[i]], idx[top[j]]])
            c = comb2(a, b, r)
            eq = float((a + b) / np.sqrt(2 + 2 * r)) if r > -1 else float("inf")
            pairs.append({"a": top[i], "b": top[j], "rho": r,
                          "best_leg_t": max(a, b), "optimal_t": c,
                          "equal_weight_t": eq,
                          "uplift_optimal": c / max(a, b) - 1,
                          "uplift_equal": eq / max(a, b) - 1})
    pairs.sort(key=lambda p: -p["optimal_t"])
    out["overlay_pairs"] = pairs
    print(f"\nOVERLAY, best 3 by optimally-weighted t")
    for p in pairs[:3]:
        print(f"  {p['a']} + {p['b']:16s} rho {p['rho']:+.3f}  "
              f"best {p['best_leg_t']:+.2f} -> {p['optimal_t']:+.2f} "
              f"({p['uplift_optimal']:+.1%}); EQUAL-weight "
              f"{p['equal_weight_t']:+.2f} ({p['uplift_equal']:+.1%})")

    # ---- 3. confluence, each against its SIZE-MATCHED control -------------
    ranks = {c: M.rank_columns(scores[c], base) for c in M.CANDIDATES}

    def legs(c, n):
        o, cnt = ranks[c]
        return M.legs_from_order(o, cnt, n, base.shape)

    def spread(ev_lo, ev_hi, k):
        lr, lc = np.nonzero(ev_lo)
        hr, hc = np.nonzero(ev_hi)
        slo, clo = M.bar_sums(fwd[k], lr, lc, T)
        shi, chi = M.bar_sums(fwd[k], hr, hc, T)
        m = (clo > 0) & (chi > 0)
        if int(m.sum()) < M.MIN_BARS:
            return None, None, 0
        d = slo[m] / clo[m] - shi[m] / chi[m]
        return (float(d.mean() * 1e4),
                float(d.mean() / (d.std(ddof=1) / np.sqrt(d.size))), int(m.sum()))

    plo, phi, _ = legs(PRIMARY, N)
    b_bp, b_t, _ = spread(plo, phi, K)
    out["baseline"] = {"candidate": PRIMARY, "N": N, "k": K,
                       "spread_bp": b_bp, "t": b_t,
                       "vs_cost": b_bp / COST_BP}
    print(f"\nBASELINE {PRIMARY} N={N} k={K}: {b_bp:+.1f} bp  t {b_t:+.2f}  "
          f"({b_bp / COST_BP:.2f}x round trip)")

    rows, matched_ns = [], set()
    for c in M.CANDIDATES:
        if c == PRIMARY:
            continue
        qlo, qhi, _ = legs(c, N)
        clo_, chi_ = plo & qlo, phi & qhi
        bars_with = max(int(clo_.any(axis=0).sum()), 1)
        per = float(clo_.sum() / bars_with)
        keep = float(clo_.sum() / max(plo.sum(), 1))
        bp, t, nb = spread(clo_, chi_, K)
        if bp is None:
            continue
        nc = max(int(round(per)), 1)
        matched_ns.add(nc)
        mlo, mhi, _ = legs(PRIMARY, nc)
        m_bp, m_t, _ = spread(mlo, mhi, K)
        rows.append({"partner": c, "rho": float(R[idx[PRIMARY], idx[c]]),
                     "keep": keep, "names_per_bar": per,
                     "confluence_bp": bp, "confluence_t": t,
                     "matched_N": nc, "matched_bp": m_bp, "matched_t": m_t,
                     "beats_matched_bp": bp - (m_bp or 0.0),
                     "beats_matched_t": t - (m_t or 0.0)})
    rows.sort(key=lambda r: -r["confluence_bp"])
    out["confluence"] = rows
    out["independence_expectation_names_per_bar"] = float(
        N * N / base.sum(axis=0)[base.sum(axis=0) > 0].mean())

    wins = [r for r in rows if r["beats_matched_t"] > 0]
    print(f"\nCONFLUENCE: {len(rows)} partners; {len(wins)} beat their "
          f"SIZE-MATCHED control on t")
    for r in rows[:4]:
        print(f"  {r['partner']:16s} rho {r['rho']:+.2f} keep {r['keep']:4.0%} "
              f"{r['names_per_bar']:4.1f}/bar  conf {r['confluence_bp']:+8.1f} bp "
              f"t {r['confluence_t']:+.2f} | matched N={r['matched_N']} "
              f"{r['matched_bp']:+7.1f} t {r['matched_t']:+.2f}")

    # ---- 4. the looks this file spent, counted rather than waved at -------
    spent = {"overlay_pairs": len(pairs),
             "overlay_triples_inspected": comb(TOP, 3),
             "confluence_partners": len(rows),
             "size_matched_controls": len(matched_ns)}
    spent["total"] = sum(spent.values())
    out["looks_spent"] = spent
    print(f"\nLOOKS SPENT BY THIS FILE, to be carried by any successor (R13):")
    for k, v in spent.items():
        print(f"  {k:28s} {v:>5,}")

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
