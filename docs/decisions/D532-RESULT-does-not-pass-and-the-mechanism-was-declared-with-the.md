# D532 RESULT — **DOES NOT PASS**, and the mechanism was declared with the sign backwards

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D532-RESULT-does-not-pass-and-the-mechanism-was-declared-with-the-sign-backwards.md`. The H1 above is the full title.*

*2026-09-15. Spec committed in `ac15ee6` BEFORE the runner (R8). In sample 2016-01-04 → 2023-12-29;
the 2024+ slice was **not read**. Nothing admitted (R15). Nothing closed.*

**This result is late: the run finished, the principal redirected to D533, and the write-up was not
done at the time.** It is recorded here in full because R8 requires the result whatever it says, and
because D533's pre-registration already relied on reading this table — a record cannot be leaned on
while it does not exist.

---

## 1. The declared verdict — all three fail

| | | |
|---|---|---|
| **PRIMARY** — `V` low tercile, 60 min, pooled CL/GC/SI/NG, both sides | n 2,447, observed **47.32 %**, base 50.00 %, p95 51.62 % | lift **−2.68 pts** → **INSIDE** |
| **N2 family**, 192 cells | best **+6.30** (`NQ-V-high-down-H15`) | family p95 **+9.89** → **INSIDE** |
| **Dose-response** — predicted `lift(low V) − lift(high V) > 0` | **5 of 12 positive**; on the four candidate roots only CL | **sign INVERTED** |

**PASS required all three. None of them holds.**

Three of 192 cells clear their own per-cell p95 (`GC-W-low-up-H120`, `NQ-V-high-down-H15`,
`NQ-V-high-down-H30`) — about what 192 draws at a 5 % threshold produce, and every one of them is
inside the family bar. **This is exactly what the 192-cell family was declared to price**, and it is
why D533 committed in advance to a 20-cell unit of selection: a family p95 of **+9.89 points** is a
bar no conditioner of this kind can clear, so the test could not have resolved either way.

## 2. The prediction that failed hardest, and why it matters more than the verdict

**P-1 said a negative dose-response means "the absorption/vacuum mechanism is inverted and the story
is wrong in the way that matters." It is negative. But the story was never what this runner tested.**

The pre-registration declared **low OR volume → break continues** ("a thin book is easy to push").
The inventory-transfer story says the opposite: a break happens **because transfer flow exhausted the
standing book**, which requires flow to have gone through it. **No flow, no exhaustion.** I wrote a
different mechanism from the one I had just described, and then declared its sign.

**The data, read with the corrected sign, points the story's way:**

| | cells | mean lift |
|---|---:|---:|
| `V` **high** tercile | 48 | **−0.67** |
| `V` **low** tercile | 48 | −1.78 |

**High-volume breaks beat low-volume breaks by 1.11 points on average across 48 cells each** — the
dose-response the story predicts, which is the one the record declared backwards. The family maximum
is also a *high*-V cell. **So D532's "DOES NOT PASS" is a verdict on my derivation, not on the
mechanism**, and that is what sent D533 back to derive the conditions from the story rather than from
a plausible-sounding sentence about thin books.

D533 then tested that corrected direction properly as **C1**, and found it the only one of four
conditions whose predicted sign held on both sides — still inside its null.

## 3. The other two predictions

**P-2 — "W adds less than V" — not supported, and not contradicted either.** Mean lift is −1.22 for V
against −1.32 for W across 96 cells each, and each conditioner supplies one of the three cells that
clear their own p95. Nothing here separates transacted quantity from range.

**P-3 — "the effect is larger on the non-index roots" — refuted, and in the direction that is
inconvenient.** Candidate roots (CL/GC/SI/NG) mean **−2.04** across 128 cells; index roots (ES/NQ)
mean **+0.28** across 64. The two strongest cells in the study are both **NQ**. The reasoning was that
a conditioner has more room where the base rate is near neutral (FINDINGS §74); what the data says is
that whatever continuation exists sits on the index roots — **where a second arm beside the admitted
NQ arm is a closure offence under the one-direction rule, not merely a C-b failure.**

That is a structural constraint, not a statistical one, and it is the reason the candidate roots were
commodities in the first place. It applies to anything this line produces.

## 4. Component line

**Not computed for this record.** Every cell here is a directional-accuracy lift measured against a
rotated base rate; the primary is 47.32 % against a 50.00 % base and the family maximum is inside its
null, so there is no construction to score. **This is a gap in the record under the standing rule**
that every construction tested for either book gets a component line whether or not it clears — the
honest statement is that it was not run, not that it was not needed. D533 carries the component line
for the corrected version of this conditioner (C1: book gross Sharpe **+0.80**, net **−0.11** at SE
0.36), which is the number this record would have wanted.

## 5. What this leaves

**Nothing closed, nothing admitted.** The unconditional break carries nothing (D531 addendum, 0 of 48
cells). This record asked whether a declared condition supplies direction and answered: **not this
condition, declared this way, against a family this size.**

Two things carry forward, and both did: **derive the condition from the story rather than from a
paraphrase of it**, and **declare the unit of selection before the run** — D533 did both.

---

Runner: [`scripts/run_d532_orb_conditioned.py`](../../scripts/run_d532_orb_conditioned.py).
Artefact: [`data/d532_orb_conditioned.json`](../../data/d532_orb_conditioned.json).
Successor: [D533](D533-RESULT-does-not-pass-C1-is-the-only-condition-whose-sign-held.md).
