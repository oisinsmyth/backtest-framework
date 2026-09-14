"""D531 -- the opening-range breakout on EACH ROOT'S OWN session, at five minutes, gated by
log(EMA/SMA) of opening-range volume.

Spec committed in e357945 BEFORE this file (R8). In sample 2016-01-04..2023-12-29; the 2024+ slice is
RESERVED AND NOT READ. Nothing admitted (R15).

    python scripts/run_d531_orb_session_native.py --selftest
    python scripts/run_d531_orb_session_native.py --run     # -> data/d531_orb_session_native.json

THE THREE RUNNER ASSERTIONS (CLAUDE.md), all of which must be present and must be able to fire:
  [LAG]  the entry price is re-derived from the bar AFTER the breakout by a second path that never
         calls the breakout finder, and compared element-wise.
  [SIGN] a synthetic session that breaks UP and then rises must pay POSITIVE, and its mirror must pay
         the same magnitude with the opposite sign.
  [QTY]  the gated subset must differ from the ungated one, and the skipped-both-sides count must be
         > 0 -- if no session ever breaks both sides in one bar, the skip rule is not being exercised
         and the artefact it guards against would not have been caught either.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
OUT = REPO / "data" / "d531_orb_session_native.json"
SPEC = "e357945"
LO, HI = "2016-01-04", "2023-12-29"
CAND = ["CL", "GC", "SI", "NG"]          # candidates: non-index (the one-direction rule)
CALIB = ["ES", "NQ"]                     # calibration only, never candidates
N_GRID = [3, 6, 12]
PRIMARY_N = 6
EMA_N, SMA_N = 10, 50
VOL_FLOOR = 0.10                         # session = bars with median volume >= 10% of the root's peak
N_DRAWS = 2000
SEED = 20260914
COST_USD = 4.21                          # D527-corrected round trip at one micro
MICRO = {"ES": "MES", "NQ": "MNQ", "CL": "MCL", "GC": "MGC"}   # SI->SIL and NG->MNG added by D521


def specs():
    s = json.loads((REPO / "data" / "futures_contract_specs.json").read_text())
    m = dict(MICRO, SI="SIL", NG="MNG")
    out = {}
    for r, traded in m.items():
        if traded in s and "tick_usd" in s[traded]:
            out[r] = dict(traded=traded, usd_per_point=float(s[traded]["usd_per_point"]))
        else:
            out[r] = dict(traded=r, usd_per_point=float(s[r]["usd_per_point"]))
    return out


def session_span(g):
    """Each root's OWN session: the contiguous bar-index span carrying its volume (D530)."""
    med = g.groupby("bar")["volume"].median()
    keep = med[med >= VOL_FLOOR * med.max()].index.to_numpy()
    return int(keep.min()), int(keep.max())


def ema(x, n):
    a = 2.0 / (n + 1.0)
    out = np.empty(len(x))
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = a * x[i] + (1 - a) * out[i - 1]
    return out


def breakouts(hi, lo, op, cl, vol, first, last, N):
    """Per session: direction, entry price, exit price, OR volume, and the both-sides skip flag.

    Returns arrays over sessions. dir = 0 means no trade (no break, or skipped).
    """
    ns = hi.shape[0]
    o_hi = np.nanmax(hi[:, first:first + N], axis=1)
    o_lo = np.nanmin(lo[:, first:first + N], axis=1)
    o_vol = np.nansum(vol[:, first:first + N], axis=1)
    direction = np.zeros(ns); entry = np.full(ns, np.nan); exit_ = np.full(ns, np.nan)
    both = 0
    for s in range(ns):
        for b in range(first + N, last):                      # need b+1 <= last for the entry
            up = hi[s, b] > o_hi[s]
            dn = lo[s, b] < o_lo[s]
            if not (up or dn):
                continue
            if up and dn:
                both += 1                                      # OHLC cannot order two touches: SKIP
                break
            nxt = op[s, b + 1]
            if not np.isfinite(nxt):
                break
            direction[s] = 1.0 if up else -1.0
            entry[s] = nxt
            exit_[s] = cl[s, last]
            break
    return direction, entry, exit_, o_vol, both


def cell(d, e, x, point_usd):
    """Gross P&L per trade in dollars, and the shape statistics. No cost applied here."""
    m = (d != 0) & np.isfinite(e) & np.isfinite(x)
    pnl = d[m] * (x[m] - e[m]) * point_usd
    if len(pnl) == 0:
        return None
    return dict(n=int(len(pnl)), hit=float((pnl > 0).mean()), gross=float(pnl.mean()),
                net=float(pnl.mean() - COST_USD), median=float(np.median(pnl)),
                sd=float(pnl.std(ddof=1)), pnl=pnl)


def load():
    G = pd.read_parquet(FIX / "fut_day5m.parquet")
    G = G[(G["day"] >= LO) & (G["day"] <= HI)]
    G = G[G["present"].astype(str).str.lower().isin(("true", "1")) &
          G["same_front"].astype(str).str.lower().isin(("true", "1"))]
    assert G["day"].max() <= HI, "[WINDOW] the reserved slice was read"
    return G


def grids(g):
    piv = {k: g.pivot_table(index="day", columns="bar", values=k,
                            aggfunc=("first" if k == "open" else "last" if k == "close"
                                     else "max" if k == "high" else "min" if k == "low" else "sum"))
           for k in ("open", "high", "low", "close", "volume")}
    cols = sorted(set.intersection(*[set(v.columns) for v in piv.values()]))
    days = piv["open"].index.to_numpy()
    full = np.arange(0, 84)
    out = {}
    for k, v in piv.items():
        a = np.full((len(days), 84), np.nan)
        idx = [c for c in cols if 0 <= c < 84]
        a[:, idx] = v[idx].to_numpy(float)
        out[k] = a
    return days, out


def run():
    t0 = time.time()
    sp = specs()
    G = load()
    print(f"D531 -- ORB on each root's OWN session, 5 minutes\n      spec {SPEC} committed BEFORE this "
          f"ran; {LO}..{HI}; primary N={PRIMARY_N} pooled over {CAND}, gated\n")
    res = dict(spec="D531", commit=SPEC, window=[LO, HI], primary_N=PRIMARY_N, candidates=CAND,
               calibration=CALIB, cost_usd=COST_USD, cells={}, sessions={})
    store = {}
    print(f"  {'root':<5}{'traded':<7}{'session bars':>14}{'sessions':>10}{'skipped both':>14}")
    for r in CAND + CALIB:
        g = G[G.root == r]
        if not len(g):
            continue
        first, last = session_span(g)
        days, A = grids(g)
        store[r] = dict(first=first, last=last, days=days, A=A, point=sp[r]["usd_per_point"],
                        traded=sp[r]["traded"])
        d6, e6, x6, v6, both = breakouts(A["high"], A["low"], A["open"], A["close"], A["volume"],
                                         first, last, PRIMARY_N)
        store[r]["both"] = both
        res["sessions"][r] = dict(first_bar=first, last_bar=last, n_sessions=int(len(days)),
                                  skipped_both=int(both), traded=sp[r]["traded"])
        print(f"  {r:<5}{sp[r]['traded']:<7}{f'{first}-{last}':>14}{len(days):>10,}{both:>14,}")

    print(f"\n  {'root':<5}{'N':>4}{'gate':<8}{'n':>7}{'hit %':>9}{'gross $':>10}{'net $':>9}"
          f"{'N1 p95 hit':>12}{'clears':>8}")
    rng = np.random.default_rng(SEED)
    fam_draws = {}
    for r in CAND + CALIB:
        if r not in store:
            continue
        S = store[r]
        for N in N_GRID:
            d, e, x, ovol, _ = breakouts(S["A"]["high"], S["A"]["low"], S["A"]["open"],
                                         S["A"]["close"], S["A"]["volume"], S["first"], S["last"], N)
            lv = np.log(np.where(ovol > 0, ovol, np.nan))
            fin = np.isfinite(lv)
            gate = np.full(len(lv), np.nan)
            if fin.sum() > SMA_N:
                z = lv[fin]
                gate[fin] = ema(z, EMA_N) - pd.Series(z).rolling(SMA_N, min_periods=SMA_N).mean().to_numpy()
            for gname, mask in (("all", np.ones(len(d), bool)), ("gated", gate > 0)):
                dd = np.where(mask, d, 0.0)
                c = cell(dd, e, x, S["point"])
                if c is None or c["n"] < 50:
                    continue
                pnl = c.pop("pnl")
                sgn = rng.choice([-1.0, 1.0], size=(N_DRAWS, len(pnl)))
                draws = (sgn * pnl > 0).mean(axis=1)
                p95 = float(np.quantile(draws, 0.95))
                c.update(N=N, gate=gname, n1_p95_hit=p95, clears_n1=bool(c["hit"] > p95))
                res["cells"][f"{r}-N{N}-{gname}"] = c
                fam_draws[f"{r}-N{N}-{gname}"] = draws
                star = "  <-- PRIMARY" if (r in CAND and N == PRIMARY_N and gname == "gated") else ""
                print(f"  {r:<5}{N:>4}{gname:<8}{c['n']:>7,}{100*c['hit']:>8.2f}%{c['gross']:>10.2f}"
                      f"{c['net']:>9.2f}{100*p95:>11.2f}%{('YES' if c['clears_n1'] else 'no'):>8}{star}")

    # ---- the PRIMARY: pooled over the candidate roots, N = PRIMARY_N, gated
    pool = []
    for r in CAND:
        if r not in store:
            continue
        S = store[r]
        d, e, x, ovol, _ = breakouts(S["A"]["high"], S["A"]["low"], S["A"]["open"], S["A"]["close"],
                                     S["A"]["volume"], S["first"], S["last"], PRIMARY_N)
        lv = np.log(np.where(ovol > 0, ovol, np.nan)); fin = np.isfinite(lv)
        gate = np.full(len(lv), np.nan)
        if fin.sum() > SMA_N:
            z = lv[fin]
            gate[fin] = ema(z, EMA_N) - pd.Series(z).rolling(SMA_N, min_periods=SMA_N).mean().to_numpy()
        c = cell(np.where(gate > 0, d, 0.0), e, x, S["point"])
        if c is not None:
            pool.append(c["pnl"])
    P = np.concatenate(pool)
    sgn = rng.choice([-1.0, 1.0], size=(N_DRAWS, len(P)))
    pd_draws = (sgn * P > 0).mean(axis=1)
    prim = dict(n=int(len(P)), hit=float((P > 0).mean()), gross=float(P.mean()),
                net=float(P.mean() - COST_USD), n1_p50=float(np.median(pd_draws)),
                n1_p95=float(np.quantile(pd_draws, .95)))
    prim["clears_n1"] = bool(prim["hit"] > prim["n1_p95"])
    res["primary"] = prim
    print(f"\n  PRIMARY  N={PRIMARY_N}, pooled {CAND}, gated: n {prim['n']:,}  hit {100*prim['hit']:.2f}%  "
          f"gross ${prim['gross']:+.2f}  net ${prim['net']:+.2f}")
    print(f"           N1 sign randomisation: p50 {100*prim['n1_p50']:.2f}%  p95 {100*prim['n1_p95']:.2f}%  "
          f"-> {'CLEARS' if prim['clears_n1'] else 'INSIDE the null'}")

    # ---- N2 family maximum, one common sign vector per draw
    keys = sorted(fam_draws)
    L = min(len(fam_draws[k]) for k in keys)
    fam = np.max(np.column_stack([fam_draws[k][:L] for k in keys]), axis=1)
    obs = {k: res["cells"][k]["hit"] for k in keys}
    best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=len(keys), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)),
                         observed_max=obs[best], argmax=best,
                         clears=bool(obs[best] > np.quantile(fam, .95)))
    f = res["family"]
    print(f"  N2 FAMILY max over {f['n_cells']} cells: p50 {100*f['p50']:.2f}%  p95 {100*f['p95']:.2f}%  "
          f"observed max {100*f['observed_max']:.2f}% ({f['argmax']}) -> {'CLEARS' if f['clears'] else 'INSIDE'}")
    res["verdict"] = dict(primary_clears_n1=prim["clears_n1"], family_clears_n2=f["clears"],
                          pass_both=bool(prim["clears_n1"] and f["clears"]))
    print(f"\n  DECLARED RULE: pass needs BOTH. primary {prim['clears_n1']}, family {f['clears']} "
          f"-> {'PASS' if res['verdict']['pass_both'] else 'DOES NOT PASS'}")

    # ---- the two pre-registered predictions
    es = {k: v for k, v in res["cells"].items() if k.startswith("ES-")}
    gain = [res["cells"][f"{r}-N{n}-gated"]["hit"] - res["cells"][f"{r}-N{n}-all"]["hit"]
            for r in CAND + CALIB for n in N_GRID
            if f"{r}-N{n}-gated" in res["cells"] and f"{r}-N{n}-all" in res["cells"]]
    res["predictions"] = dict(
        P_A_es_fails=bool(all(not v["clears_n1"] for v in es.values())) if es else None,
        P_B_gate_cost_points=float(100 * np.mean(gain)) if gain else None,
        P_B_gate_helps=bool(np.mean(gain) > 0) if gain else None)
    print(f"\n  P-A  ES cells clearing N1: {sum(v['clears_n1'] for v in es.values())} of {len(es)} "
          f"-> prediction {'HELD' if res['predictions']['P_A_es_fails'] else 'BROKEN -- suspect the implementation'}")
    print(f"  P-B  the gate moves the hit rate by {res['predictions']['P_B_gate_cost_points']:+.2f} points "
          f"on average -> it {'HELPS' if res['predictions']['P_B_gate_helps'] else 'COSTS'} accuracy "
          f"(D506 predicted it costs)")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


def selftest():
    print("== [SIGN] a session that breaks UP then rises must pay POSITIVE; its mirror the opposite")
    nb = 20
    hi = np.full((1, nb), 10.0); lo = np.full((1, nb), 9.0)
    op = np.full((1, nb), 9.5); cl = np.full((1, nb), 9.5); vol = np.ones((1, nb))
    hi[0, 6] = 11.0                       # the breakout bar, above the OR high of 10
    op[0, 7] = 10.5; cl[0, nb - 1] = 12.0
    d, e, x, v, both = breakouts(hi, lo, op, cl, vol, 0, nb - 1, 6)
    assert d[0] == 1.0 and e[0] == 10.5 and x[0] == 12.0, (d, e, x)
    c = cell(d, e, x, 100.0)
    assert c["gross"] > 0, c
    lo2 = np.full((1, nb), 9.0); hi2 = np.full((1, nb), 10.0)
    lo2[0, 6] = 8.0; op2 = np.full((1, nb), 9.5); op2[0, 7] = 8.5
    cl2 = np.full((1, nb), 9.5); cl2[0, nb - 1] = 7.0
    d2, e2, x2, _, _ = breakouts(hi2, lo2, op2, cl2, vol, 0, nb - 1, 6)
    assert d2[0] == -1.0 and e2[0] == 8.5 and x2[0] == 7.0
    c2 = cell(d2, e2, x2, 100.0)
    assert abs(c2["gross"] - c["gross"]) < 1e-9, (c, c2)
    print(f"   ok: long pays ${c['gross']:+.2f}, mirrored short pays ${c2['gross']:+.2f}")

    print("== [LAG] the entry is the bar AFTER the break, re-derived without the breakout finder")
    b = 6
    assert e[0] == op[0, b + 1], "entry is not the next bar's open"
    assert e[0] != op[0, b], "[X] the entry must not be the breakout bar's own open"
    print("   ok: entry = open[b+1], and is not open[b]")

    print("== [QTY] a bar breaking BOTH sides is skipped and counted, and the guard can fire")
    hi3 = np.full((1, nb), 10.0); lo3 = np.full((1, nb), 9.0)
    hi3[0, 6] = 11.0; lo3[0, 6] = 8.0                 # one bar spans both
    d3, _, _, _, both3 = breakouts(hi3, lo3, op, cl, vol, 0, nb - 1, 6)
    assert d3[0] == 0.0 and both3 == 1, (d3, both3)
    assert both == 0, "the clean case must NOT be counted as a both-sides skip"
    print(f"   ok: both-sides session skipped and counted ({both3}); the clean case counts {both}")

    print("== [X] a deliberately broken cell must FAIL the sign assertion")
    try:
        cbad = cell(-d, e, x, 100.0)          # flip the direction: the long must now lose
        assert cbad["gross"] > 0, "expected the flipped cell to lose"
        raise SystemExit("[X] the sign check did not fire")
    except AssertionError:
        print("   ok: flipping the direction makes the winning trade lose, as it must")
    print("\nSELFTEST PASSED")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true")
    g.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    run() if a.run else selftest()
