# D513 RESULT — CLOSE: the conditioner does not transfer. The compressed-range effect was a property of NQ's history, and the arm loses on all six unspent roots

**Result of D513** (spec `ed2e691`). Runner `scripts/run_d513_conditioner_unspent_roots.py --run`
(`--selftest` passes, six checks; 0.3 min), artefact `data/d513_conditioner_unspent_roots.json`.
**2016-01-04 → 2023-12-29 on YM, ZN, ZB, GC, CL and 6E. THE 2024+ SLICE OF ALL SIX WAS NOT READ**
and remains unread for every line.

## 0. The answer

**D512's range-expansion effect was a property of NQ's history.** On six roots it separates nothing,
and its direction is a coin flip.

| root | sessions | arm's unconditional net Sharpe | arm's $/trade | Δ/σ | Δ, $/session | top | bottom | N1 p95 | percentile |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **YM (primary)** | 1,871 | **−0.686** | −3.90 | **+0.036** | +3.38 | −1.02 | −4.40 | +0.095 | 68.2nd |
| ZN | 1,876 | −0.929 | −12.83 | −0.077 | −17.11 | −25.51 | −8.40 | +0.106 | 11.5th |
| ZB | 1,875 | −0.880 | −28.98 | −0.091 | −48.19 | −70.01 | −21.82 | +0.110 | 9.8th |
| GC | 1,844 | −0.456 | −2.16 | +0.062 | +4.71 | −1.84 | −6.55 | +0.107 | 81.0th |
| CL | 1,626 | −0.968 | −5.53 | −0.088 | −8.47 | −11.18 | −2.70 | +0.123 | 11.0th |
| 6E | 1,885 | −1.294 | −5.35 | +0.068 | +4.56 | −5.21 | −9.77 | +0.153 | 79.4th |

**Nothing clears.** The primary sits at the **68.2nd percentile** of its own exact rotation. The
six-root family bar is p50 +0.082, **p95 +0.173**, against an observed maximum of **+0.068** — **65.8%
of offsets beat the best real cell.** Δ is positive on **three of six** roots.

**Verdict: CLOSE**, on three of four terms.

## 1. The arm does not merely fail to transplant. It loses on every one of these roots

Net Sharpe runs **−0.456 to −1.294** and the mean trade **−$2.16 to −$28.98**. The other session's
D506 established that the arm clears its own null on one root of thirty-five; this adds that on the
six roots with an unread slice it is **decisively negative**, not flat.

**That is the honest limitation of this design, and it must be stated.** The claim under test was
"a compressed range is where a trend construction bleeds". Testing it on a construction that bleeds
*everywhere* is a weak test of the conditioner: a conditioner might still separate a construction
that has an edge. **What this record can say is that the conditioner does not rescue, order or even
consistently sign a losing transplant — not that it would fail on a live one elsewhere.**

**What it can say sharply** is that the effect is not a general property of the MACD machinery. On
the three roots where Δ is negative, the *expanded*-range sessions lose more: ZN's top quintile is
−$25.51 against −$8.40 at the bottom, ZB's is −$70.01 against −$21.82, CL's −$11.18 against −$2.70.
On YM, GC and 6E the ordering reverses. **Six roots, three each way.**

## 2. Within year there is no coherence either

| root | same sign as pooled | within-year mean |
|---|---:|---:|
| YM | **4 of 8** | +0.082 |
| ZN | 5 of 8 | −0.075 |
| ZB | 5 of 8 | −0.046 |
| GC | 4 of 8 | −0.003 |
| CL | 5 of 8 | −0.091 |
| 6E | 3 of 8 | −0.010 |

The primary keeps its sign in exactly half its years. D512's striking within-year coherence on NQ —
positive in six of eight, a within-year mean that exceeded the pooled figure — does not appear
anywhere here.

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | the arm flat or negative on ≥ 4 of 6, Sharpe in [−0.3, +0.3] | **0 of 6** in that band; all six from −0.46 to −1.29 | **wrong** — far worse than flat |
| X-b | primary Δ/σ in [+0.05, +0.30], not clearing an N1 p95 in [+0.30, +0.55] | Δ/σ **+0.036**, p95 **+0.095**, does not clear | the conclusion right, **both levels wrong** and far smaller |
| X-c | family p95 1.2× to 1.6× the single-cell p95 | **1.82×** | wrong |
| X-d | Δ positive on ≥ 4 of 6 | **3 of 6** | wrong |
| X-e | within-year mean keeps the pooled sign on ≥ 4 roots | **3 of 6** | wrong |
| X-f | the verdict is PICK or CLOSE, not PROCEED | CLOSE | right |

**One of six.** I predicted the shape of a weak positive result and got a null with the arm far more
negative than expected. The pre-registration was written before the run and the misses are recorded
as they fell.

## 4. What stands

- **CLOSE recommended for the range-expansion conditioner as a general instrument**; the principal
  closes. It does not transfer to six roots, its direction is three-for-three, and nothing clears a
  single-cell or family bar.
- **D512's result is now attributable**: it was NQ's history, not a property of trend constructions.
  That is the question this record was built to answer, and it answered it.
- **A limitation to carry**: the transplanted arm loses on all six roots, so this is a test of the
  conditioner on a losing construction. It cannot rule out that a range conditioner works on a live
  construction on another instrument. Anyone reviving it needs a construction with an edge to
  condition.
- **Nothing was spent.** The 2024+ slice of YM, ZN, ZB, GC, CL and 6E was not read, under a verdict
  that never called for it. That is the point of having declared the cell here rather than on NQ.
- **The three-record conditioner line on the admitted arm is closed** (BOOK_PROP, 2026-09-13), and
  this closes its one forward pointer.

## 5. Files

Runner · this record · the artefact · D512 (the NQ version) · BOOK_PROP's closure section · PICKUP.
