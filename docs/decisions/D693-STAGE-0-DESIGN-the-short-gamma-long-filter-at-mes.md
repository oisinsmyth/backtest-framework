# D693 STAGE 0 DESIGN — the principal's filter for the short-gamma continuation: long only, per-cell expected profit (alignment × volatility), scored at MES against the oracle

*2026-09-29. Committed with its runner (`scripts/stage0_d693_short_gamma_long_filter.py`), before the run.*
- **What it is:** in-sample development, walk-forward and prior-only. The result follows as a separate record.
- **The caution:** the cells were chosen after reading [D692's in-sample profile](D692-DIAG-the-mes-oracle-profile.md),
  so these numbers flatter the filter. Only unseen data can confirm it.

## The principal's formation decisions (2026-09-29, after D692)

| question | the principal's choice |
|---|---|
| trades | "Short-gamma days, long only" |
| gamma measure | "Combined G_SUM (SPX + ES)" |
| size and bar | "MES book, bar at net above zero" (1 MES, $4.42 a round trip; take when the projected net > $0) |
| inputs | "Against the day's move, Volatility floor" |
| form | "Per-cell expected profit" |

## The construction

- **The universe:** D692's candidates with G_SUM < 0 and the last 60 minutes up. Buy 1 MES at t (10:30 … 14:30) and
  sell 60 minutes later.
- **Cells:** alignment × volatility tercile, 6 in all.
  - **Alignment:** "against" means the day's move so far is down; "with" means it is up.
  - **Volatility:** today's realised 5-minute variance up to t. The tercile edges come from all candidates of strictly
    earlier days; a low-volatility cell with a negative mean is simply not traded, which is how the floor works.
- **The projection:** the prior-only mean MES net of the universe's trades in the cell, refit monthly. It needs at
  least 30 earlier trades in the cell. **Take iff the projection is above $0.** There is a 250-session burn-in.
- **Scoring, all at MES:**
  - the oracle (net > 0);
  - the gate alone against the filtered book, with CLAUDE.md's four groups and ρ with the MACD arm;
  - the accuracy assessment against the oracle (D690's library), including the calibration slope;
  - the partial-oracle curve at the filter's own take share;
  - a day-rotation null of the take grid;
  - the six cells in hindsight, labelled descriptive;
  - a lag audit that must fire when today's trades are included.
- **The declared reading: useful in-sample** if the calibration slope is > 0, the net Sharpe beats the gate alone,
  and it is above the p95 of the rotation null.
