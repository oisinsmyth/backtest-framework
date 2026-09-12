# Scan-100926 · Round 2 — slate

**Committed 2026-09-10 before the agents were dispatched.** Campaign contract and the rules every
agent carries: [`00-SCHEMA.md`](00-SCHEMA.md). Round 1: [`R1-99-record.md`](R1-99-record.md).

**Four lanes again** — round 1 came in at **~1.14M subagent tokens** against the schema's projected
1.0–1.4M, so the shape holds.

| lane | file | what it is for |
|---|---|---|
| `B1` | `R2-01-the-benchmark-question.md` | **resolves the crux of round 1's central conflict** — against what should a long leg be measured? |
| `B2` | `R2-02-profitability-deep.md` | the one surviving family `A1` can actually deliver, taken from survey depth to construction depth |
| `B3` | `R2-03-where-the-premium-accrues.md` | **does a slow characteristic premium accrue OVERNIGHT?** — joins the programme's own central fact to `A2`'s family |
| `B4` | `R2-04-shares-outstanding-and-float.md` | **closes round 1's dependency failure** — can net share issuance be rescued from free data? |

---

## Why these four: every one is a thread round 1 OPENED rather than closed

**`B1` exists because round 1's two most important lanes disagreed, and the disagreement is entirely
about a benchmark.** `A3` measured the long leg at **−0.04%/month against the value-weighted market**,
Var(t) = 0.98, below the luck null. `A2` measured **Var(t) = 1.35–1.81 and a signal share of
0.26–0.45 against each sort's own name-weighted universe**. **Both read the same literature. The
benchmark is the whole disagreement**, and nobody has asked which one is right for *this* book —
equal-weighted, long-only, dead-inclusive, absolute-return, competing with cash rather than with an
index.

**`B2` exists because round 1 narrowed the field to two families and `A1` can deliver only one.**
Profitability survives; share issuance needs a split-adjusted share count that **XBRL does not
carry**. So profitability is the single candidate with both evidence and data — and `A2` surveyed the
family without going inside it. **Which definition, constructed how, with what lag, and is there
long-only evidence for that definition specifically?**

**`B3` is the one lane not derived from a constraint, and it is the most distinctive question the
programme can ask.** Its own most load-bearing empirical fact is that **its edge is overnight**
(D247, D280). `A2` established that a characteristic premium **accrues at a constant rate across
1–12 months** — flat, with a positive control proving the flatness is a measurement. **Nobody has
asked whether that constant rate is earned overnight or intraday.** If a monthly premium turns out to
accrue overnight, that is a join between the programme's own finding and the only family still
standing. If it accrues intraday, that is a direct obstacle and worth knowing before any build.

**`B4` closes round 1's `D9` — a dependency failure rather than a contradiction.** `A2` called share
issuance its **cheapest** non-free candidate, needing *"only a split-adjusted share count."* `A1`
found **no split history anywhere in XBRL.** Both are right about different halves. **A share-count
panel is a small, answerable data question with an outsized payoff**, and it has never been asked.

## What this round deliberately does NOT do

**No new territory hunt.** Eleven died in the previous campaign and round 1's evidence says the
constraint was never the territory. **No lane re-opens the long-only question itself** — `A3` answered
it as asked, and `B1` attacks the *benchmark* beneath it, not the verdict. **And no lane re-surveys
the characteristic family** — `A2` did that; `B2` goes inside one member of it.

---

## B1 — the benchmark question

**Sub-questions.** What benchmarks the leg-decomposition literature actually uses, and whether it
justifies the choice or inherits it. The arithmetic difference between **long-minus-market**,
**long-minus-its-own-universe**, **long-minus-equal-weighted-universe**, and
**characteristic-matched** benchmarks — and what each does to a reported long-leg alpha. Whether a
characteristic-matched benchmark is **constructible from free data**. What an **absolute-return**
book should use, given that it competes with cash rather than with an index and has no tracking-error
mandate. And the question that decides the conflict: **is `A2`'s name-weighted universe the right
comparison for an equal-weighted book, or does it build the answer into the benchmark?**

**The bar.** A stated recommendation with its reasoning, **or an explicit finding that the literature
does not justify its benchmark choices** — which would itself resolve the conflict, by showing both
readings are defensible and the question is open.

## B2 — profitability, deep

**Sub-questions.** Which definition survives post-2005 cost-honest treatment — **gross, operating, or
cash-based operating** — and on what samples, reported separately rather than pooled. **Long-only
evidence for the surviving definition specifically**, since round 1 left that contested. The exact
construction: numerator, denominator, scaling, and the **lag convention** from fiscal period end to
portfolio formation. Breadth: how many names per leg, and whether ~10 effective independent
instruments suffices. And **the computability detail `A1` surfaced**: with `86–91%` of quarterly tags
being filer-invented extensions and a single-tag panel collapsing at FY2018, **which tags does each
definition actually need, and do they survive the collapse?**

**The bar.** One named definition with its construction stated precisely enough to implement, its
post-2005 cost-honest evidence, and its tag list — or a finding that the definitions disagree enough
that the family is not one candidate but several.

## B3 — where the premium accrues within the day

**Sub-questions.** Is there published evidence decomposing any **characteristic** premium into
overnight and intraday components? The known literature decomposes **market** and **momentum/reversal**
returns; the question is whether anyone has done it for a **slow, annually-rebalanced** characteristic.
What mechanisms are proposed for an overnight/intraday split — retail order flow, institutional
execution timing, the closing auction — and would any of them apply to a characteristic held for
months? Whether the documented split is **stable across eras**, since this programme's own records
show its overnight/intraday decomposition **inverting by era and by volatility**. And what this would
mean for a monthly-rebalanced book that can only transact at one price a day.

**The bar.** Either named evidence on a characteristic premium's intraday location, or **a clean
statement that nobody has decomposed a slow characteristic this way** — a confirmed absence that
would make it an original measurement rather than a replication.

**HARD SCOPE.** This is about **where a premium accrues in the trading day**. It is NOT about
overnight-session venues, extended-hours data feeds, or 24/5 trading — all permanently spent. If the
research drifts there, it is in the wrong lane.

## B4 — shares outstanding, float, and the split-history gap

**Sub-questions.** What free sources carry a **share-count time series** — XBRL cover-page tags,
the Financial Statement Data Sets, filing cover pages — and with what coverage, lag and dead-name
retention. **The split problem:** a raw share count jumps at a split, so net issuance computed from it
is contaminated; can a split be **detected from the share-count series itself** or inferred from
reported per-share figures, without a split table? **What else a share-count panel unlocks** —
float, insider-held fraction, buyback verification against reported repurchases — and which of those
the programme could use. And the honest check: **what is the measured error rate of any inference
step**, because an inferred split is a fabricated corporate action.

**The bar.** Either a named free route to a usable net-issuance series **with its error rate**, or a
finding that the split gap cannot be closed from free data — which would close `D9` rather than leave
it open.

---

## What this slate does not claim

**No lane has returned.** The figures restated are from round 1's record and the previous campaign's,
quoted rather than recomputed. **Both books are unchanged, nothing is closed and nothing is
admitted**, and **nothing in this folder is elevated out of `docs/research/`.**
