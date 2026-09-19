# Gamma-Conditioned Close: Study Design

**Status:** study design and pre-registration draft
**Instruments:** MES primarily; MNQ secondary
**Horizon:** final 30–60 minutes of the cash session; flat at the close
**Novelty:** moderate — the mechanism is well known in equity options; the 0DTE regime that
makes it large is a 2022+ phenomenon; the micro-futures close-window expression is uncrowded.

**Companions:** `OVERNIGHT_IMBALANCE.md` (template), `EVENT_PORTFOLIO.md` (stacking).

---

## 1. The mechanism

### 1.1 Dealer hedging is mechanical

Options dealers do not take directional views. They sell what customers buy, buy what customers
sell, and **delta-hedge the residual in the underlying** — for index options, that means ES.
The hedge is recomputed continuously and rebalanced as price and time move.

The size of the required rebalance per unit of price move is the dealer's **net gamma**. The
sign of that gamma determines the direction of the mechanical flow:

| Dealer net gamma | Price rises → dealer must | Price falls → dealer must | Effect on the underlying |
|---|---|---|---|
| **Negative** | Buy | Sell | **Amplifies** moves — momentum |
| **Positive** | Sell | Buy | **Dampens** moves — mean reversion |

### 1.2 Why the close

Gamma is highest near expiry and near the money. For **zero-days-to-expiry** options — now a
very large share of index options volume — gamma peaks in the final hour and goes to infinity
at the strike at the bell. Dealers hedging 0DTE books face their largest mechanical flow
requirement in the last 30–60 minutes of the session, **every day**.

### 1.3 Why it is derivable — with a correction

- Options **open interest by strike and expiry** is published daily
- The **dealer positioning convention** (customers net long puts and net short calls, so dealers
  are the opposite) is a stated assumption, standard in the practitioner literature
- Net gamma exposure from **carried** positions is therefore a **calculation from public data**,
  computable before the session opens

**Premise correction, 18 Sep 2026.** The original design computed F1 from the *prior close's*
open interest and claimed this captured the 0DTE regime. **It does not.** Most 0DTE positions
are **opened and closed within the same session**; they never appear in end-of-day OI. Prior-close
OI captures only the carried-over portion of same-day-expiring contracts (positions opened when
the contract was 1DTE, 2DTE, etc.), which is the **minority** of 0DTE gamma.

So the derived regime from public OI is a **partial** measure that systematically misses the
largest and most time-concentrated gamma component — the one the study was named for.

Consequences:
- The regime flag from prior-close OI is still meaningful for **1DTE-and-longer** gamma, which is
  real and mechanical. It is a weaker version of the mechanism.
- Capturing the **intraday 0DTE build** requires **intraday options data** (trade and quote, OPRA
  or CBOE direct) to estimate dealer gamma from volume as it accumulates. That is a materially
  more expensive data requirement than the original design admitted, and it is not held.

The study is **not** killed — the carried-gamma regime is a legitimate, weaker hypothesis — but
its data cost and its expected effect size are both revised.

### 1.4 Why the edge should persist at your scale

The mechanism is crowded in equity options and full-size ES. **It is not crowded in micro ES
in the final 30 minutes**, because the participants who trade the gamma regime professionally
have capacity constraints that make micros irrelevant to them. You are not competing with them
for fills.

---

## 2. Derivation

For each strike `K` and expiry `T`, with call OI `C_K` and put OI `P_K`:

```
GEX_K = gamma(K, T, S, σ) × [ C_K × (+1) + P_K × (−1) ] × contract_multiplier × S²
net_GEX = Σ_K GEX_K
```

The sign convention (calls +, puts −) encodes the dealer-positioning assumption in §1.3.
**State it explicitly as an assumption in the pre-registration.** It is the one place the
derivation could be wrong in sign, and if it is, every result inverts.

The **gamma flip level** — the spot price at which `net_GEX` changes sign — is also
computable, and is the second useful output: the regime can change intraday if price crosses it.

**Time-of-day weighting:** 0DTE gamma dominates in the final hour. Weight the 0DTE expiry's
contribution up as the session progresses, using the standard time-decay of gamma.

---

## 3. Features

| ID | Feature | Definition |
|---|---|---|
| F1 | **Pre-session net GEX (carried)** | §2 calculation on the prior close's OI — captures 1DTE+ and carried 0DTE only |
| F1b | **Intraday 0DTE GEX estimate** | Volume-based dealer-gamma accumulation from intraday options data — **requires data not held** |
| F2 | **Regime flag** | sign(F1): amplifying / dampening |
| F3 | **Distance to flip level** | (spot − flip) / ATR at 15:00 ET |
| F4 | **0DTE concentration** | Share of total gamma attributable to same-day expiry |
| F5 | **Move-so-far** | Return from 14:30 to 15:30 ET — the move the dealer must hedge |

**Signal, final 30 minutes:**
- **Amplifying regime** (F2 < 0): position with the direction of F5 — continuation
- **Dampening regime** (F2 > 0): position against F5 — reversion
- Size by |F1| × F4 (more gamma, more 0DTE, larger mechanical flow)
- Flat at the closing bell

---

## 4. The discriminator

The close window has reversion and continuation effects for many reasons. This study has an edge
only if **the gamma regime predicts which one occurs**.

**Pre-registered test:** the sign of the 15:30–16:00 return relative to F5 should differ between
F2 < 0 and F2 > 0 days. **Prediction:** continuation on negative-gamma days, reversion on
positive-gamma days, with the effect scaling in |F1|.

If the regime flag carries no information, the study stops — whatever close-window effect
exists is not this mechanism.

---

## 5. Data

| Data | Use | Status |
|---|---|---|
| SPX / ES options OI by strike and expiry, daily | F1, F3, F4 | CBOE / CME published; historical needs sourcing |
| **Intraday options trades and quotes** (OPRA / CBOE direct) | **F1b — the 0DTE component** | **Not held. Expensive.** This is the binding data constraint |
| ES/MES intraday | F5, targets, cost | Held |
| Implied vol surface (for gamma calc) | F1 | Approximate from ATM IV is acceptable initially |

**Sample:** daily SPX expirations expanded in 2022. The regime where 0DTE gamma dominates the
close is **2022 onward — roughly four years.** Earlier data tests a weaker version of the
mechanism. Report both, do not pool silently.

---

## 6. Targets

| Target | Window |
|---|---|
| R1 | 15:30 → 15:50 ET |
| R2 | 15:30 → 16:00 (close) — primary |
| R3 | 15:45 → 16:00 |

---

## 7. Cost

Close-window liquidity in ES is deep and micro spreads are tight — this is the **most
cost-friendly** of the five event studies. Still run the gate: a 30-minute holding period on a
signal of modest strength must clear a full round-trip.

---

## 8. Trial budget

**7 trials.** F1, F1b, F2–F5 (6), plus the §4 discriminator (1). Sign convention and time
weighting are **fixed from the literature**, not fitted. **Run F1 (carried gamma) first** — it
uses held data and tests the weaker mechanism cheaply. Only source intraday options data for F1b
if F1 shows the regime flag carries *any* information.

---

## 9. Kill criteria

1. Cost gate fails.
2. §4 discriminator shows no regime dependence. **Terminal.**
3. Effect present with the **wrong sign** — implies the dealer-positioning convention is wrong.
   Do not flip the sign and continue; that is two trials and a lost mechanism.
4. Effect present pre-2022 at equal strength — suggests it is not the 0DTE mechanism but a
   generic close effect, which is a different (more crowded) study.

---

## 10. Constraint fit

Directional, single instrument, flat at close, trades every day. Cleanest constraint fit of the
five. The only friction is sourcing historical options OI, which is a data task rather than a
research problem.

---

## 11. Sequence

1. Source **end-of-day** options OI history; build the carried-gamma GEX calculation; validate
   against a published GEX series if one is available for the overlap. **Do not source intraday
   options data yet.**
2. Cost gate on F2 × F5 → R2.
3. §4 discriminator.
4. Full harness.

---

## 12. Open questions

1. Is the dealer-positioning convention stable, or has the 0DTE retail boom (customers *selling*
   0DTE premium) inverted it on some days? This is the biggest risk to the derivation.
2. Should MNQ be treated with NDX options OI separately, or is the SPX-derived regime sufficient?
3. Does the gamma flip level crossing intraday produce a tradeable regime change, or only noise?

---

## 13. Honest position

Large, mechanical, derivable, daily. The mechanism is not in doubt. What is in doubt is whether
the micro-close expression carries enough edge after cost, and whether the positioning
convention has stayed stable through the 0DTE boom.

**Revised 18 Sep 2026:** the original design overstated what public end-of-day OI can see. The
0DTE component — the largest and most concentrated — requires intraday options data that is not
held and is costly. The cheap version of this study (carried gamma from prior-close OI) tests a
real but weaker mechanism; the strong version has a data bill attached. Sequence accordingly: run
the cheap version, and let its result decide whether the data is worth buying.

Best cost profile of the five, most crowded mechanism of the five, and the one whose sign
assumption could be wrong. The discriminator in §4 decides it quickly.
