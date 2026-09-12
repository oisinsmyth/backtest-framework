# D492 RESULT (development) — the hourly RSI confirmation removes three quarters of the trades and leaves the rest at zero, below a stale-range control on both roots; no validation read

**Development result of the declared filter set in D492 (hourly RSI, per the addendum committed
before the run).** Runner `scripts/run_d492_rsi_filter.py --dev` (`--selftest` passes; 4.1 min),
artefact `data/d492_rsi_filter_dev.json`, trade files per root and cell. **Development slice only,
2016-02-01 → 2020-12-31; the validation and final slices are untouched, and the runner refuses a
validation read because no cell cleared.**

## 0. The numbers

| one micro, $3 + fills, development | trades (share of sessions) | gross $/trade | median | hit | exits target / trail / close | net Sharpe (SE) | N1 wrong-range p50 / p95 | bar |
|---|---:|---:|---:|---:|---|---:|---:|---|
| **ES cell A** (rule + RSI ≤ 30 / ≥ 70) pooled | 287 (23%) | **−0.88** | −3.75 | 47.0% | 1 / 6 / 93% | **−0.30 (0.38)** | +1.75 / +3.46 | not cleared |
| ES A long / short | 92 / 195 | −1.88 / −0.41 | +16.88 / −7.50 | 55.4% / 43.1% | | −0.14 / −0.38 | | |
| ES cell B (RSI in place of the spike) pooled | 305 (25%) | −1.94 | −1.25 | 48.5% | 2 / 7 / 91% | −0.40 (0.38) | +0.76 / +2.14 | not cleared |
| **NQ cell A** pooled | 338 (28%) | +1.57 | −5.25 | 45.3% | 2 / 7 / 91% | −0.11 (0.42) | **+5.36 / +6.31** | not cleared |
| NQ A long / short | 99 / 239 | +4.10 / +0.52 | −5.00 / −5.50 | 46.5% / 44.8% | | +0.03 / −0.21 | | |
| NQ cell B pooled | 371 (30%) | +4.49 | −2.50 | 47.2% | 3 / 9 / 88% | +0.12 (0.40) | **+5.85 / +7.40** | not cleared |

For reference, D490 without the filter: ES −$3.48 (−1.14), NQ −$4.96 (−1.03).

## 1. What the filter did, and what it did not

- **It removed trades, not losses.** The hourly RSI keeps 287 of D490's 1,113 ES trades (−74%,
  against my 50–70% prediction). The kept trades are at zero on ES (−$0.88, a 1%-trimmed
  −$0.10) and slightly positive on NQ (+$1.57), which is $2.60 and $6.50 a trade better than the
  unfiltered rule. **None of that improvement is a positive edge:** on both roots the rule sits
  **below the wrong-range control** (ES +1.75, NQ +5.36 at the median of 20 stale ranges),
  meaning the same mechanics with an arbitrary level do as well or better than yesterday's
  actual extreme even after the RSI confirmation.
- **The target is inert.** It is reached on 0–3% of trades; 88–97% ride to the close. With the
  RSI confirmation the rule is, in practice, "buy an oversold print at yesterday's low and hold to
  the close". Both sides have a negative median with the long side's mean held up by a few
  large days (ES long median +$16.88 on 92 trades, mean −$1.88; NQ long median −$5.00, mean
  +$4.10).
- **The trail costs money again.** No-trail pooled: ES A +$0.41 against −$0.88; NQ B +$5.00
  against +$4.49; hit rates unchanged to a point. The other session's neutrality result holds a
  third time.
- **The sample is now too small to learn from.** 92 long trades on ES give a standard error near
  $16 a trade; the descriptive splits are all inside their SE (the largest, NQ long with the open
  inside yesterday's range, +$36 on an SE of 21, n 46). No split is a candidate filter, and a
  second filter on top of this one would be a cell chosen from noise.

## 2. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a the RSI removes 50–70% of trades | | **74–77%** on ES, 70% on NQ | more than predicted |
| X-b sign unchanged; A long −$6 to +$2, short −$6 to 0, Sharpe −0.8 to 0 | | −1.88, −0.41, −0.30 | right |
| X-c B better than A by $2–6; not above N1 p95; Sharpe −0.4 to +0.2 | | ES: B **worse** (−1.94 vs −0.88); NQ: B better (+4.49 vs +1.57); neither above N1 p95; Sharpe −0.40 / +0.12 | half right |
| X-d bar not cleared, no validation read | | not cleared; refused | right |

## 3. What stands

- **No cell goes to validation.** The declared rule for the read was a cleared development bar;
  none cleared, and the runner refuses the 2021–2023 slice. Both reserves are intact.
- **The range-reversion family on the index, as the principal specified it, has now failed
  twice on the same development data for the same reason:** the entry state — a print at
  yesterday's extreme — is not where the intraday reversion lives, and confirming it with an
  oscillator that measures the same stretch does not change what the level is. The stale-range
  control is the decisive fact on both records: the level carries no information the mechanics do
  not already have.
- **What would be a different construction rather than another filter:** the next-session
  reversal after a large day (D487's one clean cross-year statistic, on NQ), or a quiet drift to
  the extreme without a spike. Either is a new premise check, not a validation read.

## 4. Files

Runner · four trade files · the development artefact · this record.
