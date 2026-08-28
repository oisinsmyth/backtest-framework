"""D241 — the combined book, and first-come-first-served capital.

D240 reported that pairing S1 with A2 would reach a combined Sharpe of 1.032.
THAT WAS CLOSED-FORM ARITHMETIC ON SR_a, SR_b AND rho -- not a book. This builds
the book.

    TOTAL        capital the book may deploy
    RESERVE_S1   reserved for S1, unusable by A2
    RESERVE_A2   reserved for A2, unusable by S1
    SHARED     = TOTAL - RESERVE_S1 - RESERVE_A2

Each position is 1/57 of TOTAL CAPITAL, unchanged from every book published so
far, so the arms' standalone numbers stay comparable.

AT 100% CAPITAL THE ALLOCATOR NEVER BINDS -- combined demand peaks at 94.74%.
First-come-first-served is a rationing rule and there is nothing to ration until
capital is capped. C0 is therefore the union of the two books, asserted.

FCFS ON DAILY BARS MEANS INCUMBENCY. Both arms signal at the same close, so there
is no natural "first" within a bar; the real content is that an open position
keeps its capital against a newcomer. The intra-bar tie is split pro-rata to
unmet demand rather than by an arbitrary arm priority.

RATIONING DENIES ENTRIES, IT DOES NOT SHRINK POSITIONS. D236 rationed by scaling
every position proportionally and found all six controls cut better-than-average
bars. Denial is a different mechanism and is not covered by that result.

STAGE 1 ONLY. The holdout 60 and the 2025-2026 forward window are not touched.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


U = _load("d240_onset", "run_uptrend_onset.py")
X, L, S, J = U.X, U.L, U.S, U.J

SUMMARY = REPO / "data" / "combined_book_summary.json"
RESULTS = REPO / "COMBINED_BOOK_RESULTS.md"

PPY, SEED = X.PPY, X.SEED
RF_ANNUAL = X.RF_ANNUAL

# Declared in D241: (TOTAL, RESERVE_S1, RESERVE_A2)
CELLS = {
    "C0": (1.00, 0.00, 0.00),
    "C1": (0.50, 0.00, 0.00),
    "C2": (0.50, 0.25, 0.25),
    "C3": (0.50, 0.15, 0.15),
    "C4": (0.75, 0.00, 0.00),
}
CELL_ORDER = ("C0", "C1", "C2", "C3", "C4")
ARMS = ("S1", "A2")
EPS = 1e-12


def allocate(demand: dict, start: int, total: float, reserve: dict, *, reverse=False):
    """The capital allocator. A forward walk over bars with per-position claims.

    Written fresh because nothing in the repo can express *this entry was denied
    because the pool was full* -- D236's control scales a position matrix that
    already exists, which is a different mechanism.

    `demand[arm]` is that arm's UNCONSTRAINED book: 1.0 where it wants the name.
    Returns the granted book per arm, plus what was denied.

    THE ORDER OF OPERATIONS IS THE DESIGN (D241):
      1. release  -- a position its own arm has exited frees its capital
      2. incumbents hold; they are never evicted to make room for a newcomer
      3. new demand draws on that arm's RESERVE first
      4. then on SHARED, split PRO-RATA to unmet demand when it cannot meet both
      5. denial, not scaling -- an entry either happens at full size or not at all


    AMENDMENT 1, forced by an assertion and recorded in D241. Both arms can want
    the SAME NAME on the same bar -- 1,000 cells, 3.63% of combined demand. The
    first draft summed the two granted books and double-funded them. **A name is
    held ONCE and charged ONCE.** The allocator therefore works on NAMES, with an
    owning arm tracked only for reserve accounting and reporting. A position whose
    owner exits but which the other arm still wants CONTINUES, with ownership
    transferring and no capital event -- which is the correct reading of a shared
    pool: you cannot buy the same ETF twice with the same money.
    """
    arms = list(demand)
    n, T = demand[arms[0]].shape
    unit = 1.0 / n
    shared_cap = total - sum(reserve.values())
    assert shared_cap > -EPS, "reserves exceed total capital"

    granted = {a: np.zeros((n, T)) for a in arms}
    held = np.zeros(n, dtype=bool)
    owner = np.full(n, -1, dtype=int)          # index into `arms`
    denied = {a: 0 for a in arms}
    wanted = {a: 0 for a in arms}
    binds = np.zeros(T, dtype=bool)
    order = list(range(n))[::-1] if reverse else list(range(n))

    for t in range(start, T):
        want = {a: demand[a][:, t] > 0 for a in arms}
        anyone = want[arms[0]] | want[arms[1]]

        # 1 + 2: a held name survives if EITHER arm still wants it; ownership
        # transfers if the owner left and the other stayed -- no capital event.
        held &= anyone
        owner[~held] = -1
        for i in np.where(held)[0]:
            if not want[arms[owner[i]]][i]:
                owner[i] = 1 - owner[i]

        used = {a: float((held & (owner == j)).sum()) * unit for j, a in enumerate(arms)}
        shared_used = sum(max(used[a] - reserve[a], 0.0) for a in arms)
        room_res = {a: max(reserve[a] - used[a], 0.0) for a in arms}

        # 3: candidate new names, attributed to the arm with more unused reserve
        # when both want it (neutral -- no arbitrary arm priority)
        new = {a: [] for a in arms}
        for i in order:
            if not anyone[i] or held[i]:
                continue
            claimants = [a for a in arms if want[a][i]]
            a = (claimants[0] if len(claimants) == 1
                 else max(claimants, key=lambda x: room_res[x]))
            new[a].append(i)
        for a in arms:
            wanted[a] += len(new[a])

        # 4: reserve first, then SHARED split pro-rata to unmet demand
        need = {a: len(new[a]) * unit for a in arms}
        from_res = {a: min(need[a], room_res[a]) for a in arms}
        rest = {a: need[a] - from_res[a] for a in arms}
        free_shared = max(shared_cap - shared_used, 0.0)
        want_shared = sum(rest.values())
        if want_shared > free_shared + EPS:
            binds[t] = True
            from_shared = {a: free_shared * (rest[a] / want_shared) if want_shared > 0 else 0.0
                           for a in arms}
        else:
            from_shared = dict(rest)

        # AMENDMENT 2, also forced by an assertion. RESERVE is a FUNDING constraint
        # on an arm; TOTAL is a HARD constraint on the book, and it needs enforcing
        # separately. Ownership can transfer without a capital event (amendment 1),
        # so an arm can come to hold more than its reserve -- after which the
        # per-arm room checks alone no longer bound the sum. Cap globally.
        budget = {a: from_res[a] + from_shared[a] for a in arms}
        global_room = max(total - float(held.sum()) * unit, 0.0)
        if sum(budget.values()) > global_room + EPS:
            binds[t] = True
            tot_b = sum(budget.values())
            budget = {a: global_room * (budget[a] / tot_b) if tot_b > 0 else 0.0 for a in arms}

        # 5: denial, not scaling -- a whole number of entries, or none
        for j, a in enumerate(arms):
            k = min(int(math.floor(budget[a] / unit + 1e-9)), len(new[a]))
            for i in new[a][:k]:
                held[i] = True
                owner[i] = j
            denied[a] += len(new[a]) - k
        for j, a in enumerate(arms):
            granted[a][held & (owner == j), t] = 1.0

    return granted, {"denied": denied, "wanted": wanted,
                     "binds_fraction": float(binds[start:].mean())}


def build() -> dict:
    t0 = time.time()
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    md, hs, ok = S.base_masks(panel, cleaned, start)
    s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    up, g_lo, i_lo, atr = U.signals(panel, cleaned, start)
    a2, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start, stop_mode="fixed")
    demand = {"S1": s1, "A2": a2}

    ones = np.ones_like(s1)
    ones[:, :start] = 0.0
    solo = {a: X.score(panel, demand[a], start) for a in ARMS}
    bh = X.score(panel, ones, start)
    assert abs(solo["S1"]["excess_sharpe"] - 0.746) < 5e-4, "S1 moved"
    assert abs(solo["A2"]["excess_sharpe"] - 0.822) < 5e-4, "A2 moved"

    def excess(pos):
        tot = X.signed_log_returns(panel, pos, total_return=True)[start:]
        return X.excess_of(tot, pos, start)

    r_solo = {a: excess(demand[a]) for a in ARMS}

    cells, books, alloc, rev_diag = {}, {}, {}, {}
    for k in CELL_ORDER:
        total, r1, r2 = CELLS[k]
        g, info = allocate(demand, start, total, {"S1": r1, "A2": r2})
        book = g["S1"] + g["A2"]
        assert book.max() <= 1.0 + EPS, f"{k}: a name was double-funded"
        dep = book[:, start:].mean(axis=0)
        assert dep.max() <= total + 1e-9, f"{k}: capital over-committed"
        books[k] = book
        cells[k] = X.score(panel, book, start)
        alloc[k] = {
            **info,
            "exposure_S1": float(g["S1"][:, start:].mean()),
            "exposure_A2": float(g["A2"][:, start:].mean()),
            "denied_rate_S1": info["denied"]["S1"] / max(info["wanted"]["S1"], 1),
            "denied_rate_A2": info["denied"]["A2"] / max(info["wanted"]["A2"], 1),
            "max_deployed": float(dep.max()),
        }
        gr, _ = allocate(demand, start, total, {"S1": r1, "A2": r2}, reverse=True)
        rev_diag[k] = X.score(panel, gr["S1"] + gr["A2"], start)["excess_sharpe"]

    # C0 must be the plain union -- the allocator is inert at TOTAL = 100%
    union = np.maximum(s1, a2)
    assert np.array_equal(books["C0"], union), "C0 is not the union; the allocator rationed"

    # M1 / M2 -- the paired bootstrap that D240 could not do
    boot = {}
    for k in CELL_ORDER:
        rc = excess(books[k])
        boot[k] = {}
        for a in ARMS:
            b = J.paired_block_bootstrap(rc, r_solo[a])
            boot[k][a] = {"delta": cells[k]["excess_sharpe"] - solo[a]["excess_sharpe"],
                          "p05": b["p05"], "p95": b["p95"],
                          "excludes_zero": bool(b["p05"] > 0.0)}
    m1 = {"delta_vs_S1": boot["C0"]["S1"]["delta"], "p05": boot["C0"]["S1"]["p05"],
          "clears_M1": bool(boot["C0"]["S1"]["delta"] > 0 and boot["C0"]["S1"]["p05"] > 0)}
    m2 = {"delta_vs_A2": boot["C0"]["A2"]["delta"], "p05": boot["C0"]["A2"]["p05"],
          "clears_M2": bool(boot["C0"]["A2"]["delta"] > 0 and boot["C0"]["A2"]["p05"] > 0)}
    m3 = {"c1_minus_c2": cells["C1"]["excess_sharpe"] - cells["C2"]["excess_sharpe"],
          "clears_M3": bool(cells["C1"]["excess_sharpe"] > cells["C2"]["excess_sharpe"])}
    m4 = {k: bool(cells[k]["excess_sharpe"] > cells["C0"]["excess_sharpe"])
          for k in ("C1", "C2", "C3", "C4")}

    # the closed form D240 reported, for comparison against the book that was built
    rho = float(np.corrcoef(r_solo["S1"], r_solo["A2"])[0, 1])
    sa, sb = solo["S1"]["excess_sharpe"], solo["A2"]["excess_sharpe"]
    predicted = math.sqrt(max(sa ** 2 + sb ** 2 - 2 * rho * sa * sb, 0.0) / (1 - rho ** 2))

    return {
        "produced": "D241",
        "stage": "screen (mined 57) -- the holdout and forward window are untouched",
        "seed": SEED, "rf_annual": RF_ANNUAL,
        "n_symbols": len(panel.symbols), "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start], "last_date": panel.dates[-1],
        "cells": cells, "solo": solo, "buy_and_hold": bh,
        "cell_params": {k: {"total": CELLS[k][0], "reserve_S1": CELLS[k][1],
                            "reserve_A2": CELLS[k][2],
                            "shared": CELLS[k][0] - CELLS[k][1] - CELLS[k][2]}
                        for k in CELL_ORDER},
        "allocation": alloc, "bootstrap": boot,
        "m1": m1, "m2": m2, "m3": m3, "m4": m4,
        "rho": rho, "closed_form_prediction": predicted,
        "reverse_order_sharpe": rev_diag,
        "deployable_return": {
            k: float(np.expm1(np.log1p(cells[k]["cagr"])
                              + math.log1p(RF_ANNUAL) * (1 - cells[k]["exposure_gross"])))
            for k in CELL_ORDER
        } | {a: float(np.expm1(np.log1p(solo[a]["cagr"])
                               + math.log1p(RF_ANNUAL) * (1 - solo[a]["exposure_gross"])))
             for a in ARMS},
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    c, so, dep, al, bt = (p["cells"], p["solo"], p["deployable_return"],
                          p["allocation"], p["bootstrap"])
    cp, b = p["cell_params"], p["buy_and_hold"]
    o = ["# D241 — the combined book, and first-come-first-served capital\n"]
    o.append(f"**STAGE 1 — A SCREEN, NOT A VERDICT.** {p['stage']}\n")
    o.append(
        f"*seed {p['seed']}, {p['elapsed_seconds']}s. {p['n_symbols']} ETFs x "
        f"{p['live_bars']:,} live bars, {p['first_live_date'][:10]} .. {p['last_date'][:10]}. "
        f"Positions are 1/{p['n_symbols']} of total capital.*\n"
    )
    o.append("## The books\n")
    o.append("| | total | reserve S1/A2 | shared | exposure | excess Sharpe | CAGR | "
             "**deployable** | vol | max DD | Calmar |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        x, q = c[k], cp[k]
        cal = x["cagr"] / abs(x["max_drawdown"]) if x["max_drawdown"] else float("nan")
        o.append(
            f"| **{k}** | {q['total']:.0%} | {q['reserve_S1']:.0%} / {q['reserve_A2']:.0%} | "
            f"{q['shared']:.0%} | {x['exposure_gross']:.1%} | "
            f"**{x['excess_sharpe']:+.3f}** | {x['cagr'] * 100:.2f}% | "
            f"**{dep[k] * 100:.2f}%** | {x['vol'] * 100:.1f}% | "
            f"{x['max_drawdown'] * 100:+.2f}% | {cal:.3f} |"
        )
    for a in ARMS:
        x = so[a]
        cal = x["cagr"] / abs(x["max_drawdown"])
        o.append(
            f"| *{a} alone* | — | — | — | *{x['exposure_gross']:.1%}* | "
            f"*{x['excess_sharpe']:+.3f}* | *{x['cagr'] * 100:.2f}%* | *{dep[a] * 100:.2f}%* | "
            f"*{x['vol'] * 100:.1f}%* | *{x['max_drawdown'] * 100:+.2f}%* | *{cal:.3f}* |"
        )
    o.append(
        f"| *B&H* | — | — | — | *100.0%* | *{b['excess_sharpe']:+.3f}* | "
        f"*{b['cagr'] * 100:.2f}%* | *{b['cagr'] * 100:.2f}%* | *{b['vol'] * 100:.1f}%* | "
        f"*{b['max_drawdown'] * 100:+.2f}%* | *{b['cagr'] / abs(b['max_drawdown']):.3f}* |"
    )
    o.append("")
    o.append(
        f"**The closed form D240 reported predicted {p['closed_form_prediction']:.3f}** at "
        f"ρ = {p['rho']:+.4f}. C0, the book actually built, scores "
        f"**{c['C0']['excess_sharpe']:+.3f}**.\n"
    )

    m1, m2 = p["m1"], p["m2"]
    o.append("## M1 and M2 — the paired bootstrap D240 could not do\n")
    o.append("| | delta | p05 | p95 | excludes 0 | verdict |")
    o.append("|---|---:|---:|---:|:--:|:--:|")
    for a, lbl, mm in (("S1", "M1 — C0 vs S1 alone", m1), ("A2", "M2 — C0 vs A2 alone", m2)):
        q = bt["C0"][a]
        o.append(f"| **{lbl}** | **{q['delta']:+.3f}** | {q['p05']:+.3f} | {q['p95']:+.3f} | "
                 f"{'✓' if q['excludes_zero'] else '✗'} | "
                 f"{'✓ CLEARS' if mm.get('clears_M1', mm.get('clears_M2')) else '✗ FAILS'} |")
    o.append("")

    m3 = p["m3"]
    o.append("## M3 — does first-come-first-served beat a fixed split?\n")
    o.append(
        f"*C1 and C2 hold the same 50% of capital. The only difference is whether it is "
        f"**shared** or **partitioned 25/25**.*\n\n"
        f"| | excess Sharpe |\n|---|---:|\n"
        f"| C1 — shared, FCFS | {c['C1']['excess_sharpe']:+.3f} |\n"
        f"| C2 — fixed 25/25 | {c['C2']['excess_sharpe']:+.3f} |\n"
        f"| **difference** | **{m3['c1_minus_c2']:+.3f}** |\n"
        f"| **M3** | **{'✓ CLEARS' if m3['clears_M3'] else '✗ FAILS'}** |\n"
    )

    o.append("## How the allocator behaved\n")
    o.append("| | binds on | exposure S1 | exposure A2 | entries denied S1 | denied A2 | "
             "max deployed | reversed-order Sharpe |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        a = al[k]
        o.append(
            f"| **{k}** | {a['binds_fraction']:.2%} | {a['exposure_S1']:.1%} | "
            f"{a['exposure_A2']:.1%} | {a['denied_rate_S1']:.1%} | {a['denied_rate_A2']:.1%} | "
            f"{a['max_deployed']:.1%} | {p['reverse_order_sharpe'][k]:+.3f} |"
        )
    o.append("")
    o.append("*The reversed-order column is the arbitrariness diagnostic: entries are admitted "
             "in ascending symbol index, and this is what happens under the opposite order.*\n")

    o.append("## M4 — does any capped cell beat the unconstrained book?\n")
    o.append("| | excess Sharpe | vs C0 | beats C0 |")
    o.append("|---|---:|---:|:--:|")
    for k in ("C1", "C2", "C3", "C4"):
        d = c[k]["excess_sharpe"] - c["C0"]["excess_sharpe"]
        o.append(f"| **{k}** | {c[k]['excess_sharpe']:+.3f} | {d:+.3f} | "
                 f"{'✓' if p['m4'][k] else '✗'} |")
    o.append("")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if args.report_only:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    else:
        payload = build()
        SUMMARY.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    RESULTS.write_text(render(payload), encoding="utf-8")

    c, so, al = payload["cells"], payload["solo"], payload["allocation"]
    print()
    print(f"{'cell':5s} {'total':>6s} {'expo':>7s} {'exSh':>8s} {'CAGR':>8s} {'maxDD':>8s} "
          f"{'binds':>7s} {'denS1':>7s} {'denA2':>7s} {'rev':>7s}")
    for k in CELL_ORDER:
        x, a = c[k], al[k]
        print(f"{k:5s} {payload['cell_params'][k]['total']:6.0%} {x['exposure_gross']:7.1%} "
              f"{x['excess_sharpe']:+8.3f} {x['cagr']:8.2%} {x['max_drawdown']:+8.2%} "
              f"{a['binds_fraction']:7.2%} {a['denied_rate_S1']:7.1%} {a['denied_rate_A2']:7.1%} "
              f"{payload['reverse_order_sharpe'][k]:+7.3f}")
    for a in ARMS:
        print(f"{a:5s} {'-':>6s} {so[a]['exposure_gross']:7.1%} {so[a]['excess_sharpe']:+8.3f} "
              f"{so[a]['cagr']:8.2%} {so[a]['max_drawdown']:+8.2%}")
    m1, m2, m3 = payload["m1"], payload["m2"], payload["m3"]
    print(f"\nclosed form predicted {payload['closed_form_prediction']:.3f} at rho "
          f"{payload['rho']:+.4f};  C0 built = {c['C0']['excess_sharpe']:+.3f}")
    print(f"M1  C0 - S1 = {m1['delta_vs_S1']:+.3f}  p05 {m1['p05']:+.3f}  "
          f"{'CLEARS' if m1['clears_M1'] else 'FAILS'}")
    print(f"M2  C0 - A2 = {m2['delta_vs_A2']:+.3f}  p05 {m2['p05']:+.3f}  "
          f"{'CLEARS' if m2['clears_M2'] else 'FAILS'}")
    print(f"M3  C1 - C2 = {m3['c1_minus_c2']:+.3f}  "
          f"{'CLEARS' if m3['clears_M3'] else 'FAILS'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
