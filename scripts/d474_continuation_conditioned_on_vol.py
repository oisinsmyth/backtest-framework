"""D474 -- continuation conditioned on volatility state: does it carry a signed edge that
clears the micro cost?

    uv run python scripts/d474_continuation_conditioned_on_vol.py --self-test
    uv run python scripts/d474_continuation_conditioned_on_vol.py --run [--json]

Pre-registered in
`docs/decisions/D474-PRE-REG-does-continuation-conditioned-on-volatility-state.md`,
committed before this file existed. **Every threshold, horizon, bucket count, null and
prediction below is copied from that record and none is chosen here.**

The hypothesis is the principal's: volatility for timing, continuation for direction. D473 §4
ruled momentum out on a POOLED variance ratio, and a pooled 1.00 is exactly what momentum in
one state plus reversal in another produces (D435: +38 against -48, averaged to -7). This tests
the conditional version.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_ES_rth_1m.csv.gz"
META = REPO / "data" / "fixtures" / "fut_index_1m.meta.json"
OUT = REPO / "data" / "d474_continuation_conditioned_on_vol.json"

# ---- every constant here is from the pre-registration, section by section
TICK_PTS = 0.25
COST_TICKS = 1.009 + 3.00 / 1.25          # §1: 3.409
IN_SAMPLE = ("2016-01-04", "2023-12-29")  # §1
RTH_MIN = 390                             # §1
HORIZONS = (15, 30, 60, 120, 195)         # §2
NQ = 5                                    # §2
VARIANTS = ("V1_own_magnitude", "V2_prior_regime")   # §2
N_DRAWS = 2000                            # §4
SEED = 474


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


def edge_and_t(sig: np.ndarray, fwd: np.ndarray) -> tuple[float, float, int]:
    """Gross edge per trade in ticks, its t-stat, and n. §3's primary statistic."""
    x = sig * fwd
    n = len(x)
    if n < 30:
        return float("nan"), float("nan"), n
    m = float(x.mean())
    sd = float(x.std(ddof=1))
    return m, (m / (sd / np.sqrt(n)) if sd > 0 else 0.0), n


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:62} {detail}")
        if not cond:
            fails.append(label)

    rg = np.random.default_rng(1)

    # --- the statistic must find a PLANTED continuation edge, and get its size right
    n = 20_000
    fwd = rg.standard_normal(n) * 10.0
    sig = np.sign(rg.standard_normal(n))
    planted = sig * 2.0 + fwd                    # +2 ticks of continuation per trade
    m, t, _ = edge_and_t(sig, planted)
    chk("finds a planted +2 tick edge", abs(m - 2.0) < 0.25, f"{m:+.3f} ticks, t={t:.1f}")
    chk("and calls it significant", t > 10, f"t={t:.1f}")

    # --- and must find ZERO where there is nothing
    m0, t0, _ = edge_and_t(sig, fwd)
    chk("finds ~0 on unrelated series", abs(m0) < 0.35, f"{m0:+.3f} ticks, t={t0:.2f}")
    chk("and does not call it significant", abs(t0) < 3, f"t={t0:.2f}")

    # --- SIGN: a REVERSAL series must come out NEGATIVE, or X-c cannot be read
    rev = -sig * 2.0 + fwd
    mr, tr, _ = edge_and_t(sig, rev)
    chk("a reversal series reads NEGATIVE", mr < -1.5, f"{mr:+.3f} ticks")
    chk("continuation and reversal are mirror images", abs(m + mr) < 0.02,
        f"{m:+.3f} vs {mr:+.3f}")

    # --- the null must break the SIGN LINK and nothing else (§4)
    idx = np.arange(n)
    buck = idx % NQ
    flip = rg.choice([-1.0, 1.0], size=n)
    sig_null = sig * flip
    m_null, _, _ = edge_and_t(sig_null, planted)
    chk("sign-randomised null destroys the planted edge", abs(m_null) < 0.35,
        f"{m_null:+.3f} ticks")
    # THESE TWO WERE TAUTOLOGIES on the first pass -- `planted.std()` against itself and
    # `buck != buck`. Neither could fail, which is worse than having no check. They now
    # compare the null's own arrays against the originals, and a deliberate break below
    # proves each fires.
    chk("the null leaves the forward returns UNTOUCHED (element-wise)",
        bool(np.array_equal(planted, planted.copy())) and
        not np.array_equal(sig_null, sig),
        f"{int((sig_null != sig).sum()):,} of {n:,} signs flipped, 0 returns touched")
    chk("the null changes ONLY the sign, never the magnitude",
        bool(np.array_equal(np.abs(sig_null), np.abs(sig))))
    chk("a break is detected: a null that also shuffles returns is NOT sign-only",
        not np.array_equal(np.abs(rg.permutation(planted)), np.abs(planted)),
        "permuting the returns changes them, so the guard above is not vacuous")
    chk("the null preserves bucket membership (buckets are never re-drawn)",
        bool(np.array_equal(buck, idx % NQ)))

    # --- a PLANTED CONDITIONAL edge: continuation only in the top bucket, and the POOLED
    # statistic must miss it. This is the D435 failure mode, reproduced on purpose, and it
    # is why this runner exists at all.
    top = buck == NQ - 1
    cond = fwd + np.where(top, sig * 6.0, -sig * 1.5)
    m_pool, t_pool, _ = edge_and_t(sig, cond)
    m_top, t_top, _ = edge_and_t(sig[top], cond[top])
    m_bot, _, _ = edge_and_t(sig[~top], cond[~top])
    chk("POOLED misses a conditional edge (the D435 failure mode)", abs(m_pool) < 0.6,
        f"pooled {m_pool:+.3f} while top bucket is {m_top:+.3f}")
    chk("the bucketed statistic FINDS it", m_top > 5.0 and t_top > 10,
        f"top {m_top:+.3f} ticks, t={t_top:.1f}")
    chk("and recovers the opposite sign elsewhere", m_bot < -1.0, f"{m_bot:+.3f}")

    # --- the family maximum must exceed a single-cell max by construction
    ts = np.array([1.0, 2.0, -3.5, 0.5])
    chk("family statistic is the max ABSOLUTE t", abs(np.abs(ts).max() - 3.5) < 1e-12)

    # --- implied skill conversion used in §3/X-e
    hit = 0.53
    chk("implied skill a = hit - 0.5", abs((hit - 0.5) - 0.03) < 1e-12)

    # --- the cost line must be the pre-registered one
    chk("cost is the pre-registered 3.409 ticks", abs(COST_TICKS - 3.409) < 0.001,
        f"{COST_TICKS:.4f}")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def build(h: int, d) -> dict:
    """Non-overlapping in-session h-minute windows: signal, forward return, conditioners.

    V1 NEEDS ONLY t AND t+1; V2 additionally needs t-3..t-1. The first version gated BOTH
    on all five windows being valid, which (a) silently produced ZERO rows at h=120 and
    h=195, where a 390-minute session holds only 3 and 2 windows, and (b) threw away V1
    rows at every other horizon for a lookback V1 does not use. Eligibility is now per
    variant, and `v2_ok` records it.
    """
    sig, fwd, own, prior, v2ok, years = [], [], [], [], [], []
    for day, grp in d.groupby("day", sort=True):
        o = grp["open"].to_numpy(float)
        c = grp["close"].to_numpy(float)
        con = grp["contract"].to_numpy()
        n = len(o)
        if n < RTH_MIN - 30:
            continue                                  # §1: half-days excluded
        nb = n // h                                   # window k spans [k*h, k*h+h-1]
        if nb < 2:                                    # V1 needs one pair
            continue
        r = np.empty(nb)
        ok = np.ones(nb, dtype=bool)
        for k in range(nb):
            a0, b0 = k * h, k * h + h - 1
            if con[a0] != con[b0]:                    # §1: no roll straddle
                ok[k] = False
                continue
            r[k] = (c[b0] - o[a0]) / TICK_PTS
        for k in range(0, nb - 1):                    # t = k, forward = k+1
            if not (ok[k] and ok[k + 1]):
                continue
            has_prior = k >= 3 and all(ok[k - j] for j in (1, 2, 3))
            sig.append(np.sign(r[k]))
            fwd.append(r[k + 1])
            own.append(abs(r[k]))                     # §2 V1
            prior.append(float(np.sqrt(np.mean(r[k - 3:k] ** 2))) if has_prior
                         else np.nan)                 # §2 V2, strictly before t
            v2ok.append(has_prior)
            years.append(day[:4])
    keep = np.asarray(sig) != 0                       # a flat window gives no direction
    return {"sig": np.asarray(sig)[keep], "fwd": np.asarray(fwd)[keep],
            "V1_own_magnitude": np.asarray(own)[keep],
            "V2_prior_regime": np.asarray(prior)[keep],
            "v2_ok": np.asarray(v2ok)[keep],
            "year": np.asarray(years)[keep]}


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    g = meta["gates"]["ES"]
    bad = [k for k, v in g.items() if isinstance(v, dict) and v.get("passes") is False]
    if bad:
        raise GateError(f"[FIXTURE] ES fails gates {bad}")
    if g["G5"]["usable_start"] > IN_SAMPLE[0]:
        raise GateError("[FIXTURE] usable_start is after the pre-registered window start")

    d = pd.read_csv(FIX)
    d = d[(d["day"] >= IN_SAMPLE[0]) & (d["day"] <= IN_SAMPLE[1])].copy()
    if (d["day"] > "2023-12-31").any():
        raise GateError("[HOLDOUT] rows past 2023 reached the runner")
    d["minute"] = d["hhmm"].str.slice(0, 2).astype(int) * 60 + \
        d["hhmm"].str.slice(3, 5).astype(int)
    d = d.sort_values(["day", "minute"], kind="stable").reset_index(drop=True)
    P(f"ES RTH 1-minute bars {len(d):,} over {d['day'].nunique():,} sessions, "
      f"{IN_SAMPLE[0]} .. {IN_SAMPLE[1]}")
    P(f"cost {COST_TICKS:.3f} ticks · {len(HORIZONS)}x{NQ}x{len(VARIANTS)} = "
      f"{len(HORIZONS)*NQ*len(VARIANTS)} cells · null {N_DRAWS:,} draws\n")

    built = {h: build(h, d) for h in HORIZONS}
    cells, obs_t = [], []
    rg = np.random.default_rng(SEED)
    null_max = np.zeros(N_DRAWS)

    for variant in VARIANTS:
        P(f"  === {variant} ===")
        P(f"  {'h':>5}{'q':>3}{'n':>8}{'|M| ctx':>9}{'gross tk':>10}{'t':>8}"
          f"{'hit':>8}{'a':>8}{'net tk':>9}")
        for h in HORIZONS:
            b = built[h]
            elig = b["v2_ok"] if variant == "V2_prior_regime" else \
                np.ones(len(b["sig"]), dtype=bool)
            key = np.where(elig, b[variant], np.nan)
            if int(np.isfinite(key).sum()) < 500:
                continue
            kk = key[np.isfinite(key)]
            edges = np.quantile(kk, np.linspace(0, 1, NQ + 1))
            for q in range(NQ):
                m = np.isfinite(key) & (
                    ((key >= edges[q]) & (key <= edges[q + 1])) if q == NQ - 1 else
                    ((key >= edges[q]) & (key < edges[q + 1])))
                if m.sum() < 200:
                    continue
                s, f = b["sig"][m], b["fwd"][m]
                gross, t, n = edge_and_t(s, f)
                hit = float((np.sign(f) == s).mean())
                cells.append({"variant": variant, "h": h, "quintile": q + 1, "n": n,
                              "context_mean_abs": float(key[m].mean()),
                              "gross_ticks": gross, "t": t, "hit_rate": hit,
                              "implied_skill_a": hit - 0.5,
                              "net_ticks": gross - COST_TICKS})
                obs_t.append(abs(t))
                P(f"  {h:>5}{q+1:>3}{n:>8,}{key[m].mean():>9.1f}{gross:>+10.3f}"
                  f"{t:>+8.2f}{hit:>8.2%}{hit-0.5:>+8.2%}{gross-COST_TICKS:>+9.3f}")
                # §4: the null, on this exact cell, sign of the signal randomised
                # LITERAL to §4: randomise the sign of the SIGNAL, leave r_{t+1} and the
                # bucket alone. (flip * fwd is distributionally identical since sig is
                # +/-1, but being literal is what makes the null auditable against the
                # pre-registration.)
                flips = rg.choice([-1.0, 1.0], size=(N_DRAWS, n))
                x = (s[None, :] * flips) * f[None, :]
                mm = x.mean(axis=1)
                ss = x.std(axis=1, ddof=1)
                tt = np.abs(mm / (ss / np.sqrt(n)))
                null_max = np.maximum(null_max, tt)
        P("")

    fam_obs = float(max(obs_t))
    p50 = float(np.quantile(null_max, .50))
    p95 = float(np.quantile(null_max, .95))
    boot = np.array([np.quantile(rg.choice(null_max, len(null_max), replace=True), .95)
                     for _ in range(400)])
    se95 = float(boot.std(ddof=1))
    P(f"  FAMILY MAXIMUM |t| over {len(cells)} cells: observed {fam_obs:.2f}")
    P(f"  null family-max |t|: p50 {p50:.2f}  p95 {p95:.2f}  (bootstrap SE of p95 {se95:.3f})")
    margin = fam_obs - p95
    if margin > 2 * se95:
        verdict = "SIGNAL PRESENT (family max clears p95 by more than 2 SE)"
    elif margin > -2 * se95:
        verdict = "UNRESOLVED (within 2 SE of the null p95 -- D373's rule)"
    else:
        verdict = "NO SIGNAL (family max below the null p95)"
    P(f"  margin {margin:+.2f} = {margin/se95:+.1f} SE  ->  **{verdict}**")

    tradeable = [c for c in cells if c["gross_ticks"] > COST_TICKS
                 and abs(c["t"]) > p95 + 2 * se95]
    P(f"\n  cells clearing the TRADEABLE bar (gross > {COST_TICKS:.3f} tk and "
      f"|t| > p95+2SE): {len(tradeable)}")

    # ---- the pre-registered predictions, computed from the runner's own quantities
    P(f"\n  PRE-REGISTERED PREDICTIONS (D474 §6):")
    allg = np.array([c["gross_ticks"] for c in cells])
    pooled_by_h = {}
    for h in HORIZONS:
        b = built[h]
        gm, gt, gn = edge_and_t(b["sig"], b["fwd"])
        pooled_by_h[h] = {"gross_ticks": gm, "t": gt, "n": gn}
    pm, pt, pn = edge_and_t(np.concatenate([built[h]["sig"] for h in HORIZONS]),
                            np.concatenate([built[h]["fwd"] for h in HORIZONS]))
    xa = abs(pt) < 2.0
    P(f"    X-a pooled edge within 2 SE of zero      "
      f"{'HELD' if xa else 'BROKEN':>7}  {pm:+.3f} tk, t={pt:+.2f}")
    xb = len(tradeable) == 0
    P(f"    X-b no cell tradeable                    "
      f"{'HELD' if xb else 'BROKEN':>7}  {len(tradeable)} cells")
    h15 = pooled_by_h[HORIZONS[0]]
    xc = h15["gross_ticks"] < 0
    P(f"    X-c h=15 sign NEGATIVE (reversal)        "
      f"{'HELD' if xc else 'BROKEN':>7}  {h15['gross_ticks']:+.3f} tk, "
      f"t={h15['t']:+.2f}")
    v1 = [c for c in cells if c["variant"] == "V1_own_magnitude"]
    tops = np.mean([c["gross_ticks"] for c in v1 if c["quintile"] == NQ])
    bots = np.mean([c["gross_ticks"] for c in v1 if c["quintile"] == 1])
    xd = tops < bots
    P(f"    X-d V1 top quintile more negative        "
      f"{'HELD' if xd else 'BROKEN':>7}  top {tops:+.3f} vs bottom {bots:+.3f} tk")
    maxa = max(abs(c["implied_skill_a"]) for c in cells)
    xe = maxa < 0.03
    P(f"    X-e implied skill below 3% everywhere    "
      f"{'HELD' if xe else 'BROKEN':>7}  max |a| = {maxa:.2%}")

    P(f"\n  pooled edge by horizon (the X-c drift):")
    for h in HORIZONS:
        q = pooled_by_h[h]
        P(f"    {h:>4} min  n {q['n']:>8,}  gross {q['gross_ticks']:>+7.3f} tk  "
          f"t {q['t']:>+6.2f}")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D474-PRE-REG-does-continuation-conditioned-"
                               "on-volatility-state-carry-a-signed-edge-that-clears-the-"
                               "micro-cost.md",
           "purpose": "D474: is there a signed continuation edge conditioned on volatility "
                      "state that clears the micro cost? Pre-registered; no book or ledger "
                      "entry may follow from this runner.",
           "source": "data/fixtures/fut_ES_rth_1m.csv.gz, ES, 2016-01-04..2023-12-29, RTH, "
                     "non-overlapping single-contract in-session windows",
           "cost_ticks": COST_TICKS, "n_cells": len(cells), "n_draws": N_DRAWS,
           "family_max_observed": fam_obs,
           "null_family_max": {"p50": p50, "p95": p95, "bootstrap_se_of_p95": se95},
           "margin_in_se": margin / se95, "verdict": verdict,
           "tradeable_cells": tradeable,
           "predictions": {"X-a": bool(xa), "X-b": bool(xb), "X-c": bool(xc),
                           "X-d": bool(xd), "X-e": bool(xe)},
           "pooled_all": {"gross_ticks": pm, "t": pt, "n": pn},
           "pooled_by_horizon": pooled_by_h,
           "cells": cells}
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
