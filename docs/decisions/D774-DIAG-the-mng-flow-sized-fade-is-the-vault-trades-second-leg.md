# D774 DIAG — the MNG flow-sized post-settlement fade (D772's Fable R1) is the vault NG trade's second leg: same days, same predictor, ρ +0.16; outside 2022 its edge is real in volatility units but it trades about 19 times a year, and five volatility-spike trades carry 96% of the net

*2026-10-02. The principal: "Once everthing has been recorded the gas settlement fade sized by leveraged-fund flow,
is it similar to other strategies in the vault? How does it perform without 2022?"; then "Yes, record it as D774".*

- **What it is:** a POST HOC diagnostic on D630's spent NG in-sample (2017-05-23 → 2023-12-29). It opens, closes and
  admits nothing.
  - The construction came from D772's Fable pair, who found it in a search. Its thresholds (the top third of |I|, an
    sd of at least \$30) were chosen after looking.
- **The ruling it answers to** (D772 §1, the principal): an ex-ante volatility-gated book is not exempt from the
  one-year rule. It is judged on its other years: an even win rate, or a volatility-adjusted return that holds.
- **Runner:** `scripts/diag_d774_mng_flow_sized_fade.py` (pandas only, one process; a run-once diagnostic). **Output:** `data/diag_d774_mng_flow_sized_fade.json`.
  - It rebuilds the trade independently of the agents' scripts.
  - The first launch stopped on its own sign audit (a float equality, (2.990 − 3.000) × 1000 ≠ −10 exactly) before any
    data was read. The audit was given a tolerance and a mirrored-side check, and the run was repeated.

## 0. The legs and the checks

- **H2, the vault's NG trade** (slot 3, D723; slot 8, D649 at MNG size):
  - on D630 signal days, side = sign(q_est) at t0;
  - entry at the close of bar t0+1, exit at the close of the 14:29 bar.
- **R1, the fade:**
  - side = −sign(q_est at 13:50);
  - entry at the close of the 14:29 bar (D630's W_end close), exit at the close of the 15:29 bar;
  - one MNG (\$1,000 per \$1/MMBtu), \$4 a round trip (\$5 also reported).
  - The agents' cell entered one minute earlier (the 14:28 bar): +\$13.90 against +\$13.77 here.
- **The gates, from prior days only:**
  - T: |I| at 13:50 in its walk-forward top third (the prior 250 days, at least 120);
  - V: the trailing-20 sd of the R1 response at least \$30 a contract.
- **Checks:**
  - a lag audit re-derives both gates with explicit loops over earlier rows only;
  - a sign audit in money: funds predicted to buy into the window and a fall after 14:29 pays the fade, and the
    mirrored side loses;
  - one contract per session window; nothing on or after 2024-01-01.
- **The H2 rebuild against D630's own by-year file is approximate:**
  - trade counts within 0–6 a year (14/14, 30/32, 20/20, 111/117, 165/169, 201/205, 209/213);
  - the mean gross per full contract differs by up to about \$40 a year (2018 +\$96.67 here against +\$56.25; 2023
    −\$12.78 against +\$17.79).
  - So every H2 correlation below is indicative, not exact.

## 1. Is it similar to the vault's lines?

| | |
|---|---|
| R1 trades on the vault's NG signal days | **214 of 235 (91%)** |
| ρ(R1, H2) on all signal days (750) / on R1's days | **+0.13 / +0.16** |
| ρ of R1's daily P&L with D737's twin, NQ F2, C1 (1,446 days) | −0.047, +0.024, −0.017 |
| the commodity-index reweight lines (slots 4–6) | not computed: a different calendar |

- **R1 is the second leg of the vault's NG trade.** It trades the same days, on the same predictor (|I|), at the next
  clock, in the opposite direction. The vault line rides the funds' push into the settlement window; R1 fades it in
  the hour after.
- **They are not the same P&L.** The correlation is only +0.13 to +0.16, and it is positive: a bigger push into the
  window comes with a bigger give-back after it, as temporary price pressure predicts (D630 §7.5).
- **Run together, they would be one round trip** around the window, so they are not two independent components.
- **Against the index micros it is unrelated.**

## 2. How does it do without 2022?

**The gated R1 (T and V), one MNG:**

| | trades | mean gross | median | win rate | net at \$4 | t | volatility-adjusted* (t) |
|---|---|---|---|---|---|---|---|
| all years | 235 | +\$13.77 | +\$13.00 | 61.3% | +\$9.77 | 4.01 | +0.247σ (3.48) |
| **without 2022** | **93** | **+\$9.17** | +\$8.00 | 57.0% | **+\$5.17** | 2.32 | **+0.220σ (2.25)** |
| without 2020 and 2022 | 88 | +\$9.65 | +\$10.50 | 59.1% | +\$5.65 | 2.31 | +0.231σ (2.24) |

*The trade divided by the trailing-20 sd of the response: the trade in units of its own recent volatility.

**By year:**

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| trades | 27 | 14 | 5 | 45 | 142 | 2 |
| mean gross | +\$14.22 | −\$5.43 | +\$0.80 | +\$10.60 | +\$16.77 | +\$32.00 |
| win rate | 52% | 50% | 20% | 64% | 64% | — |
| volatility-adjusted | +0.37σ | −0.15σ | +0.03σ | +0.25σ | +0.27σ | — |

**The book (one MNG, \$4; every flow day from the first gated trade in 2018 to 2023-12-29, zero on flat days):**

| | all years | without 2022 |
|---|---|---|
| net Sharpe / Sortino; gross Sharpe | **1.30 / 2.10**; 1.80 | **0.68 / 1.11**; 1.18 |
| total net; maximum drawdown | +\$2,295; \$371 | +\$481; \$271 |
| exposure (share of days traded) | 19.8% | 9.9% |
| mean \|gross\| against the cost; breakeven cost | \$41.20 against \$4; \$13.77 | \$29.86; \$9.17 |
| skew; kurtosis; payoff | −0.19; 1.44; 1.15 | +0.24; 0.47; 1.13 |
| net mean ex-top 1% / ex-bottom 1% / trimmed | +\$8.48 / +\$11.34 / +\$10.06 | +\$3.90 / +\$6.11 / +\$4.84 |
| **five largest trades; their share of net** | 2022-06-30 +\$176, 2022-11-01 +\$142, 2022-11-28 +\$131, 2022-09-14 +\$127, 2018-12-20 +\$122; 30% | **2018-12-20 +\$122, 2018-12-21 +\$88, 2021-10-21 +\$86, 2021-10-29 +\$83, 2018-11-28 +\$83; 96%** |

**Ungated, every day (1,607): the give-back is there almost every year in volatility units.**
- **Overall:** +\$2.74 gross (t 3.85), +0.10σ (t 3.48).
- **Without 2022:** +\$0.93 (t 1.92), +0.08σ (t 2.52).
- **Volatility-adjusted by year:** +0.27 / +0.04 / +0.15 / +0.04 / −0.02 / +0.22 / +0.09σ for 2017–2023, positive in
  6 of 7.
- **In dollars it never pays the \$4 outside 2022** (+\$0.16 to +\$1.98 a trade).

## 3. The reading, against the principal's test

- **Volatility-adjusted return: it holds, weakly.**
  - The ungated fade is positive in volatility units in 6 of 7 years.
  - The gated fade is +0.22σ without 2022, against +0.27σ in 2022. 2018 and 2021 match 2022; 2019 is negative and
    2020 flat.
  - The effect is not a 2022 artefact. 2022 is simply the year it was big in dollars.
- **Win rate: not even.** 50–64% in the years with enough trades. 2020 won 1 of 5, and the gate barely opens in
  quiet years (5 trades in 2020, 2 in 2023).
- **Outside 2022 it is a volatility-spike book.**
  - About 19 trades a year, +\$5.17 net a trade, net Sharpe 0.68 / Sortino 1.11.
  - Five trades from the late-2018 and October-2021 gas spikes are 96% of that net, and the trimmed mean falls to
    +\$4.84.
  - It earns when gas is violent and abstains otherwise. That is the abstention principle working, but it is also
    what the one-year rule exists to catch: three episodes, not a steady stream.
- **Against the vault:** it adds a second leg on the vault's own NG days, on the same predictor. A confirmation
  would have to read the vault's NG window (2025-03 → 2026-09), which slots 3 and 8 already hold for H2.
  - R1 is a different trade, but it is the same days and the same predictor. Its vault read would not be independent
    of the H2 read.

## 4. What this does not settle

- **Selection:** the thresholds came from a search, so every number here is in-sample and post hoc. Only a
  pre-registered test on unread data could promote it.
- **The 2024-01 → 2025-02 slice:** D630's own in-sample ran to 2025-02, so that NG slice is not unread. It was not
  read here (seal at 2024-01-01), and it cannot serve as a clean confirmation for an NG settlement construction.
- **Nothing is proposed.** Whether R1 is worth a pre-registration is the principal's call.
