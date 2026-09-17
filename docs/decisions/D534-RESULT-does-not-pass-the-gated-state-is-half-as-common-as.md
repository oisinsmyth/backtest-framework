# D534 RESULT — **DOES NOT PASS**: the gated state is half as common as independence, and displacement predicts **size, not direction**

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D534-RESULT-does-not-pass-the-gated-state-is-half-as-common-as-independence-and-displacement-predicts-size-not-direction.md`. The H1 above is the full title.*

*2026-09-15. Spec committed in `610cb2e` BEFORE the runner (R8). In sample 2016-01-04 → 2023-12-29;
the 2024+ slice was **not read**. Nothing admitted (R15). Nothing closed.*

**The mechanism is not refuted — the falsifier did not fire. It is UNDERPOWERED, and the reason is a
premise I did not check before pre-registering.**

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — drift+thin, 60 min, contrast in σ units | **+0.0518** (WITH −0.0017 vs AGAINST −0.0535), n 238/267 | null p50 −0.0052, **p95 +0.1429** → **INSIDE** |
| **N2 family**, the 6 declared cells | best **+0.0518** — the primary itself | family p95 **+0.1740** → **INSIDE** |

The primary reaches **36 % of its own null bar**. Nothing here is close.

**[F] premise 1 passed cleanly**: correlation between the night's `h08` close and the session's first
open is **1.0000 on all four roots**, median gap 0.01 CL / 0.10 GC / 0.00 SI / 0.001 NG against median
session ranges of 1.36 / 12.20 / 0.285 / 0.082. The night scored is the night that precedes the
session. The `[X]` break in the selftest confirms a one-session shift fails the same check (−0.19).

## 2. The premise I should have checked first: the gated state barely exists

| | sessions | `\|z\|>1` | `thin` | **independent** | **observed** | |
|---|---:|---:|---:|---:|---:|---:|
| CL | 1,917 | 29 % | 49 % | 272 | **154** | 57 % |
| GC | 1,967 | 27 % | 48 % | 255 | **111** | 44 % |
| SI | 1,967 | 28 % | 48 % | 264 | **117** | 44 % |
| NG | 1,920 | 31 % | 46 % | 274 | **126** | 46 % |

**Displacement and volume are positively associated, so "a big move that was cheap to make" is
roughly half as common as chance** — 6–8 % of sessions rather than the 13–14 % independence gives.
The conjunction I declared is rare *because of the very relationship the story is about*: markets that
move overnight normally trade while they do it.

That left **505 pooled trades across four roots and eight years** — about **7 a year per root**. The
null p95 of ±0.14 σ is wide for exactly that reason. **This is my own Stage-0 rule unapplied: measure
the conditioner's own frequency before designing a study around it.** The gate's rarity was
computable in one line before the pre-registration and I did not compute it.

## 3. What the numbers say about the mechanism anyway

**P-2 fails, and it is the informative one.** The WITH arm reads **−0.0017 σ** against the unfiltered
break's **+0.0090 σ**. The gate does not add — it selects trades *slightly worse* than an ungated
break. **The contrast is positive only because the AGAINST arm is worse still (−0.0535).**

**On a thin-displaced night, breaks in BOTH directions underperform an ordinary break.** That is not
the prediction, and it is not the falsifier either (P-4 did not fire: WITH does beat AGAINST). It is
consistent with a fragile-move reading — a large overnight move nobody paid for leaves a day session
that goes nowhere in either direction — but that is a story fitted to 505 trades and I am not
advancing it as a finding.

**P-3 "holds" and must not be read as support.** The thin gate adds **+0.0501** over drift alone, in
the predicted direction — but drift-only at 60 min is **+0.0017** and drift+thin is **+0.0518**, and
**both sit inside their own nulls**. The difference has no null of its own. This is noise moving to
noise, and the discriminating prediction remains undecided.

**The drift-only cells are the clearest thing in the run, and they are not about direction:**

| drift only, n ≈ 2,224 | WITH | AGAINST | contrast | null p95 |
|---|---:|---:|---:|---:|
| 30 min | **+0.0698** | **+0.0396** | +0.0302 | +0.0697 |
| 60 min | +0.0500 | +0.0483 | +0.0017 | +0.0720 |
| 120 min | +0.0349 | +0.0463 | −0.0114 | +0.0742 |

**Both sides sit far above the unfiltered break (+0.0106 σ at 30 min), and the contrast between them
is inside the null at every horizon.** A materially displaced night makes the following break *bigger*
in both directions and no more *right* in either. **Displacement predicts size, not direction** — the
same shape D531 found in the break itself: a trigger and a clock, no edge.

One more fact against the mechanic: gated breaks split **1,096 WITH / 1,128 AGAINST**. The
opening-range break direction is **independent of the overnight move's direction**. Whatever the night
does, the morning's first break is a coin flip relative to it.

## 4. Component line

Required whatever the verdict, and computed by the runner — the WITH arm at minimum tradable size,
60-minute exit, under the pre-registered measured round trip:

| root | size | trades | gross $ | net $ | hit | daily σ | net SR (SE 0.36) | skew |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| CL | MCL | 78 | +7.21 | +3.21 | 56.4 % | $14 | +0.15 | −0.17 |
| GC | MGC | 51 | +6.84 | +1.84 | 35.3 % | $11 | +0.07 | +6.58 |
| SI | SIL | 55 | −6.27 | −14.27 | 38.2 % | $23 | −0.28 | +7.53 |
| NG | MNG | 54 | −10.57 | −15.57 | 35.2 % | $10 | −0.68 | −12.62 |
| **BOOK** | 1 each | | | | | **$34** | **−0.30** | +7.73 |

**Uninterpretable, and it should be read as uninterpretable.** 51–78 trades per root over eight years
is roughly seven a year; the skews (+7.53, −12.62) are single-trade artefacts at that count. **The
duty cycle disqualifies this as a component whatever the sign** — a construction that trades seven
times a year cannot carry a book line, and a degenerate cell has beaten a rotation null here before.

## 5. What this leaves

**Nothing closed, nothing admitted, and the principal's mechanic is not tested.** The objection that
opened this record — *if someone needs to get rid of inventory in the morning, why would they be
accepting it at night?* — is sound and remains untested, because the observable I built for it picks
out a state that happens seven times a year per root.

**The fix is to stop gating on a conjunction and measure the thing continuously.** Displacement *per
unit volume* — how far price had to travel per contract traded, signed by the direction it travelled —
is one number available on every session, keeps a third of the sample instead of a sixteenth, and is
the quantity the story actually names. It is also, exactly, the **reciprocal** of D533's C2, now
signed and ranked rather than gated. That is the natural successor and it is not run here.

---

Runner: [`scripts/run_d534_unplaced_inventory.py`](../../scripts/run_d534_unplaced_inventory.py) —
`--selftest` carries **[LAG]** (the night state re-derived in a second implementation), an **[X]**
one-session shift that must fail the alignment check, **[SIGN]** with an inverted-night break,
**[QTY]** that each gate binds, a **[NULL]** centring check on an unrelated book, and a **[WARMUP]**
check that a session cannot enter its own trailing reference.
Artefact: [`data/d534_unplaced_inventory.json`](../../data/d534_unplaced_inventory.json).
