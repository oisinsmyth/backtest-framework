"""D436 stage 0 -- shock-with-state: counts, overlaps, blocking, occupancy, cadence. Reads NO forward return.
Spec docs/decisions/D436-shock-with-state-stage-0.md (committed BEFORE this file, R8).

    uv run python scripts/run_d436_stage0.py --run
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
A34 = _load("d434", "run_d434_atlas_volume.py"); A35 = _load("d435", "run_d435_atlas_conditional.py")
OUT = REPO / "data" / "d436_stage0.json"
HOLD = 20
COMP = {"A": ("mom_hi", "long"), "B": ("price_hi", "short"), "C": ("price_lo", "long"), "D": ("mom_lo", "short")}
D435_CELLS = {"A": 13731, "B": 12597, "C": 16182, "D": 13560}          # D435 pool sizes, the [N] targets


def blocking(events, T, N):
    """One position per name, 20-bar hold: which events are refused because the name is held; daily occupancy after."""
    held_until = np.full(N, -1); accepted = np.zeros_like(events); occ = np.zeros(T, int)
    days = np.flatnonzero(events.any(axis=1))
    for t in days:
        for j in np.flatnonzero(events[t]):
            if t < held_until[j]:
                continue
            accepted[t, j] = True; held_until[j] = t + HOLD
    # occupancy: positions open on day d = accepted events in (d-HOLD, d]
    a = accepted.sum(axis=1).astype(float); cs = np.cumsum(a)
    for d in range(T):
        occ[d] = int(cs[d] - (cs[d - HOLD] if d - HOLD >= 0 else 0.0))
    return accepted, occ


def run():
    t0 = time.time()
    print("D436 STAGE 0 -- shock-with-state; dates, states and volumes only; no forward return is read\n")
    PREP = _load("d348p", "d348_prep.py"); P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"])
    dates = np.array([str(x)[:10] for x in P["dates"]]); yr = np.array([int(d[:4]) for d in dates]); SYM = P["symbols"]
    st = A35.state_pools_unshifted(P, elig); vp, F = A34.volume_pools_unshifted(P, elig)
    ev = {k: A35.shift(st[s] & vp["rv_x3"], elig) for k, (s, side) in COMP.items()}
    for k, (s, side) in COMP.items():
        un = st[s] & vp["rv_x3"]; assert not ev[k][0].any() and np.array_equal(ev[k][1:], un[:-1] & elig[1:]), f"[F] {k}"
        assert int(ev[k].sum()) == D435_CELLS[k], f"[N] {k}: {int(ev[k].sum())} != D435's {D435_CELLS[k]}"
    assert not (ev["A"] & ev["D"]).any() and not (ev["B"] & ev["C"]).any(), "[X] A&D or B&C non-empty"
    E = A35.shift(st["ret20_lo"], elig) & (ev["A"] | ev["C"])
    print("  [F] every event mask is the t-1 pool placed at t;  [N] counts equal D435's cells;  [X] A&D and B&C empty\n")
    res = dict(counts={}, by_year={}, overlap={}, blocking={}, occupancy={}, cadence={}, E={}, side={}, gate={})
    allev = ev["A"] | ev["B"] | ev["C"] | ev["D"]
    print("1. COUNTS")
    for k in COMP:
        n = int(ev[k].sum()); res["counts"][k] = dict(n=n, per_day=n / T, names=int(ev[k].any(axis=0).sum()))
        print(f"  {k} {COMP[k][0]:9s} {COMP[k][1]:5s}  {n:6,} events  {n/T:5.2f}/day  {res['counts'][k]['names']:5,} names")
    res["counts"]["all"] = dict(n=int(allev.sum()), per_day=float(allev.sum() / T), names=int(allev.any(axis=0).sum()))
    print(f"  all (union)            {int(allev.sum()):6,} events  {allev.sum()/T:5.2f}/day  {res['counts']['all']['names']:5,} names")
    print("  by year (A / B / C / D): " + "  ".join(f"{y}:{int(ev['A'][yr==y].sum())}/{int(ev['B'][yr==y].sum())}/{int(ev['C'][yr==y].sum())}/{int(ev['D'][yr==y].sum())}" for y in range(2010, 2027)))
    res["by_year"] = {str(y): {k: int(ev[k][yr == y].sum()) for k in COMP} for y in range(2010, 2027)}
    print("\n2. OVERLAPS")
    ac, bd = int((ev["A"] & ev["C"]).sum()), int((ev["B"] & ev["D"]).sum()); tot = sum(int(ev[k].sum()) for k in COMP)
    res["overlap"] = dict(AC=ac, AC_share_of_A=ac / ev["A"].sum(), BD=bd, BD_share_of_B=bd / ev["B"].sum(), share=(ac + bd) / tot)
    print(f"  A&C {ac:,} ({100*ac/ev['A'].sum():.1f}% of A)   B&D {bd:,} ({100*bd/ev['B'].sum():.1f}% of B)   overlap share of all component-events {100*(ac+bd)/tot:.1f}%")
    print("\n3. BLOCKING and 4. OCCUPANCY (one position per name, 20-bar hold, all four components together)")
    acc, occ = blocking(allev, T, N)
    for k in COMP:
        blocked = int((ev[k] & ~acc).sum()); res["blocking"][k] = blocked / ev[k].sum()
        print(f"  {k}: {blocked:,} of {int(ev[k].sum()):,} events refused ({100*blocked/ev[k].sum():.1f}%)")
    live = occ[np.flatnonzero(elig.any(axis=1))]
    res["occupancy"] = dict(mean=float(live.mean()), p50=float(np.median(live)), p90=float(np.quantile(live, .9)), max=int(live.max()), accepted=int(acc.sum()))
    print(f"  accepted {int(acc.sum()):,} of {int(allev.sum()):,};  occupancy mean {live.mean():.0f}  p50 {np.median(live):.0f}  p90 {np.quantile(live,.9):.0f}  max {live.max()}")
    print("\n5. CADENCE -- spacing between consecutive 3x-volume bars on the same name (all rv_x3, any state)")
    x3 = A35.shift(vp["rv_x3"], elig); sp = []
    for j in range(N):
        d = np.flatnonzero(x3[:, j])
        if d.size > 1: sp.append(np.diff(d))
    sp = np.concatenate(sp); s120 = sp[sp <= 120]
    q = float(((s120 >= 58) & (s120 <= 68)).mean()); res["cadence"] = dict(spacings=int(sp.size), le120=int(s120.size), quarter_share=q, uniform=11 / 120, p50=float(np.median(sp)))
    print(f"  {sp.size:,} spacings; of those <= 120 sessions ({s120.size:,}), {100*q:.1f}% fall in 58-68 (uniform would be {100*11/120:.1f}%); median spacing {np.median(sp):.0f} sessions")
    hist = np.bincount(np.clip(s120, 0, 120), minlength=121); top = np.argsort(hist)[::-1][:6]
    print("  most common spacings: " + "  ".join(f"{int(k)}d:{int(hist[k])}" for k in sorted(top)))
    print("\n6. E's COVERAGE and 7. SIDE BALANCE")
    res["E"] = dict(share_of_AC=float(E.sum() / (ev["A"] | ev["C"]).sum())); print(f"  E (ret20_lo) covers {100*res['E']['share_of_AC']:.1f}% of AUC events")
    L = ev["A"] | ev["C"]; S = ev["B"] | ev["D"]
    res["side"] = {str(y): dict(long=int(L[yr == y].sum()), short=int(S[yr == y].sum())) for y in range(2010, 2027)}
    print("  long/short by year: " + "  ".join(f"{y}:{int(L[yr==y].sum())}/{int(S[yr==y].sum())}" for y in range(2010, 2027)))
    ratio = L.sum() / S.sum(); print(f"  overall long:short = {ratio:.2f}")
    a_rate = res["counts"]["A"]["per_day"]; ov = res["overlap"]["share"]; occm = res["occupancy"]["mean"]
    cont = bool(a_rate >= 1.0 and ov <= 0.20 and occm >= 50); aband = bool(a_rate < 0.5 or ov > 0.40)
    res["gate"] = dict(continue_=cont, abandon=aband, a_rate=a_rate, overlap=ov, occupancy=occm)
    print(f"\n8. CONTINUE / ABANDON: A rate {a_rate:.2f}/day (>= 1.0)  overlap {100*ov:.1f}% (<= 20%)  occupancy {occm:.0f} (>= 50)   ->  {'CONTINUE to stage 1' if cont else ('ABANDON' if aband else 'NEITHER -- see the record')}")
    print("\n9. PREDICTIONS")
    print(f"    X-a A~13,500 B~12,400 C~15,900 D~13,300; 12-14/day; 1,400+ names : {res['counts']['A']['n']:,} {res['counts']['B']['n']:,} {res['counts']['C']['n']:,} {res['counts']['D']['n']:,}; {res['counts']['all']['per_day']:.1f}/day; {res['counts']['all']['names']:,} names")
    print(f"    X-b A&C 8-15% of A, B&D 8-15% of B, share 10-18%             : {100*res['overlap']['AC_share_of_A']:.1f}%, {100*res['overlap']['BD_share_of_B']:.1f}%, {100*ov:.1f}%")
    print(f"    X-c 35-50% of events refused by one-per-name                : " + "  ".join(f"{k} {100*res['blocking'][k]:.0f}%" for k in COMP))
    print(f"    X-d occupancy 120-200 at the median                         : p50 {res['occupancy']['p50']:.0f}  mean {occm:.0f}  p90 {res['occupancy']['p90']:.0f}")
    print(f"    X-e quarterly-cadence share 25-40% vs 9% uniform             : {100*q:.1f}%")
    print(f"    X-f E covers 25-35% of AUC                                    : {100*res['E']['share_of_AC']:.1f}%")
    print(f"    X-g long:short 0.8-1.4                                        : {ratio:.2f}")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {time.time()-t0:.0f}s   (no forward return was read)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.run:
        run()
