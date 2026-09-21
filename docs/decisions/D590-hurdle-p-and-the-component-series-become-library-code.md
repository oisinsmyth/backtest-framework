# D590 — Hurdle P and the component daily series become library code, held to every published number they inherit

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** The sixth pass at R11. Hurdle P has been computed five times — D266 (P1 as
`size = 0.04/dd`), D440 (P4 as the account's life), D495 (P5's exact haircut), D500/D501
(P3 as a rate), D503 (all six at once) — each inside the runner that needed it, each on a
slightly different convention. Extends R11 (all six amendments), R16, D48, D78/D537, D542,
D550, and `docs/COMPONENTS_PROP.md`'s C-a..C-e. Amends nothing: RULES.md,
COMPONENTS_PROP.md and every reference runner are untouched.

## Decision

Two library modules, one data artefact, one printer, four test files. **No number in this
record is new.** Everything here is either an existing published number reproduced, or a
guard that makes the next one reproducible.

### 1. `src/backtest_framework/validation/hurdle_p.py` — R11, dollar-native

```
Plan(firm, size, fee_eval, monthly, fee_activation, target, dd_eval, kind_eval,
     lock_eval, dd_fund, kind_fund, lock_fund, qual_threshold, qual_days, min_total,
     caps, max_payouts, min_payout, safety_net, consistency, fund_start=0.0,
     post_payout_floor=None, start_funded=False, notes="")   frozen; d386's fields, order and defaults

venue_keys() -> list[str]                    14 keys
venue_record(key) -> dict                    every field with its own provenance
load_venue(key) -> Plan
p6(venue) -> dict                            {automation_permitted_funded, p6_pass, provenance}

p1_size(d_usd, cap_usd=2_000.0) -> dict      USD; {max_trailing_dd_usd, size_multiplier,
                                             usd_per_year_at_traded_size,
                                             post_sizing_usd_per_year, basis}. NO pass/fail key.
p2_flatten(exit_times_et, venue) -> bool     "HH:MM" US/Eastern vs the venue's own clock
p3(d_usd, account=50_000.0) -> dict          {p3a_breaches_per_year, p3a_pass, p3b_life_cost,
                                             p3b_pass, p3c_worst_day_usd, p3c_in_sigma,
                                             p3c_share_of_loss_budget, life_*, deaths_*, ...}
p4_life(source, plan, *, basis="usd"|"return", target_dollar_vol=None, rule="static",
        lows=None, highs=None, n_paths=8_000, days=600, seed=20260911,
        shuffle=False) -> dict               USD; expected_profit_usd, account_cost_usd,
                                             net_per_cycle_usd, expected_life_days/years,
                                             expected_funded_life_days/years, p_alive,
                                             P4_binding_profit_exceeds_cost, path_basis
p5_recognised(d_usd) -> dict                 USD; d495's six keys, cap 0.30
hurdle_p(d_usd, venue_key, account=50_000.0, *, seed=20260911, label=None,
         exit_times_et=None, n_paths=8_000, days=600, run_lifecycle=True) -> dict
per_year(d_usd, dates, account=50_000.0) -> list[dict]

max_drawdown_life(d, cap) -> (n_deaths, mean_life_sessions, episodes)   d501's, verbatim
recurrence_years(n_events, n_sessions) -> float                         d501's, verbatim
p_at_least_one(n_events, n_sessions, horizon) -> float                  d501's, verbatim
expected_profit_before_breach(sharpe, sigma_frac, D=0.04) -> (profit, life_days)
                                             d496's, verbatim; ACCOUNT-FRACTION units
expected_profit_before_breach_usd(sharpe, sigma_usd, account=50_000.0, dd_usd=None)
                                             the same, in DOLLARS, with the unit boundary asserted
sigma_series, notional_series, gauss_provider, measured_provider, simulate_provider
                                             d440's, verbatim; providers return DOLLARS
```

**Dollar-native throughout (D542).** The floor is `eq += x; peak = max(peak, eq);
peak - eq >= cap` — an absolute dollar distance from a ratcheting peak on a cumulative
SUM, with the peak starting at 0. It is never a fraction of a compounded peak, and
`analytics/metrics.py:max_drawdown` is deliberately not imported.

**Units are asserted, not documented.** `expected_profit_before_breach` keeps D496's
account-fraction signature verbatim (R16: the published form is not edited), and the
dollar wrapper refuses both shapes of the slip that crashed D503's first run — a daily
sigma at or above the whole account, and one below `MIN_SIGMA_FRAC = 1e-5` ($0.50 a day on
a $50,000 account, under one tick of every instrument these venues offer). `p4_life`'s
`basis="usd" | "return"` **is** the unit assertion for a series: a dollar series may not
carry a `target_dollar_vol` and may not be vol-targeted; a return series must carry one.
Every guard raises (D48).

### 2. `data/prop_venues.json` — the venue terms, with provenance per field

Fourteen records, one per `d386_full_lifecycle.PLANS` entry, keyed `apex_25k` …
`take_profit_trader_150k`. Every one of the 24 `Plan` fields carries `{"value",
"provenance"}`; the four assumed values name the D386 ASSUMPTION they come from (#1 Take
Profit Trader's 100K/150K qualifying threshold, #2 Topstep's 50%-of-balance
approximation, #3 Apex's `min_total`), the MFFU lock levels carry the two
`help.myfundedfutures.com` URLs quoted verbatim in `data/d445_floor_lock_sources.md`, and
the two assumptions attached to no field (#4 Gaussian P&L, #5 the inactivity rules) sit at
the top level. Plus, per venue:

| | value | source |
|---|---|---|
| `flatten_time_et` | Apex 16:59, MFFU 16:10, Topstep 16:10 (= 15:10 CT, converted once, here), **Take Profit Trader `null`** | R11 P2 and its 2026-08-29 amendment |
| `automation_permitted_funded` | Topstep and MFFU `true`; Apex `false` (penalty *"forfeiture of all funds and balances"*); Take Profit Trader `false` | R11 P6 |
| `daily_loss_limit` | `null` on all fourteen | `"unverified, R11 2026-09-13"` |

### 3. `src/backtest_framework/validation/component_series.py` — the missing artefact

```
DailyPnL(name, dates: tuple[str,...], usd: tuple[float,...], size_label,
         cost_line_usd_rt, window: tuple[str,str], spec, source_sha256)   frozen, validated
  .write(dir=data/components) -> Path        <name>_daily_usd.csv (date,usd; newline "\n")
                                             + <name>_daily_usd.meta.json (carries csv_sha256)
read(path) -> DailyPnL                       csv or meta path; RAISES if the csv's sha256 moved
align(*series, calendar=None, strict=True) -> pd.DataFrame     zero-fills exactly as series_on
correlation_matrix(df) -> pd.DataFrame       C-b's statistic, over ALL calendar days
component_line(series, account=50_000.0, bars=LEDGER_BARS) -> dict    C-a..C-d, net AND gross,
                                             Sharpe AND Sortino (R17)
sharpe(x), sortino(x), sharpe_boot(x, dates, n_boot=1000, seed=7), sha256_of(path)
Bars(sharpe=0.5, rho=0.3, skew=-0.5, sigma=500.0)   == d466's BAR_* constants
```

**Why it exists.** Three rows of `docs/COMPONENTS_PROP.md` say *"ρ not computable — the
arm's daily P&L is not on disk"* (entry #3, D555, D558). `run_d466_components.py` rebuilds
every series from its fixtures and writes **summaries only**, and C-b is a pairwise
statistic that no summary can ever satisfy. Values are written with `repr`, the shortest
string that reads back to the same float, so `read(write(x)) == x` exactly; the newline is
pinned to `"\n"` on every platform (D550).

**Sortino is defined, not inherited:** `mean / sqrt(sum(min(x,0)^2)/(n-1)) * sqrt(252)` —
the ddof=1 divisor is the one `sharpe` uses, so the pair differ only in which deviations
count. `component_line` will not return one without the other (R17).

### 4. `scripts/hurdle_p_report.py` — a printer, and nothing else

`--series <csv> --venue <key> [--account 50000] [--exit-times-et 15:59] [--paths --days]`
prints the six criteria one block each and then the per-year table; `--selftest` runs 9
groups in which every guard is first shown to ACCEPT the good case and then to RAISE on
the break (the `expect_raise` idiom of `scripts/stage0_d581_gamma_close.py:39`). It
computes no statistic of its own — a second implementation of a hurdle is the thing this
record exists to prevent.

## Rationale

**R16 is the whole design.** A quantity quoted from an earlier record is the output of a
pipeline that has since moved, so the only way to know the object is the published one is
to reproduce it exactly on the original build. Every function here is held against the
runner that published its numbers, imported by path with
`importlib.util.spec_from_file_location` and never edited.

### Reproduction guards, as run on 2026-09-21

**(a) `max_drawdown_life` / `p3` vs D501.** D501's artefact stores summaries, not its daily
series — so the series was rebuilt through **D501's own input path**
(`d495.build_panel` → `d491.simulate`, NQ AGREE M = 5, 1 MNQ). `d484.series_for` raises on
any row past 2023, which is the holdout guard and is left where it is, so this reads
**2016-01-07 → 2023-12-29 and nothing from 2024-01-01 on**.

| | recomputed | `data/d501_worst_day_frequency.json` |
|---|---|---|
| sessions | 1,873 | 1,873 |
| daily σ | 180.48092874011638 | 180.48092874011638 |
| worst day | −1314.508999999949 | −1314.508999999949 · in σ −7.283367883665853, both equal |
| deaths, trailing 4% | 7 | 7 |
| mean life | 255.57142857142858 | 255.57142857142858 |
| every episode length | 817, 553, … | equal to `account_lives` element by element |
| P3a breaches / yr | 0.26908702616123864 | 0.26908702616123864 |
| recurrence | 3.7162698412698414 yr | 3.7162698412698414 yr |
| life with P3 · deaths | 198.77777777777777 · 9 | 198.77777777777777 · 9 |
| P3 days capped at −$1,000 | (7 deaths, 255.57142857142858) | (7, 255.57142857142858) |

**All equal with `==`, not `approx`.** The last row reproduces D501's own finding that a
same-day stop at the P3 level buys **zero** account life. The guard is shown able to fail:
rolling the series by one session changes the life.

**(b) `p4_life` / `simulate_provider` vs D440 and D386.** Two checks.

*The injected Gaussian reproduces `d386_full_lifecycle.simulate` bit-identically* — D440's
own `[P1]` gate, re-run through this module's port: **12 cells × 5 fields, compared with
`!=`, zero differences.** Shown able to fail: the EOD and INTRA plans score differently on
the same seed.

*The published measured cell reproduces.* `data/d440_lifecycle.json`, MFFU Rapid EOD 50K /
SPY / voltgt at f\* = 0.007, 8,000 paths (3,266 distinct starts), 600 days, seed 20260911:

| | recomputed | published |
|---|---|---|
| V | 77.73575874805616 | **77.7357587481** |
| funded life, years | 0.13508755956174695 | **0.1350875596** |
| V_se · paid_mean · fees_mean | 19.376897098369252 · 286.7357587480562 · 209.0 | 19.3768970984 · 286.7357587481 · 209.0 |
| p_paid · p_pass · p_breached · p_alive | 0.1041028781383956 · 0.320269442743417 · 1.0 · 0.0 | 0.1041028781 · 0.3202694427 · 1.0 · 0.0 |
| payouts · life days · funded days | 0.27036129822412736 · 36.190447030006126 · 34.04206500956023 | 0.2703612982 · 36.19044703 · 34.0420650096 |

The artefact was written by `pandas.to_json`, which **rounds to ten decimal places**, so
ten dp *is* the published precision; the comparison is exact at it and the tolerance was
not chosen after seeing a gap (R16 §4). Shown able to fail: the 0.011 grid point does not
reproduce the 0.007 cell. Wall time 0.05 s — no background run was needed and none was
projected.

**(c) `hurdle_p` vs D503.** D503's daily series is **not committed** and its inputs are the
2024+ forward slice, which nothing here reads. So the guard is run two ways.

*Function against function:* `scripts/d503_forward_book.py:hurdle_p` and this module on
**12 random series × 22 shared keys, all equal** (NaN-aware), and **every key D503 returns
is present** in this module's output.

*Artefact against arithmetic:* **28 keys across D503's three stored arms** (macd, k8, book)
recomputed from D503's own stored summaries and equal with `==` — P1, P3a and its
recurrence, P3c in all three units, `p_breach_in_252`, P3b from the stored lives, and P4's
Brownian pair through `expected_profit_before_breach_usd`. The headline figures the D503
record quotes are pinned: P3a **6.957055214723926**/yr, worst day **−$2,724.009**,
**136.2%** of the loss budget, life 31.05 sessions, 20 deaths.

**The remaining keys cannot be re-derived at all.** `life_dd_only_sessions`,
`life_with_P3_sessions` and both death counts are path statistics of a series D503 did not
commit. That gap is the argument for `component_series.py` and is recorded, not papered
over.

**(d) `p5_recognised` vs D495.** 50 random series in the unit file and 40 hypothesis
examples in the property file, all six keys, NaN-aware, all equal; `P5_CAP == d495.P5_CAP
== 0.30`.

**(e) Two reproductions nobody asked for, worth recording.** Scoring D501's in-sample cell
through `component_line` returns net Sharpe **0.722857225865919** — bit-identical to
D503's committed in-sample reference `IS["macd"]["sharpe"]`. And
`expected_profit_before_breach_usd` on the same cell returns a life of **177.0 days**,
which is the `brownian_model_life_sessions_D496: 177` D501 stored beside its empirical 256.

### Six disagreements with existing numbers, none of them silent

1. **D503's `P1_post_sizing_usd_per_year` is not post-sizing.** It is `mean × 252` at the
   traded size. R11 P1 says *size the account so trailing drawdown ≤ 4%, then carry the
   resulting return forward*. Using D503's own stored `max_drawdown_usd`:

   | arm | stored max DD | P1 multiplier | published "post-sizing" | actually post-sizing |
   |---|---:|---:|---:|---:|
   | macd | $7,298 | ×0.274 | $3,971/yr | **$1,088/yr** |
   | k8 | $6,566 | ×0.305 | −$888/yr | **−$270/yr** |
   | book | $9,932 | ×0.201 | $3,083/yr | **$621/yr** |

   The key keeps its name and value so a D503 figure still checks field by field;
   `P1_size_multiplier` and `P1_post_sizing_usd_per_year_sized` are added beside it. Two
   caveats travel with the table: D503's drawdown uses an unclamped running peak while the
   venue's peak starts at 0 (this module clamps), and **a multiplier below 1 is not
   available at a micro** — one MNQ is the floor, so ×0.20 is not a size, it is a statement
   that the construction is four to five times too large for the account (D493: size cannot
   fix a prop edge).
2. **D503's `P2_pass: True` is hard-coded**, not computed. This module returns `None` when
   no exit times are supplied and compares them to the venue's own clock when they are.
   R11's amendment is explicit that P2 is *"a fact about the venue, to be quoted from its
   own documentation, never assumed."*
3. **R11's header table still says P5 ≤ 40%. The operative cap is 30%** (restatement
   2026-09-12, refined the same day; `d495` has used 0.30 since). RULES.md is append-only
   and is **not** edited here; the discrepancy is recorded in this record and in the
   module's docstring, as instructed.
4. **Take Profit Trader has no flatten time anywhere in this repository** — not in R11 P2,
   not in `d386_full_lifecycle.py`, not in any script literal. `prop_venues.json` records
   `null` and `p2_flatten` RAISES on that venue rather than inventing one.
5. **No venue carries a daily-loss-limit field.** R11's 2026-09-13 amendment flagged P3's
   provenance as unverified; nothing has verified it since, and the flag is now
   machine-readable on all fourteen records. If it is not a venue term, P3 is a prudence
   rule of ours and P3a/P3b are its entire content.
6. **`docs/COMPONENTS_PROP.md` has no Sortino column** and R17 (2026-09-19) postdates it.
   `component_line` returns one beside every Sharpe it reports; the ledger is append-only
   and is not edited here.

### What was run

Four test files, **115 tests, 21 s**:

| file | tests | what it holds |
|---|---:|---|
| `tests/golden/test_hurdle_p_ledger.py` (+ `.hand.txt`) | 27 | R11's own arithmetic on a 14-session declared series, hand-worked from R11's definitions with both square roots shown as Newton iterations. Exact rationals: P3a = 36.0/yr, P3b = 2/3, P1 multiplier = 10/11, P5 haircut $1,050 of $1,500 |
| `tests/unit/test_hurdle_p.py` | 40 | guards (a)–(d), the 14 Plans field by field, the venue file's provenance, and every raise |
| `tests/unit/test_component_series.py` | 36 | round-trip, LF pinning, sha256 tamper, and estimator identity with `run_d466_components.py` |
| `tests/property/test_hurdle_p_property.py` | 12 | guard (d) quantified; the floor's dollar scale-freedom; episode partitioning; P1 puts the drawdown exactly on the cap |

`uv run ruff check` and `uv run mypy` clean on both new modules and the script.
`tests/unit/test_encoding_is_declared.py` still passes (8/8) with the new script added:
every text open in it passes `encoding="utf-8"`.

Every property test carries `SETTINGS = settings(derandomize=True, max_examples=40,
deadline=None)` and cites D78/D537 — the seed is fixed, the examples are not, so a failure
that does not reproduce when the file runs alone is not thereby a flake.

## Consequences

1. **R11 has one implementation.** The sixth record to compute hurdle P imports it; a
   seventh convention now requires editing a module three test files watch.
2. **A component's daily series can be committed**, so C-b stops being "not computable".
   The three ledger rows that say so can be filled the next time one of those constructions
   is re-run — by its own runner, writing a `DailyPnL`, not by a re-derivation here.
3. **`data/prop_venues.json` makes the unverified things visible.** Two fields are `null`
   with a stated reason rather than absent, and the four assumed Plan values name their
   assumption. A venue-terms review now has a checklist instead of a grep.
4. **D503's artefact is known to be only partly re-derivable**, and the reason is recorded.
5. **Nothing is admitted, closed or reopened.** No strategy return was computed on any
   holdout slice; the only market data read is `data/d440_holds.csv.gz` (a committed
   artefact, the published input to the published number) and `fut_sessions_hourly.csv.gz`
   through D501's own 2016-01-07 → 2023-12-29 gate. No bar from 2024-01-01 on was read for
   any return.
6. **Two tests will fail if a reference runner is edited** — deliberately. `d386.simulate`,
   `d440`'s loop, `d495.p5_recognised`, `d496.expected_profit_before_breach` and
   `d501.max_drawdown_life` are now load-bearing for the suite, which is the point: they
   are the published objects.

---

## Proposed paragraph for `docs/data-available.md`

*Not applied here — `docs/data-available.md` is outside this record's scope. Offered for
whoever next edits that file.*

> **`data/prop_venues.json`** (D590, ~90 KB, tracked) — the prop-firm venue terms, one
> record per `Plan` in `scripts/d386_full_lifecycle.py`: 14 plans across Apex (25/50/100/150K),
> MyFundedFutures Rapid and Rapid EOD (25–150K), Topstep 50K and Take Profit Trader
> (25–150K), keyed `apex_50k`, `mffu_rapid_eod_50k`, `topstep_50k` and so on. **Every one of
> the 24 plan fields carries `{"value", "provenance"}`**, so a fee, a drawdown type, a lock
> level or a payout cap can be traced without re-reading a lane file: the four assumed values
> name the D386 ASSUMPTION they come from, and the MFFU lock levels carry the two
> `help.myfundedfutures.com` URLs quoted verbatim in `data/d445_floor_lock_sources.md`. Each
> venue also carries `flatten_time_et` (R11 P2 — Apex 16:59, MFFU and Topstep 16:10, the
> latter converted once from 15:10 CT), `automation_permitted_funded` (R11 P6 — only Topstep
> and MFFU) and `daily_loss_limit`. **Two things in it are `null` and the `null` is the
> finding:** Take Profit Trader's flatten time appears in no source this repository holds, and
> **no venue carries a daily loss limit at all**, which leaves R11's P3 justification
> (*"daily loss limits run 2–3%"*) unverified as its own 2026-09-13 amendment flagged.
> `validation.hurdle_p.load_venue(key)` rebuilds the `Plan`; `p2_flatten` and `load_venue`
> RAISE on a `null` or an unknown key rather than assuming a value. Read it before quoting
> any venue term — no other machine-readable copy exists.
>
> **`data/components/` (convention, D590)** — where a component's **daily P&L in dollars**
> lives, so `docs/COMPONENTS_PROP.md`'s C-b (ρ with every prior entry) can actually be
> computed. Three ledger rows currently read *"ρ not computable — the arm's daily P&L is not
> on disk"*, because `scripts/run_d466_components.py` writes summaries only. A component is
> two files: `<name>_daily_usd.csv` (`date,usd`, one row a session, zero on a flat day, LF
> newlines, floats written with `repr` so they read back bit-exactly) and
> `<name>_daily_usd.meta.json` (the traded size, the cost line in dollars per round trip, the
> window, the record that produced it, the sha256 of the source it was derived from, and the
> sha256 of the CSV itself). `validation.component_series.read` **refuses a CSV whose bytes no
> longer match the recorded hash**, so a silently edited series cannot enter a correlation.
> Write one from the runner that computed the series — a component line computed outside its
> own runner is the error D466 and D590 both exist to prevent — and never by re-deriving it
> here. The directory is empty at the time of writing: D590 built the artefact, not its
> contents.
