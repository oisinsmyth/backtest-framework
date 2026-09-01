"""D272 -- the volume profile as a positional input.
Pre-registered in `docs/decisions/D272-the-volume-profile-as-a-positional-input.md`,
commit 3d23e63, BEFORE this file was written.

    uv run python scripts/run_volume_profile.py

STAGE (a) independence, then STAGE (b) calibration for whatever clears A1.

WHY A PROFILE IS A DIFFERENT QUANTITY. D270 found relative volume orthogonal to
price but mostly a VOLATILITY selector -- it widens the forward distribution from
58.8 to 77.2 bp sd and shifts its mean +2.15 bp. A profile is POSITIONAL: not how
much is trading, but what the current price is standing on.

DISCLOSED, NOT INHERITED. The sensor comes from the terrain programme (D189,
D194), which closed the DIRECTIONAL claim on crypto across 259 looks. That is a
different hypothesis on a different asset class, so D272 opens a new ledger and
carries the terrain evidence in its PREDICTIONS instead -- X-c declares that any
dist_hvn relationship will favour continuation, not reversal, because inventory
accumulates below price exactly when price has been falling into it.

EVERY CONSTANT IS FROM THE SENSOR'S OWN SANCTIONED SET. It raises on anything
else, calling a third value "an unregistered search", and nothing here relaxes
that.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research.terrain import VolumeProfileSensor  # noqa: E402


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


V = _load("d270", "run_volume_structure.py")
C, I, R, M, D = V.C, V.I, V.R, V.M, V.D

OUT = REPO / "data" / "d272_volume_profile_summary.json"

LOOKBACK_BARS = 180        # ~7 sessions at 26/session. In the sensor's sanctioned set.
BUCKET_ATR = 0.5           # sanctioned set: 0.25 / 0.5
ATR_WINDOW = 182           # calendar-matched to the lookback, as D194 matched to D189
VOLUME_UNITS = "shares"    # the fixture's column IS share count (D187's defect otherwise)
REBUILD_EVERY = 26         # once per session; a 7-session map needs no intra-session rebuild
HVN_Q, LVN_Q = 0.7, 0.3    # terrain_nulls.HVN_QUANTILE = 0.7; LVN is its mirror

PROFILE_SCORES = ("dist_hvn", "dist_lvn", "mass_here", "mass_imbalance")
A1_BAR = 0.50
A2_BAR = 0.50


def build_profile_scores(panel, cleaned, vol, start):
    """The four positional scores.

    R9: the profile at bar t is built with `index = t - 1`, and `density()` slices
    everything after `index` away before any arithmetic touches it -- so the
    no-look-ahead property belongs to the sensor's code path, not to my calling
    convention. The price read is also `t - 1`."""
    sensor = VolumeProfileSensor(LOOKBACK_BARS, BUCKET_ATR, VOLUME_UNITS,
                                 atr_window=ATR_WINDOW)
    n, T = panel.closes.shape
    out = {k: np.full((n, T), np.nan) for k in PROFILE_SCORES}
    warm = max(start, sensor.warm_up_bars() + 1)
    for i, sym in enumerate(panel.symbols):
        bars = cleaned[sym]
        vols = list(vol[i])
        dens = None
        for t in range(warm, T):
            if dens is None or (t - warm) % REBUILD_EVERY == 0:
                try:
                    dens = sensor.density(bars, t - 1, vols)
                except (ValueError, IndexError):
                    dens = None
            if dens is None:
                continue
            px = float(panel.closes[i, t - 1])
            bw = dens.bucket_width
            if bw <= 0:
                continue
            hvn = dens.levels(HVN_Q, "hvn")
            lvn = dens.levels(LVN_Q, "lvn")
            if hvn:
                near = min(hvn, key=lambda x: abs(px - x))
                out["dist_hvn"][i, t] = (px - near) / bw
            if lvn:
                near = min(lvn, key=lambda x: abs(px - x))
                out["dist_lvn"][i, t] = (px - near) / bw
            occ = [m for m in dens.mass if m > 0.0]
            here = dens.mass_at(px)
            if here is not None and occ:
                out["mass_here"][i, t] = float(sum(1 for m in occ if m <= here) / len(occ))
            b = dens.bucket_of(px)
            if b is not None:
                lo = float(sum(dens.mass[:b]))
                hi = float(sum(dens.mass[b + 1:]))
                tot = lo + hi + float(dens.mass[b])
                if tot > 0:
                    out["mass_imbalance"][i, t] = (hi - lo) / tot
    return out


def main() -> int:
    rp, rc = R.load_full()
    panel, cleaned = R.subset(rp, rc, R.STRATA["ALL"])
    first, _ = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    vol, px_, stamps = V.load_volume(panel)
    bod = V.bar_of_day(stamps)

    price_sc = C.build_scores(panel, cleaned)
    vol_sc = V.build_volume_scores(panel, vol, px_, bod, panel.total_log_returns)
    print("building volume profiles (rebuild once per session) ...", flush=True)
    prof_sc = build_profile_scores(panel, cleaned, vol, start)
    for k in PROFILE_SCORES:
        fin = np.isfinite(prof_sc[k][:, start:]).sum()
        print(f"  {k:16s} {fin:,} finite values")

    REAL_VOL = ("rel_vol", "vol_z", "dollar_vol", "vol_trend")
    base = list(C.SCORES) + list(REAL_VOL)
    n_sym = len(panel.symbols)
    rng = np.random.default_rng(0)
    blend = np.full(panel.closes.shape, np.nan)
    noise = np.full(panel.closes.shape, np.nan)
    for i in range(n_sym):
        rv = I.rankify(vol_sc["rel_vol"][i, start:])
        tr = I.rankify(price_sc["trailing_return"][i, start:])
        blend[i, start:] = 0.5 * rv + 0.5 * tr
        noise[i, start:] = rng.random(rv.shape[0])

    allsc = {**price_sc, **vol_sc, **prof_sc,
             "ctrl_blend": blend, "ctrl_noise": noise}

    def eff(names):
        cols = []
        for nme in names:
            per = [I.rankify(allsc[nme][i, start:]) for i in range(n_sym)]
            cols.append(np.concatenate(per))
        X = np.vstack(cols)
        X = X[:, np.all(np.isfinite(X), axis=0)]
        Rm = np.corrcoef(X)
        lam = np.maximum(np.linalg.eigvalsh(Rm), 0.0)
        return float(lam.sum() ** 2 / (lam ** 2).sum()), Rm, X.shape[1]

    eff_base, _, _ = eff(base)
    names = base + list(PROFILE_SCORES) + ["ctrl_blend", "ctrl_noise"]
    eff_all, Rm, nbars = eff(names)

    print(f"\nSTAGE (a) -- INDEPENDENCE.  {nbars:,} bars with all {len(names)} scores finite\n")
    print(f"  {'score':16s} {'max|rho| vs the 13':>19s}   worst pair            A1")
    per = {}
    a1_pass = []
    for k, nme in enumerate(list(PROFILE_SCORES) + ["ctrl_blend", "ctrl_noise"]):
        r = len(base) + k
        rhos = {base[j]: float(Rm[r, j]) for j in range(len(base))}
        worst = max(rhos, key=lambda x: abs(rhos[x]))
        mx = abs(rhos[worst])
        ok = mx < A1_BAR
        if ok and nme in PROFILE_SCORES:
            a1_pass.append(nme)
        per[nme] = {"rho_vs_base": rhos, "max_abs_rho": mx, "worst": worst, "A1": ok}
        print(f"  {nme:16s} {mx:19.3f}   {worst:16s} ({rhos[worst]:+.2f})  "
              f"{'PASS' if ok else 'fail'}")

    print(f"\n  effective independent: {eff_base:.2f} (13 scores) -> {eff_all:.2f} "
          f"({len(names)} incl. controls)")
    a2 = (eff_all - eff_base) >= A2_BAR
    print(f"  A1  at least one profile score max|rho| < {A1_BAR}: "
          f"{'PASS -> ' + ', '.join(a1_pass) if a1_pass else 'FAIL'}")
    print(f"  A2  effective rises by >= {A2_BAR}: "
          f"{'PASS' if a2 else 'FAIL'} ({eff_all - eff_base:+.2f})")

    cb, cn = per["ctrl_blend"], per["ctrl_noise"]
    print(f"\n  CONTROLS -- both must behave, or the run is void:")
    print(f"    ctrl_blend  MUST FAIL: max|rho| {cb['max_abs_rho']:.2f}  -> "
          + ("correctly FAILS" if not cb["A1"] else "*** PASSED. VOID ***"))
    print(f"    ctrl_noise  MUST PASS: max|rho| {cn['max_abs_rho']:.2f}  -> "
          + ("correctly PASSES" if cn["A1"] else "*** FAILED. VOID ***"))
    void = bool(cb["A1"] or not cn["A1"])

    payload = {"preregistration": "docs/decisions/D272-the-volume-profile-as-a-positional-input.md",
               "commit": "3d23e63", "effective_base": eff_base, "effective_all": eff_all,
               "A1_passers": a1_pass, "A2": a2, "per_score": per,
               "control_void": void, "stage_b": {}}

    if void:
        print("\nVOID: a control misbehaved. No stage (b) reading is taken.")
    elif not a1_pass:
        print("\nSTAGE (b) SKIPPED: nothing cleared A1.")
    else:
        print(f"\nSTAGE (b) -- CALIBRATION of {a1_pass}, H = {C.H} bars\n")
        floors = {}
        for st in ("ALL", "LOW", "HIGH"):
            p, cl = ((panel, cleaned) if st == "ALL"
                     else R.subset(rp, rc, R.STRATA[st]))
            keep = [panel.symbols.index(s) for s in p.symbols]
            fwd = C.forward(p, first, start)
            c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
            print(f"  {st}   cost bar 2c = {c2:.2f} bp")
            for nme in a1_pass:
                qs = C.quintile_means(prof_sc[nme][keep], fwd, start)
                if any(q.size == 0 for q in qs):
                    print(f"    {nme:16s} insufficient data")
                    continue
                mns = np.array([q.mean() for q in qs]) * 1e4
                dd = np.diff(mns)
                mono = bool(np.all(dd > 0) or np.all(dd < 0))
                extreme = mns[-1] if abs(mns[-1]) >= abs(mns[0]) else mns[0]
                payload["stage_b"][f"{st}:{nme}"] = {
                    "quintile_means_bp": mns.tolist(),
                    "spread_bp": float(mns[-1] - mns[0]), "extreme_bp": float(extreme),
                    "cost_bar_bp": c2, "M1_monotone": mono,
                    "M2_clears_bar": bool(abs(extreme) >= c2)}
                print(f"    {nme:16s} " + " ".join(f"{m:7.2f}b" for m in mns)
                      + f"  spread {mns[-1] - mns[0]:7.2f}b  M1 {'YES' if mono else 'no':>3s}"
                        f"  M2 {'YES' if abs(extreme) >= c2 else 'no':>3s}")
            print()

        # M3 for EVERY eligible cell, regardless of M1/M2. D270's runner
        # short-circuited here and that is the R6 defect D230 named.
        print("  computing the M3 shuffle floor (every cell, no short-circuit) ...",
              flush=True)
        N = 300
        rng2 = np.random.default_rng(0)
        cache = {}
        for st in ("ALL", "LOW", "HIGH"):
            p, cl = ((panel, cleaned) if st == "ALL"
                     else R.subset(rp, rc, R.STRATA[st]))
            keep = [panel.symbols.index(s) for s in p.symbols]
            cache[st] = ({k: prof_sc[k][keep] for k in a1_pass},
                         C.forward(p, first, start), len(p.symbols))
        best = np.empty(N)
        for s in range(N):
            seed = int(rng2.integers(0, 2 ** 31 - 1))
            vals = []
            for st, (sc, fwd, ns) in cache.items():
                r2 = np.random.default_rng(seed)
                span = next(iter(sc.values())).shape[1] - start
                perm = [r2.permutation(span) for _ in range(ns)]
                for k in a1_pass:
                    sh = sc[k].copy()
                    for i in range(ns):
                        sh[i, start - 1:-1] = sh[i, start - 1:-1][perm[i]]
                    qs = C.quintile_means(sh, fwd, start)
                    if any(q.size == 0 for q in qs):
                        continue
                    m = np.array([q.mean() for q in qs]) * 1e4
                    vals.append(abs(float(m[-1] - m[0])))
            best[s] = max(vals) if vals else 0.0
            if (s + 1) % 100 == 0:
                print(f"    {s + 1}/{N}", flush=True)
        floor = float(np.percentile(best, 95))
        payload["M3_floor_bp"] = floor
        print(f"\n  M3 floor (p95 of best-of-N |spread|): {floor:.2f} bp\n")
        print(f"  {'cell':24s} {'spread':>8s} {'M1':>4s} {'M2':>4s} {'M3':>4s}  ALL THREE")
        surv = []
        for k, v in payload["stage_b"].items():
            v["M3_beats_floor"] = abs(v["spread_bp"]) > floor
            v["clears_all"] = v["M1_monotone"] and v["M2_clears_bar"] and v["M3_beats_floor"]
            if v["clears_all"]:
                surv.append(k)
            print(f"  {k:24s} {v['spread_bp']:7.2f}b "
                  f"{'YES' if v['M1_monotone'] else 'no':>4s} "
                  f"{'YES' if v['M2_clears_bar'] else 'no':>4s} "
                  f"{'YES' if v['M3_beats_floor'] else 'no':>4s}  "
                  f"{'** YES **' if v['clears_all'] else 'no'}")
        payload["survivors"] = surv
        print(f"\n  SURVIVORS: {surv or 'NONE'}")

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
