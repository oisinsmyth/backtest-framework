# Spread estimation — the estimator, its three defects, and the number

[← cost index](00-index.md) · [consolidated index](../00-INDEX.md) · next: [what anomalies pay](02-what-anomalies-pay.md)

**The question.** This programme charges a spread estimated from OHLC, because it has no quotes. How
wrong is that number, and in which direction?

---

## The number, and which number it is `[REPO]`

| | |
|---|---|
| **33.8 bp/side** | D285's **mean over the names actually held**, from the **single two-day** Corwin–Schultz estimate |
| **31.7 bp/side** | universe median under the **published convention** — clamped daily estimates averaged over a month |
| **14.2 bp/side** | universe median of the **per-bar median at entry**, which every runner since D318 was charging |
| **2.03×** | how much the published convention charges over the programme's, across 92 legs (p10 1.40×, p90 3.31×) |

**All four are `[REPO]`, from [FINDINGS §17](../../../FINDINGS.md) / D332.** *"Which convention is
TRUE is not decided, and cannot be from OHLC alone."* **Until quoted `BID_ASK` bars settle it, every
net number in this programme is a `PB`/`PUB` pair.**

> **The research tree does not know this.** All six rounds of campaign 1 and the whole of
> `Scan-100926` reason from *"this programme's 33.8 bp/side"*. See
> [vs repo R1](../conflicts/02-versus-repo-measurements.md).

## Three separate defects in one estimator

### 1 · The zero clamp `[REPO]` — the only one measured on this fixture

The single two-day estimate is **clamped to exactly zero on 43.2% of all live name-bars**, uniformly
across price and **uncorrelated bar to bar**. That is the authors' own convention applied to an
estimate that is negative nearly half the time on every kind of stock. **The zeros are noise, not a
property of any name** — so a leg whose entries land above 50% zeros is charged nothing, and a leg
near 50% is charged by which side it fell.

**The generalisation D332 earned:** *check the clamp rate before summarising with a median; if it is
anywhere near half, the median is measuring the clamp.*

### 2 · It understates small illiquid names `[EXT]` `H4`

Ardia–Guidotti–Kroencke (JFE 2024) find Corwin–Schultz **underestimates** effective spreads for small
illiquid stocks — *"exactly this programme's tail, and exactly the population where its leads keep
dying."* **If it holds here, 33.8 is a FLOOR rather than an estimate**, and every breakeven
comparison on the record is more lenient than it looks.

### 3 · It fabricates its own input on no-trade days `[EXT]` `J5`

**The author's own program forward-fills the high and low** on no-trade days by re-anchoring the
prior-day range — fabricated input on **exactly the halt/no-trade set**. `J5` also records the
related rule: **fill the label, never the price**, and *"the zero-fill is the real fabrication."*

**`C7` records defects 2 and 3 as pushing the interpretation in different directions.** They are not
mutually exclusive, and neither has been checked here.

## The one action that would settle the sign `[OPEN]`

**Recompute D285's 33.8 under EDGE** — a closed-form drop-in on the same OHLC inputs, published code
(`bidask` on PyPI). It is item 2 of [`../../README.md`](../../README.md) §"What is open" and `F5`'s
own recommended first move: *"because it sets the SIGN of every cost conclusion downstream."*

**Never run.** The definitive test is separate and also unrun: **quoted `BID_ASK` bars from IBKR on a
stratified sample of live names, against `PB`, `PUB` and Abdi–Ranaldo, by lowest median absolute log
error, declared in advance** (D332's own specification; D336 is the quoted-spread validation record).

## Two things the estimator is silent about

- **It is right about what it measures and silent about borrow.** [FINDINGS §16](../../../FINDINGS.md):
  a deal stock's spread really is tiny — the pinned-takeover problem is not fixed by changing
  convention.
- **A Corwin–Schultz σ is a lower bound on total price noise** `[EXT]` `K5` — so any reassurance
  derived from it is lower-bound reassurance.

## Where the auctions come in `[EXT]`

**The NYSE MOC/LOC hard cut-off is 3:50 pm** (Nasdaq: MOC 3:55, LOC 3:58, IO 4:00), from the
exchanges' own fact sheets. **A signal computed FROM the close cannot fill IN that close** — a
constraint on construction, not a preference, and a fill convention has already inverted a result
here once (D280).

**Opening auctions carry the largest impact of the three mechanisms** — pooled square-root impact
**17.7 bp at 1% ADV against 2.35 bp modelled linearly** (Goyal–Jegadeesh–Wu, JFQA 2026). **Close
beats open.** Per-bucket figures are `[UNVERIFIED]` and are not used. Compare
[FINDINGS §44](../../../FINDINGS.md) `[REPO]`: the opening minute is 1.4% of the day and the closing
minute 7.9%.

---

**Sources.** [`the-forced-seller-and-the-cost-wall.md` §1.6, §1.7](../../the-forced-seller-and-the-cost-wall.md) ·
[`the-selection-round.md` §1.7, §1.8](../../the-selection-round.md) ·
[`the-reversal-round.md` §1.4](../../the-reversal-round.md) ·
repo: [FINDINGS §16, §17, §44](../../../FINDINGS.md), D285, D332, D336.
