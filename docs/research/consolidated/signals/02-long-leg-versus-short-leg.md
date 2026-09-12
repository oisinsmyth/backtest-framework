# The long leg — the campaign's central open question

[← signals index](00-index.md) · prev: [profitability family](01-profitability-family.md) · next: [construction dispersion](03-construction-dispersion.md)

**Why it is the central question.** This programme can hold the long leg. Its short side is a measured
cost failure (`[REPO]` [FINDINGS §19, §30](../../../FINDINGS.md)). **So every published long/short
number is unusable unless the long half pays on its own** — and the campaign found, three times
independently, that **nobody reports it.**

---

## THE BLIND SPOT — three literatures, three lanes, none told the others were looking `[EXT]`

| lane | literature | what it found |
|---|---|---|
| `C2` | non-standard errors | **measures spreads, never long legs** — zero occurrences of *"long leg"* in one paper's appendices |
| `C3` | drawdown | **no source reports a long-only tilt's drawdown.** The two that appear to are reporting a **market-neutralised** leg (2.2% vol, −0.02 beta) and a column headed *"% cumulative underperformance"* |
| `C4` | post-publication decay | **none of five decay papers reports long-leg decay separately** — verified by grep on all five |
| `D1` | construction nodes | **the fourth instance, and proven from SOURCE CODE** rather than from silence |

> **The programme can only hold the long leg. Three separate literatures do not report it.** Round 3's
> most reusable finding, and **no lane was commissioned to find it.**

## `F1` — two of the campaign's own lanes, same era, opposite verdicts `[CONFLICT F1]`

**Both asked: what does an equal-weighted profitability long leg earn against its own equal-weighted
universe?**

| | `C3` | `C4` |
|---|---|---|
| **result** | **+0.026 %/mo, IR 0.057, `t` 0.45** over 63 years; **1,235 years to reach `t` = 2.** In our era the tilt compounds at **10.62% against the universe's 10.66%** — worth nothing — with a **deeper** drawdown (−38.60% vs −36.42%) | **+0.405 %/mo, `t` 3.00** post-publication 2014–2024; **+0.379, `t` 3.56** over 2010–2024 |
| **signal** | **operating** profitability / **book equity** | **gross** profitability / **assets** |
| **dataset** | Ken French's portfolio files | the Chen–Zimmermann public dataset |
| **cut** | deciles | quintiles |
| **controls** | positive control against French's own annual block; a control that **FIRED** and was correctly re-stated | **13 negative + 5 positive**; one reproduces round 1's figure **exactly** (0.704 `t` 3.14 vs 0.70 `t` 3.14); identity control at 1.8 × 10⁻¹⁴ |

**Both fully controlled. Both stand. Nothing selects between them.**

**`C3` was then independently reproduced** by `D4` on a different script: **+0.0262 [`t` +0.45]** — and
`D4` found the obvious construction shortcut carries a **13.6 bp/month, sign-flipping error which `C3`
did not make.**

**Two things would settle `F1`**, and one is `G3`: **is `C4`'s benchmark actually its EW universe?**
`C4` used the simple mean of five quintiles, *"which for an equal-count sort is its EW universe"* —
**the conditional is right, and whether those quintiles are equal-count is unchecked.** `D4` flags it
as a question, explicitly not a refutation.

## `D1`/`E1`/`E2` — the round-1 conflict, and the benchmark under it

**`A3`: the long leg fails gross** — Var(t) = **0.98** against the VW market, below the luck null.
**`A2`: Var(t) = 1.35–1.81** and signal share 0.26–0.45, **against each sort's own name-weighted
universe.** *"The benchmark is the crux."*

**`B1` then read Var(t) = 0.98 as a benchmark artefact `[CONFLICT E2]`:** a mismatched benchmark
injects sd **1.2–2.8%/mo**, predicting Var(t) of **0.76–1.19**, so 0.98 is inside the artefact's own
range. **Both stand; `B1`'s is recorded as `B1`'s verdict.**

**And `A3`'s −0.04%/month is the cross-sectional mean over ~170 anomalies**, which its own §7.1 says.
**The compression that dropped the cross-section was the commissioner's, in round 2's slate.**

See [benchmark choice](../method/01-benchmark-choice.md) — this is the same question from the method
side.

## Do long legs dominate? `[CONFLICT E7]` / `[CONFLICT D7]`

**Blitz:** combined long Sharpe **1.10 vs 0.69** short, 1963–2018, against a 50/50 hedge.
**CFM, reproducing it:** *"the short leg should be allocated 30% of the weight, and not zero weight…
the 'no-short' recommendation is not robust against such minor changes."*

**Both are interested parties pointing opposite ways. Both stay.** And `E1`: CFM's SMB attribution
appears **only when the hedge is the cap-weighted index Blitz explicitly refused.**

`A3`'s own five internal conflicts include **a supportive paper whose own test cannot reject a 50/50
split**, and **a paper whose draft and published abstracts differ in SIGN** (+0.02% → −0.01%) while
**its prose disagrees with its own tables** on three high-fee shares.

## Where `K6` lands, and it is the harshest reading `[EXT]`

**long-minus-market Var(t) = 0.98, BELOW the null → every post-2005 survivor's long-only return
shrinks to 0.00%/month.** 162 anomalies: **+0.14%/month before borrow fees, −0.01% after.**
See [what anomalies pay](../cost/02-what-anomalies-pay.md).

## What the repo has measured, and it points the same way `[REPO]`

[FINDINGS §28](../../../FINDINGS.md): *"The long excess is cohort membership, not timing: no long
signal beats its own names at random times."* [§15](../../../FINDINGS.md): **a signal can own ONE leg,
and the two legs of a spread book need not come from the same signal.**

**Different objects — a slow annual characteristic tilt versus this programme's fast selectors — so
this is not a contradiction.** Both negatives point the same way and **neither has been run on the
other's construction.** [vs repo R10](../conflicts/02-versus-repo-measurements.md).

## What a long-only implementation would even look like `[EXT]` `A3` §4, §7

`A3` covers long-only implementations, **conditioning rather than selecting**, and **the long leg with
the short leg replaced by a market hedge or by cash**. Its §9 does the arithmetic on **what "avoiding
the bad names" is worth**. Read there; nothing here compresses it further.

---

**Sources.** [`R1-02` §7](../../Scan-100926/R1-02-persistent-characteristics.md) ·
[`R1-03`](../../Scan-100926/R1-03-the-long-only-problem.md) ·
[`R2-01`](../../Scan-100926/R2-01-the-benchmark-question.md) ·
[`R3-03`](../../Scan-100926/R3-03-the-shape-of-the-drawdown.md) ·
[`R3-04`](../../Scan-100926/R3-04-is-it-already-dead.md) ·
[`R4-01` §7](../../Scan-100926/R4-01-the-nine-unexamined-nodes.md) ·
[`the-reversal-round.md` §1.1](../../the-reversal-round.md).
