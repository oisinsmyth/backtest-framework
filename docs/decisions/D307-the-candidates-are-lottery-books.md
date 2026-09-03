# D307 — the candidates are lottery books, and 80% of the target's edge was a spread artefact

**Status:** DIAGNOSTIC, not a study. Nothing searched, nothing promoted. Every
construction was decided by D306. Runner at `d307_risk_on_candidates.py`.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. THE FINDING THAT MATTERS MOST — the target's net edge is mostly a
## measurement artefact

Each cell's net is charged the round trip of **the names it holds**. At N=2 the
no-exit book measures **86.7 bp** and the target book **73.2** — a 16% gap at the
same depth, caused only by the exit rule changing *when* positions are opened.

| | round trip | net |
|---|--:|--:|
| N=2 / none | 86.7 | +11.20 |
| N=2 / target | **73.2** | **+15.25** |
| **N=2 / target, charged the no-exit book's 86.7** | 86.7 | **+12.00** |

**The target's advantage is +4.05 on own spreads and +0.80 on a common one.**
Four fifths of it is the spread measurement, not the exit.

**And +0.80 is almost exactly the +0.79 the target was worth at N=19** in D305's
clean matched pair. Charged consistently, **the target is worth about +0.8 bp net
at both ends of the width axis** — small, stable, and a fifth of what D306's
table appears to show.

This does not overturn D306's ranking — N=2/target is still the best net cell at
+12.00 against +11.20 — but it removes most of the margin, and it means **any
comparison of two exit rules must charge them a common spread or it is partly
measuring which rule happens to trade tighter names.**

## 2. Every candidate is carried by its top 1% of trades

| cell | trades | mean | **mean ex-top-1%** | top 1% share of P&L |
|---|--:|--:|--:|--:|
| N=2 / target | 3,067 | +68.1 | **+2.5** | **96%** |
| N=3 / target | 4,613 | +54.2 | **−2.0** | **104%** |
| N=5 / none+overlay | 6,372 | +41.1 | **−13.4** | **133%** |
| N=7 / none+overlay | 8,920 | +34.1 | **−20.2** | **159%** |

**Three of the four lose money without their best 1% of trades.** The fourth
survives at +2.5 bp, which is not survival in any useful sense.

This is D285's pathology exactly — there the top 1% was 196.9% of P&L — and it is
**worse at wider books**, which is the opposite of what diversification is meant
to do.

## 3. Name concentration and drawdown

| cell | names | **to half P&L** | top-1 name | top-5 | maxDD | longest underwater | % of bars under |
|---|--:|--:|--:|--:|--:|--:|--:|
| N=2 / target | 718 | **6** | 17.0% | 46.3% | 13,478 | **466 bars** | 92% |
| N=3 / target | 842 | 7 | 13.9% | 44.7% | 14,280 | 649 bars | 92% |
| N=5 / none+overlay | 981 | 8 | 13.0% | 41.3% | 9,750 | 682 bars | 93% |
| N=7 / none+overlay | 1,086 | 9 | 11.1% | 36.9% | 54.5% → 7,861 | **967 bars** | 93% |

**Six names of 718 produce half the P&L**, and one name produces 17% of it. The
books spend **92–93% of all bars below a prior peak**, with underwater runs of
**466 to 967 bars — two to four years**.

## 4. Era and stability

| cell | years profitable | worst year | rolling 252-bar Sharpe (min / median / max) | negative windows |
|---|--:|--:|---|--:|
| N=2 / target | 10 / 14 | −32.4 | −0.70 / **+0.90** / +2.41 | 10 of 47 |
| N=3 / target | 11 / 14 | −9.7 | −1.20 / **+1.02** / +3.39 | 10 of 47 |
| N=5 / none+overlay | 9 / 14 | −27.9 | −1.52 / +0.90 / +2.78 | 11 of 46 |
| N=7 / none+overlay | 8 / 14 | −24.8 | −1.89 / +0.82 / +3.39 | 13 of 44 |

**N=3/target is the most stable** — 11 of 14 years, the shallowest worst year at
−9.7, and the highest median rolling Sharpe. **N=7/none+overlay, D306's best
Sharpe cell, is the least stable on every one of these measures.**

## 5. What theory says should be true, and whether it is

**The two things that are mechanically forced hold exactly:**

| | theory | observed |
|---|---|---|
| cost/bar invariant to `N` | turnover is the rate `1/k` | 0.2002–0.2003 at every depth, spread 0.0000 |
| gross monotone in `N` | the edge is rank-monotone | +28.57 → +7.54, no inversion |

**Everything requiring a behavioural mechanism is noisy or backwards:**

| | theory | observed |
|---|---|---|
| the target's contribution should respond **smoothly** to width | a real mechanism does not zigzag | **+4.32, +7.39, +1.38, −0.20, +2.27, +2.10, +4.46** — a 7.6 bp range with no shape |
| Sharpe should be **humped** in `N` — diversification against edge dilution | | 0.770, 0.640, 0.691, 0.661, 0.497, 0.559, 0.512 — no hump, no trend |
| the overlay should help most where **volatility is highest** | it is a drawdown-triggered de-risk | it helps at N=5–19 and **hurts at N=2**, where vol is highest |

**That is the diagnosis. The width effect is real and mechanical; the exit
effects are noise on top of it.** Both mechanical predictions hold to four
decimals, and all three behavioural ones fail.

### Cells that theory says should be better than they are

- **N=5 / target** should be strong — near the breakeven depth, with the exit
  that works at both extremes. It is **−3.12**, the worst cell at that depth. The
  target adds only +1.38 gross there while costing more.
- **N=7 / target** adds **−0.20 gross**. On any mechanism story the target should
  add *something* at every depth.
- **N=3 / target's +7.39** is the largest target contribution in the grid, at a
  depth where nothing distinguishes it. Suspiciously high rather than
  encouraging.

**The target's contribution profile is two highs, two lows and a 7.6 bp range on
an effect whose consistent value — charged a common spread — is about +0.8.** The
grid's variation is mostly noise, and N=2's apparent win is partly where the
noise landed.

## 6. The cell I would reason to, rather than maximise to

**N=3 / target.** Not the best net (+5.55 against N=2's +12.00 on a common
spread) but:

- **the most stable across eras** — 11 of 14 years, worst year −9.7 against
  N=2's −32.4, highest median rolling Sharpe at +1.02;
- **six positions rather than four**, which is still not a portfolio but is 50%
  more of one;
- **Sharpe +0.797 against N=2's +0.754** — better on the robust statistic;
- and it clears its own null at **p = 0.0050 on both statistics**, which N=2 /
  target does not (p_sharpe = 0.0597).

**Its weakness is the same as everything else here: −2.0 bp ex-top-1%.**

## 7. Stop

**No cell here is a candidate for R8.** Every one is a lottery book, three of
four lose money without their best 1% of trades, and all spend 92% of their life
underwater.

**What would change that is not another parameter.** It is either an entry signal
that produces a less skewed trade distribution — the entry has been frozen since
D293 and is the largest untested surface in the programme — or acceptance that
this edge is real but untradeable at any width.

**And borrow is still unmodelled**, on a short book of four to fourteen names.

## Files

`data/d307_risk.json` · `scripts/d307_risk_on_candidates.py`
