# D738 STAGE 0 PRE-REGISTRATION — step 1 of an expected-profit filter on D727's NQ follow: the oracle, and a profile of where its winners sit

*2026-10-01.*
- *The principal asked "Does this have an expectant profit filter?" about D727's NQ follow, then said "OK lets go for
  that".*
- *Numbered D738 after telling the other session (D737 is theirs).*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29).*

## 0. Why, and the three steps

**The gap.** [D727](D727-STAGE-0-RESULT-nq-continues-from-the-open-alone.md)'s NQ follow (the first half hour at which
|z| ≥ k, one MNQ in the drift's direction, held to 15:59) has no expected-profit filter. Its pre-registration did not
say that none was available, which the principal's standing rule requires (2026-09-28).

**The context.**
- At k 1.5 it nets +\$15.22 a trade, Sharpe 0.83.
- It loses in the calm years (2016, 2017 and 2019), and [D736](D736-STAGE-0-RESULT-only-the-compression-break-earns-and-abstains.md)
  reads it INTERMITTENT on 2016–23.
- The principal **declined it as a strategy** ("I don't want a dumb follow type strategy"). This study does not
  reverse that. It asks whether a filter can make it selective.

**The three steps, per the principal's rule for filters** (2026-09-29: score on the traded instrument, show the oracle
first, design the candidates together):

| step | what | where |
|---|---|---|
| **1** | **the prize and the profile** | this record |
| 2 | the candidate filters, designed **with the principal** from step 1's profile | an amendment, before any filter is scored |
| 3 | the filters scored: oracle accuracy, calibration, the filtered book against take-all, and the D736 standard | after step 2 |

**Nothing in step 1 chooses a filter, a threshold or a variable.**

## 1. The object

**The trades.** D727's practical NQ book, rebuilt with D727's own functions (`panel_from_raw`, `objects`, the
first-crossing rule):
- k ∈ {0.5, 1.0, 1.5}; **k 1.5 is the primary**.
- k 0.5 is profiled beside it, as the widest candidate pool a filter could select from.
- One MNQ at D711's cost line (\$4.0671 a round trip), held to 15:59.
- 2016-02 → 2023-12-29.

**The read.**
- `fut_NQ_rth_1m.csv.gz` is read **in chunks, keeping only `day ≤ 2023-12-29`** before any row is kept, then passed
  to D727's `panel_from_raw`.
- Every frame asserts no session on or after 2024-01-01.

**The known answers** (from `data/stage0_d727_trend_curve.json`), checked before anything is profiled:

| book | trades | mean net (to 1e-6) | yearly nets |
|---|---:|---:|---|
| k 1.5 | 1,024 | 15.223894518888622 | each equals the recorded `net_by_year` |
| k 1.0 | 1,505 | | each equals the recorded `net_by_year` |
| k 0.5 | 1,884 | | each equals the recorded `net_by_year` |

## 2. The prize (per k)

- **Take-all:** trades, net and gross per trade (mean and median), daily net Sharpe and Sortino, max DD, net by year,
  and D736's G1/G2/G3 label.
- **THE ORACLE** (`filter_oracle.oracle_take`, net > 0): its trades and net, by year; the ceiling.
- **The oracle at the template bar** (`oracle_take_threshold`, gross ≥ 2 × cost).
- **The SIZE oracle.** It knows the trade's |close − entry| but not its sign, and takes the trade when that is ≥ 2 ×
  cost in dollars. It answers whether the follow pays on big days.
- **The partial-oracle curve** (`partial_oracle_curve`, target = net):
  - ρ ∈ {0, 0.05, 0.10, 0.20, 0.30, 0.50, 1.0}, keeping q ∈ {0.5, 0.7} of the trades, 1,000 draws each.
  - ρ = 0 is the null. It says how accurate a filter must be before it pays.
- **Per year:** take-all net, oracle net, and the oracle's take rate. **These answer whether the calm years have
  winners to keep, or whether the follow simply does not work in them.**

## 3. The profile: where the oracle's winners sit

Eleven variables, **each known before the entry clock**, on the k 1.5 trades and the k 0.5 trades.

**From D727's panel:**

| # | variable | definition |
|---|---|---|
| V1 | dollar volatility | σ_oc × \$2 a point (prior 20 sessions' open-to-close RMS) |
| V2 | \|z\| at entry | |
| V3 | the entry clock | |
| V4 | the gap with the trade | side × (09:30 open − prior session's 15:59 close) / σ_oc |
| V5 | yesterday with the trade | side × prior session's (close − open) / σ_oc |
| V6 | the volatility trend | RMS of the prior 5 sessions' open-to-close / σ_oc |
| V7 | relative volatility | σ_oc's percentile in its own trailing 252 sessions |

**From D691's NQ frame and IV table** (built under D720's `lowered_cut`, as D720 did; asserted ≤ 2023):

| # | variable | definition |
|---|---|---|
| V8 | ln(IV / RV20) | the one input known to predict size, D691 |
| V9 | D691's day-size forecast tier τ | walk-forward, with D671's and D720's forecast and tier audits re-run |
| V10 | the prior day's dealer gamma | `gd_spx`, D663's lagged ES-book GEX; aggregates only, per the SqueezeMetrics licence |
| V11 | the overnight range | `on_range`, D671 |

Also, as categories: the event-day and opex flags.

**For each variable and each book:**
- quintile bins on the whole in-sample (a description, not a rule), with n, mean net, mean gross, win rate, the bin's
  net total, and its oracle take rate;
- Spearman with net and with gross;
- the AUC against the oracle label;
- for V1 and V7, the mean by year beside the year's net.

**Coverage.** V8–V11 exist only where D691's frame has the session. The joined count is reported, and the profile of
V8–V11 runs on that subset.

## 4. The audits (every one must fire on a deliberate break)

1. **Lag:** D727's `lag_audit` and its one-bar canary.
2. **Point in time for V4–V7:** a second implementation from the raw rows on sampled days. A canary that uses the
   same day's close for "yesterday" must raise.
3. **Sign, in money:** sampled trades re-priced from the raw rows. A long whose price rises to 15:59 pays +\$2 a point.
4. **Right quantity:** the three known answers (§1). A canary scoring the 15:00 close must miss them.
5. **The date join:** V8–V11 joined by session date. A canary joining one session late must change V9's values on
   most days and fail the join audit.
6. **D720's forecast and tier audits**, and their leak canaries.

## 5. Predictions (stated before the runner exists)

| # | prediction |
|---|---|
| 1 | the oracle's ceiling is large: > \$30,000 at k 1.5, against take-all's \$15,589 |
| 2 | the calm years (2016, 2017, 2019) have an oracle take rate within 5 points of the other years: there are winners to keep in every year |
| 3 | V1 (dollar volatility) has a positive Spearman with net at k 1.5. A filter on it would then be a volatility-regime gate (D703's trap) |
| 4 | V8 (ln IV/RV) has the largest \|Spearman\| with **gross** among V8–V11 |
| 5 | the partial-oracle curve needs a Spearman of at least 0.05 to lift the mean net a trade by \$5 at q 0.5 |

## 6. What follows

- **The RESULT presents the prize and the profile to the principal,** with **no filter chosen**.
- **Step 2:** the principal and I design the candidates from the profile. They are declared in an amendment before
  anything is scored.
- **The principal's caveats** go with any filter that results:
  - it does not change the follow's entry, so it stays a follow;
  - a filter that sits out whole calm years needs D736's G2 read with a zero year counted as an abstention. That reading
    would itself need the principal's word.

## Amendment D738-A1 (2026-10-01): step 2, the candidate filters, declared with the principal before any is scored

**The principal's choices**, after step 1's result
([D738 RESULT](D738-STAGE-0-RESULT-the-follow-loses-in-calm-regimes.md)), given to the
four design questions:
- **Axes:** all four offered (volatility level in dollars, dealer gamma, IV relative to RV, relative volatility).
- **Form:** the expected-profit template in dollars.
- **Pool:** the k 1.5 book.
- **Zero years:** a year in which the filter does not trade counts as **abstention**, not as a loss.

**Disclosed selection:** the axes were chosen after step 1's profile on the same in-sample trades. Every reading below is
in-sample. Any filter that survives needs data it has not seen before it is believed.

### A1.1 The template (one form for every filter)

For each k 1.5 trade *i*, in session order:
- σ\$ᵢ = σ_ocᵢ × \$2 (V1);
- yᵢ = grossᵢ / σ\$ᵢ, the trade's **pass-through** of a day's typical move.

The pass-through is projected from **earlier trades only**:
- p̂ᵢ = xᵢ · b̂ᵢ, where b̂ᵢ is the OLS of y on x over the trades of sessions before *i*'s session (an expanding window);
- **projected gross = p̂ᵢ × σ\$ᵢ**;
- **take the trade iff projected gross ≥ 2 × \$4.0671 = \$8.1342.**

**The burn-in:** no filter decides before 100 earlier trades with every input of that filter defined. Before that, the
session is **outside the evaluation window** for every filter and for take-all alike.

**The common evaluation window** starts at the first session at which **all five** filters can decide. It runs to
2023-12-29. A trade whose input is missing inside the window is not taken by the filters that need that input; take-all
keeps it. The count is reported.

### A1.2 The five filters (the state vector x)

| filter | x | what it asks |
|---|---|---|
| **F1 VOL** | [1] | a constant pass-through, so it trades iff σ\$ ≥ 2c / b̂: the volatility level alone |
| **F2 VOL+GAMMA** | [1, γ%] | γ% = the prior-day dealer gamma's (V10) percentile in its own trailing 252 sessions (prior values only) |
| **F3 VOL+IV/RV** | [1, ln IV/RV20] | V8 |
| **F4 VOL+RELVOL** | [1, σ_oc's 252-session percentile] | V7 |
| **F5 ALL** | [1, γ%, ln IV/RV20, σ_oc percentile] | all four axes together |

### A1.3 What is reported, per filter and for take-all on the same window

- **All four groups** (CLAUDE.md):
  - net and gross side by side, Sharpe and Sortino, max DD;
  - share of sessions in the market;
  - the trade distribution, with both-tail trims;
  - by year;
  - the null distribution.
- The accuracy against the oracle (`filter_oracle.assess`): AUC, Spearman of the projection with gross, capture.
- The **calibration** (realised gross on projected gross): its slope and bins.

### A1.4 The null and the gates

**The null.** The filter's take mask is **rotated in time** over the window's k 1.5 trades: every circular offset,
**enumerated** (exact; the SE is 0). This keeps its take count and its clustering, and breaks its alignment with the
outcomes.
- **Statistic S1:** the mean net per kept trade.
- **Statistic S2:** the efficiency, Σgross / Σ|gross| of the kept trades, beside S1. A filter that selects on size
  raises S1 mechanically when the edge scales with volatility, and D711-A1 showed S1 is the anti-conservative one.
- **p-value:** the share of offsets whose statistic is ≥ the filter's.
- **Holm** across the five filters, on S1's p-values.

| gate | standard |
|---|---|
| **Gate 1 (mechanism, gross)** | the take-all k 1.5 book on the window has mean gross > 0 with Newey–West t ≥ 2 (5 lags) |
| **Gate 2 (the filter, net)** | the filtered book's mean net per trade > take-all's; its S1 beats the rotation null at Holm-adjusted p ≤ 0.05; and the calibration slope is > 0 |
| **Gate 3 (the principal's standard, with abstention)** | on the filtered book's daily net, D736's G1–G3, counted over **traded years only**. A traded year is a calendar year with ≥ 10 filtered trades; others are abstention years, excluded from G1–G3 though their net stays in every total. Fewer than four traded years reads UNDEFINED |

**Readings, per filter:**

| reading | when |
|---|---|
| **SUPPORTED** | Gates 1, 2 and 3 all hold |
| **FILTER ONLY** | Gates 1 and 2 hold, and Gate 3 fails |
| **NOT SUPPORTED** | Gate 2 fails |
| **NO MECHANISM** | Gate 1 fails |

S2 is reported, not gated. A filter that passes S1 while S2 sits inside its null is **flagged SIZE-CARRIED**.

### A1.5 Predictions (before the scorer exists)

| # | prediction |
|---|---|
| 1 | F1 VOL raises the mean net per kept trade above take-all's, and abstains (fewer than 10 trades) in at least one of 2016, 2017 or 2019 |
| 2 | F1 is SIZE-CARRIED: S1 beats its null, S2 does not |
| 3 | F2 VOL+GAMMA has the highest S1 of the five |
| 4 | at least one filter reads SUPPORTED |
| 5 | F5 ALL does not beat the best single-axis filter on S1 (more inputs, more noise) |

### A1.6 Mechanics

- **The runner** is `scripts/stage0_d738_step3_filters.py`.
  - It rebuilds the trades and variables through step 1's own functions (`read_cut`, `book`, `full_day_arrays`,
    `d691_frame`), with step 1's audits.
  - It re-proves step 1's k 1.5 known answer.
- **Its self-test** must show four things:
  - the walk-forward fit never uses the trade's own session; a leak canary that includes it must raise;
  - the rotation null of a random mask sits near p = 0.5;
  - a planted filter is found;
  - the take rule's threshold is applied in dollars.
- **Its output** is `data/stage0_d738_filters.json`, run once, aggregates only.
