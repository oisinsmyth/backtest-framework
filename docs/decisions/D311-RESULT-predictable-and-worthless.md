# D311 RESULT — the λ path is predictable, and predicting it is worth nothing

**Status:** RESULT. Pre-registered at `0408d92`, runner committed before this
file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Stage 1 — Q2 confirmed, and the study closes here

Best fixed λ is `N_eff = 2` at **+4.37 bp/bar**. The oracle, transitions charged
and solved exactly by Viterbi:

| f | uncharged | **charged** | transitions | null p50 | null p95 | **obs gain** | **p** |
|--:|--:|--:|--:|--:|--:|--:|--:|
| 21 | +46.76 | +45.71 | 1.03 | +55.82 | +69.58 | +41.34 | 0.920 |
| 63 | +33.61 | +33.27 | 0.33 | +36.98 | +52.11 | +28.90 | 0.697 |
| 126 | +26.97 | +26.77 | 0.20 | +28.28 | +44.31 | +22.40 | 0.561 |
| 252 | +14.22 | +14.13 | 0.09 | +14.15 | +26.41 | +9.76 | 0.503 |

**Pure noise reproduces 100% to 124% of the observed gain**, at every horizon:

```
f=21    observed +41.34    null median +51.45    124% is noise
f=63    observed +28.90    null median +32.61    113% is noise
f=126   observed +22.40    null median +23.91    107% is noise
f=252   observed  +9.76    null median  +9.78    100% is noise
```

**At f=252 the observed gain and the null's median agree to two decimal places.**

**Q2 confirmed. The pre-registered stop condition fires and the study closes.**
The continuous parameterisation does not change what D308c found for the
discrete case, and the Jensen-gap argument carried over exactly as expected.

## 2. Q3 confirmed — the one thing this construction genuinely improved

**Transitions cost 2.5% of the uncharged gain at f=21** (1.05 of 42.39), against
D308's 4.9% for discrete corner jumps, and **0.6% at f=252**. Predicted under
20%.

Moving concentration continuously is about **twice as cheap** as switching
between discrete widths — `N_eff` 2 → 2.5 costs 5.4 bp where 2 → 25 costs 48.0.

**That advantage is real and it is worth nothing here**, because it is a cheaper
route to a ceiling that does not exist.

## 3. Stage 2 — Q4 FALSIFIED, and this is the interesting part

I predicted lag-1 autocorrelation under 0.20 at f=63. It is **0.224**, against a
shuffled **−0.024**.

| f | **lag-1 ρ** | shuffled | mean \|Δ log N_eff\| | shuffled |
|--:|--:|--:|--:|--:|
| 21 | **+0.163** | −0.017 | **1.059** | 1.247 |
| 63 | **+0.224** | −0.024 | **1.010** | 1.248 |
| 126 | −0.031 | −0.022 | 1.256 | 1.240 |
| 252 | −0.181 | −0.078 | 1.215 | 1.205 |

**There is genuine persistence in the optimal concentration path at 21 and 63
bars.** The path moves materially less than its own shuffle (1.010 against 1.248
at f=63) and autocorrelates where the shuffle does not.

**And this is a real difference from D308**, where the discrete width path was
*anti*-persistent at the decision frequency that mattered — 0.93 and 0.95 of its
own shuffle. Smoothing the parameter did make its optimum better behaved.

### But persistence without a ceiling is worth nothing

**Following λ\*(t) with perfect foresight earns only what noise earns.** So a
conditioner that tracked it perfectly would earn the same. The path is
predictable *and* worthless — which is a different failure from D308's, where it
was unpredictable and worthless, and a more interesting one.

**Stage 3 does not run**, per the stop condition. The four declared conditioners
are not measured.

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | uncharged oracle beats best fixed λ by > 30 bp at f=21 | **CONFIRMED** — +42.39. A harness check |
| **Q2** | **charged gain below the null median at every f** *(against)* | **CONFIRMED** — 100–124% of it is noise |
| **Q3** | transitions under 20% of the uncharged gain at f=21 | **CONFIRMED** — 2.5%, about half D308's discrete cost |
| **Q4** | lag-1 ρ under 0.20 at f=63 *(against)* | **FALSIFIED** — 0.224 against a shuffled −0.024 |
| **Q5** | the 15-level grid gives a larger raw ceiling than D308's 7 | **NOT EVALUABLE** — the two studies' baselines differ (+4.37 here against +11.20 there), so the gains are not comparable across books. My own prediction was ill-posed |
| **Q6** | no conditioner survives BH *(against)* | **NOT RUN** |
| **Q7** | dispersion is the strongest conditioner | **NOT RUN** |
| **Q8** | the Sharpe path is more persistent than the net path | **NOT RUN** — the study closed on Q2 before the Sharpe oracle was needed. D308 predicted this too and also never reached it |

## 5. What this adds

**Three studies have now tested a time-varying concentration** — D299's ladder,
D308's discrete width, and this — and all three closed. **This one closed on the
null it was designed around**, with the null inside Stage 1 rather than added
afterwards, which is the process fix D308's correction called for and it worked
as intended.

**The genuinely new finding is that smoothing the parameter fixed the path's
behaviour without fixing the economics.** D308's discrete optimum jumped between
corners anti-persistently; D311's continuous optimum drifts with real
autocorrelation. That is exactly what the smooth parameterisation was supposed to
buy, and it turns out not to be the binding constraint.

## Stop

**Time-varying concentration is closed in both its discrete and continuous
forms.** The static answer stands — `N_eff = 2` on net, `N_eff = 10` on Sharpe,
from D310.

**The entry signal remains the only untested surface of any size**, frozen since
D293.

## Files

`data/d311_adaptive_lambda.json` · `scripts/run_d311_adaptive_lambda.py`
