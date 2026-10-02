# D763 STAGE 0 PRE-REGISTRATION — the expiry-open fade: on monthly option-expiry Fridays, when index options (and, quarterly, the futures) settle on the opening prints, does the opening move (09:29 → 09:40) reverse by 10:40 more than on other Fridays? (ES, NQ, YM, RTY; VIX Wednesdays reported)

*2026-10-02. Prop book.*
- *The principal: "Ok lets close that idea and try the option expiry". They then chose "Expiry-open fade
  (Recommended)" from the constructions offered.*
- *Numbered D763, claimed with the documentation-review session.*
- ***Committed alone, before its runner exists.** In-sample only (2016-01-04 → 2023-12-29).*

## 0. The mechanism and what is on file

**The mechanism.** On the third Friday, monthly S&P 500, Nasdaq-100 and Russell 2000 index options are AM-settled:
- they settle to a **special opening quotation** (SOQ) built from each constituent's opening print;
- in March, June, September and December, the quarterly index futures settle to the same SOQ.
- **The forced trade:** holders and hedgers of expiring positions must trade at the open, whatever the price.
- **What it predicts:** pressure in the opening minutes that is not information, and gives back once it has cleared.
- **VIX expiry Wednesdays** settle the same way, through S&P option opening prints, and are reported as a second
  family.

**What it predicts that chance does not:**
- the opening move reverses more on expiry Fridays than on other Fridays, at the same clock, on the same root;
- more on quarterly Fridays (options and futures settle together) than on the other monthly ones.

**On file, and why this is not a repeat:**
- **Pinning:** read as repulsion (D614, D618; D409 on equities).
- **Gamma and the close:** nothing (D581).
- **The charm drift into Friday afternoon:** nothing (D754 B).
- **0DTE and the close:** not supported (D726).
- **None of these read the expiry open.**
- **Post hoc, from D762:** quarterly-expiry Fridays reversed after the cash close on RTY (ρ −0.32, n 26). That is the
  close, not the open, and it is not used here.

## 1. Data and the calendar (fixed now)

**Bars:** `fut_day1m.parquet` (09:00–15:59 ET, `bar` 0 = 09:00), ES, NQ, YM and RTY.
- Read with a predicate day < 2024-01-01, and the cut is asserted.
- `same_front` must be true (no roll in the session).
- The runner uses the system python (pyarrow). Ranks are computed in pandas.

**Prices** follow D727's convention: P_t is the close of the bar starting t−1, forward-filled within the session.

| quantity | definition |
|---|---|
| P₀₉:₃₀ (pre-cash) | the close of the 09:29 bar |
| **x, the opening pressure** | P₀₉:₄₀ − P₀₉:₃₀ |
| **y, the response** | P₁₀:₄₀ − P₀₉:₄₀ |
| y_close (reported) | P₁₆:₀₀ − P₀₉:₄₀ |
| gap (reported) | P₀₉:₃₀ − the prior session's P₁₆:₀₀, same contract only |

**Eligible sessions:** a root's sessions with the 09:29, 09:39, 10:39 and 15:59 bars present, from 2016-01-04 (RTY from
2017-07-10).

**The expiry calendar:**
- **E_M, the monthly expiry day:** the third Friday of each month. If ES has no session that day, the previous ES
  session (for example 2019-04-18 and 2022-04-14, the Thursdays before Good Friday).
- **E_Q:** the March, June, September and December members of E_M.
- **E_V, the VIX expiry day:**
  - find the third Friday of the following month, or the session before it if that Friday is not an ES session;
  - subtract 30 calendar days;
  - if the result is not an ES session, take the previous session.
- **Spot-checked against published dates:** 2018-02-14, 2019-03-19 (a Tuesday, because Good Friday 2019 moved the April
  reference day) and 2020-03-18.
- **Controls:**
  - C_M = every eligible Friday not in E_M;
  - C_V = every eligible Wednesday not in E_V.

## 2. The checks (per root)

**E1 — the expiry effect.**
- **The statistic:** Δ = ρ(x, y | E_M) − ρ(x, y | C_M), with Spearman ρ computed within each set.
- **The null:** the exact enumerated **rotation of the expiry label** along that root's ordered list of eligible
  Fridays (offsets 1 … N−1).
  - The rotation keeps the count and the four-to-five-week spacing of expiry days, so the null is count-matched (the
    D760 lesson).
- **Passes:** Δ < 0, below the rotation's p05 (one-sided), after Holm across the four roots at α = 0.05.
- **Reported:** ρ_E and ρ_C separately.

**E2 — the prize.**
- **The fade:** on E_M days, take the side −sign(x) at P₀₉:₄₀ and exit at P₁₀:₄₀, one micro, net of the
  default-line cost.
- **Passes:** the mean gross ≥ the cost, with t ≥ 2.
- **Reported:** the same fade on C_M days, and the difference of the means with a Welch SE.

**The readings, per root:**

| reading | when |
|---|---|
| **NO EFFECT** | E1 fails |
| **EFFECT, NO PRIZE** | E1 passes; E2 fails |
| **PREMISE HOLDS** | E1 and E2 pass |

**The VIX family:** E1 and E2 on E_V against C_V (Wednesdays), with its own Holm over the four roots. It is reported
with its own readings and **never rescues the monthly family**.

**What follows a PREMISE HOLDS:** a trading pre-registration read on the held 2024-01 → 2025-02 slice and forward, on
the principal's word. There are about 14 expiry Fridays on the held slice, so that read would have little power, and
the trading record would have to say so.

## 3. Reported, never gating

- E_Q against the other monthly expiry days: the dose-response.
- The y_close horizon, and the gap as the pressure.
- By year;
- the four groups of the E2 fade, with the top trades named;
- ρ of its daily net with F2, C1 and D737 (`data/d748_component_books.csv`);
- long against short;
- the fade's net with one extra tick of crossing.

## 4. Size and power (stated now)

- **The events:** about 96 E_M days per root (RTY about 78), 32 of them quarterly, against about 300 control Fridays.
- **The SE:**
  - ρ_E has an SE of about 0.10, so E1 can detect Δ of about −0.25 or larger;
  - the E2 fade has an SE of about sd(y) / √96. With a guessed sd near $40 per MES, that is about $4.
- **The prize:** the opening ten minutes move about $15–25 per MES. If a quarter of x reverses, a fade grosses about
  $4–6, near the cost.
- **So:** this is a test for a large effect. A NO EFFECT is weak evidence against a small one.

## 5. The runner's assertions (each proved to raise in `--selftest`)

1. **The calendar:**
   - every E_M day is a Friday, or a Thursday before a Friday with no ES session;
   - there are 12 per year;
   - E_V matches the three published dates;
   - no E_M day is in C_M.
2. **Lag audit, a second implementation:** for 40 sampled sessions per root (half of them expiry days), a plain loop
   over the raw rows re-derives P₀₉:₃₀, x, y and y_close. **Break:** reading x from the 09:40 bar (one minute late)
   must raise.
3. **Sign in money:** a favourable move pays long and short positively.
4. **The rotation's offset 0** equals the observed Δ.
5. **The seal:** a 2024-dated row injected into the input raises.
6. **Synthetic:** a planted expiry-day reversal passes E1, and noise fails E1 about 95% of the time.

**Speed.** The parquet read is filtered, and the rotation is about 400 offsets of two rank correlations per root. The
projected wall time is under a minute.

**Output:** `data/stage0_d763_expiry_open.json`.

## 6. Predictions (Opus)

- **P1: E1 fails on every root** (P 0.6). The SOQ flow is real, but the opening ten minutes carry so much other
  information (the overnight, data at 08:30) that a settlement effect is hard to see on about 96 days.
- **P2:** if any root passes E1, it is ES or RTY (P 0.6 given a pass): the deepest AM-settled option markets (SPX)
  and the Russell's thinner opening auction.
- **P3:** the E2 fade's mean gross is below the cost on every root (P 0.7).
- **P(PREMISE HOLDS on any root) ≈ 0.08.**
