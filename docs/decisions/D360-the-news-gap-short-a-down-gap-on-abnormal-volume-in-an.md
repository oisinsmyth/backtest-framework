# D360 — the news-gap short: a down-gap on abnormal volume in an ordinary name, the drift after bad news read off the tape

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D360-the-news-gap-short-a-down-gap-on-abnormal-volume-in-an-ordinary-name.md`. The H1 above is the full title.*

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book. This is the second attempt at the short-entry layer of the
principal's three-layer design; D359 was the first and found the short side has no drifting
pool among *levels* on the floored universe.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why, reasoned from the record

Two facts. D352 Q6: the only names that fall at random times on this universe are the
tops of the volatility and spread levels, by 19–29 bp per forty bars — the high-volatility,
wide, hard-to-borrow end, where the drift is smaller than the cost of trading it. D359: the
long-term losers drift up once the floor removes the ones that keep falling. Every short so
far was a **level**, and a level selects exactly the names that are expensive to short. On
a liquid, above-$5 universe a level cannot be the short.

So the short has to be an **event in an ordinary name**. The one documented negative drift
that lives in liquid, tight, easy-to-borrow names is the drift after bad news — the
post-announcement drift on a negative surprise — and a news day is visible on the tape
without a calendar: a large gap on abnormal volume. A large **down**-gap on abnormal volume
is a negative surprise, and the drift continues for weeks.

This enters a name that has just *fallen*, which the long side says bounces. The
distinction is informational and separable on the tape: a five-day drift down with no gap
is technical and bounces (`rev_5`, real on every control); a one-day gap down on volume is
news and continues. That distinction also predicts something about the existing long
(Q7): `rev_5`'s bottom-decile entries that arrived by a volume gap should earn less than
the rest.

## 1. The signal

On day g, for every name with `elig` true at g+1 (so the name is still above the floor
**after** the gap):

- **Gap:** `gap[g] = open(g) / close(g−1) − 1`, derived from the panel's own bars (the
  open→close and close→close returns the kernel uses; asserted against the raw bars).
  Condition: `gap[g]` in the **bottom p%** of the day's eligible cross-section, p ∈ {2, 5}.
- **Volume:** `rv[g] = VOL(g) / median(VOL(g−21 … g−1))`, the day's relative volume;
  condition: `rv[g]` in the **top q%** of the day's eligible cross-section, q ∈ {10, 20}.
- **Event at t = g+1**, entered **short at open(g+1)**, hedged against the floored market,
  every event taken, no slot cap, truncated at delisting. A name already held is skipped
  and counted.

**Four cells** p × q; **primary (2, 10)**; multiplicity four, stated. Reported beside and not
counted: the **no-volume arm** — the same gap with `rv` below the day's median (the
information without the attention); and the **mirror** — a gap in the **top** p% on
top-q% volume, entered **long** (the other half of the mechanism).

**Exclusions, declared:** an event on an ex-distribution day (a dividend or distribution of
at least 1% of the prior close in the events file) is not a news gap and is excluded,
counted; a gap day with zero volume or a non-finite prior close is excluded, counted.

## 2. Exits

**Cap 10** primary. **Cap 20** beside (the drift continues). **Recovery** beside: exit when the
close has retraced half the gap (`close(t) ≥ open(g) + 0.5·(close(g−1) − open(g))`), capped
at 20, implemented through the kernel's own exit mechanism on a per-name grid that keys on
the name's most recent event.

## 3. Stage 0 — the premise

The event *is* the pool here, so the premise is the event's own drift: the mean hedged
forward 10- and 20-bar return after the primary cell's events, beside the same statistic
for the no-volume arm and for the same names on random eligible days. Read before the
ledger, printed as one table.

## 4. Nulls, on the primary exit, per cell

- **A′** — each name's events rotated in time within its eligible bars, 100 draws.
- **B** — each event's name replaced by a random eligible name in the same `rsi` bucket on
  the same day, defined-percentile pool, 100 draws. This keeps the **day**, which matters:
  news gaps cluster in earnings seasons and crashes.
- **C** — random direction on the per-trade ledger, 1,000.

Statistics: mean per trade; deployed net PUB bp/bar and Sharpe beside.

## 5. Cost

Per trade: `2c` at the held names' median half-spread, PUB primary and PB beside; **borrow in
the net** at D337's GC/HTB scheme, the HTB share stated (the rule keys on the F0 window and a
$5 close, as D359 §9 records); the breakeven half-spread after commission and borrow. The
deployed base beside with the 4-crossing line as pre-registered for event books and the
2-crossing line beside (FINDINGS §38 rule 4). Four groups on the primary cell with the top
trade named and its bar shown; by-year, era and down-year splits; the `rsi` bucket
interaction.

## 6. Predictions

Q1 is load-bearing. Q4 is against.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the primary cell, short, cap 10: **mean per trade > 0 and above the p95 of A′, B and C.** |
| **Q2** | the no-volume arm's mean per trade is **at least 20 bp below** the primary cell's: the volume is the information. |
| **Q3** | the mirror (volume gap up, long) has mean per trade > 0 at cap 10. |
| **Q4** | *(against)* the primary cell nets > 0 per trade after the PUB `2c` and borrow at cap 10. |
| **Q5** | the primary cell's held half-spread under PUB is **below 30 bp a side** (D359's loser cohort was 40–47; D285's held names 33.8): these are ordinary names. |
| **Q6** | cap 20's mean per trade exceeds cap 10's on the primary cell: the drift continues. |
| **Q7** | in D353's `rev_5` bottom-decile cap-40 long ledger (reproduced to 1e-9 first), entries whose trigger bar was a primary-cell gap day earn **at least 15 bp less** per trade than the rest. |
| **Q8** | the primary cell's HTB share is below 2% and its borrow below 3 bp a trade. |
| **Q9** | era 1's mean per trade exceeds era 2's on the primary cell: the drift has weakened, as the literature says it has. |
| *check* | the derived gap equals the raw bars' open / prior close on 300 sampled events to 1e-12; the excluded ex-distribution and zero-volume gaps are counted; the `rev_5` ledger reproduces D353 before Q7's split. |

## 7. Stop conditions

- **Q1 holds** → the short entry of the three-layer design exists per trade, as an event in
  ordinary names; its cost line decides; the breakeven half-spread waits on D336.
- **Q1 fails and Q2 holds** → the information is on the tape and the drift is inside the
  name's own noise at these horizons; the record says so and stops.
- **Q1 fails and Q2 fails** → news gaps carry no drift on this universe; with levels (D352),
  loser rallies (D359) and news events all tried, the short side of the design closes on
  tape signals, and what remains is a regime gate or data from outside the tape.
- Nothing is promoted. Book: empty.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[GAP]** | the derived gap equals `open(g) / close(g−1) − 1` from the raw panel bars on 300 sampled events to 1e-12; `rv` equals a direct recomputation from `VOL` |
| **[E]** | 300 sampled events per cell satisfy both cross-sectional conditions on day g by direct count among eligible names, and `elig` holds at g+1 |
| **[XD]** · **[V0]** | no surviving event is on an ex-distribution day (≥ 1% of the prior close) or a zero-volume bar; the excluded counts printed |
| **[G]** | cells partition the volume gap-downs with their complements; the no-volume arm is disjoint from every cell |
| **[R5]** | the `rev_5` bottom-decile cap-40 long ledger equals D353's (27,316 trades, +43.3806) to 1e-9 before the Q7 split; the split covers every trade |
| **[SB]** | borrow on 200 sampled trades equals the rule × bars held / 252 |
| **[S]** | sign in money on the short: 300 A′ trades equal the open-fill recomputation to 0.0; a name that falls pays positively; +50 bp on a later bar of one held short moves that trade by −50.000 and no other |
| **[A′]** · **[B]** · **[C]** | every rotated event eligible, counts kept; date and bucket kept, defined pool, shortfall counted; C at 3 SE with the observed outside the band |
| **[HX]** | the hedged deployed series equals the ledger per bar to 1e-12 |
| **[REC]** | on the recovery exit, every closed trade either hit the cap or closed on the first bar the half-gap condition held, asserted on 300 sampled trades against the raw closes |
| **[6]** | [GAP] raises on a perturbed open; [S] raises on a sign-flipped ledger; [XD] raises when an ex-distribution event is admitted; [R5] raises on a perturbed ledger |

## 9. Files

`docs/decisions/D360-the-news-gap-short-a-down-gap-on-abnormal-volume-in-an.md`
(this record) · `scripts/run_d360_news_gap_short.py` (stages `--selftest`, `--stage0`, `--cell
P:Q --draws N --part p`, `--report`) · `data/d360_stage0.json`, `data/d360_ctrl_*.json`,
`data/d360_news_gap_short.json` (to follow). Reuses `scripts/d345_event_book.py`,
`scripts/run_d359_loser_rally_short.py` and `scripts/run_d358_flat_sleeve.py` (the event, cost
and control helpers), `scripts/run_d349_short_signal_controls.py` (the short conventions and
borrow), `scripts/run_d353_rev5_record.py` (for Q7), `scripts/d348_prep.py`, `scripts/d337_borrow.py`,
`scripts/d322_four_group_report.py`.
