# D512 RESULT — CLOSE, but the closest a conditioner has come: range expansion survives the within-year control that killed the stretch, and the contamination I designed the primary around turns out to be negligible

**Result of D512** (spec `711bbe3`). Runner `scripts/run_d512_range_expansion.py --run`
(`--selftest` passes, five checks; 0.1 min), artefact `data/d512_range_expansion.json`.
**1,876 sessions, 2016-01-04 → 2023-12-29.** The arm is imported and reproduces D504's published
per-year figures exactly (1,876 sessions, $15,423); the reshaped high/low grid is asserted to sit on
build's own sessions and its closes to equal build's `level`. The 2024+ slice was never scored.

## 0. The verdict, and why it is closer than the last two

**CLOSE by the pre-registered rule.** The declared primary — the day-session **log** range version —
reads **Δ = +$25.37 a session** against a rotation p95 of **+$27.54**, the **93.4th percentile**.
It misses by $2.17.

| cell | Δ, $/session | top | bottom | N1 p05 | N1 p50 | N1 p95 | percentile | clears N1 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **day-session, log range (primary)** | **+25.37** | +16.36 | −9.00 | −22.31 | −1.34 | +27.54 | 93.4th | **no** |
| day-session, point range | +21.54 | +17.03 | −4.50 | −23.03 | −2.49 | +30.62 | 87.9th | no |
| **23-hour, log range** | **+31.27** | +22.99 | −8.28 | −21.61 | −1.67 | +26.92 | **98.6th** | **yes** |
| 23-hour, point range | +23.70 | +20.18 | −3.52 | −23.24 | −2.09 | +28.72 | 90.2nd | no |

**N2 family maximum**, four cells, 1,875 common offsets: p50 +$3.20, **p95 +$32.92**, observed
maximum **+$31.27** — **6.0% of offsets beat the best real cell.** So the family refuses it, and
refuses it *narrowly*: p ≈ 0.06 rather than the 0.40 and 0.58 the two stretch records returned.

**The best cell is one I declared secondary, and picking it now would be selection.** The 23-hour
version clears its own N1 at the 98.6th percentile. It is reported, it is not promoted, and the
family bar — which is the multiplicity-correct statistic and does not care which cell I called
primary — refuses the whole set at 6.0%.

## 1. What is genuinely different about this conditioner

**It survives the control that killed the last two.** D508 and D509 both found the 200-day stretch
reversed sign between the pooled and the within-year read (−$10.71 within against +$13.82 pooled,
negative in seven years of eight). Range expansion does the opposite:

| 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | mean | pooled |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| +14.5 | +5.8 | +37.4 | −0.8 | +64.7 | **+97.6** | −16.0 | +16.2 | **+27.42** | **+25.37** |

**Positive in six years of eight, and the within-year mean (+$27.42) slightly exceeds the pooled
figure (+$25.37).** This is not a year proxy. It is the first conditioner tested on this arm that
holds up once the year is held fixed, and that is the substantive result of the record.

**And the shape is a threshold, not a ranking.** Net dollars per session by quintile of the primary:

| q1 | q2 | q3 | q4 | q5 |
|---:|---:|---:|---:|---:|
| **−9.00** | +0.50 | +16.01 | +17.28 | +16.36 |

Monotonicity +0.90, but the top three quintiles are flat at +$16 to +$17 and the work is done at the
bottom: **when the recent range is compressed against its own long-run level, the arm loses $9.00 a
session.** Quintile 1's net Sharpe is **−1.08** and its gross per trade is **−$5.27**, so it is
losing before costs, not because of them. The reading is "this arm needs range expansion and bleeds
without it", not "more expansion is better".

## 2. The prediction I got most wrong, and it was the premise of my own design

**X-a: I refused to run the principal's literal point-range construction as the primary, on the
grounds that a point range on a rising market measures price rather than volatility.** The selftest
proves the mechanism exists: a constant *percentage* range on a steadily rising market gives the
point version a mean V of **+0.088** while the log version stays flat at **6e-15**.

**In this data the contamination is negligible.**

| cell | ρ(V, log price) |
|---|---:|
| day-session, point range | **+0.009** |
| 23-hour, point range | +0.019 |
| day-session, log range | −0.017 |
| 23-hour, log range | −0.008 |

I predicted the point versions would correlate with log price above +0.35. They correlate at +0.01
to +0.02. **The reason is that the ratio is self-normalising and the range's own noise swamps the
drift**: my synthetic had a clean exponential trend and *zero* range noise, so it isolated an effect
that the real series buries. The point and log versions differ by $3.83 a session on Δ, well inside
the null's width.

**So the principal's construction as originally written was fine**, and my substitution neither
helped nor hurt. The right lesson is not "always use the log range" but **"demonstrate a suspected
contamination on the data before redesigning around it"** — the measurement took one line and would
have saved the redesign.

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | point ρ > +0.35, log \|ρ\| < 0.20 | point **+0.019**, log 0.017 | **wrong on the premise of the design** (§2) |
| X-b | primary Δ in [+$5, +$25] | **+$25.37** | marginally outside, at the top edge |
| X-c | N1 p95 in [+20, +35]; Δ does not clear | p95 **+27.54**; does not clear | right |
| X-d | within-year mean below +$5, negative in ≥ 5 of 8 | **+27.42**, negative in **2 of 8** | **wrong, and it is the informative miss** (§1) |
| X-e | day-session and 23-hour agree within $6 | **$5.91** | right, just |
| X-f | the verdict is CLOSE | CLOSE | right |

## 4. What stands

- **CLOSE recommended** on the declared primary; the principal closes. The family bar refuses the set
  at 6.0%, which is a refusal and a narrow one, against 40% and 58% for the two stretch records.
- **This conditioner is different in kind from the 200-day stretch.** It is not a year proxy, it
  survives stratification, and its bottom quintile loses **gross**. Those three facts are the record.
- **It cannot be pursued on this arm**, which has no unread slice on NQ (D503). **The place to carry
  it is a construction or a root that still has one** — the six roots whose 2024+ is unread, or any
  future candidate — where a declared 23-hour cell could be tested properly rather than promoted
  after the fact.
- **A method note worth keeping**: demonstrate a suspected contamination *on the data* before
  redesigning around it. Mine was real in a synthetic with no noise and worth +0.01 in the series.
- **Nothing spent.** 2024+ was never scored.

## 5. Files

Runner · this record · the artefact · D508 and D509 (the stretch versions) · PICKUP.

---

## ADDENDUM, 2026-09-13 — the 23-hour version is NOT better. Its advantage is nine sessions

**The principal asked why the 23-hour cell beat the day-session one. It does not.** Diagnostic:
`working/d512_why_23h_scratch.py`, a decomposition of this record, no new data read.

**They are the same object.** ρ(V_day, V_full) = **+0.9888**, Spearman **+0.9817**. A night-only cell
sits between them at Δ +26.15 (95.4th percentile), so there is no "the night carries it" story
either: day, night and 23-hour are one conditioner measured three ways.

**The gap is inside its own noise.** Rotating BOTH conditioners by the *same* offset preserves their
correlation and asks how large a gap arises by chance:

| | value |
|---|---:|
| observed gap, 23-hour minus day | **+$5.91** a session |
| null gaps, p05 / p50 / p95 | −8.81 / +0.33 / +7.83 |
| standard deviation of the null gap | $5.11 |
| where the observed gap sits | **89.5th percentile** |
| offsets with \|gap\| at least as large | **23.1%** |

**The gap is 1.2 standard deviations of what rotation alone produces.**

**And it is carried by nine sessions.** The two conditioners assign the same quintile to **83.5%** of
sessions, and the top quintiles share **366 of 375**:

| | n | mean net | total |
|---|---:|---:|---:|
| sessions the 23-hour version ADDS to the top quintile | **9** | **+$120.88** | +$1,088 |
| sessions it DROPS from the top quintile | **9** | **−$155.39** | −$1,399 |

The top-quintile mean moves from +$16.36 to +$22.99, which is **$2,486** across 375 sessions. The
eighteen swapped sessions account for **$2,487** of it. **The entire advantage is those nine swaps.**
The three largest additions are **2022-07-18 (+$470), 2020-02-28 (+$371) and 2016-01-13 (+$220)**.

**What this corrects in this record.** §0 reported that the 23-hour cell "clears its own N1 at the
98.6th percentile". That remains arithmetically true and is **not evidence of a better conditioner**:
the cell differs from the declared primary on nine of 375 top-quintile sessions, and the difference
is ordinary under rotation. **The right reading of §0 is that all four cells are one conditioner, the
family bar refuses it at 6.0%, and the spread between the cells is noise.** This is the repo's own
rule about a sparse contaminant dominating an order statistic, arriving from the other direction:
nine sessions moved a cell from the 93rd percentile to the 98th.

**Nothing changes in the verdict.** CLOSE stands, for a better-understood reason. And the §4
forward pointer is sharpened: what should be carried to a root with an unread slice is **the
conditioner**, declared once on whichever window is chosen in advance — not a choice between day,
night and 23-hour, which this addendum shows is a choice between three names for one thing.
