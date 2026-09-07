# D365 — the momentum buffer book: a broad, slow, hysteretic long, and whether its edge is momentum or size

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. **OHLCV only** — no auxiliary data source is opened. **The holdout fixture is not
read.**
**Date:** 2026-09-07
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

**Selection history, stated up front because it governs how every number here reads.** The
cell this record makes primary was chosen by an **eleven-combination screen run on this same
fixture** on 2026-09-07. This is therefore a **within-sample confirmation with nulls**, in
the shape of D362, and **not** a discovery. Whatever it returns, the buffer grid has been
looked at once already and the record says so rather than presenting the cell as if it had
been reasoned to in advance.

---

## 0. Why

D361–D364 established something more general than a verdict on one signal: **a reversal edge
is compensation for supplying liquidity, so its gross is denominated in the spread and cannot
be captured by crossing it.** On the fade's widest two deciles the gross is +219.8 bp a trade
against a round trip of 216.6. Selection, timing, exits and sizing were each tried and moved
the net by 4 to 19 bp against a 45 to 90 bp gap, because none of them changes what the payoff
is denominated in.

The construction that follows from that arithmetic is the **opposite of everything this
programme has built**. The toll is paid per round trip and the edge accrues per bar, so the
shape that wins is broad, slow and reluctant to trade — not concentrated, fast and
event-driven. And the record already has a candidate it walked past: **D359's Stage 0
measured the top decile of `mom_252_21` drifting +3.85 bp/bar hedged**, as a premise check
for a short, and never ran it as a book. Its beta is 1.15 and beta-adjusting leaves +3.85, so
it is not beta.

**Why the programme could not see it.** D300 fixed the book at two names per side for a
*spread* construction and that convention propagated into everything after it. A diversified
premium cannot be seen through a two-name window. The contribution here, if there is one, is
the shape rather than the signal: cross-sectional momentum is the most published anomaly in
finance and nothing in this record should read as a claim to have found it.

## 1. The construction

```
For each name i, on daily bars:

  mom[i,t]   = the 252-bar cumulative return to t less the most recent 21 bars   (`mom_252_21`)

  eligible   = as-traded close at t-1 >= $5 AND the declared dollar-volume floor
               with its 21 observations (`keep_v2`) AND outside the 189-bar
               window after a merger filing (F0) AND live and past warm-up

  pct[i,t]   = cross-sectional percentile of mom[i,t-1] among that day's eligible
               names; average rank on ties; undefined below 50 such names

  ENTER   if not held and pct[i,t] > hi
  HOLD    while pct[i,t] > lo
  EXIT    when pct[i,t] <= lo, or the name stops being eligible

  book    long, equal-weight over whatever qualifies, hedged each bar by the
          floored universe's equal-weight return. No slot cap, no stop, no
          target, no time limit.
```

**Fill: next open (D340).** The entry bar earns `ocT − m_f_oc`, every later bar
`r1T − m_f`. The screen that produced this cell used a same-close fill throughout; that
convention was worth 13.8 bp/bar on the event books, and here it touches only the ~1% of
position-bars that are entries. The open fill is the declared convention and the
close-to-close variant is reported beside it as the screen's own basis.

**The grid, declared: `hi` ∈ {90, 95} × `lo` ∈ {60, 70, 80, 85}, `lo` < `hi` — 8 cells.**
Primary: **`hi` = 95, `lo` = 80**. The grid max is reported against a grid-max null under
shared offsets. Multiplicity eight, on top of the eleven already looked at.

## 2. Stage 0 — the premise, and it is not the drift

The drift is already measured (D359 Stage 0; reproduced at +3.87 hedged, +3.85 beta-adjusted
on 189,544 name-bars). **The open question is whether it is momentum or size.** The hedge is
the floored universe's *equal-weight* return, which is a small-cap-tilted benchmark, and
momentum winners are not small. Beta-adjustment does not remove a size tilt.

Before the book is built:

1. **The DV-matched drift.** For each eligible name-bar in the top decile, the hedged return
   against the equal-weight return of eligible names **in the same dollar-volume decile that
   day**, rather than against the whole universe. Reported beside the equal-weight figure.
2. **The rank-band profile** of both, across the six bands the screen used, so the shape is
   visible rather than summarised.
3. **A two-factor decomposition**: regress the top decile's excess return on the market and
   on a size factor built from the same universe (top DV decile minus bottom DV decile), and
   report the intercept with its standard error.

## 3. Nulls, on the primary cell

- **ROT** — the record's rank rotation for a slot-style book (D348): the score's ranks
  shifted and the book re-ranked and re-run, all 24 shifts.
- **A′** — per-name time rotation of the score within each name's **eligible** bars (D351),
  the book rebuilt from the rotated score, 200 draws. This is the null that asks whether the
  timing matters or only the membership.
- **SIZE** — *the interpretive control, and the one that matters most here*: the identical
  buffer construction with `dollar_vol` as the score instead of `mom_252_21`. Not a random
  control but a rival hypothesis: if ranking on size earns what ranking on momentum earns,
  the book is a size book.
- **C** — random direction on the per-name-bar contribution ledger, 1,000 draws.

## 4. Cost, and both conventions

Round trip at the held names' median half-spread, **PUB primary and PB beside**; commission
per crossing at the as-traded price; `cost bp/bar = round trip × turnover`, turnover measured
as entries per member-bar. **Both cost conventions from D363**: the held-median line the
record has used since D285, and the per-trade line that charges each name its own spread —
this book's names are far more homogeneous than the fade's, so the two should be close, and
if they are not that is itself the finding. Four groups on the primary cell with the top
trade named and its bar shown; by-year, era and down-year splits; turnover, mean membership
and exposure.

## 5. Predictions

Q1 is load-bearing. Q5 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the primary cell's **hedged net PUB bp/bar > 0 and above the p95 of ROT, A′ and C.** |
| **Q2** | the **SIZE control earns less than half** the primary cell's gross bp/bar: the edge is momentum, not size. |
| **Q3** | the **DV-matched** hedge keeps at least half the equal-weight hedge's net, and the two-factor intercept is positive with a t above 2. |
| **Q4** | **era 1's net PUB is > 0.** The screen's 90/70 cell was −0.06 in era 1 and +2.19 in era 2; this asks whether the primary cell is better or the effect is era 2's alone. |
| **Q5** | *(against)* the buffer's advantage survives the open fill: the primary cell beats the daily-refresh cell (`hi` = `lo` = 90) by **more than 2 bp/bar net**. |
| **Q6** | the open fill costs **less than 20%** of the close-to-close gross. |
| **Q7** | at least **10 of 13 full years** are positive on gross. |
| **Q8** | at least **20 names to half the P&L** — a broad premium should be broad, where this record's books have run 8 to 14. |
| *check* | the close-to-close variant reproduces the screen (`hi` 95 / `lo` 80: 41 members, 1.01% turnover, gross +3.43, net PUB +2.65; `hi` = `lo` = 90: 5.93% turnover, gross +3.87, net −0.56) to 1e-9 |

## 6. Stop conditions

These state the construction's status. **The avenue is the principal's (R15).**

- **Q1 holds and Q2 holds** → a broad slow long whose edge is not size and clears its nulls;
  the next question is its own out-of-sample design, which is a separate record and does not
  touch D357's frozen read.
- **Q2 fails** → the book is a size book wearing a momentum label; that is worth knowing and
  the record says it plainly.
- **Q3 fails** → the drift is an artefact of hedging a large-cap-tilted book against a
  small-cap-tilted benchmark, and the whole construction is withdrawn.
- **Q1 fails on the nulls** → the buffer found a shape, not an edge.
- Nothing is promoted. Book: empty.

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[ID]** | the close-to-close variant reproduces the screen's eleven cells to 1e-9 |
| **[BUF]** | the hold state from a plain Python loop equals the vectorised one on every bar and name |
| **[LAG]** | the held set at t is re-derived from `pct[:, t]` by a second implementation that never calls the selection function, and moving `mom[t]` leaves the set at t and changes it at t+1 |
| **[FILL]** | the entry bar earns `ocT − m_f_oc` and later bars `r1T − m_f`; the open-fill and close-to-close books differ on exactly the entry bars and nowhere else |
| **[TURN]** | turnover equals entries / member-bars from an independent count; membership counts match the hold grid |
| **[SZ]** | the DV-matched hedge uses same-day, same-decile eligible names and never the held name itself; every held name has a non-empty matching pool or is counted |
| **[S]** | sign in money: a favourable move pays positively, and +50 bp on one held name moves the book's bar by 50 / n_held and no other bar |
| **[ROT]** · **[A′]** · **[SIZE]** · **[C]** | rotations keep counts and multisets; every rotated score stays within the name's eligible bars; C's mean within 3 SE of zero and the observed outside it |
| **[6]** | [BUF], [LAG], [FILL], [SZ] and [S] each raise on a deliberately broken input |

## 8. Files

`docs/decisions/D365-the-momentum-buffer-book.md` (this record) ·
`scripts/run_d365_momentum_buffer.py` (stages `--selftest`, `--stage0`, `--cell HI:LO
--draws N --part p`, `--report`) · `data/d365_stage0.json`, `data/d365_ctrl_*.json`,
`data/d365_momentum_buffer.json` (to follow). Reuses `scripts/d348_prep.py`,
`scripts/run_d358_flat_sleeve.py` (`pct_of`, the four-group and split helpers),
`scripts/run_d348_score_rotation_null.py` (the rank rotation),
`scripts/run_d351_control_a_on_the_floor.py` (the eligible-bar time rotation),
`scripts/d322_four_group_report.py`. No auxiliary data source; the holdout fixture is not read.
