# DRAFT — the in-play lever on the prop book: what it can and cannot be, and how to test it

**2026-09-13. A design, not a result. Nothing here is pre-registered** ([R8](../docs/RULES.md#r8)),
and the premise numbers below come from a scratch measurement that any runner must reproduce as its
first assertion before they may be quoted in a record.

## 0. The translation problem

The video's claim is about choosing among 5,000 tickers. The prop account trades **eight gated
futures roots**, so "stock selection" has no direct analogue. What survives translation is the
underlying arithmetic: **trade where the move is large relative to what the trade costs.** On the
prop book cost is **fixed in dollars** ($3 a micro round trip, $6 on ZN/ZB), so unlike the equity
case the in-play state does not drag its own cost up with it. That makes the prop book the *better*
home for this idea than the equity book where the video aims it.

Two applications are available, and they are different studies:

- **(A) Day selection.** Trade only the sessions whose move is expected to be large, on a root
  already chosen. This is the video's idea at the session clock.
- **(B) Root selection.** Each morning, trade whichever of the eight roots is most in play, subject
  to the account's risk budget. **Every prop study in this repo has fixed the root**; this axis has
  never been touched.

## 1. Premise measurement (scratch, 2016-01-04 → 2023-12-29, eight roots)

The in-play score is causal and known before 09:30: the **geometric mean of the overnight leg's
range and volume, each against its own trailing 20-session median**. Sessions are split into deciles
of that score; the table reads decile 1 as the quietest overnight and decile 10 as the most in play.

**The conditioner works as a conditioner.** It predicts the size of the day move it precedes at
ρ = 0.09 to 0.20 (ES 0.18, YM 0.20, NQ 0.11, CL 0.09), and it is persistent at ρ = 0.19 to 0.41
with its own next value — ordinary volatility clustering, which is what makes it usable at all.

**Decile 10 against decile 1, per root:**

| root | E\|day move\| | σ | fee as a share of E\|M\| | break-even accuracy | days beyond −$1,000 |
|---|---|---|---|---|---|
| ES | ×1.86 | ×1.60 | 3.3% → **1.8%** | 51.6% → 50.9% | 0.0% → 0.0% |
| NQ | ×1.66 | ×1.50 | 2.1% → **1.2%** | 51.0% → 50.6% | 0.5% → 1.0% |
| YM | ×1.94 | ×1.68 | 4.4% → **2.3%** | 52.2% → 51.1% | 0.0% → 0.0% |
| ZN | ×1.46 | ×1.57 | 3.1% → 2.1% | 51.5% → 51.1% | 1.0% → 4.1% |
| ZB | ×1.46 | ×1.64 | 1.3% → 0.9% | 50.6% → 50.4% | 9.7% → 19.4% |
| GC | ×1.15 | ×1.20 | 3.8% → 3.3% | 51.9% → 51.6% | 0.0% → 0.0% |
| CL | ×1.27 | ×1.25 | 3.8% → 3.0% | 51.9% → 51.5% | 0.0% → 0.0% |
| 6E | ×1.35 | ×1.35 | 9.7% → **7.1%** | 54.8% → 53.6% | 0.0% → 0.0% |

## 2. What the lever is actually worth, in Sharpe

For a directional day trade, annualised Sharpe ≈ `√252 / c · [(2p − 1) − fee/E|M|]`, where `p` is
directional accuracy and `c = σ / E|M|` (measured here at 1.3–1.4). **Selection moves only the
second term**, and by a known amount:

| root | fee share saved | Sharpe added, at unchanged accuracy |
|---|---:|---:|
| 6E | 2.6 pts | **+0.29** |
| YM | 2.1 pts | **+0.24** |
| ES | 1.5 pts | **+0.17** |
| ZN | 1.0 pts | +0.11 |
| NQ | 0.9 pts | **+0.10** |
| CL | 0.8 pts | +0.09 |
| GC | 0.5 pts | +0.06 |
| ZB | 0.4 pts | +0.05 |

**So the honest size of the idea is +0.05 to +0.30 of Sharpe, and it creates no edge.** It dilutes a
fixed fee across a bigger move. Against FINDINGS §69's arithmetic — the best real signal here (the
log MACD) reaches ≈ 50.7% accuracy against a 51.2% break-even and a 53.6% component bar — the lever
**roughly closes the break-even gap and gets nowhere near the component bar.** Any claim larger than
that is not supported by this measurement.

## 3. The part that matters more, and is not about cost at all

**Both prop death mechanisms are counted in exposure-days, and a filter that removes 90% of the days
removes 90% of the chances to die.** P3 is a daily loss limit and the trailing floor is a path
constraint; each is sampled once per session traded.

On NQ, 2016–2023, the conditional probability of a day beyond −$1,000 roughly doubles in decile 10,
0.5% → 1.0%. But trading decile 10 alone is ~25 sessions a year rather than 252:

| | sessions a year | conditional breach rate | expected breaches a year |
|---|---:|---:|---:|
| every session, one MNQ | 252 | 0.35% | **0.88** |
| decile 10 only, one MNQ | 25 | 1.0% | **0.25** |

**This is the application that speaks to what actually killed the book.** D503 found the binding
constraint is no longer the edge but the vehicle — one micro is too large for a $50k account's
$2,000 floor at 2026 index levels, with **P3a at 3.87 breaches a year against a bar of 1.0**.
Selectivity is the only lever in the repo that attacks that number *without* needing a smaller
contract: it cuts the count of exposure-days directly, while improving the fee ratio on the ones
kept. The hedged micro pair (σ $128 against $282, D504 §3) attacks the same constraint from the
other side, and the two compose.

**The price-level caveat is not optional.** Every figure in §1 and §3 is 2016–2023. D503 measured
NQ's daily σ at **$340** forward against **$180** in sample on an unchanged strategy, because MNQ
pays $2 a point and the index level doubled. **A decile-10 NQ session at 2026 prices is roughly
$500 of σ**, which breaks C-d ($500) on its own, so the in-play filter as applied to NQ today makes
the vehicle problem worse, not better, and the arithmetic must be recomputed per year before any of
this is quoted.

## 4. The frontier this produces, which is the real deliverable

Cross §1's two axes and every (root, decile) cell is a point with a **cost ratio** and a **σ**. The
account draws two horizontal lines: C-d at σ ≤ $500, and P3 at a worst day ≤ $1,000. At decile 10:

| cell | fee share | σ | fits C-d? |
|---|---:|---:|---|
| ZB decile 10 | **0.9%** | $1,017 | **no** |
| NQ decile 10 | **1.2%** | $340 (≈ $500 today) | marginal today |
| ES decile 10 | 1.8% | $232 | yes |
| ZN decile 10 | 2.1% | $404 | yes |
| YM decile 10 | 2.3% | $184 | **yes** |
| CL / GC / 6E decile 10 | 3.0% / 3.3% / 7.1% | $139 / $136 / $58 | yes |

**The cheapest cells are the ones the floor cannot carry, and the cells the floor likes are the
expensive ones.** That is [[fee-and-barrier-are-one-constraint]] drawn as a frontier rather than
stated as a rule, and it says the interesting cell is **YM decile 10**: the second-best fee ratio
improvement of any root (4.4% → 2.3%), σ of $184 that fits the floor with room, and zero days beyond
−$1,000 in eight years. YM has never been the subject of a prop study here; it has only ever been a
row in a family.

## 5. How to test it

**Stage 1 — does an existing signal's accuracy survive the filter?** The lever above assumes `p` is
unchanged on in-play days. That assumption is the whole study, and it is testable without inventing
anything.

- **Object.** Re-score the day-session constructions the repo already owns — the log MACD (D484) and
  the unconditional day drift — by in-play decile, per root, at one micro and the cost that size
  pays.
- **Primary statistic (one, per R14).** The Sharpe-relevant quantity `(2p − 1) − fee/E|M|`, top
  decile against the rest, on the declared root. Not the raw return: the point is whether accuracy
  holds while the cost ratio falls.
- **The control that decides it.** A **realised-volatility-matched** control: days with the same
  realised day-session range but a *low* causal in-play score. This separates "the day was big" from
  "we knew in advance it would be big", and without it the test is circular — the filter selects
  volatility, so any volatility-loving signal flatters it. Matched-count is not enough (D279), and a
  redrawn random subset is not a control for a persistent selector (D291).
- **Two further controls.** The previous day's overnight score in place of today's (wrong window),
  and the realised *same-day* range as the conditioner (an upper bound that is not tradeable).
- **Nulls.** Exact enumerated rotation of the in-play score against the outcome per root — a single
  market-level series, so the group is finite and the p95's error is exactly zero — plus a family
  maximum across the 8 roots × 2 signals under common offsets.
- **The bar.** PROCEED only if the improvement clears the family bar, the resulting cell clears C-a
  at one micro, **and** P3a is recomputed at 2026 price levels and passes. D503's lesson is that a
  2016–2023 C-d or P3 figure is a price-level artefact; a cell that passes on old prices and fails
  on current ones is a fail.

**Stage 2, only if stage 1 survives — root selection (application B).** Each morning rank the eight
roots by the in-play score and trade the top-ranked root that fits the σ budget, against the control
of a fixed root and of a random eligible root. This is the genuinely unexplored axis and it is where
the frontier in §4 says the value is, but it is worthless until stage 1 shows accuracy survives.

**The holdout position, which constrains the design.** The 2024-01-02 → 2026-09-09 futures slice is
**SPENT for the NQ and ES day session** (D503). It is unread for **YM, ZN, ZB, GC, CL, 6E**. So the
study runs 2016–2023 on all eight roots, treats any NQ or ES result as in-sample-only evidence that
can never be confirmed here, and **declares its forward slice on the six unspent roots** — which is
a second reason to make YM the declared primary rather than NQ.

## 6. What would make this not worth running

State it now rather than after. The lever is +0.05 to +0.30 of Sharpe on a book whose best component
reached +0.72 in sample and whose assembled version failed hurdle P on the barrier, not on return.
**If stage 1 shows accuracy holds exactly, the prop book still has no admitted arm** — it has a
cheaper version of a signal that was already not enough. The case for running it anyway is §3: the
exposure-day arithmetic is the only untested lever that attacks the constraint D503 identified as
binding, and it is cheap to measure on committed fixtures.
