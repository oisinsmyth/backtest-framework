"""D409 EXTRAS -- EXPLORATORY, RUN AFTER THE PRIMARY, AND BOTH ARMS CAN ONLY HURT THE RESULT.

    uv run python scripts/run_d409_extras.py --run

NOT part of the committed bar. The primary verdict is run_d409_expiry_pinning.py's and is not
touched here. These two arms exist because the primary produced a result whose obvious rival
explanations the pre-registration did not test, and both were run knowing they could only weaken
what was found -- which is why running them after the fact is not a rescue.

ARM 1 -- THE QUIETNESS RIVAL. Dg1 measured corr(dens, trailing quietness) = -0.28. Realised
volatility is autocorrelated and its autocorrelation DECAYS, so "currently quiet against its own
63-day sigma" predicts a 4-day |move| far better than a 63-day one. That alone would produce
h=4 >> h=63 with nothing whatever to do with open interest. So: sort on trailing quietness
DIRECTLY, and sort on dens WITHIN terciles of it.

ARM 2 -- THE MATCHED NULL THE LINE HAS NEVER HAD. D406 and D408 both reported a spread against no
null at all. Permuting dens INSIDE each snapshot holds the cross-section, the calendar, every
name's sigma and every forward move fixed, and destroys only the density ordering. p5 AND p50 are
reported, with the p5's sampling SE, per CLAUDE.md and D373's rule.

  LIMITATION, stated because it is not small: a within-snapshot permutation is a null for "dens
  carries no CROSS-SECTIONAL information". It breaks the pairing between a name's dens and that
  name's own forward move, so it does NOT control for dens proxying a persistent name-level
  characteristic. Arm 1 addresses one such characteristic; it does not address all of them.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d409", REPO / "scripts" / "run_d409_expiry_pinning.py")
M = importlib.util.module_from_spec(_s)
sys.modules["d409"] = M
_s.loader.exec_module(M)
D = M.D

OUT = REPO / "data" / "d409_extras.json"
W = 2.0
HZ = (4, 21, 63)
NDRAW = 200
SEED = 12345


def fmt(t):
    return "  ".join(f"{m:.4f}" for m in t["means"])


def run():
    t0 = time.time()
    print("D409 EXTRAS -- exploratory, after the fact, both arms can only hurt the result\n")
    snaps = D.set_dates("expiry")
    chains = D.summarise_chains(verbose=False)
    P = D.load_panel(verbose=False)
    sig, lg = D.sigma_and_fwd(P)
    allowed, _ = M.expiry_ok(P["dates"], P["pos"], snaps, M.H_PRIMARY)
    rows, _ = D.build_rows(P, chains, sig, lg, W, HZ, allowed)

    q = M.trailing_move(P, sig, lg, rows)
    for r, x in zip(rows, q):
        r["quiet"] = float(x)
    rows = [r for r in rows if np.isfinite(r["quiet"])]
    print(f"  rows {len(rows):,}\n")

    res = {"arm1": {}, "arm2": {}}

    # ---------------- ARM 1: the quietness rival ----------------
    for h in HZ:
        t = D.quintile_table(rows, h, 2)
        res["arm1"][f"dens_h{h}"] = t
        print(f"  dens        h={h:2d}   {fmt(t)}   spread {t['spread']:+.4f}")
    for r in rows:
        r["_d"], r["dens"] = r["dens"], r["quiet"]
    for h in HZ:
        t = D.quintile_table(rows, h, 2)
        res["arm1"][f"quiet_h{h}"] = t
        print(f"  quietness   h={h:2d}   {fmt(t)}   spread {t['spread']:+.4f}   (Q1 = quietest)")
    for r in rows:
        r["dens"] = r["_d"]

    e = np.quantile([r["quiet"] for r in rows], [1 / 3, 2 / 3])
    print()
    for j, name in enumerate(("lo", "mid", "hi")):
        f = (lambda r, j=j: (r["quiet"] < e[0]) if j == 0 else
             (e[0] <= r["quiet"] < e[1]) if j == 1 else (r["quiet"] >= e[1]))
        t = D.quintile_table(rows, M.H_PRIMARY, 2, strat=f)
        res["arm1"][f"dens_in_quiet_{name}"] = t
        print(f"  dens | quiet {name:3s} h= 4   {fmt(t)}   spread {t['spread']:+.4f}  n {sum(t['n'])}"
              if t else f"  dens | quiet {name:3s} h= 4   too thin")

    # ---------------- ARM 2: the within-snapshot permutation null ----------------
    obs = {h: D.quintile_table(rows, h, 2)["spread"] for h in HZ}
    by = {}
    for r in rows:
        by.setdefault(r["date"], []).append(r)
    keep = {id(r): r["dens"] for r in rows}
    rng = np.random.default_rng(SEED)
    draws = {h: [] for h in HZ}
    for _ in range(NDRAW):
        for d, rs in by.items():
            v = rng.permutation([keep[id(r)] for r in rs])
            for r, x in zip(rs, v):
                r["dens"] = float(x)
        for h in HZ:
            draws[h].append(D.quintile_table(rows, h, 2)["spread"])
    for r in rows:
        r["dens"] = keep[id(r)]

    print(f"\n  within-snapshot permutation of dens, {NDRAW} draws\n")
    print("     h    observed        p5       p50       p95   beats p5?")
    for h in HZ:
        a = np.array(draws[h])
        p5, p50, p95 = (float(np.quantile(a, x)) for x in (.05, .5, .95))
        se = float(np.std(a, ddof=1) / np.sqrt(NDRAW))
        res["arm2"][f"h{h}"] = dict(observed=obs[h], p5=p5, p50=p50, p95=p95, se_of_p5=se,
                                    beats_p5=bool(obs[h] < p5),
                                    margin_se=float((p5 - obs[h]) / se))
        print(f"    {h:2d}    {obs[h]:+.4f}   {p5:+.4f}   {p50:+.4f}   {p95:+.4f}   "
              f"{'YES' if obs[h] < p5 else 'NO '}   margin {(p5-obs[h])/se:+.1f} SE")

    OUT.write_text(json.dumps(dict(exploratory=True, w=W, ndraw=NDRAW, seed=SEED, **res),
                              indent=1, default=float), encoding="utf-8")
    print(f"\n  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()
