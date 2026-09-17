# D533 RESULT — the declared test **DOES NOT PASS**, and the dollar line disagrees with it about C3

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D533-RESULT-does-not-pass-C1-is-the-only-condition-whose-sign-held-and-the-dollar-line-disagrees-about-the-exit.md`. The H1 above is the full title.*

*2026-09-15. Spec committed in `d5bf27a` BEFORE the runner (R8). In sample 2016-01-04 → 2023-12-29;
the 2024+ slice was **not read**. Nothing admitted (R15). Nothing closed — only the principal closes
an avenue.*

**Verdict under the pre-registered rule: DOES NOT PASS.** The primary is inside its null and negative,
the family maximum is inside, and the primary's sign is inverted. All three were required.

**But the component line — mandatory, and computed by the runner — orders the four conditions
differently from the accuracy test, and the disagreement is the substance of this record.**

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — C2, fixed exit, both sides *(the principal's nomination)* | n 2,502, observed **47.88 %**, base 50.02 % | lift **−2.14 pts** → **INSIDE**, and inverted |
| **N2 family**, 22 pooled cells | best **+1.33** (`C1-fixed-up`) | family p95 **+5.77** → **INSIDE** |

**Deviation from the pre-registration, recorded rather than smoothed over:** the family was declared
as *the 20 pooled cells* (4 singles + 6 pairs, × 2 sides). The runner scored **22** — it included the
two unfiltered baselines (`none-fixed`, `none-C3`) in the maximum. That makes the bar **stricter**,
not looser, so it cannot have manufactured the verdict; but it is not what the spec said, and the
declared count was wrong by construction since the baselines were always going to be computed.

**The family discipline itself worked.** D532 priced a 192-cell family at p95 **+9.89 points** — a bar
nothing could clear. Declaring the unit of selection in advance brought it to **+5.77**.

## 2. The four conditions on the pre-registered statistic (directional accuracy)

| | prediction | measured, vs unfiltered | |
|---|---|---:|---|
| **C1** break carried flow | improves | **up +2.61, down +1.64** | **AS PREDICTED** |
| **C2** overnight inventory accumulated | improves | up −0.21, down −0.77 | inverted |
| **C4** range built by absorption | improves | up −1.25, down −0.93 | inverted |
| **C3** exit when volume normalises | improves | up −3.95, down −3.03 | inverted, and the largest effect |

**C1 is the only one whose sign held, and it held on both sides.** It lifts the up-side from the
unfiltered −1.28 to **+1.33** — the family argmax — and still does not clear its own p95 (51.25 %
observed against 52.44 %). **The duos dilute**: `C1C2-up` +0.61, `C1C4-up` +0.13, both below C1 alone
on a third of the sample, which is what pairing a real filter with an inverted one should look like.

## 3. Where the dollar line disagrees — **C3 is the best thing here in money and the worst in accuracy**

The component line at minimum tradable size (MCL/MGC/SIL/MNG), under the pre-registered measured
round trip ($4.00 CL, $5.00 GC, $8.00 SI, $5.00 NG), daily P&L, four roots one contract each:

| cell | book **gross** SR | book **net** SR (SE 0.36) | daily σ | gross-positive roots | mean hold |
|---|---:|---:|---:|---:|---:|
| unfiltered | +0.28 | **−1.50** | $188 | 4 of 4, but $0.04–2.63/trade | 12.0 |
| **C2** *(the primary)* | **+0.01** | −1.18 | $93 | 2 of 4 | 12.0 |
| **C1** | **+0.80** | −0.11 | $123 | 3 of 4 (NG −0.15) | 12.0 |
| **C1 + C3** | **+1.03** | **+0.09** | $119 | **4 of 4** | 7.9 |

**C2 has no gross edge at all** — +0.01 book Sharpe, −$0.32 and −$2.44 per trade on CL and SI. The
accuracy test and the money agree completely about the principal's nominated primary.

**They do not agree about C3.** On directional accuracy the volume-normalisation exit is the worst
thing in the study; in dollars it *raises* gross Sharpe on all four roots and is the only cell with a
positive net book. **That is D529 restated: the hit rate is the edge, the payoff ratio is exit
geometry.** C3 lowers the hit rate (39.8 % on SI against 47.1 %) and raises gross dollars per trade
($13.48 against $12.24) — it is cutting losers faster than winners. **Measuring an exit rule on
directional accuracy was the wrong instrument, and that is my error in the pre-registration, not a
property of the data.**

**What the trimmed means do to that, though:**

| cell | trades | mean | median | ex-top 1 % | ex-bottom 1 % | **symmetric trim** |
|---|---:|---:|---:|---:|---:|---:|
| unfiltered | 7,644 | +0.88 | −1.00 | −3.06 | +4.46 | **+0.51** |
| C2 | 2,542 | +0.07 | −2.00 | −3.38 | +3.28 | **−0.17** |
| C1 | 2,542 | +4.85 | +0.00 | +0.27 | +8.90 | **+4.31** |
| C1 + C3 | 2,551 | +6.04 | −1.00 | +0.52 | +9.69 | **+4.14** |

**C1+C3's dollar advantage over C1 is entirely in the tails.** On the trimmed body C1 is the better
number (+4.31 against +4.14); C3 earns its book Sharpe by holding 7.9 bars instead of 12.0, which is
a *per-unit-exposure* improvement, not a larger edge. And the top-1 % share reads 95 % for C1 only
because the untrimmed total is dragged down by an almost equal bottom tail (+$11.6k against −$10.1k
on 25 trades each side); the body carries **+$10.7k at +$4.31 a trade**, so here the symmetric trim is
the honest number and the winners-only trim is the frightening one (D307).

**And +$4.31 gross does not cover a $4.00–$8.00 round trip.** The net book Sharpes above are
−0.11 and +0.09 against an SE of **0.36** — indistinguishable from zero, on a statistic that **was
never pre-registered and has had no null run against it**. Reading C1+C3 as an edge because it came
out top of a table I looked at afterwards is exactly the selection this record's family discipline
exists to price. It is a lead, not a result.

## 4. The bug I introduced, having diagnosed it an hour earlier

C2 returned **zero coverage on all six roots** on the first run and the primary died on a division by
zero. Cause: `rolling(50, min_periods=50)` over a series with scattered NaN night rows — a 50-wide
window essentially never holds 50 clean observations, so the series collapses to NaN.

**This is the same failure I had found and written up the same day**, when `activity_filter` returned
`score finite 0 of 2,453` on this fixture for the same reason. I diagnosed it, recorded it, then wrote
the identical pattern into a new file. Fixed with `min_periods` strictly below the window, plus an
assertion that the primary produced cells at all, so a next occurrence stops at the condition rather
than four screens later at a `ZeroDivisionError`.

## 5. What this leaves

**Nothing is closed and nothing is admitted.** Of the four conditions the inventory-transfer story
implies, **one behaves as the story says on the statistic it was tested on** — C1, break flow, on both
sides — and it is inside its null. C2 and C4 are inverted on accuracy, and C2 has no gross edge in
dollars either.

**The open question this hands forward is C3**, and it is not the question the record set out to ask:
an exit rule was scored on directional accuracy, failed there, and came top in money. Testing it
properly means pre-registering the **dollar** statistic with its own null — which is a different
record, on a family that has now seen this table.

**The higher-order combinations the principal deferred look less promising than when they were
deferred**, because the duos dilute rather than compound.

---

Runner: [`scripts/run_d533_story_conditions.py`](../../scripts/run_d533_story_conditions.py) —
`--run` (the declared test), `--component` (the dollar line), `--selftest` (C4 on a ramp and an
oscillation, C3 on a planted quiet bar, a tercile selecting a third, **[SIGN] in money on both sides
with an [X] inverted-book break**, and **[QTY]** that minimum size is not the full contract).
Artefact: [`data/d533_story_conditions.json`](../../data/d533_story_conditions.json).
