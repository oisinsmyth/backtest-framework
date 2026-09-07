# YouTube lessons

Things worth keeping from the transcripts in `docs/Youtube Transcrips/`.

**Nothing in this file is a result.** These are untested ideas lifted from other people's
videos, none of which carry a null, a cost convention, or a universe control. An entry here
means "worth half an hour as a variant", not "works". Anything that survives a real study
graduates to `docs/FINDINGS.md` and is deleted from here.

Transcript filenames carry their disposition as a prefix:

| prefix | meaning |
|---|---|
| `[CLOSED]` | read, nothing taken |
| `[EXTRACTED]` | read, something taken — recorded below |

The transcripts themselves are **git-ignored** (`.gitignore`): they are third-party source material
read for review, never evidence, and not ours to redistribute. Anything worth keeping is quoted
into this file or into a decision record, so losing the folder costs nothing.

---

## 1. A self-referential exit: close on the position's own N-bar high

**Source:** `[EXTRACTED] This Algo Strategy Has 70% Win-Rate & Trades AGAINST Retail Traders.txt`
(David, Critical Trading). **The video's own claim is worthless** — a 70% win rate reported
with no payoff ratio, on a rule whose no-stop geometry produces that win rate mechanically,
wrapped in a retail-flow story the strategy never measures. Its entry (buy the 5-bar low) is a
cruder copy of `rsi` / `retrace_leg`, which this programme has already pushed to the point
where [D341](decisions/D341-RESULT-honestly-scored-retrace-leg-is-2-7-bp-a-bar.md)
recommended against spending the holdout read. **Only the exit is
worth anything.**

**The rule:** close the position when the name's own high exceeds its highest high over the
previous N bars.

**What is already built, and the narrow thing this adds.**
[D355](decisions/D355-the-invalidation-exit-on-the-candidate-books.md) already tests a
self-referential exit — *invalidation*: the name's lagged floored **cross-sectional percentile**
of the same score crossing 50 — pre-registered, on `rsi:40` and `hist_L:40`, against the 24 rank
rotations and control A'. So "exit when the position's own signal reverts" is **not** a gap.

The remaining difference is narrow but real: D355's exit reads a **percentile among peers**, so
it can still fire because *other* names moved. An N-bar-high exit reads **only the name's own
price** and is fully independent of the cross-section. That makes it the strictest available
test of the complaint CLAUDE.md records against D285 — an exit *"fired on displacement by
unrelated names, not on its own signal reverting"* — and of `docs/FINDINGS.md` §10's note that
the gap between the two lenses is **opportunity cost, which nothing here has measured**.

**So the entry is worth keeping only as a third arm beside D355's**, not as a new idea. If D355's
invalidation arm already answers the question, this adds nothing.

**What to check if it is ever run.**

1. **It carries no stop**, so it inherits a fat left tail: a name that never makes an N-bar
   high is held indefinitely. Report the trade distribution with both tails trimmed (RULES
   group 2), not the mean alone.
2. **It changes holding period**, so CLAUDE.md's cost-cutting rule applies directly — a longer
   hold lifts breakeven by amortising one round trip while per-bar edge usually falls. Say
   which moved: edge per unit exposure, or cost per trade.
3. **Both lenses, never on the same statistic.** The point of the rule is that it decouples the
   exit from the slot cap, so the path-invariant and path-variant readings should diverge more
   than usual — that divergence *is* the opportunity-cost measurement, and it is the actual
   reason to bother.

**Status:** not tested. No cell scored, no book proposed.

---

## 2. Equal weight was never chosen — it is just what the kernel does

**Source:** `[EXTRACTED] Algo Trading Strategies 19% Profit in 10 Months & 30 Minutes Per Month.txt`
(David, Critical Trading). **The video's evidence is worthless** — it levers a low-volatility
portfolio and a high-volatility benchmark by the same 2:1 and reports the drawdown difference as
skill, which is a restatement of their volatilities. But its subject, inverse-volatility sizing,
exposed a question this programme had not asked.

Every cross-sectional book here is equal-weighted (`1/n_t` per leg,
[`run_d306_width_exits.py:240`](../scripts/run_d306_width_exits.py)) and **nothing has ever been
run against it**. Inverse-vol sizing exists in the breakout/crypto lineage (D110/D118/D119) and
has never met the single-name books.

**Written up properly as
[D372](decisions/D372-equal-weight-is-the-incumbent-sizing-and-the-hurdle.md)** — equal weight
declared as the baseline, the four ways it is dumb, why it is still hard to beat, the challengers,
the confounding with the D339 floor, and the hurdle. Stage 0 there is a volatility-decile split of
contribution P&L, which may end the question before any sizing scheme is built.
