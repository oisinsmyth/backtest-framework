# D359 RESULT — the loser cohort does not drift down on the floored universe, the spike inside it earns what a random cohort name earns, and the mirror is the number worth pre-registering

**Status:** RESULT. Pre-registered at `c05a483`, runner at `c73239f` — both before this file
existed (R8). `keep_v2`, F0, next-open fill, hedged against the floored market, D345's kernel
with the hedged series, no slot cap, PUB primary, PB beside, GC/HTB borrow in the net. Four
cells, multiplicity four.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. The short side has no drifting pool on this universe.**

---

## 1. The verdict

**Two of nine, and the premise failed.** Stage 0 — the cohort's own drift, read before any
event — says the bottom decile of 12-month momentum on the floored universe drifts **up**:
+0.64 bp/bar hedged over the span, down only in era 1 (−2.36) and the down-years (−2.88).
The pool the signal was reasoned into does not exist where the programme trades. The timing
inside it — the primary cell, a fresh `rev_5` spike into the top decile on a name in the
bottom momentum decile, short, held ten bars — is **+8.9 bp a trade on 8,085 trades**, inside
every control: its own names at random eligible times (A′ p95 +21.7), a random same-day
same-bucket name (B p95 +14.1), **a random same-day name from the same cohort (B_c p95 +9.3)**
and random direction (C p95 +17.9). Three names are half its P&L.

| Stage 0, hedged next-bar drift, bp/bar [name-bars] | span | era 1 | era 2 | down-years |
|---|--:|--:|--:|--:|
| bottom momentum decile | **+0.64** [189k] | −2.36 [62k] | +2.09 [128k] | −2.88 [44k] |
| bottom momentum quintile | −0.09 | −1.36 | +0.52 | −2.55 |
| above the decile | +0.35 | +0.37 | +0.35 | +1.15 |
| top momentum decile | +3.85 | +1.64 | +4.92 | +4.40 |

By year the loser decile fell in 2014, 2015, 2017 and 2024 (−3.6, −12.2, −2.4, −5.3) and rose
in every other full year (2016 +6.8, 2020 +8.3, 2021 +7.0). `mom_252_21` is defined from late
2013 on the warm base; 2013 carries 284 name-bars.

## 2. Why the pool is not there

The floor (D339, D343) is the universe: an as-traded close above $5 at t−1 and a passing
21-observation dollar-volume window, the name replaced when it fails. The momentum
literature's losers keep losing because the ones that fall through $5 and lose their volume
are still in its sample; here they leave the universe as they fall, and D339's census already
showed that the tail the floor removes is where every short's top trade lived. **What remains
of the loser decile after the floor is the part that bounced.** It drifts down only when the
market does — era 1, the down-years — which is a regime fact and the allocator's gate, not a
signal's.

## 3. The cells

| short, bp per TRADE | exit | n | mean | median | t | hold | 2c PUB | 2c PB | borrow | HTB | net PUB | net PB | era 1 | era 2 | down |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **cell 10 / 90** | **cap 10** | 8,085 | **+8.9** | +27.9 | 0.8 | 10.0 | 91.1 | 45.4 | 2.0 | 0.1% | **−84.2** | −38.5 | +27.0 | +0.1 | +45 |
| cell 10 / 90 | inv 10 | 9,099 | +12.7 | +126.2 | 1.6 | 5.5 | 92.8 | 46.4 | 1.1 | 0.1% | −81.2 | −34.9 | +18.1 | +9.9 | +39 |
| cell 10 / 90 | cap 40 | 4,233 | −10.3 | +16.4 | −0.3 | 40.0 | 87.0 | 41.4 | 8.0 | 0.1% | −105.3 | −59.6 | +78.3 | −54.0 | +89 |
| complement 10 / 90 | cap 10 | 45,291 | +4.8 | +11.1 | 1.4 | 10.0 | 62.2 | 31.9 | 2.0 | 0.0% | −59.4 | −29.0 | +10.5 | +2.1 | −0 |
| cell 10 / 95 | cap 10 | 5,600 | +4.0 | +25.2 | 0.3 | 10.0 | 95.2 | 54.5 | 2.0 | 0.1% | −93.2 | −52.5 | +32.8 | −10.8 | +64 |
| cell 20 / 90 | cap 10 | 13,913 | +10.5 | +24.1 | 1.3 | 10.0 | 79.6 | 38.4 | 2.0 | 0.1% | −71.1 | −30.0 | +22.1 | +4.6 | +30 |
| cell 20 / 95 | cap 10 | 8,894 | +5.0 | +24.4 | 0.5 | 10.0 | 85.5 | 45.0 | 2.0 | 0.1% | −82.5 | −41.9 | +24.8 | −5.2 | +40 |

**Nothing here is a signal.** The cohort adds 4 bp over the spike outside it (Q3 wanted 10),
the wider cohort earns more than the narrower (Q7), and no cell's t reaches 1.4. The held
names are **40 to 47 bp a side** under PUB (19 to 27 under PB): the loser decile is the wide
end of the floored universe, and the round trip is 80 to 97 bp against means under 11. Borrow
is 2 bp a trade and the HTB flag fires on 0.1% — the rule keys on the F0 window and a $5
close, so losers above $5 are never flagged; Q8 is falsified by the rule, and the borrow line
on this cohort is a floor, not a measurement.

**Where it worked.** Every cell is positive in era 1 and the down-years (+27 and +45 a trade
on the primary; +78 and +89 at cap 40) and at or below zero in era 2. The short side earns
when the loser cohort falls, which is when the market falls.

## 4. The controls

| cap 10, bp per trade, 100 draws | observed | A′ p50 / p95 | B p50 / p95 | B_c p50 / p95 | C p95 | above |
|---|--:|--:|--:|--:|--:|---|
| cell 10 / 90 | +8.9 | +3.6 / +21.7 | +3.5 / +14.1 | −6.8 / +9.3 | +17.9 | none |
| cell 10 / 95 | +4.0 | +5.3 / +22.7 | +6.8 / +16.6 | −7.5 / +7.4 | +23.4 | none |
| cell 20 / 90 | +10.5 | +3.0 / +14.7 | +3.8 / +12.0 | −0.8 / +7.3 | +13.4 | B_c only |
| cell 20 / 95 | +5.0 | +3.4 / +18.0 | +5.7 / +16.2 | −1.1 / +9.3 | +18.3 | none |

A′ is centred at +3 to +5 in short P&L: these particular names, at random eligible times,
fall slightly over ten bars — but the observed is inside A′'s p95 on every cell, so the spike's
day is not better than a random day on the same name. B_c is the control that matters and it
is centred at −1 to −7: a random name from the same cohort on the same day *rises* over the
next ten bars, so the spike does pick the worse ten days in the cohort — by about 15 bp at
the median and not beyond the p95. On the deployed base (hedged, cap 10) the primary is
−17.5 net PUB against A′ p95 −12.7 and B_c p95 −16.5: below both.

## 5. Four groups, the primary cell

n 8,085 · mean +8.9 · median +27.9 · win 51.6% · payoff 0.96 · hold 10.0 · skew −0.4 · kurtosis
8.6 · trims: ex-top −27.8, ex-bottom +51.0, symmetric +14.3 · **names to half the P&L: 3 of
785** · top-1 / 5 / 10 name share 21% / 99% / 180% · profitable years 9 of 14 · **top trade DBI
entered 2020-03-05 at $13.65, DV percentile 30, held 10 bars, +8,778 bp = 12.2% of the P&L**
— a retailer in the COVID crash. Dead names +38.0 on 1,749 against alive +0.9 on 6,336; the
cheaper half +12.0 against +5.8. Median above mean, one name a fifth of the total, five names
the whole of it: the +8.9 is a handful of crash trades.

**The `rsi` interaction** is the same picture as D352's: no bucket is systematically the
short's best ground; the (2, 5] bucket is −379 on 65 trades and the (90, 95] bucket +87 on
663 — the deeply oversold loser that spikes keeps going.

## 6. The mirror, beside and not read

The pre-registration reported the mirror — a fresh `rev_5` dip into the bottom decile on a
name in the **top** decile of 12-month momentum, entered **long** — as a mechanism check and
counted it in no multiplicity. It is the largest per-trade number in the record:

| mirror, long, bp per TRADE | n | mean | median | t | 2c PUB | 2c PB | net PUB | net PB | era 1 | era 2 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 10 / 90, cap 10 | 7,290 | **+68.6** | +36.6 | 5.9 | 83.6 | 36.9 | −15.0 | +31.7 | +7.9 | +95.0 |
| 10 / 90, inv 10 | 8,190 | +47.2 | +123.4 | 5.8 | 85.5 | 36.9 | −38.3 | +10.3 | −0.5 | +67.5 |
| **10 / 90, cap 40** | 3,932 | **+160.5** | +51.5 | 5.1 | 77.7 | 31.6 | **+82.9** | +129.0 | +16.9 | +227.4 |
| 10 / 95, cap 10 | 4,955 | +74.5 | +36.1 | 4.8 | 88.4 | 32.1 | −13.9 | +42.4 | −8.4 | +108.0 |
| 20 / 90, cap 10 | 12,486 | +52.1 | +31.1 | 6.4 | 73.7 | 32.9 | −21.6 | +19.2 | +5.5 | +72.6 |

**No null was run on it, no four-group report, no top trade named, and it is era 2 almost
entirely.** D353's `rev_5` bottom-decile long, on every name, is +43.4 a trade at cap 40 and
−18.6 net PUB; restricting the same dip to 12-month winners is +160.5 and +82.9. That is
consistent with D347, D350 and D358 — a fall bounces best in a name that is not beaten down —
taken to its end: the strongest names. It is an observation. It becomes a finding only under
its own pre-registration with A′, B, B_c and C, the four groups with the top trade named, and
the deployed base, and STACK §6 puts that first.

## 7. Predictions

| | | |
|---|---|---|
| **Q0** *(premise)* | **FALSIFIED** | bottom decile +0.64 over the span, −2.36 / +2.09 by era; top decile +3.85 |
| **Q1** *(load-bearing)* | **FALSIFIED** | +8.9; inside A′ (+21.7), B_c (+9.3) and C (+17.9) |
| Q2 | FALSIFIED | A′ p50 +3.55, not ≤ 0 |
| Q3 | FALSIFIED | complement +4.8, gap 4.1 |
| Q4 *(against)* | FALSIFIED — the "against" held | −84.2 net PUB after borrow |
| Q5 | CONFIRMED | +2.32 per bar held (inv 10) against +0.89 (cap 10) |
| Q6 | CONFIRMED | mirror +68.6 on 7,290 |
| Q7 | FALSIFIED | 20% cohort +10.5 and +5.0 against 10% +8.9 and +4.0 |
| Q8 | FALSIFIED | HTB 0.1% — by the rule, not the market |
| *check* | held | (·, 90) == D352's `rev_5`/S10 row (73,109 events, grid statistic to 1e-9); the kernel reproduces D352's `retrace_leg`/S10 cap-40 mean to 1e-9; D352 stored no kernel number for `rev_5`/S10 (here −7.2 on 27,596) |

## 8. Stop conditions, executed

- **Q0 fails → the pool does not exist where the programme trades**, and the record says the
  floor removed the losers that fall. The timing stage ran and reads as D352 did.
- **Q1 fails → no short entry on the loser cohort at these shapes.** Q0 says which of the two
  readings applies: the pool is not there. The short side of the three-layer design stays
  open, and on this universe it is regime-conditional or nothing.
- Nothing is promoted. Book: empty.

## 9. Deviations and what the run found

- **Q8's borrow rule** flags HTB by the F0 window or an as-traded close under $5 (D337); it
  cannot see a loser above $5. The prediction was about the market and the rule answered
  about itself. The borrow line on this cohort is a floor.
- **The kernel's short invalidation** exits when the score crosses to ≤ 50, and the cap is
  ORed with the trigger under every exit, so invalidation-at-10 is native; the ledger's ages
  are asserted ≤ 10.
- **D352 stored `rev_5`/S10 as a grid row only** (it was not a kernel survivor); [G]
  reproduces the row exactly and asserts the kernel identity on the stored `retrace_leg`/S10
  cap-40 mean instead.
- **Stage 0's hedge** is the floored market (`m_f`, what the ledger rebuild uses), on eligible
  name-bars with a finite next-bar return; [D] recomputes every group × subset cell
  independently to 3.6e-15.
- **The `rsi` interaction** uses a forward-10 short base rate to match the cap-10 horizon;
  D352's was forward-40.
- The 2-crossing deployed line is `rt = 2·hs`, `rtc = 2·commission` at the same turnover,
  asserted equal to half the 4-crossing cost.

## 10. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[G]** | four cells partition the spike with their complements; 73,109 == D352's `rev_5`/S10 events, grid statistic −21.8990 to 1e-9; `retrace_leg`/S10 cap-40 short mean −3.8106 to 1e-9 on 23,108 trades |
| **[E]** | 300 events per cell satisfy both conditions on the raw lagged scores at t−1, fresh at t−2, grid match 0.0, unlagged rule fails on every sample |
| **[D]** | 111 group × subset cells to 3.6e-15 |
| **[SB]** | 200 trades to 0.0; HTB 7 of 8,085 by the rule |
| **[S]** | 300 A′ short trades equal the open-fill recomputation bit-identically; 137 fell / 163 rose; the long on the same path is −pnl to 0.0; +50 bp on WLT 2013-12-27 moves one short by −50.000 and the deployed series by −10.000 = −50 / 5 open, no other bar; the mirror's +50 bp on GGAL moves one long by +50.000 |
| **[A′]** · **[B]** · **[B_c]** · **[C]** | every rotated event eligible, counts kept; date and bucket kept, defined pool, 0 kept; every B_c replacement in the cohort that day and never an event name, 11,404 replaced, 0 kept; C z −0.8 at 3 SE with the observed inside the band, stated |
| **[HX]** | hedged and unhedged deployed series equal the ledger per bar to 5e-15 on all cells × exits |
| **[6]** | [S] raises on a sign-flipped ledger; [G] raises on a perturbed cohort; [B_c] raises on an out-of-cohort replacement; [D] raises on a perturbed mask |

**Speed:** self-test 14 s; A′ 0.5 s a draw, B 0.7, B_c 0.4; four cells in parallel under 3
min; Stage 0 and report under 30 s; peak working set 1.07 GB.

## 11. What this establishes

1. **On the floored universe the short side has no drifting pool.** The loser decile rises
   over the span; every short signal since D335 has been timing inside a pool that rises,
   and that is now a statement about the universe under its floor, not about a signal.
2. **The short side's value is regime-conditional**: the loser cohort falls, and the rally
   short pays before cost, in era 1 and the down-years only. That is the allocator's gate.
3. **The premise check did its job.** Without Stage 0 this record would have read "timing
   exists, cost eats it"; with it, "the pool is not there", which is a different next study.
4. **The winners' dip is the next long to pre-register.** +160 a trade at cap 40 and +83 net
   PUB is the largest per-trade number in the record and it has no null yet.

## 12. Files

`data/d359_stage0.json` · `data/d359_ctrl_{10,20}_{90,95}_p0.json` · `data/d359_loser_rally_short.json`
· `scripts/run_d359_loser_rally_short.py` · reuses `scripts/run_d358_flat_sleeve.py`,
`scripts/run_d349_short_signal_controls.py`, `scripts/run_d352_short_timing_screen.py`,
`scripts/d345_event_book.py`, `scripts/d337_borrow.py`, `scripts/d348_prep.py`,
`scripts/d322_four_group_report.py`.
