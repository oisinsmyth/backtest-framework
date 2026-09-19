# Micro-vs-Full Order Flow: A Retail Positioning Feed

**Status:** study design and pre-registration draft
**Instruments:** MES/ES, MNQ/NQ, MCL/CL, MGC/GC, M2K/RTY
**Horizon:** minutes to one day; both a standalone signal and a shared input to the other event
studies
**Novelty:** high — this dataset did not exist before 2019 and has no equivalent in any prior
market structure.

**Companions:** `EVENT_PORTFOLIO.md`. (`PROP_LIQUIDATION_CASCADES.md` originally consumed this
signal; that study was killed at premise check — see its §0 — and the retail-stop remnant
described there would use F2 if pursued.)

---

## 1. The idea

### 1.1 Micros are a segregated participant population

Full-size and micro contracts share an underlying, a tick grid, and a settlement. They do not
share the same participant mix. In the **real exchange book**, micros are traded predominantly
by **retail on genuine brokerage accounts** (Tradovate, NinjaTrader Brokerage, AMP and
similar). Institutions use them only occasionally, for granular hedging.

**Correction recorded 18 Sep 2026:** an earlier framing included funded prop-firm traders in
this population. They are **not** in the real book — the overwhelming majority of funded prop
accounts are simulated and their orders never reach the exchange (see
`PROP_LIQUIDATION_CASCADES.md` §0). The micro book is retail-skewed, but by *broker* retail,
which is a smaller population than the prop-inclusive framing implied.

Consequently, **order flow in the micro relative to the full-size contract is a real-time read
on what the broker-retail population is doing** — tick by tick, with no survey lag, no COT delay,
and no self-reporting bias. The segregation is real but **less clean than a pure retail/institution
split**; T0 (§4.1) exists to measure how clean it actually is.

Nothing like this existed before micros launched. Retail positioning in futures was previously
inferred from the Non-Reportable COT category, weekly, three days late, in aggregate.

### 1.2 Why retail flow should carry information

The equity literature documents that retail order imbalance predicts short-horizon returns —
positively at first (retail flow moves price), then reversing (retail is on the wrong side of
liquidity). Whether the same holds in micro futures is **open and testable**, and the test is
cheap because the data is held.

Two candidate mechanisms, with different predictions:

| Mechanism | Prediction |
|---|---|
| Retail is **liquidity-demanding and uninformed** | Micro flow imbalance → short-horizon **reversal** |
| Retail flow is **the marginal buyer** in thin conditions | Micro flow imbalance → short-horizon **continuation**, then reversal |

The horizon at which the sign flips is the key empirical output.

### 1.3 Why it passes the filter

Named population (broker-retail futures traders), a structural reason for their flow to be
uninformed on average (they are not the marginal informed participant), and a signal that is
**segregated by instrument** rather than inferred. Capacity is tiny — the whole signal lives in
the micro book.

---

## 2. Features

| ID | Feature | Definition |
|---|---|---|
| F1 | **Micro aggressive imbalance** | (Buy − sell) aggressive volume in the micro, rolling window, normalised by total micro volume |
| F2 | **Micro/full imbalance divergence** | F1 minus the same quantity in the full-size contract |
| F3 | **Micro share of total volume** | Micro notional ÷ (micro + full notional) — how retail-dominated the tape is right now |
| F4 | **Micro book skew** | Resting bid depth ÷ ask depth in the micro, versus the full-size |
| F5 | **Cumulative micro delta** | Session-to-date signed micro volume — the crowd's net position build |

F2 is the primary feature. **F1 alone is contaminated by the common flow both books share; F2
isolates the retail-specific component.**

F3 is a conditioning variable rather than a signal: the retail-specific information in F2
should matter more when F3 is high.

---

## 3. The confound

Micro and full-size prices are pinned together by arbitrage. So micro flow that moves price
moves the full-size price too, and **F1 will correlate with returns mechanically** regardless of
any information content.

The defences are the same as in `OVERNIGHT_IMBALANCE.md` §2: use the **divergence** (F2) rather
than the level, use **book-state** (F4) rather than trade flow, and residualise flow on the
contemporaneous return before using it as a predictor of the *next* return.

---

## 4. Pre-registered tests

### 4.1 T0 — Is there a distinct micro population?

Before anything else: is F2 meaningfully non-zero? If micro and full-size flow are near-identical
in sign and timing, the populations are not segregated and the whole premise fails.

**Prediction:** F2 has substantial variance and low correlation with F1's full-size counterpart.
Diagnostic, not a trial.

### 4.2 T1 — Sign and horizon

IC of F2 against forward returns across a horizon grid: 1, 5, 15, 30, 60 minutes, close, next
open. **Prediction:** positive at the shortest horizons (retail moves price), turning negative
beyond ~15–30 minutes (retail is faded). The zero-crossing is the primary output.

### 4.3 T2 — Conditioning on F3

The F2 effect should be **stronger when F3 is high** — when the tape is more retail-dominated.
Continuous conditioning, not a regime split.

### 4.4 T3 — Positioning extremes

F5 at session extremes (top and bottom decile of its own distribution) should predict reversal
into the close — the crowd is maximally positioned and has to exit.

---

## 5. Data

Held in full: all five micro/full pairs, Databento GLBX.MDP3 with aggressor flags.
**Sample:** micros from May 2019 (equity index), later for MCL/MGC. **Five to seven years.**

**Aggressor-side identification** is the load-bearing data element. Verify the flag is reliable
in the micro book specifically, where fills may be small and queue behaviour different.

---

## 6. Cost

Depends entirely on the horizon the sign-flip lands at. A 5-minute reversal is unlikely to clear
micro round-trip cost; a 30-minute one may. **The cost gate runs after T1, not before**, because
the horizon is the output of T1.

---

## 7. Trial budget

**5 trials:** F1, F2, F4, F5 as features (4), plus T3 (1). T0 and T2 are diagnostic / conditioning.

---

## 8. Kill criteria

1. T0 fails — populations not segregated. **Terminal.**
2. T1 shows no horizon at which IC is significant after overlap correction.
3. The horizon with edge is one where cost dominates (§6).
4. Effect confined to 2020–21 retail frenzy.

---

## 9. Constraint fit

Directional, single instrument, flat by default at whatever horizon T1 identifies. Fully
compliant. Trades continuously.

---

## 10. Why this is a shared input, not only a strategy

Even if the standalone signal fails the cost gate, **F2 and F3 are inputs to every other event
study:**

- The retail-stop remnant of `PROP_LIQUIDATION_CASCADES.md` §0.1, if pursued, would use F2 bursts near technical levels as its detector
- `OVERNIGHT_IMBALANCE.md` can condition on F3 — retail-dominated overnight sessions
- `GAMMA_CONDITIONED_CLOSE.md` can use F5 to distinguish dealer flow from retail flow into the close
- `SESSION_HANDOFF_LIQUIDITY.md` uses F4 to gauge whether thin-window flow is retail (uninformed) or not

**Build this first.** It is the cheapest of the five, the data is entirely held, and its
outputs are load-bearing for the others regardless of its own P&L.

---

## 11. Sequence

1. Build F1–F5 across all pairs; validate aggressor flags.
2. T0.
3. T1 — the horizon grid. Read the sign-flip off the IC decay curve.
4. Cost gate at the identified horizon.
5. T2, T3.
6. Export F2, F3, F4, F5 as shared features for the other studies.

---

## 12. Open questions

1. How large is the broker-retail micro population relative to institutional granular-hedging use? This sets the ceiling on F2's information content and is what T0 measures.
2. Does the micro population's behaviour differ by instrument — MNQ retail vs MCL retail?
3. Is there a **weekly** structure — retail more active on certain days?
4. Does micro flow lead full-size flow at any horizon, or only lag it?

---

## 13. Honest position

The most **generative** of the five: a genuinely new dataset, cheap to build, and useful to
everything else whether or not it stands alone. Its standalone edge is uncertain and probably
horizon-dependent in a way that may not clear costs.

If forced to build only one thing from the event portfolio first, build this — not because it is
the strongest strategy, but because several of the others depend on it.

**Premise check, 18 Sep 2026:** the population claim was corrected (§1.1). The mechanism
survives because broker-retail genuinely does route micros to the exchange. But the population
is smaller than first framed, and T0 is now load-bearing rather than a formality.
