# D408 RESULT — the magnitude replicates at 1.07×, the shape does not, and my prediction was wrong

**FAILS THE BAR. R1 MET.** Pre-registration `4fa495c` predates the runner and this file (R8).
**The ledger does not move. Nothing was admitted. No holdout was read.**

Cost: 23 seconds, on data pulled for `044f839`.

---

## 1. The primary cell

`w = 2.0` — **declared primary in advance** — on the `oos` set: 36 snapshots, 5,992 rows, 204
names, **0 dates shared with `d406`** (asserted by `[DISJOINT]`).

```
                   Q1      Q2      Q3      Q4      Q5     spread
oos  (this)     0.8424  0.8032  0.8099  0.7788  0.7613   -0.0811
d406 (spent)    0.8036  0.7621  0.7447  0.7232  0.7277   -0.0759
```

| | condition | outcome |
|---|---|---|
| **T1** | monotone DECREASING | **FAIL** — Q2→Q3 rises. Three of four steps hold, as in `d406`, **but a different step breaks** |
| **T2** | Q1 − Q5 ≥ 10% of pooled | **PASS** — +0.0811 against 0.0799 |
| **T3** | survives within vol terciles | **FAIL** — and see §3 |
| **R1** | spread ≤ −0.0569 (0.75× `d406`) | **MET** — −0.0811, a **1.07× replication** |

**D408 FAILS.** Per §4a of the pre-registration, R1 being met *"justifies writing a full
pre-registration — nothing more."*

---

## 2. MY PREDICTION WAS WRONG, AND IT WAS THE ONE I SAID MATTERED

| | prediction | outcome |
|---|---|---|
| X-a | T1 fails again | correct |
| X-b | the spread is negative | correct |
| **X-c** | **R1 fails — the magnitude shrinks**, because `w = 2.0` was the largest of three windows and *"the largest of several is a max-order statistic"* | **WRONG.** It replicated at **1.07×** and grew slightly |
| X-d | T3 fails | correct |

Three of four right, and the miss is the one the record singled out: *"If the magnitude
replicates at three-quarters of its size on unseen dates, that is a real finding about a real
effect."* It replicated at **107%**, on 36 snapshots never looked at.

**That is the strongest evidence this line has produced.** The max-order-statistic explanation for
`w = 2.0` is now ruled out — a best-of-three artefact does not hold its size on disjoint dates.

---

## 3. And the strongest evidence AGAINST is also new

`d406` had **six of six negative spreads**, every window and every volatility tercile. That
uniformity is gone:

```
             Q1      Q2      Q3      Q4      Q5     spread
vol lo    0.9692  0.9808  0.9914  0.8750  1.0186   +0.0493   <- WRONG SIGN
vol mid   0.7758  0.6802  0.7374  0.7096  0.7313   -0.0445
vol hi    0.6771  0.5867  0.6320  0.6005  0.5813   -0.0957
```

**The low-volatility tercile flips sign** — `d406` had it at −0.0370. So the pooled effect is
carried by the mid and high terciles and *reverses* in the low one. A real conditioner should not
do that, and D263's rule about a spread arriving with the wrong sign applies to a sub-population
as much as to a headline.

**Read together:** the *magnitude* is robust across slices, the *shape* is not robust within them.

---

## 4. Reported and refused

**Signed return** — `+0.0146 +0.0085 +0.0005 +0.0008 +0.0005`, spread **−0.0141/quarter**,
roughly **−5.6%/yr**, up from `d406`'s −0.0095. **Cannot clear:** no direction was declared in
advance, and it is not monotone. D263 refused its own −7.32%/yr on the same rule.

**`w = 0.5` is degenerate and is not evidence.** Its Q1 holds 237 rows against ~1,200 elsewhere,
because at half a sigma many names carry *zero* open interest in the window and the tied zeros
collapse the bottom quintile. The same artefact sat in `d406` (Q1 = 469). It is shape, it cannot
clear, and it should not be read at all.

**`[ALIGN]`** held: 5,998 delta-implied spots, median ratio **1.0180**, matching `d406`'s 1.0190.

---

## 5. Where this leaves the open-interest line

**Not clear, and no longer dismissible.**

- The effect's **size replicates out of sample** at 1.07×, which kills the selection explanation.
- Its **shape fails** in the same way twice — three of four monotone steps, a different step each
  time — which is what a weak-but-real effect *and* noise both look like.
- Its **sign is not stable within volatility strata**, which is the finding that most needs
  explaining before anything is built.

Per the pre-registration, R1 met **justifies a full pre-registration and nothing else.** That
would have to be a directional design with the sign declared in advance, powered enough to
resolve monotonicity, and it would have to confront §3 rather than pool past it.

**The `expiry` set (D409) is untouched and is the other half of this question** — pinning is
classically claimed at expiry, which is exactly where neither `d406` nor `oos` sampled.

---

## 6. R13

Ninth look. Marginal cost 23 seconds on already-pulled data. The `d406` set was not reused; the
`oos` set is now **spent** and cannot serve as confirmation for anything else.

**Evidence:** `data/d408_w2_confirmation.json`. Runner `scripts/run_d408_w2_confirmation.py`,
which imports D406's construction rather than restating it, so the two are provably the same
object measured on different dates.
