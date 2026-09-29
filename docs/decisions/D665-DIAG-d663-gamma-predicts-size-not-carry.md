# D665 — DIAG of D663: the gamma measures work, and they predict how FAR the market moves after the break, not which way it carries; the break trade loses about 3.2 bp net on both roots, and a gamma filter would need a slope 9–45× the observed one to pay

*2026-09-29. The principal: "I would like a diagnostic on this".*
- *Post hoc on D663 (`64fc0bb`), in-sample only through D663's own sealed functions. It changes no verdict.*
- *Script: `scripts/diag_d663.py`. Output: `data/diag_d663.json` (statistics only, licence-guarded).*
- ***Dealer gamma (GEX): SqueezeMetrics.***

## A. Mechanics: do the inputs measure what they claim?

**A1. The two ES gamma measures agree on level, and not on which days are short.**

| | value |
|---|---:|
| correlation of levels / ranks, SPX GEX vs the carried ES book | 0.60 / 0.77 |
| sign agreement | 69% |
| short-gamma share: SPX GEX / carried ES book | **11% / 42%** |

The SPX figure matches the literature (short on about 10% of days, D661 C1). The carried ES book's naive sign calls
dealers short four times as often. So **"short gamma" is not the same regime in D662 and D663**.

**A2. The measures are valid, as predictors of SIZE.** Short gamma predicts a bigger move after the break, in either
direction, as the damping literature says it should:

| root, measure | \|F\| on g (t) | \|F\| by g quintile, long → short (bp) | beyond trailing σ₂₀ (t of g) |
|---|---:|---|---:|
| ES, SPX GEX | +4.24 (8.7) | 13.6, 15.0, 21.0, 26.1, **36.9** | **5.9** |
| ES, carried book | +2.38 (11.8) | 12.3, 16.3, 23.1, 30.6, 30.5 | **7.2** |
| NQ, SPX GEX | +1.40 (11.0) | 21.0, 23.9, 27.8, 37.3, **49.6** | **4.8** |
| NQ, own book | +14.7 (8.1) | 19.3, 27.9, 32.5, 40.2, 38.7 | **5.9** |

- The expansion after 10:00, over the opening range, also rises with g (t 1.1–3.6).
- **Gamma's size information is not just volatility persistence.** With the prior 20 sessions' σ in the same
  regression, g keeps t 4.8–7.2.
- **This is the multiplier the principal described, measured.** It amplifies moves, but both ways: continuation and
  reversal alike. That is exactly why its carry test (D663) is null while its size test is strong.

**A3. The shock tracks the move.** The TICK window mean correlates with the root's own move from the open to the
entry: ES 0.47, NQ 0.35. Its sign agrees with the break on average (mean signed shock +0.58 ES, +0.44 NQ). So H2's
null is not a broken shock.

## B. Statistical review

**B1. ES, both measures in one regression** (2,081 breaks):
- SPX GEX: −0.08 (t −0.17);
- **carried ES book: +0.51 (t 2.27)**.

D662's post hoc slope survives controlling for SPX gamma. So what it measured is specific to the ES options book, not
the market's dealer gamma. It stays post hoc and unpromotable:
- it was picked from ten statistics;
- the two books disagree on the short regime (A1);
- D663's pre-registered measure is the SPX book, and there it is null.

**B2. The post-0DTE era alone** (after 2022-05-16, about 650 breaks per root, with its own purged rotation):

| root, measure | slope (t) | rank |
|---|---:|---:|
| ES, SPX | +1.16 (0.97) | 0.84 |
| ES, carried | +0.45 (1.26) | 0.88 |
| NQ, own | −1.19 (−0.31) | 0.35 |
| NQ, SPX | +0.14 (0.14) | 0.55 |

D663's era hint (+1.16 after 2022) is inside its null.

**B3. The tally of break × gamma cells tested.**
- D662: 2 pre-registered, 1 post hoc. D663: 4 pre-registered, 2 controls.
- None is supported.
- The only t above 2 is D662's post hoc cell (B1).

**B4. Power:** see C3. The observed slopes sit far below what an edge needs, so a larger sample would not rescue them.

## C. The edge

**C1. The break trade itself** (60-minute hold, no stop, at the micro round trip):

| root | trades | gross per trade | net per trade (t) | cost |
|---|---:|---:|---:|---:|
| ES | 2,138 | +0.31 bp | **−3.19 (−4.4)** | 3.37 |
| NQ | 2,118 | −0.66 | **−3.27 (−3.4)** | 2.09 |

**C2. Net by g quintile** (long → short gamma):

| root, measure | net per trade by quintile (bp) | top quintile net (t) |
|---|---|---:|
| ES, SPX | −4.19, −4.76, −2.86, −2.17, −1.99 | −1.99 (−0.82) |
| ES, carried | −5.30, −4.54, −2.59, −1.06, **−0.71** | −0.71 (−0.35) |
| NQ, SPX | −5.60, −3.49, −0.55, −0.70, −5.97 | −5.97 (−1.87) |
| NQ, own | −2.24, −2.45, +1.10, −5.77, −4.50 | −4.50 (−1.75) |

The ES carried book orders monotonically, which is D662's post hoc hint. **Even its best quintile loses.** No gamma
quintile of either root pays the micro round trip.

**C3. The slope an edge would need** for the top quintile to clear cost plus the vault's 80%-power MDE:

| root, measure | needed | observed | ratio |
|---|---:|---:|---:|
| ES, SPX | 10.2 | 0.22 | **45×** |
| ES, carried | 4.6 | 0.48 | **9.5×** |
| NQ, SPX | 3.8 | −0.08 | wrong sign |
| NQ, own | 39 | −1.54 | wrong sign |

## What it means

1. **Nothing is broken.**
   - GEX is lagged correctly (asserted);
   - the shock tracks the move (A3);
   - the gamma measures carry real information, about size (A2).
2. **Dealer gamma is a real, strong, volatility-independent predictor of how far the market travels after the
   break.** It is not a predictor of direction or carry. This is the principal's multiplier, measured: it multiplies
   whichever way the market is already going, reversals included.
3. **D661's ceiling applies.** Even perfect size knowledge gives a breakout about 34% vault power. The break trade
   loses about 3.2 bp net on both roots, and no gamma quintile rescues it. The carry edge would need 9–45× the
   observed slope.
4. **Where gamma's size information could be used**, which is not this construction and would need its own
   pre-registration:
   - the expected-profit filter's magnitude term (every strategy carries one);
   - stop and target distances;
   - risk sizing across components.
