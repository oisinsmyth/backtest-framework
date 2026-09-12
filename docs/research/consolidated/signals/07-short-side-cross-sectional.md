# The short side — cross-sectional signals that predict negative returns

[← signals index](00-index.md) · prev: [share count and issuance](06-share-count-and-issuance.md) · next: [structural decay instruments](08-structural-decay-instruments.md)

**Scope.** This page is the **57-liquid-ETF** stream. Its cost bar is **1.85 bp/side**, not 33.8 —
[vs repo R11](../conflicts/02-versus-repo-measurements.md). The equity campaign's short-side material
is at [long leg vs short leg](02-long-leg-versus-short-leg.md).

---

## The headline `[EXT]` `shorts/01`

> **The short-side anomaly literature is almost entirely about individual stocks, and the part that
> survives scrutiny is almost entirely about stocks we cannot trade.**

**Three independent, high-quality results — Asquith/Pathak/Ritter (2005), Hou/Xue/Zhang (2020),
Muravyev/Pearson/Pollet (2025) — each SEPARATELY eliminate the entire short-leg premium** once you
restrict to value-weighted, large-cap, cheap-to-borrow names. **That is exactly our universe.**

> **This is not a "decayed a bit" story. It is a "the effect was never in these names" story.**

## The only genuinely ETF-level short evidence, and why each fails here

| | evidence | why it does not transfer |
|---|---|---|
| **specialised/thematic ETFs** | **−3%/yr alpha, −6%/yr in year one, persisting ~5 years** (RFS 2023). Real, top journal, ETF-level, low turnover, cheap to borrow | **tiny breadth in our universe** |
| **volatility ETPs** (VXX family) | roll yield **≈ −30%/yr**. Enormous effect size | **breadth of one name**, and a documented catastrophic left tail (XIV, Feb 2018) |
| **ETF NAV mispricing reversal** | **14–26%/yr Carhart alpha** (FAJ 2017) | **explicitly only after excluding diversified US equity, Treasuries and sector funds**, and needs near-daily turnover. **Both exclusions are fatal** |

**Everything else in that document is documented, sourced, and then killed.**

## The sign warning — porting the stock result to ETFs trades the wrong way round `[EXT]`

**ETF short interest is dominated by hedging and market-maker "operational shorting", not directional
bearish views**, and the published evidence is that **high ETF short exposure POSITIVELY predicts
subsequent underlying-index returns** — **the opposite sign to the stock-level result.**

> **Naively porting Boehmer–Jones–Zhang to ETFs would have us trading the wrong way round.**

**This is the single most actionable line in the shorts stream** and it costs nothing to respect.

## Why the stock-level effect is where we cannot reach it `[EXT]` `shorts/04`

**The "return concentrates in the short leg" literature and the "return concentrates in
expensive-to-borrow names" literature are reporting the same fact from two sides.** Across **162
anomalies**: **+0.14%/month gross, entirely from the short leg, −0.01%/month after borrow fees** — and
**not profitable even before fees once the high-fee 12% of stock-dates are excluded.**

> **Our universe is, by construction, the low-fee 88% where the effect is absent.**

## `[REPO]` — the repo reached the same verdict by a different route

| | |
|---|---|
| [FINDINGS §19](../../../FINDINGS.md) | *"The short side of this programme is a cost failure, and neither sizing nor borrow changes the verdict"* |
| [FINDINGS §30](../../../FINDINGS.md) | **every short signal beats its own names at random times and still loses: the names it shorts rise** |
| [FINDINGS §39](../../../FINDINGS.md) | on the floored universe **the loser decile rises** — every short since D335 has been timing inside a pool that rises |
| [FINDINGS §41](../../../FINDINGS.md) | the **gap-up fade with the market below its 200-day mean** is the first short above every control |
| [FINDINGS §1](../../../FINDINGS.md) | the arithmetic of a short position |

**Agreement, not conflict** — [A8](../conflicts/03-agreements.md). **The repo says we cannot afford
it; the literature says it was never in the names we can reach.** *Both are reasons not to build it,
and they are different reasons — which is worth more than one reason twice.*

**And §41 is the one place the two records point somewhere:** a **conditioned, market-state-gated**
short is the only construction that has cleared controls here. The external literature has nothing to
say about it, because it does not report that object.

## The `$5` interaction `[CONFLICT D2]`

`A3`: the `$5` screen **cuts short-leg alpha 77% and the spread 68% while leaving the long leg
untouched.** **If that transfers, this programme's floor removes most of what a short leg would have
earned** — which is consistent with §39's *"no drifting pool"*. **Not tested here.**

## Where the ranking lives

`shorts/01` §4 ranks every candidate by **expected `exposure × edge`, net of costs and borrow**, and
§3 gives the **cross-cutting reasons most of them fail**. §5 carries its own standing caveats. **Read
those rather than a compression of them.**

---

**Sources.** [`shorts/01`](../../shorts/01-cross-sectional-anomalies.md) ·
[`shorts/04`](../../shorts/04-short-book-construction.md) ·
[`the-reversal-round.md` §1.1](../../the-reversal-round.md) ·
repo: [FINDINGS §1, §19, §30, §39, §41](../../../FINDINGS.md).
