# D677 PRE-REGISTRATION — month-end rebalancing flow: does a 60/40 portfolio's month-to-date drift predict ES over the last five trading days of the month?

*Drafted 2026-09-29 on the principal's word ("Write, build then run it please"). Committed alone, before its runner
exists (R8). **No return of ES, ZN or any root has been read for this construction.** For the power check, and
nothing else, the daily σ of ES, ZN and ES−ZN was measured on same-contract settlements, 2010–2023. Both books; it
measures, and admits nothing without a later confirmation.*

## 0. The mechanism, and why this is a test rather than a search

**The mechanism is deterministic and public.** Pension funds, balanced funds and target-date funds hold fixed
stock/bond weights and rebalance on the calendar, at month-end. When equities have outperformed bonds over the month,
their equity weight has drifted above target, so they must sell equities and buy bonds into month-end. The flow is
predictable in sign and roughly in size before it trades. Front-runners and early rebalancers act on it in the last
days of the month.

**The published measurement.** Harvey, Mazzoleni and Melone, *The Unintended Consequences of Rebalancing*
(NBER w33554, SSRN 5122748, 2025), sample 1997–2023, as the NBER page and two public reproductions (QuantReturns,
Quantitativo) state it:
- a one-SD rebalancing signal predicts about **−17 bp for equities over the next day**;
- the calendar effect becomes significant about **five trading days before month-end**;
- it reverses within about two weeks;
- the reproductions report Sharpe ratios of 0.94 to 1.42 for scaled futures.

**The paper's own tables were not read**: the PDF could not be parsed here. That is disclosed, and the signal below is
the construction the paper and both reproductions describe.

**Why this is a test.** The construction is fixed from the publication before any return is read. Nothing in this
record's window has been read for this idea (§7). This is a replication on futures, not an independent discovery: the
window overlaps the paper's sample.

**Power (computed before drafting, from measured σ, assuming the published effect).** 17 bp against ES's daily σ of
107.5 bp gives about 0.16 per active day:

| slice | active days | expected t, full effect | expected t, half |
|---|---:|---:|---:|
| this record, 2010-07 → 2023-12 | ~810 | 4.5 | 2.3 |
| 2024-01 → 2025-02 (unread) | ~70 | 1.3 | 0.7 |
| 2024-01 → 2025-02 plus the joint-run vault | ~160 | 2.0 | 1.0 |

So this record can decide the question in-sample. Confirmation would need the clean slice together with the vault in
the joint run.

## 1. Data

- **Settlements:** `fut_settle_strip.csv.gz` (every listed month's settlement, 2010-06-07 →), read from
  `--data-root`.
- **The front:** the `front` column of `fut_curve_front_next.csv.gz`, the breadth fixture's front election.
- **Roots:** ES is primary. ZN is the bond leg and a secondary outcome. NQ, YM and RTY are reported only.
- **Trading days:** days on which both ES and ZN publish a front settlement. A day on which either publishes none is
  a holiday for this record (data-available.md: a missing settlement is the root's exchange holiday).
- **Returns are same-contract.** Day t's return on root X is `log S_t(c) − log S_{t−1}(c)`, where c is X's front at
  day t−1 (the contract held overnight into t) and t−1 is the previous trading day. A roll never enters a return.
- **Window:** signal months 2010-07 → 2023-12. June 2010 is partial, so the first month with a full prior month-end
  is July. **No settlement dated on or after 2024-01-01 is read.** A guard raises if one survives the filter.
- **Costs:** from `data/futures_costs.json`, the house convention: a $3 round-trip commission on micros and $6 on
  full size, plus the measured crossing (`d508_exec`) in ticks.
  - A fill at the settlement assumes a trade-at-settlement or a closing fill. ES has TAS; this is disclosed, not
    modelled.

## 2. The signal (as published, with one execution fix)

For calendar month m with trading days `d_1 … d_n` (`T_m = d_n`), the 60/40 portfolio is back at target at the close of
`T_{m−1}`. For a day t in month m:

`G_E(t) = exp(Σ_{u ∈ m, u ≤ t} r_ES(u))`, `G_B(t)` likewise on ZN, `w(t) = 0.6·G_E / (0.6·G_E + 0.4·G_B)`,
`s(t) = w(t) − 0.6`.

**s > 0 means equities are overweight,** so rebalancers sell equities: the predicted sign of the next ES return is
negative.

**Active days.** The outcome days are the last five trading days of the month, `d_{n−4} … d_n`. A position is held
from the settlement of `o − 1` to the settlement of o, for each outcome day o.

**Execution lag (the fix).** The position for outcome day o is set from `s(o − 2)`: the drift through the settlement
before the entry settlement.
- **Why:** the paper trades the close with a signal that includes that close. A futures fill cannot do that, because
  the settlement is not known until it is struck.
- **The unlagged form** `s(o − 1)`, the paper's, is reported beside it as S-UNLAG and gates nothing.
- **Drift across a month boundary:** the drift is measured within o's month. When `o − 2` falls in the previous month
  (months with fewer than 7 trading days before the window, which do not occur), the day is dropped.

**Standardisation.** `z = s / σ_s`, where σ_s is the standard deviation of the lagged s over the active days of the
**prior** 36 months: an expanding window, with at least 12 months before any z exists. It is known before entry. The
slope is reported as bp per 1-SD; the regression t does not depend on the scale.

## 3. Statistics and bars

**Primary outcome:** `y(o) = r_ES(o)`, the same-contract settlement return over outcome day o, in bp.

**Gate 1, the mechanism (gross, unfiltered). It passes only if all three bars hold:**

| bar | statistic | passes when |
|---|---|---|
| **B1** | OLS slope β of y on z over active days, Newey–West t (lag 4) | β < 0 **and** t ≤ −2.0 |
| **B2** | the unfiltered sign book: `g(o) = −sign(s(o−2)) · y(o)`, mean over active days | above the **month-rotation null's p95** |
| **B3** | treatment minus placebo: B2's mean minus the same book's mean on the **placebo days** (`d_{n−14} … d_{n−10}`, mid-month, the same lagged within-month drift) | above the p95 of that difference under the same rotation |

**The null (enumerated, exact).**
- For each offset k, month m's lagged signals are paired with month `m+k`'s outcomes (circularly over the window's
  months). The treatment and placebo days rotate together.
- Every k with `2 ≤ k ≤ M−2` is used: M ≈ 162, so about 160 offsets, and the p95's SE is zero.
- `|k| ≥ 2` is a purge: adjacent months share the reversal the paper reports.
- The statistic at k = 0 is the observed value, computed by the same function.

**B3 is the placebo the house requires:** a flow-driven gain must beat its own placebo at a time the flow does not
trade (the lesson of D631 and D640). If the same drift predicts ES as well in the middle of the month, the effect is
generic month-to-date reversal, not rebalancing flow.

**Gate 2, tradeability (net, filtered by expected profit).** Per the principal's rule, every strategy carries an
expected-profit filter.
- **The size predictor known before entry:** `|z(o−2)|`.
- **Projected gross at entry:** `β̂_prior · |z| · notional`.
  - β̂_prior is the B1 slope estimated only on active days of months strictly before o's month (expanding; a
    24-month burn-in before any filtered trade).
  - Notional is MES's `$5 × S_{o−1}`.
- **Trade** when the projected gross ≥ 2 × MES's round-trip cost, and β̂_prior < 0. Otherwise stay flat.
- **Costs:** positions are ±1 MES. A change of position costs half a round trip per contract changed, so a run of
  same-sign days pays one round trip.
- **Gate 2 passes when:** the filtered book's net mean per active day is > 0 with Newey–West t ≥ 2.0, on at least 60
  traded days. With fewer, it is UNRESOLVED.

**Verdicts:** **SUPPORTED** (Gate 1 and Gate 2) / **MECHANISM ONLY** (Gate 1 alone) / **NOT SUPPORTED** (Gate 1
fails). The filter is promotable only if Gate 1 passes.

## 4. Reported beside, not gated

- **S-UNLAG,** the paper's unlagged signal.
- **Other outcomes:**
  - ZN alone (predicted β > 0: rebalancers buy bonds);
  - ES−ZN at equal notional (the paper's stock-minus-bond return);
  - NQ, YM and RTY each alone (RTY from its first clean month).
- **Quarter-end months against the rest** (quarter-end rebalancing is larger).
- **The reversal:** the slope of the cumulative ES return over the first 10 trading days of month m+1 on the last
  active day's z. Predicted β > 0. December 2023 is excluded, because its window would read January 2024.
- **Eras:** 2010–15, 2016–19 and 2020–23. **Years:** β and the book's gross per year, and the count of positive years.
- **The threshold signal of the paper is not run:** it is a second construction, and the calendar form is the
  mechanism's own clock.

## 5. The component line and the four groups (CLAUDE.md)

For the unfiltered and filtered books, at **MES and at full ES**:
- **Performance:** net and gross Sharpe **and** Sortino, on daily dollar P&L over every trading day (zero when flat)
  and √252, and per traded day by its own count. Also exposure (the share of days in a position), volatility, maxDD,
  the mean move per traded day against 2 × cost, and the breakeven cost per round trip.
- **Trade distribution:** count, mean, median, win rate, payoff, run length in days, skew, kurtosis; and the means
  ex-top-1%, ex-bottom-1% and trimmed 1% at both tails.
- **What the winners depend on:** profitable years; eras; quarter-end vs other; price terciles (cost in bp scales with
  price). There is one root, so name shares do not apply.
- **Correlation with the ledger:** with the admitted MACD arm's daily net P&L (imported through D667's `load_arm`,
  2016-01-04 → 2023-12-29), on the overlapping days.
- **Nulls:** p50 and p95 beside every gated statistic, and the percentile.

## 6. Predictions (mine, before the run)

1. **β < 0** on ES, as published.
2. **The size is smaller than published:** β between −5 and −15 bp per 1-SD, and B1's t between −2 and −4. I expect
   decay since 1997–2009.
3. **The placebo is flat:** its β is within ±5 bp, and B3 passes if B1 does.
4. **ZN's β is positive** (bonds bought).
5. **Quarter-end months have a larger |β|** than the other months.
6. **The reversal's β is positive** over the next 10 days.
7. **If Gate 1 passes, Gate 2 passes:** the cost per MES round trip (~$4) is about a tenth of a 1-SD day's projected
   gross.

## 7. Seals and what this record may read

- **This record reads 2010-06 → 2023-12-29 only.** Two slices stay unread:
  - 2024-01 → 2025-02, which is clean for this line: ES and ZN daily were never read for month-end flow;
  - the programme vault (2025-03-01 → 2026-09-18), joint run only (A10).
- **Other lines have read ES and ZN in this window for other constructions:** D555–D563 (daily trend and carry), and
  intraday studies of ES. They are disclosed here. Under the per-line rule they do not spend this slice.
- **If Gate 1 passes, the confirmation is declared now:** the frozen rule, scored on 2024-01 → 2025-02 together with
  the vault in the programme's joint run. It is not read before then. Expected t at the published effect is 2.0. The
  vault is after the paper's publication, so decay and crowding are live risks there.

## 8. Runner assertions (CLAUDE.md) and self-test

1. **Lag audit.** A second implementation re-derives every position from settlements dated at or before `o − 2`, by
   an explicit loop that never calls the signal function, and must equal the runner's positions exactly.
2. **Sign audit, in money.** A synthetic month in which equities outperform must produce a short MES, and a
   following ES decline must pay positively. Inverting either must raise.
3. **Right quantity.** The outcome must be the same-contract return. On roll days it must differ from the naive
   front-to-front series, and the runner asserts that the two differ somewhere in the window.
4. **Window guard.** No settlement on or after 2024-01-01 is read.
5. **Null identity.** The rotation at k = 0 reproduces the observed statistic exactly.

**Each audit must be able to fail:** the self-test feeds each a broken input and asserts that it raises.

**Output:** `data/d677_month_end_rebalancing.json`, from `scripts/stage0_d677_month_end_rebalancing.py`.
**Projected wall time:** under a minute.
