"""D409 -- the OI density conditional read INTO the expiry, on the third disjoint set.

    uv run python scripts/run_d409_expiry_pinning.py --run

Pre-registration db8de4e predates this file (R8). Nothing is scored, nothing is admitted, and
this runner recommends no disposition -- it reports against the bar the record already stated.

PRIMARY, DECLARED IN ADVANCE (section 3): w = 2.0, h = 4, |forward move| / sigma sqrt(h).
  w = 2.0 is CARRIED FORWARD from D408, not re-chosen.
  h = 4 is Monday's close to the third Friday's close -- the horizon the mechanism names.

THE BAR IS D406'S, UNCHANGED:
  T1  monotone DECREASING across Q1->Q5
  T2  Q1 - Q5 >= 10% of the pooled mean
  T3  T1 survives within volatility terciles
  R2  SEPARATE: the w = 2.0, h = 63 spread on this set is <= -0.0569 (0.75x d406's -0.0759).
      R2 clearing does not clear D409.
  Dg1 SEPARATE: corr(dens, trailing |21d move|/sigma). More negative than -0.40 and any T1 pass
      is a restatement of trailing quiet, not evidence about open interest.

[EXPIRY] IS AN ASSERTION BECAUSE THE HORIZON IS THE CLAIM. h = 4 counts PANEL POSITIONS, not
calendar days, so a holiday inside expiry week would push t+4 past the expiry into the following
Monday -- the wrong window measured under the right name. Snapshots whose t+4 is not the third
Friday of their own month are DROPPED, not re-anchored, and the count is reported.

The construction is imported from D406 rather than restated, so all three studies are provably the
same object measured on different dates.
"""
import argparse
import calendar
import datetime
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d406", REPO / "scripts" / "run_d406_oi_density_screen.py")
D = importlib.util.module_from_spec(_s)
sys.modules["d406"] = D
_s.loader.exec_module(D)                      # installs D406's [SPLIT] guard; D409 adds no unlock

OUT = REPO / "data" / "d409_expiry_pinning.json"
SET = "expiry"
W_PRIMARY = 2.0
H_PRIMARY = 4                                 # Monday close -> third-Friday close
HZ = (4, 21, 63)
D406_W2_SPREAD = -0.0759                      # quoted from D406's committed record
R2_FACTOR = 0.75
DG1_BAR = -0.40
TRAIL = 21


def third_friday(y, m):
    """The third Friday of month (y, m) -- the standard US equity-option expiry."""
    fri = [d for d in calendar.Calendar().itermonthdates(y, m)
           if d.month == m and d.weekday() == 4]
    return fri[2]


def expiry_ok(dates, pos, snaps, h):
    """[EXPIRY] -- keep only snapshots whose t+h panel date IS that month's third Friday."""
    keep, bad = set(), []
    for d in sorted(snaps):
        t = pos.get(d)
        if t is None or t + h >= len(dates):
            bad.append((d, "off panel"))
            continue
        landed = dates[t + h]
        want = third_friday(*(int(x) for x in d.split("-")[:2])).isoformat()
        if landed == want:
            keep.add(d)
        else:
            bad.append((d, f"t+{h} -> {landed}, wanted {want}"))
    return keep, bad


def trailing_move(P, sig, lg, rows, k=TRAIL):
    """|log(P_t / P_{t-k})| / (sigma_t sqrt(k)) -- the same units as the forward outcome."""
    out = np.full(len(rows), np.nan)
    for j, r in enumerate(rows):
        t, i = r["t"], r["i"]
        if t - k < 0:
            continue
        a, b = lg[t, i], lg[t - k, i]
        if np.isfinite(a) and np.isfinite(b) and r["sigma"] > 0:
            out[j] = abs(a - b) / (r["sigma"] * np.sqrt(k))
    return out


def run():
    t0 = time.time()
    print("D409  the OI density conditional read INTO the expiry")
    print("      the bar was committed in db8de4e BEFORE this ran\n")

    snaps = D.set_dates(SET)
    for other in ("d406", "oos"):
        o = D.set_dates(other)
        ov = snaps & o
        assert not ov, f"[DISJOINT] {len(ov)} dates shared with the spent {other} set: {sorted(ov)[:5]}"
        print(f"  [DISJOINT] {len(snaps)} expiry snapshots, 0 shared with {other}'s {len(o)}")

    chains = D.summarise_chains(verbose=False)
    P = D.load_panel(verbose=False)
    sig, lg = D.sigma_and_fwd(P)

    allowed, bad = expiry_ok(P["dates"], P["pos"], snaps, H_PRIMARY)
    print(f"\n  [EXPIRY] t+{H_PRIMARY} lands on the third Friday for {len(allowed)} of {len(snaps)} "
          f"snapshots; {len(bad)} dropped")
    for d, why in bad:
        print(f"           dropped {d}: {why}")
    assert len(allowed) >= 24, f"[EXPIRY] only {len(allowed)} usable snapshots -- too few to quintile"

    cells, dg1 = {}, {}
    for w in D.WS:
        rows, align = D.build_rows(P, chains, sig, lg, w, HZ, allowed)
        if w == W_PRIMARY:
            med = float(np.median(align)) if align.size else float("nan")
            print(f"\n  [ALIGN] delta-0.5 strike / RAW close: n {align.size:,}  median {med:.4f}")
            assert align.size > 1000, "[ALIGN] too few delta-implied spots to verify the basis"
            assert abs(med - 1.0) < 0.05, f"[ALIGN] median {med:.4f} -- the bases disagree"
            print(f"  rows {len(rows):,}  names {len({r['sym'] for r in rows})}  "
                  f"snapshots {len({r['date'] for r in rows})}")
            dv = np.array([r["dens"] for r in rows])
            tv = trailing_move(P, sig, lg, rows)
            m = np.isfinite(dv) & np.isfinite(tv)
            dg1 = dict(n=int(m.sum()), corr=float(np.corrcoef(dv[m], tv[m])[0, 1]))

        c = {}
        for h in HZ:
            c[f"h{h}_abs_sigma"] = D.quintile_table(rows, h, 2)
            c[f"h{h}_signed"] = D.quintile_table(rows, h, 0)
        sg = np.array([r["sigma"] for r in rows])
        e = np.quantile(sg, [1 / 3, 2 / 3])
        for j, name in enumerate(("lo", "mid", "hi")):
            f = (lambda r, j=j: (r["sigma"] < e[0]) if j == 0 else
                 (e[0] <= r["sigma"] < e[1]) if j == 1 else (r["sigma"] >= e[1]))
            c[f"h{H_PRIMARY}_abs_sigma_vol_{name}"] = D.quintile_table(rows, H_PRIMARY, 2, strat=f)
        cells[f"w{w}"] = c
        t = c[f"h{H_PRIMARY}_abs_sigma"]
        if t:
            tag = "PRIMARY" if w == W_PRIMARY else "shape, cannot clear"
            print(f"\n  w={w}  h={H_PRIMARY}  ({tag})  |move|/sigma: "
                  + "  ".join(f"{m:.4f}" for m in t["means"]))
            print(f"        spread {t['spread']:+.4f}   monotone_dec {t['monotone_dec']}   n {t['n']}")

    prim = cells[f"w{W_PRIMARY}"][f"h{H_PRIMARY}_abs_sigma"]
    assert prim is not None, "the primary cell did not populate"
    T1 = prim["monotone_dec"]
    T2 = (prim["means"][0] - prim["means"][-1]) >= D.T2_BAR * prim["pooled"]
    terc = {k: cells[f"w{W_PRIMARY}"][f"h{H_PRIMARY}_abs_sigma_vol_{k}"] for k in ("lo", "mid", "hi")}
    T3 = all(v is not None and v["monotone_dec"] for v in terc.values())

    print("\n  --- THE BAR (committed db8de4e) ---")
    print(f"    T1 monotone DECREASING          : {T1}")
    print(f"    T2 Q1-Q5 >= 10% of pooled mean  : {T2}   "
          f"({prim['means'][0] - prim['means'][-1]:+.4f} vs {D.T2_BAR*prim['pooled']:.4f})")
    print(f"    T3 survives within vol terciles : {T3}")
    for k, v in terc.items():
        if v:
            print(f"       vol {k:3s}  " + "  ".join(f"{m:.4f}" for m in v["means"])
                  + f"   monotone_dec {v['monotone_dec']}  spread {v['spread']:+.4f}")

    h63 = cells[f"w{W_PRIMARY}"]["h63_abs_sigma"]
    r2_bar = R2_FACTOR * D406_W2_SPREAD
    R2 = bool(h63 and h63["spread"] <= r2_bar)
    print(f"\n    R2 second replication (SEPARATE, cannot clear D409)")
    if h63:
        print(f"       h=63 spread {h63['spread']:+.4f}  vs bar {r2_bar:+.4f}  "
              f"->  {'MET' if R2 else 'NOT MET'}   ratio {h63['spread']/D406_W2_SPREAD:.2f}x")
        print(f"       h=63 means  " + "  ".join(f"{m:.4f}" for m in h63["means"])
              + f"   monotone_dec {h63['monotone_dec']}")

    print(f"\n    Dg1 corr(dens, trailing |{TRAIL}d move|/sigma) = {dg1['corr']:+.4f}  n {dg1['n']:,}")
    contaminated = dg1["corr"] < DG1_BAR
    print(f"        bar {DG1_BAR:+.2f}  ->  "
          + ("CONTAMINATED -- read as trailing quiet, not open interest"
             if contaminated else "not a restatement of trailing quiet"))

    # X-c: the prediction that separates PINNING from the general conditional.
    xc = None
    if h63:
        xc = dict(h4=prim["spread"], h63=h63["spread"],
                  smaller_at_expiry=bool(abs(prim["spread"]) < abs(h63["spread"])))
        print(f"\n    X-c  |h=4 spread| {abs(prim['spread']):.4f}  vs  |h=63 spread| "
              f"{abs(h63['spread']):.4f}  ->  "
              + ("SMALLER at expiry (X-c correct: not the pinning mechanism)"
                 if xc["smaller_at_expiry"] else "LARGER at expiry (X-c WRONG)"))

    sgn = cells[f"w{W_PRIMARY}"][f"h{H_PRIMARY}_signed"]
    if sgn:
        print(f"\n    signed return (reported, CANNOT CLEAR): "
              + "  ".join(f"{m:+.4f}" for m in sgn["means"]) + f"   spread {sgn['spread']:+.4f}")

    clears = bool(T1 and T2 and T3)
    print(f"\n  VERDICT: {'CLEARS' if clears else 'FAILS'}   "
          f"R2 {'MET' if R2 else 'NOT MET'}   Dg1 {dg1['corr']:+.4f}")
    OUT.write_text(json.dumps(dict(
        snapshot_set=SET, w_primary=W_PRIMARY, h_primary=H_PRIMARY,
        expiry_check=dict(kept=sorted(allowed), dropped=bad),
        bar=dict(T1=T1, T2=T2, T3=T3, clears=clears),
        R2=dict(met=R2, bar=r2_bar, observed=(h63 or {}).get("spread"), d406=D406_W2_SPREAD),
        Dg1=dict(**dg1, bar=DG1_BAR, contaminated=contaminated),
        Xc=xc, cells=cells, horizons=list(HZ), windows=list(D.WS)),
        indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return clears


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
