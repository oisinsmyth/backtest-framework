# D442 ADDENDUM — the two apparent wins were SELECTION ACROSS FOUR RISK FRACTIONS, and the premium the null was denied is larger than the effect

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D442-ADDENDUM-the-two-apparent-wins-were-selection-across-four-risk-fractions.md`. The H1 above is the full title.*

**Addendum to [`D442-RESULT`](D442-RESULT-O1-clears-the-ledgers-own-criterion-and-dies-inside-the.md).**
Nothing new is decided: same gate, same `θ`, same seed, same paths, same days, same `G2` test.
**Runners:** `scripts/d442_rot_extra.py`, `scripts/d442_rot_bestofn.py`. **Evidence:**
`data/d442_rot_extra.json`, `data/d442_rot_bestofn.json`.

**Two predictions were written before their runs and BOTH were wrong, in opposite directions.**

---

## THE ANSWER

> **`O1` fails `G2` on all four symbols. D442's verdict stands unqualified.**
>
> **And it took two steps to get there, because the first null was the wrong null.**

## 1. Step one — the enumeration D442 deferred, and it falsified D442's own expectation

D442 §8 left QQQ-static and DIA-static uncontrolled and said *"on SPY an increment that size sits
comfortably inside the null."* **Enumerated on their own symbols, both cleared it:**

| cell | BASE @ same frac | `O1` | ROT p50 | **ROT p95** | BLKRAND p95 | |
|---|---:|---:|---:|---:|---:|---|
| **QQQ static @ 0.4%** | −145 | **262** | −111 | **213** | 169 | **above** |
| **DIA static @ 0.4%** | −169 | **250** | −143 | **171** | 94 | **above** |
| QQQ voltgt @ 1.1% | 29 | 33 | 39 | 270 | 273 | inside |
| DIA voltgt @ 1.1% | 64 | 125 | 83 | 392 | 342 | inside |

**Both controls agreed, and my written prediction — that all four would sit inside — was wrong on
two.** 3,265 and 3,187 offsets, fully enumerated.

## 2. Step two — and the first null was giving the treatment a free advantage

**The defect is mine and it is [FINDINGS §59](../FINDINGS.md) in miniature.** The treatment's 0.4%
was chosen as **`O1`'s argmax over four risk fractions.** Every rotation was scored at **one fixed
fraction.** So the treatment carried a **best-of-4** and the null was never given one — against
margins of only 23% (QQQ) and 46% (DIA).

**Scored the same way — every offset takes its own max over the grid:**

| cell | treatment | null p95, **fixed** fraction | null p95, **best-of-4** | **the premium the null was denied** | `G2` |
|---|---:|---:|---:|---:|---|
| **QQQ static** | 262 | 213 | **455** | **+242** | **FAIL** |
| **DIA static** | 250 | 171 | **419** | **+248** | **FAIL** |

> **THE SELECTION PREMIUM IS LARGER THAN THE EFFECT IT WAS HIDING.** Allowing the null to pick its
> own best fraction moves its **median** from −111 to +79 and from −143 to +108, and its p95 by
> roughly **+245 on both**. The treatment's entire apparent edge over the fixed-fraction p95 was
> **+49 and +79.**

**And my second prediction was wrong too** — I expected the premium to swallow QQQ and DIA to
survive. **It swallowed both, comfortably.**

## 3. Why this could only ever have gone one way for D442's headline

**A more lenient null can turn a PASS into a FAIL and never the reverse.** D442's primary verdict on
SPY was `G2` **FAIL** at the fixed-fraction null, so it is **untouched** — a selection-honest null
would only push it further inside. **Only the two addendum passes were ever at risk, and they are the
only cells re-run.**

**The result table in D442-RESULT stands as written.** What changes is §8's open item, now closed:
**QQQ-static and DIA-static are controlled, and they fail.**

## 4. The reusable finding, which is worth more than the cells

> **A rotation null must be scored on the SAME STATISTIC as the treatment. If the treatment is an
> argmax over a grid, the null is an argmax over that grid — otherwise the comparison prices the
> gate and ignores the search.**

This programme already holds the general version at [§59](../FINDINGS.md) — *a best-of-N permutation
floor prices SELECTION and is blind to SIGN-FITTING* — and at
[§48](../FINDINGS.md), where three studies decided verdicts on a margin their null could not resolve.
**This is the same error arriving through a different door: not too few draws, but a null scored
one-cell-at-a-time against a treatment scored best-of-four.**

**The check is cheap and mechanical:** *count the choices the treatment was allowed to make, and
give the null every one of them.* Here that was four; the premium it bought was **+245**, against
effects of **+49 and +79**.

## 5. What this does NOT claim

- **It does not close `O1`.** Under [R15](../RULES.md#r15) it cannot, and D442 §7 already scoped the
  failure: **one gate — trailing realised volatility — on one construction, on four symbols.**
- **It does not touch the inactivity finding**, which killed `O1` independently of every economic
  number: **88 consecutive flat sessions at the primary `θ` against MFFU's 7-day rule.** That kill
  needs none of this arithmetic.
- **It does not revisit `G1` or `G3`.** Both stand as reported: `G1` passes on 13 of 16 cells, `G3`
  passes weakly, **and P4 still fails by 12×.**

## 6. A process note, recorded because it is now a pattern

**My wall-time projections this session have been unreliable in both directions** — 14 min projected
against 8 actual on D442's report, 11 against 16 on addendum 1, **22 against 49½ on addendum 2.**
**The one time I profiled the actual loop before launching, the estimate was right.** `CLAUDE.md`
already says *profile first: every guess here has been wrong*; three more instances, and the two
addenda here were launched on arithmetic rather than measurement.
