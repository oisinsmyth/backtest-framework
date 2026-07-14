# D107 — Deferrals recorded, per R3: margin lock, fill-assumption menu, FX brick, IS/OOS ratio, registry artifacts (audit F6/F7/F13/F27/F28)

**Status:** Committed (the record) / Deferred (each item, with rationale)
**Date:** 2026-07-14
**Category:** Scope & sequencing
**Source:** Audit remediation session (AUDIT_REPORT.md findings F6, F7, F13, F27, F28)

The audit surfaced five gaps that were real but wrong to close with code today.
R3's rule: a reasoned scoping decision is a portfolio asset; a silent gap is a
liability. Each is now explicit:

## 1. Buying-power lock (F7 — the unimplemented half of D43)

D43's NAV definition (cash + longs − |shorts|) is implemented, single-sourced and
golden-tested; its "margin requirement locks equivalent buying power" clause is
not — `margin_requirement()` exists on every instrument but nothing calls it, and
short proceeds are freely reusable. **Deferred because:** a lock needs a policy
(reject the order? scale it? which order first?) that is a risk-management design
decision with zero validated strategies to inform it — the same argument as D31
and D62. The honest interim posture: gross exposure is *observable* every bar
(D30), *rejectable* pre-trade behind `enforce_pretrade` (D101), and every study
reports margin interest on the borrowed portion (D5/D67), so leverage is priced
even where it isn't blocked. Trigger to build: the first study whose conclusion
depends on a hard leverage constraint.

## 2. The fill-assumption menu: D9, D11, D42 (F13)

D9 (LIMIT_TRADE_THROUGH), D11 (the VWAP rename), and D42's two-exit adverse
ordering were written for an engine with resting stop/limit orders. The engine
built has none — strategies emit target weights (D27) filled at close or next
open (D103); `stop_fill_price` (D10) and the D42 single-stop convention exist as
gate-tested components with no engine surface. **Resolved as:** D11 is moot (no
fill-assumption enum was ever built, so there is nothing dishonestly labelled —
its intent, honest fill labels, is met by D103's explicit two-mode vocabulary);
D9 and D42's multi-exit case are deferred until stop/limit orders become an
engine feature, which no committed study needs — pulling order-management into
the engine now would be speculative surface, R3's exact failure mode.

## 3. FXConversionCost brick and multi-currency NAV: D7/D19 (F27)

D7's committed half (the conversion-cost trade brick "now") was never built;
`quote_currency` is declared but unread; D19's base-currency NAV is untouched.
**Deferred because:** every instrument in every committed fixture and study is
USD — a conversion brick would be a brick no code path can exercise and no test
can ground in a real friction (D48's false-affordance rule cuts against building
it idle). The blind spot D7 wanted labelled is labelled here instead: this
framework currently measures a USD-only book; any non-USD instrument must bring
D7's brick and D19's NAV conversion with it as its first prerequisite. The
`TradeCostBrick` interface it will implement is stable and proven.

## 4. The IS/OOS overfitting ratio sibling: D21 (F27)

D21 called DSR "a sibling to the IS/OOS overfitting ratio, not a replacement" —
written for the pre-framework codebase that had such a ratio; this repo never
did. **Deferred because:** the ratio needs in-sample backtests of each window's
selected pairs, which the study runner deliberately never executes (selection
fits on train views; only OOS windows are traded). Adding IS runs doubles study
compute to produce a statistic D21 itself calls "noisy at ~8–12 OOS windows" and
which the corrected DSR (D98) strictly dominates for the program's headline
question. Trigger to build: a reviewer asks for it, or a study design produces
IS equity curves anyway.

## 5. Study registries and snapshots stay local artifacts (F6/F28)

Per-study registry SQLite files and snapshot directories remain gitignored. The
audit correctly noted the consequence: the N and V behind a published DSR are
not inspectable from a checkout without re-running. **Kept because:** every
registry is deterministically regenerable from committed fixtures by the study
script that made it (tested end-to-end), a binary sqlite blob in git is neither
diffable nor reviewable, and committing one would create two sources of truth
for the same fact. The artifact docs each carry their reproduction command; the
reproducibility loop (config → hash → reload → re-run, D102) is the audit trail.
Engine-level trial logging likewise stays opt-in (`trial_registry=None` default):
the golden masters, property suites, and tutorial runs that make up most
`run_backtest` calls are not experiments, and forcing them through a registry
would bury the real trial count under test noise — D20's "every backtest run"
binds at the study runner, where it is structural (the registry is a required
argument of `run_pairs_study`).
