# D227 — The time split that cannot answer its own question

**Status:** Committed — **designed, costed, and abandoned on power grounds before any look
was spent**
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user request to test whether D224/D225's volume gate holds in both halves of
the crypto span

> No result section will be appended, because no result was produced. The arithmetic below
> is the finding.

## What was proposed

D225 left the gate above its selectivity null on two symbols and two sampling rates, and
left one damaging fact: its working window is **one point wide**. The natural next question
is whether 50 hours is a property of the market or of these two coins over this span.

The proposed test: split the 8.28-year live span into two disjoint halves, sweep the gate
window over the same grid D225 used, and require hurdle **H to clear in both halves** —
failure in either closing the study — with argmax stability reported alongside.

**The design is sound. The sample cannot support it.** This record exists so nobody
proposes it again.

## The split, which is clean

Measured, and worth keeping because it is the one part that costs nothing to reuse:

| | BTCUSDT | ETHUSDT |
|---|---|---|
| split bar | **149,192 = 2022-06-10 02:00** | same |
| parent flat at the split? | **yes** | **yes** |
| trades straddling the split | **0** | **0** |
| parent trades, h1 / h2 | 919 / 923 | 950 / 941 |
| gate keeps, h1 / h2 | 465 / 462 | 466 / 457 |

The plain midpoint of the live span happens to fall on a flat bar with no trade straddling
it, on both symbols. Because gated cells only ever remove **entire** parent runs,
parent-flat at the split implies every cell is flat there — so a single assertion would
have carried the whole design. That is a nice property and it is not the problem.

## The power calculation, which is the problem

`MDE = 1.645 × sd` of the matched-count random null, at each segment's own removal count,
400 sims, seed 0:

| | null sd | MDE (95%) | D225's measured effect | margin |
|---|---:|---:|---:|---:|
| BTC, **full span** | 0.243 | **+0.400** | +0.635 | **+0.235** |
| BTC, h1 | 0.337 | **+0.554** | +0.635 | +0.081 |
| BTC, h2 | 0.351 | **+0.578** | +0.635 | +0.057 |
| ETH, **full span** | 0.255 | **+0.419** | +0.558 | **+0.139** |
| ETH, h1 | 0.338 | **+0.555** | +0.558 | **+0.003** |
| ETH, h2 | 0.390 | **+0.642** | +0.558 | **−0.084** |

Halving the sample raises the standard error by √2, which lifts the MDE from ~0.41 to
~0.58 — **landing it almost exactly on the effect size**. The effect clears comfortably at
full span and sits *on the threshold* in each half.

### What the proposed stop would actually have done

Assuming the effect is **real and equal in both halves** at D225's measured size:

| | P(h1 clears) | P(h2 clears) | P(both) |
|---|---:|---:|---:|
| BTCUSDT | 59% | 56% | **34%** |
| ETHUSDT | 50% | 41% | **21%** |
| **all four symbol-halves** | | | **7%** |

> **"H must clear in both halves" would have closed the study 93% of the time on an effect
> that is real by assumption.**

That is not a hurdle. It is a coin flip weighted heavily toward closure, and it cannot
distinguish *"the effect is fake"* from *"we halved the data."* Had it run and failed —
which it would have, nine times in ten — the record would have shown a falsified
replication that was nothing of the kind.

### The better-powered reformulation is also not powered enough

The obvious fix is to stop asking whether each half independently clears a bar calibrated
for the full sample, and instead test the **difference between halves** — a direct test of
instability, and better powered because it uses both estimates jointly:

```
sd(Δ_h1 − Δ_h2) = √(0.337² + 0.351²) = 0.487
```

| what we would want to detect | probability of detecting it |
|---|---:|
| the effect **halving** between regimes | **16%** |
| the effect **disappearing entirely** | **37%** |

**A test that misses a total collapse of the effect two times in three cannot be evidence
of stability when it passes.** Both formulations fail, so this is not a matter of choosing
a better statistic.

## The finding

**Two four-year halves of two correlated crypto symbols do not carry enough independent
information to answer a stability question about an effect of this size.** The constraint
is the sample, not the design, and no reformulation on this fixture escapes it.

This is the D206/D216 pattern applied to power rather than to friction: **an arithmetic
gate that ends a study before an experiment.** Computing it cost no looks — a power
calculation is not a hypothesis test — and it is deliberately **blind to the outcome**: the
prior above records the split, the census, and the null's dispersion, and never computes
the gated arm's Sharpe in either half.

## What to do instead

**Get breadth, not a temporal split.** D222 already established that this fixture supports
~11 symbol-years and resolves nothing below ~0.15 Sharpe; halving it makes that worse. The
answer is more instruments, not thinner slices of the same two.

The 57-ETF intraday fixture now being fetched (`scripts/fetch_etf_intraday.py`) is the
properly-powered version of the same question: **does the gate work across 57 instruments,
or only on BTC and ETH?** A cross-sectional test on 57 names — even correlated ones, with
an effective independent count around 2 — carries more information about generalisation
than two halves of two coins, and it asks the question that actually matters.

**The stability question is not abandoned, it is redirected.** It gets asked of the ETF
fixture, where the sample can support an answer.

## Ledger

**Zero looks.** No arm was scored, no verdict was reached, and the gated arm's per-half
performance was deliberately not computed. The census, the split verification and the null
dispersion are all filter-agnostic properties of the parent trade population — the same
standing D220's trade census and D224's oracle bound had.

## What would change this

A materially larger crypto sample: more symbols with long 15m history, or a fixture
extending meaningfully past 2026-07. `probe_binance_archive.py` already knows how to
enumerate what the Binance archive holds, so the feasibility question is answerable cheaply
if anyone wants to revisit it. **Until then, splitting this fixture in time is spending
looks on a question it cannot answer.**
