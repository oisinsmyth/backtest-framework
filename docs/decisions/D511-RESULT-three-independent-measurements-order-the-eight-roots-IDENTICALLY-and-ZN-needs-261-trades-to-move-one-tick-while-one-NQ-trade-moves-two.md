# D511 RESULT — three independent measurements order the eight roots IDENTICALLY (ρ = +1.000); ZN needs 261 trades to move one tick while a single NQ trade moves two; and D489's `τ_vol` was better than its own caveat allowed

> **RENUMBERED D492 -> D511 on 2026-09-12.** This record was committed as **D492** in
> `dea4fbf / fd05be9`; a concurrent session had already taken D492 for an unrelated study, and under this
> repository's convention the later writer moves. **No stub is left at D492** — that number
> belongs to the other session's record. Numbers were taken from a reserved block well clear
> of the active frontier (D496) because three sessions are racing the same counter and the
> next-free approach is what produced the collision.

**Pre-registration:** [`D511`](D511-PRE-REG-the-trade-count-from-tbbo-the-per-trade-tau-D489-declared-it-could-not-compute.md),
committed before the runner existed. **Runner:** `scripts/d511_trade_count.py` (`--selftest` passes,
five checks each shown to fire on a broken input). **Build:** 13 `tbbo` files, 34.7 GB,
**1,439,501,590 records scanned → 365,052,858 front-contract trades, 10.6 min** (projected 10–15)
→ `data/fixtures/fut_trade_counts.csv.gz`. **Evidence:** `data/d511_trade_count.json`.
**Window 2025-09-11 → 2026-09-09. NO RETURN WAS READ; the `side` field was not read.**

**Under [R15](../RULES.md#r15) this record closes nothing and opens nothing.**

---

## 0. THE ANSWER

> **`U1` PASSES (ZB rank 2) and `U2` PASSES at ρ = +1.000 — a PERFECT rank agreement between the
> per-trade τ and D510's quoted-spread census across all eight roots.** Three independent
> measurements of one property — tick against hourly volatility, the quoted spread itself, and tick
> against per-trade volatility — now order the eight roots the same way.
>
> **And the per-trade τ is the BETTER proxy, which is exactly what the literature claims and had
> never been checked here: τ_1h agreed with the spread census at ρ +0.929 (three transpositions);
> τ_trade agrees at ρ +1.000 (none).** Moving the denominator from the hour to the trade removes
> every disagreement.
>
> **η is the number that makes it concrete. It takes 261 trades to move ZN one tick. It takes 0.20
> to move NQ one tick — a single NQ trade moves the price more than two ticks. That is a factor of
> 1,300 across the eight roots.**

## 1. The table

| root | sess | trades/sess | sizē | σ_sess $ | **$/trade** | **τ_trade** | rk | **η** | P1 | rk |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ZN** | 256 | 93,833 | **18.43** | 296 | **0.967** | **16.16** | 1 | **261** | 1.000 | 1 |
| **ZB** | 251 | 38,511 | 10.89 | 562 | 2.864 | **10.91** | 2 | **119** | 0.998 | 2 |
| **ES** | 257 | **477,776** | 2.91 | 2,934 | 4.245 | 2.94 | 3 | 9 | 0.882 | 3 |
| 6E | 257 | 36,221 | 4.08 | 512 | 2.690 | 2.32 | 4 | 5 | 0.733 | 4 |
| CL | 257 | 109,404 | 1.80 | 2,904 | 8.779 | 1.14 | 5 | 1 | 0.502 | 5 |
| YM | 257 | 68,147 | 1.40 | 2,053 | 7.865 | 0.64 | 6 | 0.41 | 0.046 | 6 |
| NQ | 257 | 376,635 | 1.44 | 6,890 | 11.226 | 0.45 | 7 | **0.20** | 0.013 | 7 |
| GC | 257 | 118,891 | 1.44 | 8,158 | 23.659 | 0.42 | 8 | **0.18** | 0.012 | 8 |
| *RTY* | *257* | *102,284* | *1.77* | *1,632* | *5.104* | *0.98* | *—* | *0.96* | *0.131* | *—* |

**The `rk` columns are identical. That is what ρ = +1.000 means on eight objects.**

**ES has by far the most trades — 477,776 a session, 5.1× ZN's — and is still only third.** Trade
count does not make a book large-tick; **tick size relative to the move does**, which is the whole
content of the ratio and is now shown rather than asserted.

## 2. The two declared conditions

| | condition | observed | |
|---|---|---|---|
| **`U1`** | ZB in the top 3 of 8 on `τ_trade` | **rank 2** (ZN 16.16, **ZB 10.91**, ES 2.94) | **PASSES.** D489's `T1` survives on the quantity D489 said it could not compute |
| **`U2`** | ρ(`τ_trade` order, D510 `P1` order) ≥ 0.7 | **ρ = +1.000**, zero transpositions | **PASSES** |

## 3. `U3` — I predicted D489's `τ_vol` would misrank, and it does not. Saying so, as declared.

The identity `τ_vol = τ_trade × √sizē` **holds to 1e-6 on every root** (asserted in the runner; if
it had failed, `n̄` and `v̄` would not have come from the same sessions and every ratio above would
compare different denominators).

| root | √sizē | τ_trade rk | τ_vol rk | moved |
|---|---:|---:|---:|---:|
| ZN | 4.29 | 1 | 1 | . |
| ZB | 3.30 | 2 | 2 | . |
| ES | 1.71 | 3 | 3 | . |
| 6E | 2.02 | 4 | 4 | . |
| CL | 1.34 | 5 | 5 | . |
| YM | 1.18 | 6 | 6 | . |
| NQ | 1.20 | 7 | 7 | . |
| GC | 1.20 | 8 | 8 | . |

**Total rank displacement: ZERO.**

> **`V-d` predicted at least two positions of movement, and the pre-registration said: *"If they
> turn out identical, D489's `τ_vol` was a better statistic than its own caveat allowed and I will
> say so."* Saying so.**
>
> **The contamination is real — `√sizē` runs 1.18 to 4.29, a 3.6× spread — and it reorders
> nothing, because it is MONOTONE-ALIGNED with the signal: the large-tick roots are also the ones
> with the biggest prints** (ZN averages 18.4 contracts a trade against NQ's 1.44). **The
> contaminant pushes in the same direction as the quantity it contaminates.** That is luck, not
> design, and a root with a large tick and small prints would have broken it — but on these eight
> the caveat cost nothing.

## 4. Predictions — 4 of 7, the best of this chain, and the misses are informative

| | predicted | observed | |
|---|---|---|---|
| **`V-a`** | `U1` passes, ZB top 3 | **rank 2** | **RIGHT** |
| **`V-b`** | `U2` passes with ρ ≥ 0.85 | **+1.000** | **RIGHT** |
| **`V-c`** | ES highest trade count; ZN highest `sizē` | **ES 477,776; ZN 18.43** | **RIGHT, both clauses** |
| **`V-d`** | `τ_vol` misranks by ≥ 2 positions | **0** | **WRONG** — §3 |
| **`V-e`** | η ≈ 100–1,500 on ZN; **1–30 on NQ and GC** | **ZN 261 ✓**; **NQ 0.20, GC 0.18 ✗** | **HALF RIGHT.** The ZN band held; NQ and GC are **below one**, which I did not allow for at all |
| **`V-f`** | ZB's `n̄` below ZN's by **3–10×** | **2.44×** | **WRONG**, just outside the band |
| **`V-g`** | 10–15 min | **10.6 min** | **RIGHT** |

**Four of seven, against 2-of-6, 1-of-7 and 5-of-6 wrong in the three preceding records.** `V-e`
was the one deliberately written as an order-of-magnitude band rather than a point because I did
not know the trade counts; **the half that failed failed because I did not consider that η could go
below one at all** — that a single trade routinely moves a price more than a full tick.

## 5. η below one is not a rounding artefact, it is the regime

**η < 1 on YM (0.41), NQ (0.20) and GC (0.18).** η is trades-per-one-tick-move, so η = 0.20 says
**one NQ trade moves the price about 2.2 ticks on average.**

> **That is the definition of a small-tick book: the tick is so fine relative to the move that it
> imposes no discretisation at all.** It is the mirror of ZN, where **261 trades are absorbed before
> the price moves one tick** — 4,863 lots sitting at the touch (D510) being worked through at 18.4
> contracts a print.
>
> **The two regimes are not points on a smooth continuum; they are 1,300× apart**, and every one of
> the three measurements puts the same two roots at one end.

## 6. POST HOC, decides nothing: what a crossing costs against the move a trade makes

`τ_trade × mean_spread_ticks` (D510's spread) = **the quoted spread in units of per-trade volatility**:

| root | σ/trade $ | spread $ | **spread / σ_per_trade** |
|---|---:|---:|---:|
| **ZN** | 0.967 | 15.63 | **16.17** |
| **ZB** | 2.864 | 31.32 | **10.93** |
| ES | 4.245 | 14.00 | 3.30 |
| 6E | 2.690 | 8.10 | 3.01 |
| CL | 8.779 | 16.78 | 1.91 |
| GC | 23.659 | 44.35 | 1.87 |
| NQ | 11.226 | 18.84 | 1.68 |
| YM | 7.865 | 12.91 | 1.64 |

**On ZN you pay sixteen times the per-trade volatility to cross. On the bottom five you pay under
two.** This is [D510 §6](D510-RESULT-the-tick-binds-on-ZN-and-ZB-and-on-nothing-else-lane-21s-ES-claim-is-refuted-and-the-property-that-makes-them-predictable-is-what-makes-them-expensive.md)'s
tension restated at the trade horizon, and it is sharper here than it was there.

> **The consequence for `C6`, stated as an implication and not as a verdict: a short-horizon
> directional rule on ZN or ZB cannot be a TAKER. At 16× the per-trade volatility, no direction
> call at that horizon survives one crossing.** The large-tick literature's own strategies are
> **maker** strategies — you join the 4,863-lot queue rather than cross it — and **this programme
> has already read the maker route's price**: lane 21 records Moallemi's *"queue value can be of
> the same order of magnitude as the bid-ask spread"* and *"adverse selection costs are increasing
> with queue position"*, filed there as killing `R2`.
>
> **So `C6`'s premise is confirmed and its execution route is narrowed to the one this repo's own
> research has already priced unfavourably.** **Whether that closes `C6` is the principal's call
> under R15; this record does not make it, and a maker study on ZN has never actually been run
> here** — the lane-21 reading was about equities on NASDAQ ITCH, not about ZN on Globex.

## 7. What the four records now stand on

| | measurement | window | ZN/ZB vs the rest |
|---|---|---|---|
| **D489** | `τ_1h` = tick / hourly σ | 2016–23 **and** 2025–26 | 3.3× clear of 3rd |
| **D510** | `P1` = quoted spread census | 2025–26 | 0.998+ vs ES 0.882 |
| **D511** | `τ_trade` = tick / per-trade σ | 2025–26 | 10.9 vs ES 2.94 |

**`C6` named the right pair, on three independent quantities, with the per-trade version agreeing
with the direct census exactly.** Nothing here touches
[D468](D468-RESULT-none-of-24-session-windows-on-eight-roots-clears-the-component-standard-the-best-sits-at-the-78th-percentile-of-its-family-null.md)'s
`C-a` rejection of ZB, and **none of these numbers is an edge** — all three are properties of the
instrument, which is precisely what a stage-0 premise check is for.

## 8. What was spent

**Trade counts and sizes on 2025-09-11 → 2026-09-09 — the same window and the same non-return
character as D510's quote census.** No construction was scored, no component line computed, no
signed quantity read. **The 2024+ slice remains unspent for every return-bearing construction.**

**Cost: one pre-registration, one runner, one 10.6-minute build over 34.7 GB, one new committed
fixture (`fut_trade_counts.csv.gz`, 2,306 root-sessions).**

**One defect caught before launch and worth recording:** the first day-ordinal implementation used
`DatetimeIndex.view("int64")`, which returned **microseconds** — pandas 2.x infers an index's
resolution from its input, so that view is not reliably nanoseconds. Every timestamp mapped to
January 1970, the day filter would have dropped all 365 million rows, and the build would have
produced an empty fixture after ten minutes. **Check `[1]` compares the fast path against the
`strftime` path it replaces across both DST boundaries and caught it** — the optimisation guard
CLAUDE.md asks for, doing the job it is there for.
