# D408 PRE-REGISTRATION — D406's `w = 2.0` cell, made primary, on dates never looked at

**R8: committed before the runner exists. Result separately.**

**Number.** `D408`, from the block `D407–D410` reserved on master in `044f839`.

---

## 1. Why this exists

[D406](D406-RESULT-open-interest-density-fails-its-bar.md) failed its bar and closed. But it
recorded one cell as **available and declined**:

```
w = 2.0    0.8036  0.7621  0.7447  0.7232  0.7277     spread -0.0759
           T2 bar 0.0752  ->  CLEARS
           monotone on THREE OF FOUR steps, failing only Q4->Q5, by 0.0045
```

`w = 1.0` was the committed primary and `w = 2.0` was declared as *shape*. Promoting it on
D406's own data would be the post-hoc selection D197–D203 made five times — each refinement
beating its predecessor, none moving the null gap.

**Promoting it on data that has never been looked at, with the promotion declared in advance, is
a different act.** That is this study, and it is the only legitimate way to cash a declined cell.

---

## 2. The slice — disjoint, and never examined

| set | dates | status |
|---|---|---|
| `d406` | 15 Feb / May / Aug / Nov, 2015–2023 | **SPENT.** Not reused here. |
| **`oos`** | **15 Jan / Apr / Jul / Oct, 2015–2023** | **36 snapshots, 7,558 chains. This study.** |
| `expiry` | Monday of expiry week | D409's, not this one |

Same 210 names, same cadence, same years, **disjoint dates**. Pulled by
`scripts/pull_av_options_snapshots.py --set oos` (`044f839`), which computes no statistic and
states no bar.

**`d406` is not pooled with `oos`.** Pooling after seeing `oos` would be post-hoc, and pooling
before makes the confirmation meaningless. A pooled table may be reported **descriptively and
cannot clear.**

---

## 3. WHAT IS DECLARED PRIMARY, IN ADVANCE

**`w = 2.0`**, outcome `|forward move| / sigma`, horizon `h = 63`. Everything else is D406's
construction unchanged and is not re-derived here: density is the share of a name's total open
interest within `w` daily sigmas of spot, calls and puts **summed and never netted**, names below
10 strikes at OI ≥ 100 excluded per snapshot, snapshots below 50 names dropped, levels on
`RAW_CLOSE` with `[ALIGN]` against the delta-0.5 strike.

`w = 1.0` and `w = 0.5` are reported as shape. **They cannot clear** — the whole point of this
study is that the primary was named first.

---

## 4. THE BAR — D406's, unchanged

| | condition |
|---|---|
| **T1** | mean \|forward move\| / sigma **monotone DECREASING** across Q1→Q5 |
| **T2** | Q1 − Q5 ≥ **10% of the pooled mean** |
| **T3** | T1 **survives within volatility terciles** |

**The bar is not relaxed for the confirmation.** D406 set it, D406's `w = 2.0` cell failed T1 on
one step of four, and applying a laxer standard here would be the loosening this study exists to
avoid.

### 4a. And a SEPARATE, pre-declared replication statistic

Because the bar above is strict and the honest prior is that T1 fails again on a technicality,
one further question is declared **now**, with its own threshold, and reported beside it:

> **R1 — the `w = 2.0` spread on `oos` is negative and at least `0.75x` its `d406` value**, i.e.
> **≤ −0.0569** against the observed `−0.0759`.

**R1 clearing does not admit anything and does not clear D408.** It would justify writing a full
pre-registration — nothing more. That is D263's ladder logic: a cheap rung earns the right to pay
for an expensive one, and never substitutes for it.

**R1 failing, with T1–T3 also failing, is the end of the open-interest line.**

---

## 5. Predictions, so they cannot be re-read afterwards

| | prediction | confidence |
|---|---|---|
| **X-a** | T1 fails again — full monotonicity across five quintiles is a strict shape and D406 missed it by one step | **high** |
| **X-b** | The spread is **negative** — D406 had six of six negative spreads across every window and every volatility tercile, which is the one thing that separated it from D263 | **moderate-high** |
| **X-c** | **R1 fails**: the magnitude shrinks. `w = 2.0` was the largest of three windows on the spent slice, and the largest of several is a max-order statistic | **moderate** |
| **X-d** | T3 fails — no volatility tercile was monotone in D406 | **high** |

**X-c is the one that matters.** If the magnitude replicates at three-quarters of its size on
unseen dates, that is a real finding about a real effect. If it shrinks toward zero, D406's
`w = 2.0` was the biggest of three draws and nothing more.

---

## 6. What this does not do

- No position, no book consequence, no admission. **The ledger does not move.**
- **No holdout read.** Nothing here touches a holdout fixture.
- **No signed or gamma-weighted aggregation**, excluded by D406 §4 as inference.
- **Does not reuse `d406`'s dates** for anything that can clear.
- **Does not touch the `expiry` set**, which is D409's.

---

## 7. R13

Ninth look by object on price levels. Its marginal cost is **one screen on data already pulled**,
which is why it is worth running rather than assuming the answer.
