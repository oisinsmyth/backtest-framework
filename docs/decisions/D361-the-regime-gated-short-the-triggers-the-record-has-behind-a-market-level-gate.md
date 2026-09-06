# D361 — the regime-gated short: the triggers the record has, switched on by a market-level gate, with the gate's own null

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book. The signal criterion is R15's: a positive **gross** mean per
trade above the pre-registered controls; cost is reported in full beside it and decides
nothing here.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why, reasoned from the record

No unconditional tape short has cleared its controls on the floored universe (D352, D359,
D360). Every conditional split says the same thing the other way: the loser cohort drifts
−2.4 bp/bar in era 1 and −2.9 in the down-years and up everywhere else (D359 Stage 0); the
loser-rally short earned +27 a trade in era 1 and +45 in the down-years and nothing
otherwise; the gap-up fade — D360's mirror, the most positive raw short in the record at +15
per ten bars with t up to 3.7 — was strongest in the down-years. **The record has never
tested a time-series object as a signal**; it has split results by era afterwards. This
record makes the regime the signal.

**The exemption, in the record's quantities (STACK §7 item 30):** the held finding —
"shorts lose" — was measured unconditionally. D359's Stage 0 table shows the loser cohort's
drift changing sign with the regime; no short in the record has been measured inside the
state where that table says the cohort falls. Stage 0 tests that exemption before any
timing is read.

## 1. The signal

**Gate**, computed on the floored market's own equal-weight return series `m_f`, lagged one
bar (the value at t uses bars to t−1):

- **G1:** the trailing 63-bar cumulative return of the floored market **< 0**.
- **G2:** the floored market's cumulative index **below its trailing 200-bar mean**.

**Trigger**, on eligible bars where the gate is on, each exactly as its parent record
built it and asserted to reproduce it when the gate is removed:

- **T1** — D359's primary: a fresh `rev_5` entry into the top decile on a name in the
  bottom decile of `mom_252_21`, entered **short**.
- **T2** — D360's mirror, entered **short**: a gap in the **top** 2% of the day on
  top-decile relative volume, in a name eligible after the gap, with D360's exclusions.

**Four cells** gate × trigger; **primary G1 × T1**; multiplicity four, stated. Reported beside
and not counted: each trigger **ungated** (the parent's number) and **gate-off** (the
complement), so the gated mean is read against both.

Entry at the next open, hedged against the floored market, every event taken, no slot
cap, truncated at delisting; a position opened while the gate is on is held to its exit
whether or not the gate turns off.

## 2. Exits

**Cap 10** primary; **cap 20** beside. The parents' invalidation and recovery exits are not
run here (the gate is the object under test).

## 3. Stage 0 — the premise, two numbers per gate

Before any ledger:

1. **Does the gate persist into the horizon it gates?** The correlation between the gate's
   level at t (the 63-bar trailing return; the index minus its 200-bar mean) and the loser
   cohort's hedged drift over the **next 20 bars**, on non-overlapping 20-bar blocks; and
   the cohort's forward-20 drift with the gate on and off.
2. **How often, and in how many pieces?** The share of defined bars the gate is on, the
   number of distinct on-episodes, their lengths, and the years they fall in. This is the
   effective sample the gate null draws from and it is stated before the null is read.

Beside: the floored market's own forward-20 return with the gate on and off (the trades are
hedged; this says what the gate predicts about the hedge itself).

## 4. Nulls, on the primary exit, per cell

- **Gate rotation** *(load-bearing)* — the gate series is circularly shifted in time by a
  random offset, keeping its run structure and on-share exactly, the trigger fixed; the
  gated ledger re-simulated; **200 draws.** Statistic: gross mean per trade of the gated
  ledger; the gated deployed net beside. If a random stretch of history of the same size
  and shape earns what the gated stretch earns, the gate is doing nothing.
- **A′ within the gate** — each name's gated events rotated in time within its eligible
  bars **on which the gate is on**, 100 draws: the trigger's timing inside the regime.
- **B** — the same-day same-`rsi`-bucket random eligible name, defined-percentile pool,
  100 draws, shortfall counted (D360: clustered events run the pool down; stated).
- **C** — random direction on the gated ledger, 1,000.

## 5. Cost, reported beside and deciding nothing

Per trade: `2c` at the held names' median half-spread **on the gated ledger** (spreads widen
when the market falls; the gated line is the one that applies), PUB and PB; GC/HTB borrow,
HTB share; net after both; breakeven half-spread. The deployed base with the 4- and
2-crossing lines. **Exposure**: the share of defined bars with a position, which for a gated
sleeve is the first honest flat-by-default number in the record. Four groups on the primary
cell with the top trade named and its bar shown; by-year and by-episode splits; the `rsi`
interaction.

## 6. Predictions

Q0 is the premise; Q1 is load-bearing; Q5 is against.

| | prediction |
|---|---|
| **Q0** | *(premise)* for G1: the loser cohort's forward-20 hedged drift is **< 0 with the gate on and > 0 with it off**; the gate's level correlates **positively** with the forward drift on non-overlapping blocks; the gate has **at least four** distinct on-episodes. |
| **Q1** | *(load-bearing)* the primary cell (G1 × T1), cap 10: **gross mean per trade > 0 and above the p95 of the gate rotation, A′-within-gate and C.** |
| **Q2** | T1's gated mean exceeds its gate-off mean by **at least 20 bp** per trade (D359: era 1 +27, era 2 0). |
| **Q3** | T2's gated gross mean exceeds its ungated mean (+14.8, D360's mirror with the sign reversed) by at least 10 bp. |
| **Q4** | the primary cell is deployed on **fewer than half** the defined bars (the gate share plus a ten-bar tail). |
| **Q5** | *(against)* the primary cell nets > 0 per trade after the PUB `2c` and borrow. |
| **Q6** | the gated ledger's held half-spread under PUB is **at least 3 bp a side wider** than the parent's ungated ledger's (spreads widen in drawdowns). |
| **Q7** | G2 (the 200-bar gate) gives a lower gated mean than G1 for both triggers: the slower gate stays on into the bounce. |
| *check* | with the gate removed, T1 reproduces D359's primary (8,085 trades, +8.91) and T2 reproduces D360's mirror ledger with the side reversed (20,621 trades, +14.76 gross before borrow), each to 1e-9; the gate rotation keeps the on-share and the run-length multiset exactly. |

## 7. Stop conditions

These state the construction's status. **The avenue is the principal's to close (R15).**

- **Q1 holds** → the gated short is a signal by R15's criterion; cost engineering (hold,
  spread ceiling, fill) and confluences are the next records, on the principal's choice.
- **Q0 fails** → the gate does not forecast the cohort's drift at the horizon; the
  regime split was hindsight; what was not tested is listed (a different gate variable, a
  different horizon, the fade under its own controls ungated).
- **Q0 holds and Q1 fails on the gate rotation** → the regime carries the short's value
  and the trigger adds nothing inside it; the record says so and lists the ungated
  regime-only short (short the loser cohort itself while the gate is on) as untested.
- **Q1 fails on A′ or C only** → the gate works and the trigger's timing inside it does not;
  same listing.
- Nothing is promoted. Book: empty.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[GT]** | both gates equal an independent recomputation from `m_f` to 1e-12; lagged one bar; the on-share, episode count and run lengths printed |
| **[G]** | T1 and T2 with the gate removed reproduce D359's and D360's event matrices exactly; gated ∪ gate-off == ungated, disjoint |
| **[ID]** | the ungated ledgers reproduce the parents' to 1e-9 (T1: 8,085, +8.9095; T2: 20,621 with the side reversed) |
| **[D]** | Stage 0's conditional drifts equal an independent masked mean to 1e-12; the block correlation is recomputed on shuffled blocks and is near zero there |
| **[ROT]** | every gate rotation keeps the on-share and the run-length multiset; the rotated gate is never the observed one; 200 distinct offsets |
| **[A′]** · **[B]** · **[C]** | every rotated event eligible and gate-on, counts kept; date and bucket kept, shortfall counted; C at 3 SE with the observed outside the band |
| **[SB]** · **[S]** | borrow on 200 trades equals the rule; 300 A′ short trades equal the open-fill recomputation to 0.0; +50 bp on a later bar of one held short moves that trade by −50.000 and no other |
| **[HX]** | the hedged deployed series equals the ledger per bar to 1e-12 |
| **[6]** | [GT] raises on a perturbed gate; [ROT] raises on a rotation that changes the on-share; [ID] raises on a perturbed ledger; [S] raises on a sign-flipped ledger |

## 9. Files

`docs/decisions/D361-the-regime-gated-short-the-triggers-the-record-has-behind-a-market-level-gate.md`
(this record) · `scripts/run_d361_regime_gated_short.py` (stages `--selftest`, `--stage0`,
`--cell GATE:TRIGGER --draws N --part p`, `--report`) · `data/d361_stage0.json`,
`data/d361_ctrl_*.json`, `data/d361_regime_gated_short.json` (to follow). Reuses
`scripts/run_d359_loser_rally_short.py` and `scripts/run_d360_news_gap_short.py` (the
triggers), `scripts/run_d358_flat_sleeve.py`, `scripts/run_d349_short_signal_controls.py`,
`scripts/d345_event_book.py`, `scripts/d337_borrow.py`, `scripts/d348_prep.py`,
`scripts/d322_four_group_report.py`.
