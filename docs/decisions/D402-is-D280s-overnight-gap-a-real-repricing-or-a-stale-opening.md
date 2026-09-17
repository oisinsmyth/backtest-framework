# D402 PRE-REGISTRATION — is D280's overnight gap a real repricing, or a stale opening print?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D402-is-D280s-overnight-gap-a-real-repricing-or-a-stale-opening-print.md`. The H1 above is the full title.*

**Number.** Pre-registered as `D390` and **renumbered to `D402` on 2026-09-09**. `D390-D399` is reserved for the `worktree-signal-hunt-part2` branch (`fb2af62`), which master had already stepped out of once — the D163 re-cost went D389 -> D390 -> D400. I took D390 anyway, having checked `ls docs/decisions/`, which PICKUP's own warning says is insufficient and will collide. **Master takes D400 and upward.** The commit hashes below are historical and unchanged: pre-registration `6843a39`, result `c6c63f6`.

**R8: committed before the runner exists. Result separately.** A **measurement record**, like D280
itself: it scores no cell, ranks no name, proposes no rule, admits nothing, reads no holdout, and
touches no multiplicity ledger (R13).

---

## 1. Why this exists

**D280's gap IC is the largest committed measurement in the D264 → D280 sequence** and PICKUP §1a
headlines it:

```
ALL   gap        -0.01531   t -4.71     <-- the edge
ALL   intraday   +0.00168   t +0.65     <-- nothing
QUAL  gap        -0.01255   t -3.45
QUAL  intraday   +0.00868   t +2.85     <-- runs AGAINST the short
```

with `gap(t+1) = open(t+1)/close(t) − 1`.

**D280 tested the obvious confound exhaustively and it survived** — dividend-adjusted −0.01498,
ex-dates excluded −0.01494, and the effect localises on the 0.834% of bars that go ex (−0.05197).

**It never tested whether the OPENING PRINT IS REAL.** The gap is formed entirely from the vendor's
`open`, on the **ALL** universe, which includes thin and low-priced names — and price alone killed
D284. A carried-forward, single-print or otherwise stale open manufactures a gap that never traded.

**The prompt is the prop-firm research folder's own prerequisite** (`docs/research/Prop-Firm-080926/`,
row C19-2): *"run the stale-price / closing-auction contamination test first."* That session required
it of its candidate; it has never been required of ours.

**What is NOT in doubt and is not re-litigated:** D280's own runner already records that the IC does
not survive into money at N=25 — *"the ascending short LOSES 11–18 bp per night overnight"*, and *"a
rank IC describes the WHOLE cross-section; a top-N book lives in ONE TAIL."* **This record tests the
STRUCTURAL claim only** — that the move happens overnight rather than intraday — because that claim
is what closes the exit-overlay branch and what PICKUP headlines.

---

## 2. The contamination signatures, declared in advance

All computable from daily OHLCV, all applied to bar `t+1` (the bar whose `open` forms the gap):

| tag | signature | why it means the open may not be a real trade |
|---|---|---|
| **S1** | `open(t+1) == close(t)` **exactly** | a carried-forward print; no opening trade occurred |
| **S2** | `open == high == low == close` on `t+1` | a single-print bar |
| **S3** | `open(t+1) == high(t+1)` or `== low(t+1)` exactly | the open is the session extreme — consistent with one early print and the range forming after |
| **S4** | volume on `t+1` is zero or missing | nothing traded |
| **S5** | `close(t)` below the 20th percentile of that bar's cross-sectional price | tick granularity is a larger share of the gap |
| **S6** | dollar volume on `t` below the 20th cross-sectional percentile | thin name |

**CLEAN = none of S1–S4, and neither S5 nor S6.** S1–S4 are exact data signatures; S5–S6 are
liquidity cuts and are reported **separately as well as jointly**, because excluding them is a
universe change and not only a cleanliness change.

---

## 3. What is measured

**The gap IC is recomputed by D280's own `ic_series` on its own fixture, signal and split** — the
lagged `hist_L`, out of sample from 2018-01-01, universes ALL and QUAL.

1. **P1 — does the edge survive on CLEAN bars?** Gap IC on CLEAN against the committed −0.01531,
   with the bar count retained.
2. **P2 — does it CONCENTRATE in contaminated bars?** Gap IC computed *within* each signature.
3. **P3 — THE DISCRIMINATING TEST: which way does it move with liquidity?** Gap IC by dollar-volume
   quintile and by price quintile. **A real overnight repricing should be at least as strong in
   liquid names with genuine opening auctions; a print artefact should concentrate in the thin and
   cheap tail.** These two hypotheses predict opposite gradients, so this cell decides the record
   even if P1 is ambiguous.
4. **P4 — does the gap REVERSE?** `corr(gap, intraday)` on the same bars, contaminated against clean.
   A stale open is corrected by the first real trade, so an artefact should show materially more
   negative reversal on contaminated bars. D280 already reports pooled `corr(gap, body) = −0.0429`
   and a QUAL intraday IC of +0.00868 that "runs AGAINST the short" — **so some reversal is already
   on the record and this asks whether contamination explains it.**

**Reported beside each:** the share of bars each signature flags, because a signature flagging 0.1%
of bars cannot explain a t of −4.71 however strong its own IC.

---

## 4. Decision rules

**V1 — SURVIVES.** CLEAN gap IC is within 25% of the committed value and retains its sign and
significance → **the opening print is not the explanation; D280's structural claim stands** and this
record closes the question.

**V2 — CONTAMINATED.** CLEAN gap IC loses more than half its magnitude, or its significance →
**a material part of the headline is price formation, not repricing.** D280 would need an amendment,
and PICKUP §1a with it.

**V3 — LIQUIDITY-INVERTED.** P3 shows the IC concentrated in the thin/cheap tail and absent in the
liquid tail → **the same conclusion as V2 and by a stronger route**, because it does not depend on
any exact-equality signature firing.

**V1 and V3 can both be true**, and if they are, V3 wins: an edge that lives only where you cannot
trade is not an edge, whatever the exact-print tests say.

---

## 5. Assertions

| tag | what it proves |
|---|---|
| **`[REP]`** | the runner reproduces **D280's committed gap IC to 3 decimal places** — ALL −0.01531 and QUAL −0.01255 — **before any filter is applied.** If it cannot, it is not measuring D280's object and nothing below is about D280 |
| **`[LAG]`** | the signal is the **lagged** `hist_L` D280 used, re-derived independently, and a deliberately unlagged variant must give a different IC |
| **`[MASK]`** | every cell reports its bar count; no IC is quoted on fewer than 1,000 bars |
| **`[SIG]`** | each contamination signature's flagged share is reported, and **S1–S4 are asserted to be exact-equality tests** on raw OHLC, not tolerance comparisons |
| **`[SPLIT]`** | out-of-sample from 2018-01-01, D280's own split; the default-deny holdout hook is installed and never unlocked |
| **`[X]`** | every audit raises on a break that moves the exact scalar it compares |

---

## 6. Predictions

| | |
|---|---|
| **Q1** | **the exact-print signatures S1–S4 flag under 2% of bars** and cannot by themselves explain a t of −4.71 |
| **Q2** | **P1 survives** — the CLEAN gap IC stays within 25% |
| **Q3** | **AGAINST myself, and this is the one I expect to hurt: P3 inverts.** The IC concentrates in the cheap and thin quintiles. D284 was killed by exactly this and the gap is measured on the **ALL** universe |
| **Q4** | **contaminated bars show materially more gap→intraday reversal** than clean ones |
| **Q5** | **QUAL is cleaner than ALL** — it is the set D279 actually ranked inside — so the gap between the two universes narrows on CLEAN bars |
| **Q6** | **AGAINST myself: at least one assertion fires on the first run.** Held in D388 and D389, both times by predicting failure |

---

## 7. What would make me abandon this

- **`[REP]` fails** → the runner is not reproducing D280's measurement. Stop; publish nothing, and
  fix the reproduction before any filter is read.
- **Every signature flags under 0.2% of bars AND the liquidity gradient is flat** → there is nothing
  to find; report V1 and close the question rather than sweeping for a cut that fires.

---

*Pre-registered 2026-09-09. Runner does not exist at the time of this commit (R8). Measurement only:
no cell scored, nothing admitted, no holdout read, no new data fetched.*
