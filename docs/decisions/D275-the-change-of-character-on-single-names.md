# D275 — The change of character, on single names at fifteen minutes

**Status:** PRE-REGISTERED. Committed **before the run**. Nothing here is a result.
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

---

## What this is

The **BOS / CHoCH state machine** — `research/structure.market_structure` — run as a short on the
eight-name intraday fixture. It is the one component of the structure programme that has never
been tested outside crypto, and it is a **different shape** from everything this session has run:
an event and state-transition rule, not a continuous score.

**That distinction matters.** [D267](D267-the-magnitude-calibration-screen.md) closed nine
continuous scores on their failure to be magnitude-calibrated. **A state machine has no strength
dimension to calibrate**, so that verdict does not transfer to it.

## Disclosure — the structure programme, and why its 86 looks are not inherited

`STRUCTURE_RESULTS.md` (D204–D211) mechanised five price-action components on BTC/ETH 15m and
closed them. **But C1 — the change of character itself — was the weakest part of that closure:**

| symbol | real Sharpe | null p95 | percentile |
|---|---:|---:|---:|
| BTCUSDT | +0.124 | +0.533 | **66.2th** |
| ETHUSDT | −0.068 | +0.532 | **43.6th** |

**A null result on two symbols with opposite signs, not a refutation.** The programme's decisive
finding was about the *confluence stack* and the *features* — *"once leg size relative to ATR is
held constant, no component predicts anything"* — and its three apparent survivors turned out to
be **one quantity under three names**, `stop_atr`, at pairwise correlations of 0.79–0.88.

**And its closure is scoped in its own words:** *"a result about these definitions, on these bars,
in this decade"*, with the state machine listed explicitly under **"not closed — reusable and
pinned by test."**

**So: new ledger, structure's 86 disclosed and not summed** — the reasoning the principal
established for the terrain programme in [D272](D272-the-volume-profile-as-a-positional-input.md),
applied again. Multiplicity corrects for looks at the same hypothesis; crypto components under a
confluence stack is not this hypothesis.

---

## Construction — one rule, nothing stacked

```
state    = market_structure(bars, k = 2)        # PRIMARY_K, the structure programme's own
position = -1  while state.trend is DOWN
            0  otherwise
flatten  at every session open (intraday-only, as D247 defines it)
lag      = 1 — the state at t-1 decides the position held through t
```

**`k = 2` is the structure programme's pre-registered primary and is not varied.** No confluence
filter, no flipped level, no Fibonacci, no fair-value gap, no RSI — those are the four components
whose stacking D211 measured as **making the arm worse before costs**, and adding any of them here
would be re-running the study that closed.

**Long controls** (`trend is UP` → long) are included because [D247](D247-the-short-side-at-fifteen-minutes.md)'s
design requires them: without them a short failure cannot be attributed to direction rather than
to 15-minute sampling breaking the estimator.

**Cells: 1 arm × 2 directions × 3 strata = 6.** Counted in full.

**Fixture:** `single_name_intraday_15m_panel.csv.gz`. No fetch. Costs and borrow exactly as D264
set them.

---

## Hurdles

| | standard |
|---|---|
| **Z1** | **Mean move per trade ≥ `2c`** — 4.00 bp LOW, 12.84 bp HIGH, 8.42 bp ALL. The primary, because D265 reduced the entire cost problem to this and the trade count cancels out of it |
| **Z2** | **Matched-count rotation null at ≥95th on BOTH legs**, Sharpe and money ([R10](../RULES.md#r10)'s second corollary) |
| **Z3** | **Positive net CAGR** after fees, financing and borrow (hurdle V) |
| **Z4** | **Paired bootstrap p05 > 0.** Never optional (R6 / D230) |
| **Z5** | **Best-of-6 floor** (D228), one shared offset vector |

**All five.**

**The `Leg` is measured as a DIAGNOSTIC, not a cell.** The state machine emits the impulse leg
following each CHoCH, and how far that leg actually runs is the thing a target rule would need. It
is reported and **not hurdled**, because a leg-relative exit is a second construction and would
need its own registration.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **Z-a** | **The CHoCH short does not clear Z1.** Nine scores, three orthogonal input families, a volume profile three ways and two exit levers have all failed the same arithmetic | **high** |
| **Z-b** | **The post-CHoCH leg runs further than `2c` on average, while the tradeable arm does not.** This separates *"there is no move"* from *"there is a move we cannot capture"*, and only the second leaves anything open | **moderate** |
| **Z-c** | **The short clears the rotation null's SHARPE leg while failing its money leg.** [D256](D256-the-book-on-single-names.md) measured exactly that shape — 100.0th on Sharpe, **0.0th** on money — because a short in a rising market beats a rotated book by being less exposed to the rally. **Declared so a single-leg pass cannot be read as evidence** | **moderate-high** |
| **Z-d** | **The long control also loses**, reproducing D247's *"15-minute sampling breaks both estimators in both directions"* | **moderate-high** |

---

## Stop

**If no short cell clears all five, the change of character is closed on this fixture** — no second
`k`, no confluence component added back, no alternative exit, no re-cut strata.

**Nothing is promoted under any outcome.** R8 governs.

---

## Ledger

| count | N |
|---|---:|
| fresh — 1 arm × 2 directions × 3 strata | **6** |
| + the leg diagnostic | 9 |
| carried from D273 | 46,233 |
| + [D274](D274-the-exit-timing-diagnostic.md)'s exit sweep (12 k × 2 arms) and the halt test's 6 | 46,263 |
| **total** | **46,272** |

**Disclosed and not summed: the structure programme's 86 looks**, spent on five components under a
confluence stack, on crypto.
