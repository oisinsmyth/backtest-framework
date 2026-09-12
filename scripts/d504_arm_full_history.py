"""D504 -- the MACD arm across EVERY year the fixture holds, per year and overall.

    uv run python scripts/d504_arm_full_history.py --self-test
    uv run python scripts/d504_arm_full_history.py --run [--json]

**A DESCRIPTION, NOT A STUDY.** One frozen construction, every year on disk, no search, no grid,
no threshold, no selection. Nothing is pre-registered because nothing is being decided: no
parameter is chosen and no verdict is drawn. Nothing admitted (R15).

**The 2024+ slice was already spent by D503**, so describing it year by year is not a re-read --
the read happened and this reports the same series. **No cell may be sharpened on the strength of
anything here**, and none is.

WHAT THIS IS FOR
----------------
Every hurdle figure this programme quoted for the prop book -- C-d's sigma, P3's breach rate,
P4's profit before breach -- was computed on a window AVERAGING 2016-2023, and D503 found that
MNQ's dollar volatility nearly doubled over it because NQ's index level did. A per-year table is
the only honest way to read a hurdle that moves with the price level.

THE TWO THINGS THAT MOVE IN OPPOSITE DIRECTIONS
-----------------------------------------------
As the index level rises at a fixed $0.50 tick and a fixed $3 commission:
  * the FEE becomes cheaper relative to the move  -> the edge gets easier to clear
  * the CONTRACT becomes larger relative to the account's fixed floor -> the account dies sooner
Both are reported per year, because the whole prop question is which one wins.

THE YEARLY SHARPE IS NEARLY UNINTERPRETABLE ON ITS OWN and the table says so in a column: a
one-year annualised Sharpe carries SE ~ sqrt(1 + S^2/2) ~ 1.0. Year-to-year swings of +/- 1.0 are
what no edge looks like. The SE is printed beside every yearly Sharpe so the column cannot be
read as a track record.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import (  # noqa: E402
    COMMISSION_RT, CROSS_TICKS, GateError, SEGMENTS, SPECS, impulse_macd, macd_hist, rotate)
from d491_conditional_hold import DAY_FIRST_DECIDE, LAST_SEG, TRADING_DAYS, simulate  # noqa: E402
from d495_agree_confluence import FIX, META, agree_signal  # noqa: E402
from d501_worst_day_frequency import max_drawdown_life  # noqa: E402
from d503_forward_book import series_window, simulate_trades  # noqa: E402

OUT = REPO / "data" / "d504_arm_full_history.json"

ROOT, SIZED = "NQ", "MNQ"
M_HOLD = 5
FULL_LO, FULL_HI = "2010-01-01", "2026-12-31"
USABLE_LO = "2016-01-04"          # the fixture's own usable start for the index day session
ACCOUNT = 50_000.0
TRAIL_DD = 0.04 * ACCOUNT
P3_CAP = 0.02 * ACCOUNT
FEE_ACCOUNT = 209.0               # MFFU 50K, one-time (D386)
N_DRAWS = 2000
SEED = 504


def P(*a, **k):
    print(*a, **k, flush=True)


def build(d_all, meta, spec):
    """The frozen component over the whole fixture. Signal identical to D495/D503."""
    s = series_window(ROOT, d_all, meta, FULL_LO, FULL_HI)
    nseg = len(SEGMENTS)
    k = len(s["log_close"]) // nseg
    g = lambda a: np.exp(a[:k * nseg]).reshape(k, nseg)      # noqa: E731
    md = impulse_macd(s["log_high"], s["log_low"], s["log_close"])[1][:k * nseg]
    b1 = np.where(md == 0.0, 0.0,
                  np.sign(impulse_macd(s["log_high"], s["log_low"],
                                       s["log_close"])[0][:k * nseg])).reshape(k, nseg)
    b2 = np.sign(macd_hist(s["log_close"])[:k * nseg]).reshape(k, nseg)
    pure = s["pure"][:k * nseg].reshape(k, nseg)
    keep = pure[:, DAY_FIRST_DECIDE:LAST_SEG + 1].all(axis=1)
    lvl = g(s["log_close"])[:, LAST_SEG]
    return {"O": g(s["log_open"])[keep], "C": g(s["log_close"])[keep],
            "AGREE": agree_signal(b1, b2)[keep], "days": s["days"][:k][keep],
            "level": lvl[keep], "days_all": s["days"][:k], "keep": keep,
            "first": DAY_FIRST_DECIDE, "tick_pts": spec[ROOT]["tick_points"],
            "tick_usd": spec[SIZED]["tick_usd"], "point_usd": spec[SIZED]["tick_usd"]
            / spec[ROOT]["tick_points"],
            "cost": COMMISSION_RT / spec[SIZED]["tick_usd"] + CROSS_TICKS}


def sharpe_se(sharpe: float, n_sessions: int) -> float:
    """Lo (2002): SE of an annualised Sharpe ~ sqrt((1 + S^2/2) / years)."""
    yrs = n_sessions / TRADING_DAYS
    if yrs <= 0:
        return float("nan")
    return float(np.sqrt((1.0 + sharpe * sharpe / 2.0) / yrs))


def describe(d, tr_net, tr_gross, level, point_usd, cost_usd, tick_usd):
    """Every statistic the table needs, for one slice of sessions."""
    n = len(d)
    mu, sd = float(d.mean()), float(d.std(ddof=1)) if n > 1 else (float(d.mean()), np.nan)
    sh = mu / sd * np.sqrt(TRADING_DAYS) if sd and sd > 0 else np.nan
    eq = np.cumsum(d)
    absmove = float(np.abs(tr_gross).mean()) if len(tr_gross) else np.nan
    out = {"n_sessions": n, "n_traded": int((d != 0).sum()), "n_trades": int(len(tr_net)),
           "trips_per_session": float(len(tr_net) / n) if n else np.nan,
           "mean_usd": mu, "median_usd": float(np.median(d)), "daily_sigma_usd": sd,
           "sigma_pct_of_account": (sd / ACCOUNT) if sd else np.nan,
           "sharpe": sh, "sharpe_se": sharpe_se(sh if np.isfinite(sh) else 0.0, n),
           "total_usd": float(d.sum()),
           "max_drawdown_usd": float((np.maximum.accumulate(eq) - eq).max()) if n else np.nan,
           "worst_day_usd": float(d.min()), "best_day_usd": float(d.max()),
           "worst_day_share_of_budget": float(-d.min() / TRAIL_DD),
           "skew": float(((d - mu) ** 3).mean() / sd ** 3) if sd and sd > 0 else np.nan,
           "kurtosis": float(((d - mu) ** 4).mean() / sd ** 4) if sd and sd > 0 else np.nan,
           "p3_breaches": int((d <= -P3_CAP).sum()),
           "p3a_per_year": float((d <= -P3_CAP).sum() / n * TRADING_DAYS) if n else np.nan,
           "nq_mean_level": float(np.mean(level)) if len(level) else np.nan,
           "mnq_notional_usd": float(np.mean(level) * point_usd) if len(level) else np.nan,
           "notional_over_account": float(np.mean(level) * point_usd / ACCOUNT)
           if len(level) else np.nan}
    if len(tr_net):
        w, l = tr_net[tr_net > 0], tr_net[tr_net < 0]
        lo1, hi1 = np.percentile(tr_net, 1), np.percentile(tr_net, 99)
        # a 1% tail needs >= 100 trades to contain one; below that the trim is undefined and
        # is reported as such rather than as a NaN that reads like a number
        trimmable = len(tr_net) >= 100
        out.update({"trade_mean_net_usd": float(tr_net.mean()),
                    "trade_median_net_usd": float(np.median(tr_net)),
                    "trade_mean_gross_usd": float(tr_gross.mean()),
                    "hit_rate": float((tr_net > 0).mean()),
                    "payoff": float(w.mean() / abs(l.mean())) if len(l) else np.nan,
                    "trims_defined": bool(trimmable),
                    "trade_mean_ex_top_usd": float(tr_net[tr_net <= hi1].mean())
                    if trimmable else None,
                    "trade_mean_ex_bottom_usd": float(tr_net[tr_net >= lo1].mean())
                    if trimmable else None,
                    "trade_mean_trimmed_usd": float(
                        tr_net[(tr_net >= lo1) & (tr_net <= hi1)].mean()) if trimmable else None,
                    "mean_abs_gross_move_usd": absmove,
                    "fee_share_of_move": float(cost_usd / absmove) if absmove else np.nan,
                    "gross_over_cost": float(tr_gross.mean() / cost_usd) if cost_usd else np.nan,
                    "breakeven_cost_usd": float(tr_gross.mean())})
    return out


def account_economics(d, fee=FEE_ACCOUNT):
    """Replaceable accounts: profit REALISED inside each life, every fee paid, opens forfeited."""
    nd, life, segs = max_drawdown_life(d, TRAIL_DD)
    dead = [float(d[a:b + 1].sum()) for a, b, _ in segs]
    tail = float(d[segs[-1][1] + 1:].sum()) if segs else float(d.sum())
    yrs = len(d) / TRADING_DAYS
    net = sum(dead) + tail - nd * fee
    return {"deaths": nd, "mean_life_sessions": life, "realised_in_dead_lives_usd": sum(dead),
            "open_life_usd": tail, "fees_usd": -nd * fee, "net_usd": net,
            "net_usd_per_year": net / yrs if yrs else np.nan,
            "net_pct_of_account_per_year": (net / yrs) / ACCOUNT if yrs else np.nan,
            "dead_lives_positive": sum(1 for x in dead if x > 0),
            "mean_realised_per_dead_life_usd": (sum(dead) / nd) if nd else np.nan,
            "per_life_usd": dead}


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:60} {detail}")
        if not cond:
            fails.append(label)

    # --- the Sharpe SE, which is the table's most important column ---------------------------
    chk("a one-year Sharpe of 0 carries SE 1.00", abs(sharpe_se(0.0, 252) - 1.0) < 1e-12,
        f"{sharpe_se(0.0, 252):.4f}")
    chk("SE falls as 1/sqrt(years): ten years is ~0.32x one year",
        abs(sharpe_se(0.0, 2520) - 1.0 / np.sqrt(10)) < 1e-12, f"{sharpe_se(0.0, 2520):.4f}")
    chk("a higher Sharpe carries a WIDER SE", sharpe_se(1.0, 252) > sharpe_se(0.0, 252),
        f"{sharpe_se(1.0, 252):.3f} vs {sharpe_se(0.0, 252):.3f}")
    chk("[X] SE is not constant across window lengths -- the whole point of the column",
        abs(sharpe_se(0.0, 252) - sharpe_se(0.0, 504)) > 0.2)

    # --- account economics on a hand-built series --------------------------------------------
    # +100 x 30 then -2000 in one day: the account dies, having realised +1000, fee 209
    d = np.concatenate([np.full(30, 100.0), [-2000.0], np.full(10, 50.0)])
    ec = account_economics(d, fee=209.0)
    chk("one death, and the dead life's realised total is its own sum",
        ec["deaths"] == 1 and abs(ec["realised_in_dead_lives_usd"] - 1000.0) < 1e-9,
        f"deaths {ec['deaths']}, realised ${ec['realised_in_dead_lives_usd']:,.0f}")
    chk("the open life is carried separately, not merged into the dead ones",
        abs(ec["open_life_usd"] - 500.0) < 1e-9, f"${ec['open_life_usd']:,.0f}")
    chk("every death pays a fee", abs(ec["fees_usd"] + 209.0) < 1e-9)
    chk("net = dead + open - fees", abs(ec["net_usd"] - (1000.0 + 500.0 - 209.0)) < 1e-9,
        f"${ec['net_usd']:,.0f}")
    chk("[X] a series that never breaches pays NO fee and has no dead lives",
        account_economics(np.full(50, 10.0), fee=209.0)["deaths"] == 0
        and account_economics(np.full(50, 10.0), fee=209.0)["fees_usd"] == 0.0)

    # --- the fee/move yardstick, which is the whole cost story -------------------------------
    st = describe(np.array([10.0, -5.0, 0.0]), np.array([5.0, -10.0]),
                  np.array([8.5, -6.5]), np.array([20000.0, 20000.0, 20000.0]), 2.0, 3.5, 0.5)
    chk("fee share of move = cost / mean |gross move|",
        abs(st["fee_share_of_move"] - 3.5 / 7.5) < 1e-9, f"{st['fee_share_of_move']:.4f}")
    chk("gross over cost = mean gross / cost",
        abs(st["gross_over_cost"] - 1.0 / 3.5) < 1e-9, f"{st['gross_over_cost']:.4f}")
    chk("notional = mean index level x dollars per point",
        abs(st["mnq_notional_usd"] - 40000.0) < 1e-9, f"${st['mnq_notional_usd']:,.0f}")
    chk("[X] a HIGHER index level raises the notional, which is D503's mechanism",
        describe(np.array([1.0, 2.0]), np.array([1.0]), np.array([1.0]),
                 np.array([30000.0, 30000.0]), 2.0, 3.5, 0.5)["mnq_notional_usd"] > 40000.0)

    # --- the trims, and the rule about which one to lead with --------------------------------
    tr = np.concatenate([np.full(198, 5.0), [500.0, -400.0], np.full(100, 5.0)])
    st2 = describe(np.zeros(len(tr)), tr, tr, np.ones(len(tr)), 2.0, 3.5, 0.5)
    chk("the SYMMETRIC trim sits between the two one-sided trims",
        st2["trade_mean_ex_top_usd"] < st2["trade_mean_trimmed_usd"] < st2[
            "trade_mean_ex_bottom_usd"],
        f"{st2['trade_mean_ex_top_usd']:.2f} < {st2['trade_mean_trimmed_usd']:.2f} < "
        f"{st2['trade_mean_ex_bottom_usd']:.2f}")
    chk("[X] on a two-sided book the ex-top trim alone MISLEADS -- it reads below the "
        "symmetric one", st2["trade_mean_ex_top_usd"] < st2["trade_mean_trimmed_usd"])
    thin = describe(np.zeros(5), np.full(5, 5.0), np.full(5, 8.5), np.ones(5), 2.0, 3.5, 0.5)
    chk("[X] under 100 trades the trims are reported UNDEFINED, not as a silent NaN",
        thin["trims_defined"] is False and thin["trade_mean_trimmed_usd"] is None
        and st2["trims_defined"] is True)

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    pk = build(pd.read_csv(FIX), meta, spec)
    days = pk["days"]
    pnl_tk, trips = simulate(pk["O"], pk["C"], pk["AGREE"], pk["first"], M_HOLD, pk["cost"],
                             pk["tick_pts"])
    gross_tk, _ = simulate(pk["O"], pk["C"], pk["AGREE"], pk["first"], M_HOLD, 0.0,
                           pk["tick_pts"])
    rows = simulate_trades(pk["O"], pk["C"], pk["AGREE"], pk["first"], M_HOLD, pk["cost"],
                           pk["tick_pts"])
    chk_per = np.zeros(len(days))
    for i, _, _, _, v, _w in rows:
        chk_per[i] += v
    if np.abs(chk_per - pnl_tk).max() > 1e-12:
        raise GateError("[TRADES] the instrumented machine disagrees with simulate")
    tick = pk["tick_usd"]
    d_all_usd = pnl_tk * tick
    g_all_usd = gross_tk * tick
    tr_sess = np.array([r[0] for r in rows])
    tr_net = np.array([r[4] * tick for r in rows])
    tr_gross = tr_net + pk["cost"] * tick
    cost_usd = pk["cost"] * tick
    yrs = np.array([str(x)[:4] for x in days])

    P("D504 -- the MACD arm across every year the fixture holds")
    P(f"  frozen spec: NQ front month as 1 {SIZED}, day session, both log MACDs agree,")
    P(f"  min hold {M_HOLD} h, flat 16:00 ET, ${COMMISSION_RT:.0f} + {CROSS_TICKS} ticks a round "
      f"trip = ${cost_usd:.2f}")
    P(f"  {len(days):,} sessions {days.min()} -> {days.max()}, {len(rows):,} trades\n")
    P(f"  NOTE: the fixture's usable start for the index day session is {USABLE_LO} "
      f"(GLBX coverage);")
    P(f"  years before it are shown as DIAGNOSTIC ONLY and excluded from every total.\n")

    per_year = {}
    for y in sorted(set(yrs)):
        m = yrs == y
        tm = np.isin(tr_sess, np.flatnonzero(m))
        per_year[y] = describe(d_all_usd[m], tr_net[tm], tr_gross[tm], pk["level"][m],
                               pk["point_usd"], cost_usd, tick)

    early = [y for y in per_year if y < USABLE_LO[:4]]
    live = [y for y in per_year if y >= USABLE_LO[:4]]

    P("=== 1. PER YEAR: TRADING, P&L AND RISK ===")
    P("     year  sess  trades  trips  mean$/d  median  sigma$   Sharpe   (SE)   total$"
      "   maxDD$   worst$  %budget  skew")
    for y in early + live:
        r = per_year[y]
        tag = "  (diag)" if y in early else ""
        P(f"     {y}{r['n_sessions']:>6}{r['n_trades']:>8}{r['trips_per_session']:>7.2f}"
          f"{r['mean_usd']:>9.2f}{r['median_usd']:>8.2f}{r['daily_sigma_usd']:>8.0f}"
          f"{r['sharpe']:>+9.2f}{r['sharpe_se']:>7.2f}{r['total_usd']:>9,.0f}"
          f"{r['max_drawdown_usd']:>9,.0f}{r['worst_day_usd']:>9,.0f}"
          f"{r['worst_day_share_of_budget']:>8.0%}{r['skew']:>+7.2f}{tag}")
    P("\n     EVERY yearly Sharpe carries an SE near 1.0. A column swinging +/-1 is what NO")
    P("     edge looks like over one year; only the pooled row below is interpretable.")

    P("\n=== 2. PER YEAR: THE TWO THINGS THAT MOVE IN OPPOSITE DIRECTIONS ===")
    P("     year   NQ level   1 MNQ notional   x account   E|move|/trade   fee/move   "
      "gross/cost   hit   P3a/yr")
    for y in early + live:
        r = per_year[y]
        P(f"     {y}{r['nq_mean_level']:>11,.0f}{r['mnq_notional_usd']:>17,.0f}"
          f"{r['notional_over_account']:>12.2f}{r['mean_abs_gross_move_usd']:>16.0f}"
          f"{r['fee_share_of_move']:>11.1%}{r['gross_over_cost']:>13.2f}"
          f"{r['hit_rate']:>6.1%}{r['p3a_per_year']:>9.2f}")
    P("\n     LEFT half: the contract grows against a FIXED $2,000 floor -> the account dies")
    P("     sooner. RIGHT half: the fee shrinks against a growing move -> the edge clears")
    P("     more easily. The prop question is which of the two wins, and it is not the same")
    P("     answer in 2016 as in 2026.")

    # ---- pooled, on the usable window only
    mu_live = np.isin(yrs, live)
    tm_live = np.isin(tr_sess, np.flatnonzero(mu_live))
    d_live = d_all_usd[mu_live]
    overall = describe(d_live, tr_net[tm_live], tr_gross[tm_live], pk["level"][mu_live],
                       pk["point_usd"], cost_usd, tick)
    g_live = g_all_usd[mu_live]
    overall["gross_sharpe"] = float(g_live.mean() / g_live.std(ddof=1) * np.sqrt(TRADING_DAYS))

    P(f"\n=== 3. OVERALL, {live[0]}-{live[-1]} ({overall['n_sessions']:,} sessions, "
      f"{overall['n_trades']:,} trades) ===")
    for lab, v, f in (("net Sharpe", overall["sharpe"], "{:+.3f}"),
                      ("  its SE", overall["sharpe_se"], "{:.3f}"),
                      ("gross Sharpe", overall["gross_sharpe"], "{:+.3f}"),
                      ("mean $/session", overall["mean_usd"], "{:+.2f}"),
                      ("median $/session", overall["median_usd"], "{:+.2f}"),
                      ("daily sigma $", overall["daily_sigma_usd"], "{:,.0f}"),
                      ("  as % of $50k", overall["sigma_pct_of_account"], "{:.2%}"),
                      ("total $", overall["total_usd"], "{:,.0f}"),
                      ("max drawdown $", overall["max_drawdown_usd"], "{:,.0f}"),
                      ("worst day $", overall["worst_day_usd"], "{:,.0f}"),
                      ("  % of the budget", overall["worst_day_share_of_budget"], "{:.0%}"),
                      ("skew", overall["skew"], "{:+.2f}"),
                      ("kurtosis", overall["kurtosis"], "{:.1f}"),
                      ("trips/session", overall["trips_per_session"], "{:.2f}"),
                      ("hit rate", overall["hit_rate"], "{:.1%}"),
                      ("payoff", overall["payoff"], "{:.2f}"),
                      ("mean $/trade net", overall["trade_mean_net_usd"], "{:+.2f}"),
                      ("mean $/trade gross", overall["trade_mean_gross_usd"], "{:+.2f}"),
                      ("  gross / cost", overall["gross_over_cost"], "{:.2f}x"),
                      ("median $/trade", overall["trade_median_net_usd"], "{:+.2f}"),
                      ("ex-top 1% $/trade", overall["trade_mean_ex_top_usd"], "{:+.2f}"),
                      ("ex-bottom 1%", overall["trade_mean_ex_bottom_usd"], "{:+.2f}"),
                      ("TRIMMED both tails", overall["trade_mean_trimmed_usd"], "{:+.2f}"),
                      ("P3 breaches", overall["p3_breaches"], "{:.0f}"),
                      ("  per year", overall["p3a_per_year"], "{:.2f}")):
        P(f"  {lab:<22}{f.format(v):>12}")

    # ---- concentration
    total = float(d_live.sum())
    srt = np.sort(d_live)
    order = np.argsort(-d_live)
    run, half = 0.0, None
    for j, i in enumerate(order, 1):
        run += d_live[i]
        if run >= 0.5 * total:
            half = j
            break
    k1 = max(1, len(srt) // 100)
    conc = {"sessions_to_half_pnl": half,
            "top1": float(srt[-1:].sum() / total), "top5": float(srt[-5:].sum() / total),
            "top10": float(srt[-10:].sum() / total),
            "top1pct": float(srt[-k1:].sum() / total),
            # the SYMMETRIC counterpart: the one-sided share above is the statistic CLAUDE.md
            # warns "always frightens" on a two-sided book, so both are reported
            "bottom1pct": float(srt[:k1].sum() / total),
            "pnl_ex_both_1pct_usd": float(srt[k1:-k1].sum()),
            "share_ex_both_1pct": float(srt[k1:-k1].sum() / total),
            "pnl_ex_both_top10_usd": float(srt[10:-10].sum()),
            "n_trimmed_each_side": int(k1)}
    P(f"\n=== 4. CONCENTRATION, {live[0]}-{live[-1]} -- BOTH SIDES ===")
    P(f"  sessions to half the P&L   {half} of {len(d_live):,}")
    for k, lab in (("top1", "top 1 session"), ("top5", "top 5"), ("top10", "top 10"),
                   ("top1pct", f"top 1% ({k1} sessions)"),
                   ("bottom1pct", f"bottom 1% ({k1} sessions)")):
        P(f"  {lab:<26}{conc[k]:>8.1%}")
    P(f"  P&L with BOTH 1% tails cut  ${conc['pnl_ex_both_1pct_usd']:>9,.0f}  "
      f"= {conc['share_ex_both_1pct']:.1%} of the total")
    P(f"  P&L with the best AND worst 10 sessions cut  "
      f"${conc['pnl_ex_both_top10_usd']:>9,.0f}")
    P("  The one-sided share is the statistic CLAUDE.md calls a flag and not a verdict.")
    P("  Both are printed so neither can be quoted alone.")

    # ---- account economics, whole window and per era
    P(f"\n=== 5. REPLACEABLE-ACCOUNT ECONOMICS (${FEE_ACCOUNT:.0f} a 50K account) ===")
    eras = {"2016-2023 (in-sample)": (yrs >= "2016") & (yrs <= "2023"),
            "2024-2026 (spent holdout)": yrs >= "2024",
            f"{live[0]}-{live[-1]} (all usable)": mu_live}
    econ = {}
    P("     era                          deaths  mean life  realised$   fees$     net$   $/yr"
      "   %/yr")
    for lab, m in eras.items():
        e = account_economics(d_all_usd[m])
        econ[lab] = e
        P(f"     {lab:<28}{e['deaths']:>7}{e['mean_life_sessions']:>11.0f}"
          f"{e['realised_in_dead_lives_usd'] + e['open_life_usd']:>11,.0f}"
          f"{e['fees_usd']:>8,.0f}{e['net_usd']:>9,.0f}{e['net_usd_per_year']:>7,.0f}"
          f"{e['net_pct_of_account_per_year']:>7.1%}")

    # ---- the null, on the usable window
    P(f"\n=== 6. ROTATION NULL on {live[0]}-{live[-1]}, {N_DRAWS:,} draws ===")
    rng = np.random.default_rng(SEED)
    idx = np.flatnonzero(mu_live)
    O, C, S = pk["O"][idx], pk["C"][idx], pk["AGREE"][idx]
    nn = np.empty(N_DRAWS)
    for i in range(N_DRAWS):
        pn, _ = simulate(O, C, rotate(S, int(rng.integers(1, len(idx)))), pk["first"], M_HOLD,
                         pk["cost"], pk["tick_pts"])
        dd = pn * tick
        nn[i] = dd.mean() / dd.std(ddof=1) * np.sqrt(TRADING_DAYS) if dd.std(ddof=1) > 0 else 0.0
    p50, p95 = float(np.percentile(nn, 50)), float(np.percentile(nn, 95))
    bs = np.array([np.percentile(rng.choice(nn, len(nn)), 95) for _ in range(200)])
    se = float(bs.std(ddof=1))
    marg = (overall["sharpe"] - p95) / se
    P(f"  observed {overall['sharpe']:+.3f}   p50 {p50:+.3f}   p95 {p95:+.3f}   SE {se:.4f}"
      f"   {marg:+.1f} SE   {'CLEARS' if overall['sharpe'] > p95 else 'does NOT clear'}"
      + ("   UNRESOLVED" if abs(marg) < 2 else ""))
    P(f"  the null's p95 on {overall['n_sessions']:,} sessions is much tighter than on D503's")
    P(f"  652 -- which is the point: length is what buys resolution, not a better signal.")

    art = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D504: the frozen MACD arm described year by year across every year the "
                      "fixture holds. A DESCRIPTION, not a study -- no search, no selection, "
                      "nothing admitted. 2024+ was already spent by D503.",
           "spec": {"root": ROOT, "sized_as": SIZED, "m_hold": M_HOLD,
                    "cost_usd_per_trade": cost_usd, "usable_start": USABLE_LO,
                    "span": [str(days.min()), str(days.max())]},
           "per_year": per_year, "diagnostic_years": early, "usable_years": live,
           "overall_usable": overall, "concentration_usable": conc,
           "account_economics": econ,
           "null_usable": {"observed": overall["sharpe"], "p50": p50, "p95": p95,
                           "p95_se": se, "margin_se": marg,
                           "clears": bool(overall["sharpe"] > p95),
                           "unresolved": bool(abs(marg) < 2)},
           "limitations": [
               f"years before {USABLE_LO} are DIAGNOSTIC ONLY -- the GLBX archive covers "
               "21-42% of index day sessions in 2010-2012 and >=96% from 2016 (D462)",
               "2024-01-02..2026-09-09 was spent by D503; this describes that series and "
               "must not be used to sharpen or re-score anything",
               "a one-year annualised Sharpe carries SE ~1.0 -- the yearly column is not a "
               "track record",
               "fills are open-of-next-segment at the measured half-spread, no queue, no "
               "partial fills; every figure is an upper bound",
               "the account economics assume profit is WITHDRAWN before a breach; a breach "
               "forfeits what is still open, and MFFU's withdrawal mechanics have not been "
               "read"]}
    OUT.write_text(json.dumps(art, indent=2, default=float), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2, default=float))
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
