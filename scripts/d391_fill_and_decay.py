"""D391 addendum -- WHERE does the +43 come from? The bar-by-bar decomposition, and the fill.

    uv run python scripts/d391_fill_and_decay.py

D392's addendum asked why D391's long (+43.02) and its short mirror (+43.73) both sit far above
their atlas floors (+6.38 and +3.54). It offered a hypothesis and THE HYPOTHESIS AS WRITTEN WAS
WRONG, which this file corrects before testing anything:

    D392 6a said "the next open after such a bar may gap systematically in the direction of that
    close, which would credit BOTH books mechanically."

    **D391 ENTERS AT THE NEXT OPEN.** The close(t) -> open(t+1) gap is therefore EXCLUDED by
    construction -- that is the whole point of D340's convention, which replaced a same-close fill
    that FINDINGS 21 found "credited the overnight gap to every entry, and it was worth more than
    the spread". The gap cannot be crediting these books; it is the one thing already removed.

SO THE QUESTION IS RESTATED AS THE ONE THE DATA CAN ANSWER:

  1. WHERE IN THE HOLD does the +43 accrue? The same event set is scored at cap 1, 2, 3, 5, 10, 20
     and the increments read off. Concentrated in the first bar or two => a continuation artifact
     of high-range bars, which a uniform atlas draw cannot see. Spread evenly => drift, and the
     pool comparison is the right frame after all.
  2. HOW BIG IS THE GAP D340 EXCLUDES on these particular bars? Re-scored under a same-close fill
     (entry bar earns close-to-close instead of open-to-close). This does NOT propose reverting the
     convention -- D340 settled that -- it measures what these events' gaps are worth, because an
     event defined by a large intrabar range is exactly where that number should be unusual.

DESCRIPTIVE. Scores no new construction, admits nothing (R15). Both arms are D391's own masks,
rebuilt by importing its runner rather than re-deriving them.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


OUT = REPO / "data" / "d391_fill_and_decay.json"
CAPS = (1, 2, 3, 5, 10, 20)
PRIMARY = 20

D391 = _load("d391", "run_d391_undercut_reclaim.py")
from backtest_framework.research import structure as MS      # noqa: E402

PREP = _load("d348p", "d348_prep.py")
V59 = _load("d359r", "run_d359_loser_rally_short.py")
ST = _load("ragged_structure_scores", "ragged_structure_scores.py")


def main() -> int:
    t0 = time.time()
    P = PREP.prep(need_grids=True)
    M = PREP.M
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    live = panel.live
    PV = D391.build_pivots(type("V", (), {"M": M})(), MS, panel, cleaned, live)
    n, T = live.shape
    atr = np.full((n, T), np.nan)
    for i in range(n):
        at = np.flatnonzero(live[i])
        if at.size >= 2:
            atr[i, at] = ST._atr_price(g["open"][i, at], g["high"][i, at],
                                       g["low"][i, at], g["close"][i, at])
    elig = np.asarray(P["elig"])
    EV, POOL, UNDER, MIRROR = D391.event_masks(PV, g, atr, elig)
    sc = np.full((T, n), 50.0)
    print(f"  rebuilt D391's masks in {time.time() - t0:.0f}s | event {int(EV.sum()):,} "
          f"mirror {int(MIRROR.sum()):,}", flush=True)

    # [ID] the primary cell must reproduce D391's published ledger before anything is read
    r0 = V59.run_mirror(P, EV, sc, "cap", PRIMARY)
    m0 = float(PREP.V47.pnl_bp(r0).mean())
    assert abs(m0 - 43.02) < 0.01 and abs(len(r0["trades"]) - 61835) < 2, \
        f"[ID] {m0:+.2f} on {len(r0['trades']):,} != D391's published +43.02 on 61,835"
    print(f"    [ID] reproduces D391's +43.02 on {len(r0['trades']):,} trades", flush=True)

    # ---- 1. WHERE IN THE HOLD -------------------------------------------
    decay = {}
    for side, mask in (("long", EV), ("short", MIRROR)):
        run = V59.run_mirror if side == "long" else V59.run_short
        prev, rows = 0.0, []
        for cap in CAPS:
            res = run(P, mask, sc, "cap", cap)
            mu = float(PREP.V47.pnl_bp(res).mean())
            rows.append(dict(cap=cap, mean_bp=mu, trades=int(len(res["trades"])),
                             increment_bp=mu - prev))
            prev = mu
        decay[side] = rows

    print(f"\n  1. WHERE IN THE HOLD does it accrue? cumulative mean per trade by cap\n")
    print(f"  {'cap':>4s} {'long cum':>10s} {'long +':>9s} {'short cum':>10s} {'short +':>9s}")
    for a_, b_ in zip(decay["long"], decay["short"]):
        print(f"  {a_['cap']:>4d} {a_['mean_bp']:>+10.2f} {a_['increment_bp']:>+9.2f} "
              f"{b_['mean_bp']:>+10.2f} {b_['increment_bp']:>+9.2f}")
    l1 = decay["long"][0]["mean_bp"] / decay["long"][-1]["mean_bp"]
    s1 = decay["short"][0]["mean_bp"] / decay["short"][-1]["mean_bp"]
    print(f"\n     bar 1 alone is {100 * l1:.0f}% of the long's 20-bar total and "
          f"{100 * s1:.0f}% of the short's")

    # ---- 2. the gap D340 excludes, on THESE bars -------------------------
    A3c = dict(P["A3"], ocT=np.asarray(P["r1T"]), mkt_oc=np.asarray(P["m_f"]))
    fill = {}
    for side, mask in (("long", EV), ("short", MIRROR)):
        run = V59.run_mirror if side == "long" else V59.run_short
        openf = float(PREP.V47.pnl_bp(run(P, mask, sc, "cap", PRIMARY)).mean())
        closef = float(PREP.V47.pnl_bp(run(P, mask, sc, "cap", PRIMARY, A3=A3c)).mean())
        fill[side] = dict(next_open=openf, same_close=closef, gap_bp=closef - openf)
    print(f"\n  2. THE GAP D340 EXCLUDES, on these events (cap {PRIMARY})\n")
    print(f"  {'side':<6s} {'next-open (D391)':>18s} {'same-close':>12s} {'the gap':>10s}")
    for side, d in fill.items():
        print(f"  {side:<6s} {d['next_open']:>+18.2f} {d['same_close']:>+12.2f} "
              f"{d['gap_bp']:>+10.2f}")

    # ---- 3. B_r AT THE HORIZON THE EFFECT ACTUALLY LIVES AT ---------------
    #      D391's H3 compared reclaim against no-reclaim on the forward-20 drift. If the whole
    #      effect is bar 1, that test was run at the wrong horizon and diluted 20:1. The same
    #      comparison at h = 1 is the number that decides whether H3's failure was real.
    pool_h = {}
    for h in (1, 2, 5, 20):
        Fh = D391.forward_h(P, h, start=1)
        row = {}
        for nm, m in (("reclaim", EV), ("no_reclaim", POOL)):
            v = Fh[m]
            v = v[np.isfinite(v)]
            row[nm] = dict(n=int(v.size), bp=float(v.mean()) * 1e4)
        row["diff_bp"] = row["reclaim"]["bp"] - row["no_reclaim"]["bp"]
        pool_h[h] = row
    print(f"\n  3. B_r AT EACH HORIZON -- D391's H3 was measured at h=20 only\n")
    print(f"  {'h':>3s} {'reclaim':>10s} {'no-reclaim':>12s} {'difference':>12s}")
    for h, r in pool_h.items():
        print(f"  {h:>3d} {r['reclaim']['bp']:>+10.2f} {r['no_reclaim']['bp']:>+12.2f} "
              f"{r['diff_bp']:>+12.2f}")

    payload = dict(study=391, addendum="fill and decay", caps=list(CAPS), decay=decay, fill=fill,
                   pool_by_horizon={str(k): v for k, v in pool_h.items()},
                   note="D392 6a's hypothesis as written was wrong: D391 enters at the NEXT OPEN, "
                        "so the close->open gap is excluded by construction. Restated as (1) where "
                        "in the hold the return accrues and (2) how large the excluded gap is on "
                        "these particular bars.")
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
