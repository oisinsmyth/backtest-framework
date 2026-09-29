# D684 SIZING — NO-GO: the long-gamma fade earns $0.2–0.3 a trade against an $8.84 bar at every horizon; D683's 5-minute gradient does not survive a same-day volatility control; the only effect with money in it is the mirror image, short-gamma continuation at 60 minutes (post hoc)

*2026-09-29. In-sample on D688's panel (1,989 sessions, 2016-01-05 → 2023-12-29). A go/no-go for a
pre-registration, not a verdict; no slice spent. The principal: "I'll go with your recommendation", which was to size
the long-gamma reversion before pre-registering it.*
- **The script** `scripts/size_d684_gamma_reversion.py` was committed before its run (`5a6e3ba2`), with its statistics
  and the GO rule in its docstring. It ran once, in 115 s. Output: `data/d684_gamma_reversion_sizing.json`
  (statistics only, no per-date GEX).
- **D688's β_G reproduced exactly.**

## The answer in one line

**NO-GO under the declared rule.**
- **The fade fails at every horizon.** On long-gamma days its best gross is $0.26 a trade (30 minutes, t 1.1) and
  $0.79 at its best threshold (60 minutes, 58 trades a year, t 0.3), against the $8.84 bar. No long-gamma fade cell
  clears even one MES round trip ($4.42).
- **D683 needs a correction.** Its 5-minute reversion gradient mostly disappears once the same-day volatility up to the
  decision is controlled: c = −0.0065, t −0.62, the 31st percentile of the rotation null.
- **What survives is the other half.** Short-gamma days continue at 15–60 minutes, and at 60 minutes that is +$3.77 a
  MES trade (t 2.9, 379 a year). It is post hoc (§4).

## 1. S1 — the reversion slope of the next h minutes on the last h minutes (day-clustered)

| h | all days | long gamma | short gamma | by G_SUM quintile, 0 (most short) → 4 |
|---:|---|---|---|---|
| 5 | −0.015 (t −2.0) | −0.024 (t −4.1) | −0.010 (t −0.9) | −0.004, −0.021, −0.025, −0.028, −0.039 |
| 15 | +0.011 (t 1.3) | −0.010 (t −1.0) | +0.024 (t 2.0) | +0.022, +0.004, +0.010, +0.005, −0.033 |
| 30 | −0.008 (t −0.5) | −0.009 (t −0.6) | −0.008 (t −0.3) | −0.029, +0.035, +0.003, −0.018, −0.021 |
| 60 | +0.016 (t 0.9) | +0.012 (t 0.6) | +0.019 (t 0.7) | +0.009, +0.038, +0.039, −0.042, +0.002 |

**The monotone 5-minute gradient D683 reported reproduces.** It does not persist to slower bars: at 30 and 60 minutes,
long-gamma days are indistinguishable from a random walk.

## 2. S2 — the gradient with the volatility confound controlled (the check D683 did not run)

`f = a + b·m + c·m·LG + d·m·log rv_t + e·m·log σ_d² + …`, where rv_t is the day's realised variance up to the decision
(known at t). Day-clustered t; enumerated day-rotation null of LG (1,970 offsets).

| h | c (m × long gamma) | t | rotation percentile (p05) | c on G_SUM $bn, t, percentile |
|---:|---:|---:|---|---|
| 5 | −0.0065 | −0.62 | 0.312 (−0.025) | −0.0010, −1.07, 0.130 |
| 15 | −0.0293 | −1.70 | 0.054 (−0.030) | −0.0010, −0.75, 0.194 |
| 30 | **−0.0603** | **−2.26** | **0.017** (−0.048) | −0.0041, −1.96, 0.011 |
| 60 | −0.0429 | −1.27 | 0.097 (−0.054) | −0.0033, −1.29, 0.057 |

**The double sort** (the slope b within same-day volatility terciles, long against short gamma):
- **5 minutes:** −0.026/−0.032, −0.021/−0.014, −0.025/−0.010. Gamma adds little once the level is fixed.
- **30 minutes:** +0.006/+0.109, −0.002/+0.057, −0.016/−0.013.
- **60 minutes:** −0.004/+0.091, +0.006/+0.089, +0.015/+0.012.

**At 30 and 60 minutes the gradient is real, but it comes from the short-gamma side.** Short-gamma days in the low- and
mid-volatility terciles CONTINUE (+0.06 to +0.11); long-gamma days sit at zero.

## 3. S3 — the fade in money (1 MES, $4.42 a round trip; the declared object)

**Mean gross a trade on long-gamma days, $, with the day-clustered t:**

| h | k = 0 | 0.5 | 1.0 | 1.5 | 2.0 |
|---:|---|---|---|---|---|
| 5 | +0.22 (5.5), 12,417/yr | +0.31 (4.9) | +0.30 (2.5) | +0.29 (1.4) | +0.50 (1.5), 421/yr |
| 15 | +0.18 (1.7), 4,181/yr | +0.04 (0.2) | −0.08 (−0.2) | −0.37 (−0.6) | −1.31 (−1.5), 124/yr |
| 30 | +0.26 (1.1), 2,041/yr | +0.02 (0.1) | −0.58 (−0.8) | −0.47 (−0.4) | −1.21 (−0.7), 63/yr |
| 60 | −0.15 (−0.3), 858/yr | −0.20 (−0.3) | +0.16 (0.1) | +0.79 (0.3) | −1.12 (−0.3), 28/yr |

- **The bar was $8.84, and no cell comes within a factor of 10.**
- **The 5-minute fade is statistically real** (t 5.5) and worth $0.22 a trade: a twentieth of one round trip.
- **Full ES does not rescue it.** Its cost per bp is 0.44× MES's, but the net per trade is −$14 to −$32 in every cell.

**GO cells: none. The decision is NO-GO.** Under the declared rule, gamma goes only into the expected-profit filter's
size term.

## 4. The mirror image: short-gamma continuation (post hoc; these were the fade's control cells)

The fade loses money on short-gamma days, so the opposite trade, following the last h minutes, earns:

| h | k | trades/yr | gross/trade, MES | t | gross, bp | median gross, MES | net MES | net full ES |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 15 | 0 | 1,868 | +$0.71 | 2.5 | +0.38 | $0.00 | −$3.71 | −$12.1 |
| 30 | 0 | 900 | +$1.13 | 1.7 | +0.62 | +$1.25 | −$3.29 | −$7.9 |
| **60** | **0** | **379** | **+$3.77** | **2.9** | **+2.12** | **+$3.75** | **−$0.65** | **+$18.5** |
| 60 | 0.5 | 210 | +$4.60 | 2.6 | +2.60 | +$5.00 | +$0.18 | +$26.8 |
| 60 | 1.0 | 92 | +$4.70 | 1.8 | +2.69 | +$8.75 | +$0.28 | +$27.8 |

**Why it is worth writing down.**
- **It is the mechanism's other half.** Short-gamma dealers hedge with the move.
- **It is coherent.** It grows with the horizon (+0.4 → +0.6 → +2.1 bp).
- **The median carries it, not the tail:** the median equals the mean at 60 minutes, and 54% of trades win.
- **It is about one MES round trip gross.** At full ES, where the cost per bp is 0.44× MES's, it is about twice the
  round trip.

**Why it is not a finding yet.**
- **Selection:** it was read after seeing 15 control cells, and the declared object was the fade.
- **Concentration is unmeasured.** Short-gamma days cluster in 2018, 2020 and 2022, and D683 showed the close
  effect was entirely February–April 2020. No by-year or ex-crash split has been run.
- **The price-path record is against it.** Momentum has failed unconditionally at every horizon tested on futures, so
  only a short-gamma condition could rescue it.
- **Full ES is a different size class.** It sits against the prop account's drawdown geometry; the memory "one micro
  has grown into the prop barrier" applies.
- **The confirmation premise is unknown.** SPX GEX called one short-gamma day in 2024-01 → 2025-02. G_SUM's
  short-gamma count there depends on the ES book, which has not been read for 2024+.

## 5. The correction to D683

D683 §2 read the 5-minute autocorrelation gradient (below every rotation) as continuous hedging along the path. It
controlled only trailing σ, and flagged the same-day volatility confound as the one check not run.

This record ran it. **With the day's realised variance up to the decision as a control, the 5-minute gamma gradient is
not distinguishable from zero** (t −0.62, the 31st percentile), and the double sort shows little gamma effect within
volatility terciles.

**What stands and what falls:**
- **Stands:** D683's rejection of "too little impact" (§1), the realised-variance result (gamma predicts the size of
  the day), and the crash concentration of the close slope.
- **Falls:** "long gamma deepens the path's reversion". At 5 minutes that is mostly the volatility level. At 30–60
  minutes the gamma effect beyond volatility is short-gamma continuation.

D683's headline therefore narrows. **The hedging does not land at the close. What gamma demonstrably changes is how
much the day moves, and on short-gamma days, whether the last hour keeps going.**

## 6. What this decides, for the principal

1. **The long-gamma fade is dead** at every bar from 5 to 60 minutes, on MES and on full ES.
2. **Gamma's confirmed role is size.** It halves or doubles the day's variance: t ≈ 12 in D683, and D665's |move|
   results. That belongs in the expected-profit filter's magnitude term, as recommended.
3. **One lead, the principal's call: short-gamma continuation at 60 minutes, on full ES.** Before any
   pre-registration it needs two cheap checks:
   - **(a) Concentration:** by year and without February–April 2020.
   - **(b) The confirmation premise:** the short-gamma count of G_SUM in 2024-01 → 2025-02 and the vault. That means
     reading the ES options book's OI for those dates, no returns. If there are too few short-gamma days to power a
     test, the lead is unconfirmable, whatever (a) shows.

## CLOSED by the principal, 2026-09-29

"Close them, renumber and merge, then go after short-gamma days with volatility is controlled."
- **The long-gamma fade is closed.**
- **The short-gamma lead of §4 is taken up next** under its own number, starting with §6's two checks, with
  volatility controlled.
