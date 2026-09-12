# Scan-100926 · Round 1 — slate

**Committed 2026-09-10 before the agents were dispatched.** Contract, inherited exclusions and the
rules every agent carries: [`00-SCHEMA.md`](00-SCHEMA.md).

**Four lanes, each broad.** Every one attacks a **constraint** the previous campaign identified rather
than hunting a territory, because **eleven signal territories died across six rounds and the evidence
now says the constraint was never the territory.**

| lane | file | the constraint it attacks |
|---|---|---|
| `A1` | `R1-01-free-fundamentals.md` | **the DATA constraint** — 7 of the 10 strongest survivors need fundamentals we do not have |
| `A2` | `R1-02-persistent-characteristics.md` | **the STRATEGY-TYPE constraint** — survivors are slow characteristics; we have only built fast dated events |
| `A3` | `R1-03-the-long-only-problem.md` | **the LONG-ONLY constraint** — survivors' return sits in the short leg, and our shorting is constrained |
| `A4` | `R1-04-filing-text-at-scale.md` | **the MEASUREMENT-LAYER constraint** — the events that mattered are prose, not item codes |

---

## Why these four, and the reasoning is the point

**The previous campaign's last round found that the binding constraint is not what the programme
thought it was** ([`../the-reversal-round.md`](../the-reversal-round.md)):

- **Cost is not what binds the survivors.** They are annually rebalanced at 1.2–7.2% one-sided
  monthly turnover — **~1.4 bp/month** at 33.8 bp/side. **And 33.8 bp/side is the cost-honest
  literature's own measured number, not a pessimistic outlier.**
- **The gross edge is gone**: median **7 bp/month, t = 0.45** post-2005 in the top 90% of market cap,
  and **~85% of published alpha required both pre-2006 data and microcaps.**
- **What remains is in the short leg**: long-minus-market Var(t) = **0.98, below the null**.
- **Zero of the ten strongest survivors are computable from permitted free data** — seven need
  fundamentals, two of the three price-only ones are on the exclusion list, one needs options.

**Four constraints, four lanes.** `A1` asks whether the fundamentals constraint is real or merely
unexamined. `A2` asks what the slow-characteristic family actually is, since the programme has never
built one. `A3` asks whether any survivor is long-only, because that is the shape this account can
trade. `A4` asks what can be extracted from filing **text** at scale, because round 5 measured a
text-level phenomenon that round 6's item-code census **could not speak to**.

**This is a deliberate pivot and it may be the wrong one.** The alternative is a twelfth territory
hunt. **If the principal prefers that, one lane gets swapped.**

---

## A1 — free, point-in-time, dead-inclusive FUNDAMENTALS

**The constraint.** Seven of the ten strongest post-2005 survivors need Compustat-style fundamentals.
The programme has none. **If that gap is closable from free primary sources, it changes what every
future round can even consider.**

**Sub-questions.** What the SEC's own XBRL products actually provide — company facts, the Financial
Statement Data Sets, the frames API — and their coverage, earliest date, and lag from period end to
availability. **Whether they are POINT-IN-TIME or restated**, which is the question that decides
usefulness: a restated fundamental is a look-ahead. How amendments and restatements are represented.
**Whether dead issuers are retained** — the programme is 35.7% dead, and free identifier maps have
been measured survivors-only six times. Tag taxonomy stability across 2010–2026 and the Inline XBRL
phase-ins. What is **not** in XBRL that Compustat has (standardisation, industry normalisation,
point-in-time snapshots). And which of the named survivor signals become computable if this works.

**The bar.** A named free source with its coverage, its lag, its point-in-time status **stated and
tested**, and a list of which survivor signals it does and does not unlock. **An explicit negative is
a result.**

## A2 — the PERSISTENT-CHARACTERISTIC family

**The constraint.** The survivors share a shape the programme has never built: **a persistent
characteristic held for months, not a dated event held for bars.** Every book here has been fast and
event-driven.

**Sub-questions.** What the surviving characteristic families are, named specifically, with their
post-2005 cost-honest evidence and what data each needs. **What holding period and rebalance frequency
the evidence supports**, and what happens to each as the hold shortens toward this programme's
horizon. The **capacity and breadth** each needs — how many names per leg, and whether ~10 effective
independent instruments is enough. **Whether any of them is a pure price/volume characteristic**, since
that is the only input class available free. And the honest question: **is the monthly-rebalanced
slow-characteristic book a different activity from what this programme is set up to do**, in data,
machinery and reporting?

**The bar.** A ranked shortlist with **data requirement, holding period, breadth need and
cost-honest post-2005 evidence** for each — or a finding that the family is closed to free
price-and-volume inputs.

## A3 — the LONG-ONLY problem

**The constraint.** Long-minus-market Var(t) = 0.98, below the null, and 162 anomalies pay
**+0.14%/month before borrow fees and −0.01% after.** **This programme's shorting is constrained and
borrow is excluded ground.** So: is there anything here for a long-only account at all?

**Sub-questions.** Is there documented post-2005 cost-honest evidence for any **long-only** anomaly
return, as against long-short? **Why is the return in the short leg** — short-sale constraints, limits
to arbitrage, overpricing asymmetry — and is the explanation testable without shorting? What does the
literature say about **long-only implementations** of known factors, including the dilution from
dropping the short leg. **Is the short-leg concentration a fact about the whole post-2005 sample or
about specific cohorts** (microcaps, hard-to-borrow, distressed)? And what is documented about
**timing or conditioning a long-only book** rather than selecting within it.

**The bar.** Either a named long-only survivor with cost-honest post-2005 evidence, or **an explicit,
well-sourced finding that long-only is where the returns are not** — which would be one of the most
consequential findings this programme could hold.

## A4 — FILING TEXT AT SCALE

**The constraint.** Round 5 measured **62.2% of dividend initiations and 36–68% of split
announcements** arriving inside an earnings release. Round 6 then censused **all 1,185,352 8-K
submissions** and found it **could not speak to that finding at all**, because those announcements
**have no item code** — they are prose inside 8.01, 7.01 and 2.02 bodies. **The measurement layer is
the constraint.**

**Sub-questions.** What is free and bulk-retrievable for filing **text** — EDGAR full-text search and
its documented limits and coverage start, the bulk archives, the dissemination files. **What has been
published using filing text**, and which of those results survive post-2010 cost-honest treatment.
The **extraction problem**: what accuracy is documented for rule-based versus model-based extraction of
dated corporate facts from filing prose, and what the published error rates are. **The look-ahead
problem in text**: amendments, restatements, and the fact that a filing's *content* date and its
*availability* date differ. And the cheap question that decides feasibility: **roughly what volume of
text, in bytes and requests, would a 2010–2026 pass over one item code cost?**

**The bar.** A stated route with its volume, its licensing position, and a documented error rate for
the extraction step — **or a finding that text-level work is out of reach at this programme's scale**,
which would close round 5's open question rather than leave it hanging.

---

## What this slate does not claim

**No lane has returned.** No number here is measured; the figures restated are from the previous
campaign's records and are quoted, not recomputed. **Both books are unchanged, nothing is closed and
nothing is admitted**, and **nothing in this folder is elevated out of `docs/research/`.**
