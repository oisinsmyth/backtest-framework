# D212 — the cost convention, and a post-close restatement in Sharpe and PnL

**Status:** Committed — a defect correction plus a descriptive addendum to a closed programme
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** a request to see the results in Sharpe and money, which surfaced the defect

## Part 1 — the defect: two halves of one study priced the same tier differently

`structure_setups.friction_in_r` charged `cost_bps` **once** for a round trip.
`structure_strategies.r_multiples` charged it **per side**, via `(entry + exit) / risk`.

So WP2's census and WP4's lattice were pricing the identical 40 bps tier a factor of two
apart, for the whole study.

**The per-side reading is right**, and the repo says so in two places that were not
consulted when `friction_in_r` was written:

- `breakout_study.CostTier.fee_bps` is a *fee tier* — an exchange fee, charged per fill;
- `terrain_strategies.StrategyResult.net_returns` doubles it explicitly:
  `charge = 2.0 * self.cost_bps / 10_000.0`, with the docstring "gross less a **round-trip**
  charge". `PositionResult.equity_curve` reaches the same place by charging every unit of
  exposure changed.

### Why the test suite did not catch it

There was a test named `test_friction_reproduces_the_numbers_d196_already_published`, and a
second one, `test_the_cost_charged_in_r_matches_the_census_arithmetic`. The second one's
name is a claim it does not make: it asserted `r_multiples` matched a formula retyped from
`r_multiples`. **It compared the function to itself.**

Neither test ever put the two cost paths side by side. That pin now exists
(`test_the_two_cost_paths_agree_on_the_same_tier`) and is the only thing that would have
caught this.

The general form, and it is a fourth variation on the theme this programme keeps producing:
**a test named after an agreement between two components has to actually call both of
them.** D205 found an invariant that could not see a starved branch, D206 a drop that was
never counted, D209 a guard whose rejections were never compared to anything. This is the
same shape once more — a check that looked like a cross-reference and was a tautology.

### What changed

WP2's friction figures double. The conclusion strengthens:

| | superseded | corrected |
|---|---:|---:|
| base-arm friction, BTC / ETH | 0.48R / 0.34R | **0.96R / 0.68R** |
| stacked-arm friction, BTC / ETH | 0.71R / 0.51R | **1.41R / 1.01R** |
| required hit rate at 5R, base | 24.7% / 22.3% | **32.7% / 28.0%** |
| required hit rate at 5R, stacked | 28.4% / 25.1% | **40.2% / 33.5%** |

The stacked arm's friction now exceeds **1.0R** on both symbols: the round trip costs more
than the entire risk of the trade. That is the same statement as D210's untradeable share,
arrived at from the other direction.

**Nothing in D208, D210 or D211's verdict moves.** Those rest on the zero-cost diagnostic,
the rank correlations and the matched-placebo comparisons, none of which touch `cost_bps`.
D206's headline — that the course's 20%-at-5R claim loses money — is unchanged and now has
more room in it.

An ambiguity this study inherited rather than created, and does not resolve: D196's prose
calls `taker_40bp` "a 40 bps round trip" while the code that produced its numbers charges
per side. The code is treated as the authority here, and the addendum below reports a
10 bps/side tier as well so that nothing depends on settling it.

## Part 2 — the addendum: every arm in Sharpe and PnL

The programme reported R multiples. It never reported Sharpe, money, or a passive baseline,
because R-based arms have no equity curve — R says how much was won per unit risked and
never how much to risk.

`scripts/run_structure_pnl.py` supplies the missing sizing rule and reports the arms in the
units most people mean by "how did it do".

**Sizing rule:** constant unit exposure through each trade, flat between, cost charged on
every unit of exposure changed — the `PositionResult` path D197–D202 used, reused rather
than rewritten so these numbers sit on the same footing as terrain's. Fixed-fractional risk
is deliberately avoided: on a book where a third of trades cost at least their whole risk to
put on, it would produce an equity curve that describes the sizing rule rather than the
signal.

**Baselines:** buy-and-hold over the exact span each arm trades, and cash. Both, because a
losing strategy has to be compared to not trading and not only to a rising asset.

### The result

- **0 of 16 arms make money at 40 bps/side. 0 of 16 at 10 bps/side either** — so the verdict
  does not rest on the punitive tier.
- At zero cost 7 of 16 make money. The largest, `ETHUSDT` C1, returns **+1,788%** at Sharpe
  +0.77 and beats buy-and-hold — and goes to **−9,532 of 10,000** at ten basis points a
  side. A book that cannot survive a tenth of a percent per side is not an edge with a cost
  problem; it is turnover with no edge.
- Buy-and-hold over the same span returns **+460%** (BTC, Sharpe +0.32) and **+115%** (ETH,
  Sharpe +0.11). Neither is a high bar and no arm clears either.

## The rule this addendum runs under

D211 closed the programme, and its stop names "sizing rule" explicitly. This introduces one.

It is admitted as a **descriptive restatement of arms already run**, not a test, on three
conditions, all stated before the numbers were looked at:

1. every look is counted in the ledger (16, taking the total to **102**);
2. **a positive result here would have been a new hypothesis requiring its own
   pre-registration, not a result** — the rule was written down first precisely so it could
   not be renegotiated afterwards;
3. no arm is re-specified, re-tuned or re-selected. The eight arms are exactly WP4's.

Condition 2 did not bind, because nothing was positive. It was worth writing anyway: the
value of a pre-committed rule is that you find out afterwards whether you would have kept it.
