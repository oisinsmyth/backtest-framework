# D727 STAGE 0 RESULT — NQ's move since the open continues into the rest of the day at every clock (strongest at 10:00), RECOGNISABLE FROM 14:30 by the declared rule; it DOES NOT TRANSFER (YM reverses in the morning, RTY continues only partly); the practical book pays on NQ (first |z| ≥ 1.5: +$19.29 gross / +$15.22 net a MNQ, net Sharpe +0.83), so GO is false on transfer alone

*2026-10-01. The runs:*
- *one run of `scripts/stage0_d727_trend_curve.py` (0.2 min, `--data-root` the main checkout);*
- *one POST HOC overlap check (`scripts/diag_d727_overlap.py`), declared below as post hoc.*

**The order:** the [pre-registration](D727-STAGE-0-PRE-REG-the-trend-detection-curve.md) was committed first, and the
runner (`09584c15`) before the run.

**The data:**
- NQ 1,941 sessions (2016-02 → 2023-12), YM 1,938, RTY 1,557 (from 2017-08);
- roll days excluded;
- nothing dated 2024-01-01 or later read.

**The audits:**
- the lag audit (a second implementation from raw rows) passed on 45 samples per root, and its canary fired;
- the x + y identity held;
- the self-test shows the audit catching D724's wrapped index;
- the self-test shows a within-day permutation reproducing a day-level drift, which is why it is not the null.

**The output:** `data/stage0_d727_trend_curve.json` and `data/diag_d727_overlap.json`.

## 1. The curve: β_t, the slope of the rest of the day on the move since the open

The null is the enumerated cross-day rotation: one day's morning against another day's afternoon.

| clock | NQ β (NW t) | NQ rank | NQ reading | YM β (rank) | RTY β (rank) | trend-day move still to come (NQ) |
|---|---|---:|---|---|---|---:|
| 10:00 | **+0.130 (+2.23)** | 0.997 | **CONTINUATION** | −0.029 (0.29) | **+0.120 (0.995)** | 79% |
| 10:30 | +0.057 (+1.41) | 0.957 | NONE | −0.022 (0.27) | +0.073 (0.984) | 67% |
| 11:00 | +0.014 (+0.40) | 0.709 | NONE | −0.047 (0.07) | +0.042 (0.93) | 57% |
| 11:30 | +0.032 (+1.02) | 0.927 | NONE | −0.017 (0.25) | +0.029 (0.88) | 49% |
| 12:00 | +0.023 (+0.91) | 0.876 | NONE | −0.005 (0.40) | +0.021 (0.84) | 43% |
| 12:30 | +0.037 (+1.64) | 0.981 | NONE | −0.000 (0.49) | +0.011 (0.71) | 38% |
| 13:00 | +0.030 (+1.49) | 0.968 | NONE | −0.005 (0.39) | +0.007 (0.66) | 34% |
| 13:30 | **+0.050 (+2.66)** | 0.999 | **CONTINUATION** | +0.014 (0.79) | +0.013 (0.80) | 30% |
| 14:00 | +0.024 (+1.56) | 0.965 | NONE | +0.002 (0.55) | +0.009 (0.74) | 24% |
| 14:30 | **+0.031 (+2.13)** | 0.995 | **CONTINUATION** | +0.013 (0.85) | +0.014 (0.89) | 20% |
| 15:00 | **+0.034 (+2.63)** | 1.000 | **CONTINUATION** | +0.017 (0.95) | **+0.026 (0.995)** | 15% |

- **On NQ, β is positive at all eleven clocks** (ranks 0.71–1.00). Wherever NQ is relative to its open, the rest of
  the day tends to go the same way.
  - The strongest point is 10:00: the first half hour's move continues to the close.
  - That is the opposite of ES, where D487 found the first half hour reversing into the last.
- **The declared reading is RECOGNISABLE FROM 14:30.** 14:30 and 15:00 are the first pair of consecutive
  CONTINUATION clocks; 10:00 and 13:30 are isolated. This is NQ F2's own clock: the last-hour continuation is the end
  of this curve.
- **Transfer: DOES NOT TRANSFER.** At NQ's four CONTINUATION clocks:
  - RTY ranks ≥ 0.90 at two (10:00, 15:00), and a majority was needed;
  - YM ranks ≥ 0.90 at one (15:00).
- **YM is the opposite in the morning.** β is negative from 10:00 to 13:00 (rank 0.07 at 11:00): the Dow's early
  move reverses.
- **RTY looks like NQ in the morning** (10:00 and 10:30 are both CONTINUATION), then fades. It is the partial echo,
  not a transfer.

**Detection against the oracle's trend days** (the top third of |C − O|/σ_oc within each year), for |z_t| ≥ 1:

| | 10:00 | 14:30 |
|---|---:|---:|
| precision (vs a base rate of 0.33) | 0.37 | 0.80 |
| recall | 0.55 | 0.74 |
| share of the trend day's move still to come | 79% | 20% |

**Early knowledge is weak, and certain knowledge comes late. That is the trade-off the principal named.**

## 2. The money (one micro: MNQ $4.07, MYM $3.80, M2K $3.76; held to 15:59)

**The practical book:** the first clock at which |z_t| ≥ k, going with the drift.

| root, k | trades | gross (median) | net | net Sharpe (Sortino); gross Sharpe | max DD | years + | largest year | the oracle ceiling (gross) |
|---|---:|---|---:|---|---:|---|---:|---:|
| **NQ, 0.5** | 1,884 | +$7.81 (+$5.50) | +$3.75 | +0.27 (+0.39); +0.57 | $6,716 | 4/8 | 76% | +$201.77 (536) |
| **NQ, 1.0** | 1,505 | +$11.21 (+$8.00) | +$7.14 | +0.47 (+0.66); +0.74 | $5,021 | 5/8 | 59% | +$175.74 |
| **NQ, 1.5** | 1,024 | **+$19.29 (+$8.75)** | **+$15.22** | **+0.83 (+1.21)**; +1.05 | $4,131 | 5/8 | 41% | +$152.69 |
| YM, 0.5 / 1.0 / 1.5 | 1,880 / 1,450 / 986 | −$2.99 / −$3.84 / −$1.72 | −$6.79 / −$7.64 / −$5.51 | −1.04 / −0.98 / −0.58 | — | 2/8, 1/8, 1/8 | — | +$72–93 |
| RTY, 0.5 / 1.0 / 1.5 | 1,531 / 1,292 / 930 | +$1.94 / +$3.27 / +$2.28 | −$1.82 / −$0.49 / −$1.48 | −0.31 / −0.08 / −0.20 | — | 4/7, 5/7, 2/7 | — | +$69–91 |

- **NQ at k 1.5, the trade distribution:**
  - win 51%, skew −0.32;
  - means: ex-top 1% +$7.91, ex-bottom +$23.84, both trimmed +$16.53.
  - It is not a tail book: the median is +$8.75.
- **NQ at k 1.5, when it enters:** 62% at 10:00, 16% at 10:30.
- **NQ at k 1.5, by year:**
  - net 2016 −$197, 2017 −$537, 2018 +$2,132, 2019 −$508, 2020 +$2,732, 2021 +$3,268, 2022 +$6,325, 2023 +$2,374;
  - weak in the calm low-volatility years (2016, 2017, 2019); 2022 is the largest share at 41%.
- **The max drawdown at one MNQ is $4,131.** That is more than a $50k account's 4% trailing barrier, but fits a
  $150k one.
- **NQ's ceiling (+$150–200 a trend day) dwarfs every real book.** The detection problem is unsolved; what pays is
  the average continuation, not trend-day recognition.
- **k was not chosen.** All three are reported, and k 1.5 is the best of the three after the fact: a selection, if
  anyone builds on it.

**GO is false:** NQ is RECOGNISABLE and its practical book grosses ≥ 2 × $4.07 with net > 0, but the curve DOES NOT
TRANSFER.

## 3. POST HOC (declared: computed after the readings, changes none of them)

The overlap with the ledger's NQ components, on the common 1,941 sessions:

| NQ book | ρ with the MACD arm | ρ with NQ F2 | days shared with the arm | the arm + this book, net Sharpe (arm alone 0.69) |
|---|---:|---:|---:|---:|
| k 1.0 | +0.22 | −0.09 | 88% | 0.74 |
| k 1.5 | +0.24 | −0.10 | 88% | 0.96 |

- Despite trading on 88% of the arm's days, the book is only weakly correlated with the arm and slightly negatively
  with NQ F2. The arm enters later and exits on its own signal; this holds to the close from the first threshold.
- In-sample, it would be a distinct component.

## 4. What it says

1. **On NQ, the trend is recognisable early in a weak, average sense, not in a trend-day sense.** The move since the
   open predicts the rest of the day at every clock, from 10:00. But at 10:00 that is precision 0.37 for a trend
   day, against a base of 0.33. The money comes from many modest continuations, not from catching the big days.
2. **It is NQ's alone.** YM reverses in the morning; RTY echoes NQ in the morning only. The lesson of D474/D475 and
   the transplanted arm (D513) holds: NQ trends; the other index roots do not, or not the same way.
3. **The practical NQ book is the best new in-sample number in this line:** net Sharpe 0.83 at one MNQ, a median
   above the fee, ρ 0.24 with the arm. But it failed its declared transfer test, and its k is a choice among three.
4. **Confirmation is the open problem.**
   - NQ's 2024+ is unread for this question, but it holds the last hour, which is D716's joint-vault look.
   - The only clean confirmation is a separate vault pre-registration: a new family, in programme slot 10 (free),
     with k fixed in advance and its power computed first. **That needs the principal's explicit, separate word.**
   - The alternative is step 2 (cross-asset agreement), which may explain why NQ continues and the Dow does not.
5. **Proposed, not decided:**
   - (a) a vault pre-registration for NQ's open-drift follow, slot 10, on the principal's word;
   - (b) step 2 first;
   - (c) close.
