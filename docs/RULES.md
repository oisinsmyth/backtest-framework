# Standing Rules

Unlike [decisions](decisions/README.md), these aren't one-time calls — they're constraints
that apply continuously across the project's life. Originally logged as R1–R4 in
[`DESIGN_DECISIONS.md`](../DESIGN_DECISIONS.md). Add new rules here as R5, R6, ...

These are specific and binding. For the underlying values that generated them — useful when
a new situation isn't covered by an existing rule — see [`../PHILOSOPHY.md`](../PHILOSOPHY.md).

---

## R1. No new framework code until the framework has produced one real number

The XLE/XOP walk-forward, run through the *current* imperfect version of the framework.

**Because:** research output, not infrastructure, is what a quant portfolio is judged on,
and observed defects motivate better fixes than theorised ones.

**Scope:** suspended for design-only sessions; binding on execution sessions.

## R2. Timebox the CostStack + Instrument refactor to ~2 weeks of available time

**Because:** satisfying architecture work expands to fill all available time; the framework
earns its existence at the cost-multiplier sweep, not before.

## R3. The deferred list is explicit and written

Options wing ([`docs/options_extension.md`](options_extension.md) — not yet written, see D16),
full multi-currency accounting, live IBKR integration.

**Because:** a reasoned scoping decision is a portfolio asset; silent sprawl is a liability.

## R4. Design decisions get recorded as "decision — because rationale"

**Because:** theorising must converge to commitments, not sprawl into open-ended exploration.
[`docs/decisions/`](decisions/README.md) is the map.

---

## R5. This doc suite is source of truth; keep it in sync as code lands

New decisions go in `docs/decisions/` (next number: **D283**), shipped changes go in
[`CHANGELOG.md`](../CHANGELOG.md), current work-in-progress goes in [`AITODO.md`](../AITODO.md).

**Because:** the original four docs (`MASTER_PROJECT_DOC.md`, `DESIGN_DECISIONS.md`,
`VERIFICATION_SCHEME.md`, `DEVELOPMENT_TIMETABLE.md`) were written before implementation
started and are frozen planning artifacts; the doc suite added on 2026-07-13 is what stays
current once code exists.

---

## R6. A hurdle that names a test is not cleared until that test is run

A record claiming a hurdle passed must point at the artifact field holding that test's output.
A runner implementing a multi-leg hurdle must compute **every** leg or fail loudly.

**Because:** D217 and D218 both wrote hurdle A as *"≥ +0.10 Sharpe, above the paired
bootstrap's p95"* and **neither runner ever computed a bootstrap** — `ladder_deltas` compared
the point estimate to +0.10 and stopped. Both records read as though the second leg had passed.
When D229 built the leg and D230 swept all 24 reported deltas through it, **zero cleared the
hurdle as claimed**, against 8 that cleared it as scored.

Prose that is not enforced in code gets skipped, and a hurdle that exists only in prose is
worse than no hurdle: it manufactures confidence nobody earned.

**Scope:** binding on every study. Introduced by [D230](decisions/D230-the-bootstrap-sweep.md).

## R7. Null the overlay, not the book

A study that applies an **overlay** to an existing book — a stop, a target, a partial exit,
anything that modifies positions a base rule already chose — must be controlled against a null
that **keeps the base book and randomises only the overlay's decisions, matched on how many it
makes.**

A rotation null is the wrong control here. Rotation randomises the *whole book's* timing, which
is the right question for an **entry** rule and the wrong one for a rule that modifies an
existing book.

**Because:** D235 tested seven stop and target overlays. All seven beat their baseline and the
pre-registered rotation null cleared — at a p95 of **−0.284**, a bar anything not actively
harmful would clear, because a rotated 17.5%-exposure book scores far below the unrotated 18.9%
baseline by construction. Against the correct null — cutting **the same 146 of 1,124 trades**
short at *random* bars — the best overlay landed at the **63rd percentile**, with the median
random-exit book scoring +0.785 against the real +0.794. **The trigger carried no information at
all**, and the pre-registered hurdle said the opposite.

Corollary, and it is the cheaper half of the rule: **a hurdle that everything clears is not
evidence, it is a broken hurdle.** A clean sweep of positive results is a tell, not a triumph —
the same tell that surfaced D224's look-ahead defect.

**Scope:** binding on every study applying an overlay. Introduced by
[D235](decisions/D235-stops-and-targets-on-the-recovery-rule.md).

### ADDITION, 2026-09-08 — the control is a NULL, not a POLICY, and the verdict depends on the objective

*Three things [D380](decisions/D380-RESULT-no-exit-overlay-beats-not-cutting-and-R7s-control-inherits-the-rule.md)
and [D381](decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange-rate-is-fixed.md)
found by running R7's control properly. They bind future overlay studies; they do not reopen anything.*

**1. Report the overlay against the UN-OVERLAID BASELINE as well as the control.** R7's control
answers *"does the rule beat random cutting?"* It does not answer *"does the rule beat not cutting?"*,
and those can have opposite answers. D380 had an overlay clear its control while earning **61% less
per trade than doing nothing**.

**2. The control's difficulty is inherited from the rule's trade selection, so control-only verdicts
are not comparable between rules.** Measured across six properly-scaled arms, the control's own
centre ran from **+11.95** (rule fires on winners) to **+290.58** (fires on losers) against a
baseline of **+160.55** — a loser-firing rule is graded against a control **better than doing
nothing**. **State which trades the rule selects whenever a control-relative verdict is quoted.**

**3. The control is a NULL and never a POLICY.** When the rule's trade selection is knowable only
**ex post** — which paths *will* breach a threshold — the control's level is unattainable and must
not be quoted as an achievable alternative.

**And the verdict depends on the objective, which is the strategy's to declare.** An overlay judged
on **mean per trade** is being judged for an unconstrained book. Under a hard drawdown limit the
criterion is **return per unit of drawdown**, because the drawdown caps size ([R11](#r11)'s P1 is the
sharpest case, restated as a sizing rule in
[D375](decisions/D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md) §5).
**An overlay that cuts drawdown by more than it cuts mean wins on that criterion and loses on the
other.** Which objective applies is **a property of the individual strategy and book, assessed at its
own test stage** — not something a methodology record settles in advance. **What binds here is only
that the study must say which objective it is testing against.**

## R8. Admission to the book requires a pre-registered out-of-sample test

A strategy enters [`BOOK.md`](BOOK.md) only after a test whose **hurdles were committed before
the withheld data was touched**, and it enters carrying its own **falsification conditions** and
a full statement of what is still wrong with it.

**Because:** D215 committed that a positive needs its own pre-registration and holdout, and
nine studies then produced nothing that reached one. When S1 finally did, the temptation was to
report the pass and not the four things still broken about it — a +0.978-correlated holdout, an
interval containing zero, a failing sample-size hurdle, and a loss to buy-and-hold over the only
forward period tested. **A book entry that records only its evidence is a marketing document.**

**Corollary:** a place in the book is **not** a decision to trade. Sizing, leverage and capital
allocation are separate decisions, recorded separately.

**Scope:** binding. Introduced alongside [S1](BOOK.md#s1--the-recovery-rule).


## R9. A conditioning variable in an anatomy must be lagged exactly as the rule would lag it

A descriptive cut that buckets returns by some variable must use **the value the rule could have
seen** — `z[t-1]`, not `z[t]` — whenever the variable is computed from the same bar whose return
is being measured.

**Because:** [D248](decisions/D248-the-strength-filtered-intraday-short.md) was pre-registered on
a monotone quintile relationship spanning **465 percentage points**, from +396% at the weakest
signal to -68% at the strongest. `z = |hist_L| / sd`, and `hist_L[t]` is computed from bar `t`'s
close — so a large `|hist_L|` with `hist_L < 0` means **the bar had already fallen.** The anatomy
selected bars on that and then measured the fall it had conditioned on.

**Lagged by one bar the entire effect vanishes**: the spread collapses to under two points, the
ordering scrambles, and the two halves of the sample disagree on the sign.

**The runners were never wrong** — `hold_book` shifts by `lag = 1` and always did. The error
lived in a throwaway analysis script, **upstream of every null, hurdle and stop the programme
has**, and it drove a full pre-registration before anything downstream could catch it.

**Corollary, and it is the expensive half:** an ad-hoc script gets none of the look-ahead
protection the runners have. **A number that motivates a pre-registration deserves the same
scrutiny as one that comes out of it.**

**Scope:** binding on every descriptive cut, anatomy and conditional-return table. Introduced by
D248.


## R10. A pooled conditional-return table must report concurrency beside it

Any table that pools forward returns across `(symbol, bar)` must be accompanied by **how many
names the resulting book would hold at once** — mean, max, and the fraction of bars above a stated
crowding line — each measured **against a per-symbol-rotated book of identical exposure**.

**Because:** [D249](decisions/D249-the-inverse-wedge-breakout.md) was proposed on a conditional-
return table showing **1,474 down-break observations returning +15% to +18%** against a +7.84%
baseline. The table was correct. Every cell was properly lagged and R9 was satisfied. **The book
those bars assemble into still failed its null**, because the 1,474 observations were not 1,474
independent events — they were a few dozen market-wide ones.

The measurement that named it:

| | held bars' own volatility | names held, max | *rotated max* | bars over 20 names | *rotated* |
|---|---:|---:|---:|---:|---:|
| the wedge book | **1.14x** | **41** of 57 | *23* | **13.7%** | *0.0%* |

**The bars were barely louder than average; the book was vastly more crowded.** Converging
channels break downward together because they break when the market falls, so the rule was not
selecting *which* instrument to buy but *when* to buy all of them. That is why the book ran
**2.20x** the null's volatility, cleared the money leg at the **99.8th** percentile and failed the
Sharpe leg at the **63.0th**, and carried an **-18.24%** drawdown at 15.4% exposure where S2
carries **-5.83%** at 13.3%.

**This is R9's neighbour, not a case of it.** R9 catches a table that conditions on the bar it
measures. **R10 catches a table that is correct per bar and misleading about the portfolio** — the
diversification a pooled count appears to supply is illusory on exactly the bars that matter.

**Corollary — pooled counts are not sample sizes, and the fix is not a bigger universe.** Effective
independent instruments on this universe saturate near **2.2** regardless of headcount, so a
pooled trade count overstates the sample by roughly the concurrency factor. Report both, always,
and never quote the pooled number alone.

**Second corollary — a per-symbol rotation null is a biased control for a market-wide signal.**
`rotation_nulls` draws an **independent offset per symbol**, which destroys cross-sectional
synchrony by construction and therefore **understates the volatility of any book whose triggers
synchronise**. It is conservative on money and harsh on Sharpe. Requiring **both** legs is what
brackets the truth; a single-leg verdict on such a rule is not safe.

**Scope:** binding on every pooled conditional-return table, anatomy and setup census whose
triggers can synchronise across the universe — which is nearly all of them on a single asset
class. Introduced by D249.


## R11. A candidate for the prop-firm route must clear hurdle P, and the book does not

**Anything intended for external funding is measured against the venue's rules, not against
`max_drawdown`.** The statistics this programme computes are closed-equity and far kinder than
what a funded account is actually judged on.

**Hurdle P, all six:**

| | standard | why |
|---|---|---|
| **P1** | **SIZING RULE, NOT A FILTER — see the 2026-09-08 restatement below.** Size the account so trailing drawdown ≤ 4% on **OPEN** equity, then carry the resulting return forward | Apex trails on unrealised intraday equity; open profit lifts the floor before anything is closed. Our closed-equity max-DD is a different and gentler statistic |
| **P2** | **No exposure across the VENUE'S FLATTEN TIME** — see the amendment below; this is venue-specific, not universal | Topstep 3:10pm CT, Apex 4:59pm ET, MyFundedFutures 4:10pm ET |
| **P3** | **Worst single day ≤ 2%** | Daily loss limits run 2–3% |
| **P4** | **Expected time-to-breach > 3 years** | Against a trailing barrier and positive drift, ruin is certain eventually; the question is only when. At Sharpe 0.9 a 20-account book died every ~3.85 years |
| **P5** | **No single day > 40% of trailing-year profit** | Consistency rules cap a single day at 30–50%, so a lumpy-but-profitable strategy is ineligible for payout while up |
| **P6** | **Venue permits automation at the FUNDED stage** | Apex: *"No Automation or Algorithm Usage allowed"* on Performance Accounts, penalty *"forfeiture of all funds and balances"*. Take Profit Trader bans EAs throughout. **Only Topstep and MyFundedFutures permit it.** Third-party comparison tables contradict both firms' own terms and must not be relied on |

### RESTATEMENT, 2026-09-08 — **P1 is a sizing rule and cannot fail. It was listed as a filter and it is not one.**

*From [D375](decisions/D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md) §5,
which audited every absolute threshold in the programme for whether anything had ever cleared or
failed it. P1 is the one that can do neither.*

**[D266](decisions/D266-the-prop-cross-screen.md) applies P1 by scaling the strategy until max
drawdown reaches 4%** — *"none of it helps, because P1 is a sizing constraint"*. A constraint
satisfied **by construction** rejects nothing. It converts into a **return penalty**: D266's best
cell fell to **+0.535%/yr** after P1 sizing, and the best P2-compliant one to **+0.413%/yr**.

**So P1 is not a hurdle, and listing it as one alongside P2–P6 has two costs.** It implies a
candidate can *fail* P1, which no candidate can; and it hides that P1's real output is a **number**
— the post-sizing return — which is the thing that actually decides whether a prop candidate is
worth anything. **Under [R6](#r6), a hurdle that names a test is not cleared until that test is run;
P1 names no test, because there is nothing to pass.**

**P1 as it now stands:**

> **Size the account so trailing drawdown ≤ 4% on OPEN equity. Report the post-sizing return, and
> judge the candidate on that number.** P1 is never reported as PASS or FAIL. **The verdicts belong
> to P2–P6, of which P2 and P6 are structural facts and P3, P4 and P5 have never been computed on
> anything (D375 §5).**

**What does not change.** The 4% figure, the open-equity basis, and the reason for both are
unchanged; the committed book's −29.82% at deployed size is still the measurement that shows how far
it is from prop-viable. What changes is that this is stated as a **sizing outcome**, not as a gate
the book failed.

**Because:** the committed book requires roughly sevenfold de-sizing under P1 (−29.82% at deployed
size against 4%)
and **fails P2 structurally** — it holds overnight, and [D247](decisions/D247-the-short-side-at-fifteen-minutes.md)
measured that **86.6% of its return is timing that accrues overnight**. **No amount of position
sizing fixes P2.**

**Corollary, and it is the operative one:** the prop route needs a **different, intraday strategy**,
not a scaled version of this book. **The two goals must be tracked separately**, and the 4% trailing
constraint must not be allowed to distort the own-capital book, where a −15% drawdown is
survivable and a −29.82% one is merely uncomfortable.

**Second corollary — the cost wall does not transfer.** This programme's ~1.9 bp/side ETF figure and
the "one round trip per day costs 8.90%/yr" arithmetic are **equity** numbers. Futures round-turn
commission on the instruments these firms offer is roughly an order of magnitude cheaper, so
**intraday constructions excluded on ETF cost arithmetic must be re-costed before being excluded on
futures.**

### CLARIFICATION, 2026-08-29 — hurdle P is measured on the ACCOUNT, not on a strategy

**P1, P3 and P4 are constraints on the funded account. They are not constraints on a strategy, and
[D260](decisions/D260-the-vol-targeted-overnight-hold.md) applied them as though they were** —
measuring a single arm running alone at 100% of the book. **The principal caught this.**

**What it does NOT change:** weight and size are the same lever. Running an arm at book weight `w`
is arithmetically identical to running it at size `w`, so D260's answer is unchanged for a
*solo* arm — the 0.60 weight that clears P3 gives the same **+1.87%/yr** as the 0.21x size did.

**What it DOES change is that the constraint is shared, and diversification relaxes it.** With `k`
uncorrelated arms each sized so the BOOK meets the limit, each runs at `1/sqrt(k)` of solo size and
there are `k` of them:

| arms | each at | book return | accounts needed for $50k |
|---:|---:|---:|---:|
| 1 | 1.00x | **1.87%** | 20 |
| 2 | 0.71x | **2.64%** | 14 |
| 4 | 0.50x | **3.73%** | 10 |
| 9 | 0.33x | **5.60%** | 7 |

**So a closure on P1/P3/P4 closes a candidate AS A STANDALONE BOOK. It does not close it as a
component.** A verdict must now say which.

*The `sqrt(k)` law is vol-scaling; tails do not add in exact quadrature, so it is the right order
rather than the exact number. And it requires arms that are genuinely uncorrelated —
[BOOK_PROP.md](BOOK_PROP.md) is empty, so `k = 1` today.*

**Scope:** binding on any candidate proposed for external funding. Introduced 2026-08-29 from the
prop-firm review in [`research/shorts/05-prop-firm-reality.md`](research/shorts/05-prop-firm-reality.md).

### AMENDMENT to P2, 2026-08-29 — it is venue-specific, and one venue permits the overnight

**P2 was written as "zero overnight exposure" and that is wrong.** Checked against the firms' own
documentation the same day it was recorded:

**MyFundedFutures, from its own help centre:** *"Trades may be placed beginning at 6:00 PM EST when
the Globex session opens"*, and such trades *"remain open until the New York session closes at 4:10
PM EST."*

**So a position may be opened at the 6:00pm ET Globex open and held through the entire overnight
session to 4:10pm ET the next day — roughly a 22-hour hold — at a venue that also permits
automation at the funded stage.** [D258](decisions/D258-the-prop-track-candidates.md)'s C1 is
therefore **live, not a loophole**, and **the +8.59%/yr overnight drift is reachable inside prop
rules.**

**Topstep is the opposite and its own sources conflict.** Its funded-account rules give a
wall-clock rule — *"All positions MUST be closed prior to 3:10 PM CT or prior to the market close
of that product, whichever is sooner"* — while its help centre says *"Topstep does not permit
holding positions from one session to the next."* **Treated as BLOCKED**, because an ambiguity
whose downside is account forfeiture is not one to resolve by inference.

**P2 is therefore restated as: no exposure across the venue's stated flatten time.** Whether that
forbids the overnight is a fact about the venue, to be quoted from its own documentation, never
assumed.

**Two cautions that come with it:**

1. **P1 becomes the binding constraint, and it bites harder here.** A 22-hour futures hold is 22
   hours of **open-equity** exposure against a ratcheting 4% floor. The equity overnight return is
   a close-to-open *gap*; the futures position lives through the whole *path*. **A −2% overnight
   excursion breaches at half the deployed size, even if the position closes green.**
2. **The measured +8.59% is a CASH-EQUITY statistic and may not transfer.** It is the close→open
   gap on ETFs. Futures trade that period continuously, so the drift may be the same while the path
   — which is what P1 measures — is entirely different. **We hold no futures data and cannot test
   this on anything we own.**

**And the rule is new.** MyFundedFutures' overnight permission dates from March 2026 by secondary
report. A rule that changed recently can change back, which is a business risk on top of the
research one.


## R12. Two tracks, two standards — and a candidate closed on one is screened against the other before it is discarded

**This programme now serves two books with incompatible constraints**, and a single set of hurdles
cannot serve both:

| | **personal** | **prop** |
|---|---|---|
| book | [BOOK.md](BOOK.md) | [BOOK_PROP.md](BOOK_PROP.md) |
| drawdown tolerance | ~20% | **4% trailing, on OPEN equity** |
| overnight | permitted | venue-specific ([R11](#r11) amendment) |
| automation | unrestricted | funded stage: Topstep and MyFundedFutures only |
| instrument | ETFs, single names | futures |
| **round-trip cost** | **~3.8 bp** (IBKR Pro, and the **$0.35 minimum binds below ~$1,000 per position**) | **~0.2 bp** |
| hurdles | E, H, V | **P1–P6** |

**The rule:** a candidate that fails one track's standards is **screened against the other's before
it is closed**. A `CLOSED` verdict is track-specific and does not travel.

**Because the differences are large enough to flip a verdict, in both directions:**

1. **Drawdown tolerance differs fivefold.** A strategy failing P1's 4% trailing floor may sit
   comfortably inside a personal book that already runs at −18%.
2. **Cost differs by roughly twenty times.** [D258](decisions/D258-the-prop-track-candidates.md)
   recorded this: constructions excluded on ETF cost arithmetic — scalping,
   [D247](decisions/D247-the-short-side-at-fifteen-minutes.md)'s intraday shorts, most of the
   intraday microstructure literature — **clear their costs by an order of magnitude on futures.**
   **A cross-screen must RE-COST, not merely re-threshold.**
3. **Timeframe is not a property of the edge.** D247 measured S1 and S2 breaking at 15 minutes while
   working daily — *"15-minute sampling breaks both estimators in both directions."* **A rule that
   fails on a lower timeframe may work on a higher one, and the converse.** Neither result closes
   the other.
4. **The prop route cannot use the personal book's edge at all.** 86.6% of it is timing that
   accrues overnight, so P2 forecloses it on most venues regardless of sizing.

**Corollary — a stop condition must now name its track.** "CLOSED" without a track is ambiguous, and
the cross-screen is what stops nine studies' worth of work being thrown away because it failed the
wrong bar.

**Scope:** binding from 2026-08-29. Applies retroactively to every candidate closed in the
2026-08-28/29 sessions, none of which was screened against the prop track's cost structure.

## R13. A ledger is scoped to a hypothesis, and transfers only where it shaped the search

**A multiplicity count corrects for the looks that could have produced the candidate being
reported. It therefore transfers to a new study exactly when the new study's search space was
shaped by those looks — and not otherwise.**

**Two tests, both required, before a count is carried:**

1. **Same hypothesis?** Not the same *goal* — every study in this programme wants a tradeable
   edge — but the same *proposition under test*, on a comparable universe.
2. **Did it shape the search space?** If the new study's candidates, scores or fixtures exist
   *because of* the earlier work, the count carries. If the candidates were arrived at
   independently, it does not.

**Because inheriting looks spent on a different hypothesis is not conservatism, it is
over-correction, and it makes a finding unfalsifiable by construction.** A programme that sums
every look it has ever taken into every new ledger eventually reaches a floor no measurement can
clear — at which point the count has stopped being a statistical correction and become a way of
never having to accept a result.

### The two worked examples, both settled by the principal

**The terrain programme's 259 — NOT carried into
[D272](decisions/D272-the-volume-profile-as-a-positional-input.md).**
`TERRAIN_RESULTS.md` says *"anything that reuses these sensors inherits the count"*, and I applied
it. **The principal pushed back and the document supports them:** that row is labelled **"Total on
one hypothesis"**, and the same file closes with *"a different data source, a different claim, or a
genuinely new construction starts a new document and a new ledger, with this one disclosed."* D272
had all three — equities not crypto, independence of an input not directional signal from a map.

**The ETF programme's 45,783 — NOT carried into the single-name intraday work.**
[D218](decisions/D218-the-impulse-macd-replication.md) states its own floor as *"+1.42 Sharpe at 45,803 looks — no
arm anyone runs on **this fixture** can clear it"*, scoped in its own words to the 57-ETF **daily**
fixture. That count accumulates pairs studies, breakouts, the MACD ladder and structure work:
hypotheses the single-name 15-minute search is not testing, on universes it does not use.

**What DOES carry into that work is roughly 118** — D264 through D276 — because those studies built
the bases and the scores the later ones mine, so their search space was not chosen independently.

### Corollaries

- **A count is never reset to zero by relabelling.** Test 2 is the guard: reusing a component, a
  fixture or a candidate list carries the looks that produced it.
- **Disclose what you do not carry, and say why.** An undisclosed exclusion is indistinguishable
  from an oversight.
- **The ledger is bookkeeping; the floor is the test.** What actually prices a search is the
  empirical best-of-N floor over that search (D228), computed from the data. R13 governs what
  number appears in a table, not what evidence exists.

**Scope:** binding from 2026-09-01. **Records D247 through D276 carry the older convention** —
a single cumulative count across the whole programme — and are **not** restated. R13 explains the
discontinuity rather than erasing it, the same way [R11](#r11)'s amendment and
[R12](#r12)'s retroactive scope were handled.

---

## R14. The whole promotion tree is pre-registered before stage 1, and looks multiply across stages

The promotion flow is **signal hunt → sharpen with exits → strategy → tested as
100% of a book → admitted as an arm**. That is the route **when things go well**, and
written down it is a ladder. Left implicit it becomes a reason never to close anything,
because every failure at stage *n* invites one more attempt at stage *n−1*.

**Both halves of this rule exist because the pipeline is otherwise a licence.**

**1. The tree is registered ONCE, up front** — the exit family, the target family, the
strategy construction, the promotion rule and the stop condition at every stage — before
stage 1 runs. Registering stage by stage as results arrive is the same search wearing a
new label each time.

**2. Looks MULTIPLY, they do not add.** Four stages with five choices each is `5^4 = 625`,
not 20. A candidate reaching stage 3 carries stage 1's and stage 2's looks under
[R13](#r13), because both decided which candidate arrived. A stage-1 selection made on the
fixture stages 2–3 then reuse contaminates everything downstream, so the floor that matters
at the end prices the whole tree.

### What the pipeline relaxes, and what it does not

It relaxes **sufficiency to existence**: stage 1 must show the effect is *there*, not that
it is *enough*. Stage-1 gates are therefore **t-based, not magnitude-based** — D288's
spread floor was the wrong instrument and its best candidate stood at 1.70× the null's
largest draw while failing on size.

It relaxes nothing else, and **the empirical uplift from stage 2 in this programme is
~1.0× — nothing.** D286: the exit rule carried no information and the rule nobody designed
beat all three deliberate ones. D285: the cap genuinely cut losers, touched trades ending
−860 bp at 23.2% profitable, and still produced no viable book. **Stage 2 supplies margin,
never rescue.** A signal failing cost by a factor of two at stage 1 is closed at stage 1.

### Two orderings are fixed

- **Correlation to existing arms is measured at STAGE 1**, not at admission. It is nearly
  free, and discovering at stage 5 that a candidate is 0.9 with S1 spends four stages to
  learn something available on day one.
- **The holdout is read at STAGE 4 or not at all.** It is the scarcest asset in the
  programme — one clean read — and spending it on a bare signal that was always going to
  need stages 2–3 is the worse trade.

**Low correlation is necessary and nowhere near sufficient for admission.** A zero-edge
strategy is uncorrelated with everything; an arm needs a standalone IR before its
correlation is worth discussing.

**Scope:** binding from 2026-09-02. Full statement of the stage gates in
[D289](decisions/D289-the-promotion-pipeline.md).

### ADDITION to R14, 2026-09-08 — a FUNCTION choice is a free parameter too, and a worse one, because it cannot be swept

**The principal's argument, recorded because it corrects a bias in how this programme has been
reasoning about parameters.**

The received position here has been that free parameters are the danger and parameter-free
constructions are safer. **That is half the picture, and the missing half is the more useful one.**

> **A swept parameter is dangerous but DIAGNOSABLE.** Sweep it and the shape tells you what you have:
> monotone progression or regression, a smooth hump, or a knife-edge. Those shapes are evidence in
> their own right.
>
> **A parameter-free function forfeits that diagnostic** — you cannot sweep what does not exist — and
> **the choice of function is itself a free parameter**, drawn from a large discrete space, undeclared
> and un-swept. It is *less* diagnosable than a continuous one, because functions have no natural
> neighbourhood: `lower_wick`'s neighbour is not `upper_wick` in any sense that makes a shape readable.

**The record supports this and I had it backwards.** This programme's most informative results have
come from *swept* parameters, and its parameter-related *failures* were about thresholds that were
never swept at all:

| | |
|---|---|
| [D381](decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange-rate-is-fixed.md) | stops hurt **monotonically in fire rate** — 5% → 10% → 20% gave +142.79, +126.06, +109.86. **The monotonicity was the finding**: it said the damage was mechanical, not a bad threshold. A parameter-free stop could not have said that |
| [D378](decisions/D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md) | the horizon profile, 7.82 → 3.94 bp/bar across caps 5→60, **carried the front-loading result** — a shape, not a point |
| [D368](decisions/D368-RESULT-the-relaxation-sweep.md) | asked the shape question directly and answered "**neither knife-edge nor curve**" — only reachable by sweeping |
| **against** | [D374](decisions/D374-RESULT-the-breadth-bar-was-unreachable-and-it-failed-the-most-diversified-book-in-the-null.md) and [D376](decisions/D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two-cohort-books-at-0.92.md) retired H4's 10% bar and gate 1d's 0.50 — **both fixed in advance and NEVER swept.** The defect was un-calibration, not parameterisation |

**So the rule is not "prefer fewer parameters". It is:**

> **Declare the parameter, sweep it over a stated grid, report the whole grid, and read the SHAPE as
> evidence.** A result that survives only at one grid point is a knife-edge and is reported as
> unresolved. A result that moves monotonically, or peaks smoothly in the interior, has told you
> something a single point could not.
>
> **And when a construction has no tunable parameter, say what discrete space its FUNCTION was chosen
> from and price that**, because that is the free parameter you actually used.

**The multiplicity cost of a dense sweep is much smaller than the cell count implies**, and this is
what makes the rule affordable. Neighbouring grid points are near-duplicates, so the max over them
grows far more slowly than the max over the same number of independent tests. Measured here:
[D382](decisions/D382-RESULT-nothing-clears-on-the-stable-statistic-and-the-books-are-the-market.md)'s
best-of-38 rotation floor at hold 20 ran **p50 +185.02, p95 +190.01, max +192.32** over 50 draws —
**a 4% spread from median to maximum across 38 correlated cells.** Adding grid points to a continuous
parameter is cheap; adding independent hypotheses is not.

### AMENDMENT to R14, 2026-09-02 — both "tightenings" were wrong, and the principal was right

R14 was written the same day and is corrected here rather than rewritten, because the
error is instructive and the original claims have already been quoted.

**1. "Looks MULTIPLY across stages" is WRONG. Selection on spent data is free.**

Selecting on data that is already burnt does not invalidate a later test on data that has
never been touched. The out-of-sample p-value does not care how many candidates were
auditioned in-sample; 625 in-sample combinations followed by ONE holdout test is still one
test at its stated level. The principal's objection was correct: **the mining fixture does
not become more spent.**

What a wider search actually costs is the **PRIOR** — the survivor is likelier to be noise,
so a holdout read is likelier to be wasted. That is an economic cost on a scarce resource,
not a statistical invalidity, and R14 stated it as the latter.

**The distinction that does hold: in-sample numbers are free for SELECTION and expensive as
EVIDENCE.** The moment an in-sample number is reported as a result, multiplicity bites that
claim. Under the pipeline, stages 1-3 are selection and only stage 4 is evidence, which
makes an in-sample floor a **TRIAGE DEVICE** -- "is this worth one of my scarce holdout
reads?" -- and not a verdict on whether the effect is real. D288's gate A read as a verdict;
it was a triage.

**The ledger therefore counts HOLDOUT READS, not in-sample looks.** In-sample looks are
still disclosed, because what shaped a search is worth knowing, but they are bookkeeping
rather than a bar. The one place multiplicity genuinely compounds is iterating THROUGH the
holdout -- fail, search more, read it again -- which [R8](#r8)'s one-read discipline
already governs.

**2. "Exits cannot create edge" is WRONG, and the evidence cited against them shows the
opposite.**

R14 cited D285's cap CUTTING LOSERS -- touched trades ending -860 bp at 23.2% profitable --
as evidence that exits do not work. That is a measurement of an exit WORKING. The
inference does not follow.

The correct reading, which is the principal's: the exit improved per-trade quality, and the
money was lost because **exiting forced RE-ENTRY into a weak signal**. Earlier exit -> more
noise -> re-enter -> repeat. That is a failure of the entry rule the exit handed control
back to, not of the exit.

**The real constraint is COUPLING, not prohibition: an exit cannot be evaluated at trade
level.** A stop that improves the average trade and hands the freed slot to a coin flip is
a book-level loss wearing a trade-level win. Stage 2 is therefore measured **on the book,
including whatever re-enters** -- which is why D286's `disp` beat the designed exits: it
exited on displacement, so the slot always went to a BETTER-RANKED name rather than back to
the same weak signal.

**Stage 2's gate becomes:** report the exit's effect on per-trade quality AND on the book
that includes re-entry, and say which of the two moved. An exit that improves trades while
the book gets worse has located a re-entry problem, and that is a finding about the ENTRY
rule.

### SECOND AMENDMENT to R14, 2026-09-02 — name-split CV is necessary and NOT sufficient

D290 ran a 51-candidate stage 1 under this rule and its ranking statistic proved
blind to the thing that mattered most.

**AN ENTRY ARTIFACT GENERALISES ACROSS NAMES PERFECTLY WELL.** `lower_wick` ranked
second on the short book at name-split CV +6.19, on an effect that keeps **-11%**
of itself after one skipped bar and **+1%** entered at the next open. Fifteen of
51 candidates collapsed on a test that was not in the pre-registration.

**NEW GATE 1e, BINDING ON EVERY FUTURE STAGE 1 -- CAPTURABILITY.** Enter at
open[t] rather than at the close[t-1] that generated the signal. Require
**open-entry t >= 2.0 and retention >= 50%**. Open entry rather than skipping a
bar, because skipping removes a real fast signal and an entry artifact ALIKE --
"the edge dies at skip 1" cannot tell them apart. The skip test remains a
reported diagnostic, not the gate.

**TWO DIAGNOSTICS MUST BE REPORTED ALONGSIDE.** The overnight/intraday split,
asserted to compose to the price return, showing what share is earned in the
segment you cannot trade into. And LIQUIDITY-TERCILE SCALING, which is the only
cut that identifies bid-ask bounce specifically: bounce is proportional to the
spread and information is not. That cut corrected an over-confident claim in
D290 -- the axis-B effects scale 1.2x against a 5.2x spread gap and are therefore
NOT bounce, while the volume signals scale 3.0x-4.2x and are.

**Name-split CV stays as gate 1f, necessary and explicitly insufficient.** Full
statement in [D289](decisions/D289-the-promotion-pipeline.md)'s second amendment.

### THIRD AMENDMENT to R14, 2026-09-02 — a cost ratio is unreadable without turnover

D290 ranked `price_log` first on the spread construction and it was the only
tier-1 candidate clearing its measured cost, at 1.96x. It turns over 1.9% per bar
and holds a name for 51 bars: it is a STATIC CHARACTERISTIC TILT, not a signal.
It never says when to do anything, and its cost ratio is one round trip
amortised over a book that scarcely changes.

**NEW GATE 1g -- report TURNOVER PER BAR, MEAN HOLDING RUN, and DEAD-NAME SHARE
PER LEG with every candidate.** Reported, not thresholded: a slow signal is fine.
What this prevents is a characteristic presenting itself as a signal, and a cost
ratio being read as good when it is the product of inactivity. Cost per unit time
is `round trip x turnover`; the ratio alone is meaningless.

`price_log` also carried 33.5% dead names in its LONG leg against 10.7% in its
short. On a 35.7%-dead fixture "buy the cheapest fifty" is buying the
pre-bankruptcy tail, and the asymmetry is what the per-leg split exists to show.

**NULL-DESIGN NOTE.** Rotation is a WEAK null for a near-static score -- rotating a
score that is almost constant per symbol barely changes the book, so the z is
inflated. Under ~5% turnover per bar, read the within-bar permutation null first.

### FOURTH AMENDMENT to R14, 2026-09-02 — a score is a ranking; its direction is a choice

`legs_from_order` hard-codes long = `order[:N]`, short = `order[cnt-N:cnt]`. No
score in D290 was ever asked which way round it should go, so the DIRECTION is
imposed by the construction rather than carried by the signal. Seven of 51 came
out NEGATIVE on the spread -- range_frac -140.3 bp, upper_wick -17.2 t-2.20 --
which read the other way are positive results that nothing priced.

**NEW GATE 1h.** Gate 1b is extended: THE MECHANISM MUST DECLARE WHICH END GOES
LONG, before the run. That is the guard against sign-shopping, because a
direction chosen after seeing the sign is a free parameter no floor prices. Both
directions are then reported and the LEDGER COUNTS BOTH.

The point estimate is algebraically free -- `spread(-s) = -spread(s)`, the legs
simply swap -- but THE NULL IS NOT, because `max(-t) != -max(t)` and the
best-of-grid statistic is asymmetric. A result in the direction the mechanism did
NOT predict is reported as DIRECTION-INVERTED, and counts against the mechanism
even when the number is good.

**TWO CONSEQUENCES OF "IT IS A RANKING".** Monotone transforms are the SAME
candidate -- price_log and raw price give an identical ordering -- so candidate
lists are deduplicated by ORDERING, not by formula. And a rank book cannot say
"nothing qualifies today": it holds exactly N names however ordinary they are, so
LEVEL- OR THRESHOLD-BASED SELECTION IS UNTESTED by this design and needs its own
pre-registration.

### FIFTH AMENDMENT to R14, 2026-09-02 — a boundary peak is unresolved, not concluded

Measured on D290's 51: EVERY long-only candidate peaks at the corner (N=50, k=40)
and 1 of 51 survives the nulls. On short-only, EDGE peaks pass 0 of 6 against 19
of 45 interior. A peak at the edge of the sweep means the statistic was STILL
CLIMBING when the grid ran out -- which is what drift accumulating with horizon
and variance shrinking with N both look like.

The SPREAD does not show the pattern, and that is correct rather than an
exception: the corner peak signals drift accumulation and the spread construction
removes drift. The flag belongs to constructions that carry exposure.

**NEW GATE 1i -- report where the peak sits. An interior peak is a maximum; an
edge or corner peak is UNRESOLVED, not concluded.**

A SEPARATE CAUTION APPLIES TO THE SPREAD ANYWAY: t rises with N through
AVERAGING, not a larger edge. close_in_range earns +71.8 bp at N=3 and +20.4 at
N=50 while its t rises. A peak at N=50 is a small per-name effect rescued by
breadth -- FINDINGS sections 4 and 9. REPORT THE PER-NAME EFFECT BESIDE t so
breadth cannot masquerade as strength. A peak at max k means the grid may be too
short; extend it or record the result as horizon-unresolved.

### FOURTH AMENDMENT to R14, 2026-09-03 — the holding period is a DEPLOYMENT variable, not a research one

D294 re-read D293's grid cost-adjusted and found the confluence's horizon peaks
in three different places depending on what you optimise:

| optimise | k | gross bp | t | bp/bar | × robust cost |
|---|--:|--:|--:|--:|--:|
| **Sharpe / edge density** | 2–3 | +30 to +44 | +2.84 / +3.45 | **+15.14 / +14.68** | 0.29 / 0.42 |
| **t** | 5 | +61.91 | **+3.80** | +12.38 | 0.588 |
| **gross and cost coverage** | 13–16 | **+84.84 / +85.45** | +3.38 / +3.23 | +6.53 / +5.34 | **0.805 / 0.811** |

**The principal's ruling, and it is right: stage 1 does not own this choice.**
Hold length trades gross against edge density, and which one you want is a
function of the CAPITAL, not of the signal:

- **dedicated capital** → maximise **gross**. The slot has no alternative use,
  so total return per slot is what matters.
- **shared capital** → maximise **Sharpe / edge per unit exposure**. The
  constraint is the opportunity cost of the slot, so density is what matters.

**So stage 1 REPORTS the whole horizon profile and picks nothing.** Picking a
single k on any one criterion smuggles a capital-allocation decision into a
signal test, and then prices it as if it were a discovery.

**Two consequences.** A candidate is described by its profile, not by one cell —
gate 1i's "interior vs edge" reading applies to the profile's *shape*, and
`hist_L`'s N=25 being a spike while the confluence's k=13–16 is a plateau is a
real difference in robustness that a single-cell summary hides. And the
multiplicity a grid-max null prices is the search for max `t`; **selecting k on
any other criterion is a different search over the same grid and needs its own
null.**

## R15. A signal is a positive gross mean per trade above its nulls; cost is tuned afterwards, and only the principal closes an avenue

*Added 2026-09-06 at the principal's ruling, after D360.*

**The criterion for a signal at the signal stage is gross:** a positive mean per
trade, above the p95 of its pre-registered controls. The cost line — spread
convention, borrow, the crossing convention — is reported beside it in full and
**decides nothing at that stage**; cost is engineered afterwards (hold, floor,
fill, spread ceiling), and confluences and gates are the next step for a signal
that passes, not grounds for discarding one that nets negative.

**A research avenue is closed by the principal, never by a record.** A stop
condition says what the construction showed and lists what was not tested. It
does not say the axis is closed, that "what remains" is X, or that no further
study is worth writing. Three constructions failing is three constructions.
D360's §6 and §9 were written against this rule and carry an addendum.

---

## R16. A published number is not reproducible without naming the build it was computed on — reproduce it EXACTLY on that build, or do not inherit it

*Added 2026-09-08, after D390's `[ID]` gate.*

**A quantity quoted from an earlier record is not a constant. It is the output of
a pipeline that has since moved.** Reproducing it is the only way to know whether
the object being extended is the object that was published — and the check must be
**exact on the original build**, never approximate on today's.

### What happened, and it is the whole of the rule

D390 rebuilt D280's part-4C composite in order to score one of its terms alone.
`[ID]` required the composite to reproduce D280's published mean IC before the new
term was read. **It failed:**

```
D280 published, 2026-09-02   mean IC  -0.013726972    t -5.074623
recomputed, today's default  mean IC  -0.013728429    t -5.075204
relative difference          1.06e-04
```

**1.06e-04 is not float noise.** A summation-order artefact is ~1e-16; this is
twelve orders larger. The cause was found by `git log` on the dependency, not by
staring at the numbers: **`ragged_panel.load_ragged` gained a `dividend_bound`
argument on 2026-09-05 (D333, `3849274`), three days after D280's artifact was
committed, and it defaults to `True`.** D280's numbers live on the *unbounded*
panel, which no longer exists by default.

**Under `dividend_bound=False` the composite reproduces to 1e-9.** The object was
D280's all along; the build was not.

### The rule

1. **Name the build.** A record that re-derives, extends or checks a published
   quantity states which panel, fixture, cache and estimator version it is on.
   *"Reproduces D280's IC"* is not a claim until that sentence exists.
2. **Reproduce on the ORIGINAL build, exactly.** The identity check runs on the
   configuration the number was published under, at 1e-9 or bit-equality — not on
   today's, and never at a tolerance chosen after seeing the gap.
3. **Then measure on today's, and report BOTH with the delta attributed.** D333's
   own convention: it repriced the stack *"under both panels"* and asserted
   *"identity with D332 under the unbounded panel."* A pipeline change that moves
   a number is a finding about the record, not an inconvenience.
4. **DO NOT WIDEN THE TOLERANCE.** A failing identity check is evidence. Loosening
   it converts a discoverable fact — *this published number is no longer
   reproducible* — into a silent one. If the original build cannot be
   reconstructed, say so and mark the inherited quantity **UNVERIFIED**; do not
   quote it as though it were checked.

### Why it is a standing rule and not a D380 footnote

**Every study here inherits numbers.** The pipeline has changed under them at
least twice in recorded memory — D334 added `ragged_panel.py` to a cache key for
exactly this reason, and D333 changed what a return *is*. **Any quantity published
before 2026-09-05 and derived from `load_ragged` is on the unbounded panel**, and
that includes D256, D279, D280, D281, D283 and D284. None is wrong; each is
conditional on a build, and R16 is what makes that condition visible instead of
assumed.

**The cheap form of this rule is one line in a runner**: an assertion that
reproduces the inherited number before anything new is computed. D390's `[ID]`,
D373's `[MIR]`, D362's `[ID]` and D377's `[REC]` are the same instrument, and
**D377 already set the precedent for what to do when it cannot be met exactly —
correct the record, do not quietly loosen the bar.**
