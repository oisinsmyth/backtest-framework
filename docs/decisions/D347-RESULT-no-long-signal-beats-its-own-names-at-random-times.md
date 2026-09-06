# D347 RESULT — no long signal beats its own names at random times: the excess is which names, not when, and the extreme `rsi` rank makes it worse

**Status:** RESULT. Pre-registered at `1536eed`, runner at `90c3b2c` with a fix at `fade96e`
(the hedge-defined confinement; §8) — all before this file existed (R8). `keep_v2`, F0,
next-open fill, hedged against the floored universe's own market, PUB primary.
**Date:** 2026-09-06
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is a book. Nothing is promoted. The pair book waits for a signal that earns it.**

---

## 1. The verdict

**Zero of eight predictions held, and the load-bearing one failed in the most informative
way possible.** Every one of the four long signals earns a positive hedged excess per
trade — `hist_L` +60 bp over forty bars, t = 4.8 on 15,889 trades — and **every one of
them earns less than the same names held at random times.** Control A, the per-name time
rotation, has a median of +71 for `hist_L`'s names, +60 for `rev_21`'s, +45 and +48 for
the two `rsi` references; the observed statistics sit *below* those medians. Whatever the
long signals are measuring, it is not *when* to buy. It is *which names* they touch, and
those names earn their excess whenever they are held.

| long, cap exit, bp per trade | observed | **control A** p50 / p95 | control B p50 / p95 | control C p95 | above A / B / C |
|---|--:|--:|--:|--:|---|
| `hist_L` | +60.4 | **+70.8** / +90.8 | +24.0 / +39.7 | +21.7 | **no** / yes / yes |
| `rev_21` | +46.5 | **+59.6** / +80.1 | +29.0 / +42.0 | +21.5 | **no** / yes / yes |
| `rsi` turn | +16.0 | +45.2 / +60.3 | +26.3 / +36.7 | +20.5 | no / no / no |
| `rsi` decile | +30.4 | +48.0 / +65.9 | +20.2 / +26.4 | +18.1 | no / yes / yes |

100 distinct draws for A and B, 1,000 for C. **Q1 falsified: no survivors.**

## 2. What the three controls say together

- **Control B** (same day, same `rsi` bucket, a random other name) is beaten by three of
  the four: the signal's name earns more than a random name in its cohort that day. Read
  alone, that is name selection with edge.
- **Control A** (the same names, random dates) beats all four: the signal's names earn
  *more* at random times than at the signal's times. Read with B, the name selection is
  real and it is **static** — a property of the names, not of the moment. The signals
  select a cohort of names that carries positive hedged returns across the whole sample,
  and their timing then costs 10 to 30 bp of it.
- **Control C** (random direction) is beaten by three of four, which only says the long
  side of these cohorts is the right side. It was never in doubt for a rising market.

**The base rates say the same thing about `rsi` itself.** Forward-40 hedged excess of
every floored name-bar, by `rsi` percentile bucket: +23, +10, +21, +32, +27, +22 for the
six buckets below the 75th percentile and +6, −8, −12, −31 above it. The `rsi` ranking's
long-side profile *is* a base rate: low-`rsi` names earn +20 to +30 bp over forty bars
without any signal firing, and high-`rsi` names lose it. That is the spread ranking's
edge as the slot book sees it, and it is a cohort property too.

## 3. The two hedges, and why neither removed it

**Q3 falsified** — the control-A distributions are centred at +45 to +71, not at zero. The
equal-weight hedge against the floored market removes the level of drift and leaves
whatever these cohorts earn over it. **Q4 falsified**: beta adjustment (trailing 63-bar
OLS, lagged, fixed at entry) takes `hist_L` from +60 to +52 and `rev_21` from +47 to +37,
under 30% as predicted, but lifts both `rsi` references — +16 to +37, +30 to +49 — so the
prediction's direction was wrong for half the signals. Contemporaneous beta explains a
fraction of the cohort's excess; the rest is idiosyncratic to the names. A market hedge,
by any beta, cannot remove a per-name mean. **The hedge for cohort drift is control A
itself**: the name's own unconditional excess. Measured that way, every long signal's
timing value is negative — `hist_L` −10, `rev_21` −13, `rsi` turn −29, `rsi` decile −18 bp
a trade.

## 4. The splits

| | down-years mean (n) | era 1 / era 2 | mirror (short) cap | mirror beta-adj |
|---|--:|--:|--:|--:|
| `hist_L` | +67 (3,793) | −13 / +96 | −15.4 | +14.3 |
| `rev_21` | +33 (3,544) | −12 / +74 | −17.4 | +7.5 |
| `rsi` turn | +43 (3,577) | −6 / +27 | −18.6 | −9.8 |
| `rsi` decile | +57 (4,366) | −8 / +49 | −1.8 | +1.6 |

Down-years (floored market negative): 2015, 2018, 2022. **Q6's clause on down-years
held for every signal** — the hedged excess is positive when the market falls — but Q6
was conditioned on a survivor and there is none. **Q7 falsified**: every mirror loses;
shorting the same cohorts costs the cohort premium. The era halves show the same thing
the slot books showed: the first half is at or below zero, the second half carries it.

## 5. The interaction with the `rsi` ranking — the pairing idea, tested

`E[signal, bucket] − E[bucket] − E[signal] + E[all]`, long, cap exit:

| `rsi` bucket at t−1 | `hist_L` n / E_sb / E_b / **I** | `rev_21` n / E_sb / E_b / **I** |
|---|---|---|
| [0, 2] | 1,896 / +1 / +23 / **−81** | 1,947 / −32 / +23 / **−99** |
| (2, 5] | 2,264 / +64 / +10 / −5 | 2,954 / +20 / +10 / −35 |
| (5, 10] | 2,824 / +44 / +21 / −36 | 3,671 / +34 / +21 / −32 |
| (10, 25] | 4,736 / +62 / +32 / −28 | 5,029 / +90 / +32 / +13 |
| (25, 50] | 3,086 / +103 / +27 / **+17** | 1,793 / +49 / +27 / −23 |
| (50, 75] | 892 / +95 / +22 / **+14** | 232 / +318 / +22 / +251 |

**Q5 falsified, and reversed.** For every signal the interaction is most negative in the
most oversold `rsi` bucket and turns positive in the middle. `hist_L`'s events on names
in the bottom 2% by `rsi` earn **+1 bp**; on names in the middle half they earn **+103**.
The principal's design — run the long signal on the top of the `rsi` ranking — selects
exactly the bucket where the long signals do worst. A `hist_L` extreme on a name that is
*also* deeply oversold is a name in free fall, and forty bars later it has not recovered;
a `hist_L` extreme on a name whose `rsi` is neutral is a pullback, and it has.

## 6. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* `hist_L` or `rev_21` above all three controls | **FALSIFIED** — none above A; all four below A's median |
| **Q2** | `rsi` turn beats A, fails B | **FALSIFIED** — fails all three |
| **Q3** | control A centred within ±10 bp of zero | **FALSIFIED** — +45 to +71 |
| **Q4** | beta-adjusted below equal-weight, by < 30% | **FALSIFIED** — true for `hist_L`, `rev_21`; the `rsi` references rise |
| **Q5** | *(against)* survivors' bottom decile beats the middle by > 20 | **FALSIFIED** — no survivor; the bottom decile is the *worst* bucket for every signal, by 62 to 74 bp |
| **Q6** | survivors positive in down-years | **FALSIFIED** as conditioned; every signal is positive in down-years |
| **Q7** | *(against)* survivors' mirror > 0 | **FALSIFIED** — every mirror loses |
| **Q8** | *(against)* some signal nets > 0 after PUB under invalidation | **FALSIFIED** — −12 to −34 |
| *check* | kernel identity; event counts | held; 23,491 `hist_L` events → 15,889 trades (a third fire while the name is already held) |

Zero of eight.

## 7. Stop conditions, executed

- **Q1 fails → no long signal among the three is real against drift-matched controls
  under the current conventions.** D290's verdict for long books stands for long signals,
  in a sharper form: it is not market drift, the ledger is hedged; it is **cohort drift**,
  the names these signals touch earn their excess whenever they are held. **The pair book
  waits for a signal that earns it.**
- **Q3 fails → the beta-adjusted excess becomes primary** for these signals, and this
  record says it does not help: the cohort's excess is not contemporaneous beta.
- **Q5 reversed → the pairing design is contradicted on its own terms**: a long signal
  conditioned on the extreme `rsi` rank is worse than the same signal unconditioned.

## 8. Deviations and what the run found in the runner

- **Control A first produced NaN medians.** The floored market is undefined in the panel's
  first weeks (fewer than 20 names pass `keep_v2` before any dollar-volume estimate
  exists); observed events never fall there, rotated events did, and a trade there has
  no hedge. Every signal — observed and rotated — is now confined to bars from the first
  bar after which the hedge is defined everywhere, and [A] asserts no rotated trade
  carries a NaN. Fixed at `fade96e` before any control was read; the stale files were
  deleted.
- Two self-test catches, recorded: the percentile grid ranked tied scores by argsort
  position and the direct check by lowest rank, so a tie at the decile boundary landed on
  different sides — both now use the average rank; and control B assigned two same-day
  events the same replacement name — it now draws distinct names per day and bucket.
- **Process parallelism hurt here.** Six concurrent control processes made the panel load
  sixty times slower (about 50 minutes each against 45 seconds alone); two at a time was
  fine. The parallelism rule in CLAUDE.md is about the GIL; this was memory.
- The pre-registration's [X] said the interaction summed with event weights is zero; the
  correct identity is `Σ_b n_b (E_sb − E_s) = 0`, which is what the runner asserts.

## 9. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor == census; `keep_v2` share == D343 |
| **[ID]** | D345's kernel identity re-asserted: 4,021 trades bit-identical to the slot book's invariant ledger |
| **[E]** | 300 sampled events per signal satisfy the entry condition on the raw lagged score at t−1 by direct count and are fresh; the unlagged condition differs on 300 of 300 |
| **[H]** | the floored market equals a direct mean over 200 sampled bars to 1e-12; a synthetic name with returns 2m + noise recovers β = 2.000 |
| **[S]** | every `hist_L` cap-exit trade equals the open-fill recomputation against the floored market to 1.8e-15; favourable paths pay positively |
| **[A]** | control A keeps every name's event count except the < 2% rotated onto bars before the hedge is defined; no rotated trade carries a NaN |
| **[B]** | control B keeps every event's date and `rsi` bucket; 0 of 23,491 kept their name by chance |
| **[C]** | control C's mean −0.03 bp, within 2 standard errors of zero |
| **[F]** | the forward-40 base-rate grid equals a direct per-cell recomputation on 3,000 sampled cells to 3.4e-15 |
| **[X]** | `Σ_b n_b (E_sb − E_s) = 0`; the buckets partition the events |
| **[6]** | [S] raises on events handed +50 bp |

**Speed:** self-test 59 s; each control process 3.5 to 4 minutes alone; report 65 s.

## 10. What this establishes

1. **The long excess in this programme is cohort membership, not timing.** Four long
   signals, every one below its own names' random-time excess. A per-name time rotation
   is the control that shows it, and it has never been applied to the slot books' cells,
   whose nulls rotate names within the gate on the same day — control B, which these
   signals beat. **Every per-trade positive in D335, D346 and D344's long legs was
   measured without control A.** It goes on the candidate cells next, and it may take
   them.
2. **A market hedge cannot remove a per-name mean.** Neither the floored equal-weight
   hedge nor a rolling beta removed the cohort's excess. The hedge for cohort drift is the
   name's own unconditional excess.
3. **Conditioning a long signal on the extreme of the `rsi` ranking makes it worse**, for
   every signal, by 62 to 74 bp a trade against the middle buckets. The pair book as
   designed would run the long signal where it does worst.
4. **The `rsi` ranking's own long-side profile is a base rate.** Low-`rsi` names earn +20
   to +30 bp over forty bars with no signal at all. Whether that base rate survives its
   own control A is the question for the slot book, not for these signals.
5. **D290's long-only verdict stands, sharpened.** "Market drift" was the right verdict
   for the wrong reason; the ledger is hedged and the excess is still not the signal's.

## 11. Files

`data/d347_long_signal_controls.json` · `data/d347_ctrl_*.json` (five control files) ·
`scripts/run_d347_long_signal_controls.py` · reuses `scripts/d345_event_book.py`
