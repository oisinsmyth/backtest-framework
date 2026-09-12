"""D475 -- does the volatility-conditioned continuation gradient TRANSFER to seven roots it
was never seen on?

    uv run python scripts/d475_continuation_transfer.py --self-test
    uv run python scripts/d475_continuation_transfer.py --run [--json]

Pre-registered in
`docs/decisions/D475-PRE-REG-does-the-volatility-conditioned-continuation-gradient-TRANSFER-to-seven-instruments-it-was-never-seen-on.md`,
committed before this file existed. **Every root, horizon, bucket count, statistic, null,
threshold and prediction below is copied from that record. None is chosen here.**

HOW MOMENTUM IS MEASURED, stated plainly because it is the whole content of the signal
---------------------------------------------------------------------------------------
    signal(t) = sign( close[last segment of window t] - open[first segment of window t] )
    trade     = that sign, held through window t+1, entered at its open, exited at its close

**No magnitude, no moving average, no breakout level, no trend fit, no second lag.** This is
the canonical time-series momentum estimator (Moskowitz-Ooi-Pedersen use the sign of the past
12-month return held 12 months) transplanted to intraday horizons.

Magnitude is excluded ON PURPOSE: magnitude *is* the volatility conditioner, so using it would
make direction and timing the same variable -- which is why D474's V1 was demoted to a
secondary. The cost is power, and it is accepted.

**THE KNOWN GAP, recorded here rather than discovered later: the lookback is locked EQUAL to
the holding period.** Real momentum work uses lookback != hold. This grid tests only the
diagonal of a 2-D space, so a gradient at (4-hour lookback, 1-hour hold) would be invisible to
it. Widening that is a declared amendment to D475 §2, not a silent change, and has not been
made.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "d475_continuation_transfer.json"

# ---- every constant is from the pre-registration, by section
PRIMARY = ("NQ", "YM", "ZN", "ZB", "GC", "CL", "6E")   # §1: the 7 unseen roots
DISCOVERY = "ES"                                        # §1: spent, not evidence
EXCLUDED = {"RTY": "fails gate G2 (reverting roll 2020-06-14 RTYU0->RTYM0)"}   # §1
IN_SAMPLE = ("2016-01-04", "2023-12-29")                # §1
SEGMENTS = ([f"h{h:02d}" for h in range(18, 24)]
            + [f"h{h:02d}" for h in range(0, 17)])      # §1: 18:00 -> 16:59 ET, 23 segments
HORIZONS = (1, 2, 3, 4, 5)                              # §2: hours
PRIOR_SEGS = 3                                          # §2: vol over 3 segments before t
NQ_BUCKETS = 5                                          # §2: quintiles
N_DRAWS = 2000                                          # §4
MIN_ROOTS_POSITIVE = 5                                  # §5: at least 5 of 7
CROSS_TICKS = 1.009                                     # §8 limitation: an ES measurement
COMMISSION_RT = 3.00                                    # D466's declared cost line
MICRO_OF = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K"}
SEED = 475


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ---------------------------------------------------------------- the statistic

def trend_slope(indicator: np.ndarray, qrank: np.ndarray) -> float:
    """OLS slope of the same-sign indicator on quintile rank, in PERCENTAGE POINTS.

    §3's primary per-cell quantity. Closed form rather than a solver so the units cannot
    drift: slope = cov(q, ind) / var(q), then x100.
    """
    if len(indicator) < 10:
        return float("nan")
    q = qrank.astype(np.float64)
    vq = float(((q - q.mean()) ** 2).mean())
    if vq <= 0:
        return float("nan")
    cov = float(((q - q.mean()) * (indicator - indicator.mean())).mean())
    return 100.0 * cov / vq


def slopes_from(ind: np.ndarray, qr: np.ndarray, cell: np.ndarray, n_cells: int):
    """trend_slope per (root, horizon) cell, given a flat cell index. NaN where too few."""
    out = np.full(n_cells, np.nan)
    for c in range(n_cells):
        m = cell == c
        if m.sum() >= 200:
            out[c] = trend_slope(ind[m], qr[m])
    return out


def slope_se(ind: np.ndarray, qr: np.ndarray) -> float:
    """Analytic SE of trend_slope, in pp. Used to SET TEST TOLERANCES rather than guess them.

    slope = cov(q, ind)/var(q), so SE ~ 100*sqrt(var(ind)/(n*var(q))). A tolerance of 0.06
    pp was chosen by eye on the first pass and sits BELOW one SE (~0.08), which failed a
    correct null for being correctly noisy -- the same error D469 made with a "2%" band.
    """
    q = qr.astype(np.float64)
    vq = float(((q - q.mean()) ** 2).mean())
    if vq <= 0 or len(ind) < 2:
        return float("nan")
    return 100.0 * float(np.sqrt(ind.var() / (len(ind) * vq)))


# ---- THE TWO NULLS AS FUNCTIONS, so the self-test exercises the code the run uses rather
# than a re-implementation of it (§4).

def null1_sign_randomised(ind: np.ndarray, rng) -> np.ndarray:
    """N1: randomise the signal's sign. Flipping the signal maps the same-sign indicator to
    its complement, so this is exactly ind -> 1-ind with probability 1/2, element-wise.
    Quintiles and forward returns are untouched."""
    flip = rng.random(len(ind)) < 0.5
    return np.where(flip, 1.0 - ind, ind)


def null2_quintiles_shuffled(qr: np.ndarray, cell: np.ndarray, n_cells: int,
                             rng) -> np.ndarray:
    """N2: permute the quintile labels WITHIN each cell. The indicator is untouched, so the
    mean hit rate is preserved exactly and only the conditioner's alignment is destroyed."""
    out = qr.copy()
    for c in range(n_cells):
        m = cell == c
        out[m] = rng.permutation(out[m])
    return out


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:64} {detail}")
        if not cond:
            fails.append(label)

    rg = np.random.default_rng(7)
    n = 200_000
    qr = rg.integers(1, NQ_BUCKETS + 1, size=n)

    # TOLERANCES COME FROM THE ANALYTIC SE, not from eye. On the first pass a 0.06 pp band
    # sat below one SE and failed a correct null for being correctly noisy.
    cell0 = np.zeros(n, dtype=np.int64)

    # --- UNITS: a hit rate rising exactly 1 pp per quintile must read slope = 1.00
    ind = (rg.random(n) < 0.50 + 0.01 * (qr - 3)).astype(np.float64)
    se = slope_se(ind, qr)
    s = trend_slope(ind, qr)
    chk("units: a 1 pp-per-quintile gradient reads 1.00", abs(s - 1.0) < 3 * se,
        f"{s:+.4f} +- {se:.4f} (3 SE band)")
    # --- and a 3 pp gradient reads 3.00, so the scale is linear, not merely monotone
    ind3 = (rg.random(n) < 0.50 + 0.03 * (qr - 3)).astype(np.float64)
    se3 = slope_se(ind3, qr)
    chk("units are linear: a 3 pp gradient reads 3.00",
        abs(trend_slope(ind3, qr) - 3.0) < 3 * se3,
        f"{trend_slope(ind3, qr):+.4f} +- {se3:.4f}")
    # --- a FLAT hit rate reads zero, however far from 50% it sits
    flat = (rg.random(n) < 0.55).astype(np.float64)
    sef = slope_se(flat, qr)
    chk("a FLAT 55% hit rate reads ~0 (level is not slope)",
        abs(trend_slope(flat, qr)) < 3 * sef,
        f"{trend_slope(flat, qr):+.4f} +- {sef:.4f}")

    # --- N1 and N2 are exercised THROUGH THE FUNCTIONS THE RUN CALLS, not re-implemented
    ind_n1 = null1_sign_randomised(ind3, rg)
    qr_n2 = null2_quintiles_shuffled(qr, cell0, 1, rg)

    chk("N1 destroys a planted gradient", abs(trend_slope(ind_n1, qr)) < 3 * se3,
        f"{trend_slope(ind_n1, qr):+.4f} from {trend_slope(ind3, qr):+.4f}")
    chk("N1 CHANGES the indicator", not np.array_equal(ind_n1, ind3),
        f"{int((ind_n1 != ind3).sum()):,} of {n:,} flipped")
    chk("N1 returns the indicator only -- quintiles are not its output",
        ind_n1.shape == ind3.shape)

    chk("N2 destroys a planted gradient", abs(trend_slope(ind3, qr_n2)) < 3 * se3,
        f"{trend_slope(ind3, qr_n2):+.4f} from {trend_slope(ind3, qr):+.4f}")
    chk("N2 CHANGES the quintile labels", not np.array_equal(qr_n2, qr),
        f"{int((qr_n2 != qr).sum()):,} of {n:,} relabelled")
    # THE DISCRIMINATING PAIR: N2 must be a conditioner test, not a second N1. It leaves the
    # indicator untouched (so the hit-rate LEVEL survives exactly) while N1 does not.
    chk("N2 preserves the quintile MULTISET (a permutation, not a redraw)",
        bool(np.array_equal(np.bincount(qr_n2, minlength=7),
                            np.bincount(qr, minlength=7))))
    chk("N2 leaves the hit-rate LEVEL exactly intact, N1 does not",
        abs(float(ind3.mean()) - float(ind3.mean())) < 1e-12
        and abs(float(ind_n1.mean()) - 0.5) < 0.01,
        f"N2 level {ind3.mean():.4f} (indicator never touched); "
        f"N1 level {ind_n1.mean():.4f} -> 0.5")
    # and on level+gradient, N2 must remove ONLY the slope
    mixed = (rg.random(n) < (0.55 + 0.03 * (qr - 3))).astype(np.float64)
    sem = slope_se(mixed, qr)
    qr_n2b = null2_quintiles_shuffled(qr, cell0, 1, rg)
    chk("N2 on level+gradient removes the slope and keeps the level",
        abs(trend_slope(mixed, qr_n2b)) < 3 * sem and abs(mixed.mean() - 0.55) < 0.01,
        f"slope {trend_slope(mixed, qr_n2b):+.4f} +- {sem:.4f}, level {mixed.mean():.4f}")

    # --- and the per-cell driver must agree with the single-cell call
    sl = slopes_from(ind3, qr, cell0, 1)
    chk("slopes_from on one cell equals trend_slope directly",
        abs(sl[0] - trend_slope(ind3, qr)) < 1e-12, f"{sl[0]:+.4f}")
    chk("slopes_from returns NaN for an under-populated cell",
        bool(np.isnan(slopes_from(ind3[:50], qr[:50], cell0[:50], 1)[0])))

    # --- the segment clock: 23 hourly segments in chronological order across midnight
    chk("23 segments", len(SEGMENTS) == 23, f"{len(SEGMENTS)}")
    chk("segments start at h18 and end at h16", SEGMENTS[0] == "h18" and SEGMENTS[-1] == "h16")
    chk("segments cross midnight in order h23 -> h00",
        SEGMENTS.index("h23") + 1 == SEGMENTS.index("h00"))
    chk("no segment repeats", len(set(SEGMENTS)) == 23)

    # --- window construction: non-overlapping, conditioner STRICTLY before the signal
    for h in HORIZONS:
        nwin = len(SEGMENTS) // h
        starts = [k * h for k in range(nwin)]
        pairs = [(k, k + 1) for k in range(nwin - 1) if starts[k] >= PRIOR_SEGS]
        ok = all(starts[b] == starts[a] + h for a, b in pairs)
        strictly_before = all(starts[a] - PRIOR_SEGS >= 0 for a, _ in pairs)
        chk(f"h={h}: windows abut, conditioner strictly before, {len(pairs)} pairs/session",
            ok and strictly_before and len(pairs) >= 1,
            f"starts {starts[:4]}{'...' if len(starts) > 4 else ''}")

    # --- the family-of-roots consistency rule, §5
    sl = np.array([1.0, 0.5, 0.2, -0.1, 0.3, 0.4, -0.2])
    chk("5-of-7 rule counts individually positive roots",
        int((sl > 0).sum()) == 5 and int((sl > 0).sum()) >= MIN_ROOTS_POSITIVE,
        f"{int((sl > 0).sum())} of 7")
    sl2 = np.array([1.0, -0.5, -0.2, -0.1, 0.3, -0.4, -0.2])
    chk("and refuses a mean driven by one root",
        int((sl2 > 0).sum()) < MIN_ROOTS_POSITIVE, f"{int((sl2 > 0).sum())} of 7 positive")

    # --- cost in ticks at micro size, from the committed specs
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    mes = COMMISSION_RT / spec["MES"]["tick_usd"] + CROSS_TICKS
    mnq = COMMISSION_RT / spec["MNQ"]["tick_usd"] + CROSS_TICKS
    chk("MES cost is the familiar 3.409 ticks", abs(mes - 3.409) < 0.001, f"{mes:.3f}")
    chk("MNQ cost is MUCH worse in ticks (its tick is worth less)", mnq > 1.8 * mes,
        f"MNQ {mnq:.3f} vs MES {mes:.3f} ticks")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


# ---------------------------------------------------------------- build

def build_root(root: str, d, tick: float | None) -> dict:
    """Per-root observations: signal sign, forward return, prior-3-segment vol, horizon.

    Returns ticks where a committed tick size exists; otherwise PRICE units, flagged by the
    caller (§2: 6E has no entry in futures_contract_specs.json).
    """
    o = np.stack([d[f"{s}_o"].to_numpy(float) for s in SEGMENTS], axis=1)
    c = np.stack([d[f"{s}_c"].to_numpy(float) for s in SEGMENTS], axis=1)
    scale = tick if tick else 1.0
    rows = {"h": [], "sig": [], "fwd": [], "vol": []}
    nseg = len(SEGMENTS)
    for h in HORIZONS:
        nwin = nseg // h
        for k in range(nwin - 1):
            a0 = k * h
            if a0 < PRIOR_SEGS:                     # §2: conditioner strictly before t
                continue
            b0 = a0 + h - 1                         # last segment of the signal window
            a1, b1 = a0 + h, a0 + 2 * h - 1         # the forward window
            if b1 >= nseg:
                continue
            sig_r = (c[:, b0] - o[:, a0]) / scale
            fwd_r = (c[:, b1] - o[:, a1]) / scale
            # prior volatility: RMS of the PRIOR_SEGS hourly segment returns before a0.
            # Computed EXPLICITLY rather than via nanmean: a session with every prior
            # segment missing would make nanmean warn and return NaN, and relying on that
            # NaN to propagate into the `good` mask is implicit behaviour. Require all
            # PRIOR_SEGS present instead, which is the honest reading of "vol over the 3
            # segments before t".
            pr = (c[:, a0 - PRIOR_SEGS:a0] - o[:, a0 - PRIOR_SEGS:a0]) / scale
            pr_ok = np.isfinite(pr).all(axis=1)
            vol = np.where(pr_ok, np.sqrt((np.where(pr_ok[:, None], pr, 0.0) ** 2)
                                          .mean(axis=1)), np.nan)
            good = (np.isfinite(sig_r) & np.isfinite(fwd_r) & np.isfinite(vol)
                    & (sig_r != 0) & (fwd_r != 0) & (vol > 0))
            rows["h"].append(np.full(int(good.sum()), h))
            rows["sig"].append(np.sign(sig_r[good]))
            rows["fwd"].append(fwd_r[good])
            rows["vol"].append(vol[good])
    return {k: (np.concatenate(v) if v else np.array([])) for k, v in rows.items()}


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))

    # §1: every primary root's own gates are READ and required to pass
    for root in PRIMARY:
        g = meta["gates"].get(root)
        if g is None:
            raise GateError(f"[FIXTURE] no gate block for {root}")
        bad = [k for k, v in g.items() if isinstance(v, dict) and v.get("passes") is False]
        if bad:
            raise GateError(f"[FIXTURE] {root} fails gates {bad}; it is a PRIMARY root")
    for root, why in EXCLUDED.items():
        P(f"  excluded: {root} -- {why}")

    d_all = pd.read_csv(FIX)
    if (d_all["day"] > "2023-12-31").any():
        pass    # the fixture legitimately extends past 2023; the FILTER below is the gate
    P(f"\nfixture {FIX.name}: {len(d_all):,} rows, roots {sorted(d_all['root'].unique())}")

    obs, flags = {}, {}
    for root in (DISCOVERY,) + PRIMARY:
        start = max(IN_SAMPLE[0], meta["usable_start"][root])
        d = d_all[(d_all["root"] == root) & d_all["same_front"]]
        d = d[d["day"].between(start, IN_SAMPLE[1])]
        # §1: 2024+ is SEALED. This is the gate, and it raises.
        if len(d) and d["day"].max() > "2023-12-31":
            raise GateError(f"[HOLDOUT] {root}: rows past 2023 survived the filter")
        tick = spec[root]["tick_points"] if root in spec else None
        flags[root] = {"unit": "ticks" if tick else "PRICE (no committed tick size)",
                       "usable_start": start, "sessions": int(len(d))}
        obs[root] = build_root(root, d, tick)
        P(f"  {root:4} {len(d):>5} same-front sessions from {start} · "
          f"{len(obs[root]['sig']):>7,} observations · {flags[root]['unit']}")

    # ---- §2/§3: quintiles within root x horizon, then the per-cell trend slope
    cells, ind_all, qr_all, cell_all = [], [], [], []
    for root in PRIMARY:
        b = obs[root]
        for h in HORIZONS:
            m = b["h"] == h
            if m.sum() < 1000:
                continue
            vol, sig, fwd = b["vol"][m], b["sig"][m], b["fwd"][m]
            edges = np.quantile(vol, np.linspace(0, 1, NQ_BUCKETS + 1))
            qr = np.clip(np.searchsorted(edges[1:-1], vol, side="right") + 1,
                         1, NQ_BUCKETS)
            ind = (np.sign(fwd) == sig).astype(np.float64)
            cells.append({"root": root, "h": h, "n": int(m.sum()),
                          "hit_rate": float(ind.mean()),
                          "slope_pp_per_quintile": trend_slope(ind, qr),
                          "by_quintile": [
                              {"q": q, "n": int((qr == q).sum()),
                               "hit_rate": float(ind[qr == q].mean()),
                               "gross_ticks": float((sig * fwd)[qr == q].mean())}
                              for q in range(1, NQ_BUCKETS + 1)]})
            ind_all.append(ind)
            qr_all.append(qr)
            cell_all.append(np.full(int(m.sum()), len(cells) - 1))

    ind_all = np.concatenate(ind_all)
    qr_all = np.concatenate(qr_all)
    cell_all = np.concatenate(cell_all)
    n_cells = len(cells)

    P(f"\n  {n_cells} cells (root x horizon) over {len(ind_all):,} observations")
    P(f"  {'root':>5}{'h':>3}{'n':>9}{'hit':>8}{'slope pp/q':>12}   by quintile hit %")
    for c in cells:
        qs = " ".join(f"{q['hit_rate']*100:5.2f}" for q in c["by_quintile"])
        P(f"  {c['root']:>5}{c['h']:>3}{c['n']:>9,}{c['hit_rate']:>8.2%}"
          f"{c['slope_pp_per_quintile']:>+12.3f}   {qs}")

    # ---- §3: THE PRIMARY STATISTIC, one number
    slopes = np.array([c["slope_pp_per_quintile"] for c in cells])
    S = float(np.nanmean(slopes))
    P(f"\n  PRIMARY STATISTIC S = mean slope over {n_cells} cells = "
      f"{S:+.4f} pp per quintile")

    # §1: ES is the DISCOVERY root -- reported descriptively, never in S, never in a null,
    # never in the bar. Without it the reader cannot see discovery against transfer.
    es_cells = []
    b = obs[DISCOVERY]
    for h in HORIZONS:
        m = b["h"] == h
        if m.sum() < 1000:
            continue
        vol, sig, fwd = b["vol"][m], b["sig"][m], b["fwd"][m]
        edges = np.quantile(vol, np.linspace(0, 1, NQ_BUCKETS + 1))
        qr = np.clip(np.searchsorted(edges[1:-1], vol, side="right") + 1, 1, NQ_BUCKETS)
        ind = (np.sign(fwd) == sig).astype(np.float64)
        es_cells.append({"root": DISCOVERY, "h": h, "n": int(m.sum()),
                         "hit_rate": float(ind.mean()),
                         "slope_pp_per_quintile": trend_slope(ind, qr),
                         "top_quintile_hit": float(ind[qr == NQ_BUCKETS].mean())})
    es_S = float(np.nanmean([c["slope_pp_per_quintile"] for c in es_cells]))
    P(f"\n  DISCOVERY ROOT (descriptive, carries NO evidential weight -- §1):")
    P(f"  {'root':>5}{'h':>3}{'n':>9}{'hit':>8}{'slope pp/q':>12}{'top-q hit':>11}")
    for c in es_cells:
        P(f"  {c['root']:>5}{c['h']:>3}{c['n']:>9,}{c['hit_rate']:>8.2%}"
          f"{c['slope_pp_per_quintile']:>+12.3f}{c['top_quintile_hit']:>11.2%}")
    P(f"    ES mean slope {es_S:+.4f} against the 7 unseen roots' {S:+.4f}")

    # the LEVEL, which is a different question from the SLOPE and worth seeing
    lvl = {r: float(np.mean([c["hit_rate"] for c in cells if c["root"] == r]))
           for r in PRIMARY}
    P(f"\n  pooled hit rate by root (the LEVEL, not the gradient) -- "
      f"50% is a coin flip:")
    P("    " + "  ".join(f"{r} {v:.2%}" for r, v in lvl.items()))

    # ---- §4: two nulls
    rg = np.random.default_rng(SEED)
    n1 = np.empty(N_DRAWS)
    n2 = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        # THE SAME FUNCTIONS THE SELF-TEST EXERCISES -- not a second implementation
        n1[i] = float(np.nanmean(slopes_from(
            null1_sign_randomised(ind_all, rg), qr_all, cell_all, n_cells)))
        n2[i] = float(np.nanmean(slopes_from(
            ind_all, null2_quintiles_shuffled(qr_all, cell_all, n_cells, rg),
            cell_all, n_cells)))

    def summarise_null(x, name):
        p50, p95 = float(np.quantile(x, .50)), float(np.quantile(x, .95))
        boot = np.array([np.quantile(rg.choice(x, len(x), replace=True), .95)
                         for _ in range(400)])
        se = float(boot.std(ddof=1))
        P(f"  {name}: p50 {p50:+.4f}  p95 {p95:+.4f}  (bootstrap SE of p95 {se:.4f})  "
          f"margin {S - p95:+.4f} = {(S - p95)/se:+.1f} SE")
        return {"p50": p50, "p95": p95, "se_of_p95": se,
                "margin": S - p95, "margin_in_se": (S - p95) / se,
                "clears_by_2se": bool(S - p95 > 2 * se)}

    P("")
    nn1 = summarise_null(n1, "N1 sign-randomised ")
    nn2 = summarise_null(n2, "N2 quintile-shuffle")

    # ---- §5: the bar
    by_root = {r: float(np.nanmean([c["slope_pp_per_quintile"] for c in cells
                                    if c["root"] == r])) for r in PRIMARY}
    n_pos = sum(1 for v in by_root.values() if v > 0)
    P(f"\n  per-root mean slope:")
    for r, v in by_root.items():
        P(f"    {r:>4} {v:+.4f} pp/quintile")
    P(f"  individually positive: {n_pos} of {len(PRIMARY)} "
      f"(need >= {MIN_ROOTS_POSITIVE})")

    transfer = (S > 0 and nn1["clears_by_2se"] and nn2["clears_by_2se"]
                and n_pos >= MIN_ROOTS_POSITIVE)
    partial = (S > 0 and nn1["clears_by_2se"] and not nn2["clears_by_2se"])
    # UNRESOLVED and NO TRANSFER are different states and the first label conflated them:
    # a statistic sitting just under the null p95 is unresolved, one sitting far BELOW it
    # (or on the wrong side of zero) is a decisive negative. Say which.
    near = min(nn1["margin_in_se"], nn2["margin_in_se"]) > -2.0
    verdict = ("TRANSFER CONFIRMED" if transfer else
               "PARTIAL -- clears N1 but not N2: direction predictable, conditioner not the "
               "selector" if partial else
               "UNRESOLVED -- within 2 SE of a null p95, neither shown nor excluded" if near
               else "NO TRANSFER -- the statistic is decisively short of both nulls"
                    + (" and on the WRONG SIDE OF ZERO" if S <= 0 else ""))
    P(f"\n  **VERDICT: {verdict}**")

    # ---- §5 secondary: tradeability, ES/NQ/YM only, where a micro exists
    trade = []
    for root in ("NQ", "YM"):                          # ES is discovery, not evidence
        micro = MICRO_OF.get(root)
        if micro not in spec or flags[root]["unit"] != "ticks":
            continue
        cost = COMMISSION_RT / spec[micro]["tick_usd"] + CROSS_TICKS
        for c in [c for c in cells if c["root"] == root]:
            top = c["by_quintile"][-1]
            trade.append({"root": root, "micro": micro, "h": c["h"],
                          "cost_ticks": cost, "top_q_gross_ticks": top["gross_ticks"],
                          "top_q_net_ticks": top["gross_ticks"] - cost,
                          "net_positive": bool(top["gross_ticks"] - cost > 0)})
    n_trade_roots = len({t["root"] for t in trade
                         if sum(1 for u in trade if u["root"] == t["root"]
                                and u["net_positive"]) >= 2})
    P(f"\n  tradeability (top quintile, micro cost): "
      f"{sum(1 for t in trade if t['net_positive'])} of {len(trade)} cells net positive; "
      f"{n_trade_roots} root(s) positive at >= 2 horizons")

    # ---- §6: the pre-registered predictions
    best_a = max((c["by_quintile"][-1]["hit_rate"] - 0.5) for c in cells)
    eq = [by_root[r] for r in ("NQ", "YM")]
    non_eq = [by_root[r] for r in ("ZN", "ZB", "GC", "CL", "6E")]
    ya = S > 0 and nn1["clears_by_2se"]
    yb = not nn2["clears_by_2se"]
    yc = all(v > 0 for v in eq) and float(np.mean(eq)) > float(np.mean(non_eq))
    yd = n_trade_roots == 0
    ye = best_a < 0.05
    P(f"\n  PRE-REGISTERED PREDICTIONS (D475 §6):")
    P(f"    Y-a S>0 and clears N1 by 2 SE          {'HELD' if ya else 'BROKEN':>7}")
    P(f"    Y-b S FAILS to clear N2 by 2 SE        {'HELD' if yb else 'BROKEN':>7}")
    P(f"    Y-c equity index > non-equity          {'HELD' if yc else 'BROKEN':>7}  "
      f"eq {np.mean(eq):+.3f} vs non-eq {np.mean(non_eq):+.3f}")
    P(f"    Y-d nothing tradeable at 2+ horizons   {'HELD' if yd else 'BROKEN':>7}")
    P(f"    Y-e best implied skill below 5%        {'HELD' if ye else 'BROKEN':>7}  "
      f"{best_a:.2%}")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D475-PRE-REG-does-the-volatility-conditioned-"
                               "continuation-gradient-TRANSFER-to-seven-instruments-it-was-"
                               "never-seen-on.md",
           "momentum_definition": "sign(close[last segment of window t] - open[first segment "
                                  "of window t]); traded through window t+1 at its open and "
                                  "close. No magnitude, no moving average, no breakout, no "
                                  "trend fit, no second lag. Lookback is LOCKED EQUAL to the "
                                  "holding period -- only the diagonal of a 2-D space is "
                                  "tested, which is a stated gap, not an oversight.",
           "source": str(FIX.relative_to(REPO)),
           "roots_primary": list(PRIMARY), "root_discovery": DISCOVERY,
           "roots_excluded": EXCLUDED, "window": list(IN_SAMPLE),
           "root_flags": flags, "n_cells": n_cells, "n_observations": int(len(ind_all)),
           "S_primary": S, "slopes_by_root": by_root, "roots_positive": n_pos,
           "discovery_root_cells": es_cells, "discovery_root_mean_slope": es_S,
           "pooled_hit_rate_by_root": lvl,
           "null_N1_sign_randomised": nn1, "null_N2_quintile_shuffled": nn2,
           "verdict": verdict, "tradeability": trade,
           "predictions": {"Y-a": bool(ya), "Y-b": bool(yb), "Y-c": bool(yc),
                           "Y-d": bool(yd), "Y-e": bool(ye)},
           "cells": cells,
           "limitations": [
               "hourly resolution; the D472 volume-clock exit (+1.18 pp) is NOT applied, so "
               "net figures understate by roughly that much",
               "the 1.009-tick crossing is an ES measurement ASSUMED for other roots",
               "five asset classes are not five independent draws: ZN/ZB are both US rates "
               "and NQ/YM both equity index, so effective breadth is nearer 4-5 than 7 and "
               "the 5-of-7 rule does not fix it",
               "in-sample on unseen INSTRUMENTS is not out-of-sample in TIME; 2024+ remains "
               "the confirmation slice",
               "fixed hold to the window close: no stop, no target, and D471 section 5's "
               "adverse/|move| ~ 0.50 says a stop would bind",
               "6E has no committed tick size, so its returns are in PRICE units and its "
               "slope is scale-free but its gross edge is not comparable with the others"]}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.run:
        return do_run(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
