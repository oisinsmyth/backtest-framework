# Cost — what trading actually costs, and what that rules out

[← consolidated index](../00-INDEX.md)

**Cost was the programme's assumed binding constraint for five rounds. Round 6 showed it is not**,
and the correction was to a premise the commissioner wrote into the prompt himself. This folder holds
the estimator, the level, the screens and the construction artefacts, in that order.

| | one line |
|---|---|
| **[01 · spread estimation](01-spread-estimation.md)** | the number is `33.8 / 31.7 / 14.2` depending on convention, and the estimator has **three separate defects** |
| **[02 · what anomalies pay](02-what-anomalies-pay.md)** | **cost is not what binds the survivors** — the gross edge is gone, what remains is mostly luck, and it lives in the short leg |
| **[03 · the price floor](03-price-floor-and-screens.md)** | the `$5` floor is right, and the reason the repo states for it is the weaker of the two |
| **[04 · equal-weight bias](04-equal-weight-bias.md)** | paid **per rebalance, not per bar** — and inverting it reproduces our spread to 2% |
| **[05 · borrow and financing](05-borrow-and-financing.md)** | borrow is a rounding error; **the short-proceeds rate gradient is the size constraint** |

---

## The three numbers to hold in mind

| | |
|---|---|
| **33.8 bp/side** | D285's held mean — **a superseded statistic**, see [vs repo R1](../conflicts/02-versus-repo-measurements.md), and the number the whole research tree reasons from |
| **34 bp/side** | what **204 published anomaly implementations actually pay** post-2005. **The same number.** |
| **1.85 bp/side** | the `shorts/` stream's bar, on **57 liquid ETFs**. **A different fixture. Never carry it across.** |

## The two open items that would move the most

1. **Recompute D285's 33.8 under EDGE.** Closed form, same OHLC inputs, published code. *"It sets the
   SIGN of every cost conclusion downstream."* → [01](01-spread-estimation.md)
2. **Does the weight array get recomputed from the current bar's close for names already held, or
   only at entry?** One property of the code; it decides whether a multi-bar book carries the large
   equal-weight bias or `1/H` of it. → [04](04-equal-weight-bias.md)

## The standing rule this folder does not replace

`CLAUDE.md`: **estimate the spread of the names HELD rather than trusting a fee assumption** — D285
missed a guessed 15 bp/side bar by 0.65 and the held names measured 33.8. **That rule is unaffected
by everything above.** What changed is which *convention* of the estimator is charged, and whether a
high cost is a reason to reject a lane.
