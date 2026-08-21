# D169 — The short book ships with a CLOSE-based stop, and the shortfall is measured rather than assumed

**Status:** Committed; the close-based-stop limitation is disposed of by [D170](D170-intrabar-stop-execution.md), and one number below is withdrawn
**Date:** 2026-08-21
**Category:** Signals & strategy interface
**Source:** Phase 2 session (breakdown short book)

> **DISPOSITION, 2026-08-21 ([D170](D170-intrabar-stop-execution.md)).** The engine now
> has intrabar stop execution, so the deviation recorded below no longer applies.
>
> **One claim here is withdrawn.** This record and the report it accompanied said "4 of 4
> stop exits filled beyond their own stop, the worst by 38.5%". That was a measurement
> artifact: `measure_stop_gaps` inferred stop exits from whether an exit price ended up
> beyond the stop level, which also counts ordinary trailing-channel exits that closed
> past it. With the engine recording causation directly, the stop caused **one** exit
> across both symbols, and it did not gap.
>
> The finding that replaces it is less dramatic and more useful: the stop sits at the far
> side of the entry channel, so the trailing exit reaches every position first. The tail
> discipline is **present but not binding**. The rest of this record — why the deviation
> was shipped, why enforcement is asymmetric, why borrow is not optional — stands as
> written, per the D111 precedent that the original reasoning is the half worth keeping.

## Decision

The breakdown short book is built as specified — regime-gated, own parameter sweep,
inverse-vol sizing, borrow charged — with one deviation from the brief that is recorded
here rather than buried:

**The per-trade stop is a signal-level, close-based rule, not an intrabar stop.** The
brief requires "a hard per-trade stop above the entry channel high" and states that
*"short expectancy is only calculable with the squeeze tail truncated by construction"*.
That standard is **not met**, and cannot be met with the current engine. The study
therefore MEASURES the gap between the stop level and the realised fill on every stop
exit, so the shortfall is a reported number instead of an unstated assumption.

Alongside it, three things ARE enforced:

1. **Tail discipline is non-optional and enforced at construction.** A `SHORT`
   `BreakoutStrategy` without a `ChannelStopExit` raises; so does one whose weight source
   caps above 1.0. There is deliberately no flag that turns either off.
2. **Borrow is charged**, at 10%/yr on the short notional (D124's rate), via
   `SHORT_TIERS`. The long tiers are untouched and still hash identically.
3. **The exposure-matched random-SHORT-entry null is the primary verdict**, and the null
   generator takes a `direction` parameter — the fourth forward-compat requirement D166
   recorded as undelivered.

## Rationale

**Why the stop cannot be a real stop.** `simulator/fills.stop_fill_price` implements
correct gap-through semantics (D10: a gapped stop fills at the bar's open, not the stop
price) and names `BUY_STOP` as "the exit order for a short position". It is reachable only
from `config/fill_model.py`, whose own docstring calls it a "Step 2 demonstration
vehicle… not the full execution/fill pipeline from D9/D11/D42". `run_backtest` never
imports it. The engine's order path is weight-target → quantity → fill at close or next
open; there is no per-position stop order in it.

Wiring one in is a genuine piece of engine work with its own verification gate — property
tests, a golden master, the D79 cross-engine reconciliation — comparable in size to D168.
Doing it inside a strategy session, on the most load-bearing part of the simulator, is
exactly the kind of drive-by change this project does not make.

**Why ship the close-based version anyway.** Because the alternative is either no short
book or a months-long engine detour, and because the limitation is measurable. The report
prints, per symbol, how many stop exits filled beyond their own stop and by how much.
That converts a silent assumption into evidence — and the evidence turned out to matter:
**every stop exit on both symbols gapped through, by roughly 18%.** A reader who only had
the brief's premise would have believed the tail was bounded. It was not, and now the
document says so with a number attached.

**Why the enforcement is asymmetric.** The long book is not forced to carry a stop. A long
position's worst case is the instrument going to zero; a short's has no ceiling at all.
The requirement follows the risk, not a symmetry principle.

**Why borrow is not optional either.** D124 made this point for the pairs book's short
leg and it applies here with full force: the borrow accrues on ~100% of NAV for the entire
life of every trade, and assuming free shorts is the single most result-corrupting choice
available to a spot-crypto short study. `CostTier.borrow_annual_rate` defaults to 0.0 and
the brick is emitted only when non-zero, so every long-side tier config — and therefore
every long-side trial hash — is unchanged.

**Why regime slicing is the headline and not an appendix.** A short book that is flat
through a bull sample and profitable through the bears is a success; full-sample Sharpe
would score that as a failure. The brief says so explicitly and the report is laid out to
match.

**Why correlation includes flat bars.** The diversification claim is about the combined
equity curve. Excluding the bars where one book is flat would measure "how do they behave
when both happen to be trading", which is not the question — the whole thesis is that the
short book wakes when the long book sleeps.

## Consequences

- **The primary verdict is a split, and the report refuses to read it as a pass.** ETH
  clears the 95% null bar (96th percentile); BTC does not (51st — the median of randomly
  placed shorts). The long study fixed the rule for this case before looking: one symbol
  out of two is a coin flip. By that rule the entry rule is not demonstrated.
- **Diversification holds; profitability does not.** Correlation against the long book is
  ~0.00 on both symbols, comfortably inside the brief's ≤0.2 target. But the combined
  equal-vol book has a LOWER Sharpe than the long book alone on both symbols, because you
  cannot diversify with a negative-expectancy asset — you can only spread the same losses
  more smoothly. Combined max drawdown does improve, which is the same drawdown-shape
  finding the long study landed on and carries the same caveat: never quote it without
  the Sharpe cost attached.
- **Two of the brief's three success criteria are missed.** The regime gate works — the
  book is ~1% exposed through bull markets. But the bear-regime return is around flat
  rather than strongly profitable, and the chop bleed is the largest single loss on the
  board.
- `ExitRule` joins `EntryFilter` as a composable brick family, with the mirror-image
  contract: a filter can only keep you out of a trade, an exit rule can only get you out
  of one. The trailing channel remains the safety net underneath every added rule.
- `exit_rules` is emitted from `config()` only when non-empty, so long-flat configs
  written before exit rules existed still hash identically.

## What would need to be true to meet the brief's standard

Intrabar stop execution in `run_backtest`: per-position stop orders carried across bars,
filled through the existing `stop_fill_price` with its D10 gap semantics, priced through
the same `CostStack`. The primitive already exists and is already tested in isolation —
what is missing is the order lifecycle in the engine, and the verification that comes with
touching it. Until that lands, no short result in this project should be described as
having a bounded per-trade loss.
