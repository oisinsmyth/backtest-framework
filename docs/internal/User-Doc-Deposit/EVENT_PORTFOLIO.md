# Event Portfolio: How the Intraday Studies Stack

**Status:** index and portfolio logic for the six intraday/event studies
**Purpose:** the route to a high Sharpe is breadth across orthogonal event windows, not a single
mechanism. This document holds the stacking argument, the build order, and the shared
infrastructure.

---

## 1. The studies

| Doc | Mechanism | Window | Instruments | Novelty | Prop-compliant |
|---|---|---|---|---|---|
| `MICRO_FLOW_SIGNAL.md` | Retail positioning feed | Continuous | 5 micro/full pairs | **High** | Yes |
| ~~`PROP_LIQUIDATION_CASCADES.md`~~ | ~~Forced exits under shared DLL rules~~ | — | — | **KILLED at premise** — prop orders do not reach the exchange. See its §0 | — |
| `OVERNIGHT_IMBALANCE.md` | Cash-open constrained participants | 09:30 → ~10:30 ET | ES/NQ/RTY micros | Moderate | Yes |
| `GAMMA_CONDITIONED_CLOSE.md` | Dealer gamma hedging — **carried gamma from public OI; the 0DTE component needs intraday options data not held** | 15:30 → 16:00 ET | MES/MNQ | Moderate | Yes (tight on Topstep's 3:10 CT cutoff) |
| `FUNDING_CYCLE_BASIS.md` | Perp funding cash flow | 8-hourly, minutes | MBT/MET | Moderate | Verify crypto permitted **and** whether 00:00 UTC falls foul of forced-flat rules |
| `SESSION_HANDOFF_LIQUIDITY.md` | Liquidity staffing gaps | 3 windows daily | All micros | Low | **No** — two-sided, and sim fill engines flatter passive quoting |

---

## 2. Why they stack

Five directional strategies trading **different windows on overlapping instruments** are
structurally decorrelated in a way that five signals on the same daily bars cannot be. The
overnight study is flat by 10:30; the close study opens at 15:30; the funding study trades a
different asset class entirely; cascades are event-triggered at unpredictable times.

Rough priors on pairwise correlation, to be replaced by measurement:

| | Overnight | Gamma close | Funding | Handoff |
|---|---|---|---|---|
| **Overnight** | — | ~0 | ~0 | 0.1 |
| **Gamma close** | | — | ~0 | ~0 |
| **Funding** | | | — | ~0 |
| **Handoff** | | | | — |

(Cascade study removed — killed at premise, 18 Sep 2026.)

The funding study is **the only one uncorrelated by asset class**, which makes it worth more to
the portfolio than its standalone Sharpe suggests.

## 3. The arithmetic, stated honestly

```
SR_portfolio ≈ S̄ × √( n / (1 + (n−1)ρ̄) )
```

| Scenario | Standalone S̄ | n surviving | ρ̄ | Portfolio SR |
|---|---|---|---|---|
| Pessimistic | 0.5 | 2 | 0.2 | 0.65 |
| Base | 0.6 | 3 | 0.1 | 0.95 |
| Good | 0.7 | 4 | 0.1 | 1.23 |
| Everything works | 0.8 | 4 | 0.05 | 1.49 |

**With the cascade study dead there are four candidates, one of which (handoff) is
personal-capital only.** The prop-compliant set is three: overnight, gamma-close, funding. 2.0
is not reachable from three intraday event strategies at plausible standalone Sharpes. **The
realistic prop-compliant ceiling from this portfolio is ~1.0–1.2**, and that requires all three
surviving their cost gates. The realistic target is the base-to-good range, **0.9–1.2**, which
per `ALPHA_PROGRAMME.md` §12 is the range where a prop estate becomes a real income stream
rather than a fee-transfer mechanism.

**The cost haircut applies to every row.** All five are intraday at micro notionals. Expect the
cost gate to kill at least one and materially reduce the others. Two or three survivors is the
planning assumption, not five.

## 4. Shared infrastructure — build once

Every study needs the same foundation. Build it as a layer, not per study.

| Component | Used by | Notes |
|---|---|---|
| **Micro/full aggressor-flagged flow** (F1–F5 from `MICRO_FLOW_SIGNAL.md`) | All | Build first; validate the aggressor flag in micro books |
| **Time-of-day liquidity map** (depth, spread by 15-min bucket, per instrument) | All — for cost modelling | By-product of `SESSION_HANDOFF_LIQUIDITY.md` step 1; build it even if that study is dropped |
| **Session and event calendar** (holidays, halts, releases, funding times in UTC, expiries) | All | One versioned table |
| **Realistic fill model** from the book (queue position or spread-crossing) | All | This is where micro-scale strategies live or die |
| **Post-2017 clean-sample flag** | All book-state work | Per `DATA_EXPANSION_PLAN.md` §2.1 |

## 4a. Prop-environment realities — checked 18 Sep 2026

These surfaced during the premise check that killed the cascade study. They apply to **every**
study intended for a funded account.

| Reality | Consequence |
|---|---|
| **Funded accounts are predominantly simulated.** Payouts are real; execution is against the firm's fill engine, not the exchange. Topstep called up 0.71% of Express Funded traders to live in 2025; Apex keeps PA accounts on sim. | Two cost models per study: sim engine for prop, real book for personal capital. A sim-favourable fill assumption will inflate prop-side edge and is what firms' anti-exploitation rules target. **A sim track record is not a live track record** — its credential value is much lower than earlier discussion assumed. |
| **The firm is the counterparty.** Consistently profitable traders are a cost. | Expect payout caps, consistency rules, and rule changes that target algorithmic edges. Do not plan on a rule set being stable for years. |
| **Forced-flat cutoffs.** Topstep: 3:10 PM CT, no overnight/weekend, all account types. Apex 4.0: 4:59 PM ET, overnight eliminated. | Gamma-close's 16:00 ET exit has ~10 min of slack on Topstep. Funding's 00:00 UTC event needs per-firm verification. Anything holding through the US close is out. |
| **Product restrictions change.** Apex removed metals (MGC included). | Universe per study must be checked against each firm's *current* permitted list, not a general assumption. |
| **Automation policy varies.** | Some firms restrict fully unattended trading or require presence. Constraint 6 (algorithmic) is not automatically satisfied — **verify per firm**. |

**The general lesson:** every "prop-compliant" tick in the tables above was assessed against
hedging rules alone. It should be assessed against all five rows here. Several ticks may not
survive that.

## 5. Build order

Ranked by dependency and by cheapness of the kill test:

1. **`MICRO_FLOW_SIGNAL.md`** — cheapest, entirely held data, and four others depend on its
   outputs. Its own standalone result is secondary.
2. **Time-of-day liquidity map** — the first step of the handoff study, needed by all for cost.
3. **`OVERNIGHT_IMBALANCE.md`** — the most developed design; strongest mechanism among the
   moderate-novelty set.
4. **`GAMMA_CONDITIONED_CLOSE.md`** — carried-gamma version first (held data). Intraday options
   data only if that shows the regime flag carries information.
5. **`FUNDING_CYCLE_BASIS.md`** — needs the perp data pipeline; verify crypto is permitted and
   which settlement times survive the forced-flat rules.
6. **`SESSION_HANDOFF_LIQUIDITY.md`** — last, personal-capital only.

~~`PROP_LIQUIDATION_CASCADES.md`~~ — killed at premise. Its retail-stop remnant (§0.1 of that
doc) is a possible low-expectation follow-on, not part of this build order.

**Each study runs its cost gate before its mechanism test, and its mechanism test before its
full harness.** The expected pattern is that most fail cheaply at the gate. That is the design
working, not failing.

## 6. Trial accounting across the portfolio

| Study | Trials |
|---|---|
| Micro flow | 5 |
| ~~Cascades~~ | 0 — killed before any trial was spent |
| Overnight | 9 (+2 dispersion arm) |
| Gamma close | 7 |
| Funding | 7 |
| Handoff | 7 |
| Combination | 1 |
| **Total** | **~38** |

At `FEATURE_RESEARCH.md` §6.1, 38 trials on a ~5-year sample means the best result from pure
noise would show a Sharpe around 0.85. **A survivor must clear that by a margin.** The DSR
adjustment is computed at 44, not at the count for whichever study looked best.

## 7. What this is and is not

**Is:** the realistic route to a portfolio Sharpe above 1.0 with your constraints — breadth
from many small event edges, decorrelated by window and asset class, each with a stated
mechanism and a cheap kill test.

**Is not:** a set of strategies with track records. Every one is a hypothesis. The novel ones
have short samples; the crowded ones have small edges. The cost environment at micro notionals
is hostile to all of them.

**Also is not:** as novel as first framed. The premise check on 18 Sep 2026 killed the most novel
study outright and downgraded the gamma study's data claims. What remains is a portfolio of
moderate-novelty, well-understood mechanisms whose edge at your scale rests on capacity and
care, not on knowing something others do not. That is a more honest and more defensible
position, and it is the one to present.

**The portfolio argument only works if the survivors are genuinely orthogonal.** Measure the
correlations on live-ish data — walk-forward, not full-sample — and measure the drawdown
overlap, not just the return correlation. Three strategies that all lose money on the same
high-vol Wednesday are one strategy.

## 8. Relationship to the slow book

The slow strategies (trend, carry, hedging pressure, basis-momentum) and this event portfolio
are **complementary by construction**: different horizons, different exposure profiles, and —
critically — the event portfolio is flat overnight while the slow book carries the gap risk.

The combined book's drawdown should be materially shallower than either half. That combination
is the actual product, and it is where the first-passage arithmetic finally starts to favour
you.
