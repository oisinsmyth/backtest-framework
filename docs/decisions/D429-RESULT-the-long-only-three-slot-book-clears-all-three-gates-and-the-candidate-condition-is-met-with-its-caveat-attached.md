# D429 RESULT — the long-only three-slot book clears all three gates, and the candidate condition is met, with its caveat attached

**T1 PASSES, T2 PASSES, T3 PASSES. THE CANDIDATE CONDITION IS MET** — under the principal's
standing rule, this book is a *tradeable indicator* and a candidate for `holdout2`. Pre-registration
`477df47` predates the runner and this file (R8). **The ledger does not move. Nothing was admitted.
No holdout of any kind was read — whether to read one is the principal's separate, explicit
decision, and this record does not make it.** Daily bars.

**The caveat, in the same sentence as the result, as the pre-registration required:** the arm
(long-only), the slot count (three) and the window (2018+) were all chosen after D428 was seen,
and T1's number had already been observed there. **The one number that had not been seen is
T3 — the 2018–2026 book — and it passed at +2.6 SE.** T2 is a new control (long pools) on a
book whose pooled result was known.

Cost: 230 s (24 books in 2 s; one worker measured at 970 MB; 100 control books).

```
[STAGE0] 1,416 / 165 reproduce;  [COST] the borrow term is identically zero on the pool
[P2]     the N=3 priority book == D428's LONG_N3 on every seed (net, gross, trade count to 1e-12)
[RECON]  24 books;  [CHUNK] worker draw 0 == in-process
```

---

## 1. The bar — N = 3, long, priority

```
T1  pooled net bp/bar          +4.395 ± 1.993      +2.2 SE     PASS   (a reproduction of D428)
T2  vs random cell-2 LONG pools of 1,416   p50 −0.790  p95 +1.549 (±0.125)   +22.8 SE   PASS
T3  2018–2026 net              +7.915 ± 3.055      +2.6 SE     PASS   (the unseen number)
```

---

## 2. The book

```
N   arm     gross    net    cost   util   trades  per trade   net by seed             pooled ± SE     2018+ ± SE      2021–26 ± SE
2   PRIO   +7.014  +4.085  2.928  42.4%    699    +82.64    +4.09 +5.21 +4.46    +4.59 ± 2.29    +8.72 ± 3.51    +7.14 ± 4.93
3   PRIO   +6.635  +4.199  2.436  35.8%    885    +92.62    +4.20 +4.52 +4.47    +4.40 ± 1.99    +7.92 ± 3.06    +8.28 ± 4.48
4   PRIO   +5.001  +2.953  2.048  30.0%    988    +83.38    +2.95 +3.15 +3.16    +3.09 ± 1.65    +5.29 ± 2.53    +5.40 ± 3.77
5   PRIO   +4.281  +2.512  1.769  25.7%  1,060    +83.16    +2.51 +2.59 +2.62    +2.57 ± 1.38    +4.46 ± 2.08    +4.55 ± 3.12
priority delta at N=3: +0.17 -- inside its noise, as in D428

N=3 by year (net bp/bar):
2010 +7.1  2011 +0.2  2012 +5.1  2013 +9.6  2014 −6.9  2015 −8.6  2016 −3.7  2017 +2.7  2018 +6.1
2019 +2.1  2020 +13.5  2021 +9.8  2022 −1.9  2023 −1.5  2024 +12.9  2025 +18.3  2026 +13.9
```

**Every book at every slot count is net-positive on every seed and in every window.** The peak
does not hold on the long arm — N = 2 is at or above N = 3 in every window (+4.59 vs +4.40
pooled; +8.72 vs +7.92 in 2018+), inside the noise; with 0.34 events a day even two slots are
42% utilised. X-e was wrong on that half. **Twelve of seventeen years are positive; 2014–2016
are three negative years in a row (−6.9, −8.6, −3.7), and 2022–2023 are slightly negative.**
The five years from 2020 are +13.5, +9.8, −1.9, −1.5, +12.9, then +18.3 and +13.9 (partial).

---

## 3. Per trade, and where the money sits

```
                       n     gross   median   cost    NET    win   payoff   trim    ex-top   ex-bot
long pool           1,416   +79.93   +99.0   35.1   +44.9  58.6%   1.00   +76.8   +53.4   +103.5
  2018+               764  +113.25  +119.8   36.2   +77.1  60.5%   1.01  +108.1   +81.4   +140.0
  2021–2026           528  +120.26  +117.3   37.0   +83.2  59.5%   1.05  +119.6   +89.2   +146.1
priority sub-cell     165  +113.25   +95.5   31.6   +81.7  58.8%   1.20  +108.0

concentration        names   to half   top1    top5    top10   years+   top name   top year
pooled                 336      11      9.7%   29.6%   48.3%   12/17     U         2026  19.8%
2018+                  226       8     12.7%   39.0%   63.1%    8/9      U         2026  25.9%
2021–2026              191       5     17.3%   51.7%   83.1%    5/6      U         2026  35.3%
```

The long pool's median is above its mean in every window — the ordinary distribution D422
identified — and it survives the symmetric trim and the removal of its top 1% (+53). No long
trade exceeds |50%|, so the corporate-action variant is the pool itself. **The top trade is named
and its bars were read: KSS, 2025-11-19, 15.41 → 24.10, a +45% move that arrived on the fourth
session on 35.5M shares** — a real event, 4.0% of pooled P&L and 5.2% of 2018+.

**The concentration is the thing to carry.** In the 2018+ window that passed T3, **eight names
are half the P&L and the top ten are 63%**; in 2021–2026, five names are half and ten are 83%,
with 2026 — a partial year — at 35%. T3's SE of 3.06 is those eight names being resampled. The
gate passed at +2.6 SE; it did not pass by a distance that makes that sentence unnecessary.

---

## 4. Predictions — six of six, one half

| | prediction | outcome |
|---|---|---|
| X-a | pooled reproduces +4.40 ± 1.99 | exact |
| X-b | 2018+ +5.5..+8, SE 2.5..3.5 | +7.92 ± 3.06 |
| X-c | 2018+ 8–12 names to half, top year ≤ 30% | 8 of 226; 2026 25.9% |
| X-d | control p95 +0.5..+2.0, beaten by > 2 SE | +1.55; +22.8 SE |
| X-e | priority inside ±0.4; **peak at N=3** | +0.17 ✓; **N=2 ≥ N=3 in every window** |
| X-f | ≥ 11 of 17 years positive; 2022 or 2023 < 0 | 12/17; both slightly negative |

Six of six because every prediction was arithmetic on a table that had already been seen — the
pre-registration said so. That is what a second look at a known object is supposed to look like,
and it is also why a second look is worth less than a first.

---

## 5. What this leaves

1. **The candidate condition is met**, on the terms the principal set after D428: long-only,
   three slots, 2018+ as the second-half window. Under the standing rule that makes this book a
   tradeable indicator. **Reading `holdout2` is not a consequence of this record; it is a decision
   the principal makes explicitly, and it is the one thing left that can move the ledger.**
2. **What a holdout read would be judging:** a three-slot long book on second touches of cheap
   demand zones, `t+5` and nothing else, at ~36% utilisation, +4.4 bp/bar pooled and +7.9 in
   2018+ on the spent data — with eight names carrying half of the passing window, three
   consecutive negative years in the first half, and a cost model that has been checked against
   nothing but the OHLC.
3. **The arm, slots and window were chosen on the data that then passed.** The pre-registration
   said so before the run; the result says so after. The holdout exists for exactly this.
4. **N = 2 is not worse than N = 3 on this arm.** A two-slot book is the same object with
   higher utilisation; the record does not pick between them and neither was the primary.

**Disposition — and whether the holdout is read — is the principal's.**

---

## 6. R13

Twenty-ninth look by object on price levels; the second look at this book. No new data spent.

**Evidence:** `data/d429_long_book.json`. Runner `scripts/run_d429_long_book.py`; pool
`scripts/d428_pool.py` (D428's, unchanged).
