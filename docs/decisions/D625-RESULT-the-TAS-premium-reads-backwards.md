# D625 RESULT — the TAS premium does not pass as pre-registered; its control fired on a base-rate effect, and the TAS price level reads BACKWARDS: a premium goes with SELLING in the window

*2026-09-25. Pre-registration: [D625](D625-PRE-REG-the-TAS-premium-as-a-signed-stand-in-for-window-flow.md),
committed alone in `158b2d2`. Runner: `scripts/validate_tas_premium.py`; output:
`data/ledger_tas_premium_validation.json`, which reproduces byte for byte (`--check`). The NG/CL gate has not
been read. Under §5 it could not rescue a use the siblings did not support.*

## The pre-registered outcome: no use admitted, for either role

The sibling phase raised on its own control, as designed:
**`C1 failed (W, RB): day-shifted agreement 0.6115`**. That is above the 0.60 ceiling: the chosen window measure
agreed with the NEXT session's flow sign as often as with the same session's.

The cause is not a bug, and the post-hoc diagnostic below shows it:
- **the window flow's sign is persistent.** In RB's second half, 79% of sessions were net selling.
- **the chosen measure leaned the same way.**
- **So raw sign agreement can reach D625's 70% bar with no day-to-day information.** That is a flaw in the
  pre-registered statistic, and the control caught it.

As pre-registered, D625 would have failed even without the control:

| role | chosen (first half) | second-half sign agreement against the 0.70 bar | chance agreement from the base rates |
|---|---|---|---|
| W: window | T3 (TAS tick rule), mean 0.545 | HO 0.53, RB 0.61 | ≈ 0.48, 0.64 |
| P: pre-window, τ = 14:10 | T1 (T3 within 0.01, simpler wins) | HO 0.51, RB 0.55 | ≈ 0.47, 0.54 |

**Neither role is admitted.** Stage B's update step stays blocked (A8), and there is no H1b from D625.

## The post-hoc finding: the level reads backwards

This part was written after C1 fired, and it is not D625's statistic. The runner's `--diagnose` computes Cohen's
κ per root, half, role and measure. κ measures sign agreement beyond what the two series' sign frequencies give
by themselves.

For the window role, the volume-weighted TAS differential T1 anti-agrees with the true window-flow sign on
**every** sibling sample:

| T1, window role | κ, pre-registered sign (+) | κ, reversed sign (−) | reversed-sign agreement / chance | n |
|---|---|---|---|---|
| HO, first half | −0.33 | **+0.33** | 0.66 / 0.49 | 108 |
| HO, second half | −0.39 | **+0.42** | 0.72 / 0.52 | 141 |
| RB, first half | −0.43 | **+0.49** | 0.76 / 0.53 | 108 |
| RB, second half | −0.19 | **+0.44** | 0.83 / 0.70 | 140 |

- **Across measures:** T2 (TAS volume signed by level) behaves like T1. T3 (the tick rule on TAS) sits near 0,
  between −0.16 and +0.15.
- **The pre-window role (P)** is near 0 for every measure (|κ| ≤ 0.16).
- **The asymmetry:** κ is not exactly symmetric under a sign flip, because a zero measure is its own category.

**Not a pass, and not usable yet.**
- D625 fixed the sign as + and forbade flipping it afterwards. This is exactly the case that rule exists for.
- The whole sibling year has now been SEEN. The reversed-sign hypothesis is therefore tested only on data D625
  never read, in [D626](D626-PRE-REG-a-TAS-premium-goes-with-selling-in-the-window.md): NG/CL post-vault and
  HO/RB after 2026-09-18, with κ and a pooled bar.

## Lessons

- **Raw sign agreement needs a base rate.** A persistent flow sign lets an uninformative measure clear a raw
  agreement bar. Every sign test here now uses κ (or agreement against the chance level implied by the base
  rates).
- **A pre-registered sign can be wrong, and the discipline held.** The effect was strong and consistent, but
  inverted. It gets a fresh test; it is not a re-labelled pass.

## Deviations

- The runner gained a `--diagnose` mode (post hoc, labelled). It records the pre-registered sibling phase's
  raise as the outcome.
- It also gained a `temp/` cache of decoded frames, keyed on source files and arguments. Reproduction went
  from about 20 minutes to 44 seconds. The pre-registered path is otherwise unchanged.
