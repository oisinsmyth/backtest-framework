# D455 RESULT — insider purchases pay +89 bp a quarter against their cell, in the body of the distribution not the tail, and net zero at the crossed line: NOT a candidate

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D455-RESULT-insider-purchases-pay-89-bp-a-quarter-against-their-cell-and-net-zero-at-the-crossed-line-not-a-candidate.md`. The H1 above is the full title.*

**NOT A CANDIDATE: T1 passes; T2, T3, T4 and T5 fail.** Spec `398669b` predates the runner (R8).
**In-sample; no holdout read; nothing admitted.** 2.7 min (primary and nine reported sets, 100
state-matched draws, 198 exact rotation offsets, 100 name-preserving shuffles). The first
forward-return look at insider demand in this repo.

```
[K] kernel probe;  [F] every availability bar is strictly after its filing date (asserted on 127,105 filings)
purchase filings 2010-2023 on eligible names 10,641 -> primary (no 10% owner, value >= $25k) 7,478 -> 4,086 trades (the kernel skips a name already held)
cluster 3,023 / single 4,455;  officer-only 1,371 / director-only 4,405;  10%-owner 1,247;  sales mirror 80,513 filings -> 17,335 shorts
selftest: masks, dilation, the family-trust cap, [F] on the real events, C2 at offset 0 == the real mask, the C1 pool excludes every purchase name
```

---

## 1. The bar (primary set, cap 63, crossed)

```
T1  per-trade gross > C1 p95 by 2 MC-SE      +89.4  vs  C1 p50 +24.3, p95 +72.3 +- 2.8;  draw SD 28: real +2.35 SD above the median, +0.62 beyond p95    PASS
T2  book gross > C2 p95 (exact) and > C3 p95   +1.110 vs  C2 p50 +0.657 p95 +1.474  |  C3 p50 +0.670 p95 +1.294 +- 0.043                                  FAIL / FAIL
T3  book net crossed > 0 by 2 SE               +0.082 +- 0.557                                                                                            FAIL
T4  era-2 net crossed > 0 by 2 SE              +0.386 +- 0.899   (era 1 -0.222 +- 0.608)                                                                  FAIL
T5  >= 20 names to half, top 1% <= 50%         14 names, 70%                                                                                              FAIL
```

---

## 2. The two lenses

```
per trade, 63-bar hold, hedged (bp)        n      gross    median   trimmed 1%   win   2c PUB   net     C1 p50 / p95        increment
  PRIMARY                                4,086    +89.4    +96.4     +89.3      53%    64.7    +24.7    +24.3 / +72.3       +65.0 (2.35 SD)
  cluster (>= 2 distinct buyers)         1,352   +120.1    +61.0                       71.0    +49.2
  single                                 3,202    +53.9    +91.6                       62.9     -8.9
  director-only                          2,855   +101.3   +111.2                       63.3    +38.0
  officer-only                             993    +58.4    +47.1                       67.2     -8.8
  value top tercile / bottom tercile   1,671 / 1,717   +96.9 / +91.6
  10%-owner set (reported)                 438   +163.1   +210.8                       88.9    +74.3      (1 name to half the P&L)
  sales mirror, SHORTED                 17,335    -23.2 +- 12.3   -47.2                58.1   -96.7 (with borrow 15.4)

the book (bp/bar)                       gross     SE     crossed  net crossed   passive net   era1             era2 (2017-02 on)
  PRIMARY cap 63                        +1.110   0.557    1.028    +0.082        +0.617       -0.222 +- 0.608  +0.386 +- 0.899
  cap 21                                +1.889   0.890    3.08     -1.189
  cap 126                               +0.876   0.457    0.516    +0.360
  by year (net crossed): 2010 -0.8  2011 +0.3  2012 +1.2  2013 -0.6  2014 -1.5  2015 -2.0  2016 +1.6  2017 -0.3  2018 -0.6  2019 +1.1  2020 -1.3  2021 +0.3  2022 +3.9  2023 +2.0
```

**Per trade the effect is real and it is in the body.** A non-10%-owner insider's open-market
purchase of at least $25k is followed by +89 bp hedged over the next quarter; a random name in
the same price × volatility × momentum cell on the same day earns +24. The increment is +65,
2.35 draw-SDs above the control median (p ≈ 0.01). **The median is +96 and the 1%-trimmed mean
is +89.3 — identical to the mean.** This is not a tail effect; the win rate is 53% on a
distribution whose 5th and 95th percentiles are ±2,550 bp. The top name (MTDR) is 6% of the
P&L across 865 names.

**The book does not clear its cost.** +1.11 bp/bar gross on an SE of 0.56; the rotated calendar
earns +0.66 on any dates (the names insiders buy are beaten-down small names that recover on
average, hedged); the alignment adds +0.45, under one SE. Crossed cost 1.03 a bar — a quarter's
hold in names whose modelled round trip is 65 bp — leaves +0.08. The passive line leaves +0.62 at
1.1 SE. Shortening the hold to 21 bars triples the gross per bar and triples the cost: −1.19 net.

---

## 3. What the reported lines say

- **Clusters carry it, as the literature says:** a second distinct insider within a week doubles
  the per-trade gross (+120 vs +54). Officers do *not* beat directors here (+58 vs +101), the
  reverse of the prediction — on this universe the informed buyer is the board.
- **Value has no gradient** (+97 top tercile vs +92 bottom) once the $25k floor is applied.
- **The 10%-owner set is a lottery** (+163 per trade, one name to half the P&L, 438 trades) and
  was rightly set aside.
- **Shorting insider sales loses:** −23 ± 12 per trade before cost, −97 after borrow and spread.
  Sales are not information; they are diversification, and the names go on rising.
- **Era 2 is better than era 1** (+0.39 vs −0.22), against X-f; 2022–2023 are the best years.

---

## 4. T5, read honestly

T5 fired on **top 1% of trades = 70% of P&L**, which on a 4,086-trade book with ±2,500 bp tails
measures dispersion, not a lottery: the symmetric 1% trim leaves the mean unchanged and the
largest name is 6%. The clause was written for D446's shape (five names, one 29% trade) and is
the wrong instrument here; **the bar stands as pre-registered and T5 fails as written**, and the
next insider record — if there is one — should state concentration as names-to-half and the
symmetric trim, which is what CLAUDE.md's reporting rule asks for anyway.

---

## 5. Predictions — two of six

| | prediction | outcome |
|---|---|---|
| X-a | gross +120..+260, median +40..+120; C1 p50 +20..+60; increment +80..+200 at ≥ 2 SD | **+89**, +96 ✓; +24 ✓; **+65** at 2.35 SD |
| X-b | gross +2.0..+4.0, SE 0.8–1.2, crossed 1.2–2.2, net +0.3..+2.2, passive ≥ +1.5 | **+1.11**, 0.56, 1.03, **+0.08**, **+0.62** |
| X-c | C2 p50 +0.5..+1.2, p95 +1.5..+2.5; C3 within 0.3 / 0.4 of C2 | +0.66 ✓, **+1.47**; C3 +0.67 / +1.29 ✓ |
| X-d | cluster > single +40..+100; officer > director; value hi > lo; 10% below primary; sales 0 ± 40 | +66 ✓; **director > officer**; **flat**; **10% above**; −23 ✓ |
| X-e | cap 21 per bar ≥ cap 63; cap 126 below | ✓ ✓ |
| X-f | era 2 > 0 and < era 1, T4 fails; to-half ≥ 40, top 1% ≤ 40 | era 2 **> era 1**; T4 fails ✓; **14**, 70% |

The size of the effect was over-predicted by about half; every structural prediction about the
controls held.

---

## 6. What this leaves — the principal's call

1. **Insider purchases are a real, contrarian, body-of-the-distribution effect on this
   dead-inclusive fixture**: +65 bp a quarter over the cell, doubled when insiders cluster,
   carried by directors, absent in sales.
2. **They are not a book at the crossed line**, for the same reason issuance was not: the effect
   lives in small, thin, beaten-down names where a quarter's round trip costs what the quarter
   earns. Under the passive assumption the book is +0.62 at 1.1 SE. **Two filing-based lines now
   give one answer, and it is about the cost of the names, not the signal.**
3. **What is not proposed:** a hold sweep (21 is worse net, 126 is +0.36 at 0.8 SE), a cluster-only
   book (1,352 trades, −0.42 net crossed), or a value floor sweep — each a selection on spent
   events. **What would change the verdict:** the quoted-spread pull (D441's instrument, still
   unrun) — if the modelled 65 bp round trip on these names is a range and the quote is half of
   it, the passive net of +0.62 becomes a crossed net near +0.6 on an SE of 0.56, still ~1 SE;
   the sample, not the cost, is then the ceiling.
4. **The holdouts stay shut.**

**Disposition is the principal's.**

---

## 7. R13

Forty-seventh look by object; look #1 of the insider line's forward-return ledger; no holdout.
**Evidence:** `data/d455_insider_book.json`. Runner `scripts/run_d455_insider_book.py`.
