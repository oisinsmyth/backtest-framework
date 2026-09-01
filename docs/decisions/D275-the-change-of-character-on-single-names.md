# D275 — The change of character, on single names at fifteen minutes

**Status:** **RUN AND CLOSED.** Zero of three short cells clear. The legs run; the rule captures 0.3% of them.

**Everything above the RESULT heading was committed in `0b39133`, BEFORE the runner was written.**
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

---

## RESULT — the move is there, and the rule captures a three-hundredth of it

`uv run python scripts/run_choch_short.py` · `data/d275_choch_summary.json` · seed 0, 1,000
rotations, 1,000 bootstrap draws.

### The leg diagnostic, which was not hurdled and is the finding

**188,687 down-legs. Median 182.7 bp, mean 263.0 bp. 99.1% of them exceed the cost bar.**

**The move exists.** The state machine finds real impulse legs, and almost all of them are large
enough to pay for a round trip several times over.

### And the tradeable arm captures +0.57 bp

| stratum | exposure | CAGR | Sharpe | turnover | trades | **move/trade** | cost bar |
|---|---:|---:|---:|---:|---:|---:|---:|
| ALL | 46.9% | −22.17% | −2.020 | 474 | 15,628 | **+0.57 bp** | 8.42 |
| LOW | 45.9% | −11.83% | −1.436 | 471 | 7,770 | **−0.64 bp** | 4.00 |
| HIGH | 47.8% | −31.31% | −1.762 | 476 | 7,858 | **+1.76 bp** | 12.84 |

**A median leg of 182.7 bp; a captured move of 0.57 bp. Three tenths of one percent.**

**The mechanism is visible in the turnover: 474 per year at 47% exposure.** At `k = 2` on
15-minute bars the trend state flips constantly, so the book churns *around* the legs rather than
riding them. Every flip is a round trip, and 474 of them at 8.42 bp costs 40%/yr.

### The hurdle table

| cell | move | Z1 | SR pct | $ pct | Z2 | Z3 | Z4 | Z5 |
|---|---:|---|---:|---:|---|---|---|---|
| ALL short | +0.57b | no | 92.4th | **99.4th** | no | no | no | no |
| LOW short | −0.64b | no | 83.0th | 96.6th | no | no | no | no |
| HIGH short | +1.76b | no | 87.9th | **99.2th** | no | no | no | no |
| ALL long | −0.27b | no | **0.0th** | 10.7th | no | no | no | no |
| LOW long | +1.58b | no | 5.6th | 33.2th | no | no | no | no |
| HIGH long | −2.17b | no | **0.0th** | 13.2th | no | no | no | no |

**Zero of six clear all five.**

### The predictions

| | outcome |
|---|---|
| **Z-a** no short cell clears Z1 | **CONFIRMED** — +0.57, −0.64, +1.76 against bars of 8.42, 4.00, 12.84 |
| **Z-b** the leg runs past `2c` while the arm does not | **CONFIRMED, and by a factor of 320.** This separates *"there is no move"* from *"there is a move we cannot capture"* — and it is decisively the second |
| **Z-c** the short clears the Sharpe leg and fails the money leg | **FALSIFIED, and informatively.** The **money** percentile EXCEEDS the Sharpe percentile in all three shorts — 99.4th against 92.4th — which is the reverse of D256's 100.0th / 0.0th shape. A 47%-exposed short in a rising market loses heavily whatever it does, so rotation loses *more*, and the money leg reads high while the arm still returns −22%/yr. **FINDINGS §3 in its purest form yet: real timing, comprehensively unprofitable** |
| **Z-d** the long control also loses | **CONFIRMED**, and it is at the **0th percentile** on Sharpe in two strata. The state machine's direction *is* informative and it is mirror-imaged: short-in-DOWN beats random, long-in-UP is worse than random |

---

## Stop — fired

**The change of character is closed on this fixture** — no second `k`, no confluence component
added back, no alternative exit, no re-cut strata.

**And the stop is binding on the obvious next thought.** The 182.7 bp leg against a 0.57 bp capture
points at a **leg-relative exit** — hold the leg rather than the state. That is a second
construction, it would need its own registration, and **D274 has just closed time-based exits on
S1 and S2 after finding a random exit bar beats a fixed one.** Named here so the idea is on record
rather than pursued.
