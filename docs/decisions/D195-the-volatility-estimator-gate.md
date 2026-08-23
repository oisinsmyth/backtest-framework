# D195 — Does finer data give a better ESTIMATE? The volatility gate, and the sizing study it may or may not unlock

**Status:** Pre-registered — written and committed BEFORE the gate runs
**Date:** 2026-08-23
**Category:** Validation & research integrity
**Source:** A named, unfixed defect in the final report, and the one question D160–D194 never asked

> Written and committed **before** the run, as every pre-registration in this project has
> been. Result sections are appended and nothing above them edited.

## The question this project has not asked

Twice now it has asked whether finer data gives a better **signal**. D160–D165 walked the
cost-frequency frontier and found no trend edge at any frequency. D189 and D194 tested a
volume-at-price sensor on daily bars and then on exchange-native 15m volume, and closed it.

It has never asked whether finer data gives a better **estimate**. That is a different
claim with a very different prior, and there is a documented defect sitting exactly on it.
From the final report's list of gaps left deliberately unfixed:

> inverse-volatility weighting pays a book for being absent, handing the losing leg 70% of
> the risk budget precisely because it barely trades

`InverseVolatilityWeight` sizes every position off `vol_window: int = 20` — **twenty
close-to-close daily log returns**. Twenty observations. The same twenty calendar days at
15m hold **1,920**.

Realized variance converging as sampling frequency rises is among the most replicated
results in empirical finance, and 5–30 minutes is the standard sampling window: fine
enough to converge, coarse enough that microstructure noise has not taken over. 15m sits
in the middle of it.

## Why this survives the constraint that kills most 15m ideas

D163 settled the cost wall without needing any return data: a channel-breakout rule at 15m
turns over ~790×/yr and pays ~315% of capital annually in fees. Any high-turnover
directional rule at that frequency is dead before it starts.

**A sizing change is not a turnover change.** It alters how large a trade is, not how many
there are. D185 already measured the portfolio's resizing cost — 1.8×/yr turnover, 0.025
Sharpe, break-even at 972 bp. Nowhere near binding.

## Two steps, both registered now

### Step 1 — the gate (this document's run)

**Does a 20-day realized volatility computed from 15m returns predict the next 20 days'
volatility better than the 20-day close-to-close standard deviation does?**

No strategy, no costs, no trading. A forecasting comparison and nothing else.

- **Estimator A (incumbent).** Sample stdev of 20 daily close-to-close log returns ending
  at day *t* — exactly what `InverseVolatilityWeight` computes today.
- **Estimator B (candidate).** Realized volatility over the same 20 calendar days, built
  from 15m returns: for each UTC day, `RV_d = Σ r²` over that day's 15m log returns; the
  window estimate is `sqrt(mean(RV_d))`, which is per-day units and therefore directly
  comparable to A.
- **Target.** The same two constructions over the *disjoint forward* window
  `(t, t + 20 days]`.

**Both estimators are computed from the same 15m fixture**, with the daily series
resampled from it. Provider, span and calendar are held identical so the estimator is the
only thing that differs. Using the yfinance daily fixture for A would have reintroduced
provider as a confound in a study whose entire content is a like-for-like comparison.

**Two targets are reported, not one, and this is the methodological point of the design.**
The accurate target is realized vol from 15m. But B is built the same way, so if 15m
realized vol carries a systematic component — microstructure noise inflating it
consistently — both estimator and target inherit it and B's apparent skill is flattered.
So the incumbent's own basis, the daily close-to-close stdev, is scored as a second target.
**B must win on both.** A win only on the 15m target is the shared-basis artifact and will
be reported as that rather than as a result.

**Losses:** mean squared error on log volatility, and QLIKE on variance —
`σ²/σ̂² − ln(σ²/σ̂²) − 1` — which is the standard loss robust to noise in the volatility
proxy. Plus the Mincer–Zarnowitz R².

### Step 2 — the sizing study (conditional, and its bar is fixed here)

Only if step 1 passes. Swap the vol estimate feeding `InverseVolatilityWeight` from A to B
and change nothing else: same book, same entries, same exits, same walk-forward.

**Its bar, committed now while step 1's answer is unknown: the Sharpe improvement must be
at least +0.10 on both BTC and ETH.** Grounds: D185 measured the entire rebalancing-cost
machinery as worth 0.025 Sharpe, and D183's portfolio edge over its benchmark was +0.075
after costs. An improvement smaller than +0.10 is inside the noise of effects this project
has already shown it cannot resolve, and calling it a result would be D194's p = 0.008 all
over again in a different costume.

## The bar for step 1

**B must reduce forecast loss by at least 30%, on both symbols, on both targets, on both
losses.**

That number is a judgement call and is labelled as one rather than dressed up as derived.
Its grounding: 30% is the rough order the realized-variance literature reports for
intraday estimators against daily-close ones. If the improvement here is materially
smaller than the literature that motivated the idea, that gap is itself the finding — it
would mean crypto's 15m bars are noisier than the equity data those results come from, and
step 2 would be building on an estimator barely better than the one it replaces.

**Symbols.** BTCUSDT and ETHUSDT carry the gate. XEMUSDT and BTGUSDT are reported as a
secondary check, because a path tested only on majors is tested only where it works
(D140/D180) — and thin, dying instruments are exactly where a 15m estimator might degrade,
since their empty-bar rates at 1m were 25.3% and 44.7%.

## The predictions

**H1 — B beats A, and comfortably.** Predicted **TRUE**, **high** confidence.

This is the first proposal in this project with a strong *positive* prior, and that needs
saying plainly rather than being allowed to look like a discovery afterwards. If it passes
it confirms textbook statistics on a new dataset; it does not find anything. The honest
description of a pass is "the arithmetic works here too".

**H2 — the effect is smaller on XEMUSDT and BTGUSDT than on the majors.** Predicted
**TRUE**. Realized variance converges on the assumption that the sampling interval
contains trading. On instruments whose 1m bars were 25–45% empty, 15m returns carry more
zero-return staleness, which biases realized variance downward and should erode the
advantage.

**H3 — step 2 fails its +0.10 bar even though step 1 passes.** Predicted **TRUE**,
moderate confidence, and this is the prediction that matters.

A better estimate of volatility is not the same thing as a better book. Every filter and
overlay this project has tried removed good trades along with bad, and the final report's
own summary of the sizing defect — that inverse-vol weighting hands the risk budget to
whichever leg trades least — is a **structural** problem with the weighting rule, not an
accuracy problem with the input. A sharper number fed into a rule with the wrong shape
gives a sharper wrong answer.

If H1 passes and H3 also holds, the finding is that 15m data's value here is real,
measurable, and does not reach the P&L — which would be the most useful thing this line of
work could establish, and is worth stating in advance so it cannot be spun as a
disappointment afterwards.

## Multiplicity

Step 1 is 2 symbols × 2 targets × 2 losses = **8 looks** on the gate, plus 8 on the
secondary pair. Step 2, if it runs, is 2 symbols × 1 metric = 2. This is a separate
hypothesis from the terrain programme's 147 and starts its own ledger; it does not inherit
that count, and the reason is that nothing here is a claim about supply and demand.

## What a pass would and would not mean

It would mean the incumbent sizing input is measurably worse than an available
alternative. It would **not** mean the book improves, which is step 2's question and has
its own bar. Building step 2 on a passed gate is legitimate; reporting the gate as though
it were the result is not.

---

# RESULT — appended 2026-08-23, after the run. Nothing above this line was edited.

**Status: the gate FAILS. H1 falsified, H2 falsified. Step 2 does not run.**

## The numbers

Loss reduction, candidate against incumbent. Positive means the candidate forecasts
better. The bar was **≥ 30% on every cell**.

| symbol | pairs | realized/MSE | realized/QLIKE | c2c/MSE | c2c/QLIKE | worst | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| BTCUSDT | 3,026 | +18.6% | +29.9% | **+15.8%** | +27.2% | +15.8% | FAIL |
| ETHUSDT | 3,026 | +22.0% | +26.5% | **+22.7%** | +25.8% | +22.0% | FAIL |
| XEMUSDT | 1,250 | +32.8% | +55.7% | **−0.2%** | +34.6% | −0.2% | FAIL |
| BTGUSDT | 511 | +36.2% | +51.6% | **−29.6%** | +13.9% | −29.6% | FAIL |

Mincer–Zarnowitz R² on the majors, against the accurate target: BTC 0.2128 → 0.2710,
ETH 0.2145 → 0.2938.

## H1 — FALSIFIED

Predicted at **high** confidence that the candidate would beat the incumbent
*comfortably*, and called it "the first proposal in this project with a strong positive
prior".

**The direction was right on every one of the eight gate cells. The magnitude was not.**
BTC's worst cell is +15.8% against a floor of 30% — short by 14.2 points. ETH's is +22.0%,
short by 8.0.

This is the case D195 wrote down in advance:

> If the improvement here is materially smaller than the literature that motivated the
> idea, that gap is itself the finding — it would mean crypto's 15m bars are noisier than
> the equity data those results come from.

That is what happened. Intraday realized variance is a better forecaster of crypto
volatility than twenty close-to-close returns — reliably, on both majors, on both targets,
on both losses — by roughly **16–30%** rather than the 30%+ the equity literature reports.

**The honest reading is that the floor was set from the wrong reference class**, and that
I set it there before seeing anything, which is the only reason that sentence is worth
believing. A floor calibrated on equity data was applied to 24/7 crypto with no session
structure, no opening auction, and a materially different microstructure. Nothing about
the run tells us whether 30% was too strict; it tells us the effect here is smaller than
30%, and that is all a floor can ever tell you.

**What I will not do is move the floor now.** A 20% loss reduction is a real improvement
and a reader may reasonably think it worth having — the numbers are above so they can
judge. But re-deciding the threshold after seeing the result is precisely the move that
makes every subsequent number in a project unbelievable, and D194's `p = 0.008` is only
three days old.

## H2 — FALSIFIED, and the two-target design is why we know

Predicted the effect would be **smaller** on the thin, dying instruments, because 1m
empty-bar rates of 25.3% and 44.7% mean staleness biases realized variance downward.

Against the accurate target, the effect is **larger**: XEM +32.8%/+55.7%, BTG
+36.2%/+51.6% — the only cells anywhere in the run that clear the 30% bar.

Against the incumbent's own basis it goes **negative**: XEM −0.2%, BTG **−29.6%**.

| symbol | realized/MSE | c2c/MSE | divergence |
|---|---:|---:|---:|
| XEMUSDT | +32.8% | −0.2% | 33.0 points |
| BTGUSDT | +36.2% | −29.6% | **65.8 points** |

**This is the shared-basis artifact, caught by the guard built to catch it.** On a thin
instrument, 15m realized variance carries a large idiosyncratic component from stale
prices and zero-return bars. The candidate estimator and the realized target both inherit
it, so the candidate predicts *itself* extremely well — and predicts what actually happened
to close-to-close volatility **worse than the twenty-observation estimator does**.

Scored on the accurate target alone, BTGUSDT would have been the strongest result in the
run: +36% and +52%, both clearing the bar that the majors missed. It is the weakest. A
single-target design would have reported a thin dying coin as the best evidence for the
method, which is the same shape as D180 — the instruments where a result looks best being
the instruments where it is least real.

The prediction was wrong about the direction of the bias and right that thin instruments
would behave differently. That is worth separating: the mechanism was real, the sign was
not, which is now the seventh time in this project a prediction has done exactly that.

## Step 2 does not run

D195: *"Only if step 1 passes."* It did not. The sizing study is not run and its +0.10
Sharpe bar is not tested.

Worth stating plainly, because the temptation runs the other way: the candidate estimator
is genuinely better on the majors, and it would have been easy to call 16–30% "close
enough", run step 2, and report whatever came out. The gate exists so that decision is
made once, in advance, by someone who does not yet know the answer.

**H3 is therefore untested.** It predicted step 2 would fail its bar even if step 1 passed,
on the grounds that the sizing defect is structural in the weighting rule rather than an
accuracy problem with its input. That argument is untouched by this run and remains the
more likely explanation of the 70%-of-risk-budget defect — a better input does not fix a
rule with the wrong shape. Recorded as unresolved, not as supported.

## What this settles

**Finer data does give a better estimate here — measurably, consistently, and by less than
the theory that motivated the study.** Both majors improve on all four cells; the R²
of forecasting 20-day-ahead volatility rises from 0.2128 to 0.2710 on BTC and 0.2145 to
0.2938 on ETH. That is a real property of the data and it did not require any alpha to exist.

It also does not clear a bar set in advance, so nothing is built on it.

The finding with the longest reach is the thin-instrument divergence. Any future study that
validates an intraday-derived estimator against an intraday-derived target is measuring
self-consistency, and on illiquid instruments that can invert the answer by 66 points. The
second target cost one extra column of arithmetic.

## What is not settled

Whether a 16–30% better volatility forecast improves a book. That is step 2's question and
this run declines to answer it, by its own rule.

Whether a different estimator clears 30% — a jump-robust bipower variation, a two-scale
estimator correcting for microstructure noise, or a simple 5m/30m sampling sweep. None was
pre-registered, none was run, and adding one now to reach the bar would be searching for a
configuration that passes, which is the failure this project's whole apparatus exists to
prevent. If it is worth doing it is worth pre-registering as its own question.
