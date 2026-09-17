# D528 ADDENDUM 6 — the combined test, and why 109 trades cannot be tested at all

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D528-ADDENDUM-6-the-combined-test-and-why-109-trades-cannot-be-tested.md`. The H1 above is the full title.*

Date: 2026-09-14. Runner: `working/d528_combined.py`.

**Nothing admitted (R15).** Micro universe (8 roots), in sample only; the reserved slice
(2026-04-11 → 2026-09-09) remains UNREAD.

**Declared before running:** target = `reflect`, frame = `drift`, `G = 3.0` (the principal's own
`1.5·X` proposal), τ = 40, `traverse`, micro, 3 slots. `G = 4.0` was deliberately NOT declared
despite being the only rung that turned positive net in ADDENDUM 5, because it was chosen by
reading that file's ladder and declaring it would score the same look twice.

---

## 0. Why this file exists: ADDENDUM 5 did not test the combination

The principal asked. ADDENDUM 5 crossed `target × frame`, so `opposite`+drift and `reflect`+drift
appeared in its tables — but its **G and τ ladders, and all of its nulls, were run only in the
FROZEN frame.** Two consequences:

* the best cell in that file (`reflect` + drift, net −$1.66/trade) had **no null at all**, and
* the one rung that turned positive net (`G = 4.0`, frozen) was **never tried with drift**,

so "all the improvements at once" was never actually measured. The full grid
(3 targets × 2 frames × 5 stop widths) is measured here, with 20-shuffle nulls on all ten
drift-frame rungs, on both lenses.

## 1. The finding: the combination is inside its null on every statistic

`traverse`, `reflect`, drift, G = 3.0, τ = 40, 3 slots, n = 109:

| statistic | real | null p50 | null p95 | verdict |
|---|---:|---:|---:|---|
| path-invariant gross $/trade | +3.00 | −0.88 | **+8.84** | inside |
| path-variant Sharpe gross | +1.17 | −0.32 | +1.70 | inside |
| path-variant Sharpe net | −0.65 | −2.18 | **+0.81** | inside |

## 2. And the reason is the sample size, not the construction

**At n = 109 a sign-shuffled universe reaches a POSITIVE net Sharpe 5% of the time** — the null's
p95 on net Sharpe is **+0.81**, and on gross per trade it is **+$8.84**. A genuinely good
construction would have to clear a net Sharpe of 0.81 merely to register as different from noise.

**Cell C is therefore untestable at this sample size, and that is the load-bearing conclusion of
this addendum.** It retrospectively explains every encouraging `traverse` number in this
programme's session:

| reading | where | now explained by |
|---|---|---|
| gross Sharpe +0.87 vs p95 +0.80 | ADD 3 §2.2 | a 20-draw p95 whose SE swamps 0.07 |
| P(target) above its null at all six stop widths | ADD 4 §4 | one look, not six |
| net +$1.57, Sharpe +0.45 at G=4.0 | ADD 5 §3 | inside the null on gross AND net Sharpe (below) |
| gross +$1.79, "the only positive-gross cell" | ADD 5 §2 | null p50 is itself +$1.11 |

### 2.1 The G = 4.0 rung, now with the null it never had

| statistic | real | null p50 | null p95 | verdict |
|---|---:|---:|---:|---|
| gross $/trade | +5.66 | −2.11 | +8.22 | inside |
| Sharpe gross | +1.67 | −0.58 | +1.47 | **above p95** |
| Sharpe net | +0.30 | −1.85 | +0.57 | inside |

**Above p95 on one statistic of three, and inside on both of the ones that matter** (gross per
trade is the programme's signal criterion; net Sharpe is what a book is scored on). ADDENDUM 5
recorded this rung as noise on four structural grounds; the null now agrees.

## 3. Cell B is where the signal is, and it is unambiguous and too small

`no classifier`, n = 12,865, so the null bands are tight. Above p95 on **gross in 6 of 10 rungs**,
and on **all three statistics** at `reflect`/G = 2.5:

| target | G | real gross | null p50 | null p95 | real Sh_g | null p95 | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| reflect | 2.5 | −0.15 | −0.64 | −0.37 | −0.71 | −2.21 | above on gross + Sh_g + **Sh_n** |
| reflect | 3.0 | −0.33 | −0.79 | −0.41 | −1.38 | −2.03 | above on gross + Sh_g |
| reflect | 3.5 | −0.49 | −0.99 | −0.55 | −1.90 | −2.09 | above on gross + Sh_g |
| opposite | 2.5 | −0.23 | −0.75 | −0.44 | −1.44 | −3.09 | above on gross + Sh_g |
| opposite | 3.0 | −0.44 | −0.92 | −0.49 | −2.40 | −2.59 | above on gross + Sh_g |
| opposite | 3.5 | −0.62 | −1.07 | −0.66 | −2.79 | −2.66 | above on gross |

**Every one is net-negative.** `reflect`/G=3.0 beats its p95 by $0.08 on a tight band and is still
−$0.33 per trade. This is ADDENDUM 2's result — the drift is real and 4–8× too small — reproduced
on a seventh construction with a different target, a different exit frame and both lenses. The
sign gate makes the comparison empty for booking purposes ("beats the control is empty below
zero"), and it is strong evidence the underlying effect is not an artefact.

Cell A (`cross2`) is **inside the band on every rung of both targets** — consistent with it being
the classifier that selects continuation.

## 4. The increment: what each change was worth, and it is not additive

Cell C, at the principal's own G = 3.0:

| step | NET $/trade | book Sh_n | delta |
|---|---:|---:|---:|
| start: level target, frozen exits | −5.16 | −2.76 | |
| + target at the band edge | −2.87 | −1.17 | **+2.29** |
| + target at the mirror instead | −3.66 | −1.43 | −0.80 |
| + drift-following exits = **PRIMARY** | −1.66 | −0.65 | **+2.01** |

**+3.50 in total, from −5.16 to −1.66 — the principal's two changes remove about two-thirds of the
loss.** Both are real improvements to the construction and both should be kept.

**They are not cleanly additive.** Drift is worth +2.00 on the mirror target but only +0.31 on the
band edge (−2.87 → −2.56); and the mirror is *worse* than the band edge frozen (−3.66 vs −2.87)
while *better* under drift (−1.66 vs −2.56). On n = 109, with the null p95 at +$8.84 gross, that
interaction is not distinguishable from noise and must not be read as structure.

## 5. Disposition

1. **The combination is tested and does not clear its null.** No promotion, no component line.
2. **`traverse` cannot be tested on this fixture.** n = 109 over 147 sessions gives a null whose
   p95 net Sharpe is +0.81. This is now a measured fact, not a judgement, and it closes the
   question of whether more in-sample cells could resolve it: they cannot. **Any further work on
   `traverse` requires more data — the multi-year 5-minute fixture — not more variants.**
3. **Keep both of the principal's changes** (opposite-extreme target, drift-following exits) as
   the construction's settings, on the increment in §4, and do not tune either: the interior
   optimum's location is unstable across cells and the interaction is inside the noise.
4. **Cell B's repeated p95 exceedances are the strongest evidence yet that the ~0.04σ drift is
   real**, across a seventh construction and both lenses — and every one of them is net-negative.
5. Unchanged: cost binds, $3.00 of ~$4.66 being commission; the axis is not closed; the reserved
   slice is not spent, and remains the wrong instrument for a sub-cost effect.

**One method note worth carrying.** `classify2` does not depend on target, frame, stop or τ, so it
is called once per session and all 30 variants resolve off it — 1 pass instead of 30, which is what
made nulls on the whole grid affordable (60 shuffled passes rather than 1,800). Self-test 1 asserts
the single-classify path is **bit-identical** to per-variant calls on both a Gaussian and a
tie-heavy input.
