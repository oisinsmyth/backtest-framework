# D406 — options open-interest density at spot: a pre-screen

**Status:** design and bar committed BEFORE the screen runs. Data acquisition in flight.
**Date:** 2026-09-09
**Area:** Strategy research

**This is a PRE-SCREEN, not a pre-registration.** D263's inversion: *measure the conditional
first, against a bar stated before looking, and only pay for a full pre-registration if it clears.*
That pattern has paid three times and cost twenty minutes against a day. **The ledger does not
move. Nothing will be admitted to any book.**

**Number.** `D406`, by PICKUP's three-command procedure: `git log --all` shows D400–D405 used and
nothing at D406+; the only reserved block is `D390–D399` (`945cbb5`). Both branches were live when
this was claimed, so it is committed immediately to stake it.

---

## 1. Why this object, after seven failures

Seven price-level programmes have closed here, and D405 produced the diagnosis that governs this
one:

> A wick — or a volume node, or a swing band, or an inventory field — is evidence that interest was
> **absorbed**, not that it **remains**. Every one of them is a trace of completed trading, read as
> a forecast of trading to come.

And the mechanical corollary: **all seven were pure functions of the past price path**, which is why
a rotation or a shuffle control killed each of them.

**Open interest is different in kind.** It is not derived from prices. It is a count of contracts
outstanding — obligations that must be closed, exercised or expire — and **a strike is a price
level**, so OI at a strike is unfilled interest *at a price*. That is the object the whole line has
been reaching for, with the ingredient finally observed rather than inferred.

**The counter-evidence, stated up front.** [D263](D263-the-cot-positioning-prescreen.md) screened
CFTC positioning — also genuinely observed, also not inferred from price — on the best-powered panel
the prop track has assembled, and got **zero of eight cells with monotonicity failing on all
eight**. "Observe obligations instead of inferring them" has already lost once. D263 also explicitly
left **"Rung 3 — open interest"** untested, which is what this is.

---

## 2. What the coverage probe established

49 requests, 2026-09-09, `temp/av_options_probe.py`:

- **The endpoint is not premium-gated.** It returns `open_interest`, `volume`, `bid`/`ask` with
  sizes, and full Greeks per contract.
- **History reaches at least 2014** — all eight depth probes returned data.
- **OI density collapses below the second dollar-volume decile.** Strikes with OI ≥ 100, by decile:
  **43, 19**, then 4, 8, 4, 4, 2, 2. Four strikes is not a price-level map.

So the usable universe is the top two deciles, ~210 names.

**The structural tension, recorded now rather than discovered later:** those are exactly the names
where this programme has already found the short premium **absent, not merely expensive**
(`research/shorts/01`, value-weighted liquid names). The data is densest where the effect has
historically been most arbitraged away. That is the thing I expect to bite.

---

## 3. The data

`scripts/pull_av_options_snapshots.py`, acquisition only — no statistic and no bar in that file.

- **210 names**, top two dollar-volume deciles, ranked on each name's **first 252 eligible bars**
  in the window: causal, and the convention the fixture's own build screen uses.
- **36 quarterly snapshots**, 2015-02-13 → 2023-11-15, at **mid-quarter (15 Feb/May/Aug/Nov)**,
  deliberately away from the third-Friday quarterly expiry where OI mechanically collapses.
- 7,560 pairs, ~1.9 h at 66/min. Cached under `data/raw/alphavantage/options/`, gitignored (D191).
- **Quarterly rather than monthly is a breadth-over-resolution choice**: 210 names × 36 dates gives
  usable cross-sections, where 59 names × monthly would not.

**The binding universe filter is applied at SCREEN time, not here** — a name enters a snapshot only
if it carries enough OI density at that date (§4). That keeps the universe dynamic and causal
rather than pre-selected on the full window.

---

## 4. THE CONDITIONAL

For name `n` at snapshot `t` with spot `P`:

```
strike axis   OI(K) = calls_OI(K) + puts_OI(K)          summed, NEVER signed
window        W = P +- w * sigma_daily(n, t) * P        in the name's OWN sigma
density       dens = SUM_{K in W} OI(K)  /  SUM_all_K OI(K)
```

A share of the name's total open interest sitting within one daily sigma of where price actually
is. Scale-free, so it is comparable across names, and the contract multiplier cancels.

**Calls and puts are summed and never netted.** A signed aggregate — "dealer gamma" — requires
assuming customers are net long calls and short puts. **That is an inference, and inference is the
thing this whole line keeps dying of.** Per-contract Greeks are observed and may be reported; a
signed dealer-positioning estimate is not used anywhere.

`w = 1.0` primary; `0.5` and `2.0` as shape. Names with fewer than **10 strikes at OI ≥ 100** on a
snapshot are excluded from that snapshot — the density of a four-strike ladder is not a density.

---

## 5. THE BAR — stated before the screen runs

Quintile `dens` cross-sectionally within each snapshot. Two outcomes, and **only the first can
clear.**

### 5a. THE THESIS SCREEN — forward absolute move

**The thesis predicts movement, not direction.** If OI at spot is unfilled interest that gets
absorbed on contact, price should be *held* near it.

| | condition |
|---|---|
| **T1** | mean \|forward move\| is **monotone DECREASING** across Q1→Q5 of `dens` |
| **T2** | Q5 − Q1 is at least **10% of the pooled mean \|move\|**, in that direction |
| **T3** | T1 **survives within volatility terciles** |

**T3 is not optional and is the most likely killer.** `dens` is mechanically higher for low-volatility
names — if a name barely moves, more of its OI sits near spot — and low-volatility names have
smaller subsequent moves. **T1 would be confirmed by a tautology without T3.** Vol terciles use
D392's `tercile_pools` idiom.

**The direction is declared here and cannot be re-read afterwards.** D263 recorded its largest
spread arriving with the wrong sign and refused it as a rescue; the same rule binds here.

### 5b. THE TRADEABILITY SCREEN — signed forward return

Reported for completeness and **cannot clear on its own.** The thesis makes no directional
prediction, so any sign found here is post-hoc, and an undeclared sign is not evidence. It exists
only to say whether a passing thesis result would be an *input* or an *edge*.

Horizons: **1 quarter (to the next snapshot)** primary, **21 bars** as shape.

### 5c. ABANDON

**If 5a fails, D406 closes.** No pre-registration is written, no further rung is pulled, and the
recommendation to close the supply-and-demand line — already standing from D405 §6 — is put to the
principal a second time with this added to it.

---

## 6. WHAT THIS DOES NOT DO

- No position, no book consequence, no admission. A screen scores nothing.
- **No holdout read.** Nothing here touches a holdout fixture.
- **No signed dealer-gamma estimate**, anywhere, for the reason in §4.
- **Does not proceed past a failed bar by widening it.** D197–D203 ran five refinements, each
  beating its predecessor, none moving the null gap.

---

## 7. R13

Seven price-level programmes have closed. This is the eighth look **by object** but the first on an
observable that is not a function of the price path — which is precisely the property §1 argues
makes it worth one afternoon. The ledger carries regardless: 259 terrain looks, 86 structure looks,
D403 and D405 on top.

**Cost if it fails: one afternoon and 7,560 requests.** That is the whole point of the inversion.
