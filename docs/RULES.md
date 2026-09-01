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

New decisions go in `docs/decisions/` (next number: **D268**), shipped changes go in
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
| **P1** | **Trailing drawdown ≤ 4%**, measured on **OPEN** equity | Apex trails on unrealised intraday equity; open profit lifts the floor before anything is closed. Our closed-equity max-DD is a different and gentler statistic |
| **P2** | **No exposure across the VENUE'S FLATTEN TIME** — see the amendment below; this is venue-specific, not universal | Topstep 3:10pm CT, Apex 4:59pm ET, MyFundedFutures 4:10pm ET |
| **P3** | **Worst single day ≤ 2%** | Daily loss limits run 2–3% |
| **P4** | **Expected time-to-breach > 3 years** | Against a trailing barrier and positive drift, ruin is certain eventually; the question is only when. At Sharpe 0.9 a 20-account book died every ~3.85 years |
| **P5** | **No single day > 40% of trailing-year profit** | Consistency rules cap a single day at 30–50%, so a lumpy-but-profitable strategy is ineligible for payout while up |
| **P6** | **Venue permits automation at the FUNDED stage** | Apex: *"No Automation or Algorithm Usage allowed"* on Performance Accounts, penalty *"forfeiture of all funds and balances"*. Take Profit Trader bans EAs throughout. **Only Topstep and MyFundedFutures permit it.** Third-party comparison tables contradict both firms' own terms and must not be relied on |

**Because:** the committed book fails P1 by roughly sevenfold (−29.82% at deployed size against 4%)
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
