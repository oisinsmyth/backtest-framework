"""D408 -- D406's w = 2.0 cell, made PRIMARY, on the disjoint `oos` snapshot set.

    uv run python scripts/run_d408_w2_confirmation.py --run

Pre-registration 4fa495c predates this file (R8). Nothing is scored, nothing is admitted.

THE BAR IS D406'S, UNCHANGED, with w = 2.0 declared primary IN ADVANCE:
  T1  |forward move|/sigma monotone DECREASING across Q1->Q5
  T2  Q1 - Q5 >= 10% of the pooled mean
  T3  T1 survives within volatility terciles
  R1  a SEPARATE pre-declared replication statistic: the w = 2.0 spread on `oos` is negative
      and at least 0.75x its d406 value, i.e. <= -0.0569 against the observed -0.0759.
      R1 CLEARING DOES NOT CLEAR D408 -- it would justify a full pre-registration, nothing more.

The construction is imported from D406 rather than restated, so the two studies are provably
the same object measured on different dates.
"""
import argparse
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
_s.loader.exec_module(D)                      # installs D406's [SPLIT] guard; D408 adds no unlock

OUT = REPO / "data" / "d408_w2_confirmation.json"
SET = "oos"
W_PRIMARY = 2.0
D406_W2_SPREAD = -0.0759                      # quoted from D406's committed record
R1_FACTOR = 0.75
HZ = (63, 21)


def run():
    t0 = time.time()
    print("D408  D406's w = 2.0 cell, made PRIMARY, on the disjoint `oos` set")
    print("      the bar was committed in 4fa495c BEFORE this ran\n")
    allowed = D.set_dates(SET)
    spent = D.set_dates("d406")
    overlap = allowed & spent
    assert not overlap, f"[DISJOINT] {len(overlap)} dates shared with the spent d406 set: {sorted(overlap)[:5]}"
    print(f"  [DISJOINT] {len(allowed)} oos snapshots, 0 shared with d406's {len(spent)}")

    chains = D.summarise_chains(verbose=False)
    P = D.load_panel(verbose=False)
    sig, lg = D.sigma_and_fwd(P)

    cells, rows_by_w = {}, {}
    for w in D.WS:
        rows, align = D.build_rows(P, chains, sig, lg, w, HZ, allowed)
        rows_by_w[w] = rows
        if w == W_PRIMARY:
            med = float(np.median(align)) if align.size else float("nan")
            print(f"  [ALIGN] delta-0.5 strike / RAW close: n {align.size:,}  median {med:.4f}")
            assert align.size > 1000, "[ALIGN] too few delta-implied spots to verify the basis"
            assert abs(med - 1.0) < 0.05, f"[ALIGN] median {med:.4f} -- the bases disagree"
            print(f"  rows {len(rows):,}  names {len({r['sym'] for r in rows})}  "
                  f"snapshots {len({r['date'] for r in rows})}")
        c = {}
        for h in HZ:
            c[f"h{h}_abs_sigma"] = D.quintile_table(rows, h, 2)
            c[f"h{h}_signed"] = D.quintile_table(rows, h, 0)
        sg = np.array([r["sigma"] for r in rows])
        e = np.quantile(sg, [1 / 3, 2 / 3])
        for j, name in enumerate(("lo", "mid", "hi")):
            f = (lambda r, j=j: (r["sigma"] < e[0]) if j == 0 else
                 (e[0] <= r["sigma"] < e[1]) if j == 1 else (r["sigma"] >= e[1]))
            c[f"h63_abs_sigma_vol_{name}"] = D.quintile_table(rows, 63, 2, strat=f)
        cells[f"w{w}"] = c
        t = c["h63_abs_sigma"]
        if t:
            tag = "PRIMARY" if w == W_PRIMARY else "shape, cannot clear"
            print(f"\n  w={w}  ({tag})  |move|/sigma: " + "  ".join(f"{m:.4f}" for m in t["means"]))
            print(f"        spread {t['spread']:+.4f}   monotone_dec {t['monotone_dec']}   n {t['n']}")

    prim = cells[f"w{W_PRIMARY}"]["h63_abs_sigma"]
    assert prim is not None, "the primary cell did not populate"
    T1 = prim["monotone_dec"]
    T2 = (prim["means"][0] - prim["means"][-1]) >= D.T2_BAR * prim["pooled"]
    terc = {k: cells[f"w{W_PRIMARY}"][f"h63_abs_sigma_vol_{k}"] for k in ("lo", "mid", "hi")}
    T3 = all(v is not None and v["monotone_dec"] for v in terc.values())
    r1_bar = R1_FACTOR * D406_W2_SPREAD
    R1 = prim["spread"] <= r1_bar

    print("\n  --- THE BAR (committed 4fa495c) ---")
    print(f"    T1 monotone DECREASING          : {T1}")
    print(f"    T2 Q1-Q5 >= 10% of pooled mean  : {T2}   "
          f"({prim['means'][0] - prim['means'][-1]:+.4f} vs {D.T2_BAR*prim['pooled']:.4f})")
    print(f"    T3 survives within vol terciles : {T3}")
    for k, v in terc.items():
        if v:
            print(f"       vol {k:3s}  " + "  ".join(f"{m:.4f}" for m in v["means"])
                  + f"   monotone_dec {v['monotone_dec']}  spread {v['spread']:+.4f}")
    print(f"\n    R1 replication (SEPARATE, cannot clear D408 on its own)")
    print(f"       oos spread {prim['spread']:+.4f}   vs bar {r1_bar:+.4f} "
          f"(0.75 x d406's {D406_W2_SPREAD:+.4f})   ->  {'MET' if R1 else 'NOT MET'}")
    print(f"       replication ratio {prim['spread'] / D406_W2_SPREAD:.2f}x")
    sgn = cells[f"w{W_PRIMARY}"]["h63_signed"]
    if sgn:
        print(f"\n    signed return (reported, CANNOT CLEAR): "
              + "  ".join(f"{m:+.4f}" for m in sgn["means"]) + f"   spread {sgn['spread']:+.4f}")

    clears = bool(T1 and T2 and T3)
    print(f"\n  VERDICT: {'CLEARS' if clears else 'FAILS'}   "
          f"R1 {'MET -- justifies a full pre-registration, nothing more' if R1 else 'NOT MET'}")
    OUT.write_text(json.dumps(dict(snapshot_set=SET, w_primary=W_PRIMARY,
                                   bar=dict(T1=T1, T2=T2, T3=T3, clears=clears),
                                   R1=dict(met=R1, bar=r1_bar, observed=prim["spread"],
                                           d406=D406_W2_SPREAD,
                                           ratio=prim["spread"] / D406_W2_SPREAD),
                                   cells=cells), indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return clears


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
