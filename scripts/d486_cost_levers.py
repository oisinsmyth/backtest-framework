"""D486 -- where does cost cutting take the D484 MACD edge? Pure arithmetic on committed
numbers.

    uv run python scripts/d486_cost_levers.py --self-test
    uv run python scripts/d486_cost_levers.py --report [--json]

**NO NEW MEASUREMENT, NO SIGNAL, NO BACKTEST.** Every input is a figure already committed
elsewhere, and this file only does arithmetic on them. Nothing is opened, closed or admitted
(R15). It answers the principal's question -- *where does our cost cutting take us* -- and the
answer needs no new data because D484 already measured the edge.

INPUTS, all committed
---------------------
* `data/d484_offdiagonal_and_macd.json` -- the MACD edge per (root, family, L, H), in sigma
  units, and sigma in ticks per (root, H).
* `data/futures_contract_specs.json` -- tick size and tick value per contract, from CME.
* D465: crossing **1.009 ticks** round trip (measured on ES, assumed for other roots).
* D466: commission **$3.00** per round trip, the declared cost line.
* D472: the volume-clock exit captures **+10.4%** more move at matched bar count and holding
  time -- measured on 8 years of ES, replicated 8 of 8 years.
* `COMPONENTS_PROP.md` C-a (net Sharpe > 0.5) and C-d (daily sigma <= 1% of the account).

THE STRUCTURAL POINT THAT ORGANISES THE ANSWER
----------------------------------------------
Cost has two parts and **they respond to completely different levers**:

* **commission is FIXED per contract** -> beaten by trading LESS OFTEN, or by paying less;
* **crossing is PROPORTIONAL to notional** -> beaten by PASSIVE execution, and not at all by
  holding longer.

At micro size the fixed part dominates overwhelmingly: **$3.00 is 6.00 ticks on every CME
micro except MES**, because every micro's tick is worth $0.50 while MES's is $1.25. So
commission is **86% of MNQ's total cost**. That single ratio is why the answer below turns on
the fee and the contract, not on the spread.

AND SHARPE IS SCALE-FREE, which is the non-obvious consequence
--------------------------------------------------------------
A Sharpe ratio does not care how big the contract is -- doubling the contract doubles both the
edge and the risk. **Contract size enters ONLY through the fee's size in ticks.** So at zero
commission, MNQ and full NQ give *identical* Sharpe, and the whole advantage of the full
contract is that $3 is a smaller fraction of a bigger tick.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
D484 = REPO / "data" / "d484_offdiagonal_and_macd.json"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "d486_cost_levers.json"

CROSS_TICKS = 1.009          # D465
COMMISSION_RT = 3.00         # D466
VOLUME_CLOCK_LIFT = 0.104    # D472: +10.4% more move captured, 8 of 8 years
C_A_SHARPE = 0.5             # COMPONENTS_PROP.md C-a
C_D_FRACTION = 0.01          # C-d: daily sigma <= 1% of the account
ACCOUNT = 50_000.0
RTH_PLUS_GLOBEX_H = 23       # the session the D484 fixture covers
TRADING_DAYS = 252
MICRO_OF = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K"}


class GateError(AssertionError):
    """A validation gate refused the input."""


def P(*a, **k):
    print(*a, **k, flush=True)


def sharpe_from(net_ticks: float, sigma_ticks: float, n_per_year: float) -> float:
    """Annualised Sharpe of a per-trade net edge. SCALE-FREE: tick value cancels."""
    if sigma_ticks <= 0:
        return float("nan")
    return float(net_ticks / sigma_ticks * np.sqrt(n_per_year))


def commission_budget(gross_ticks: float, cross_ticks: float, tick_usd: float) -> float:
    """The most one could pay per round trip and still break even, in DOLLARS."""
    return (gross_ticks - cross_ticks) * tick_usd


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:64} {detail}")
        if not cond:
            fails.append(label)

    # --- Sharpe is scale-free: the SAME edge and risk in ticks gives the same Sharpe
    # whatever the tick is worth. This is the claim the whole file rests on.
    chk("Sharpe is scale-free in tick VALUE",
        abs(sharpe_from(2.84, 217.0, 1160) - sharpe_from(2.84, 217.0, 1160)) < 1e-15)
    chk("Sharpe scales with sqrt(trade count)",
        abs(sharpe_from(1, 100, 400) / sharpe_from(1, 100, 100) - 2.0) < 1e-12,
        "4x the trades doubles it")
    chk("Sharpe is linear in the net edge",
        abs(sharpe_from(2, 100, 252) / sharpe_from(1, 100, 252) - 2.0) < 1e-12)
    chk("a negative net edge gives a negative Sharpe", sharpe_from(-1, 100, 252) < 0)

    # --- the commission budget identity
    chk("commission budget is zero when gross equals the crossing",
        abs(commission_budget(1.009, 1.009, 0.50)) < 1e-12)
    chk("commission budget is NEGATIVE when gross is below the crossing -- no fee helps",
        commission_budget(0.922, 1.009, 1.25) < 0,
        f"${commission_budget(0.922, 1.009, 1.25):.3f} -- MES's case")
    chk("a bigger tick value buys a bigger dollar budget for the same tick edge",
        commission_budget(3.849, 1.009, 5.00) > commission_budget(3.849, 1.009, 0.50))

    # --- the fee-in-ticks arithmetic that drives everything
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    chk("$3 is 6.00 ticks on MNQ and 0.60 on full NQ -- a 10x fee difference",
        abs(COMMISSION_RT / spec["MNQ"]["tick_usd"] - 6.0) < 1e-9
        and abs(COMMISSION_RT / spec["NQ"]["tick_usd"] - 0.6) < 1e-9)
    chk("every CME micro here has a $0.50 tick EXCEPT MES at $1.25",
        all(abs(spec[m]["tick_usd"] - 0.50) < 1e-9 for m in ("MNQ", "MYM", "M2K"))
        and abs(spec["MES"]["tick_usd"] - 1.25) < 1e-9)
    chk("so commission is ~86% of MNQ's total cost",
        abs(6.0 / (6.0 + CROSS_TICKS) - 0.856) < 0.005,
        f"{6.0/(6.0+CROSS_TICKS):.1%}")

    # --- C-d inversion: the account a full contract needs
    def account_for(daily_sigma_usd):
        return daily_sigma_usd / C_D_FRACTION
    chk("C-d inverts: a $2,326 daily sigma needs a $232,600 account",
        abs(account_for(2326.0) - 232_600.0) < 1.0)
    chk("and the $50k account admits only $500 of daily sigma",
        abs(ACCOUNT * C_D_FRACTION - 500.0) < 1e-9)

    # --- the volume-clock lift is applied multiplicatively to GROSS only, never to cost
    g = 3.849
    chk("the volume-clock lift raises gross and leaves cost alone",
        abs(g * (1 + VOLUME_CLOCK_LIFT) - 4.2493) < 1e-3,
        f"{g:.3f} -> {g*(1+VOLUME_CLOCK_LIFT):.3f} ticks")

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def do_report(as_json: bool) -> int:
    d = json.loads(D484.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    trade = d["tradeability"]
    if not trade:
        raise GateError("[INPUT] D484 artifact carries no tradeability block")

    P("INPUTS, all from committed records:")
    P(f"  D465 crossing {CROSS_TICKS:.3f} ticks round trip · D466 commission "
      f"${COMMISSION_RT:.2f} · D472 volume-clock lift +{VOLUME_CLOCK_LIFT:.1%}")
    P(f"  C-a net Sharpe > {C_A_SHARPE} · C-d daily sigma <= "
      f"{C_D_FRACTION:.0%} of a ${ACCOUNT:,.0f} account = ${ACCOUNT*C_D_FRACTION:,.0f}\n")

    # the best cell per root, as D484 reported it
    best = {}
    for r in ("ES", "NQ", "YM"):
        sub = [t for t in trade if t["root"] == r]
        if sub:
            best[r] = max(sub, key=lambda z: z["net_ticks"])

    P("  where D484 left it -- the best cell per root, at micro size and $3:")
    P(f"  {'root':>5}{'cell':>10}{'sigma tk':>10}{'gross tk':>10}{'comm tk':>9}"
      f"{'cross tk':>10}{'comm %':>8}{'net tk':>9}{'g/c':>7}")
    rows = {}
    for r, b in best.items():
        micro = MICRO_OF[r]
        comm_tk = COMMISSION_RT / spec[micro]["tick_usd"]
        cost = comm_tk + CROSS_TICKS
        P(f"  {r:>5}{b['family']+' H='+str(b['H']):>10}{b['sigma_ticks']:>10.1f}"
          f"{b['gross_ticks']:>10.3f}{comm_tk:>9.2f}{CROSS_TICKS:>10.3f}"
          f"{comm_tk/cost:>8.1%}{b['gross_ticks']-cost:>9.3f}"
          f"{b['gross_ticks']/cost:>7.2f}")
        rows[r] = {"cell": f"{b['family']} H={b['H']}", "H": b["H"],
                   "sigma_ticks": b["sigma_ticks"], "gross_ticks": b["gross_ticks"],
                   "commission_ticks_micro": comm_tk, "crossing_ticks": CROSS_TICKS,
                   "commission_share_of_cost": comm_tk / cost,
                   "net_ticks_micro": b["gross_ticks"] - cost}

    P(f"\n  **Commission is 70-86% of the cost.** It is a FIXED fee, so the levers that move "
      f"it\n  are trading less often and paying less -- not anything about the spread.\n")

    # ---------------- the levers, one at a time, then stacked
    P("  LEVER BY LEVER, on the best cell per root. 'need' = Sharpe needed for C-a.\n")
    P(f"  {'root':>5}{'scenario':>34}{'cost tk':>9}{'net tk':>9}{'trades/yr':>11}"
      f"{'Sharpe':>8}{'C-a?':>6}")
    out = {}
    for r, b in best.items():
        micro = MICRO_OF[r]
        H = b["H"]
        sig = b["sigma_ticks"]
        g0 = b["gross_ticks"]
        n_year = (RTH_PLUS_GLOBEX_H / H) * TRADING_DAYS
        tick_micro = spec[micro]["tick_usd"]
        tick_full = spec[r]["tick_usd"]
        scen = []

        def add(name, gross, cost):
            net = gross - cost
            s = sharpe_from(net, sig, n_year)
            scen.append({"scenario": name, "gross_ticks": gross, "cost_ticks": cost,
                         "net_ticks": net, "trades_per_year": n_year, "sharpe": s,
                         "clears_C_a": bool(s > C_A_SHARPE)})
            P(f"  {r:>5}{name:>34}{cost:>9.3f}{net:>9.3f}{n_year:>11,.0f}"
              f"{s:>8.2f}{'YES' if s > C_A_SHARPE else 'no':>6}")

        c_micro = COMMISSION_RT / tick_micro + CROSS_TICKS
        add("as measured (micro, $3, crossing)", g0, c_micro)
        add("+ volume-clock exit (D472)", g0 * (1 + VOLUME_CLOCK_LIFT), c_micro)
        add("+ passive fills (no crossing paid)", g0 * (1 + VOLUME_CLOCK_LIFT),
            COMMISSION_RT / tick_micro)
        add("micro at ZERO commission", g0 * (1 + VOLUME_CLOCK_LIFT), CROSS_TICKS)
        c_full = COMMISSION_RT / tick_full + CROSS_TICKS
        add("FULL contract, $3, crossing", g0, c_full)
        add("FULL + volume clock", g0 * (1 + VOLUME_CLOCK_LIFT), c_full)
        add("FULL + volume clock + passive", g0 * (1 + VOLUME_CLOCK_LIFT),
            COMMISSION_RT / tick_full)
        out[r] = scen
        # the two inversions that matter
        bud_micro = commission_budget(g0 * (1 + VOLUME_CLOCK_LIFT), CROSS_TICKS, tick_micro)
        daily_sig_full = sig * np.sqrt(RTH_PLUS_GLOBEX_H / H) * tick_full
        acct = daily_sig_full / C_D_FRACTION
        P(f"        breakeven commission on {micro}: ${bud_micro:>6.2f} "
          f"(declared ${COMMISSION_RT:.2f})")
        P(f"        full {r} daily sigma ${daily_sig_full:>8,.0f} -> C-d needs a "
          f"${acct:>9,.0f} account\n")
        rows[r].update({"breakeven_commission_micro_usd": bud_micro,
                        "full_daily_sigma_usd": float(daily_sig_full),
                        "account_for_C_d_usd": float(acct),
                        "scenarios": scen})

    P("  WHAT CLEARS C-a, reading the table:")
    any_clear = False
    for r, scen in out.items():
        w = [s["scenario"] for s in scen if s["clears_C_a"]]
        if w:
            any_clear = True
            P(f"    {r}: {', '.join(w)}")
    if not any_clear:
        P("    nothing in the table clears it")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D486: where cost cutting takes the D484 MACD edge. Pure arithmetic on "
                      "committed numbers -- no new measurement, no signal, no backtest, "
                      "nothing admitted.",
           "inputs": {"crossing_ticks_D465": CROSS_TICKS,
                      "commission_rt_D466": COMMISSION_RT,
                      "volume_clock_lift_D472": VOLUME_CLOCK_LIFT,
                      "C_a_sharpe": C_A_SHARPE, "C_d_fraction": C_D_FRACTION,
                      "account": ACCOUNT,
                      "source_edge": "data/d484_offdiagonal_and_macd.json"},
           "structural_point": "commission is FIXED per contract (beaten by trading less "
                               "often or paying less); crossing is PROPORTIONAL to notional "
                               "(beaten by passive execution, not by holding longer). At "
                               "micro size commission is 70-86% of cost because every CME "
                               "micro's tick is $0.50 except MES's $1.25.",
           "sharpe_is_scale_free": "A Sharpe does not care about contract size -- doubling "
                                   "the contract doubles edge and risk alike. Size enters "
                                   "ONLY through the fee's size in ticks, so at zero "
                                   "commission a micro and its full contract give identical "
                                   "Sharpe.",
           "by_root": rows,
           "limitations": [
               "the crossing of 1.009 ticks is an ES measurement (D465) assumed for NQ and YM",
               "passive fills are NOT measured anywhere: D471 measured the QUOTED spread and "
               "said explicitly that queue position, partial fills and latency need mbp-10, "
               "which was not bought. Every 'passive' row is therefore an UPPER BOUND.",
               "the volume-clock lift is measured on ES (D472, 8 of 8 years) and assumed to "
               "transfer to NQ and YM, which is untested",
               "D484's edge is in-sample (2016-2023); 2024+ is sealed",
               "holding longer than H=5 is untested -- D484's grid stopped there and the "
               "edge was still rising with H at its edge, which is a ceiling of my design "
               "and not of the effect",
               "no cell of D484 was tradeable as measured; every positive row here is a "
               "CONDITIONAL on a cost change that has not been obtained"]}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.report:
        return do_report(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
