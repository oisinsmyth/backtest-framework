# DEPOSIT TEST MAP

**Rendered from [`data/deposit_test_map.json`](../../data/deposit_test_map.json) by `backtest_framework.validation.crosswalk` (D607).** The JSON is the truth; this page is a render and editing it by hand is a change that the next render throws away.

Five of the pre-registration documents deposited in `docs/internal/User-Doc-Deposit/` close with a numbered **Required unit tests** list: `SETTLEMENT_FLOW_LEDGER_PREREG.md`, `INDEX_REWEIGHT_FLOW_PREREG.md`, `OPENING_AGENT_STATE_PREREG.md`, `SHOCK_CLASSIFIER_PREREG.md` and `LETF_CLOSE_FLOW_PREREG.md`. Those documents are **untracked**, so they are named here in prose and never linked: a relative link to a file that is not in `git ls-files` is a dead link for every reader who is not the author, which is what `scripts/check_doc_links.py` exists to say. `ARCHITECTURE_OVERVIEW.md` has no numbered list -- its section 9 is a power-class table -- and is not on this page.

**The path translation.** The deposit writes its own outputs under `results/`. This repository has no root `results/`: rendered pages live in `docs/results/` and machine-readable state lives in `data/`, the mapping D592 recorded for the programme registry and `validation/power.py` declined to invent.

**A percentage below is a COUNT, not a verdict.** "claimed" means one repository test names that number in its function name, a section banner, or a docstring or assertion message. It does not say the test is right, that the claimed items are the important ones, or that the unclaimed ones are not. Nothing here has been run against a market.

**The three spellings, and why a grep misses half.** A claim is made in one of three conventions -- a function name (`def test_ledger_51_...`), a section banner (`# ===== ledger test 66`), or a docstring or assertion message (`Ledger unit test 11 and shock unit test 9, long side.`). Of the 79 claims here, **59 use the function name, 15 a docstring or message and 5 a banner**; at the 28 claims D607 opened with, `grep 'def test_ledger'` found six. **Going forward (D607): a test that discharges a numbered deposit item names the number in its FUNCTION NAME** -- `test_<doc>_<number>_<what>` -- because that is the spelling `pytest -k`, a traceback, a test id and a grep all see. The other two conventions stay valid for the tests that already use them, `scripts/deposit_test_map.py --scan` reads all three, and one function name can only carry ONE number -- an item discharged by a test named for a different document still needs the docstring spelling.

---

## Coverage

| Document | Section | Tests | Claimed | Covered via | Declined | Unclaimed | % claimed |
|---|---|---:|---:|---:|---:|---:|---:|
| Settlement flow ledger (`SETTLEMENT_FLOW_LEDGER_PREREG.md`) | 12. Required unit tests (line 705) | 71 | 65 | 0 | 5 | 1 | 91.5% |
| Index reweight flow (`INDEX_REWEIGHT_FLOW_PREREG.md`) | 13. Required unit tests (line 347) | 28 | 6 | 0 | 0 | 22 | 21.4% |
| Opening agent state (`OPENING_AGENT_STATE_PREREG.md`) | 15. Required unit tests (line 334) | 25 | 6 | 4 | 0 | 15 | 24.0% |
| Shock classifier (`SHOCK_CLASSIFIER_PREREG.md`) | 9. Required unit tests (line 293) | 13 | 2 | 0 | 0 | 11 | 15.4% |
| LETF close flow (`LETF_CLOSE_FLOW_PREREG.md`) | 8. Required unit tests (line 242) | 9 | 0 | 0 | 0 | 9 | 0.0% |
| **All five** | | **146** | **79** | **4** | **5** | **58** | **54.1%** |

**By class**, over all 146 items: arithmetic 40, data_guard 25, execution 16, leak 31, rendering 3, statistical 31.

---

## The items

One table per document, every numbered item in the document's own order. The **Claim** column is `file:line` and, where the convention supplies one, the symbol; the line is the one that CARRIES THE NUMBER, which for a banner or a docstring is not the line of the first assertion. An unclaimed row carries its paraphrase so a future agent can pick it up without opening the deposit.

### Settlement flow ledger — `SETTLEMENT_FLOW_LEDGER_PREREG.md`

Section 12. Required unit tests, heading at line 705, items at lines 707–777. **65 of 71 claimed (91.5%).**

| # | Line | Class | Status | Claim | Item |
|---:|---:|---|---|---|---|
| 1 | 707 | arithmetic | claimed | `tests/golden/test_ledger_flows_ledger.py:78` `test_ledger_1_q1_notional_at_l_plus_two_and_minus_two` | `Q1` for L = +2, AUM = 1e9, r = 0.05, f_fut = 1 gives +1e8 notional before contract conversion. L = −2 gives +3e8 (the same sign as the move).<br>**Note:** D610. |
| 2 | 708 | arithmetic | claimed | `tests/unit/test_ledger_flows.py:62` `test_ledger_2_l_plus_one_funds_contribute_zero_rebalance_flow` | L = +1 funds contribute zero rebalance flow.<br>**Note:** D610. |
| 3 | 709 | arithmetic | claimed | `tests/unit/test_ledger_flows.py:88` `test_ledger_3_f_fut_routes_wholly_to_p1_or_to_p2` | `f_fut = 0` routes all rebalance to P2; `f_fut = 1` routes all to P1.<br>**Note:** D610. |
| 4 | 710 | leak | claimed | `tests/unit/test_ledger_funds.py:150` `test_ledger_4_the_execution_day_lag_picks_one_term_and_never_both` | `lag_c = 1`: Q3_known uses ΔShares from t−1 and no forecast term; `lag_c = 0`: the forecast term only.<br>**Note:** D611. |
| 5 | 711 | arithmetic | claimed | `tests/unit/test_ledger_update.py:116` `test_ledger_5_p_zero_leaves_the_prior_alone_and_infinite_R_kills_the_gain` | Update step: with p = 0 the posterior equals the prior and Q_rem = μ_total; with R → ∞, K → 0.<br>**Note:** D610. |
| 6 | 712 | arithmetic | claimed | `tests/golden/test_ledger_flows_ledger.py:112` `test_ledger_6_update_step_on_the_documents_own_numbers` | Update step: a known synthetic case (μ = 100, σ² = 400, p = 0.5, R = 100, z = 60) matches hand-calculated K, Q_hat, Q_rem.<br>**Note:** D610. |
| 7 | 713 | arithmetic | claimed | `tests/unit/test_futures_impact.py:123` `test_ledger_7_impact_sign_follows_q_rem` | Impact: sign follows Q_rem; zero Q_rem gives zero I.<br>**Note:** D604. Three test_ledger_7_* functions here, under the banner at line 120, and two more in tests/golden/test_futures_impact_ledger.py. |
| 8 | 714 | leak | claimed | `tests/unit/test_ledger_update.py:76` `test_ledger_8_s_norm_excludes_the_evaluation_day_and_everything_after_it` | No look-ahead: V_d, σ_d, S_norm and the fund data used on day t exclude data from day t onward (fund data respects `published_at`).<br>**Note:** D610. |
| 9 | 715 | execution | claimed | `tests/unit/test_ledger_update.py:179` `test_ledger_9_earliest_pass_signals_at_the_first_passing_t0_and_never_re_enters` | Earliest-pass rule: signals at the first passing t0 and never re-enters.<br>**Note:** D610. |
| 10 | 716 | execution | claimed | `tests/golden/test_futures_fills_ledger.py:200` | Entry constraint: an entry that would complete less than 3 min before W_start is rejected.<br>**Note:** D587. The docstring of test_entry_must_complete_three_minutes_before_the_window. |
| 11 | 717 | execution | claimed | `tests/golden/test_futures_fills_ledger.py:99` | Intra-bar pessimism: a bar spanning the stop and a profit exit records the stop.<br>**Note:** D587. One docstring claims ledger 11 and shock 9 together. |
| 12 | 718 | data_guard | claimed | `tests/unit/test_ledger_flows.py:163` `test_ledger_12_flow_lands_on_the_held_months_never_the_front` | Contract mapping: flow is attributed to the held contract months per holdings, not the front month by default.<br>**Note:** D610. |
| 13 | 719 | execution | claimed | `tests/unit/test_settlement_windows.py:153` | DST: W_start/W_end and the t0 grid map correctly to UTC in both transition weeks.<br>**Note:** D586. The DST test's own docstring. |
| 14 | 720 | arithmetic | claimed | `tests/golden/test_ledger_funds_ledger.py:128` `test_ledger_14_inav_zero_move_is_nav_times_one_plus_accruals` | iNAV with zero futures move equals NAV[t−1] × (1 + accruals); with L = 2 and r = +1% it rises about 2%; with L = −2 it falls about 2%.<br>**Note:** D611. |
| 15 | 721 | arithmetic | claimed | `tests/unit/test_ledger_premium.py:61` `test_ledger_15_the_premium_reads_the_midpoint_and_never_the_last_trade` | Premium uses the NBBO midpoint: a synthetic series with trades at the ask but a constant mid shows zero premium.<br>**Note:** D611. |
| 16 | 722 | data_guard | claimed | `tests/unit/test_ledger_premium.py:92` `test_ledger_16_a_stale_or_futureless_minute_is_excluded_from_all_features` | Stale-minute exclusion: an ETF quote not updated for more than 60 s, or a futures minute with no trade, is excluded from all features.<br>**Note:** D611. |
| 17 | 723 | leak | claimed | `tests/unit/test_ledger_premium.py:129` `test_ledger_17_no_premium_feature_uses_a_minute_at_or_after_w_start` | No premium feature uses any minute at or after W_start.<br>**Note:** D611. |
| 18 | 724 | arithmetic | claimed | `tests/unit/test_ledger_funds.py:179` `test_ledger_18_h_is_in_the_open_interval_and_non_increasing_in_stress` | h is in (0, 1) and non-increasing in stress when h1 ≥ 0.<br>**Note:** D611. |
| 19 | 725 | arithmetic | claimed | `tests/unit/test_ledger_funds.py:206` `test_ledger_19_the_creation_sign_comes_from_the_leverage` | Creation sign: a KOLD (L = −2) creation gives negative Create_flow (the fund sells futures); a BOIL creation gives positive.<br>**Note:** D611. |
| 20 | 726 | arithmetic | claimed | `tests/golden/test_ledger_funds_ledger.py:182` `test_ledger_20_gate_0b_reproduces_the_hand_calculated_error` | Gate 0b check reproduces a hand-calculated iNAV-vs-NAV error for a synthetic fund.<br>**Note:** D611. |
| 21 | 727 | leak | claimed | `tests/unit/test_attention.py:318` `test_ledger_21_zscores_use_only_the_prior_sixty_matched_days` | Attention z-scores on day t use only data from days t−60 … t−1 for the same hour-of-day and day-of-week.<br>**Note:** D612. |
| 22 | 728 | leak | claimed | `tests/unit/test_attention.py:186` `test_ledger_22_an_hourly_pageview_is_unavailable_at_1410_and_available_at_1415` | Publication-time guard: an hourly pageview for 13:00–14:00 is unavailable at τ = 14:10 and available at τ = 14:15 or later.<br>**Note:** D612. |
| 23 | 729 | leak | claimed | `tests/unit/test_attention.py:216` `test_ledger_23_gdelt_items_are_keyed_on_publication_not_event_time` | GDELT items are keyed on publication timestamp; items published after τ are excluded even if their event time is earlier.<br>**Note:** D612. |
| 24 | 730 | arithmetic | claimed | `tests/unit/test_attention.py:373` `test_ledger_24_att_accel_is_positive_on_a_ramp_and_zero_once_flat` | `att_accel` on a synthetic step increase in attention is positive during the ramp and returns to about zero once the level is flat.<br>**Note:** D612. |
| 25 | 731 | rendering | claimed | `tests/unit/test_attention.py:79` `test_ledger_25_query_lists_load_from_queries_md_and_hash` | Query lists are loaded from `QUERIES.md` and hashed. The hash is stored with every trial in `trials.csv`.<br>**Note:** D612. 1 more test_ledger_25_* function(s) in the same file. |
| 26 | 732 | arithmetic | claimed | `tests/golden/test_ledger_funds_ledger.py:287` `test_ledger_26_the_p9_rebalance_is_twelve_and_twenty_four_million` | P9 formula: a +3× product with AUM $50m and r = +4% gives ΔH = +$12m; a −3× product gives +$24m (same sign as the move).<br>**Note:** D611. |
| 27 | 733 | leak | claimed | `tests/unit/test_ledger_non_us.py:121` `test_ledger_27_fx_uses_the_prior_settlement_and_never_the_current_day` | FX conversion uses the rate at the prior settlement, never the current day's.<br>**Note:** D611. |
| 28 | 734 | data_guard | claimed | `tests/unit/test_ledger_non_us.py:148` `test_ledger_28_flow_maps_to_each_products_own_index_contract_month` | P9 flow is mapped to each product's own index contract month (2nd-front for WisdomTree NG, front for BetaPro).<br>**Note:** D611. |
| 29 | 735 | arithmetic | claimed | `tests/golden/test_ledger_funds_ledger.py:333` `test_ledger_29_the_restrike_fires_at_six_point_seven_and_not_at_six_point_five` | Restrike detection: for a +3× product, a synthetic −6.7% underlying move from the prior reset triggers a restrike; −6.5% doesn't. After a restrike, the settlement ΔH is computed from the restrike level.<br>**Note:** D611. |
| 30 | 736 | data_guard | claimed | `tests/unit/test_ledger_non_us.py:168` `test_ledger_30_a_missing_published_notional_uses_stated_l_and_flags_the_day` | BetaPro L_eff: when published notional is missing for a day, stated L is used and the day is flagged.<br>**Note:** D611. |
| 31 | 737 | rendering | claimed | `tests/unit/test_recorder.py:141` `test_ledger_31_a_second_record_never_overwrites` | Recorder never overwrites: a second fetch on the same day creates a new file; checksums differ only if content differs.<br>**Note:** D608. Also claimed in tests/golden/test_recorder_ledger.py and, as a property, in tests/property/test_recorder_property.py. |
| 32 | 738 | leak | claimed | `tests/unit/test_recorder.py:328` `test_ledger_32_availability_is_fetched_at` | Recorder availability: a forward test reading a record uses `fetched_at`, not `published_at`, as the time it became usable.<br>**Note:** D608. Also claimed in tests/golden/test_recorder_ledger.py and in tests/property/test_recorder_property.py. |
| 33 | 739 | data_guard | claimed | `tests/unit/test_recorder.py:482` `test_ledger_33_a_missed_daily_window_is_flagged` | Gap detection flags a missed daily job, and no downstream code fills the gap.<br>**Note:** D608. Five test_ledger_33_* functions here and four more in tests/golden/test_recorder_ledger.py. |
| 34 | 740 | data_guard | claimed | `tests/unit/test_frozen.py:215` `test_ut34_assert_frozen_is_silent_when_nothing_moved` | Frozen-protocol guard: evaluation code refuses to run if the parameters differ from `FROZEN_<stage>.json`.<br>**Note:** D594. Seven test_ut34_* functions; the first is the claim site. |
| 35 | 741 | arithmetic | claimed | `tests/golden/test_track3_ledger.py:102` `test_ledger_35_shortfall_sign_long_and_short_hand_ticks` | Implementation shortfall sign: a long filled 2 ticks above the model price records +2 ticks of shortfall; a short filled 2 ticks below records +2.<br>**Note:** D605. The ticks case; the dollar case is the next function, at line 116. |
| 36 | 742 | statistical | claimed | `tests/golden/test_track3_ledger.py:248` `test_ledger_36_futility_stops_at_n100_only_when_mean_negative_and_t_below_minus_one` | Futility rule: synthetic trade series trigger a stop at N = 100 only when mean < 0 and t < −1.<br>**Note:** D605. Under the banner at line 236; the N = 99 boundary case is at line 273. |
| 37 | 743 | execution | claimed | `tests/unit/test_ledger_rolls.py:39` `test_ledger_37_ung_rolls_four_days_at_25_percent_from_two_weeks_before_expiry` | UNG roll fractions: four days at 25% each; cumulative 100%; day 1 starts two weeks before near-month expiration per the rule.<br>**Note:** D610. |
| 38 | 744 | execution | claimed | `tests/golden/test_ledger_flows_ledger.py:138` `test_ledger_38_roll_legs_sign_and_the_price_scaling` | Roll sign: a long fund's roll sells the expiring month and buys the next; an inverse fund does the reverse. New-month contracts are scaled by P_old / P_new.<br>**Note:** D610. |
| 39 | 745 | data_guard | claimed | `tests/unit/test_ledger_rolls.py:109` `test_ledger_39_holdings_at_25_percent_a_day_pass_and_one_big_day_falls_back_to_p8b` | Roll validation: synthetic holdings changing by 25% per day across the window pass; holdings that change all on one day fail and trigger the P8b fallback.<br>**Note:** D610. |
| 40 | 746 | arithmetic | claimed | `tests/unit/test_ledger_rolls.py:151` `test_ledger_40_a_fund_counted_in_p8a_contributes_exactly_zero_to_p8b` | No double counting: a fund in P8a contributes zero to P8b.<br>**Note:** D610. |
| 41 | 747 | leak | claimed | `tests/unit/test_ledger_netting.py:67` `test_ledger_41_a_cot_week_is_usable_only_from_its_friday_release` | COT availability: a weekly record is usable only at or after its Friday release timestamp.<br>**Note:** D610. |
| 42 | 748 | statistical | claimed | `tests/golden/test_ledger_flows_ledger.py:174` `test_ledger_42_lambda_is_projected_onto_the_unit_interval_and_the_flag_fires` | The swap-dealer fit constrains λ to [0, 1]; the consistency flag triggers when \|n_flow − (1 − λ̂)\| > 2 combined SE.<br>**Note:** D610. |
| 43 | 749 | data_guard | claimed | `tests/unit/test_ledger_netting.py:124` `test_ledger_43_the_swap_predictor_never_sees_futures_held_exposure` | The swap-exposure predictor includes only swap-routed exposure (1 − f_fut) and P9, never futures-held exposure.<br>**Note:** D610. |
| 44 | 750 | leak | claimed | `tests/unit/test_ledger_netting.py:167` `test_ledger_44_swap_records_are_keyed_on_dissemination_not_execution` | Swap dissemination records are keyed on dissemination time, not execution time, for any predictive use.<br>**Note:** D610. |
| 45 | 751 | leak | claimed | `tests/unit/test_futures_impact.py:219` `test_ledger_45_depth_bar_takes_the_trailing_prior_days` | MBO depth is measured at the t0 bar close within ±5 ticks; D̄ uses prior days only.<br>**Note:** D604. Under the banner at line 212. tests/unit/test_fut_book_depth.py repeats it against the order-book panel and is fixture-gated, so it can skip. |
| 46 | 752 | arithmetic | claimed | `tests/unit/test_futures_impact.py:161` `test_ledger_46_and_index_18_i_d_equals_i_when_depth_equals_depth_bar` | I_D equals I when D(t0) = D̄.<br>**Note:** D604. One function discharges ledger 46 AND index 18; the function-name convention carries only the first number, which is why index 18 is claimed by a docstring instead. |
| 47 | 753 | leak | claimed | `tests/unit/test_ledger_flows.py:200` `test_ledger_47_large_lot_threshold_is_prior_days_only_and_ties_count_as_large` | Large-lot threshold uses the trailing 20 prior days only; trades exactly at L_min count as large.<br>**Note:** D610. |
| 48 | 754 | statistical | claimed | `tests/golden/test_error_budget_ledger.py:168` `test_ledger_48_zero_contribution_term_changes_oos_mse_by_exactly_zero` | Error budget: removing a term with zero forecast contribution changes OOS MSE by zero on synthetic data.<br>**Note:** D606. Also asserted in tests/unit/test_error_budget.py, on the exactness of the zero. |
| 49 | 755 | data_guard | claimed | `tests/golden/test_error_budget_ledger.py:327` `test_ledger_49_reordered_stage_without_a_log_entry_is_refused` | Stage reordering: the code refuses to run a reordered stage unless a matching decision-log entry exists.<br>**Note:** D606. Also asserted in tests/unit/test_error_budget.py, on a near-miss log entry. |
| 50 | 756 | leak | claimed | `tests/unit/test_fund_panel.py:303` `test_ledger_50_options_oi_is_joined_at_the_prior_days_publication` | Options open interest by strike is joined point-in-time (the prior day's published values only).<br>**Note:** D619. 2 more test_ledger_50_* function(s) in the same file. |
| 51 | 757 | statistical | claimed | `tests/unit/test_power.py:51` `test_ledger_51_design_effect_m10_rho01_gives_n_over_1p9` | Design effect: m = 10 and ρ = 0.1 give n_eff = n / 1.9.<br>**Note:** D588. |
| 52 | 758 | statistical | claimed | `tests/unit/test_power.py:59` `test_ledger_52_mde_calculation_at_n_eff_2500` | MDE calculation: n_eff = 2,500 gives SE = 0.02, MDE_t2 = 0.04, MDE_80 = 0.056.<br>**Note:** D588. |
| 53 | 759 | statistical | claimed | `tests/unit/test_power.py:74` `test_ledger_53_underpowered_stage_blocks_adoption_by_significance` | A stage whose MDE exceeds its recorded plausible effect is labelled underpowered, and adoption by individual significance is blocked.<br>**Note:** D588. |
| 54 | 760 | statistical | declined | `docs/decisions/D588-power-analysis-module.md:152` | Marginal-contribution regression includes all retained terms; VIF > 5 triggers the confounding flag.<br>*Marginal-contribution regression with a VIF confounding flag*<br>**Note:** DECLINED in D588: the rule-4 marginal-contribution regression and its VIF flag need a regression, not planning arithmetic, and belong with the study that runs them. |
| 55 | 761 | statistical | declined | `docs/decisions/D588-power-analysis-module.md:154` | Parameter recovery harness: on synthetic data with known p, h, n, the estimator's recovery rate is computed and compared with the 80% / ±0.15 rule.<br>*Parameter recovery against the 80% within 0.15 rule*<br>**Note:** DECLINED in D588 with tests 56-58: the section 9B toolkit needs a simulator. |
| 56 | 762 | statistical | declined | `docs/decisions/D588-power-analysis-module.md:154` | Decision-relevance metric: the share of changed take/skip or direction decisions across a parameter range is computed correctly on a synthetic case.<br>*Share of decisions changed across a parameter range*<br>**Note:** DECLINED in D588 with tests 55, 57 and 58: the section 9B toolkit. |
| 57 | 763 | statistical | declined | `docs/decisions/D588-power-analysis-module.md:154` | P9 scale check: forecast variance share vs P1 computed correctly; below 5% excludes P9.<br>*P9's forecast variance share gates its inclusion*<br>**Note:** DECLINED in D588 with tests 55, 56 and 58: the section 9B toolkit. |
| 58 | 764 | statistical | declined | `docs/decisions/D588-power-analysis-module.md:154` | Restrike calibration: realised/predicted ratio CI and sign share computed correctly; restrike trades are never generated.<br>*Restrike calibration ratio CI and sign share, never traded*<br>**Note:** DECLINED in D588 with tests 55-57: the section 9B toolkit. |
| 59 | 765 | statistical | claimed | `tests/unit/test_power.py:110` `test_ledger_59_forward_evaluation_length_and_the_cap` | Forward evaluation length: plausible effect 0.1 with 2 instruments gives n_needed = 400 and 200 evaluation days; a plausible effect of 0.05 gives n_needed = 1,600, exceeds the cap, and routes the stage to 9B.<br>**Note:** D588. |
| 60 | 766 | data_guard | claimed | `tests/unit/test_frozen.py:286` `test_ut60_evaluation_length_cannot_be_extended` | The evaluation length in `FROZEN_<stage>.json` can't be changed after evaluation starts (code refuses).<br>**Note:** D594. |
| 61 | 767 | statistical | **unclaimed** | — | Forward consistency test: passes when the forward estimate lies inside the Track 1 90% CI with the same sign; fails otherwise.<br>*The forward estimate must sit inside the Track 1 interval with its sign*<br>**Note:** NOT COVERED. validation/power.py:464 says 'consistency check' in a docstring about the Track 3 route; that is a phrase, not an assertion, and nothing compares a forward estimate with a Track 1 interval. |
| 62 | 768 | statistical | claimed | `tests/unit/test_power.py:138` `test_ledger_62_track3_power_check_routes_on_the_edge_estimate` | Track 3 power check: an edge estimate of 0.08σ selects the combined-evidence route; 0.15σ selects the N = 300 efficacy route.<br>**Note:** D588. |
| 63 | 769 | rendering | claimed | `tests/unit/test_power.py:155` `test_ledger_63_track_map_validation_names_the_missing_statement` | `TRACK_MAP.md` validation: every stage has a track, a power class, n_eff, SE, MDE and a plausible-effect statement before it runs.<br>**Note:** D588. |
| 64 | 770 | data_guard | claimed | `tests/unit/test_frozen.py:398` `test_ut64_opening_without_a_frozen_model_is_refused` | Vault guard: the loader raises on any date from 2025-03-01 to 2026-09-18 unless `FROZEN_VAULT.json` exists and the vault-open flag is set.<br>**Note:** D594. Three test_ut64_* functions under the banner at line 397. |
| 65 | 771 | data_guard | claimed | `tests/unit/test_frozen.py:426` `test_ut65_the_opening_is_logged_and_a_second_one_is_refused` | One-shot vault: a second vault opening for the same model is refused and logged.<br>**Note:** D594. Two test_ut65_* functions under the banner at line 397. |
| 66 | 772 | statistical | claimed | `tests/unit/test_programme.py:53` | Programme registry: a family's promotion check uses α = 0.005; registering an eighth to tenth family uses a reserved slot; an eleventh is refused without a doc amendment.<br>**Note:** D592. A section banner; no function name carries the number. |
| 67 | 773 | statistical | claimed | `tests/unit/test_programme.py:203` | Programme DSR: the trial count equals the total rows across all docs' `trials.csv` files.<br>**Note:** D592. A section banner; no function name carries the number. |
| 68 | 774 | statistical | claimed | `tests/unit/test_programme.py:377` | Haircut: sizing and the Track 3 power check use 50% of the walk-forward edge, or the vault estimate if lower.<br>**Note:** D592. A section banner; no function name carries the number. |
| 69 | 775 | statistical | claimed | `tests/golden/test_episodes_ledger.py:4` | Episode checks: removing the best year and the best 1% of days are computed correctly on synthetic P&L.<br>**Note:** D592. A module docstring sentence; the doc named nearest it is the opening document, so the number's owner is not machine-decidable here. |
| 70 | 776 | leak | claimed | `tests/unit/test_lookahead.py:325` | One-bar-delay rerun shifts every signal by exactly one bar and reports the retained edge fraction.<br>**Note:** D593. The docstring of test_retained_edge_reports_a_number_and_not_a_verdict. |
| 71 | 777 | leak | claimed | `tests/unit/test_lookahead.py:379` | Leak canary: a feature built from bar t+1 is rejected by the static no-future-data check.<br>**Note:** D593. One docstring claims ledger 71 and opening 25 together. |

### Index reweight flow — `INDEX_REWEIGHT_FLOW_PREREG.md`

Section 13. Required unit tests, heading at line 347, items at lines 349–376. **6 of 28 claimed (21.4%).**

| # | Line | Class | Status | Claim | Item |
|---:|---:|---|---|---|---|
| 1 | 349 | arithmetic | **unclaimed** | — | Drifted weights sum to 1 at every date.<br>*Drifted weights sum to one at every date* |
| 2 | 350 | arithmetic | **unclaimed** | — | If all components' sub-indices move by the same factor, the drifted weights stay equal to the prior targets.<br>*A common factor move leaves drifted weights at their prior targets* |
| 3 | 351 | arithmetic | **unclaimed** | — | A component that doubles relative to the rest gets a higher drifted weight, and its ΔN is negative when its target is unchanged.<br>*A doubling component gains weight and its share change turns negative* |
| 4 | 352 | arithmetic | **unclaimed** | — | **Drift beats headline:** a synthetic case where the target falls but the drifted weight fell further gives **positive** ΔN (trackers buy).<br>*A target that falls less than the drift still buys* |
| 5 | 353 | arithmetic | **unclaimed** | — | Contract conversion: AUM $100bn, weight gap +0.5%, price 50, multiplier 1,000 gives +10,000 contracts.<br>*Weight gap to contract count at a stated price and multiplier* |
| 6 | 354 | arithmetic | **unclaimed** | — | Daily split: ΔN_i,d sums to ΔN_i across execution days per the verified fractions.<br>*Daily share changes sum to the total across execution days* |
| 7 | 355 | arithmetic | **unclaimed** | — | Full-index net dollar flow ≈ 0 (within tolerance) on a synthetic 25-component index.<br>*Net dollar flow across a synthetic full index is about zero* |
| 8 | 356 | leak | **unclaimed** | — | No prices after the determination date are used in ΔN computed for that date.<br>*No price after the determination date enters that date's flow* |
| 9 | 357 | leak | claimed | `tests/unit/test_folds.py:131` | Leave-one-year-out guard: a model evaluated on year y was not fitted using year y data.<br>**Note:** D593. An assertion message naming the document by file name; tests/golden/test_folds_ledger.py:125 and tests/property/test_lookahead_property.py:201 repeat the claim. |
| 10 | 358 | arithmetic | **unclaimed** | — | Construction B: the inverse-volatility-weighted long and short books have equal risk within 1%.<br>*The two inverse-volatility legs carry equal risk within one percent* |
| 11 | 359 | execution | **unclaimed** | — | Construction B timing: each leg exits at its own product's W_end; the common entry precedes the earliest chosen window.<br>*Each leg exits at its own window; entry precedes the earliest*<br>**Note:** NOT COVERED. D586-FIXTURE-cme-settlement-windows-with-effective-dates.md:58 supplies the data this test needs -- the three COMEX metals settle three hours apart from ES -- and names the test, but asserts nothing about legs or entry ordering. |
| 12 | 360 | data_guard | claimed | `tests/unit/test_settlement_windows.py:3` | Settlement windows are taken from the sourced table only; an unmapped product raises an error.<br>**Note:** D586. The module docstring; the assertions are at lines 93, 99 and 209 and none of them names the number. |
| 13 | 361 | data_guard | **unclaimed** | — | Excluded-year rule: a year with more than 10% index weight in missing-price components is excluded.<br>*A year with over ten percent missing-price weight is excluded* |
| 14 | 362 | leak | **unclaimed** | — | CIT and COT records are usable only at or after their Friday release timestamp.<br>*CIT and COT records are usable only from their Friday release* |
| 15 | 363 | leak | **unclaimed** | — | κ_CIT fit uses only weeks before the evaluation period (walk-forward), and is restricted to covered ag contracts.<br>*The CIT coefficient is fitted walk-forward on covered ag only* |
| 16 | 364 | statistical | **unclaimed** | — | The consistency flag triggers when \|κ_flow − κ_CIT\| > 2 combined SE.<br>*The consistency flag fires past two combined standard errors* |
| 17 | 365 | data_guard | **unclaimed** | — | The swap-dealer proxy is never used as a prior unless the R-D12 agreement condition is met.<br>*The swap-dealer proxy is a prior only under the agreement condition* |
| 18 | 366 | arithmetic | claimed | `tests/golden/test_futures_impact_ledger.py:205` | I_D equals I when D(t0) = D̄; depth is measured within ±5 ticks at the t0 bar close.<br>**Note:** D604. The docstring of test_ledger_46_and_index_18_the_depth_identity_is_exact (line 203). No function name spells index 18. |
| 19 | 367 | statistical | claimed | `tests/unit/test_error_budget.py:91` `test_index_19_zero_contribution_component_leaves_oos_error_unchanged` | Error budget: removing a zero-contribution component leaves OOS error unchanged on synthetic data.<br>**Note:** D606. Claimed again beside ledger 48 in tests/golden/test_error_budget_ledger.py. |
| 20 | 368 | data_guard | claimed | `tests/unit/test_error_budget.py:444` `test_index_20_stage_reordering_requires_a_matching_decision_log_entry` | Stage reordering requires a matching decision-log entry.<br>**Note:** D606. Claimed again beside ledger 49 in tests/golden/test_error_budget_ledger.py. |
| 21 | 369 | statistical | **unclaimed** | — | Design effect with 10 year clusters computed from the observed within-year correlation.<br>*Design effect from the observed within-year correlation over ten clusters* |
| 22 | 370 | statistical | **unclaimed** | — | Yearly sign test: 9 of 10 positive gives one-sided binomial p ≈ 0.011 (pass); 8 of 10 gives p ≈ 0.055 (fail).<br>*Yearly sign test binomial p-values at nine and eight of ten* |
| 23 | 371 | data_guard | **unclaimed** | — | Yearly Spearman uses only traded commodities with valid data for that year.<br>*The yearly Spearman uses only traded commodities with valid data* |
| 24 | 372 | statistical | **unclaimed** | — | Calibration ratio CI computed by bootstrap over years; pass requires overlap with [0.5, 2].<br>*Bootstrap calibration ratio CI must overlap the stated band* |
| 25 | 373 | statistical | **unclaimed** | — | Adoption logic requires all three checks (pooled, sign test, calibration).<br>*Adoption requires the pooled test, the sign test and calibration* |
| 26 | 374 | statistical | **unclaimed** | — | With 11 years, 9 positive votes pass (p ≈ 0.033) and 8 fail (p ≈ 0.113).<br>*Sign-test p-values at nine and eight of eleven years* |
| 27 | 375 | leak | **unclaimed** | — | The 2027 consistency test uses Track 1 intervals computed only from 2016–2026.<br>*The 2027 consistency test uses intervals from 2016 to 2026 only* |
| 28 | 376 | statistical | claimed | `tests/golden/test_track3_ledger.py:319` | Track 3 January trades are never counted as independent efficacy evidence.<br>**Note:** D605. A docstring; tests/unit/test_track3.py repeats the number inside an efficacy_reason string. No function name carries it. |

### Opening agent state — `OPENING_AGENT_STATE_PREREG.md`

Section 15. Required unit tests, heading at line 334, items at lines 336–360. **6 of 25 claimed (24.0%).**

| # | Line | Class | Status | Claim | Item |
|---:|---:|---|---|---|---|
| 1 | 336 | arithmetic | **unclaimed** | — | Labels: synthetic sessions reproduce each rule in order (CONT/REV before FADE before RANGE).<br>*Synthetic sessions reproduce every labelling rule in its order* |
| 2 | 337 | leak | claimed | `tests/unit/test_lookahead.py:500` | Labels never enter features (static check on the feature pipeline).<br>**Note:** D593. One docstring claims opening 2 and 19 together. |
| 3 | 338 | data_guard | **unclaimed** | — | d0 = 0 gives an unclassified, untraded day.<br>*A zero opening displacement gives an unclassified, untraded day* |
| 4 | 339 | arithmetic | **unclaimed** | — | A1: open above the prior high gives positive pressure scaled by ATR; inside the range gives 0.<br>*Gap pressure scales with ATR and is zero inside the range* |
| 5 | 340 | arithmetic | **unclaimed** | — | A2: a known price path gives the hand-calculated target change across L ∈ {20, 60, 120}.<br>*Trend-follower target change hand-calculated at three lookbacks* |
| 6 | 341 | arithmetic | **unclaimed** | — | A3: exposure capped at 2; rising σ20 gives negative pressure.<br>*Volatility-target exposure is capped and falls as sigma rises* |
| 7 | 342 | arithmetic | **unclaimed** | — | A4: dealer gamma sign follows the pre-registered positioning assumption; zero overnight move gives zero pressure.<br>*Dealer gamma sign follows positioning; zero move gives zero* |
| 8 | 343 | leak | **unclaimed** | — | A5: zero on non-release days; uses only data to 09:25.<br>*Macro pressure is zero off release days and reads only to 09:25* |
| 9 | 344 | leak | **unclaimed** | — | A6: fair ratio uses prior days' 15:59 values only; computed no earlier than the first SPY print after 09:30.<br>*The index-arbitrage fair ratio uses prior closes and the first print* |
| 10 | 345 | leak | **unclaimed** | — | A7: large-lot threshold uses prior 20 days only.<br>*The large-lot threshold uses the prior twenty days only* |
| 11 | 346 | leak | **unclaimed** | — | Standardisation uses the prior 250 sessions only.<br>*Standardisation uses the prior two hundred and fifty sessions* |
| 12 | 347 | arithmetic | **unclaimed** | — | Direction-relative transformation: flipping all prices (a mirror-image day) leaves direction-relative features and labels unchanged.<br>*A mirrored day leaves direction-relative features and labels unchanged* |
| 13 | 348 | data_guard | claimed | `tests/golden/test_error_budget_ledger.py:230` `test_opening_13_parameter_budget_refuses_twelve_features` | Parameter budget: the pipeline refuses to fit a stage exceeding 11 features.<br>**Note:** D606. The parameter-budget refusal, proved on a twelfth feature. |
| 14 | 349 | execution | **unclaimed** | — | Policy: argmax RANGE or max(p) < θ produces no trade; FADE trades towards the prior close.<br>*RANGE or a low maximum probability stands aside; FADE trades homeward* |
| 15 | 350 | execution | **unclaimed** | — | State-flip exit triggers when the traded state's probability falls below 0.30 at the next checkpoint.<br>*The state-flip exit fires below the stated probability at a checkpoint* |
| 16 | 351 | statistical | **unclaimed** | — | Pooled n_eff uses the estimated same-day ES/NQ correlation.<br>*Pooled effective sample size uses the same-day ES/NQ correlation* |
| 17 | 352 | execution | **unclaimed** | — | DST: 09:30 ET maps correctly to UTC in both transition weeks.<br>*The cash open maps to UTC in both DST transition weeks* |
| 18 | 353 | data_guard | claimed | `tests/unit/test_frozen.py:397` | Vault guard covers ES, NQ, SPY, QQQ and ES/NQ options data for 2025-03-01 → 2026-09-18.<br>**Note:** D594. A section banner whose parenthesis carries opening 18 and 20; the function names below it spell the ledger numbers only. |
| 19 | 354 | leak | claimed | `tests/unit/test_lookahead.py:500` | Label frequency reports and power estimates use in-sample dates only (static check).<br>**Note:** D593. One docstring claims opening 2 and 19 together. |
| 20 | 355 | data_guard | claimed | `tests/unit/test_frozen.py:397` | One-shot vault opening, logged; a second opening refused.<br>**Note:** D594. A section banner whose parenthesis carries opening 18 and 20. |
| 21 | 356 | statistical | covered via | → Settlement flow ledger 66 | H-O2 promotion check uses programme α = 0.005 from the shared registry.<br>*The promotion check uses the programme alpha from the registry*<br>**Note:** The opening document's restatement of the ledger's registry test; no test names the opening number. |
| 22 | 357 | statistical | covered via | → Settlement flow ledger 67 | Programme DSR uses the programme-wide trial count.<br>*The programme DSR uses the programme-wide trial count*<br>**Note:** The opening document's restatement of the ledger's programme-DSR test; no test names the opening number. |
| 23 | 358 | statistical | covered via | → Settlement flow ledger 68 | Haircut applied to sizing and the Track 3 power check.<br>*The haircut applies to sizing and the Track 3 power check*<br>**Note:** The opening document's restatement of the ledger's haircut test; no test names the opening number. |
| 24 | 359 | statistical | covered via | → Settlement flow ledger 69 | Episode checks (best year, best 1% of days) and one-bar-delay rerun computed correctly.<br>*Episode checks and the one-bar-delay rerun are computed correctly*<br>**Note:** The opening document's restatement of the ledger's episode test AND of ledger 70, the one-bar-delay rerun; no test names the opening number. |
| 25 | 360 | leak | claimed | `tests/unit/test_lookahead.py:379` | Leak canary: a feature using any bar after t0 is rejected.<br>**Note:** D593. One docstring claims ledger 71 and opening 25 together. |

### Shock classifier — `SHOCK_CLASSIFIER_PREREG.md`

Section 9. Required unit tests, heading at line 293, items at lines 295–307. **2 of 13 claimed (15.4%).**

| # | Line | Class | Status | Claim | Item |
|---:|---:|---|---|---|---|
| 1 | 295 | leak | **unclaimed** | — | `σ_tod` on day t uses only days t−60 … t−1 (look-ahead test).<br>*Time-of-day sigma uses only the prior sixty days* |
| 2 | 296 | leak | **unclaimed** | — | Peer β and ρ on day t use only days t−60 … t−1.<br>*Peer beta and correlation use only the prior sixty days* |
| 3 | 297 | arithmetic | **unclaimed** | — | Shock detection: a synthetic 5σ one-minute jump triggers; a 3σ jump doesn't at z = 4.<br>*A five-sigma jump triggers; a three-sigma jump does not* |
| 4 | 298 | execution | **unclaimed** | — | Cooldown: a second jump 30 min after the first is ignored; one at 61 min is detected.<br>*A second jump inside the cooldown is ignored, outside it detected* |
| 5 | 299 | arithmetic | **unclaimed** | — | Confirmation ratio: a peer with β = 0.5 moving exactly 0.5 × own gives C_j = 1. A negatively correlated peer (β = −0.3) moving −0.3 × own also gives C_j = 1.<br>*Confirmation ratio is one for positively and negatively loaded peers* |
| 6 | 300 | data_guard | **unclaimed** | — | A peer with \|ρ\| < 0.3 is excluded; fewer than 2 valid peers gives class NONE.<br>*Weak peers are dropped and too few peers give class NONE* |
| 7 | 301 | arithmetic | **unclaimed** | — | Classification truth table, including the event override (event and C = 0.35 gives INFO; event and C = 0.1 gives NONE).<br>*The classification truth table including the event override* |
| 8 | 302 | execution | **unclaimed** | — | Trade direction: INFO follows d; LIQ opposes d.<br>*INFO trades with the move; LIQ trades against it* |
| 9 | 303 | execution | claimed | `tests/golden/test_futures_fills_ledger.py:99` | Intra-bar pessimism: a bar spanning both the stop and target records the stop.<br>**Note:** D587. One docstring claims ledger 11 and shock 9 together. |
| 10 | 304 | execution | claimed | `tests/golden/test_futures_fills_ledger.py:80` | Stress fill picks the worst close among t0+1 … t0+5 for the trade direction.<br>**Note:** D587. The docstring of test_stress_fill_picks_the_worst_close_for_the_direction. |
| 11 | 305 | data_guard | **unclaimed** | — | Session windows: shocks outside Section 3.3 windows and on roll days are excluded.<br>*Shocks outside the session windows and on roll days are excluded* |
| 12 | 306 | execution | **unclaimed** | — | DST: window boundaries map correctly to UTC in both transition weeks.<br>*Window boundaries map to UTC in both DST transition weeks* |
| 13 | 307 | data_guard | **unclaimed** | — | Event window: a shock at release + 5 min is flagged; one at release + 6 min is not.<br>*A shock inside the event window is flagged; just outside is not* |

### LETF close flow — `LETF_CLOSE_FLOW_PREREG.md`

Section 8. Required unit tests, heading at line 242, items at lines 244–252. **0 of 9 claimed (0.0%).**

| # | Line | Class | Status | Claim | Item |
|---:|---:|---|---|---|---|
| 1 | 244 | arithmetic | **unclaimed** | — | `rebalance_flow(L=3, A=1e9, r=0.02)` = +1.2e8.<br>*Rebalance flow at leverage three and a two percent move* |
| 2 | 245 | arithmetic | **unclaimed** | — | `rebalance_flow(L=-3, A=1e9, r=0.02)` = +2.4e8 (same sign as the move).<br>*An inverse product's flow carries the same sign as the move* |
| 3 | 246 | arithmetic | **unclaimed** | — | `rebalance_flow(L=2, A=1e9, r=-0.01)` = −2e7.<br>*A negative move at leverage two gives negative flow* |
| 4 | 247 | arithmetic | **unclaimed** | — | Zero return gives zero flow for all L.<br>*A zero return gives zero flow at every leverage* |
| 5 | 248 | leak | **unclaimed** | — | Point-in-time guard: the AUM used on day t equals the stored value for t−1, and never t.<br>*The AUM used on day t is the stored prior-day value* |
| 6 | 249 | leak | **unclaimed** | — | The rolling V and σ_d on day t use no data from day t or later (look-ahead test).<br>*Rolling volume and sigma read no data from day t onward* |
| 7 | 250 | arithmetic | **unclaimed** | — | Contract conversion: Q_usd = 1e7 at NQ price 25,000 gives 20 contracts.<br>*Dollar notional to contract count at a stated price* |
| 8 | 251 | execution | **unclaimed** | — | DST: 15:00 ET maps correctly to UTC in both March and November transition weeks.<br>*The close maps to UTC in both DST transition weeks* |
| 9 | 252 | data_guard | **unclaimed** | — | Early-close sessions are excluded from the trade calendar.<br>*Early-close sessions are excluded from the trade calendar* |

---

## What a future agent does

1. Pick an **unclaimed** row above. Its paraphrase is the handle and its verbatim text is the specification; the deposit document is not needed to read either.
2. Write the test with the number in the function name: `test_ledger_29_restrike_triggers_at_the_threshold`.
3. Add the row's claim to `data/deposit_test_map.json` and re-render this page with `uv run python scripts/deposit_test_map.py --render`.
4. `uv run python scripts/deposit_test_map.py --scan` must report zero disagreements, and `--check` must find the claim as a collected pytest node.

A claim that is not in the JSON is invisible to everyone but its author, which is the state this page was written to end.
