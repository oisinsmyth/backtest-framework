# D513 RESULT — CLOSE: the conditioner does not transfer. The compressed-range effect was a property of NQ's history, and the arm loses on all six unspent roots

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D513-RESULT-CLOSE-the-conditioner-does-not-transfer-it-was-a-property-of-NQs-history-and-the-arm-loses-on-all-six-unspent-roots.md`. The H1 above is the full title.*

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

---

## ADDENDUM, 2026-09-13 — this record reported NET only, which hid the answer. GROSS is positive on three of the six

**A correction to my own reporting.** CLAUDE.md's first reporting rule is *performance, NET AND GROSS
side by side*, because *"gross separates cost failure from signal failure: opposite fixes."* §0 and §1
of this record quote net figures throughout and never quote gross. The runner computed gross, asserted
`net == gross − cost × trips`, and then discarded it. Diagnostic:
`working/d513_why_only_nq_scratch.py`, same window, nothing new read.

| root | GROSS $/trade | gross Sharpe | cost $/RT | cost in ticks | NET $/trade | net Sharpe | E\|move\|/trade | cost ÷ move | gross ÷ cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **NQ** (reference) | **+12.46** | **+1.130** | 3.50 | 7.00 | **+8.96** | **+0.811** | 108.91 | **3.2%** | **3.56** |
| YM | −0.40 | −0.070 | 3.50 | 7.00 | −3.90 | −0.686 | 55.47 | 6.3% | −0.11 |
| ZN | **+5.79** | **+0.422** | **18.62** | 1.19 | −12.83 | −0.929 | 142.80 | **13.0%** | 0.31 |
| ZB | **+5.27** | **+0.161** | **34.25** | 1.10 | −28.98 | −0.880 | 351.70 | 9.7% | 0.15 |
| GC | **+1.84** | **+0.390** | 4.00 | 4.00 | −2.16 | −0.456 | 47.90 | 8.4% | 0.46 |
| CL | −1.53 | −0.270 | 4.00 | 4.00 | −5.53 | −0.968 | 60.46 | 6.6% | −0.38 |
| 6E | −1.10 | −0.268 | 4.25 | 3.40 | −5.35 | −1.294 | 45.05 | 9.4% | −0.26 |

**Gross is positive on four of seven roots and net on one.** §1's sentence *"the arm does not merely
fail to transplant, it loses on every one of these roots"* is true of **net** and **wrong as a
statement about the signal**. The correct reading is that the six roots split into two groups with
**opposite diagnoses**:

- **Cost-dead, not signal-dead: ZN, ZB, GC.** Gross Sharpe +0.42, +0.16, +0.39 and gross of +$5.79,
  +$5.27, +$1.84 a trade. The signal is present and small. It dies on the **tick**: ZN's tick is
  $15.62 and ZB's $31.25, so a single crossing costs $18.62 and $34.25 against those edges. ZN would
  need **3.2×** its gross to break even, ZB **6.5×**, GC **2.2×**. Commission is trivial on the
  large-tick roots (ZN's $3 is 0.19 of a tick); **the spread is the whole cost**, which is the
  mirror image of `commission-not-spread-binds-at-micro-size`.
- **Signal-dead: YM, CL, 6E.** Gross is **negative** — −$0.40, −$1.53, −$1.10 — so there is nothing
  for a cheaper venue to rescue. Notably **YM is an equity index and pays the same $3.50 as NQ**, so
  this is not a commodity-versus-index split and not a cost split.

**What this strengthens.** §4's stated limitation — that D513 conditions a construction that bleeds
everywhere — is now sharper and partly **wrong in the helpful direction**: on ZN, ZB and GC the
construction is not signal-dead, it is cost-dead, so the conditioner was being asked to sort a
**real if small** gross edge on three of six roots and still sorted nothing. That is a somewhat
stronger null for the conditioner than the record claimed, not a weaker one.

**What does not change.** The verdict, the nulls, and every conditioner figure: Δ/σ is computed on
**net** P&L by design, which is the quantity an account experiences, and none of it is restated.

**And the structural fact the table makes plain:** **NQ pays 3.2% of its per-trade move in cost and
the next cheapest root pays 6.3%.** That ratio, not the signal, is what the arm's transplant runs
into first on ZN, ZB and GC.
