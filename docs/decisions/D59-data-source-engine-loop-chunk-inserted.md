# D59 — Insert a minimal data-source + production-engine-loop chunk ahead of Step 5

**Status:** Committed
**Date:** 2026-07-13
**Category:** Data & portfolio layers
**Source:** Implementation session (post-Phase B, pre-Step 5)

## Decision

Before starting Step 5 (real equity cost bricks), build exactly enough to unblock it
and Step 6: a minimal, explicitly unhardened `EquityDataSource` (yfinance-backed) and a
production `run_backtest` loop generalizing Step 3's test-only mini-backtest harness.
Not a numbered `VERIFICATION_SCHEME.md` step — inserted infrastructure, planned with
the user before writing code (see the approved plan in this session).

**Explicit scope cuts, each also called out in its own module/decision:**
- No D24 immutable snapshotting, D25 cleaning report, or D26 sanity gate — genuinely
  Step 7's job. `EquityDataSource` is a raw yfinance passthrough, labelled as such.
- No volume/ADV field on bars — D3's sqrt-impact brick will add it when it actually
  needs it (see `data/bars.py`).
- `RiskMonitor` violations are recorded in `BacktestResult`, not enforced — no
  corrective orders or halting exist yet (D62).
- Single-instrument backtests only — multi-instrument alignment (D45, e.g. a real
  XLE/XOP pair) is out of scope for this chunk (see `engine/backtest.py`).

## Rationale

`DEVELOPMENT_TIMETABLE.md`'s build order already expects Step 6's "first real number"
(the XLE/XOP walk-forward, R1's existence-justification gate) to happen *before* Step
7's hardened data layer lands — meaning some minimal, unhardened data source and some
engine loop were always implicitly required earlier than Step 7, they just were never
named as their own step. Rather than let that stay an unnamed gap that Step 5 would
trip over silently, it's named, scoped, and built now, with every cut corner labelled
so it can't be mistaken for finished work — the same discipline D53 used for the
Step 3 gate reinterpretation. Planned with `EnterPlanMode` before implementation since
it touches new architectural ground (first production dependency, first stateful
portfolio class, first strategy interface) that Steps 1–4 didn't have precedent for.
