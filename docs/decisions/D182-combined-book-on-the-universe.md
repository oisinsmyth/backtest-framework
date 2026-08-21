# D182 — The combined long+short book on the D140 universe

**Status:** Committed (H1 and H2 both confirmed)
**Date:** 2026-08-21
**Category:** Analytics
**Source:** D172 combined the two books on two instruments; D180 established what two-instrument findings are worth here

> Written and committed **before** the study runs, as D173, D178 and D180 were. The
> predictions below are falsifiable and dated by git. A result section will be appended and
> nothing above it edited.

## The question

D172 combined the long and short books on BTC/ETH and found the combination has a **lower
Sharpe** than the long book alone but a **smaller drawdown**. That is a two-instrument
finding, and D180 has just shown what those are worth in this project: E1 cleared its bar
five times on BTC/ETH and failed on sixty-two coins, because those two sit at the 97th and
85th percentile of the variable that decided the outcome.

**Nobody has ever run a combined book across the cross-section.** That is the gap. Testing
a rule against an unmeasured baseline is the mistake D179 made — it landed as a headline
before the universe test that undercut it, and before the weighting fix that halved it.

## What is built

`scripts/run_combined_universe.py`. Two runs, both fixed before meeting this universe (D141):

- **Long arm:** `breakout_universe.baseline_variant()`, reused directly rather than
  re-derived — it is the same configuration the published D140/D141 universe study runs.
- **Short arm:** the published short baseline — 20/5, SMA200 regime gate, inverse-vol
  sizing, `channel_stop`, borrow at 10%/yr.

**Per-symbol, not portfolio.** Each coin's own long and short series are combined into one
book, which is the direct analogue of D179 and reuses `combine_books` unchanged. This is
**not** a long/short portfolio across 62 coins — there is no cross-sectional capital
allocation in this framework, and building one is a separate piece of work with its own
design decisions. The two legs remain entirely separate backtests blended after the fact.

Weights are the expanding-window inverse-vol from D181. Running this before that fix would
have inherited the whole-sample look-ahead sixty-two times over.

## The predictions

Scored at `taker_40bp`, per cohort (SURVIVED / COLLAPSED / DELISTED).

**H1 — the combination scores a LOWER Sharpe than the long book alone on >50% of coins,
and a SMALLER max drawdown on >50%.** Predicted **TRUE**.

This is D172's BTC/ETH finding asserted on the cross-section. The mechanism is arithmetic
rather than empirical: you cannot diversify with a negative-expectancy asset, you can only
spread the same losses more smoothly. The short book loses money on 55 of 62 coins (D180),
so adding it must cost return; what it buys is a smoother path, because its losses arrive
at different times than the long book's.

Against this: D181 has just changed the weighting, and the corrected BTC combined Sharpe
(0.462) is **above** the long leg's… no — it is far below the long leg's 1.223. On both
symbols the combination already scores below the long book alone, which is what H1 asserts.
The open question is whether it holds where the long book is weak, and there are 41
collapsed coins where it might not.

**H2 — the long/short correlation sits within ±0.2 on more than 75% of coins, and this is
NOT evidence for the ensemble.** Predicted **TRUE**, and the second clause is the point.

`BREAKDOWN_SHORT_STRATEGY.md` sets a ~0.2 correlation target and D172 reported the books
clearing it. But the short book is flat on ~85% of bars, so the two legs rarely carry
simultaneous exposure at all. **Near-zero correlation here is mechanical — an artifact of
non-overlapping exposure — not evidence of complementary payoffs.** Two books can be
perfectly uncorrelated and still combine into something worse than the better one, which is
exactly what H1 predicts. If H2's first clause holds and H1 also holds, the correlation
target is measuring something real and worthless.

**What would falsify each:** H1, a majority of coins where the combination scores a higher
Sharpe, or a majority where it draws down more. H2, correlation outside ±0.2 on more than a
quarter of coins.

**Confidence:** high on H1, which is close to an arithmetic claim; high on H2's first
clause; the second clause of H2 is an interpretation the data can support but not settle.

My last three mechanism-first predictions in this project were falsified (D173 H1, D178 H2,
D180 all three). H1 differs in kind from those — it predicts a *cost*, not a benefit, and
every one of the falsified predictions was a prediction that something would work.

## What this cannot establish

**Nothing here makes either book worth running**, whichever way H1 lands. The long book's
DSR sits near 1.0 only because its plateau is flat; the short book's is 0.04–0.538, and
D181 has just shown its ETH Sharpe was carried entirely by 2018. Combining two books does
not create an edge neither has.

**And the combination is measured with a known-flawed weighting.** Inverse-vol reads a book
that is flat 85% of the time as low-risk rather than as absent, so the short leg draws the
majority of the risk budget *because* it barely trades (mean long weight 0.389 on BTC).
That is recorded in D181 and reported on the face of this study's output; it is not fixed
here, and every combined figure inherits it.

## Multiplicity

**None added.** Both baselines already exist and are already in their pools. Own registry
`data/combined_universe_registry.sqlite` under `combined-universe-*`, exactly as D174 and
D180 did. No DSR in either published report moves.

---

# RESULT — appended 2026-08-21, after the run. Nothing above this line was edited.

**Status: H1 CONFIRMED on both clauses. H2 CONFIRMED, and more strongly than predicted.**

62 symbols, none skipped, 283s. Weighting fell back to 50/50 on **0.8%** of bars — against
75% for the 63-bar trailing window D181 rejected, which is the clearest evidence the
expanding scheme was the right call.

## H1 — the combination costs Sharpe and buys drawdown: CONFIRMED

| Cohort | Symbols | Combined beats long (Sharpe) | Mean Δ Sharpe | Median Δ | Combined draws down less | Mean Δ max DD |
|---|---|---|---|---|---|---|
| **ALL** | 62 | **8%** | **−0.382** | −0.422 | **68%** | **−4.7 pp** |
| survived | 19 | 0% | −0.492 | −0.547 | 89% | −9.3 pp |
| collapsed | 41 | 12% | −0.302 | −0.335 | 59% | −3.7 pp |
| delisted | 2 | 0% | −0.992 | −0.992 | 50% | +17.2 pp |

Both clauses hold, and the Sharpe side holds far harder than predicted: the combination is
worse on **57 of 62 coins**. On the 19 survivors it is worse on every single one.

## The absolute P&L, which is the real headline

| Arm | Median total return | Mean, ex blow-ups | Mean Sharpe | Mean max DD | Profitable |
|---|---|---|---|---|---|
| long | **+123.2%** | +257.3% | +0.392 | 48.1% | **51 / 62** |
| short | −59.4% | −47.7% | −0.478 | 67.7% | 5 / 62 |
| **combined** | **+5.7%** | +23.7% | **+0.010** | 43.4% | **34 / 62** |

**Combining destroys roughly 118 percentage points of median return and 17 profitable
symbols, to buy 4.7 points of drawdown.** The combined book's mean Sharpe is +0.010 — not
low, *zero*.

The single clearest illustration: **BTC's long book returns +4,672% over the scored span;
combined with the short book it returns +197%.**

## H2 — the correlation target is met perfectly and it does not matter: CONFIRMED

| p05 | p25 | median | p75 | p95 | within ±0.2 | max \|corr\| |
|---|---|---|---|---|---|---|
| −0.0011 | −0.0000 | +0.0004 | +0.0009 | +0.0016 | **62 / 62** | **0.0023** |

The prediction was ">75% within ±0.2". The actual answer is **100%, with the largest
absolute correlation anywhere in the cross-section being 0.0023** — three orders of
magnitude inside the brief's ~0.2 target.

**And the second clause is what the pair of results establishes.** The two books are as
close to perfectly uncorrelated as a measurement gets, and combining them still costs 0.38
Sharpe on 92% of coins. That is not a failure of diversification; it is diversification
working exactly as advertised on an asset that has nothing to contribute.

The near-zero correlation is **mechanical**. The short book is regime-gated and flat on ~85%
of bars, so the two legs almost never carry simultaneous exposure. `BREAKDOWN_SHORT_STRATEGY.md`'s
~0.2 correlation target is therefore measuring non-overlapping exposure, not complementary
payoffs — **a real quantity, and a worthless one**. It should never again be quoted as
support for the ensemble.

## The drawdown benefit is real, scales correctly, and inverts in the tail

This is the one thing that survives, and it needs stating precisely because it is the
combined book's only defence.

| Long-book max DD | Symbols | Mean Δ max DD | Improved |
|---|---|---|---|
| Q1: 21–39% | 15 | **+1.0 pp** | 8/15 |
| Q2: 40–48% | 16 | −5.1 pp | 11/16 |
| Q3: 48–54% | 15 | −6.3 pp | 12/15 |
| Q4: 54–80% | 16 | **−8.3 pp** | 11/16 |

Monotone: the worse the long book's drawdown, the more combining helps. That is the right
shape for a hedge and it is genuine.

**But it fails exactly where a hedge has to work.** Drawdown got *worse* on 20 of 62 coins,
and the five worst are led by the two that destroyed the short account:

| Symbol | Status | Long DD → Combined DD | | Long weight |
|---|---|---|---|---|
| `LUNA1-USD` | delisted | 21.2% → **74.5%** | **+53.3 pp** | 0.188 |
| `LUNC-USD` | collapsed | 52.1% → 70.5% | +18.4 pp | 0.406 |
| `EOS-USD` | collapsed | 44.4% → 58.2% | +13.9 pp | 0.549 |
| `XMR-USD` | survived | 33.7% → 47.4% | +13.6 pp | 0.511 |
| `LSK-USD` | collapsed | 47.0% → 59.6% | +12.7 pp | 0.562 |

On LUNA1 the long book took a 21% drawdown and returned +1,298%; the combination took a
**75%** drawdown and returned −5%. The hedge smooths ordinary drawdowns and amplifies the
one that would have ended the account — because a short's loss has no ceiling and this
engine has no margin call (D175).

## The D181 weighting flaw, now measured rather than asserted

D181 recorded that inverse-vol reads a flat book as low-risk when what it actually is, is
absent, and that this hands the short leg the majority of the risk budget. The
cross-section prices that:

- Median long-leg weight **0.456**, range 0.188–0.778. The long leg holds a **minority** of
  the risk budget on **47 of 62** coins.
- **corr(long-leg weight, Δ Sharpe vs long) = +0.604.** The more of the book the long leg
  was given, the better the combination did. The weighting's misallocation is the second
  strongest driver of the outcome after the short book's expectancy itself.
- **corr(long-leg weight, short-leg Sharpe) = −0.043.** The weight is entirely unrelated to
  how good the short leg actually is on that coin.

So the allocator sizes on **how often a book trades** and not on **how good it is**, and on
LUNA1 it put 81% of the risk budget on the leg that was about to lose more than the account.
That is the flaw described in D181, doing measurable damage.

## What this settles

**The combined book is not a strategy.** Median +5.7% and a mean Sharpe of +0.010 against a
long book at +123.2% and +0.392. There is no reading of these numbers on which combining is
worth doing, and the drawdown consolation inverts in the tail where it would have to pay.

**D172's BTC/ETH finding replicates, and replicating did not rescue it.** The
lower-Sharpe-smaller-drawdown shape holds across 62 coins. It was never evidence the
combination was good; it was a description of what adding a losing book does, and now it is
that description with a cross-section behind it.

**The correlation target is retired as evidence.** Met perfectly, on every coin, while the
combination destroyed 92% of them.

**No multiplicity was added**, as pre-registered. Both baselines were already in their
pools; the long arm is `breakout_universe.baseline_variant()` itself. No DSR in either
published report moves.

## What it does not settle

**This is not a portfolio result.** Per-symbol combination asks "does pairing this coin's
two books help?" — not "does a long/short book across 62 coins work?". A portfolio could
net exposure across coins, size legs against each other cross-sectionally, and would face
an entirely different set of questions. Nothing here rules that out; nothing here supports
it either.

**And the short book is what it is.** Every number above is downstream of a leg that loses
money on 57 of 62 coins and whose ETH Sharpe was carried entirely by 2018 (D181). The
finding is not that combining is a bad technique. It is that this short book is not worth
combining with anything.

---

*Note on the text above the line: the H1 paragraph contains a visible mid-sentence
self-correction ("is **above** the long leg's… no — it is far below"). It was committed
that way in b75e2e3 and is left as written, because the value of "nothing above the RESULT
line is edited" comes from its being unconditional. The claim it lands on — that the
combination already scored below the long leg on both symbols — is the one H1 was scored
against.*
