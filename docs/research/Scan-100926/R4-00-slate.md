# Scan-100926 · Round 4 — slate

**PREPARED, NOT DISPATCHED.** Committed before any agent exists. **No agent has been launched.**
Campaign contract: [`00-SCHEMA.md`](00-SCHEMA.md). Round 3: [`R3-99-record.md`](R3-99-record.md).

**Four lanes, and every one is downstream of a round-3 finding — two of them downstream of findings no
lane was commissioned to make.** Budget, on the contract's now-revised §2: a four-lane round **under the
depth mandate** costs **~1.3–1.5M**, not the pre-mandate ~1.1M. Round 3 was **~1.44M**.

| lane | file | what it is for |
|---|---|---|
| `D1` | `R4-01-the-nine-unexamined-nodes.md` | **`C2` handed us twelve ranked construction nodes. We had found three. Two of the nine we missed OUTRANK all three.** |
| `D2` | `R4-02-is-the-quarterly-advantage-seasonal.md` | **`C1`'s post-bar finding, which if true kills `C1`'s own headline** |
| `D3` | `R4-03-are-these-two-signals-the-same-signal.md` | puts **evidence** under round 3's central conflict `F1` — **without adjudicating it** |
| `D4` | `R4-04-when-does-the-premium-arrive.md` | **`C4` measured three of 132 months carrying half the total, and nobody asked the obvious question** |

---

## The overlap audit, run against BOTH campaigns — and it moved one lane's scope rather than killing it

**Zero hits** across `docs/` for: `conditional sort` · `value-weight within` · `rank weight` ·
`signal weighting` · `concentration of the premium` · `arrival of the premium` · `premium
concentration`. **Single hits**, all inside round 3's own briefs: `quantile count`, `sort dependence`,
`number of portfolios`. Non-zero hits **opened, not assumed**: `seasonality` **11**, `winsor` **6**,
`loss-mak` **3**, `multiple testing` **5**, `trailing four-quarter` **2**.

**One lane had its scope changed by the audit, and this is the important one.** `seasonality` returns
11 files — and two of them are **exclusion declarations**: `R1-02` line 13 states *"This brief does not
research momentum, calendar/seasonality effects"*, and its line 230 marks seasonal momentum
**"EXCLUDED (calendar)"**. The first campaign excluded **calendar effects** as a signal territory.
**So `D2` is hard-scoped to the ACCOUNTING INPUT and away from calendar returns entirely** — see `D2`'s
scope block. The distinction is real: a retailer's fiscal-Q4 revenue being four times its Q1 is a
property of the *variable being sorted on*, not a calendar effect in returns.

**Two candidate lanes were cut.**

1. **A multiple-testing / critical-value lane, cut.** `C2` found that **nobody reports the non-standard
   error of a null**, which is tempting ground. But `multiple testing` resolves to **our own decision
   records `D29`, `D350` and `D352`**, plus [`../shorts/01-cross-sectional-anomalies.md`](../shorts/01-cross-sectional-anomalies.md)
   and `R1-02`'s own `[C5]` flag on selecting from 209 signals. **The territory is partly covered and
   the bootstrap-block-length half of it is excluded ground from the first campaign.**
2. **A live-money fund-record lane, cut as a standalone.** `C4` already read **filed N-CSRs** and found
   large-cap quality funds at −82 to −124 bp/yr against indexes at −68/−60, with mid/small positive,
   and caught **one fund's own filing disclosing it tracked a different, non-quality index until June
   2019**. A whole lane would be **deepening `C4` rather than opening ground**, and the segment question
   it would ask is folded into `D4` instead, where it belongs.

---

## Why these four

**Round 3 ended with the field's own answer to "how much does the answer move" — a lot — and with two of
its own lanes reaching opposite verdicts on the same question. Round 4 is about closing that out, and
not one lane is a new signal.**

**`D1` exists because `C2` handed over a list and we have only examined a quarter of it.** `C2` found a
published ranking of **twelve** construction nodes by how much each moves a `t`-statistic. Round 2 had
independently discovered **three** of them the hard way. **Nine remain unexamined here — and two of the
nine outrank all three we found:** outlier treatment at mean |Δt| **3.74** (reaching **12.86** on
quasi-random profitability ratios), and **dropping loss-makers, which is the #1 node for profitability
sorts specifically.** Leaving a ranked list of known traps unexamined after paying to discover it is the
one clearly wasteful thing this campaign could do next.

**`D2` exists because `C1` found it after its bar was met, and if it is true it kills `C1`'s own
headline.** Round 3's biggest positive finding is that the **quarterly** variant is 2–4× the annual one
(0.16 → 0.51, `t` 1.04 → 3.40). `C1` then noted, uncommissioned, that **a single-quarter sort is an
unadjusted seasonal sort** — the word *"season"* appears **zero times** in the source paper in either
version and zero times in its 2025 retrospective, and Hou–Xue–Zhang reach the point for `ROE` and
**never apply it** to the gross-profitability variant. **If the quarterly advantage is a fiscal-calendar
artefact, round 3's best result is an artefact.** Nobody has checked.

**`D3` exists because `F1` is the round's central conflict and nothing has been put UNDER it.** `C3`
says an equal-weighted profitability long leg earns `t` **0.45** against its own universe; `C4` says
**`t` 3.00–3.56**. Both fully controlled. The named differences are **definition, dataset and cut** —
and `C4` reports that its own two datasets disagree with each other too, *"resolving on definition"*.
**So the question is whether these are two measurements of one signal or measurements of two different
signals.** That is answerable from published sources, and answering it does not require picking a
winner — **it tells the principal what the disagreement IS.**

**`D4` exists because `C4` measured the most decision-relevant number of the round in passing and nobody
asked the follow-up.** Against the value-weighted market the long leg is **flat post-publication**
(+0.187 → +0.179 %/mo, `t` 1.25) — **and three of 132 months carry half the total.** A premium that
arrives in 2% of the months is a completely different proposition from a steady drip, and it governs
whether a book can be *held* long enough to collect it. `C3` touched this once (*"concentration worsens
drawdown and return together"*) and did not make it the subject. **`concentration of the premium` and
`arrival of the premium` return zero hits across both campaigns.**

---

## `D1` — the nine unexamined nodes, asked for a LONG LEG

**Sub-questions.** For each of the highest-ranked nodes this programme has **not** examined — **outlier
treatment** (winsorise vs trim vs neither, and at what cutoff), **dropping loss-makers / negative
denominators**, **quantile count**, **sort dependence** (dependent vs independent, and the order of a
multi-way sort), **rebalancing frequency**, **level vs log**, **stock-age filters** — what does the
literature say about **how to choose**, and does it justify the choice or inherit it? Which are
**arbitrary** and which **encode a different economic question**? `C2` found that every node it examined
closely turned out to be **non-arbitrary**, including a June rebalancing convention that carries a
momentum exposure — **test that claim on the nodes `C2` did not examine closely.** And the question
round 3 makes unavoidable: **what does each node do to a LONG LEG specifically**, given that three
separate literatures report only spreads?

**The bar.** A node-by-node statement of what the literature justifies, what it inherits, and which
nodes move a long leg rather than only a spread — **or** an explicit finding that the rankings are
spread-only and **silent about the long leg**, which would be the fourth independent instance of round
3's organising fact.

## `D2` — is the quarterly advantage a seasonal artefact?

**Sub-questions.** What is documented about **fiscal-quarter seasonality in the accounting variables
themselves** — how large is it, in which industries, and for the specific inputs a profitability sort
needs (revenue, cost of goods, SG&A, assets)? What do the standard constructions **do** about it:
single quarter, **trailing four quarters**, year-over-year change, **seasonal differencing**, or
nothing? Is there published evidence that a **quarterly characteristic sort** is contaminated by
seasonality, and has anyone measured a quarterly profitability sort **with and without** seasonal
adjustment? Does the contamination **vary with the fiscal-year-end distribution** — because a sort
formed in one calendar month mixes firms at different points in their own fiscal cycles? And the
programme-facing question: **does the trailing-four-quarter form, which `C1` found is the only
seasonality-free one, retain the quarterly advantage, or does it collapse back to the annual result?**

**The bar.** A named measurement of the quarterly advantage under a seasonality-robust construction —
**or** a clean finding that **nobody has ever checked**, which would make round 3's headline result
explicitly provisional and would be worth as much.

**HARD SCOPE — AND THE AUDIT MOVED THIS BOUNDARY, SO READ IT TWICE.** This lane is about **seasonality
in the ACCOUNTING INPUT being sorted on**. It is **NOT** about calendar effects in returns,
turn-of-month, day-of-week, FOMC dates, holiday effects, sell-in-May, or **seasonal momentum** — **all
of which are permanently excluded ground from the first campaign**, and one of which `R1-02` explicitly
refused. If the research drifts to *"do returns have a calendar pattern"*, it is in the wrong lane.

## `D3` — are these two signals the same signal?

**Sub-questions.** What exactly is the relationship between **gross profitability deflated by assets**
and **operating profitability deflated by book equity**? Numerator and denominator differences stated
precisely, and **whether any source regresses one on the other** or reports their correlation. Does the
literature treat them as **one family or as distinct signals**, and does it say so explicitly or just
assume it? Whether the **deflator choice — assets versus book equity — is itself one of `C2`'s ranked
nodes**, and if so where it ranks. How the two **reference datasets** construct each, **quoted from
their own documentation and code**, since round 3 found one dataset's code comment contradicting a
paper's restatements. And the sharp version: **is there a published measurement that computes BOTH on
one sample, so that the difference is construction rather than dataset?**

**The bar.** A sourced statement of what separates the two definitions and whether the literature
treats them as one signal — **or** a finding that no source computes both on one sample, which would
mean **`F1` cannot be resolved from published work** and would say exactly that.

**THIS LANE DOES NOT ADJUDICATE `F1`.** Its job is to say **what the disagreement is made of**. Both
`C3`'s and `C4`'s readings stay on the record whatever this lane finds, and a lane that comes back
saying *"the literature cannot separate them"* has **succeeded**.

## `D4` — when does the premium arrive?

**Sub-questions.** What is documented about the **concentration of a characteristic premium in TIME** —
the share of the total earned in the best *k* months, the number of months to reach half the cumulative
return, and whether any source reports it at all? The same **in NAMES**: how many names carry half the
leg's return, and the top-1/5/10 name share. Whether the premium's arrival is **clustered around
identifiable events or regimes**, or looks like a draw from a fat-tailed distribution with no structure.
What the literature says about **how long a holding period is needed for the premium to be reliably
present** — which is `C3`'s drawdown-duration question seen from the other side. And the question that
decides whether any of this is usable: **if the premium arrives in a small number of months, is there
any published evidence that those months are identifiable EX ANTE — or is the honest answer that it
must simply be held through?**

**The bar.** Named concentration figures with their samples and constructions — **or** a finding that
the literature reports **only means and `t`-statistics and never the arrival pattern**, which would
make `C4`'s three-of-132-months measurement the only number of its kind this programme has and would
say so plainly.

**A CAUTION THIS LANE CARRIES IN PARTICULAR.** This programme's own reporting rules require the
trade-distribution and concentration report **with the mean BELOW its median treated as the tell**, and
require trimming **1% from BOTH tails** — because dropping only winners is *"a flag, not a verdict"*, and
on a two-sided fat-tailed book the asymmetric trim *"always frightens"*. **If you report a concentration
figure, report the symmetric version beside it.**

---

## What every lane carries

**The depth mandate** ([`00-SCHEMA.md`](00-SCHEMA.md) §2a), verbatim and ahead of everything else — the
bar is a floor and meeting it is not a reason to stop; sources read **in full**, chasing appendices,
working papers, author pages, repositories and code; **at least one independent measurement with a
negative control**; exhaust the sub-questions **and then go past them**; and an explicit **"what I did
not open"** list. **Round 3's evidence that it works is in [`R3-99-record.md`](R3-99-record.md) §6, and
round 4's prompts will carry that evidence rather than just the instruction** — including the two
controls that **fired**, because a control that can fire is the only kind worth having.

**Then the standing rules** in §4 — with the wrong-HTTP-200 catalogue at **twelve** flavours and the
summariser rule at **eleven** caught instances. Plus the hazards on each lane's own path: `D1` and `D3`
get **the draft-versus-published break in the very paper that invented "non-standard errors"** (a 9% vs
53.5% swing on one winsorization choice); `D2` and `D3` get `C1`'s finding that **a reference
repository's code comment contradicted three independent second-hand restatements, and the code comment
was right**; `D4` gets the reminder that **`frames` returns last-filed values** and that `prevrpt` is a
hindsight column.

## What this slate does not claim

**No lane has been dispatched and no agent exists.** Every figure restated here is quoted from rounds
1–3's records, **not recomputed**. **Round 3's `F1` is open and this slate does not lean on either
side of it.** Both books are unchanged, nothing is closed, nothing is admitted, and **nothing in this
folder is elevated out of `docs/research/`.**
