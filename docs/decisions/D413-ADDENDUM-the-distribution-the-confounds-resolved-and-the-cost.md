# D413 ADDENDUM — the trade distribution, both confounds resolved, and the cost arithmetic

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D413-ADDENDUM-the-distribution-the-confounds-resolved-and-the-cost-arithmetic.md`. The H1 above is the full title.*

**EXPLORATORY. Clears nothing, admits nothing, and does not change D413's verdict (`1587f66`).**
All of it is measured on data D413 has already spent. Written because the principal asked whether
the win rate could be raised, and because D413's record left CLAUDE.md's reporting standard half
done and two confounds named but unresolved.

---

## 1. THE COST ARITHMETIC, WHICH IS THE ANSWER TO THE QUESTION ASKED

Corwin–Schultz off the OHLC of **the names actually held**, using D285's own estimator, imported.
IBKR's published `$0.0035`/share.

```
GROSS                       +13.22 bp
spread (Corwin-Schultz)     -76.65      (one-way median 17.0 bp)
commission (IBKR floor)      -2.41
NET                         -65.84 +-1.48

coverage on MEANS    13.22 / 79.07  =  0.17x
coverage on MEDIANS   8.80 / 57.87  =  0.15x
```

**The edge covers about one sixth of its own cost. It would have to be roughly SIX TIMES BIGGER to
break even.**

Both figures are reported because Corwin–Schultz floors each negative daily estimate at zero, which
truncates noise on one side and **biases the mean upward**. The median is the more conservative
central estimate and **it agrees**: 0.15× against 0.17×. The tail is not what is doing this.

**And no filter in the data closes it:**

```
age >= 3 bars              n 136,510   gross +20.80   NET -57.17 +-1.64
age >= 3 and price >= $20  n 109,661   gross +15.11   NET -57.48 +-1.73
price >= $20 only          n 144,523   gross  +8.14   NET -65.44 +-1.57
```

The largest gross sub-population anywhere in D413 is the most-reverted quintile at **+48.79 bp** —
still below a ~58–79 bp round trip, and those are the widest-spread bars in the sample.

**The door that would normally be open here is shut by the data.** A longer hold amortises one round
trip over more edge, which is the standard fix. The horizon scan says there is no longer hold:

```
h= 1  +2.31   h= 3  +8.56   h= 5 +13.21   h= 8 +13.37
h=10  +4.33   h=15  -1.81   h=21  -4.59
```

**The edge peaks at 5–8 bars and is gone by 10.** It decays faster than cost amortises.

---

## 2. So: can the win rate be raised?

```
n 180,050   mean +13.21 +-1.48 bp   MEDIAN +8.79 bp   win 50.77%
avg win +410.38   avg loss -399.22   payoff 1.028
skew -0.73   kurtosis 66.3
```

**Win rate is not the binding constraint and raising it would not help.** The book is nearly
symmetric — 50.77% at a payoff of 1.028 — so the expectation is a thin residue of two large opposing
averages. Any exit rule that raises the hit rate does so by cutting the right tail, and with a
payoff already at 1.03 there is no slack to give up. The binding constraint is §1: a 6× shortfall.

**A note on a number that looks alarming and is not.** The top 1% of trades account for **192.3% of
total P&L**, and dropping them turns the mean to **−12.31 bp**. That is D307's trap exactly — on a
two-sided fat-tailed book, dropping only winners always frightens. **The symmetric trim is the
verdict: 1% off BOTH tails gives +13.05 bp against a raw +13.21.** The edge lives in the middle 98%
and is not tail-driven.

---

## 3. Both confounds resolved, and they cost most of T2

**The fix is direct standardisation** — the control's per-bin mean reweighted to the *real*
population's bin weights, so the two are compared on the same event mix rather than on the same
inputs.

```
real                                  +13.21 bp
LVL raw (D413's T2 comparison)         +4.56      gap +8.66
LVL standardised on AGE                +10.68      gap +2.54
LVL standardised on AGE x REVERSAL      +9.82      gap +3.39
```

**The age-mix artefact was worth about 70% of T2's margin.** D413 reported +77.7 SE; the honest
level contribution is **+2.5 to +3.4 bp**, not +8.7.

And within reversal bins, the level's contribution is not general:

```
rev bin 1  real +48.79   LVL +27.78   gap +21.01 +-4.20   (+5.0 SE)
rev bin 2  real +18.12   LVL +15.24   gap  +2.88 +-2.97   (+1.0 SE)
rev bin 3  real  +6.05   LVL  +4.27   gap  +1.78 +-2.56   (+0.7 SE)
rev bin 4  real  -3.27   LVL  -4.40   gap  +1.13 +-2.67   (+0.4 SE)
rev bin 5  real  -3.60   LVL  -6.05   gap  +2.45 +-3.91   (+0.6 SE)
```

**One bin of five.** The level beats a matched band only where price has already fallen hardest into
it — and even there, `LVL` alone pays +27.78 of the +48.79, so most of that cell is the move, not
the level.

**A binning bug was caught and fixed before any of this was read.** The first run took `np.quantile`
over an array carrying NaNs from the early bars, every edge came back NaN, and all 180,050 events
collapsed into one bin — which printed as a tidy one-row table showing a `+5.8 SE` gap. **It would
have been reported as a reversal control that controlled for nothing.** Non-finite values are now
excluded rather than swept into bin 0, and both populations' bin occupancy is printed.

---

## 4. What the winners depend on

**Concentration is healthy, which is the one unambiguously good number here.** 1,433 names,
**52 names to reach half the P&L**, top-1 name 1.9%, top-5 8.5%, top-10 15.2%.

**The era split is not.**

```
2010 +67  2011 +37  2012 +47  2013 +20  2014  -7  2015 +21  2016 -14  2017  +6
2018  -9  2019  -1  2020 +35  2021  -1  2022  +5  2023  +8  2024 +12  2025 +17  2026 +18
```

**12 of 17 years profitable, but the first four carry it** — 2010–2013 averages ~+43 bp against
~0 for 2014–2019. Whatever this is, it was larger before 2014.

**And the price split is the D284 shape:**

```
$13.6 +33.54    $26.9 +11.48    $41.9 +10.09    $67.1 +4.81    $149.3 +6.20
```

**Monotone decreasing in price** — the gross edge is largest exactly where cost in bp is largest.
That combination killed D284, and §1 shows it doing the same thing here: the cheapest quintile has
the best gross (+33.54) and the worst cost (101.13).

---

## 5. What would have to be true

Stated as arithmetic, not as a recommendation. **Disposition is the principal's.**

1. **A ~6× larger gross edge per trade.** The best sub-population found is 3.7× (reversal bin 1) and
   is mostly the move rather than the level.
2. **Or a round trip near 10 bp instead of 58–79.** That is a different execution venue or a
   different instrument, not a different filter.
3. **Or a longer hold** — closed off by the horizon scan in §1.

**Not run, and still the two cleanest open questions:** whether the +2.5–3.4 bp standardised gap
survives a time rotation, and whether it survives out of sample. Neither is worth paying for until
§1 has an answer.

---

**Evidence:** `data/d413_diagnostics.json`, `data/d413_costs.json`. Runners
`scripts/run_d413_diagnostics.py`, `scripts/run_d413_costs.py`, the latter importing D285's
`corwin_schultz` rather than reimplementing it.
