"""D452 -- D440's full lifecycle, controls and BAR, run on ES itself.

    python scripts/d452_d440_on_es.py

WHAT IS AND IS NOT ALREADY DONE. D449 put ES holds through d440's lifecycle and reported V at
the best grid point. That is one number. D440 is a study: two controls that separate kurtosis
from clustering, a circular block bootstrap for an honest SE, an era split, and three gates. None
of that has ever been run on the instrument -- only on the equity proxy. This runs it, unchanged,
on the ES series now that the acquisition is complete (3,584 holds, 2010-06-07 .. 2026-09-09).

NOTHING IN d440_lifecycle.py IS EDITED. Its run_cell, block_bootstrap_V and provider machinery
are imported and called on the ES frame. The [P1] gate -- the injected Gaussian reproducing
d386_full_lifecycle bit-identically -- is re-run here too, because a study that skips its own
gates because they passed somewhere else is not running them.

THE BAR, as D440 declared it, and it is quoted unchanged:
  T1  V > 0 by 2 SE, circular block bootstrap on the hold sequence
  T2  P4: expected FUNDED life > 3 years at that same size   (R11's ruling of 2026-09-11)
  T3  V > 0 by 2 SE in 2021-2026 alone

PREDICTIONS, WRITTEN BEFORE THE RUN:
  V1  GAUSS >> MEASURED again, and SHUF sits between with CLUSTERING carrying most of the gap --
      D440 measured the fat marginal at 14-18% on four equity symbols and the mechanism is not
      instrument-specific.
  V2  T2 FAILS, and not narrowly. D451 put ES funded life at 0.15-0.32 years against a 3-year
      bar; more data does not move an order of magnitude.
  V3  T1 UNRESOLVED. D440's proxy bootstrap gave 0.69-0.99 SE; ES has ~10% more holds, which
      moves an SE by about 5%.
  V4  ES's V comes out ABOVE the proxy's at the matched grid point, continuing D451 section 3 --
      the proxy is the conservative series, not the optimistic one.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import d386_full_lifecycle as D386          # noqa: E402
import d440_lifecycle as D440               # noqa: E402

ES = REPO / "data" / "fixtures" / "es_c1_holds.csv.gz"
OUT = REPO / "data" / "d452_d440_on_es.json"
N_PATHS, DAYS = 8_000, 600
PLAN = "MFFU Rapid EOD/50"


def main() -> int:
    es = pd.read_csv(ES)
    spy = pd.read_csv(D440.HOLDS_CSV)
    spy = spy[spy["symbol"] == "SPY"].reset_index(drop=True)
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]

    print("D452 -- D440's lifecycle, controls and bar, on ES\n")
    print(f"  ES holds {len(es):,}  {es['day'].min()} .. {es['day'].max()}")
    print(f"  eras: {es['era'].value_counts().sort_index().to_dict()}\n")

    print("GATES")
    fails = D440.p1_gate()
    if fails:
        for f in fails[:6]:
            print("   ", f)
        print("\n[P1] FAILED -- stopping, per D440's own rule.")
        return 1

    r = es["d_end"].to_numpy(dtype=float)
    sk = float(((r - r.mean()) ** 3).mean() / r.std() ** 3)
    ku = float(((r - r.mean()) ** 4).mean() / r.std() ** 4)
    print(f"\n  ES series: mean {100 * r.mean():.4f}%  sd {100 * r.std(ddof=1):.3f}%"
          f"  ann Sharpe {r.mean() / r.std(ddof=1) * np.sqrt(252):.3f}"
          f"  skew {sk:.2f}  kurt {ku:.2f}")

    rows = []
    print("\nV PER EVALUATION -- MFFU Rapid EOD 50K, by provider and risk")
    print(f"  {'series':<8}{'rule':<8}{'provider':<10}"
          + "".join(f"{100 * f:>9.1f}%" for f in D386.RISK_FRACS) + f"{'best':>10}")
    best = {}
    for name, frame in (("ES", es), ("proxy", spy)):
        for rule in ("static", "voltgt"):
            for kind in ("GAUSS", "MEASURED", "SHUF"):
                if kind == "GAUSS" and rule == "voltgt":
                    continue
                row = [D440.run_cell(frame, plan, f, rule, kind, N_PATHS, DAYS)
                       for f in D386.RISK_FRACS]
                b = max(row, key=lambda x: x["V"])
                best[(name, rule, kind)] = b
                rows += [dict(x, series=name) for x in row]
                print(f"  {name:<8}{rule:<8}{kind:<10}"
                      + "".join(f"{x['V']:>10,.0f}" for x in row) + f"{b['V']:>10,.0f}")

    print("\nTHE GAP -- best risk, static (where all three providers exist)")
    for name in ("ES", "proxy"):
        g = best[(name, "static", "GAUSS")]["V"]
        m = best[(name, "static", "MEASURED")]["V"]
        s = best[(name, "static", "SHUF")]["V"]
        short = (g - m) / g if g else float("nan")
        share = (g - s) / (g - m) if (g - m) else float("nan")
        print(f"  {name:<7} GAUSS {g:>8,.0f}  SHUF {s:>8,.0f}  MEASURED {m:>8,.0f}"
              f"   shortfall {100 * short:>6.1f}%   fat-marginal share {100 * share:>5.1f}%")

    # ------------------------------------------------------------------ THE BAR, on ES
    print(f"\nTHE BAR -- ES, {PLAN}, voltgt, at the V-maximising size")
    row = [D440.run_cell(es, plan, f, "voltgt", "MEASURED", N_PATHS, DAYS)
           for f in D386.RISK_FRACS]
    b = max(row, key=lambda x: x["V"])
    f_star = b["frac"]
    print(f"  argmax {100 * f_star:.1f}%   V {b['V']:,.0f}   P(pass) {b['p_pass']:.3f}"
          f"   P(paid) {b['p_paid']:.3f}   payouts {b['n_payouts_mean']:.2f}")

    print("\n  T1 -- circular block bootstrap on the hold sequence")
    boots = {}
    for bl in (1, 20, 60):
        bs = D440.block_bootstrap_V(es, plan, f_star, "voltgt", "MEASURED", bl, 200,
                                    N_PATHS, DAYS, D440.SEED)
        boots[bl] = bs
        m = bs["V_mean"] / bs["V_se"] if bs["V_se"] else float("nan")
        print(f"    b={bl:<3} V {bs['V_mean']:>8,.0f} +- {bs['V_se']:>7,.0f}"
              f"   [{bs['V_p05']:>8,.0f}, {bs['V_p95']:>8,.0f}]   {m:>6.2f} SE"
              f"   P(V>0) {bs['p_above_zero']:.3f}")
    worst = min(boots.values(), key=lambda x: x["V_mean"] / x["V_se"] if x["V_se"] else 0.0)
    m1 = worst["V_mean"] / worst["V_se"] if worst["V_se"] else float("nan")
    t1 = "PASS" if m1 > 2.0 else ("UNRESOLVED" if m1 > 0 else "FAIL")

    print("\n  T2 -- P4: expected FUNDED life > 3 years (R11, 2026-09-11)")
    life = b["fund_days_mean"] / 252.0
    t2 = "PASS" if (life > 3.0 and b["p_alive_at_horizon"] > 0) else "FAIL"
    print(f"    funded life {life:.2f} years ({b['fund_days_mean']:.0f} days),"
          f" {b['p_alive_at_horizon']:.1%} alive at {DAYS}d -> {t2}")
    print("    every grid point: " + "  ".join(
        f"{100 * x['frac']:.1f}%={x['fund_days_mean'] / 252:.2f}yr" for x in row))

    print("\n  T3 -- V > 0 by 2 SE in 2021-2026 alone")
    e21 = es[es["era"] == "2021-2026"].reset_index(drop=True)
    r21 = [D440.run_cell(e21, plan, f, "voltgt", "MEASURED", N_PATHS, DAYS)
           for f in D386.RISK_FRACS]
    b21 = max(r21, key=lambda x: x["V"])
    bs21 = D440.block_bootstrap_V(e21, plan, b21["frac"], "voltgt", "MEASURED", 20, 200,
                                  N_PATHS, DAYS, D440.SEED)
    m3 = bs21["V_mean"] / bs21["V_se"] if bs21["V_se"] else float("nan")
    t3 = "PASS" if m3 > 2.0 else ("UNRESOLVED" if m3 > 0 else "FAIL")
    print(f"    {len(e21):,} holds   V {bs21['V_mean']:>8,.0f} +- {bs21['V_se']:>7,.0f}"
          f"   {m3:>6.2f} SE   P(V>0) {bs21['p_above_zero']:.3f} -> {t3}")

    print(f"\n  T1 {t1}   T2 {t2}   T3 {t3}"
          f"   ->  {'CANDIDATE' if t1 == t2 == t3 == 'PASS' else 'NOT A CANDIDATE'}")

    rows.append({"kind": "BAR", "series": "ES", "f_star": f_star, "V": b["V"],
                 "life_years": life, "T1": t1, "T2": t2, "T3": t3,
                 "boot": {str(k): v for k, v in boots.items()}, "boot_2021": bs21})
    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
