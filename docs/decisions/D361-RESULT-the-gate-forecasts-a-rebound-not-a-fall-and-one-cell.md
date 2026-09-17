# D361 RESULT — a negative trailing market return forecasts a rebound in the loser cohort, not a fall; the gated loser rally fails; and one cell, the gap-up fade with the market below its 200-day mean, is above every control

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D361-RESULT-the-gate-forecasts-a-rebound-not-a-fall-and-one-cell-the-gap-up-fade-in-a-bear-market-is-above-every-control.md`. The H1 above is the full title.*

**Status:** RESULT. Pre-registered at `0773ad7`, runner at `8f095e5` — both before this file
existed (R8). `keep_v2`, F0, next-open fill, hedged against the floored market, D345's kernel
with the hedged series, no slot cap, PUB primary, PB beside, GC/HTB borrow in the net. Four
cells, multiplicity four. The signal criterion is R15's: gross mean per trade above the
controls; cost reported beside and deciding nothing.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. The avenue's status is the principal's decision (R15).**

---

## 1. The verdict

**Two of eight; the premise and the load-bearing prediction failed; a non-primary cell
passed every control.**

**The premise inverted.** With the floored market's trailing 63-bar return below zero, the
loser cohort *rises* **+96 bp over the next 20 bars** (55,966 name-bars) and falls 16 bp when
the gate is off; the market itself returns +188 bp over the next 20 bars with the gate on
against +80 off. The block correlation between the gate's level and the cohort's forward
drift is **−0.23** on 159 non-overlapping blocks, against a shuffled |r| p95 of 0.16: the
gate forecasts, and what it forecasts is a rebound. D359's era-1 and down-year splits were
averages over stretches that contained both the falls and the rebounds; as a *state* the
gate picks the rebounds.

**The primary cell fails.** The loser-rally short with the 63-day gate on is **−4.5 bp a
trade on 2,516 trades**, inside the gate rotation (p95 +56.5 at 200 draws), inside A′ within
the gate (+25.2), inside B and C. Gate off it is +22.5 (t 1.7). The gate removes the trades
that paid.

**One cell is above every control.** The gap-up fade — D360's mirror entered short, a gap
in the top 2% of the day on top-decile volume — with the market **below its 200-day mean**:

| G2 × T2, short, cap 10 | n | gross mean | median | t | ROT p50 / p95 | A′ p50 / p95 | B p50 / p95 | C p95 | above |
|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| gated | 3,977 | **+42.3** | +16.9 | 2.5 | +14.7 / +36.0 | +2.9 / +25.8 | +22.9 / +37.7 | +25.2 | **all four** |
| gate off | 16,808 | +9.6 | +16.0 | 1.3 | | | | | |
| ungated (D360's mirror) | 20,621 | +14.8 | +16.0 | 2.1 | | | | | |

A random gate of the same shape and share gives the fade +14.7 at the median — the ungated
number — and +36.0 at the p95; the trigger's own names at random gate-on times give +2.9 /
+25.8; a random same-day same-bucket name in the regime gives +22.9 / +37.7. **The gate adds
about +27 a trade over a random gate, and the trigger adds about +40 over its own names in
the regime.** By R15's criterion this is a positive gross mean above the nulls. It is the
third cell of four, the primary failed, and the margins over the rotation and B p95s are 6
and 5 bp; §6 says what that is worth.

| cap 10, gated, bp per TRADE | n | gross | median | t | held ½-spread PUB | 2c PUB | borrow | HTB | net PUB | net PB | era 1 | era 2 | down |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **G1 × T1** (primary) | 2,516 | **−4.5** | +25.2 | −0.2 | 50.4 | 104.5 | 2.0 | 0.1% | −111.0 | −47.3 | +22.7 | −14.6 | +50 |
| G1 × T2 | 5,609 | +15.6 | +14.9 | 1.1 | 37.9 | 78.8 | 2.6 | 3.5% | −65.8 | −23.4 | +9.7 | +19.5 | +36 |
| G2 × T1 | 1,931 | +4.2 | +11.0 | 0.2 | 56.2 | 116.3 | 2.0 | 0.2% | −114.2 | −40.3 | +44.6 | −9.9 | +42 |
| **G2 × T2** | 3,977 | **+42.3** | +16.9 | 2.5 | 42.0 | 86.9 | 2.6 | 3.7% | −47.2 | **+3.3** | +18.9 | +55.1 | +50 |

## 2. The gates

| | defined from | on-share | episodes | run length min / median / max | cohort fwd-20 on / off | market fwd-20 on / off |
|---|---|--:|--:|--:|--:|--:|
| G1: 63-bar return < 0 | 2010-07-06 | 28.5% | 98 | 1 / 3 / 101 | +96.2 / −15.9 | +188 / +80 |
| G2: below the 200-bar mean | 2011-01-19 | 21.7% | 62 | 1 / 2 / 160 | +105.7 / −8.5 | +180 / +80 |

Both gates are on in the stretches one would name — mid-2011, mid-2012, June to November
2015, October 2018 to January 2019, February to June 2020, January to April 2022, February
to June 2025 — and in dozens of one- to three-bar flickers around them. Half the episodes
have fewer than four bars; the ten longest hold 55% of the primary's trades.

## 3. What the primary's episodes say

The gated loser rally is a coin flip by episode: 78 episodes with trades, 42 positive. The
largest are the market's turns — **+47,206 bp over 249 trades in June to November 2015**,
**−44,591 over 142 in January to March 2016**, **−29,977 over 184 in the COVID crash**,
+17,531 over 191 in the first four months of 2022 and −19,178 over 109 in its summer. The
short pays while the market is still falling and gives it all back when the market turns,
and the 63-day gate cannot tell the two apart because it is on for both. That is the
mechanism behind Stage 0's inversion.

## 4. Cost, beside

Spreads widen in the regime: the primary's held half-spread is **50.4 bp a side against
43.6 ungated** (Q6 confirmed), and G2 × T1's is 56. The gap-up fade's names are cheaper (38
to 42 a side, PB 18 to 19) and general collateral on 96%. G2 × T2 nets **+3.3 under PB and
−47 under PUB** after borrow; its breakeven half-spread after commission and borrow is 18.4
bp a side. Cost decides nothing here (R15); it says what the engineering has to close.

**Exposure.** The gated arms are the first flat-by-default constructions in the record: the
primary holds a position on 42% of the kernel's defined bars (33% of the gate's), G2 × T2 on
28%. Q4 confirmed.

## 5. Predictions

| | | |
|---|---|---|
| **Q0** *(premise)* | **FALSIFIED** | cohort +96 on / −16 off; corr −0.23; 98 episodes |
| **Q1** *(load-bearing)* | **FALSIFIED** | −4.5; ROT p95 +56.5, A′ +25.2, C +38.2 |
| Q2 | FALSIFIED | gated −4.5 against off +22.5, gap −27 |
| Q3 | FALSIFIED | G1 × T2 +15.6 against +14.8, gap +0.8 |
| Q4 | CONFIRMED | 41.9% of defined bars |
| Q5 *(against)* | FALSIFIED — the "against" held | −111 net PUB |
| Q6 | CONFIRMED | 50.4 against 43.6 a side |
| Q7 | FALSIFIED | G2 above G1 on both triggers (+4.2 vs −4.5; +42.3 vs +15.6) |
| *check* | held | T1 == D359 (8,085, +8.9136 — the pre-registration wrote +8.9095, a transcription; the stored file governs); T2 == D360's mirror reversed (20,621, +14.7555); 200 distinct offsets, on-share and circular run multiset kept in every draw, the wrap splitting one run in 49 |

## 6. Stop conditions, executed — and what the record does not decide

- **Q0 fails** → the 63-day gate does not forecast a falling cohort; it forecasts a
  rebound. The regime split in D359 was an average over both halves of a drawdown, not a
  state.
- **Q1 fails on every control** → the loser rally has no timing value inside the regime.
- **G2 × T2 is above every control**, on a non-primary cell of four, by 5 to 6 bp at the
  p95s and by 27 to 40 bp at the medians. Under R15 it is a positive gross mean above the
  nulls. The record states it and does not promote it: the honest next step is **its own
  pre-registration as the primary**, on the same fixture with the multiplicity of one and
  the gate's parameters fixed before the run, plus the two neighbours that would tell
  whether it is a cell or a region — the 100- and 150-bar means, and the 5% gap. Whether
  to spend that is the principal's decision.
- **Untested and listed:** the loser cohort as a *long* after a negative 63-day market
  return (Stage 0's +96 bp per 20 bars, hedged, on 56,000 name-bars, with no controls run);
  the fade under a gate defined on volatility rather than return; the regime-only short
  (short the cohort itself with the gate on) — Stage 0 says it would lose.
- Nothing is promoted. Book: empty. The avenue is the principal's.

## 7. Deviations and what the run found

- **The pre-registration's check value for T1 was a transcription** (+8.9095 written,
  +8.9136 stored); the runner asserts against the stored file and prints the discrepancy.
- **The rotation's wrap** splits one run in 49 of 200 draws; the circular run multiset and
  the on-share are kept exactly in every draw; reported, not relaxed. Offsets are drawn
  without replacement so 200 draws are 200 distinct gates.
- **The 63-bar return is compounded** from `m_f` (a simple return); the additive sum would
  flip the gate on 74 of 4,061 bars. G2 is evaluated on the index levels directly.
- **Stage 0's block correlation** drops blocks with no cohort name at the block start (44
  of 159 for G1; the cohort is undefined before late 2013).
- **[C]** at 3 SE, as D358–D360. No assertion weakened.

## 8. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | via the shared prep |
| **[GT]** | both gates equal a plain-Python loop to 0.0 / 1.6e-15; lagged (moving `m_f[t]` moves only `level[t+1]`); on-share, episodes and run lengths printed with their years |
| **[G]** · **[ID]** | T1 == D359's event matrix (11,404), T2 == D360's mirror (24,736), gated ∪ off == ungated, disjoint; ungated T1 8,085 / +8.9136 and T2 20,621 / +14.7555 == the parents' stored ledgers to 1e-9, T2 trade for trade against a long re-run |
| **[D]** | conditional drifts == an independent masked mean to 1.4e-14; the block correlation on shuffled levels is +0.008 (z 0.1) and +0.065 (z 0.8) |
| **[ROT]** | 200 distinct offsets; on-share and circular run multiset kept in every draw; never the observed gate; off outside the defined range |
| **[A′]** · **[B]** · **[C]** | every rotated event eligible and gate-on, counts kept; date and bucket kept, 0 shortfall on the primary; C z −0.5 at 3 SE with the observed inside the band, stated |
| **[SB]** · **[S]** | 200 trades' borrow == the rule; 300 A′ short trades == the open-fill recomputation to 0.0; +50 bp on DLR 2014-02-07 moves one short by −50.000 and no other |
| **[HX]** | hedged deployed series == the ledger per bar to 4e-15 on every arm × exit |
| **[6]** | [GT] raises on a flipped bar; [ROT] on a changed on-share; [ID] on +1 bp on one trade; [S] on a sign-flipped ledger; [D] on a perturbed table |

**Speed:** self-test 12 s; rotation 0.08 s a draw, A′ 0.2, B 0.2; four cells under a minute
each; report 18 s; peak working set 1.15 GB.

## 9. What this establishes

1. **A negative trailing market return is a rebound forecast on this universe**, for the
   market (+188 against +80 bp per 20 bars) and for the loser cohort (+96 against −16), with
   a block correlation of −0.23 that a shuffle does not reproduce. As a gate for a short it
   selects the half of a drawdown that pays the short and the half that takes it back.
2. **The era splits that motivated the gate were not states.** A stretch's average is not
   a condition one can be in at the time; STACK §7 item 31.
3. **The gap-up fade with the market below its 200-day mean is above every control on one
   cell of four**, +42 gross a trade on 3,977, +3.3 net under PB. It is the first short in
   the record to clear all its nulls, it is not the primary, and it is not yet its own
   record.
4. **The gated arms are flat by default** (28 to 42% exposure), which the ungated event
   books never were (D358).

## 10. Files

`data/d361_stage0.json` · `data/d361_ctrl_{G1,G2}_{T1,T2}_p0.json` · `data/d361_regime_gated_short.json`
· `scripts/run_d361_regime_gated_short.py` · reuses `scripts/run_d359_loser_rally_short.py`,
`scripts/run_d360_news_gap_short.py`, `scripts/run_d358_flat_sleeve.py`,
`scripts/run_d349_short_signal_controls.py`, `scripts/d345_event_book.py`, `scripts/d337_borrow.py`,
`scripts/d348_prep.py`, `scripts/d322_four_group_report.py`.
