# D101 — Opt-in pre-trade enforcement; sleeve-level fill instrumentation (audit F12/F5)

**Status:** Committed
**Date:** 2026-07-14
**Category:** Portfolio layer / Backtest engine
**Source:** Audit remediation session (AUDIT_REPORT.md findings F5, F12)

## Decision

**Pre-trade gate wired, opt-in (F12).** `run_backtest` gains
`enforce_pretrade: bool = False`. When enabled (requires `risk_limits`), each
netted order is checked with `RiskMonitor.pretrade_check` against a running
simulated position before it fills; a breaching order is rejected — it never
executes, the violation is recorded with its bar index, and the rejected
instrument's *virtual* orders are dropped too, so sleeve books stay reconciled
with the broker book and the strategies simply re-attempt (and re-reject) next
bar. The default `False` preserves D62's recorded-not-enforced behaviour and
every existing baseline byte-for-byte. This closes the audit's observation that
the Step 4 gate's "pre-trade gate still rejects an order" was passing on a
function production never invoked.

The virtual-order rollback is the load-bearing design choice: rejecting only the
broker-facing order while letting virtual books believe they hold the target
would desynchronize the sizer permanently (it sizes deltas off virtual books, so
the broker book would stay short of target forever with no order ever re-issued).

**Sleeve instrumentation (F5).** `BacktestResult` gains `virtual_fills`
(timestamp, strategy_id, instrument_id, signed quantity, price — each strategy's
own order as if filled in full at that bar's price, regardless of netting) and
`final_virtual_positions` ((strategy_id, instrument_id) → quantity). This is
D46's "fills are strategy-tagged" made real at the result surface: sleeve-level
price-P&L streams are now derivable by any consumer from `virtual_fills` plus the
price series. Trade costs remain attributed to the netted broker fills only —
post-netting cost attribution to sleeves is genuinely ambiguous (whose order
"caused" the net?), and inventing an allocation rule here would be a research
methodology decision smuggled into the engine. Deferred, per R3, until the
allocator work (D31) needs it and can argue for a rule.

## Rationale

Both changes are additive instrumentation plus an opt-in flag — verified against
the full suite with zero baseline drift. D30 named "corrective orders or halt
flags" as the eventual response to violations; rejection-of-the-triggering-order
is the minimal honest step between D62's detection-only and that future work,
and it exists behind a flag rather than as default behaviour because no study has
yet decided what its risk policy should be — enforcement changing published
numbers silently would be worse than enforcement being available and off.
