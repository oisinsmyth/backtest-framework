# D492 — the trade count from `tbbo`: the PER-TRADE τ that D489 declared it could not compute

**Pre-registration. Committed before the runner exists ([R8](../RULES.md#r8)).** Result in a
separate file. **NO RETURN IS READ.** Trade counts, trade sizes and quoted prices only.

**Occasioned by:** the principal's instruction, closing the last gap named in
[D489's amendment](D489-PRE-REG-stage-0-is-ZB-actually-a-large-tick-instrument-the-premise-C6-has-never-had-checked.md)
and [D491 §7](D491-RESULT-the-tick-binds-on-ZN-and-ZB-and-on-nothing-else-lane-21s-ES-claim-is-refuted-and-the-property-that-makes-them-predictable-is-what-makes-them-expensive.md).

## 1. The exact quantity D489 could not reach, and why this closes it

D489's amendment said, in writing:

> *"The literature's per-trade τ is not computed here. The proper denominator is the volatility per
> **trade**… `ohlcv-1m` carries no trade count at all, so no column of this fixture could have
> supplied one."*

**`tbbo` carries one record per trade.** That supplies the denominator directly:

| | definition |
|---|---|
| **σ_per_trade** | `σ_session / √n̄`, with **n̄ the mean number of TRADES per front-contract session** |
| **`τ_trade`** | `tick_usd / σ_per_trade` = **`tick_usd × √n̄ / σ_session`** — the literature's ratio |
| **η** | `τ_trade²` — the Dayri–Rosenbaum reading: **how many trades it takes to move one tick** |
| **`sizē`** | mean contracts per trade |

**σ_session comes from `fut_sessions_hourly` on the SAME window**, the era control D491 established
was not a formality (GC's τ fell 5.3× between the two eras). **No quantity here is compared against
D489's 2016–2023 numbers.**

## 2. The loop this also closes: what D489's `τ_vol` was actually measuring

D489 used `τ_vol = tick × √v̄ / σ_session` with **contract volume** v̄ in place of a trade count, and
flagged it: *"volume is not a trade count: it is trades × average trade size, and average trade
size differs across roots."* **That flag can now be turned into a number**, because

```
v̄ = n̄ × sizē        ⇒        τ_vol = τ_trade × √sizē
```

**is an identity.** The runner asserts it holds to 1e-6 on every root. **`√sizē` is therefore
exactly the contamination in D489's secondary statistic, and §5's `U3` measures how many rank
positions it moved.**

## 3. The data, and a semantic caveat named BEFORE the run

**Files:** `data/raw/databento/*/glbx-mdp3-*.tbbo.dbn.zst` — 13 files, **34.7 GB compressed**,
2025-09-11 → 2026-09-10, `stype_in=raw_symbol`, **1,339,484 symbols**, ~**1.4 billion** records.
Outright front contracts of the eight D467/D468 roots (RTY reported, outside every bar), same
`^(ROOT)[FGHJKMNQUVXZ][0-9]{1,2}$` filter and same D467 front-contract map as D491.

> **CAVEAT, stated first: "trade count" means TRADE RECORDS AS PUBLISHED BY MDP3.** CME aggregates
> an aggressing order's fills, so one sweep across several resting orders may arrive as one record
> or as several depending on how the match engine reports it. **This is the same convention the
> microstructure literature uses when working from an exchange feed, and it is not the same as
> "number of aggressor orders."** A root whose participants sweep differently will have its `n̄`
> shifted by that convention, and **`sizē` is reported beside `n̄` precisely so the reader can see
> whether a low count is few trades or big ones.**

**The runner asserts `action == 'T'` on every kept record** and raises otherwise — if `tbbo`
carries non-trade records, counting them would inflate `n̄` for every root silently.

**Session clock:** 18:00 → 17:00 ET, D467's, as in D489 and D491.

## 4. Speed: the projection and the optimisation pass, before launching

**Profiled:** the smallest file (955 MB) decoded **38,193,225 rows in 7.4 s** (5.1 M rows/s, 80
bytes a row). 34.7 GB is ~36× that, so **decode alone is ~4.5 min**.

**Three things in D491's runner would not survive this scale, and all three are changed:**

1. **The per-symbol regex ran on every mapping.** At 16,309 symbols that was free; at **1,339,484**
   it is not. → **cheap prefix test against the root set before the regex.**
2. **`[ids[int(x)][0] for x in a["instrument_id"]]` is a Python loop.** Fine over D491's ~250k kept
   rows a file; here the kept set is hundreds of millions. → **vectorised `np.searchsorted` into
   sorted id arrays.**
3. **`strftime` over the kept timestamps is the real bottleneck** — Python-level formatting per
   element. → **integer day ordinals** (`normalize()` then one integer division), with strings
   built **only on the aggregated output**. Aggregation is per chunk, so memory stays flat.

**Projected wall time: 10–15 minutes.** Chunked at 5 M records (≈400 MB resident), aggregated per
chunk, never concatenated.

## 5. Declared conditions

- **`U1` — the D489 test on the quantity D489 could not compute.** **`U1` passes iff ZB ranks in the
  TOP 3 of the eight roots on `τ_trade`.** D489's `T1` passed on `τ_1h`; this asks whether it
  survives on the literature's own ratio.
- **`U2` — three-way agreement.** Spearman rank correlation of the `τ_trade` ordering against
  **D491's `P1` ordering** on the same window. **`U2` passes iff ρ ≥ 0.7.** `P1` saturates at the
  top (ZN 1.000, ZB 0.998) and `τ_trade` does not, so **if they agree, the large-tick tier is
  robust across three independent measurements; if they disagree, `P1`'s ceiling was hiding the
  ordering.**
- **`U3` — how much of D489's `τ_vol` was trade size?** Report `√sizē` per root and **the number of
  rank positions that differ between the `τ_vol` ordering and the `τ_trade` ordering.**
  **Descriptive, no pass/fail** — it quantifies a caveat D489 already made in writing, and turning
  a stated caveat into a verdict after the fact would be scoring my own past hedge.

**`U1` and `U2` do not gate each other and nothing is abandoned on this record.**

## 6. Predictions

- **`V-a` — `U1` PASSES: ZB in the top 3 on `τ_trade`.** ZN and ZB lead both prior measurements by
  wide margins and `√n̄` would have to differ by more than an order of magnitude to overturn it.
- **`V-b` — `U2` PASSES with ρ ≥ 0.85.** Three measurements of one property should order eight
  objects nearly the same way; D491 already got ρ +0.929 against `τ_1h`.
- **`V-c` — ES has the HIGHEST trade count of the eight and ZN the highest `sizē`.** ES is the most
  traded contract here; ZN's 4,863-lot touch (D491) implies large resting size and I expect large
  prints with it.
- **`V-d` — `τ_vol`'s ordering differs from `τ_trade`'s by AT LEAST TWO rank positions**, because
  `√sizē` cannot be constant across roots whose touch depth spans 4 to 4,863 lots. **If they turn
  out identical, D489's `τ_vol` was a better statistic than its own caveat allowed and I will say
  so.**
- **`V-e` — η (trades per one-tick move) is of order 100–1,500 on ZN and of order 1–30 on NQ and
  GC.** This is the widest-uncertainty prediction here: **I do not know these trade counts and am
  not pretending to.**
- **`V-f` — ZB's `n̄` is well below ZN's, by 3–10×.** D491 put ZB's touch at 1,386 lots against ZN's
  4,863 and ZB's queue at 207 orders against 527.
- **`V-g` — wall time 10–15 min** (§4).

> **My last three records ran 2-of-6, 1-of-7 and 5-of-6 wrong, with the ZB misses all in the same
> direction.** `V-e` is written with an explicit order-of-magnitude band rather than a point,
> because a confident number I do not have is worse than a stated ignorance.

## 7. Not in scope

**No return, no signal, no strategy, no cost model, no component line, no book.** Counts, sizes and
the quoted prices already censused in D491. **The `side` field is NOT read** — aggressor direction
is a flow quantity and reading it would take this past a count.

**The 2024+ slice is the same one D491 spent for a quote census and it is spent here for the same
kind of quantity.** **It remains unspent for every return-bearing construction**, and this record
says so explicitly so that a later study cannot claim otherwise.
