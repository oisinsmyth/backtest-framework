# DRAFT — proposed amendment to `docs/FINDINGS.md` §48

**STATUS: NOT APPLIED. This is a proposal awaiting the principal's decision.**
`docs/FINDINGS.md` is untouched by the session that wrote this.

**Why it is a draft and not a commit.** Two reasons, both procedural:

1. **FINDINGS is written from records that carry decision numbers.** The evidence behind this
   amendment lives in `docs/research/the-signal-hunt-part2.md` §7f–§7g, which is a research record
   under [R15](../docs/RULES.md#r15) and explicitly carries none. Promoting it needs either a
   D-number of its own or the principal's say-so.
2. **A concurrent session was live on `master`** while this was written (it committed D373's
   runner, the segmentation diagnostic and holdout #2). FINDINGS.md is the one file that must not
   be mangled by two writers.

**Where it goes.** Appended to §48 as a dated amendment, in the style of R14's amendments — §48 is
D368's section on null precision, and this does not contradict it. §48's point 1 is about the
null's **variance**; this is about its **bias**, which is a separate and additive defect.

**Evidence.** `scripts/c2_calm_vs_gate.py` → `data/c2_calm_vs_gate.json`;
`scripts/c2b_rotation_audit.py` → `data/c2b_rotation_audit.json`. Both carry `[ID]` reproducing
D361's published per-cell values to 1e-9 before any null is read, and `[E]` asserting the scored
offsets are exactly {1 … Td−1} as a set.

---

## The proposed text

### AMENDMENT to §48, 2026-09-08 — the p95 is not only noisy, it is BIASED, and for one null family the bias can be removed exactly

**From C2/C2b (`docs/research/the-signal-hunt-part2.md` §7f–§7g), on all four of D361's cells.**
§48 established that a 200-draw rotation p95 carries enough **run-to-run spread** to swallow the
margins three studies decided on. It did not ask whether that spread is **centred**. It is not.

D361's rotation null is a circular shift of a market-level gate, which has exactly **Td − 1
admissible offsets — a finite group of about 4,000.** Scoring every one of them gives the p95 with
**no sampling error at all**, so the published 200-draw value can be compared against the truth
rather than against another sample.

| cell | observed | p50 pub | p50 exact | Δ | p95 pub | **p95 exact** | **Δ** | margin | verdict |
|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| G1:T1 | −4.48 | +9.41 | +8.05 | −1.36 | +56.54 | +56.82 | **+0.27** | −61.29 | inside |
| G1:T2 | +15.57 | +14.26 | +14.06 | −0.19 | +35.04 | +36.08 | **+1.04** | −20.51 | inside |
| G2:T1 | +4.18 | +6.51 | +6.69 | +0.18 | +61.60 | +68.51 | **+6.91** | −64.33 | inside |
| G2:T2 | +42.33 | +14.66 | +14.78 | +0.12 | +35.95 | +41.81 | **+5.86** | **+0.52** | **ABOVE** |

**NO VERDICT CHANGED. All four of D361's rotation verdicts stand** — three fail by 20 to 64 bp,
margins no exact p95 could close, and G2:T2 clears. The audit prices D361's one surviving cell; it
does not overturn it.

**But the exact p95 was HIGHER in 4 of 4 cells, mean +3.52**, against a p50 delta of −0.31 with
mean |Δ| 0.46. **The centre is estimated well at 200 draws and the tail is estimated badly, in a
direction** — and that has a mechanism rather than being a count:

> **A sample extreme quantile is biased TOWARD THE CENTRE of its own distribution.** The p95 of n
> draws is about the ⌈0.95n⌉-th order statistic; on a right-skewed null — and all four of these are,
> p50 +7 to +15 against a max of +70 to +105 — it sits **below** the true 95th percentile.
> **Every finite-draw null threshold is therefore easier to beat than it appears, and every such
> test is more lenient than its nominal level.** It reverses sign where the low tail is the bar:
> against a p05 the sample threshold is too high, and leniently again.

On its own 4-of-4 is p ≈ 0.06 one-sided and would not carry the claim; **it is the mechanism that
carries it, and the count that corroborates.**

**THE MAGNITUDE DOES NOT GENERALISE, in any units.** "0 to 7 bp per trade" belongs to this
statistic, this null family, this trigger's skew and n = 200. As a share of each null's own
(p95 − p50) the four biases are **0.6%, 4.7%, 11% and 22%** — four cells pin the direction and not
the size. Any study quoting a number from this table outside this null family is quoting a
coincidence.

**THE EXACT FIX IS ONE FAMILY.** Enumeration needs a group that is finite *and* small:

| null | group | enumerable |
|---|---|---|
| time rotation of a **single market-level series** | Td − 1 ≈ 4,000 | **yes**, ~6 min a cell |
| A′ — per-name event rotation | product over names | no |
| rank / score rotation | vast | no |
| B, B_c — same-day replacement | vast | no |
| C — random direction | 2^trades | no |
| DROP, FROT | combinatorial | no |

**The warning is broad; the cure is one corner** — the corner D361 and D362 decided their gate
verdicts in.

**What it means, as additions to §48's four points.**

5. **Where the null's group is finite and small, ENUMERATE it.** Not more draws — all of them.
   `Td − 1` offsets is 330 to 520 seconds a cell on this fixture and the reported SE is then
   exactly 0, so the verdict cannot move again. D369 asked for more draws generally; the draw
   count only needs to grow **when the margin is small relative to the null's spread**, and where
   the group is finite that question can be closed instead of estimated.
6. **Elsewhere the bias stands and must be carried, not assumed away.** Cheapest first:
   (i) report the p95's **bootstrap SE** and record a margin within **2 SE** as UNRESOLVED —
   [D373](../docs/decisions/D373-the-winners-dip-long-and-the-median-criterion.md) pre-registered
   exactly this, so the precedent exists and is simply not universal; (ii) a **bias-reduced
   quantile estimator** (Harrell–Davis, or interpolated order statistics), which attacks the bias
   at the *same* draw count and is therefore strictly cheaper than more draws — **UNMEASURED here,
   and it should be measured before it is recommended**; (iii) more draws.
7. **A "clears p95" on a thin margin is now known to be the fragile case in both directions** —
   §48 showed its noise, this shows its bias, and both push the same way. G2:T2 was the only one of
   D361's four cells whose published margin (+6.4) sat inside the band, and it is exactly the one
   whose margin collapsed, to **+0.52**. It survived. It was the only one that could have failed to.

---

## What the principal is being asked to decide

1. **Does this become an amendment to §48, or its own numbered section?** It is offered as an
   amendment because §48 owns the same instrument, and because a section implies a study the
   research record did not run.
2. **Does it need a D-number first?** The measurement is descriptive, reproduces published values
   to 1e-9 and scores no construction — but it does change how future nulls are read, which is
   rule-shaped rather than finding-shaped.
3. **Is the `CLAUDE.md` clause already added in this worktree the right scope?** It carries the
   bias warning, the 2-SE UNRESOLVED rule and the enumeration prescription, and names what is *not*
   enumerable so the cure is not over-applied.
4. **Is the Harrell–Davis option worth a measurement?** It is the only cheap route to the bias on
   the six non-enumerable null families, and nothing here has tested it.
