# 23 — what transfers, regardless of whether anyone ever trades a prop account

**Written 2026-09-08.** Nothing in this file is about prop firms. It is the methodology this research
turned up that applies to **any study in this programme**, collected here so it survives the topic.

**Nothing here is a result under [R15](../../RULES.md#r15).** Several items are candidate amendments
to `CLAUDE.md` or `docs/RULES.md`; **none has been made**, because a change to a standing rule is the
principal's.

---

## 1. Tools worth having

### `per-trade Sharpe = t / √N`

Any published t-statistic converts to a per-trade Sharpe. That makes a per-trade threshold applicable
to **every** claim, not only to papers that report per-trade moments — and it is how lane 19 sorted
the entire review in one column. Worked: Gao et al. → 0.068; the CSI-300 late-day drift (t = 10.1,
N ≈ 945) → 0.329.

**Inverted, it gives the sample a claim needs to establish its own sign.** An effect at per-trade
Sharpe 0.068 needs **~834 trades** at t = 2. A twenty-day evaluation gives ±$555 around an $86 mean —
which is to say it establishes nothing at all.

### The economically-dead calibration specimen

**0.781 basis points per half-hour leg, at t = 62.71.** Keep this number. It is the cleanest example
available of *statistically overwhelming and economically irrelevant*, and it is a ready-made
reference for reading any t-statistic in a short-horizon claim. Anything in that family reporting
more than ~2 bp should be reconciled against it before being believed.

### `freqtrade`'s `lookahead-analysis`, as a fourth runner assertion

It re-runs each signal on **truncated slices** and diffs indicator values and signal timing. Unlike a
hand-written audit it **does not depend on guessing where the leak is**. Its documented false-negative
mode (signal types that never trigger in the truncated window) is honestly stated by its authors.
Worth porting to sit beside the lag, sign and right-quantity audits.

---

## 2. Failures this session actually committed, and the invariant underneath each

### An identity holds only at ABSORPTION — assert the precondition, not the identity

`E[extracted] = buffer` is a martingale identity. It failed twice in this session's self-tests, at
$1,681 and again at $1,832, and **the simulator was right both times**: paths were still unresolved at
the horizon and were counted as neither outcome. Expected absorption for +3,000/−2,000 at $250/day is
`a·b/σ² = 96` days; the horizon was 252.

**The same defect then escaped into a published table** — a $100/day row reading **0.2614 for a static
floor whose true value is 0.4000** — because the precondition existed in the runner's self-test and
was never applied to the report.

> **Any conservation or closed-form identity must carry an explicit `p_unresolved < ε` precondition,
> and the precondition must be asserted everywhere the identity is used, not only where it was first
> written.**

### A break-even quantity computed with the other term held fixed describes a world that cannot exist

This session computed a *break-even pass rate* by solving `fee = P × (E[extracted] − activation)` for
`P` **while holding `E[extracted]` at its zero-edge value** — and read the resulting 1.3725 as "this
is impossible at any edge". It is not. You cannot raise a pass rate without drift, and drift raises
extraction too.

> **When solving for a break-even in one variable, check whether the other terms are functions of the
> same underlying driver. If they are, the break-even is not a threshold, it is an artefact.**

### A logged block must name the TOOL and the HEADERS, never just the host

Twice in one session a recorded "this host blocks us" turned out to be a **user-agent exclusion**.
Apex returned **HTTP 200 on 28 of 28 pages** to a browser-headered `curl`, against a ledger entry
pointing at an Internet Archive that held **zero captures** of those pages. Reddit is reachable by RSS
and by a mirror API, against an entry calling it unfetchable.

**A wrong dead-end entry is worse than no entry**, because it is trusted and it routes the next
session somewhere that cannot reach the material.

### One query surface is not a search

A lane declared saturation after four zero-yield **listings**, then found its best candidate in a
**full-text search of a subreddit it had just written off**. A `top` listing and a full-text search
return different populations.

> **Saturation must be declared per query SURFACE, not per source.**

### An audit that reads the signal function without following the call site produces a false accusation

`ict_signals.py` reads as riddled with look-ahead — centred pivot windows, `lows[-1]` anchors,
full-list selection. **The caller's slice made it sound.** This is a direct validation of the existing
rule that the lag audit must re-derive the held set in a **second implementation that never calls the
selection function**: it tests the *composition*, not the part.

---

## 3. Screening lessons

### Screen on the statistics that survive, not the ones we like

Quantopian's 888 version-locked algorithms, in-sample → out-of-sample:

| statistic | R² |
|---|---:|
| Sharpe | **0.02** |
| annual return | 0.015, and *negative* |
| IR / Calmar / alpha | < 0.005 |
| **volatility** | **0.67** |
| **max drawdown** | **0.34** |

**Drawdown is 17× more persistent than Sharpe.** The statistic every screen here is built on is the
one that does not survive; the risk statistics do. **A risk screen on a backtest is better founded
than an edge screen on the same backtest** — which inverts the usual ordering and applies to both
books.

### Year-instability, not cost, is the modal failure

And our screens carry **no per-year sign-stability gate**. This session produced a textbook instance
within hours: a premise check at **t = −5.17** whose effect was carried entirely by 2020–2021 and was
absent in 2018–2019 and 2022–2023, on a statistic that also fell to t = −2.82 on a sample-definition
change alone.

### Two more anti-screen tells, earned here

- **#13 — internal arithmetic that does not reproduce from the page's own stated inputs.** Cheapest
  check in the set. It fired on a vendor ($4.00/RT called "32% of a 2-tick scalp"; it is 16.0%) **and
  on a regulator** (a CFTC paper's ES minimum tick stated as $25 against a $12.50 contract spec, while
  its ZN figure was exact).
- **#14 — a source that has never published a negative result.** Two outfits whose headline numbers
  this review nearly rested on run **14 positive posts to 1** and **13 to 0**. Contrast the tier that
  does: one author publicly **retracted a chapter of his own book** after finding an implicit forward
  fill; a trend-following CTA published the death of short-term trend and rejected three of its own
  four explanations.

---

## 3a. Tool trust — two findings that change how sources should be read here

**`WebFetch`'s PDF summariser FABRICATED an entire sample description** for one paper in lane 21.
Not a paraphrase error — an invented sample. Every academic number in that lane was consequently
extracted locally instead.

> **Numbers taken from a PDF must be extracted from the PDF, not from a summary of it.**

And the enabling correction: **`pypdf` is installed.** Lane 14 recorded "PDFs are blocked (no
poppler)" and that entry should be lifted — lane 21 read **seven papers locally that `WebFetch` could
not**, including two CFTC documents.

**A contemporaneous regression is not a predictive one, and the sector conflates them.** The
frequently-cited *"order flow explains 65% of price moves"* is a **same-interval** regression, with
its own authors flagging the tautology. The **predictive** R² for the identical quantity is **1–5%**.
Whenever a claimed R² is large for a market quantity, check the timing convention before anything
else.

## 3b. When a family is closed, close it with the arithmetic

Lane 21's verdict is the model to copy: rather than "order flow doesn't work retail", it computed
**the required directional accuracy per cell** and found it **exceeds 1.0 in seven of twelve** — a
level at which a *perfect* forecaster still loses to the spread. The arithmetic is committed as
evidence (`data/lane21_horizon_cost.py`) so the closure can be re-opened by changing an input rather
than by re-litigating a judgement.

The same lane also separated **three constraints that get conflated** and got a different answer for
each: **speed is not binding** (25 ms against a 1-second signal is 2.5% of its life), **data is not
binding** (the signal needs only Level 1), and **cost is binding**. Anyone "fixing" that family with
a faster connection has diagnosed it wrong.

## 4. Two facts about backtesting infrastructure

- **Five open-source engines, 15 strategies, 180 stocks: divergence 0.000% at zero cost, up to 3.71%
  with costs on**, ρ = 0.93 with cost intensity — traced to **seven previously undocumented defects
  across three engines, all in transaction-cost logic.** The engines are wrong precisely where the
  papers are.
- **A widely-used engine represented daily bars midnight-to-midnight by default for years** — its own
  documentation says *"ignoring this introduces look-ahead bias"* — with one user reporting a **100%
  difference in annual returns** after the fix.
