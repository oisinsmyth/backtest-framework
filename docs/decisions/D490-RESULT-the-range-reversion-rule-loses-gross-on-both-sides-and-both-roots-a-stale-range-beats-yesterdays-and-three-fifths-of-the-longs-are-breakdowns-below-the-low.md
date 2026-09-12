# D490 RESULT (development) — the range-reversion rule loses gross on both sides and both roots; a stale range beats yesterday's; three fifths of the longs are breakdowns below yesterday's low

**Development result of the pre-registered rule in D490.** Runner `scripts/run_d490_range_reversion.py --dev`
(`--selftest` passes, including trade-for-trade agreement of the scalar simulator and the
vectorised exit table on real sessions; 2.1 min), artefacts `data/d490_range_reversion_dev.json`,
`data/d490_trades_dev_{ES,NQ}.csv.gz`. **Development slice only, 2016-02-01 → 2020-12-31, 1,225
full sessions per root; the validation (2021–2023) and final (2024+) slices are untouched.**

**The bar is not cleared, on either root, and not narrowly.**

## 0. The numbers

| one micro, $3 + fills | trades | share of sessions | gross $/trade | median | hit | payoff | exits target / trail / close | MAE p50 / p95 / worst | net Sharpe (SE) |
|---|---:|---:|---:|---:|---:|---:|---|---|---:|
| **ES long** | 491 | 40% | **−2.70** (−1.5 bp) | +10.00 | 57.6% | 0.66 | 4 / 22 / 74% | −39 / −237 / −538 | −0.60 (0.42) |
| **ES short** | 622 | 51% | **−4.09** (−3.6 bp) | −6.25 | 45.0% | 1.01 | 6 / 14 / 80% | −33 / −152 / −640 | −1.03 (0.38) |
| ES pooled | 1,113 | 85% | −3.48 | +1.25 | 50.6% | 0.84 | 5 / 17 / 78% | | **−1.14 (0.38)** |
| NQ long | 465 | 38% | −5.43 (−3.1 bp) | +11.50 | 55.5% | 0.70 | 3 / 22 / 75% | −52 / −344 / −1,010 | −0.63 (0.42) |
| NQ short | 645 | 53% | −4.62 (−3.3 bp) | −5.00 | 46.8% | 0.98 | 6 / 13 / 81% | | −0.82 (0.31) |
| NQ pooled | 1,110 | 85% | −4.96 | +1.25 | 50.5% | 0.85 | 5 / 16 / 79% | | **−1.03 (0.33)** |

Net of the $3, every line is worse by $3. By year on ES the pooled net Sharpe is −1.48, −1.41,
**−2.51 (2018)**, −1.78, −0.01 (2020). No day below −2% of a $50k account at one micro.

## 1. What the nulls say, and it is the unusual direction

| ES, gross $/trade | the rule | N1 wrong-range control (yesterday's range replaced by one 3–22 sessions old) | N2 random entries, same exits |
|---|---:|---:|---:|
| pooled | **−3.48** | p50 **+0.10**, p95 +1.23 | p50 −7.55, p95 −5.77 (SE 0.05) |
| long | −2.70 | long p95 +4.57 | long p95 −3.16 |

**The rule is below the wrong-range control.** Running the identical mechanics against a stale
range, which turns "yesterday's extreme" into an arbitrary level, produces a mean of about zero;
using yesterday's actual extreme produces −$3.48. The specific level is where the losses come
from. NQ is the same shape (rule −4.96; N1 p50 +0.03, p95 +2.27). The rule does beat random
entries with the same exits (N2 p50 −7.55): the exit machinery on its own loses, because a
target at the far side of the range is reached on 5% of trades and the other 95% ride to the
close or a trailing stop. **Both nulls point the same way: the entry state is not a reversion
state, and the exits do not manufacture one.**

## 2. Why, read from the trades

- **Three fifths of the long entries are below yesterday's low** (296 of 491 on ES have `P < 0`),
  and the rule requires a volume spike at that moment. A price under yesterday's low on twice the
  usual volume is a breakdown with the flow behind it, not a stretched tape. The in-band entries
  (`0 ≤ P ≤ 0.05`) are no better (−$4.4, SE 5.6). Shorts at the top are the mirror and worse
  (45% hit), because the index drifts up against them.
- **The distribution is exactly the one P1 punishes.** Long median +$10 against a mean of −$2.70,
  skew −1.5, worst MAE −$538: a high hit rate paid for by a fat left tail, the trend days. The
  trail improves the hit rate (57.6% vs 55.6%) and lowers the mean (−2.70 vs −1.05), as the other
  session's neutrality result said it would; it does not change the sign.
- **The target is almost never reached** (4–6%). The rule is, in practice, "buy the breakdown and
  hold to the close", and D487 told us the close does not tend to be at the far side of the
  range on those days.
- **2018 is the worst year** (−2.51), the year D487 found the most intraday continuation. The
  rule is a short-continuation bet, and it loses most where continuation lives.

## 3. The splits, for the principal's filter question

Every split is within about 1.3 SE of zero; none is a signal worth a validation read:

| ES, gross $/trade (SE, n) | long | short |
|---|---:|---:|
| `P < 0` / in-band | −1.6 (6.1, 296) / −4.4 (5.6, 195) | — / −4.1 (3.1, 622) |
| spike 2–3× / > 3× | −4.6 (6.2, 314) / **+0.7** (4.8, 177) | −6.8 (3.4, 465) / **+3.8** (7.2, 157) |
| before / after 11:00 | −2.5 (6.2) / −3.1 (4.4) | −4.3 (4.0) / −3.6 (4.6) |
| open in / outside yesterday's range | −5.0 (5.1) / +0.7 (7.6) | −0.1 (3.9) / −7.3 (4.7) |

NQ agrees on the only positive-looking cell (short on a > 3× spike, +11.6 with SE 9.4) and
disagrees on the rest. **Recorded so the choice is on the record; my reading is that there is no
filter here, only noise around a negative mean**, and a filter chosen from these cells and taken
to 2021–2023 would be D470 again with a worse base.

## 4. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a long 35–50% of sessions, short 25–40% | | 40% / **51%** | shorts trigger more than I expected: the index sits at the top of yesterday's range half the time |
| X-b long +3 to +10 bp, hit 52–58%, short +0 to +5 bp, long median < mean | | **−1.5 bp**, 57.6%, **−3.6 bp**, median **above** the mean | wrong sign both sides; the tail is on the left |
| X-c trail raises hit, lowers mean, Sharpe within ±0.1 | | 50.6 vs 48.8%; −3.48 vs −2.71; −1.14 vs −0.97 | right |
| X-d N1 within 2 bp of the rule; long clears N2 | | N1 **above** the rule by $3.6; long above N2 by $0.5 (inside 2 SE) | wrong direction |
| X-e Sharpe +0.1 to +0.4; 2018 worst | | **−1.14**; 2018 worst | worse than predicted; 2018 right |
| X-f `P < 0` worse; after 11:00 better | | `P < 0` better (−1.6 vs −4.4); after 11:00 no better | wrong |

## 5. What stands

- **The rule as stated is not a candidate and does not go to the validation slice.** The bar was
  declared; it fails by a wide margin; the nulls say the entry level is the problem.
- **The validation and final slices are intact** for a different construction on this family.
- **What the trades suggest, without being a test of it:** the entry that would sit on the
  reversion D487 found is not "at yesterday's extreme on a spike" (that is flow) but the
  opposite, a quiet stretch to the extreme; and the mechanism paper's intraday reversal is on
  the *next day*. A construction on either is a new record with its own premise check.

## 6. Files

Runner · two trade files · the development artefact · this record.
