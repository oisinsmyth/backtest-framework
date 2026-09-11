# D446 RESULT — issuance pays per trade on both sides against its state, and the book is a lottery carried by GameStop and three biotechs: NOT a candidate

**NOT A CANDIDATE: T3 passes on both sides; T1, T2, T4 and T5 fail.** Spec `84793d8` predates the
runner (R8). **In-sample; no holdout was read; nothing is admitted.** 10.7 min (two sides, 200
state-matched draws, 198 exact rotation offsets, 100 persistent-selector draws, three robustness
lines). **The first forward-return look at share supply in this repo.**

```
[K] kernel probe;  [F] masks shifted one bar (fill at the next open);  score: 535 names with a fresh NS per bar (median), first bar 2010-07-30, last 2023-12-29
slot book: 40 a side, 50 in each decile, cap 126 -> 1,055 short and 1,063 long trades, hold 125, turnover 0.8%/bar a side
selftest: availability / freshness / supersession / scale guard / percentile / shift; C3 transition rows; C2 at offset 0 == the real masks; C1 never draws a decile name
```

---

## 1. The bar (combined book, cap 126, n_max 40, crossed line)

```
T1  gross > C2 p95 (exact) AND > C3 p95 by 2 SE      +2.296  vs  C2 p95 +3.768 (p50 +1.122)   FAIL  |  vs C3 p95 +1.761 +- 0.081 (p50 +0.391)  pass
T2  net crossed > 0 by 2 SE                          +0.967 +- 1.515   (+0.6 SE)               FAIL
T3  per trade > C1 p95 by 2 SE   short / long        +72.1 vs +0.8 +- 6.5  /  +208.4 vs +163.0 +- 6.9      PASS / PASS
T4  era-2 net crossed > 0 by 2 SE                    +0.524 +- 2.586                             FAIL
T5  >= 20 names to half the P&L, top 1% <= 50%       5 names, 85%                                FAIL
```

---

## 2. The two lenses

```
per trade (126-bar hold, hedged, bp)      n      gross    median   2c PUB   borrow   net     C1 state-matched p50 / p95     increment
  short (net issuers)                   1,055    +72.1    +127.9    75.4     33.4    -36.7        -96.6 / +0.8 +- 6.5        +168.7
  long  (net repurchasers)              1,063   +208.4    +218.3    56.9      0.0   +151.5        +34.2 / +163.0 +- 6.9      +174.2
the book (bp/bar, hedged, deployed)      gross     crossed  net      passive  net      era1            era2 (2017-04 on)     Sharpe
  short                                  +0.755    0.872   -0.118
  long                                   +1.541    0.457   +1.084
  COMBINED                               +2.296    1.329   +0.967    0.773   +1.523   +1.41 +- 1.56   +0.52 +- 2.59          +0.17
  by year (net crossed): 2010 -4.6  2011 +1.1  2012 +0.6  2013 +12.1  2014 -1.0  2015 +3.6  2016 -4.6  2017 -0.1  2018 +2.7  2019 -3.4  2020 -14.5  2021 +13.2  2022 +3.4  2023 +2.0
robustness (not gated):  cap 63 gross +1.79 net -0.62   cap 252 +1.63 / +0.81   n_max None +1.96 / +0.64
```

**Per trade the effect is there and it is large.** A net issuer, shorted for six months and hedged,
earns +72 bp against −97 for a random name in the same price × volatility × momentum cell —
shorting small volatile names loses money hedged, and the issuers do not; a net repurchaser
earns +208 against +34 for its cell. Both increments are +170 bp per trade, 25 SE past the
control's p95. That is the literature's sign on both sides, on the dead-inclusive fixture, with
first-filed counts.

**The book does not collect it.** +2.3 bp/bar gross on an SE of 1.5; net of the crossed line +1.0
at 0.6 SE; the second half +0.5 at 0.2 SE. And the reason is not the noise alone — it is the
shape: **five names carry half the combined P&L and the top 1% of trades is 85% of it.**

---

## 3. What carries it, named

```
SHORT   RVNC  35%   PACB  32%   ARQT  26%   AHT  20%   RIG  19%   MRSN  19%      (biotech and collapse names; RVNC's best trade +11,794 bp from 2023-08)
LONG    GME   29%   RH    10%   HIBB   6%   ORLY  6%   UI    6%   USNA  5%       (GME: +49,515 bp on a trade entered 2020-10-15 -- the January 2021 squeeze, held as a REPURCHASER)
```

**GameStop entered the long leg on 2020-10-15 as a net repurchaser (it had bought back a third of
its shares) and was held through January 2021.** One trade is 29% of the long side and more than
a fifth of the combined book. The short side is three biotechs that collapsed while in the top
issuance decile. Strip nothing — the record does not trim — but say what the +2.3 bp/bar is: a
median-positive per-trade edge whose *book* is dominated by six trades in thirteen years.

---

## 4. The controls, and what each one said

- **C1 (state-matched names)** is the control that mattered: it moved the short side's baseline
  to −97 and the long side's to +34. Without it, the long leg's +208 would read as pure edge; with
  it, +174 of it is. Passing C1 by 25 SE on both sides is the finding of this record.
- **C2 (the panel rolled in time, exact on the 21-bar grid)** has **p50 +1.12 and p95 +3.77** —
  a persistent decile selector on the *wrong dates* still earns +1.1 bp/bar, because rolling the
  panel keeps each name's state (a repurchaser rolled a year is still a large, low-volatility name;
  an issuer is still small and volatile) and the hedged base rate of that composition is positive.
  The real book is +1.2 above C2's median: 0.8 SE of its own noise. **C2 is the stricter of the two
  book controls and it is the one that failed.**
- **C3 (the persistent random selector, matched on the empirical transition matrix — self-transition
  0.76 in the top decile, 0.75 in the bottom, 0.47–0.55 in the middle)** has p50 +0.39, p95 +1.76:
  with the *names* randomised the base rate falls to a third of C2's. The real book clears it by
  6.6 SE. The gap between C2's and C3's medians (+0.7 bp/bar) is the price of the state tilt, and
  X-c said they would be within 0.5 — they are not.

---

## 5. Predictions — three of six

| | prediction | outcome |
|---|---|---|
| X-a | short +40..+120, long +20..+60, short median < mean | short +72 ✓ (median **+128** — the left tail is the squeezes, not the right tail the collapses); long **+208**, median +218 |
| X-b | gross +1.5..+3.5, SE 1.2–1.6, net +0.5..+2.5, short > long | +2.30 ✓, 1.51 ✓, +0.97 ✓, **long > short** |
| X-c | C1 p50 ≈ 0 both; C2 p50 ≈ 0, p95 +1.5..+2.5; C3 within 0.5 of C2 | C1 **−97 / +34**; C2 p50 **+1.12**, p95 **+3.77**; C3 p95 2.0 below C2's |
| X-d | T1 passes C2, coin on C3; T3 short pass, long marginal; T5 pass; T4 fail | C2 **fail**, C3 pass; T3 **both pass**; T5 **fail**; T4 fail ✓ |
| X-e | cap 63 within 30%; cap 252 lower; n_max None 20–40% lower | +1.79 ✓; +1.63 ✓; +1.96 (−15%) |
| X-f | short HTB > 20%, borrow > 5, 2c 60–90 | HTB **4%**, borrow 33 ✓ (six months of GC), 2c 75 ✓ |

The misses are the record: the state-matched baselines are far from zero on both sides, the
rotated persistent selector has a large positive base rate, and the book is far more concentrated
than a supply effect should be.

---

## 6. What this leaves — the principal's call

1. **Share supply predicts the hedged return of the name, per trade, on both sides, against the
   right control, on the dead-inclusive fixture.** That is new in this repo and it survived the
   control that killed D405.
2. **It is not a book at 40 slots and 126 bars:** the P&L is six trades, the noise is the book's
   own, and the second half is flat. The spec's T5 was written for this and it fired.
3. **The path that is not a refinement:** the concentration says the per-trade effect is real but
   the *tails* dominate a 40-name book — which is what an equal-weight book of small volatile
   names does. The two honest next questions are (a) whether the effect is in the *median* trade
   at all horizons (a per-trade study across caps, no book), and (b) whether a broader book —
   every decile name, n_max None, which was −15% on gross but 3.5× the trades — has the same
   per-bar mean on a smaller SE; the robustness line says +1.96 ± 1.24, so no. Either is a new
   record; neither is a sweep of this one.
4. **The holdouts stay shut** — no candidate condition was met, and they have no EDGAR panel.

**Disposition is the principal's.**

---

## 7. R13

Forty-fourth look by object; look #1 of the issuance line's forward-return ledger; no holdout.
**Evidence:** `data/d446_issuance_book.json`. Runner `scripts/run_d446_issuance_book.py`.
