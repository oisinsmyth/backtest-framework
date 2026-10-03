# D791 EXPLORE (scope note, written before the run): patterns in the oracle's China-open trades. What separates the winners from the losers, and can a model trained on past years pick next year's winners?

*2026-10-03. The principal: "Look at the oracle filter show those results?", then "Can try to find patterns in the
oracle filtered trades?".*

- **What it is:** a disclosed in-sample exploration (RULES.md's correction to R14).
  - **The oracle** is D767's: take a session if and only if its realised net > 0. It is hindsight.
  - **The question:** do the sessions it keeps share anything visible before 09:31, alone or in combination?
- **The object:** D765's MGC China-open fade, as in D786–D790 (side −sign(x), entry 09:31, exit 15:00 Beijing).
  - The passive book (D770's, about \$3.03) is primary; taker (\$5.93) is reported beside it.
  - Sessions and books are D786's build, which reproduces D767 and D770 exactly. Nothing on or after 2024-01-01 is
    read.

## The features (every one stamped no later than 09:30 Beijing; oriented along the fade where signed)

- **The open:**
  - |x| and its relative size; the side (long or short fade);
  - D790's shape features S1–S10;
  - the Tokyo half-hour (08:00–08:30) and the pre-open half-hour (08:30–09:00) along x.
- **The night:**
  - the CME overnight move g along the fade (−sign(x)·g);
  - g_US along the fade;
  - the hours since SHFE's last close (the long-closure flag).
- **Cross-asset and onshore:**
  - the AUD's move in the window along x;
  - the SGE premium's level and its 20-day dislocation along the fade;
  - the CNY fix change along x;
  - the US day session's return R_US along x, and the London morning's.
- **Microstructure:** R* (D786's impact-decay ratio, relative to its trailing median).
- **Trend and volatility:**
  - D790's T1–T6, the distances to SMA200/50/20, unsigned and along x, the 250-day high, RSI and the 20-day return;
  - realised volatility of the daily closes over 20 sessions, and its ratio to 250 sessions.
- **The calendar:** month (sine and cosine), weekday, the US clock (EST/EDT).

## Part A: describe the oracle's winners

- **For every feature:**
  - the AUC of the feature for the oracle's take/reject label (passive and taker), and its median among the taken and
    the rejected;
  - the same for the top quartile of the fade's gross against the bottom quartile (big winners against big losers).
- **The null:** each feature's exact rotation over the candidate sequence, with the family-max null across features
  (one offset applied to all).
- **The halves** (2016–19 / 2020–23) are reported for every AUC.

## Part B: learn the oracle, walk-forward (the honest test of "knowable before the trade")

- **The split:** for each test year from 2018 to 2023, train on every earlier year and predict the test year. No test
  year's outcome touches its model, its feature scaling or its threshold.
- **The models:**
  - (a) ridge regression of the gross's rank on rank-scaled features;
  - (b) a gradient-boosted tree regressor (scikit-learn HistGradientBoosting: depth ≤ 3, learning rate 0.05, 200
    iterations, at least 50 sessions a leaf), which can find interactions;
  - (c) logistic regression on the oracle's label.
  - Hyper-parameters are fixed here and are not tuned.
- **Out of sample:**
  - the Spearman of the prediction with the gross, pooled and by year;
  - the AUC for the oracle label;
  - **the top-third book**, with the threshold the 2/3 quantile of the TRAINING years' predictions: passive and taker
    net, t, profitable years.
- **The null:** 50 runs with the training labels shuffled within each training year, per model. Reported: the null's
  p50 and p95 of the out-of-sample Spearman.
- **The importances:** the ridge coefficients, and the boosted model's permutation importance on the out-of-sample
  years.

## The bar for a lead (stated now)

- **For a model:** out-of-sample Spearman above its shuffled-label p95, positive in at least 4 of 6 test years. Its
  passive top-third book's net t is stated against G2's 2.
- **For a single feature:** AUC beyond its own rotation p97.5, the same side in both halves, and its place against the
  family-max null.
- **Triage only:** a lead earns one frozen pre-registration for a 2024+ read, with its power stated, split at the SHFE
  auction change (2023-05-26). Nothing is admitted.

## Output

- `scripts/explore_d791_oracle_patterns.py`:
  - `--build` (system Python: the tape) writes a feature cache in `temp/d791/`;
  - `--run` (uv Python: scikit-learn) writes `data/explore_d791_oracle_patterns.json`.
- The findings go in a separate record.
