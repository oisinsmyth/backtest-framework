# D662 STAGE 0 RESULT — NOT SUPPORTED: neither the gap nor the stop run is multiplied by dealer short gamma at the opening-range break, and both nulls are powered against the mechanism's own best case. Post hoc and unpromotable: breaks carry about 2.7 bp further on short-gamma days, too small to trade or confirm

*2026-09-28.*
- *One run of `scripts/stage0_d662_gamma_product.py` (`7712e61`) under D662's design (`c9a40a5`), in 0.87 min.*
- *ES, the usable sessions 2016-01-04 → 2025-02-28 through the sealed loader: 2,227 sessions, 2,081 morning breaks,
  2,132 midday breaks. Nothing from 2025-03-01 was read.*
- *Output: `data/stage0_d662_gamma_product.json`.*
- *The selftest's six audits fired on broken inputs. In the run:*
  - *the break equalled `b3_trade`'s on every session;*
  - *the 60-minute exit equalled B3's time exit wherever the stop did not fire;*
  - *every OLS equalled statsmodels';*
  - *the batched null equalled per-offset lstsq on a tie-heavy probe.*

## The pre-registered tests

| | gap × short gamma (primary) | stop run × short gamma (secondary) |
|---|---|---|
| **b₃, interaction** (bp of follow-through per unit g × s) | **−0.79** (HAC t −1.06) | **−0.70** (t −0.75) |
| Holm p (one-sided, b₃ > 0) | 1.00 | 1.00 |
| purged rotation of g (2,206 offsets): rank; null p50, p95 | **0.10**; +0.002, +0.94 | 0.19; +0.008, +1.24 |
| midday placebo b₃ (t) | +0.36 (0.71) | +0.66 (1.13) |
| slope on s: short-gamma vs long-gamma sessions | −0.27 vs +1.44 (diff t −0.55) | +1.50 vs +2.61 (diff t −0.26) |
| **the model's own claim**, β on the predicted push (90% CI) | **0.08 (−0.11, 0.26)** | 0.14 (−0.16, 0.43) |
| MDE of b₃ (80%) against the paper's best-case b₃ | 2.09 against **+5.40** | 2.62 against **+5.00** |
| **verdict** | **NOT SUPPORTED** | **NOT SUPPORTED** |

- **Both nulls are powered.** The paper's best case implies b₃ ≈ +5, which is 2–2.6× the MDE. The estimates are
  negative, and β against the model's own push sits wholly below 0.5.
- **The square-root law's lagged-hedging push is not realised.** This agrees with A4's first-hour null (D645 H-O6,
  t 0.00).
- **The negative b₃ is 2020's:** 2020 alone is −6.97, and without it the leave-one-year-out b₃ is +0.03. Without
  February–April 2020 it is −0.24. So what b₃ there is sits in the tails, as prediction 6 said.

**Predictions (§9): all six held.**
1. Gap not supported.
2. Stop run not supported.
3. The gap's own claim is a powered null.
4. The short and long slopes do not differ.
5. The placebo is inside noise.
6. The tail moves b₃ by more than half.

**F** (the 60-minute follow-through, in bp, 2,081 breaks):

| mean | median | sd | ex-top 1% | ex-bottom 1% | trimmed | kurtosis |
|---:|---:|---:|---:|---:|---:|---:|
| +0.66 | +0.94 | 33.2 | −0.65 | +1.96 | +0.65 | 7.3 |

## Post hoc, unpromotable: the break itself, times gamma

§5.2's control "F on g alone" came out at **b 0.48 bp per unit g, t 2.30**. This is the **break × gamma** form: the
break is the shock, and the dealers' short gamma is the multiplier. It is the form the principal's super-additivity
question pointed at, and the one I had dismissed on paper (a ~1.1 multiplier on ~0 follow-through). It was examined
after the run by `scripts/diag_d662_gamma_alone.py` (`data/diag_d662_gamma_alone.json`):

| | morning (the break) | midday (the placebo) |
|---|---|---|
| slope (HAC t) | **+0.48 (2.30)** | +0.13 (0.69) |
| purged rotation rank; null p50, p95 | **0.98**; −0.01, +0.38 | 0.73 |
| without February–April 2020 | +0.51 (t 2.59) | +0.10 |
| years with a positive slope | 8 of 10 (2020 and the two months of 2025 negative) | 6 of 10 |
| F by g quintile, long → short gamma | −1.41, −1.18, +0.81, +2.43, **+2.67** bp | no order |
| F on short- vs long-gamma sessions | **+2.18 vs −0.51** bp | +0.72 vs −0.74 |

**Read it with four cautions:**
1. **It was picked after seeing ten reported statistics.** The rotation rank answers chance for this one statistic,
   not the choice of it.
2. **The year count has no null of its own** (memory: a year count of slopes needs its own null).
3. **It is small.** Short-gamma breaks carry about 2.7 bp further over an hour. The top quintile's +2.67 bp gross is
   about one micro round trip (2.2 bp).
4. **It cannot be confirmed.** The vault holds about 360 ES breaks, so the slope's SE there would be about 0.5,
   against an effect of 0.48: power near 15%.

It is the first time the gamma mechanism has shown the sign the literature describes (continuation when dealers are
short gamma) in this programme. That makes it a direction worth remembering, not a trade.

## Routing (§7)

**Neither shock is SUPPORTED.**
- The shock × gamma product is closed at the opening range on the ES carried book.
- It is the gamma mechanism's fourth null here: D581 at the close; H-O6 and S-H at the open; now D662.
- The opening line's closure is recommended with it: D658 H-O2 (slot 7), and D652 v2 without its vault look (slot 9
  never taken).

**What stays open, named and not pursued without the principal's word:**
- the post hoc break × gamma continuation above, too small at this clock and unconfirmable on the vault;
- **SPX/0DTE gamma**, the only measurement never tried. It needs paid OPRA data and a quote first.
