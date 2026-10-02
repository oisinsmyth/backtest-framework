# D764 STAGE 0 RESULT — EFFECT, NO PRIZE: the CME bitcoin expiry window does reverse relative to other Fridays (Δρ −0.30, p 0.023), but the fade grosses $2.96 against a $4.31 cost, and the effect lived in 2018–2020 and is gone in the MBT era

*2026-10-02. Prop book.*
- *Pre-registration: [D764](D764-STAGE-0-PRE-REG-the-bitcoin-expiry-window.md) (`00b6509d`).*
- *Runner: `scripts/stage0_d764_btc_expiry_window.py` (`c046449d`).*
- *Output: `data/stage0_d764_btc_expiry_window.json`. Wall 4 s.*

**The first launch stopped before any result.** Nothing was printed or written: an empty percentile.
- **The cause:** the minute index came from an int64 view of the parsed timestamps, which pandas held in microseconds,
  so no bar fell in any window.
- **The fix** (`19bfcaf4`): minutes by subtraction, with a self-test that a fixture-format timestamp maps to the exact
  London-clock minute. It was committed before the one complete run.

**The checks:**
- the calendar: 72 expiry days, including the substitutes 2018-03-29 and 2020-12-24, and all 72 eligible with no
  stale prices;
- the lag audit (a raw-row loop on 40 sessions) passed;
- the rotation's offset 0 reproduced Δ;
- nothing dated 2024-01-01 or later was read.

## 1. The reading

x is the window move (P at 16:00 London − P at 15:00 London); y is the response (P at 17:00 London − P at 16:00
London).

| | value |
|---|---|
| ρ(x, y \| expiry days) | **−0.180** (n 72) |
| ρ(x, y \| other Fridays) | **+0.117** (n 229) |
| **E1: Δ** | **−0.296**; the full exact rotation's p05 / p50 / p95 are −0.227 / −0.001 / +0.240; **p 0.023** |
| E2: the fade's gross per MBT | **+$2.96** (t 0.81, median +$2.50) against a cost of **$4.31** |
| the same fade on other Fridays | −$3.41 (Welch t of the difference +1.59) |
| **reading** | **EFFECT, NO PRIZE** |

**Half of Δ is the control.** On ordinary Fridays the 15:00–16:00 London move *continues* into the next hour
(ρ +0.12). On expiry days it reverses (ρ −0.18).

**The rotation is conservative.** The expiry label recurs monthly, so the median rotation re-selects 24% of expiry
days, and the 90th percentile 38%. The pass is not that artefact.

## 2. The effect is in the early years

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|---:|---:|
| ρ_E (12 days a year) | −0.41 | **−0.72** | −0.59 | +0.10 | −0.08 | −0.14 |
| fade net, the year's sum | +$9 | +$50 | +$1 | **−$104** | **−$81** | +$29 |

- **The MBT era** (2021-05 onward, 32 expiries): ρ_E −0.06 against ρ_C +0.21. The fade grosses +$7.63 (t 1.43), but
  on 32 trades and with the reversal itself gone.
- **The reversal was strongest when CME bitcoin was young and thin.** It has faded as the market deepened, the same
  shape as D685's month-end and YM's close in D762.
- **The ETF era (2024 onward)** is outside this window. Nothing here says the effect returned there.

## 3. The fade (one MBT; four groups)

| | value |
|---|---|
| trades | 71 |
| net mean (median) | −$1.34 (−$1.81) |
| gross mean (median) | +$2.96 (+$2.50) |
| win (net) | 40.8% |
| payoff | 1.23 |
| skew / kurtosis (net) | −0.57 / 6.8 |
| daily net Sharpe (Sortino) | −0.15 (−0.20) |
| gross Sharpe (Sortino) | 0.33 (0.47) |
| max DD | $315 |
| break-even cost | $2.96 a round trip |
| with one extra tick | −$1.84 |

- **The trims are empty** (fewer than 100 trades).
- **Long against short:** long −$0.16 (30), short −$2.21 (41).
- **The best and worst days:**
  - the best is 2021-10-29 (+$112), the week of the first US bitcoin futures ETF (BITO launched 2021-10-19);
  - the worst are 2021-01-29 (−$118) and 2021-04-30 (−$112), both in the 2021 bull run.
- **ρ with F2, C1 and D737:** within ±0.02.

## 4. Reported

| | expiry days | other Fridays |
|---|---|---|
| **window volume (median contracts)** | **576** | 409 |
| mean \|x\| per MBT | $19.20 | $16.90 |
| mean \|y\| per MBT | $16.55 | $13.52 |
| mean x per MBT (the pressure's sign) | +$1.30 (t 0.36) | −$0.25 |
| ρ(x, y₂) (two hours) | −0.11 | +0.06 |
| ρ(pre-hour, x) | −0.06 | −0.09 |

- **The settlement window is busier on expiry days:** 41% more volume and 14% larger moves. **P2 held.**
- **No selling pressure:** the mean x is not negative. The basis-unwind story's direction is absent; only the
  reversal shape is there.
- **The reversal holds to two hours,** weaker (−0.11).

## 5. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | E1 fails (P 0.65) | **missed:** E1 passes (p 0.023) |
| P2 | \|x\| larger on expiry days (P 0.55) | **held:** $19.20 against $16.90; volume +41% |
| P3 | E2 below the cost (P 0.8) | **held:** +$2.96 against $4.31 |
| | P(PREMISE HOLDS) ≈ 0.06 | EFFECT, NO PRIZE |

## 6. What it shows, and the multiplicity

**The first clock-tied effect on the micros in this line.** On the day CME bitcoin settles, the reference-rate window
is busier and its move gives back afterwards, unlike ordinary Fridays.
- **It is a settlement-flow signature,** the shape the mechanism predicts.
- **It is too small for one MBT, and it faded after 2020.**

**The multiplicity.** This is one test among the line's tries:
- D762: four roots;
- D763: four roots, two families;
- D764: one.

At p 0.023, one pass in about 13 primary tests is near what chance alone gives. The year pattern (strong early, gone
since) makes chance less likely than a real effect that decayed, but neither reading makes it tradeable.

**What follows:**
- No trading pre-registration in-sample, since E2 fails.
- **An ETF-era read** (the held slice holds about 14 expiries; forward about 12 a year) would test whether a larger
  basis trade revived it. It would have little power, and it is the principal's call.
- **The principal's call:** whether to close the MBT expiry line.
