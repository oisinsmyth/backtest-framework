"""D469 -- the scalping re-cost R13 has owed since D258, on measured futures cost.

    uv run python scripts/d469_scalping_feasibility.py --self-test
    uv run python scripts/d469_scalping_feasibility.py --review [--json]

**A FEASIBILITY REVIEW, NOT A STRATEGY SCREEN.** It computes two things: what a scalp must
clear, and what the instrument actually offers at that horizon. **No signal, no entry rule,
no edge, no Sharpe.** Nothing is admitted or closed.

WHY THIS IS OWED
----------------
[R13](../docs/RULES.md#r13) §2, verbatim: constructions excluded on ETF cost arithmetic --
*"scalping, D247's intraday shorts, most of the intraday microstructure literature"* -- **clear
their costs by an order of magnitude on futures**, and *"a cross-screen must RE-COST, not
merely re-threshold."* [D258](../docs/decisions/D258-the-prop-track-candidates.md) is where
scalping was excluded: **31-187%/yr** on ETF costs, against ES futures at *"~$4-5 on ~$250k
notional = 0.2 bp"*.

**That 0.2 bp is COMMISSION ONLY.** D465 measured the half that was missing: crossing is
**0.364 bp round trip** on ES. So the futures cost D258 used to wave scalping through is
**2.8x understated**, and the re-cost R13 asks for has never been run on a measured number.

**AND THE SPREAD IS NOT WHAT BINDS.** It turns out commission is, and only at micro size,
which is the one size the component standard allows. See below.

THE THING THAT DECIDES IT, AND IT IS NOT THE SPREAD
---------------------------------------------------
`COMPONENTS_PROP.md` C-a scores a component at the instrument's **MINIMUM TRADABLE SIZE --
the micro**. Commission is charged **per contract**, and a micro's tick is worth **one tenth**
of its e-mini's. So the same commission that is a rounding error on ES dominates on MES:

    ES   1 tick = $12.50   crossing ~= 1 tick   commission ~$4/RT   -> breakeven ~1.4 ticks
    MES  1 tick =  $1.25   crossing ~= 1 tick   commission ~$3/RT   -> breakeven ~3.5 ticks

**A scalp scored under the component standard therefore faces a bar 2.5x higher than the same
scalp on the full-size contract.** That asymmetry is the review's central quantity and it is
arithmetic, not an estimate.

WHAT IS MEASURED HERE
---------------------
Against that bar, the **realised move distribution** at scalping horizons, from D465's cached
ES tick series (121,617,272 trades, 2025-09-11 -> 2026-09-10, front month by id WINDOW), on a
one-second last-trade grid. For each horizon: the distribution of |move| in ticks, and the
**directional accuracy a scalp would need** to clear cost -- at the real cost, and at a
hypothetical zero commission, because only the second is a fact about the market.

The accuracy figure is the review's output. It is a NECESSARY condition, not a sufficient one:
clearing it says the cost wall is passable, never that anything passes it.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


class GateError(AssertionError):
    """A validation gate refused the input. Raising, never a warning."""

REPO = Path(__file__).resolve().parents[1]
# v2 -- the cache with D465's instrument-id windows APPLIED. The v1 cache pooled two
# expiries priced ~60 points apart, and the first run of this review reported a p99 |move|
# of exactly 240 ticks at every horizon against a median of 2. That flat 240 was the
# calendar basis, not a move. A guard at this script's own door now refuses mixed input
# rather than trusting the upstream fix.
TICKS = REPO / "temp" / "d465_es_ticks_v2.npz"
OUT = REPO / "data" / "d469_scalping_feasibility.json"

SPECS = REPO / "data" / "futures_contract_specs.json"
PX_SCALE = 1e-9
TICK_PTS = 0.25

# COMMISSION IS NOT CME DATA. Contract geometry (usd_per_point, tick_usd) is read from
# data/futures_contract_specs.json, which came from CME's own ContractSpecs service.
# Commission is a BROKERAGE number and is declared here with its source:
#   MES $3.00 / round trip -- D466's declared cost line for K1
#   ES   $4.00 / round trip -- D258's "~$4-5 on ~$250k notional", low end
# Conflating the two would let a brokerage assumption borrow CME's authority.
COMMISSION_RT = {"MES": 3.00, "ES": 4.00}
COMMISSION_SRC = {"MES": "D466 declared cost line", "ES": "D258 '~$4-5', low end"}


def load_contracts() -> dict:
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    out = {}
    for name, comm in COMMISSION_RT.items():
        s = spec[name]
        if abs(s["tick_points"] - TICK_PTS) > 1e-12:
            raise GateError(f"[SPEC] {name} tick is {s['tick_points']}, not {TICK_PTS}")
        if abs(s["usd_per_point"] * s["tick_points"] - s["tick_usd"]) > 1e-9:
            raise GateError(f"[SPEC] {name} tick_usd disagrees with usd_per_point x tick")
        out[name] = {"usd_per_point": float(s["usd_per_point"]),
                     "tick_usd": float(s["tick_usd"]), "commission_rt": comm}
    if abs(out["ES"]["tick_usd"] / out["MES"]["tick_usd"] - 10.0) > 1e-9:
        raise GateError("[SPEC] the micro is not a tenth of the e-mini; the whole "
                        "commission-dominance argument rests on that ratio")
    return out


CONTRACTS = load_contracts()
# D465's measured round-trip crossing, READ from its artifact rather than copied. The
# copied value was 0.3664 and went stale the moment D465 was re-run on windowed ids
# (0.3644) -- a hardcoded constant is a silent fork of someone else's measurement.
D465_JSON = REPO / "data" / "d465_es_spread_and_mae_bias.json"


def crossing_bp_round_trip() -> float:
    d = json.loads(D465_JSON.read_text(encoding="utf-8"))
    half = float(d["spread"]["half_spread_bp_per_side"]["mean"])
    if not 0.05 < half < 1.0:
        raise GateError(f"[COST] half-spread {half} bp is outside any sane band for ES")
    return 2.0 * half


CROSS_BP_RT = crossing_bp_round_trip()
HORIZONS_S = (10, 30, 60, 120, 300, 900)


def P(*a, **k):
    print(*a, **k, flush=True)


def breakeven_ticks(name: str, px_level: float) -> dict:
    """What one round trip costs, in ticks, at a given price level."""
    c = CONTRACTS[name]
    notional = px_level * c["usd_per_point"]
    cross_usd = CROSS_BP_RT / 1e4 * notional
    total = cross_usd + c["commission_rt"]
    return {"notional_usd": notional, "crossing_usd": cross_usd,
            "commission_usd": c["commission_rt"], "total_usd": total,
            "breakeven_ticks": total / c["tick_usd"],
            "crossing_ticks": cross_usd / c["tick_usd"],
            "commission_ticks": c["commission_rt"] / c["tick_usd"]}


def need_p(G: float, C: float) -> float:
    """Directional accuracy to net zero: p*G - (1-p)*G = C  =>  p = (1 + C/G)/2."""
    return (1.0 + C / G) / 2.0


# Outcome model: the trade pays +|M| or -|M| with probability p, less a fixed cost C. Write
# q = (2p-1)*E|M| for the GROSS signed mean. Then, with S the sign and M independent of it,
#   E[X]   = q - C
#   E[X^2] = E[M^2] - 2*C*q + C^2
#   Var(X) = E[M^2] - 2*C*q + C^2 - (q-C)^2 = E[M^2] - q^2
# so the cost shifts the mean and leaves the variance alone, and
#   annualised Sharpe = sqrt(252*N) * (q - C) / sqrt(RMS^2 - q^2).
#
# TWO WRONG VERSIONS PRECEDED THIS, and both agreed with a simulation where I first checked
# them. The first put RMS in place of sigma; the second put the NET mean where the GROSS one
# belongs. Each was ~0.2% right at a small edge and ~7% wrong at a large one -- an
# approximation is at its most convincing exactly where it was tested.

def sharpe_of(q: float, cost: float, rms: float, n_day: float) -> float:
    var = rms * rms - q * q
    if var <= 0:
        return float("inf") if q > cost else float("-inf")
    return float(np.sqrt(252.0 * n_day) * (q - cost) / np.sqrt(var))


def q_for_sharpe(target: float, cost: float, rms: float, n_day: float) -> float:
    """Invert sharpe_of for the gross signed mean a target Sharpe needs.

    (q-C)^2 = k^2 (RMS^2 - q^2) with k = target/sqrt(252N) gives
        q = [C + k*sqrt((1+k^2)*RMS^2 - C^2)] / (1+k^2).
    """
    k = target / np.sqrt(252.0 * n_day)
    disc = (1.0 + k * k) * rms * rms - cost * cost
    if disc < 0:
        return float("nan")
    return float((cost + k * np.sqrt(disc)) / (1.0 + k * k))


# Each break perturbs the SCALAR a check reads -- not the check's name. Three duds in one
# session came from breaking a label instead of the number under it, so the verification
# below asserts the named checks go red and every OTHER check stays green.
BREAKS = {
    "cross":  ("crossing 5x the measured spread", ["ES crossing", "MES crossing"]),
    # the last two cascade truthfully: a micro tick worth an e-mini's also destroys the
    # scale-free crossing ratio, and a cut commission also destroys the 10x claim. The
    # first run of this harness listed only the direct target and the cascade showed up
    # as UNEXPECTED -- the declaration was incomplete, not the check.
    "tickval": ("micro tick worth the same as the e-mini's",
                ["MES crossing", "commission in ticks", "MICRO breakeven"]),
    "comm":   ("micro commission a tenth of the e-mini's",
               ["commission in ticks", "MICRO breakeven"]),
    "ident":  ("accuracy identity sign inverted",
               ["cost == move", "monotone in cost", "unreachable"]),
}


def run_checks(break_key: str | None, verbose: bool) -> dict[str, bool]:
    """Every check, returning label -> passed. Pure: restores globals it perturbs."""
    global CROSS_BP_RT
    saved_cross, saved = CROSS_BP_RT, {k: dict(v) for k, v in CONTRACTS.items()}
    if break_key == "cross":
        CROSS_BP_RT = CROSS_BP_RT * 5
    elif break_key == "tickval":
        CONTRACTS["MES"]["tick_usd"] = CONTRACTS["ES"]["tick_usd"]
    elif break_key == "comm":
        CONTRACTS["MES"]["commission_rt"] = CONTRACTS["ES"]["commission_rt"] / 10

    npf = (lambda G, C: (1.0 - C / G) / 2.0) if break_key == "ident" else need_p
    out: dict[str, bool] = {}

    def chk(label, cond, detail=""):
        out[label] = bool(cond)
        if verbose:
            P(f"    [{'PASS' if cond else 'FAIL'}] {label:56} {detail}")

    try:
        # crossing is ~1 tick on BOTH contracts: the spread is one tick and the tick value
        # scales with the contract, so the ratio is scale-free.
        es, mes = breakeven_ticks("ES", 7600.0), breakeven_ticks("MES", 7600.0)
        chk("ES crossing ~ 1 tick", abs(es["crossing_ticks"] - 1.0) < 0.2,
            f"{es['crossing_ticks']:.3f}")
        chk("MES crossing ~ 1 tick too (scale-free)", abs(mes["crossing_ticks"] - 1.0) < 0.2,
            f"{mes['crossing_ticks']:.3f}")
        chk("commission in ticks is 10x worse on the micro",
            mes["commission_ticks"] > 5 * es["commission_ticks"],
            f"{mes['commission_ticks']:.2f} vs {es['commission_ticks']:.2f}")
        chk("so the MICRO breakeven is the higher bar",
            mes["breakeven_ticks"] > es["breakeven_ticks"],
            f"{mes['breakeven_ticks']:.2f} vs {es['breakeven_ticks']:.2f} ticks")
        chk("accuracy identity: cost 0 needs 50%", abs(npf(4.0, 0.0) - 0.50) < 1e-12)
        chk("accuracy identity: cost == move needs 100%", abs(npf(4.0, 4.0) - 1.00) < 1e-12)
        chk("accuracy identity is monotone in cost", npf(4, 1) < npf(4, 2) < npf(4, 3))
        chk("a move at breakeven is unreachable (p > 1)", npf(2.0, 3.5) > 1.0,
            f"p = {npf(2.0, 3.5):.2f} -- no accuracy suffices")

        # THE IDENTITY THE REVIEW TURNS ON, checked against a simulation rather than
        # asserted in prose. Draw |M| from a fat-tailed law, sign it with accuracy p, pay
        # cost C per trade, and the realised annualised Sharpe must match
        # 2*(p-p_be)*sqrt(252*N)*E|M|/RMS.
        rng = np.random.default_rng(20260912)
        C_, N_, DAYS = 3.41, 100, 20_000
        m = rng.lognormal(mean=1.5, sigma=0.9, size=(DAYS, N_))
        e_abs_, rms_ = float(m.mean()), float(np.sqrt(np.mean(m ** 2)))
        p_be_ = (1.0 + C_ / e_abs_) / 2.0
        # BOTH SIGNS, and one sitting exactly at breakeven -- an identity verified only
        # where it is large and negative has not been verified where the review uses it.
        for tag, p_ in (("below p_be", p_be_ - 0.05), ("AT p_be", p_be_),
                        ("above p_be", p_be_ + 0.02)):
            sign = np.where(rng.random((DAYS, N_)) < p_, 1.0, -1.0)
            daily = (sign * m - C_).sum(axis=1)
            realised = float(daily.mean() / daily.std(ddof=1) * np.sqrt(252))
            pred = sharpe_of((2 * p_ - 1) * e_abs_, C_, rms_, N_)
            # TOLERANCE FROM THE SIMULATION'S OWN NOISE, not a guessed percentage. The
            # annualised Sharpe of T days has SE ~ sqrt(252*(1 + S_d^2/2)/T). A "2%" band
            # failed this check at 4,000 days on a discrepancy of 1.1 SE -- the formula was
            # right and the band was arbitrary.
            s_d = realised / np.sqrt(252.0)
            se = float(np.sqrt(252.0 * (1.0 + s_d * s_d / 2.0) / DAYS))
            chk(f"Sharpe identity, {tag}", abs(realised - pred) < 3.0 * se,
                f"predicted {pred:>8.3f} vs simulated {realised:>8.3f}  "
                f"({abs(realised-pred)/se:.2f} SE, band 3)")
        chk("fat tails penalise the identity (RMS > E|M|)", rms_ > e_abs_,
            f"RMS/E|M| = {rms_/e_abs_:.2f}")
        # and the inversion must round-trip, or the margin the review reports is wrong
        q_t = q_for_sharpe(0.5, C_, rms_, N_)
        chk("q_for_sharpe inverts sharpe_of",
            abs(sharpe_of(q_t, C_, rms_, N_) - 0.5) < 1e-9,
            f"q {q_t:.4f} ticks -> Sharpe {sharpe_of(q_t, C_, rms_, N_):.6f}")
        chk("q_for_sharpe at target 0 returns the breakeven q = C",
            abs(q_for_sharpe(0.0, C_, rms_, N_) - C_) < 1e-9)

        # the input gate, on the scalar it actually reads. This review's FIRST run reported
        # a p99 of exactly 240 ticks at every horizon because nothing checked this.
        s = np.array([1, 1, 2, 2, 3, 3], dtype=np.int64)
        chk("input gate passes one expiry per second",
            one_expiry_per_second(s, np.array([10, 10, 10, 10, 11, 11])) == 0)
        chk("input gate FIRES on two expiries in one second",
            one_expiry_per_second(s, np.array([10, 11, 10, 10, 11, 11])) == 1,
            "the check whose absence made the basis look like a move")
    finally:
        CROSS_BP_RT = saved_cross
        for k, v in saved.items():
            CONTRACTS[k] = v
    return out


def do_self_test() -> int:
    clean = run_checks(None, verbose=True)
    fails = [k for k, ok in clean.items() if not ok]
    if fails:
        P(f"\n  SELF-TEST FAILED on the unbroken case: {fails}")
        return 1

    P("\n  and each check PROVEN to fail when the scalar it reads is perturbed:")
    bad = []
    for key, (what, must_fail) in BREAKS.items():
        got = run_checks(key, verbose=False)
        reds = [k for k, ok in got.items() if not ok]
        hit = all(any(m in r for r in reds) for m in must_fail)
        # a break must go red ONLY where claimed -- a break that reddens everything
        # proves nothing about the individual check
        extra = [r for r in reds if not any(m in r for m in must_fail)]
        ok = hit and not extra
        P(f"    [{'PASS' if ok else 'FAIL'}] break {key:8} {what:44} "
          f"{len(reds)} red{'' if not extra else '  UNEXPECTED: ' + str(extra)}")
        if not ok:
            bad.append(key)
    if bad:
        P(f"\n  SELF-TEST FAILED: breaks that did not fire as claimed: {bad}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def one_expiry_per_second(sec: np.ndarray, iid: np.ndarray) -> int:
    """Seconds carrying more than one instrument_id. Must be 0 before any path is walked."""
    _, first = np.unique(sec, return_index=True)
    i = iid.astype(np.int64)
    return int((np.maximum.reduceat(i, first) != np.minimum.reduceat(i, first)).sum())


def do_review(as_json: bool) -> int:
    if not TICKS.exists():
        raise SystemExit(f"missing {TICKS}; run d465 --extract")
    z = np.load(TICKS)
    if "iid" not in z:
        raise GateError("[INPUT] cache carries no instrument_id -- this is the v1 cache "
                        "that pooled expiries; re-run d465 --extract")
    ts, px = z["ts"], z["px"].astype(np.float64) * PX_SCALE
    iid = z["iid"]
    good = px > 0
    ts, px, iid = ts[good], px[good], iid[good]
    level = float(np.median(px))
    P(f"ES ticks {len(px):,}   median price {level:,.2f}   "
      f"{len(np.unique(iid))} expiries, windowed")

    # ---- the cost bar ----
    P(f"  {'':6}{'notional':>12}{'crossing':>11}{'commission':>12}{'total':>9}"
      f"{'= ticks':>9}{'  (cross / comm)':>18}")
    bars = {}
    for name in ("ES", "MES"):
        b = breakeven_ticks(name, level)
        bars[name] = b
        P(f"  {name:6}{b['notional_usd']:>12,.0f}{b['crossing_usd']:>11.2f}"
          f"{b['commission_usd']:>12.2f}{b['total_usd']:>9.2f}"
          f"{b['breakeven_ticks']:>9.2f}"
          f"   {b['crossing_ticks']:.2f} / {b['commission_ticks']:.2f}")
    P("\n  D258 waved scalping through on '~0.2 bp' for futures -- COMMISSION ONLY.")
    mb = bars["MES"]
    P(f"  At micro size the total is {mb['total_usd'] / mb['crossing_usd']:.1f}x the crossing "
      f"alone: commission is {mb['commission_ticks']:.1f} of the "
      f"{mb['breakeven_ticks']:.1f} ticks.")

    # ---- the available move: one-second last-trade grid ----
    sec = (ts // 1_000_000_000).astype(np.int64)
    n_mixed = one_expiry_per_second(sec, iid)
    if n_mixed:
        raise GateError(f"[INPUT] {n_mixed:,} seconds carry two expiries; a cross-record "
                        f"move on this input measures the calendar basis, not a move")
    P(f"  one expiry per second on every second  [INPUT ok]")

    uniq_sec, first_idx = np.unique(sec, return_index=True)
    last_of = np.append(first_idx[1:], len(px)) - 1            # last trade in each second
    last_px, last_id = px[last_of], iid[last_of]
    P(f"  one-second grid: {len(uniq_sec):,} seconds with a trade")

    rows = {}
    for h in HORIZONS_S:
        # match seconds exactly h apart, so a gap does not become a fake move
        pos = np.searchsorted(uniq_sec, uniq_sec + h)
        ok = (pos < len(uniq_sec)) & (uniq_sec[np.clip(pos, 0, len(uniq_sec) - 1)] == uniq_sec + h)
        j = np.clip(pos, 0, len(uniq_sec) - 1)
        # AND both ends must be the SAME contract. The windows leave one roll instant per
        # quarter where a pair would straddle two expiries -- four pairs of that kind would
        # each read ~240 ticks and land squarely in the p99 this review turns on.
        ok &= last_id == last_id[j]
        a, b = last_px[ok], last_px[j[ok]]
        signed = (b - a) / TICK_PTS
        mv = np.abs(signed)
        if len(mv) < 1000:
            continue

        # UNCONDITIONAL, and that is the whole point. The first run of this review took the
        # mean move AMONG pairs that cleared the cost bar -- which is look-ahead: no rule
        # can select a trade by the move it turned out to make. `share_exceeding` is kept
        # below as description only and is NOT an input to any requirement.
        e_abs = float(mv.mean())
        rms = float(np.sqrt(np.mean(signed ** 2)))
        # always-in trade rate at this horizon over a 23h Globex day
        n_day = 23 * 3600 / h
        # THE IRREDUCIBLE FLOOR. Commission is a broker variable; the half-spread is not.
        # Crossing is ~1.01 ticks on BOTH contracts (the ratio is scale-free), so this
        # single column is what no brokerage deal, and no contract size, can improve.
        cross_ticks = bars["MES"]["crossing_ticks"]
        r = {"n_pairs": int(len(mv)), "mean_abs_ticks": e_abs, "rms_ticks": rms,
             "fat_tail_ratio_rms_over_mean": rms / e_abs,
             "p50": float(np.median(mv)), "p90": float(np.quantile(mv, .9)),
             "p99": float(np.quantile(mv, .99)),
             "trades_per_day_always_in": n_day,
             "crossing_only_ticks": cross_ticks,
             "breakeven_accuracy_at_ZERO_commission": (1.0 + cross_ticks / e_abs) / 2.0}
        for name in ("ES", "MES"):
            be = bars[name]["breakeven_ticks"]
            # p to net zero on the UNCONDITIONAL move
            p_be = (1.0 + be / e_abs) / 2.0
            # the gross signed mean C-a's Sharpe 0.5 needs, then the accuracy delivering it
            q_t = q_for_sharpe(0.5, be, rms, n_day)
            p_need = (1.0 + q_t / e_abs) / 2.0
            r[name] = {"breakeven_ticks": be,
                       "share_exceeding_descriptive_only": float((mv > be).mean()),
                       "breakeven_accuracy": p_be,
                       "q_ticks_for_sharpe_0p5": q_t,
                       "accuracy_needed_for_sharpe_0p5": float(p_need),
                       "accuracy_margin_over_breakeven_pp": float((p_need - p_be) * 100),
                       "reachable": bool(p_need < 1.0)}
        rows[h] = r

    P("\n  realised |move| in ticks (UNCONDITIONAL -- selecting on the realised move "
      "would be look-ahead):")
    P(f"  {'horizon':>9}{'pairs':>12}{'E|M|':>7}{'RMS':>8}{'p50':>6}{'p90':>7}"
      f"{'p99':>7}{'trades/d':>10}")
    for h, r in rows.items():
        lab = f"{h}s" if h < 60 else f"{h//60}m"
        P(f"  {lab:>9}{r['n_pairs']:>12,}{r['mean_abs_ticks']:>7.2f}{r['rms_ticks']:>8.1f}"
          f"{r['p50']:>6.1f}{r['p90']:>7.1f}{r['p99']:>7.1f}"
          f"{r['trades_per_day_always_in']:>10,.0f}")

    P("\n  the directional accuracy a scalp must hold. 'need p' reaches C-a's Sharpe 0.5;")
    P("  'free' is the floor if commission were ZERO -- the half-spread alone, and the one")
    P("  column no brokerage deal and no contract size can improve:")
    P(f"  {'horizon':>9}{'free':>9}   {'ES: BE tk':>10}{'p_be':>8}{'need p':>9}"
      f"   {'MES: BE tk':>11}{'p_be':>8}{'need p':>9}")
    for h, r in rows.items():
        lab = f"{h}s" if h < 60 else f"{h//60}m"
        e, m = r["ES"], r["MES"]
        P(f"  {lab:>9}{r['breakeven_accuracy_at_ZERO_commission']:>9.1%}"
          f"   {e['breakeven_ticks']:>10.2f}{e['breakeven_accuracy']:>8.1%}"
          f"{e['accuracy_needed_for_sharpe_0p5']:>9.1%}"
          f"   {m['breakeven_ticks']:>11.2f}{m['breakeven_accuracy']:>8.1%}"
          f"{m['accuracy_needed_for_sharpe_0p5']:>9.1%}")

    # where does the MICRO become plausible at all? solve E|M| for a stated accuracy.
    be_m = bars["MES"]["breakeven_ticks"]
    for target in (0.60, 0.55):
        need_move = be_m / (2.0 * target - 1.0)
        # E|M| grows ~sqrt(h); calibrate the exponent off the measured 1m and 15m rows
        h1, h2 = 60, 900
        if h1 in rows and h2 in rows:
            a1, a2 = rows[h1]["mean_abs_ticks"], rows[h2]["mean_abs_ticks"]
            beta = np.log(a2 / a1) / np.log(h2 / h1)
            h_star = h1 * (need_move / a1) ** (1.0 / beta)
            P(f"\n  MES breaks even at {target:.0%} accuracy only once E|M| reaches "
              f"{need_move:.1f} ticks -- about {h_star/60:.0f} minutes "
              f"(E|M| ~ h^{beta:.2f}, fitted on the 1m and 15m rows).")

    # ---------------- does selecting on PREDICTABLE volatility lower the wall? ----------
    #
    # p_be = (1 + cost/E|M|)/2 falls when the MOVE grows, not only when accuracy improves.
    # Volatility is one of the few genuinely forecastable quantities (direction is not), so
    # the question is whether conditioning on it buys a lower cost bar.
    #
    # THE CONDITIONER MUST BE KNOWN AT ENTRY. Bucketing on the window's OWN move is the
    # look-ahead this review already committed once. Here the bucket is the move over the
    # PRECEDING h seconds -- observable at t -- and the measured quantity is the move over
    # the FOLLOWING h seconds.
    cond = {}
    for h in (300, 900):
        pos_f = np.searchsorted(uniq_sec, uniq_sec + h)
        pos_b = np.searchsorted(uniq_sec, uniq_sec - h)
        okf = (pos_f < len(uniq_sec)) & (uniq_sec[np.clip(pos_f, 0, len(uniq_sec) - 1)]
                                         == uniq_sec + h)
        okb = (pos_b < len(uniq_sec)) & (uniq_sec[np.clip(pos_b, 0, len(uniq_sec) - 1)]
                                         == uniq_sec - h)
        jf = np.clip(pos_f, 0, len(uniq_sec) - 1)
        jb = np.clip(pos_b, 0, len(uniq_sec) - 1)
        ok = okf & okb & (last_id == last_id[jf]) & (last_id == last_id[jb])
        past = np.abs(last_px[ok] - last_px[jb[ok]]) / TICK_PTS       # known at t
        fwd = np.abs(last_px[jf[ok]] - last_px[ok]) / TICK_PTS        # measured after t
        fwd_s = (last_px[jf[ok]] - last_px[ok]) / TICK_PTS
        if len(past) < 10_000:
            continue
        edges = np.quantile(past, [0, .2, .4, .6, .8, 1.0])
        be_m = bars["MES"]["breakeven_ticks"]
        lab = f"{h//60}m"
        P(f"\n  {lab} forward move, bucketed on the PRECEDING {lab} move (known at entry):")
        P(f"  {'quintile':>10}{'n':>11}{'past |M|':>10}{'fwd E|M|':>10}"
          f"{'MES p_be':>10}{'corr':>8}")
        rowsc = []
        for k in range(5):
            m = (past >= edges[k]) & (past <= edges[k + 1] if k == 4 else past < edges[k + 1])
            if m.sum() < 1000:
                continue
            e_f = float(fwd[m].mean())
            rms_f = float(np.sqrt(np.mean(fwd_s[m] ** 2)))
            p_b = (1.0 + be_m / e_f) / 2.0
            # trades a day if this quintile is the only moment traded
            n_q = (23 * 3600 / h) * (m.sum() / len(past))
            rowsc.append({"quintile": k + 1, "n": int(m.sum()),
                          "past_mean_abs_ticks": float(past[m].mean()),
                          "fwd_mean_abs_ticks": e_f, "fwd_rms_ticks": rms_f,
                          "trades_per_day_this_quintile_only": n_q,
                          "MES_breakeven_accuracy": p_b,
                          # THE SENSITIVITY THAT DECIDES IT. Sharpe against accuracy, held
                          # at this bucket's own move distribution and trade rate.
                          "sharpe_by_accuracy": {
                              f"{p:.3f}": sharpe_of((2 * p - 1) * e_f, be_m, rms_f, n_q)
                              for p in (0.52, 0.54, 0.55, 0.56, 0.57, 0.58, 0.60)}})
            P(f"  {k+1:>10}{m.sum():>11,}{past[m].mean():>10.1f}{e_f:>10.1f}"
              f"{p_b:>10.1%}"
              f"{'' if k else f'  {np.corrcoef(past, fwd)[0,1]:.3f}':>8}")
        cond[h] = rowsc
        # how steep is the cliff? the whole outcome lives in a 1-2 pp band of accuracy.
        if rowsc:
            top = rowsc[-1]
            P(f"\n    top quintile, {lab} hold, {top['trades_per_day_this_quintile_only']:.0f} "
              f"trades/day -- Sharpe against directional accuracy:")
            P("      " + "".join(f"{k:>9}" for k in top["sharpe_by_accuracy"]))
            P("      " + "".join(f"{v:>9.2f}" for v in top["sharpe_by_accuracy"].values()))

    # C-d is what FORCES the micro, so it is computed rather than asserted.
    P("\n  C-d, daily sigma at minimum size against 1% of a $50k account ($500):")
    for name in ("ES", "MES"):
        c = CONTRACTS[name]
        # one-day sigma of the instrument itself, from the 15m row scaled to a day
        r15 = rows.get(900)
        if not r15:
            continue
        sig_day = r15["rms_ticks"] * np.sqrt(23 * 3600 / 900) * c["tick_usd"]
        P(f"    {name:4} one contract, held flat all day: sigma ~${sig_day:>8,.0f}   "
          f"{'FITS' if sig_day <= 500 else 'BREACHES'} the $500 cap "
          f"({sig_day/500:.1f}x)")
    P("    -> the micro is not a conservative choice, it is the only size C-d admits.")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "purpose": "D469: the scalping re-cost R13 has owed since D258, on the measured "
                      "futures cost line. A feasibility review -- no signal, no edge, no "
                      "Sharpe; nothing admitted or closed.",
           "source": "D465's cached ES front-month ticks, 2025-09-11..2026-09-11",
           "median_price": level, "crossing_bp_round_trip_measured": CROSS_BP_RT,
           "cost_bars": bars, "by_horizon_seconds": rows,
           "conditioned_on_trailing_move": cond,
           "note_on_conditioning": "quintiles of the PRECEDING h-second absolute move, "
                                   "which is observable at entry; the measured quantity is "
                                   "the FOLLOWING h-second move. Bucketing on the window's "
                                   "own move would be the look-ahead this review already "
                                   "made once. Lowering p_be this way needs no directional "
                                   "skill -- it only needs the trade to happen when moves "
                                   "are large -- but it selects the moments that are hardest "
                                   "to get filled in, which this does NOT measure.",
           "identity": "annualised Sharpe = 2*(p - p_be)*sqrt(252*N)*E|M|/RMS, for N "
                       "round trips a day at directional accuracy p, where "
                       "p_be = (1 + cost/E|M|)/2. Inverting it at Sharpe 0.5 gives the "
                       "accuracy MARGIN above breakeven that C-a demands.",
           "assumptions_of_that_identity": [
               "the trade outcome is the full h-second move, signed by the call -- an "
               "upper bound on what any exit rule captures",
               "trades are independent across the day; overlapping or clustered entries "
               "would lower the effective N",
               "no slippage beyond the measured half-spread, and no queue position",
               "the move distribution is stationary over the measured year"],
           "note_on_accuracy": "breakeven_accuracy uses the UNCONDITIONAL mean absolute "
                               "move. An earlier version used the mean among pairs that "
                               "cleared the cost bar, which is look-ahead: no rule can "
                               "select a trade by the move it turned out to make. "
                               "share_exceeding is descriptive only and feeds nothing.",
           "window_caveat": "measured on 2025-09-11..2026-09-11, which is NOT the "
                            "in-sample window a component is scored on (2016-01-04.."
                            "2023-12-29, D462). The unconditional move distribution "
                            "carries no rule and no selection, so it cannot spend the "
                            "confirmation slice -- but any actual scalp must be scored "
                            "on the in-sample window."}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.review:
        return do_review(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
