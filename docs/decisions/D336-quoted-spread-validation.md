# D336 — quoted-spread validation of the estimator convention: the design D332 Part C called for

**Status:** PRE-REGISTERED. Committed **before the script exists** (R8). The selection
rule is D332 Part C's and is not re-derived here. **The pull needs the principal's IBKR
session and is not run by this record's author; the script is built and dry-tested.**
**Date:** 2026-09-05
**Area:** Cost model

---

## 0. Why

D332 found the programme had charged a per-bar Corwin–Schultz median (PB, 14.2 bp
universe median) where the estimator's authors specify a monthly mean (PUB, 31.7 bp),
and that the choice moves the incumbent from +14.57 to −5.16 bp/bar. **Which is true
cannot be decided from OHLC.** Part C declared the test: quoted BID_ASK bars on a
stratified sample of live names, PB vs PUB vs Abdi–Ranaldo, **selection by lowest
median absolute error in log spread**; the winner becomes the cost convention.

## 1. The sample, declared

From `data/fixtures/us_shorts_daily_raw.meta.json` and the fixture's last **252 bars**:
eligible = `cohort == "alive"`, `last_bar == "2026-08-26"`, `n_splits == 0`, ≥ 252
finite closes. Strata = 5 price quintiles (median close over the window) × 5
dollar-volume quintiles (mean close × volume over the last 63 bars); `default_rng(336)`;
**4 per cell → N = 100**. Written to `data/d336_sample.json` before any quote is seen.
`primaryExchange` from the meta: NYSE, NASDAQ, AMEX ("NYSE MKT" → AMEX), BATS.

## 2. The pull, declared (the principal runs it)

`Stock(sym, "SMART", "USD", primaryExchange)`; `reqContractDetails` first;
`reqHistoricalData(end = 2026-08-26 23:59:59 US/Eastern, "1 Y", "1 day", "BID_ASK",
useRTH = True)`, one request per name. BID_ASK requests count double against IBKR's
60-per-10-minutes pacing: a token bucket of **30 per 600 s** plus `+PACEAPI`, ~35 min
for 100 names, resumable. Raw bars to `data/raw/ibkr/` (git-ignored; exchange-licensed
data is cached, never committed) with a provenance `_meta.json`. Errors 162 / 10167 /
354 are logged per symbol and never filled; ten consecutive abort with "subscription
missing". **Bar semantics gate:** IBKR daily BID_ASK bars carry open = time-average bid,
close = time-average ask, high = max ask, low = min bid; the script asserts
`close ≥ open` on ≥ 99% of bars per name or stops. Quoted half-spread per day =
`(close − open) / 2 / mid`; per name, the median over the window.

## 3. The comparison

Per name, on the fixture OHLC over **exactly the quoted dates** (inner join, no
look-ahead): **PB** = median of per-bar CS/2; **PUB** = median of the trailing-21 mean of
lagged clamped daily estimates /2 (`CS_BARS = 21`); **AR** = Abdi–Ranaldo (2017),
`c_t = ln C_t`, `η_t = (ln H_t + ln L_t)/2`, `S² = 4·mean_t[(c_t − η_t)(c_t − η_{t+1})]`,
`S = √max(S², 0)`, half = `S/2`, once per name. Errors in log spread; **MALE** per
estimator; 5 × 5 stratum medians; `select_winner()` called once. A clamped-zero estimate
is floored at 1 bp for the log and counted.

## 4. Predictions

| | prediction |
|---|---|
| **Q1** | `MALE(PUB) < MALE(PB)`, and `MALE(PB) > ln 2` — the per-bar median is off by more than 2× on the typical name. |
| **Q2** | `MALE(AR) < min(MALE(PB), MALE(PUB))`. |
| **Q3** | among names whose per-bar zero rate exceeds 50%, `median(log_err_PB) < −ln 2`; among names below 25%, within ± ln 1.5. |
| **Q4** | the sample's median quoted half-spread lies in **[18, 28] bp** — between D332's two universe medians. |
| **Q5** | the winner's `MALE < ln 1.5`. **If not, no daily OHLC estimator is fit for a cost convention** and this record recommends a declared floor instead. |

## 5. Assertions (in `--compare`; `--selftest` runs them on a mocked client)

**[W]** date alignment and no look-ahead; **[U]** units — bp per side, finite, ≥ 0;
**[N]** ≥ 200 quoted days per compared name; **[K]** one `select_winner` call and the rule
text equals D332's; **[Z]** floored zeros counted; **[G]** `|ln(IB mid / fixture close)| <
0.05` on the last common date per name (adjusted-vs-unadjusted or wrong-contract guard);
**[S]** the self-test's Abdi–Ranaldo recovers a synthetic 50 bp half-spread within 5 bp
and returns 0 on a pure random walk; **[P]** the token bucket never exceeds 30 requests
per 600 s; **[6]** raises.

## 6. Outcome path

The winner becomes the `HALF` array every runner reads — a one-array swap, as D332
showed — and STACK §0 is re-costed under it. If Q5 fails, PUB stays as the default with
an explicit "unvalidated" tag.

## 7. Scope and dependency

`ib_async` is added as a dependency group (`ibkr`), imported lazily inside `--pull`
only; `--plan`, `--compare`, `--selftest` run without a broker library. **Out:** any
estimator beyond the three; intraday quotes; dead names (IBKR's history excludes them —
the convention is validated on live names and applied to all, which is stated).

## 8. Files

`docs/decisions/D336-quoted-spread-validation.md` (this record) ·
`scripts/d336_ibkr_quoted_spreads.py`, `data/d336_sample.json` (to follow) ·
`data/d336_comparison.json` and a RESULT record after the principal's pull.
