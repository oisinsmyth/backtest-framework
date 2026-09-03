"""D297 -- the premise for a SPREAD-referenced stop, measured before designing one.

    uv run python scripts/d297_spread_stop_premise.py

THE FLAW IT WOULD FIX. D295's stops trail on a position's OWN cumulative return.
The book is a spread, so what a position is worth is its move RELATIVE to its
leg: a long name down 2% while its leg is down 3% has made money for the book
and a raw stop closes it anyway. The spread construction exists to remove drift
and a per-position stop puts the drift straight back into the exit decision.

THE PREMISE THAT HAS TO HOLD. That only matters if the common component is
large. If a position's cumulative move is nearly all idiosyncratic, a
spread-referenced stop fires on almost the same trades as a raw one and the idea
is not worth a study.

Decomposed per held position-bar:

    raw    = sgn * r_i                what D295's stop trails on
    beta   = sgn * r_mkt              the part the OTHER LEG cancels
    excess = sgn * (r_i - r_mkt)      what survives into the spread

THE REFERENCE IS THE MARKET, NOT THE LEG. Netting a position against its own
leg mean would remove the signal's own tilt -- the leg mean IS the edge. What
a spread cancels is the term common to BOTH legs:

    mean(long r) - mean(short r) = mean(long excess) - mean(short excess)

exactly, because r_mkt appears in both and drops out. So the spread-relevant
quantity for one position is its return net of the market, carrying its leg
sign.

and then, over the life of each position, how often the two disagree about
whether to stop.
"""

from __future__ import annotations

import importlib.util
import json
import sys
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


E = _load("d295", "run_d295_exits.py")
R, M = E.R, E.M
OUT = REPO / "data" / "d297_spread_stop_premise.json"


def main() -> int:
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    n = base.shape[0]
    ctx, r1, vol, plan = E.build_inputs(z, base, panel, live, T)
    # the market: the cross-sectional mean return of every live name that bar.
    # It is what a dollar-neutral spread cancels, so it is what a stop meant to
    # measure SPREAD damage must not react to.
    mkt = np.full(T, np.nan)
    for t in range(T):
        v = r1[:, t][live[:, t] & np.isfinite(r1[:, t])]
        if v.size > 20:
            mkt[t] = v.mean()
    mkt = np.nan_to_num(mkt)

    # walk the CONTROL book (5-bar hold) and decompose every held position-bar
    raws, comms, idios = [], [], []
    # per position: cumulative raw and cumulative idio, and whether a 1.0-vol
    # stop would have fired on each
    fired_raw = fired_idio = both = neither = 0
    npos = 0
    open_ = {"lo": {}, "hi": {}}
    for t in range(1, T):
        for side in ("lo", "hi"):
            sel, rk = ctx[side]["sel"], ctx[side]["rank"]
            held = open_[side]
            sgn = 1.0 if side == "lo" else -1.0
            for row in list(held):
                if held[row][0] >= E.BASE_HOLD and held[row][0] > 0:
                    st = held.pop(row)
                    npos += 1
                    fr = st[3] is True
                    fi = st[4] is True
                    fired_raw += fr
                    fired_idio += fi
                    both += (fr and fi)
                    neither += ((not fr) and (not fi))
            for row in list(held):
                if not np.isfinite(r1[row, t]):
                    held.pop(row)
            free = E.N_SLOTS - len(held)
            if free > 0:
                cand = np.flatnonzero(sel[:, t] & np.isfinite(r1[:, t]))
                if cand.size:
                    cand = cand[np.argsort(rk[cand, t], kind="stable")]
                    for row in cand:
                        if free == 0:
                            break
                        r = int(row)
                        if r in held:
                            continue
                        # [age, cum_raw, cum_idio, fired_raw, fired_idio]
                        held[r] = [0, 0.0, 0.0, False, False]
                        free -= 1
            if not held:
                continue
            rows = list(held)
            v = np.array([r1[row, t] for row in rows])
            fin = np.isfinite(v)
            if not fin.any():
                continue
            for row, vi, ok in zip(rows, v, fin):
                if not ok:
                    continue
                st = held[row]
                raw = sgn * vi
                comm = sgn * mkt[t]
                idio = raw - comm
                st[0] += 1
                st[1] += raw
                st[2] += idio
                u = vol[row, t]
                if np.isfinite(u) and u > 0:
                    if st[1] <= -1.0 * u:
                        st[3] = True
                    if st[2] <= -1.0 * u:
                        st[4] = True
                raws.append(raw)
                comms.append(comm)
                idios.append(idio)

    raws = np.array(raws)
    comms = np.array(comms)
    idios = np.array(idios)
    print(f"decomposed {raws.size:,} held position-bars from the 5-bar control\n")
    print(f"  {'component':12s} {'sd (bp)':>10s} {'mean (bp)':>11s} "
          f"{'share of var':>13s}")
    vr, vc, vi = raws.var(), comms.var(), idios.var()
    for nm, a, v in (("raw", raws, vr), ("beta (market)", comms, vc),
                     ("idio", idios, vi)):
        print(f"  {nm:12s} {a.std() * 1e4:10.1f} {a.mean() * 1e4:+11.2f} "
              f"{(v / vr if nm != 'raw' else 1.0):13.1%}")
    rho = float(np.corrcoef(raws, idios)[0, 1])
    print(f"\n  corr(raw, idio) = {rho:+.3f}   "
          f"-- 1.00 would mean the two stops are the same rule")
    print(f"  market share of a position-bar's variance: {vc / vr:.1%}")

    print(f"\nWOULD A 1.0-VOL STOP FIRE ON THE SAME TRADES?  "
          f"({npos:,} completed positions)")
    print(f"  raw-cum stop fires        : {fired_raw:7,d}  ({fired_raw / npos:5.1%})")
    print(f"  idio-cum stop fires       : {fired_idio:7,d}  ({fired_idio / npos:5.1%})")
    print(f"  BOTH                      : {both:7,d}  ({both / npos:5.1%})")
    print(f"  neither                   : {neither:7,d}  ({neither / npos:5.1%})")
    dis = fired_raw + fired_idio - 2 * both
    print(f"  DISAGREE                  : {dis:7,d}  ({dis / npos:5.1%})"
          f"   <- the trades the change would move")
    ov = both / max(fired_raw + fired_idio - both, 1)
    print(f"  Jaccard overlap           : {ov:.3f}"
          f"   -- 1.00 means the same rule wearing two names")

    json.dump({"purpose": "D297 premise: how much of a held position's move is "
                          "common to its leg, and would a spread-referenced "
                          "stop fire on different trades than a raw one.",
               "bars": int(raws.size), "positions": int(npos),
               "sd_raw_bp": float(raws.std() * 1e4),
               "sd_market_bp": float(comms.std() * 1e4),
               "sd_idio_bp": float(idios.std() * 1e4),
               "market_var_share": float(vc / vr),
               "corr_raw_idio": rho,
               "fired_raw": int(fired_raw), "fired_idio": int(fired_idio),
               "both": int(both), "disagree": int(dis),
               "jaccard": float(ov)}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
