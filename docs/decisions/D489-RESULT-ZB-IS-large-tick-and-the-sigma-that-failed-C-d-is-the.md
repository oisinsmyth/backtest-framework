# D489 RESULT — ZB **is** large-tick, and the σ that failed `C-d` is the WINDOW, not the contract; but `C6`'s own median split cuts exactly where the data is densest

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D489-RESULT-ZB-IS-large-tick-and-the-sigma-that-failed-C-d-is-the-window-not-the-contract-but-C6s-median-split-cuts-where-the-data-is-densest.md`. The H1 above is the full title.*

**Pre-registration:** [`D489`](D489-PRE-REG-stage-0-is-ZB-actually-a-large-tick-instrument-the.md),
committed before the runner existed, with a 2026-09-12 amendment (below, §5) also made before the
runner existed. **Runner:** `scripts/d489_large_tick_premise.py` (`--selftest` passes, five checks
each shown to fire on a broken input; `--run` in **4 seconds**). **Fixture:**
`data/fixtures/fut_sessions_hourly.csv.gz` (D467). **Evidence:** `data/d489_large_tick_premise.json`.
**Slice 2016-01-04 → 2023-12-29, D468's own. 2024+ NOT READ. NO RETURN WAS READ.**

**Under [R15](../RULES.md#r15) this record closes nothing and opens nothing.** It reports a premise.

---

## 0. THE ANSWER

> **`T1`, `T2` and `T3` all SURVIVE. `C6`'s premise is TRUE and it is not close: ZN and ZB are the
> large-tick tier by a factor of 3.3 over the third root, and the ordering is stable at
> ρ = +0.944 across 95 consecutive month pairs.**
>
> **And the thing the principal actually asked about: ZB's σ $682–939 is a property of the WINDOW
> D468 chose, not of the contract. A ZB hold started at 18:00 ET stays under the $500 `C-d` bar for
> NINE HOURS. ZN stays under it for the ENTIRE 23-hour session ($418).**

**But `C6`'s declared decider is defective in the same way two of D461's abandon conditions were.**
It says *"ranked monthly, **split at median**"*. The median cut falls between **GC (0.0322) and ES
(0.0317) — a 1.5% difference.** The real gap is between **ZB (0.1459) and 6E (0.0440) — 3.3×.**
**A median split would put 6E and GC in the "large-tick" tier and ES and CL in the "small-tick"
tier on a rounding error**, and the tier contrast `C6` proposes to measure would be mostly noise.

## 1. The table

`τ_1h = tick_usd / σ(hour-to-hour close change, in dollars)`. **`ticks/h` is `1/τ_1h`** — how many
ticks an hour's move spans, which is the same number said the legible way.

| root | sessions | tick $ | σ_1h $ | σ_sess $ | **τ_1h** | rk | **ticks/h** | τ_vol | rk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ZN** | 1,974 | 15.625 | 90.4 | 417.9 | **0.1729** | **1** | **5.8** | 43.83 | 1 |
| **ZB** | 1,973 | 31.250 | 214.2 | 981.0 | **0.1459** | **2** | **6.9** | 17.31 | 2 |
| 6E | 1,982 | 6.250 | 142.0 | 649.9 | 0.0440 | 3 | 22.7 | 4.14 | 4 |
| GC | 1,965 | 10.000 | 310.4 | 1,488.9 | 0.0322 | 4 | 31.0 | 3.08 | 6 |
| **ES** | 1,973 | 12.500 | 393.9 | 1,883.4 | **0.0317** | **5** | **31.5** | 8.30 | **3** |
| CL | 1,915 | 10.000 | 332.6 | 1,573.1 | 0.0301 | 6 | 33.3 | 4.05 | 5 |
| YM | 1,967 | 5.000 | 306.2 | 1,443.3 | 0.0163 | 7 | 61.2 | 1.47 | 7 |
| NQ | 1,970 | 5.000 | 613.4 | 2,984.0 | 0.0082 | 8 | 122.7 | 1.15 | 8 |
| *RTY* | *1,581* | *5.000* | *276.3* | *1,279.2* | *0.0181* | *—* | *55.3* | *1.57* | *—* |

*RTY is D472's ninth root; it is reported and held outside every bar, because D468's family was
eight and the pre-registration named eight.*

**Read the `ticks/h` column and the premise is obvious: ZN moves 5.8 ticks an hour and NQ moves
123.** That is a factor of **21**, and it is what "large-tick" means.

## 2. The three conditions, as declared

| | condition | observed | |
|---|---|---|---|
| **`T1`** | ZB in the TOP 3 of 8 on τ | **rank 2** on τ_1h, **rank 2** on τ_vol | **SURVIVES** — both denominators agree, so the amendment's UNRESOLVED clause does not fire |
| **`T2`** | monthly rank ordering persists, ρ ≥ 0.50 | **ρ = +0.944** over **95** consecutive month pairs (96 complete months); median +0.976, p10 +0.867, **min +0.690** | **SURVIVES** |
| **`T3`** | `min(τ ZB, ZN) > max(τ ES, NQ, YM)` | gap **+0.1142** on τ_1h (0.1459 vs 0.0317), **+9.01** on τ_vol | **SURVIVES** |

`T2`'s minimum of +0.690 matters as much as its mean: **no single month's ordering collapses**, so
the persistence is not an average over a stable majority and a few scrambles.

## 3. Predictions — two wrong, and BOTH in the optimistic direction

| | predicted | observed | |
|---|---|---|---|
| **`Q1`** | `T1` survives; τ_sess(ZB) ≈ 0.033 | **rank 2**; τ_sess(ZB) = **0.0319** | **RIGHT**, and the arithmetic from D468's published σ held to 3% |
| **`Q2`** | **ZN ranks ABOVE ZB** | **ZN 0.1729, ZB 0.1459** | **RIGHT.** The ledger's *"(ZN, ZB)"* has them in the right order, and **ZB is the weaker of the pair it names** |
| **`Q3`** | `T3` survives *but not cleanly*; **ES sits far closer to the treasuries than NQ or YM do**, making it a three-way split | **WRONG on the shape.** `T3` survives **very** cleanly — 3.3× — and **ES is 5th of 8**, statistically tied with GC and CL (0.0322 / 0.0317 / 0.0301). It is nowhere near the treasuries | see §4 |
| **`Q4`** | `T2` ≥ 0.8 | **+0.944** | **RIGHT** |
| **`Q5`** | **ZB's σ will not reach $500 at any window longer than about two hours** | **WRONG, by 4.5×.** ZB from 18:00 is under $500 out to **9 hours**; **ZN is under it for the whole session** | see §6 — this is the answer to the question that was asked |
| **`Q6`** | under 2 minutes | **4 seconds** | **RIGHT** |

> **Both misses make ZB/ZN look BETTER than I expected.** That is the second time in two sessions
> (D460's `E2` was the first); every earlier miss in the prop chain ran pessimistic. **A run of
> optimistic misses is the pattern that precedes believing something, so both are stated as misses
> here rather than as findings.**

## 4. The corpus contradicted itself about ES, and τ resolves it — against BOTH readings

Lane 21 says *"**ES** is the canonical large-tick book: the spread is one tick essentially always."*
The ledger's `C6` says the large-tick outrights are **ZN and ZB**. §1 says **neither reading is
quite right, and they are not even about the same quantity**:

- **At the HOUR horizon ES is mid-pack** — 31.5 ticks an hour, indistinguishable from GC and CL.
  **On τ_1h, lane 21's claim is false.**
- **On τ_vol — tick against volatility per unit of VOLUME — ES jumps to rank 3**, past 6E, CL and
  GC, because ES's volume is an order of magnitude larger than theirs. **That is where lane 21's
  claim lives: the spread is pinned at one tick because the queue is enormous, which is a
  per-event property, not a per-hour one.**
- **On neither measure does ES reach ZN or ZB.** τ_vol: ZN 43.8, ZB 17.3, ES 8.3.

> **Both statements are true of different horizons, and the corpus never said which.** `C6` is a
> *short-horizon direction* rule, so **which τ it means decides which instruments it is about** —
> and the ledger row does not say. **That ambiguity is now named, and it is a defect in the
> candidate's specification, not in either source.**

## 5. The amendment, and what it costs — restated because it bounds this record

The pre-registration's `τ_trade` named `_n` as *"the session's trade count."* **It is a count of
populated one-minute bars**, capped at 60 an hour (`build_fut_sessions_hourly.py:60–64`: *"sum
volume, **count bars**"*; its self-test asserts `h09_n == 30`). **Databento's `ohlcv-1m` schema
carries no trade count at all**, so no column could have supplied one. Amended before the runner
existed: **τ_1h is primary, τ_vol is a flagged secondary, and the two agree on every bar here.**

**What this record therefore does NOT settle:** the literature's per-trade τ. Reaching it needs a
`trades`/`tbbo` extraction over 2016–2023 (not held; the archive has `ohlcv-1m` and `mbo` for that
span), **or** the `tbbo` and `bbo-1m` files already on disk — **which cover 2025-09-11 → 2026-09-10,
inside the slice this pre-registration declared unread.** Those files would answer it *better* than
any ratio here, because large-tick is *defined* by the quoted spread sitting at its minimum and
`bbo-1m` censuses that directly. **Reading them is the principal's call, and this record does not
touch them.**

## 6. `R1`/`R1b` — descriptive, NO BAR ATTACHED: the σ that failed `C-d` is the window

**`C-d` is "daily σ at minimum size ≤ 1% of a $50k account" = $500.** D468 scored ZB at $682–939 and
recorded `C-d` against it. **That is true of the three windows D468 chose and false of ZB generally.**

σ in dollars, one contract, hold from 18:00 ET:

| h | end | ZB | ZN | ES | NQ |
|---:|---|---:|---:|---:|---:|
| 1 | 19:00 | **167** | **65** | 314 | 472 |
| 4 | 22:00 | **311** | **130** | 549 | 813 |
| 8 | 02:00 | **400** | **169** | 691 | 983 |
| 12 | 06:00 | 559 | **227** | 907 | 1,353 |
| 16 | 10:00 | 767 | **322** | 1,211 | 1,868 |
| 23 | 16:00 | 981 | **418** | 1,883 | 2,984 |

**ZN never crosses $500 at all.** `C-d` is not a barrier for ZN on any window — **the ledger's
*"ZN's whole daily range is $310–390, so $150/day needs size the floor forbids"* is the same fact
read as a disqualification, and it is exactly what makes ZN expressible.**

**And placement on the clock matters as much as length** (`R1b`, the longest ZB hold with σ ≤ $500,
by start hour):

```
18:00  9h     22:00  9h     02:00  6h     06:00  3h     10:00  3h     14:00  3h
19:00  9h     23:00  9h     03:00  5h     07:00  2h     11:00  4h     15:00  2h
20:00  9h     00:00  8h     04:00  5h     08:00  2h     12:00  5h     16:00  1h
21:00  9h     01:00  7h     05:00  4h     09:00  2h     13:00  4h
```

> **ZB's variance is concentrated in the 07:00–10:00 ET window** — the European close and the US
> data/open — where a **two-hour** hold already spends the budget. **The evening is quiet enough for
> nine.** D468's W3 (09:00→16:00) landed at $682 for seven hours; a seven-hour *evening* hold is
> **$379**. **Same length, 1.8× the σ, purely from where it sits on the clock.**

## 7. What this changes, and what it emphatically does not

**Does not change:** **ZB's `C-a` failure stands untouched and it is the binding one.** Gross Sharpe
+0.10 / +0.05 / +0.05 is no edge at zero cost, and nothing in this record reads a return or disputes
D468's *"the treasuries, gold, crude and the euro hold no session-window drift at this resolution in
2016–2023."* **A favourable σ is an expressibility fact, not an edge.**

**Does change, for whatever is designed next:**

1. **`C6`'s premise is confirmed and its instruments are the right ones** — the strongest
   `[PERSONAL]` lead now has its stage-0 behind it rather than an assertion.
2. **`C6`'s median split should be replaced by the gap split.** `{ZN, ZB}` against the other six,
   not the top four against the bottom four. **A cut between GC and ES on a 1.5% difference is the
   D461 defect again: a condition that cannot fail on a rounding error is not a condition.** This
   is a specification change to a candidate and therefore the principal's to make.
3. **`C-d` should be evaluated per WINDOW, not per root.** The ledger's ZB row reads
   *"σ $682–939 (> 1% of the account)"* as though it were a property of the contract. **It is a
   property of a 7–23 hour hold.** ZN's row (*"σ $290–400 a day"*) records `C-a` only and is
   correct as written.
4. **The per-trade τ, and lane 21's spread claim, are answerable from files already on disk** —
   `bbo-1m`, 2025-09-11 → 2026-09-10 — **at the cost of touching the unread slice for a
   NON-RETURN quantity.** Whether a spread census counts as spending the holdout is a judgement
   this record does not make.

## 8. Cost

**One pre-registration, one amendment, one runner, one 4-second run, no extraction, no new
fixture.** **The premise number was obtainable before any return was read, and no return was read.**
