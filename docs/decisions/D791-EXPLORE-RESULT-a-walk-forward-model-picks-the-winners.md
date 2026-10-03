# D791 EXPLORE RESULT: the oracle's winners share no single visible trait, but a linear model trained only on earlier years picks them out of sample. A passive book of +\$4.80 net a trade (t 2.00) on 2018–2023, balanced across months, and profitable outside Dec–Mar

*2026-10-03. `scripts/explore_d791_oracle_patterns.py --build` (system interpreter: the tape) then `--run` (uv:
scikit-learn), 207 seconds, under the [scope note](D791-EXPLORE-patterns-in-the-oracle-s-china-open-trades-scope.md)
committed before it (`9861ee31`).*
- **One fix before any statistic was computed:** the cache moved to CSV (`09ffba48`), since the uv environment reads
  no parquet.
- **The follow-up was taken AFTER seeing the run:** `scripts/explore_d791_followup_calendar.py`, the calendar ablation
  with 500 shuffled-label runs (§3). It is disclosed.
- **Outputs:** `data/explore_d791_oracle_patterns.json`, `data/explore_d791_followup_calendar.json`.
- **This is in-sample triage** (RULES.md's correction to R14). D786's build reproduced D767 and D770 exactly. Nothing on
  or after 2024-01-01 is read.

## 1. The oracle's winners, feature by feature: no single trait

- **The oracle:**
  - passive: takes 695 of 1,466 (47.4%) at +\$37.12 net, and rejects the rest at −\$35.21;
  - taker: 793 of 1,697 at +\$35.09.
- **The best single features, by AUC for the oracle's passive take** (0.5 is chance; 40 features):

  | feature | AUC (2016–19 / 2020–23) | rank in its own rotation |
  |---|---|---|
  | **the prior US day session's return, along x** (D786's tug of war) | **0.544** (0.561 / 0.528) | 0.995 |
  | **month (sine)** | **0.543** (0.528 / 0.557) | 0.995 |
  | **the AUD's move in the window, along x** (D767's F3 inverse) | **0.535** (0.516 / 0.547) | 0.977 |
  | the CNY fix change, along x | 0.468 (0.466 / 0.468) | 0.973 |
  | the open stretching from SMA50 / SMA200 / SMA20 (D790) | 0.527 each | 0.90–0.93 |
  | R* (D786's 117) | 0.473 | 0.90 |

- **Against the family-max null across all 40 features, the best single feature has p 0.15 (passive) and p 0.13
  (taker).** No one trait separates the winners.
- Big winners against big losers (the top and bottom quartiles of gross) separate on nothing (family p 0.50).
- **The shapes of the open** (D790's S1–S10) are all within 0.475–0.525.

## 2. Learning the oracle, walk-forward: each test year predicted by a model fit only on earlier years

| model (fixed in the scope note, not tuned) | out-of-sample ρ with gross | shuffled-label p50 / p95 (50 runs) | years positive | passive top third: n, net, **t** | taker top third: net, t |
|---|---|---|---|---|---|
| **ridge** | **+0.068** | −0.005 / +0.049 | 5 of 6 | 475, **+\$5.41, 2.24** | +\$2.22, 1.01 |
| **logistic** (on the oracle's label) | **+0.072** | −0.002 / +0.049 | 5 of 6 | 447, +\$4.14, 1.55 (6 of 6 years profitable) | +\$1.44, 0.61 |
| boosted trees (depth 3) | +0.029 | +0.000 / +0.052 | 5 of 6 | 383, +\$2.92, 1.10 | +\$0.43, 0.18 |

- **The test years are 2018–2023.** The unfiltered passive book nets −\$0.07 over them; taker −\$2.02.
- **The two linear models clear their declared lead bar:** above the shuffled-label p95, with at least 4 of 6 years
  positive.
- **The boosted trees do not.** On about 1,500 noisy sessions the interactions they look for are mostly fitted noise.
  The edge is additive: many weak, near-independent pieces, each worth 0.02–0.04.
- **Ridge, by year** (ρ; passive net):

  | | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
  |---|---|---|---|---|---|---|
  | ρ | −0.046 | +0.102 | +0.036 | +0.142 | +0.020 | +0.139 |
  | passive net | −\$0.59 | −\$0.32 | +\$8.80 | +\$12.35 | +\$1.29 | +\$13.85 |

  - 2018's model was trained on only two years.
- **What the ridge leans on** (the full-sample coefficients, descriptive):
  - the AUD along x;
  - month;
  - g_US along the fade;
  - the late push into 09:30;
  - the open stretching from SMA200;
  - the retrace from the extreme;
  - the US day session along x;
  - an early-done open (negative).
  - These are the pieces D786, D787 and D790 found one at a time, each too weak alone.

## 3. The follow-up (taken after seeing §2): is it the season? No

| ridge | out-of-sample ρ (500 shuffles: p95; rank) | passive top third: n, net, t, years | month gap | Dec–Mar share, selected / pool | passive net Dec–Mar / Apr–Nov |
|---|---|---|---|---|---|
| all 40 features | +0.068 (p95 +0.047) | 475, +\$5.41, 2.24, 4 of 6 | 3.1 pts | 35.8% / 31.6% | +\$7.25 / +\$4.39 |
| **without the calendar** (month, weekday, US clock: 36 features) | **+0.059 (p95 +0.041)** | **479, +\$4.80, 2.00, 4 of 6** | **2.2 pts** | **32.2% / 31.6%** | **+\$7.99 / +\$3.29** |

- **Without the calendar features the model keeps most of its edge, selects evenly across months, and earns outside
  Dec–Mar.** That is the debate's B1 and B2, both passed, at a passive net t of 2.00.
- **The shuffled-label p95 needed 500 runs.** At 50 runs it read 0.049 on one seed and 0.060 on another, too noisy to
  judge a thin margin. At 500, both models clear it by about 0.02.

## 4. What this means, and its limits

- **To the principal's question: the winners are partly knowable before the trade.** Not from one trait, but from many
  weak ones added together:
  - the Western sessions before the open (the US day session reverses into the Asian session; the US afternoon
    continues);
  - the open's cross-asset confirmation (the AUD);
  - how the open was made (a late push reverts more);
  - where it sits against its trend.
- **The limits, which decide what to do next:**
  1. **Pseudo out-of-sample.** The walk-forward protects the model's FIT. It does not protect the feature list, which
     was assembled after D786, D787 and D790 had looked at these years. Some of its 40 features were kept because they
     sorted this sample. That inflates the result by an unknown amount. Only data no study has seen measures it.
  2. **Three models were tried.** Two pass, and the better one is reported first.
  3. **The passive book is a model:** GC's queue, D770's fill rule, with the 8% of best sessions that never fill.
  4. **Concentration:** 2020, 2021 and 2023 carry the ridge book; 2018–19 are flat or slightly negative.
- **The next step is one frozen model, read once on 2024+:**
  - **frozen:** the 36-feature no-calendar ridge (fixed α = 100), trained on all of 2016–2023, its threshold the 2/3
    quantile of the 2016–23 in-sample predictions, passive primary;
  - **the slice:** 2024-01 → 2026-09, about 650 sessions; about 560 passive-valid, so a top third of about 190
    trades;
  - **power:** at the measured +\$4.80 net (sd about \$52), the expected net t is about 1.3. P(t ≥ 2) is about 23%,
    and a one-sided 5% test of the model score's ρ (0.059, SE about 0.042) passes about 40% of the time;
  - **one confound to state in the pre-registration:** the SHFE auction change of 2023-05-26.
  - **The alternative is the forward recorder:** freeze the model now, let it trade on paper from today, and read it
    when the power is there. That spends nothing.
- **Nothing is admitted.**

## Addendum (2026-10-04): the overfit, measured. Partly overfit, with weights that hold their signs, but fragile

*The principal: "That looks like a severe overfit? How did in perform out of the training data?". The looks were taken
after D791. Script `scripts/explore_d791_followup_overfit.py`; output `data/explore_d791_followup_overfit.json`. The
36-feature no-calendar ridge, as above.*

- **Every performance figure above was already out of sample** (each test year predicted by a model fitted only on
  earlier years). The full-sample weights were descriptive only.
- **The training fit against the next year:**

  | test year | trained on | ρ on its training years | ρ on the test year | passive net in the test year (n) |
  |---|---|---|---|---|
  | 2018 | 2016–17 | +0.234 | **−0.060** | −\$0.88 (74) |
  | 2019 | 2016–18 | +0.214 | +0.092 | −\$4.00 (103) |
  | 2020 | 2016–19 | +0.183 | +0.061 | +\$10.67 (89) |
  | 2021 | 2016–20 | +0.168 | +0.131 | +\$13.05 (49) |
  | 2022 | 2016–21 | +0.172 | **−0.007** | +\$1.94 (85) |
  | 2023 | 2016–22 | +0.162 | +0.108 | +\$12.94 (79) |

  - **The fit is overfit by about two-thirds:** about 0.17–0.23 in training against 0.059 out of sample. The
    full-sample fit is 0.162.
  - **Three years carry the book** (2020, 2021, 2023). Two lose or barely earn, and 2018 is negative.
- **The weights are not noise.** 23 of the 36 keep the same sign in all six folds, and 30 in at least five. The top 12
  by weight hold their sign in 5–6 of 6, with steady magnitudes: the US day session 0.020–0.028 in every fold; the
  Tokyo half-hour −0.013 to −0.024.
  - Fitted noise would flip signs from fold to fold. These features carry a stable, weak relation.
- **The sensitivity is the warning:**

  | | expanding window (all prior years) | rolling 3-year window |
  |---|---|---|
  | α 10 | ρ +0.048; passive +\$3.81, t 1.55 | ρ −0.005; +\$0.94, t 0.40 |
  | **α 100 (the registered setting)** | **ρ +0.059; +\$4.80, t 2.00** | ρ +0.002; +\$0.82, t 0.35 |
  | α 1000 | ρ +0.057; +\$3.95, t 1.58 | ρ −0.004; +\$0.59, t 0.26 |

  - **α = 100 happens to be the best of the three.** It was fixed in the scope note before the run, but the margin over
    its neighbours shows how much of t 2.00 is that luck.
  - **A 3-year rolling window has no edge at all.** Either the weak weights need five or more years of sessions to be
    estimated, or the relation lives mainly in the older years. Both mean a live model fitted on recent data alone
    would not work.
- **The reading:**
  - the out-of-sample edge is real in the narrow sense: a stable-signed, weak, additive relation, worth about
    ρ 0.05–0.06 with an expanding window;
  - it is fragile: lumpy by year, sensitive to the window, and its best number sits on the luckiest setting;
  - combined with the pseudo-out-of-sample feature list (§4.1), the honest expectation forward is below the in-sample
    +\$4.80. Somewhere between 0 and about +\$3 a trade, passive, is a fair prior.
  - **The test it needs is forward or 2024+, and the paper-trading route remains the right one. Nothing is admitted.**
