"""Hurdle P (R11) on one committed component series, at one venue -- D590.

    uv run python scripts/hurdle_p_report.py --selftest
    uv run python scripts/hurdle_p_report.py --series data/components/<name>_daily_usd.csv \
        --venue mffu_rapid_eod_50k [--account 50000]

Prints the six criteria, one line each, then the per-year table -- because D503/D504
measured that sigma at a fixed micro DOUBLED as NQ's level doubled, so a single
window-wide P3c or C-d figure describes no year in the window.

NO NUMBER IS COMPUTED HERE. Every statistic comes from
`backtest_framework.validation.hurdle_p`, which is the module the tests hold against
D440, D495, D496, D501 and D503. This file is a printer; a second implementation of a
hurdle is exactly what D590 exists to prevent.

`--series` takes either a `data/components/` artefact (a `date,usd` CSV beside its
`.meta.json`, read through `component_series.read`, which verifies the CSV's sha256) or
a bare `date,usd` CSV. The bare form carries no size, no cost line and no provenance, so
C-e is not discharged and the report says so.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation import component_series as CS   # noqa: E402
from backtest_framework.validation import hurdle_p as HP           # noqa: E402


def P(*a, **k):
    print(*a, **k, flush=True)


def expect_raise(fn, what, exc=Exception, log=P) -> bool:
    """The house idiom (scripts/stage0_d581_gamma_close.py): prove the guard FIRES."""
    try:
        fn()
    except exc as e:
        log(f"    RAISES on {what}: {type(e).__name__}: {str(e)[:78]}")
        return True
    raise AssertionError(f"guard did not raise on {what}")


# ------------------------------------------------------------------ reading a series


def load_series(path: Path) -> tuple[list[str], np.ndarray, str]:
    """(dates, dollars, provenance line). Prefers the D590 artefact with its sidecar."""
    meta = path.with_name(path.name[: -len(".csv")] + ".meta.json") if path.suffix == ".csv" \
        else None
    if meta is not None and meta.exists():
        s = CS.read(path)
        return (list(s.dates), s.values,
                f"{s.spec}; {s.window[0]}..{s.window[1]}; {s.size_label}; "
                f"${s.cost_line_usd_rt:.2f} RT; source sha256 {s.source_sha256[:12]}")
    raw = path.read_text(encoding="utf-8").splitlines()
    if not raw or raw[0].strip() != "date,usd":
        raise ValueError(f"{path.name}: expected a 'date,usd' header, got {raw[:1]!r}")
    dates, vals = [], []
    for i, line in enumerate(raw[1:], start=2):
        if not line.strip():
            continue
        d, _, v = line.partition(",")
        if not _:
            raise ValueError(f"{path.name}:{i}: no comma in {line!r}")
        dates.append(d.strip())
        vals.append(float(v))
    return dates, np.asarray(vals, dtype=float), (
        "NO SIDECAR: bare CSV, so size, cost line and provenance are UNKNOWN -- C-e is "
        "not discharged and no component line may be written from this")


# ------------------------------------------------------------------ the report


def report(path: Path, venue: str, account: float, exits: list[str] | None,
           n_paths: int, days: int) -> int:
    dates, d, prov = load_series(path)
    rec = HP.venue_record(venue)
    h = HP.hurdle_p(d, venue, account, label=path.stem, exit_times_et=exits,
                    n_paths=n_paths, days=days)

    P("HURDLE P (RULES.md R11, all six amendments) -- D590\n")
    P(f"  series   {path}")
    P(f"           {len(d):,} sessions {dates[0]} .. {dates[-1]}")
    P(f"  C-e      {prov}")
    P(f"  venue    {venue}  ({rec['firm']}, ${rec['size']:,})   account ${account:,.0f}")
    P(f"  net      mean ${h['mean_usd']:+,.2f}/session   sigma ${h['daily_sigma_usd']:,.2f}"
      f"   Sharpe {h['sharpe']:+.3f}   Sortino {h['sortino']:+.3f}   (R17: both, always)\n")

    P("  P1  SIZING RULE -- a number, never PASS/FAIL (R11 restatement 2026-09-08)")
    P(f"      max trailing drawdown ${h['P1_max_trailing_dd_usd']:,.0f} against the "
      f"${HP.DD_FRACTION * account:,.0f} budget"
      f"  ->  size x{h['P1_size_multiplier']:.3f}")
    P(f"      ${h['P1_post_sizing_usd_per_year']:+,.0f}/yr at the traded size, "
      f"${h['P1_post_sizing_usd_per_year_sized']:+,.0f}/yr after P1 sizing")
    P(f"      basis: {h['P1_basis']}")

    P("\n  P2  NO EXPOSURE ACROSS THE VENUE'S FLATTEN TIME (amendment 2026-08-29)")
    P(f"      flatten {h['P2_flatten_time_et'] or 'UNVERIFIED'} ET   "
      f"verdict {'PASS' if h['P2_pass'] else ('FAIL' if h['P2_pass'] is False else 'NOT ASSERTED')}")
    P(f"      {h['P2_note']}")

    P("\n  P3  A RATE, NOT A MAXIMUM (amendment 2026-09-13)")
    P(f"      P3a  {h['P3a_breaches_per_year']:.3f} breaches/yr "
      f"({h['P3a_breaches']} beyond -${HP.P3_CAP_FRACTION * account:,.0f}, one every "
      f"{h['P3a_recurrence_years']:.2f} yr)  bar {h['P3a_bar']:.1f}  "
      f"{'PASS' if h['P3a_pass'] else 'FAIL'}")
    P(f"      P3b  life cost {h['P3b_life_cost']:.1%} "
      f"({h['life_dd_only_sessions']:.1f} -> {h['life_with_P3_sessions']:.1f} sessions, "
      f"{h['deaths_dd_only']} -> {h['deaths_with_P3']} deaths)  bar {h['P3b_bar']:.0%}  "
      f"{'PASS' if h['P3b_pass'] else 'FAIL'}")
    P(f"      P3c  worst day ${h['P3c_worst_day_usd']:,.0f} = "
      f"{h['P3c_worst_day_in_sigma']:.2f} sigma = "
      f"{h['P3c_share_of_loss_budget']:.0%} of the whole loss budget  REPORTED, not a gate")
    P(f"      daily loss limit: {h['P3_daily_loss_limit_usd']}  -- "
      f"{h['P3_daily_loss_limit_provenance'][:96]}")

    P("\n  P4  THE ACCOUNT'S LIFE (ruling 2026-09-11), profit vs cost binding (2026-09-12)")
    ep = h["P4_expected_profit_usd"]
    P(f"      Brownian (D496): profit ${ep:,.0f}   life {h['P4_expected_life_days']:.1f} d"
      if ep is not None else
      "      Brownian (D496): not defined at a non-positive Sharpe")
    P(f"      lifecycle (D386/D440): expected profit "
      f"${h['P4_lifecycle_expected_profit_usd']:,.0f} vs account cost "
      f"${h['P4_lifecycle_account_cost_usd']:,.0f}  ->  net per cycle "
      f"${h['P4_lifecycle_net_per_cycle_usd']:+,.0f}")
    P(f"      life {h['P4_lifecycle_expected_life_days']:.0f} sessions "
      f"({h['P4_lifecycle_expected_life_years']:.2f} yr), funded "
      f"{h['P4_lifecycle_expected_funded_life_years']:.2f} yr, "
      f"P(pass) {h['P4_lifecycle_p_pass']:.3f}, P(paid) {h['P4_lifecycle_p_paid']:.3f}")
    P(f"      BINDING profit > cost: {'PASS' if h['P4_lifecycle_P4_binding_profit_exceeds_cost'] else 'FAIL'}"
      f"   PREFERRED life >= 1 yr: "
      f"{'yes' if h['P4_lifecycle_P4_preferred_life_pass'] else 'no'} (not binding)")
    P(f"      path: {h['P4_lifecycle_path_basis']}")

    P("\n  P5  A CALCULATION CONVENTION, NEVER A SCREEN (restatement 2026-09-12)")
    P(f"      total ${h['P5_total_usd']:+,.0f}   best day "
      f"{h['P5_best_day_share']:.1%} of it   haircut ${h['P5_haircut_usd']:,.0f} at "
      f"{h['P5_cap']:.0%}   recognised ${h['P5_recognised_usd']:+,.0f}")
    P(f"      {h['P5_note']}")

    P("\n  P6  VENUE PERMITS AUTOMATION WHEN FUNDED")
    P(f"      {'PASS' if h['P6_pass'] else 'FAIL'} -- {h['P6'][:150]}")

    P("\n  PER YEAR -- because sigma at a fixed micro tracks the price level (D503/D504)")
    P(f"    {'year':<6}{'days':>6}{'total $':>11}{'mean $':>9}{'sigma $':>9}"
      f"{'Sharpe':>8}{'Sortino':>9}{'worst $':>10}{'P3a':>7}{'P1 x':>8}")
    for r in HP.per_year(d, dates, account):
        P(f"    {r['year']:<6}{r['n_sessions']:>6}{r['total_usd']:>11,.0f}"
          f"{r['mean_usd']:>9,.1f}{r['daily_sigma_usd']:>9,.1f}{r['sharpe']:>8.2f}"
          f"{r['sortino']:>9.2f}{r['worst_day_usd']:>10,.0f}"
          f"{r['p3a_breaches_per_year']:>7.2f}{r['p1_size_multiplier']:>8.2f}"
          + (f"   {r['note']}" if r["note"] else ""))
    P("\n  P1 is a sizing outcome and P3c a report; the verdicts are P2, P3a, P3b, P4's")
    P("  binding clause and P6. A closure on P1/P3/P4 closes a STANDALONE BOOK, not a")
    P("  component (R11 clarification 2026-08-29).")
    return 0


# ------------------------------------------------------------------ the self-test


def selftest() -> int:
    fails: list[str] = []

    def chk(label, cond, detail=""):
        P(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"   {detail}" if detail else ""))
        if not cond:
            fails.append(label)

    P("hurdle_p_report self-test -- every guard is shown to ACCEPT the good case first,")
    P("then to RAISE on the break. A check that cannot fire is worse than none.\n")

    good = np.array([100.0, -50.0, 25.0, -300.0, 400.0, -10.0, 60.0, -20.0])

    P("== 1. max_drawdown_life: the known answer, then the break")
    n_d, life, segs = HP.max_drawdown_life(np.array([100.0, -300.0, 50.0, 50.0]), 250.0)
    chk("dies where the trailing dd first reaches the cap", (n_d, life) == (1, 2.0),
        f"deaths={n_d} life={life}, expected (1, 2.0)")
    chk("and it is a dollar distance from a ratcheting peak, not a fraction (D542)",
        HP.max_drawdown_life(np.array([1000.0, -400.0]), 300.0)[:2] == (1, 2.0),
        "a from-zero reading sees +600 and never dies")
    chk("the segments cover the death, start to death index", segs == [(0, 1, 2)], f"{segs}")
    expect_raise(lambda: HP.max_drawdown_life(good, -1.0), "a NEGATIVE cap", ValueError)
    expect_raise(lambda: HP.max_drawdown_life(good, 0.0), "a ZERO cap", ValueError)

    P("\n== 2. p1_size: a number, never a verdict")
    s = HP.p1_size(good, 2_000.0)
    chk("the multiplier is cap / max trailing drawdown",
        abs(s["size_multiplier"] - 2000.0 / s["max_trailing_dd_usd"]) < 1e-12,
        f"dd ${s['max_trailing_dd_usd']:.0f} -> x{s['size_multiplier']:.3f}")
    chk("no PASS/FAIL key exists (R11 restatement 2026-09-08)",
        not any("pass" in k.lower() for k in s), f"{sorted(s)}")
    expect_raise(lambda: HP.p1_size(np.array([]), 2_000.0), "an EMPTY series", ValueError)
    expect_raise(lambda: HP.p1_size(good, -5.0), "a NEGATIVE cap", ValueError)
    expect_raise(lambda: HP.p1_size(np.array([1.0, 2.0, 3.0]), 2_000.0),
                 "a series that NEVER draws down", ValueError)
    expect_raise(lambda: HP.p1_size(np.array([1.0, np.nan]), 2_000.0),
                 "a NON-FINITE value", ValueError)

    P("\n== 3. p2_flatten: the venue's own clock, in ET")
    chk("a 15:59 ET exit clears MFFU's 16:10",
        HP.p2_flatten(["15:59", "16:10"], "mffu_rapid_eod_50k"))
    chk("[X] a 16:11 ET exit does NOT",
        not HP.p2_flatten(["15:59", "16:11"], "mffu_rapid_eod_50k"))
    expect_raise(lambda: HP.p2_flatten(["15:59"], "take_profit_trader_50k"),
                 "a venue whose flatten time is UNVERIFIED", ValueError)
    expect_raise(lambda: HP.p2_flatten([], "topstep_50k"), "an EMPTY set of exits", ValueError)
    expect_raise(lambda: HP.p2_flatten(["25:00"], "topstep_50k"), "an impossible ET time",
                 ValueError)
    expect_raise(lambda: HP.p2_flatten(["15:59"], "no_such_venue"), "an UNKNOWN venue", KeyError)

    P("\n== 4. p3: the rate, on a hand case")
    d = np.zeros(252)
    d[10] = -1200.0
    d[20:30] = 100.0
    g = HP.p3(d, 50_000.0)
    chk("one breach in exactly 252 sessions reads 1.00 a year",
        abs(g["p3a_breaches_per_year"] - 1.0) < 1e-12, f"{g['p3a_breaches_per_year']:.6f}")
    chk("and passes exactly AT the bar", g["p3a_pass"])
    d2 = d.copy()
    d2[40] = -1200.0
    chk("[X] two breaches in a year FAIL P3a", not HP.p3(d2, 50_000.0)["p3a_pass"],
        f"{HP.p3(d2, 50_000.0)['p3a_breaches_per_year']:.2f}/yr")
    chk("P3c is the worst day's share of the $2,000 budget",
        abs(g["p3c_share_of_loss_budget"] - 0.6) < 1e-12, f"{g['p3c_share_of_loss_budget']:.3f}")
    expect_raise(lambda: HP.p3(np.array([1.0]), 50_000.0), "a ONE-session series", ValueError)
    expect_raise(lambda: HP.p3(good, 0.0), "a ZERO account", ValueError)

    P("\n== 5. the UNIT boundary -- the slip that crashed D503's first run")
    pf, li = HP.expected_profit_before_breach_usd(0.72, 180.48, 50_000.0, 2_000.0)
    chk("dollars in, dollars out", pf > 0 and li > 0, f"${pf:,.0f} over {li:.1f} days")
    chk("and it equals the account-fraction form times the account",
        pf == HP.expected_profit_before_breach(0.72, 180.48 / 50_000.0, 0.04)[0] * 50_000.0)
    expect_raise(lambda: HP.expected_profit_before_breach_usd(0.72, 0.0036, 50_000.0),
                 "a FRACTION passed where dollars belong", ValueError)
    expect_raise(lambda: HP.expected_profit_before_breach_usd(0.72, 180.48, 0.0),
                 "a ZERO account", ValueError)
    expect_raise(lambda: HP.expected_profit_before_breach_usd(0.72, 180.48, 50_000.0, 60_000.0),
                 "a drawdown budget ABOVE the account", ValueError)

    P("\n== 6. p4_life: the basis IS the unit assertion")
    plan = HP.load_venue("mffu_rapid_eod_50k")
    lc = HP.p4_life(np.tile(good, 40), plan, basis="usd", n_paths=200, days=120)
    chk("a dollar series runs and reports the account's life, not a per-hold rate",
        lc["expected_life_days"] > 0 and "close-only" in lc["path_basis"],
        f"{lc['expected_life_days']:.0f} sessions")
    expect_raise(lambda: HP.p4_life(np.tile(good, 40), plan, basis="usd",
                                    target_dollar_vol=350.0),
                 "a dollar series handed a target vol", ValueError)
    expect_raise(lambda: HP.p4_life(np.tile(good, 40) / 50_000.0, plan, basis="return"),
                 "a RETURN series with no target vol", ValueError)
    expect_raise(lambda: HP.p4_life(np.tile(good, 40), plan, basis="usd", rule="voltgt"),
                 "a dollar series asked to vol-target", ValueError)
    expect_raise(lambda: HP.p4_life(np.tile(good, 40), plan, basis="usd",
                                    lows=np.zeros(320)),
                 "lows without highs", ValueError)

    P("\n== 7. p5_recognised: the 30% haircut")
    h = HP.p5_recognised(np.array([1000.0, 200.0, 200.0, 200.0, 200.0]))
    chk("a best day above 30% of the total is cut to the excess",
        abs(h["haircut_usd"] - (1000.0 - 0.30 * 1800.0)) < 1e-12
        and abs(h["recognised_usd"] - (1800.0 - 460.0)) < 1e-12,
        f"haircut ${h['haircut_usd']:.0f}, recognised ${h['recognised_usd']:.0f}")
    chk("[X] an even series is not cut at all",
        HP.p5_recognised(np.ones(100))["haircut_usd"] == 0.0)
    chk("a losing series has no recognised profit and no haircut",
        HP.p5_recognised(np.array([-1.0, -2.0]))["haircut_applies"] is False)

    P("\n== 8. the venue file")
    chk("14 venues load", len(HP.venue_keys()) == 14, f"{HP.venue_keys()}")
    chk("Apex forfeits on automation and therefore fails P6",
        not HP.p6("apex_50k")["p6_pass"] and HP.p6("topstep_50k")["p6_pass"])
    expect_raise(lambda: HP.load_venue("mffu_rapid_eod_999k"), "an UNKNOWN venue key", KeyError)

    P("\n== 9. component_series: the artefact round-trips, and a tampered CSV is caught")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        s = CS.DailyPnL(name="selftest", dates=("2016-01-04", "2016-01-05", "2016-01-06"),
                        usd=(1.5, -2.25, 0.0), size_label="1 MNQ", cost_line_usd_rt=3.0,
                        window=("2016-01-04", "2016-01-06"), spec="D590",
                        source_sha256="0" * 64)
        p = s.write(td)
        chk("write -> read returns an EQUAL object", CS.read(p) == s)
        chk("the newline is pinned to LF (D550)",
            b"\r\n" not in Path(p).read_bytes(), repr(Path(p).read_bytes()[:20]))
        Path(p).write_text(Path(p).read_text(encoding="utf-8").replace("1.5", "1.6"),
                           encoding="utf-8", newline="\n")
        expect_raise(lambda: CS.read(p), "a CSV edited after it was written", ValueError)
    expect_raise(lambda: CS.DailyPnL(name="x", dates=("2016-01-04", "2016-01-04"),
                                     usd=(1.0, 2.0), size_label="1 MNQ",
                                     cost_line_usd_rt=3.0,
                                     window=("2016-01-04", "2016-01-04"), spec="D590",
                                     source_sha256="0" * 64),
                 "a DUPLICATED session", ValueError)
    expect_raise(lambda: CS.DailyPnL(name="x", dates=("2016-01-05", "2016-01-04"),
                                     usd=(1.0, 2.0), size_label="1 MNQ",
                                     cost_line_usd_rt=3.0,
                                     window=("2016-01-04", "2016-01-05"), spec="D590",
                                     source_sha256="0" * 64),
                 "dates out of order", ValueError)

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--series", type=Path, help="a date,usd CSV (D590 artefact or bare)")
    ap.add_argument("--venue", type=str, help=f"one of {', '.join(HP.venue_keys())}")
    ap.add_argument("--account", type=float, default=HP.ACCOUNT_DEFAULT)
    ap.add_argument("--exit-times-et", type=str, default=None,
                    help="comma-separated HH:MM ET exit times, for P2")
    ap.add_argument("--paths", type=int, default=8_000)
    ap.add_argument("--days", type=int, default=600)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.series or not a.venue:
        ap.print_help()
        return 1
    exits = [t.strip() for t in a.exit_times_et.split(",")] if a.exit_times_et else None
    return report(a.series, a.venue, a.account, exits, a.paths, a.days)


if __name__ == "__main__":
    raise SystemExit(main())
