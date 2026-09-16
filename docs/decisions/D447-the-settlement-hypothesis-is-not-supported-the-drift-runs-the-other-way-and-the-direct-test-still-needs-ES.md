# D447 — the settlement hypothesis is not supported: US drift runs the OTHER way as the lag shortens, the placebo is clean, and the direct test still needs ES

**MEASUREMENT record. No hurdle is claimed and no candidate is scored.** **Runner:**
`scripts/d447_settlement_regimes.py`. **Evidence:** `data/d447_settlement_regimes.json` (49 rows).
**Predictions were written into the runner before it was run; two of three hold.**

---

## THE ANSWER

> **The US natural experiment does NOT support the settlement mechanism. The drift is monotone in
> the settlement lag — in the DIRECTION OPPOSITE to the prediction — on both readings, and the
> slope is not significant either way.**

**For the prop track that is the useful half:** the story that C1's +9.04%/yr is a T+n artefact
with no counterpart in a T+0 future **has no support from US data.** **The kill-risk on D440's
input is reduced. It is not removed, because this is not the direct test.**

## 1. What was tested, and why it needed no futures data

**The claim, external, from prop-firm research lane 19:** China's natural experiment — same
underlying, same days — gives **opposite signs** on the overnight return, **T+1 cash −0.073%
(t −4.03) against T+0 futures +0.055% (t +3.19)** — supporting *"the overnight drift is a property
of the settlement rule, not of the passage of time."*

**The US changed its settlement rule twice inside this fixture's window**, and **both dates are the
ones the corporate-action research independently flagged as declared ex-dividend holes**, which
corroborates them:

| regime | lag | from | to | session pairs |
|---|---:|---|---|---:|
| **T+3** | 3 | 2010-01-04 | 2017-09-01 | 7,661 |
| **T+2** | 2 | 2017-09-05 | 2024-05-24 | 6,735 |
| **T+1** | 1 | 2024-05-28 | 2026-08-25 | 2,252 |

**This is a WITHIN-instrument comparison** — same market, same names, same construction, only the
rule changes — where the China evidence is **cross-instrument.** Weaker in one way (a time series
carries era confounds), stronger in another (nothing but the rule moves).

## 2. The result, and it is the wrong way round

**Annualised, ex-2020** (2020 sits inside T+2 and is reported both ways):

| window | T+3 | T+2 | **T+1** |
|---|---:|---:|---:|
| post | 2.66% | 5.87% | 7.47% |
| **untraded** | **22.27%** | **20.68%** | **24.59%** |
| pre | 0.80% | 2.03% | **20.42%** |
| *rth — PLACEBO* | *18.81%* | *2.85%* | *14.40%* |
| **overnight** | **25.72%** | **28.58%** | **52.48%** |

> **The settlement hypothesis predicts T+3 > T+2 > T+1. The observed ordering is exactly
> REVERSED**, and the regression of the per-session return on the settlement lag gives
> **−1.233 bp per day of lag, t −1.69** — shorter settlement, *more* drift.

**But the slope is not significant at 2 SE**, so this does not establish a reversed effect either.
**What it does is reject the predicted direction.**

### The placebo is clean, which is the part that makes the test worth anything

**RTH shows no monotone pattern and an opposite-signed, insignificant slope: +0.466 bp, t +0.46.**
So the overnight pattern is **specific to the overnight window** and is not a generic era drift
showing up everywhere. **That was my X2 prediction and it was wrong in the informative direction.**

### The one window that should have moved, did not

**If a settlement lag drove the drift, the `untraded` window — the pure overnight carry, and the
window D259 measured as 66% of the total — is where it would live.** It reads **22.27% / 20.68% /
24.59%**. **It barely moves across sixteen years and two rule changes.**

## 3. The confound I expected to explain it, and what happened when I tested it

**73.4% of the T+1-minus-T+3 gap sits in the `pre` window** (+19.62 of +26.75 points), and that is
exactly the window whose **measurement coverage** changed most — D259 measured the share of sessions
printing a literal 04:00 bar at **22.1% for DIA in 2010–2019 against 89.8% in 2021–2026.** A window
observed more often in later years carries more return in later years for reasons that have nothing
to do with any rule.

**So the coverage-matched reading was run** — `strict`, keeping only sessions with a literal 19:45
*and* a literal 04:00 print:

| window | T+3 | T+2 | T+1 |
|---|---:|---:|---:|
| overnight | **12.73%** | 24.28% | **53.09%** |
| *rth* | *15.21%* | *5.01%* | *12.60%* |
| n | 3,504 | 4,769 | 2,223 |

> **It does not rescue the coverage story. The wrong-direction gap gets LARGER, not smaller** —
> +40.4 points against +26.75. **And T+3's overnight halves, 25.72% → 12.73%, on a subsample that
> keeps 46% of its pairs against 99% of T+1's.**

**Both readings stand and they disagree about T+3's level by a factor of two. That disagreement is
itself a finding about how fragile this decomposition is**, and it is the reason §4 does not claim a
reversed effect.

## 4. What this settles and what it does not

- **It rejects the predicted direction.** On US data the drift does not shrink as settlement
  shortens; the point estimates say the opposite on both readings.
- **It does not establish the reverse.** `t` −1.68 and −1.69 are below 2 SE, and the two readings
  disagree on levels.
- **IT IS NOT THE DIRECT TEST.** The falsifier the leads doc named is **ES beside SPY, same days** —
  a cross-instrument comparison like China's. **That is still owed.**
- **It reduces the kill-risk on D440's input without removing it.** The mechanism that would have
  voided C1's entire series has no US support; the instrument question remains open.

## 5. Why the direct test was not run, stated plainly

**The futures acquisition has `ohlcv-1m` on disk for 2010-06-06 → 2022-08-17** — three chunks,
7.3 GB — **and the 2022-08-17 → 2026-09-11 chunk is still `submitted`.** But it is **`ALL_SYMBOLS`
raw DBN under `temp/`, with no continuous series built**, and the manifest says so itself:
*"Acquisition only — no fixture was built and no study was run."*

**Building a continuous ES series from it is the roll problem** that
[`docs/research/prop-firm-leads/02`](../research/prop-firm-leads/02-data-acquisition-prompt.md) §3 flagged as the
gate that matters most — *a synthetic roll gap scored as an adverse excursion that never happened* —
and **`temp/` is deletable any time, unasked, while a live job is still writing into it.** **That
work belongs to the acquisition, not to this record.**

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| **X1** | the drift is **not cleanly monotone** in the settlement lag; the experiment fails to support the mechanism | **CONFIRMED, and more strongly than written** — it *is* monotone, in the opposite direction, on both readings |
| **X2** | whatever pattern appears in overnight **also appears in RTH**, making it era rather than settlement | **WRONG** — the placebo is clean: no monotone pattern, opposite-signed slope, t +0.46. **The effect is overnight-specific** |
| **X3** | T+2 vs T+1 **unresolved at 2 SE** | **CONFIRMED** — the lag slope is t −1.68 / −1.69 |

**X2 is the useful miss.** I expected to find an era artefact and expected the placebo to convict
it. The placebo exonerated it instead, which makes the wrong-direction result harder to dismiss and
is the reason §4 stops at *"rejects the predicted direction"* rather than *"finds nothing."*
