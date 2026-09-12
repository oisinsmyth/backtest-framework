# D489 — stage 0: is ZB actually a LARGE-TICK instrument? The premise `C6` has never had checked

**Pre-registration. Committed before the runner exists ([R8](../RULES.md#r8)).** Result in a
separate file. **STAGE 0: NO RETURN IS READ.** Tick sizes, realised volatility and trade counts
only. Abandon conditions declared below before any number is looked at.

**Occasioned by:** the principal's *"investigate ZB that failed at σ $682–939"*
([D468](D468-RESULT-none-of-24-session-windows-on-eight-roots-clears-the-component-standard-the-best-sits-at-the-78th-percentile-of-its-family-null.md)).

## 1. What D468 actually found about ZB, and why that is not the end of it

D468 scored ZB on three session windows and rejected all three. The row, from the ledger:

| | net Sharpe | gross | σ $/day | worst $ |
|---|---|---|---|---|
| ZB-W1 / W2 / W3, 1 ZB, $6 | +0.01 / −0.08 / −0.08 | **+0.10 / +0.05 / +0.05** | **939 / 686 / 682** | −8,350 |

**Two distinct failures, and they are not equally interesting.**

- **`C-d` (σ $682–939 against a $500 bar) is a SCALE failure.** It is a property of the contract —
  $100,000 face, $1,000 a point, no micro — divided by an account size we chose. It moves if the
  account moves (150K) or if the window shortens. **It says nothing about whether there is an
  edge.**
- **`C-a` (gross Sharpe +0.05 to +0.10) is the BINDING failure, and it is scale-free.** At those
  numbers ZB has no session-window drift even at zero cost. Shrinking σ cannot fix a Sharpe,
  because Sharpe is a ratio: a shorter window divides the mean by the same factor.

> **So the σ headline is the visible failure and `C-a` is the real one.** D468's own framing agrees:
> *"the treasuries, gold, crude and the euro hold no session-window drift at this resolution in
> 2016–2023."* This pre-registration does **not** dispute that and does **not** re-test a session
> window on ZB.

## 2. The thing that IS open, and it is a premise, not a result

The candidate ledger's **`C6`** — *"short-horizon direction on **large-tick** CME outrights (ZN,
ZB)"*, marked **the strongest `[PERSONAL]` lead** — names ZB for a reason **D468 never tested**.
Its declared decider is:

> `τ = tick/σ`, ranked monthly, split at median: survives iff **large-tick beats small-tick** by
> more than the bootstrap SE, post-2009.

**`C6` has never been run.** A grep for `tick/σ`, `large-tick` and `τ` across `docs/decisions/`
returns nothing: **no decision record in this repo has ever computed τ.** D468 tested a
*directional hold across a session window*. `C6` is a *short-horizon rule conditioned on a
tick-to-volatility ratio*. Different object, different horizon, different conditioner.

**And the corpus contradicts itself on which instrument is large-tick.** Lane 21 states *"**ES** is
the canonical large-tick book: the spread is one tick essentially always"*, while the ledger's `C6`
names **ZN and ZB**. Both cannot be the identifying tier. **τ decides it, and τ is computable from
data already committed.**

## 3. Stage 0: measure the conditioner before designing anything that conditions on it

This is the standing rule — *measure the conditioner's own persistence before designing a study
that conditions on it* — applied to `C6`'s τ. **`C6`'s decider ranks τ monthly and splits at the
median. That classification step is only meaningful if τ (a) separates the roots and (b) is stable
month to month.** Neither has been checked. Checking them reads no return.

## 4. The statistic

**Fixture:** `data/fixtures/fut_sessions_hourly.csv.gz` (D467; eight roots, hourly OHLCV **and
trade counts** `_n`, the 18:00→16:00 ET Globex session, gates passed from 2016-01-04). **Window:
2016-01-04 → 2023-12-29, the same in-sample slice D468 used. 2024+ stays unread.**

**Tick sizes** come from `data/futures_contract_specs.json`, each verified against CME's own
contract-specification service (see its `_provenance` block). Nothing is hardcoded here.

Two ratios, because the literature's τ is a *per-trade* quantity and the ledger's row does not say
which horizon it meant:

| | definition | what it means |
|---|---|---|
| **τ_h** | `tick_usd / σ_h`, with σ_h the dollar σ of the h-hour price change on the front contract | how many ticks a horizon-`h` move spans |
| **τ_trade** | `tick_usd × √n̄ / σ_session`, with n̄ the session's trade count | **the literature's ratio**: tick against the volatility **per trade**. Large-tick ⇔ τ_trade large ⇔ the price needs many trades to move one tick |

τ_h is reported at **h = 1 hour** and **h = 1 session**. All eight roots, in **contract dollars at
one full contract** — the ratio is scale-free in the multiplier, so the micro/mini distinction
cannot enter it.

**σ is measured on the front contract only** (`same_front == True` rows), so a roll cannot enter a
price change. **Trade counts `_n` are summed over the session's hours**, and a session is dropped
if any of its hours is missing rather than imputed.

## 5. Abandon conditions — declared before any number is read

- **`T1` — if ZB does not rank in the TOP 3 of the 8 roots on τ_trade, `C6`'s instrument choice is
  wrong and ZB is ABANDONED as a large-tick candidate.** The premise is that ZB *is* the large-tick
  tier. Eight roots is the reference distribution; a rank outside the top 3 means the ledger named
  the wrong contract and any downstream τ split would be classifying on something else.
- **`T2` — if the month-to-month Spearman rank autocorrelation of τ_trade across the eight roots
  (lag 1, pooled over months) is below 0.5, `C6`'s DECIDER is ABANDONED.** *"Ranked monthly, split
  at median"* requires the monthly ranking to be a stable property of the instrument. If the
  ordering reshuffles every month, the split is labelling noise and no return test built on it can
  identify.
- **`T3` — if ZB and ZN do not separate from the index roots by more than the index roots separate
  among themselves** — i.e. if `min(τ_trade of ZB, ZN) ≤ max(τ_trade of ES, NQ, YM)` — **the
  two-tier split `C6` rests on does not exist in this data and `C6` is ABANDONED.** A median split
  on a continuum with no gap is an arbitrary cut.

**`T1 ∧ T2 ∧ T3` must all survive for `C6` to earn a stage 1.** Any one failing ends it, and under
[R15](../RULES.md#r15) that is a measurement reported to the principal, not an avenue closed by me.

## 6. A descriptive rider, with NO bar attached

**`R1` — ZB's dollar σ at horizons from 1 hour to a full session**, so the `C-d` question has a
number instead of an inference. D468 reports σ at three windows; this reports the curve. It is
**descriptive and decides nothing** — the `C-d` bar is a scale constraint and `C-a` is what
rejected ZB. It is recorded so that *"would a shorter ZB window be expressible?"* never has to be
guessed at again.

## 7. Predictions

- **`Q1` — `T1` SURVIVES: ZB ranks top 3 on τ_trade.** From D468's own published σ and the verified
  ticks: τ_session(ZB) = 31.25/939 = **0.033**; τ_session(ES at one full ES) = 12.50/1,830 =
  **0.0068** (D463/D464's ES night σ). A factor of ~5 before any trade count enters.
- **`Q2` — ZN ranks ABOVE ZB, not below.** ZN's tick is half ZB's ($15.625), but D468 puts its σ at
  $290–400 against ZB's $682–939 — a bigger divisor cut than the tick cut. τ_session(ZN) ≈
  15.625/345 = **0.045**. **If so, the ledger's "(ZN, ZB)" has them in the right order, and ZB is
  the weaker of the pair it names.**
- **`Q3` — `T3` SURVIVES but not cleanly, and ES is the reason.** Lane 21's claim about ES is about
  *the spread being pinned at one tick*, which is a consequence of a high τ. **I expect ES to sit
  far closer to the treasuries than NQ or YM do**, making the "gap" a three-way split rather than a
  two-tier one. **If ES lands above ZB on τ_trade, the corpus's conflict resolves AGAINST the
  ledger, and `C6` is naming the wrong instruments while sitting next to the right one.**
- **`Q4` — `T2` SURVIVES comfortably, ≥ 0.8.** τ is a ratio of a fixed exchange constant to a
  volatility, and volatility ranks *across* instruments are among the most persistent quantities in
  finance. **If `T2` fails, the likeliest cause is a bug in my monthly grouping, not a fact about
  markets** — so a `T2` failure is a reason to audit the runner before believing it.
- **`Q5` — `R1`: ZB's σ will NOT reach $500 at any window longer than about two hours**, so no
  session-scale ZB construction is `C-d`-expressible on a $50k account. Reported; decides nothing.
- **`Q6` — runtime under 2 minutes**, one file, 33,387 rows.

## 8. Not in scope

**No return, no signal, no strategy, no cost model, no session-window re-test.** Ratios and ranks
only. **Nothing here opens or admits anything**; a stage 0 that clears its abandon conditions earns
a stage 1, not a candidate. **2024+ is not read.**

---

## AMENDMENT, 2026-09-12 — §4's `τ_trade` NAMED A COLUMN THAT DOES NOT HOLD WHAT I SAID IT HOLDS

**Made before the runner existed and before any number was read. §4 above stands as written; this
block replaces its `τ_trade` row and nothing else. The abandon conditions `T1`–`T3` and the
predictions `Q1`–`Q6` are unchanged in substance.**

### The error

§4 defined `τ_trade = tick_usd × √n̄ / σ_session` with *"n̄ the session's trade count"* and said
*"trade counts `_n` are summed over the session's hours"*. **`_n` is not a trade count.**
`scripts/build_fut_sessions_hourly.py:60–64` documents the hourly aggregation as *"open at the
earliest minute, close at the latest, max high, min low, sum volume, **count bars**"*, assigning
`n=1` per minute row; its own self-test asserts `h09_n == 30` for a half-populated hour.
**`_n` is a count of populated one-minute bars, capped at 60 an hour.** Using it as `n̄` would have
computed `tick × √(minutes) / σ`, which is a *horizon* ratio wearing a per-trade label — and it
would have been almost constant across roots, because every root has ~60 bars an hour.

**Databento's `ohlcv-1m` schema carries no trade count at all**, so no column of this fixture could
have supplied one. The quantity was not available and I wrote it into the statistic anyway.

### What replaces it

| | definition | status |
|---|---|---|
| **`τ_1h`** | `tick_usd / σ_1h`, σ_1h the dollar σ of the hour-to-hour close change | **PRIMARY. `T1`, `T2` and `T3` are decided on this.** Exact and assumption-free: every quantity is read, none is scaled |
| **`τ_sess`** | `tick_usd / σ_session` | reported; the horizon D468 scored at, so the two records are comparable |
| **`τ_vol`** | `tick_usd × √v̄ / σ_session`, v̄ the session's **contract volume** | **SECONDARY and FLAGGED.** Volume is not a trade count: it is trades × average trade size, and average trade size differs across roots. It is the nearest available event count and it is reported as a robustness check, not as the literature's ratio |

**`T1`/`T2`/`T3` are evaluated on `τ_1h`.** If `τ_vol` puts ZB on the other side of any of the three
bars, **that condition is reported UNRESOLVED rather than passed** — the two denominators disagreeing
is exactly the situation where a rank is an artefact of the event count.

### What this record therefore cannot settle, stated plainly

**The literature's per-trade τ is not computed here.** The proper denominator is the volatility per
*trade*, and reaching it needs one of two things this record does not spend:

1. **a `trades` or `tbbo` extraction over 2016–2023** — not held; the raw archive has `ohlcv-1m`
   and `mbo` for that span, and `mbo` is the full order book, which is a large extraction for a
   stage-0 premise check; or
2. **the `tbbo` / `bbo-1m` files already on disk** — but those cover **2025-09-11 → 2026-09-10**,
   inside the slice §8 declares unread. **Those files would answer the question better than any
   ratio here** (large-tick is *defined* by the quoted spread sitting at one tick, which `bbo-1m`
   censuses directly rather than estimates). **Reading them is the principal's call under
   [R15](../RULES.md#r15), not mine, and this record does not touch them.**

**So `Q1`–`Q3` are now predictions about the HOURLY ratio.** Their numbers were computed from
D468's published session σ and are unchanged; the ordering they predict is the same ordering
`τ_1h` ranks.
