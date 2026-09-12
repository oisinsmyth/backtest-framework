"""D473 -- what horizon the micro cost structure wants, given a stated level of skill.

    uv run python scripts/d473_optimal_horizon.py --self-test
    uv run python scripts/d473_optimal_horizon.py --measure [--json]

**A COST-GEOMETRY CALCULATION, NOT A STUDY.** It contains no entry rule, no signal, no
forecast and no backtest. It asks a conditional question -- *IF* a rule had directional
accuracy `a` above a coin flip, what holding period would maximise its Sharpe, and what Sharpe
would that be -- using E|M| measured on the in-sample window. Nothing is opened, closed or
admitted (R15). **No rule may be scored off this without a pre-registration (R8).**

WHY THIS IS THE QUESTION
------------------------
[D472](../docs/decisions/D472-RESULT-the-volume-clock-exit-replicates-8-of-8-years-but-the-15-minute-horizon-does-not-survive-its-own-scoring-window.md)
put the 15-minute in-sample breakeven at **61.4%**. That invites "so find a 62%-accurate
signal", which is the wrong response, because **the horizon is a free parameter and it trades
off against itself**:

* cost is **fixed per round trip** (3.41 MES ticks), so a longer hold amortises it -- breakeven
  accuracy falls toward 50%;
* but a longer hold means **fewer trades**, and Sharpe scales with sqrt(count).

[CLAUDE.md](../CLAUDE.md) states the trap outright: *"Cost-cutting is not edge-sharpening. A
longer hold lifts breakeven by amortising one round trip; per-bar edge usually FALLS, so Sharpe
can drop as cost coverage rises."* So the two effects must be resolved together, not argued
about.

THE ARITHMETIC, WHICH HAS A CLEAN ANSWER
----------------------------------------
Write `a = p - 1/2` for raw directional skill, `E|M|(h) = k*sqrt(h)` for the mean absolute move
(the sqrt is MEASURED -- D469 fitted h^0.50 -- not assumed), `N(h) ∝ 1/h` for trades a day, and
`C` for cost. Per-trade mean is `2a*E|M| - C`, and Sharpe ∝ sqrt(N) * mean / sd, giving

    Sharpe(h) ∝ a/sqrt(h) - C/(2k*h)

Setting the derivative to zero:

    sqrt(h*) = C / (a*k)     i.e.     **E|M|(h*) = C / a**

and substituting back, `p_be(h*) = 1/2 + a/2`. **The optimal horizon is the one where the mean
absolute move equals cost divided by skill -- equivalently, where you are running at exactly
TWICE the breakeven excess.** Both are checked against a numerical argmax of the exact
(non-asymptotic) Sharpe in `--self-test`.

The consequence is the point of the file: **for any plausible skill level the optimum is hours,
not minutes.** 15 minutes is optimal only for a rule with roughly ten percentage points of
directional edge, which nothing in this repo has ever demonstrated.
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
OUT = REPO / "data" / "d473_optimal_horizon.json"

TICK_PTS = 0.25
COST_TICKS = 1.009 + 3.00 / 1.25          # D465 crossing + D466 commission, at micro size
IN_SAMPLE = ("2016-01-04", "2023-12-29")
RTH_MIN = 390
HORIZONS_MIN = (5, 15, 30, 60, 120, 195, 390)
SKILLS = (0.01, 0.02, 0.03, 0.05, 0.075, 0.10)


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


def sharpe_of(q: float, cost: float, rms: float, n_year: float) -> float:
    """Exact annualised Sharpe for a +/-|M| outcome. q is the GROSS signed mean."""
    var = rms * rms - q * q
    if var <= 0:
        return float("inf") if q > cost else float("-inf")
    return float(np.sqrt(n_year) * (q - cost) / np.sqrt(var))


def sharpe_at(a: float, e_abs: float, rms: float, n_year: float, cost: float) -> float:
    return sharpe_of(2.0 * a * e_abs, cost, rms, n_year)


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:62} {detail}")
        if not cond:
            fails.append(label)

    # A synthetic market with EXACT sqrt scaling, so the closed form has a right answer.
    k = 4.0                       # ticks per sqrt(minute)
    cost = 3.409
    rms_over_eabs = 1.49          # measured on ES; held fixed so the test isolates horizon

    def e_abs(h):
        return k * np.sqrt(h)

    def n_year(h):
        return (RTH_MIN / h) * 252.0

    # the closed form: E|M|(h*) = cost / a  ->  h* = (cost/(a*k))^2
    for a in (0.02, 0.05, 0.10):
        h_closed = (cost / (a * k)) ** 2
        grid = np.geomspace(0.5, 5000, 20000)
        vals = [sharpe_at(a, e_abs(h), rms_over_eabs * e_abs(h), n_year(h), cost)
                for h in grid]
        h_num = float(grid[int(np.argmax(vals))])
        chk(f"closed form matches the numerical argmax at a={a:.0%}",
            abs(h_num - h_closed) / h_closed < 0.02,
            f"closed {h_closed:>8.1f} min vs numerical {h_num:>8.1f} min")
        # and at the optimum, E|M| must equal cost/a
        chk(f"E|M| at the optimum equals cost/a at a={a:.0%}",
            abs(e_abs(h_closed) - cost / a) / (cost / a) < 1e-9,
            f"{e_abs(h_closed):.2f} vs {cost/a:.2f} ticks")
        # and breakeven there must be 1/2 + a/2, i.e. skill is TWICE the excess
        p_be = 0.5 + cost / (2 * e_abs(h_closed))
        chk(f"p_be at the optimum is 0.5 + a/2 at a={a:.0%}",
            abs(p_be - (0.5 + a / 2)) < 1e-9, f"{p_be:.4f} vs {0.5 + a/2:.4f}")

    # MONOTONICITY THE OTHER WAY, which is the trap CLAUDE.md names: a longer hold always
    # lowers breakeven accuracy, and that alone is NOT an improvement.
    chk("a longer hold always lowers breakeven accuracy",
        all((0.5 + cost / (2 * e_abs(h))) > (0.5 + cost / (2 * e_abs(2 * h)))
            for h in (15, 60, 240)))
    # ... while Sharpe at FIXED skill is NOT monotone in h -- it has an interior maximum
    a = 0.03
    s = [sharpe_at(a, e_abs(h), rms_over_eabs * e_abs(h), n_year(h), cost)
         for h in (5, 15, 60, 240, 1000, 4000)]
    chk("Sharpe at fixed skill RISES then FALLS in h (an interior optimum exists)",
        s[0] < s[2] and s[-1] < s[-2], f"{[round(x, 2) for x in s]}")
    chk("below breakeven the Sharpe is negative", sharpe_at(0.0, 10.0, 15.0, 6552.0, cost) < 0)

    # THE FOLK ANSWER, DISPOSED OF: "let winners run, cut losers short" -- an asymmetric
    # W/L bracket. On a driftless walk the hit probability adjusts EXACTLY to offset the
    # payoff: P(hit +W before -L) = L/(W+L), so expected gross is identically zero for
    # every bracket. Skew buys nothing for free; only the SUM W+L helps, and only through
    # the same fixed-cost channel as a longer horizon.
    rgb = np.random.default_rng(473)
    for W, L in ((10.0, 10.0), (30.0, 10.0), (5.0, 20.0)):
        steps = rgb.choice([-1.0, 1.0], size=(40_000, 4000))
        pathm = np.cumsum(steps, axis=1)
        hitW = np.argmax(pathm >= W, axis=1)
        hitL = np.argmax(pathm <= -L, axis=1)
        hitW = np.where(pathm.max(axis=1) >= W, hitW, 1 << 30)
        hitL = np.where(pathm.min(axis=1) <= -L, hitL, 1 << 30)
        decided = np.minimum(hitW, hitL) < (1 << 30)
        p_win = float((hitW < hitL)[decided].mean())
        theory = L / (W + L)
        chk(f"driftless bracket W={W:.0f} L={L:.0f}: P(win) = L/(W+L)",
            abs(p_win - theory) < 0.012, f"{p_win:.4f} vs {theory:.4f}")
        gross = p_win * W - (1 - p_win) * L
        chk(f"  ... so expected GROSS is ~0 (skew is not free)", abs(gross) < 0.4 * L / 10,
            f"{gross:+.3f} ticks")
    # and the excess needed over that baseline is cost/(W+L) -- decreasing in the SUM
    for W, L in ((10.0, 10.0), (40.0, 40.0)):
        need = (cost + L) / (W + L) - L / (W + L)
        chk(f"excess needed over the bracket baseline is cost/(W+L), W+L={W+L:.0f}",
            abs(need - cost / (W + L)) < 1e-12, f"{need:.4f}")
    chk("at zero cost more trades is always better (no interior optimum)",
        sharpe_at(0.03, e_abs(5), rms_over_eabs * e_abs(5), n_year(5), 0.0)
        > sharpe_at(0.03, e_abs(390), rms_over_eabs * e_abs(390), n_year(390), 0.0),
        "cost is what creates the optimum")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def do_measure(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    g = meta["gates"]["ES"]
    bad = [k for k, v in g.items() if isinstance(v, dict) and v.get("passes") is False]
    if bad:
        raise GateError(f"[FIXTURE] ES fails gates {bad}")

    d = pd.read_csv(FIX)
    d = d[(d["day"] >= IN_SAMPLE[0]) & (d["day"] <= IN_SAMPLE[1])].copy()
    if (d["day"] > "2023-12-31").any():
        raise GateError("[HOLDOUT] rows past 2023 reached the measurement")
    d["minute"] = d["hhmm"].str.slice(0, 2).astype(int) * 60 + \
        d["hhmm"].str.slice(3, 5).astype(int)
    d = d.sort_values(["day", "minute"], kind="stable").reset_index(drop=True)
    P(f"ES RTH 1-minute bars {len(d):,} over {d['day'].nunique():,} sessions, "
      f"{IN_SAMPLE[0]} .. {IN_SAMPLE[1]}")
    P(f"cost at micro size: {COST_TICKS:.3f} ticks per round trip\n")

    # E|M| and RMS by horizon, on NON-OVERLAPPING in-session windows, single contract
    meas = {}
    for h in HORIZONS_MIN:
        nets = []
        for _, grp in d.groupby("day", sort=True):
            o = grp["open"].to_numpy(float)
            c = grp["close"].to_numpy(float)
            con = grp["contract"].to_numpy()
            n = len(o)
            if n < RTH_MIN - 30:
                continue                        # skip half-days (G3 lists 128)
            for a0 in range(0, n - h + 1, h):
                b0 = a0 + h - 1
                if con[a0] != con[b0]:
                    continue
                nets.append((c[b0] - o[a0]) / TICK_PTS)
        x = np.asarray(nets)
        if len(x) < 500:
            continue
        e_abs = float(np.abs(x).mean())
        rms = float(np.sqrt(np.mean(x ** 2)))
        n_year = (RTH_MIN / h) * 252.0
        meas[h] = {"n_windows": int(len(x)), "mean_abs_ticks": e_abs, "rms_ticks": rms,
                   "rms_over_mean_abs": rms / e_abs,
                   "trades_per_year_always_in": n_year,
                   "breakeven_accuracy": 0.5 + COST_TICKS / (2 * e_abs)}

    P(f"  {'horizon':>9}{'windows':>10}{'E|M| tk':>9}{'RMS':>8}{'RMS/E|M|':>10}"
      f"{'trades/yr':>11}{'p_be':>8}")
    for h, m in meas.items():
        P(f"  {h:>7} m{m['n_windows']:>10,}{m['mean_abs_ticks']:>9.2f}{m['rms_ticks']:>8.2f}"
          f"{m['rms_over_mean_abs']:>10.2f}{m['trades_per_year_always_in']:>11,.0f}"
          f"{m['breakeven_accuracy']:>8.2%}")

    # the measured scaling exponent -- D469 fitted 0.50 on ticks; check it here
    hs = np.array(sorted(meas))
    es = np.array([meas[h]["mean_abs_ticks"] for h in hs])
    beta = float(np.polyfit(np.log(hs), np.log(es), 1)[0])
    k_fit = float(np.exp(np.polyfit(np.log(hs), np.log(es), 1)[1]))
    P(f"\n  E|M| ~ {k_fit:.2f} * h^{beta:.3f}   (D469 fitted 0.50 on tick data; "
      f"0.5 is a random walk)")
    ratio = float(np.mean([meas[h]["rms_over_mean_abs"] for h in meas]))

    # ---- the conditional question: given skill a, what horizon and what Sharpe?
    P(f"\n  IF a rule had directional accuracy a above a coin flip, then at micro cost:")
    P(f"  {'skill a':>9}{'accuracy':>10}{'E|M| wanted':>13}{'-> horizon':>12}"
      f"{'p_be there':>12}{'Sharpe':>9}   {'Sharpe at 15m':>14}")
    rows = {}
    for a in SKILLS:
        e_want = COST_TICKS / a
        h_star = (e_want / k_fit) ** (1.0 / beta)
        n_year = (RTH_MIN / h_star) * 252.0
        s_star = sharpe_at(a, e_want, ratio * e_want, n_year, COST_TICKS)
        m15 = meas.get(15)
        s15 = sharpe_at(a, m15["mean_abs_ticks"], m15["rms_ticks"],
                        m15["trades_per_year_always_in"], COST_TICKS) if m15 else float("nan")
        sess = h_star / RTH_MIN
        unit = (f"{h_star:,.0f} min" if h_star < RTH_MIN
                else f"{sess:,.1f} sessions")
        rows[a] = {"skill": a, "accuracy": 0.5 + a, "e_abs_wanted_ticks": e_want,
                   "optimal_horizon_min": h_star,
                   "optimal_horizon_sessions": sess,
                   "p_be_at_optimum": 0.5 + a / 2,
                   "sharpe_at_optimum": s_star, "sharpe_at_15min": s15,
                   "trades_per_year_at_optimum": n_year}
        P(f"  {a:>8.1%}{0.5+a:>10.1%}{e_want:>11.0f} tk{unit:>12}"
          f"{0.5+a/2:>12.1%}{s_star:>9.2f}{s15:>14.2f}")

    P(f"\n  and the 15-minute horizon is optimal only near a = "
      f"{COST_TICKS/meas[15]['mean_abs_ticks']:.1%} "
      f"(accuracy {0.5+COST_TICKS/meas[15]['mean_abs_ticks']:.1%}), "
      f"which nothing in this repo has demonstrated.")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D473: the horizon the micro cost structure wants, conditional on a "
                      "stated directional skill. A cost-geometry calculation -- no entry "
                      "rule, no signal, no backtest, nothing admitted.",
           "source": "data/fixtures/fut_ES_rth_1m.csv.gz, 2016-01-04..2023-12-29, RTH, "
                     "non-overlapping single-contract windows",
           "cost_ticks": COST_TICKS,
           "closed_form": "E|M|(h*) = cost / a, equivalently p_be(h*) = 0.5 + a/2: the "
                          "optimum is where skill is exactly twice the breakeven excess. "
                          "Verified against a numerical argmax in --self-test.",
           "scaling": {"k": k_fit, "beta": beta,
                       "note": "beta 0.5 is a random walk; D469 fitted 0.50 on ticks"},
           "rms_over_mean_abs": ratio,
           "by_horizon": meas, "by_skill": rows,
           "limitations": [
               "RTH-only and intraday: horizons past one session are EXTRAPOLATED through "
               "the fitted exponent, not measured, and a multi-session hold also collects "
               "overnight moves this RTH fixture does not contain",
               "the +/-|M| outcome model assumes the rule captures the full move signed by "
               "its call -- an upper bound on any exit, so every Sharpe here is optimistic",
               "trades are assumed independent and always-in; a selective rule trades less "
               "often and its Sharpe scales by sqrt(its own count), not this one",
               "skill is assumed constant across horizons, which is the strongest "
               "assumption in the file and is almost certainly false",
               "no slippage beyond the measured half-spread and no queue position"]}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.measure:
        return do_measure(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
