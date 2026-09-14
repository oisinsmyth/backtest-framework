# D528 ADDENDUM 7 — the trade anatomy: the geometry is free, and the edge is fifty cents

Date: 2026-09-14. Runner: `working/d528_trade_anatomy.py`.

**Nothing admitted (R15).** Micro universe (8 roots), in sample only; reserved slice UNREAD.

The principal asked three things: why is it so bad, why isn't the win rate higher, and why are the
nulls so high. The first two have one answer. The third has two, and only one of them is real.

---

## 1. Why a good reward-to-risk is not an edge — the conservation law, measured

On any martingale, optional stopping forces `E[gross] = 0` for **any** target/stop pair. So the hit
rate is not something a strategy earns — it is the **price the market charges for the payoff you
asked for.** Cell B (n=12,865, tight enough to read), all 30 geometries:

| | hit rate | payoff | hit × payoff | NULL gross $ | real gross $ | **real − null** |
|---|---:|---:|---:|---:|---:|---:|
| reflect / drift / 2.5 | **9.2%** | 2.16 | 0.198 | −0.66 | −0.15 | **+0.51** |
| reflect / frozen / 3.0 | 17.1% | 2.15 | 0.367 | −1.10 | −0.26 | **+0.84** |
| opposite / frozen / 3.0 | 18.5% | 1.95 | 0.360 | −1.22 | −0.46 | +0.76 |
| level / drift / 3.0 | 21.4% | 1.36 | 0.291 | −1.37 | −0.87 | +0.49 |
| level / frozen / 4.0 | 36.5% | 0.89 | 0.323 | −2.37 | −2.04 | +0.34 |
| level / frozen / 5.0 | **44.1%** | 0.71 | 0.312 | −2.94 | −2.50 | +0.44 |

**The hit rate spans 9.2% to 44.1% — a factor of 4.8 — and the payoff spans 0.71 to 2.30, a factor
of 3.2. Their product spans 0.198 to 0.386.** The product is far more stable than either factor,
which is the conservation law showing up in real data: **a high win rate and a good payoff are two
ends of one dial and cannot be had together.**

So the answer to "the win rate should be much higher" is that it *can* be, instantly, by moving the
stop out — and it is revenue-neutral. ADDENDUM 4 measured exactly that: win rate 30.6% → 55.3%
across the stop ladder, net P&L moving ~$1 on a $7 loss.

### 1.1 And `real − null` is positive in ALL THIRTY geometries

Range **+0.24 to +0.84**, mean about **+$0.50 per trade**. That is the edge, and its consistency
across 30 different target/stop/frame combinations is the strongest evidence in the programme that
it is real rather than an artefact of any one geometry.

**The cost is $4.68 per round trip. The edge is $0.50. It is 11% of cost.**

That is the whole answer to "why is it so bad". **It is not bad — it is very nearly fair, and
fair loses by exactly the cost.** Note the null's gross is itself negative everywhere (−0.66 to
−2.94) and tracks the geometry monotonically: that is the realised-fill overshoot charge, which is
why only real-minus-null at a fixed convention is interpretable.

## 2. Why the nulls are so wide — it is n, against a skewed payoff

| cell | n | per-trade sd | SE of mean | skew | kurt | trades carrying half the +P&L |
|---|---:|---:|---:|---:|---:|---|
| C `traverse` | 109 | $36.54 | **$3.50** | +3.71 | 22.0 | **5 of 30 winners** |
| B `no classifier` | 12,865 | $26.82 | **$0.24** | +3.95 | 50.8 | 432 of 3,643 winners |

A 1.645-SE p95 therefore sits **+$5.76** above the null median in cell C, and **+$0.39** in cell B.

**The edge is $0.50.** So:

* **cell B resolves it** — $0.50 against an SE of $0.24 is ~2.1 SE, which is exactly why cell B
  clears its p95 in 6 of 10 rungs (ADDENDUM 6 §3) on a genuinely negative net number;
* **cell C cannot** — it would need about **14,500 trades** for its SE to fall far enough
  (`n = (1.645 × 36.54 / 0.50)²`), and it produces 109 in 147 sessions.

**The null is not inflated. The estimator is imprecise, and the null is the only thing that was
telling us so.** Nothing smaller than a few dollars a trade is resolvable at n=109, and the effect
is thirty to fifty cents.

## 3. And cell C's apparent advantage is five trades

`traverse`, `reflect`, drift, G=3.0, n=109:

| | n | share | mean $ | median $ | sd | min | max | mean bars |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| TARGET | 12 | 11.0% | +70.56 | +50.37 | 64.98 | +11.4 | +242.6 | 8.0 |
| STOP | 91 | **83.5%** | −13.78 | −11.82 | 10.64 | −56.6 | +4.1 | 3.6 |
| TIMEOUT | 6 | 5.5% | +37.74 | +34.27 | 21.41 | +8.4 | +63.4 | 22.2 |

Net percentiles: p25 −15.6, **p50 −10.0**, p75 −3.2, p90 +41.5, p99 +136.2, max +242.6. Mean
−$1.66 against a median of −$10.00 — the mean is a tail artefact.

**Concentration: the top 1 trade is 22.3% of gross positive P&L, the top 5 are 55.9%, the top 10
are 80.3%.** There are only 30 winners in 109 trades.

**By root, NQ is the only profitable one** (+$392 total, mean +$19.60) and **all five others lose**
(BTC −$147, GC −$134, ES −$126, RTY −$79, YM −$54). Four of the five biggest winners are NQ:

```
WIN  +242.61  NQ  2025-11-14  10:13 ET  LONG   15 bars  TARGET
WIN  +139.07  NQ  2026-02-03  13:09 ET  SHORT   5 bars  TARGET
WIN  +103.44  NQ  2026-01-15  10:29 ET  LONG    7 bars  TARGET
LOSS  -56.62  GC  2026-04-08  09:31 ET  LONG    1 bars  STOP
LOSS  -43.07  NQ  2025-12-18  14:56 ET  LONG    2 bars  STOP
```

By the programme's own rule — predict the book from the **trimmed** mean when the top 1% carries
more than 30% of P&L — cell C's headline is not bookable and never was. **Its entire advantage over
cell B is a handful of NQ trades.**

**Cell B, by contrast, has no concentration problem at all**: top 1 trade 0.8%, top 5 3.0%, top 10
5.1% of gross positive P&L — and every one of its eight roots loses money. That is the honest
picture of this construction, and it is why cell B is the cell to believe.

### 3.1 Two structural facts worth keeping

**The median trade lasts 2 bars** (p10 = p25 = 1 bar, p50 = 2, p75 = 6). With the stop at G=3.0
sitting only ~0.32σ beyond a realised entry that averages 2.68σ, 83.5% of trades are stopped inside
3.6 bars. This is not a mean-reversion hold; it is noise-scalping at a fixed cost per round trip.

**Timeouts are profitable in both cells** (+$37.74 cell C at 22.2 bars, +$23.73 cell B at 18.3
bars). Trades that reach neither barrier end up favourable, which says the stop is cutting some
winners. But ADDENDUM 4 measured the stop ladder and net is flat across it, so this is a
redistribution between outcome buckets, not a recoverable amount.

Expectancy decomposes exactly: `0.110 × 70.56 + 0.835 × (−13.78) + 0.055 × 37.74 = −1.67`, against
a measured mean of −1.66. **The stop bucket contributes −$11.51 of it; the target bucket +$7.76.**

## 4. Disposition

**Nothing changes, and the reason is now precisely quantified rather than merely negative.**

1. **The construction is close to fair, not bad.** `real − null` is positive in 30 of 30 geometries
   at about +$0.50 a trade. Cost is $4.68. The edge is 11% of cost.
2. **The win rate is not a defect and cannot be improved for free.** Hit rate × payoff is conserved;
   the win rate is the price of the payoff.
3. **The nulls are wide because n is small, not because the null is generous.** Cell B resolves the
   edge at ~2.1 SE; cell C would need ~14,500 trades and has 109.
4. **Cell C is retired as a candidate.** Its advantage is 5 NQ trades out of 109, top-1
   concentration 22.3%, and five of six roots losing. It should not be cited again without that
   line attached.
5. **Cell B remains the honest measurement** of an effect that is real, consistently signed, and
   about a ninth of what it needs to be.

Unchanged: cost binds, $3.00 of ~$4.66 being commission; the axis is not closed; the reserved slice
is not spent.

**One reporting defect fixed.** The five-biggest-trades block printed `bar // 60` as a clock hour,
so bar 73 read as "01:13" instead of **10:13 ET** — the fixture stores `bar` re-indexed 0–419 from
`DAY_LO = 540` minutes (09:00 ET), so clock time is `(540 + bar)` minutes past midnight. Times above
are the corrected ones.
