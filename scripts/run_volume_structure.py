"""D270 -- volume structure, retested under a control that can fail.
Pre-registered in `docs/decisions/D270-volume-structure-retest.md`, commit
4e186ce, BEFORE this version was written.

    uv run python scripts/run_volume_structure.py

STAGE 1 independence (V1a, V1b) -- then STAGE 2 calibration (M1, M2, M3) for
whatever survives.

THE NORMALISATION IS THE WHOLE TEST. Intraday volume is violently U-shaped by
time of day, so a RAW volume score is orthogonal to price BECAUSE IT MEASURES THE
CLOCK. Every score is normalised WITHIN BAR-OF-DAY against the trailing 20
sessions at the same clock position.

WHY THE CONTROLS ARE TWO-SIDED NOW. D269 used `signed_vol = rel_vol x
sign(return)` as a one-sided control, required to FAIL the independence bar. It
passed at 0.14, voiding that run -- and the diagnosis showed the CONTROL was
wrong, not the method: multiplying by a symmetric +/-1 decorrelates the product
from BOTH parents (`signed_vol` vs `rel_vol` is +0.013), and a sign alone reaches
only +0.279 against `trailing_return`, so a 0.5 bar was never reachable.

D270 keeps `signed_vol` as an ordinary candidate score and instruments the test
from both sides instead:

  ctrl_blend  0.5*rank(rel_vol) + 0.5*rank(trailing_return)   MUST FAIL V1b
  ctrl_noise  seeded uniform random                           MUST PASS V1b

Neither is eligible to pass the study. If either misbehaves the run is void.
"""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import sys
from collections import defaultdict
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


C = _load("d267", "run_magnitude_calibration.py")
I = _load("d268", "d268_score_independence.py")
R, M, D = C.R, C.M, C.D

OUT = REPO / "data" / "d270_volume_summary.json"
FIXTURE = REPO / "data" / "fixtures" / "single_name_intraday_15m_panel.csv.gz"

# D270: the five REAL volume scores. `signed_vol` was D269's control and is
# removed -- it decorrelated from both its parents, so it could not test anything.
VOL_SCORES = ("rel_vol", "vol_z", "dollar_vol", "vol_trend", "signed_vol")
REAL_VOL = ("rel_vol", "vol_z", "dollar_vol", "vol_trend", "signed_vol")
# Two-sided instrumentation. Neither is eligible to pass the study.
CONTROLS = ("ctrl_blend", "ctrl_noise")
LOOKBACK_SESSIONS = 20      # trailing sessions at the same bar-of-day
TREND_BARS = 8
SIGN_BARS = 8
V1A_BAR = 3.5
V1B_BAR = 0.50
N_SIMS = 300


def load_volume(panel):
    """Volume aligned to the panel's (symbol, bar) grid, from the same fixture."""
    want = {s: i for i, s in enumerate(panel.symbols)}
    rows = defaultdict(dict)
    with gzip.open(FIXTURE, "rt", newline="") as f:
        for r in csv.DictReader(f):
            if r["symbol"] in want:
                rows[r["symbol"]][r["timestamp"].replace(" ", "T")] = (
                    float(r["volume"]), float(r["close"]))
    n, T = panel.closes.shape
    vol = np.full((n, T), np.nan)
    px = np.full((n, T), np.nan)
    stamps = None
    with gzip.open(FIXTURE, "rt", newline="") as f:
        first_sym = panel.symbols[0]
        stamps = [r["timestamp"].replace(" ", "T") for r in csv.DictReader(f)
                  if r["symbol"] == first_sym]
    assert len(stamps) == T, f"grid mismatch: {len(stamps)} vs {T}"
    for s, i in want.items():
        d = rows[s]
        for t, st in enumerate(stamps):
            if st in d:
                vol[i, t], px[i, t] = d[st]
    return vol, px, stamps


def bar_of_day(stamps):
    bod, k, prev = [], 0, None
    for st in stamps:
        day = st[:10]
        k = 0 if day != prev else k + 1
        prev = day
        bod.append(k)
    return np.array(bod)


def build_volume_scores(panel, vol, px, bod, rets):
    """Every score normalised WITHIN bar-of-day, trailing sessions only."""
    n, T = vol.shape
    out = {k: np.full((n, T), np.nan) for k in VOL_SCORES}
    lv = np.log(np.where(vol > 0, vol, np.nan))
    ldv = np.log(np.where(vol > 0, vol * px, np.nan))
    for i in range(n):
        for d in range(int(bod.max()) + 1):
            idx = np.flatnonzero(bod == d)
            for j, t in enumerate(idx):
                if j < LOOKBACK_SESSIONS:
                    continue
                w = idx[j - LOOKBACK_SESSIONS:j]          # TRAILING ONLY -- R9
                a, b = lv[i, w], lv[i, t]
                if not np.isfinite(b) or not np.isfinite(a).any():
                    continue
                med = np.nanmedian(a)
                sd = np.nanstd(a, ddof=1)
                out["rel_vol"][i, t] = b - med
                if sd > 0:
                    out["vol_z"][i, t] = (b - med) / sd
                a2, b2 = ldv[i, w], ldv[i, t]
                if np.isfinite(b2) and np.isfinite(a2).any():
                    out["dollar_vol"][i, t] = b2 - np.nanmedian(a2)
        rv = out["rel_vol"][i]
        for t in range(TREND_BARS, T):
            seg = rv[t - TREND_BARS + 1:t + 1]
            if np.isfinite(seg).sum() == TREND_BARS:
                out["vol_trend"][i, t] = np.polyfit(np.arange(TREND_BARS), seg, 1)[0]
        # An ordinary candidate score in D270; it was D269's failed control.
        cum = np.full(T, np.nan)
        cs = np.concatenate([[0.0], np.cumsum(np.nan_to_num(rets[i]))])
        cum[SIGN_BARS:] = cs[SIGN_BARS + 1:] - cs[1:T - SIGN_BARS + 1]
        out["signed_vol"][i] = rv * np.sign(cum)
    return out


def main() -> int:
    raw_panel, raw_cleaned = R.load_full()
    panel, cleaned = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    first, _ = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    vol, px, stamps = load_volume(panel)
    bod = bar_of_day(stamps)
    price_sc = C.build_scores(panel, cleaned)
    vol_sc = build_volume_scores(panel, vol, px, bod, panel.total_log_returns)

    # ---- D270's two-sided controls, built from the ranked columns ----
    n_sym = len(panel.symbols)
    rng = np.random.default_rng(0)
    ctrl = {}
    blend = np.full(panel.closes.shape, np.nan)
    noise = np.full(panel.closes.shape, np.nan)
    for i in range(n_sym):
        rv = I.rankify(vol_sc["rel_vol"][i, start:])
        tr = I.rankify(price_sc["trailing_return"][i, start:])
        blend[i, start:] = 0.5 * rv + 0.5 * tr        # MUST fail V1b
        noise[i, start:] = rng.random(rv.shape[0])    # MUST pass V1b
    ctrl["ctrl_blend"], ctrl["ctrl_noise"] = blend, noise

    names = list(C.SCORES) + list(VOL_SCORES) + list(CONTROLS)
    allsc = {**price_sc, **vol_sc, **ctrl}
    cols = []
    for nme in names:
        per = [I.rankify(allsc[nme][i, start:]) for i in range(len(panel.symbols))]
        cols.append(np.concatenate(per))
    X = np.vstack(cols)
    ok = np.all(np.isfinite(X), axis=0)
    X = X[:, ok]
    print(f"STAGE 1 -- INDEPENDENCE.  {X.shape[1]:,} bars with all {len(names)} scores finite\n")
    Rm = np.corrcoef(X)

    print(f"  {'score':14s} " + " ".join(f"{n[:7]:>8s}" for n in C.SCORES)
          + f" {'max|rho|':>9s}  V1b")
    v1b_pass = []
    per_score = {}
    for k, nme in enumerate(list(VOL_SCORES) + list(CONTROLS)):
        r = k + len(C.SCORES)
        rhos = [float(Rm[r, j]) for j in range(len(C.SCORES))]
        mx = max(abs(x) for x in rhos)
        ok_b = mx < V1B_BAR
        if ok_b and nme in REAL_VOL:
            v1b_pass.append(nme)
        per_score[nme] = {"rho_vs_price": rhos, "max_abs_rho": mx, "V1b": ok_b}
        print(f"  {nme:14s} " + " ".join(f"{x:8.2f}" for x in rhos)
              + f" {mx:9.2f}  {'PASS' if ok_b else 'fail'}")

    lam = np.maximum(np.linalg.eigvalsh(Rm), 0.0)
    eff = float(lam.sum() ** 2 / (lam ** 2).sum())
    v1a = eff >= V1A_BAR
    print(f"\n  effective independent scores: {eff:.2f} of {len(names)}   "
          f"(price-only was 2.87 of 9)")
    print(f"  V1a  >= {V1A_BAR}: {'PASS' if v1a else 'FAIL'}")
    print(f"  V1b  at least one volume score max|rho| < {V1B_BAR}: "
          f"{'PASS -> ' + ', '.join(v1b_pass) if v1b_pass else 'FAIL'}")

    # D270's TWO-SIDED instrumentation. Both must behave or the run is void.
    cb, cn = per_score["ctrl_blend"], per_score["ctrl_noise"]
    print("\n  CONTROLS -- both must behave, or the run is void:")
    print(f"    ctrl_blend  MUST FAIL V1b (it is half a price score):  "
          f"max|rho| {cb['max_abs_rho']:.2f}  -> "
          + ("correctly FAILS -- correlation does detect contamination here"
             if not cb["V1b"] else
             "*** PASSED. CORRELATION CANNOT DETECT CONTAMINATION. VOID ***"))
    print(f"    ctrl_noise  MUST PASS V1b (it is pure random):         "
          f"max|rho| {cn['max_abs_rho']:.2f}  -> "
          + ("correctly PASSES -- the instrument is not spuriously correlating"
             if cn["V1b"] else
             "*** FAILED. THE INSTRUMENT IS BROKEN. VOID ***"))
    void = bool(cb["V1b"] or not cn["V1b"])

    payload = {"preregistration": "docs/decisions/D270-volume-structure-retest.md",
               "commit": "4e186ce", "names": names,
               "effective_independent": eff, "V1a": v1a, "V1b_passers": v1b_pass,
               "per_score": per_score, "control_void": void, "stage2": {}}

    if void:
        print("\nSTOPPING: the control failed, so no stage-2 reading is taken.")
    elif not v1b_pass:
        print("\nSTAGE 2 SKIPPED: nothing cleared V1b, so nothing is eligible.")
    else:
        print(f"\nSTAGE 2 -- CALIBRATION of {v1b_pass}, H = {C.H} bars\n")
        for st in ("ALL", "LOW", "HIGH"):
            p, cl = ((panel, cleaned) if st == "ALL"
                     else R.subset(raw_panel, raw_cleaned, R.STRATA[st]))
            keep = [panel.symbols.index(s) for s in p.symbols]
            fwd = C.forward(p, first, start)
            c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
            print(f"  {st}  cost bar 2c = {c2:.2f} bp")
            for nme in v1b_pass:
                qs = C.quintile_means(vol_sc[nme][keep], fwd, start)
                if any(q.size == 0 for q in qs):
                    print(f"    {nme:14s} insufficient data")
                    continue
                means = np.array([q.mean() for q in qs]) * 1e4
                d = np.diff(means)
                mono = bool(np.all(d > 0) or np.all(d < 0))
                extreme = means[-1] if abs(means[-1]) >= abs(means[0]) else means[0]
                spread = float(means[-1] - means[0])
                payload["stage2"][f"{st}:{nme}"] = {
                    "quintile_means_bp": means.tolist(), "spread_bp": spread,
                    "extreme_bp": float(extreme), "cost_bar_bp": c2,
                    "M1_monotone": mono, "M2_clears_bar": bool(abs(extreme) >= c2)}
                print(f"    {nme:14s} " + " ".join(f"{m:7.2f}b" for m in means)
                      + f"  spread {spread:7.2f}b  M1 {'YES' if mono else 'no':>3s}"
                        f"  M2 {'YES' if abs(extreme) >= c2 else 'no':>3s}")
            print()
        surv = [k for k, v in payload["stage2"].items()
                if v["M1_monotone"] and v["M2_clears_bar"]]
        payload["stage2_survivors_before_M3"] = surv
        print(f"  clearing M1 AND M2 (before the M3 floor): {surv or 'NONE'}")
        if not surv:
            print("  -> M3 not computed: nothing reached it. V2 FAILS.")

    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
