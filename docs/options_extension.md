# Options Extension — Scoping Decision (D16, D84)

**Status: deliberately deferred, with this document as the written rationale.**
Written 2026-07-14 (Step 11). This is a scoping decision, not a design doc for
imminent work — see [Trigger conditions](#trigger-conditions) for what would ever
un-defer it. Per R3, a reasoned scoping decision is a portfolio asset; a half-built
options module would be a liability.

## The decision in one paragraph

The original put-spread thesis (buying downside protection structures on overhyped
names) is unrepresentable without a real options wing: historical chain data (paid),
a pricing/marking model, per-contract cost structures with 5–10%+ spreads on illiquid
strikes, Reg-T margin math, and expiry/assignment lifecycle mechanics. That is
months of work and recurring data cost, none of which serves the pairs-trading
research this framework exists to produce (R1). What exists instead is a
**well-formed stub** — the correct dataclass shape with honest multiplier arithmetic,
and the genuinely hard parts left out in writing rather than fabricated —
plus this document, which records what "done" would actually take so the deferral is
a decision rather than an omission.

## What exists today

`backtest_framework.instruments.option_stub.OptionStub`
(`underlying_symbol`, `strike`, `expiry`, `option_type`, `multiplier=100`,
`quote_currency`) — gate-tested in `tests/unit/test_instruments.py`:

| Surface | Behaviour | Why |
|---|---|---|
| `notional(qty, price)` | works: `qty × premium × multiplier` | correct and cheap; the multiplier is the one piece of options arithmetic with no modelling content |
| `tradeable_quantity` | works: whole contracts | ditto |
| `carry_components()` | works: returns `()` | **correctly empty, not unimplemented** — theta decay is priced into the option's mark, not a carry brick, in this framework's model |
| `margin_requirement` | raises `NotImplementedError` → this doc | a wrong margin number is worse than an honest crash (D48) |
| pricing / Greeks / assignment | **absent entirely** | the `Instrument` protocol has no pricing surface; methods that don't exist can't be mistaken for working ones — stronger than stubbing them (D48) |

## Why this is months, not weeks — the six hard problems

**1. Data (the blocker).** Backtesting needs *historical* chains: every strike/expiry
with bid/ask/mark, ideally IV and greeks, survivorship-complete. yfinance serves only
the *current* chain — useless for backtests. Real sources are paid: EOD chain vendors
(ORATS, CBOE DataShop, Polygon.io options tiers, historicaloptiondata.com) run on the
order of $30–100+/month subscription or hundreds of dollars for one-off historical
pulls — *estimates as of writing, to be re-quoted at trigger time, not planned
against*. Data volume is also 100–1000× the equity fixture (thousands of contracts
per underlying per day), which stresses the D24 snapshot store's flat-CSV format.

**2. Pricing and marking.** Positions must be marked every bar. Either trust vendor
marks (stale/wide for illiquid strikes — the exact strikes the thesis trades) or
model: Black-Scholes-Merton at minimum, and US single-name options are American-style
with dividends, so honest marking needs a binomial/BAW model plus a dividend schedule
(the D75 corporate-actions table helps here). An IV surface (interpolating quotes to
mark non-traded strikes) is its own sub-project with well-known failure modes.

**3. Costs.** The CostStack shape fits (per-instrument-class stacks — D13 anticipated
exactly this), but every brick is new: `PerContractCommission` (IBKR publishes
~$0.65/contract, $1 order minimum — same published-schedule X-test discipline as D65,
same manual-verification caveat), premium-proportional spread with the 5–10%+
illiquid-strike reality (D16's own numbers), and exercise/assignment fees.

**4. Margin.** Reg-T short-option margin is a max-of-formulas calculation (e.g.
short put: 20% of underlying − OTM amount + premium, floored at 10% of strike +
premium), position- and moneyness-dependent, different again under portfolio margin.
This is why `margin_requirement` raises: the number feeds `MarginInterest` (D67) and
`RiskMonitor` (D57), and a plausible-looking wrong value would silently corrupt both.

**5. Lifecycle: expiry and assignment.** Options are finite-lived instruments. The
engine has no concept of an instrument that *ends*: D45's inner-join alignment would
silently drop every bar after the shortest-lived contract's expiry — for the whole
portfolio. Expiry needs an engine event (cash-settle or convert to shares), early
assignment on American shorts needs a modelled hazard, and post-assignment share
positions need to flow into the equity book. The D75 split-scaling machinery is the
precedent for engine-applied position events, but expiry is a bigger concept: the
instrument *universe* becomes time-varying, which also touches strategy interfaces
(chain selection — which strike/expiry to trade — is a strategy-level decision with
its own look-ahead risks under D32).

**6. Risk.** `RiskMonitor`'s gross-exposure formula is notional-based (D57); option
notional wildly misstates economic exposure. Honest limits need at least
delta-adjusted exposure, which circles back to problem 2 (greeks).

## How it would bolt on (the Lego audit)

Fits existing sockets, no redesign: `Instrument` protocol (the stub already conforms),
`DataSource` interface for a chain source (D18), per-class cost bricks (D13),
declarative configs (D52), snapshot store for chain data (D24, format upgrade needed),
dividend tables (D75). **Needs genuinely new engine concepts**: finite-lived
instruments / time-varying universe (breaks D45's current alignment assumption),
expiry/assignment events, a pricing-model layer, delta-aware risk. The split is
roughly: costs and data are additive bricks; lifecycle is real engine surgery.

## What "done" would mean (verification gates, in this framework's style)

- X: `PerContractCommission` vs IBKR's published options schedule (≥10 worked rows).
- X: model marks vs vendor marks on a liquid pinned date (reconciliation doc, D41
  style).
- G: hand-computed Reg-T margin for short put / covered call / spread, to the penny.
- G: expiry day golden master — ITM exercise into shares, OTM expiry to zero, with
  fees.
- U/P: put-call parity residuals bounded on the pricing model; assignment conserves
  portfolio value at the strike boundary.

## Trigger conditions

Revisit only if **all** of: (1) the pairs study writeup is complete (R1 — research
output first), (2) the put-spread thesis is still live after that work, (3) the data
budget is accepted after re-quoting vendors. Estimated effort at that point: 6–10
weeks at this project's ~7 h/week cadence, dominated by problems 1, 2 and 5. Absent
those conditions, this document is the deliverable — the shape is committed, the
cleverness is deferred (D31's pattern, applied to a whole asset class).

---

*Enforced against rot: `tests/unit/test_instruments.py` asserts the stub's honest
surface and that `margin_requirement`'s error points here;
`test_options_extension_doc` asserts this document remains the scoping decision
(sections present, stub banner gone).*
