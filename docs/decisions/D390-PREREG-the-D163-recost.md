# D390 PRE-REGISTRATION — re-costing D163's sub-hourly closure at futures commission

**Status:** Pre-registered — committed before the runner exists (CLAUDE.md habit, R8's discipline)
**Date:** 2026-09-08
**Category:** Validation & research integrity
**Discharges:** [R11](../RULES.md#r11)'s standing corollary — *"every construction this programme
excluded on cost arithmetic must be re-costed before it stays excluded"* — for the Donchian
channel breakout down the frequency ladder.

---

## Why

[D163](D163-sub-hourly-is-a-turnover-measurement-not-a-result.md) closed the 15m/30m rungs of the
breakout ladder on one sentence: at 15m the rule turns over ~790×/yr and *"pays roughly 300% of
capital a year in fees at the taker tier"*, and *"there is no fee tier in this study at which a
rule paying a triple-digit percentage of capital annually in fees can be run."*

**That taker tier is crypto spot, 40 bp/side.** [D258](D258-the-prop-track-candidates.md) records
the futures figure as *"~$4–5 on ~$250k notional ≈ 0.2 bp"* round trip, i.e. **~0.1 bp/side** — a
400× change in the only number the closure rests on.

**And D163 has a second problem the re-cost cannot fix**, stated in its own sibling
[D165](D165-the-crossover-rule-and-the-spliced-gross-edge.md): over the 2024-08 → 2026-08 window
yfinance served, *"a long-only crypto trend follower loses money at every frequency including daily
and at every cost tier including the free one."* Under [R15](../RULES.md#r15) a signal is a
**positive gross mean per trade above its nulls**. If the gross edge is negative the cost re-work is
irrelevant and the closure stands on signal, not on arithmetic.

## What this is and is NOT

**The data is BTC/ETH spot crypto. A pass here is a FEASIBILITY BOUND, not a deployable backtest** —
the same category [D260](D260-the-vol-targeted-overnight-hold.md) uses for its equity-proxy result.
The question under test is *"does this construction survive at futures-level cost?"*, never *"is
this a futures strategy?"*. Crypto's own volatility, session structure and 365-day calendar are not
ES's, and nothing here transfers to an instrument this programme holds no data for.

**This record does not close or reopen any avenue.** Only the principal does that
([R15](../RULES.md#r15)). It reports a finding and its consequence for D163's exclusion.

---

## The fixture, and why it is not D163's

D163 named its own blocker and declined to attempt it: *"Exchange APIs — Binance and Kraken both
serve complete 1m history free — would give the years of sub-hourly data a real walk-forward needs.
… It is out of scope here."*

**That blocker was subsequently discharged by another study.**
`data/fixtures/crypto_binance_15m_raw.csv.gz` holds BTCUSDT and ETHUSDT 15m bars from
**2018-02-12 to 2026-07-31 — 294,336 bars, 3,066 complete UTC days, ~8.4 years**, built from
Binance monthly 1m flat-file archives under D161's resampling contract with D161's day-level drop
policy already applied (`empty_bars_15m: 0`, `bar_count == days_kept × 96` exactly).

So the 15m rung can now carry a return claim, which is precisely what D163 said it could not. **This
is a different fixture from D163's**, and every level below is therefore NOT comparable to a level in
`docs/results/breakout_intraday.md`. Only the *ladder* is comparable, and only within itself.

## The construction, fixed here

Unchanged from D163/D109 except where stated:

- **Signal.** Enter long when `close[t] > max(high)` over `t−N_entry … t−1`; exit when
  `close[t] < min(low)` over `t−N_exit … t−1`. Both extrema exclude the current bar. **Long or
  flat, never short.**
- **Fill.** `next_open` (D103) — a signal on bar `t`'s close is filled at `open[t+1]`.
- **Two designs (D162).** **A** = constant calendar horizon, `N_entry = 40 days`, `N_exit = 10 days`
  in bars at each rung. **B** = constant bar count, `N_entry = 40 bars`, `N_exit = 10 bars`. They
  must coincide **exactly** at 1d, which is an asserted right-quantity check, not a hope.
- **Ladder.** `15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d` — every rung's minutes divide 1440, so buckets
  align to 00:00 UTC (D161). Every rung is cut from the **same** day set, so frequency is the only
  variable. Rungs are resampled **one at a time** and released.

**One declared deviation: sizing.** D163 sized positions inverse-vol to a 40% annual vol target,
capped at 1.0. **This runner holds unit weight when long and zero when flat.** Reasons, stated
before the numbers: (i) R15's criterion is a gross mean **per trade**, and a vol-target weight makes
per-trade P&L a statement about the sizing rule as much as the signal; (ii) exposure then reads
directly as time-in-market and turnover as `2 × trades/yr`, which is what a cost re-cost needs;
(iii) D163's own numbers show the cap binds nearly always — its 15m BTC book turned over 786.3× on
402 round trips/yr, an average weight of **0.978**. The deviation is small and it is disclosed
rather than absorbed.

## The scoring span

`TRAIN_DAYS + TEST_DAYS = 315` days are dropped from the front at **every** rung and both designs,
matching D163's walk-forward convention, so all rungs score the identical calendar span and the
longest warm-up (Design A at 15m = 40 days) sits comfortably inside the discarded prefix. **Nothing
is fitted** — both designs are fixed-config — so this is a span convention, not parameter selection.

## The cost conventions, both reported at every rung

| convention | per side | source |
|---|---:|---|
| `crypto_taker_40bp` | **40.0 bp** | D163's reference tier, `DEFAULT_TIERS` (D114) |
| `futures_0.1bp` | **0.1 bp** | D258: ~$4–5 on ~$250k ≈ 0.2 bp round trip |

Charged as `bp/side × |Δweight|` on traded notional at each fill. `fee_drag_annual = annual turnover
× rate per side`, which is the identity D163's integration suite already checks.

## What gets reported — all four of CLAUDE.md's groups, per rung

1. **Performance, gross and net side by side** at both conventions: total return, CAGR, annualised
   Sharpe, annualised vol, max drawdown, **exposure**, annualised turnover, mean move per trade
   against `2c` at each convention, and **breakeven cost in bp/side**.
2. **Trade distribution:** count, mean, **median**, win rate, payoff, mean/median holding run, skew,
   kurtosis, and the **1% two-tail trim reported as all three means** — ex-top, ex-bottom, trimmed.
3. **What the winners depend on:** trades to reach half the P&L, top-1/5/10 trade share, profitable
   years, and the split on what this universe varies — **era** (pre-2022 / 2022+) and **symbol**.
4. **Nulls as a distribution:** a **circular rotation of the position vector** against the return
   series, 500 draws, seeded. Rotation preserves exposure, trade count, holding-run distribution and
   turnover **exactly** while destroying timing, so it is matched on the nuisance and not merely on
   the count. **p50 and p95 reported beside the score**, with a statement of whether the null is
   decisive.

## The crossover, re-read

D163's reading (3) is the load-bearing one and is kept: **cost drag in Sharpe units**
(`annual fee drag ÷ annual vol`) at or above the reference gross Sharpe. Reported here **twice** —
once at 40 bp/side and once at 0.1 bp/side — against **two** reference edges: D163's imported
`REFERENCE_GROSS_SHARPE` constants (BTC 1.27, ETH 0.84, 2015–2025 daily), and **this fixture's own
measured gross Sharpe at the same rung**, which the 8.4-year sample can now support and the 60-day
one could not. Readings (1) net Sharpe ≤ 0 and (2) costs ≥ 100% of gross are reported alongside, with
D165's caveat that both are hostage to the window's own edge.

## Runner assertions — all three, and each proved able to fail

1. **Lag audit in a second implementation.** The position vector is re-derived by an explicit
   bar-by-bar loop that never calls the vectorised rolling-extremum path, and the two must be
   **bit-identical**. Separately, asserted that `pos[t+1]` is a function of data through `close[t]`
   only, by perturbing every bar strictly after `t` and requiring `pos[:t+2]` unchanged.
2. **Sign audit, in money.** On a synthetic monotonically rising series the long book must earn
   **strictly positive** P&L; on its mirror image the same book must not; and raising the cost rate
   must **strictly reduce** net P&L wherever turnover is non-zero.
3. **Right-quantity.** Design A and Design B must be **identical at 1d and different at every other
   rung**; the compounded equity must differ from the additive one; and the scored span must have
   the same first and last timestamp at every rung.

**Each of the three is exercised against a deliberately broken input and must raise.** A self-test
that cannot fail is worse than none.

## Stop condition, fixed before the numbers

- **If the measured gross mean per trade is negative, or does not exceed its rotation null's p95, at
  every rung of both designs** → the closure stands **on signal**, the cost re-work is reported as
  arithmetic that changed nothing that matters, and no further construction is proposed here.
- **If gross is positive above the null at some rung, and the futures convention moves that rung
  from net-negative to net-positive** → the closure **does not survive on the cost arithmetic it was
  written on**, and the record says exactly which rungs and by how much. It still says nothing about
  whether the avenue is open; that is the principal's call.
- **A pass here is not an admission of anything.** [R8](../RULES.md#r8) requires a separate
  pre-registered out-of-sample test on a fixture never seen; the prop book additionally needs
  hurdle P (R11), all six, of which P3/P4/P5 have never been computed on anything (D375 §5).

## Multiplicity, disclosed

**Cells:** 8 frequencies × 2 designs × 2 symbols = **32**, each read at 2 cost conventions
(a cost overlay on one book, not a new search). **Parameters tuned: 0. Filters added: 0.
Configurations selected on performance: 0.** Under [R13](../RULES.md#r13) this study inherits
D160–D165's looks — same hypothesis, same rule, and its candidate list exists **because of** that
work — and inherits nothing from the ETF or terrain programmes, which test different propositions on
universes this does not use.

## Memory

Peak working set is held under **~1.5 GB** and the peak actually reached is reported. Rungs are
resampled and scored one at a time; intermediates go to `temp/`.
