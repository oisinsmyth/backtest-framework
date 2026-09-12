"""D498 -- ADDENDUM to D497: is the worst day a one-off or a habit?

    uv run python scripts/d498_worst_day_frequency.py --self-test
    uv run python scripts/d498_worst_day_frequency.py --run [--json]

**AN ADDENDUM, NOT A NEW STUDY.** Same cell, same window, same cost line as D497. It reads one
statistic family off a series D497 already computed: the FREQUENCY and CLUSTERING of large loss
days, with the days NAMED. No search, no new grid, no new signal. Nothing opened, closed or
admitted (R15).

WHY THIS EXISTS
---------------
D497 reported a worst day of -$1,315 against P3's $1,000 cap and stopped at the binary. The
principal's reading is that the extremum is not the interesting quantity:

> *"the worst day is not the end of the world? If its a one off it does not matter but if it
> happens all the time then thats a different story"*

That is a question about a RATE, and a rate is a different object from a max -- one bad day in
eight years is a tail draw, one a quarter is a property of the construction. D497 never named
the days either, which is this repo's own standing lesson: a concentration report is not
finished until the top trade is named and its bar printed.

AND THE WORST DAY MATTERS THROUGH A SECOND CHANNEL that has nothing to do with P3. The 50K
account's entire loss budget is the $2,000 trailing drawdown (P1). A -$1,315 day spends two
thirds of it in one session, so the large-loss RATE feeds D496's barrier model whether or not
P3 is a real venue term -- and D496's model is Brownian, so it cannot see a fat tail at all.
This runner therefore also computes the EMPIRICAL trailing-drawdown life, which D496 could not.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from math import erfc, sqrt
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import (  # noqa: E402
    GateError, IN_SAMPLE, SEGMENTS, SPECS, series_for)
from d491_conditional_hold import LAST_SEG, TRADING_DAYS, simulate  # noqa: E402
from d495_agree_confluence import META, FIX, build_panel  # noqa: E402

OUT = REPO / "data" / "d498_worst_day_frequency.json"

CAND = {"root": "NQ", "arm": "AGREE", "M": 5}
ACCOUNT = 50_000.0
TRAIL_DD = 0.04 * ACCOUNT        # P1: the account's ENTIRE loss budget, $2,000
P3_CAP = 0.02 * ACCOUNT          # R11 P3: $1,000
THRESHOLDS = (-250.0, -500.0, -750.0, -1000.0, -1250.0)


def P(*a, **k):
    print(*a, **k, flush=True)


def max_drawdown_life(d: np.ndarray, cap: float) -> tuple[int, float, list]:
    """Deaths and mean life, where a death is the TRAILING drawdown first reaching `cap`.

    The account restarts flat after each death, which is what a prop account does: a new one is
    bought. Returns (n_deaths, mean_life_in_sessions) with the mean UNROUNDED, 0.0 when it never
    dies -- unrounded because lives of 1 and 2 sessions average 1.5 and truncating that to 1
    would understate every mean this runner reports.
    """
    if cap <= 0:
        raise ValueError("cap must be a positive dollar amount")
    lives, eq, peak, start = [], 0.0, 0.0, 0
    for i, x in enumerate(d):
        eq += x
        peak = max(peak, eq)
        if peak - eq >= cap:
            lives.append((start, i, i - start + 1))
            eq, peak, start = 0.0, 0.0, i + 1
    n_life = [t[2] for t in lives]
    return len(lives), float(np.mean(n_life)) if lives else 0.0, lives


def recurrence_years(n_events: int, n_sessions: int) -> float:
    """Mean sessions between events, in years of 252 sessions. inf when never seen."""
    if n_events <= 0:
        return float("inf")
    return (n_sessions / n_events) / TRADING_DAYS


def p_at_least_one(n_events: int, n_sessions: int, horizon: int) -> float:
    """P(>=1 event in `horizon` sessions) at the empirical per-session rate."""
    if n_sessions <= 0:
        raise ValueError("no sessions")
    rate = n_events / n_sessions
    return float(1.0 - (1.0 - rate) ** horizon)


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"  [{'ok' if cond else 'FAIL'}] {label}" + (f"   {detail}" if detail else ""))
        if not cond:
            fails.append(label)

    # --- the drawdown walker, on series whose answers are computable by hand ------------------
    n_d, life, _ = max_drawdown_life(np.array([100.0, -300.0, 50.0, 50.0]), 250.0)
    chk("dies where the trailing dd first reaches the cap", (n_d, life) == (1, 2.0),
        f"deaths={n_d} life={life}, expected (1, 2)")
    n_d2, _, _ = max_drawdown_life(np.array([100.0, -300.0, 50.0, 50.0]), 500.0)
    chk("[X] a cap above the worst drawdown yields NO death", n_d2 == 0, f"deaths={n_d2}")
    n_d3, life3, _ = max_drawdown_life(np.array([1000.0, -400.0]), 300.0)
    chk("dd is measured from the running PEAK, not from zero", (n_d3, life3) == (1, 2.0),
        f"deaths={n_d3} life={life3}; a from-zero reading sees +600 and never dies")
    n_d4, life4, seg4 = max_drawdown_life(np.array([-250.0, 100.0, -250.0, 100.0]), 250.0)
    chk("a death restarts the account flat: lives of 1 and 2 sessions, mean 1.5",
        (n_d4, life4) == (2, 1.5), f"deaths={n_d4} life={life4}")
    chk("[X] with a cap the series cannot reach, the second death is invisible",
        max_drawdown_life(np.array([-250.0, 100.0, -250.0, 100.0]), 600.0)[0] == 0)
    chk("the segments are contiguous and cover every death, start to death index",
        seg4 == [(0, 0, 1), (1, 2, 2)], f"{seg4}")

    # --- recurrence and probability arithmetic ------------------------------------------------
    r = recurrence_years(2, 1873)
    chk("2 events in 1,873 sessions is one every 3.72 years",
        abs(r - (1873 / 2) / 252) < 1e-12 and abs(r - 3.716) < 0.01, f"{r:.3f} yr")
    chk("[X] a never-seen event recurs at infinity, not zero",
        recurrence_years(0, 1873) == float("inf"))
    p = p_at_least_one(2, 1873, 149)
    chk("P(>=1 in 149 sessions) at 2/1,873 is ~15% and strictly below the naive rate x horizon",
        0.13 < p < 0.16 and p < 149 * (2 / 1873), f"{p:.4f} vs naive {149 * 2 / 1873:.4f}")
    chk("[X] a zero-session horizon carries zero probability",
        p_at_least_one(2, 1873, 0) == 0.0)

    # --- the point of the addendum: a MAX does not determine a RATE --------------------------
    rng = np.random.default_rng(4980)
    body = rng.normal(0.0, 180.0, 2000)
    one_off = body.copy()
    one_off[7] = -1315.0
    habit = body.copy()
    habit[rng.choice(2000, 40, replace=False)] = -1315.0
    n_one = int((one_off <= -1000.0).sum())
    n_hab = int((habit <= -1000.0).sum())
    chk("two series with the SAME worst day differ 40x in RATE",
        one_off.min() == habit.min() == -1315.0 and n_hab >= 20 * max(n_one, 1),
        f"same max {one_off.min():,.0f}; counts {n_one} vs {n_hab}")
    _, life_one, _ = max_drawdown_life(one_off, TRAIL_DD)
    _, life_hab, _ = max_drawdown_life(habit, TRAIL_DD)
    chk("and the account's life follows the RATE, not the max", life_hab < life_one,
        f"one-off {life_one:.0f} sessions vs habit {life_hab:.0f}")

    # --- date alignment, the thing that would silently misname a day ------------------------
    dd = np.array([10.0, -20.0, 30.0, -1315.0, 5.0])
    days = np.array(["a", "b", "c", "d", "e"])
    chk("the worst day is named from the ALIGNED date vector", days[int(dd.argmin())] == "d")
    chk("[X] a date vector rolled by one names the WRONG day",
        np.roll(days, 1)[int(dd.argmin())] != "d",
        f"rolled names {np.roll(days, 1)[int(dd.argmin())]!r}")

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    d_all = pd.read_csv(FIX)

    root, arm, M = CAND["root"], CAND["arm"], CAND["M"]
    p = build_panel(d_all, meta, spec)[root]
    pnl_tk, trips = simulate(p["O"], p["C"], p[arm], p["first"], M, p["cost"], p["tick_pts"])
    d = pnl_tk * p["tick_usd"]
    n = len(d)

    # rebuild the DAY index exactly as series_for filtered it, then apply build_panel's keep mask
    nseg = len(SEGMENTS)
    start = max(IN_SAMPLE[0], meta["usable_start"][root])
    df = d_all[(d_all["root"] == root) & d_all["same_front"]]
    df = df[df["day"].between(start, IN_SAMPLE[1])].sort_values("day", kind="stable")
    s = series_for(root, d_all, meta)
    k = len(s["log_close"]) // nseg
    keep = s["pure"][:k * nseg].reshape(k, nseg)[:, p["first"]:LAST_SEG + 1].all(axis=1)
    days = df["day"].to_numpy()[:k][keep]
    if len(days) != n:
        raise GateError(f"[ALIGN] {len(days)} dates against {n} sessions of P&L")

    # the session's own move over the traded window, for context on each named day
    sess_ret = p["C"][:, LAST_SEG] / p["O"][:, p["first"]] - 1.0
    sd = float(d.std(ddof=1))

    P("D498 -- ADDENDUM to D497: is the worst day a one-off or a habit?\n")
    P(f"  cell: {root} {arm} M={M}, 1 {p['sized_as']}, {n:,} sessions "
      f"{days[0]} -> {days[-1]} (IN-SAMPLE)")
    P(f"  daily sigma ${sd:,.0f}    P3 cap ${P3_CAP:,.0f}    "
      f"the account's WHOLE loss budget ${TRAIL_DD:,.0f}\n")

    P("=== 1. THE BAD DAYS, NAMED ===")
    P("      date           P&L   in sigma   % of the $2,000 budget   NQ move   trips")
    worst_rows = []
    for i in np.argsort(d)[:12]:
        row = {"day": str(days[i]), "pnl": float(d[i]), "sigma": float(d[i] / sd),
               "share_of_budget": float(-d[i] / TRAIL_DD),
               "session_move": float(sess_ret[i]), "trips": float(trips[i])}
        worst_rows.append(row)
        P(f"  {row['day']}  ${row['pnl']:>9,.0f}     {row['sigma']:>6.2f}"
          f"{row['share_of_budget']:>22.0%}{row['session_move']:>11.2%}"
          f"{row['trips']:>8.0f}")

    P("\n=== 2. THE RATE, WHICH IS THE QUESTION ===")
    P("    threshold   days   % of sessions    one every      expected/yr")
    freq = {}
    for t in THRESHOLDS:
        c = int((d <= t).sum())
        rec = recurrence_years(c, n)
        freq[f"{t:.0f}"] = {"days": c, "share": c / n, "recurrence_years": rec,
                            "per_year": c / n * TRADING_DAYS}
        rs = "never" if rec == float("inf") else f"{rec:.2f} yr"
        P(f"    <= ${t:>7,.0f}{c:>7}{c / n:>15.2%}{rs:>13}{c / n * TRADING_DAYS:>17.2f}")

    P("\n=== 3. TAIL DRAW, OR THE BODY OF THE DISTRIBUTION? ===")
    worst_sig = float(d.min() / sd)
    n_norm = n * 0.5 * erfc(abs(worst_sig) / sqrt(2.0))
    kurt = float(((d - d.mean()) ** 4).mean() / sd ** 4)
    P(f"    the worst day is {worst_sig:.2f} sigma. A normal with sigma ${sd:,.0f} would put")
    P(f"    {n_norm:.2e} such days in {n:,} sessions, so the tail is FAT, not Gaussian:")
    P(f"    excess kurtosis {kurt - 3.0:+.1f}. D496's Brownian barrier model cannot see this")
    P(f"    at all, which is why section 5 computes the EMPIRICAL life beside it.")

    P("\n=== 4. CLUSTERING: SPREAD OVER THE WINDOW, OR BUNCHED? ===")
    yrs = np.array([str(x)[:4] for x in days])
    P("     year   sessions   worst day   <= -$500   <= -$1,000")
    per_year = {}
    for y in sorted(set(yrs)):
        m = yrs == y
        row = {"sessions": int(m.sum()), "worst": float(d[m].min()),
               "beyond_500": int((d[m] <= -500.0).sum()),
               "beyond_1000": int((d[m] <= -1000.0).sum())}
        per_year[y] = row
        P(f"     {y}{row['sessions']:>11}{row['worst']:>12,.0f}"
          f"{row['beyond_500']:>11}{row['beyond_1000']:>13}")
    big = np.flatnonzero(d <= -500.0)
    gaps = np.diff(big)
    med = float(np.median(gaps))
    P(f"\n    the {len(big)} days beyond -$500 sit {gaps.min()} to {gaps.max()} sessions apart")
    P(f"    (median {med:.0f}), so they are "
      f"{'BUNCHED' if med < 20 else 'SPREAD ACROSS THE WINDOW'}.")

    P("\n=== 5. WHAT IT COSTS THE ACCOUNT, THE ONLY THING THAT MATTERS ===")
    n_deaths, life_emp, segs = max_drawdown_life(d, TRAIL_DD)
    P(f"    EMPIRICAL trailing-4% life: {n_deaths} deaths over {n:,} sessions "
      f"-> {life_emp:.0f} sessions")
    P(f"    D496's Brownian model said 177. The realised path is the one to believe.")
    n_p3 = int((d <= -P3_CAP).sum())
    P(f"\n    P(>=1 day beyond ${P3_CAP:,.0f} in a 149-session life) = "
      f"{p_at_least_one(n_p3, n, 149):.1%}")
    P(f"    P(>=1 day beyond ${P3_CAP:,.0f} in a 252-session year)  = "
      f"{p_at_least_one(n_p3, n, 252):.1%}")
    n_d_cap, life_cap, _ = max_drawdown_life(np.where(d <= -P3_CAP, -P3_CAP, d), TRAIL_DD)
    P(f"\n    and if every P3-breaching day were CAPPED at -${P3_CAP:,.0f} -- the BEST a")
    P(f"    same-day stop could do -- life {life_cap:.0f} sessions against {life_emp:.0f}, "
      f"{n_d_cap} deaths against {n_deaths}.")

    P("\n=== 6. EVERY ACCOUNT LIFE IN THE WINDOW, WHICH IS WHERE THE REGIME SHOWS ===")
    P("     bought       died      sessions   worst day in that life")
    lives_rows = []
    for a, b, ln in segs:
        w = float(d[a:b + 1].min())
        lives_rows.append({"bought": str(days[a]), "died": str(days[b]), "sessions": int(ln),
                           "worst_day": w})
        P(f"     {days[a]}  {days[b]}{ln:>12}{w:>25,.0f}")
    tail = n - (segs[-1][1] + 1) if segs else n
    P(f"     {days[segs[-1][1] + 1]}  (alive){tail:>12}"
      f"{float(d[segs[-1][1] + 1:].min()):>25,.0f}   <- still open at the window end")

    P("\n=== 7. WHAT P3 COSTS IF IT IS ACTUALLY ENFORCED ===")
    # a second walker: dies on EITHER the trailing drawdown OR a single day beyond the P3 cap
    lives2, eq, peak, start = [], 0.0, 0.0, 0
    for i, x in enumerate(d):
        eq += x
        peak = max(peak, eq)
        if peak - eq >= TRAIL_DD or x <= -P3_CAP:
            lives2.append((start, i, i - start + 1, "P3" if x <= -P3_CAP else "DD"))
            eq, peak, start = 0.0, 0.0, i + 1
    life_both = float(np.mean([t[2] for t in lives2]))
    n_p3_deaths = sum(1 for t in lives2 if t[3] == "P3")
    P(f"    trailing drawdown alone     {n_deaths} deaths, mean life {life_emp:>5.0f} sessions")
    P(f"    drawdown OR a P3 breach     {len(lives2)} deaths, mean life {life_both:>5.0f} "
      f"sessions  ({n_p3_deaths} of them by P3)")
    P(f"    so enforcing P3 costs {1 - life_both / life_emp:.0%} of the account's life.")
    for a, b, ln, why in lives2:
        if why == "P3":
            P(f"      the {days[b]} breach truncates a life bought {days[a]} at {ln} sessions")

    art = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D498: ADDENDUM to D497 -- the RATE of large loss days, with the days "
                      "named, and the EMPIRICAL trailing-drawdown life beside D496's Brownian "
                      "one. Same cell, window and cost line. Nothing admitted.",
           "candidate": dict(CAND, sized_as=p["sized_as"], n_sessions=n,
                             window=[str(days[0]), str(days[-1])]),
           "daily_sigma_usd": sd, "excess_kurtosis": kurt - 3.0,
           "worst_day_in_sigma": worst_sig,
           "normal_implied_count_at_that_sigma": n_norm,
           "worst_12_days": worst_rows,
           "frequency_by_threshold": freq,
           "per_year": per_year,
           "gaps_between_days_beyond_500": {"n": int(len(big)), "min": int(gaps.min()),
                                            "median": med, "max": int(gaps.max())},
           "account_lives": lives_rows,
           "life_if_P3_enforced_sessions": life_both,
           "deaths_if_P3_enforced": len(lives2),
           "deaths_by_P3": n_p3_deaths,
           "p3_truncated_lives": [{"bought": str(days[a]), "died": str(days[b]),
                                   "sessions": int(ln)}
                                  for a, b, ln, why in lives2 if why == "P3"],
           "sessions_still_open_at_window_end": int(tail),
           "empirical_trailing_dd_life_sessions": life_emp,
           "empirical_trailing_dd_deaths": n_deaths,
           "brownian_model_life_sessions_D496": 177,
           "life_if_P3_days_were_capped": life_cap,
           "deaths_if_P3_days_were_capped": n_d_cap,
           "p_breach_in_149_sessions": p_at_least_one(n_p3, n, 149),
           "p_breach_in_252_sessions": p_at_least_one(n_p3, n, 252),
           "limitations": [
               "in-sample only, 2024+ sealed",
               "an order statistic is the figure most exposed to fill optimism: "
               "open-of-next-segment at the measured half-spread, no queue, no partial fills, "
               "so a real gap day is worse and never better",
               "the empirical life is ONE realised path, so it is one draw and its own "
               "standard error is large",
               "P3's justification in R11 is a generic 'daily loss limits run 2-3%'; the five "
               "MFFU plans and Topstep as encoded in D386 carry NO daily-loss-limit field, "
               "only a trailing drawdown. Whether P3 is a venue term for the two venues P6 "
               "permits is UNVERIFIED and needs the terms pages read"]}
    OUT.write_text(json.dumps(art, indent=2), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2))
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
