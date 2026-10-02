# D767 STAGE 0 RESULT — MGC NOT ABOVE NULL, SIL and MHG NO MECHANISM: the unconfirmed China open does not reverse more; the filter's accuracy is negative on all three metals

*2026-10-02. One run of `scripts/stage0_d767_china_open_fade_filter.py --run` (0.91 minutes).*
- **The order:** the [pre-registration](D767-STAGE-0-PRE-REG-fade-the-unconfirmed-china-open.md) (`fd15cbb4`) came
  before the runner (`21d91f27`), and the runner before its one run.
- **Output:** `data/stage0_d767_china_open_fade_filter.json` (statistics only).
- Before the run, the whole run path was exercised on synthetic bars.
- **The priors were:** a SUPPORTED cell about 15%, gold about 8%.

## 0. Checks

- **The candidates are D765's eligible sessions with x ≠ 0:** MGC 1,697, SIL 1,649, MHG 1,681.
- **The selectable pool** (past the 250-session burn-in, with a finite score and 100+ finite prior scores): 1,447,
  1,397 and 1,430.
- **U's walk-forward third:** 486, 470 and 470 trades. The secondary (D765's |x| third ∩ U): 93, 97 and 115.
- **The lag audit:**
  - explicit-loop, sorted-median recomputations of F3, F4 and U on 40 sampled sessions per cell agree;
  - a hand-written quantile re-derives every selection flag;
  - the self-test proved the flag audit raises on a threshold that includes the current session.
- **Right quantity:**
  - U differs from F3 and from F4;
  - the filtered book differs from the unfiltered one;
  - rotation offset 0 reproduces the observed selection and its mean net.
- **The null:** an exact rotation of U against the candidates, 1,648–1,696 offsets per cell on 8 processes. The
  rotated books' counts sit at 448–486, so the statistic is count-stable.

## 1. The readings

| | G1 the unfiltered fade, gross (t) | N: U's mean net against the rotation (p50 / p95 / rank) | B1 / B2 | G2 | reading |
|---|---|---|---|---|---|
| **MGC** | **+\$3.14 (2.49): pass** | −\$2.96 against −\$2.35 / +\$0.83; rank 0.36 | pass / fail | fail | **NOT ABOVE NULL** |
| **SIL** | +\$6.01 (1.73): fail | −\$3.40 against −\$1.44 / +\$7.77; rank 0.36 | pass / fail | fail | **NO MECHANISM** |
| **MHG** | +\$2.28 (1.73): fail | −\$3.93 against −\$2.14 / +\$1.41; rank 0.21 | pass / fail | fail | **NO MECHANISM** |
| S2 (secondary) | | MGC −\$1.69 (rank 0.48), SIL +\$18.44 (rank 0.81), MHG −\$5.66 (rank 0.25) | | fail | **SECONDARY: NOT ABOVE NULL / NO MECHANISM / NO MECHANISM** |

- **GO false.**
- **The filter does worse than a random third on every cell** (ranks 0.21–0.36).
- Only gold's unfiltered fade shows a gross mechanism, and it was D765's in-sample discovery.

## 2. Why: the accuracy has the wrong sign

| | ρ(U, gross) | ρ(F3 the AUD, gross) | ρ(F4 the metals, gross) | AUC of U against the oracle | share of the oracle's net captured |
|---|---|---|---|---|---|
| MGC | **−0.042** | **−0.052** | −0.001 | 0.47 | −5.9% |
| SIL | −0.033 | −0.029 | −0.018 | 0.48 | −2.5% |
| MHG | −0.028 | −0.027 | −0.006 | 0.48 | −6.8% |

- **The partial-oracle curve said:** break-even needs about +0.05 (MGC, MHG) or +0.02 (SIL). The filter sits at −0.03
  to −0.04.
- **The AUD half carries the sign.** When the AUD does NOT confirm the metal's opening move, that move reverses
  slightly LESS. The SE of ρ is about 0.026, so gold's −0.052 is about 2 SE; the three cells agree in sign.
- **The other-metals half is about zero.**
- **POST HOC, not a finding:** the inverse filter ("fade the AUD-confirmed opens") would sit at about +0.03 to +0.05.
  That is at or below break-even, and it was found after the run. Recorded so it is not re-derived.

## 3. U's book: all four groups (the filtered fade; one micro)

| | MGC | SIL | MHG |
|---|---|---|---|
| trades | 486 | 470 | 470 |
| **mean gross / net** | **+\$2.97 / −\$2.96** | **+\$4.60 / −\$3.40** | **+\$0.32 / −\$3.93** |
| t gross / t net | 1.31 / −1.31 | 0.72 / −0.54 | 0.12 / −1.43 |
| Sharpe net / gross; Sortino net | −0.50 / +0.50; −0.73 | −0.21 / +0.28; −0.32 | −0.55 / +0.05; −0.73 |
| max drawdown | \$1,747 | \$2,790 | \$2,688 |
| mean \|gross\| against 2c | \$35.20 (3.0×) | \$87.72 (5.5×) | \$41.64 (4.9×) |
| breakeven cost; thin-book net | \$2.97; −\$4.96 | \$4.60; −\$13.40 | \$0.32; −\$6.43 |
| median net; win rate; payoff | −\$6.93; 45.9%; 1.00 | −\$8.00; 46.4%; 1.07 | −\$3.00; 46.6%; 0.95 |
| skew; kurtosis | 1.00; 7.1 | 1.75; 14.4 | −0.22; 5.5 |
| net ex-top 1% / ex-bottom 1% / trimmed | −5.22 / −1.49 / −3.75 | −11.08 / +1.27 / −6.44 | −6.24 / −1.39 / −3.70 |
| profitable years; net without the best two | 2 of 7; −\$1,826 | 1 of 7; −\$2,748 | 3 of 7; −\$2,444 |
| **B1, the largest month-share gap; year gap** | **1.4 pts; 2.7 pts** | **2.1; 1.6** | **1.4; 2.2** |
| **B2, net outside Dec–Mar (n)** | **−\$1,880 (340)** | −\$1,062 (324) | −\$1,309 (316) |
| Dec–Mar net (n) | +\$439 (146) | −\$538 (146) | −\$536 (154) |
| EDT / EST mean net | −\$6.72 / +\$4.90 | −\$5.63 / +\$1.69 | −\$2.07 / −\$7.80 |
| largest trades | 2022-03-08 +\$337; 2020-03-18 −\$207 | 2020-07-27 +\$1,032; 2020-08-05 −\$613 | 2020-03-18 +\$300; 2022-03-08 −\$349 |
| ρ with D737's twin / NQ F2 / C1 | +0.08 / +0.08 / −0.03 | +0.03 / +0.03 / +0.00 | −0.03 / −0.04 / +0.04 |

- **The principal's balance requirement held as designed:** the selected trades sit across the calendar like the pool
  (within 1.4–2.1 points). There was simply no edge for the balance to carry.
- **Gold's book still earns only in EST** (+\$4.90 against −\$6.72). July–October average −\$10 to −\$13 a trade.
  This is D765's season pattern again, and B2 fails on it.
- **The reported single parts:**
  - F3 alone: −\$3.52 / −\$2.76 / −\$3.68 net;
  - F4 alone: −\$2.27 / −\$6.69 / −\$3.07;
  - the unfiltered fade: −\$2.79 / −\$1.99 / −\$1.97.
  - **No variant beats taking every trade by enough to matter, and none is net positive.**
- **The secondary on silver** (+\$18.44 net, 97 trades, t 1.03, rank 0.81 in its rotation) is inside its null, and
  three trades carry it. It is not read.

## 4. The reading

- **Declared:** MGC **NOT ABOVE NULL**; SIL and MHG **NO MECHANISM**; the secondary the same. GO false.
- **What was learned:**
  1. **"News against flow" via the AUD does not sort the China open's reversals,** and if anything runs the other way.
     The confirmed opens are the ones that give back slightly more.
  2. **The oracle's winners are spread evenly across the year, and an honest filter can select evenly.** U did:
     the principal's balance design works as a guard. But no outcome-free signal tried here finds those winners.
  3. **D765's reversal stays what it was:** real on gold, about half a micro's round trip, and seasonal in-sample.
- **Recommendation:** close the China-open line (D765 and D767) for the prop book. Closing it is the principal's call.
