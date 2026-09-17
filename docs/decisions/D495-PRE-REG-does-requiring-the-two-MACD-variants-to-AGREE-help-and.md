# D495 — PRE-REG: does requiring the two MACD variants to AGREE help, and is any help direction or just fewer trades?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D495-PRE-REG-does-requiring-the-two-MACD-variants-to-AGREE-help-and-is-any-help-direction-or-just-fewer-trades.md`. The H1 above is the full title.*

**2026-09-12, committed before the runner exists** (CLAUDE.md, [R8](../RULES.md#r8)).
Directed by the principal: *"another confluence"*, chosen as B1 ∧ B2 agreement.

---

## 0. Why this confluence, and why it is the cheapest one available

[D491](D491-RESULT-the-first-component-candidate-and-why-it-is-thinner.md) produced
the line's first component candidate and, in the same tables, **two sharp disagreements between
the two MACD variants on the same root and window**:

- **NQ**: B1 gives the single best cell (+0.583) while **B2 beats B1 pooled**;
- **CL**: B2 is the best gross cell measured anywhere (+10.53 ticks/session) while **B1 is
  negative** (−0.52 to −4.55).

Two smoothed variants of the same indicator disagreeing that hard is either noise or
information. **Requiring them to agree is the direct test, it costs one extra arm rather than a
grid, and both series are already computed.**

**And the specs blocker is gone.** `data/futures_contract_specs.json` gained **MGC, MCL, M6E and
6E** on 2026-09-12 (MNQ re-fetched as a control, reproducing its committed values exactly). So
**all eight roots can be costed for the first time**:

    ES  -> MES  $1.25  cost 3.409 tk       GC  -> MGC  $1.00  cost 4.009 tk
    NQ  -> MNQ  $0.50  cost 7.009 tk       CL  -> MCL  $1.00  cost 4.009 tk
    YM  -> MYM  $0.50  cost 7.009 tk       6E  -> M6E  $1.25  cost 3.409 tk
    ZN  -> no micro, 1 full contract, cost 1.201 tk
    ZB  -> no micro, 1 full contract, cost 1.105 tk

**ZN and ZB have no micro**, so they are scored at one full contract and **C-d is expected to
reject ZB** (D468 measured its daily σ at $682–939 against the $500 cap). That is a real
rejection, not an omission.

### What the fetch already settled, recorded here so this record does not re-discover it

Costing D491's non-index cells with the fetched values leaves **1 of 20 net positive**: CL B2
M=5 at **+1.06 ticks/session**. **GC dies completely** (−2.82 to −6.43). I had called GC and CL
"where the value is" on their *gross* figures; charging 2.0–2.6 round trips a session at $3
against a $1.00 tick removes all but one cell. **The gross numbers looked large because the fee
had not been applied.**

## 1. The construction, fixed now

**Everything is D491's, unchanged, except the signal gate.** Same imported D484 signal code,
same published parameters (impulse 34/9, plain 12/26/9, **no re-tuning**), same conditional-hold
state machine, same P2 cap at the close of segment 21, same closure confining ES/NQ/YM to the
day session.

**Three arms, and only one is new:**

| arm | signal each hour |
|---|---|
| **AGREE** (new) | `sign(B1) if sign(B1) == sign(B2) and both ≠ 0, else 0` |
| **B1** (comparison) | `sign(B1)`, D491's construction |
| **B2** (comparison) | `sign(B2)`, D491's construction |

A zero means **no position**, and under the conditional exit it **closes** one after the minimum
hold. So disagreement flattens the book.

**Minimum hold M ∈ {1, 2, 3, 5}** on index roots (6-hour window), **{1, 2, 3, 5, 8}** on the
rest. **Cells: AGREE 3×4 + 5×5 = 37; all three arms 111.**

## 2. The statistics, fixed now — and the decomposition is the point

**Requiring agreement does two things at once and they must not be confused.** Agreement is
rarer than either variant alone, so it **enters less often and pays fewer round trips.** Since
commission is 70–86% of cost, that alone could raise net Sharpe **without any directional
improvement whatsoever.**

So every arm is scored **twice**:

| | |
|---|---|
| **gross Sharpe** | cost set to **zero** — pure direction |
| **net Sharpe** | cost charged per round trip — direction *and* frugality |
| **trips per session** | the frugality channel, reported explicitly |

**P1 — the confluence's own bar:** family-maximum **net** Sharpe over the **37 AGREE cells**,
against a rotation null over those same 37.

**P2 — the LIFT, which is the actual question:** per root, `AGREE` at its best M minus the better
of `B1`/`B2` at their best M, **computed on gross and on net separately**, then pooled across the
eight roots. **One number each.**

- **Lift positive on NET but not on GROSS ⇒ the confluence buys frugality, not direction.**
- **Lift positive on GROSS ⇒ agreement genuinely carries information.**

**C-a, C-c and C-d are reported for every cell** (net, at minimum size), since D491 showed they
can be computed directly.

## 3. The null, fixed now

**R1 — rotate BOTH signal series by the SAME offset, then re-run the state machine.** Rotating
them together is essential: rotating them independently would destroy their *agreement
structure*, which is the very thing under test, and would make the null a test of something else.
The common offset preserves each series' autocorrelation **and** their mutual agreement rate, so
the null enters and exits about as often and pays a comparable bill.

**2,000 draws.** Statistics: the family maximum for P1, and the pooled lift for P2. Report p50
and p95 with the **bootstrap SE of the p95**; within **2 SE** is **UNRESOLVED**, not a pass.
One-sided.

## 4. The bars, fixed now

| verdict | requires |
|---|---|
| **CONFLUENCE SIGNAL** | P1's family max clears its R1 p95 by > 2 SE |
| **CONFLUENCE HELPS** | P2's **net** lift clears its R1 p95 by > 2 SE |
| **HELPS ON DIRECTION** | additionally P2's **gross** lift clears its own p95 by > 2 SE |
| **COMPONENT CANDIDATE** | a cell clearing P1 **and** C-a > 0.5, C-c ≥ −0.5, C-d ≤ $500 |

**Nothing is entered off this runner.** 2024+ stays sealed.

## 5. Predictions

- **U-a.** The **net** lift is **positive** and clears its null — agreement helps on the bottom
  line.
- **U-b.** The **gross** lift does **NOT** clear its null. **So the help is frugality, not
  direction.** *This is my central prediction and the reason §2 splits the two: agreement fires
  less often, and fewer round trips is worth real money when commission is 86% of cost.*
- **U-c.** **Trips per session fall by at least 15%** on the AGREE arm against the better single
  variant.
- **U-d.** **NQ remains the only index root with a positive net Sharpe**, and CL the only
  non-index one — the root ordering of D491 survives the confluence.
- **U-e.** **ZB fails C-d** at one full contract, and ZN fails C-a.

## 6. What would make me wrong

U-b breaking — the **gross** lift clearing its null — would mean the two variants' agreement
carries directional information rather than merely trading less. That would be a genuinely new
finding and the first evidence in this line that a confluence adds signal rather than subtracting
cost.

## 7. Stated limitations, before any number exists

1. **111 cells against D491's 24.** The family null prices the search, but the bar rises with it,
   and D491's margin was only **+0.072** of Sharpe. **A wider search must find more to clear
   more.** P1's null covers the 37 AGREE cells only; the comparison arms are reported beside it.
2. **ZN and ZB are scored at one FULL contract** because no micro exists — a different risk scale
   from the other six, which is why C-d is reported per cell rather than assumed.
3. **6E's tick carries a venue split** — Globex $6.25 against ClearPort $1.25 — and the Globex
   value is used because the data is GLBX.MDP3. Recorded in the specs file with a warning field.
4. **Execution is open-of-next-segment at the measured half-spread**: no queue, no partial fills,
   no slippage on a flip. Fills need `mbp-10` (D471 §1). **Every figure is an upper bound.**
5. **The volume-clock exit (D472, +10.4%) is not applied.**
6. **The index window is six hours**, so the conditional exit fires on ~17% of sessions there
   (D491) — the confluence is being tested mostly on the non-index roots, where it has room.
7. **In-sample.** 2024+ is the confirmation slice and is not read.
