# D668 — STAGE 0 DESIGN: the plain break of yesterday's range sets the direction, and a walk-forward expected-profit predictor built from the open, the gap, dealer gamma and flow decides whether to take it and how big; confirmed on YM and RTY, which have never seen the construction

*2026-09-29.*
- *The principal's direction: "what if we use a plain break for direction and have all our previous results, flow,
  gamma as confluences with a profit predictor?"*
- *Their choice of target: **"Expectant profit"**. The predictor forecasts each trade's profit in basis points, not
  the probability that the break holds.*
- *It follows D667, the diagnostic of D666. To be committed alone, before any runner or any YM/RTY feature exists
  (R8).*

## 1. Why this, and what is already known

**What D666/D667 found** (in-sample 2016-01-04 → 2025-02-28), for NQ's plain break with the trailing stop:
- **+4.29 bp gross per trade (HAC t 3.57), 8 of 10 years positive, +1.69 net at 1 micro.** It holds after 0DTE
  (+5.56, t 2.18).
- On ES the same construction makes +1.20 (t 1.31).
- **The money splits on whether the break comes back to yesterday's level.** E4 gross ≈ 44 × P(hold) − 19 bp; the
  breaks that never return earn +25 bp (NQ), the rest lose −19.
- **So the prize is a predictor that sorts breaks.** Each 5 points of hold rate among the selected trades is worth
  about 2 bp.

**What counts against it, and what this design does about each:**

| D667's caveat | the answer here |
|---|---|
| post hoc: found on NQ, as D666's control, with one of four exits | the evidence comes from **YM and RTY**, which have never been run through this construction; ES and NQ are run identically but reported as development only |
| the drift is uncontrolled | the gate's null is a **same-clock, same-side-mix random entry on every session** (§5) |
| the confluences showed no incremental value one at a time (t 1.3–1.4) | they are not filters here; they enter one small walk-forward model, and the predictor must **discriminate out of sample** (β_disc, §4) to count |
| net is below one extra tick; 29% of fills are at the open | a **slippage ladder** on every fill, and on the open fills separately (§6) |
| vault power about 30–37% on NQ | the vault is not read here; YM and RTY carry the evidence (§7) |

**Other things already known:**
- **The ledger's K8** (long the NQ day session after a down day, PROVISIONAL) shares NQ's clock and the long side.
  Its ρ is part of the component line (§6).
- **K4** (YM last-30-min momentum) is a different clock and a different signal. No trend or channel study has read
  YM or RTY through a break of yesterday's range.

## 2. The direction: D666's plain break, unchanged

**Per root r ∈ {YM, RTY} (evidence) and {ES, NQ} (development), day session 09:30–16:00, one-minute bars from D462's
`fut_{r}_rth_1m`:**
- **Levels, known before the open:** L⁺ = the prior session's RTH high, L⁻ = its RTH low; A = D644's `atr20`.
- **Entry:** a buy stop at L⁺ + 0.25 A and a sell stop at L⁻ − 0.25 A, live from the 09:30 bar. The first to fill is
  the day's only trade. No entry after 15:29.
- **Fill:** at the stop, or at the bar's open if it opens through the stop, **plus one tick**.
- **Exit, primary:** **E4**, the trailing stop: initial stop at L, then trailing 0.25 A behind the best price since
  entry, never loosening; else flat at the 15:59 close. Exits are checked from the bar after the entry; stops fill at
  the stop, or the open through it, minus one tick.
- **Exit, secondary (reported, never gated):** E2, the stop at L and hold to the close.

**Nothing in the setup changes from D666.** The runner must reproduce D666's ES and NQ plain-break E4 and E2 gross
means exactly before it computes anything else.

**Cost:** the micro round trip in dollars, per trade, from `data/futures_costs.json`: $3 commission + the micro's
measured crossing (MES 1.112, MNQ 2.270, MYM 2.268, M2K 1.934 ticks) + one tick of stop slippage, divided by the micro's
notional at the entry. At recent prices that is about 2.6 bp (MYM) and 4–6 bp (M2K). The micros launched in May 2019;
before that the same micro cost is applied, as in every opening study.

## 3. The features, each known at the entry bar and signed by the trade's direction D

**The principal asked for "all our previous results, flow, gamma". The list is capped at nine, each with a stated
reason it could carry "will this break hold".** More would fit noise at about 150 trades a year.

| # | feature | definition | why it could carry the hold |
|---|---|---|---|
| f1, f2 | **open class** | dummies for gap-inside (the open beyond L, inside the stop) and gap-through (beyond the stop); no-gap is the base | D667 §2: the classes differ in how often price returns to L (40–55%) |
| f3 | **overnight gap** | D × (open / prior close − 1) / (A / prior close) | an overnight move the break agrees with has already been accepted |
| f4 | **dealer gamma** | 1 if dealers are short gamma, from the prior row: ES SPX GEX (SqueezeMetrics); NQ its own options book G; **YM and RTY SPX GEX** (no own book on disk) | D665: short gamma predicts a bigger move, and a trailing stop is paid by size |
| f5 | **large-lot futures flow** | D × A7 at the latest checkpoint (09:45 / 10:00 / 10:30 / 11:00) at or before the entry, the root's own; 0 before 09:45 | informed size in the break's direction. It pointed the wrong way on NQ in D667; **coefficient signs are free** |
| f6 | **cash breadth** | D × the constituent TICK z over 09:30 → the entry bar (D663's definition): ES TICK-SP, NQ TICK-NQ, **YM TICK-NYSE**, **RTY the mean of the TICK-NYSE and TICK-NASDAQ z** | the cash market's participation in the move |
| f7 | **travel** | D × (entry − open) / A | how much of the day's range the break has already used |
| f8 | **clock** | minutes from 09:30 to the entry / 390 | an early break and a late break are different events |
| f9 | **side** | 1 if long | **the drift term**, declared as such. The gate's null (§5) absorbs it; the predictor may use it |

**Data rules:**
- A7 for YM and RTY is **built for this study** from Sierra Chart tick files, with `scripts/build_opening_a7.py`'s
  definition unchanged, in-sample sessions only (a contract running into the vault is sliced at 2025-02-28, as A10
  does). **The download needs the principal's approval** (§9).
- **Gate F** (D663) is applied to every TICK series. A series that fails it drops f6 for that root, declared in the
  output. The other features keep their slot.
- **Not used: the opening model's p_FADE.** It exists for ES and NQ only, and cannot be built for YM and RTY without
  the whole opening model. As D666's veto it removed only 48 NQ trades. It enters **only an ES/NQ development variant**
  (the model plus p_FADE), reported and never gated.

## 4. The expected-profit predictor, walk-forward, per root

**The target:** the trade's **E4 gross** in bp (the principal: "Expectant profit").

**The model:** ordinary least squares of the target on f1–f9 plus an intercept.
- It is fitted per root on **every earlier session's trades only**, and refitted before each session. A session's
  trades close by 16:00, so no fit sees its own outcome.
- Features are standardised with the training rows' means and sds.
- There is **no tuning, no feature selection and no penalty search**. The nine are the model.

**Burn-in:** the first **250 trades** of each root (about 1.6 years) are fitting only. The predictor's first forecast
is the 251st trade's.

**The prediction ŷ_i** is the model's forecast of trade i's gross.

**The pass-through π̂ and the projected profit** (the principal's rule): **projected_i = π̂_i × ŷ_i**.
- π̂_i is the through-origin slope of realised gross on ŷ over **all earlier out-of-sample forecasts** of the root:
  Σ y·ŷ / Σ ŷ².
- It needs a burn-in of 40 forecasts. Until then π̂ = 0 and nothing is traded by the filter.
- An overfitted model gets π̂ < 1, and one with no information gets π̂ near 0. The shrinkage is measured, not assumed.

**The filter:** trade when **projected_i ≥ 2 × cost_i** (the programme's k = 2).

**Sizing (secondary):** 1 micro at ≥ 2×cost, 2 at ≥ 4×cost, 3 at ≥ 6×cost.

**Does the predictor discriminate? (β_disc)** The out-of-sample slope, **with an intercept**, of realised gross on ŷ
over every forecast trade, with HAC t.
- π̂ can be positive just because ŷ's level is right. β_disc > 0 says the ranking is right.
- **Only β_disc shows the confluences are working.**

**Canaries, each must raise in `--selftest`:**
- a fit that includes the trade's own session;
- A7 taken at a checkpoint after the entry;
- a gap measured to the entry price;
- a π̂ that includes the trade's own outcome.

## 5. The controls

**N1, the clock-and-side null (the gate's null).** On **every** in-sample session of the root, not just the break
sessions:
- a trade at a minute drawn from **the break's own entry-minute distribution** on that root;
- its side is long with **the break's own long share**;
- entry at the bar's close + 1 tick, initial stop 0.25 A + 1 tick away, then the same E4 trail and close;
- 1,000 draws (seed 668), each the same size as the break's trade count;
- statistic: mean E4 gross per trade.

It has the same clock, the same side mix (so the same drift) and the same exit, **with no knowledge of the break**. It
is drawn on every session, so it cannot be handed the break's future (D666-A1's lesson).

**N2, for the predictor: the permuted-feature forecast.** The same walk-forward pipeline, with the feature rows shuffled
across sessions within each year (the targets stay in place). 200 draws. It gives a null for β_disc and for the
filtered net, and shows how much the filter earns by chance through the level term alone.

## 6. Statistics, reported per root, E4 primary

**Gate 1, the MECHANISM (unfiltered, gross):**
- the mean E4 gross per trade, one-sided, HAC t, **Holm across YM and RTY**;
- it must exceed N1's p95 by more than 2 bootstrap SE;
- it must be positive without February–April 2020.

**Gate 2, TRADEABILITY (filtered, net):** on a root that passed Gate 1:
- the filtered book's **net** per trade at 1 micro, one-sided, Holm across the roots at Gate 2;
- at least 30 filtered trades after both burn-ins, else UNRESOLVED;
- **β_disc > 0 with HAC t ≥ 2**, and above N2's p95;
- the filtered net stays > 0 at **+1 extra tick on every fill**.

**The four groups, per root and for the unfiltered, filtered and sized books:**
- net and gross side by side; Sharpe and Sortino, annualised by the book's own trades a year; exposure; maxDD;
  breakeven cost; the mean move per trade against 2c;
- the trade distribution: count, mean, median, win rate, payoff, skew, kurtosis, and the three 1%-trimmed means;
- what the winners depend on: by year, long against short, open class, before and after 2022-05-16, the top trade
  named;
- nulls: N1's and N2's p50 and p95, with the bootstrap SE, beside every score.

**The component line** (CLAUDE.md), computed by the runner:
- daily $ net Sharpe at 1 micro, hit rate, skew, gross beside net;
- ρ with every ledger component whose daily P&L the runner can rebuild. **K8 is rebuilt from the same fixture.** Any
  component it cannot rebuild is named as missing.

**Also reported:**
- the slippage ladder: net at +0 / +1 / +2 extra ticks on every fill, and on the open fills only;
- the filter's pass rate and π̂'s path;
- the net of the trades the filter removes;
- the fitted coefficients' walk-forward paths (sign stability of each feature).

**Development (ES, NQ):** everything above, run identically, **labelled DEVELOPMENT, with no verdict**. NQ is where
the thread was found; ES was its control. The ES/NQ variant with p_FADE (§3) is reported here only.

## 7. The prize and the power, before the run

The per-trade sd of E4 gross is taken from D667 (ES 34.7 bp, NQ 45.5), not from YM or RTY, which are unread. YM is
assumed ES-like and RTY NQ-like (similar ATR in bp).

| root | in-sample trades (≈ 157 a year) | assumed σ | Gate-1 MDE (80% power, Holm α 0.025) | vs NQ's +4.29 | vs ES's +1.20 |
|---|---:|---:|---:|---|---|
| YM | ≈ 1,430 (2016-01 →) | 35 bp | **2.6 bp** | powered | not powered |
| RTY | ≈ 1,200 (2017-07 →, the fixture's start) | 45 bp | **3.6 bp** | powered | not powered |

**So Gate 1 is decisive if the construction transfers at NQ's size, and blind if it transfers at ES's.**

**Gate 2 is harder on RTY.** M2K costs 4–6 bp a round trip, so the filter needs a projected 8–12 bp.

**Vault power,** for the later joint run: NQ about 245 vault trades, MDE ≈ 8 bp.

## 8. Verdict and routing, on YM and RTY

**Verdicts per root:**
- Gate 1 and Gate 2: **SUPPORTED**.
- Gate 1, and the **unfiltered** net > 0 (Holm), but Gate 2's β_disc fails: **BREAK ONLY**. The break carries, but
  the confluences do not predict. It routes as a plain-break component without a predictor.
- Gate 1 only: **MECHANISM ONLY**.
- Neither: **NOT SUPPORTED**.

**The construction's verdict:**
- **SUPPORTED on either evidence root:** a pre-registration for the joint vault run on all four roots (the break,
  the frozen model form, the filter, the component line), to the principal with its vault power. Anything built on
  GEX informs only the principal's own trading (the SqueezeMetrics permission).
- **BREAK ONLY:** the same, without the predictor.
- **NOT SUPPORTED on both:** the plain-break thread closes. NQ's in-sample +4.29 is recorded as not transferring.

## 9. Data, seals and order of work

**Seals, all in force:**
- **The vault** (2025-03-01 → 2026-09-18) is not read, on any root.
- Sierra tick and TICK files are read only before 2025-03-01.
- SqueezeMetrics is the prior row only. No per-date gamma leaves the runner (the licence guard), and it is credited.
- CL/NG post-vault data stays sealed until D626's read on 2026-10-10. It is not touched here.

**The order of work:**
1. This record, committed alone.
2. **The principal's approval for the Sierra downloads:** YM (CBOT) 2016H → 2025H, about 37 contracts, and RTY (CME)
   2017U → 2025H, about 31.
3. A7 for YM and RTY built and gated, the build's meta committed. The Gate F check on TICK-NYSE and TICK-NASDAQ.
4. `scripts/stage0_d668_break_predictor.py`, with `--selftest` (every canary above raises), `--dry-run`, and `--run`
   once.

**Speed, by design:** roots fan out to processes. The walk-forward refit is one OLS of at most ~1,500 × 10 per
session. N1's 1,000 draws and N2's 200 run on precomputed per-session paths.

## 10. Predictions, written before the run

1. **YM fails Gate 1.** It behaves like ES (+1.2).
2. **At most one of YM and RTY passes Gate 1.**
3. **β_disc has HAC t < 2 on every root, development included.** The confluences are individually weak (D667 §4).
4. **Development NQ reproduces D666's +4.29 exactly unfiltered, and its filtered net is within ±1.5 bp of the
   unfiltered.**
5. **The long side's gross exceeds the short side's on every root** (the drift).
6. **RTY's filter passes fewer than 30% of its forecast trades** (the M2K cost).
7. **The sign of f5 (A7) is negative on NQ's final fit,** as in D667.

## 11. Outputs

- `scripts/stage0_d668_break_predictor.py`;
- `data/stage0_d668_break_predictor.json` (statistics only, licence-guarded);
- A7 for YM and RTY under `data/opening/` (statistics only, as for ES and NQ);
- a RESULT record crediting SqueezeMetrics, with the component line.

No trials rows are written.
