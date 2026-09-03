# D295 — stage 2 on the confluence: early exits and idle conditions

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**The holdout is not read. Holdout reads spent: 0.**

---

## The candidate, fixed

`hist_L` × mean-rank(`macd_hist`, `rsi`) at **f = 0.75, N = 25, k = 5**, exactly
as D293 tested it. **Nothing about the base book is re-searched here** — not
`f`, not the pair, not the primary, not N.

**Hold length is OUT OF SCOPE**, per R14's fourth amendment: it is a deployment
variable and stage 1 reports its profile rather than picking from it. `k = 5`
is retained only so "early exit" has a fixed baseline to be early *relative to*.

## THE PRIOR, STATED BEFORE THE TEST: ARM B FIGHTS THE BINDING CONSTRAINT

Cost is what blocks this candidate — it covers 0.238×–0.597× of its measured
round trip. **An early exit shortens holds → raises turnover → raises cost per
bar.** Arm B is structurally pushing the wrong way and only pays if the loss it
cuts exceeds the extra round trip it buys.

**Arm C pushes the right way**: idling reduces trading and therefore reduces
cost.

That asymmetry is why both arms are tested and why Q5 below is written the way
it is. It is stated now rather than discovered afterwards.

## THE MEASUREMENT: ON THE BOOK, INCLUDING RE-ENTRY

R14's first amendment, which cost D285 a wrong conclusion: **an exit cannot be
evaluated at trade level.** A stop that improves the average trade and hands the
freed slot to a coin flip is a book-level loss wearing a trade-level win. D286's
`disp` beat all three deliberate exits precisely because it exited on
displacement, so the slot always went to a BETTER-RANKED name.

**This requires a position-level simulation, which this programme has not built
before.** Everything to date has used "fresh entries earn k-bar returns", which
models no slots and no capital. Here:

```
N slots per leg. Each bar:
  1. age every open position
  2. close those hitting an exit trigger, or k bars
  3. refill freed slots from the current ranking's best available names
  4. book return = mean(long holdings' 1-bar return) - mean(short holdings')
```

**The control is the SAME simulation with no exit rule** — a flat k-bar hold —
so the comparison is like-for-like including re-entry. Nothing is compared
against the fresh-entry accounting used upstream.

## Arm B — early exits

Each replaces "hold 5 bars" with "hold until 5 bars **or** the trigger, whichever
first". Declared in full:

| | rule | why it is here |
|---|---|---|
| **B1** | **signal reversion** — the name leaves the composite's selected set | the exit that keys on *its own signal*, which is what D285 thought it was testing and was not |
| **B2** | **displacement** — the name leaves `hist_L`'s top N because better names appeared | D286's `disp`, which beat all three designed exits. The slot goes to a better name by construction |
| **B3** | **adverse stop** at 1.0 / 1.5 / 2.0 × the name's own 21-bar vol | in vol units, not price, so it is not a price-level tilt in disguise (D284) |
| **B4** | **profit target** at 1.0 / 1.5 / 2.0 × the same | the mirror of B3, so an asymmetry between them is readable |

**8 exit configurations.**

## Arm C — idle conditions

Two kinds, kept separate because they are different claims:

| | rule | why it is here |
|---|---|---|
| **C1** *(per name)* | **partner disagreement** — skip a name when \|pct(`macd_hist`) − pct(`rsi`)\| exceeds the bar's 50th / 70th / 90th percentile | confluence-specific and genuinely new: is the edge in the AGREEMENT? Nothing tested so far distinguishes "both partners like it" from "the average likes it" |
| **C2** *(whole book)* | **dispersion idle** — sit out entirely when the cross-sectional spread of the composite rank is in the bottom tercile | D290's dispersion pre-test found ρ ≈ 0 and was largely negative. Included because it was probed and never tested on this candidate |
| **C3** *(whole book)* | **wide-spread idle** — sit out when the bar's median Corwin–Schultz estimate is in the top tercile | attacks the binding constraint directly. **REPORTED SEPARATELY AND FLAGGED**: it keys on the estimator that clamps 41.9% of held cells to zero, so a positive result here is an estimator result until a real spread source says otherwise |

**5 idle configurations. 13 cells in total**, declared, on one fixed base book.

## What is reported for every cell — BOTH, and which moved

R14's amended stage-2 gate: *"report the exit's effect on per-trade quality AND
on the book that includes re-entry, and say which of the two moved."*

| per-trade | on the book |
|---|---|
| mean and **median** P&L per trade | per-bar book return and its `t` |
| win rate, payoff, holding run | **paired t against the no-exit control** |
| the mean after dropping the best 1% | turnover per bar, and cost per bar = round trip × turnover |
| what fraction of exits the trigger fired | **net after measured cost, both aggregations** |

**And what the exit KEYS ON.** D285's exit fired on displacement by unrelated
names while its record claimed it fired on its own signal reverting. For every
B rule: the share of exits attributable to the trigger versus the k-bar cap, and
for B1/B2 the overlap between them.

## Pass conditions

1. **paired t ≥ 2 on the book**, against the no-exit control, per bar
2. **cost coverage does not fall** — an exit that improves the book while
   raising cost per bar more than it raises return has not helped this candidate
3. beats a **rate-matched, persistence-matched null**: exits fired at random at
   the same rate *and* with the same holding-run distribution. Matched-count is
   not matched-turnover (D279), and a random exit re-draws every bar where a
   real one persists (D291's voided veto arm)
4. above the **best-of-13 floor**, drawn from that null's joint maximum

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **Q1** | **no exit or idle rule clears all four conditions.** Stage 2's measured uplift in this programme is ~1.0× across D285 and D286 | **AGAINST** | **high** |
| **Q2** | **B2 (displacement) beats B1, B3 and B4** — D286's finding reproduces, for the same reason: the freed slot goes to a better-ranked name by construction | for B2 | moderate |
| **Q3** | **the early exits improve PER-TRADE quality while leaving the BOOK flat or worse.** This is the coupling failure R14's amendment was written for, and it is the specific thing the two-column report exists to catch | for | moderate-high |
| **Q4** | **C1 (partner disagreement) does nothing.** The mean-rank operator already uses both partners; requiring them to agree is a second bite at the same information | **AGAINST** | moderate |
| **Q5** | **every Arm B rule RAISES cost per bar**, so condition 2 fails for all of them even where condition 1 passes | **AGAINST** | **moderate-high** |

**Q3 and Q5 are the load-bearing ones and both are against.** Q5 in particular
would mean Arm B is closed by arithmetic rather than by evidence — which is the
prior stated at the top, tested rather than assumed.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: **13 cells** on one fixed base book, plus the no-exit control. Every
upstream selection — `hist_L` from 51, the pair from 80, `f` from 4 — is
inherited and priced when the holdout is read.

## Stop

**If nothing clears, stage 2 is closed for this candidate** and the programme's
stage-2 uplift stands at ~1.0× across three studies. The candidate then stands
or falls on its stage-1 evidence and its cost question, which is where D293 left
it.

**A negative here does not close:** the cost question (a spread-source problem,
not a rule problem), or the candidate itself.

## Not attempted here

Any re-search of the base book. Hold length (R14 fourth amendment). Combinations
of exit rules — each is tested alone, because a stage-2 search over combinations
is a stage-1 mine wearing a stage-2 label.

---

# AMENDMENT — 2026-09-03, before the runner exists: the design had the point of an exit backwards

Raised by the principal: **"the whole point of an exit is to trim the losers and
let the winners run."** The arms above do the first and actively prevent the
second. Corrected here, before anything is built, rather than after.

## What was wrong

**1. The fixed `k = 5` cap cuts every winner short by construction.** Arm B was
specified as "hold until 5 bars **or** the trigger, whichever first" — so every
rule in it could only ever *shorten* a trade. A design in which no trade can run
longer than the baseline cannot test "let the winners run"; it has assumed the
answer.

**2. B4, the profit target, is the anti-pattern.** It caps winners harder. It
was listed as a candidate rule; it is a **deliberate control** for the
principle, and it is expected to lose.

**3. And this REVERSES the prior at the top of this document.** I argued Arm B
fights the binding cost constraint because early exits shorten holds and raise
turnover. **That is true only of a SYMMETRIC early exit.** An asymmetric rule
shortens losers and lengthens winners, so the net turnover effect can go either
way — and in a book whose losers are what you most want out, it can fall.
**Arm B is not structurally against the constraint. I had it backwards.**

## The corrected Arm B

`k = 5` is now the **baseline hold, not a cap**. A rule may exit before it or
run past it.

| | rule | direction | why |
|---|---|---|---|
| **B1** | signal reversion — the name leaves the composite's selected set | either | the exit that keys on *its own signal*, which is what D285 believed it was testing and was not |
| **B2** | displacement — a better-ranked name takes the slot | either | D286's `disp`, which beat all three designed exits |
| **B3** | adverse stop at 1.0 / 1.5 / 2.0 × the name's own 21-bar vol, **k cap retained** | trims losers only | the pure loser-trim |
| **B4** | **trailing stop** — run with no cap, exit on giving back 1.0 / 1.5 / 2.0 × vol from the trade's peak | **lets winners run** | the missing arm |
| **B5** | **asymmetric** — B3's stop on losers AND no cap on winners, exiting only on B1 | **both halves at once** | the principal's rule stated directly, and the one the whole amendment exists to test |
| **B6** | profit target at 1.0 / 1.5 / 2.0 × vol | **caps winners** | **ANTI-PATTERN CONTROL, predicted to lose.** If it wins, the principle is wrong on this book and that is worth knowing |

**14 exit configurations**, Arm C unchanged at 5. **19 cells.**

## Two things this forces into the report

**Hold length becomes an OUTPUT, not an input.** B4 and B5 have no cap, so mean
holding run is a *result* of the rule. R14's fourth amendment says stage 1 may
not PICK a fixed k on a criterion; it does not say a rule may not DETERMINE the
hold. Those are different, and the distinction is why B4/B5 are legitimate here.

**Winner and loser holding runs are reported SEPARATELY.** A rule claiming to
trim losers and let winners run makes a specific, checkable claim about two
numbers, not one:

```
mean holding run | profitable trades
mean holding run | losing trades
ratio of the two            <- the claim, in one number
```

A rule whose two runs are equal has not done the thing whatever its P&L says,
and a rule with the ratio inverted is doing the opposite. **Reported for every
cell including the controls**, so the mechanism is visible rather than inferred
from the outcome.

## Corrected predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **Q1** | no rule clears all four conditions (unchanged — stage 2's uplift here is ~1.0× across D285/D286) | AGAINST | moderate-high *(was high; B4/B5 are a genuinely untested shape)* |
| **Q2** | B2 (displacement) beats B1, B3 and B6 (unchanged) | for B2 | moderate |
| **Q3** | the CAPPED rules (B3, B6) improve per-trade quality while leaving the book flat — the coupling failure R14's amendment exists for | for | moderate-high |
| **Q4** | C1 (partner disagreement) does nothing (unchanged) | AGAINST | moderate |
| **Q5** | **WITHDRAWN AND REPLACED.** Was: every Arm B rule raises cost per bar. **Now: B4 and B5 LOWER cost per bar** by extending winners, and are the only rules in the study that push with the binding constraint | **for B4/B5** | moderate |
| **Q6** | **B6 (profit target) is the worst rule in the study**, and B5 the best of Arm B | for | moderate |

**Q5 has flipped direction entirely**, which is the substance of this amendment
rather than a wording change. **Q6 is new and is the principal's principle
stated as a falsifiable ranking.**
