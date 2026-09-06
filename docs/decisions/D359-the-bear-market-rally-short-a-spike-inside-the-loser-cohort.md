# D359 — the bear-market rally short: a spike inside the loser cohort, the first short signal reasoned from why the others failed

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). Nothing here is a
result. Nothing here is a book. This is the short-entry layer of the principal's three-layer
design (a ranking names the pool, separate long and short signals enter, a defined exit
under ten bars); the long-entry layer is D350/D353/D358's and the ranking layer is not
tested here.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why, reasoned from the record

Every short signal in the record fails the same way. D352's control A′ is the tell: the names
each of 139 short events picks **rise** at random eligible times, by 18 to 30 bp per forty
bars; the signal's timing is real (11 to 47 bp better than a random day on the same name) and
smaller than that drift. Every score screened puts high-momentum, high-attention names at
its top, and those carry a positive premium. Timing cannot win inside a pool that drifts up.

So a short needs a pool that drifts **down**, ex ante, on the tape, and then timing inside it.
Long-term losers are the one documented negative drift among liquid names — momentum
continuation — and the record has never shorted that end: it shorts the *top* of every
score, so on `mom_252_21` it shorted the winners. And the long side's own finding is the
mirror of what this record proposes: D347, D350 and D358 show a sharp fall bounces best in a
name that is *not* already beaten down. The short analogue is a sharp rise in a name that
*is*: the bear-market rally, short covering and retail, retraced.

## 1. The signal

Both conditions on the lagged, floored (`keep_v2`), deal-filtered (F0), warm-based
cross-sectional percentile at t−1 (D347's closure; `pct` undefined below 50 finite names),
on eligible bars after the hedge is defined:

- **Cohort:** `pct_mom[t] ≤ c`, the bottom c% of `mom_252_21` (the 252-day return less the
  last 21 days; high is a winner). c ∈ {10, 20}.
- **Spike:** a fresh entry of `rev_5` into the top: `pct_rev[t] ≥ s` and `pct_rev[t−1] < s`.
  s ∈ {90, 95}. This is D352's S10 / S5 shape on `rev_5`, restricted to the cohort.
- **Entry:** short at the next open, every event taken (no slot cap), hedged against the
  floored universe's equal-weight return; truncated at delisting.

**Four cells**, c × s; the **primary cell is (10, 90)**; multiplicity four, stated. Reported
beside and not counted: the **complement** (the same spike where `pct_mom[t] > c`) and the
**mirror** (`pct_mom[t] ≥ 100 − c` and a fresh dip `pct_rev[t] ≤ 100 − s`, entered **long**).

## 2. Exits

**Cap 10** is the primary exit (the principal's hold). **Invalidation** — `pct_rev` crosses
back below 50 — capped at 10, reported beside with its own cost line. **Cap 40** reported
beside for comparison with D352 only.

## 3. Stage 0 — the premise, one number each

Before any event is read: the cohort's own drift. For c ∈ {10, 20}, over every eligible
name-bar with `pct_mom[t] ≤ c`, the mean of the hedged next-bar return (`r1T − m`) in bp per
bar, over the span and by era half and by year; the same for the complement and for the
top decile (`pct_mom ≥ 90`). This reads returns and is stated as such. It is what the
timing stage is read against.

## 4. Nulls, on the primary exit, per cell

- **A′** — each name's events rotated in time within its **eligible** bars (D351), 100 draws.
- **B** — D347's: each event's name replaced by a random eligible name in the same `rsi`
  bucket that day, defined-percentile pool, 100 draws. Breaks the cohort by design.
- **B_c** — each event's name replaced by a random eligible name **in the same cohort** that
  day (`pct_mom ≤ c`, not an event name); 100 draws. Isolates the spike's timing inside the
  pool.
- **C** — random direction on the per-trade ledger, 1,000.

Statistics: mean per trade; deployed net PUB bp/bar and Sharpe beside.

## 5. Cost

Per trade: `2c` at the held names' median half-spread, PUB primary and PB beside; **borrow
in the net**, D337's GC/HTB scheme as D352 applied it (HTB by the F0 window or an as-traded
close under $5), the HTB share stated; the breakeven half-spread after commission and
borrow. The deployed base beside, hedged, with the 4-crossing line as pre-registered for
event books and the 2-crossing line beside it (FINDINGS §38 rule 4). Four groups on the
primary cell with the top trade named; by-year, era and down-year splits; the interaction
with the `rsi` bucket.

## 6. Predictions

Q0 is the premise; Q1 is load-bearing; Q4 is against.

| | prediction |
|---|---|
| **Q0** | *(premise)* the bottom-decile cohort's hedged drift on eligible bars is **< 0 bp/bar** over the span and in both era halves; the top decile's is > 0. |
| **Q1** | *(load-bearing)* the primary cell, short, cap 10: **mean per trade > 0 and above the p95 of A′, B_c and C.** |
| **Q2** | A′ for the primary cell is **centred at or below zero** (p50 ≤ 0 in short P&L): for the first time on the short side, the names do not rise at random times. |
| **Q3** | the complement's mean per trade is **at least 10 bp below** the primary cell's: the cohort is doing work the spike alone does not. |
| **Q4** | *(against)* the primary cell nets > 0 per trade after the PUB `2c` and borrow on the cap-10 exit. |
| **Q5** | the invalidation exit's mean per bar held exceeds cap 10's on the primary cell. |
| **Q6** | the mirror (winners' fresh dip, long) has mean per trade > 0: the mechanism is symmetric. |
| **Q7** | the c = 20 cells earn less per trade than the c = 10 cells at the same s. |
| **Q8** | the HTB share of the primary cell's trades exceeds 10%: losers are hard to borrow, and that is on the cost line. |
| *check* | with the cohort condition dropped, the (·, 90) events equal D352's `rev_5`/S10 event matrix and the kernel reproduces its cap-40 short mean exactly. |

## 7. Stop conditions

- **Q0 fails** (the cohort drifts up on the floored universe) → the pool does not exist where
  the programme trades; the timing stage runs and is read as D352 was, and the record says
  the floor removed the losers that fall.
- **Q1 holds** → the short entry of the three-layer design exists per trade on the loser
  cohort; its cost line, with borrow, decides whether it is tradeable, and the breakeven
  half-spread waits on D336. Nothing is promoted.
- **Q1 fails** → there is no short entry on the loser cohort at these shapes; the short side
  of the design stays open and the record says the cohort was the right question and the
  spike the wrong answer, or the pool is not there (Q0 says which).
- Nothing is promoted. Book: empty.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[G]** | event counts per cell; with the cohort dropped, (·, 90) equals D352's `rev_5`/S10 matrix and its cap-40 short mean to 1e-9; the cells partition the spike events with the complement |
| **[E]** | 300 sampled events per cell satisfy both conditions on the raw lagged scores at t−1, the spike is fresh at t−2, and the unlagged rule fails on every sample |
| **[D]** | Stage 0's drift equals an independent masked mean of `r1T − m` to 1e-12 |
| **[SB]** | borrow on 200 sampled trades equals the rule × bars held / 252; every HTB flag agrees with the rule |
| **[S]** | sign in money: a short on a name that falls pays positively; the mirror's long on the same path pays oppositely; 300 A′ trades equal the open-fill recomputation to 0.0 |
| **[A′]** · **[B]** · **[B_c]** · **[C]** | every rotated event eligible, counts kept; date and bucket kept, defined-percentile pool; every B_c replacement in the cohort that day, never an event name, counted shortfall; C's mean within 3 SE of zero and the observed outside the band |
| **[HX]** | the hedged deployed series equals the ledger per bar to 1e-12 |
| **[6]** | [S] raises on a sign-flipped ledger; [G] raises with the cohort mask perturbed; [B_c] raises when a replacement outside the cohort is admitted; [D] raises on a perturbed mask |

## 9. Files

`docs/decisions/D359-the-bear-market-rally-short-a-spike-inside-the-loser-cohort.md` (this
record) · `scripts/run_d359_loser_rally_short.py` (stages `--selftest`, `--stage0`, `--cell
C:S --draws N --part p`, `--report`) · `data/d359_stage0.json`, `data/d359_ctrl_*.json`,
`data/d359_loser_rally_short.json` (to follow). Reuses `scripts/d345_event_book.py`,
`scripts/run_d349_short_signal_controls.py` (the short conventions and borrow),
`scripts/run_d352_short_timing_screen.py`, `scripts/run_d347_long_signal_controls.py`,
`scripts/run_d358_flat_sleeve.py` (the event and deployed-base helpers), `scripts/d348_prep.py`,
`scripts/d337_borrow.py`, `scripts/d322_four_group_report.py`.
