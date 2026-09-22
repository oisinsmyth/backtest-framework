# D611 — The fund model is pure algebra with no fund in it, and every absent fact RAISES rather than defaulting

**Status:** Committed
**Date:** 2026-09-22
**Category:** Model
**Source:** `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` (v1.9, untracked,
read-only): Section 3.1 "Fund universe" (lines 58-65), 3.1b "Non-US leveraged commodity ETPs"
(lines 72-84), 3.2 "Fund facts to source and verify (Gate 0)" (lines 86-93), P3.1 iNAV and Gate
0b (lines 181-191), P3.2 premium (lines 193-201), P3.3 features (lines 203-213), P3.4 creations
(lines 215-226), P3.5 hedging split (lines 228-237), P3.7 the attention term (line 271), P9
(lines 276-297), Section 8 constraints (line 472), and required unit tests 4, 14-20 and 26-30
(lines 710, 720-726, 732-736). Builds on D604 (`costs/futures_impact.py`'s shape for quoting a
ledger formula verbatim and refusing at the point of use), D48 (raise loudly, never default),
D39 and CONTRIBUTING.md (the hand ledger), D78/D537 (property-test settings), D550 (newline
pinning), R16 (exact reproduction). Sits in the same package as D610's `flows.py`, `update.py`,
`rolls.py` and `netting.py` and imports none of them.

## Decision

Four library modules under `src/backtest_framework/ledger/` — `funds.py`, `premium.py`,
`creations.py`, `non_us.py` — one script, `scripts/fund_model_selftest.py`, and five test files.
`ledger/__init__.py` is D610's. **No fixture is read, no file under `data/` is written, and no
strategy return is computed.** Every input in every test is either a figure the deposit itself
states or a round illustrative number labelled as such.

### `funds.py` — the six funds, the iNAV, Gate 0b

| | units / contract |
|---|---|
| `Fund(name, L: int, underlying_root, multiplier, currency="USD", er=None, index_month_rule=None)` | frozen; `multiplier` is the held root's contract size in USD per point; `.rebalance_factor` is the INTEGER `L(L-1)` |
| `BOIL KOLD UCO SCO UNG USO`, `US_FUNDS` | lines 60-65 exactly; **`er=None` and `index_month_rule=None` on all six** |
| `NG_MULTIPLIER = 10000.0`, `CL_MULTIPLIER = 1000.0` | `data/futures_contract_specs.json` — "10,000 MMBtu" and "1,000 barrels" |
| `inav(nav_prev, L, r_held, y_cash, er) -> float` | line 184, left to right, ONE day's accrual on two day counts; NAV currency per share; **raises on `er=None`** |
| `gate_0b(inav_at_settle, official_nav, bp_limit=5.0, share=0.95) -> Gate0b` | line 191; `bp_errors` signed, in bp of the OFFICIAL NAV; both comparisons inclusive |

### `premium.py` — the midpoint, the valid minute, the four features, stress

| | units / contract |
|---|---|
| `Quote(bid, ask, last, ts)`, `.mid` | **refuses `bid >= ask` at construction**; `last` is carried and never read |
| `premium(quote, inav) -> float` | line 196; dimensionless fraction of iNAV |
| `valid_minute(quote_age_s, futures_traded) -> bool` | line 200, both clauses, inclusive at 60.0 s |
| `Minute(ts, quote, inav, quote_age_s, futures_traded, volume, signed_volume)` | refuses `\|signed\| > volume`, a non-bool `futures_traded`, a non-positive iNAV |
| `minute_feature(minute, inav) -> float \| None` | `None`, **never 0.0**, for an excluded minute |
| `features(minutes, *, w_start, c_ap=0.001, trailing_volume_mean=None) -> Features` | lines 205-213; `sv_etf` in USD; `vol_x` is `None` without a trailing mean; raises `PremiumWindowError` on any minute at or after `W_start` and on zero valid minutes |
| `stress(prem_twa, trailing, *, day, min_obs=20) -> float` | line 211; `trailing` is `(date, value)` pairs and **an entry dated `day` or later raises**; sd is ddof = 1 |

### `creations.py` — the creation, the lag, the hedged fraction, the split

| | units / contract |
|---|---|
| `delta_create(shares_out, shares_prev, nav)` | line 217, USD |
| `creation_term(lag_c, realised_prev, forecast)` | line 226; `lag_c = 1` is `Q3_known`, `0` is the forecast, anything else raises |
| `hedged_fraction(h0, h1, stress, *, g1=0.0, att_accel=0.0)` | lines 232 and 271; enforces line 472's `h1 >= 0`, `g1 >= 0`; **raises on a saturated logistic** |
| `create_flow(L, delta_create_usd, multiplier, p_held)` | line 231, CONTRACTS of the held month, signed |
| `split(h, flow) -> (q3_window, q3_intraday)` | lines 233-234, as written, not as a residual |

### `non_us.py` — P9

| | units / contract |
|---|---|
| `Product(...)`, the eight of Section 3.1b, `NON_US_PRODUCTS` | every `status` carries line 74's *"indicative, re-source point-in-time"*; every unsourced field is `None` |
| `effective_leverage(published_notional, nav, stated_L) -> (L_eff, flagged)` | line 282, decision D19 |
| `delta_h(aum_usd_prev, L_eff, r_idx)` | line 284, USD of required notional |
| `q9(delta_h_total, n9, multiplier, p_held)` | line 285, contracts; `n9` in [0, 1] |
| `fx_rate_prior(fx_by_day, day)`, `aum_usd(aum_local, fx_by_day, day)` | line 288; the last key STRICTLY before `day`, else raise |
| `index_month(product, curve)` | line 289; front for BetaPro, 2nd-front for WisdomTree NG, raise otherwise |
| `product_value`, `Restrike(threshold=0.20, L=3)`, `.underlying_trigger`, `.check`, `RestrikeEvent`, `RestrikeLog.write(path)` | lines 292-294 |

## Rationale

**The fund model is the one part of this pre-registration that can be built completely today and
tested on nothing.** P1 through P9 are arithmetic; what is missing is every number they consume.
`docs/internal/DEPOSIT_INFRASTRUCTURE_TRACKER.md` lists the point-in-time fund panel, the fund
facts, the P9 products' NAV/units/FX/restrike terms and the ETF NBBO quotes as four separate
missing items, and this repository holds no equities feed at all. So the tests here are hand
calculations not by preference but by necessity, and the hand ledger says so in its preamble
rather than letting a reader assume a fixture was consulted.

**That makes the interesting decisions the REFUSALS, not the formulas.** A module that computes
an iNAV from a plausible expense ratio produces a premium, which produces a stress, which
produces a hedged fraction, which produces a trade — and nothing downstream can tell that the
first number was invented. Section 0 instruction 3 of the deposit is *"Never fabricate data or
facts. This includes fund holdings, creation cut-offs, settlement window times"*, and the way to
make that binding in code rather than in prose (R6) is for the absent fact to stop the
computation at the point of use. Hence: `er=None` on all six funds and `inav` raising on it;
`index_month_rule=None` on 3OIL and 3OIS and `index_month` raising for them;
`restrike_threshold=None` on the three WisdomTree lines the table marks "verify";
`trailing_volume_mean=None` giving `vol_x=None` rather than 1.0; `minute_feature` returning
`None` rather than 0.0; `n9` with no default at all.

**Seven readings the document does not fix, each made once and recorded.**

1. **Gate 0b's error is a fraction of the OFFICIAL NAV.** Line 191 writes
   `|iNAV - official NAV| <= 5 bp` and does not say what the 5 bp is of. At the limit the two
   candidate denominators differ by 5 parts in 10,000 of each other, so the choice moves a
   measured error by 0.0025 bp; it could only decide a day already sitting on the boundary to
   four decimal places. The official NAV is the published number and the conventional
   denominator, and the docstring says so where a reader will hit it.
2. **Both of Gate 0b's comparisons are inclusive**, and the hand case is built on the second
   boundary deliberately: 19 of 20 is exactly 0.95 and passes. A `>` would fail the case line
   191 permits, and 19/20 is exactly representable so nothing rounds.
3. **"Within the last 60 s" is inclusive.** Required unit test 16 excludes a quote "not updated
   for MORE than 60 s"; taking `<= 60.0` as valid is the reading on which line 200 and the test
   agree.
4. **`prem_twa` is the simple mean over valid minutes.** The minutes are equal length, so the
   time weighting is a constant and reduces to the mean — and `features` refuses a repeated or
   out-of-order timestamp so that a duplicated minute cannot double-weight itself quietly.
5. **`stress` z-scores `|prem_twa|` against the distribution of `|prem_twa|`.** Line 211's "its"
   is read as the same quantity. Against the SIGNED distribution the statistic is negative on a
   calm day and positive on a stressed one in the same units, which is not a stress.
6. **The restrike threshold is measured on the PRODUCT's value; the 6.67% is the underlying move
   that reaches it.** Line 292 states both in one sentence and they are different quantities.
   `Restrike.check` takes the product value, `underlying_trigger` reports `threshold / |L|`, and
   `product_value(level, L, r)` is the bridge the -6.7% / -6.5% test is asserted through. The
   same arithmetic covers a -3x product, where the adverse move is a rise: what falls is the
   product in both cases.
7. **The split is computed as the document writes it, not as a residual.** `(1-h) x flow` and
   `h x flow` are two roundings and their sum need not reconstruct `flow` exactly; the residual
   form would be exact and would not be line 233. The golden asserts the exact sum on the hand
   case, notes that the canonical counterexample in doubles is `0.7 + 0.3 = 0.9999999999999999`,
   and the property test asserts conservation within four ulp rather than hiding the question
   behind a tolerance nobody chose.

**The hedged fraction raises when the logistic saturates, and that is a decision and not a
nicety.** Required unit test 18 is *"h is in (0, 1)"*, an open interval. A double reaches 1.0 at
about `|x| = 37` — measured: `1/(1+exp(-36))` is `0.9999999999999998` and `1/(1+exp(-37))` is
`1.0` — and at `h = 1.0` the module would be asserting that the entire creation flow was hedged
intraday and none of it reaches the settlement window, which is a statement about floating point
and not about a market. Clamping would be worse: it returns the same wrong claim without the
tell.

**The illustrative inputs are labelled everywhere they appear.** `y_cash = 0.05` and `er = 0.01`
are round numbers chosen so that `a + a*x` and `a*(1+x)` are the same double and required unit
test 14's first clause can be an equality; they are not any fund's figures, and the hand ledger,
the golden's module docstring and the selftest's own output each say so. The one place a real
figure is used is a refusal: `Fund(er=0.95)` raises, because a percentage typed where a fraction
belongs is a hundredfold error in the accrual.

## What was measured

| | |
|---|---|
| required unit test 26 | `+$12,000,000` and `+$24,000,000` **exactly**, asserted `==`; the intermediates are `1.5e8`, `3.0e8` and `-1.5e8`, `6.0e8`. The exactness is a property of THESE numbers and the record says so: at `L_eff = 1.4` the same expression gives `1119999.9999999998` |
| the `-3x` to `+3x` ratio | **exactly 2**, on 40 hypothesis-drawn AUMs and returns, because the two differ by a power of two and scaling a double by a power of two is exact |
| required unit test 29 | -6.7% gives a product value of `79.89999999999999` and a drawdown of `-0.2010000000000001`, which fires; -6.5% gives `80.5` and `-0.195`, which does not. The inclusive boundary, a value of exactly `80.0`, is `-0.2` and fires |
| Gate 0b's hand case | 19 of 20 within 5 bp is `share_within == 0.95` and passes; 18 of 20 is `0.90` and fails; `1000.5` against `1000.0` is exactly `5.0` bp |
| the two day counts | line 184's accrual is `0.00011149162861491629`; written both on 365 it is `0.00010958904109589043`, **1.7% smaller** — a one-way drift that would spend part of Gate 0b's 5 bp budget on a day count |
| the logistic's saturation point | `1.0` at `x = 37`, `0.9999999999999998` at `x = 36`; `hedged_fraction(40.0, 0.0, 0.0)` raises |
| the split's conservation | exact on the hand case (`179.29428091333006 + 487.3723857533366 == 666.6666666666666`) and within four ulp in the property test |
| tests added | **76** — golden 17, unit 48 (funds 20, premium 11, non_us 17), property 11 — against 1,636 lines of new library carrying **111 `raise` sites**, 362 lines of script and 1,425 of test, with 13 numbered deposit claims |
| the selftest | 11 declared blocks, every guard fired on its break, exit 0 |

### The hand file came first, and one of its numbers was wrong

`tests/golden/test_ledger_funds_ledger.hand.txt` was written before
`tests/golden/test_ledger_funds_ledger.py`, and the arithmetic in it was worked in a scratch
calculator that never imports `backtest_framework`. It earned its keep immediately: the hand
file's first draft gave the both-on-365 accrual as `0.00011095890410958904`, a transposition,
and the golden test failed on it. The hand file is now right and carries the division that
produces it. The library's formulas are the document's, transcribed before either file existed.

### A break that trips the wrong guard proves the wrong thing

The selftest's block 5 originally built its two invalid minutes at the same timestamp, so the
"a day with no valid minute" case raised `features`'s **strictly-increasing** guard instead of
its **no-valid-minute** guard, and printed a pass. Fixed by giving them distinct timestamps; the
message printed beside each raise is what surfaced it, which is why the selftest prints the
exception text rather than a tick.

## Disagreements and what is NOT resolved

1. **Nothing is fitted and nothing here could be.** `h0`, `h1`, `g1`, `n9`, `a0..a3`, `b1..b4`
   are Stage C2/C3 parameters estimated in walk-forward windows against realised window flow
   (Section 8, decision D11), and neither the flow nor the panel exists. These modules evaluate
   the functions those parameters enter and supply no defaults for any of them.
2. **No fund fact is sourced.** The expense ratio, `lag_c`, the futures/swap split, the NAV
   strike basis and the roll schedule are Section 3.2's list, being sourced into
   `data/fund_facts/` by another record this round. Until then `inav` raises and `creation_term`
   refuses any `lag_c` outside {0, 1} rather than assuming one.
3. **Gate 0b has not been RUN**, on any fund, on any day. It is a function with a hand case. The
   deposit makes it a gate on all P3 work, and that gate is still open.
4. **The accrual is one day and a weekend is not modelled.** Line 184 writes `y_cash / 360` with
   no day count multiplier. Over a Friday-to-Monday gap the real accrual is three days and this
   charges one. That is the document's formula; amending it is a doc edit under Section 0
   instruction 2, not a library's call, and the module docstring names the discrepancy.
5. **P9 is Q14-shaped and stays open.** Not one figure in Section 3.1b is sourced — line 74 says
   so itself — and three of the eight products carry no index month rule or no restrike
   threshold because the document says "verify" rather than stating one. `3NGS` is given the
   2nd-front rule on line 289's issuer-level sentence ("2nd-front month for WisdomTree NG")
   while line 81 marks its index "verify"; that is the one place this module resolves a tension
   in the document's favour rather than refusing, and it is flagged here.
6. **`sv_etf` takes its aggressor sign from the caller.** Section 3.3b permits exchange-provided
   or Lee-Ready classification "documented"; nothing here classifies anything and nothing here
   documents the caller's choice.
7. **The restrike detector has no time axis.** `Restrike.check` is a per-observation test and
   line 293's *"Restrike times are computable from futures prices and the product terms"* needs
   a minute series and a product's reset history to walk. `RestrikeLog` is the output shape for
   when something does.
8. **No `restrike_events.csv` is committed**, and `RestrikeLog.write` has no default path. The
   same reason D606 committed no `ERROR_BUDGET.md`: a rendered artefact with no run behind it is
   a claim about nothing.

## CHANGELOG bullet (draft, for the integrator)

- **D611 — the deposit's fund model: iNAV, the premium, creations, the hedged fraction, P9 and
  the restrike.** Four library modules under `ledger/` — `funds.py` (the six US funds of Section
  3.1 with the NG/CL contract multipliers from `data/futures_contract_specs.json`, `inav` on line
  184's two day counts, `gate_0b` on line 191's 5 bp / 95%), `premium.py` (`Quote` refusing a
  crossed NBBO, the valid-minute rule of line 200, `prem_twa`/`prem_frac`/`vol_x`/`sv_etf`, and
  `stress` refusing a trailing entry that is not prior), `creations.py` (`delta_create`, the
  `lag_c` branch, the logistic hedged fraction with line 472's `h1 >= 0` and `g1 >= 0` enforced,
  `create_flow` and the window split) and `non_us.py` (the eight Section 3.1b products carrying
  line 74's "indicative" warning, `effective_leverage` with decision D19's flag, `delta_h`, `q9`,
  prior-settlement FX, the index month, and the 20% restrike) — plus
  `scripts/fund_model_selftest.py`. **Every fact the deposit marks "to source" is `None` and
  every function that needs one RAISES**: all six funds carry `er=None`, 3OIL and 3OIS carry no
  index month rule, three WisdomTree lines carry no restrike threshold, and `vol_x` is `None`
  without a trailing mean. Measured: required unit test 26's `+$12m` and `+$24m` are EXACT
  doubles and the `-3x` rebalance is exactly twice the `+3x` one; -6.7% fires a restrike at
  `79.89999999999999` and -6.5% does not; line 184's accrual is 1.7% larger than the same
  formula written on one day count. 76 tests (golden 17 hand-worked, unit 48, property 11), 13
  numbered ledger claims (4, 14-20, 26-30). No fixture read, nothing written under `data/`, no
  strategy return computed.

## The numbered deposit tests claimed

| ledger | function | file |
|---|---|---|
| 4 | `test_ledger_4_the_execution_day_lag_picks_one_term_and_never_both` | `tests/unit/test_ledger_funds.py` |
| 14 | `test_ledger_14_inav_zero_move_is_nav_times_one_plus_accruals` | `tests/golden/test_ledger_funds_ledger.py` |
| 15 | `test_ledger_15_the_premium_reads_the_midpoint_and_never_the_last_trade` | `tests/unit/test_ledger_premium.py` |
| 16 | `test_ledger_16_a_stale_or_futureless_minute_is_excluded_from_all_features` | `tests/unit/test_ledger_premium.py` |
| 17 | `test_ledger_17_no_premium_feature_uses_a_minute_at_or_after_w_start` | `tests/unit/test_ledger_premium.py` |
| 18 | `test_ledger_18_h_is_in_the_open_interval_and_non_increasing_in_stress` | `tests/unit/test_ledger_funds.py` |
| 19 | `test_ledger_19_the_creation_sign_comes_from_the_leverage` | `tests/unit/test_ledger_funds.py` |
| 20 | `test_ledger_20_gate_0b_reproduces_the_hand_calculated_error` | `tests/golden/test_ledger_funds_ledger.py` |
| 26 | `test_ledger_26_the_p9_rebalance_is_twelve_and_twenty_four_million` | `tests/golden/test_ledger_funds_ledger.py` |
| 27 | `test_ledger_27_fx_uses_the_prior_settlement_and_never_the_current_day` | `tests/unit/test_ledger_non_us.py` |
| 28 | `test_ledger_28_flow_maps_to_each_products_own_index_contract_month` | `tests/unit/test_ledger_non_us.py` |
| 29 | `test_ledger_29_the_restrike_fires_at_six_point_seven_and_not_at_six_point_five` | `tests/golden/test_ledger_funds_ledger.py` |
| 30 | `test_ledger_30_a_missing_published_notional_uses_stated_l_and_flags_the_day` | `tests/unit/test_ledger_non_us.py` |

`data/deposit_test_map.json` lists all thirteen as `missing`; `scripts/deposit_test_map.py
--scan` reports each as a claim site in an untracked test file and **NO DISAGREEMENTS**. The map
is D607's to update once these files are staged.
