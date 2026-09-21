# `data/recorder/GAPS.md` — every recorder window that closed without a record

*D608. **Append-only**: a line is added and never rewritten, and no gap is ever filled
with an estimate — `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.3, "Gaps are **never** filled
with estimates". Written by `backtest_framework.data.recorder.append_gaps`; the module has
no `fill_gap` and must never acquire one. A line here is a hole in the record that stays a
hole.*

| date (ET) | job | cadence | window (ET) | window closed (UTC) | reason | logged (UTC) |
|---|---|---|---|---|---|---|
