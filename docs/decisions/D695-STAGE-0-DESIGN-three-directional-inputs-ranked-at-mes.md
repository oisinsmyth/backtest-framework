# D695 STAGE 0 DESIGN — three new directional inputs for the short-gamma long continuation, ranked continuously at MES: order flow, breadth across the index futures, and where the price sits in the gamma profile

*2026-09-29. Committed with its builder (`scripts/build_fut_es_signed_1m.py`) and its runner
(`scripts/stage0_d695_directional_inputs.py`), before the runner is run.*
- **What it is:** in-sample, 2016-01-05 → 2023-12-29; nothing dated 2024-01-01 or later is read. No filter is fitted:
  each input is a raw score with a direction declared in the runner's docstring. The filter is designed with the
  principal afterwards.
- **Why:** [D693](D693-STAGE-0-RESULT-the-cell-filter-is-anti-calibrated-at-mes.md) found that none of the inputs
  tried so far carries the Spearman of about 0.05 that would lift this trade from +0.28 to about +0.6.

## The principal's decisions (2026-09-29)

"Look for a new directional input". Then, from the candidates put to the principal: "A, B and C, continuous
ranking, 2016–2023 only". D (the intraday change in implied volatility) needs data not on disk, and E (the overnight
context) has a weaker mechanism; neither was chosen.

## The universe and the outcome (D693's)

- **When:** G_SUM < 0, and the last 60 minutes up.
- **The trade:** buy 1 MES at 10:30, 11:30, 12:30, 13:30 or 14:30, and sell 60 minutes later.
- **The outcome** is the MES net, and the oracle label is net > 0.

## The inputs (a higher score is declared better for the long trade)

**A — order flow.** From a new fixture, `fut_ES_signed_1m`: Sierra Chart's ES tick files, with the aggressor side,
for each session's front contract, 09:30–16:00, 2016–2023.
- **The fixture's declared validation** is against the Databento 1-minute bars:
  - median volume ratio in [0.98, 1.02];
  - volume correlation ≥ 0.98;
  - signed share ≥ 0.99;
  - the last trade equal to the bar's close on ≥ 95% of minutes.

  If it fails, A is VOID.
- **The true aggressor side cannot be checked for ES here,** because Databento's side-flagged ES trades are only in
  the sealed vault. On HO and RB, Sierra's 2-minute net flow correlates with the truth at r 0.88.
- **The scores:**
  - **A1:** (buy − sell) / volume over the last hour;
  - **A2:** buy − sell, over the median volume of the same hour in the prior 20 sessions;
  - **A3:** (buy − sell) / volume over the last 15 minutes.
- **Mechanism:** on a short-gamma day, a rise driven by aggressive buying (dealers hedging with market orders, or a
  metaorder being worked) is still running.

**B — breadth across NQ, RTY and YM** (the same minutes).
- **B1:** how many of the three also rose over the last hour.
- **B2:** their mean last-hour move, each over its own prior-20-session standard deviation of hourly moves.
- **Mechanism:** index-wide hedging and macro flow are broad and continue; an ES-only rise is idiosyncratic.

**C — the gamma profile at the decision.** D688's ES options book, with the same options and prior-settlement iv,
re-evaluated at the decision: F moves with the front's move since the settlement, and τ falls to the hours left to
16:00. SPX GEX has no strikes and is held fixed.
- **C1:** −(G_SPX + G_ES(t)): how short gamma the dealers are now.
- **C2:** −(G_ES(t) − G_ES(prior settlement)): how much the move so far has made them shorter.

## Statistics and reading (declared)

**Per input:**
- the Spearman of the score with the MES net, and its value on the partial-oracle curve (q = 50%);
- the AUC against the oracle label;
- the enumerated day-rotation null of the Spearman, and the family null (the maximum over the seven scores for each
  rotation);
- terciles of the score (descriptive).

**The reading:** an input **carries direction** if its Spearman is above 0 and above its own rotation p95. It
**survives the family** if above the family-maximum p95. It is **worth a filter** if it also reaches a Spearman of
0.05.

**Audits:**
- G_ES re-evaluated at the prior settlement must equal D688's exactly;
- the rotation's k = 0 must reproduce each observed Spearman;
- every loader cuts at 2024-01-01.
