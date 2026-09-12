# D465 RESULT — the cost line was never what killed C1: crossing takes a tenth of the edge, the bar grid was conservative, and P4 remains the only thing standing

**MEASUREMENT record. No hurdle is claimed and no candidate is admitted.** Closes the two
cost/instrument questions the acquisition was partly bought to answer. **Runner:**
`scripts/d465_es_spread_and_mae_bias.py`. **Evidence:**
`data/d465_es_spread_and_mae_bias.json`. **Source:** 126,575,117 ES front-month trades
extracted from the 37.3 GB `tbbo` set (1.44 billion records), 2025-09-11 → 2026-09-11.

**Under [R15](../RULES.md#r15) this record does not close the avenue. It reports what two
measurements settle and what they leave standing.**

---

## 0. The two things I predicted would matter, and both were wrong

I told the principal (a) the assumed cost line was understated badly enough to threaten C1,
and (b) coarse bars *understate* a trailing drawdown, so C1's published 3.980% MAE p99 was
optimistic and its P4 pass unsafe. **Neither survived measurement, and they failed in
opposite directions.**

---

## 1. The spread — four studies had assumed it, and now it is measured

| | |
|---|---:|
| share at exactly one tick | **97.384%** |
| spread, mean / p50 / p99 / p99.9 | 1.032 / 1 / 2 / 4 ticks |
| half-spread per side crossed | **0.183 bp** ($12.90/contract) |
| **round-trip crossing** | **0.366 bp** |
| RTH vs overnight half-spread | 0.181 vs 0.191 bp — **ratio 1.05** |
| worst hour (18:00 ET open) | 0.229 bp |

**Two corrections, one in each direction.**

The programme's standing line is ~0.2 bp **round-turn commission**. Crossing *alone* is
0.366 bp, so a realistic round trip is nearer **0.57 bp** — roughly **2.8×** the figure
carried by four separate studies.

And `data-purchase-proposal.md` §6 **overstated it by 2.2×**, predicting "~0.4 bp per side"
and "nearer 1.0 bp than 0.2". It treated the **full** spread as the per-side cost. Crossing
costs the **half**-spread against mid.

**The overnight penalty is 5%, not a multiple.** C1's whole edge is an overnight hold and
nobody had split the cost line by session. This is the one result here that helps C1.

### Why this does not decide anything

D464's ungated ES hold: **+5.52 bp ± 2.02 per night, n = 2,043.**

| cost line | net per hold | cost as share of gross |
|---|---:|---:|
| assumed 0.2 bp | +5.32 | 3.6% |
| crossing only, measured | +5.15 | 6.6% |
| **commission + crossing, measured** | **+4.95** | **10.3%** |

> **The entire correction is 0.37 bp against a 5.52 bp gross edge — 6.6%, on an edge sitting
> 2.73 SE from zero. I proposed re-running C1 at the corrected cost as "the cheapest next
> thing". It was nearly worthless: cost was never the binding constraint.**

## 2. The MAE grid error — one-directional, and the wrong way for my hypothesis

Same ticks throughout; only the sampling grid changes. p99 of MAE over 260 sessions:

| bar width | bars/session | optimistic | **EXACT (ticks)** | pessimistic | understates | overstates |
|---|---:|---:|---:|---:|---:|---:|
| 1 min | 1,315 | 3.907% | **3.907%** | 3.907% | +0.000 | +0.000 |
| 5 min | 264 | 3.907% | **3.907%** | 4.151% | +0.000 | +0.243 |
| **15 min** | 88 | 3.907% | **3.907%** | 4.273% | **+0.000** | **+0.365** |
| 60 min | 23 | 3.911% | **3.911%** | 4.276% | +0.000 | +0.365 |
| 240 min | 7 | 3.911% | **3.911%** | 4.276% | +0.000 | +0.365 |

**The optimistic convention is EXACT at every width. Only the pessimistic one drifts, and it
OVERSTATES — by up to 0.365 pp at the 15-minute grid D259 used.**

**Why, and it is structural rather than lucky.** The conventions differ only when the running
**peak** and the **trough** fall inside the *same* bar. Across a 22-hour hold they are hours
apart, so every width picks the same peak bar, and the trough bar's low **is** the tick
minimum. **A bar-grid MAE on a hold this long cannot understate.**

**Exact tick MAE, C1-shaped 18:00→16:10 ES hold at 1×, 260 sessions:** p50 1.851%,
p95 3.349%, p99 **3.907%**, max 5.147%.

This agrees with [D449](D449-RESULT-the-untraded-window-was-not-the-problem-the-proxy-understates-MAE-by-five-percent-and-flatters-the-ENTRY.md)'s
amendment 2 from the other direction: on the complete sample ES's breach rate is **9–14%
LOWER** than the proxy's. **The proxy was conservative on the instrument; the grid was
conservative on the path.** Neither flattered C1.

## 3. What actually stands, and it is not either of mine

| attack | record | outcome |
|---|---|---|
| longer holds | [D458](D458-RESULT-the-hold-length-curve-has-no-identifiable-optimum-and-the-observed-argmax-is-below-its-own-nulls-MEDIAN.md) | no identifiable optimum; argmax **below its nulls' median** |
| beyond 22 hours | [D459](D459-RESULT-beyond-22-hours-the-shape-constraints-lever-does-not-exist-at-the-frequency-the-rules-operate-on.md) | the shape constraint's lever does not exist at this frequency |
| conditional exits | [D460](D460-RESULT-conditional-exits-are-the-first-thing-in-the-chain-to-beat-a-matched-control-and-they-still-fail-P4.md) | first construction in the chain to beat a matched control; **best funded life 0.87 yr against 3** |
| gating on the personal arms | D464 | higher mean but **inside the rotation null**; no cell clears P4 |
| the cost line | **this record** | **not the constraint — 10% of gross** |
| the bar grid | **this record** | **not the constraint — conservative, not flattering** |

> **C1 has a real per-trade edge that survives its own corrected cost, measured on the
> instrument it would actually trade. What it does not have is an account that lives three
> years. P4 is missed fourfold by the best cell anyone has built, and every rescue —
> length, exits, gating — has now failed.**

### AMENDMENT 1, 2026-09-12 — **§3 SAID "FAILS P4" WITHOUT SAYING WHICH, AND R11 REQUIRES IT**

*Raised by the principal, who reported another agent working to a 1.5-Sharpe single-strategy
bar. **No Sharpe threshold exists anywhere in hurdle P** — P1 is a sizing rule, P2 and P6 are
venue facts, P3 is a daily-loss bound, P4 is account life, P5 is a consistency bound. The
"Sharpe 0.9" in P4's rationale is illustrative arithmetic, not a gate.*

[R11's clarification of 2026-08-29](../RULES.md#r11) is explicit, and the
[P4 ruling of 2026-09-11](../RULES.md#r11) repeats it:

> **"A closure on P1/P3/P4 closes a candidate AS A STANDALONE BOOK. It does not close it as
> a component. A verdict must now say which."**

**§3 above did not say which, and that is the error the clarification was written to
prevent.** Corrected:

| | verdict |
|---|---|
| **C1 as a standalone prop book** | **CLOSED.** P4 missed fourfold; D458–D460 and D464 exhaust length, exits and gating |
| **C1 as a COMPONENT of a layered book** | **OPEN, and this record's own numbers support it** |

**The component case, on the measurements in this record and D464's table.** The ungated ES
hold is **+5.52 bp ± 2.02 per night on 2,043 real holds — 2.73 SE from zero** — and it
**survives its own corrected cost with 90% of the gross intact**. Under
[R15](../RULES.md#r15) that is a signal: a positive gross mean per trade, and the cost line
does not erase it.

**And C1 is not the only one.**
[D460](D460-RESULT-conditional-exits-are-the-first-thing-in-the-chain-to-beat-a-matched-control-and-they-still-fail-P4.md)
found **five of ten stop cells clearing their time-matched control's p95, three at
`p` = 0.000 on 60 draws — the first constructions in this chain to beat a control** — and
reported them as failures because none reached three years *alone*. On R11's own arithmetic,
`k` uncorrelated arms each sized so the **book** meets the floor run at `1/sqrt(k)` of solo
size, so a component is never required to carry the floor by itself.

**What is genuinely closed by the control, not by P4:** D464's S1/S2 gating, whose higher
mean sits **inside the rotation null**. That fails R15's criterion and is dead as a component
too. The distinction matters: *failing P4 alone* and *failing a control* are not the same
verdict, and only the second closes a component.

**What is still missing before any of this is a book, and it is not small.** The layering
arithmetic needs arms that are **uncorrelated with each other**, and no correlation between
C1 and D460's stop cells has been computed — they are variants of the same overnight hold on
the same instrument, so the prior should be that they are *highly* correlated and contribute
far less than `sqrt(k)`. `data/futures_breadth_projection.json` measures **instrument**
breadth, which is a different quantity and must not be substituted for it.

**Nothing here reopens C1 as a standalone book, and nothing here admits anything.** It
records that the standalone verdict was stated as if it were the only verdict.

## 4. What this record does NOT claim

- **It does not close C1 or the avenue.** [R15](../RULES.md#r15): that is the principal's.
- **It does not compute a return, a Sharpe or a book.** Two cost/instrument measurements.
- **The sample is one year** of `tbbo` against D259's full span, at 1× with no vol
  targeting. The spread figures are 2025-09 → 2026-09 only; a 2020-style dislocation is not
  in them, and the p99.9 of 4 ticks is the widest thing this window contains.
- **Nothing is elevated** into `FINDINGS.md`, `RULES.md` or either book.

## 5. Two bugs this runner's own checks caught

**The mean spread read 875 ticks beside a p99 of 2.** `(bid > 0) & (ask > 0) & (ask >= bid)`
admits DBN's INT64 sentinel, which scales to 9.2e9 index points. **Three records out of
126,575,117 moved the mean by three orders of magnitude.** 338 records (0.00027%) are now
excluded and the count is reported. *A sane median beside an insane mean is the tell.*

**The first MAE run had all three conventions agreeing at 1 minute**, and the self-test
passed while every arm returned the same number — a bracket where every arm agrees is not a
passing test, it is an absent one. The cause was the optimistic peak being clamped to the
first bar's high, collapsing it onto the pessimistic bound. Fixed; the test now proves each
bound errs in **its own** direction on hand-checkable paths. And the tie at 1 minute was
still the wrong answer to quote, because **D259 measured on 15-minute bars** — the grid sweep
is what turned a suspicious tie into a one-directional bound.
