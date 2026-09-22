# PICKUP - handoff for the next session

**What data exists, and what bites each dataset: [`docs/data-available.md`](../data-available.md).**

## ROUND 4 — THE LAST SHARED ITEM AND THE SETTLEMENT LEDGER'S OWN INFRASTRUCTURE, D609–D619 BUILT AND VERIFIED, STAGED, NOT COMMITTED, 2026-09-22

The principal's instruction (2026-09-21): *"finish off the shared infrastructure points then move on to
the Settlement ledger infrastructure. Pick 5 points and give them to 5 opus agents."* Three decisions
taken before launch (2026-09-22): the five below; the Databento energy-options pull is **quote only**;
the attention sample is one week (it became two days — see D612). Five parallel Opus agents on disjoint
files, each verified here by running its tests and selftest and reproducing its hand cases
independently. **Do not rebuild any of the following.**

| record | component | files | reproduced here |
|---|---|---|---|
| **D609** | the panel loader chokepoint (`load_panel`, `reserved_from` **no default**, D594's three layers, manifest sha re-derived; `panel_catalogue.py` declares the date column for all 128 manifest panels, 19 wrong-cut columns, 19 dateless panels refused; honest-skip rule moved out of `conftest.py`) **and the seven-root 100× fix** (`tick_usd_full_contract` in the definition snapshot; `from_specs` reads it; `futures_costs.json` and `futures_impact_params.json` rebuilt) | `data/panels.py`, `data/panel_catalogue.py`, `scripts/panel_catalogue_check.py`, `instruments/future.py`, `scripts/probe_definition_specs.py --rescale`, 3 data files, 6 test files | ZC/ZS/ZW $12.50, ZL $6.00, LE/HE $10.00, SR3 $6.25; ES/ZN unchanged; `from_table("ZC").tick_usd == 12.5`; TypeError without `reserved_from`; breadth panel 140,814 rows to 2023-12-29, zero reserved; depth panel **zero rows** at the seal; d555 dollar book byte-identical |
| **D610** | the flow ledger's algebra: P1/P2 + routing, §5.1, §5.2 Kalman update, §7.1 entry rule, §8A.5 large lot, P8a/P8b rolls, §8A.2 netting fit, COT and swap clocks; **no data read** | `ledger/{__init__,flows,update,rolls,netting}.py`, `scripts/ledger_selftest.py`, 6 test files | test 6: k 1.0, Q_hat 110.0, var_post 200.0, Q_rem 55.0 exact, σ_rem 5√2; K = 0 at R = ∞; test 1 +1e8/+3e8/0; L = −2 roll buys 25 old, sells 23.4375 new; same-day large-lot trade raises |
| **D611** | the fund model: iNAV + Gate 0b, NBBO-mid premium + valid minute + features + stress, creations + `lag_c` + hedged fraction + split, P9 + restrike; **every "to source" fact is `None` and raises** | `ledger/{funds,premium,creations,non_us}.py`, `scripts/fund_model_selftest.py`, 5 test files | iNAV at r = 0 = NAV·(1 + accruals) exact; ±2% at L = ±2; ΔH +12m/+24m exact; KOLD creation −66.67 vs BOIL +66.67; −6.5% no restrike, −6.7% restrike with level 79.9 |
| **D612** | the attention layer: `QUERIES.md` hashed first, Wikimedia dump + GDELT GKG parsers, four point-in-time guards, a **two-day** sample; **erratum on deposit line 112**; no backfill; `attention` recorder job ready | `data/attention.py`, `scripts/fetch_attention.py`, `data/attention/*`, `attention_sample.csv.gz` + meta, `jobs.json`, 3 test files | hash matches `QUERIES.sha256`; 13:00 hour available at 14:15 exactly (14:10 and 14:14:59 not); sample 3,072 rows, `available_at > observed_at` on every row; recorder https gate passes |
| **D619** | `fund_nav_daily` (BOIL/KOLD/UCO/SCO NAV, shares, AUM 2008→2026), one day of holdings, `fund_facts/{SOURCES.md,fund_facts.json}` (30 sourced / 10 unknown / 8 P9 not sourced), the CME census (TAS **present** as `CLT.FUT`/`NGT.FUT`; options OI **not on disk**; quote 178.91 GB / $3.17, **nothing submitted**) | `scripts/{fetch_fund_nav,fetch_fund_holdings,fetch_fund_facts,build_fund_panel,probe_energy_options_parents,quote_energy_options_pull}.py`, 4 data JSONs, fixture + meta, 2 test files | 16,402 rows, four funds, spans as stated, 82 BOIL seed rows excluded and dated; `submitted: false` and `submit_job` absent from the code; TAS conclusion `present` |

**Integration DONE (2026-09-22, staged, NOT committed):** the crosswalk map moved from 43 to **79 of 146
claimed** (ledger 65/71 — 54–58 declined in D588 and 61 remain) and the page re-rendered, `--scan` at
zero, `--check` collecting 801 node ids; four data-available §4 paragraphs; a CHANGELOG block of six
bullets; the recorder schedule's `fund_snapshot` split into four jobs from D619's draft (19 jobs, 10
ready) and the TAS note extended; the manifest rebuilt at **128 panels, 13 blob-less**, named on the
running page with the anchor test moved to 128/13; the catalogue given rows for the two new panels
(`attention_sample`: `observed_at_utc`, wrong cut `available_at_utc`; `fund_nav_daily`: `date`, wrong cut
`fetched_at`) and its pinned counts moved 126→128 in the unit test, the golden and the hand file;
register and README counts (845 records, 571 numbers, D1→D619); the living documents' quoted counts
(golden 331→383, property 181→215, unit 2,882→3,199, total 3,553→3,956, non-bare raises 829→1,120 across
74 of 113, bare unchanged at 4 so "(833)"→"(1,124)", modules 63→74 across 12 packages); the encoding
ratchet (two `Path.open("rb")` calls in the catalogue checker rewritten as builtin `open(path, "rb")` —
the ratchet does not recognise the method form as binary); two citation anchors in `panels.py` reworded;
ledger 33's claim line re-pinned after a comment was added above it; the tracker's shared rows 1, 2 and
17 updated, its per-document settlement bullets rewritten, two wrong lines corrected (TAS symbology;
"statistics schema held"), and a settlement-ledger status table added. **Full suite on the staged tree:
3,955 passed, 1 skipped, 6 deselected (4:54); skip count unchanged** against round 3's 3,552 passed / 1 skipped / 6 deselected. **Only the commit is owed,
on the principal's word**; the message is drafted in this session's scratchpad.

**Round 4b (2026-09-22, same day, on the principal's answers to the five findings):** the fund-panel
record was renumbered to **D619** when the concurrent expiry-pinning branch pushed the six numbers
below it to origin (its first number, and the next two, were taken there); two
more agents ran in parallel and are verified here: **D620** (all 231 10-Q/10-K filings recorded and
parsed into `fund_holdings_quarterly` — 415 fund-quarters, signed contracts, held months, `f_fut`;
and `fund_panel_projected` for UNG/USO, which answers *"can we project backwards / between
filings?"* by measurement on the four funds with daily truth: **backwards yes, between no** — median
36–44% share error, 18–33% AUM, creation flow uncorrelated; reproduced here: UCO `f_fut` 0.183 and
SCO 1.000 at 2026-06-30, every projected row `est_flag = 1`, method `step` only) and **D621** (retail
attention from creations + Robinhood holders + GDELT hourly via the API, replacing the deposit's
hourly-Wikipedia row on the principal's approval; the amendment text is drafted in D621 §7d, the
deposit not edited; reproduced here: UCO Spearman(Δholders, Δshares) 0.557 on 362 creation days
against the record's 0.556 on 360, the validation JSON byte-identical on `--check`). **The free
Databento pull was submitted** (`scripts/fetch_energy_options.py`, six jobs, USD 0.00; the paid TAS
`trades` line deferred by the principal) and is downloading under `data/raw/databento/`. Integration
of 4b: four more data-available paragraphs, three CHANGELOG bullets, four catalogue rows (manifest
**130** panels, **15** blob-less, named on the running page), the tracker's settlement table and
bullets, register and counts. **Full suite on the staged tree after 4b: 4,151 passed, 1 skipped, 6 deselected (4:32); skip count unchanged.** **Still owed on the principal's word: the commit, the merge with
origin (the expiry-pinning branch's six records), the push.** Decisions the principal gave: Wikipedia hourly dropped (item 2 —
plan approved), paid TAS deferred (3), filings parser built (4), the host / seal date / automation /
calendar flags on hold (5).

**Shared list, re-checked against the split TEXT rather than the status table (2026-09-22, at the
principal's request):** every sub-piece the seventeen items name has code, with three that are not a
builder's — the recorder host (Q17), the seal-date reconciliation, the 14:30 UK automation (O-Q3) — and
**one gap inside a "built" row: item 8's calendar carries no `eia` and no `index_rebalance` flag** though
the split names both. EIA dates are already in `data/calendar/events.csv` (573 WPSR, 574 NGSR), so that
flag is a join; index-rebalance dates exist nowhere in the repo and need a source. Recorded in the
tracker, not built (the principal has not asked for it).

**Findings the agents surfaced that a later study must carry:** the ledger document's units do not
reconcile — line 160's `var_Q1` is notional² while line 156's `Q1` is contracts, and §5.1 sums both into
what §5.2 divides (D610 returns the document's form by default and raises on a half-converted call);
the P1/P2 routing identity is exact only at `f_fut ∈ {0, 1}` and one ulp wide inside; line 156 is exact
in binary64 only in the document's own operand order; **the deposit's line 112 is wrong** — per-article
hourly Wikipedia pageviews exist only in the dumps (~2.5 TB for 2016–2023; GDELT GKG ~1.64 TB), and the
daily REST alternative re-derives `att_accel` and voids test 22 as written (the principal's call);
GDELT's DOC API allows one request per 5 s with a long cooldown and its resolution autoscales, so the
raw files are the backfill route and the API only the forward one; `dumps.wikimedia.org` throttles two
sustained connections below one; three of the four ProShares ticker articles are disambiguation pages;
the ProShares NAV series is fully back-adjusted for reverse splits (BOIL's earliest rows imply 0.5
shares) and shares are published in thousands to two decimals, so the AUM identity gates at half a
rounding unit, not a basis point; **UCO held 75% of its exposure in swaps** across four counterparties
on 2026-09-18 while SCO was 100% futures, and both hold DEC26/JUN27/DEC27, not the front; **`lag_c = 0`
on all six funds**, ProShares strikes NAV at 2:30 p.m. ET at the close of the settlement window, TAS is
mentioned in none of the three 10-Ks, USO's roll changed from ten days to five on 2026-01-01, and the
four ProShares roll schedules are unknown (Q19) — **Gate 0 does not clear**; UNG/USO have no free NAV
route (USCF's page is JS-gated) and no fund has a free holdings history (commodity pools file no N-PORT;
the 10-Q/10-K Schedule of Investments is quarterly); **TAS is present** on GLBX.MDP3 as `CLT.FUT` and
`NGT.FUT` (their own roots — the archive scan missed them because both pulls used `{root}.FUT`), and
**CL/NG options OI needs a pull**: 178 GB at $0.00 plus TAS trades at $3.17, free only until
~2026-10-11; `hkm_factors.csv.gz` is two panels stacked (monthly and quarterly); 26 scripts reference
`RESERVED_FROM`, not nine; the definition snapshot's cents/percent trap shipped in commit `7d03311`
(2026-09-13) and D591's cost table carried it in seven roots nobody had yet charged; `Future.__post_init__`
cannot catch a scale error because `usd_per_point` is derived from `tick_usd`, now pinned as a test;
`scripts/d508_micro_crossing_tbbo.py:98` still reads the old `tick_usd` as a fallback (none of the seven
roots; a frozen runner, named not edited); the vault-window-vs-seal reconciliation is still the
principal's decision and now gates the fund NAV panel and the attention sample as well.

## SHARED INFRASTRUCTURE, ROUND 3 — D604–D608 BUILT AND VERIFIED, COMMITTED `f03ab6f` + MERGE `9bf41e8`, 2026-09-21

The tracker for the whole programme is now `docs/internal/DEPOSIT_INFRASTRUCTURE_TRACKER.md` (the
principal's research-vs-infrastructure split verbatim, with a status table on top). Round 3 took the
remaining shared items except the loader chokepoint (item 2's second half), which is deferred and
stated there. Five parallel Opus agents on disjoint files, each verified here by running its tests
and selftest and reproducing one claim independently. **Do not rebuild any of the following.**

| record | component | files | reproduced here |
|---|---|---|---|
| **D608** | forward data recorder (ledger §13A.3): never-overwrite raw cache, sha256 per file, `fetched_at` = availability, gap log, health line, 16-job schedule; **no host installed (Q17)** | `data/recorder.py`, `scripts/recorder.py`, `data/recorder/{jobs.json,GAPS.md}`, `data/raw/README.md` (re-included in `.gitignore`), 3 test files | second record → new file, first bytes intact; closed window → one gap line, no duplicate on rerun; no `fill_gap` |
| **D604** | futures √-impact brick (Y = 0.7) keyed on `Future.root`, `depth_scaled`, params on 36 roots in three lines, and the **first MBO reader**: `fut_book_depth_1m` (65,688 minute rows, 8 roots, 21 days of 2026-08/09) | `costs/futures_impact.py`, `config/cost_stack.py` (+1 row), `data/futures_impact_params.json`, 2 scripts, fixture meta, 3 test files | `impact_fraction` == equity `SqrtImpact` on the same numbers; `depth_scaled(I, D, D) == I`; fixture bytes sha `df64af13…` |
| **D605** | Track 3 log (`TradeRow`/`TradeLog`), shortfall in ticks signed against the trade, latency and share beyond t0+5, 50-trade cost review as a FLAG, `TrialCounter` with futility looks; **no automation (O-Q3 open), no trade exists** | `validation/track3.py`, `scripts/track3_report.py`, `data/track3/SCHEMA.md`, 3 test files | long +2 / short −2 ticks; futility at N=100 only with both conditions; index-28 counter never reports efficacy |
| **D606** | `fit.py` (OLS bit-identical to D365, `rolling_ols`, log loss, 11-feature budget, retention check) and `error_budget.py` (leave-one-term-out, `StageOrder`); **no `ERROR_BUDGET.md` committed, no study has run** | `validation/fit.py`, `validation/error_budget.py`, 4 test files | zero-contribution term Δ == 0.0 exactly; 12 features refused; reorder refused without a log entry, accepted with one |
| **D607** | the 146-test crosswalk: `data/deposit_test_map.json` (truth) → `docs/results/DEPOSIT_TEST_MAP.md`; `--scan/--check/--render` | `validation/crosswalk.py`, `scripts/deposit_test_map.py`, 2 test files | 146 rows, per-doc counts equal the parsed sections, 622 claimed node ids collected; **43 of 146 claimed after round 3 (28 before), LETF 0 of 9** |

**Integration DONE (2026-09-21, staged, NOT committed):** four data-available §4 paragraphs, five CHANGELOG
bullets plus one fix line, the results-index row, manifest rebuilt (126 panels, 11 blob-less, named on the
running page with the anchor test moved to 126/11), register and README counts, the ten living documents'
quoted counts (golden 248→331, property 145→181 across 17 files, unit 2,455→2,882, total 3,007→3,553,
non-bare raises 580→829 across 63 of 101, bare raises 2→4 with the gate and the sentence moved together,
modules 57→63, records 830→835, numbers 558→563, highest D600→D608 after the merge with the closure branch, which took D603 — the recorder is D608), the encoding ratchet (five `to_csv`
sites in the depth builder declared; `ensure_ascii=True` dropped from the impact table, the default is the
same bytes), three citation anchors reworded, and the D604 record renamed to 83 characters (its first
filename was 102 and the tracked-path ceiling is 85, D540). **Two defects fixed in committed code:** the
D590 property "enforcing P3 never lengthens the account" was false on the MEAN (`[-2000, 0, -1000]`
adds a second, longer episode: life 1.0 → 1.5, `p3b_life_cost` −0.5) and now asserts the true invariant
with the counterexample pinned; the D591 golden's brick-row guard was an equality over the whole set
difference, so D604's additive row turned it red — widened to membership. **Full suite on the staged tree, and again on the tree merged with the closure branch (D600–D603):
3,552 passed, 1 skipped, 6 deselected (5:29)** against round 2's 2,995/1/6; the skip count is unchanged
and the concurrent session's untracked files were gone by the time it ran, so nothing is red. **Only the
commit is owed, on the principal's word.**

**Findings the agents surfaced that a later study must carry:** `Future.from_specs` returns
`usd_per_point` **100× wrong on seven roots** (ZC, ZS, ZW, ZL, LE, HE high; SR3 low — the definition
file's cents), and D591's `TickCrossing` inherits it: nothing on disk charges those roots today, the next
thing that does will be wrong, and the fix belongs in the specs loader with a golden; ZN's 2025–26 ADV is
2.23× its 2016–23 ADV, so the impact default line is `day1m_2016_2023`; a ±5-tick depth band is 14.34 bp
on ZB and 0.42 bp on NQ — not comparable across roots; Labor Day 2026-09-07 holds every crossed or locked
minute of the whole MBO month and is excluded; the deposit's "CME settlement" job is settlement PRICES
where D586's pages are TIMES, and `cmegroup.com` 403s from this machine; the spec asks for a Parquet copy
and this venv has no `pyarrow` (CSV written instead); the deposit never defines "the CostStack slippage
assumption" or a model EXIT price (D605 takes half the crossing plus one adverse tick, and the exit
shortfall is not computable from the log alone); `t ≥ 2` at exactly 2.0 is one ULP from a fail and a
forward test finishing there is on the bar, not a pass; `np.linalg.lstsq` is not bit-identical to D365's
normal-equations OLS (4.4e-16), so `fit.ols` uses the normal equations and `lstsq` only as the rank
oracle; importing a runner whose module body installs `sys.addaudithook` poisons the collectability gate
for the whole process — compile only the needed function (D593's import-by-path pattern is unsafe for
such runners); a numbered deposit test is claimed by its number in the test FUNCTION NAME from now on,
and a test discharging two documents' items carries the second in its docstring; the D604 depth month
and two of the three impact lines lie inside the deposit's sealed vault window, still unreconciled with
this record's 2024-01-01 holdout — **that reconciliation is the principal's decision and gates every
deposit study**. The MBO replay projected 3.1 min and took 10.2 min on 6 workers at 91%: the probe day
was the second-smallest file.

## SHARED INFRASTRUCTURE, ROUND 2 — D590–D594 COMMITTED `c192908`, 2026-09-21

The principal chose the next five shared components from the same infrastructure list; five parallel
Opus agents built them on disjoint file sets and each was verified here by running its tests and
selftest and reproducing one published number independently. **Do not rebuild any of the following.**

| record | component | files | reproduced here |
|---|---|---|---|
| **D590** | hurdle P (R11) dollar-native, 14 venue plans with per-field provenance, the persisted component daily-P&L series | `validation/hurdle_p.py`, `validation/component_series.py`, `data/prop_venues.json`, `scripts/hurdle_p_report.py`, 4 test files | D440's SPY/voltgt/f* 0.007 cell (life 0.1350875596, V 77.7357587481) exact at 10 dp; a series round-trips through disk and a moved byte is refused |
| **D591** | futures cost layer: `FuturesCommission`, `TickCrossing`, `FuturesRoundTrip.from_table`, the `futures_round_trip` config brick, the reconciled cost table | `costs/futures_bricks.py`, `config/cost_stack.py` (additive), `data/futures_costs.json`, `scripts/futures_cost_table.py`, 4 test files | D527 $4.205511636799441, D556 MNQ 3.50 / MES 4.25 / ZN 21.625 / ZB 37.25, D469 MES 3.40856872519306 ticks — all `==` |
| **D592** | programme α registry (10 slots), `TrialsCsv`, programme trial count, programme DSR, haircut, episode checks | `validation/programme.py`, `validation/episodes.py`, `scripts/programme_registry.py`, `data/programme_registry.json`, `docs/results/PROGRAMME_REGISTRY.md`, 4 test files | D504 `share_ex_both_1pct` 0.9169861341900946 exact from the published totals; the eleventh family refused |
| **D593** | `lag1`/`delayed`/both `audit_lag` generations, `retained_edge`, the AST forward-index scan, leave-one-year-out and purged folds | `validation/lookahead.py`, `validation/folds.py`, `tests/unit/_leaky_canary_module.py`, 4 test files | `lag1` bit-identical to the runner on a tie-heavy NaN/−0.0 grid; canary caught at 4 sites; 8 LOYO folds partition 2016–2023 |
| **D594** | `freeze`/`assert_frozen`, `SealedWindow` with no default dates, the `RESERVED_FROM` helpers, `open_once`, `refuse_without_word` | `validation/frozen.py`, `scripts/freeze.py`, 3 test files | a one-byte drift named; CRLF-only rewrite not drift; second open raises; refusal returns 2 |

**Integration DONE (2026-09-21):** §4 paragraphs in `data-available.md` for `prop_venues.json` + the
`data/components/` convention, `futures_costs.json` and `programme_registry.json`; CHANGELOG bullets
for all five under the round-1 heading; one defect fixed on integration — `component_series.write`
used `repr` on each value and a numpy-backed series wrote `np.float64(…)` that `read` refused; the
writer casts through `float` and a regression test pins it. **One process fault to know about:** the
D591 agent staged its files mid-build to clear `test_cited_decisions_exist`, and the concurrent
basis-momentum session's commit `a3a3ff0` (D600) swept that intermediate state into history — its
record, `futures_costs.json`, the bricks, the builder, `cost_stack.py` and four test files. The final
D591 state is a small staged diff on top; nothing is lost, but D591's first appearance in `git log` is
under D600's message. The other session's own untracked files (`data/fixtures/eia_weekly_stocks.*`,
`hkm_factors.meta.json`, `oecd_ir3tib_monthly.*`, `scripts/build_fut_cleared_volume_cm.py`,
`fetch_macro_series.py`, `stage0_d600_bm_closure.py`) are theirs and were not staged here.

**Findings the agents surfaced that a later study must carry:** D503's `P1_post_sizing_usd_per_year`
is mean × 252 at traded size, not post-sizing (macd sized: $1,088/yr, published $3,971), and its
`P2_pass: True` is hard-coded; no venue file records a daily loss limit, so R11's P3 justification
stays unverified, and Take Profit Trader's flatten time exists in no source here; R11's header still
says P5 ≤ 40% where 30% is operative (RULES.md untouched); the measured `d508_exec` crossing line is
4–48% dearer per round trip than the one-tick line D555/D556 charged on all eight micros where both
exist (MGC +48%, MCL +26%, MBT +23%, MNQ +16%); full-size commission is $4 in D469 and $6 in
D468/D555; D533 charged GC and NG $5.00 that no line derives; `tick_usd` for ZC/ZS/ZW/HE/LE/ZL is in
cents in the definition snapshot and SR3's is a hundredfold small; D504's `concentration_usable`
window runs to 2026-09-09 (not in-sample) and its daily series is not persisted, so its block is
reproduced as a code identity, not recomputed; D504's loop returns `sessions_to_half_pnl = 1` on a
negative total where the port returns `None`; the deposit's "same months" in the shared-period check
is unspecified and was operationalised as the intersection of each model's fewest best-first months
carrying half its P&L; the runners' `np.full_like(a, np.nan)` casts to the grid dtype (int → minimum
int64, bool → `True`, which ranks bar 0 first); the forward-index scan is a tripwire — it cannot see
aliasing, helper indirection, negative strides or a name holding a negative shift; the sealed-window
date is still the principal's open decision and the module refuses to default it.

## SHARED INFRASTRUCTURE FOR THE SIX NEW DEPOSIT PRE-REGISTRATIONS, ROUND 1 — D585–D589 COMMITTED `89feba9`, 2026-09-21

Six more documents landed in `docs/internal/User-Doc-Deposit/` on 2026-09-21: `SETTLEMENT_FLOW_LEDGER_PREREG`
(v1.9, the parent design), `INDEX_REWEIGHT_FLOW_PREREG`, `LETF_CLOSE_FLOW_PREREG`, `SHOCK_CLASSIFIER_PREREG`,
`OPENING_AGENT_STATE_PREREG`, `ARCHITECTURE_OVERVIEW`. They were reviewed against this record and split
into research items and infrastructure items; the principal chose **five shared infrastructure components**
and had them built by five parallel agents (Opus; the `.claude/agents/opus-high.md` definition written for
the effort pin was not visible to the launching session, so effort was not pinned). **Do not rebuild any
of the following.** Each is on disk, untracked, with its tests passing and its record written:

| record | component | files | verified |
|---|---|---|---|
| **D586** FIXTURE | CME settlement-window table, 17 products, CT+ET, effective dates | `data/settlement_windows.csv` + meta, `data/settlement_flow/SOURCES.md`, `scripts/settlement_windows.py`, `tests/unit/test_settlement_windows.py` | 48 tests; `window_for("NG", 2023-06-01)` = 14:28–14:30 ET (SER-4867, 2009); ES 15:59:30–16:00 ET (SER-8591, 2020-10-26); XX and GC-2023 raise; in-window volume 2.5–16.9× the flanks on 128/128 root-years |
| **D587** design | shared futures fill model + `Future` instrument | `src/backtest_framework/instruments/future.py`, `simulator/futures_fills.py`, 4 test files under `tests/{unit,golden,property}/` | 129 tests; bit-identical to `run_d490_range_reversion.py:simulate` (44 trades) and `d465` pessimistic MAE (50 sessions); 20/20 mutations caught. The ONE tracked edit: `instruments/__init__.py` (+21 lines, deliberately does not cite D587 until the record is committed) |
| **D588** design | power module (design effect, ICC, n_eff, SE, MDE, forward-length and Track-3 routes, POWER.md renderer) | `src/backtest_framework/validation/power.py`, `scripts/power_table.py`, 3 test files | 78 tests; ledger unit tests 51/52/53/59/62/63 exact; `n_eff_cross_series` == `scripts/ragged_panel.py:effective_instruments` |
| **D589** FIXTURE (was to be D584; D584 was taken by the concurrent basis-momentum session) | CME session calendar + event flags, 36 roots, 205,428 rows 2010-06-07 → 2026-09-09 | `data/fixtures/cme_session_calendar.csv.gz` + meta (gitignored by suffix → **needs a manifest entry**), `scripts/build_cme_session_calendar.py`, `tests/unit/test_cme_session_calendar.py` | 24 tests; ES early closes 2019-11-29 / 2019-12-24 (225 bars), 390 on 2019-11-27; `roll_day` == `fut_sessions_rolls` on all 9 roots; per-root closes measured (SI 13:25, HG 13:00, GC 13:30 ET). G6 (CME holiday page) `not_fetched`: cmegroup.com blocks this machine |
| **D585** FIXTURE | sourced release calendar with times (CPI, EMPSIT, FOMC scheduled + unscheduled at each statement's printed clock, EIA WPSR, EIA NGSR), 1,501 rows 2016-01-06 → 2026-12-31 | `data/calendar/events.csv` + meta + `SOURCES.md`, `scripts/fetch_release_calendar.py`, `tests/unit/test_release_calendar.py`; 196 raw pages in `data/raw/calendar/` (gitignored) | 25 tests; CPI 12/yr except **11 in 2025** (the 2025-10 funding lapse, sourced); FOMC_UNSCHEDULED 2020-03-15 17:00 ET present; 0 `inferred` rows; **nine 2016-2023 dates in `data/macro_release_calendar.json` are wrong** (enumerated in the meta; that file untouched, `run_d494_outside_path.py` still reads it) |

**Integration DONE (2026-09-21, all staged, NOT committed):** session calendar rebuilt with `--events
data/calendar/events.csv` (flags now span 2016-01 → 2026-09-09; fixture sha256 `1164a241…`; amendment
block at the top of D589); D585/D586/D589 paragraphs in `data-available.md` (§1 for the calendar, §4 for
the two reference tables); CHANGELOG entries for all five under "Added (2026-09-21, shared
infrastructure…)"; `data/data_manifest.json` rebuilt (123 entries, the calendar fixture added, nothing
else changed); every new file staged by explicit path (the six untracked deposit docs and
`working/arm_spread_at_entries.csv.gz` deliberately NOT staged — they are the principal's); register
regenerated (`build_decision_register.py --write`, 303 numbers) and README counts regenerated
(`build_readme_counts.py --build` — run it under `uv run`, the system python has no pytest). **Full suite
on the staged tree: 2489 passed, 1 skipped, 6 deselected (4:57)** against the pre-build baseline of 2185
passed, 1 skipped, 5 deselected — the skip count is unchanged, the 304 new tests all pass. The first run
showed 16 red, all repo gates reacting to new files, none a defect in the components: the quoted-count
gates (nine living documents updated by hand: golden 101→133, property 67→96 across 10 files, unit
1,859→2,102, total 2,186→2,490, decisions D584→D589 / 819 files / 552 numbers, raises 280→359 across
49 of 87, modules 46→49); the running-page figure gates (`docs/RUNNING.md` now says 123 panels and names
the calendar fixture as the eighth without a blob; the anchor in `tests/unit/test_running_page_figures.py`
moved with it); the encoding ratchet (`test_encoding_is_declared` reads the INDEX, so a fix is invisible
until re-staged; ten `read_text`/`write_text`/`read_csv`/`to_csv` sites in the calendar builder now pass
`encoding="utf-8"`); and one agent test that had pinned the old flag source's end date, rewritten to
assert against the meta's recorded source. **Only the commit is owed, on the principal's word.** 47 files
staged, 18,406 insertions.

**Findings the agents surfaced that a later study must carry:** CME publishes windows in CT for CME/CBOT
products and ET for NYMEX/COMEX (the deposit's "Chicago time" is half wrong); the energy expiring month's
last day settles on 14:00–14:30 ET, a different object; the livestock and equity-index windows are 30 s
long and unresolvable on a 1-minute bar; the three COMEX metals settle three hours apart from grains and
equity, so the index doc's basket has staggered `W_end`s; "COMEX metals close 13:30" is gold only; the
D490 runner's `MULT={"ES":5.0,"NQ":2.0}` are the MICRO point values (its numbers are right, its labels are
not); a fourth incomplete March-2020 ES session (2020-03-18) and a second archive dropout (2020-02-27) exist
beyond those recorded; D588 found the ledger doc's §13A.7(2) cap ambiguous (it capped evaluation days) and
the LETF §6A H1 cell straddling its own adoption rule; two pre-existing ruff F601 errors sit in
`scripts/stage0_d575_livestock_placements.py`. One stray: the D586 agent fetched SER-8591 through the browser
pane, which left a byte-identical copy in `C:\Users\O\Downloads\`; the cited copy is in `data/raw/cme_settlement/`.

**The review itself, not yet recorded anywhere else:** the six docs' sealed vault (2025-03-01 → 2026-09-18)
has to be reconciled with this record's 2024-01 futures holdout and the spent NQ/overnight/trend/carry slices
before any of them runs; every signed-flow feature they specify (ledger update step, TAS, large-lot, opening
A7, shock flow-flip exit, index C0 calibration) lives only inside that vault period (tbbo 2025-09-11 →
2026-09-11; mbo one month), and the historical pull is free only until ~2026-10-11; the opening doc's H-O2
subtracts "the best of B1–B3 per day", an ex-post oracle that must mean the best baseline overall; the LETF
doc's k = 3 activation gate is on for almost every day at micro cost. None of the six constructions has been
built here — the record holds baselines and single-ingredient tests in the same windows (D463/D530/D581 at the
close, D499/D528 after large moves, D531–D535 at the open), not the combining layer.

## THE DEPOSIT FOLDER, AND ITS FIRST STUDY (D555), 2026-09-19

The principal dropped fourteen documents into `docs/internal/User-Doc-Deposit/` — a mechanism-first
research programme written outside this repository (framework: `ALPHA_PROGRAMME`, `FEATURE_RESEARCH`,
`DATA_EXPANSION_PLAN`, `READING_LIST`; slow-book derivations: `HEDGING_FLOW_DERIVATION`,
`BASIS_MOMENTUM`, `PUBLISHED_STRATEGIES`; seven intraday event studies indexed by `EVENT_PORTFOLIO`,
one of them killed at premise). **Its conflicts with this record are set aside on the principal's
instruction** (micro flow as a retail proxy, the spent overnight holdouts, the micro cost floor);
the instruction is to examine the programme, starting with its published strategies.

**[D555](../decisions/D555-RESULT-does-not-pass-and-the-harness-reproduces-AQR-at-0-815.md) —
TSMOM as published, 36 roots, DOES NOT PASS; HARNESS OK.** The replication correlates **0.815** with
AQR's own monthly factor over 2011–2023 and out-earns it (0.44 vs 0.30), so the futures data layer
is calibrated against a free published benchmark for the first time. On 2016–2023 the 12-month book
scores **+0.30 gross** at the 78th percentile of an enumerated sign-rotation null (p95 +0.95), and
AQR's factor reads **−0.02** on the same window. **Two things to carry:** (i) the pre-registered
rotation null was contaminated — offsets within a lookback of either end of the cycle are look-ahead
on one side and stale momentum on the other, and were purged in the record (the offset profile shows
+2.3 at a −252…−21 shift and **−0.76 at +252…+504**, the long-horizon reversal); (ii) the breadth
fixture carries a **placeholder Sunday row every week** (0 bars, no close) and 69 one-bar weekend
stubs — chain returns across kept rows only, or a fifth of every root's returns vanish.
**[D556](../decisions/D556-RESULT-does-not-pass-carry-timing-is-negative-on-2016-2023.md) — carry
timing as published, DOES NOT PASS.** The settlement strip now exists (`fut_settle_strip.csv.gz`,
3.3 M settlements, 36 roots, every listed month, 2010 → 2026; and `fut_curve_front_next.csv.gz`, the
front/next basis per root-session), gated: it reproduces D526's CL/GC strip **exactly**. On it the KMPV
rule is **−0.20 gross on 2016–2023** (38th percentile of its purged null) after **+1.61 on 2011–2015**;
ρ with trend is **0.18** as the deposit said, and folding carry into the trend book at equal weight
takes the Sharpe from +0.30 to +0.20 while cutting max drawdown from −36% to −29%. **The dollar book
at minimum size reads +0.20 and it is one contract of palladium** (+$276k of a +$216k total) —
a 34-root one-contract book is a bet on whichever full-size contracts carry the largest dollar σ,
and it can disagree in sign with the equal-risk book.

**D557–D559, the three cross-sectional sorts, ran in parallel as three agents in three worktrees
(2026-09-19), each committing its pre-registration first on its own branch; merged with `--no-ff`
so the cited spec hashes (`e3a5785`, `60aa4fc`, `000eda0`) resolve on main.** All three DO NOT PASS,
all three dollar books at minimum size are one contract of palladium, and all three rotation nulls
have a positive median because a persistent cross-sectional membership is mostly a fixed per-root
tilt that a common-offset rotation keeps. **One cross-agent check did not agree and is explained,
not resolved:** D559's in-process single sorts read −0.065 / −0.105 against D557's −0.207 and
D558's −0.259 because D559 drops a name missing EITHER signal from BOTH sorts (declared), so its
single sorts are on a different eligibility. **Two defects the agents found in the shared machinery:**
(i) D555's `signal_at_month_ends` floor (240 returns per 12 months) scales to 20 returns for a
1-month read and voids every 19-session month — livestock and grains routinely, and April 2017
and April 2023 for every root; D559's unfloored amendment moved its primary from −0.11 to −0.44;
(ii) the term-structure/momentum sorts leave a 0.55 correlation between each other and 0.72/0.80
with the double sort, so the deposit's "two mechanisms" is what the data shows.

**[D557](../decisions/D557-RESULT-does-not-pass-the-term-structure-sort-is-negative.md) — cross-sectional term structure as published, DOES NOT PASS.** Rank the 17 commodities by the front–next basis, long the six most backwardated, short the six most contangoed, equal weight, hold a month: **−0.21 gross on 2016–2023**, at the **14th percentile** of its purged rotation null — whose **median is +0.16**, because the membership is mostly a fixed per-root tilt (NG short 66 of 96 months, PA long 60) that a common-offset rotation keeps and re-times; the sort's own timing is among the worst phases. The long leg earns and the short leg loses on every statistic (the contango leg was short gas, wheat, corn and hogs, which rallied); March and May 2020 are −12% and −11% on the same three energy names, long then short. Vol-scaling the identical membership gives +0.02: at 17 names the weighting choice is worth 0.23 of Sharpe and neither form carries the sort. The dollar book at minimum size is +0.28 net and, as in D556, **it is palladium** (113% of the total). ρ with CM carry timing is 0.49 daily — half the variance shared, not one mechanism.

**[D558](../decisions/D558-RESULT-does-not-pass-xs-12-1-momentum-negative-on-commodities.md) — cross-sectional 12-1 momentum as published, 17 commodities, DOES NOT PASS.** Rank on the 11 months ending the month before, long the top third, short the bottom third, equal weight, held a month: **−0.26 gross on 2016–2023** (SE 0.31), at the **35th percentile** of its purged rotation null (p95 +0.71), −0.20 over 2011–2023; ρ 0.62 with D555's time-series book on the same roots (which is −0.06). The loss is the **short leg** (−0.77 bp a root-month against +0.29 for the long leg) and the **energy block** — the five energy roots contributed −0.39 of a −0.27 total, sit in one leg on 56 of 96 month-ends, and ex-energy the book is +0.12; a sector-capped sort is a different construction, not an amendment. The worst month is May 2020, short CL/RB/BZ/HO on the April crash — the momentum crash, and TSMOM lost it too. The dollar book at minimum size is +0.05 and it is palladium (+$133k) against RB (−$84k).

**[D559](../decisions/D559-RESULT-does-not-pass-the-double-sort-is-negative-2016-2023.md) — the momentum × term-structure double sort as published (FMR 2010), DOES NOT PASS.** Terciles on 12-1 momentum, then the most-backwardated third of the top tercile long and the most-contangoed third of the bottom tercile short, two names a side: **−0.11 gross on 2016–2023** at the **25th percentile** of a purged rotation null whose median is **+0.08**; −0.44 with the calendar artefact removed. It is the two single sorts intersected (ρ 0.72 / 0.80, both negative under the same rule), at 1.5× their vol and a −55% drawdown; the loss lives in the **short corner** (NG, ZW, livestock — the seasonally-contangoed names, D556's un-deseasonalised carry). The dollar book is palladium a third time (+$85k of +$82k).

**[D561](../decisions/D561-RESULT-none-sharpens-trend-is-carry-s-tail-not-its-hedge.md) — three sharpenings of D555's trend book, each evaluated, none sharpens it at the declared standard.** The principal asked whether the mechanism could be sharpened; the assessment was that the signal could not be and the three real levers were power, sizing and role, and each was pre-registered with a null and run (38 s). **Power:** the 13-year rotation null is nearly as wide as the 8-year one (sd 0.51 against 0.58, predicted 0.43) and its median moves to **+0.11** with the window's long tilt; the 2011–2023 book (+0.46) sits at the **68th** percentile — the null's width is set by regimes, not sessions, and no window of this fixture passes a trend book of published size. **Sizing:** a per-root leverage cap is monotone in Sharpe (+0.07 / +0.20 / **+0.25** / +0.27 against +0.30 at caps 1 / 5 / 10 / 20 / ∞), binds only on ZT / ZF / ZN / SR3 at the declared 10, and the worst day is the **same macro session at every cap** (2021-11-26, the Omicron Friday: −6.0% capped against −6.8%); the component line is D555's, unchanged. **Role:** on ES's worst 5% of days trend earns **+0.26 σ**, 0.93 σ above a null whose median (a long-tilted random sign book) loses 0.68 σ — rank **0.939 against a bar of 0.95**, and the vol-matched blend halves the equity drawdown at the 9th percentile against a bar of 5; four of ES's five worst months were positive. Beside D556's carry the sign flips: **−0.56 σ on carry's worst days, below all 1,562 rotations**, at ρ 0.18 — the deposit's "uncorrelated, so hold both" is true of the body and false of the days, and C-b is a body statistic. Recommended for any pair entered in the ledger: the worst-day c5 with its rotation null beside ρ.

**[D562](../decisions/D562-RESULT-forward-slice-plus-0-51-inside-null-not-a-hedge.md) — THE FORWARD READ, on the principal's instruction ("settle the forward slice"): the 2024+ slice of the futures fixtures is SPENT for trend, for carry timing, and for any assembled book containing either.** Pre-registered in `04ea121` before any 2024+ session was read. D555's 12m book on 2024-01-02 → 2026-09-09 (696 sessions): **+0.51 gross / +0.50 net, Sortino +0.71**, inside its rotation null (median **+0.18** — the long tilt again — p95 +1.30, rank 0.69); harness held out of sample at **ρ 0.73** with AQR, whose own factor earned +0.93 on the same months against this replication's +0.45 monthly (universe, not construction). Six of seven predictions held. **The whole P&L is 2026** (metals and equities; 2024 +0.27, 2025 −0.31); two roots reach half. **The shape inverted:** on ES's 34 worst days trend lost **1.29 σ at the 5th percentile** of random sign books, ρ with ES +0.31 (in sample −0.13), because the 2024–2026 selloffs (Aug 2024, Apr 2025, Mar 2026) were V-reversals and the book was long into them; the vol-matched blend's drawdown ratio sits exactly at the null's median. D561's falsifier ("diversification, not convexity") is confirmed out of sample with the sign reversed. Carry A forward **−0.56**. Dollar book net +0.71 = three full-size contracts (NKD, HO, RB), σ $10,920, sub-book −0.08: no prop vehicle. **Disposition B by the declared rule: a return-component candidate for the personal book only, not a hedge, sized by vol target** — admission is the principal's, and `BOOK.md` has no written standard for a monthly-hold futures stream yet. Loader fact for anyone reading the extended fixture: from 2026-05-30 BTC carries weekend-dated rows with up to 22 hourly closes (CME weekend crypto sessions); D562's loader drops them so the Monday return spans the weekend as every other root's does.

**[D563](../decisions/D563-CLOSED-the-trend-and-carry-lines-on-the-futures-fixtures.md) — the trend line and the carry-timing line are CLOSED by the principal, 2026-09-19**, after D562 ("This does not seem to have sufficient edge"). Closed: MOP's 12m sign book and every lookback and cap scored here (D555, D561), KMPV's carry timing in all three cells (D556), the deposit's §8 combined forecast and the seasonal-adjusted carry (both carry-timing constructions). No new pre-registration on either construction on these fixtures. **Not closed:** the three cross-sectional sorts (D557–D559, DOES NOT PASS, 2024+ unread — D557 and D559 rank on the same `carry_ann`, cross-sectionally; the principal's word covered the two lines named, and extending it to the sorts is a one-line addendum to D563); the deposit's parked premia (hedging pressure, basis-momentum, skewness, value), untested here. Surviving instruments are D563 §4: the purged rotation null, the tilt reading of its median, the worst-day c5 beside ρ for any ledger pair, per-root decomposition of a one-contract book.

**[D564](../decisions/D564-RESULT-passes-only-under-the-formation-amendment.md) — basis-momentum as published (Boons–Prado 2019, the construction as Kwon–Kang–Yun 2021 state it): as pre-registered DOES NOT PASS; under a formation-rule amendment, the first PASS of the deposit series.** Twelve-month momentum of the first-nearby minus the second-nearby, both built from the settlement strip by the delivery rule (≥ m+2, energy ≥ m+3), High4 long / Low4 short on the 17 commodity roots. Run as pre-registered: **+0.42 gross at the 80th percentile**, with **24 of 97 formation month-ends flat** — traced to two calendar sessions, **2020-06-30** (a truncated archive day, 237 of ~900 settlements) and **2021-05-31** (Memorial Day, in the session calendar on a Globex evening bar), each voiding twelve month-ends for every root. Amended to D556's rule (last settlement within five sessions of the month-end), applied to all cells, pre-registered number kept beside: **+0.69 gross / +0.99 Sortino, rank 0.972 in N1 (p95 +0.54), 0.971 in N2, 0.975 in the name-randomised N3 (5.5 SE above its p95)**; eight of nine predictions hold, including no post-2010 decay and the vol interaction (high-vol months Sharpe 1.15 vs 0.36). **The amendment was made after the pre-registered percentile was read**, and it restored the June 2020 → May 2022 months, which earned +0.28 of the +0.64 total at Sharpe 1.21; on the 73 month-ends both books position they agree (0.49 vs 0.52, ρ 0.95). **Caveats that matter:** two roots reach half the P&L (NG, short 81 of 83 months, and ZL); the nine non-seasonal roots read **−0.09** — the effect here lives in the seasonal curves, the deposit's §6.4 warning; it shares carry A's worst days at the **0.5th percentile** (c5 −0.29 σ), as the deposit's T4 predicted. Dollar book net +0.36 at σ $3,803 (HO 37%); the C-d-eligible six-root sub-book **+0.49 at σ $340**, 0.015 under the C-a bar. **2024+ unread — the one deposit line whose in-sample result would justify the forward read; the principal's call.** Next reads, each its own pre-registration: a de-seasonalised BM (or the paper's 21-commodity universe), and the six-root sub-book as a construction.

**THE PER-ROOT AVATAR PROGRAMME (the principal, 2026-09-20): each root's strategy built to the party its constraint binds, flat by default.** Data fetched into `data/raw/eia/` and `data/raw/usda/` (gitignored cache, public domain, committable as derived fixtures): EIA weekly working gas 2010 → 2026-09 with regions and the capacity report; EIA weekly distillate, gasoline, crude and Cushing stocks plus the capacity workbooks; USDA WASDE every monthly report as published, April 2010 → September 2026 (69 files, each with its release date; the 2016–2020 archive zip did not land and October 2025 is missing by name); the COT fixture already holds the disaggregated report for NG, LE, HE, ZC, ZS, ZW — ZL, ZM, HO, RB, PL, PA and the supplemental index-trader report are still to add. NASS Quick Stats needs a key the agent cannot register.

**NG Stage 0 (diagnostic, this session):** the storage state the mechanism names — working gas against its five-year band, lagged to release — predicts nothing about the next month of the NG curve once the calendar is removed (residual Spearman −0.02, year-block p 0.7); the calendar itself is where the curve moves (the front falls 11 % in December, 10 of 13 years; the front-minus-second spread is small and short-paying 10 of 13 in Nov, Feb and Mar). The NG avatar is therefore the **obligated winter buyer**, not the storage owner, and the construction is a scheduled spread.

**[D565](../decisions/D565-RESULT-NG-spread-rank-0-94-provisional-avatar-unsupported.md) — the NG winter-premium calendar spread, flat by default: DOES NOT PASS by 0.007, and the ledger's SECOND ENTRY, PROVISIONAL.** Short T1 (delivery ≥ m+3), long T2, one MNG a leg, formed at the last session before each of November–March (the EIA withdrawal season, declared from the agency's definition with the Stage 0 windows disclosed), flat otherwise. **+0.69 gross / +1.03 Sortino** on 2016–2023 at the **94.2nd percentile** of its placement null (p95 +0.699); 40 positioned months, hit 0.75, median +0.34 %, worst −3.5 %; beats the always-on spread three to one per positioned day, and the off-season is negative. At one micro a leg: **net +0.62, skew +1.98, σ $24 a day, +$1,261 over eight years** — every ledger bar clears, and under D468's rule it enters as PROVISIONAL **#3** (K8 #1 is CLOSED and the MACD arm #2 ADMITTED since 2026-09-13; the row was first written as #2 in error and corrected). Cost is a third of gross at one pair. **The avatar is unsupported**: commercial long share rises into Oct–Nov in only 7 of 13 years (0.396 vs 0.390); the legacy category nets buyers against sellers, and the supplemental report or FERC 552 would be the test. **The joint read is the principal's**: the assembled book is the admitted MACD arm (#2, its NQ day-session 2024+ slice spent in D503) plus this spread; the NG 2024+ slice is unread (thirteen positioned months). Pre-registered as D566 when taken.

**[D566](../decisions/D566-RESULT-the-NG-spread-did-not-transfer-REMOVED-book-unchanged.md) — THE JOINT FORWARD READ, on the principal's word: the NG spread did not transfer and entry #3 is REMOVED; the prop book is unchanged.** NG's 2024+ slice is spent for the withdrawal-season spread and any book containing it. Forward, thirteen positioned months: **−1.07 gross / −1.22 net**, 5 of 13 positive, mean −1.76 %, worst −9.72 % (January 2026), **−$878** at one pair; placement null rank **0.277** (its median −0.73: a short spread placed anywhere lost on these seasons). The two forward seasons were formed with the front **8 and 13 % below** the second — the opposite curve state to every in-sample season — and the short lost into two cold snaps; skew went from −0.01 to −3.1. The assembled book with the admitted MACD arm: **+0.650** at one pair against **+0.712** for the arm alone on the 696-session union calendar (Sortino 0.99 vs 1.09), **−0.325** at twenty pairs; ρ **+0.01**; the joint null (MACD signal rotated and spread placed at random, 2,000 draws) puts the one-pair book at rank 0.943 UNRESOLVED, exactly where the MACD alone sits (0.948) — the book is the arm. Hurdle P: **P2 fails structurally** (a spread held through the month crosses every permitted venue's flatten time), P3a 1.09/yr at one pair and 6.16 at twenty against a bar of 1.0. The MACD arm's forward series was regenerated by D503's frozen code and reproduced its artifact to 1e-6 before use. **Lesson for the next avatars, recorded and not applied:** a formation-basis premise (a winter spread already in backwardation is not the premium the mechanism names) belongs in the grains' and livestock's Stage 0 as a test, not in NG as an amendment.

**[D567 Stage 0](../decisions/D567-STAGE-0-RESULT-avatar-fails-on-corn-inverts-on-soybeans.md) — the grains at harvest, designed first (`d557e52`) and then run: the merchant-at-harvest avatar fails on corn and inverts on soybeans.** Thirteen harvests a root, 2011–2023, 2024+ shut; the WASDE stocks-to-use fixture (`data/fixtures/wasde_grains_su.csv`, 163 releases, point-in-time) is committed. Corn's Z/H spread **narrows** over Sep–Nov in 9 of 13 (the carry is priced by the end of August; the curve is at full carry at formation in 1 year of 13); stocks-to-use says nothing (ρ −0.09). Soybeans' F/H spread widens as designed (11 of 13, t −2.3) but **most when stocks are tight** (ρ +0.65, p 0.02; tight tercile −1.05 % vs full −0.10 %): a pre-harvest inverse collapsing, the short-bought crusher and exporter as the constrained party — an avatar re-derived from the data, to be written as seen. Wheat is the only root at full carry at harvest (8 of 13); its outright falls 5.6 % on average (9 of 13, 2012 +32 % the tail). **Survives:** (1) corn post-harvest carry narrowing, Dec–Feb, long H / short K, **9 of 12, t +2.6, monotone in stocks-to-use** (tight +1.11 %, full +0.24 %) — the honest next pre-registration, ZC's 2024+ unread; (2) corn weather-premium decay, short new-crop Z Jun–Aug, 9 of 13, −8.7 % in non-drought years, **+29 % in the two drought years** — recorded, not a prop candidate; (3) the soybean harvest widening, pre-registrable only as seen. Two design corrections made before reading: WASDE release dates normalised (some files are month/day/year), and pairs chosen to survive the window (the design's X/F and N/U pairs expire inside it). The leave-one-year-out control is vacuous with one observation a year and the record says so; a placement null in the runner replaces it.

**[D568](../decisions/D568-RESULT-does-not-pass-the-always-on-spread-beats-the-window.md) — the corn post-harvest carry narrowing, pre-registered (`752041d`) and run: DOES NOT PASS, and the finding is the control.** Long H / short K by the grains delivery rule (asserted to survive the window), one ZC a leg, December → February, flat otherwise. **+0.60 gross / +1.00 Sortino** on 2016–2023 at the **85th percentile** of its exact placement null (p95 +0.71); 24 positioned months, hit 0.58, worst −0.61 %; net +0.42 in return space and **+0.43 in dollars at one pair** (σ $28 a day, +$760, cost 29 % of gross) — fails C-a, **not entered**. **The always-on long spread earns more per positioned day than the window (1.11 vs 0.90 bp; +0.50 gross / +0.35 net)**: by calendar month the corn front gains on its deferred in **April (+6.4 bp a day) and June (+7.0)** and gives it back in July (−5.8); December, where the design put the merchant's selling, **loses 10 of 13**; the window's return is February. The real-time stocks-to-use gate (≤ the median of prior Novembers, one declared cut) opened 4 of 10 decidable windows including both losers — the seen ordering (ρ −0.44) is real and the cut did not select. The merchant avatar fails in the COT (commercial net short share falls through the window in 5 of 12, mean change +0.018): **with D567's harvest result the merchant-at-harvest avatar has failed on corn in both halves of its year**, as the pre-registered falsifier said. The corn curve's spring narrowing is a diagnostic, not a licence; any further corn construction is a new Stage 0 **with the always-on control per positioned day in it** — D567's Stage 0 had none, and the window that led was the drift sampled in its third month. ZC 2024+ unread (eight positioned months). Also recorded: the WASDE fixture on disk spans 2010-04 → 2026-09 (195 releases), not the 163 D567 states; corrected in D567 and D568, and the runner filters it first.

**[D569 Stage 0](../decisions/D569-STAGE-0-RESULT-schedule-holds-avatar-does-not-october-reverses.md) — the soybean harvest addendum, designed (`7b06f8f`) and run: the schedule holds where corn's failed; the avatar does not.** The short first-nearby soybean spread earns **+0.42 bp a positioned day over Sep–Nov against −1.15 always-on** (it loses every other month, most in Jun–Aug: the nearby strengthens through the growing season and harvest releases it); placement rank **0.972 exact**; the one declared real-time stocks-to-use cut (August S/U ≤ the median of prior Augusts) opened **2016, 2021, 2022, 2023 — all four paid, +0.71 % vs +0.16 % ungated**, the seven flat years −0.16 %. Against it: the curve is inverted at formation only in 2012–13 (the "pre-harvest inverse" is not the ordinary state); commercial net short **falls** through harvest in 8 of 13 and the spread widens most when it falls least (ρ +0.57, p 0.045, the predicted sign reversed); **2012 is half the thirteen-year total** on either object (without it B pays 10 of 12 at +0.28 %); and the rule-rolled object A gives back October on its X/F leg and pays a roll (cost 39 % of gross at one ZS a leg), where D567's F/H survival pair B is smooth (Sep +0.27 %, Oct +0.05 %, Nov +0.21 %) and four sides. **Under the design's declared rule the schedule may be pre-registered, as seen, avatar unsupported — the principal's call**; if taken, on B, gate as a secondary with its cut unchanged, hit and without-2012 mean predicted, ZS 2024+ (the 2024 and 2025 harvests, six positioned months) the only clean test. Not licensed: a summer long spread (the same mechanism's other side, unseen as a schedule), any other cut, the T7 sign as a signal.

**[D570](../decisions/D570-RESULT-does-not-pass-best-placement-is-july-september-on-X-F.md) — the soybean harvest spread on the F/H pair, pre-registered as seen on the principal's word (`2503321`) and run: DOES NOT PASS; the construction's own placement null found the real window two months earlier.** B (short F / long H, Sep–Nov, one ZS a leg): **+0.40 gross / +0.54 Sortino** on 2016–2023, net +0.32; months hit 0.62, worst −0.64 %; in dollars **net +0.41, skew −1.31, σ $57, +$1,542, cost 16 %** — fails C-a and C-c, **not entered**. The schedule is real: the always-on short loses −0.80 bp a day and D569's rolled cousin under the same mask is at the **99.3rd percentile** of its exact placement null (+0.80 / +1.24). But **the same construction placed at each of the twelve calendar months puts Sep–Nov third: July → September on X/F earns +1.24 / Sortino +1.97 (2011–2023 +0.61), Aug–Oct +0.77** — the pre-harvest widening of the new-crop November against January starts in July and the harvest window catches its tail (corn's D568 shape with the season reversed). And **the rolled cousin beats the F/H pair per positioned day in sample (+0.67 vs +0.53 bp)** — which the seen thirteen-year table already showed on the 2016–2023 subset; the F/H pair's lead was 2012 and 2013, outside the primary window. **The object was chosen on the wrong window of a table already in hand; recorded as the lesson.** The gate (seen) did as D569 said: 2016, 2021, 2022, 2023, four of four, +0.68 gross / +0.61 net, skew +0.54 — the only cell clearing C-a, a declared secondary on four windows, not carried. **The July X/F placement is a null cell, now seen for all twelve placements: any construction on it is a new Stage 0 and would be pre-registered as seen with ZS 2024+ (unread) as its only test.** Seven audits and the N2-by-construction check proven to raise; the current-year-median gate break inert, recorded.

**[D571 Stage 0](../decisions/D571-STAGE-0-RESULT-not-supported-profiles-are-root-specific.md) — the cross-root placement profiles, designed (`935dfcf`) with the best placement predicted from the soybean profile, then run on corn, wheat, oil and meal: NOT SUPPORTED.** The prediction held on corn (best *m*6, in {6, 7}) and meal (*m*7, in {7, 8, 9}) and was **falsified on wheat** (flat profile, best *m*2) **and oil** (*m*7 is the *worst* of twelve, −1.13 on 2016–2023: the same crop, the opposite sign) — two of four, chance level; profile Spearmans with soybeans +0.27 / −0.39 / −0.14 / +0.01. What held on all four is the always-on control's sign: a short nearby grain spread held year-round loses everywhere. **Corn's own structure is a different pair: short the old-crop September against the new-crop December, June → August, +0.75 / +1.04, +2.3 % a window, 13 of 13** — D567's weather-premium decay from the spread side; a null cell, seen, not licensed. Meal's declared *m*7 V/Z is the one candidate by the rule (best of twelve, above control, +0.42 gross) and fails C-a (net +0.29; the return is September alone, hit 0.85; the neighbouring placement is its worst). **No entry.** The grains now hold three seen, unlicensed cells — corn U/Z Jun–Aug, soybeans X/F Jul–Sep, meal V/Z Sep — each pre-registrable only as seen with two forward windows; the principal's call. **Erratum, fixed in the shared helper:** December delivery months were labelled one year late in the pair tables of D565's and D567's artifacts and D571's first log (labels only; every number stands, asserted by re-running).

**[D572](../decisions/D572-FIXTURE-COT-extended-to-the-six-missing-commodity-roots.md) — the COT fixture extended to ZL ZM HO RB PL PA: 34 symbols, 274,473 rows, every one of the 17 commodity roots now has its positioning series.** Two more resolution traps pinned (`%HEATING OIL%` matches only spreads, the outright is `NY HARBOR ULSD`; `%RBOB%` matches ten, the outright is `GASOLINE RBOB`). The six new series run to 2026-09-15, the original 28 to 2026-08-25 (not re-fetched); nothing before 2024 differs. **BZ has no COT series** (ICE Brent is not a CFTC market), so a positioning sort ranks 16 roots. A positioning-only probe for the hedging-pressure pre-registration (no outcomes read): legacy commercial rows are complete on all 16 roots 2010-06 → 2023-12 (709 reports each, no gap over ten days, a release date on every row); hedgers' hedging pressure persists at the monthly horizon (13-week autocorrelation 0.27 RB → 0.87 PA); and **53 % of the cross-sectional variance of the 13-week mean is the root's own mean** — the metals (PL 0.25, GC 0.31, PA 0.33, SI 0.36) sit permanently low and NG (0.56) and ZW (0.54) permanently high, so the published sort is in large part a static tilt, which the pre-registration declares a de-meaned cell and a name-randomised null to separate.

**[D573](../decisions/D573-RESULT-does-not-pass-the-sort-is-the-tilt-and-the-tilt-lost.md) — hedging pressure as published, pre-registered (`563eafa`) and run: DOES NOT PASS; the sort is the tilt and the tilt lost.** EW published **−0.20 gross / −0.28 Sortino** (SE 0.36) on 2016–2023, net −0.21, max DD −53 %; **below its time-rotation median** (rank 0.076, p50 +0.085, 1,562 offsets exact) and at the **26th percentile of the name-randomised null** (2,000 draws, p50 +0.01, p95 +0.57 with SE 0.013). The tilt prediction held at 71–98 %: PL GC SI PA long, NG ZW short, at nearly every month-end, and CL HO ZS HG short in more than half — the book was short the energies through 2021–22 (HO −$138k, CL the largest loser in book units) and long palladium as its one winner (+$207k of a −$46k dollar total). Every cell negative: vol-scaled −0.37, dollar −0.065 net at σ $5,504, the six-root sub-book −0.06 at σ $573 (fails C-a, C-c, C-d together), the de-meaned cell −0.23 (−0.48 on 2011–2023), so the premium is not in the movement either. ρ with the term-structure sort on the same 16 roots +0.18 (predicted > 0.4; both negative; legs shared about half). The long leg earns +3 bp a root-month and the short leg loses 6. By era 2011–15 +0.14, 2016–19 −0.06, 2020–23 −0.30; Basu–Miffre's sample ended 2011. Six audits proven to raise; the release-date audit found 141 of 300 cells change under report-date keying. **Not entered. The deposit's list is scored end to end**; skewness and value remain parked by the deposit itself. Palladium was the largest single line in four of five cross-sectional dollar books on this universe — declare its treatment before any future sort.

**[D574](../decisions/D574-RESULT-inside-the-total-transfers-the-composition-inverts.md) — THE FORWARD READ of basis-momentum (D564) on 2024-01-02 → 2026-09-09, pre-registered (`7085aac`) and run on the principal's word: INSIDE; the total transfers at 70 % and the composition inverts. The 2024+ slice is SPENT for basis-momentum in every form on the 17 commodity roots and for the C-d sub-book.** Harness first: the in-sample primary rebuilt on the full calendar equals D564's artifact to 1e-9 (+0.692157 amended, +0.420717 as pre-registered). Forward, 696 sessions and 33 months: EW High4/Low4 **+0.48 gross / +0.69 Sortino** (SE 0.58), hit 0.55, worst month −6.1 %, **March 2026 +13.2 %** (2024 +0.43, **2025 −0.35**, 2026 +1.21); rank **0.728** in the full-span rotation (p95 +1.05) and **0.798** in the name randomisation (p95 +0.93) — a 33-month window cannot decide, and the verdict rule says INSIDE. **The amendment is inert forward** (the as-pre-registered book is identical to every digit; no flat month-ends). **The composition prediction failed in every clause**: the seasonal roots that carried the in-sample result (NG short 81 of 83 months, ZL) read **−9.4 % at Sharpe −0.47** forward, NG was long at 59 % of month-ends and short at none and lost −8.4 %, ZL lost −10.1 %; the nine non-seasonal roots (−0.09 in sample) made **+27.1 % at +0.84**; **heating oil is 86 % of the forward P&L** and one root reaches half. The dollar book: net **+0.99**, +$251k, σ $5,791, HO +$154k (61 %) — clears its own rotation null on one contract; the six-root sub-book **+0.04**, +$428. The time-series diagnostic cell is +1.09 forward (in sample +0.22), unpredicted. c5 on carry A's worst forward days −0.22 σ: still carry's tail. **Nothing enters**, as declared before the number: the dollar book failed C-a and C-d in sample; the sub-book was a subset under the bar. **Lesson:** a total that transfers while its carriers reverse is a rule that picks something every month and was lucky in sample about what; before any forward read of a cross-sectional book, predict the names and rank that above the Sharpe. The futures-curve programme now has no construction with an unread slice and an in-sample pass.

**[D575 Stage 0](../decisions/D575-STAGE-0-RESULT-not-supported-no-open-construction-on-the-curve.md) — the livestock placement profiles, designed (`892b177`) with each root's best placement predicted from its own supply calendar and cattle's feedlot-hedge avatar named as a disjoint alternative, then run: NOT SUPPORTED, and the closing clause fires.** Hogs: the predicted placements {7, 8, 9} are the three most consistently negative of the twelve (−0.16 / −0.19 / −0.29); best *m*12 (Dec–Feb on J/K, +0.46 / +0.22), predicted by nothing; the declared Aug–Oct Z/G construction **−0.28 / −0.38**, hit 0.42, **2020 window −17.2 %**; the always-on short loses 2.7 bp a day. Cattle: a flat profile (eleven of twelve within ±0.4), best *m*2 (Feb–Apr on M/Q, **+0.63 / +0.84**, 10 of 13), outside both the supply set {3, 4, 5} and the hedge set {10, 11}; the declared Apr–Jun Q/V construction −0.08; the control +0.05 bp a day, the one root where the always-on short neither loses nor earns. Neither declared construction is best of twelve; no candidate; both fail C-a at one contract. **The seasonal-spread line on the commodity curve has no open construction**: after twenty records it holds five seen cells (corn U/Z Jun–Aug, soybeans X/F Jul–Sep, meal V/Z Sep, hogs J/K Dec–Feb, cattle M/Q Feb–Apr), each with two forward windows as its only test, and nothing pre-registrable with a clean test. What every root shares is a sign, not a schedule: the always-on short nearby spread loses on every grain and on hogs and is flat on cattle. Closing the line is the principal's call (R15). Six audits a root proven to raise.

**[D576](../decisions/D576-CLOSED-the-seasonal-line-and-the-futures-curve-synthesis.md) — THE SEASONAL CALENDAR-SPREAD LINE IS CLOSED by the principal, 2026-09-20, and the futures-curve programme D555 → D575 is synthesised** (`docs/FINDINGS.md` §76 carries the substantive result). Closed: every flat-by-default nearby commodity spread held through a mechanism-named window — NG, the corn, soybean, oil, meal, cattle and hog constructions and their variants — and the avatar programme including the two roots (HO, CL) not yet designed. Not closed: the five seen cells (corn U/Z Jun–Aug, soybeans X/F Jul–Sep, meal V/Z Sep, hogs J/K Dec–Feb, cattle M/Q Feb–Apr), parked as one-shots; the fixtures and machinery. **The synthesis:** no published commodity premium is a component at this account's size (five sorts negative or inside their nulls, four dollar books one palladium contract; basis-momentum the one pass, forward INSIDE with its composition inverted; trend real, small, rare, no vehicle; carry negative twice); every seasonal window that looked real failed the always-on control, its own placement null, a prediction made before the read, or the forward slice; what every agricultural root shares is that the always-on short nearby spread loses, which is carry. The prop book is one arm; the ledger has no entry from the curve. **The search for component #2 moves off the commodity curve** — the day-session mechanism on the index roots other than NQ, and the COT fixture's financial families on the index and rates futures — both unscoped, each to the principal before a slice is read. Spent slices by line: trend and carry (36 roots), the NG spread, basis-momentum (17 CM roots), the NQ day session, the overnight leg; every other line on every other root is unspent.

**[D577 Stage 0](../decisions/D577-STAGE-0-RESULT-P9-neither-declared-net-swap-dealer-responds.md) — P9 of the CL hedging-flow derivation (`HEDGING_FLOW_DERIVATION.md` §1.7, §12: "P9 first"), designed (`a42d19a`) and run on 708 weekly disaggregated reports 2010–2023 with the 12–24-month strip as the regressor and no return read: NEITHER CATEGORY RESPONDS on the declared statistic.** Gross short vs the strip over four weeks: swap dealers +18k contracts a log-point (NW t 1.2, shift-null rank 0.939, p95 +18.9k), producer/merchant t 0.8, SD share 0.57 against a bar of 0.6; SD's split betas have the ratchet's mirror shape and PM's have the ratchet's shape. **The response is two orders of magnitude below the derivation's prior** (+477 contracts per $1 over four reports vs 18–37k). The statistics declared beside say what the declared one cannot license: the **swap-dealer NET short responds** (+44k, t 2.7 at four weeks; +71k, t 3.7 at eight) while **producer/merchant net short moves the other way** (t −2.0, −3.6) — the categories' gross longs (index and consumer clients; refiners) rebalance with their shorts, so PM+SD gross nets to nothing; SD gross short clears its null at eight weeks (t 2.1, rank 0.982); the yearly SD net-short levels match the derivation's three natural experiments (128k → 35k through 2015–16, 144k held through 2020, 61k → 22k in 2022–23); producer/merchant is net LONG in eleven of fourteen years. The corrected mapping (SD net short, eight weeks) is post-hoc on seen data; **its clean sample is the 2024+ reports (~90 weekly, untouched)**, and a pre-registration of it there is the honest next record; the scale gap is what it must also explain. Seven audits proven to raise, including a synthetic-flow check of the sign convention.

**[D578](../decisions/D578-RESULT-does-not-transfer-no-weekly-instrument-in-the-COT.md) — the corrected mapping pre-registered (`5f0cfcd`) and tested once on the 139 unread CL disaggregated reports 2024-01 → 2026-08, on the principal's word: DOES NOT TRANSFER.** Harness first (the in-sample betas equal D577's artifact to 1e-6). Forward, the swap-dealer net short's eight-week response to the 12–24-month strip is **−32k contracts a log-point (t −1.1, rank 0.112 in the exact shift null; −110k on seventeen non-overlapping changes)** against +71k in sample; four weeks −8.6k; the gross short −8.5k; the mean eight-week change is negative on rallies and positive on declines. The producer/merchant net short falls hard on rallies (−275k, rank 0.000) with nothing on the other side. The June 2025 rally and the March 2026 spike produced +677 and +5,302 contracts of net swap-dealer selling in the eight reports after — a fortieth of the derivation's arithmetic, neither top quartile. The yearly levels rose (SD net short 29k → 57k → 87k, 2024–26) — the story at the resolution of years, as in D577 — and at weeks there is nothing. **The derivation's flow model has no weekly instrument in the disaggregated report as built; P1–P3 cannot be run on it; the line stops at the measurement as the deposit's §12 says.** What would measure it (a fetch and a record each, none on disk): the CFTC supplemental report to strip index clients from the swap-dealer line; disclosed hedge ratios as a quarterly series (the derivation's P7); Dodd–Frank swap data. **Spent:** the CL disaggregated 2024+ reports for this line. **Seen:** the CL 12–24-month settlement path to 2026-09, read as a regressor — any later CL curve study on those tenors must say so. **Post-mortem (§4 of the RESULT, `scripts/diag_d578_postmortem.py`):** the in-sample +71k was robust to every outlier cut but was a 2014–2019 phenomenon (2015–19 +118k t 5.5; 2020–23 +23k t 0.8; rolling three-year β −0k at end-2023) carried by a swap-dealer gross short that fell from 184k to 32k contracts over 2019–2023; the forward slice continued a regime already dead in sample. D577's fault: no era split, rolling β or level path reported before the statistic was taken forward.

**[D579](../decisions/D579-FIXTURE-perpetual-funding-rates-and-open-interest-three-venues.md) — FIXTURE: perpetual-swap funding rates (Binance, Bybit, OKX; BTC and ETH; 46,892 settlements 2018-11-15 → 2026-09-20) and Bybit daily open interest from 2020-08-04, free, `scripts/fetch_perp_funding.py`, six gates proven to raise.** What bites: Binance +1 ms wire offsets (floored to the minute), a third to a half of every series at the +0.01 % default (exclude from signed tests), the rate at S known only to within the last minutes (the in-advance rate is S−8h's), open-interest history Bybit's alone.

**[D580](../decisions/D580-STAGE-0-RESULT-not-supported-a-five-minute-unsigned-burst.md) — Stage 0 of the funding-cycle premise on CME bitcoin ([design](../decisions/D580-STAGE-0-DESIGN-the-funding-clock-on-CME-bitcoin-premise-check.md) `382ef54`): NOT SUPPORTED.** Fixture `fut_btc_1m.csv.gz` built (`build_fut_btc_1m.py`, 3 min, gates green, in the manifest). The clock IS on CME at the settlement minute — volume 1.9× and r² 1.8× the cycle mean for five minutes, profile peak at minute 0, beats every other top of the hour, non-overlapping placement rank 1.00 — but the declared 60-minute window ranks 0.937 / 0.874 in the 96-placement null (bar 0.95), clears it in 0 of 6 years, and the burst is gone in 2022–2023 as |F1| fell from 2–3 bp to 0.7 bp. The funding sign orders nothing: y_post(30) −1.0 bp (SE 1.5), ranks 0.38 / 0.08, +4.8 bp in 2021 and −9.6 in 2022. Five amendments recorded (presence by session not by bar — the literal rule kept 1,215 of 6,611 settlements on a contract that prints 59 % of open minutes; the halt inside the 00:00 cycle; no trade count in the schema; non-overlapping rank beside; London offset). Terminal by the deposit's kill 2 and kill 4; nothing follows; the 2024+ minute slice is unread by this line. The five-minute unsigned burst is parked.

**[D581](../decisions/D581-STAGE-0-RESULT-not-supported-gamma-sign-orders-nothing.md) — Stage 0 of the gamma-conditioned close on ES ([design](../decisions/D581-STAGE-0-DESIGN-gamma-conditioned-close-on-ES-the-discriminator.md) `3d7db80`): NOT SUPPORTED.** Two zero-cost Databento pulls on the principal's word (`ES.OPT` is the QUARTERLY family alone — 47.7 GB; the 24 weekly/daily families are their own parents — 336.2 GB billable, ~67 GB compressed) built `fut_es_options_eod.csv.gz` (19.2M rows, 2,658 sessions, 25 families, six gates green, `build_fut_es_options_eod.py`). The interaction of the 15:30→16:00 return with the 14:30→15:30 move and the carried-gamma sign is **c −0.023 (NW t −0.66), rank 0.32 in the enumerated day-shift null** on 1,990 sessions; +0.0005 in 2016–21, −0.076 (rank 0.08) in 2022–23, −0.003 in 2023 alone; the little there is sits on sessions WITHOUT a same-day expiry. The close continues its prior hour in every regime (b +0.10, t 2.9 — D463's momentum). Carried OI sees ≤ 8.5 % of same-day gamma even in 2023. Kill 2; the convention neither confirmed nor refuted; nothing follows; the 2024+ minute slice unread. Four data traps recorded in data-available (parent symbols, recycled year codes, expired-option OI, the AM quarterly).

**The deposit's list is CLOSED ([D582](../decisions/D582-CLOSED-the-deposit-and-the-mechanism-programme-synthesis.md), the principal, 2026-09-21).** Every one of the fourteen files is run or killed: the five published strategies (D555–D559), basis momentum (D564/D574), hedging pressure (D573), the hedging-flow derivation (D577/D578 and the post-mortem), micro flow (D485), the overnight imbalance (D468/D470; line closed 2026-09-12), the cascades (killed at premise by the deposit), the session handoff (not prop-compliant, never designed), the funding cycle (D579/D580), the gamma close (D581), and the seasonal avatars (D576). Nothing on it is pre-registered again without a new deposit or a new fixture the record names. Three parked facts with numbers are in D582 §3. **Next is the principal's decision:** a purchase that opens a line not on the list, or a new deposit; Norgate extends only closed lines and signed option flow serves the mechanism whose cheap test failed.

**Basis momentum's M7 is NOT SUPPORTED ([D583](../decisions/D583-STAGE-0-RESULT-not-supported-quarter-ends-order-nothing.md), 2026-09-21; design `00100c5`).** The one open deposit item with data on disk and no closure in the way: the reporting calendar does not order the D564 book (ΔPRE −0.37 bp/day, rank 0.47 in the 63 enumerated placements, 0.34 non-overlapping; the quarter-ends rank 0.23 among the 495 four-month subsets and sit *below* the other month-ends; December is the worst quarter, above the other three in 4 of 12 years; 5 of 12 years positive). Harness to D564's artifact to 1e-9 first; every audit raised on its break; no 2024+ session read. Parked facts: the book earns its December in the first four sessions of January (+65 bp after the year-end, −30 bp into it); the quarter-end settlement session itself is −10 bp pooled and −39 bp in December. M1–M5 remain undesigned; M4 (the He–Kelly–Manela capital ratio, a fetch) would separate "wrong mechanism" from "wrong instrument", but with the line's forward slice spent (D574) nothing could use the answer, so it is not recommended. What the deposit still names without a run needs inputs not on disk (M3–M5; the hedging-pressure disaggregated COT) and is behind the D582 closure.

**The basis-momentum closure programme has run on commodities ([D600 design](../decisions/D600-STAGE-0-DESIGN-basis-momentum-closure-programme-M3-M4-M5-T3.md), [D601 fixtures](../decisions/D601-FIXTURE-macro-series-for-the-basis-momentum-closure-programme.md), [D600 result](../decisions/D600-STAGE-0-RESULT-M3-M4-not-supported-M5-unresolved-on-storage.md), 2026-09-21; numbered from D600 because the concurrent session had claimed the numbers just below) and the ruling on `BASIS_MOMENTUM.md` is the principal's.** Five verdicts: M3 NOT SUPPORTED (BM(2,3) +0.37 at N1 rank 0.90, curvature −0.08; the primary scored on the second nearby earns +0.70, as much as on the front — the curve moves together); the de-seasonalised signal SURVIVES N1 (0.958) but is 0.9-correlated with BM because a twelve-month sum cannot carry a calendar (arithmetic, not evidence); T3 clears the paper's bar (IC(1) +0.048, t 2.2; buckets monotone; 9 of 12 years) and not the protocol's (t ≥ 3), and the IC rises with horizon; M4 NOT SUPPORTED (β +0.006, t 0.13 on the He–Kelly–Manela factor; after the capital ratio's lowest tercile the book earns 81 bp/month less, rank 0.05); M5 UNRESOLVED on its letter and against the paper on its meaning — on the five energy roots the signal is negatively correlated with the inventory surprise on every root (−0.13 to −0.48), storage in the signal. The capacity table shows the COMEX metals' held contracts are the inactive months (PL 25 lots a day). **Not run, on the ruling below:** the NASS fixture would have waited on the principal's `NASS_API_KEY` (free registration at quickstats.nass.usda.gov/api; env var or `~/.config/nass/key`), after which `fetch_macro_series.py --fetch nass --build` and a re-run of block E extend M5 to ZC ZS ZW LE HE; T2 on FX ran and is **VOID on its own harness** ([D602](../decisions/D602-RESULT-VOID-the-parity-correction-over-shoots-on-monthly-rates.md)): the covered-parity correction from monthly-average 3-month rates over-shoots the rate-differential component (BM_raw −0.51 with the twelve-month change in the differential, BM_fx +0.60 against a bar of 0.3), so no verdict on FX is available; the raw form is −0.04 in sample, the only cell that clears a null is a time-series form 0.6-correlated with rate momentum, and the FX 2024+ slice stays unread; a passing construction needs forward or OIS rates not on disk. **The principal ruled on 2026-09-21: closed** ([D603](../decisions/D603-CLOSED-basis-momentum-every-free-test-run-none-supported.md), in D582's shape) — the NASS extension of M5, a re-specified FX construction and T1 are not run, with the reasons in the record; nothing on BASIS_MOMENTUM.md is pre-registered again without a new deposit or a fixture the record names; the FX 2024+ slice stays unread.

**Basis momentum's M1 and M2 are NOT SUPPORTED and the negative control is UNRESOLVED on its letter ([D584](../decisions/D584-STAGE-0-RESULT-M1-M2-not-supported-the-control-unresolved.md), 2026-09-21; design `958bf07`, on the principal's word).** The 8 least liquid roots earn +5.46 bp/root-day more than the 9 most liquid at rank 0.85 in the 24,310 splits, Spearman +0.02 against a predicted negative, 5 of 12 years, and the difference is two roots the book holds least (PL +34.5 on 107 days, GC −12.2 on 61; without them −0.2). The 21 sessions after a vol spike earn −0.57 bp/day less than the rest at rank 0.44 in 3,224 shifts, 5 of 10 years, profile peak at lag 31–35. The BM signal's correlation with commercial HP is −0.15 (SE 0.05) and with its 12-month change −0.11, inside the bar; the same-week signed commercial flow is −0.35, above the 0.3 bar but with the sign opposite to "riding the flow" and equal to the commercials-against-price relation every root shows (−0.47, 16 of 16 negative); the prior week's flow predicts nothing (−0.03). Four of the four free mechanism tests (M1, M2, M7, and the control's letter) now fail or stall on the seen book; M6 alone held. Lesson recorded in the record: a control's bar needs the sign its falsifier names. M4 (a fetch) remains the only separating test and is not recommended, since the line's forward slice is spent.

---

## CME FUTURES ARE NOW ON DISK — 111.0 GB, verified, 2026-09-12

Databento `GLBX.MDP3` under a one-month CME Standard subscription. Every job quoted **$0.00**
against **$7,719** at published rates; total cost was the $199 subscription.
**`data/raw/databento/<job-id>/*.dbn.zst`** — gitignored, and **NOT in `temp/`**.

| schema | scope | window |
|---|---|---|
| `ohlcv-1m` | every instrument | 2010-06-06 → **2026-09-10** |
| `mbo` order book | ES NQ RTY YM CL GC ZN ZB | 2026-08-11 → 2026-09-10 |
| `tbbo` trade+quote | every instrument | 2025-09-11 → 2026-09-11 |
| `statistics` / `definition` / `status` | 41 roots | 2010-06-06 → 2026-09-11 |
| `bbo-1m` | 41 roots | 2025-09-11 → 2026-09-11 |

**129/129 hashes and byte counts verified, 16/16 DBN headers match the request, and the ten
`ohlcv-1m` slices tile with zero gaps and zero overlaps**
([`data/futures_acquisition_verification.json`](../../data/futures_acquisition_verification.json)).

**Four things before anything reads it.** Prices are **UNADJUSTED raw symbols with no
continuous series at all** — the roll must be built from `definition`. The pull ends
**2026-09-10**, so "through 2026-09-11" is wrong by one session. `ohlcv-1m` arrived in **ten
jobs** and a loader must read all ten. And it is free to re-fetch only to **~2026-10-11**.

**No fixture exists over it yet.** That needs the seven gates in `fetch_futures_1m.py`
reworked: they assume a *continuous stitched* series and this is *raw-symbol full-universe
across seven schemas*, so the roll gates do not transfer.

---

## PRICE ACTION AND VOLUME — the slate, and the first one reported (D497), 2026-09-12

The principal asked for price-action and volume constructions for the prop book. **The specification
any prop day-session candidate faces is now FINDINGS §69** (a measurement, closing nothing): the
cost/move table by micro, the accuracy targets, and the fee-and-barrier identity. **The arithmetic
that should govern the choice** (committed fixtures, this session): on the NQ day session the
average 10:00→16:00 move is 286 MNQ ticks against a 7.01-tick round trip, so **the fee is 2.4% of
the average move**. Break-even is **51.2% directional accuracy**, a component Sharpe of 0.5 needs
**53.6%**, and the log MACD gets ≈ 50.7%. **Cost is not the binding constraint at this horizon;
direction is.** That also kills the "trade only the wide days" lever, which only pays where
cost/E|M| is large.

**The slate, ranked, with the dead ones named:** (1) open interest against price — **RUN, see
below**; (2) volume per unit of overnight range, an absorption read that is not the overnight
return D494 already killed; (3) where in the session the volume sits (front-loaded against
building into the close); (4) session-scale signed order flow on the D485 tape fixture (right
horizon, one year of sample); (5) the prior session's volume point of control, ranked last because
D490 showed the specific level is where the losses come from. **Already dead, do not re-propose:**
yesterday's range plus a volume spike (D490, D492), volatility-conditioned continuation (D474,
D475), opening-range breakouts, path shape (D471), channels (D476–D483), contract size as a
participant proxy (D485). **Held by the other session:** MACD confluence and the daily-state fades.

**[D497 RESULT](../decisions/D497-RESULT-the-four-quadrant-open-interest-read-carries-nothing.md)
— the four-quadrant open-interest read carries nothing.** The `statistics` schema had never been
read here; it is now a gated fixture (`fut_open_interest_daily.csv.gz`, four roots, 2010→2026,
100% coverage, causality asserted: open interest for trade date T is first published ≈ 21:00 ET on
T, so a 10:00 entry on T+1 legitimately knows it). No cell is positive net, none clears its exact
rotation p95 or the family bar. The open-interest term adds +3.5 and +6.4 gross dollars a session
on ES and NQ and subtracts 5.9 and 5.4 on CL and GC, with no consistent ordering against a
cleared-volume version and every difference inside one SE. On gold the "short covering, therefore
fade" quadrant is the most *positive* (+$10.7 over 334 sessions). **Useful negative: open interest
is distinguishable from volume**, so neither can be dismissed as the other in a later record.
One gate could not fire as written and is recorded as amended rather than passed off.

---

## ALL IN ON THE PROP BOOK — the principal, 2026-09-12; the lane split between sessions

The principal: *"we are going all in on the prop book, so if it doesn't help that then we have to
figure something else out."* Three interactive sessions are open on this repo. **The lane this
session holds** (D493, D494): the account-size lever through the lifecycle, and one stage 0 for
direction from outside the price path on the day session (cross-instrument overnight moves,
index-level retail sentiment, release days as a gate on the MACD). **The lane the MACD/cost session
holds** (D484, D486 and its §6): extending the MACD hold past five hours, costing GC and CL,
passive fills, the real commission schedule. Neither touches the other's; decision numbers are
taken at commit time against `docs/decisions/` (D485 → D486 → D492 were taken by three sessions
inside one hour). The retail line's single-name herding test and the micro proxy are **dropped
for the prop book**; Robintrack stays on disk for the personal book.

**Both reported the same evening.** [D493 RESULT](../decisions/D493-RESULT-the-account-size-lever-fixes-the-fee-and-runs-into-the.md):
the size lever fixes the fee (NQ last-30 net Sharpe −0.13 at one micro → +0.48 at one full contract)
and runs into the barrier — a full contract's daily σ is 3–6× the plan's trailing drawdown, funded
life 0.03–0.16 years on all 14 plans, **0 of 448 cells carry**; the MACD at one round trip a session
is +0.16, not D486's +0.35 (that lane owns the reconciliation). **A prop signal needs a daily Sharpe
near 0.1 at the size that makes the fee small; size cannot supply it.**
[D494 RESULT](../decisions/D494-RESULT-outside-the-price-path-on-the-day-session-eighteen.md):
eighteen day-session cells from outside the price path — five cross-instrument overnight
predictors, index-level Robintrack sentiment, three release-day gates on the MACD — **no pick**; the
largest is the euro at one ES tick a session; the MACD earns *less* on CPI and payroll days. The
shifted-predictor [F] control was mis-designed (it measures spillover) and is withdrawn in the record.
**Where this leaves the prop book:** nothing the programme holds carries a funded account, and the
day session on the index futures at hourly resolution does not carry direction from bonds, FX,
commodities, retail or the calendar. What has not been tried: a component whose gross per session
is several full-contract ticks by construction — which on D473's arithmetic means a hold of most of
a session with ~55% accuracy from a source not yet on the table — and the account-size lever is
closed as a fix on its own.

---

## THE RETAIL-FLOW LINE — OPENED 2026-09-12; the futures arm reported (D485), the equity arm drafted

The principal: *"Lets try using more auxiliary data. Lets hunt retail traders."* Scoping in
[`docs/research/retail-flow/00-scoping.md`](../research/retail-flow/00-scoping.md): the literature
says the **body** of retail flow is weakly informed *with* it (+10 bp a week, Boehmer et al.) and only
the **extreme of attention** is contrarian (−4.7% over 20 days for the day's most-herded Robinhood
stocks, Barber et al. 2022) — "trade against retail" as a blanket rule is not what the evidence says.

**D485 (futures arm, pre-reg `0651bb9`, RESULT):** the micro contracts' signed flow (exact aggressor
side from `tbbo`; new fixture `fut_micro_flow_5m.csv.gz`) is **not a retail identifier**: within-session
correlation with the E-mini's imbalance 0.71 (ES) / 0.76 (NQ); micro trades are *not* smaller (NQ's
E-mini has more one-lots than the micro); no contrarian tilt, no sell bulge into the flatten window,
no relation between the day's micro flow and the last hour. The declared four-cell read against the
micro crowd's excess flow: ES/F1 +$26 a session at one MES sits exactly at its own exact-rotation p95
and at the 58th percentile of the family maximum — **no pick**; the reserve (2026-07 → 2026-09) unread.
My recommendation: close the futures arm on this record; the principal decides.

**The equity arm:** Robintrack is on disk (`data/raw/robintrack/`, 4.0 GB, 8,597 tickers hourly
2018-05 → 2020-08, 959 of the mining names covered), pre-reg drafted in
`working/DRAFT-robintrack-stage-0.md` (top-decile herding, 20-day hedged return, a same-day
|return|×volume matched control that must take at least half of it). **Needs a decision number and
a commit before its runner.** The Nasdaq RTAT10 ten-year daily top-10 table needs a Data Link API
key from the principal (free tier; I cannot create accounts).

---

## THE DAILY CHANNEL LINE IS CLOSED — the principal's decision, 2026-09-12

D399 → D483 on the `worktree-signal-hunt-part2` branch, **no holdout read**.
[Closing record](../decisions/D483-CLOSE-the-daily-channel-line-D399-to-D483.md);
FINDINGS §68. Direction: five causal cells below their rotation nulls (long +1 to +17 bp gross),
worse as the gradient floor rises, including the cell that reproduces the principal's own
hand-drawn lines (D480/D481). Level: +44 bp gross over 5 bars above its null (D482) — and a
close 4% below the 30-bar low with **no lines** earns +47 (D483). The channel is not the
ingredient.

**Kept:** the labelled set `data/d478_hand_drawn_lines.json` and its scorer
`scripts/d478_score_hand_lines.py`; the hand cell `scripts/d480_hand_cell.py`; the runner
`scripts/run_d478_grow_trades.py` (three rules, two sources); five pages (Draw the Lines,
Step by Step, Grow Right, Perfect Hindsight, the hand cell). **The line was renumbered at the
merge on 2026-09-12** because the branch's numbers collided with master's: the channel line now
sits at D398, D399, D476 and D477–D483 (the closing record carries the old→new map; master's own
D434 and D450–D463 are unrelated records). The branch's `docs/FINDINGS.md` §59 became §68.

**Owed to a different line, if picked up:** the reversal after a 4% break of a 30-bar range,
both directions — the book and a null at the cost-clearing hold (15–20 bars), a
volatility-matched control, and the literature on one-month reversal.

---

## D521 — THE DATA LAYER IS CLEAN: NO BUILDER LABELS A BAR FROM A FLAT ID DICT, AND ONE FIXTURE WAS WRONG, 2026-09-13

On the principal's instruction to port the windowed mapping to the three flat builders, after the
audit in [`working/AUDIT-flat-id-map-exposure.md`](../../working/AUDIT-flat-id-map-exposure.md).

**`fut_open_interest_daily.csv.gz` was carrying a phantom contract and is now corrected.**
Instrument 42007396 was `6AF4` (Australian dollar, January 2024) until 2024-01-21 and was reissued
as `CLG36` in November; the flat dict keeps only the last label, so an FX contract was counted as a
**61st crude contract on 2024-01-03 … 2024-01-19**, overstating `oi_total` by 235–401 contracts
(0.014–0.026%). **`oi_front` was never touched anywhere** and all 63 gate scalars are identical.
**Re-pull any cached CL total from before this commit.**

**The other two fixtures are byte-identical.** `fut_micro_flow_5m` (one year, ES/MES/NQ/MNQ) and all
six `fut_index_1m` outputs. The index build had **16,077 foreign RTH bars (0.229%, 18 of 26 files)**
ingested by the flat map and the front-by-volume rule dropped **every one** — the D520 outcome again.

**The rule this leaves:** *front-month columns are insulated from the id defect; totals and strip
counts are not.* The open-interest fixture is the only one here with a column that has no volume
filter in front of it, and it is the only one that moved. A **term-structure study reads exactly
those columns** — which is why the audit said to do this before any curve work, and it was right.

**Also: `build_fut_index_1m.py` is now parallel** — 1.02 billion rows went from ~20 min
single-process to **6.2 min on 6 workers (5.67×, 94%)**. `--verify N` proves the pool is a speed
change only (serial vs pool, `check_exact=True`, per-file frames, concatenated frames and assembled
bars), and it must keep passing or a fixture diff means nothing. **Run these three builders with the
SYSTEM `python`, never `uv run`** — databento lives only in the system interpreter.

**Everything is recomputed by** [`scripts/d521_flat_vs_windowed_audit.py`](../../scripts/d521_flat_vs_windowed_audit.py)
→ [`data/d521_flat_vs_windowed_audit.json`](../../data/d521_flat_vs_windowed_audit.json), reading the
flat-map side from **git** rather than `temp/`, so it survives `temp/` being deleted.

---

## AVENUE 3 CLOSED BY THE PRINCIPAL, 2026-09-14 — and 16 of 36 ROOTS DO NOT TRADE IN THE day5m CLOSE

The leveraged-ETF daily reset: a fund must reset exposure to a fixed multiple of THAT DAY'S CLOSING
NAV, so after a move r the forced trade is A*L*(L-1)*r — positive for L=+3 AND for L=-3, so long and
inverse funds both BUY after an up day. Forced by prospectus, deterministic size, hedged in index
futures. It came out of the lead-scan census as a genuine hole: absent from all 43 briefs and all six
exclusion lists.

**Its tradeable form was already dead** (D463; ledger K2/K3/K4: NQ gross +$0.66, ES +$0.62, YM +$0.08
against $4.21). **Its two MECHANISM predictions, never tested, now fail too:** dose-response in
|return of day| reads 47.20% -> 50.63% with Q5 at z ~ 0.49, and concentration in the equity index
reads **hit 50.03%, z = +0.1 on 7,489 observations**. Per-root the signs disagree. The flow IS real —
the equity roots trade **15.7-21.1% of session volume in the closing hour against an even 14.3%** —
it just carries no direction. See
[D530](../decisions/D530-avenue-3-closed-the-leveraged-ETF-reset-flow-is-real-and.md).

**THE DURABLE PART, and it is a trap for any day5m study.** My first run showed a spectacular
z = -12.6 "closing reversion" across 19 non-index roots. It was my control group measuring dead air:
**the five grains have ZERO bars in 15:00-15:59** (they close 14:20 ET), livestock 0.02% on 18
sessions, and **CL 3.1% / HG 2.6% / NG 3.9% / SI 4.4% have full bars and dead volume** because COMEX
closes 13:30 and NYMEX 14:30. A close measured in an illiquid tail bounces on the spread, and
**bid-ask bounce is indistinguishable from mean reversion**. **16 of 36 roots** have that hour outside
their market. Recorded in data-available.md note (ii-b).

**AND IT REACHES BACKWARD:** every price-action statistic computed over the 09:00-15:59 template on a
COMMODITY root in this programme has included hours that root barely trades — **D515's CL and GC rows
included**. NQ's day edge is measured on NQ's own session and stands. A session-native re-measurement
of the commodity roots is the obvious next move.

---

## D527 — THE ADMITTED ARM FILLS AT THE WORST MINUTE OF THE DAY; ITS COST LINE IS AMENDED, 2026-09-14

The loose end from the micro-spread census, checked on the principal's instruction. **The arm's
1.009-tick crossing is a market-wide average and the arm does not trade at an average moment.**
It decides at h09's close and fills at h10's open, and two thirds of the time the signal already
agrees at 09:59 — so **66.6% of entries land at 10:00, where MNQ averages 3.66 ticks and is one tick
only 19.5% of the time**, against a day-session baseline of 1.61. **75% of exits are the forced flat
at 15:59, the day's BEST quote (1.44).** The arm systematically enters at the worst moment and exits
at the best, and the concentration is structural, not luck.

    round-trip crossing   1.009 tk assumed -> 2.411 measured
    round trip            $3.50            -> $4.21   (+20.3%)
    in-sample net Sharpe  +0.724           -> +0.661    (C-a's bar is 0.5)

**THE ENTRY STANDS** — amended, not retired; see the amendment at the foot of `COMPONENTS_PROP.md`.
**The row's headline +0.698 is NOT restated**, because a full re-score would have to read the spent
2024+ slice and that needs a better reason than this. Nothing was touched in the arm's code: the
instrumented copy of `simulate` is asserted bit-identical (1,876 sessions, 1,908 trips, $15,423 —
D508's own figure).

**THE BIAS RUNS IN THE ARM'S FAVOUR and the record says so.** tbbo is 2025-26 and the window is
2016-23; NQ went 4,000 -> 27,000 against a FIXED $0.50 tick, so the tick was ~7x coarser then and a
coarser tick locks at one tick more often. **$4.21 is nearer an upper bound on the in-sample cost
than an estimate of it — and it is the right number for DEPLOYMENT.**

**THE GENERALISABLE POINT, and the reason this matters beyond one row:** gross was 3.9x the assumed
cost so the arm absorbed a 2.4x error. **A construction whose gross is 1.5x its assumed cost would
have been reported viable and been dead**, and nothing in the prior process would have caught it.
Measure the spread at the strategy's OWN fill timestamps.

**Not taken:** entering a few minutes after the hour, or skipping h10, would avoid the worst quote —
but that is a DIFFERENT construction and this entry is frozen. It needs its own pre-registration.

---

## THE SEARCH FOR COMPONENT #2 IS OPEN — three Stage 0s run, 2026-09-14

The principal opened it with a framing: **tell a STORY** — a mechanical account of what is happening
under the numbers — and added a constraint, **"our first strategies must not be venue specific and
can fit any venue for now."** That constraint is written into `RULES.md` as an amendment: **score
hurdle P at the INTERSECTION of venues, not per venue** — flat by 3:10pm CT, no overnight, assume a
2% daily loss limit and the 30% consistency cap. It partly reverses the P2 amendment's 22-hour
MyFundedFutures route, and it costs nothing live because the principal had already closed overnight
for prop. **The admitted arm already complies.**

**THE REFRAME THAT SHOULD DRIVE THE SEARCH.** The admitted arm hits **50.5%** with a payoff ratio of
**1.13**: `0.505 x 1.13 - 0.495 = +0.076`. At a payoff of 1.00 its edge would be **+0.005**. *The one
thing that works is not paid for being right — it is paid for being right BIGGER.* Every previous
search hunted ~55% accuracy. **Hunt shape, not accuracy.**

> **THAT REFRAME IS WRONG AND WAS CORRECTED THE SAME DAY — [D529](../decisions/D529-the-payoff-ratio-is-exit-geometry-the-hit-rate-is-the-edge-and.md).**
> A detached signal run through the arm's OWN exit produces a payoff ratio of **1.041 at the median
> and 1.138 at p95**; the arm's 1.128 is **inside** that. Its **hit rate of 50.5% is outside it
> entirely — 0 of 400 draws reach it.** Accuracy alone flips the null's expectation from −0.031 to
> **+0.031**; asymmetry alone only reaches +0.011. **The arm is paid for being RIGHT, and the payoff
> ratio is exit geometry.** Hunt accuracy — about three points of hit rate over the candidate's own
> exit null — not shape. Everything below this line that reasons from "shape" inherits the error.

**Stage 0 #1 — taker affordability across every CME-verified root** (`working/stage0_taker_affordability.py`).
NQ is **not** uniquely cheap: NG ties it at 2.1% cost/move, HG 3.1% and SI 3.4% all beat ES's 4.2%.
But **a root is cheap BECAUSE it moves and fails C-d for the same reason** — corr(log cost ratio,
log σ) = **−0.541** — and NG/HG/SI are locked out at σ $1,081/$704/$1,249 against a $500 bar. **The
micro is what breaks the tie**, and we had verified only seven of them.

**Stage 0 #2 — the micro census.** MNG, MHG and SIL all exist and trade (3,191 / 5,090 / 24,932 lots
a day-session against our ONE lot). **All three are now CME-verified in `futures_contract_specs.json`**
with ticks cross-checked against the archive. Re-priced at their own measured spreads: **SIL 4.8%
(1-tick median), MNG 8.0%, MHG 10.8% (drop it)**. **Two corrections fell out:** the repo's 1.009-tick
crossing assumption is an INDEX-micro number — **MGC quotes 2 ticks wide, one-tick only 25.7% of the
time**, so GC's 5.6% was understated; and **MNQ's median spread is 1.00 tick but its mean is 1.55
with only 56.8% of trades seeing a one-tick market**, which is worth checking at the arm's actual
entry timestamps. Then the MACD edge on the three new roots: **silver's edge is in the NIGHT**
(day +0.0028 vs night +0.0193), gas and copper are flat, **none clears its rotation null** — while
the reference roots reproduce D515 exactly (NQ day **+0.0275**, GC and CL inside). Closes the MACD
construction on those day sessions, not the roots.

**Stage 0 #3 — the curve story, [D526](../decisions/D526-the-curve-story-fails-stage-0-the-level-is-a-regime-and-the.md).**
Persistence passes, collinearity passes (**pearson +0.498 but spearman +0.162** — not momentum), and
then **the test turns out to be invalid: 0 of 8 CL years contain both curve states.** The tercile is
a period, not a state. **This is the third conditioner to fail this way (D508, D512, D526) and it is
now FINDINGS §73**: on a daily clock with an eight-year window, **a conditioner slower than about a
month has n_eff in YEARS** — count the years containing both extreme states before designing
anything. The repair (the CHANGE) has real within-period variation, 8 of 8 years, and carries
nothing: year gaps −0.038 and −0.005, positive in 3 of 8.

**Kept:** the settlement strip (`data/d526_curve_strip_CL_GC.csv.gz`, 263,983 settlements, CL 188
contracts) — the first curve data in the repo. **And a second missing-value sentinel: settlements of
exactly `0.0`, 646 of them, which `UNDEF` filtering does not catch and which must NOT be swept up by
a "drop non-positive" rule, because CL settled −37.63 on 2020-04-20.**

**Still on the table, not yet told:** the queue rent on ZN (its premise was dented — 9.0%, not
cost-dead — but its day edge is the second-largest of eight and its failure is purely execution);
and a day-session signal other than the MACD on the three newly-expressible roots.

---

## D524 — day5m VERIFIES CLEAN, AND A FLAT ID DICT IS **NON-REPRODUCIBLY** WRONG, 2026-09-13

The last builder to get the D520/D521 rebuild-and-diff treatment. `build_fut_day5m.py` already
imported the windowed `ids_of`, so there was nothing to port — only to verify. **The fixture is
correct;** the finding is about the defect it avoids.

**Two routes, both clean.** `--build` re-run into a temp path (a concurrent session was active, so
the committed parquet was never opened for writing): **byte-identical**, 10,384,830 rows, sha256
`aa2eb147…` both ways, 1.0 min. And because `--build` reads a **cached decode** — the id mapping is
applied in `--decode`, 88 min — that alone says nothing about the mapping, so the 5-minute bars were
folded into hours and compared with `fut_breadth_hourly`, a separate decode pass: **906,905
root-session-hours, 0 differences in o/h/l/c/v AND trade count, 0 orphan hours either way.**

**THE FLAT DICT IS NOT DETERMINISTIC.** `store.metadata.mappings` iterates in a different order in
every process (string hash randomisation), so "the last write wins" picks a different winner each
run. On the 2019 file, **all 8 ambiguous ids get a different surviving label depending on the
process** (8 observed of 8 over six hash seeds, 0 appearing stable against 0.25 expected by chance) —
id 73454 reads the Nikkei `NKDU0` five times and then **silver `SIF9`** on the sixth, so a five-read
probe would have called it stable. Count it with enough draws: an unstable id looks stable with
probability 2^-(n-1), so a three-seed probe reported "5 of 8" once and "6 of 8" next time with a
different set of ids. The *count* of
mislabelled windows is stable; the *identities* are not. **So two flat-dict builds of the same code
over the same archive produce different fixtures, and a flat-built fixture cannot be reproduced or
audited after the fact.** D521's twelve bad CL sessions might have been a different twelve on a
re-run — distrust any pre-D520 flat-built artefact beyond the rows a diff happened to catch.

**The 36-root list is where the mapping actually bites:** **29** mislabelled outright windows and
**14,139** foreign windows, against **0 and 712** for the four index roots — because it contains CL
(the decade-slot reuse) and the FX complex. Named: `CLN9`↔`CLN29`, and cross-root ones like
`NKDU0`↔`SIF9` (Nikkei/silver) and `6BU5`↔`6AQ0` (sterling/Aussie).

**Every futures builder has now been rebuilt and diffed.** Open item, deliberately not done: the
88-minute decode was not re-run, so day5m's cache is verified by agreement with breadth rather than
by regeneration. If the cache is ever deleted, that decode is the stronger check — diff it.

Recompute: `scripts/d524_day5m_verification.py --rebuild-diff --aggregate --precheck --determinism --name`
→ `data/d524_day5m_verification.json`.

---

## D522 — THE RTY G4 FAILURE WAS ONE HALTED OPEN; ALL FOUR INDEX ROOTS NOW PASS EVERY GATE, 2026-09-13

**2020-03-16 alone carried it.** Dropping that one session takes RTY's open-to-close correlation with
IWM from **0.989854 to 0.999339**. Both fixtures are right about the day: all four roots printed
**once at 09:30 and nothing until 09:45** (376 bars, exactly minutes 09:31–09:44 missing; RTY's print
is 115 lots at a single price, the limit), while the ETFs' 09:30 fifteen-minute bars barely traded —
QQQ at **0.4%** of its median opening volume, SPY 26%, IWM 37%, DIA 48%. **The gate was comparing a
limit-locked futures print against a cleared equity price.** The independent hourly builder returns
the identical −9.897%, so the futures side is not the problem.

**G4 amended:** it now gates on sessions whose minute bars are **contiguous over 09:30–09:44** — the
span of the ETF 09:30 bar the open leg is measured against, so not a free parameter — decided from
the futures bars alone, never from the disagreement it judges. It excludes **3 sessions on ES/NQ/YM**
(2020-03-09, 03-12, 03-16, the Level-1 circuit-breaker days) and **5 on RTY**. `corr_open_to_close`
keeps its old meaning and value and is still written, now **reported rather than gated**; the gated
figure is `corr_open_to_close_continuous_open` (ES 0.9997, NQ 0.9991, YM 0.9995, **RTY 0.9996**), and
the gate fails outright if more than 10 sessions are ever excluded.

**`fut_RTY_rth_1m.csv.gz` is now committed** — all gates pass on all four roots for the first time.

**FOR ANY STUDY: drop 2020-03-09, 2020-03-12 and 2020-03-16 if you read the 09:30 open of an index
future, or read the open at 09:45 on those sessions.** The prints are real and are not tradeable
opens. The usable start is still **2016-01-04** for ES/NQ/YM (G5) and 2017-07-10 for RTY.

The threshold was **not** lowered and the statistic was **not** made robust: a rank correlation would
have passed too, and would also have hidden a handful of badly-wrong days, which is the exact
signature the D520/D521 id defect produces.

---

## D515 — WHY THE ARM WORKS ON ONE ROOT: THE LARGEST DAY EDGE **AND** THE CHEAPEST COST, 2026-09-13

The principal asked whether the signal is real everywhere and just slower on the failing roots. Spec
`78fb1f3`, result `1bfaf85`. A **signal** measurement — no cost, no flatten, no day-session
constraint — so "is it real" is answered apart from "can this book trade it".

**The ladder has the predicted shape and does not clear.** ES, NQ, YM, ZN and ZB peak at **H = 5**,
inside the ~7-segment window, and turn **negative by H = 21**; **GC and CL peak at H = 13** and stay
positive to H = 34. But over 64 cells the rotation gives p95 **+0.0444** against an observed maximum
of **+0.0416**, so **zero cells clear the family bar** (17 of 64 clear their own). The primary is
+0.0099 against its own p95 of +0.0144.

**The decomposition is the useful part: split the one-bar edge into the day segments the arm trades
and the overnight segments it never does.**

| | day | night |
|---|---:|---:|
| NQ | **+0.0275** | −0.0008 |
| ZN | **+0.0225** | −0.0096 |
| YM | **−0.0004** | **+0.0078** |

**The Dow is not slow, it is trading the wrong hours** — its day edge is zero and what it has is
overnight, which P2 forbids holding. D514 exonerated the exit; this exonerates the horizon and names
the cause. **ZN has the second-largest day edge of the eight, larger than the S&P, and still loses
$12.83 a trade** — the cost-dead diagnosis shown at the signal level.

**Why NQ, in one sentence: the largest day-session edge of the eight AND the cheapest cost relative
to its move (3.2% against 6.3% for the next best).** Both at once. ZN has the edge and a $18.62
crossing; YM has the cost and no day edge.

**Two flags.** NQ's edge does not merely decay past the session, it **inverts** (−0.024 at H = 21),
the same overnight reversal that closed the hourly clock. And **CL's row is PROVISIONAL**: an existing
note records that the D467 fixture pools expiries on CL and calls its gross Sharpe suspect; this reads
the **breadth** fixture and **nobody has checked whether it shares the defect.** Worth checking before
the crude half of the slow-signal story is used.

## D514 — THE HOLD IS NOT WHAT IS WRONG WITH THE DOW, AND THE WINDOW IS THE CEILING, 2026-09-13

Asked by the principal after D513's addendum split the transplant roots into **cost-dead** (ZN, ZB,
GC: a real gross edge killed by the tick) and **signal-dead** (YM, CL, 6E: gross itself negative):
does the Dow's gross turn positive without the five-hour minimum hold? Spec `85c4cc5`, result
`61e0f1d`.

**No, and it goes the other way.** YM's gross per session by minimum hold: **−1.837** at M ≤ 1,
−1.868, −1.518, −0.814, **−0.412** at the frozen M = 5. The primary is −$1.837 against its own
rotation p95 of +3.509 and an 18-cell family p95 of +5.016. **NEGATIVE**; the exit is exonerated and
D513's reading stands.

**A longer hold gives better gross on three roots of four** — NQ +10.13 → +13.02, YM −1.84 → −0.41,
6E −1.75 → −1.13, with CL the exception. **NQ's ladder is monotone across all six values and the
frozen M = 5 is the best of them, still rising where the window stops it.**

**Why nothing moved: the exit has no room, exactly as D491 predicted.** Removing the hold entirely
shifts trips only 1.03 → 1.13 a session and the mean hold 4.78 → 3.83 segments. **The hold is not the
binding constraint on this construction; the window is**, and the only way past six decision points
is to hold overnight, which P2's flatten forbids. **That is a venue constraint, not a signal one.**

Nothing about the admitted arm is re-specified (NQ was a reference row, not a declared cell) and no
2024+ slice was read.

## THE CONDITIONER LINE IS CLOSED AND ITS FORWARD POINTER IS ANSWERED — D513, 2026-09-13

**The principal closed the conditioner line on the admitted arm** after D508, D509 and D512
(BOOK_PROP has the closure) **and directed that the range-expansion conditioner be carried to a root
with an unread slice.** That is D513: spec `ed2e691`, result `9d38c1c`, declared in advance on
**YM, ZN, ZB, GC, CL and 6E**, whose 2024+ is unread.

**It does not transfer. D512's effect was NQ's history.** Δ/σ reads +0.036, −0.077, −0.091, +0.062,
−0.088, +0.068 — **positive on three of six**, a coin flip. The declared primary (YM) sits at the
**68.2nd percentile** of its own exact rotation; the six-root family p95 is **+0.173** against an
observed maximum of **+0.068**, beaten by **65.8%** of offsets. Within year the primary keeps its
sign in exactly four of eight years, and D512's coherence on NQ appears nowhere.

**A second finding, sharper than D506 could state: the arm does not merely fail to transplant, it
LOSES on every one of these roots** — net Sharpe −0.456 to −1.294, −$2.16 to −$28.98 a trade. On the
three roots where Δ is negative the *expanded*-range sessions lose more (ZN −$25.51 against −$8.40,
ZB −$70.01 against −$21.82, CL −$11.18 against −$2.70); on the other three the ordering reverses.

**The limitation to carry:** this tests a conditioner on a construction that bleeds everywhere, which
cannot rule out that a range conditioner works on a *live* construction elsewhere. Anyone reviving it
needs an edge to condition.

**NOTHING WAS SPENT.** The 2024+ slice of all six roots is still unread, under a verdict that never
called for it. That is what declaring the cell off NQ bought.

## D512 — RANGE EXPANSION: CLOSE, BUT THE CLOSEST A CONDITIONER HAS COME TO THIS ARM, 2026-09-13

The principal's construction: `log(EMA50(range) / SMA200(range))` on daily bars. Spec `711bbe3`,
result `bee99d7`. Scored with D509's economic primary so the three studies on this arm compare
directly.

**CLOSE on the declared primary** (day-session log range): Δ **+$25.37 a session** against a rotation
p95 of **+$27.54**, the 93.4th percentile, missing by $2.17. The **23-hour** version, declared
secondary, reads **+$31.27 at the 98.6th percentile and clears its own N1** — taking it now would be
selection, and the family bar refuses the set at **6.0%** (p95 +32.92 against an observed max of
+31.27). **A refusal, and a narrow one: 6% against 40% and 58% for the two stretch records.**

**Three things make it different in kind from the 200-day stretch.** It is **not a year proxy** —
positive in 6 of 8 years, within-year mean **+$27.42** slightly exceeding the pooled +$25.37, where
the stretch reversed sign. Its shape is a **threshold, not a ranking**: net $/session by quintile runs
−9.00, +0.50, +16.01, +17.28, +16.36, so the top three are flat and the work is at the bottom. And
**the bottom quintile loses gross** (−$5.27 a trade, net Sharpe −1.08), so a compressed range hurts
this arm before costs, not through them.

**Where to carry it:** not to this arm, which has no unread slice on NQ. To a construction or root
that still has one, where a 23-hour cell could be **declared** rather than promoted after the fact.

**A method note.** I refused the principal's literal point-range version as primary, expecting a
price-level contamination. The selftest proves that mechanism is real (a constant percentage range on
a rising market gives the point version +0.088 while the log version stays at 6e-15) but **in this
data ρ(V, log price) is +0.01 to +0.02, and the two versions differ by $3.83 on Δ, well inside the
null.** The construction as written was fine. **Demonstrate a suspected contamination on the data
before redesigning around it.**

## D509 — THE SAME QUESTION ON AN ECONOMIC PRIMARY, SAME ANSWER, 2026-09-13

The principal asked why D508 used a Spearman, then directed a re-score on the statistic I said would
have been better: **top-minus-bottom quintile in net dollars per session.** Spec `4a138f4`, result
`fd22b7b`. **Provenance is on the record: the primary was chosen after seeing D508**, so no outcome
could have been a discovery, and the arm has no unread slice on NQ in any case.

**CLOSE, on all four terms.** Δ = **+$13.82 a session** (top +20.45, bottom +6.63) against an exact
rotation with **p05 −27.18, p50 +0.13, p95 +26.45** — the 76.9th percentile. **The decisive number is
the null's width:** rotating the conditioner leaves it a persistent gate of identical duty cycle and
identical run lengths and merely starts it elsewhere, and that alone swings the quintile difference
±$27 a session. Family p95 +$33.00 against an observed max of +$13.82, beaten by 40.1% of offsets.
Within-year Δ is **negative in seven years of eight, mean −$10.71**, with 2022 alone at +$47.00.

**The methodological result is the keeper: an exact rotation of a quintile-difference statistic
SUBSUMES a hand-built run-length-matched gate**, and the runner proves it (duty 20.0% → 20.0%, 38
runs → 38, run-length multiset identical). D508 needed the hand-built band because its primary was a
correlation; this one gets the control for free, and the two agree to within a percentile.
**Prefer a statistic whose own null contains its control.**

**Two defects in our own instruments, fixed and disclosed:** `spearman` in D508 divides the
covariance by n and the standard deviations by n−1, so it is short by (n−1)/n — 0.05% at n = 1,876,
so **no D508 number moves**, but 20% at five points; and its n ≥ 30 guard silently returned NaN for
the five-row monotonicity check. `rank_corr_small` in D509 fixes both and asserts the difference.

## D508 — THE 200-DAY STRETCH RANKS YEARS, NOT SESSIONS, 2026-09-13

Asked by the principal: can `|log(P/SMA200)|` or `|log(P/EMA200)|` rank the admitted MACD arm's
performance? (The **absolute** value: distance from the average, not side. D502 had already tested
the signed binary gate and found a gate whose mirror beat it.) Spec `c47feae`, result `e4dcaed`.

**The runner imports the frozen arm and reproduces D504's published per-year figures exactly**
(1,876 sessions, $15,423), so the admitted construction is what was ranked, not a copy.

**CLOSE.** Primary Spearman **+0.0089**, the 43rd percentile of its own exact rotation; the four-cell
family p95 is +0.0505 against an observed maximum of +0.0089, beaten by 58% of offsets. The signed
versions are **−0.034** and sit at the 13th percentile of the lower tail, so they fail two-sided too.

**The quintile table looks strong and two controls dispose of it.** The top quintile earns +$20.45
net a session against +$3.54 to +$6.92 elsewhere, net Sharpe +1.36. But **a random persistent gate
matched on duty cycle AND run-length distribution has p50 +0.797 at 20% duty, and 23.9% of those
gates beat the observed +1.364.** And **within a year the relationship is negative in seven years of
eight (mean −0.042) against a pooled +0.009** — the stretch ranks which year it is, and once the year
is held fixed it ranks the wrong way.

**Two method lessons worth more than the result.** A conditioner that ranks a regime-concentrated arm
pooled can rank it **backwards** within each regime, so **stratify by year before believing any
conditioner on this arm**. And **a matched-random band must be recomputed at the duty cycle in use**:
D502's ≈ +0.2 was measured at 82% duty, and at 20% duty the same construction gives +0.797 — quoting
the old figure would have passed this cell.

**Nothing spent**: `simulate` is row-independent (asserted), so sessions were clipped before
simulating and the arm's 2024+ slice was never scored.

## THE IN-PLAY CONSTRUCTION CLOSED, THE ACTIVITY FILTER KEPT — the principal, 2026-09-13

**Closed:** conditioning a day-session signal on how active the overnight session was, as a way of
choosing *when* to trade. **Kept:** the filter itself, as an instrument of the survival layer, now a
standing module — **`scripts/activity_filter.py`** (`--selftest`, six checks), causal and
root-agnostic, with both indications and D506's measured properties in its docstring.

**The one indication: reach for it when a construction fails P3a and nothing else.** It cuts the
breach rate three to five fold (ZB 14.00 → 2.71 a year, ZN 2.00 → 0.71, the NQ day drift 0.57 → 0.00)
because both prop death mechanisms are counted in exposure-days. **Never use it to choose direction**
— that is exactly what D506 closed. Recorded in R11's P3 amendment, BOOK_PROP's closure section and
the ledger.

**The arm admitted today does not need it**: the MACD day-session arm reads P3a 0.50 a year against a
bar of 1.0 and P3b 10.0% against 33%. The filter is for what comes next, and for the day a live arm's
breach rate drifts.

## D506 — STAGE 1, CLOSE: IN-PLAY SELECTION FAILS AS ALPHA AND WORKS AS DRAWDOWN MANAGEMENT, 2026-09-13

From the in-play video (`docs/youtube-lessons.md` §6) and the design in
`working/DRAFT-in-play-on-the-prop-book.md`. Spec `2bea9d9`, result `45c2c85`. Conditioner: the
causal overnight range-and-volume score, top decile against the rest; two signals the repo already
owns (the day drift, and D484's log MACD at d−1); eight roots; 2016–2023; 2024+ not read.

**The fee lever is exactly what the premise promised and it is swallowed.** Across 16 cells the fee
term is **+0.85 points, positive in 16 of 16**; directional accuracy is **−2.09 points, negative in
11 of 16**. Primary YM-MACD: in play **−$10.61 gross a trade and net Sharpe −1.32** against +$2.10
on the rest; Δ −0.0504 with 73% of its exact offsets above it; the 16-cell family p95 is +0.2192
against an observed maximum of +0.0620, so **97.8% of offsets beat the best real cell.** CLOSE.

**The decisive figure is the untradeable bound: −0.0018.** Conditioning on the day's *realised*
range, which nobody can do in advance, earns nothing either — so the whole family is disposed of,
not just its causal version. Mechanism, and it now has three confirmations (FINDINGS §70, §71, §72):
**by 09:30 the information is spent, and a night that moved a lot has spent more of it.**

**Two things kept, both in FINDINGS §72.** Selectivity **cuts P3a three to five fold** (ZB 14.00 →
2.71 a year, ZN 2.00 → 0.71, NQ drift 0.57 → 0.00) because both prop death mechanisms are counted in
exposure-days — it belongs in the sizing and survival layer, not the signal layer, and is worth
reaching for when a construction fails P3a and nothing else. And **§69's accuracy targets are
corrected**: they assume symmetric payoffs, and the long drift clears 55.7 / 55.2 / 54.4% on ES / NQ
/ YM with net Sharpes of +0.02 / +0.11 / −0.31, because `(2p−1)·E|M|` overstates the realised edge by
2× to 13× on these roots. Quote the payoff ratio beside any accuracy target.

**Stage 2 (root selection) was NOT run** — the design made it conditional on stage 1, and stage 1
says the state predicts worse direction. Nothing spent.

## TWO CLOSURES BY THE PRINCIPAL, 2026-09-13 — K8 AND THE CROSS-MARKET-INTO-THE-OPEN LINE

**K8 (ledger entry #1) is CLOSED.** D503's forward read had it at gross −$4.46 a trade against
+$17.87 in sample and net Sharpe −0.160; D498's rule said PROVISIONAL and the principal closed it on
the negative gross mean. **The prop ledger holds no live entry.** The 2024-01-02 → 2026-09-09 futures
slice is SPENT for K8, the MACD component and the assembled book.

**The cross-market-into-the-open line is CLOSED** (D494 index-level, D504 cross-sectional): any
construction that reads a foreign market before the US open and enters at or after that open. Kept as
measurements in FINDINGS §71 — the channel clears in the gap, so it could only be traded IN the gap
(pre-market execution, a different cost model); and the MNQ/MES pair's daily σ is $128 against one
MNQ's $282, the only construction that lowers dollar σ without leaving the micro.

**Where the prop book actually stands:** no live component; the binding constraint is the VEHICLE,
not the signal (one micro is too big for a $50k account's $2,000 floor at 2026 index levels, D503);
and four unrelated routes to intraday direction have each ended at about one tick (D487, D494, D499,
D504). The unexplored answers are the hedged micro pair (sizing unstudied) and a larger account or a
wider floor.

## D504 — STAGE 0, CLOSE: THE ASIAN CHIP CHANNEL IS REAL AND CLEARS ENTIRELY IN THE GAP, 2026-09-13

The principal's direction after D499: make the Asia-into-US question **cross-sectional** (semis
against Asian tech). Spec `7578140`, amended `0cf06db` **before the run** (the pre-registered
z-difference failed the known-answer selftest and was replaced by a causal residual; the
z-difference, kept as `P1_z`, indeed came out at −11.6 bp on real data). Conditioner = the EWT+EWY
overnight gap relative to QQQ, measured to the close of bar 0 (09:30–09:45); entry at bar 1's open
(09:45), so the predictor is strictly before the entry — that timing is why the 15-minute ETF
fixture is used and not the daily one.

**The finding, and it is clean: the channel is real, semis-specific, and fully priced in the gap.**
A one-sigma Asian chip move is **+25.65 bp (t +4.25) into the semis' relative opening gap and
−1.65 ± 2.6 bp into the day session**. The traded primary is +8.0 bp on 82 trades against 11.7 bp
crossed, z +0.96 inside its own exact rotation (p95 +1.63), with yearly means +5 / −27 / +39 / −5.
**The family maximum is a CONTROL** — transports against QQQ at +27.97 bp, hit 61%, clearing its own
null at the 0.8th percentile with no mechanism at all; banks and homebuilders also beat semis;
nothing clears the eleven-cell family p95 of +2.56. Every control behaves (Europe/Brazil/emerging
all negative and inside; the wrong-window cell −17.3; the partner-randomised spread is ±20 bp and
QQQ's +8.0 sits mid-pack). **Verdict CLOSE** (the principal closes).

**Two things kept as measurements (FINDINGS §71).** The gap-versus-day decomposition above, which is
why the ADR-style "closed market" mechanism does not pay at a tradeable horizon. And, from the prop
arm, a **vehicle** measurement that matters after D503: the unconditional MNQ/MES day-session pair
has a daily σ of **$128 against one MNQ's $282** ($135 vs $273 in 2023), zero days beyond −$1,000 in
six years. **A hedged micro pair is the only construction that lowers the dollar σ without leaving
the micro**, which is the one unexplored answer to the floor problem D503 exposed. Dollar beta of NQ
on ES is 1.72, so 1:1 under-hedges and 1:2 over-hedges at $9 — sizing it is its own record, not
started.

**Spent: nothing.** 2024+ on the 15-minute fixtures is unread by this line. Note the futures 2024+
day session is spent by D503, so the prop arm could never have had a forward read.

## D499 — THE HOURLY CLOCK CLOSED BY THE PRINCIPAL, 2026-09-13: THE HOUR AFTER A LARGE MOVE IS WORTH A TICK ON EIGHT ROOTS

The principal's direction for the second component: a 24-hour future, a construction that prefers
the off-hours. Stage 0 (`467500f`, RESULT) on D467's hourly tables, eight roots, 2016–2023: fade
the next hour after a top-decile hourly move (causal, per hour-of-day), thin vs thick hours by
volume, k = 1 primary, exact common rotation per root, 16-cell family maximum. **Best gross cell
+$2.46 a trade (NQ thick) against $3; 15 of 16 component lines negative; family p95 +2.70, observed
max +1.84 (CL thin, 43% of offsets). CLOSE by the pre-registered rule.** What is real: the
next-hour reversal on the US-clock off-hours of ES/NQ/YM (pooled β −0.03 to −0.04, outside exact
rotation bands; the `us_off` fade clears N1 on ES and NQ) at **1.7–4.9 ticks a trade, net negative
after the fee**; crude continues in the same hours. The volume-thin hours (London h03/h04/h07/h08
are *thick*) show nothing, and low-relative-volume moves revert *less* — the transitory-impact
mechanism is backwards here. **The arithmetic closes the clock before any signal: fee A is 14.5% /
7.1% of the expected hourly move on MNQ (thin / thick; break-even 57.2% / 53.5%), 21% / 11% on MES,
19–60% on ZN/ZB with the tick.** Nothing spent; 2024+ unread on every root. **Next for a
24-hour-market component: a session-long hold on a *state*, on a non-index root** — the
daily-state family (D495/D498's clock) on CL/GC/6E/ZN is unscored and outside the overnight
closure (which names only the index leg). Not started; the principal's direction.

**CLOSED BY THE PRINCIPAL, 2026-09-13:** any hourly-horizon construction on the eight gated roots
at micro cost. Recorded in `docs/BOOK_PROP.md` (closure section), the ledger, FINDINGS §70. The
US-off-hours reversal stays as a measurement, not a trade. **Open and not started:** a session-long
hold on a non-index root gated on a daily state (fee 4–7% of the move, not 14%).

## D498 — K8 IS THE LEDGER'S FIRST ENTRY (PROVISIONAL): LONG THE NQ DAY SESSION AFTER A DOWN DAY, NET SHARPE +0.61 AT ONE MICRO, 2026-09-12

Declared as a component candidate from D495's other side (selection stated), with three
second-clock cells beside it (`b463999`, RESULT). **NQ K8: 871 trades (44% of sessions, about
twice a week), gross +$17.87 a trade (+11.6 bp, SE 4.0; median +$20.50), hit 57%, skew −0.02,
positive in 6 of 8 years and both sub-periods; after an up day the day session is −3.1 bp, so
the difference is z +2.89 against a family p95 of +2.41 (1.5% of common rotations); net Sharpe
+0.61 (0.32); C-a, C-c, C-d pass → PROVISIONAL entry #1 in `docs/COMPONENTS_PROP.md`.** ES is the
same sign at half the size (+4.9 bp, +0.18, inside its null; ρ ≈ 0.85 with NQ). The second clocks
are flat: turn-of-month +6.9 bp vs +3.7 other side (z +0.46), pre-FOMC to 14:00 +2.8 bp (z +0.06),
the first-30 fade +0.4 bp. **Promotion is the declared forward read** (`--forward
--principals-word`: 2024-01-02 → 2026-09-09, ≈ 300 trades; FULL if gross > 0, net Sharpe > 0 and
the difference vs after-up days has z ≥ 1; REMOVED if net Sharpe < −0.3 or the difference is
negative) — **unrun; the principal's word.** A second component needs a different instrument or
state; every session window and overnight construction on the eight roots is already scored.

**PARKED by the principal, 2026-09-12: the forward read is HELD, not run.** The 2024+ day session
is the only unseen slice the prop line has, and the ledger confirms the assembled book on that
same slice; a K8-only read would make the book's confirmation a re-read for K8. The read waits
for a second component, then K8's promotion, the second component's promotion and hurdle P on
the assembled book are read in ONE pass on 2024+. Do not sharpen, filter or re-score K8
in-sample meanwhile. Noted in `docs/BOOK_PROP.md` (last section) and under the ledger table.

## D495 — THE DAY SESSION AFTER A BIG DOWN DAY ON NQ PAYS ITS COST AND IS A PICK; MOST OF IT IS THE DRIFT AFTER ANY DOWN DAY, 2026-09-12

Stage 0 (`6d551b9`, RESULT), intraday only (09:30 open + tick → 15:59 close, one micro, $3):
cell A fades the next day session after a top-decile (causal) day-session move; cell B trades it
after a daily RSI(2) extreme; ES and NQ; family of eight; the family null is the max of a
difference-between-sides z under a common rotation (D472's lesson). **NQ cell A long: +$42.61
gross a trade on 110 trades (+21.9 bp, SE 14.5), hit 56%, sign in 6 of 8 years and both
sub-periods, net Sharpe +0.47 (0.25), clears its own rotation null — a PICK.** It fails the
family bar (z +0.78 vs p95 +2.45) because the **other side — long NQ's day session after ANY down
day — is +10.2 bp on 761 days**: most of the pick is that drift, not a big-day effect. Cell A's
short side (+0.21) and both RSI(2) cells are closed (the RSI(2) longs are the unconditional
drift; the shorts lose). **Post hoc observation, not scored:** "long the NQ day session after a
down day" would trade 38% of sessions at ≈ $20 gross, net Sharpe in the region of 0.5; it is the
natural single declared cell for a next record, with 2024+ still clean. The cost is not the
problem in this family for the first time; the sample is.

## D490 — THE PRINCIPAL'S RANGE-REVERSION RULE LOSES GROSS ON BOTH SIDES; A STALE RANGE BEATS YESTERDAY'S, 2026-09-12

Buy the bottom 5% of yesterday's RTH range on a 2× same-minute volume spike, target the top 5%,
trail from the last confirmed swing once past the midpoint, else the close; short symmetric; one
micro, $3 + fills. Three-way split declared (`738ddfa`): **development 2016-02→2020, validation
2021→2023 (touched once per declared filter set), final 2024+ (principal's word)**. Development
RESULT: ES pooled gross **−$3.48/trade**, net Sharpe **−1.14 (0.38)**; NQ −$4.96, −1.03; long hit
57.6% with median +$10 and mean −$2.70 (skew −1.5, worst MAE −$538); shorts 45% hit; the target is
reached on 5% of trades, 78% ride to the close. **The wrong-range control (a range 3–22 sessions
old, same mechanics) has a mean of ≈ 0 — the rule is BELOW it**; random entries with the same
exits are worse still (−$7.55). Three fifths of the longs are below yesterday's low on a spike: a
breakdown with flow, not a stretched tape; 2018 (D487's continuation year) is the worst year. No
split is beyond ~1.3 SE of zero (short on a > 3× spike +3.8 ± 7.2 is the best-looking). Bar not
cleared; **not taken to validation; both reserves intact.** If the principal wants a filter, the
splits are on the record; my reading is noise around a negative mean.
**D492 (`b512918` + addendum `fff18b9`, RESULT): the first declared filter set — an HOURLY RSI(14)
confirmation (the principal moved it up from five-minute before the run; holds run for hours).**
It removes 74–77% of the trades and leaves the rest at zero: ES cell A −$0.88 / Sharpe −0.30 on
287 trades, cell B −1.94 / −0.40; NQ +$1.57 / −0.11 and +$4.49 / +0.12 — **below the wrong-range
control on both roots** (a stale range does as well); the target is reached on 0–3% of trades;
92 ES long trades (SE ≈ $16) leave nothing to filter further. No cell cleared; the runner refused
the validation read; both reserves intact. The family has failed twice for the same reason: a
print at yesterday's extreme is not where the intraday reversion lives.

## D487 — THE ORB LINE CLOSED AT STAGE 0: CONTINUATION LIVES IN 2018 AND 2022, NOT IN THE CRASH YEAR, 2026-09-12

The principal asked about opening-range breakouts; the literature says an ORB is a wrapper on
intraday continuation (hedging demand, delayed rebalancing; late in the day; regime-dependent;
flat in the 0DTE era). The other session had already measured the pooled premise on ES (their
D471/D473: variance ratio 0.82–1.02; D474: an unresolved volatility gradient; D475: no transfer).
D487 (`554d916`, RESULT) added the by-year split with a null that destroys both lag-structured
and day-common dependence (the spec's within-day permutation is blind to a trend day — proved in
the self-test and amended before the numbers). **CLOSE by the declared rule:** ES clears the
calm-year pooled null on neither the variance ratio nor the trend-day share; one calm year of five
clears on each. **Continuation is 2018 and 2022** (VR 1.32 / 1.23 on ES, the same two on NQ);
**2020 is the most mean-reverting year** (0.88); the **quiet-vol tercile trends most** (1.18);
rest-of-day → last-30 is +3.1 SE in the calm years and is 2018 alone; **the first half-hour
reverses into the last** (ES −0.10, −4.3 SE, 2020–2022); **the next-day reversal after
top-decile days is −24.5 bp on NQ** (2.2 SE, outside its rotation null, calm and stress alike).
2024+ day session still unread. Both sessions now converge on intraday continuation; the
first-30 → last-30 reversal and the quiet-tercile trending are measured, unconstructed facts for
whoever takes that lane. Note: both sessions have a D473 on master (theirs cost-structure, mine
K7) — a clash recorded, not resolved.

## THE OVERNIGHT LINE IS CLOSED FOR THE PROP BOOK (PRINCIPAL, 2026-09-12); OPEN FOR THE PERSONAL BOOK

After D466–D473 and the literature read (NY Fed: the index overnight drift was compensation for
closing order imbalances at 2–3 a.m. ET and has been ~zero since 2021 because the imbalances
compressed), the principal closed **any gate, window or size on the index overnight leg at micro
cost** for the prop book. The unconditional drift is real (strong even in 2024–2026, both sides)
and unaffordable at $3 a micro round trip; it is the personal book's at full size if taken there
(BOOK_PROP closure section). **Next for the prop book, in the order recommended:** (1) the
account-size lever through D440's lifecycle — which plan and contract size makes a gross-positive
session hold carryable (the cost is per contract, the floor is per account; 2016–2023, no new
data); (2) declared calendar/event constructions on the DAY session (turn-of-month, FOMC 14:00
day, release days) with calendar-matched controls — one stage 0, cells named first, 2024+ on the
day leg still clean; (3) the closing-imbalance observable measured directly from the last minutes
of the day session as a dormant-channel monitor, not a strategy.

## THE PROP TRACK IS NOW A COMPONENTS SEARCH — D466 / D467 / D468, 2026-09-12

**The principal's correction, and the rule it produced.** Three prop records (C1, D463, D464) were
written "closed / not a candidate" on standalone hurdle-P bars without a component line. The book
is built by **layering components with net Sharpe > 0.5 and pairwise ρ < 0.3** to reach the
account's book-level 1.5–2, never by one strategy; CLAUDE.md now carries the two-altitude rule
(*score BOTH, every time*), `docs/COMPONENTS_PROP.md` is the append-only ledger with the
pre-registered standard (C-a net Sharpe > 0.5 at **minimum tradable size and the cost that size
pays**, C-b ρ < 0.3 with every prior entry, C-c skew ≥ −0.5, C-d σ ≤ 1% of $50k, C-e provenance;
PROVISIONAL entries below a family-maximum null's p95), and **only the assembled book is tested
against hurdle P and confirmed on the unread 2024+ slice.**

**The ledger is empty after 30 constructions.** The figures that opened it (C1 0.62, NQ last-30
0.42, book 0.91) were shell-line numbers at full-size cost in basis points; under the standard
(dollars, one micro, $3 ≈ 2 bp of notional) they are **+0.37 and −0.01** (D466, `e5ad3bc`). D467
(`59a151d`, RESULT + fixtures) built **hourly session tables for ES, NQ, YM, ZN, ZB, GC, CL, 6E**
(`data/fixtures/fut_sessions_hourly.csv.gz`, 18:00→16:59, front by volume, roll nights flagged,
five gates, usable from 2016-01-04 on all eight after two gate amendments — holiday sessions have
no 16:00 print, and the pre-2016 index/crude sessions are partial). D468 (`cff45f2`, RESULT)
scored **24 windows** (full session, overnight leg, day leg × 8 roots, long only): **best ES-W1
+0.39 (SE 0.32) at the 78th percentile of the common-sign family-max null (p50 +0.55, p95 +0.95)**;
the overnight index drift is gross +0.54..+0.64 on ES/NQ/YM and the $3 micro round trip takes
30–70% of it; treasuries, gold, crude, euro carry no session drift (gross within ±0.3); W2 ⊥ W3
(ρ 0.00..−0.05); the three index roots are one construction (ρ 0.91).

**D470 stage 0 (`b3671b2`, RESULT): can a state at the entry concentrate the drift?** Four
declared gates on ES/NQ, both windows, D464's two gate nulls and a family-max null. **The
principal's continuation and above-average conditions come out with the sign reversed:** the
drift follows DOWN sessions and DOWN overnight legs on 8 of 8 cells; the cleanest cell (the
overnight leg after a negative overnight leg) is +$10.66 vs −$1.37 on ES (2.5 SE), +$13.32 vs
−$1.57 on NQ (2.1 SE), gated net Sharpe +0.70 / +0.62 at micro cost, clears the rotation and
run-length nulls on both roots — **and fails the family-max p95 on both, because its size lives
in 2020–2022** (2016–2019: the two sides are equal). A pick, not a component; an in-sample
stage 1 would re-report it; the unread 2024+ slice (~190 gated nights, SE ≈ $7.8 vs +$10.7
expected) is the only test and is underpowered — **the principal's call whether to spend it.**

**D472 (`4290eeb`, RESULT): the pick tested on what the family null had not priced.** On a
standardised scale the in-sample family bar still refuses it (z 2.78 vs p95 3.13; gated Sharpe
+0.70 vs p95 +0.79 — the rotation null is centred on the drift, so the best of eight random
45%-gates on a drifting series sits at +0.48 median; eight years cannot beat that). **On SPY and
IWM cash 2010–2015, a period and instrument outside the family, the same construction (the
overnight gap after a negative overnight gap) is +5.5 / +7.7 bp vs ≈ 0 on the other side, 1.9 /
2.0 SE, clears both single-cell nulls, and is on the right side in 11 of 12 symbol-years; over
2010–2023 it is 24 of 28.** The prior-session variant (NQ-W1's big dollar cell) does not
replicate in cash. The declared step-3 criterion fails on the family condition alone; whether the
replication outweighs it is the principal's decision. If yes: one declared component (ES or NQ
overnight leg after a down leg, one micro, $3, in-sample gated net Sharpe +0.70 / +0.62), promotion
on the unread 2024+ futures slice (weak alone, ~190 gated nights) plus the cash 2024+ reserve.
**D473 (`fb69179`, in-sample RESULT): the component record, K7.** The principal took the pick to
a component record on the replication. One declared construction, no in-sample sharpening: long the
NQ overnight leg 18:00→09:00 on nights after a negative overnight leg (prior session's leg ≤ 0),
one MNQ, $3, NQ chosen on cost share; ES the check root; the 09:30 open a declared secondary exit.
In-sample line: **+0.62 (0.25)**, gross +0.80, 887 of 2,009 nights, +$13.32 vs −$1.57 (2.1 SE), N1/N2
cleared, C-a..C-d pass; ES +0.70 (2.5 SE); **the 09:30 exit is worse (−20% mean, +0.45)**; 71% of
the gated P&L follows prior falls > 1% (16% of nights; the dose–response is monotone on ES, not
on NQ — recorded, not used); worst night −$794, none below −2% at one micro; ρ(K7, K1) 0.39.
**Not entered** (the family bar). **The forward read is declared and unrun:**
`uv run python -u scripts/run_d473_downleg_component.py --forward --principals-word` reads NQ/ES
futures 2024-01-02→2026-09-09 and SPY/IWM cash 2024-01-02→2026-08-26 and applies the rule
(PROVISIONAL if diff > 0 on NQ and SPY, pooled z ≥ 1.5, NQ net Sharpe > 0; FULL if also futures
z ≥ 2 or pooled z ≥ 2.5; REMOVED if futures diff < 0, pooled z < 0.5 or Sharpe < −0.3). **It
spends the 2024+ slice for this construction; only the principal runs it.**
**RUN on the principal's word (forward RESULT): K7 REMOVED.** 2024-01→2026-09: NQ after a down
leg +$30.76 vs after an up leg +$21.29 (+0.4 SE; in bp −1.0), ES +0.1 SE; SPY cash gap after a
down gap +0.71 vs +9.22 bp (−1.6 SE), IWM −1.5 SE; pooled z −1.30. The gated nights paid (forward
net Sharpe +0.76 at one MNQ) because the whole overnight drift was strong (≈ +5.6 bp a night on
NQ, both sides); the down-then-up structure did not carry, and on cash it reversed. Every forward
prediction was wrong in the same direction. **Spent: the 2024+ futures slice for the 18:00→09:00
leg on NQ and ES (both sides read, so the ungated leg too) and the cash 2024+ reserve on SPY/IWM
(gap and close-to-close). Unread: 2024+ on W1/W3, every other root, the last-30 constructions,
the single-name and cohort reserves.** The D472 structural claim ("the drift is the post-down
nights") is withdrawn. The process held: rule first, no sharpening, the rule fired.
RTY added to the D467 table (nine roots; eight rebuilt bit-identically) and held back on G2
(a Sunday-session volume flip, 2020-06-14). A difference-between-sides family statistic, centred
on zero, is the right declaration for any future concentration test (noted in D472 §1, not run).

**What stands.** The overnight index drift is real on the futures and **unaffordable at micro
size** (breakeven cost for C-a on ES-W1 is $1.48 a round trip); the plan's 16:10 flat rule forbids
holding across sessions; the only lever inside this family is notional per contract, which the
$50k floor forbids (one ES night σ ≈ $1,840). **Next component families must have gross mean per
round trip large against $3 and their own σ** — anything with more than one round trip a session is
dead on arrival at micro cost. Unread: 2024-01 onward on every futures fixture. Untried: the
RTY/other-root event windows on the hourly grid (FOMC 14:00, CPI 08:30 — declared nowhere yet),
and the TWS quote pull that would pin the cost lines (D336/D441, no TWS listening).

## D464 — THE PERSONAL ARMS AS GATES ON THE SESSION HOLD: BETTER NIGHTS, INSIDE THE NULL, AND LIFE BOUGHT ONLY BY NOT TRADING, 2026-09-12

S1 and S2 (the book's own code on SPY) gating C1's 18:00→16:00 ES hold, 2,043 nights 2016–2023:
S1 on 8.7% of nights at +13.8 ± 10.0 bp, S2 on 10.0% at +9.1 ± 4.7, both with a lower MAE
tail than the average night (321 vs 369 bp) — **and both inside the exact rotation null (p95
+16.7 for a tenth of a 113-bp series).** Hurdle P at whole ES contracts: one contract's
overnight σ is the 4% floor, zero size at f ≤ 0.7%, a fixed contract breaches on 791 nights; at
micros the surviving sizes earn +0.2–2.2%/yr and the gates lengthen life to at most 1.94 years
at +0.8%/yr by removing 90% of the exposure. **Not a candidate; the personal book untouched.**
**Three prop records in one day say the same thing: the binding constraint is the
instrument–account pair** (ES σ per hold vs a $50k floor), not the candidate list. Records: spec
`0391331`, RESULT `docs/decisions/D464-RESULT-…md`; BOOK_PROP updated.

## D462 / D463 — THE PROP TRACK ON THE FUTURES THEMSELVES: THE DATA LAYER, AND THE FIRST CANDIDATE SCREENED ON ES, 2026-09-12

**The archive** (111 GB, `data/raw/databento/`, moved out of `temp/` by the principal) is now a
data layer: **ES, NQ, YM one-minute regular-hours fixtures**, front month by measured volume, no
stitching, five gates (`scripts/build_fut_index_1m.py`), **usable from 2016-01-04** — the archive
carries the index futures' evening bars but not their day session on most days before 2016 (21–42%
of the calendar in 2010–12; a fifth gate had to be added to see it; every earlier ES study's
2010–2015 numbers rest on 20–85% of days). RTY failed the cross-check on the 2020-03-16
limit-down open and is not committed. **Records: D462 (`de75a63`, RESULT `d69b59e`).**

**The candidate** — market intraday momentum, the last 30 minutes, lane 13's only near-miss —
screened on ES 2016–2023 (D463, `dd5801c`): **+1.18 ± 0.86 bp per trade at a 49% hit rate, slope
+1.8 (×100) against the published 6.18, inside the sign null; net +0.07 bp at a $17 round trip.**
**Hurdle P's P3/P4/P5 computed for the first time**, on the measured 30-minute path through
D440's lifecycle model: the C4 rule sizes below one contract at f ≤ 0.4%, and at every size that
trades the worst day breaches 2% on 13–87 days, the funded account lives 0.07–0.48 years, V < 0.
**Not a candidate; closed on this window; the 2024–2026 slice unread.** The durable output is the
arithmetic: a single ES contract's 30-minute σ (~$650) on a $50k account puts the floor 3σ away
per trade, so **no single-contract ES construction at that σ clears P3/P4 on this account size**,
whatever its edge. Records: RESULT `docs/decisions/D463-RESULT-…md`; BOOK_PROP updated.

## D457 — THE 8-K ATLAS WITH RETURNS: NO CELL CLEARS, THE DISTRESS ITEMS REBOUND, THE REACTION IS IN THE GAP, 2026-09-12

17 item cells × all/pure × both sides, cap 10, C1 (state-matched, no 8-K within ±5 bars) and
C2 (exact rotation) on every cell, a family bar with 0.04 cells expected to clear both. **Zero
clear both; four clear C1 (chance 0.85) — 2.02 earnings, 8.01, 5.07, 3.01 — all LONG.** The
common finding: a name that filed *any* 8-K drifts +8 to +16 bp over ten bars against a quiet
name in the same cell, and the rotated calendar earns the same (+0.7 to +1.1 bp/bar): filer
composition, not filing timing. **Every distress item is long-favoured after the next open**
(impairments +59, delisting notices +103, auditor changes +92 per trade; medians negative) — the
fall is in the gap, what follows is a two-sided rebound lottery; every short-side sign prediction
was wrong. 5.02 officer changes: −5 bp, the one short below the rotation band. Nothing within a
factor of four of its 51–80 bp round trip. **The line closes at stage 1; the 2024–2026 slice
stays unread.** Untested: 6-K filers; a same-day construction on the 15m fixtures (its own line).
Records: spec `0aad00a`, RESULT `docs/decisions/D457-RESULT-…md`, artefact `data/d457_8k_atlas.json`.

## D456 — THE 8-K ITEM ATLAS, STAGE 0: 155k CORPORATE EVENTS, DEAD-INCLUSIVE, SAME-DAY, 15 CELLS; THE ATLAS WITH RETURNS IS NEXT, 2026-09-12

The insider line was parked (real per trade, zero net at the crossed line — the third line to end
at the cost wall). The successor is chosen for *where it lives*: corporate events resolve in days
and move names by more than their spread. Parsed from D331's cached EDGAR submissions index
(0 new requests): **154,970 8-Ks 2010–2023 on 82% of the fixture and 81% of the dead** (the 18%
gap is foreign 6-K filers), median filing lag 0–2 business days, **15 item cells with ≥ 300
filings** (1.01, 1.02, 2.01, 2.02, 2.03, 2.05, 2.06, 3.01, 3.02, 3.03, 4.01, 5.02, 5.03, 5.07,
8.01; 4.02 and 2.04 too rare). Every cell sits in the thin half of the universe; **2.06
impairments are the one distress cell in liquid names**; 3.01 delisting notices are half
late-filers who survive. **28,492 filings from 2024-01 to 2026-08 are parsed and flagged
unread — the confirmation slice for the stage-1 atlas** (long and short scored on every cell,
cap 10, state-matched control per cell, enumerated rotation, both cost lines, reproduction on
the unread slice as the family's multiplicity control; opened only on the principal's word).
Records: spec `5f8899e`, RESULT `docs/decisions/D456-RESULT-…md`, events `data/d456_8k_events.csv.gz`.

## D455 — INSIDER PURCHASES, STAGE 1: REAL PER TRADE, ZERO NET AT THE CROSSED LINE, NOT A CANDIDATE, 2026-09-12

The event book (long, cap 63, every event, 7,478 primary filings → 4,086 trades once the kernel
skips names already held): **+89 bp per trade, median +96, 2.3 control-SDs above state-matched
names in the same cell (C1 p50 +24)** — a real, contrarian insider effect on the dead-inclusive
fixture. **The book: +1.11 ± 0.56 bp/bar gross against a rotated-calendar median of +0.66 and
p95 +1.47; crossed cost 1.03 → net +0.08; passive net +0.62 (1.1 SE); 14 names to half, top 1% =
70%.** Clusters (+120) beat singles (+54); directors (+101) beat officers (+58), against the
prediction; value has no gradient; shorting insider sales loses (−23 ± 12). Cap 21 is the
strongest per bar (+1.89) and the most expensive; every hold nets ≤ 0 crossed. **Two events
lines in a row now say the same thing: a genuine per-trade effect of +65 to +170 bp over a
quarter or two, in exactly the small, thin, beaten-down names where the modelled 60–90 bp round
trip is closest to the truth, and no book at that cost.** Not a candidate; holdouts shut.
Records: spec `398669b`, RESULT `docs/decisions/D455-RESULT-…md`, artefact `data/d455_insider_book.json`.

## D454 — INSIDER PURCHASES, STAGE 0: THE DATA IS THERE, DEAD-INCLUSIVE, TWO DAYS OLD, AND SHAPED FOR THE KERNEL, 2026-09-12

The issuance line was parked (real, factor-grade, unbookable on 13 years). Its successor is an
*event*: insider open-market purchases from the SEC's Form 3/4/5 bulk data (81 quarters, 910 MB
git-ignored, `scripts/fetch_sec_form345.py`), CIK-mapped through D331. **17,270 purchase filings
2010–2023 on 1,279 names — 76% of the fixture and 71% of the dead cohort — 90% filed within the
two-business-day rule.** Insiders buy what has fallen (47% after a bottom-tercile 20-day
return), what is small, cheap and thin (60% in the bottom dollar-volume tercile), and they
cluster (a second distinct insider within a week on 47%). No abandon condition fires. **Stage 1
is the next record, and stage 0 fixed four of its choices:** separate 10% owners (18% of filings,
nine of the ten largest dollar buys: Roche in FMI, Berkshire in BAC); a family-trust guard on
clusters (Hyster-Yale's 60+ Rankin trusts are every top cluster); the state-matched control is
required (the buys sit in exactly the cells with their own hedged drift); a declared value floor.
Records: spec `4ce4b86`, RESULT `docs/decisions/D454-RESULT-…md`, events
`data/d454_insider_events.csv.gz`. Later quarters 2024q1–2026q1 are cached and unread.

## D453 — ISSUANCE STAGE 1b: THE ACCOUNTING FIX HALVES THE LOTTERY AND DOES NOT MOVE THE VERDICT, 2026-09-12

D446's trades re-accounted with a per-name beta hedge and vol-scaled weights ([K2] identity at
β=1, w=1 asserted). SE 1.52 → 1.17 at the same gross (+2.2 bp/bar); nine names to half the P&L
(was 5), top 1% 51% (was 85%), GameStop 10% of the long leg (was 29%). **Net crossed +0.86 ±
1.17; the same four tests fail; T3 passes both sides at 2.2 control-SDs.** The record's own
prediction failed the informative way: **the rotated selector's base rate did not collapse (C2
median +1.12 → +1.27) while the name-randomised selector's did (+0.39 → +0.08)** — the deciles'
composition earns in excess of beta on any dates (a low-vol / quality tilt the six tested axes do
not name); the alignment to the actual issuance year adds ~+1.0 bp/bar on an SE of 1.2. **The
issuance line now has two forward-return looks on the same trades and one answer: real per trade,
unresolvable as a book on thirteen years of one universe.** Not a candidate; holdouts shut. What
would change it is calendar time or a second universe with its own EDGAR panel — not a factor
hedge, a shorter hold or another decile (each a new selection on spent data). Records: spec
`8b7747d`, RESULT `docs/decisions/D453-RESULT-…md`, artefact `data/d453_beta_vol_book.json`.

## D446 — ISSUANCE STAGE 1: REAL PER TRADE ON BOTH SIDES, A LOTTERY AS A BOOK, NOT A CANDIDATE, 2026-09-11

The first forward-return look at share supply. Decile slot book (40 a side, cap 126) on D444's
first-filed counts through the D345 kernel. **Per trade, against state-matched names (price ×
vol × mom cells), both sides pass the gate (2.5–2.6 control-SDs above the control median; see the RESULT addendum):** net issuers shorted +72 vs the cell's −97, net
repurchasers long +208 vs the cell's +34. **The book does not collect it:** +2.3 ± 1.5 bp/bar
gross, net crossed +1.0 at 0.6 SE, era 2 flat, **five names to half the P&L, GameStop's
2021 squeeze trade (entered as a repurchaser 2020-10-15) 29% of the long leg**, three collapsed
biotechs the short leg. The exact common-offset rotation has p50 +1.1 and p95 +3.8 (a persistent
selector on the wrong dates still earns its state tilt); the persistent random selector p95 +1.8
is cleared. **Not a candidate; holdouts shut (they have no EDGAR panel anyway).** Two honest next
questions in the record §6, neither a refinement of this one. Records: spec `84793d8`
(numbered D446 because D445 was taken by another session mid-write), RESULT
`docs/decisions/D446-RESULT-…md`, artefact `data/d446_issuance_book.json`.

## D444 — THE EDGAR ACQUISITION: THE DEAD ARE SERVED, ISSUANCE HOLDS, A STAGE 1 IS THE NEXT RECORD, 2026-09-11

D443's line, re-sourced from the SEC's XBRL companyfacts (`scripts/fetch_edgar_companyfacts.py`,
7 min, 226 MB git-ignored cache; CIKs from D331's resolution). **77% of the 562 dead names now
carry a point-in-time share series** (first-filed value, available the bar after `filed`; median
lag 38 days from period end; 0.1% ever restated). D443's tables re-run unchanged on the
dead-inclusive panel: persistence **0.54** a year out (survivors 0.44), rank R² on the six tested
axes 0.10, momentum +0.04, net-repurchase share 50%. **None of the three abandon conditions
fires.** Two gaps to carry: 168 multi-class/foreign filers (11%) have no undimensioned count in
this API; filer scale errors on 0.2% of rows need a 50× guard in stage 1. **Next, on the
principal's word: a stage-1 pre-registration** — issuance as a persistent state, slot book both
sides, state-matched control, enumerated rotation, persistent-selector control, both cost lines.
Records: spec `f0d97af`, RESULT `docs/decisions/D444-RESULT-…md`; panel `data/d444_issuance_panel.csv.gz`.

## D443 — NET SHARE ISSUANCE, STAGE 0: ABANDONED ON A1 (THE VENDOR SERVES NO DEAD NAME), 2026-09-11

The first non-price-path line after the volume line's close. Alpha Vantage `BALANCE_SHEET` +
`CASH_FLOW` on all 1,573 names (51 min, cached under `data/raw/alphavantage/fundamentals/`):
**0 of 562 dead names are served**, so the pre-registered abandon condition A1 (dead coverage
< 50%) fired and the line ends on this vendor. On the 988 survivors the object itself is good:
one-year persistence 0.44, rank R² on the six tested axes 0.10, momentum correlation +0.07,
tilted to small/cheap/volatile/thin names and 62% of name-quarters net repurchasers. **If the
principal wants issuance, the source is EDGAR's XBRL `companyfacts` API (by CIK, dead-inclusive,
with filing dates)** — a data acquisition record, not a study. Records: spec `0fa0d5c`, RESULT
in `docs/decisions/D443-RESULT-…md`. Memory: the vendor's three quirks (gross flow fields
empty; shares restated for later splits on half the names; delisted tickers empty).

---

## THE VOLUME LINE — D434 → D441, PARKED ON A COST MEASUREMENT 2026-09-11; THE PULL IS THE PRINCIPAL'S

**State in one line:** a real, state-conditional volume effect (B: a 3× volume bar in a top-price
name, sold short — +21 bp per trade over its state-matched control, +64 SE over the enumerated
rotation null) that is **not a book at any cost line the repo can justify** (D440: crossed
−0.63/bar, passive +0.65 ± 0.89, era 2 +1.06 ± 1.48; cap 40 +0.95 ± 0.59). **Both daily holdouts
are unseen by this line and stay shut**: the D440 candidate condition (T1 ∧ T3 ∧ T4 ∧ T5) failed
at +0.7 SE. Nothing is admitted. The principal chose, 2026-09-11, to park B and run the quote
pull rather than refine or spend a holdout.

**The chain:** D434 volume atlas (five axes; flat as a universe average) → D435 conditional atlas
(the shock is +38 in top-momentum names and −48 in top-price ones — a universe average hid a sign
flip) → D436 stage 0 → D437 stage 1 (A and B carry a shock increment; every component net-negative
under the kernel's PUB 52–75 bp) → D438 (the increment lives in the widest spread third; only B at
every horizon) → D439 (a passive order at the open fills 92%, chase 9 bp, net capture 0.66 —
**and the modelled half-spread on MSFT-class names is 17–55 bp/side against a quoted 1–2: the
cost models are range models**) → D440 (B under both lines: not a candidate) → **D441
pre-registered `a92710a`, runner and sample `295c70f`: the quoted spreads on the 272 names B
trades, and B re-costed at the quote.**

**WHAT THE NEXT SESSION DOES — in this order, nothing else first:**

1. The principal opens TWS or Gateway (paper 7497 / live 7496; Gateway 4002 / 4001) and runs, from
   the repo root, **D336 first** (the convention question outranks B's; ~35 min):

   ```bash
   uv run --group ibkr python scripts/d336_ibkr_quoted_spreads.py --pull --host 127.0.0.1 --port <PORT> --client-id 336
   ```

   then D441 (~80 min; 17 of its 272 names are already cached by D336 and are skipped):

   ```bash
   uv run --group ibkr python scripts/run_d441_b_quotes.py --pull --host 127.0.0.1 --port <PORT> --client-id 441
   ```

   Both are resumable (a name with a CSV is skipped), `readonly=True`, need the US-equity
   historical-quote subscription, and abort on ten consecutive subscription errors or on a name
   whose BID_ASK bars violate open ≤ close on 1% of days. Raw bars land in `data/raw/ibkr/`
   (git-ignored, exchange-licensed, never committed).

2. Then, no session needed:

   ```bash
   uv run python scripts/d336_ibkr_quoted_spreads.py --compare
   ```

   ```bash
   uv run python -u scripts/run_d441_b_quotes.py --compare
   ```

3. Write the two RESULT records. **D336's is owed since 2026-09-05** and must read Q2 on the
   non-clamped subset and mark Q3's second clause not evaluable (§8a). D441's bar: T3q ∧ T4q on
   the **crossed-at-the-quote** line → candidate for a holdout read, only on the principal's word.
   **X-e already says the book most likely still fails at 2 SE even at a favourable quote** — the
   pull decides whether B is closed on cost or on its own noise, and whether the wide tercile's
   +64 passive net is a per-trade object at all. Two known deviations to disclose in D441's RESULT:
   17 (not 33) names overlap D336's sample; 11 (not 10) padded names were excluded (GOCOQ).

**Two things the pull will hit, known now:** (i) the fixture carries acquired names as `alive`
with a constant close and zero volume since the acquisition (SPLK at 156.9, SGEN, KRTX, AVNS …;
the meta counts a delisting after the span end as alive). D441 excludes them by rule; **D336's
sample has one (AVNS)** — it will come back unresolved and D336's compare counts a missing CSV,
not a failure. (ii) D441's compare *excludes and lists* a name failing `[N]` or `[G]` where D336's
aborts; the RESULT reports every exclusion by tag.

**Parked by the principal, not closed** ("keep the rest in mind", 2026-09-11): a calendar-split
stage 2 (A off-cadence long / B on-cadence short); equal-risk sizing; anything on A, C, D.
**Method yield of the line, already in memory:** align the event mask to the kernel's fill
(D434's one-bar look-ahead); condition a new feature on the atlas states before calling it flat
(D435); read the cost convention the kernel gates on before predicting a net (D437); the cost
models are range models (D439).

---

## THE SECOND-ZONE LINE — D412 → D433, CLOSED BY THE PRINCIPAL 2026-09-10, BOTH DAILY HOLDOUTS SPENT

**Read this before touching either daily holdout: they are both spent, by this line, on
2026-09-10.** `us_shorts_daily_holdout` (803 names) was read a second time under the principal's
ruling that a holdout spent by an unrelated strategy is unseen by a new line (D430);
`us_shorts_daily_holdout2` (576 names) was read once (D433). There is no unseen daily
single-name data left for anything descended from a departure-zone touch.

**The line:** D412 departure zones → D413 distance arming + cell 2 (REV/EFF/DV medians) → D414–D416
entry timing (touch-day close wins) → D417–D419, D423–D425 nine exit constructions (none beats
`t+5`, no stop) → D420–D422 the second touch (STACK2-ANY, +45 in-sample) → D426 double-down (dead)
→ D427 five layers → D428/D429 the combined long book at 3 slots, which met the in-sample
candidate condition → **D430 holdout 1: the long arm −29 gross, everything above the base
rung gone** → D431 short arm on the union (tail-carried, unbookable) → D432 breadth gate (wrong
sign), DV lever (+8 bp), gap by half (inverts) → **D433 holdout 2: net Sharpe −0.19; the touch
effect reproduces a third time.**

**What is TRUE across three disjoint name sets (1,573 / 803 / 576):** a distance-armed
departure-zone touch entered at the touch-day close and exited at `t+5` earns **+9.8 / +10.1 /
+13.0 bp gross**; cell 2 makes it **+30 / +18 / +18**. Cost is 24–34 bp. **Net Sharpe of the best
transferable object (cell 2 ∧ top-ADV tercile, 10 slots): +0.05 / −0.03 / −0.19.** File the touch
effect as a base rate a future study must beat; it is not a trade.

**What did NOT travel, on both unseen sets:** the second-touch rung (+45 → +6 / +17), the cheap
tercile (+86 → +17 / +28), long-only (+80 → −29 / −21), the gap ordering (inverts), the ADV
tercile's gross side, every exit, every gate. The short arm's mean was positive on all three
sets on a median of ~0 and no 2–5 slot book collects it. In-sample nulls (within-day
permutation, matched random pools) were passed at +5 to +10 SE by selections that did not
transfer: **they test selection inside the spent names, not transfer.**

**Process disclosure — the door.** `run_d411` installs an unconditional audit hook refusing any
path containing "holdout" (no `allow` switch; `run_d365`'s `V65.allow_holdout(why)` is the
designated, logged unlock, but it lives on a module this line's chain does not import). D430's
ADDENDUM opened each holdout in a **separate hook-free process** (`scripts/d430_oos_loader.py`,
`scripts/d433_oos2_loader.py`, `--spend-the-holdout`), wrote the panel to a cache named without
"holdout", printed a receipt with the file's SHA-256, and the runner read the cache. The
information the designated door would have logged is in the receipts (D430/D433 RESULT); the
designated function was not called. If the guard is consolidated, the two hooks should become one
with the `allow` switch, and openers should call it.

**Reusable from this line:** `scripts/run_d430_holdout.py` (a fixture-parametrised pipeline with a
`--proof` mode that reproduces in-sample bit-identically before any out-of-sample read),
`run_d431_shorts_union.py::union` (two fixtures on one calendar), the ladder printed on every
out-of-sample read so a failure is located, Sharpe with a monthly block-bootstrap SE
(`run_d433_holdout2.py`), and the memory rules written on 2026-09-10 (measure the worker before a
fan-out; a required book is not utilisation × base; a tail-carried mean does not book; layers
selected on spent names vanish out of sample).

**The one lever never measured:** execution — passive fills at the zone versus the crossed-spread
Corwin–Schultz model. Blocked on the TWS session like everything else in 0d2 (1).

---

## AFTER THE RETIREMENT — the three atlas floor gaps are CLOSED, 2026-09-09

On the principal's instruction, and **outside the retired chain**:
[**D392 ADDENDUM 2**](../decisions/D392-ADDENDUM-2-the-last-three-floor-gaps.md) — six cells,
**193 → 199**, `data/d392_atlas.json`. Runner `scripts/run_d392_atlas_gapfill.py`.
**A MEASUREMENT: admits nothing, closes no avenue, spends no holdout read.**

| gap | trades | **floor p95** | ± SE | D391's observed | ratio |
|---|--:|--:|--:|--:|--:|
| cap 5, long | 94,198 | **+2.43** | 0.19 | +4.97 | 2.05× |
| cap 5, short | 106,888 | **+2.21** | 0.11 | +2.89 | 1.31× |
| cap 1, short | 167,179 | **+0.83** | 0.05 | +1.06 | 1.28× |

**Three things worth carrying:**

1. **The atlas seed was never reproducible.** Each cell was seeded through `hash(side) % 97`, and
   `hash()` on a `str` is **salted per interpreter process**. Nothing is biased — every draw is
   uniform over the same eligible index either way — but **the 193 cells written before today
   cannot be reproduced bit-identically, and no record said so.** Fixed to an explicit code map;
   cells written from here on reproduce exactly. The 193 were not recomputed.
2. **Printing the null's SPREAD reframes D391's table.** Nine of its twelve cells sit above their
   p95 floor; **eleven of twelve sit inside the range 500 uniform draws actually produced.** Only
   cap-5 long exceeds every draw. `--d391table` regenerates it. **It changes no verdict** — D391
   died on `B_r`, a same-pool control.
3. **My extrapolation failed (Q3), against interest.** I read a straight line through a bend: the
   p95 curve flattens above ~90,000 trades, so the cap-5 short floor came in **higher** than
   predicted and D391's margin **thinner** (1.31× where I said 1.5×–2.4×).

**Still owed on the atlas** (§R7): the *conditional*-pool trade range (2,827–19,241 at cap 20),
cap 60 above 26,991 trades, and the pools it cannot pre-compute — including the one D391 actually
needed, *names on a large-intrabar-range bar*.

---

## THE SIGNAL HUNT — D391 → D397, CHAIN RETIRED AND **MERGED** 2026-09-09

**Merged to `master` as a clean fast-forward** (`483ac82..e89e821`, 84 files, +53,818) on the
principal's instruction, reversing the branch's standing rebase-only rule. **The principal ran the
merge from the main checkout**, because `master` was checked out there with another session
actively committing to it — git refuses to update a branch checked out elsewhere, and forcing it
would have desynced that worktree's index under a live session.

**Shared programme records touched by this merge, and only these three:** `CLAUDE.md` (the
sampled-p95 bias clause), `docs/RULES.md` (**R16** — a published number is not reproducible without
naming the build), and `docs/decisions/D289-the-promotion-pipeline.md` (its **sixth** and
**seventh** amendments). **`docs/FINDINGS.md`, `docs/BOOK.md` and `docs/BOOK_PROP.md` are
UNTOUCHED** — nothing was admitted and no finding was published without the principal's ruling.

[D396](../decisions/D396-RETIREMENT-the-sign-sequence-chain.md) is the retirement record and the
place to start.

> **THE D390 COLLISION WAS RESOLVED BEFORE THE MERGE, NOT CARRIED INTO IT.** Master had taken
> `D390` **twice** — the D163 re-cost and the D280 overnight-gap pre-registration — while this
> branch was running on a reserved D390–D399 block. **The branch's D390 (the volatility tilt) was
> renumbered to [D397](../decisions/D397-the-volatility-tilt-zr-scored-alone.md)**, along with
> its RESULT, its runner (`scripts/run_d397_volatility_tilt.py`) and its artifact
> (`data/d397_stage0.json`).
>
> **Every reference was moved by explicit, count-asserted replacement — never a blanket sed** —
> because a blanket rename once corrupted a link to a *different* record in `RULES.md`. Nine
> references were updated across `RULES.md` (R16's three), `D392`, `D393`, `run_d392` and the
> renamed files themselves; the three *"reserved D390–D399 block"* mentions in D393/D394/D395 were
> deliberately **left alone**, since they name the block and not the study. **A leftover grep after
> the rename shows every remaining `D390` belongs to master.** D391–D397 do not collide.
>
> **BOTH OF MASTER'S TWO `D390`s HAVE NOW MOVED OUT OF THE RESERVED BLOCK.** The D163 re-cost went
> `D389 → D390 → D400`. The **D280 overnight-gap check went `D390 → D402`** on 2026-09-09 — records,
> runner (`scripts/run_d402_stale_open_check.py`) and artifact (`data/d402_stale_open_check.json`),
> by the same count-asserted replacement, with the nine collision-history mentions of `D390` in this
> file deliberately left alone. **It was taken after checking `ls docs/decisions/`, which this file
> already warned is insufficient and will collide.** Commit hashes are historical and unchanged:
> pre-registration `6843a39`, result `c6c63f6`.

**THE ONE LINE: eight candidates, zero admitted, zero holdout reads, and the chain RETIRED by the
principal on 2026-09-09.** [D396](../decisions/D396-RETIREMENT-the-sign-sequence-chain.md) is the
retirement record and the place to start.

| | |
|---|---|
| **Retired 2026-09-09** | **D393** sign sequences (+ 6 addenda), **D394** exit rules, **D395** the CHOP cell |
| **How far it got** | `up_run_21` E1/cap 20 cleared **all four** nulls (B the binding one at **+0.91**, resolved ABOVE only at 4,000 draws) — and **never cleared H1**, whose best-of-10 floor was never computed |
| **The one cell that reached 1.00× coverage** | cap-20 CHOP, **net −0.44** — found by searching 36 cells, at a hold that was not the declared primary, whose own primary **failed the search floor by 22 SE**. Retired with the rest |
| **Books** | **unchanged.** S1, S2, neither at capital; prop book empty |

**The instruments are the durable output and they outlive the chain:**
`scripts/lag_audit.py` (the shared `[L]` audit, built because D391 shipped a look-ahead that cost
82% of its result) · `data/d392_atlas.json` + `run_d392_base_rate_atlas.py` (193 measured base-rate
cells; `lookup` **raises** outside the grid) · **the exact permutation floor** in
`run_d395_chop.py` (best-of-N for a cell picked from a grid — no independence assumption, 10,000
draws in 44 s; **should replace normal-approximation floors programme-wide**) ·
`scripts/ragged_sign_scores.py` (Axis I; `sign_flips_21` is the most orthogonal score measured,
max |ρ| 0.025) · the shard/merge pattern with one `item_at()` and `[SHARD]` bit-identity.

**Six findings worth carrying** (full list in D396 §2): base rates are large enough to look like
signals (price tercile **36.8 bp** for a *random* long) · **the edge lives where trading is
dearest**, measured three independent ways · a clairvoyant delisting filter would **lose** money ·
hit rate is immovable at **50.1–50.8%** · eleven observables all predict both tails equally · no
exit rule closes a cost gap (126 cells, best recovered 2.53 bp of 50.88).

**Open and NOT closed by the retirement:** `sign_flips_21` as an independent *input* (retired as a
signal, not as a variable) · `working/SLEEVE-VS-ALLOCATOR-PROPOSAL.md` (three questions) ·
`working/FINDINGS-52-corollary-NOTE.md` (six questions) · the FINDINGS §48 amendment draft ·
~~three atlas floor gaps (cap 5 both sides, cap 1 short)~~ **— CLOSED 2026-09-09, see the block at
the top of this file** · a `docs/research/the-signal-hunt-part2.md` §2a correction already made in
place.

---

**Updated 2026-09-09.** **D365 → D401.** **Three** sessions on master, plus one on a branch: the
first spent the programme's first holdout read, ran D373 and audited the hurdles that judged it; the
second built and **retired the density line (D384 → D388)** and **answered the correlation floor
(D389)**; the third **priced the prop instrument end to end (D386)**, **settled the D383 debt by
running it**, **discharged R11's re-costing corollary (D400)**, and recorded the principal's
**closure of two avenues (D401)**. Everything below §7 is older strata, newest first, kept because
the traps in them still bite.

> ## ⚠ READ THIS BEFORE YOU PICK A DECISION NUMBER
>
> **`ls docs/decisions/` IS NOT SUFFICIENT AND WILL COLLIDE.** It happened **twice within the hour**
> on 2026-09-09 — the second time *while fixing the first*:
>
> 1. Two sessions both took **D389** — the D163 re-cost pre-registered 23:17 (`7d04812`), the
>    correlation floor 00:24 (`5bd7d97`). The re-cost had it first by commit time but was renumbered,
>    because the other had already propagated `D389 = correlation floor` into this file.
> 2. It was renumbered to **D390 — which was already RESERVED.** The `worktree-signal-hunt-part2`
>    branch reserved **D390–D399** at 2026-09-08 12:27 (`fb2af62`), after master took D380, D381 and
>    D382 out from under it twice. **That reservation is a commit message on another branch** —
>    invisible to `ls`, and invisible to `git log` run on master alone.
>
> **Both records were then moved clear of the block: the re-cost is `D400`, the closure `D401`.**
>
> **THE PROCEDURE IS THREE COMMANDS, NOT ONE:**
> ```
> git log --all --oneline | grep -iE "\bD<n>\b"    # usage on ANY branch
> git log --all --oneline | grep -i "RESERVE"      # reserved blocks
> git branch -a --format="%(refname:short) %(committerdate:relative)"  # who is live right now
> ```
> **D390–D399 belongs to `worktree-signal-hunt-part2`. Master takes D400 and upward.**

**This file had been stale since 2026-09-02** (D264→D284) and both `STACK.md` and the 2026-09-07
handoff said so in writing. It is current again as of this line.

---

## 0. THE ONE-LINE STATE, 2026-09-09

**THE MOMENTUM BOOK FAILED OUT OF SAMPLE AND WAS RETIRED. ITS SUCCESSOR WAS THE SAME BOOK, AND THE
COHORT — NOT THE SIGNAL — IS ~73–80% OF ITS EDGE. THE REMAINING ~27% IS A REAL ENTRY-TIMING EFFECT
WORTH AT MOST HALF A ROUND TRIP. HOLDOUT #1 IS SPENT; HOLDOUT #2 IS BUILT AND UNSPENT. BOTH BOOKS ARE
UNCHANGED.**

**AS OF 2026-09-09: the density line is RETIRED — the object works, the conditioner is inert. The
0.44 correlation floor is ONE unidentified factor and none of the four named candidates explains it.
D383 IS RUN AND THE QUEUE IS NOW EMPTY — nothing is pre-registered and unrun. The single highest-value
item in the programme — D336's quoted-spread pull — is BLOCKED ON THE PRINCIPAL'S TWS SESSION, and it
decides whether the incumbent book is positive at all.**

**AND THE PROP INSTRUMENT IS NOW PRICED, WHICH IT NEVER WAS. [D386](../decisions/D386-the-prop-account-is-worth-its-buffer.md):
at zero edge a funded account is worth EXACTLY ITS DRAWDOWN BUFFER — you cannot extract more in
expectation than the amount they let you lose — and the whole question reduces to one
leverage-invariant number, CALMAR ≥ 18.9 ON OPEN EQUITY. The best audited intraday CME programme in a
199-programme database is 1.07. Twenty-two research lanes found ONE prop-eligible candidate, with a
known contamination risk. THE PROP TRACK IS NOT BLOCKED ON VALUATION ANY MORE; IT IS BLOCKED ON
HAVING A STRATEGY, and the shape it needs is now known.**

| | |
|---|---|
| **Personal book** — `docs/BOOK.md` | **S1, S2 only, neither at capital** |
| **Prop book** — `docs/BOOK_PROP.md` | **none**, and the candidate list C1–C4 is **exhausted** (D379 §6) |
| **Holdout reads spent, programme total** | **1** (D371, 2026-09-07) |
| **Retired 2026-09-07** | **S6** (nine-condition gate), **C9** (252-bar high alone) |
| **The winners'-dip avenue** | **RETIRED 2026-09-08, then REOPENED NARROWLY** for one test. **D378's gate PASSED** so the abandon condition never fired; **D380 then closed the exit half — no overlay beats not cutting.** The timing picture is complete: **the entry day carries information, the exit does not, and neither is large enough to matter after cost.** **STATUS IS THE PRINCIPAL'S.** [FINDINGS §52](../FINDINGS.md) |
| **Hurdles retired or replaced** | **H4 → H4′** (D374) · **1d → 1d′** (D376) · **hedge H0 → H1** for future studies (D377) · **P1 restated as a SIZING RULE, not a filter** (D375 → R11, 2026-09-08) |
| **THE DENSITY LINE — RETIRED 2026-09-09 by the principal (R15)** | D384 -> D388, five studies. **The OBJECT works** (TV 0.18-0.51, ratio CV 0.51-1.31, 2-3 modes, causal, proved). **The CONDITIONER is inert**: beats the path-shuffle null 34/36 at p to 7.2e-11, beats the ROTATED-DENSITY null 0/36, and corr(density shape, edge) is -0.027 across all 36 cells - positive in 10/36, below chance. Net negative in all 36. [FINDINGS 56](../FINDINGS.md) |
| **What the density line cost, and what survives** | **~4.5 h of compute, three of five studies measuring the wrong thing** (D384 wrong statistic; D385 flat object; D387 flat on half its universe with mismatched gates). Survives: the proved construction, `f_hat` constant between events under plain decay (24x), sigma-unit thresholds (rarity spread 4.37x -> 1.37x), and **beating a path-shuffle null is nearly free - the persistent-selector control is the test** |
| **ONE PRE-REGISTRATION IS AWAITING A RUNNER** | **D383** — the time-series structure screen at 15 minutes (`af91504`, amended `cb864cb`). Fixture gated `3c9d57c`. **The runner does not exist and was deliberately not built.** |

**For D285 → D364 read [`docs/STACK.md`](../STACK.md) §0 and §§32–42**, not this file. That is the
layer-by-layer statement of what the stack earns once costed, and its §7 records what earlier
versions of it got wrong. This section deliberately does not restate it.

**One defect to fix in the truth file:** `docs/FINDINGS.md` has **two sections numbered §51** (the
holdout read, and equal-weight sizing). The new section was added as §52; the collision is upstream
and untouched.

---

## 0a. THE HOLDOUT LEDGER — READ BEFORE ANYTHING ELSE

| fixture | slice of the pinned permutation | names | state |
|---|---|---:|---|
| mining prefix | `order[:3400]` | — | spent many times over; free to mine further (see the ruling below) |
| `us_shorts_daily_holdout.csv.gz` | `order[3400:5100]` | 803 | **SPENT 2026-09-07 (D371, momentum). READ AGAIN 2026-09-10 (D430, the second-zone line) under the principal's ruling that a holdout spent by an unrelated strategy is unseen by a new line.** Spent for both lines. |
| `us_shorts_daily_holdout2.csv.gz` | `order[5100:6300]` | **576** | **SPENT 2026-09-10 (D433, the second-zone line).** 1,532,631 rows, dead share 32.6%, gates clean; unseen by every OTHER line — the principal's per-line ruling applies |
| remaining unfetched | `order[6300:]` | **2,301** | never fetched, never scored |

The permutation is deterministic — alphabetical sort, one shuffle at `POOL_SEED = 20260828` — so any
further slice can be cut without re-picking anything.

**The 5,201 figure in the 2026-09-07 handoff was wrong.** It counted from the end of the *mining*
prefix and therefore included holdout #1 itself. The true remainder at that moment was **3,501**.
Corrected here; verified directly against `data/raw/alphavantage/daily_adjusted/_pool.json`.

**The guard is default-deny.** `run_d365_momentum_buffer.py` installs an audit hook refusing any path
containing "holdout", metadata included; an authorised process calls `V65.allow_holdout(why)`, which
prints loudly and logs every holdout file opened. CPython has no `removeaudithook`, so this is the
only way through. **Building and rehearsing on a holdout is fine. Reading is not, without explicit
specific authorisation from the principal.**

**Breadth is the unsolved problem with holdout #2.** Panel coverage per bar: mining **1,008**,
holdout #1 **534**, holdout #2 **369**. On D371's stricter study-eligibility mask holdout #1 gave
369, so holdout #2 should land near **255** — about **0.69×** holdout #1's breadth. D371 already
failed a breadth hurdle. **Decide what breadth a read needs before spending this fixture, not
after.**

---

## 0b. THE PRINCIPAL'S RULING ON MINING SPENT DATA, 2026-09-07

*Quoted because it governs every study that follows:* a **brand-new construction** may mine the
already-spent in-sample fixture, **provided nothing crosses into a holdout**. The contamination cost
rises slowly on its own as a share, and is accepted for now. D373 was run under this ruling and
nothing crossed.

---

## 0c. D373 — the last study, and what it settled

**[D373](../decisions/D373-the-winners-dip-long-and-the-median-criterion.md)** pre-registered
(`aa7bc2f`, amended `462f894`), **[RESULT](../decisions/D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md)**
(`9162a64`). The winners' dip long: a fresh `rev_5` dip inside the `mom_252_21` **top** decile,
entered long, 40-bar cap. 3,932 trades, 796 names.

| | | |
|---|---|---|
| **H1** signal vs A′/B/B_c/C | **PASS** | +160.55 vs p95s +105.76 / +51.92 / **+155.60** / +52.72 |
| **H2** `mean > median > 0` | **FAIL** | median **+51.55**, below A′'s p95 +81.42 and B_c's +87.43 |
| **H3** era 1 standalone | **FAIL** | +16.86 vs p95s +64.60 / +77.24 |
| **H4** breadth | **FAIL** | 18 of 796 names = **2.26%** to half the P&L; bar 10% |
| **H5** capturability | **PASS** | open-entry t 5.11, retention 98.7% |
| **H7** independence | **FAIL** | **ρ = 0.9346** to the retired D365 book |

**Three things from it that outlive it:**

1. **`B_c` is the control that matters and its p50 is +126.54.** Most of the observed +160.55 is
   available to a random name drawn from the same momentum decile on the same day. **Any study
   selecting inside a cohort must null against a same-day same-cohort swap, or it is measuring
   cohort membership.**
2. **The H1 margin was one trade wide.** Top trade: **GME, entered 2021-01-04 at $17.25, held 40
   bars, +40,029 bp — 6.34% of the ledger.** Drop it and the mean falls to +150.41, **below B_c's
   p95**. So does dropping all ten GME trades, and so does dropping Nov-2020→Mar-2021 entirely.
   `scripts/d373_posthoc_probes.py`, post-hoc and labelled so.
3. **`mean > median > 0` IS CONFOUNDED WITH HOLDING PERIOD.** Re-cutting D365's *own* stored paths:
   PASS at 20/40/60 bars, FAIL at 100 and at its native ~99. D373 and D365 **agree** at equal
   segmentation. The mechanism is arithmetic — summing fat-tailed returns over a longer window lifts
   the mean and drops the median. **Within-study null comparisons hold segmentation fixed on both
   sides and stay fair; cross-construction median comparison does not.**
   `scripts/d373_segmentation_probe.py`, `docs/decisions/D373-RESULT-*.md` §3a.

---

## 0c2. D374 — the breadth hurdle was unreachable, and H4 is retired

**[D374](../decisions/D374-is-the-breadth-hurdle-reachable.md)** pre-registered (`4c0816c`),
runner (`c2f7887`), **[RESULT](../decisions/D374-RESULT-the-breadth-bar-was-unreachable-and-it-failed-the-most.md)**
(`520dd40`). A METHODOLOGY study: it adjudicates a hurdle, not a strategy, and adds no looks to any
multiplicity ledger.

**Across 4,952 defined null draws in three arms, the most diversified random book reached 2.98%. The
median reached 0.63%. The bar was 10%.** D373's book, at 2.2613%, sits at the **100.00th percentile
of its own nulls** — above A′'s *maximum*, with 0 of 1,971 A′ draws and 0 of 981 B draws as
diversified. A′ holds the name set and each name's trade count exactly fixed, so this is what a
fat-tailed return distribution does to any ~800-name book here; selection has nothing to do with it.

**H4 IS RETIRED. Its replacement, in force for all future studies:**

> **H4′** — `names_to_half_share` at or above the **p05 of A′ computed on that study's own ledger**,
> with the degenerate-draw count reported beside it. **The threshold comes from the study's own null,
> never fixed in advance of the universe.**
>
> **The top-1 and top-5 name-share bars are DROPPED, not re-thresholded.** The statistic is unbounded
> above: **233 of 1,971 A′ draws (11.8%) have a top-5 share over 100%**, with maxima to 37,546%,
> because a small positive denominator explodes it while it stays technically "defined". D371's
> real-world 142% was not exceptional. Any percentile of it is contaminated.

**Two lessons wider than this hurdle:**

1. **"Has anything ever passed this?" is a cheap and powerful test, and it has not been run on the
   rest of the hurdle set.** H4 had never once been cleared, by anything, and nobody had checked
   whether it could be.
2. **A threshold fitted to one observed failure carries no information about the next book.** D373 §5
   said in writing that H4's bars were "calibrated to exclude the shape that just failed". That was
   honest about provenance and fatal as evidence.

---

## 0c3. D375 → D377 — the hurdle audit and what it turned up

**[D375](../decisions/D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is.md)
(`1732fd0`), a REVIEW.** I predicted H4's disease would be widespread. **It is not**, and the reason
is structural: most stage-1 gates are built on **t-statistics, whose null centre is zero by
construction**, so `t ≥ 2` means the same thing in every universe and cannot be unreachable. **H4 was
the only threshold nothing had ever cleared.** What the audit did find:

- **Three of hurdle P's six thresholds have never been computed on anything** — **P3, P4, P5**. D266
  says outright P4 is *"not calculable from these artifacts"*. Under [R6](../RULES.md) the prop
  track carries three hurdles nobody has run.
- **P1 cannot fail.** It is applied by scaling until drawdown reaches 4%, so it is a **sizing rule
  that converts to a return penalty**, not a filter. R11's table lists it as one. **Recommended
  restatement, not yet made.**
- **P5 is the only surviving threshold with H4's disease** — a ratio whose denominator
  (trailing-year profit) **can cross zero**.

**[D376](../decisions/D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two.md)
(`ca8a89c`) — the correlation floor.** 500 draws, 280,625 pairs.

| | p50 | p95 |
|---|---:|---:|
| A′ identical name set | +0.448 | +0.485 |
| **B unrelated books** | **+0.476** | **+0.526** |
| B_c same cohort | **+0.923** | +0.930 |

- **It is TIME, not names.** A′ books hold the *identical* names and correlate **less** than B books,
  which hold different names on the **same days**. The residual factor is a **per-bar** effect.
- **Gate 1d measures POOL OVERLAP, not independence** — same pool ≈ 0.42–0.53, different pools ≈ 0 or
  negative (the observed book sits at **−0.091** against B draws), same cohort ≈ 0.92. **1d′ therefore
  SCOPES: compare to the p95 of the candidate's OWN pool, and NAME THE POOL.** A raw correlation
  without it is uninterpretable.
- **[CLU]** — cluster the bootstrap on **books**, not pairs. 280,625 pairs came from 1,250 books.

**[D377](../decisions/D377-RESULT-the-beta-hedge-is-adopted-and-it-fixes-seven-percent-of.md)
(`cd97e4f`) — the hedge.** The incumbent assumed **beta exactly 1 for every name**; a lagged
`roll_beta(63, 21)` existed unused.

| hedge | B p50 | M1 | gross/trade | kept | M2 |
|---|---:|:--|---:|---:|:--|
| H0 unit market | +0.4728 | baseline | +160.55 | 100% | baseline |
| **H1 per-name beta — ADOPTED** | **+0.4404** | PASS (10.6 SE) | +156.57 | 97.5% | PASS |
| H2 cohort | +0.3242 | PASS (38.8 SE) | **+34.08** | **21.2%** | **FAIL** |
| H3 price decile | +0.4439 | PASS (9.7 SE) | +160.47 | 99.9% | PASS |

- **H1 binds for future studies. It fixes ~7% of the problem** — the floor falls 0.473 → 0.440,
  decisive but small. **Past records stay on H0 and must be labelled**; re-basing them is the
  principal's call and is not obviously worth it.
- **The common factor is mostly NOT unhedged beta.** Untested and now the open question: **shared
  slot mechanics, equal-weighting, the eligibility floor itself.**
- **H1 and H3 are a near-tie and whether they are complementary was NOT tested** — a combined hedge
  was not in the pre-registered grid.

---

## 0c4. D378 — the entry day DOES matter, and D379 — the prop account is a barrier option

**[D378](../decisions/D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its.md)
(`7117478`).** The one test the narrow reopening authorised. **A′_c**: for each observed entry, a
replacement bar drawn from the days **that same name** was eligible **and** in the top decile — name,
cohort and per-name count fixed, **only the day moves**. 2,000 draws.

| | | |
|---|---|---|
| **T1** | mean per trade > A′_c p95 | **PASS** — +160.55 vs +144.57, **+26.9 SE** |
| **T2** | *reported* — the **median** | **FAIL** — +51.55 vs +64.00 |
| **T3** | **GATE** — largest trade removed | **PASS** — **+150.41**, **+9.8 SE** |

- **A′_c's centre is +116.91**, so **73% is still cohort** — a third independent measurement beside
  D373's 79% and D377's 79%.
- **The front-loading is the dip's.** Observed bp/bar halves across caps 5→60 (7.82 → 3.94) while
  A′_c's barely moves (2.01 → 2.75). At cap 5 the observed runs at **3.9×** the control's rate.
- **The gain is in the mean, not the median.** Timing makes good trades bigger; it does not lift the
  typical trade. **Win rate is the median's neighbour — nothing shows a better one is available.**
- **Cost decides it and cost is unresolved:** the increment is **0.19–0.47× a round trip under PUB**,
  **0.50–1.21× under PB**. Which convention is right is **D336's quoted-spread pull**, which needs
  the principal's TWS session.
- **FINDINGS §52's corollary was amended** — it called the selector "a rounding error on a factor
  exposure" and that is withdrawn. **A real effect small relative to cost is a small real effect.**

**[D379](../decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no.md)
(`861ec8f`, amended `7b4e58f`) — FRAMING, from a session other than the one that ran D373–D378.** No
measurement on any fixture; one toy Monte Carlo, labelled as illustration and deliberately not
committed to `data/`.

- **A funded prop account is a down-and-out call**, component for component: fee = premium, P&L =
  underlying, **drawdown limit = knock-out barrier monitored continuously on OPEN equity — which is
  P1 exactly.** Accounts are purchasable in quantity, so `fee / P(pass)` is the acquisition cost of
  one funded account.
- **Hurdle P has six screens and no objective function behind them.** It admits candidates; it never
  ranks them. `E[payout]` would.
- **Measured consequence:** at zero edge on a Topstep-like eval, a **static** floor gives the
  optional-stopping **40.0%** pass rate and the **trailing** floor **26.5%** — the ratchet costs ~13
  points.
- **It changes nothing yet.** No candidate reopened, no threshold loosened, and its own bound is
  stated: *"this is a valuation framework, not an edge… the prop candidate list is exhausted, so
  there is currently nothing to value."*

---

## 0d. WHAT IS LIVE NOW, RANKED

**RE-RANKED 2026-09-09 (later), after D383 was run and the prop instrument was priced. THE QUEUE IS
EMPTY: nothing is pre-registered and unrun.** What follows is candidates, not commitments.

> ### 0d0. THE NEGATIVE-SPACE SCAN AND ITS SEVEN EXTERNAL BRIEFS, 2026-09-09 — **ELEVEN LEADS, THREE STILL STANDING AFTER THE EVIDENCE, AND THREE METHOD FINDINGS ALONGSIDE THEM**
>
> **THIS WAS COMMISSIONED AS A LEAD SCAN AND ITS DELIVERABLE IS LEADS.** An earlier version of
> this section led with *"no strategy was found"*, which measured a lead scan against a bar
> nobody set for it — a lead that survives a smell test and a costed literature check **is** the
> product here. **What follows is the inventory; §0d0a ranks it.** Testing is a separate act
> under R8 and none has occurred.
>
> **[`docs/research/the-negative-space-scan.md`](../research/the-negative-space-scan.md)**
> (`bbc2790`, consolidated `00eaccb`). A scan of the categories the record had **never** put in a
> runner, scored on seven axes drawn from what has actually killed studies here. **Then seven
> agents researched the published literature, one per lead, briefs in `working/leads/` under that
> directory's quarantine contract.**
>
> **Status of every item below: a LEAD.** None has been tested — that is R8's separate act and it
> has not happened. Both books are unchanged.
>
> ### 0d0a. THE INVENTORY — eleven leads, by category
>
> **REGIME DETECTORS**
> 1. **Cross-asset state** — `log(HYG/IEF)`, `log(IEF/SHY)`, defensive-vs-cyclical, as a
>    market-level time gate. **The only gate this programme could build that is not a function of
>    the equity universe it trades.** → [D404](../decisions/D404-the-cross-asset-state.md).
>    **STANDING**, with the horizon in doubt.
> 2. **Even-week FOMC cycle** (Cieslak–Morse–Vissing-Jorgensen, JF 2019) — surfaced by the K1
>    brief as **better founded than the pre-FOMC drift it was sent to check**: far more events,
>    causal evidence, no published OOS failure found. **STANDING, and untouched by the K1 verdict.**
> 3. Turn-of-month / day-of-week / pre-FOMC window. **FELL** — location, not decay: on FOMC days
>    the CAPM works, α insignificant, and equal weighting *shrinks* it (36→25→20 bp).
>
> **CROSS-SECTIONAL SIGNALS**
> 4. **Industry-relative reversal in liquid names + a low-volatility screen** — +0.31%/mo,
>    t=2.73, VW large-cap. **Two agents that never communicated converged on it** from different
>    literatures. **STANDING and it is the strongest of the eleven** — but it is *someone else's
>    published result*, never tested here, and in both accounts **the cost filter does the
>    rescuing, not the residualisation.**
> 5. **Combining the 16 OHLC terms** — equal-weight cross-sectional rank average, every sign
>    declared in writing, floored against a sign-fitting null. **ROSE FROM LAST TO FIRST** of the
>    unregistered leads once §59 showed our own reasoning against it was backwards.
> 6. Cluster-residual reversal. **FELL** — net moves −1.28 → −0.80%/mo, still 80 bp under water,
>    and correlation clusters give a 0.02 out-of-sample spread in small caps, which is our case.
> 7. Closed-end fund discount. **FELL** — Flynn ran the exact hedged trade on 462 CEFs, zero
>    significant alphas, and the edge is front-loaded into month one, killing the "slow" thesis.
> 8. Lead–lag between size cohorts. **DEAD** — measured into a decile averaging $47m cap.
> 9. **Geographic lead–lag** (co-HQ, different sectors), 5–6%/yr, **explicitly unrelated to size,
>    volume and coverage** — the one liquid-name variant the X2 brief found real. **STANDING as a
>    lead**, monthly, sample ends 2013, no cost test in the paper.
>
> **INDICATORS / DATA ROUTES**
> 10. Short interest and days-to-cover. **FELL** — borrow fee takes 162 anomalies from +0.14%/mo
>     gross to −0.01% net, and free FINRA exchange-listed data starts June 2021.
> 11. **FINRA daily short-sale volume + the SEC FTD file** — the replacement route the N1 brief
>     found: one-day lag, point-in-time, consolidated from 2018-08, and **the FTD file carries
>     CUSIP so it doubles as a delisted-symbol crosswalk.** **STANDING as an input, not a signal.**
>
> **Ranked for a next step: #4, then #5, then #1.**
>
> **ALL ELEVEN ARE RECORDED AS LEADS WITH FULL ANATOMY** — the quantity, why it is not in the
> catalogue, the mechanism, the data, **the premise number that kills it**, and the honest risk —
> in [the scan record](../research/the-negative-space-scan.md) **§§3–7** for the original seven
> and **§9b** for the four the briefs surfaced. **§8's scored table carries all eleven**, with the
> seven axis scores **deliberately left unrevised** so the scan's own calibration can be audited
> against what the literature said. **That audit is unflattering and is recorded there: the score
> did not predict the outcome** — C1 scored lowest of seven and now ranks first, while K1 and N1
> scored 17 and both fell hard. **The axis that failed was `KILL`, and it was measuring my
> knowledge rather than the lead.**
>
> **The three findings that outlive the scan, and each was RE-MEASURED here rather than quoted:**
>
> 1. **[FINDINGS §59](../FINDINGS.md) — a best-of-N floor prices SELECTION and is blind to
>    SIGN-FITTING.** At k=16 a composite of **pure noise** clears the selection floor by **+1.28**
>    (2.95 vs 4.23). **Pre-declaring every sign in writing is worth a factor of ~2 in the hurdle
>    (4.23 → 1.65) for no computation** — the cheapest hurdle reduction on offer here. The D395
>    floor is *not* wrong; it must be **extended** wherever a construction orients its own
>    components in sample.
> 2. **[FINDINGS §60](../FINDINGS.md) — `etf_wide_daily_raw` IS NOT AN ETF FIXTURE.** **≥27.2%
>    closed-end funds** and **23 of its 24 deaths are fund wind-ups**, on a fixture **D382, D384
>    and D385 already ran on**. Their P&L used total return and is unaffected; what is affected is
>    anything reading `closes` as a **level**. **A metadata correction and any re-read is the
>    principal's call** — nothing was edited.
> 3. **D280's own gloss was backwards.** Orthogonality **multiplies** detectability by `√k`
>    (3.7–4.0× for the OHLC family against 1.69× for the nine price scores). The empirical part of
>    D280 stands; **the inference that independence makes combination hopeless is withdrawn.**
>
> **The leads, after the evidence.** **C1** (combining the 16 OHLC terms) **rose from last to
> first** — it now has a nameable form and a concrete hurdle. **X2 is dead** on measurement.
> **K1, N1, V1 and X1 all fell hard**, each on a specific published quantity, not a vibe.
> **R1 is [D404](../decisions/D404-the-cross-asset-state.md), pre-registered and amended.**
>
> **One construction surfaced that is NOT ours and has never been tested here:** two agents that
> never communicated converged on **industry-relative reversal in liquid names with a
> low-volatility screen** (+0.31%/mo, t=2.73, value-weighted, large-cap) as the only cost-surviving
> thing in the area — **and in both accounts it is the COST FILTER doing the rescuing, not the
> residualisation.** It would need its own pre-registration.
>
> **The quarantine rule paid for itself immediately: the brief that read most confidently (R1's)
> was the one whose two headline construction claims did NOT survive measurement.** Treat an
> enthusiastic brief with more suspicion than a damning one.

> ### 0d0b. ROUND 2 — SIX NEW TERRITORIES, ALL SIX BRIEFS IN, 2026-09-09
>
> **[`docs/research/the-forced-seller-and-the-cost-wall.md`](../research/the-forced-seller-and-the-cost-wall.md)**
> (`335fcc0`, completed `20a083a`). Territories and the exclusion list that kept round 2 off round
> 1's ground: [`working/leads2/README.md`](../../working/leads2/README.md) (`f31535d`).
>
> **THE SAME SHAPE AS ROUND 1: the most valuable returns are not leads.** Four of the six most
> consequential findings are method, data or cost.
>
> 1. **THE HOUSE SPREAD ESTIMATOR IS BIASED THE WRONG WAY.** `CLAUDE.md` mandates Corwin–Schultz;
>    **Ardia–Guidotti–Kroencke (JFE 2024) find CS UNDERESTIMATES effective spreads for small,
>    illiquid stocks** — our tail. **D285's 33.8 bp/side may be a FLOOR, not an estimate**, which
>    would make every breakeven in the record more lenient than it looks. **EDGE is a closed-form
>    drop-in on the same OHLC inputs (`bidask` on PyPI). Recompute D285 under EDGE FIRST — it sets
>    the SIGN of every cost conclusion downstream.** Not computed; re-opening D285 is the
>    principal's call.
> 2. **A CLOSE-DECIDED BOOK CANNOT FILL AT THAT CLOSE.** NYSE MOC/LOC hard cut-off **3:50 pm**
>    (Nasdaq MOC 3:55, LOC 3:58). A constraint on construction, not a preference.
> 3. **THE SPIN-OFF DEFECT HAS A NAMED FIX.** The correct adjustment is a multiplicative step on
>    all PRIOR bars, `f = (P_cum − r·P_child)/P_cum` — **date-dependent, which is exactly why a
>    scalar `raw_price_factor` cannot fix it**; the child has no pre-WI history at all. **Vendors
>    log spin-off factors in the SPLIT table, so a distribution ratio read as a split ratio shifts
>    the series by a clean integer — that is the 5× shape.**
> 4. **THE SURVIVORS-ONLY IDENTIFIER TRAP, TWICE.** `company_tickers.json` and Wikipedia's
>    `List of S&P 500 companies` are both survivors-only. **The free fix: `ISSUERTRADINGSYMBOL` is
>    NOT NULL inside every Form 4**, so dead names carry their own point-in-time ticker forever.
>    Join on `(ticker, date-in-listing-interval)`.
>
> **The four signal territories, none closed.** `F1` index reconstitution — **my premise was
> INVERTED**: large-and-liquid is where the effect is dead (S&P 500 adds 7.4% → 0.3%), and where it
> survives (SmallCap 600, MidCap, Russell 2000) is where our per-share cost is worst; **but the
> 500's zero is a composition artefact — direct adds still ran +5.40%**, and **deletions of names
> that DELIST are unpublished because every study drops them, which a dead-inclusive fixture is the
> right instrument for.** `F2` insiders — data excellent, **no cost-honest post-2010 survival**;
> the one positive assumes 10 bp/side against our measured 33.8. `F3` earnings — PEAD dead outside
> microcaps since 2006, premium's published US window **ends 2004**, **but its timing split (34.6%
> pre-open / 45.4% post-close, four corroborating sources) independently corroborates D280's
> overnight finding** — and carries a day-0 lag hazard `[L]`. `F6` supply events — **three of four
> families resolve overnight, so daily bars are a bar late by construction**; only buyback
> *execution*, as a **state**, is recommended.
>
> **`F5` cost: 0.5–1.5 bp/side saveable, not 5.** Published price-improvement numbers **do not
> reach an auction-only book** — IBKR takes no order-flow payment on On Open/On Close and the
> auction print is a full half-spread, **so our cost model is CORRECT there**. One actionable
> change: **Fixed → Tiered**, and it corrects a recorded number — **the minimum binds on a SHARE
> COUNT (200 Fixed, 100 Tiered), not on "$2,100 notional"**. **The 1.92 bp intraday cell still
> loses at a zero spread.** **Dated freebie: IBKR's first amended-Rule-605 broker-level report,
> with E/Q by order size, is due published before end-September 2026.**
>
> **TWO OF MY OWN COMMISSIONING PREMISES WERE WRONG**: the 2023 granular buyback rule was **vacated
> by the Fifth Circuit 2023-12-19** before producing data (our span is Item 703 — monthly, HTML,
> untagged, 40–45 days late), and index flow does not live in large liquid names.
>
> ### 0d0c. ROUND 3 — PREPARED, NOT COMMISSIONED
>
> **[`working/leads3/README.md`](../../working/leads3/README.md)** (`2e89d37`, withdrawal `4f3e2e3`).
> Six lanes written up; **no agent dispatched**, deliberately — round 2's returns had to extend the
> exclusion list first. **`G1`** fund/ETF flows as the forced seller · **`G2`** the death process,
> which [`FINDINGS.md`](../FINDINGS.md) §60's own rule demands and which `F1` independently
> pointed at · **`G3`** halts/LULD, where D343 met the event as 4.4% of D342's P&L and excluded it
> as hygiene · **`G4`** 13D/13G · **`G5`** the revenue side of a long book · **`G6`** documented
> defects in data we own. **`G2` and `G3` are route (b)** — the first round to ask it; round 2's
> four signal lanes were all route (a), which was my omission.
>
> ### 0d1. D404 — THE CROSS-ASSET STATE, PRE-REGISTERED AND AMENDED, RUNNER DOES NOT EXIST
>
> **[D404](../decisions/D404-the-cross-asset-state.md)** (`fd4275e`, amended `c88673a`). All 52
> catalogue scores are functions of one name's own OHLCV; the one exception builds its market
> return from the panel's own cross-section. **No study has ever gated an equity book on another
> asset class.** The two fixtures' grids are **identical bar for bar** (4,187 dates), so the join
> needs no fetch — **the whole of the new code is the `raw` array.**
>
> **Its second question is why it exists:** D389's factor is **98.5% unexplained in arm B** and all
> four tested candidates were *internal* to the book's machinery. `data/d376_series.npz` already
> holds the 500-book matrix on the same grid, so testing a market-level state against it is nearly
> free.
>
> **§12a amendment, before the runner exists.** One alleged defect **false** (drift −0.92%/yr, not
> 2–5%, and the imbalance runs the other way), one **confirmed** (`(XLU+XLP)/(XLY+XLK)` is a sum of
> share prices; a synthetic split moves it 0.338 log units), and **one found that neither party
> had: a trailing-median rule on a TRENDING series is a TREND RULE, not a state classifier.**
> `DEFENSIVE` sits on one side 71% of the time and equal-weighting does not fix it. **A new `[BAL]`
> assertion fails any state outside 40–60%; `DEFENSIVE` fails it today.**
>
> **Recorded, not adopted:** the literature places credit/curve predictability at **quarters to
> years**, not the 20 days D404 inherited. None of those papers has been read here. **The runner
> must report the whole horizon curve h ∈ {5…252}, and if h=20 is the PEAK that is an overfitting
> flag, not a confirmation.**

**TWO AVENUES WERE CLOSED BY THE PRINCIPAL ON 2026-09-09 —
[D401](../decisions/D401-the-principal-closes-the-winners-dip-and-the-15m-structure.md):
the WINNERS' DIP and the 15-MINUTE TIME-SERIES STRUCTURE SCREEN.** Both are shut and neither will be
reopened. **What outlives them and must not be closed with them:** D378's entry-timing finding stands
as truth (T1 at **+26.9 SE**, largest-trade-removed gate at **+9.8 SE**); D383's **`n_eff` instruments
= 2.17 of 57 at 15 minutes** is a property of the universe and constrains any future intraday design;
and D383's **bp/bar RISES with hold** at 15m, opposite to daily, so a successor assuming daily
front-loading transfers would be wrong. D383's 111 uncorrected-p95 survivors — a volatility-timing
tilt with an undeclared direction — remain **recorded and unclaimed**, and closing the avenue does not
license mining them without a fresh pre-registration.

**ONE decision remains the principal's and blocks nothing else:** whether to **re-base past records**
onto D377's H1 hedge (D377 §4 argues not — the benefit is 0.032 on a 0.47 floor).

1. ~~D383 is a debt~~ — **SETTLED. [D383 RESULT](../decisions/D383-RESULT-the-time-series-screen-clears-nothing-and-its-ten.md)
   (`c5dc05a`). 0 OF 572 CELLS CLEAR**, and the best cell at every hold sits **−0.06 to −0.95 SE of
   the floor's own CENTRE** — on the median, not near the bar. **§8's abandon condition is met; the
   close is the principal's.**
   - **THE PRE-REGISTRATION CAUGHT EXACTLY WHAT IT WAS WRITTEN FOR.** Ten cells clear on the primary
     PER-TRADE statistic and **all ten are buy-and-hold** — hold 78, exposure 1.000, 57 trades on 57
     names, median run **37,643 of 37,648** available bars, **`n_eff` trades = 1**, excess over B&H at
     matched exposure **0.00%**. That is the confound §5.1 nominated bp-per-bar to catch: **48 of 143
     hold-78 cells run >10× nominal against 0 of 143 at hold 26**, the hold nominated primary in
     advance. Choosing the primary statistic *and* the primary hold before seeing anything is what
     separated the artefact from the result.
   - **`n_eff` INSTRUMENTS = 2.17 OF 57 AT 15 MINUTES** — first measurement at this frequency, and it
     confirms FINDINGS §4's ~2.2 daily figure. **26× more sampling buys no breadth.** This constrains
     every intraday study this programme might design.
   - **Q3 falsified in an interesting direction: bp/bar RISES with hold at 15m** — the edge is **not**
     front-loaded, opposite to D378 daily. Q2 also fell (32 interior humps, not flat).
   - Recorded but **not claimed**: 111 of 572 beat their own *uncorrected* p95, and at the primary hold
     they are one coherent family — the low tail of `park_vol_21` / `gk_minus_cc` / `range_frac`, a
     volatility-timing tilt with an undeclared direction and confounded with spread.

1b. **THE PROP INSTRUMENT IS PRICED — [D386](../decisions/D386-the-prop-account-is-worth-its-buffer.md),
   22 lanes, `docs/research/Prop-Firm-080926/`.** Read
   [00-SYNTHESIS](../research/Prop-Firm-080926/00-SYNTHESIS.md),
   [23-method-lessons](../research/Prop-Firm-080926/23-method-lessons.md) and
   [24-candidate-ledger-both-books](../research/Prop-Firm-080926/24-candidate-ledger-both-books.md).
   - **At zero edge `E[extracted] = the drawdown buffer`, exactly** (optional stopping), so **the
     payout ladder is decoration** and **you cannot extract more in expectation than the amount they
     let you lose**. **94.7% of evaluations return exactly $0.**
   - **The whole question reduces to CALMAR ≥ 18.9 ON OPEN EQUITY**, leverage-invariant — verified on
     one manager's own 1× and 1.5× versions of the same book. **Best audited intraday CME programme:
     1.07. Best in a 199-programme database: 5.88.**
   - **A Calmar above 18 is a property of RECORD LENGTH, not strategy** — every Collective2 system ≥18
     is under 370 days old, zero of 37 older than two years. **That is a screening rule for both books.**
   - **The scissors close on LONG WINDOWS, not small edges.** Every rejection is a *size* rejection;
     cost is 15–20% of gross and never binding. **The binding variable is the hold.**
   - **D379 gains an uncomputed term**: the barrier is administered against a market that **can suspend
     your exit** (CME Velocity Logic halts on a rolling-millisecond move), and a floor on open equity
     keeps moving through those windows.
   - **The one quantity nobody publishes, confirmed five independent ways: MAE within the holding
     window, on open equity.** Absent from the literature, the code, the published drawdowns, the best
     retail record, and every verified CTA database.

1c. **R11's RE-COSTING COROLLARY IS DISCHARGED FOR ONE CONSTRUCTION — [D400](../decisions/D400-RESULT-the-D163-recost.md)
   (`7e39fe3`, renumbered D389 -> D390 -> D400).** D163's *"~315% of capital a year in fees"* is a **crypto taker
   number and is wrong by ~400×** at futures commission (0.786%/yr) — **but the closure survives on
   SIGNAL, not cost.** Gross first: BTC Design B at 15m is **−1.4 bp/trade at the 2.4th percentile of
   its own null**, below its p05. **Left to the principal: the 30m–2h band**, where cost moves three
   rungs per symbol from ruin to profit and the nulls disagree (ETH 1h clears at 96.4, BTC 1h fails at
   79.8, both fail at 2h). **R11 itself was NOT edited** — a standing-rule change is the principal's.

2. **D336's quoted-spread pull — the highest-value item in the programme, and it needs the principal's TWS
   session.** D378 put the entry-timing increment at **0.19–0.47× a round trip under PUB** and
   **0.50–1.21× under PB**. **The same measurement decides whether that effect is deployable and
   whether the incumbent book is positive at all** (D332: PUB post-D333 is −12.68 bp/bar). Nothing
   else on this list changes as many conclusions.
3. ~~Where does the remaining 0.44 correlation floor come from?~~ — **ANSWERED, and the answer is a
   sharp negative. [D389](../decisions/D389-RESULT-the-floor-is-ONE-factor-and-none-of-the-four-candidates.md).**
   **It is ONE factor** — PC1 reproduces the pairwise rho to three decimals (0.449 vs 0.449), PC2 is
   0.006, all 500 books load the same sign. **And it is none of the four candidates**: slot mechanics
   0.029, equal-weighting 0.031, eligibility floor 0.052, shared hedge term likewise. **Unattributed:
   85% in A-prime, 98.5% in B.**
   - **The arms disagree by 9x and backwards.** A-prime (same names) correlates 0.480 with the market;
     **B (same days) only 0.138 and with nothing else.** B is the arm gate 1d-prime is calibrated
     against, and its floor is **98.5% unexplained**.
   - **Gate 1d-prime needs NO restating.** The floor is not a scorer artefact — 1/nlive scores 0.031.
   - **Where a successor should look:** the factor lives in **which days get traded**, not in the
     market on them — i.e. the **entry-condition distribution**, which no driver here could reach.

4. ~~Exit timing~~ — **DONE. [D380](../decisions/D380-RESULT-no-exit-overlay-beats-not-cutting-and-R7s-control.md)
   (`43db0df`) and [D381](../decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange.md)
   (`eac6650`). NINE ARMS, NONE BEATS HOLDING TO THE CAP** — on **gross mean per trade**, which is the
   unconstrained objective. D380's first pair were mis-scaled (±200 bp fired on ~80% of trades, caught
   by the principal); D381 re-ran them at declared **fire rates** of 5/10/20% and every arm still lost.
   - **A stop is a LATE trigger by construction.** Don't cut +160.55 · cut the worst 5% at a **random**
     bar **+226.52** · cut them at −3,229 **+142.79**. The threshold is only reached *after* the
     adverse move, and these losers recover.
   - **The median/mean exchange rate is fixed at ~0.44** and flat from a 20% to an 81% fire rate. The
     dose is free; the price is not. **A better win rate is available and costs about two basis points
     of mean for every four of median.**
   - **The R7 lessons are now in [RULES.md](../RULES.md) under R7** and bind future overlay studies:
     report against the baseline as well as the control; the control's difficulty is inherited from
     the rule's trade selection; the control is a null and never a policy.
   - **NOT queued, deliberately.** Under a hard drawdown limit the criterion is return per unit of
     drawdown rather than mean, and an overlay can win there while losing here (D381 §5a gives each
     arm's exact drawdown hurdle). **That is for an individual strategy and book to assess at its own
     test stage** — the principle is recorded under R7 and is not being pursued on this construction.
5. **A genuinely new construction**, designed from in-sample reasoning only and pre-registered before
   anything is fetched. **It must not select inside a narrow cohort** — [FINDINGS §52](../FINDINGS.md)
   closes winner-selection variants as a family.
   - **AND IT MUST HAVE ITS PERSISTENT-SELECTOR CONTROL DESIGNED IN AT PRE-REGISTRATION.** The density
     line (D384 → D388) beat a path-shuffle null at `p` = 7.2e-11 and a rotated-density null at
     nothing. **Beating a path shuffle is nearly free.** Four of five studies there would have
     reported a headline without the A′-equivalent.
   - **The most promising open lead in the programme is [FINDINGS §57](../FINDINGS.md)'s**: two
     unrelated books co-move at 0.476 and **98.5% of it is unexplained**, and the disagreement between
     the arms says the cause is **which days get traded** — the entry-condition distribution — not the
     market on them. That is a target, not a construction, and nothing has been built against it.
6. **P5 should be computed** on anything reaching the prop track, ahead of the other uncomputed legs
   (D379 §6). **P3 and P4 remain uncomputed** and under R6 that is a live defect.
7. **D371's 0.8% breadth failure is NOT retroactively cleared.** H4′ is per-study; that book lived in
   a different universe at roughly half the breadth and **its A′ distribution has never been
   computed.** Nothing material changes — but the record should not be read as saying its breadth
   was bad.
8. **The short side** (`hist_L` k=40, D357) lost its clean fixture when D371 spent holdout #1 on
   momentum. It needs holdout #2 or a later slice.
9. **C1's size sweep is unfinished** — extend below 0.48× and locate the value peak against D379 §4's
   ladder cap. Needs MyFundedFutures' payout ladder terms, which no record holds.
10. ~~Restate P1 as a sizing rule~~ — **DONE 2026-09-08**, R11.
11. ~~The D373 avenue~~ — retired, reopened, tested; **status is the principal's** (see §0 table).
12. ~~Audit the rest of the hurdle set~~ — **DONE, D375.**
13. ~~Make the breadth hurdles breadth-relative~~ — **DONE, D374** (H4′) and **D376** (1d′).

**The breadth test the 2026-09-07 handoff ranked first was dropped, with the principal's agreement.**
It targets a retired object, and the H5 mis-specification it was partly meant to expose is a
definition fix rather than an empirical question.

---

## 0d2. PARKED — SUPPLY AND DEMAND: THE IDEAS NOT TAKEN, 2026-09-09

**D403 was closed by the principal** — *"this construction is dead, I don't think this accurately
captures supply and demand."* The wick-stack potential map is finished and will not be reopened.
Its durable findings are in its own record; what follows is the design work that came out of the
close and is **not** spent.

**THE DIAGNOSIS THAT OUTLIVES D403, and it explains all six price-level failures at once:**

> **A wick is evidence that interest was ABSORBED, not that it REMAINS.** If price spiked to 110 and
> came back, the sellers at 110 were filled — the zone is spent. The same is true of a volume node
> (TERRAIN S1), a swing band (S5), a signed inventory field (S6), a flipped level (D211), a fair
> value gap, and D403's potential. Every one is a trace of trading that already completed, read as a
> forecast of trading still to come.

And the mechanical corollary that predicts the failure **before** a study is built: **all six maps
are pure functions of the past price path.** That is exactly why the rotation control kills them —
rotating preserves the path and destroys only the alignment, and the alignment carries nothing. **Any
candidate that is another function of OHLC alone will die the same way.** Require of a seventh that
it carry information the price path cannot.

**THE PRINCIPAL CHOSE (2) ON 2026-09-09 and it is drafted, not committed** — see
`docs/decisions/DRAFT-capital-gains-overhang.md`, uncommitted, **no decision number taken** (the
three-command procedure runs at commit time, not before). The other three are parked here:

**(1) RESTING LIQUIDITY — the order book.** Literally supply and demand, and the honest ceiling on
every approximation below it. **Blocked, not rejected.** D336's quoted-spread pull needs the
principal's TWS session and is top-of-book only; `scripts/d364_databento_equity_plan.py` is an
arithmetic-only cost plan with no submit path. **If the TWS blocker ever clears, this outranks
everything in this section.**

**(3) OPTIONS OPEN INTEREST / DEALER GAMMA.** Genuinely forward-looking and size-carrying — resting
*obligations* at specific strikes, which is the property every price-history map lacks. Nothing in the
repo. Alpha Vantage serves `HISTORICAL_OPTIONS` on the existing key, so it is reachable at request
cost and no new vendor. **Do not spend this until (2) has reported** — it is a real acquisition and
(2) tests the same "unfilled interest" thesis for free.

**(4) EXECUTION ANCHORS — VWAP and the closing auction.** Weak as *zones*, but they hold the one
property nothing else here does: somebody is **obliged** to trade there. `scripts/d364_auction_bound.py`
already documents the 1-minute call shape. Cheapest of the four; lowest ceiling.

**UPDATE 2026-09-10:** (2) the capital-gains overhang ran as D405 and **abandoned at stage 0** (the
overhang is momentum); (3) options open-interest density ran as D406 and **failed its bar**; the
departure-zone line (D412–D433, above) was the seventh price-path map and died out of sample twice.
**Never tested in this repo, and each carries information the price path cannot:** short interest /
days-to-cover as a *signal* (FINRA bi-monthly, public), insider transactions, share issuance /
buybacks / lockup expiries (the literal supply of shares), 13F holdings changes, index-inclusion
flows. Zero decision files on any of them.

**MULTIPLICITY: any of these is look #7 on price-level maps.** The R13 ledger carries 259 terrain
looks and 86 structure looks in, and D403 makes six programmes with six written closes. **None of
them paid.** That base rate is the reason (2) is drafted as a stage-0 discriminator with an abandon
condition rather than as a study with a sweep.

---

## 0e. THE LESSON THAT OUTRANKS BOTH RESULTS

**In-sample null strength does not forecast out-of-sample survival.** The momentum construction
cleared its time rotation at **164 standard errors with zero of 10,000 draws beating it**, cleared a
best-of-ten multiplicity control, and cleared a symmetric winner-removal test. **It still failed.**
Permutation nulls test whether a pattern is real *in the data you have*; they say nothing about
whether it recurs.

Three studies went into making those in-sample verdicts precise (D369) and unbiased (D370). Both
were necessary. Neither was sufficient.

**And the successor built to replace it was the same book.** D373's H7 says a construction can be
re-derived from different-sounding premises and still hold 70% of the same name-bars. **Measure
independence on day one, not at stage 5.**

**Two more, earned across D374–D377 and worth as much as the above:**

**A threshold you have never calibrated is not a hurdle, it is a guess.** H4 was unreachable by a
factor of four and failed the most diversified book in its own null. Gate 1d was measuring pool
overlap. Both had adjudicated real studies. **The cheap test — "has anything ever passed this, and
what does a null draw score?" — takes minutes and should run when the hurdle is written, not five
studies later.**

**Direction right, scale wrong — four times running.** D374, D376, D377 and D373's own predictions
all had the sign of the effect correct and the magnitude badly off, always in the same direction:
**I under-estimate how much of these books is structure and over-estimate how much a correction will
move.** Weight point estimates accordingly.

---

## 0f. TRAPS, 2026-09-07 — all cost real time

- **Persist before you render.** D371's first execution computed its evidence and lost the JSON to a
  `KeyError` in the print loop; the console had printed only booleans. D373 hit the *same shape*
  twice more (arm C's dict differs from `verdict()`'s) and lost nothing, because the artifact is
  written first. **Keep that ordering.**
- **Three D373 hurdles reported the wrong verdict from lookup faults, not from bad data.** H4 read
  `top_name_share` by `"top1"` when it is keyed by `int`, so it returned UNRESOLVED with two null
  legs; H7 was stored with no verdict and rendered as `-`, entering no roll-up. **A hurdle that
  cannot fail loudly is as bad as no hurdle** — check the roll-up actually consumes it.
- **Cumulative s/draw in a progress log is not the marginal rate.** D373's five parts printed 7.09
  s/draw at draw 130 and 5.73 at draw 400; the marginal rate was ~3.9 throughout. The numerator
  carries one-time prep. **Estimate remaining time from the last two lines, not the running mean.**
- **`_m_start_of` took the bar after the LAST undefined market bar** — correct only when every gap is
  a warm-up prefix. Holdout #1's 3 interior holiday bars gave `m_start` 4,125 of 4,190, **a 65-bar
  sample with every check green.** Fixed `ce2947c`.
- **`V58.pct_of` memoises by score NAME only.** A process touching two fixtures gets the **wrong**
  percentile grid for the second. Clear `V58._PCT` between re-points.
- **`np.savez` appends `.npz`** unless the name already ends in it; **`np.load` returns a lazy
  handle** Windows will not let you replace until closed.
- **Backticks in `git commit -m` are command substitution.** Use `-F <file>` written with the Write
  tool — the heredoc hook blocks heredocs for exactly this reason.
- **Never pipe a background command through `tail`/`grep`** — the pipe buffers and progress is
  invisible. Redirect to `temp/<job>.log` and tail the file.

---

## 0g. STANDING CONSTRAINTS FROM THE PRINCIPAL — these bind

- **R15: a signal is a positive GROSS mean per trade above its nulls.** Costs and confluences come
  later. **ONLY THE PRINCIPAL CLOSES A RESEARCH AVENUE.**
- **No holdout read without explicit, specific authorisation.**
- **Costs are IBKR's official costs.**
- **No subagents unless the work is genuinely parallel.** Build and run sequential work directly.
- **R8:** pre-registration committed *before* the runner exists; the result committed **separately**.
- **Clearing a study's hurdles does not admit a strategy.** R8 needs a separate pre-registered
  out-of-sample test on a fixture it has never seen; the prop book also needs hurdle P (R11), all six.

---

## 0h. WHERE TO READ

| | |
|---|---|
| how to work here | `CLAUDE.md` |
| rules | `docs/RULES.md` — **R8, R13, R14 + amendments, R15** |
| substantive truth | `docs/FINDINGS.md` — **§§46–51** newest |
| where the programme stands, D285→D364 | `docs/STACK.md` **§0, §§32–42, 40a**; **§7 is what earlier versions got wrong** |
| the momentum session | `docs/HANDOFF-2026-09-07-momentum-holdout.md`, `docs/decisions/D366…D371*` |
| the holdout read itself | `data/d371_read.json`; construction frozen in `data/d371_construction.json` |
| the last study | `docs/decisions/D373*` · `data/d373_winners_dip_long.json`, `data/d373_posthoc.json` |
| the two books | `docs/BOOK.md` (S1, S2), `docs/BOOK_PROP.md` (**admitted arms: none**) |

---
---

# OLDER STRATA — newest first

**Everything below predates 2026-09-05 and describes the short-side and futures work. It is kept for
the traps and the standing data constraints, not for its state claims.** Where it disagrees with §0
above, §0 wins.

---


## THE 2026-09-02 SESSION — D264 → D284, the directional shorts

*Superseded as a state file by §0 above; the closures and traps below still stand.*

### 0-2026-09-02. THE ONE-LINE STATE, AS IT WAS

**EIGHT CONSTRUCTIONS, FIVE UNIVERSES, TWO FREQUENCIES, BOTH DIRECTIONS. NOTHING SURVIVES.**

| study | construction | outcome |
|---|---|---|
| D264-D278 | the intraday single-name short, every lever | closed on `2c` |
| [D279](../decisions/D279-the-concentrated-short-on-dead-inclusive-names.md) | daily concentrated, top-N by score | **0 of 14.** Its first RESULT reported two survivors and **they were LOOK-AHEAD. Withdrawn.** |
| [D281](../decisions/D281-the-unfiltered-ranking.md) | rank the whole universe | **0 of 10**, and worse than random |
| [D282](../decisions/D282-the-overnight-only-short.md) | overnight-only, ascending | **0 of 19.** Loses 24 bp/night |
| [D283](../decisions/D283-the-descending-ranking.md) | descending, both tails | **0 of 26.** Symmetry fails BY SIGN |
| [D284](../decisions/D284-the-overnight-long.md) | the overnight LONG | **0 of 13.** Clears `2c` at 2.41x and dies on SPREAD |

Everything intraday closed on one condition, in which the trade count cancels and hit rate never
appears:

```
mean move per trade  >=  2c        (the round-trip cost)
2c = 4.00 bp LOW - 8.42 bp ALL - 12.84 bp HIGH
```

**Six signal families, three input families, a volume profile three ways, two exit levers, a
300-cell mine and a 16-name instrument holdout all failed that bar.** Nothing failed for want of a
null.

**D279 closed on something different and worse: it never reached the cost question.** Re-scored at
zero fees, zero borrow and zero rf, `S1_short|top25` posts **-0.432 Sharpe and -0.26% CAGR**. Every
cell in the grid has a negative net CAGR, every breakeven borrow rate is negative, and the
best-of-14 floor is **-0.178** against a best cell of **-0.337**. **On the daily fixture the binding
constraint is the drift, not the toll.**

**What is live is one pre-registered study and one untouched branch.** See section 5.

## 1. PICK THIS UP FIRST - the D279 look-ahead, because the lesson is a runner lesson

**`run_concentrated_short.top_n` ranked the qualifying names with `score[:, t]` - `hist_L` computed
from the close of the very bar the position was about to be paid for - and then held that position
through bar t's return.**

`hold_book` lags the qualifying MASK correctly and always did (`p[:, 1:] = mask[:, :-1]`), so
**which names QUALIFIED was honest and [D256](../decisions/D256-the-book-on-single-names.md) is
untouched.** What was contaminated is **which N of the qualifiers were HELD** - which is exactly the
quantity hurdle C exists to test.

```
corr(hist_L at t,   hist_L at t-1)   +0.9805      the score barely moves when lagged
corr(hist_L at t,   return at t)     +0.0737      ranking on this is peeking
corr(hist_L at t-1, return at t)     -0.0103      the tradeable version

top25   UNLAGGED  +1.43% CAGR  +2.250 SR      LAGGED  -0.32%  -0.638
top50   UNLAGGED  +2.05% CAGR  +1.865 SR      LAGGED  -0.56%  -0.659
```

**THE LESSON, and it is new to the programme: a lagged position built from an UNLAGGED RANKING is
still look-ahead, and the base being correctly lagged is what hides it.** Every look-ahead guard we
own points at `hold_book`, and `hold_book` was right. The defect entered one layer above it, in a
function that *filters* an already-lagged book - a place nothing was watching, because filtering a
lagged book feels like it cannot introduce a lag error. **[R9](../RULES.md#r9)'s third appearance**
after D224 and D248, and the second on `hist_L` specifically.

**The fix now lives INSIDE `top_n`**, not at the call site, because three other modules call it.
**One consequence:** re-running `scripts/d279_lookahead_check.py` no longer reproduces its own
UNLAGGED column - its two arms have become lag-1 and lag-2. The correlations still reproduce; the
UNLAGGED Sharpes are only reproducible against the pre-fix runner and are quoted from the withdrawn
artefact, kept as `data/d279_concentrated_summary.WITHDRAWN_lookahead.json`.

**Three further caveats in D279's corrected RESULT, all still live for anything that inherits this
construction:**

1. **Hurdle H is FAILED for that study, not passed.** `S1_short|all` scores the **100th percentile
   on both legs with -0.757 Sharpe and -2.45% CAGR**; seven of fourteen cells clear it and all
   fourteen lose money. [R7](../RULES.md#r7)'s corollary applies. **Do not reuse that null
   unmodified.**
2. **Hurdle C is scored against ONE random draw, not a distribution.** The same control cell scored
   **-1.528** in the runner and **-1.633** in the decomposition; at S2/N=50 the gap is 0.16 Sharpe.
   `rotation_nulls` takes 300 draws and C took one.
3. **E' degenerates on a rotating book.** `top25` scored **28.00 on 28 names** - the correlation
   matrix is the identity, because almost no *pair* shares the 250-bar overlap minimum. It silently
   became "how many names were held >=250 bars", on which `top10` scores **1.00 on one name**. **The
   runner still has this defect**; `data/d279_concentrated_summary.json` carries an
   `Eprime_panel_defect` flag on every cell and the honest values are in
   `data/d279_eprime_corrected.log`.

## 1a. THE EDGE IS ENTIRELY OVERNIGHT - [D280](../decisions/D280-the-forecast-precheck.md)

**TESTED FOR STALE OPENING PRINTS 2026-09-09 AND IT SURVIVED — [D402](../decisions/D402-RESULT-the-overnight-gap-survives-and-the-contamination-is.md).**
The gap is formed entirely from the vendor open and that had never been checked. **17.6% of
out-of-sample bars DO carry a detectable print artefact** — `open == prior close` exactly on
5.84% — with a **-0.1564** gap-to-intraday reversal confined to them and **+0.0082** on the rest.
**But the edge is not there:** on CLEAN bars the IC is **-0.01746 (1.14x the committed value)**,
and it is **1.8x STRONGER in the most liquid $-volume quintile than the thinnest**. A print
artefact must concentrate where prints are unreliable; this concentrates where they are most
reliable. **The measurement stands. The money question below is untouched.**


**D280 is a MEASUREMENT record - it scores no cell, ranks no name and proposes no rule, and its
ledger is 0.** It ran BEFORE any pre-registration because it decides whether there is anything to
pre-register.

**THE HEADLINE, and it is the largest result of the D264-D280 sequence.** Cross-sectional IC of the
R9-lagged `hist_L` against each PART of the next bar, out of sample. Negative = tradeable for a
short:

```
universe   target       mean IC       t
ALL        total        -0.00524   -1.79
ALL        gap          -0.01531   -4.71     <-- the edge
ALL        intraday     +0.00168   +0.65     <-- nothing
QUAL       total        +0.00462   +1.43
QUAL       gap          -0.01255   -3.45
QUAL       intraday     +0.00868   +2.85     <-- runs AGAINST the short
```

> **There is a real, correctly-signed OVERNIGHT edge and a wrong-signed INTRADAY move that cancels
> it. Close-to-close - the only quantity D256 and D279 ever measured - is the SUM OF THE TWO, which
> is why it read as noise.**

- **No intraday stop, target, partial exit or overlay can reach it**, and taking the position at the
  open to shed overnight risk discards the edge and keeps the leg that fights it. **Both branches
  close on one measurement.**
- **It is NOT ex-dividend drops** - the obvious confound, since `gap` is raw OHLC and a short OWES
  the dividend. Dividend-adjusted the IC is **-0.01498 (t -4.59)**; ex-dates excluded, **-0.01494**.
  Only 0.834% of bars go ex next session. **On those 216 bars the IC is -0.05197**, 3.4x the average,
  so the mechanism is real and localised - **charge dividends explicitly in any book built on this.**
- **AN IC IS NOT MONEY.** An overnight book trades a full round trip EVERY NIGHT - ~252/yr against
  ~17/yr for D279's ~15-day holds - so D265's bar (`mean move per trade >= 2c`, 10 bp at 5 bp/side)
  must be cleared **15x more often**. A rough prior, **not computed from these artefacts**, puts the
  per-night edge near 4 bp against that 10 bp toll. **D282 is pre-registered to measure it. Do not
  predict it.**

**THE STRUCTURAL FINDING, and it is the second thing to carry out of this session:**

> **D256 and D279 both filter on `hist_L < 0 & md_L >= 0` and then rank the survivors by `hist_L`
> again. The filter and the ranking are the SAME VARIABLE. The signal is spent by the time the
> ranking runs, and what remains inside the filtered set reverses.**

Cross-sectional IC - Spearman, within each bar, against the NEXT bar's return, out of sample:

```
hist_L over ALL live names       mean IC -0.00524   t -1.79   2,173 bars   correctly signed
hist_L over the QUALIFYING set   mean IC +0.00462   t +1.43   2,147 bars   WRONG SIGN
```

**That is the whole of why D279's ranking bought +0.203 gross Sharpe on a book sitting at -0.432.**

**What else D280 settled:**

- **The DEMA + velocity/acceleration/jerk extrapolation is dead.** It loses to naive persistence in
  **all 48** level comparisons, all nine delta comparisons and all nine range comparisons.
  Derivatives correct the smoother's own lag rather than forecasting; longer n is monotonically
  worse; jerk hurts in 8 of 12 cells (noise multiplier C(2k,k) = 20).
- **16 OHLC derivative terms carry 13.50-15.76 EFFECTIVE inputs**, not the sub-3 collapse predicted.
  **The intrabar axis is real, independent, and carries no predictive power** - the mirror image of
  D268's lesson, and it belongs beside it.
- **`open(t+1) := close(t)` is NOT free.** Median |gap| **0.5263%**, mean **0.9393%**,
  **|gap|/|body| = 0.515**. Range is separately predictable at correlation **+0.87** and
  persistence-of-range still beats the DEMA stack on MAE, so range is a sizing input at best.
- **Multiplicity: 165 statistics across five parts, 161 distinct.** The median largest |t| under a
  161-test null is **2.86**, so the best *extrapolation* result (**|t| 2.29**) is a best-of and is
  **not evidence**, and the only un-searched baseline (`hist_L` alone, all names, t **-1.79**) is not
  significant either. **The overnight numbers are the exception: |t| 4.71, 5.07 and 5.97 clear a
  best-of-161 correction comfortably**, and part 4's gap leg was declared in the script before it
  ran. **The t is small on 2.2M name-bars because n is 2,173 BARS** - the IC is computed within each
  bar and averaged.

## 2. WHAT WAS CLOSED, AND ON WHAT

| | closed by | on |
|---|---|---|
| S1 / S2 shorts, intraday, single names | D264 | 0 of 12 cells; commission alone beats the breakeven |
| entry timing | D265 | early entries are 1.57× the bar; whole-book +0.38%/yr |
| magnitude calibration, 9 price scores | D267 | 0 of 27; whole Q1–Q5 spread < one round trip |
| the consensus proposal | D268 | 2.87 effective inputs of 9; **RSI is trailing return at ρ +0.78** |
| volume as a third input | D270 | orthogonal at ρ 0.09, best cell 0.92× the bar |
| the volume profile, as an input | D272 | most orthogonal thing measured (ρ 0.085), 0 of 6 |
| the volume profile, as a travel estimator | D273 | travel is flat in room; the node is a distance |
| exits, time-based | D274 | **a random exit bar beats a fixed one** |
| change of character | D275 | legs run 182.7 bp median, the rule captures 0.57 bp |
| exits, structural | D276 | removing churn made it worse; exposure 47% → 4.5% killed it |
| the mine, 300 cells | D277 | best +0.392 against a best-of-300 floor of +0.605 |
| **all five in-sample winners** | **D278** | **every one reverses sign on 16 fresh names** |
| **the concentrated DAILY short** | **D279** | **0 of 14; `top25` is −0.432 Sharpe GROSS, so it loses before costs** |
| the DEMA derivative forecast | **D280** | loses to naive persistence in **all 48** level comparisons, all 9 delta, all 9 range |
| **intraday exit overlays on this construction** | **D280** | **the edge is entirely overnight** (gap IC −0.01531 t −4.71; intraday +0.00168 t +0.65) |
| taking the position at the open to shed overnight risk | **D280** | same measurement, reversed — it discards the edge and keeps the leg fighting it |

## 3. THE FIVE THINGS WORTH CARRYING

1. **The cost bar is `mean move per trade ≥ 2c`, and it is signal-independent.** The trade count
   cancels; hit rate never enters. Any future intraday construction should be screened on this
   first, for the cost of one measurement.
2. **Most technical indicators are monotone transforms of trailing return.** D268: nine scores,
   **2.87 effective inputs**; RSI ↔ macd_line at **+0.85**. "Several indicators agree" is usually
   one indicator agreeing with itself. `scripts/d268_score_independence.py` is the instrument.
3. **Overnight drift is a property of VOLATILITY, not of equities.** Low-vol names accrue it
   **intraday with the sign reversed** (+4.36% overnight vs +5.56% intraday); high-vol names run
   +13.81% vs −8.97%. D247's +8.59%/−0.36% is an average over instruments, not a constant. **This
   belongs in the wide extended-hours pre-registration before it runs.**
4. **A correlation on a continuous score does not survive to its tails.** ρ = −0.83 between
   `mass_imbalance` and `impulse_md` gave only **53% bar overlap** at the quintile extremes — and
   +0.392 against −0.481 Sharpe. I called them "near-identical" and was wrong.
5. **A LAGGED POSITION BUILT FROM AN UNLAGGED RANKING IS STILL LOOK-AHEAD, AND THE BASE BEING
   CORRECTLY LAGGED IS WHAT HIDES IT.** D279's `hold_book` shifted the qualifying mask by one bar
   and always did; `top_n` then chose *which N of the qualifiers to hold* on the unlagged score.
   **Every look-ahead guard this programme owns points at `hold_book`, and `hold_book` was right.**
   Anything that *filters* an already-lagged book is a place to check, precisely because it feels
   like it cannot introduce a lag error. **A second, independent re-derivation of the held set from
   `score[:, t-1]` — not a call into the same function — is the cheap guard**, and D281's runner
   is the first to carry one.

## 4. R13 IS NEW AND IT CHANGES HOW LEDGERS ARE COUNTED

**[R13](../RULES.md#r13): a ledger is scoped to a hypothesis and transfers only where it shaped
the search.** Written after the principal pushed back twice, correctly, on inherited counts.

- terrain's **259** is disclosed, not carried (D272)
- the ETF programme's **45,783** is disclosed, not carried — **D218 scopes its own floor to "this
  fixture"**, meaning 57 ETFs daily
- what carries into the single-name work is **~118**, because D264–D276 built the bases and scores

**D247–D276 keep the older single-cumulative convention and are NOT restated.** R13 explains the
discontinuity rather than erasing it.

**And nothing reopened.** Every closure above fired on a hurdle failure, not on multiplicity.

## 5. WHAT IS ACTUALLY LIVE

1. **The wide extended-hours decomposition** — fixture built and gated (`c25218d`), nothing
   decomposed, prediction declared. **Add the volatility split from §3.3 before running it.**
2. ~~A concentrated ranked short on the DAILY dead-inclusive fixture~~ — **RUN AND CLOSED, D279.
   0 of 14.** Its stop fired. Nothing further may be tuned on that fixture.
3. **[D281](../decisions/D281-the-unfiltered-ranking.md) — rank the WHOLE universe, removing the
   filter/ranking collision D280 measured and changing nothing else.** Pre-registered before its
   runner existed; **result pending at the time this handoff was written.** It inherits D280's 150
   comparisons under [R13](../RULES.md#r13) test 2, because D280 shaped its search space.
4. **[D282](../decisions/D282-the-overnight-only-short.md) - the cost arithmetic of the overnight construction** part 4 implies: ~252 round trips a
   year against D265's `2c` bar. **Pre-registered by another agent; result pending. Do not predict
   it.**
5. **The volatility tilt D280 part 4 turned up** — `zh + zv + za + zr` reaches IC **−0.01373
   (t −5.07)** on all live names, the only directional statistic in that record that clears its own
   multiplicity. **It is a volatility tilt, not a stronger `hist_L`** (flip `zr`'s sign and the IC
   goes positive), it does nothing on the qualifying set, `zr` alone was never scored, and no book,
   cost model or `sigma^2` tax has been applied to it. **Needs its own pre-registration.**
6. **The factor-neutral branch of FINDINGS §9** — still untouched after D256, D264, D279 and D280.
7. **Prop track:** rung 2's micro/mini form and rung 3, both free, both untested.
   [D266](../decisions/D266-the-prop-cross-screen.md) screened this session's work against
   hurdle P and the best cell earned +0.535%/yr after P1 sizing. BOOK_PROP.md stays empty.

## 6. DATA THAT NOW EXISTS

| | |
|---|---|
| `single_name_intraday_15m_{raw,panel}.csv.gz` | 8 names, 55,004 bars, 26.0/session, gates PASS |
| `holdout_intraday_15m_raw.csv.gz` | 16 names, 899,196 rows — fetch finished, D278 spent it |
| `cohort3_intraday_15m_raw.csv.gz` | **8 names, 448,861 rows, gates PASS, all 28 steps REAL. UNSPENT — spendable ONCE** |
| Alpha Vantage 15m cache | 57 ETFs + 24 single names, ~2,500 slices. **Any of these starts at zero requests.** |

**The provider limit is settled, do not re-probe it:** `TIME_SERIES_INTRADAY` serves **nothing**
for a delisted ticker (TWTR/FRC/SIVB/AABA, four for four). `TIME_SERIES_DAILY_ADJUSTED` does.
**41.6% of the 2013–17 cohort is unreachable at 15 minutes**, so every intraday single-name study
is survivor-only and the bias runs *against* a short.

---

## EARLIER THE SAME DAY — the D264 session, as it stood mid-way

*Superseded by the section above; kept because its data-layer notes are still accurate.*

---

## 0. THIS SESSION — D264 ran and closed. Three commits.

```
fc5b080  D264 RESULT: closed -- zero of twelve, and the cost decides, not the signal
7492402  Single-name 15m fixture: gates pass, and all 30 flagged steps are real
56c6156  D264 PRE-REGISTRATION, committed BEFORE the fixture is scored
```

**Working tree CLEAN. Suite 1,831 passing, 5 deselected, 1 failing** — the same pre-existing
`test_every_gap_is_a_non_empty_band_that_price_left_behind`. **Still not to be fixed.**

**Next decision number is D265.** Both counters (`docs/decisions/README.md`, `docs/RULES.md` R5)
are correct.

### What was built and is now durable

| | |
|---|---|
| `data/fixtures/single_name_intraday_15m_raw.csv.gz` | 8 names, 448,279 rows, 2018→2026, gates PASS |
| `data/fixtures/single_name_intraday_15m_panel.csv.gz` | **8 × 55,004 bars, 2,117 sessions, exactly 26.0/session** |
| `scripts/select_single_name_intraday.py` | the sample rule, on a window disjoint from the test span |
| `scripts/fetch_single_name_intraday.py` | fetcher, reusing the ETF one's helpers |
| `scripts/classify_single_name_steps.py` | D226's allow-list, built by measurement |
| `scripts/run_single_name_intraday.py` | 16 cells, six hurdles, every leg computed |

**~848 Alpha Vantage requests spent. Any further single-name intraday work on PG LMT PM MO CLF SM
YELP RH starts at zero requests.**

### THE PROVIDER LIMIT THAT SHAPES ALL FUTURE INTRADAY WORK — measured, five calls

**`TIME_SERIES_INTRADAY` serves NOTHING for a delisted ticker.** TWTR, FRC, SIVB and AABA all
return `Invalid API call` at 155 bytes; AAPL returns a clean 546 bars. **`TIME_SERIES_DAILY_ADJUSTED`
DOES serve dead names** — that is how D252 built a 35.7%-dead daily fixture.

**So any intraday single-name study on this provider is survivor-only, and 41.6% of the 2013–2017
cohort is unreachable.** Do not re-probe this; it is settled. If a dead-inclusive intraday fixture
is ever needed, it requires a different vendor (Polygon, Databento) and that is a spending decision.

### The result, in one line

**Zero of twelve short cells cleared.** The construction produces the **largest gross short edge
this programme has measured** — held bars returning **−28.87%/yr**, hurdle H cleared on both legs at
the **96.9th / 99.7th** percentile — and loses **15.84%/yr**, because:

```
exposure x edge   +8.31%/yr        (continuously compounded; percentages do not add)
- sigma^2 tax     -4.87%           59% of the gross, exactly as FINDINGS 1b describes
= realisable      +3.43%           still profitable at this point
- trading cost   -20.68%           324 turns/yr at 6.42 bp/side -- 6.0x the realisable gross
= net            -17.24%
```

**And the kill is assumption-free: mean commission ALONE is 1.92 bp against a 1.06 bp breakeven.
The cell loses at a zero spread**, so the verdict does not depend on the half-spread figure that was
named in advance as the design's weakest number.

**The closure is bounded**: it closes *that construction on those eight survivor names, personal
track*. It does not close the intraday short, because the survivorship bias runs **against** the
short and that direction was declared before the data was seen.

---

## 0b. THE THREE THINGS FROM D264 WORTH ACTING ON

### (a) OVERNIGHT DRIFT IS A PROPERTY OF VOLATILITY, AND THIS CHANGES A QUEUED STUDY

| | overnight/yr | intraday/yr |
|---|---:|---:|
| **LOW vol** — PG LMT PM MO | +4.36% | **+5.56%** |
| **HIGH vol** — CLF SM YELP RH | +13.81% | **−8.97%** |
| *57 ETFs — D247* | *+8.59%* | *−0.36%* |

**In low-volatility names the drift accrues INTRADAY and the sign reverses.** D247's figure is an
average over instruments whose volatility differs, not an asset-class constant.

> **ACT ON THIS: the wide extended-hours pre-registration in §4c below should carry a VOLATILITY
> SPLIT.** It already asks where untraded-window drift accrues across 11 instruments, and PICKUP
> already records SPY and QQQ disagreeing 33% against 91%. **D264 says that disagreement has a
> measurable axis.** Add it to the design *before* running, alongside the EEM/FXI prediction that is
> already declared.

### (b) COST PER BASIS POINT IS A FUNCTION OF PRICE — post-hoc, disclosed, NOT tested

IBKR charges **per share**, so commission in bps is inversely proportional to price. Inside the
high-vol stratum it varied twenty-fold:

| | RH | YELP | SM | CLF |
|---|---:|---:|---:|---:|
| commission, bp/side | **0.20** | 1.44 | 1.89 | **4.15** |

**A high-priced, high-volatility name gets the high stratum's edge at a fraction of its commission.**
Invisible on ETFs, which cluster in price.

> **This is NOT eligible as a D264 follow-up** — D264's stop forbids an additional stratum, and
> computing a per-symbol verdict now is precisely the complement-chasing D246 Constraint 3 forbids.
> **It is eligible as its own pre-registration with the provenance stated**, which Constraint 3
> explicitly permits. If you take it: select on price × volatility on a pre-period, fetch a fresh
> sample, and declare in advance that the breakeven must exceed commission alone.

### (c) BREADTH IS NOT CAPPED AT 2.2

**Effective instruments 3.02 of 8 single names**, against **2.23** on 57 ETFs and 1.80 of 35 on
crypto. FINDINGS §4's saturation near 2.2 is a property of the ETF universe, **not a ceiling**. Any
future breadth argument should stop quoting 2.2 as universal.

---

## 0c. WHAT IS STILL LIVE, IN PRIORITY ORDER

1. **The wide extended-hours decomposition** (§4c) — fixture built and gated, nothing decomposed,
   prediction already declared. **Add D264's volatility split before running.**
2. **Rung 2's free micro/mini form and rung 3** (§4) — untested, free, prop track.
3. **The factor-neutral branch of FINDINGS §9** — never attempted on the 1,580-name daily fixture.
4. **The price-stratified intraday question** (0b above) — needs its own pre-registration.

**Note on the personal track's short side:** with D264 closed, *directional* shorts are now closed on
liquid ETFs (D238/D240/D247/D248/D249), on single names daily (D256), and on concentrated single
names intraday (D264). **The remaining untested shapes are factor-neutral, not directional.**

---

## PREVIOUS SESSION — the futures data layer

*Written 2026-09-01 at the end of the session that built the free half of the futures data layer.
Everything below this line predates D264 and is preserved unedited; §1 and §2 restate that
session's tree state, not the current one — see §0 above for the current state.*

Read this first, then [`docs/decisions/D262-the-futures-data-layer-and-the-free-rung.md`](../decisions/D262-the-futures-data-layer-and-the-free-rung.md).
Everything below is verifiable from the repo; nothing here is a plan I intend to be trusted on faith.

---

## 1. State of the tree

**Working tree is CLEAN. Everything is committed.** Nine commits this session, `520e71b..0b40695`.

```
0b40695  WP4: the 2010-2017 backfill lands, and the 57-ETF extended fixture is REFUSED
8df1bc1  fetch_databento: close the two guard gaps found by reviewing the guards
0b99ac1  fetch_etf_intraday: --extended writes its OWN fixture, and 64 bars not 26
1043544  D262: the futures data layer documented, and three corrections to the proposal
02d8277  Continuous-contract stitcher, and the gates that reject a bad splice
4ef9a61  Databento client: verify-first, and structurally unable to spend
c18a4e6  CFTC Commitments of Traders: rung 1 of the ladder, built and committed
b1af940  futures-data: close lane 01, and close the forum search entirely
520e71b  data-purchase-proposal.md: the full costing, with the tick figure corrected
```

**Suite: 1,831 passing, 5 deselected, 1 failing.** The failure is
`tests/property/test_structure_invariants.py::test_every_gap_is_a_non_empty_band_that_price_left_behind`
and it is **PRE-EXISTING and explicitly not to be fixed.** Do not "helpfully" repair it.

**Next decision number is D263.** The README counter was stale at D260 and is now correct.

---

## 2. THE ONE THING BLOCKING PROGRESS, and it is not yours to unblock

`scripts/fetch_databento.py --verify` **cannot run: there is no Databento key on this machine**, and
no account behind it.

```
key file expected at:  C:\Users\O\.config\databento\key        (does not exist)
or env var:            DATABENTO_API_KEY                        (not set)
```

**Do not create the account. Do not handle, write, or ask for the key.** The principal has been given
the two steps (sign up choosing **usage-based $0/mo, NOT Standard**; save the key to that path). If
they say it is done, run `--verify` — it is free, metadata endpoints only, ~7 calls, ~4 seconds.

### What `--verify` settles, and why it matters more than it looks

**The single inferred number the entire $181.81 costing rests on.** We derived **$28.00/GiB** from
Databento's own two worked examples. **Their published `list_unit_prices` example shows `ohlcv-1m` at
280.0** for an unnamed dataset — ten times that. Unit prices are per-dataset so it is *probably* not a
contradiction, but the spread is **$182 against $1,820** and probably is not good enough.

It also resolves `ES.c.0` / `ES.v.0` / `ES.n.0` to settle whether the roll-rule letters mean what
`databento-python`'s `RollRule` enum implies. **See §5 — this one nearly cost real money.**

---

## 3. What now exists that did not before

| | |
|---|---|
| `scripts/fetch_cftc_cot.py` + fixture | **rung 1 of the ladder, free, BUILT** |
| `scripts/futures_continuous.py` | the stitcher §12 requires, tested against **no vendor data** |
| `scripts/fetch_databento.py` | a client that **cannot spend by accident** |
| `docs/cftc_cot.md`, `docs/databento_api.md` | provider references |

**`data/fixtures/cftc_cot_raw.csv.gz` — 210,717 rows, 28 symbols, three report families,
1986-01-15 → 2026-08-25, 3.1 MB, COMMITTED.** It is the only source in the futures data layer that
may be committed, because COT is a work of the US government and is public domain.

**Also durable:** the Alpha Vantage 15-minute cache is now **complete at 11,400 slices** (526 MB,
gitignored), including the 2010–2017 backfill. **Any future extended-hours study starts at zero
requests.**

---

## 4. UPDATE — rung 1 was screened after this file was first written, and it CLOSED

**[D263](../decisions/D263-the-cot-positioning-prescreen.md), commits `4dd6d3c` (design, before
the run) and `48c2d36` (result).**

**Zero of eight cells cleared. Monotonicity failed on all eight**, which is the decisive one —
`nonreportable (disagg)` runs +1.83 / −5.53 / **−19.33** / +8.82 / −1.32. Best gross was
**+1.26%/yr** against a 2% bar. **2020 is not the cause**: seven of eight signs survive its removal,
so the result is *empty* rather than regime-dependent.

**Weekly category positioning is CLOSED for the prop track.** The stop applies: no threshold sweep,
no second lookback, no third category. **Do not reopen it with a variant.**

**Two things worth carrying forward:**

- **The largest spread had the WRONG SIGN** — `managed_money` at −7.32%/yr against a declared `+1`.
  Disclosed, not claimed: it is non-monotone, and D246 Constraint 3 forbids re-reading a falsified
  direction. Do not resurrect it as a momentum signal.
- **THE PANEL SURVIVES AND IS THE REAL ASSET.** 11 contract/ETF pairs, 9,232 weekly observations,
  16.2 years, **effective instruments 3.76, MDE 0.21** — assembled free from two committed fixtures
  and better powered than anything the prop track has run. `scripts/prescreen_cot_positioning.py`
  builds it in ~20 seconds. **Any future weekly cross-sectional question should be asked here.**

### So what is next

**Rung 2's free form — the micro/mini split — is still untested**, and it is a *different
construction on a different quantity*, named on the ladder before D263 ran. It is not a rescue.
Scope it to **ES/MES (272 weeks) and NQ/MNQ (302 weeks)**; M2K has 136, MYM 78, MSI 5. Thin, and R10
applies to two correlated instruments.

**Rung 3 — open interest against volume — is also untested and free.**

**And weigh this honestly before spending:** the ladder's premise was that positioning/flow is one
of the few families with the shape hurdle P wants. **The cheapest rung came back empty.** That is
evidence about the family, bought for £0, and it is exactly what §7.5 was built to produce. It does
not close intraday order flow — a weekly survey says nothing about an hours horizon — but it should
lower the prior before ~$205 is spent.

---

## 4b. The original next step (superseded by §4 above)

**Screen rung 1.** The ladder in §7.5 of the proposal says test the cheap instruments before buying
the expensive one, and rung 1 is now sitting in the repo.

> **This is a STUDY, so it needs its own pre-registration under R8 before anything is scored.**
> D262 is a *data acquisition* record — it deliberately scored nothing. Do not read the fixture and
> report a number without registering first. That is the whole discipline of this repo.

**The question worth registering:** does institutional-versus-retail positioning, as the CFTC
classifies it, carry information at a weekly horizon?

**Two constructions are available and they are not the same test:**

1. **Category positioning** — `leveraged_money` / `asset_manager` / `dealer` net positioning and its
   changes, per contract. Available on the widest history.
2. **The micro/mini split** — the free weekly form of rung 2. **THIS IS THE FINDING OF THE SESSION:**
   the CFTC reports micros as their own contracts (MES `13874U`, MNQ `209747`, M2K `239747`,
   MYM `124608`, plus micro metals), each with its own `nonrept` small-trader column. The proposal
   costs this at $14.28 of Databento minute bars to *infer* the split from contract choice; the CFTC
   classifies the traders directly.

**BUT READ THIS BEFORE SCOPING IT.** A contract enters COT only once it has enough *reportable*
traders, which lags listing by years:

| | listed | first COT report |
|---|---|---|
| MES | 2019-05-06 | **2020-07-28** |
| MNQ | 2019-05-06 | 2020-08-04 |
| M2K | 2019-05-06 | **2021-11-30** |
| MYM | 2019-05-06 | **2022-07-26** |
| MSI / MHG | 2022 | **2026-01** — unusable |

**So it is ES/MES and NQ/MNQ at ~6 years, not four pairs at seven.** Scope the registration to the
pairs that have history, and state the breadth honestly — two correlated pairs is thin, and R10
applies.

**Rung 3 is also free** and needs no new data: open interest against volume, in the fixture already.

---

## 4c. INTRADAY — a wide extended-hours fixture is built and gated, decomposition NOT run

**Commit `c25218d`. `data/fixtures/wide_extended_15m_raw.csv.gz` — 2,440,395 rows, 11 symbols,
2010-01 → 2026-08, all four gates PASS. Zero API requests; every slice was already cached.**

Built to settle a question **D259 explicitly left open**: SPY and QQQ *disagree* about where the
overnight drift accrues — the untraded 20:00–04:00 window carries **33% of SPY's and 91% of QQQ's**
— and D259 said in terms that *"nothing should be built on the untraded window's dominance."*
Four instruments cannot separate noise from structure. This is eleven.

**Universe:** SPY QQQ IWM DIA GLD SLV USO UNG GDX EEM FXI. Selected by **coverage** (median ≥45
extended bars of 64), a data-quality rule fixed before any decomposition ran and one that cannot
select on the quantity being measured.

### THE NEXT STEP, AND THE PREDICTION IS ALREADY DECLARED

**20:00–04:00 ET is Asian trading hours.** EEM and FXI track markets that are **open** during the
window the US calls untraded. **So if the untraded-window drift is a real transfer of information,
those two should show the LARGEST untraded share. If they do not, the effect is an artefact of
measuring a closed market rather than a real overnight risk** — and that would materially weaken
the case that overnight futures holds are structurally bad for hurdle P.

**Declare that prediction in the pre-registration before running it.** D263 showed the value: the
biggest number in that table had the wrong sign, and only the advance declaration made it legible
rather than reinterpretable.

**This is a STUDY. It needs its own R8 pre-registration.** Nothing was decomposed.

### Two findings from the build itself

- **THE EVENTS SIDECAR CANNOT EXPRESS A SPIN-OFF.** XLF qualified on coverage and was excluded
  anyway: it closes 23.63 on 2016-09-16 and opens 19.30 — **then holds there all day on 5.9M
  shares.** A −18.3% step persisting at full volume is a corporate action, the XLRE real-estate
  spin-off, and **Alpha Vantage's `SPLITS` reports zero splits for XLF.** `SPLITS` + `DIVIDENDS`
  between them do not cover spin-offs and this project has no general handling. **Check any new
  symbol for one before trusting its returns.**
- **D226's gate spec always required a documented real-events allow-list** — "no move above 15%
  *that is not on a documented list of real events*". The four-symbol build never needed the second
  half of that sentence. It exists now, the threshold is unchanged at 15%, and admission uses D252's
  test: does the move revert (bad print), persist at volume (corporate action), or is it
  corroborated (real).

---

## 5. Traps found this session that will bite you if you do not know them

**The symbol map is derived for a reason. Never type a CFTC contract code.**
`%CRUDE OIL%` matches **seven** contracts. Worse, **`%NATURAL GAS%` matches the main Henry Hub
contract NOT AT ALL** — the CFTC abbreviates it to `NAT GAS NYME`, so the pattern returns two
plausible wrong answers and no right one. A wrong code returns a full, well-formed series for the
wrong market and **nothing downstream errors**.

**The COT open-interest identity is not `OI == sum(long)`.** That fails on 94% of rows. A **spread
position is one long AND one short held by the same trader** — inside open interest, outside the
directional columns. It is `OI == sum(long) + sum(spread) == sum(short) + sum(spread)`, and it then
holds on **55,661/55,661 rows exactly**.

**Key COT dates on `release_date_nominal`, never `report_date`.** Report is Tuesday, release is the
**Friday of that week** — not a flat +3, because the survey day shifts on holidays. Rows before 1993
carry **no release date at all**, deliberately: there was no weekly schedule then and a fabricated
date would look usable.

**`6E` predates the euro.** Legacy rows run from 1986 under the name `EURO FX`; the euro began
1999-01-01 and continuous coverage starts exactly **1999-01-05** after a 644-week gap. **Use
1999-01-05 onward.** `RTY` separately spans an ICE venue change (2008–2017).

**The provider's typos are load-bearing.** `swap__positions_short_all` and
`swap__positions_spread_all` have **double underscores**; `noncomm_postions_spread_all` says
**"postions"**. Pinned by test. If you "fix" them the columns go silently empty.

**`ES.c.0` is almost certainly the CALENDAR roll — rolling at expiry.** §11 of the proposal
hard-coded it. That is precisely the defect §12's acceptance tests were written to catch in Yahoo's
`ES=F`. **The default is now `ES.v.0`.** Do not revert it on the basis of the proposal's text.

**The 57-ETF extended-hours fixture is REFUSED, on measurement.** Only **2 of 57 symbols** reach a
median 58 of 64 session slots; the tail is at 27–28; the raggedness is **liquidity-correlated**,
which is disqualifying for anything volume-related. And an unfiltered **+428.52%** bad print survives
(EWJ 2018-05-23 08:15 prints 11.46 on 912 shares against ~60.60 either side). `--extended` refuses
with the numbers as the reason. **Use `fetch_index_extended.py`**, which applies D259's
corroboration filter and carries a `suspect` column.

---

## 6. Two mistakes I made, so you do not repeat the shape of them

**I overwrote a committed fixture's meta.** The commit *before* it existed specifically to stop
`--extended` clobbering the regular-hours artifact. It parameterised the fixture path and the events
path and **missed the meta.** Caught only because `git status` flagged the committed file as
modified. Fixed by giving one function (`build_targets`) all three paths, plus a test asserting
`do_build` reaches for no unparameterised output constant. **Three constants with two swapped hides
the one you forget.**

**I wrote gates that were wrong before they were right** — the open-interest identity passed on 5.82%
of rows on its first version, and the release convention put a Friday report's release on itself
(zero lag, look-ahead by construction). Both were found by *looking at the output*, not by reasoning.
**Run the gate and read the number before believing it.**

**Practical note:** `Bash` heredocs on this machine mangle backslashes — a `"\n"` inside a Python
heredoc became a literal newline and silently broke a string, and an earlier `str.replace` missed for
the same reason. **Use the Edit/Write tools for anything containing escapes.**

---

## 7. Standing constraints — these do not lapse

**Alpha Vantage key** at `~/.config/alphavantage/key`, read via `ALPHAVANTAGE_API_KEY`
first. **Never inlined, never printed, never logged, redacted from any displayed URL.** Pace at
**66 req/min** against the 75 ceiling. Cache every response; hard stop after 5 consecutive failures.
**The ToS requires this repo stay private.**

**Exchange-licensed data is NEVER committed.** CME, Sierra Chart and NinjaTrader all forbid
redistribution. `.gitignore` carries `data/raw/databento/`, `data/raw/futures/`,
`data/fixtures/*futures*`, `data/fixtures/*glbx*`. The pattern is **gitignored cache + committed
re-fetch script + committed `.meta.json`**. CFTC COT is the sole exception and only because it is
public domain.

**Raw caches are not committed (D191); derived fixtures are.**

**No purchase without the principal's explicit decision.** `--submit` refuses without a passed
`--verify` *and* an accepted figure, and is then deliberately unwired. **Leave it that way** until
the purchase is actually decided — wire it up in the same commit, not before.

---

## 8. Where things are

| | |
|---|---|
| the costed purchase | `docs/research/futures-data/data-purchase-proposal.md` |
| the twelve-lane free search | `docs/research/futures-data/00-SYNTHESIS.md` |
| this session's record | `docs/decisions/D262-...md` |
| standing rules R1–R12 | `docs/RULES.md` |
| the two books | `docs/BOOK.md` (personal), `docs/BOOK_PROP.md` (prop — **admitted arms: none**) |
| substantive findings | `docs/FINDINGS.md` |
| providers | `docs/alpha_vantage_api.md`, `docs/cftc_cot.md`, `docs/databento_api.md` |

**Prop track status: every candidate so far is closed.** C1, C2, C3 and D261's spreads all failed —
three of them on **shape** rather than return, which is why the smart-money detector was worth
reaching for: order flow and positioning are among the few signal families with the shape hurdle P
wants. **Rung 1 is the cheapest available test of that idea and it is ready to screen.**

---

## 9. If you do only one thing

**Pre-register the COT screen and run it.** It costs nothing, the data is committed, and a negative
result is worth as much as a positive one — it would tell the principal not to spend £205 on the
Databento purchase at all.
