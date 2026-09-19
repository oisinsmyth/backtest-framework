# Session-Handoff Liquidity Provision: Study Design

**Status:** study design and pre-registration draft
**Instruments:** MES, MNQ, MCL, MGC, M6E — anything with a genuine 24-hour session
**Horizon:** minutes; fixed windows; flat outside them
**Novelty:** low on mechanism — liquidity handoffs are structural and well understood. The edge,
if any, is in capacity: this is market-making at a size no market-maker bothers with.

**Companions:** `OVERNIGHT_IMBALANCE.md` (template), `EVENT_PORTFOLIO.md` (stacking).

---

## 1. The mechanism

### 1.1 Liquidity is provided by people, and people work shifts

Globex trades ~23 hours a day, but the liquidity providers do not. Market-making desks are
staffed by region: Asia, then Europe, then the US. **At each handoff, the outgoing desk winds
down and the incoming one has not yet ramped up.** Quoted depth thins, effective spreads widen,
and the book's ability to absorb an order without moving falls.

The windows are structural and recur daily:

| Handoff | Approximate ET time | Character |
|---|---|---|
| Asia → Europe | ~02:00–03:30 | European cash open; FX and index most affected |
| Europe → US pre-market | ~07:30–08:30 | US data releases at 08:30 land in the thin window |
| US close → Asia | ~16:00–18:00 | Includes the 17:00–18:00 Globex maintenance halt |

### 1.2 Who trades badly in the thin window

Anyone who **must** trade at that time regardless of cost: stop-loss orders triggered by
overnight moves, participants reacting to overseas news, algorithmic rebalancers on fixed
schedules. They pay the wide effective spread because they have no choice.

### 1.3 The trade

Provide liquidity in the thin window: rest limit orders on both sides, capture the spread, and
hold inventory for minutes until depth returns and the position can be unwound at the normal
spread. This is **market-making with a time filter**.

### 1.4 Why it passes the filter

Named counterparty (anyone forced to trade in the thin window), structural constraint (staffing
patterns, scheduled releases), derivable timing (the windows recur), and a documented payment
(the bid–ask spread).

### 1.5 Why the edge should persist

**Capacity, entirely.** A market-maker running this at institutional size would be the liquidity
that closes the gap. At micro-contract size you are a rounding error — small enough that the
thin window stays thin, and the spread stays available.

---

## 2. Derivation

The expected profit per round trip is the effective half-spread captured minus adverse selection
minus inventory cost:

```
E[π] = ½ · spread_thin  −  E[adverse selection | thin window]  −  cost_inventory(hold_time)
```

- `spread_thin / spread_normal` is directly measurable from the book — **the size of the
  opportunity is observable before you trade it**
- Adverse selection is the risk that the counterparty who hits your quote knows something.
  In the thin window, the informed share of flow is **likely higher** (news-driven), which
  works against you. This is the term that decides the study.
- Inventory cost scales with how long depth takes to return

The derivation gives you the **shape**; the adverse-selection term is estimated.

---

## 3. Features

| ID | Feature | Definition |
|---|---|---|
| F1 | **Depth ratio** | Depth at touch (5 levels) ÷ same-time-of-day trailing median |
| F2 | **Spread ratio** | Effective spread ÷ trailing median at that time |
| F3 | **Window flag** | Inside a pre-registered handoff window |
| F4 | **Toxic-flow proxy** | Recent aggressive volume ÷ depth — high values mean informed or forced flow |
| F5 | **Depth recovery rate** | Slope of F1 over the prior 10 min — is liquidity returning? |

**Signal:** provide two-sided liquidity when F3 is on, F2 is elevated, and F4 is **not** extreme
(avoid quoting into a news shock). Size inversely to F4. Unwind when F1 recovers past a
pre-registered threshold or on a fixed timer.

---

## 4. The discriminator

Passive liquidity provision earns the spread and pays adverse selection at **all** times. This
study has an edge only if **the thin-window spread capture exceeds the thin-window adverse
selection by more than the same calculation in normal hours.**

**Pre-registered test:** realised spread (the standard microstructure measure, capturing net of
adverse selection) inside handoff windows versus a matched sample of normal-hours windows.
**Prediction:** realised spread is higher inside handoff windows.

If it is not — if the wider spread is fully explained by higher adverse selection — the thin
window is fairly priced and there is nothing here.

---

## 5. Data

| Data | Use | Status |
|---|---|---|
| Full-session MBP-10 for all target micros | F1–F5, targets, cost | Held |
| Exchange session and maintenance schedule | Window definition | Free |
| Economic release calendar | Exclude 08:30 releases from the provision window | Free |

**Sample:** post-2017 for book-state reliability (per `DATA_EXPANSION_PLAN.md` §2.1). Nine
years, every trading day, three windows — **the deepest event sample of the five.**

---

## 6. Targets

Market-making targets differ from directional ones:

| Target | Definition |
|---|---|
| T1 | **Realised spread** per fill — the primary metric |
| T2 | Inventory P&L over the hold window |
| T3 | Fill rate — fraction of quotes that execute |

Report all three. A high spread with a low fill rate is not a strategy.

---

## 7. Cost — different shape here

You are **earning** the spread rather than paying it, so the gate is different: commission per
side must be well below the half-spread captured. On micros with $0.50–1.50 commissions and a
$1.25 tick (MES), **a single-tick spread capture barely covers commission.** This is the
binding constraint, and it may kill the strategy on MES while leaving it viable on MCL or MGC
where the tick is worth more relative to commission.

**Test per instrument, not pooled.**

---

## 8. Trial budget

**7 trials.** F1–F5 (5), the §4 discriminator (1), the per-instrument cost split (1). Window
boundaries are set from the observed depth-ratio troughs, **not tuned to P&L**.

---

## 9. Kill criteria

1. Commission ≥ ½ spread captured on all instruments. **Terminal.**
2. §4: realised spread inside windows ≤ realised spread outside. **Terminal — fairly priced.**
3. Fill rate too low for the breadth argument to hold.
4. Effect present only in the 2020 vol regime.

---

## 10. Constraint fit

| Constraint | Fit |
|---|---|
| Futures only | Yes |
| **Prop rules** | **Problematic.** Two-sided quoting is inherently a hedged structure. Most prop firms prohibit simultaneous opposing positions. This may be **personal-capital only.** |
| Trailing DD | Minutes of exposure; small inventory |
| Minimum activity | Very high |
| Algorithmic | Fully — but requires limit-order management, not just timed market orders |

The prop conflict is real and probably decisive for that account type. A **one-sided** variant
(only bid or only offer, direction from a separate signal) is compliant but is a different and
weaker strategy.

**Second, independent prop problem, added 18 Sep 2026.** Funded prop accounts are predominantly
**simulated** (see `PROP_LIQUIDATION_CASCADES.md` §0). A passive-quoting strategy's P&L in a sim
environment is determined by the **firm's fill engine**, not by the real book. Sim engines
commonly fill resting limit orders at the touch or when price trades through, with no queue
position and no adverse selection — which makes market-making look far better in sim than it is
live, and is exactly the kind of "exploiting sim" that firms' rules prohibit and risk teams
watch for. **This study should be treated as personal-capital only**, and its cost model must be
built from the real book, not from a sim fill assumption.

---

## 11. Sequence

1. Characterise depth and spread by time-of-day across all instruments. **This alone is a useful
   artefact** — it tells every other event study when liquidity is available.
2. Per-instrument cost gate. **Stop on instruments where commission dominates.**
3. §4 realised-spread discriminator.
4. Build the quoting logic; paper-fill against the historical book.
5. Full harness on T1–T3.

---

## 12. Open questions

1. Does the 08:30 ET release cluster make the Europe→US window untradeable, or is the window
   before 08:25 clean?
2. Is the Asia→Europe window better in FX micros (M6E) than in index?
3. How much does queue position matter at micro scale? If fills require being first in queue,
   this is a latency competition and you lose.

---

## 13. Honest position

Lowest novelty, deepest sample, most reliable mechanism, worst prop-compatibility, and a cost
structure that may kill it on the most liquid instruments.

Its real value to the programme may be the **by-product**: a time-of-day liquidity map across all
your instruments, which every other study in `EVENT_PORTFOLIO.md` needs for cost modelling.
Build step 1 regardless of whether the strategy proceeds.
