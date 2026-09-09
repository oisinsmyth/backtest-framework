# D399 FORK — two ratchets, and the one I built by mistake produced the better number

**Status:** A FORK RECORD, in `working/` because it is a live decision the principal owns, not a
result. **Nothing here is admitted (R15). No holdout read.**
**Date:** 2026-09-09 · Opened on the principal's instruction: *"Record your version and this split
as a fork to return to as yours genuinely got good results."*

---

## 0. Why this exists

I misread the principal's specification. The misreading is a **different, well-defined
construction** — not a bug — and on the exit the principal specified it produced the first cost
clearance anything in D399 has achieved. **Both branches are recorded so neither is lost, and the
choice between them is the principal's.**

---

## 1. The two ratchets, stated so they cannot be confused again

Both share everything else: S2's fits (`k=3`, `WINDOW=252`, `MIN_PIVOTS=3`), the level dead band
**δ = 1e-3** on both slopes, the gradient hysteresis **h = 1e-3**, the same warm-up, the same
`keep_v2` minimum-$5 universe, the same overlays.

**They differ in ONE line, and it is what the intercept follows.**

### Branch A — "track the refit" (what I built; `run_d399_ratcheted_line.ratchet`)

```
    UP:   L[t] = min(L[t-1] + G,  g_fresh[t]*t + c_fresh[t])
    DOWN: L[t] = max(L[t-1] + G,  g_fresh[t]*t + c_fresh[t])
```

**The line never looks at price.** It advances at the held gradient and is pulled to the fresh OLS
fit whenever that fit is further from price. It therefore converges on the **lower envelope of the
fitted support lines** — a level price revisits constantly.

### Branch B — "respect the line" (what the principal specified; `d399_draw_construction.ratchet_corrected`)

```
    L[t] = L[t-1] + G
    UP:   if low[t]  < L[t]:  L[t] = low[t]      pushed away, exactly as far as needed
    DOWN: if high[t] > L[t]:  L[t] = high[t]
```

**The line never looks at the refit.** It advances at the held gradient and moves **only when price
violates it**, by exactly the violation. If the trend is respected, the intercept does not move at
all.

> **The tell that separates them, on MSFT over 260 bars: Branch B moves the intercept 19 times.
> Branch A moves it on essentially every bar.**

---

## 2. What each produced

### Branch A — measured, in `data/d399_stage0.json`

**Events:** 264,501 UP touches / 152,612 DOWN. **On the state-end exit, primary cell:**

| dir | trades | gross | 2c | **net** | **ratio** | hold | bp/bar |
|---|--:|--:|--:|--:|--:|--:|--:|
| **UP** | 2,699 | **+185.99** | 65.52 | **+120.47** | **2.84×** | 135.3 | 1.37 |
| DOWN | 1,807 | −5.11 | 84.38 | −89.49 | −0.06× | 127.1 | −0.04 |

**All eight UP state-end cells clear H3 at 1.66×–3.72×.** That is the first cost clearance in the
record, and it is why this branch is being kept.

**With the three things that qualify it, carried so the number is never quoted bare:**

1. **It clears by AMORTISATION.** Per-bar edge falls 3.38 → 1.37 (−59%) from cap 5 to the
   state-end exit while gross per trade rises 11-fold. Cost is one round trip whatever the hold.
2. **The atlas cannot floor it.** D392 measures a fixed-cap book and stops at cap 60; the hold is
   135 bars. Cap 60 (+54.45 ± 5.26) is a **nearest-only** stand-in, not a pass.
3. **H1 and H4 are unspent.** No best-of-8 floor beneath cells spanning 1.66×–3.72×, no null, and
   no Sharpe, volatility or maximum drawdown computed.

### Branch B — drawn, not yet measured

`scripts/d399_draw_construction.py` and the published chart page. Over 260 bars:

| | re-anchors lo/hi | **pushes lo/hi** |
|---|--:|--:|
| MSFT | **1** / 0 | 19 / 0 |
| WYNN | 3 / 2 | **38** / 1 |
| GME | 2 / 3 | 4 / **36** |
| INTC | 3 / 3 | 35 / 30 |
| F | 3 / 2 | 23 / 15 |
| DVN | 3 / 2 | 21 / 10 |

**Branch B has a quantity Branch A does not: the push asymmetry.** WYNN is pushed 38 times on
support and once on resistance; GME is the mirror. **Which line price keeps breaking is a signal
Branch A cannot express**, because Branch A's line is not a level price breaks — it is a level
price is dragged to.

---

## 3. Where they would diverge as strategies

| | Branch A | Branch B |
|---|---|---|
| what the line is | the lower envelope of recent fits | a fixed-slope barrier price must respect |
| a "touch" | common, ~265k events | rare by construction, and it MOVES the line |
| the natural signal | price at a well-supported level → **retracement entry** | **how often the line is broken** → trend health |
| the natural exit | the state ending | the line being broken badly, or the gradient re-anchoring |
| measured? | **yes**, and it clears cost on the long side | **no** — drawn only |

**They are not variants of one idea to be swept. They are two hypotheses**, and R13 counts them
separately.

---

## 4. What is owed on each, if the principal returns to them

**Branch A** — the four things §2 lists as unspent, in order: the **best-of-8 floor** (H1); a
**matched-hold null** (A′ or B_s), since the atlas cannot floor a variable-hold book; **Sharpe,
vol and maxDD**; and only then a verdict. **Its short leg is closed by Q6 regardless** — dead names
earn +682.8 bp/trade against survivors' −213.4, so the short side is the delisting trade and cannot
go to a survivor-only 15-minute fixture.

**Branch B** — a Stage 0 of its own, pre-registered, with the signal declared *before* the runner.
The push asymmetry is the obvious candidate and it has never been tested. **It must not inherit
Branch A's hurdles or its event definition.**

---

## 5. The honest note on provenance

**Branch A exists because I misread a specification, and its number is the best in the record.**
That is exactly the situation `docs/BOOK.md` warns about — D240's A2 at the 99.6th percentile,
D251's five cleared spreads, D235's seven cells — *"a result in the complement of what was
registered."* **It is disclosed here rather than quietly promoted**, and if it is ever taken
further, the pre-registration must say that it was found this way.

**Neither branch is retired and neither is admitted. Only the principal closes an avenue (R15).**
