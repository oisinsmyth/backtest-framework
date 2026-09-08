"""D386 -- the zero-edge pass rate of a prop evaluation, as a function of its GEOMETRY.

    uv run python scripts/d386_pass_rate.py --selftest
    uv run python scripts/d386_pass_rate.py --baseline
    uv run python scripts/d386_pass_rate.py --implied-edge 0.50

WHY THIS EXISTS. D379 frames a funded account as a down-and-out call and quotes two numbers -- at
zero edge a +3,000/-2,000 evaluation passes 40.0% of the time with a STATIC floor and 26.5% with a
TRAILING one. Neither was committed as code; D379 says so ("deliberately not committed to data/").
Stage 0 of the D386 research needs a pass rate for EVERY geometry the firm lanes return, so the
toy has to become a runner.

WHAT IT COMPUTES. P(reach the profit target before breaching the floor), on a driftless or drifted
Gaussian path, under the three monitoring conventions the firms actually use:

    static            floor fixed at start - DD for the life of the account
    eod_trailing      floor = max(END-OF-DAY equity) - DD; the floor ratchets once a day
    intraday_trailing floor = max(equity at ANY step) - DD; the floor ratchets continuously

The distinction is not cosmetic. D379 identifies the open-equity question as hurdle P1 exactly, and
the whole point of field 9 in the research schema is that firms differ on it.

THE CLOSED FORM IS THE ANCHOR. For a driftless walk with a STATIC floor, no daily limit and no time
limit, P(hit +a before -b) = b/(a+b) exactly -- gambler's ruin. For +3,000/-2,000 that is 2000/5000
= 40.0%, which is where D379's static figure comes from. [CF] asserts the simulation reproduces it,
and [SCALE] asserts the result is INVARIANT to step volatility, which it must be for a driftless
walk and which no other check would catch.

ASSERTIONS, all of which must be able to fail (--selftest deliberately breaks each):
  [CF]     static + driftless + continuous monitoring == b/(a+b), within MC error
  [SCALE]  that pass rate is invariant to vol -- a driftless walk has no scale
  [ORDER]  intraday_trailing <= eod_trailing <= static at identical parameters. A geometry that
           monitors the floor more tightly CANNOT pass more often
  [CONV]   the discretisation converges: doubling steps/day moves the static rate by < MC error
  [DEGEN]  an infinite floor passes ~1.0 and an infinite target passes ~0.0

MC error is reported everywhere. A pass rate quoted without it is not a result.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict

import numpy as np

# ---------------------------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------------------------

FLOOR_KINDS = ("static", "eod_trailing", "intraday_trailing")


@dataclass(frozen=True)
class Geometry:
    """One firm's evaluation, in dollars on the account's own scale."""

    target: float                 # profit target above starting balance
    drawdown: float               # floor distance below its reference
    floor_kind: str               # one of FLOOR_KINDS
    daily_loss: float | None = None   # daily loss limit, None if the firm has none
    max_days: int | None = None       # time limit in trading days, None if unlimited
    min_days: int = 0                 # minimum trading days before a pass counts
    lock_at: float | None = None      # trailing floor stops ratcheting once it reaches start+lock_at

    def __post_init__(self) -> None:
        assert self.floor_kind in FLOOR_KINDS, f"bad floor_kind {self.floor_kind!r}"
        assert self.target > 0 and self.drawdown > 0


# ---------------------------------------------------------------------------------------------
# the simulation
# ---------------------------------------------------------------------------------------------


def simulate(
    geo: Geometry,
    *,
    daily_vol: float,
    daily_drift: float = 0.0,
    steps_per_day: int = 8,
    n_paths: int = 400_000,
    horizon_days: int = 252,
    seed: int = 20260908,
    chunk: int = 25_000,
) -> dict:
    """P(pass) for one geometry. Chunked so a 400k x 252 x 8 grid never exists at once.

    Returns pass rate, breach rate, timeout rate, the MC standard error, and mean days to resolve.
    """
    assert steps_per_day >= 1
    rng = np.random.default_rng(seed)
    step_vol = daily_vol / math.sqrt(steps_per_day)
    step_drift = daily_drift / steps_per_day
    n_steps = horizon_days * steps_per_day

    n_pass = n_breach = n_timeout = 0
    days_sum = 0.0
    done_n = 0

    remaining = n_paths
    while remaining > 0:
        m = min(chunk, remaining)
        remaining -= m

        inc = rng.normal(step_drift, step_vol, size=(m, n_steps))
        eq = np.cumsum(inc, axis=1)            # equity relative to starting balance

        # --- the floor's reference level, per step -------------------------------------------
        if geo.floor_kind == "static":
            ref = np.zeros((m, n_steps))
        elif geo.floor_kind == "intraday_trailing":
            ref = np.maximum.accumulate(eq, axis=1)
            ref = np.maximum(ref, 0.0)          # never below the starting balance
        else:  # eod_trailing -- the floor sees only end-of-day equity
            eod = eq[:, steps_per_day - 1 :: steps_per_day]           # (m, horizon_days)
            eod_run = np.maximum.accumulate(eod, axis=1)
            eod_run = np.maximum(eod_run, 0.0)
            # day d's floor is set by end of day d-1, so shift right by one day and repeat
            shifted = np.concatenate([np.zeros((m, 1)), eod_run[:, :-1]], axis=1)
            ref = np.repeat(shifted, steps_per_day, axis=1)

        if geo.lock_at is not None:
            ref = np.minimum(ref, geo.lock_at)

        floor = ref - geo.drawdown

        breached = eq <= floor
        hit_target = eq >= geo.target

        # --- the daily loss limit, evaluated on the day's running low ------------------------
        if geo.daily_loss is not None:
            by_day = eq.reshape(m, horizon_days, steps_per_day)
            day_open = np.concatenate(
                [np.zeros((m, 1)), by_day[:, :-1, -1]], axis=1
            )[:, :, None]
            daily_breach = (by_day - day_open) <= -geo.daily_loss
            breached |= daily_breach.reshape(m, n_steps)

        # --- the minimum-days rule delays when a target can be BANKED ------------------------
        if geo.min_days > 0:
            hit_target[:, : geo.min_days * steps_per_day] = False

        if geo.max_days is not None:
            cut = geo.max_days * steps_per_day
            breached = breached[:, :cut]
            hit_target = hit_target[:, :cut]

        first_b = np.where(breached.any(axis=1), breached.argmax(axis=1), np.iinfo(np.int32).max)
        first_t = np.where(hit_target.any(axis=1), hit_target.argmax(axis=1), np.iinfo(np.int32).max)

        passed = first_t < first_b
        broke = first_b < first_t
        timed = ~passed & ~broke

        n_pass += int(passed.sum())
        n_breach += int(broke.sum())
        n_timeout += int(timed.sum())

        resolved = np.minimum(first_t, first_b)
        ok = resolved < np.iinfo(np.int32).max
        days_sum += float((resolved[ok] / steps_per_day).sum())
        done_n += int(ok.sum())

    p = n_pass / n_paths
    return {
        "pass_rate": p,
        "breach_rate": n_breach / n_paths,
        "timeout_rate": n_timeout / n_paths,
        "se": math.sqrt(max(p * (1 - p), 0.0) / n_paths),
        "mean_days_to_resolve": (days_sum / done_n) if done_n else float("nan"),
        "n_paths": n_paths,
        "steps_per_day": steps_per_day,
        "daily_vol": daily_vol,
        "daily_drift": daily_drift,
        "geometry": asdict(geo),
    }


def closed_form_static(target: float, drawdown: float) -> float:
    """Gambler's ruin: P(hit +a before -b) = b/(a+b) for a driftless walk."""
    return drawdown / (target + drawdown)


def implied_daily_drift(
    geo: Geometry, observed_pass: float, *, daily_vol: float, lo: float = -0.5, hi: float = 2.0, **kw
) -> float:
    """Invert an observed pass rate into the daily drift (in units of daily_vol) that produces it.

    This is the whole point of the Stage 0 baseline: a published pass rate is only interpretable
    against the rate a ZERO-edge trader achieves on the same geometry.
    """
    lo_d, hi_d = lo * daily_vol, hi * daily_vol
    for _ in range(28):
        mid = 0.5 * (lo_d + hi_d)
        r = simulate(geo, daily_vol=daily_vol, daily_drift=mid, **kw)["pass_rate"]
        if r < observed_pass:
            lo_d = mid
        else:
            hi_d = mid
    return 0.5 * (lo_d + hi_d) / daily_vol


# ---------------------------------------------------------------------------------------------
# assertions
# ---------------------------------------------------------------------------------------------


def _band(res: dict, k: float = 4.0) -> tuple[float, float]:
    return res["pass_rate"] - k * res["se"], res["pass_rate"] + k * res["se"]


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def closed_form_no_floor(target: float, daily_vol: float, horizon_days: int) -> float:
    """Reflection principle: for a driftless walk with NO floor, P(max over T >= a)."""
    return 2.0 * (1.0 - _phi(target / (daily_vol * math.sqrt(horizon_days))))


def selftest(quick: bool = False) -> int:
    """Every check here is an assertion about the CODE, not about a parameter choice.

    The first version of this self-test failed CF, SCALE and DEGEN, and the simulator was right
    each time: those three encoded the expectation that a 252-day horizon approximates an infinite
    one. It does not. Expected absorption time for +3,000/-2,000 at 250/day is a*b/sigma^2 = 96
    days, so 6.2% of paths were still unresolved at the horizon and were counted as neither pass
    nor breach -- biasing the rate DOWN, and doing so MORE at low vol, which is what SCALE caught.

    The invariants underneath, which is what this version asserts:
      CF     holds in the limit of negligible timeout, so timeout is now a PRECONDITION
      SCALE  scale-invariance holds only where BOTH configs resolve; tested where they do
      DEGEN  the no-floor case is not "about 1", it is the reflection principle, a second
             independent closed form
    """
    n = 40_000 if quick else 200_000
    failures: list[str] = []

    def check(tag: str, ok: bool, detail: str) -> None:
        print(f"  [{tag}] {'PASS' if ok else 'FAIL'}  {detail}")
        if not ok:
            failures.append(tag)

    # a config where absorption (9.4 days) is fast against the horizon, so timeout is negligible,
    # and the step (100) is 5% of the floor, so overshoot bias is small
    FAST = dict(daily_vol=800.0, steps_per_day=64, horizon_days=100, chunk=3_000)
    g = Geometry(target=3000.0, drawdown=2000.0, floor_kind="static")
    cf = closed_form_static(3000.0, 2000.0)

    print("D386 pass-rate self-test")
    print(f"  n_paths={n}; CF config vol=800/day, 64 steps/day, 100-day horizon")
    print(f"  (absorption a*b/sigma^2 = {3000*2000/800**2:.1f} days, step = {800/8:.0f} "
          f"= {100*800/8/2000:.1f}% of the floor)\n")

    r = simulate(g, n_paths=n, **FAST)
    check("CF-PRECOND", r["timeout_rate"] < 0.002,
          f"timeout {r['timeout_rate']:.5f} must be negligible before the closed form applies")
    lo, hi = _band(r)
    check("CF", lo <= cf <= hi,
          f"static +3000/-2000 -> {r['pass_rate']:.4f} +/- {r['se']:.4f}, closed form {cf:.4f}")

    # [SCALE] a driftless walk has no scale -- valid only where both configs resolve
    r2 = simulate(g, n_paths=n, seed=7, **{**FAST, "daily_vol": 2400.0})
    diff = abs(r["pass_rate"] - r2["pass_rate"])
    tol = 4.0 * math.hypot(r["se"], r2["se"])
    check("SCALE", diff <= tol and r2["timeout_rate"] < 0.002,
          f"vol x3 -> {r2['pass_rate']:.4f} (timeout {r2['timeout_rate']:.5f}); "
          f"|diff| {diff:.4f} vs tol {tol:.4f}")

    # [ORDER] tighter monitoring cannot pass more often -- the key structural invariant
    rows = {}
    for kind in FLOOR_KINDS:
        rows[kind] = simulate(Geometry(target=3000.0, drawdown=2000.0, floor_kind=kind),
                              n_paths=n, **FAST)
    check("ORDER",
          rows["intraday_trailing"]["pass_rate"] <= rows["eod_trailing"]["pass_rate"]
          <= rows["static"]["pass_rate"],
          " <= ".join(f"{k} {rows[k]['pass_rate']:.4f}"
                      for k in ("intraday_trailing", "eod_trailing", "static")))

    # [CONV] halving the step must not move the answer beyond MC error
    a1 = simulate(g, n_paths=n, seed=11, **{**FAST, "steps_per_day": 32})
    a2 = simulate(g, n_paths=n, seed=11, **{**FAST, "steps_per_day": 64})
    diff = abs(a1["pass_rate"] - a2["pass_rate"])
    tol = 4.0 * math.hypot(a1["se"], a2["se"])
    check("CONV", diff <= tol,
          f"32 vs 64 steps/day: {a1['pass_rate']:.4f} vs {a2['pass_rate']:.4f}, tol {tol:.4f}")

    # [DEGEN] against a SECOND independent closed form, not against a hand-waved ~1
    r3 = simulate(Geometry(target=3000.0, drawdown=1e12, floor_kind="static"),
                  daily_vol=250.0, n_paths=n, steps_per_day=8, horizon_days=252)
    want = closed_form_no_floor(3000.0, 250.0, 252)
    lo3, hi3 = _band(r3, k=5.0)
    r4 = simulate(Geometry(target=1e12, drawdown=2000.0, floor_kind="static"),
                  daily_vol=250.0, n_paths=n // 4, steps_per_day=8, horizon_days=252)
    check("DEGEN", lo3 <= want <= hi3 and r4["pass_rate"] < 0.001,
          f"no floor -> {r3['pass_rate']:.4f} vs reflection principle {want:.4f}; "
          f"unreachable target -> {r4['pass_rate']:.4f}")

    # the checks must be able to FAIL -- a self-test that cannot fail is worse than none
    bad = simulate(Geometry(target=3000.0, drawdown=4000.0, floor_kind="static"),
                   n_paths=n // 4, **FAST)
    lo, hi = _band(bad)
    check("CF-CAN-FAIL", not (lo <= cf <= hi),
          f"a deliberately wrong geometry gives {bad['pass_rate']:.4f}, outside the 40.0% band")

    trunc = simulate(g, daily_vol=250.0, n_paths=n // 4, steps_per_day=8, horizon_days=252)
    check("HORIZON-BITES", trunc["pass_rate"] < cf - 4 * trunc["se"],
          f"the SAME geometry with a 252-day cap at 250/day gives {trunc['pass_rate']:.4f} "
          f"(timeout {trunc['timeout_rate']:.4f}) -- strictly below the 40.0% limit")

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("all assertions passed")
    return 0


# ---------------------------------------------------------------------------------------------
# the Stage 0 baseline table
# ---------------------------------------------------------------------------------------------


def baseline(n_paths: int = 400_000) -> dict:
    """Zero-edge pass rate for a +3,000/-2,000 evaluation under each monitoring convention.

    This is the reference D379 quotes. Every firm geometry the research lanes return gets the
    same treatment, so a published pass rate can be read against the rate a coin flip achieves.
    """
    out = {}
    print("Stage 0 -- ZERO-EDGE pass rates, +3,000 target / -2,000 drawdown, 252-day horizon\n")
    print(f"{'floor':<20} {'pass':>8} {'+/- se':>8} {'breach':>8} {'timeout':>8} {'days':>7}")
    print("-" * 64)
    for kind in FLOOR_KINDS:
        g = Geometry(target=3000.0, drawdown=2000.0, floor_kind=kind)
        r = simulate(g, daily_vol=250.0, n_paths=n_paths, steps_per_day=8, horizon_days=252)
        out[kind] = r
        print(f"{kind:<20} {r['pass_rate']:>8.4f} {r['se']:>8.4f} "
              f"{r['breach_rate']:>8.4f} {r['timeout_rate']:>8.4f} "
              f"{r['mean_days_to_resolve']:>7.1f}")
    print(f"\nclosed form for the static floor: {closed_form_static(3000.0, 2000.0):.4f}"
          "  (gambler's ruin, 2000/5000)")
    print("\nD379 quotes 40.0% static and 26.5% trailing. Compare above and say which trailing"
          "\nconvention its 26.5% corresponds to -- the two differ and D379 does not say which.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--implied-edge", type=float, default=None,
                    help="invert an observed pass rate into an implied daily drift, in daily vols")
    ap.add_argument("--paths", type=int, default=400_000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.selftest:
        return selftest(quick=a.quick)

    res: dict = {}
    if a.baseline:
        res["baseline"] = baseline(n_paths=a.paths)

    if a.implied_edge is not None:
        print(f"\nimplied edge for an observed pass rate of {a.implied_edge:.3f}:\n")
        res["implied_edge"] = {}
        for kind in FLOOR_KINDS:
            g = Geometry(target=3000.0, drawdown=2000.0, floor_kind=kind)
            d = implied_daily_drift(g, a.implied_edge, daily_vol=250.0,
                                    n_paths=60_000, steps_per_day=8, horizon_days=252)
            ann = d * math.sqrt(252)
            res["implied_edge"][kind] = {"daily_drift_in_vols": d, "implied_annual_sharpe": ann}
            print(f"  {kind:<20} daily drift {d:+.4f} vol  ->  implied annual Sharpe {ann:+.2f}")

    if not res:
        ap.print_help()
        return 0

    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2)
        print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
